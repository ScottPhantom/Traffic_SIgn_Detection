"""YOLO54 improvement R3: source and evaluation readiness (validation-only, no training).

Contract: `docs/review/d1_yolo54_improvement_r3_contract.md`. Append-only successor of
`m1.yolo54_improvement_r2` (the QA-passed single-change trainer), which stays unchanged. R3 adds:

- **A0** (agnostic / grid NMS): an assessment of whether the saved D1-VRE-R2 candidates can answer
  the NMS question. They are post class-wise-NMS outputs, so A0 returns
  `A0_REQUIRES_VALIDATION_ONLY_REINFERENCE` and never claims an agnostic-NMS result;
- **A0b** (class-wise confidence): an offline diagnostic on the saved candidates, reported beside
  the global-threshold baseline with paired group-bootstrap CIs. Per-class thresholding after
  class-wise NMS is exact when no image reaches `max_det`; that is checked. Every result is
  `DIAGNOSTIC_PENDING_OWNER_D05_Q4_INTERPRETATION`; no threshold is ever selected or locked;
- **A1** hard-negative mining: always
  `A1_BLOCKED_PENDING_TRAIN_LABEL_COMPLETENESS_AND_HUMAN_REVIEW`;
- **A2/A3** run specifications frozen with `training_authorized=false`, and the train-only A2
  repeat-factor roster computed from the verified pilot export.

Inputs are read from an evidence root (the checkout holding the D1-VRE-R2 artifacts) through a
guard that refuses absolute or escaping paths, any `test` path component, symlinks and hardlinks.
The matcher, operating point, threshold grid and group bootstrap are `m1.metrics`; the module first
reproduces the D1-VRE-R2 fixed point and bootstrap CI exactly and refuses otherwise. It never loads
a model, never reads validation pixels, never lists a test directory and writes one canonical JSON
only after re-verifying every pinned input.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import stat
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from m1 import contract
from m1.metrics import Frame, group_bootstrap, operating_point, select_threshold

PACKAGE = "D1-YOLO54-IMPROVEMENT-R3"
STATUS = "YOLO54_IMPROVEMENT_R3_AWAITING_INDEPENDENT_QA"
BOUNDARY = "VALIDATION_ONLY_ANALYSIS_NO_TRAINING_NO_INFERENCE_NO_SEALED_TEST"
SCHEMA_VERSION = 1

A0_REINFERENCE = "A0_REQUIRES_VALIDATION_ONLY_REINFERENCE"
A0B_STATUS = "DIAGNOSTIC_PENDING_OWNER_D05_Q4_INTERPRETATION"
A1_BLOCKED = "A1_BLOCKED_PENDING_TRAIN_LABEL_COMPLETENESS_AND_HUMAN_REVIEW"
RUN_WAITING = "WAITING_FOR_L4_AND_OWNER_AUTHORIZATION"

RUN = "D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2"
RUN_DIR = Path("results/experiments") / RUN
VRE_DIR = RUN_DIR / "d1_vre_r2"
REPORT = VRE_DIR / "eval_val_vrl_r3_vre_r2.json"
PREDICTIONS = VRE_DIR / "predictions_conf0001.csv"
R3_LABELS = Path("data/processed/m1_yolo_val_vrl_r3/labels/val")
TRAIN_LABELS = Path("data/processed/m1_yolo/labels/train")
WP35_SOURCE_LABELS = Path("data/processed/wp35_enrichment/labels")
CLASS_MAP = Path("docs/review/generated/m1_yolo_classes.csv")
SPLIT_FRAMES = Path("docs/review/generated/wp36_r1_split_frames.csv")
EXPORT_MANIFEST = Path("docs/review/generated/m1_yolo_export_manifest.json")
WP35_LINEAGE = Path("docs/review/generated/wp35_enrichment_lineage.csv")
OUTPUT = Path("docs/review/generated/d1_yolo54_improvement_r3_analysis.json")

# Every evidence authority this package consumes, relative to the evidence root.
PINNED: dict[Path, str] = {
    REPORT: "559c6c6a78a0d653da09a43bf6dc0663a2dbcb07f6aef4748cade369ef857c87",
    PREDICTIONS: "87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893",
    RUN_DIR / "weights/best.pt": "5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633",
    RUN_DIR
    / "run_contract.json": "9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88",
    RUN_DIR / "args.yaml": "a457c6d51547477348c19a06ec4cf3c8794508169b2e0e1a43edc6260b7d16f0",
    Path("models/pretrained/yolo11s.pt"): (
        "85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5"
    ),
    Path("detector/m1/val_reeval_r2.py"): (
        "2a0823faa15f7cb9cecb64a1f21e48e8b5b84f7e7f949683683a6992ee13ccc9"
    ),
    Path("docs/review/d1_vre_r2_contract.md"): (
        "751d78fe3decf3b3e54cc6f4d004c6c6408ce97ae3a44a09e77f35bffc990ab0"
    ),
    Path("docs/review/d1_vre_r2_source_independent_qa_record.md"): (
        "1530942a747b9d2f49aef0df4156247dd5c8453dcbcb2ec499feea271c6e886f"
    ),
    Path("docs/review/d1_vre_r2_result_report.md"): (
        "96255be888e5a06c40e18441a86dc3140702ba4558bcc32e9dec00bacffdf68b"
    ),
    Path("docs/review/d1_vre_r2_result_independent_qa_record.md"): (
        "95db91cbe640e27ee6de2c185a09b61902da4412717310932aa3b36e48be031b"
    ),
    Path("docs/review/d1_improvement_experiments_r1_contract.md"): (
        "4b144ee19fa66176616ac3ab254e6ca4a977662df960151eb979b38d474ecde0"
    ),
    Path("docs/review/d1_ea_r1_evidence_report.md"): (
        "981f3c09355550cf97f221a26a3344416b3188d219c161ad04820692abc395df"
    ),
    Path("docs/review/d1_ea_r1_independent_qa_record.md"): (
        "273c63563634d0ba002b9e5e0c9728e66e638477703715d33f2e80967262d65e"
    ),
    Path("docs/review/d1_vrl_r3_owner_acceptance_record.md"): (
        "4d9482856771960240cdf727834e9283fb9ba072f88992c6204dcbb6405d7480"
    ),
    Path("docs/review/generated/d1_vrl_r3_manifest.json"): (
        "87dd0fd9ecea85745f613a788ef70ae830d396fc9e747f233db0c6fc536b8e07"
    ),
    Path("docs/review/d05_owner_decision_record.md"): (
        "c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702"
    ),
    Path("docs/review/generated/d1_run_registry.json"): (
        "ba5ab04fd6e28e849a6b1aaf345bb5e284eb2a7aa1ee9c7cee0714209ed2b0c9"
    ),
    CLASS_MAP: "7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242",
    SPLIT_FRAMES: "8e197d9c7103ac5dc6b7ffc8a3d1aeb30bb6034048d470e4887dd868df95823a",
    EXPORT_MANIFEST: "8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71",
    WP35_LINEAGE: "e802fc264feff5168c28b531801af04051a36accc3c893ad5ab2e72975d38fed",
    Path("detector/m1/metrics.py"): (
        "d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f"
    ),
    Path("detector/m1/contract.py"): (
        "901e7e372d9660cd79e6bfcab43684b1693f0a4aafad9f4c331fd8f04ba6bbbf"
    ),
    Path("detector/m1/cli.py"): "3e0c13b3c47fb396429a0d06e16c6e6d98ca063d10d68d81a4c87af42b4cf967",
}
R3_LABEL_ROSTER_SHA256 = "dc72ebd944a38535d4f766ba4f8babc60cb6732dfcd253ed0e8d79dc86eb8343"
TRAIN_STEM_LIST_SHA256 = "6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372"
TRAIN_LABELS_SHA256 = "d907fb9f82bbcee4bfb0d6f34d9a673c6f7dbe4173967c92b7552c607abb3b49"

FRAMES, R3_BOXES, CLASSES, TRAIN_FRAMES, WP35_IMAGES = 376, 624, 54, 1912, 1800
IMAGE_SIZE = (960, 540)  # D1-VRE-R2 resolution breakdown: all 376 frames
PREDICTION_ROWS = 1999
PREDICTION_FIELDS = ["stem", "rank", "yolo_id", "conf", "x1", "y1", "x2", "y2"]
CANDIDATE_CONF, NMS_IOU, MAX_DET, IOU_MATCH = 0.001, 0.7, 300, 0.5
CONF = 0.20
BOOTSTRAP_ROUNDS, BOOTSTRAP_SEED = 1000, 20261018
GLOBAL_GRID = tuple(round(x, 2) for x in np.arange(0.05, 0.96, 0.05))
# A0b search space, fixed before looking at any class-wise result: the four focus classes may each
# be lowered to one of three values; everything else stays at the global 0.20.
FOCUS_KEYS = ("7", "32", "41", "46")
CLASSWISE_GRID = (0.05, 0.10, 0.15)
COMBINED_PROBE = 0.10
A2_REPEAT_KEYS = ("7", "32", "41")
A2_REPEAT_FACTOR = 2


# ----------------------------------------------------------------------------------- guards


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_test_part(part: str) -> bool:
    return "test" in part.lower()


def guard(
    root: Path, relative: Path, *, directory: bool = False, package_source: bool = False
) -> Path:
    """Refuse absolute/escaping paths, test components, symlinks, hardlinks and odd files.

    `package_source=True` is used only to hash this package's own files for the manifest, where
    `detector/tests/` is the unit-test folder, not the sealed split; every other check still runs.
    """
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise RuntimeError(f"refused non-relative path: {relative}")
    if not package_source and any(_is_test_part(part) for part in relative.parts):
        raise RuntimeError(f"refused sealed-test path: {relative}")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeError(f"refused symlink in input chain: {relative}")
    info = os.lstat(current)
    if directory:
        if not stat.S_ISDIR(info.st_mode):
            raise RuntimeError(f"refused non-directory: {relative}")
    elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RuntimeError(f"refused non-regular or hardlinked file: {relative}")
    if not current.resolve().is_relative_to(root.resolve()):
        raise RuntimeError(f"refused path escaping the root: {relative}")
    return current


def read_pinned(root: Path, relative: Path) -> bytes:
    data = guard(root, relative).read_bytes()
    if relative in PINNED and sha256_bytes(data) != PINNED[relative]:
        raise RuntimeError(f"pinned input differs: {relative}")
    return data


def verify_pins(root: Path, pins: dict[Path, str] | None = None) -> dict[str, str]:
    observed = {}
    for relative, expected in sorted((PINNED if pins is None else pins).items()):
        digest = sha256_bytes(guard(root, relative).read_bytes())
        if digest != expected:
            raise RuntimeError(f"pinned input differs: {relative}")
        observed[str(relative)] = digest
    return observed


def _regular_files(root: Path, relative: Path) -> dict[str, bytes]:
    folder = guard(root, relative, directory=True)
    blobs = {}
    for entry in sorted(os.scandir(folder), key=lambda e: e.name):
        if _is_test_part(entry.name) or not entry.name.endswith(".txt"):
            raise RuntimeError(f"refused unexpected entry in {relative}: {entry.name}")
        guard(root, relative / entry.name)
        with open(entry.path, "rb") as handle:
            blobs[entry.name] = handle.read()
    return blobs


def _strict_bool_false(value: Any, label: str) -> None:
    if value is not False:  # rejects 0, None and every other false-like value
        raise RuntimeError(f"{label} must be the JSON boolean false")


def _strict_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError(f"{label} must be an integer, not {type(value).__name__}")
    return value


def _strict_float(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise RuntimeError(f"{label} must be a finite number")
    return float(value)


# ----------------------------------------------------------------------------------- inputs


def class_map(root: Path) -> tuple[list[str], dict[str, int]]:
    rows = list(csv.DictReader(io.StringIO(read_pinned(root, CLASS_MAP).decode("utf-8"))))
    names = [""] * len(rows)
    for row in rows:
        names[int(row["yolo_id"])] = row["derived_key"]
    if len(names) != CLASSES or "" in names or len(set(names)) != CLASSES:
        raise RuntimeError("class map is not a dense unique 54-class YOLO range")
    return names, {key: index for index, key in enumerate(names)}


def _parse_label(name: str, text: str) -> list[tuple[int, tuple[float, ...]]]:
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 5 or not fields[0].isdigit():
            raise RuntimeError(f"malformed label row in {name}")
        cls, values = int(fields[0]), tuple(float(v) for v in fields[1:])
        if not 0 <= cls < CLASSES or not all(math.isfinite(v) and 0 <= v <= 1 for v in values):
            raise RuntimeError(f"label row outside the 54-class unit box in {name}")
        if values[2] <= 0 or values[3] <= 0:
            raise RuntimeError(f"degenerate label box in {name}")
        rows.append((cls, values))
    return rows


def load_r3_labels(root: Path) -> dict[str, list[tuple[int, tuple[float, ...]]]]:
    blobs = _regular_files(root, R3_LABELS)
    roster = json.dumps({n: sha256_bytes(d) for n, d in sorted(blobs.items())}, sort_keys=True)
    if len(blobs) != FRAMES or sha256_bytes(roster.encode()) != R3_LABEL_ROSTER_SHA256:
        raise RuntimeError("R3 validation label roster differs from 376 files / dc72ebd9…")
    labels = {name[:-4]: _parse_label(name, data.decode("utf-8")) for name, data in blobs.items()}
    if sum(map(len, labels.values())) != R3_BOXES:
        raise RuntimeError("R3 validation labels do not hold 624 boxes")
    return labels


def load_groups(root: Path, stems: Iterable[str]) -> dict[str, str]:
    rows = csv.DictReader(io.StringIO(read_pinned(root, SPLIT_FRAMES).decode("utf-8")))
    split = {row["stem"]: (row["split"], row["group_id"]) for row in rows}
    groups = {}
    for stem in stems:
        if stem not in split or split[stem][0] != "val":
            raise RuntimeError(f"frame {stem} is not a WP36-R1 validation frame")
        groups[stem] = split[stem][1]
    return groups


def load_report(root: Path) -> dict[str, Any]:
    read_pinned(root, REPORT)
    report = contract.strict_json(guard(root, REPORT))
    for flag in (
        "test_included",
        "sealed_test_accessed",
        "training_authorized",
        "gates_changed",
        "threshold_lock_written",
    ):
        _strict_bool_false(report.get(flag), f"D1-VRE-R2 {flag}")
    if report.get("package") != "D1-VRE-R2" or report.get("run") != RUN:
        raise RuntimeError("D1-VRE-R2 report identity differs")
    settings = report.get("settings", {})
    expected = {"candidate_conf": CANDIDATE_CONF, "nms_iou": NMS_IOU, "iou_match": IOU_MATCH}
    if any(_strict_float(settings.get(k), k) != v for k, v in expected.items()):
        raise RuntimeError("D1-VRE-R2 inference settings differ from the contract")
    resolution = report["primary_r3"]["fixed_conf_0_20"]["resolution_breakdown"]
    width, height = IMAGE_SIZE
    if set(resolution) != {f"{width}x{height}"}:
        raise RuntimeError("validation frames are not all 960x540")
    _strict_int(resolution[f"{width}x{height}"]["images"], "images")
    return report


def parse_predictions(data: bytes, stems: Sequence[str]) -> dict[str, list[tuple[Any, ...]]]:
    """Strict CSV schema: exact header, ranked by descending score, finite in-range values."""
    reader = csv.reader(io.StringIO(data.decode("utf-8")))
    if next(reader, None) != PREDICTION_FIELDS:
        raise RuntimeError("prediction CSV header differs from the D1-VRE-R2 schema")
    known = set(stems)
    rows: dict[str, list[tuple[Any, ...]]] = {}
    count = 0
    for record in reader:
        count += 1
        if len(record) != len(PREDICTION_FIELDS):
            raise RuntimeError("prediction CSV row has the wrong number of fields")
        stem, rank, yolo_id = record[0], record[1], record[2]
        if stem not in known:
            raise RuntimeError(f"prediction CSV names a frame outside the roster: {stem}")
        if not rank.isdigit() or not yolo_id.isdigit() or not 0 <= int(yolo_id) < CLASSES:
            raise RuntimeError(f"prediction CSV rank/class is not a valid integer for {stem}")
        values = [float(v) for v in record[3:]]
        if not all(math.isfinite(v) for v in values):
            raise RuntimeError(f"prediction CSV holds a non-finite value for {stem}")
        conf, x1, y1, x2, y2 = values
        if not CANDIDATE_CONF <= conf <= 1.0 or x2 < x1 or y2 < y1:
            raise RuntimeError(f"prediction CSV box or score out of range for {stem}")
        rows.setdefault(stem, []).append((int(rank), int(yolo_id), conf, (x1, y1, x2, y2)))
    if count != PREDICTION_ROWS:
        raise RuntimeError(f"prediction CSV holds {count} rows, not {PREDICTION_ROWS}")
    for stem, items in rows.items():
        if [r[0] for r in items] != list(range(len(items))):
            raise RuntimeError(f"prediction ranks are not contiguous for {stem}")
        if any(a[2] < b[2] for a, b in zip(items, items[1:], strict=False)):
            raise RuntimeError(f"prediction scores are not in descending rank order for {stem}")
        if len(items) >= MAX_DET:
            raise RuntimeError(f"{stem} reached max_det; class-wise thresholds would not be exact")
    return rows


def build_frames(
    labels: dict[str, list[tuple[int, tuple[float, ...]]]],
    groups: dict[str, str],
    predictions: dict[str, list[tuple[Any, ...]]],
) -> list[Frame]:
    width, height = IMAGE_SIZE
    frames = []
    for stem in sorted(labels):
        gt = np.asarray([r[1] for r in labels[stem]], dtype=float).reshape(-1, 4)
        gt_boxes = np.column_stack(
            [
                (gt[:, 0] - gt[:, 2] / 2) * width,
                (gt[:, 1] - gt[:, 3] / 2) * height,
                (gt[:, 0] + gt[:, 2] / 2) * width,
                (gt[:, 1] + gt[:, 3] / 2) * height,
            ]
        ).reshape(-1, 4)
        rows = predictions.get(stem, [])
        frames.append(
            Frame(
                stem=stem,
                group_id=groups[stem],
                gt_boxes=gt_boxes,
                gt_classes=np.asarray([r[0] for r in labels[stem]], dtype=int),
                pred_boxes=np.asarray([r[3] for r in rows], dtype=float).reshape(-1, 4),
                pred_classes=np.asarray([r[1] for r in rows], dtype=int),
                pred_scores=np.asarray([r[2] for r in rows], dtype=float),
                image_width=width,
                image_height=height,
            )
        )
    if len(frames) != FRAMES:
        raise RuntimeError("validation frame roster differs from 376 frames")
    return frames


def reproduce(frames: Sequence[Frame], report: dict[str, Any], names: list[str]) -> dict[str, Any]:
    """The shared matcher must reproduce the QA-passed D1-VRE-R2 fixed point and bootstrap CI."""
    stored = report["primary_r3"]["fixed_conf_0_20"]
    point = operating_point(frames, CONF)
    reference = stored["operating_point"]
    observed = {
        "true_positives": point.true_positives,
        "false_positives": point.false_positives,
        "ground_truth": point.ground_truth,
        "images": point.images,
        "agnostic_recall": point.agnostic_recall,
        "fp_per_image": point.fp_per_image,
        "precision": point.precision,
    }
    if any(observed[k] != reference[k] for k in observed):
        raise RuntimeError("the shared matcher does not reproduce the D1-VRE-R2 fixed point")
    hits = {names[c]: h for c, h in point.per_class_hits.items()}
    if hits != {k: v["hits"] for k, v in reference["per_class"].items()}:
        raise RuntimeError("per-class hits do not reproduce D1-VRE-R2")
    ci = group_bootstrap(frames, CONF, BOOTSTRAP_ROUNDS, BOOTSTRAP_SEED)
    if {k: list(v) for k, v in ci.items()} != stored["bootstrap_95ci"]:
        raise RuntimeError("the group bootstrap does not reproduce the D1-VRE-R2 CI")
    selected = select_threshold(frames, contract.GATES["agnostic_recall"], GLOBAL_GRID)
    if selected.conf != report["primary_r3"]["d05_q4_selected"]["operating_point"]["conf"]:
        raise RuntimeError("D-05 Q4 grid selection does not reproduce D1-VRE-R2")
    return {**observed, "bootstrap_95ci": stored["bootstrap_95ci"], "d05_q4_conf": selected.conf}


# ----------------------------------------------------------------------------------- A0


def a0_assessment(settings: dict[str, Any], *, prediction_stage: str) -> dict[str, Any]:
    """Whether saved candidates can answer agnostic/grid NMS. Post-NMS outputs never can."""
    if prediction_stage != "PRE_NMS_CANDIDATES":
        return {
            "status": A0_REINFERENCE,
            "prediction_stage": prediction_stage,
            "agnostic_nms_verified": False,
            "nms_grid_evaluated": False,
            "reinference_authorized": False,
            "reason": (
                f"the D1-VRE-R2 candidates were kept after class-wise NMS at IoU "
                f"{settings['nms_iou']} (conf >= {settings['candidate_conf']}, max_det {MAX_DET}); "
                "boxes suppressed there are absent, so neither agnostic NMS nor a class-wise IoU "
                "grid can be reconstructed exactly. A validation-only re-inference contract is "
                "required, and it needs Owner authorization before it runs."
            ),
        }
    return {
        "status": "A0_DATA_SUFFICIENT_NOT_EVALUATED_IN_R3",
        "prediction_stage": prediction_stage,
        "agnostic_nms_verified": False,
        "nms_grid_evaluated": False,
        "reinference_authorized": False,
        "reason": "pre-NMS candidates would allow A0 under its own contract; R3 evaluates nothing.",
    }


# ----------------------------------------------------------------------------------- A0b


def apply_thresholds(frames: Sequence[Frame], thresholds: Sequence[float]) -> list[Frame]:
    """Keep each candidate whose score reaches its own class's threshold (then score at conf 0)."""
    table = np.asarray(thresholds, dtype=float)
    kept = []
    for frame in frames:
        keep = frame.pred_scores >= table[frame.pred_classes]
        kept.append(
            Frame(
                stem=frame.stem,
                group_id=frame.group_id,
                gt_boxes=frame.gt_boxes,
                gt_classes=frame.gt_classes,
                pred_boxes=frame.pred_boxes[keep],
                pred_classes=frame.pred_classes[keep],
                pred_scores=frame.pred_scores[keep],
                image_width=frame.image_width,
                image_height=frame.image_height,
            )
        )
    return kept


def frame_counts(frames: Sequence[Frame]) -> dict[str, np.ndarray]:
    """Per-frame additive counts of `operating_point`: agnostic hits, GT, FP, class hits/support."""
    hits, support, fps = [], [], []
    class_hits = np.zeros((len(frames), CLASSES), dtype=np.int64)
    class_support = np.zeros((len(frames), CLASSES), dtype=np.int64)
    for index, frame in enumerate(frames):
        point = operating_point([frame], 0.0)
        hits.append(point.true_positives)
        support.append(point.ground_truth)
        fps.append(point.false_positives)
        for cls, value in point.per_class_hits.items():
            class_hits[index, cls] = value
        for cls, value in point.per_class_support.items():
            class_support[index, cls] = value
    return {
        "hits": np.asarray(hits, dtype=np.int64),
        "support": np.asarray(support, dtype=np.int64),
        "fps": np.asarray(fps, dtype=np.int64),
        "class_hits": class_hits,
        "class_support": class_support,
    }


def bootstrap_samples(frames: Sequence[Frame], rounds: int, seed: int) -> list[np.ndarray]:
    """Frame indices of each round, drawn exactly as `metrics.group_bootstrap` draws them."""
    groups: dict[str, list[int]] = {}
    for index, frame in enumerate(frames):
        groups.setdefault(frame.group_id, []).append(index)
    names = sorted(groups)
    rng = np.random.default_rng(seed)
    return [
        np.asarray(
            [i for g in rng.choice(names, size=len(names), replace=True) for i in groups[g]],
            dtype=np.int64,
        )
        for _ in range(rounds)
    ]


def _summary(counts: dict[str, np.ndarray], index: np.ndarray, images: int) -> dict[str, Any]:
    hits, support, fps = (int(counts[k][index].sum()) for k in ("hits", "support", "fps"))
    return {
        "agnostic_recall": hits / support if support else 0.0,
        "fp_per_image": fps / images if images else 0.0,
        "precision": hits / (hits + fps) if hits + fps else 0.0,
        "class_hits": counts["class_hits"][index].sum(axis=0),
        "class_support": counts["class_support"][index].sum(axis=0),
    }


def _ci(values: Sequence[float]) -> list[float]:
    return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]


def describe(
    counts: dict[str, np.ndarray],
    baseline: dict[str, np.ndarray],
    samples: Sequence[np.ndarray],
    names: list[str],
    ids: dict[str, int],
) -> dict[str, Any]:
    """Point estimates, absolute CIs and paired CIs of the difference from the 0.20 baseline."""
    full = np.arange(len(counts["hits"]))
    point = _summary(counts, full, len(full))
    base = _summary(baseline, full, len(full))
    gated = {}
    for cls in range(CLASSES):
        support = int(point["class_support"][cls])
        if support >= contract.GATES["min_support_for_class_gate"]:
            critical = names[cls] in contract.CRITICAL_KEYS
            gate = contract.GATES["critical_class_recall" if critical else "other_class_recall"]
            recall = int(point["class_hits"][cls]) / support
            gated[names[cls]] = {
                "hits": int(point["class_hits"][cls]),
                "support": support,
                "recall": recall,
                "baseline_recall": int(base["class_hits"][cls]) / support,
                "reference": gate,
                "meets_reference": recall >= gate,
            }
    focus_ids = [ids[key] for key in FOCUS_KEYS]
    draws: dict[str, list[float]] = {"recall": [], "fp": [], "d_recall": [], "d_fp": []}
    focus_deltas: dict[str, list[float]] = {key: [] for key in FOCUS_KEYS}
    for index in samples:
        a, b = _summary(counts, index, len(index)), _summary(baseline, index, len(index))
        draws["recall"].append(a["agnostic_recall"])
        draws["fp"].append(a["fp_per_image"])
        draws["d_recall"].append(a["agnostic_recall"] - b["agnostic_recall"])
        draws["d_fp"].append(a["fp_per_image"] - b["fp_per_image"])
        for key, cls in zip(FOCUS_KEYS, focus_ids, strict=True):
            support = int(a["class_support"][cls])
            if support:
                delta = int(a["class_hits"][cls]) - int(b["class_hits"][cls])
                focus_deltas[key].append(delta / support)
    focus = {}
    for key, cls in zip(FOCUS_KEYS, focus_ids, strict=True):
        support = int(point["class_support"][cls])
        focus[key] = {
            "support": support,
            "hits": int(point["class_hits"][cls]),
            "recall": int(point["class_hits"][cls]) / support,
            "delta_vs_baseline": (int(point["class_hits"][cls]) - int(base["class_hits"][cls]))
            / support,
            "paired_delta_95ci": _ci(focus_deltas[key]),
            "bootstrap_rounds_with_support": len(focus_deltas[key]),
        }
    return {
        "agnostic_recall": point["agnostic_recall"],
        "fp_per_image": point["fp_per_image"],
        "precision": point["precision"],
        "true_positives": int(counts["hits"].sum()),
        "false_positives": int(counts["fps"].sum()),
        "bootstrap_95ci": {
            "agnostic_recall": _ci(draws["recall"]),
            "fp_per_image": _ci(draws["fp"]),
        },
        "paired_delta_vs_global_0_20": {
            "agnostic_recall": point["agnostic_recall"] - base["agnostic_recall"],
            "fp_per_image": point["fp_per_image"] - base["fp_per_image"],
            "agnostic_recall_95ci": _ci(draws["d_recall"]),
            "fp_per_image_95ci": _ci(draws["d_fp"]),
        },
        "focus_classes": focus,
        "gated_classes": gated,
        "screening_flags": {
            "recall_at_least_0_85": point["agnostic_recall"] >= contract.GATES["agnostic_recall"],
            "fp_per_image_not_above_baseline": point["fp_per_image"] <= base["fp_per_image"],
            "every_gated_class_meets_reference": all(v["meets_reference"] for v in gated.values()),
        },
    }


def a0b_configs(ids: dict[str, int]) -> list[dict[str, Any]]:
    """The fixed A0b search space: one focus class lowered at a time, plus one combined probe."""
    configs = []
    for key in FOCUS_KEYS:
        for value in CLASSWISE_GRID:
            configs.append({"name": f"class_{key}_at_{value:.2f}", "overrides": {key: value}})
    configs.append(
        {
            "name": f"focus_classes_at_{COMBINED_PROBE:.2f}",
            "overrides": {key: COMBINED_PROBE for key in FOCUS_KEYS},
        }
    )
    for config in configs:
        if set(config["overrides"]) - set(FOCUS_KEYS) or not all(
            0 < v < CONF for v in config["overrides"].values()
        ):
            raise RuntimeError("A0b config outside the pre-registered search space")
        table = [CONF] * CLASSES
        for key, value in config["overrides"].items():
            table[ids[key]] = value
        config["thresholds"] = table
    return configs


def a0b_analysis(
    frames: Sequence[Frame],
    names: list[str],
    ids: dict[str, int],
    *,
    rounds: int = BOOTSTRAP_ROUNDS,
) -> dict[str, Any]:
    samples = bootstrap_samples(frames, rounds, BOOTSTRAP_SEED)
    baseline = frame_counts(apply_thresholds(frames, [CONF] * CLASSES))
    global_points = {}
    for conf in GLOBAL_GRID:
        counts = frame_counts(apply_thresholds(frames, [conf] * CLASSES))
        global_points[f"{conf:.2f}"] = describe(counts, baseline, samples, names, ids)
    classwise = {}
    for config in a0b_configs(ids):
        counts = frame_counts(apply_thresholds(frames, config["thresholds"]))
        classwise[config["name"]] = {
            "overrides": config["overrides"],
            **describe(counts, baseline, samples, names, ids),
        }
    support = {
        key: int(sum((f.gt_classes == ids[key]).sum() for f in frames)) for key in FOCUS_KEYS
    }
    return {
        "status": A0B_STATUS,
        "official_threshold": None,
        "selected_config": None,
        "gate_pass_claimed": False,
        "threshold_lock_written": False,
        "baseline": "global conf 0.20 (D1-VRE-R2 fixed point and D-05 Q4 grid candidate)",
        "exactness": (
            "class-wise NMS keeps or drops a box by higher-scoring same-class boxes only, and no "
            "image reached max_det, so thresholding the saved post-NMS candidates per class "
            "equals re-running inference with those thresholds"
        ),
        "search_space": {
            "focus_classes": list(FOCUS_KEYS),
            "values_per_class": list(CLASSWISE_GRID),
            "combined_probe": COMBINED_PROBE,
            "configurations": len(classwise),
            "other_classes": CONF,
            "validation_support": support,
        },
        "overfit_note": (
            "376 validation images in few D-02 groups; every configuration is scored on the same "
            "frames it would be chosen on. Point estimates are not a selection rule."
        ),
        "bootstrap": {"rounds": rounds, "seed": BOOTSTRAP_SEED, "unit": "D-02 group, paired"},
        "global_grid": global_points,
        "classwise": classwise,
    }


# ----------------------------------------------------------------------------------- A1/A2/A3


def a1_status(review_package: Path | None = None) -> dict[str, Any]:
    """A1 stays blocked: no QA-passed human train-label-completeness review exists."""
    return {
        "status": A1_BLOCKED,
        "review_package_supplied": review_package is not None,
        "training_data_written": False,
        "reason": (
            "the train split may contain unlabelled real signs; an unmatched prediction is never "
            "treated as background without a QA-passed human review package, and R3 defines none"
        ),
    }


def _label_hash(texts: dict[str, str]) -> str:
    return sha256_bytes("".join(f"{s}\n{texts[s]}" for s in sorted(texts)).encode("utf-8"))


def a2_repeat_roster(root: Path, ids: dict[str, int]) -> dict[str, Any]:
    """Train-only repeat-factor roster, from labels verified against the pilot export manifest."""
    manifest = contract.strict_json(guard(root, EXPORT_MANIFEST))
    read_pinned(root, EXPORT_MANIFEST)
    train = manifest["splits"]["train"]
    if (train["stem_list_sha256"], train["labels_sha256"]) != (
        TRAIN_STEM_LIST_SHA256,
        TRAIN_LABELS_SHA256,
    ):
        raise RuntimeError("export manifest train binding differs from the pilot")
    lineage = {
        row["augmented_id"]: row["label_sha256"]
        for row in csv.DictReader(io.StringIO(read_pinned(root, WP35_LINEAGE).decode("utf-8")))
    }
    blobs = _regular_files(root, TRAIN_LABELS)
    texts = {name[:-4]: data.decode("utf-8") for name, data in blobs.items()}
    raw = {stem: text for stem, text in texts.items() if stem not in lineage}
    if set(texts) - set(raw) != set(lineage) or len(lineage) != WP35_IMAGES:
        raise RuntimeError("WP35 train labels differ from the 1,800-image lineage")
    names_hash = sha256_bytes("\n".join(sorted(raw)).encode("utf-8"))
    if len(raw) != TRAIN_FRAMES or names_hash != TRAIN_STEM_LIST_SHA256:
        raise RuntimeError("raw train label roster differs from the pilot export")
    if _label_hash(raw) != TRAIN_LABELS_SHA256:
        raise RuntimeError("raw train labels differ from the pilot export manifest")
    # The lineage pins the WP35 source label (derived keys); the export maps keys to YOLO ids.
    sources = _regular_files(root, WP35_SOURCE_LABELS)
    if set(sources) != {f"{stem}.txt" for stem in lineage}:
        raise RuntimeError("WP35 source label roster differs from the lineage")
    for stem, expected in lineage.items():
        source = sources[f"{stem}.txt"]
        if sha256_bytes(source) != expected:
            raise RuntimeError(f"WP35 source label differs from its lineage: {stem}")
        rows = [line.split() for line in source.decode("utf-8").splitlines() if line.strip()]
        if texts[stem] != "".join(f"{ids[r[0]]} {' '.join(r[1:])}\n" for r in rows):
            raise RuntimeError(f"exported WP35 label differs from its lineage source: {stem}")
    targets = {ids[key] for key in A2_REPEAT_KEYS}
    repeated = sorted(
        stem
        for stem, text in texts.items()
        if targets & {cls for cls, _ in _parse_label(stem, text)}
    )
    boxes = {
        key: {
            part: sum(
                1
                for stem, text in texts.items()
                if (stem in lineage) == (part == "wp35")
                for cls, _ in _parse_label(stem, text)
                if cls == ids[key]
            )
            for part in ("raw", "wp35")
        }
        for key in A2_REPEAT_KEYS
    }
    return {
        "rule": (
            f"every train image (raw or WP35) whose label holds class "
            f"{'/'.join(A2_REPEAT_KEYS)} is listed {A2_REPEAT_FACTOR}x; no new pixels"
        ),
        "train_images": len(texts),
        "raw_train_frames": len(raw),
        "wp35_images": len(lineage),
        "repeated_images": len(repeated),
        "repeated_raw_frames": sum(1 for s in repeated if s not in lineage),
        "train_boxes_per_class": boxes,
        "repeated_roster_sha256": sha256_bytes("\n".join(repeated).encode("utf-8")),
        "train_list_entries": len(texts) + (A2_REPEAT_FACTOR - 1) * len(repeated),
        "validation_used": False,
    }


PILOT_TRAIN_ARGS = {
    "batch": 4,
    "deterministic": True,
    "device": "0",
    "epochs": 100,
    "fliplr": 0.0,
    "fraction": 1.0,
    "imgsz": 1280,
    "patience": 0,
    "plots": False,
    "pretrained": True,
    "seed": 20261018,
    "workers": 4,
}
# Names follow the QA-passed pilot runner (`colab/run_d1_colab_pilot_r5.py`).
EXPECTED_ARTIFACTS = (
    "<run>/weights/best.pt",
    "<run>/weights/last.pt",
    "<run>/results.csv",
    "<run>/args.yaml",
    "<run>/run_contract.json",
    "<drive state>/colab_execution.json",
    "<drive state>/execution_attempts.jsonl",
    "<drive state>/DB_logger.db",
    "<drive state>/colab_train.log",
    "<drive state>/<run>_result.tar.gz",
    "<drive state>/<run>_result.tar.gz.manifest.json",
    "<checkpoint dir>/latest.json + snapshots/epoch-NNNN/checkpoint_manifest.json",
)


def run_specs(repeat: dict[str, Any] | None) -> dict[str, Any]:
    """A2 and A3 frozen as source specs; neither is authorised to train."""
    common = {
        "model": "YOLO11s, 54 classes",
        "pretrained_sha256": PINNED[Path("models/pretrained/yolo11s.pt")],
        "baseline_run": RUN,
        "train_data": "pilot M1 export 8a8df5f2… (WP36-R1 train + WP35 train-only)",
        "export_manifest_sha256": PINNED[EXPORT_MANIFEST],
        "train_stem_list_sha256": TRAIN_STEM_LIST_SHA256,
        "train_labels_sha256": TRAIN_LABELS_SHA256,
        "validation": "D1-VRL-R3 labels, 376 images / 624 GT (roster dc72ebd9…), scoring only",
        "label_authority": "D1-VRL-R3 owner acceptance 4d948285…",
        "seed": 20261018,
        "expected_artifacts": list(EXPECTED_ARTIFACTS),
        "checkpoint": "per-epoch mirror and verified resume (m1.resumable_train, checkpoint_store)",
        "evaluator": "a D1-VRE-R2 successor accepting registered ablation weights (not built)",
        "training_authorized": False,
        "sealed_test_accessed": False,
        "status": RUN_WAITING,
    }
    a2_args = {**PILOT_TRAIN_ARGS, "data": "<A2 train list: pilot train + repeat roster>"}
    a3_args = {**PILOT_TRAIN_ARGS, "epochs": 40, "cos_lr": True}
    return {
        "A2_repeat_factor_7_32_41": {
            **common,
            "single_change": "repeat-factor sampling of train images holding classes 7/32/41",
            "train_args": a2_args,
            "repeat_roster": repeat,
            "success_criterion": (
                "on R3 at conf 0.20: recall of classes 7, 32 and 41 each up by >= 0.05; FP/image "
                "up by no more than 0.03; overall recall >= 0.85; paired group-bootstrap CIs "
                "reported"
            ),
        },
        "A3_schedule_40e_cos": {
            **common,
            "single_change": "epochs 40 and cos_lr True, no repeat factor",
            "train_args": a3_args,
            "success_criterion": (
                "on R3: mAP50-95 not below the pilot reference 0.6261; FP/image compared at the "
                "highest grid confidence whose recall reaches the pilot's 0.8766, against the "
                "pilot's 0.3989; overall recall >= 0.85; paired group-bootstrap CIs reported"
            ),
        },
    }


# ----------------------------------------------------------------------------------- output


def _finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise RuntimeError(f"non-finite number in output at {path}")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise RuntimeError(f"non-string key in output at {path}")
            _finite(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _finite(item, f"{path}[{index}]")


def canonical(document: dict[str, Any]) -> bytes:
    _finite(document)
    return (
        json.dumps(
            document, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def analyse(root: Path, *, rounds: int = BOOTSTRAP_ROUNDS) -> dict[str, Any]:
    """Pure analysis of the pinned evidence; the document carries the pre-analysis pin hashes."""
    pins = verify_pins(root)
    names, ids = class_map(root)
    report = load_report(root)
    labels = load_r3_labels(root)
    groups = load_groups(root, sorted(labels))
    predictions = parse_predictions(read_pinned(root, PREDICTIONS), sorted(labels))
    frames = build_frames(labels, groups, predictions)
    reproduction = reproduce(frames, report, names)
    a0b = a0b_analysis(frames, names, ids, rounds=rounds)
    if rounds == BOOTSTRAP_ROUNDS and (
        a0b["global_grid"][f"{CONF:.2f}"]["bootstrap_95ci"] != reproduction["bootstrap_95ci"]
    ):
        raise RuntimeError("the paired bootstrap does not reproduce metrics.group_bootstrap")
    document = {
        "package": PACKAGE,
        "status": STATUS,
        "boundary": BOUNDARY,
        "schema_version": SCHEMA_VERSION,
        "run": RUN,
        "evidence_pins": pins,
        "validation": {
            "frames": FRAMES,
            "ground_truth": R3_BOXES,
            "label_roster_sha256": R3_LABEL_ROSTER_SHA256,
            "groups": len(set(groups.values())),
            "prediction_rows": PREDICTION_ROWS,
            "max_candidates_per_image": max(len(v) for v in predictions.values()),
        },
        "reproduction_of_d1_vre_r2": reproduction,
        "a0": a0_assessment(report["settings"], prediction_stage="POST_CLASSWISE_NMS"),
        "a0b": a0b,
        "a1": a1_status(),
        "runs": run_specs(a2_repeat_roster(root, ids)),
        "training_authorized": False,
        "test_included": False,
        "sealed_test_accessed": False,
    }
    return document


def publish(out_root: Path, evidence_root: Path, document: dict[str, Any]) -> dict[str, str]:
    """Write the canonical JSON once, after re-verifying that no pinned input changed."""
    if any(_is_test_part(part) for part in OUTPUT.parts):
        raise RuntimeError("refused output under a test path")
    if verify_pins(evidence_root) != document["evidence_pins"]:
        raise RuntimeError("an evidence input changed between preflight and write")
    payload = canonical(document)
    folder = guard(out_root, OUTPUT.parent, directory=True)
    target = folder / OUTPUT.name
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    if sha256_bytes(guard(out_root, OUTPUT).read_bytes()) != sha256_bytes(payload):
        raise RuntimeError("written analysis differs from the canonical payload")
    return {"path": str(OUTPUT), "sha256": sha256_bytes(payload)}


MANIFEST = Path("docs/review/generated/d1_yolo54_improvement_r3_manifest.json")
PACKAGE_FILES = (
    Path("detector/m1/yolo54_improvement_r3.py"),
    Path("detector/tests/test_yolo54_improvement_r3.py"),
    Path("docs/review/d1_yolo54_improvement_r3_contract.md"),
    Path("docs/review/d1_yolo54_improvement_r3_implementation_record.md"),
    Path("docs/review/d1_yolo54_improvement_r3_qa_brief.md"),
    OUTPUT,
)


def write_manifest(out_root: Path) -> dict[str, str]:
    """Pin the package roster and the consumed evidence; never a QA record (it does not exist)."""
    analysis = contract.strict_json(guard(out_root, OUTPUT))
    if any("qa_record" in path.name for path in PACKAGE_FILES):
        raise RuntimeError("the manifest must not pin a QA record")
    document = {
        "package": PACKAGE,
        "status": STATUS,
        "schema_version": SCHEMA_VERSION,
        "files": {
            str(p): sha256_bytes(guard(out_root, p, package_source=True).read_bytes())
            for p in PACKAGE_FILES
        },
        "evidence_root": "the checkout holding the D1-VRE-R2 artifacts (read-only)",
        "evidence_pins": {str(p): h for p, h in sorted(PINNED.items())},
        "analysis_evidence_pins_match": analysis["evidence_pins"]
        == {str(p): h for p, h in sorted(PINNED.items())},
        "training_authorized": False,
        "sealed_test_accessed": False,
    }
    if not document["analysis_evidence_pins_match"]:
        raise RuntimeError("the analysis was built from different evidence pins")
    payload = canonical(document)
    target = guard(out_root, MANIFEST.parent, directory=True) / MANIFEST.name
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
    return {"path": str(MANIFEST), "sha256": sha256_bytes(payload)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "build", "manifest"))
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, default=contract.REPO_ROOT)
    args = parser.parse_args(argv)
    try:
        evidence = args.evidence_root.expanduser().absolute()
        if args.command == "check":
            pins = verify_pins(evidence)
            names, _ids = class_map(evidence)
            labels = load_r3_labels(evidence)
            frames = build_frames(
                labels,
                load_groups(evidence, sorted(labels)),
                parse_predictions(read_pinned(evidence, PREDICTIONS), sorted(labels)),
            )
            result: Any = {
                "pins": len(pins),
                "reproduction": reproduce(frames, load_report(evidence), names),
            }
        elif args.command == "build":
            document = analyse(evidence)
            result = publish(args.out_root.expanduser().absolute(), evidence, document)
        else:
            result = write_manifest(args.out_root.expanduser().absolute())
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
