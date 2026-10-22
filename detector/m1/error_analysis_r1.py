"""D1-EA-R1: validation-only prediction export and error atlas for the QA-passed R10 result.

Implements the evidence package required by
`docs/review/d1_corrected_val_r10_error_analysis_and_improvement_packet_r1.md`:

1. export every prediction retained at the locked diagnostic point (conf 0.20, NMS IoU 0.70) with
   its matched ground truth or background disposition, plus every unmatched ground-truth box;
2. render contact sheets for all background false positives, all ground-truth errors of the
   critical classes 7/32/41, and the 46→10 and 8→12 confusion pairs;
3. pin the R10 report, the weights, the corrected-validation data authority and the class map.

`build` runs inference once on the R10 reference device (MPS) through the same loader that R10
used, and refuses to write anything unless the regenerated operating point, confusion matrix and
class-aware hits equal the pinned R10 report exactly. `verify` needs no model: it re-derives every
count from the exported prediction CSV and the label files, then regenerates the CSVs, atlas pages,
report and manifest and byte-compares them.

The package is diagnosis-only. It never reads the sealed test, and no validation image, crop or
prediction may enter training.
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
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from m1 import contract
from m1.metrics import Frame, _greedy_pairs, confusion_matrix, iou_matrix, operating_point

REPO_ROOT = contract.REPO_ROOT
PACKAGE = "D1-EA-R1"
STATUS = "D1_EA_R1_AWAITING_INDEPENDENT_QA"
BOUNDARY = "VALIDATION_ONLY_DIAGNOSIS_NO_TRAINING_NO_SEALED_TEST_NO_VAL_PIXELS_IN_TRAIN"

RUN = "D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2"
RUN_DIR = Path("results/experiments") / RUN
WEIGHTS = RUN_DIR / "weights/best.pt"
R10_REPORT = RUN_DIR / "eval_val_wp38_r1_r4_r10.json"
R10_MODULE = Path("detector/m1/corrected_val_r10.py")
R1_MODULE = Path("detector/m1/corrected_val_r1.py")
METRICS_MODULE = Path("detector/m1/metrics.py")
CLASS_MAP = Path("docs/review/generated/m1_yolo_classes.csv")
EXPORT_DIR = Path("data/processed/m1_yolo_wp38_r1_integration_r4")

PINNED: dict[Path, str] = {
    R10_REPORT: "b33e247038c237d059207f75ad8ff33e0b5d6d00e4380826cd35ae85aefa02d5",
    WEIGHTS: "5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633",
    R10_MODULE: "5897e951244a5e8761bda7202779fe30acb0d5da085686d49c96a04f69e5dfd3",
    R1_MODULE: "0e56949d4a8e01b01a3de509f982ecbb4d0fd4ec1b44ef51975b47621289b8e5",
    METRICS_MODULE: "d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f",
    CLASS_MAP: "7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242",
    Path("docs/review/d1_corrected_val_r10_result_independent_qa_record.md"): (
        "9940b31c344e9e683d0bd3d6ddc25b8a31053bbeb83398801637be08df2d06a2"
    ),
    Path("docs/review/d1_corrected_val_r10_error_analysis_and_improvement_packet_r1.md"): (
        "9ec8dd0d9e2866ef098ca3afada624ea5562837531f9b077981c45940ed0f78f"
    ),
    Path("docs/review/d1_corrected_val_r10_error_analysis_r1_independent_qa_record.md"): (
        "c4b8fa62bd158ba4f300b28cf14bb9c4d8f1147dbf410e4a57582f70fb565942"
    ),
}

CONF = 0.20
NMS_IOU = 0.70
IMGSZ = 1280
DEVICE = "mps"
CRITICAL = ("7", "32", "41")
PAIRS = (("46", "10"), ("8", "12"))

GENERATED = Path("docs/review/generated")
PREDICTIONS_PATH = GENERATED / "d1_ea_r1_predictions.csv"
MISSED_PATH = GENERATED / "d1_ea_r1_missed_gt.csv"
ATLAS_INDEX_PATH = GENERATED / "d1_ea_r1_atlas_index.csv"
MANIFEST_PATH = GENERATED / "d1_ea_r1_manifest.json"
REPORT_PATH = Path("docs/review/d1_ea_r1_evidence_report.md")
ATLAS_DIR = Path("docs/review/assets/d1_ea_r1")

PREDICTION_FIELDS = [
    "stem",
    "group_id",
    "image_width",
    "image_height",
    "pred_rank",
    "pred_class",
    "conf",
    "x1",
    "y1",
    "x2",
    "y2",
    "disposition",
    "gt_index",
    "gt_class",
    "iou",
]
MISSED_FIELDS = [
    "stem",
    "group_id",
    "gt_index",
    "gt_class",
    "x1",
    "y1",
    "x2",
    "y2",
    "best_retained_iou",
    "best_retained_class",
]
INDEX_FIELDS = ["category", "page", "slot", "stem", "pred_rank", "gt_index", "caption"]

TILE = 256
CAPTION = 30
COLUMNS = 6
ROWS = 5
PER_PAGE = COLUMNS * ROWS


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_pins(repo_root: Path = REPO_ROOT) -> None:
    for relative, expected in PINNED.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned D1-EA-R1 source differs: {relative}")


def load_r10_report(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    report = json.loads((repo_root / R10_REPORT).read_text(encoding="utf-8"))
    if report.get("test_included") is not False or report.get("sealed_test_accessed") is not False:
        raise RuntimeError("R10 report is not validation-only")
    if report.get("split") != "val" or report.get("device") != DEVICE:
        raise RuntimeError("R10 report split/device differs")
    if report["operating_point"]["conf"] != CONF or report.get("nms_iou") != NMS_IOU:
        raise RuntimeError("R10 operating point differs from the locked diagnostic point")
    if report["weights"]["sha256"] != PINNED[WEIGHTS]:
        raise RuntimeError("R10 report does not bind the pinned weights")
    return report


def class_names(repo_root: Path = REPO_ROOT) -> list[str]:
    """Derived keys indexed by YOLO id."""
    with (repo_root / CLASS_MAP).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    names = [""] * len(rows)
    for row in rows:
        names[int(row["yolo_id"])] = row["derived_key"]
    if "" in names:
        raise RuntimeError("class map is not a dense YOLO id range")
    return names


# --------------------------------------------------------------------------------------------
# Ground truth from the pinned export (no model needed)


def _label_rows(repo_root: Path, stem: str) -> list[list[str]]:
    path = repo_root / EXPORT_DIR / "labels/val" / f"{stem}.txt"
    return [line.split() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _xywh_to_xyxy(rows: np.ndarray, width: int, height: int) -> np.ndarray:
    values = np.asarray(rows, dtype=float).reshape(-1, 4)
    if not len(values):
        return np.zeros((0, 4), dtype=float)
    return np.column_stack(
        [
            (values[:, 0] - values[:, 2] / 2) * width,
            (values[:, 1] - values[:, 3] / 2) * height,
            (values[:, 0] + values[:, 2] / 2) * width,
            (values[:, 1] + values[:, 3] / 2) * height,
        ]
    )


def val_images(repo_root: Path = REPO_ROOT) -> list[Path]:
    image_dir = repo_root / EXPORT_DIR / "images/val"
    images = sorted(p for p in image_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if len(images) != 376:
        raise RuntimeError("validation image roster differs from 376 frames")
    return images


# --------------------------------------------------------------------------------------------
# Prediction table <-> frames


def _repr(value: float) -> str:
    return repr(float(value))


def prediction_rows(frames: Sequence[Frame], names: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for frame in frames:
        pairs, _missed, false_predictions = _greedy_pairs(frame, CONF)
        paired = {pred: gt for gt, pred in pairs}
        keep = np.flatnonzero(frame.pred_scores >= CONF)
        keep = keep[np.argsort(-frame.pred_scores[keep], kind="stable")]
        ious = iou_matrix(frame.pred_boxes, frame.gt_boxes)
        background = set(false_predictions)
        for rank, index in enumerate(keep.tolist()):
            box = frame.pred_boxes[index]
            row = {
                "stem": frame.stem,
                "group_id": frame.group_id,
                "image_width": frame.image_width,
                "image_height": frame.image_height,
                "pred_rank": rank,
                "pred_class": names[int(frame.pred_classes[index])],
                "conf": _repr(frame.pred_scores[index]),
                "x1": _repr(box[0]),
                "y1": _repr(box[1]),
                "x2": _repr(box[2]),
                "y2": _repr(box[3]),
            }
            if index in paired:
                gt = paired[index]
                row.update(
                    disposition="PAIRED",
                    gt_index=gt,
                    gt_class=names[int(frame.gt_classes[gt])],
                    iou=f"{ious[index, gt]:.4f}",
                )
            elif index in background:
                row.update(disposition="BACKGROUND", gt_index="", gt_class="", iou="")
            else:  # pragma: no cover - _greedy_pairs partitions the retained predictions
                raise RuntimeError("prediction neither paired nor background")
            rows.append(row)
    return rows


def frames_from_rows(
    rows: Iterable[dict[str, str]], names: list[str], repo_root: Path = REPO_ROOT
) -> list[Frame]:
    """Rebuild retained-prediction frames from the exported table and the label files."""
    index = {name: number for number, name in enumerate(names)}
    by_stem: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_stem.setdefault(row["stem"], []).append(row)
    groups = contract.group_of()
    frames: list[Frame] = []
    for path in val_images(repo_root):
        stem = path.stem
        with Image.open(path) as image:
            width, height = image.size
        labels = _label_rows(repo_root, stem)
        gt = np.asarray([[float(v) for v in r[1:]] for r in labels]).reshape(-1, 4)
        preds = sorted(by_stem.get(stem, []), key=lambda r: int(r["pred_rank"]))
        for row in preds:
            if int(row["image_width"]) != width or int(row["image_height"]) != height:
                raise RuntimeError(f"prediction table image size differs for {stem}")
        frames.append(
            Frame(
                stem=stem,
                group_id=groups[stem],
                gt_boxes=_xywh_to_xyxy(gt, width, height),
                gt_classes=np.asarray([int(r[0]) for r in labels], dtype=int),
                pred_boxes=np.asarray(
                    [[float(r[k]) for k in ("x1", "y1", "x2", "y2")] for r in preds], dtype=float
                ).reshape(-1, 4),
                pred_classes=np.asarray([index[r["pred_class"]] for r in preds], dtype=int),
                pred_scores=np.asarray([float(r["conf"]) for r in preds], dtype=float),
                image_width=width,
                image_height=height,
            )
        )
    unknown_stems = set(by_stem) - {frame.stem for frame in frames}
    if unknown_stems:
        raise RuntimeError(f"prediction table names unknown stems: {sorted(unknown_stems)[:3]}")
    return frames


def missed_rows(frames: Sequence[Frame], names: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for frame in frames:
        _pairs, missed, _fp = _greedy_pairs(frame, CONF)
        keep = np.flatnonzero(frame.pred_scores >= CONF)
        ious = iou_matrix(frame.gt_boxes, frame.pred_boxes[keep])
        for gt in missed:
            box = frame.gt_boxes[gt]
            if len(keep):
                best = int(np.argmax(ious[gt]))
                best_iou = f"{ious[gt, best]:.4f}"
                best_class = names[int(frame.pred_classes[keep][best])]
            else:
                best_iou, best_class = "0.0000", ""
            rows.append(
                {
                    "stem": frame.stem,
                    "group_id": frame.group_id,
                    "gt_index": gt,
                    "gt_class": names[int(frame.gt_classes[gt])],
                    "x1": f"{box[0]:.2f}",
                    "y1": f"{box[1]:.2f}",
                    "x2": f"{box[2]:.2f}",
                    "y2": f"{box[3]:.2f}",
                    "best_retained_iou": best_iou,
                    "best_retained_class": best_class,
                }
            )
    return rows


# --------------------------------------------------------------------------------------------
# Reproduction of the pinned R10 report


def reproduction_check(
    frames: Sequence[Frame], report: dict[str, Any], names: list[str]
) -> dict[str, Any]:
    """Refuse unless the frames reproduce the R10 operating point, confusion and class hits."""
    point = operating_point(frames, CONF)
    expected = report["operating_point"]
    observed = {
        "images": point.images,
        "ground_truth": point.ground_truth,
        "true_positives": point.true_positives,
        "false_positives": point.false_positives,
    }
    errors = [
        f"{key}: {observed[key]} != {expected[key]}"
        for key in observed
        if observed[key] != expected[key]
    ]
    matrix = confusion_matrix(frames, CONF, len(names))
    if matrix != report["confusion_matrix"]["rows_gt_cols_pred"]:
        errors.append("confusion matrix differs from R10")
    if report["confusion_matrix"]["labels"] != [*names, "BACKGROUND"]:
        errors.append("confusion labels differ from the class map")
    for key, gate in report["gates"]["classes"].items():
        cls = names.index(key)
        hits = point.per_class_hits.get(cls, 0)
        if hits != gate["hits"] or point.per_class_support.get(cls, 0) != gate["support"]:
            errors.append(f"class {key} hits/support differ from R10")
    if errors:
        raise RuntimeError("D1-EA-R1 does not reproduce R10: " + "; ".join(errors[:8]))
    background = sum(matrix[len(names)][: len(names)])
    missed = sum(row[len(names)] for row in matrix[: len(names)])
    return {
        "images": point.images,
        "ground_truth": point.ground_truth,
        "retained_predictions": point.true_positives + point.false_positives,
        "paired_predictions": point.true_positives,
        "background_false_positives": background,
        "unmatched_ground_truth": missed,
        "confusion_matrix_sha256": sha256_bytes(json.dumps(matrix).encode()),
        "reproduces_r10": True,
    }


# --------------------------------------------------------------------------------------------
# Atlas


@dataclass(frozen=True)
class Item:
    category: str
    stem: str
    pred_rank: str
    gt_index: str
    pred_box: tuple[float, float, float, float] | None
    gt_box: tuple[float, float, float, float] | None
    caption: str


def atlas_items(
    frames: Sequence[Frame], pred_rows: list[dict[str, Any]], names: list[str]
) -> list[Item]:
    gt_lookup = {
        (f.stem, i): tuple(f.gt_boxes[i].tolist()) for f in frames for i in range(len(f.gt_boxes))
    }
    gt_class = {
        (f.stem, i): names[int(f.gt_classes[i])] for f in frames for i in range(len(f.gt_boxes))
    }
    items: list[Item] = []

    def pbox(row: dict[str, Any]) -> tuple[float, float, float, float]:
        return tuple(float(row[k]) for k in ("x1", "y1", "x2", "y2"))  # type: ignore[return-value]

    background = sorted(
        (r for r in pred_rows if r["disposition"] == "BACKGROUND"),
        key=lambda r: (names.index(r["pred_class"]), r["stem"], int(r["pred_rank"])),
    )
    for row in background:
        items.append(
            Item(
                "background_fp",
                row["stem"],
                str(row["pred_rank"]),
                "",
                pbox(row),
                None,
                f"{row['stem']} p{row['pred_class']} {float(row['conf']):.2f}",
            )
        )
    paired = [r for r in pred_rows if r["disposition"] == "PAIRED"]
    for cls in CRITICAL:
        wrong = sorted(
            (r for r in paired if r["gt_class"] == cls and r["pred_class"] != cls),
            key=lambda r: (r["stem"], int(r["gt_index"])),
        )
        for row in wrong:
            key = (row["stem"], int(row["gt_index"]))
            items.append(
                Item(
                    f"critical_{cls}",
                    row["stem"],
                    str(row["pred_rank"]),
                    str(row["gt_index"]),
                    pbox(row),
                    gt_lookup[key],
                    f"{row['stem']} g{cls}->p{row['pred_class']}",
                )
            )
        for frame in frames:
            _pairs, missed, _fp = _greedy_pairs(frame, CONF)
            for gt in missed:
                if gt_class[(frame.stem, gt)] == cls:
                    items.append(
                        Item(
                            f"critical_{cls}",
                            frame.stem,
                            "",
                            str(gt),
                            None,
                            gt_lookup[(frame.stem, gt)],
                            f"{frame.stem} g{cls} missed",
                        )
                    )
    for gt_cls, pred_cls in PAIRS:
        rows = sorted(
            (r for r in paired if r["gt_class"] == gt_cls and r["pred_class"] == pred_cls),
            key=lambda r: (r["stem"], int(r["gt_index"])),
        )
        for row in rows:
            key = (row["stem"], int(row["gt_index"]))
            items.append(
                Item(
                    f"pair_{gt_cls}_to_{pred_cls}",
                    row["stem"],
                    str(row["pred_rank"]),
                    str(row["gt_index"]),
                    pbox(row),
                    gt_lookup[key],
                    f"{row['stem']} g{gt_cls}->p{pred_cls} {float(row['conf']):.2f}",
                )
            )
    return items


def _tile(image: Image.Image, item: Item, font: ImageFont.ImageFont) -> Image.Image:
    boxes = [b for b in (item.pred_box, item.gt_box) if b is not None]
    x1 = min(b[0] for b in boxes)
    y1 = min(b[1] for b in boxes)
    x2 = max(b[2] for b in boxes)
    y2 = max(b[3] for b in boxes)
    side = max(96.0, 4.0 * max(x2 - x1, y2 - y1))
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    left = int(round(min(max(cx - side / 2, 0), max(image.width - side, 0))))
    top = int(round(min(max(cy - side / 2, 0), max(image.height - side, 0))))
    right = int(round(min(left + side, image.width)))
    bottom = int(round(min(top + side, image.height)))
    crop = image.crop((left, top, right, bottom))
    scale = TILE / max(crop.width, crop.height)
    crop = crop.resize(
        (max(1, int(round(crop.width * scale))), max(1, int(round(crop.height * scale)))),
        Image.BILINEAR,
    )
    tile = Image.new("RGB", (TILE, TILE + CAPTION), "white")
    tile.paste(crop, (0, 0))
    draw = ImageDraw.Draw(tile)

    def rect(box: tuple[float, float, float, float], colour: str) -> None:
        draw.rectangle(
            [
                (box[0] - left) * scale,
                (box[1] - top) * scale,
                (box[2] - left) * scale,
                (box[3] - top) * scale,
            ],
            outline=colour,
            width=2,
        )

    if item.gt_box is not None:
        rect(item.gt_box, "#00c000")
    if item.pred_box is not None:
        rect(item.pred_box, "#ff0000")
    draw.text((4, TILE + 8), item.caption, fill="black", font=font)
    return tile


def render_atlas(
    items: list[Item], repo_root: Path = REPO_ROOT
) -> tuple[dict[Path, bytes], list[dict[str, Any]]]:
    font = ImageFont.load_default()
    image_dir = repo_root / EXPORT_DIR / "images/val"
    suffix = {p.stem: p for p in val_images(repo_root)}
    categories: dict[str, list[Item]] = {}
    for item in items:
        categories.setdefault(item.category, []).append(item)
    pages: dict[Path, bytes] = {}
    index: list[dict[str, Any]] = []
    cache: dict[str, Image.Image] = {}
    for category, members in categories.items():
        for page_number, start in enumerate(range(0, len(members), PER_PAGE), start=1):
            chunk = members[start : start + PER_PAGE]
            sheet = Image.new("RGB", (COLUMNS * TILE, ROWS * (TILE + CAPTION)), "white")
            for slot, item in enumerate(chunk, start=1):
                if item.stem not in cache:
                    with Image.open(
                        suffix.get(item.stem, image_dir / f"{item.stem}.jpg")
                    ) as source:
                        cache[item.stem] = source.convert("RGB")
                tile = _tile(cache[item.stem], item, font)
                column, row = (slot - 1) % COLUMNS, (slot - 1) // COLUMNS
                sheet.paste(tile, (column * TILE, row * (TILE + CAPTION)))
                index.append(
                    {
                        "category": category,
                        "page": page_number,
                        "slot": slot,
                        "stem": item.stem,
                        "pred_rank": item.pred_rank,
                        "gt_index": item.gt_index,
                        "caption": item.caption,
                    }
                )
            buffer = io.BytesIO()
            sheet.save(buffer, format="JPEG", quality=88)
            pages[ATLAS_DIR / f"{category}_page_{page_number:02d}.jpg"] = buffer.getvalue()
    return pages, index


# --------------------------------------------------------------------------------------------
# Rendering of tables, report and manifest


def csv_bytes(fields: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _counts_table(counter: Counter[str], total: int) -> str:
    lines = ["| Class | Count | Share |", "| --- | ---: | ---: |"]
    for key, value in counter.most_common():
        lines.append(f"| {key} | {value} | {value / total:.1%} |")
    return "\n".join(lines)


def render_report(
    summary: dict[str, Any], pred_rows: list[dict[str, Any]], index: list[dict[str, Any]]
) -> str:
    background = Counter(r["pred_class"] for r in pred_rows if r["disposition"] == "BACKGROUND")
    pages = Counter((r["category"], r["page"]) for r in index)
    per_category = Counter(r["category"] for r in index)
    category_lines = "\n".join(
        f"| `{cat}` | {count} | {len({p for c, p in pages if c == cat})} |"
        for cat, count in per_category.items()
    )
    return f"""# D1-EA-R1 — validation error evidence package

Status: `{STATUS}`
Boundary: `{BOUNDARY}`

Built by `detector/m1/error_analysis_r1.py` as required by
`docs/review/d1_corrected_val_r10_error_analysis_and_improvement_packet_r1.md`. Inference ran once
on the R10 reference device (`{DEVICE}`, imgsz {IMGSZ}, NMS IoU {NMS_IOU}) with the pinned weights
`{PINNED[WEIGHTS][:16]}…`; the build refuses to write unless the regenerated predictions reproduce
the pinned R10 report exactly. Validation only: `test_included=false`,
`sealed_test_accessed=false`. No validation image, crop or prediction may enter training.

## Reproduction of R10 at conf {CONF}

| Quantity | Value |
| --- | ---: |
| Images | {summary["images"]} |
| Ground-truth boxes | {summary["ground_truth"]} |
| Retained predictions | {summary["retained_predictions"]} |
| Paired with ground truth | {summary["paired_predictions"]} |
| Background false positives | {summary["background_false_positives"]} |
| Unmatched ground truth | {summary["unmatched_ground_truth"]} |

The operating point, the full confusion matrix and the class-aware hits of every gated class equal
the R10 report.

## Background false positives by predicted class

{_counts_table(background, sum(background.values()))}

## Atlas

Green box = ground truth, red box = prediction. Pages are in `{ATLAS_DIR}/` (git-ignored: they
contain DATASET01 pixels); the page/slot roster is `{ATLAS_INDEX_PATH}`.

| Category | Items | Pages |
| --- | ---: | ---: |
{category_lines}

`critical_<c>` holds every ground-truth box of class c that the diagnostic pairing either assigns
to another class or leaves unmatched. Pairing is the score-ordered class-agnostic one-to-one
matching of the R10 confusion matrix; D-05 class-aware gate hits use a separate matcher.

## Not concluded here

Root causes are not stated by this package. The visual review that turns the atlas into
hypotheses, and the independent QA of this package, are separate steps.
"""


def render(
    frames: Sequence[Frame], report: dict[str, Any], repo_root: Path = REPO_ROOT
) -> dict[Path, bytes]:
    names = class_names(repo_root)
    summary = reproduction_check(frames, report, names)
    pred_rows = prediction_rows(frames, names)
    miss_rows = missed_rows(frames, names)
    if (
        len(pred_rows) != summary["retained_predictions"]
        or len(miss_rows) != summary["unmatched_ground_truth"]
    ):
        raise RuntimeError("exported rows differ from the reproduced counts")
    pages, index = render_atlas(atlas_items(frames, pred_rows, names), repo_root)
    artifacts: dict[Path, bytes] = {
        PREDICTIONS_PATH: csv_bytes(PREDICTION_FIELDS, pred_rows),
        MISSED_PATH: csv_bytes(MISSED_FIELDS, miss_rows),
        ATLAS_INDEX_PATH: csv_bytes(INDEX_FIELDS, index),
        **pages,
    }
    artifacts[REPORT_PATH] = render_report(summary, pred_rows, index).encode("utf-8")
    manifest = {
        "package": PACKAGE,
        "status": STATUS,
        "boundary": BOUNDARY,
        "run": RUN,
        "diagnostic_point": {"conf": CONF, "nms_iou": NMS_IOU, "imgsz": IMGSZ, "device": DEVICE},
        "summary": summary,
        "pinned_sources": {
            str(path): digest for path, digest in sorted(PINNED.items(), key=lambda kv: str(kv[0]))
        },
        "pillow_version": importlib.metadata.version("pillow"),
        "artifacts": {
            str(path): sha256_bytes(data)
            for path, data in sorted(artifacts.items(), key=lambda kv: str(kv[0]))
        },
        "atlas_pages": len(pages),
        "test_included": False,
        "sealed_test_accessed": False,
        "training_authorized": False,
        "validation_pixels_in_training": False,
    }
    artifacts[MANIFEST_PATH] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    return artifacts


# --------------------------------------------------------------------------------------------
# Commands


def infer_frames(repo_root: Path = REPO_ROOT) -> list[Frame]:
    """Run the exact R10 loader once; verifies the R10 data authority first."""
    sys.path.insert(0, str(repo_root / "detector"))
    from m1 import corrected_val_r1, corrected_val_r10

    corrected_val_r10.verify_corrected_data()
    binding = contract.bind_run_weights(str(repo_root / WEIGHTS))
    if binding["sha256"] != PINNED[WEIGHTS]:
        raise RuntimeError("bound weights differ from the pinned weights")
    contract.disable_telemetry()
    return corrected_val_r1.load_corrected_frames(binding["path"], IMGSZ, DEVICE, NMS_IOU)


def build(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    verify_pins(repo_root)
    report = load_r10_report(repo_root)
    targets = [MANIFEST_PATH, PREDICTIONS_PATH, MISSED_PATH, ATLAS_INDEX_PATH, REPORT_PATH]
    if any((repo_root / path).exists() for path in targets) or (repo_root / ATLAS_DIR).exists():
        raise RuntimeError("D1-EA-R1 outputs already exist; the package is append-only")
    names = class_names(repo_root)
    raw = infer_frames(repo_root)
    reproduction_check(raw, report, names)  # raw float32 predictions must reproduce R10
    table = csv_bytes(PREDICTION_FIELDS, prediction_rows(raw, names)).decode("utf-8")
    # Render from the exported table so that build and verify see byte-identical inputs.
    frames = frames_from_rows(csv.DictReader(io.StringIO(table)), names, repo_root)
    artifacts = render(frames, report, repo_root)
    if artifacts[PREDICTIONS_PATH].decode("utf-8") != table:
        raise RuntimeError("prediction table does not survive its own round trip")
    for path, data in artifacts.items():
        target = repo_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    manifest = json.loads(artifacts[MANIFEST_PATH])
    return {"status": STATUS, "artifacts": len(artifacts), "summary": manifest["summary"]}


def verify(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        verify_pins(repo_root)
        report = load_r10_report(repo_root)
        with (repo_root / PREDICTIONS_PATH).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        frames = frames_from_rows(rows, class_names(repo_root), repo_root)
        expected = render(frames, report, repo_root)
        for path, data in expected.items():
            target = repo_root / path
            if not target.is_file() or target.is_symlink() or target.read_bytes() != data:
                errors.append(f"artifact differs: {path}")
        atlas = repo_root / ATLAS_DIR
        extra = (
            sorted(p.name for p in atlas.iterdir() if ATLAS_DIR / p.name not in expected)
            if atlas.is_dir()
            else []
        )
        errors += [f"unexpected atlas file: {name}" for name in extra]
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        errors.append(str(error))
    return {"status": STATUS, "valid": not errors, "errors": errors[:20]}


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("build", help="run MPS inference once and write the package")
    commands.add_parser("verify", help="re-derive and byte-compare without a model")
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
