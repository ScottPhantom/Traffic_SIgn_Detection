# ruff: noqa: E501
"""D1-VRL-R2: derived validation labels, hand-drawn successor of D1-VRL-R1 (append-only, validation only).

Implements the owner re-decision in `docs/review/d1_vrl_r1_correction_r1.md` after the D1-VRL-R1
independent QA (FAIL on H1):

- `ACCEPT_REFINED`: the D1-VRL-R1 pixel re-fit (`val_relabel_r1.refine_box`) is re-run and used;
- `ACCEPT_REFINED_ADJUSTED`: the re-fit must still succeed, and the noted box may only tighten it
  (QA L1);
- `HAND_DRAWN`: the box in the pinned notes, drawn by eye without the model box, is used; allowed
  only when the locator's longer side is > 17.5 px;
- `IGNORE_REGION`: allowed only when the locator's longer side is ≤ 17.5 px; the region is the
  locator expanded by 25 % per side, as in D1-VRL-R1.

The diagnostic re-scores the D1-EA-R1 exported predictions at conf 0.20; it is not an evaluation
authority. `verify` regenerates everything and byte-compares, and refuses any other file anywhere
under the derived root (QA L3). The R4 validation labels are pinned by content (QA L4).
"""

from __future__ import annotations

import argparse
import importlib.metadata
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from m1 import contract
from m1 import error_analysis_r1 as ea
from m1 import val_relabel_r1 as r1
from m1.metrics import operating_point

REPO_ROOT = contract.REPO_ROOT
PACKAGE = "D1-VRL-R2"
STATUS = "D1_VRL_R2_AWAITING_INDEPENDENT_QA"
BOUNDARY = r1.BOUNDARY

NOTES = Path("docs/review/d1_vrl_r2_box_review_notes.csv")
CORRECTION = Path("docs/review/d1_vrl_r1_correction_r1.md")
R4_MANIFEST = Path("docs/review/generated/m1_yolo_wp38_r1_integration_r4_manifest.json")
R4_VAL_LABELS_SHA256 = "e64345bb3a618187d10828ccc135172736ff45956570359da4fa99d441f320cc"
PINNED: dict[Path, str] = {
    **r1.PINNED,
    NOTES: "a9c05fa8ad578de0eaa819e123e5a89c055576d2c28853cf529708d5407eda2e",
    CORRECTION: "d3376ec32b13ea33ec94a43b124d6738d541ab2c1b35a465fa07361ce4b318d0",
    Path(
        "docs/review/d1_vrl_r1_independent_qa_record.md"
    ): "e168b6bf2cb5b3322ff3f3ffb7701bf65433952610baeafe42aeca1e435fab0c",
    Path(
        "detector/m1/val_relabel_r1.py"
    ): "9fba10089ad23fc494b2548fec60acf4d07ae34feebcc8bfb530887b0ff5eff5",
    Path(
        "docs/review/generated/d1_vrl_r1_manifest.json"
    ): "3fd91263dabc775bf8967e604a589bb20143bfc43fb45f2e16fa814e973eb34f",
    R4_MANIFEST: "6982a76f06f7486dd5d14015b7858ea74088f6ab3fcad6d54c576772b3c7e602",
}

SMALL_PX = 17.5
MAX_TIGHTEN_PX = 6
DARK_STEMS = {f"{n:04d}" for n in range(1823, 1838)}
DECISIONS = {"ACCEPT_REFINED", "ACCEPT_REFINED_ADJUSTED", "HAND_DRAWN", "IGNORE_REGION"}

OUT_DIR = Path("data/processed/m1_yolo_val_vrl_r2")
OUT_LABELS = OUT_DIR / "labels/val"
OUT_IGNORE = OUT_DIR / "ignore_regions.json"
GENERATED = Path("docs/review/generated")
ADDED_PATH = GENERATED / "d1_vrl_r2_added_boxes.csv"
IGNORE_PATH = GENERATED / "d1_vrl_r2_ignore_regions.csv"
MANIFEST_PATH = GENERATED / "d1_vrl_r2_manifest.json"
REPORT_PATH = Path("docs/review/d1_vrl_r2_report.md")
ATLAS_DIR = Path("docs/review/assets/d1_vrl_r2")

ADDED_FIELDS = [
    "proposal_id",
    "stem",
    "derived_key",
    "yolo_id",
    "source",
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
IGNORE_FIELDS = r1.IGNORE_FIELDS


def r4_val_labels_sha256(repo_root: Path) -> str:
    labels = {
        p.stem: p.read_text(encoding="utf-8") for p in (repo_root / r1.SOURCE_LABELS).glob("*.txt")
    }
    return r1.sha256_bytes(
        "".join(f"{stem}\n{labels[stem]}" for stem in sorted(labels)).encode("utf-8")
    )


def verify_pins(repo_root: Path = REPO_ROOT) -> None:
    for relative, expected in PINNED.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or ea.sha256_file(path) != expected:
            raise RuntimeError(f"pinned D1-VRL-R2 source differs: {relative}")
    if r4_val_labels_sha256(repo_root) != R4_VAL_LABELS_SHA256:
        raise RuntimeError("WP38-R1 R4 validation labels differ from labels_sha256 e64345bb…")


def _box(note: dict[str, str]) -> tuple[int, int, int, int]:
    return tuple(int(note[k]) for k in ("x1", "y1", "x2", "y2"))  # type: ignore[return-value]


def check_box_decision(
    note: dict[str, str],
    locator: tuple[float, ...],
    refined: tuple[int, int, int, int] | None,
    size: tuple[int, int],
) -> tuple[str, tuple[int, int, int, int]] | None:
    """Validate one decision against the owner rules; return (source, box) for added GT, None for ignore."""
    rid, decision = note["proposal_id"], note["box_decision"]
    longer = max(locator[2] - locator[0], locator[3] - locator[1])
    if decision not in DECISIONS or not note["note"].strip():
        raise RuntimeError(f"invalid box decision for {rid}")
    if decision == "IGNORE_REGION":
        if longer > SMALL_PX:
            raise RuntimeError(f"{rid}: ignore regions are only for locators <= {SMALL_PX} px")
        return None
    if decision == "HAND_DRAWN" and longer <= SMALL_PX:
        raise RuntimeError(f"{rid}: hand-drawn boxes are only for locators > {SMALL_PX} px")
    if decision in {"ACCEPT_REFINED", "ACCEPT_REFINED_ADJUSTED"} and refined is None:
        raise RuntimeError(f"{rid} accepted but re-fitting finds no box")
    if decision == "ACCEPT_REFINED":
        return "REFINED", refined  # type: ignore[return-value]
    box = _box(note)
    width, height = size
    if (
        not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height)
        or min(box[2] - box[0], box[3] - box[1]) < 8
    ):
        raise RuntimeError(f"{rid}: box outside the frame or degenerate")
    if decision == "ACCEPT_REFINED_ADJUSTED":
        inside = (
            box[0] >= refined[0]
            and box[1] >= refined[1]
            and box[2] <= refined[2]
            and box[3] <= refined[3]
        )  # type: ignore[index]
        if (
            not inside
            or max(abs(a - b) for a, b in zip(box, refined, strict=True)) > MAX_TIGHTEN_PX
        ):  # type: ignore[arg-type]
            raise RuntimeError(
                f"{rid}: adjustment may only tighten the re-fit by <= {MAX_TIGHTEN_PX} px"
            )
        return "REFINED_ADJUSTED", box
    return "HAND_DRAWN", box


def derive(repo_root: Path) -> dict[str, Any]:
    proposals = r1._read_csv(repo_root / r1.PROPOSALS)
    notes = r1._read_csv(repo_root / NOTES)
    if len(notes) != len(proposals):
        raise RuntimeError("box-review notes must cover every proposal")
    key_to_yolo = {
        r["derived_key"]: int(r["yolo_id"]) for r in r1._read_csv(repo_root / r1.CLASS_MAP)
    }
    images = {p.stem: p for p in ea.val_images(repo_root)}
    added, ignored = [], []
    for number, (prop, note) in enumerate(zip(proposals, notes, strict=True), start=1):
        if (
            note["proposal_id"] != f"R{number:03d}"
            or note["stem"] != prop["stem"]
            or note["derived_key"] != prop["derived_key"]
        ):
            raise RuntimeError(f"box-review note {number} does not match its proposal")
        with Image.open(images[prop["stem"]]) as source:
            image = source.convert("RGB")
        width, height = image.size
        x, y, w, h = (float(prop[k]) for k in ("x_center", "y_center", "width", "height"))
        locator = (
            (x - w / 2) * width,
            (y - h / 2) * height,
            (x + w / 2) * width,
            (y + h / 2) * height,
        )
        refined = (
            r1.refine_box(image, locator) if note["box_decision"].startswith("ACCEPT") else None
        )
        result = check_box_decision(note, locator, refined, (width, height))
        if result is None:
            mx, my = (
                r1.IGNORE_MARGIN * (locator[2] - locator[0]),
                r1.IGNORE_MARGIN * (locator[3] - locator[1]),
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
            continue
        source_kind, (bx1, by1, bx2, by2) = result
        added.append(
            {
                "proposal_id": note["proposal_id"],
                "stem": prop["stem"],
                "derived_key": prop["derived_key"],
                "yolo_id": key_to_yolo[prop["derived_key"]],
                "source": source_kind,
                "x1": bx1,
                "y1": by1,
                "x2": bx2,
                "y2": by2,
                "x_center": f"{(bx1 + bx2) / 2 / width:.6f}",
                "y_center": f"{(by1 + by2) / 2 / height:.6f}",
                "width": f"{(bx2 - bx1) / width:.6f}",
                "height": f"{(by2 - by1) / height:.6f}",
                "iou_vs_model_box": f"{r1._iou((bx1, by1, bx2, by2), locator):.4f}",
                "source_review_ids": prop["source_review_ids"],
            }
        )
    return {"added": added, "ignored": ignored, "images": images}


def derived_labels(repo_root: Path, added: list[dict[str, Any]]) -> dict[str, bytes]:
    return r1.derived_labels(repo_root, added)


# -------------------------------------------------------------------------------------- render


def render_atlas(
    added: list[dict[str, Any]], images: dict[Path, Path] | dict[str, Path]
) -> dict[Path, bytes]:
    font = ImageFont.load_default(size=16)
    tile = 360
    pages = {}
    for start in range(0, len(added), 16):
        sheet = Image.new("RGB", (4 * tile, 4 * (tile + 24)), "white")
        draw = ImageDraw.Draw(sheet)
        for k, row in enumerate(added[start : start + 16]):
            with Image.open(images[row["stem"]]) as source:
                image = source.convert("RGB")
            if row["stem"] in DARK_STEMS:
                image = ImageEnhance.Brightness(image).enhance(3.5)
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
            bright = " x3.5" if row["stem"] in DARK_STEMS else ""
            draw.text(
                (x + 3, y + tile + 3),
                f"{row['proposal_id']} {row['stem']} k{row['derived_key']}->y{row['yolo_id']} {row['source']}{bright}",
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
    by_source = Counter(r["source"] for r in added)
    by_key = Counter(r["derived_key"] for r in added)
    ious = sorted(float(r["iou_vs_model_box"]) for r in added)
    independent_fp = diag["false_positives_before_ignore"]
    return f"""# D1-VRL-R2 — derived validation labels (hand-drawn successor of D1-VRL-R1)

Status: `{STATUS}`
Boundary: `{BOUNDARY}`

Built from the owner re-decision in `{CORRECTION}` after the D1-VRL-R1 QA FAIL (H1). Raw, WP38-R1
R4, train and test labels are unchanged; the R4 validation labels are pinned by content
(`labels_sha256` `{R4_VAL_LABELS_SHA256[:8]}…`). Derived labels: `{OUT_LABELS}/` (git-ignored) and
ignore regions `{OUT_IGNORE}`, all hashed in the manifest. These labels are **not yet the
evaluation authority**.

## Boxes

- Added ground truth: **{len(added)}** — {", ".join(f"{k}: {v}" for k, v in sorted(by_source.items()))}.
  Keys: {", ".join(f"{k}: {v}" for k, v in sorted(by_key.items(), key=lambda kv: int(kv[0])))}; ids are YOLO ids through `{r1.CLASS_MAP}`.
- `HAND_DRAWN` boxes were drawn by eye on zoomed tick-grid crops that did not show the model box;
  each edge was snapped to the strongest luminance step only if that step lay within 1 px of the
  eye estimate (the dark 1823/1824 discs were not snapped). Eye estimates are kept in the notes.
- IoU of the added boxes with the model box: min {ious[0]:.2f}, median {ious[len(ious) // 2]:.2f}, max {ious[-1]:.2f}.
- **Geometry is guaranteed by the visual check, not by the colour fit** (QA L2): on existing human
  boxes the colour fit agrees only loosely. A re-evaluation must keep the IoU-0.5 matching rule.
- Ignore regions: **{len(ignored)}**, exactly the proposals whose locator is ≤ {SMALL_PX} px on the longer
  side (the builder refuses any other); locator expanded by {r1.IGNORE_MARGIN:.0%} per side; an unmatched
  prediction with ≥ {r1.IGNORE_IOA:.0%} of its area inside is not a false positive.

## Diagnostic at conf {ea.CONF} (re-scoring the D1-EA-R1 exported predictions)

| Labels | GT | FP before ignore | FP in ignore regions | FP | FP/image | Agnostic recall | Precision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R10 (WP38-R1 R4) | {base["ground_truth"]} | {base["false_positives"]} | — | {base["false_positives"]} | {base["fp_per_image"]:.3f} | {base["agnostic_recall"]:.4f} | {base["precision"]:.4f} |
| D1-VRL-R2 | {diag["ground_truth"]} | {independent_fp} | {diag["false_positives_in_ignore_regions"]} | {diag["false_positives"]} | {diag["fp_per_image"]:.3f} | {diag["agnostic_recall"]:.4f} | {diag["precision"]:.4f} |

- **Independent of the model geometry:** {independent_fp} FP ({independent_fp / diag["images"]:.3f} per image),
  using only the {len(added)} pixel-fitted or hand-drawn boxes.
- **Circular by construction:** the further {diag["false_positives_in_ignore_regions"]} FP are predictions inside
  ignore regions built from those same predictions' boxes; that drop restates the owner's ignore decision
  and is no evidence that the model is right on the small discs.

This is a diagnostic, not an evaluation: only predictions with confidence ≥ {ea.CONF} are used, so it
cannot select a threshold or compute mAP, and it changes no gate. The critical classes 7, 32 and 41 are
untouched. A D-05 decision needs a QA-passed evaluator run on the derived labels.

## Limits

- Only signs the model detected were audited (D1-VLA-R1); unlabelled signs it missed remain.
- The {len(ignored)} small pole discs are removed from both recall and FP on their frames.
- The 1823/1824 discs are drawn on a dark, partly occluded scene; their edges carry about ±2 px.
- Review pages: `{ATLAS_DIR}/` (git-ignored; frames 1823–1837 shown brightened 3.5×).
"""


def render(repo_root: Path = REPO_ROOT) -> dict[Path, bytes]:
    verify_pins(repo_root)
    derived = derive(repo_root)
    added, ignored = derived["added"], derived["ignored"]
    labels = derived_labels(repo_root, added)
    ignore_doc = {
        "rule": {
            "margin_per_side": r1.IGNORE_MARGIN,
            "min_prediction_area_inside": r1.IGNORE_IOA,
            "max_locator_side_px": SMALL_PX,
        },
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
        ea.frames_from_rows(r1._read_csv(repo_root / ea.PREDICTIONS_PATH), names, repo_root),
        ea.CONF,
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
    diag = r1.diagnostic(repo_root, added, ignored)
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
        "supersedes": "D1-VRL-R1",
        "summary": {
            "added_ground_truth": len(added),
            "added_by_source": dict(sorted(Counter(r["source"] for r in added).items())),
            "ignore_regions": len(ignored),
            "baseline": base,
            "diagnostic": diag,
        },
        "derived_label_dir": str(OUT_LABELS),
        "source_label_dir": str(r1.SOURCE_LABELS),
        "source_val_labels_sha256": R4_VAL_LABELS_SHA256,
        "derived_label_roster_sha256": r1.sha256_bytes(
            json.dumps(
                {n: r1.sha256_bytes(d) for n, d in sorted(labels.items())}, sort_keys=True
            ).encode()
        ),
        "pinned_sources": {str(p): d for p, d in sorted(PINNED.items(), key=lambda kv: str(kv[0]))},
        "pillow_version": importlib.metadata.version("pillow"),
        "artifacts": {
            str(p): r1.sha256_bytes(d)
            for p, d in sorted(artifacts.items(), key=lambda kv: str(kv[0]))
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
    targets = [ADDED_PATH, IGNORE_PATH, MANIFEST_PATH, REPORT_PATH, OUT_DIR, ATLAS_DIR]
    if any((repo_root / p).exists() for p in targets):
        raise RuntimeError("D1-VRL-R2 outputs already exist; the package is append-only")
    artifacts = render(repo_root)
    for path, data in artifacts.items():
        (repo_root / path).parent.mkdir(parents=True, exist_ok=True)
        (repo_root / path).write_bytes(data)
    return {
        "status": STATUS,
        "artifacts": len(artifacts),
        "summary": json.loads(artifacts[MANIFEST_PATH])["summary"],
    }


def stray_paths(repo_root: Path, expected: dict[Path, bytes]) -> list[str]:
    """Every file, link or empty directory under the derived root or atlas that is not an artifact (QA L3)."""
    stray = []
    for root in (OUT_DIR, ATLAS_DIR):
        folder = repo_root / root
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*")):
            relative = path.relative_to(repo_root)
            if path.is_symlink() or (path.is_file() and relative not in expected):
                stray.append(str(relative))
            elif path.is_dir() and not any(p.is_relative_to(relative) for p in expected):
                stray.append(str(relative))
    return stray


def verify(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        expected = render(repo_root)
        for path, data in expected.items():
            target = repo_root / path
            if not target.is_file() or target.is_symlink() or target.read_bytes() != data:
                errors.append(f"artifact differs: {path}")
        errors += [f"unexpected path: {p}" for p in stray_paths(repo_root, expected)]
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
