# ruff: noqa: E501
"""D1-VLA-R1: validation label-completeness audit of the D1-EA-R1 background false positives.

Scope (QA disposition of D1-EA-R1, `docs/review/d1_ea_r1_independent_qa_record.md`, and hypothesis
H2 of `docs/review/d1_ea_r1_hypothesis_correction_r1.md`):

- Candidates are the background false positives of the pinned D1-EA-R1 export whose best IoU with
  any ground-truth box is below 0.1 (stratum `NO_LABEL_NEARBY_IOU_LT_0_1`). The other strata, a
  prediction overlapping or inside a labelled box, are duplicates or box-extent issues (H1/H3),
  not missing labels.
- Every candidate carries one pinned visual-review decision
  (`docs/review/d1_vla_r1_review_notes.csv`): `UNLABELLED_IN_TAXONOMY` (with proposed class and
  confidence), `OUT_OF_TAXONOMY_UNLABELLED`, `OUT_OF_TAXONOMY_LABELLED_UNKNOWN`, `NOT_A_SIGN` or
  `UNCLEAR`.
- The package proposes candidate validation boxes for the owner. It does **not** relabel
  validation, change any gate or the R10 result, or authorize training. The label-adjusted metrics
  are diagnostic what-ifs only.

No model is loaded. `build` refuses to overwrite; `verify` regenerates every artifact and
byte-compares, and checks the pinned manifest anchor of D1-EA-R1.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from m1 import contract
from m1 import error_analysis_r1 as ea
from m1.metrics import Frame, iou_matrix, operating_point

REPO_ROOT = contract.REPO_ROOT
PACKAGE = "D1-VLA-R1"
STATUS = "D1_VLA_R1_AWAITING_INDEPENDENT_QA"
BOUNDARY = (
    "VALIDATION_LABEL_AUDIT_PROPOSAL_ONLY_NO_RELABEL_NO_GATE_CHANGE_NO_TRAINING_NO_SEALED_TEST"
)

NOTES = Path("docs/review/d1_vla_r1_review_notes.csv")
NOTES_SHA256 = "7fd81195e50992dcf45c0b4fc22499f3a0104a26a8d46e305a1153a4e8d26cec"
PINNED: dict[Path, str] = {
    ea.PREDICTIONS_PATH: "cb3cb05f0cadc7d2c3e077120d5b1311648247f74a9648e287da1c4be915f1dd",
    ea.MANIFEST_PATH: "d87f090e11d7acc547fb49eeb76935e2e0bcc743f3bc3fba56ab23a1cd8e07ab",
    Path("detector/m1/error_analysis_r1.py"): (
        "6268c3fec6695fa568ed2f7ac59e824b1aad9fc537cf7df729a7040dd38d8192"
    ),
    Path("docs/review/d1_ea_r1_independent_qa_record.md"): (
        "273c63563634d0ba002b9e5e0c9728e66e638477703715d33f2e80967262d65e"
    ),
    Path("docs/review/d1_ea_r1_hypothesis_correction_r1.md"): (
        "f0c63f99c92f2ac6f0de6bded72af8b41113a63327aa6f89bad8533e75e0d95c"
    ),
    NOTES: NOTES_SHA256,
}

DECISIONS = {
    "UNLABELLED_IN_TAXONOMY",
    "OUT_OF_TAXONOMY_UNLABELLED",
    "OUT_OF_TAXONOMY_LABELLED_UNKNOWN",
    "NOT_A_SIGN",
    "UNCLEAR",
}
CONFIDENCES = {"HIGH", "MEDIUM", "LOW"}
NO_LABEL = "NO_LABEL_NEARBY_IOU_LT_0_1"
DUPLICATE_IOU = 0.5

GENERATED = Path("docs/review/generated")
STRATA_PATH = GENERATED / "d1_vla_r1_background_fp_strata.csv"
DECISIONS_PATH = GENERATED / "d1_vla_r1_decisions.csv"
PROPOSED_PATH = GENERATED / "d1_vla_r1_proposed_val_labels.csv"
MANIFEST_PATH = GENERATED / "d1_vla_r1_manifest.json"
REPORT_PATH = Path("docs/review/d1_vla_r1_report.md")
ATLAS_DIR = Path("docs/review/assets/d1_vla_r1")

STRATA_FIELDS = [
    "stem",
    "pred_rank",
    "pred_class",
    "conf",
    "best_gt_iou",
    "max_containment",
    "stratum",
]
DECISION_FIELDS = [
    "review_id",
    "stem",
    "pred_rank",
    "pred_class",
    "conf",
    "x1",
    "y1",
    "x2",
    "y2",
    "decision",
    "proposed_class",
    "class_confidence",
    "duplicate_of",
    "note",
    "atlas_page",
    "atlas_slot",
]
PROPOSED_FIELDS = [
    "stem",
    "derived_key",
    "x_center",
    "y_center",
    "width",
    "height",
    "class_confidence",
    "source_review_ids",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verify_pins(repo_root: Path = REPO_ROOT) -> None:
    for relative, expected in PINNED.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or ea.sha256_file(path) != expected:
            raise RuntimeError(f"pinned D1-VLA-R1 source differs: {relative}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_frames(repo_root: Path) -> tuple[list[dict[str, str]], dict[str, Frame], list[str]]:
    names = ea.class_names(repo_root)
    rows = _read_csv(repo_root / ea.PREDICTIONS_PATH)
    frames = {f.stem: f for f in ea.frames_from_rows(rows, names, repo_root)}
    return rows, frames, names


def stratify(rows: list[dict[str, str]], frames: dict[str, Frame]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        if row["disposition"] != "BACKGROUND":
            continue
        frame = frames[row["stem"]]
        box = np.asarray([[float(row[k]) for k in ("x1", "y1", "x2", "y2")]])
        best = float(iou_matrix(box, frame.gt_boxes).max()) if len(frame.gt_boxes) else 0.0
        area = (box[0, 2] - box[0, 0]) * (box[0, 3] - box[0, 1])
        contain = 0.0
        for gt in frame.gt_boxes:
            w = max(0.0, min(box[0, 2], gt[2]) - max(box[0, 0], gt[0]))
            h = max(0.0, min(box[0, 3], gt[3]) - max(box[0, 1], gt[1]))
            contain = max(contain, w * h / area if area > 0 else 0.0)
        if best >= 0.5:
            stratum = "OVERLAPS_LABELLED_IOU_GE_0_5"
        elif contain >= 0.6:
            stratum = "INSIDE_LABELLED_BOX"
        elif best >= 0.1:
            stratum = "PARTIAL_OVERLAP_0_1_TO_0_5"
        else:
            stratum = NO_LABEL
        out.append(
            {
                "stem": row["stem"],
                "pred_rank": row["pred_rank"],
                "pred_class": row["pred_class"],
                "conf": row["conf"],
                "best_gt_iou": f"{best:.4f}",
                "max_containment": f"{contain:.4f}",
                "stratum": stratum,
            }
        )
    return out


def load_notes(
    repo_root: Path, candidates: list[dict[str, str]], names: list[str]
) -> list[dict[str, str]]:
    notes = _read_csv(repo_root / NOTES)
    keys = [(c["stem"], c["pred_rank"]) for c in candidates]
    if [(n["stem"], n["pred_rank"]) for n in notes] != keys:
        raise RuntimeError(
            "review notes must cover every no-label candidate exactly once, in order"
        )
    for note, cand in zip(notes, candidates, strict=True):
        if note["pred_class"] != cand["pred_class"]:
            raise RuntimeError(f"review note pred_class differs for {note['stem']}")
        if note["decision"] not in DECISIONS or not note["note"].strip():
            raise RuntimeError(f"invalid review decision for {note['stem']}")
        if note["decision"] == "UNLABELLED_IN_TAXONOMY":
            if note["proposed_class"] not in names or note["class_confidence"] not in CONFIDENCES:
                raise RuntimeError(
                    f"unlabelled sign needs a known class and confidence: {note['stem']}"
                )
        elif note["proposed_class"] or note["class_confidence"]:
            raise RuntimeError(f"only in-taxonomy decisions carry a class: {note['stem']}")
    return notes


def decision_rows(
    candidates: list[dict[str, str]], notes: list[dict[str, str]], rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    by_key = {(r["stem"], r["pred_rank"]): r for r in rows}
    out: list[dict[str, Any]] = []
    for number, (cand, note) in enumerate(zip(candidates, notes, strict=True), start=1):
        pred = by_key[(cand["stem"], cand["pred_rank"])]
        out.append(
            {
                "review_id": f"V{number:03d}",
                "stem": cand["stem"],
                "pred_rank": cand["pred_rank"],
                "pred_class": cand["pred_class"],
                "conf": pred["conf"],
                **{k: pred[k] for k in ("x1", "y1", "x2", "y2")},
                "decision": note["decision"],
                "proposed_class": note["proposed_class"],
                "class_confidence": note["class_confidence"],
                "duplicate_of": "",
                "note": note["note"],
                "atlas_page": (number - 1) // 12 + 1,
                "atlas_slot": (number - 1) % 12 + 1,
            }
        )
    # A lower-scored in-taxonomy candidate on the same physical sign is a duplicate, not a new box.
    kept: dict[str, list[dict[str, Any]]] = {}
    for row in sorted(out, key=lambda r: (r["stem"], -float(r["conf"]))):
        if row["decision"] != "UNLABELLED_IN_TAXONOMY":
            continue
        box = np.asarray([[float(row[k]) for k in ("x1", "y1", "x2", "y2")]])
        for other in kept.get(row["stem"], []):
            other_box = np.asarray([[float(other[k]) for k in ("x1", "y1", "x2", "y2")]])
            if iou_matrix(box, other_box)[0, 0] >= DUPLICATE_IOU:
                row["duplicate_of"] = other["review_id"]
                break
        else:
            kept.setdefault(row["stem"], []).append(row)
    return out


def proposed_labels(
    decisions: list[dict[str, Any]], frames: dict[str, Frame]
) -> list[dict[str, Any]]:
    """Unique in-taxonomy boxes with HIGH/MEDIUM class confidence, in YOLO normalized xywh."""
    dups: dict[str, list[str]] = {}
    for row in decisions:
        if row["duplicate_of"]:
            dups.setdefault(row["duplicate_of"], []).append(row["review_id"])
    out = []
    for row in decisions:
        if row["decision"] != "UNLABELLED_IN_TAXONOMY" or row["duplicate_of"]:
            continue
        if row["class_confidence"] not in {"HIGH", "MEDIUM"}:
            continue
        frame = frames[row["stem"]]
        w, h = frame.image_width, frame.image_height
        x1, y1, x2, y2 = (float(row[k]) for k in ("x1", "y1", "x2", "y2"))
        out.append(
            {
                "stem": row["stem"],
                "derived_key": row["proposed_class"],
                "x_center": f"{(x1 + x2) / 2 / w:.6f}",
                "y_center": f"{(y1 + y2) / 2 / h:.6f}",
                "width": f"{(x2 - x1) / w:.6f}",
                "height": f"{(y2 - y1) / h:.6f}",
                "class_confidence": row["class_confidence"],
                "source_review_ids": " ".join([row["review_id"], *dups.get(row["review_id"], [])]),
            }
        )
    return out


def what_if(
    frames: dict[str, Frame],
    decisions: list[dict[str, Any]],
    names: list[str],
    *,
    include_low: bool,
) -> dict[str, Any]:
    """Diagnostic only: operating point if the unique in-taxonomy candidates were labelled."""
    extra: dict[str, list[tuple[int, list[float]]]] = {}
    for row in decisions:
        if row["decision"] != "UNLABELLED_IN_TAXONOMY" or row["duplicate_of"]:
            continue
        if row["class_confidence"] == "LOW" and not include_low:
            continue
        extra.setdefault(row["stem"], []).append(
            (names.index(row["proposed_class"]), [float(row[k]) for k in ("x1", "y1", "x2", "y2")])
        )
    adjusted = []
    for frame in frames.values():
        add = extra.get(frame.stem, [])
        adjusted.append(
            Frame(
                frame.stem,
                frame.group_id,
                np.vstack([frame.gt_boxes, np.asarray([b for _c, b in add]).reshape(-1, 4)]),
                np.concatenate([frame.gt_classes, np.asarray([c for c, _b in add], dtype=int)]),
                frame.pred_boxes,
                frame.pred_classes,
                frame.pred_scores,
                frame.image_width,
                frame.image_height,
            )
        )
    point = operating_point(adjusted, ea.CONF)
    return {
        "added_boxes": sum(len(v) for v in extra.values()),
        "ground_truth": point.ground_truth,
        "false_positives": point.false_positives,
        "fp_per_image": round(point.fp_per_image, 6),
        "agnostic_recall": round(point.agnostic_recall, 6),
        "precision": round(point.precision, 6),
    }


def render_atlas(decisions: list[dict[str, Any]], repo_root: Path) -> dict[Path, bytes]:
    images = {p.stem: p for p in ea.val_images(repo_root)}
    font = ImageFont.load_default(size=18)
    tile = 420
    pages: dict[Path, bytes] = {}
    for start in range(0, len(decisions), 12):
        sheet = Image.new("RGB", (4 * tile, 3 * (tile + 28)), "white")
        draw = ImageDraw.Draw(sheet)
        for k, row in enumerate(decisions[start : start + 12]):
            with Image.open(images[row["stem"]]) as source:
                image = source.convert("RGB")
            w, h = image.size
            b = [float(row[q]) for q in ("x1", "y1", "x2", "y2")]
            side = max(160.0, 6.0 * max(b[2] - b[0], b[3] - b[1]))
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            left = max(0.0, min(cx - side / 2, w - side))
            top = max(0.0, min(cy - side / 2, h - side))
            crop = image.crop(
                (int(left), int(top), int(min(w, left + side)), int(min(h, top + side)))
            )
            scale = tile / max(crop.size)
            crop = crop.resize((int(crop.width * scale), int(crop.height * scale)))
            ImageDraw.Draw(crop).rectangle(
                [
                    (b[0] - left) * scale,
                    (b[1] - top) * scale,
                    (b[2] - left) * scale,
                    (b[3] - top) * scale,
                ],
                outline="red",
                width=3,
            )
            x, y = (k % 4) * tile, (k // 4) * (tile + 28)
            sheet.paste(crop, (x, y))
            label = row["proposed_class"] or row["decision"].split("_")[0]
            draw.text(
                (x + 4, y + tile + 4),
                f"{row['review_id']} {row['stem']} p{row['pred_class']} -> {label}",
                fill="black",
                font=font,
            )
        buffer = io.BytesIO()
        sheet.save(buffer, format="JPEG", quality=88)
        pages[ATLAS_DIR / f"review_page_{start // 12 + 1:02d}.jpg"] = buffer.getvalue()
    return pages


def render_report(
    strata: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    proposed: list[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    s_counts = Counter(r["stratum"] for r in strata)
    d_counts = Counter(r["decision"] for r in decisions)
    unique = [
        r for r in decisions if r["decision"] == "UNLABELLED_IN_TAXONOMY" and not r["duplicate_of"]
    ]
    by_class = Counter((r["proposed_class"], r["class_confidence"]) for r in unique)
    base, med, low = summary["baseline"], summary["what_if_high_medium"], summary["what_if_all"]
    lines = [
        "# D1-VLA-R1 — validation label-completeness audit\n",
        f"Status: `{STATUS}`",
        f"Boundary: `{BOUNDARY}`\n",
        "Audits the D1-EA-R1 background false positives (manifest `d87f090e…`) at conf 0.20.",
        "Proposal only: it does not relabel validation, change any gate or the R10 result, or",
        "authorize training. Validation remains diagnosis-only; the sealed test stays closed.\n",
        "## Strata of the 214 background false positives\n",
        "| Stratum | Count |",
        "| --- | ---: |",
        *[f"| `{k}` | {v} |" for k, v in sorted(s_counts.items())],
        f"\nOnly `{NO_LABEL}` candidates can be missing labels; the others are H1 duplicates or H3",
        "box-extent issues and are not reviewed here.\n",
        f"## Visual-review decisions ({len(decisions)} candidates)\n",
        "| Decision | Count |",
        "| --- | ---: |",
        *[f"| `{k}` | {v} |" for k, v in sorted(d_counts.items())],
        f"\n{len(unique)} unique in-taxonomy unlabelled signs after merging"
        f" {sum(1 for r in decisions if r['duplicate_of'])} same-sign duplicates.\n",
        "| Proposed class | Confidence | Unique boxes |",
        "| --- | --- | ---: |",
        *[
            f"| {c} | {conf} | {n} |"
            for (c, conf), n in sorted(by_class.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
        f"\n`{PROPOSED_PATH}` lists the {len(proposed)} HIGH/MEDIUM boxes as YOLO-normalized proposals.\n",
        "## Diagnostic what-if (not a result, not a gate)\n",
        "| Ground truth | Added boxes | FP | FP/image | Agnostic recall | Precision |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        f"| R10 labels | 0 | {base['false_positives']} | {base['fp_per_image']:.3f} | {base['agnostic_recall']:.4f} | {base['precision']:.4f} |",
        f"| + HIGH/MEDIUM proposals | {med['added_boxes']} | {med['false_positives']} | {med['fp_per_image']:.3f} | {med['agnostic_recall']:.4f} | {med['precision']:.4f} |",
        f"| + all proposals incl. LOW | {low['added_boxes']} | {low['false_positives']} | {low['fp_per_image']:.3f} | {low['agnostic_recall']:.4f} | {low['precision']:.4f} |",
        "\nRecall changes because added labels are new ground truth that the model must also match.",
        "These numbers show how much of FP/image is label incompleteness. They must not replace R10",
        "or be used for gating until the owner approves a derived validation relabel and it passes QA.\n",
        "## Limits\n",
        "- Only signs the model detected are audited; unlabelled signs the model missed are not found.",
        "- Proposed boxes are the model's boxes, not hand-drawn; a relabel must redraw them.",
        "- Classes 10/23/39/41 on the 1208–1229 and 1342–1357 poles are read partly by consistency",
        "  with sharper frames of the same pole (MEDIUM); the 3.5t truck disc needs its QCVN variant.",
        f"- Review pages: `{ATLAS_DIR}/` (git-ignored, DATASET01 pixels).",
    ]
    return "\n".join(lines) + "\n"


def render(repo_root: Path = REPO_ROOT) -> dict[Path, bytes]:
    verify_pins(repo_root)
    rows, frames, names = load_frames(repo_root)
    strata = stratify(rows, frames)
    candidates = [s for s in strata if s["stratum"] == NO_LABEL]
    notes = load_notes(repo_root, candidates, names)
    decisions = decision_rows(candidates, notes, rows)
    proposed = proposed_labels(decisions, frames)
    base = operating_point(list(frames.values()), ea.CONF)
    summary = {
        "background_false_positives": len(strata),
        "no_label_candidates": len(candidates),
        "decisions": dict(sorted(Counter(r["decision"] for r in decisions).items())),
        "unique_in_taxonomy_unlabelled": sum(
            1
            for r in decisions
            if r["decision"] == "UNLABELLED_IN_TAXONOMY" and not r["duplicate_of"]
        ),
        "proposed_boxes": len(proposed),
        "baseline": {
            "ground_truth": base.ground_truth,
            "false_positives": base.false_positives,
            "fp_per_image": round(base.fp_per_image, 6),
            "agnostic_recall": round(base.agnostic_recall, 6),
            "precision": round(base.precision, 6),
        },
        "what_if_high_medium": what_if(frames, decisions, names, include_low=False),
        "what_if_all": what_if(frames, decisions, names, include_low=True),
    }
    if base.false_positives != 214 or base.ground_truth != 560:
        raise RuntimeError("D1-EA-R1 baseline differs from R10 (214 FP / 560 GT)")
    artifacts: dict[Path, bytes] = {
        STRATA_PATH: ea.csv_bytes(STRATA_FIELDS, strata),
        DECISIONS_PATH: ea.csv_bytes(DECISION_FIELDS, decisions),
        PROPOSED_PATH: ea.csv_bytes(PROPOSED_FIELDS, proposed),
        **render_atlas(decisions, repo_root),
    }
    artifacts[REPORT_PATH] = render_report(strata, decisions, proposed, summary).encode("utf-8")
    manifest = {
        "package": PACKAGE,
        "status": STATUS,
        "boundary": BOUNDARY,
        "summary": summary,
        "pinned_sources": {str(p): d for p, d in sorted(PINNED.items(), key=lambda kv: str(kv[0]))},
        "pillow_version": importlib.metadata.version("pillow"),
        "artifacts": {
            str(p): sha256_bytes(d) for p, d in sorted(artifacts.items(), key=lambda kv: str(kv[0]))
        },
        "validation_relabelled": False,
        "gates_changed": False,
        "training_authorized": False,
        "test_included": False,
        "sealed_test_accessed": False,
    }
    artifacts[MANIFEST_PATH] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    return artifacts


def build(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    targets = [STRATA_PATH, DECISIONS_PATH, PROPOSED_PATH, MANIFEST_PATH, REPORT_PATH]
    if any((repo_root / p).exists() for p in targets) or (repo_root / ATLAS_DIR).exists():
        raise RuntimeError("D1-VLA-R1 outputs already exist; the package is append-only")
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
        atlas = repo_root / ATLAS_DIR
        if atlas.is_dir():
            errors += [
                f"unexpected atlas file: {p.name}"
                for p in atlas.iterdir()
                if ATLAS_DIR / p.name not in expected
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
