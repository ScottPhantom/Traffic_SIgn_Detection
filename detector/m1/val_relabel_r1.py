# ruff: noqa: E501
"""D1-VRL-R1: derived validation labels with ignore regions (append-only, validation only).

Implements the owner scope `docs/review/d1_vrl_r1_owner_scope_record.md` on the D1-VLA-R1
proposals (`docs/review/generated/d1_vla_r1_proposed_val_labels.csv`, independent QA PASS):

- every proposal's model box is used only as a locator; the written box is re-fitted from the
  image pixels (red/blue sign region, HSV saturation > 0.15) by the deterministic `refine_box`;
- the pinned box-review notes decide each proposal: `ACCEPT_REFINED` adds the re-fitted box as
  ground truth; `IGNORE_REGION` adds no ground truth and marks the locator box, expanded by 25 % per
  side, as a region where an unmatched prediction is not a false positive;
- derived label files = the WP38-R1 R4 validation labels plus the accepted boxes, written to a new
  git-ignored directory; raw, R4, train and test labels are untouched; ids follow
  `m1_yolo_classes.csv` (QA L2 of D1-VLA-R1).

The diagnostic at conf 0.20 re-scores the D1-EA-R1 exported predictions; it is not an evaluation
authority and changes no gate. No model is loaded. `build` refuses to overwrite; `verify`
regenerates everything and byte-compares, including every derived label file.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import sys
from collections import Counter, deque
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from m1 import contract
from m1 import error_analysis_r1 as ea
from m1.metrics import IOU_MATCH, Frame, iou_matrix, operating_point

REPO_ROOT = contract.REPO_ROOT
PACKAGE = "D1-VRL-R1"
STATUS = "D1_VRL_R1_AWAITING_INDEPENDENT_QA"
BOUNDARY = "DERIVED_VALIDATION_LABELS_NOT_YET_EVALUATION_AUTHORITY_NO_GATE_CHANGE_NO_TRAINING_NO_SEALED_TEST"

PROPOSALS = Path("docs/review/generated/d1_vla_r1_proposed_val_labels.csv")
NOTES = Path("docs/review/d1_vrl_r1_box_review_notes.csv")
SCOPE = Path("docs/review/d1_vrl_r1_owner_scope_record.md")
CLASS_MAP = Path("docs/review/generated/m1_yolo_classes.csv")
SOURCE_LABELS = Path("data/processed/m1_yolo_wp38_r1_integration_r4/labels/val")
PINNED: dict[Path, str] = {
    PROPOSALS: "70773b4be23e223ae149e616098d7d91d1042cdcfd689f220030fa83fbd32356",
    NOTES: "4458474f2c75830567bc094f43d46cad885fab4245d3347ad4f9790f78736101",
    SCOPE: "a96e55f464dfd98c0a08ace0db11d589429a420b3f752d02f74584a04c4a103b",
    Path(
        "docs/review/generated/d1_vla_r1_manifest.json"
    ): "3fbbe7fd2b2bc44f632f676cfa60861f963a1cf31b193119c49049e9ed9c2e46",
    Path(
        "detector/m1/val_label_audit_r1.py"
    ): "3826fa57a7cb8d7611c941ce590d7b9f785f4fc23e562842f9aa39c7a99838cf",
    Path(
        "docs/review/d1_vla_r1_independent_qa_record.md"
    ): "5e856b77dace347774246e4f11a38379f3b068182e65bf35e92dac56c030948c",
    Path(
        "docs/review/d1_vla_r1_correction_r1.md"
    ): "be06ee8949db75bc964e5d41d4c646fe95de7a90b9a1790194b23727fd282765",
    ea.PREDICTIONS_PATH: "cb3cb05f0cadc7d2c3e077120d5b1311648247f74a9648e287da1c4be915f1dd",
    CLASS_MAP: "7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242",
}

SATURATION = 0.15
IGNORE_MARGIN = 0.25
IGNORE_IOA = 0.5

OUT_DIR = Path("data/processed/m1_yolo_val_vrl_r1")
OUT_LABELS = OUT_DIR / "labels/val"
OUT_IGNORE = OUT_DIR / "ignore_regions.json"
GENERATED = Path("docs/review/generated")
ADDED_PATH = GENERATED / "d1_vrl_r1_added_boxes.csv"
IGNORE_PATH = GENERATED / "d1_vrl_r1_ignore_regions.csv"
MANIFEST_PATH = GENERATED / "d1_vrl_r1_manifest.json"
REPORT_PATH = Path("docs/review/d1_vrl_r1_report.md")
ATLAS_DIR = Path("docs/review/assets/d1_vrl_r1")

ADDED_FIELDS = [
    "proposal_id",
    "stem",
    "derived_key",
    "yolo_id",
    "x1",
    "y1",
    "x2",
    "y2",
    "x_center",
    "y_center",
    "width",
    "height",
    "iou_vs_model_box",
    "source_review_ids",
]
IGNORE_FIELDS = [
    "proposal_id",
    "stem",
    "derived_key",
    "x1",
    "y1",
    "x2",
    "y2",
    "reason",
    "source_review_ids",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verify_pins(repo_root: Path = REPO_ROOT) -> None:
    for relative, expected in PINNED.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or ea.sha256_file(path) != expected:
            raise RuntimeError(f"pinned D1-VRL-R1 source differs: {relative}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


# ------------------------------------------------------------------------------- box re-fitting


def colour_mask(rgb: np.ndarray) -> np.ndarray:
    hsv = np.asarray(Image.fromarray(rgb).convert("HSV"), dtype=np.float32)
    h, s, v = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
    red = ((h < 20) | (h > 330)) & (s > SATURATION) & (v > 0.15)
    blue = (h > 190) & (h < 260) & (s > SATURATION) & (v > 0.12)
    return red | blue


def components(mask: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Bounding boxes (x0, y0, x1, y1, exclusive) of 8-connected components, in scan order."""
    seen = np.zeros(mask.shape, dtype=bool)
    height, width = mask.shape
    boxes = []
    for y in range(height):
        for x in range(width):
            if not mask[y, x] or seen[y, x]:
                continue
            queue = deque([(y, x)])
            seen[y, x] = True
            y0, y1, x0, x1 = y, y, x, x
            while queue:
                a, b = queue.popleft()
                y0, y1, x0, x1 = min(y0, a), max(y1, a), min(x0, b), max(x1, b)
                for da in (-1, 0, 1):
                    for db in (-1, 0, 1):
                        c, d = a + da, b + db
                        if 0 <= c < height and 0 <= d < width and mask[c, d] and not seen[c, d]:
                            seen[c, d] = True
                            queue.append((c, d))
            boxes.append((x0, y0, x1 + 1, y1 + 1))
    return boxes


def _iou(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = w * h
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def refine_box(
    image: Image.Image, locator: tuple[float, float, float, float], min_iou: float = 0.3
) -> tuple[int, int, int, int] | None:
    width, height = image.size
    x1, y1, x2, y2 = locator
    bw, bh = x2 - x1, y2 - y1
    left, top = int(max(0, x1 - bw)), int(max(0, y1 - bh))
    right, bottom = int(min(width, x2 + bw)), int(min(height, y2 + bh))
    mask = colour_mask(np.asarray(image.crop((left, top, right, bottom)).convert("RGB")))
    best: tuple[float, tuple[int, int, int, int]] | None = None
    for cx0, cy0, cx1, cy1 in components(mask):
        box = (cx0 + left, cy0 + top, cx1 + left, cy1 + top)
        score = _iou(box, locator)
        if best is None or score > best[0]:
            best = (score, box)
    if best is None or best[0] < min_iou:
        return None
    return best[1]


# ------------------------------------------------------------------------------------- derive


def load_inputs(repo_root: Path) -> dict[str, Any]:
    proposals = _read_csv(repo_root / PROPOSALS)
    notes = _read_csv(repo_root / NOTES)
    if len(notes) != len(proposals):
        raise RuntimeError("box-review notes must cover every proposal")
    for number, (prop, note) in enumerate(zip(proposals, notes, strict=True), start=1):
        if (
            note["proposal_id"] != f"R{number:03d}"
            or note["stem"] != prop["stem"]
            or note["derived_key"] != prop["derived_key"]
        ):
            raise RuntimeError(f"box-review note {number} does not match its proposal")
        if (
            note["box_decision"] not in {"ACCEPT_REFINED", "IGNORE_REGION"}
            or not note["note"].strip()
        ):
            raise RuntimeError(f"invalid box decision for {note['proposal_id']}")
    key_to_yolo = {r["derived_key"]: int(r["yolo_id"]) for r in _read_csv(repo_root / CLASS_MAP)}
    images = {p.stem: p for p in ea.val_images(repo_root)}
    return {"proposals": proposals, "notes": notes, "key_to_yolo": key_to_yolo, "images": images}


def derive(repo_root: Path) -> dict[str, Any]:
    data = load_inputs(repo_root)
    added, ignored = [], []
    for prop, note in zip(data["proposals"], data["notes"], strict=True):
        with Image.open(data["images"][prop["stem"]]) as source:
            image = source.convert("RGB")
        width, height = image.size
        x, y, w, h = (float(prop[k]) for k in ("x_center", "y_center", "width", "height"))
        locator = (
            (x - w / 2) * width,
            (y - h / 2) * height,
            (x + w / 2) * width,
            (y + h / 2) * height,
        )
        refined = refine_box(image, locator)
        if note["box_decision"] == "ACCEPT_REFINED":
            if refined is None:
                raise RuntimeError(f"{note['proposal_id']} accepted but re-fitting finds no box")
            rx1, ry1, rx2, ry2 = refined
            added.append(
                {
                    "proposal_id": note["proposal_id"],
                    "stem": prop["stem"],
                    "derived_key": prop["derived_key"],
                    "yolo_id": data["key_to_yolo"][prop["derived_key"]],
                    "x1": rx1,
                    "y1": ry1,
                    "x2": rx2,
                    "y2": ry2,
                    "x_center": f"{(rx1 + rx2) / 2 / width:.6f}",
                    "y_center": f"{(ry1 + ry2) / 2 / height:.6f}",
                    "width": f"{(rx2 - rx1) / width:.6f}",
                    "height": f"{(ry2 - ry1) / height:.6f}",
                    "iou_vs_model_box": f"{_iou(refined, locator):.4f}",
                    "source_review_ids": prop["source_review_ids"],
                }
            )
        else:
            mx, my = (
                IGNORE_MARGIN * (locator[2] - locator[0]),
                IGNORE_MARGIN * (locator[3] - locator[1]),
            )
            ignored.append(
                {
                    "proposal_id": note["proposal_id"],
                    "stem": prop["stem"],
                    "derived_key": prop["derived_key"],
                    "x1": f"{max(0.0, locator[0] - mx):.2f}",
                    "y1": f"{max(0.0, locator[1] - my):.2f}",
                    "x2": f"{min(width, locator[2] + mx):.2f}",
                    "y2": f"{min(height, locator[3] + my):.2f}",
                    "reason": note["note"],
                    "source_review_ids": prop["source_review_ids"],
                }
            )
    return {"added": added, "ignored": ignored, "images": data["images"]}


def derived_labels(repo_root: Path, added: list[dict[str, Any]]) -> dict[str, bytes]:
    extra: dict[str, list[str]] = {}
    for row in added:
        extra.setdefault(row["stem"], []).append(
            f"{row['yolo_id']} {row['x_center']} {row['y_center']} {row['width']} {row['height']}"
        )
    out = {}
    for path in sorted((repo_root / SOURCE_LABELS).glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        lines = [line for line in text.splitlines() if line.strip()] + extra.get(path.stem, [])
        out[path.name] = ("\n".join(lines) + "\n").encode("utf-8") if lines else b""
    if len(out) != 376 or set(extra) - {name[:-4] for name in out}:
        raise RuntimeError("derived label roster differs from the 376 validation frames")
    return out


# --------------------------------------------------------------------------------- diagnostic


def unmatched_predictions(frame: Frame, conf: float) -> list[np.ndarray]:
    """Boxes of the class-agnostic false positives, in the same greedy order as `metrics.match`."""
    keep = frame.pred_scores >= conf
    boxes, scores = frame.pred_boxes[keep], frame.pred_scores[keep]
    ious = iou_matrix(boxes, frame.gt_boxes)
    matched = np.zeros(len(frame.gt_boxes), dtype=bool)
    out = []
    for index in np.argsort(-scores, kind="stable"):
        candidates = ious[index].copy()
        candidates[matched] = -1.0
        best = int(np.argmax(candidates)) if len(candidates) else -1
        if best >= 0 and candidates[best] >= IOU_MATCH:
            matched[best] = True
        else:
            out.append(boxes[index])
    return out


def diagnostic(
    repo_root: Path, added: list[dict[str, Any]], ignored: list[dict[str, Any]]
) -> dict[str, Any]:
    names = ea.class_names(repo_root)
    rows = _read_csv(repo_root / ea.PREDICTIONS_PATH)
    frames = ea.frames_from_rows(rows, names, repo_root)
    add: dict[str, list[tuple[int, list[float]]]] = {}
    for row in added:
        add.setdefault(row["stem"], []).append(
            (names.index(row["derived_key"]), [float(row[k]) for k in ("x1", "y1", "x2", "y2")])
        )
    regions: dict[str, list[list[float]]] = {}
    for row in ignored:
        regions.setdefault(row["stem"], []).append(
            [float(row[k]) for k in ("x1", "y1", "x2", "y2")]
        )
    relabelled = []
    for frame in frames:
        extra = add.get(frame.stem, [])
        relabelled.append(
            replace(
                frame,
                gt_boxes=np.vstack(
                    [frame.gt_boxes, np.asarray([b for _c, b in extra]).reshape(-1, 4)]
                ),
                gt_classes=np.concatenate(
                    [frame.gt_classes, np.asarray([c for c, _b in extra], dtype=int)]
                ),
            )
        )
    point = operating_point(relabelled, ea.CONF)
    ignored_fp = 0
    for frame in relabelled:
        for box in unmatched_predictions(frame, ea.CONF):
            area = (box[2] - box[0]) * (box[3] - box[1])
            for region in regions.get(frame.stem, []):
                w = max(0.0, min(box[2], region[2]) - max(box[0], region[0]))
                h = max(0.0, min(box[3], region[3]) - max(box[1], region[1]))
                if area > 0 and w * h / area >= IGNORE_IOA:
                    ignored_fp += 1
                    break
    fp = point.false_positives - ignored_fp
    return {
        "images": point.images,
        "ground_truth": point.ground_truth,
        "added_ground_truth": len(added),
        "ignore_regions": len(ignored),
        "false_positives_before_ignore": point.false_positives,
        "false_positives_in_ignore_regions": ignored_fp,
        "false_positives": fp,
        "fp_per_image": round(fp / point.images, 6),
        "agnostic_recall": round(point.agnostic_recall, 6),
        "precision": round(point.true_positives / (point.true_positives + fp), 6),
    }


# -------------------------------------------------------------------------------------- render


def render_atlas(added: list[dict[str, Any]], images: dict[str, Path]) -> dict[Path, bytes]:
    font = ImageFont.load_default(size=16)
    tile = 360
    pages = {}
    for start in range(0, len(added), 16):
        sheet = Image.new("RGB", (4 * tile, 4 * (tile + 24)), "white")
        draw = ImageDraw.Draw(sheet)
        for k, row in enumerate(added[start : start + 16]):
            with Image.open(images[row["stem"]]) as source:
                image = source.convert("RGB")
            width, height = image.size
            b = [row["x1"], row["y1"], row["x2"], row["y2"]]
            side = max(40.0, 2.5 * max(b[2] - b[0], b[3] - b[1]))
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            left, top = (
                max(0.0, min(cx - side / 2, width - side)),
                max(0.0, min(cy - side / 2, height - side)),
            )
            scale = tile / side
            crop = image.crop((int(left), int(top), int(left + side), int(top + side))).resize(
                (tile, tile), Image.LANCZOS
            )
            ImageDraw.Draw(crop).rectangle(
                [
                    (b[0] - left) * scale,
                    (b[1] - top) * scale,
                    (b[2] - left) * scale,
                    (b[3] - top) * scale,
                ],
                outline="#00ff00",
                width=2,
            )
            x, y = (k % 4) * tile, (k // 4) * (tile + 24)
            sheet.paste(crop, (x, y))
            draw.text(
                (x + 3, y + tile + 3),
                f"{row['proposal_id']} {row['stem']} key {row['derived_key']} -> yolo {row['yolo_id']}",
                fill="black",
                font=font,
            )
        buffer = io.BytesIO()
        sheet.save(buffer, format="JPEG", quality=90)
        pages[ATLAS_DIR / f"added_page_{start // 16 + 1:02d}.jpg"] = buffer.getvalue()
    return pages


def render_report(
    added: list[dict[str, Any]],
    ignored: list[dict[str, Any]],
    diag: dict[str, Any],
    base: dict[str, Any],
) -> str:
    by_key = Counter(r["derived_key"] for r in added)
    reasons = Counter(
        "small low-saturation sign" if r["reason"].startswith("no reliable") else "partial re-fit"
        for r in ignored
    )
    ious = sorted(float(r["iou_vs_model_box"]) for r in added)
    return f"""# D1-VRL-R1 — derived validation labels with ignore regions

Status: `{STATUS}`
Boundary: `{BOUNDARY}`

Built from the owner scope `{SCOPE}` on the 104 D1-VLA-R1 proposals. Raw, WP38-R1 R4, train and
test labels are unchanged. The derived validation labels are written to `{OUT_LABELS}/`
(git-ignored) and ignore regions to `{OUT_IGNORE}`; every file is hashed in the manifest. These
labels are **not yet the evaluation authority**: that needs independent QA of this package, an
owner acceptance record and a QA-passed re-evaluation contract.

## Boxes

- Added ground truth: **{len(added)}** re-fitted boxes ({", ".join(f"key {k}: {v}" for k, v in sorted(by_key.items(), key=lambda kv: int(kv[0])))}).
  Each is re-fitted from the sign's red/blue pixels (HSV saturation > {SATURATION}) around the
  model's locator box and visually checked. IoU with the model box: min {ious[0]:.2f}, median
  {ious[len(ious) // 2]:.2f}, max {ious[-1]:.2f} — the re-evaluation does not match the model
  against its own boxes (D1-VLA-R1 QA M1).
- Ignore regions: **{len(ignored)}** ({", ".join(f"{k}: {v}" for k, v in reasons.items())}). Locator box
  expanded by {IGNORE_MARGIN:.0%} per side; an unmatched prediction with ≥ {IGNORE_IOA:.0%} of its area
  inside a region is not a false positive. No ground truth is added for them.
- Ids are YOLO ids mapped from derived keys through `{CLASS_MAP}`.

## Diagnostic at conf {ea.CONF} (re-scoring the D1-EA-R1 exported predictions)

| Labels | GT | FP | FP in ignore regions | FP/image | Agnostic recall | Precision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| R10 (WP38-R1 R4) | {base["ground_truth"]} | {base["false_positives"]} | — | {base["fp_per_image"]:.3f} | {base["agnostic_recall"]:.4f} | {base["precision"]:.4f} |
| D1-VRL-R1 | {diag["ground_truth"]} | {diag["false_positives"]} | {diag["false_positives_in_ignore_regions"]} | {diag["fp_per_image"]:.3f} | {diag["agnostic_recall"]:.4f} | {diag["precision"]:.4f} |

This is a diagnostic, not an evaluation: it uses only predictions with confidence ≥ {ea.CONF}, so it
cannot select a threshold or compute mAP, and it changes no gate. The critical classes 7, 32 and 41
are untouched. A D-05 decision needs a QA-passed evaluator run on the derived labels.

## Limits

- **The ignore-region FP drop is circular by construction.** Each region is the model's own locator
  box expanded by {IGNORE_MARGIN:.0%}, so the {diag["false_positives_in_ignore_regions"]} ignored false
  positives are those same predictions. The drop from {diag["false_positives_before_ignore"]} to
  {diag["false_positives"]} FP restates the owner's ignore decision; it is not evidence that the model
  is right on those discs. Only the {len(added)} re-fitted boxes are independent of the model geometry.
- Only signs the model detected were audited (D1-VLA-R1); unlabelled signs it missed remain.
- Ignore regions remove the small pole discs from both recall and false positives; per-class recall
  for classes 10/23/39/41 on those frames is therefore not measured.
- Review pages: `{ATLAS_DIR}/` (git-ignored).
"""


def render(repo_root: Path = REPO_ROOT) -> dict[Path, bytes]:
    verify_pins(repo_root)
    derived = derive(repo_root)
    added, ignored = derived["added"], derived["ignored"]
    labels = derived_labels(repo_root, added)
    ignore_doc = {
        "rule": {"margin_per_side": IGNORE_MARGIN, "min_prediction_area_inside": IGNORE_IOA},
        "regions": {
            stem: [
                [float(r[k]) for k in ("x1", "y1", "x2", "y2")]
                for r in ignored
                if r["stem"] == stem
            ]
            for stem in sorted({r["stem"] for r in ignored})
        },
    }
    names = ea.class_names(repo_root)
    base_point = operating_point(
        ea.frames_from_rows(_read_csv(repo_root / ea.PREDICTIONS_PATH), names, repo_root), ea.CONF
    )
    base = {
        "ground_truth": base_point.ground_truth,
        "false_positives": base_point.false_positives,
        "fp_per_image": round(base_point.fp_per_image, 6),
        "agnostic_recall": round(base_point.agnostic_recall, 6),
        "precision": round(base_point.precision, 6),
    }
    if base["false_positives"] != 214:
        raise RuntimeError("D1-EA-R1 baseline differs from R10")
    diag = diagnostic(repo_root, added, ignored)
    artifacts: dict[Path, bytes] = {
        ADDED_PATH: ea.csv_bytes(ADDED_FIELDS, added),
        IGNORE_PATH: ea.csv_bytes(IGNORE_FIELDS, ignored),
        OUT_IGNORE: (json.dumps(ignore_doc, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        **{OUT_LABELS / name: data for name, data in labels.items()},
        **render_atlas(added, derived["images"]),
    }
    artifacts[REPORT_PATH] = render_report(added, ignored, diag, base).encode("utf-8")
    manifest = {
        "package": PACKAGE,
        "status": STATUS,
        "boundary": BOUNDARY,
        "summary": {
            "added_ground_truth": len(added),
            "ignore_regions": len(ignored),
            "baseline": base,
            "diagnostic": diag,
        },
        "derived_label_dir": str(OUT_LABELS),
        "source_label_dir": str(SOURCE_LABELS),
        "derived_label_roster_sha256": sha256_bytes(
            json.dumps(
                {n: sha256_bytes(d) for n, d in sorted(labels.items())}, sort_keys=True
            ).encode()
        ),
        "pinned_sources": {str(p): d for p, d in sorted(PINNED.items(), key=lambda kv: str(kv[0]))},
        "pillow_version": importlib.metadata.version("pillow"),
        "artifacts": {
            str(p): sha256_bytes(d) for p, d in sorted(artifacts.items(), key=lambda kv: str(kv[0]))
        },
        "evaluation_authority": False,
        "gates_changed": False,
        "training_authorized": False,
        "train_or_test_labels_changed": False,
        "test_included": False,
        "sealed_test_accessed": False,
    }
    artifacts[MANIFEST_PATH] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    return artifacts


def build(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    targets = [ADDED_PATH, IGNORE_PATH, MANIFEST_PATH, REPORT_PATH]
    if (
        any((repo_root / p).exists() for p in targets)
        or (repo_root / OUT_DIR).exists()
        or (repo_root / ATLAS_DIR).exists()
    ):
        raise RuntimeError("D1-VRL-R1 outputs already exist; the package is append-only")
    artifacts = render(repo_root)
    for path, data in artifacts.items():
        (repo_root / path).parent.mkdir(parents=True, exist_ok=True)
        (repo_root / path).write_bytes(data)
    return {
        "status": STATUS,
        "artifacts": len(artifacts),
        "summary": json.loads(artifacts[MANIFEST_PATH])["summary"],
    }


def verify(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        expected = render(repo_root)
        for path, data in expected.items():
            target = repo_root / path
            if not target.is_file() or target.is_symlink() or target.read_bytes() != data:
                errors.append(f"artifact differs: {path}")
        for directory in (OUT_LABELS, ATLAS_DIR):
            folder = repo_root / directory
            if folder.is_dir():
                errors += [
                    f"unexpected file: {directory / p.name}"
                    for p in folder.iterdir()
                    if directory / p.name not in expected
                ]
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        errors.append(str(error))
    return {"status": STATUS, "valid": not errors, "errors": errors[:20]}


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    sub.add_parser("verify")
    args = root.parse_args(argv)
    try:
        result = build() if args.command == "build" else verify()
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command == "build" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
