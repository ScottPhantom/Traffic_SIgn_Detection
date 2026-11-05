"""D1 YOLO54 + CompactCNN R2 classifier fusion R1: pre-registered relabel-only ablation scorer.

Contract ``docs/review/d1_yolo54_classifier_fusion_r1_contract.md`` (``40cbe72f…``), as amended by
Addendum 1 (``fa2ea121…``); Owner authorization ``…_owner_authorization_2026-11-05.md``. This module
is contract §8 step 3. It must pass independent source QA before ``run`` executes once.

Subcommands (run from ``detector/``)::

    uv run python -m m1.classifier_fusion_r1 step0      # arm A only (pilot CSV), no classifier
    uv run python -m m1.classifier_fusion_r1 latency    # print the C3 schedule; measures nothing
    uv run python -m m1.classifier_fusion_r1 run \\
        --source-qa-record docs/review/<record>.md --source-qa-sha256 <hash>
    uv run python -m m1.classifier_fusion_r1 verify     # model-free byte-identical rebuild

Rules bound here (contract section / addendum item / addendum-QA clarification):

* Arm B = arm A with one change: a pilot candidate whose ORIGINAL class ``s`` is a P1–P6 source may
  take the pair target ``t`` iff ``argmax(p) == t and float(p[t]) >= 0.80`` (C5: float32 softmax,
  exact float64 compare, inclusive). No chaining, relabel only, NMS not re-run, boxes/scores/order
  untouched, so TP/FP must stay 547/150 (§2; a deviation is ``INVALID``).
* Crop (§5, C4): the pinned ``evaluate_cascade_b0_r1.crop_prediction`` on a PIL RGB image, after
  NumPy-clipping the raw box; non-finite / non-positive extent or a ``ValueError`` is
  ``crop_invalid`` (class kept, probabilities empty). The scored box stays the raw CSV box.
* Step 0 (§6, C1, Q6): TP 547, FP 150, Σ hits 457, recall == 547/624, FP/image == 150/376 exactly,
  hits 66/18/12/55 (yolo 7/33/42/48) and 14 (yolo 40), common-path mAP within 1e-9.
* Guards G1–G7, G4b and the first-match outcome table (C2); paired group bootstrap (C6, Q3).
* Latency (§6.4, C3, Q1, Q2): counterbalanced AB/BA, 50 warm-up + 300 measured, measured
  iteration ``j`` uses image ``(50 + j) % 376``; a sample is valid iff the timed call returned
  without exception and its duration is finite and > 0 ms.
* Inputs (Q4): only the verified N1 bundle ``tmp/yolo11n_n1_extract_r1`` (regular files). Every
  input path is refused if any component is a symlink or contains ``test``; the R4-export image
  directory (symlinks into ``data/raw/DATASET01``) is not used. The module and its tests are
  hashed through the allow-listed ``_source_file`` at the start of ``run`` (QA R1).
* Before any write, every pin, the module/test SHAs, the classifier and the used bundle members
  are re-verified (QA R2). A post-Step-0 stop is ``INVALID`` with a write-once stop report and no
  result file (QA R4).

Never: training, sealed test, D-05/threshold change, app integration, overwriting an output.
Behaviour output stays simulation only.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import math
import os
import re
import secrets
import shutil
import stat
import sys
import tempfile
import time
import unicodedata
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np

from m1 import contract
from m1 import val_reeval_r2 as vre
from m1.metrics import Frame, iou_matrix, latency_stats, match, operating_point

PACKAGE = "D1-YOLO54-CLASSIFIER-FUSION-R1"
BOUNDARY = "VALIDATION_ONLY_RELABEL_ABLATION_NO_TRAINING_NO_SEALED_TEST_NO_APP_NO_GATE_CHANGE"
REPO_ROOT = contract.REPO_ROOT

# ------------------------------------------------------------------------------------- paths

RUN_DIR = vre.RUN_DIR
PILOT_WEIGHTS = vre.WEIGHTS
PILOT_CSV = RUN_DIR / "d1_vre_r2/predictions_conf0001.csv"
VRE_EVAL = RUN_DIR / "d1_vre_r2/eval_val_vrl_r3_vre_r2.json"
SAHI_LATENCY = RUN_DIR / "sahi_r1/sahi_r1_latency_mps.json"
BUNDLE = Path("tmp/yolo11n_n1_extract_r1")
BUNDLE_DATA = BUNDLE / "data"
BUNDLE_IMAGES = BUNDLE_DATA / "images/val"
BUNDLE_LABELS = BUNDLE_DATA / "labels54/val"
BUNDLE_GROUPS = BUNDLE_DATA / "val_groups.json"
BUNDLE_CSV_MEMBER = "data/yolo54_predictions_val.csv"
CLASSIFIER_DIR = Path(
    "results/experiments/cascade_classifier_improvement_r1/compact_combined_local_r2"
)
CLASSIFIER = CLASSIFIER_DIR / "best.pt"
CLASSIFIER_CONTRACT = CLASSIFIER_DIR / "contract.json"
CLASSIFIER_EPOCH = 18
EVALUATOR = Path("detector/colab/evaluate_cascade_b0_r1.py")
EVALUATOR_RUNNER = Path("detector/colab/run_cascade_b0_r1.py")
CLASS_MAP = Path("docs/review/generated/m1_yolo_classes.csv")
SIGNNAMES = Path("data/processed/dataset01_crops/signnames.csv")
SPLIT_FRAMES = Path("docs/review/generated/wp36_r1_split_frames.csv")
MODULE = Path("detector/m1/classifier_fusion_r1.py")
TESTS = Path("detector/tests/test_classifier_fusion_r1.py")
CONTRACT_DOC = Path("docs/review/d1_yolo54_classifier_fusion_r1_contract.md")
ADDENDUM_DOC = Path("docs/review/d1_yolo54_classifier_fusion_r1_addendum_1.md")
AUTH_DOC = Path("docs/review/d1_yolo54_classifier_fusion_r1_owner_authorization_2026-11-05.md")

OUT_DIR = RUN_DIR / "classifier_fusion_r1"
PREDICTIONS_NAME = "fusion_r1_predictions_conf0001.csv"
PROBS_NAME = "fusion_r1_crop_probs.csv"
EVAL_NAME = "fusion_r1_eval.json"
LATENCY_NAME = "fusion_r1_latency_mps.json"
MANIFEST_NAME = "fusion_r1_manifest.json"
OUTPUT_NAMES = (PREDICTIONS_NAME, PROBS_NAME, EVAL_NAME, LATENCY_NAME, MANIFEST_NAME)
# Written alone (no result file) when the run stops INVALID after Step 0 (QA R4).
STOP_REPORT_NAME = "fusion_r1_stop_report.json"
# The only paths hashed without the ``test``-substring refusal (QA R1); data inputs keep it.
SOURCE_FILES = (MODULE, TESTS)

CONTRACT_SHA256 = "40cbe72ff095b8aea9d2253c02a52c013797b2148febc4bbbd647e68a77c700c"
ADDENDUM_SHA256 = "fa2ea121623a0072256cd56e88ba1d1e60a90cd85a51f0869fa5d70623bdd6e9"
AUTH_SHA256 = "9f8c5f20c4dab52258d64270d490fc720c941bc1478a22550a549560e3556fcd"
BUNDLE_MANIFEST_SHA256 = "8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da"
PILOT_CSV_SHA256 = "87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893"
CLASSIFIER_SHA256 = "d1e69eefce644cdce044017aeb265e2179cbb94eb07a8ecdb114de16930350cc"
IMAGE_ROSTER_SHA256 = "24e2a67d1e176a7e09caf4b1f6daa2bf5240981d00c8e1a535640e6b8066118e"
LABEL_ROSTER_SHA256 = "dc72ebd944a38535d4f766ba4f8babc60cb6732dfcd253ed0e8d79dc86eb8343"

# Every input pin (contract §10 subset that this module reads, plus Addendum 1 §0/§4/§7). The
# runner imported by the pinned evaluator is pinned here as well (implementation-time pin).
PINS: dict[Path, str] = {
    CONTRACT_DOC: CONTRACT_SHA256,
    ADDENDUM_DOC: ADDENDUM_SHA256,
    AUTH_DOC: AUTH_SHA256,
    PILOT_WEIGHTS: "5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633",
    RUN_DIR / "run_contract.json": (
        "9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88"
    ),
    PILOT_CSV: PILOT_CSV_SHA256,
    VRE_EVAL: "559c6c6a78a0d653da09a43bf6dc0663a2dbcb07f6aef4748cade369ef857c87",
    SAHI_LATENCY: "a8b06702cfe50f4956c9b1f118b5b58b5494aa52e218013ba76cc07a43d811b8",
    CLASSIFIER: CLASSIFIER_SHA256,
    CLASSIFIER_CONTRACT: "b659a4fd78901b9f094f5d909b317f7b9b69c7bbfe88083075bdd2ee803ced5a",
    Path("detector/d1_cascade_classifier/model.py"): (
        "fdcbc4156a4bef9b5eed56a8ebc58746408a14f6558cd4b3c38a4e49df47b77a"
    ),
    Path("detector/d1_cascade_classifier/data.py"): (
        "e55fbaddea154131a0ef20f8d2653150b0f2c8eecdc8ff31dbcb16d6a463ed5d"
    ),
    Path("detector/m1/metrics.py"): (
        "d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f"
    ),
    Path("detector/m1/val_reeval_r2.py"): (
        "2a0823faa15f7cb9cecb64a1f21e48e8b5b84f7e7f949683683a6992ee13ccc9"
    ),
    Path("detector/m1/sahi_eval_r1.py"): (
        "2ca327ed2901b03b1c302457c881eac0bdf0018c601ac413f70bee489163ebeb"
    ),
    EVALUATOR: "8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42",
    EVALUATOR_RUNNER: "0ece03891ebe0f8c318efd7a062fdb8d799d4cf9cc357b0cf8840b4103ad876a",
    CLASS_MAP: "7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242",
    SIGNNAMES: "cd885b463109d1bec3169ccb9306c7eb46c9f1c26647b527129e1257281affca",
    Path("data/processed/m1_yolo/data.yaml"): (
        "4cd8303540ecf7bf8ce461b440a07ae35b5ffb047348613c3cdbc8d9c1d78bd0"
    ),
    SPLIT_FRAMES: "8e197d9c7103ac5dc6b7ffc8a3d1aeb30bb6034048d470e4887dd868df95823a",
    BUNDLE / "manifest.json": BUNDLE_MANIFEST_SHA256,
}

# ------------------------------------------------------------------------------ fixed rules

FRAMES, GT_BOXES, GROUPS, CLASSES, PILOT_ROWS = 376, 624, 9, 54, 1999
CONF = 0.20
TAU = 0.80
TAU_GRID = (0.50, 0.95)
ROUNDS, SEED = 1000, 20261018
IMGSZ, NMS_IOU, MAX_DET = 1280, 0.70, 300
OVERLAP_IOU = 0.70
WARMUP, ITERATIONS = 50, 300
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}

# (pair, source yolo_id, target yolo_id); contract §4.1, Addendum 1 §9.
PAIRS: tuple[tuple[str, int, int], ...] = (
    ("P1", 10, 48),
    ("P2", 19, 7),
    ("P3", 40, 42),
    ("P4", 7, 33),
    ("P5", 41, 42),
    ("P6", 12, 8),
)
PAIR_NAMES = tuple(name for name, _, _ in PAIRS)
SOURCE_PAIR = {source: (name, target) for name, source, target in PAIRS}

# yolo_id -> derived key, as bound by contract §3 (plus the G5 classes); checked against the map.
EXPECTED_DERIVED_KEYS = {
    6: "6",
    7: "7",
    8: "8",
    10: "10",
    12: "12",
    19: "17",
    20: "18",
    25: "23",
    33: "32",
    35: "34",
    40: "39",
    41: "40",
    42: "41",
    48: "46",
}

STEP0_REFERENCE: dict[str, Any] = {
    "images": 376,
    "ground_truth": 624,
    "true_positives": 547,
    "false_positives": 150,
    "correct_class_hits": 457,
    "agnostic_recall_fraction": [547, 624],
    "fp_per_image_fraction": [150, 376],
    "per_class_hits_yolo": {"7": 66, "33": 18, "42": 12, "48": 55, "40": 14},
    "map50": 0.8520835680,
    "map50_95": 0.6088678435,
    "map_tolerance": 1e-9,
}

G1_MIN_HITS = 467
G4_MIN_HITS = {7: 66, 33: 18, 42: 12}  # DK 7 / 32 / 41
G4B_MIN_HITS = {40: 14}  # DK 39
G5_DERIVED_KEYS = ("6", "8", "10", "12", "23", "34", "46")
G5_MAX_LOSS = 2
G7_P95_MS = 100.0

GUARD_ORDER = ("S0", "L", "delta_positive", "G1", "G2", "G3", "G4", "G4b", "G5", "G6", "G7")
OUTCOME_ROWS: tuple[tuple[int, str, tuple[str, ...]], ...] = (
    (1, "INVALID", ("S0", "G3", "L")),
    (2, "NO_GO", ("delta_positive", "G4", "G4b", "G5", "G6")),
    (3, "NO_GO_UNCERTAIN", ("G1", "G2")),
    (4, "NO_GO_LATENCY", ("G7",)),
)
GO = "GO_CANDIDATE_FOR_CONFIRMATION"

SIZE_BINS = (
    ("lt16", 0.0, 16.0),
    ("16_32", 16.0, 32.0),
    ("32_64", 32.0, 64.0),
    ("ge64", 64.0, None),
)

FLAGS = {
    "sealed_test_accessed": False,
    "training_authorized": False,
    "app_enable_authorized": False,
    "threshold_lock_written": False,
    "d05_changed": False,
    "push_authorized": False,
    "rerun_after_results_authorized": False,
}
SENSITIVITY_LABEL = "SENSITIVITY_NOT_DECISION"
PILOT_FIELDS = ["stem", "rank", "yolo_id", "conf", "x1", "y1", "x2", "y2"]
PREDICTION_FIELDS = [
    "stem",
    "rank",
    "yolo_id",
    "fused_id",
    "derived_key",
    "fused_derived_key",
    "conf",
    "x1",
    "y1",
    "x2",
    "y2",
    "pair",
    "p_target",
    "p_source",
    "top1_id",
    "relabelled",
    "crop_invalid",
]
PROB_FIELDS = ["stem", "rank", "yolo_id", "derived_key", "pair"] + [
    f"p_{k:02d}" for k in range(CLASSES)
]
VERDICT_RE = re.compile(r"^Verdict:\s*(?:\*\*)?(PASS giới hạn|PASS)(?:\*\*)?(?:\s|$|—|-|\.|,)")


# ------------------------------------------------------------------------- guards and pins


def sha256_file(path: Path) -> str:
    return vre.sha256_file(path)


def sha256_bytes(data: bytes) -> str:
    return vre.sha256_bytes(data)


def guard(repo_root: Path, relative: Path) -> Path:
    """Refuse absolute/escaping paths, any ``test`` component and any symlink in the chain."""
    return vre.guard_path(repo_root, Path(relative))


def regular_file(repo_root: Path, relative: Path) -> Path:
    path = guard(repo_root, relative)
    try:
        info = os.lstat(path)
    except FileNotFoundError as error:
        raise RuntimeError(f"missing input: {relative}") from error
    if not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"refused non-regular input: {relative}")
    return path


def verify_pins(repo_root: Path = REPO_ROOT, pins: dict[Path, str] | None = None) -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative, expected in (PINS if pins is None else pins).items():
        digest = sha256_file(regular_file(repo_root, relative))
        if digest != expected:
            raise RuntimeError(f"pinned fusion R1 input differs: {relative}")
        observed[str(relative)] = digest
    return observed


def _source_file(repo_root: Path, relative: Path) -> Path:
    """The scorer's own module or test file (QA R1). ``guard_path`` refuses every component that
    contains ``test``, which is right for data inputs but refuses ``detector/tests/…``. This
    helper is allow-listed to exactly ``SOURCE_FILES`` and keeps the symlink-component and
    ``S_ISREG`` checks."""
    relative = Path(relative)
    if relative not in SOURCE_FILES:
        raise RuntimeError(f"refused: not an allow-listed fusion R1 source file: {relative}")
    current = Path(repo_root)
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeError(f"refused symlink in source chain: {current}")
    try:
        info = os.lstat(current)
    except FileNotFoundError as error:
        raise RuntimeError(f"missing source file: {relative}") from error
    if not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"refused non-regular source file: {relative}")
    return current


def source_hashes(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    """SHA-256 of the module and its tests; ``run`` captures this before reading any input."""
    return {str(path): sha256_file(_source_file(repo_root, path)) for path in SOURCE_FILES}


def verify_bundle(
    repo_root: Path = REPO_ROOT,
    *,
    full: bool = True,
    manifest_sha256: str = BUNDLE_MANIFEST_SHA256,
) -> dict[str, Any]:
    """Re-verify the N1 bundle manifest (Addendum 1 §7): every member, or only the used ones."""
    manifest_path = regular_file(repo_root, BUNDLE / "manifest.json")
    if sha256_file(manifest_path) != manifest_sha256:
        raise RuntimeError("bundle manifest differs from 8e6ffe77…")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("test_included") is not False
        or manifest.get("sealed_test_accessed") is not False
        or manifest.get("counts", {}).get("val") != {"images": FRAMES, "boxes": GT_BOXES}
    ):
        raise RuntimeError("bundle is not the governed validation-only package")
    for forbidden in ("data/test", "data/images/test", "data/labels/test", "data/labels54/test"):
        if os.path.lexists(repo_root / BUNDLE / forbidden):
            raise RuntimeError(f"refused: bundle holds a test directory: {forbidden}")
    members: dict[str, dict[str, Any]] = manifest["members"]
    if any("test" in part.lower() for name in members for part in Path(name).parts):
        raise RuntimeError("refused: bundle manifest lists a test member")
    used = {
        name
        for name in members
        if name.startswith(("data/images/val/", "data/labels54/val/"))
        or name in ("data/val_groups.json", BUNDLE_CSV_MEMBER)
    }
    checked = 0
    for name in sorted(members if full else used):
        entry = members[name]
        path = regular_file(repo_root, BUNDLE / name)
        if path.stat().st_size != entry["bytes"] or sha256_file(path) != entry["sha256"]:
            raise RuntimeError(f"bundle member differs from its manifest: {name}")
        checked += 1
    if members[BUNDLE_CSV_MEMBER]["sha256"] != PILOT_CSV_SHA256:
        raise RuntimeError("bundle pilot CSV is not byte-identical to the run-directory CSV")
    return {
        "manifest_sha256": manifest_sha256,
        "members_listed": len(members),
        "members_verified": checked,
        "full": full,
    }


def bundle_images(repo_root: Path = REPO_ROOT) -> list[Path]:
    """The 376 validation images; Q4 policy: regular files only, no symlink anywhere (refused)."""
    folder = guard(repo_root, BUNDLE_IMAGES)
    entries = sorted(folder.iterdir())
    images = []
    for entry in entries:
        relative = BUNDLE_IMAGES / entry.name
        path = regular_file(repo_root, relative)
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            raise RuntimeError(f"refused non-image entry in validation images: {entry.name}")
        images.append(path)
    if len(images) != FRAMES:
        raise RuntimeError("validation image roster differs from 376 frames")
    return images


def roster_sha256(paths: Iterable[Path]) -> str:
    """``{file name: SHA-256}`` roster hash, as ``val_reeval_r2.image_roster``."""
    roster = {path.name: sha256_file(path) for path in paths}
    return sha256_bytes(json.dumps(roster, sort_keys=True).encode())


# ------------------------------------------------------------------------------ class maps


def class_names(repo_root: Path = REPO_ROOT) -> list[str]:
    """Derived keys indexed by yolo_id; aligned with ``signnames.csv`` and the contract table."""
    names, _ = vre.class_map(repo_root)
    with regular_file(repo_root, SIGNNAMES).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != CLASSES or any(
        int(row["ClassId"]) != index or row["DerivedKey"] != names[index]
        for index, row in enumerate(rows)
    ):
        raise RuntimeError("classifier class map differs from the YOLO class map")
    for yolo_id, key in EXPECTED_DERIVED_KEYS.items():
        if names[yolo_id] != key:
            raise RuntimeError(f"derived-key translation differs for yolo_id {yolo_id}")
    return names


def g5_yolo_ids(names: Sequence[str]) -> dict[str, int]:
    return {key: names.index(key) for key in G5_DERIVED_KEYS}


# ---------------------------------------------------------------------------------- frames


@dataclass(frozen=True)
class Row:
    """One pilot CSV candidate, in file order; raw strings are kept for exact re-emission."""

    index: int
    stem: str
    rank: int
    yolo_id: int
    conf: float
    box: tuple[float, float, float, float]
    raw: dict[str, str]

    @property
    def key(self) -> tuple[str, int]:
        return (self.stem, self.rank)


@dataclass(frozen=True)
class State:
    frames: list[Frame]  # GT only, in sorted image order
    rows: list[Row]
    names: list[str]
    images: dict[str, Path]
    checks: dict[str, Any]


def read_groups(repo_root: Path, stems: Sequence[str]) -> dict[str, str]:
    groups = json.loads(regular_file(repo_root, BUNDLE_GROUPS).read_text(encoding="utf-8"))
    if set(groups) != set(stems) or len(set(groups.values())) != GROUPS:
        raise RuntimeError("validation group map differs from the 376-frame / 9-group roster")
    with regular_file(repo_root, SPLIT_FRAMES).open(newline="", encoding="utf-8") as handle:
        split = {row["stem"]: row["group_id"] for row in csv.DictReader(handle)}
    if any(split.get(stem) != groups[stem] for stem in stems):
        raise RuntimeError("bundle group map differs from wp36_r1_split_frames.csv")
    return groups


def gt_frames(repo_root: Path, images: Sequence[Path]) -> list[Frame]:
    """GT exactly as ``evaluate_cascade_b0_r1.infer``; images are opened for their size only."""
    from PIL import Image

    stems = [path.stem for path in images]
    if len(set(stems)) != len(stems):
        raise RuntimeError("duplicate image stems")
    groups = read_groups(repo_root, stems)
    blobs: dict[str, bytes] = {}
    frames: list[Frame] = []
    for path in images:
        with Image.open(path) as source:
            width, height = source.size
        label = regular_file(repo_root, BUNDLE_LABELS / f"{path.stem}.txt")
        blobs[label.name] = label.read_bytes()
        gt_classes, gt_boxes = [], []
        for line in blobs[label.name].decode("utf-8").splitlines():
            if not line.strip():
                continue
            cls, cx, cy, w, h = map(float, line.split())
            gt_classes.append(int(cls))
            gt_boxes.append(
                [
                    (cx - w / 2) * width,
                    (cy - h / 2) * height,
                    (cx + w / 2) * width,
                    (cy + h / 2) * height,
                ]
            )
        frames.append(
            Frame(
                path.stem,
                groups[path.stem],
                np.asarray(gt_boxes, dtype=float).reshape(-1, 4),
                np.asarray(gt_classes, dtype=int),
                np.zeros((0, 4)),
                np.zeros(0, dtype=int),
                np.zeros(0),
                width,
                height,
            )
        )
    if vre._r3_roster_hash(blobs) != LABEL_ROSTER_SHA256:
        raise RuntimeError("R3 label roster differs from dc72ebd9…")
    if sum(len(f.gt_boxes) for f in frames) != GT_BOXES:
        raise RuntimeError("validation GT differs from 624 boxes")
    return frames


def parse_pilot_csv(data: bytes, frames: Sequence[Frame]) -> list[Row]:
    """Pilot candidates in file order, validated as ``load_pinned_baseline`` does."""
    size = {f.stem: (f.image_width, f.image_height) for f in frames}
    reader = csv.DictReader(io.StringIO(data.decode("utf-8"), newline=""))
    if reader.fieldnames != PILOT_FIELDS:
        raise RuntimeError("pilot prediction schema differs")
    rows: list[Row] = []
    seen: set[tuple[str, int]] = set()
    for index, raw in enumerate(reader):
        stem = raw["stem"]
        if stem not in size:
            raise RuntimeError("pilot CSV contains a non-validation stem")
        try:
            rank, cls, conf = int(raw["rank"]), int(raw["yolo_id"]), float(raw["conf"])
            box = tuple(float(raw[k]) for k in ("x1", "y1", "x2", "y2"))
        except (TypeError, ValueError) as error:
            raise RuntimeError("pilot CSV contains malformed values") from error
        width, height = size[stem]
        if (
            rank < 0
            or not 0 <= cls < CLASSES
            or not math.isfinite(conf)
            or not 0 <= conf <= 1
            or not all(math.isfinite(v) for v in box)
            or not (0 <= box[0] <= box[2] <= width and 0 <= box[1] <= box[3] <= height)
        ):
            raise RuntimeError("pilot CSV contains an invalid prediction")
        if (stem, rank) in seen:
            raise RuntimeError("pilot CSV repeats a (stem, rank) key")
        seen.add((stem, rank))
        rows.append(Row(index, stem, rank, cls, conf, box, dict(raw)))  # type: ignore[arg-type]
    return rows


def arm_frames(frames: Sequence[Frame], rows: Sequence[Row], classes: Sequence[int]) -> list[Frame]:
    """Attach candidates in CSV order with the given per-row class (same boxes and scores)."""
    if len(classes) != len(rows):
        raise RuntimeError("class vector length differs from the candidate rows")
    by_stem: dict[str, list[tuple[Row, int]]] = {f.stem: [] for f in frames}
    for row, cls in zip(rows, classes, strict=True):
        by_stem[row.stem].append((row, int(cls)))
    return [
        replace(
            f,
            pred_boxes=np.asarray([r.box for r, _ in by_stem[f.stem]], dtype=float).reshape(-1, 4),
            pred_classes=np.asarray([c for _, c in by_stem[f.stem]], dtype=int),
            pred_scores=np.asarray([r.conf for r, _ in by_stem[f.stem]], dtype=float),
        )
        for f in frames
    ]


def load_state(repo_root: Path = REPO_ROOT, *, full_bundle: bool = True) -> State:
    """Verify every pin and the bundle, then rebuild GT frames and pilot candidates. No model."""
    pins = verify_pins(repo_root)
    bundle = verify_bundle(repo_root, full=full_bundle)
    images = bundle_images(repo_root)
    image_roster = roster_sha256(images)
    if image_roster != IMAGE_ROSTER_SHA256:
        raise RuntimeError("validation image roster differs from 24e2a67d…")
    names = class_names(repo_root)
    frames = gt_frames(repo_root, images)
    csv_bytes = regular_file(repo_root, PILOT_CSV).read_bytes()
    if sha256_bytes(csv_bytes) != PILOT_CSV_SHA256:
        raise RuntimeError("pilot CSV differs")
    rows = parse_pilot_csv(csv_bytes, frames)
    if len(rows) != PILOT_ROWS:
        raise RuntimeError("pilot CSV row count differs from 1,999")
    checks = {
        "pins_verified": len(pins),
        "bundle": bundle,
        "image_roster_sha256": image_roster,
        "label_roster_sha256": LABEL_ROSTER_SHA256,
        "pilot_csv_sha256": PILOT_CSV_SHA256,
        "image_source": str(BUNDLE_IMAGES),
        "symlink_policy": "refuse_every_symlink_component",
    }
    return State(frames, rows, names, {p.stem: p for p in images}, checks)


# ------------------------------------------------------------------------- pinned evaluator


def load_evaluator(repo_root: Path = REPO_ROOT) -> Any:
    """Import the pinned common-path evaluator (crop rule + AP) after re-verifying its hash."""
    for relative in (EVALUATOR, EVALUATOR_RUNNER):
        if sha256_file(regular_file(repo_root, relative)) != PINS[relative]:
            raise RuntimeError(f"pinned evaluator source differs: {relative}")
    name = "fusion_r1_pinned_evaluate_cascade_b0_r1"
    if name in sys.modules:
        return sys.modules[name]
    colab = str(repo_root / EVALUATOR.parent)
    if colab not in sys.path:
        sys.path.insert(0, colab)
    spec = importlib.util.spec_from_file_location(name, repo_root / EVALUATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import the pinned evaluator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------------------------- rule F1


def relabel(probabilities: np.ndarray, source: int, tau: float = TAU) -> bool:
    """F1 with C5 semantics: float32 vector, first-index argmax, exact float64 ``>=`` compare."""
    p = np.asarray(probabilities)
    if p.dtype != np.float32 or p.shape != (CLASSES,):
        raise ValueError("F1 needs a float32 54-vector")
    target = SOURCE_PAIR[source][1]
    top1 = int(np.argmax(p))
    return top1 == target and float(p[target]) >= tau


def crop_input(image: Any, raw_box: Sequence[float], crop_fn: Callable[..., np.ndarray]):
    """C4: clip a copy of the raw box, filter, then the pinned crop; ``None`` = crop_invalid."""
    box = np.asarray(raw_box, dtype=np.float64).copy()
    box[[0, 2]] = np.clip(box[[0, 2]], 0, image.width)
    box[[1, 3]] = np.clip(box[[1, 3]], 0, image.height)
    if not np.isfinite(box).all() or box[2] <= box[0] or box[3] <= box[1]:
        return None
    try:
        return crop_fn(image, box)
    except ValueError:
        return None


def classify(model: Any, crops: np.ndarray, device: str) -> np.ndarray:
    """Same tensor ops, in the same order, as ``evaluate_cascade_b0_r1.infer`` (lines 199–203)."""
    import torch

    with torch.inference_mode():
        tensor = torch.from_numpy(crops.transpose(0, 3, 1, 2).copy()).float().to(device) / 255
        probs = torch.softmax(model((tensor - 0.5) / 0.5), 1).cpu().numpy()
    if probs.dtype != np.float32 or probs.shape != (len(crops), CLASSES):
        raise RuntimeError("classifier output is not an (n, 54) float32 softmax")
    return probs


def decide(
    rows: Sequence[Row],
    probs: dict[tuple[str, int], np.ndarray],
    invalid: set[tuple[str, int]],
    tau: float = TAU,
    pairs: Sequence[str] = PAIR_NAMES,
) -> list[int]:
    """Fused class per row. Keys on the ORIGINAL class only, so a relabel is never re-examined."""
    active = set(pairs)
    fused = []
    for row in rows:
        cls = row.yolo_id
        if cls in SOURCE_PAIR:
            if (row.key in probs) == (row.key in invalid):
                raise RuntimeError(
                    f"source candidate needs probabilities xor crop_invalid: {row.key}"
                )
            name, target = SOURCE_PAIR[cls]
            if name in active and row.key in probs and relabel(probs[row.key], cls, tau):
                cls = target
        elif row.key in probs or row.key in invalid:
            raise RuntimeError(f"non-source candidate was cropped: {row.key}")
        fused.append(cls)
    return fused


# --------------------------------------------------------------------------- output tables


def _float_text(value: np.float32) -> str:
    return repr(float(value))


def probs_csv(
    rows: Sequence[Row], probs: dict[tuple[str, int], np.ndarray], names: list[str]
) -> bytes:
    sink = io.StringIO()
    writer = csv.writer(sink, lineterminator="\n")
    writer.writerow(PROB_FIELDS)
    for row in rows:
        if row.key not in probs:
            continue
        p = probs[row.key]
        if p.dtype != np.float32 or p.shape != (CLASSES,):
            raise RuntimeError("probabilities must be float32 54-vectors")
        writer.writerow(
            [row.stem, row.rank, row.yolo_id, names[row.yolo_id], SOURCE_PAIR[row.yolo_id][0]]
            + [_float_text(v) for v in p]
        )
    return sink.getvalue().encode("utf-8")


SOFTMAX_SUM_TOLERANCE = 1e-5


def softmax_ok(p: np.ndarray) -> bool:
    """The softmax predicate of ``parse_probs_csv``: finite, non-negative, sum within 1e-5."""
    return bool(
        np.isfinite(p).all()
        and not (p < 0).any()
        and abs(float(p.astype(np.float64).sum()) - 1.0) <= SOFTMAX_SUM_TOLERANCE
    )


def softmax_violations(probs: dict[tuple[str, int], np.ndarray]) -> list[list[Any]]:
    """Keys whose in-memory probabilities would fail ``parse_probs_csv`` (QA R4)."""
    return sorted(
        [key[0], key[1]]
        for key, p in probs.items()
        if p.dtype != np.float32 or p.shape != (CLASSES,) or not softmax_ok(p)
    )


def parse_probs_csv(data: bytes, rows: Sequence[Row]) -> dict[tuple[str, int], np.ndarray]:
    """Model-free reload; every value must be an exact float32 and each row a softmax."""
    by_key = {row.key: row for row in rows}
    reader = csv.DictReader(io.StringIO(data.decode("utf-8"), newline=""))
    if reader.fieldnames != PROB_FIELDS:
        raise RuntimeError("crop-probability schema differs")
    out: dict[tuple[str, int], np.ndarray] = {}
    order = []
    for raw in reader:
        key = (raw["stem"], int(raw["rank"]))
        row = by_key.get(key)
        if row is None or row.yolo_id not in SOURCE_PAIR or key in out:
            raise RuntimeError(f"crop-probability row is not a unique source candidate: {key}")
        if int(raw["yolo_id"]) != row.yolo_id or raw["pair"] != SOURCE_PAIR[row.yolo_id][0]:
            raise RuntimeError(f"crop-probability row identity differs: {key}")
        values = [float(raw[f"p_{k:02d}"]) for k in range(CLASSES)]
        p = np.asarray(values, dtype=np.float32)
        if any(float(a) != b for a, b in zip(p, values, strict=True)) or not softmax_ok(p):
            raise RuntimeError(f"crop probabilities are not an exact float32 softmax: {key}")
        out[key] = p
        order.append(row.index)
    if order != sorted(order):
        raise RuntimeError("crop-probability rows are not in pilot CSV order")
    return out


def predictions_csv(
    rows: Sequence[Row],
    probs: dict[tuple[str, int], np.ndarray],
    invalid: set[tuple[str, int]],
    fused: Sequence[int],
    names: list[str],
) -> bytes:
    sink = io.StringIO()
    writer = csv.writer(sink, lineterminator="\n")
    writer.writerow(PREDICTION_FIELDS)
    for row, new in zip(rows, fused, strict=True):
        pair = p_target = p_source = top1 = ""
        if row.yolo_id in SOURCE_PAIR:
            pair, target = SOURCE_PAIR[row.yolo_id]
            if row.key in probs:
                p = probs[row.key]
                p_target, p_source = _float_text(p[target]), _float_text(p[row.yolo_id])
                top1 = str(int(np.argmax(p)))
        writer.writerow(
            [
                row.raw["stem"],
                row.raw["rank"],
                row.raw["yolo_id"],
                new,
                names[row.yolo_id],
                names[new],
                row.raw["conf"],
                row.raw["x1"],
                row.raw["y1"],
                row.raw["x2"],
                row.raw["y2"],
                pair,
                p_target,
                p_source,
                top1,
                int(new != row.yolo_id),
                int(row.key in invalid),
            ]
        )
    return sink.getvalue().encode("utf-8")


def canonical(document: dict[str, Any]) -> bytes:
    return (
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")


# ------------------------------------------------------------------------------- statistics


def frame_stats(frames: Sequence[Frame], conf: float = CONF) -> dict[str, np.ndarray]:
    """Per-frame additive counts (identical to ``operating_point`` when summed)."""
    n = len(frames)
    stats = {
        "gt": np.zeros(n),
        "agnostic_hits": np.zeros(n),
        "aware_hits": np.zeros(n),
        "fp": np.zeros(n),
    }
    for i, frame in enumerate(frames):
        agnostic, fps = match(frame, conf, class_aware=False)
        aware, _ = match(frame, conf, class_aware=True)
        stats["gt"][i] = len(frame.gt_boxes)
        stats["agnostic_hits"][i] = agnostic.sum()
        stats["aware_hits"][i] = aware.sum()
        stats["fp"][i] = fps
    return stats


def summarize(stats: dict[str, np.ndarray], index: np.ndarray) -> dict[str, float]:
    gt = stats["gt"][index].sum()
    return {
        "correct_class_recall": stats["aware_hits"][index].sum() / gt,
        "agnostic_recall": stats["agnostic_hits"][index].sum() / gt,
        "fp_per_image": stats["fp"][index].sum() / len(index),
    }


def resample_indices(
    frames: Sequence[Frame], rounds: int = ROUNDS, seed: int = SEED
) -> list[np.ndarray]:
    """C6: ``default_rng(seed)`` and ``rng.choice(sorted(groups), size=len, replace=True)``."""
    groups: dict[str, list[int]] = {}
    for i, frame in enumerate(frames):
        groups.setdefault(frame.group_id, []).append(i)
    names = sorted(groups)
    rng = np.random.default_rng(seed)
    return [
        np.asarray([i for g in rng.choice(names, size=len(names), replace=True) for i in groups[g]])
        for _ in range(rounds)
    ]


def ci95(values: Sequence[float]) -> list[float]:
    return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]


def paired_bootstrap(
    arm_a: Sequence[Frame],
    arm_b: Sequence[Frame],
    samples: Sequence[np.ndarray],
    conf: float = CONF,
) -> dict[str, Any]:
    """Both arms scored on the same resampled frames each round; Δ = B − A."""
    if [f.stem for f in arm_a] != [f.stem for f in arm_b]:
        raise RuntimeError("paired arms are not frame-aligned")
    sa, sb = frame_stats(arm_a, conf), frame_stats(arm_b, conf)
    draws = [(summarize(sa, s), summarize(sb, s)) for s in samples]
    full = np.arange(len(arm_a))
    pa, pb = summarize(sa, full), summarize(sb, full)
    out: dict[str, Any] = {}
    for metric in ("correct_class_recall", "agnostic_recall", "fp_per_image"):
        diffs = [b[metric] - a[metric] for a, b in draws]
        out[metric] = {
            "arm_a": float(pa[metric]),
            "arm_b": float(pb[metric]),
            "delta_b_minus_a": float(pb[metric] - pa[metric]),
            "paired_ci95": ci95(diffs),
            "arm_a_marginal_ci95": ci95([a[metric] for a, _ in draws]),
            "arm_b_marginal_ci95": ci95([b[metric] for _, b in draws]),
            "share_rounds_delta_gt_0": float(np.mean(np.asarray(diffs) > 0)),
        }
    return out


def correct_matrices(frames: Sequence[Frame]) -> list[np.ndarray]:
    """Pinned Ultralytics matcher, exactly as ``evaluate_cascade_b0_r1.average_precision``."""
    from types import SimpleNamespace

    import torch
    from ultralytics.engine.validator import BaseValidator

    validator = SimpleNamespace(iouv=torch.linspace(0.5, 0.95, 10))
    return [
        BaseValidator.match_predictions(
            validator,
            torch.as_tensor(f.pred_classes),
            torch.as_tensor(f.gt_classes),
            torch.as_tensor(iou_matrix(f.gt_boxes, f.pred_boxes)),
        ).numpy()
        for f in frames
    ]


def map_pair(
    frames: Sequence[Frame], correct: Sequence[np.ndarray], index: np.ndarray
) -> tuple[float, float]:
    from ultralytics.utils.metrics import ap_per_class

    target = np.concatenate([frames[i].gt_classes for i in index])
    pred = np.concatenate([frames[i].pred_classes for i in index])
    if not len(target) or not len(pred):
        return 0.0, 0.0
    ap = ap_per_class(
        np.concatenate([correct[i] for i in index]),
        np.concatenate([frames[i].pred_scores for i in index]),
        pred,
        target,
        plot=False,
        names={i: str(i) for i in range(CLASSES)},
    )[5]
    return float(ap[:, 0].mean()), float(ap.mean())


def paired_map_bootstrap(
    arm_a: Sequence[Frame], arm_b: Sequence[Frame], samples: Sequence[np.ndarray]
) -> dict[str, Any]:
    ca, cb = correct_matrices(arm_a), correct_matrices(arm_b)
    full = np.arange(len(arm_a))
    pa, pb = map_pair(arm_a, ca, full), map_pair(arm_b, cb, full)
    draws = [(map_pair(arm_a, ca, s), map_pair(arm_b, cb, s)) for s in samples]
    out: dict[str, Any] = {"label": "REPORTED_NOT_DECISIVE"}
    for k, metric in enumerate(("map50", "map50_95")):
        diffs = [b[k] - a[k] for a, b in draws]
        out[metric] = {
            "arm_a": pa[k],
            "arm_b": pb[k],
            "delta_b_minus_a": pb[k] - pa[k],
            "paired_ci95": ci95(diffs),
        }
    out["note"] = "class set = classes present in each resample (Ultralytics ap_per_class)"
    return out


# --------------------------------------------------------------------------------- scoring


def common_ap(evaluator: Any, frames: Sequence[Frame]) -> dict[str, Any]:
    result = evaluator.average_precision(list(frames))
    return {
        "map50": float(result["map50"]),
        "map50_95": float(result["map50_95"]),
        "per_class_ap50": {str(k): float(v) for k, v in result.get("per_class_ap50", {}).items()},
    }


def point(frames: Sequence[Frame], names: Sequence[str], conf: float = CONF) -> dict[str, Any]:
    op = operating_point(frames, conf)
    return {
        "images": op.images,
        "ground_truth": op.ground_truth,
        "true_positives": op.true_positives,
        "false_positives": op.false_positives,
        "agnostic_recall": op.agnostic_recall,
        "fp_per_image": op.fp_per_image,
        "correct_class_hits": int(sum(op.per_class_hits.values())),
        "correct_class_recall": sum(op.per_class_hits.values()) / op.ground_truth
        if op.ground_truth
        else 0.0,
        "per_class": {
            str(c): {
                "derived_key": names[c],
                "hits": op.per_class_hits[c],
                "support": op.per_class_support[c],
                "recall": op.per_class_recall[c],
            }
            for c in op.per_class_support
        },
    }


def step0_check(state: State, evaluator: Any) -> dict[str, Any]:
    """Arm A from the pilot CSV only. No classifier, no fusion number (contract §6, C1, Q6)."""
    frames_a = arm_frames(state.frames, state.rows, [r.yolo_id for r in state.rows])
    p = point(frames_a, state.names)
    ap = common_ap(evaluator, frames_a)
    ref = STEP0_REFERENCE
    hits = {key: p["per_class"].get(key, {}).get("hits") for key in ref["per_class_hits_yolo"]}
    checks = {
        "images": p["images"] == ref["images"],
        "ground_truth": p["ground_truth"] == ref["ground_truth"],
        "true_positives": p["true_positives"] == ref["true_positives"],
        "false_positives": p["false_positives"] == ref["false_positives"],
        "correct_class_hits": p["correct_class_hits"] == ref["correct_class_hits"],
        "agnostic_recall_exact_547_over_624": p["agnostic_recall"] == 547 / 624,
        "fp_per_image_exact_150_over_376": p["fp_per_image"] == 150 / 376,
        "per_class_hits": hits == ref["per_class_hits_yolo"],
        "map50": abs(ap["map50"] - ref["map50"]) <= ref["map_tolerance"],
        "map50_95": abs(ap["map50_95"] - ref["map50_95"]) <= ref["map_tolerance"],
    }
    return {
        "label": "ARM_A_PILOT_ONLY_NO_FUSION",
        "passed": all(checks.values()),
        "checks": checks,
        "observed": {
            "images": p["images"],
            "ground_truth": p["ground_truth"],
            "true_positives": p["true_positives"],
            "false_positives": p["false_positives"],
            "correct_class_hits": p["correct_class_hits"],
            "agnostic_recall": p["agnostic_recall"],
            "fp_per_image": p["fp_per_image"],
            "per_class_hits_yolo": hits,
            "per_class_hits_derived_key": {state.names[int(k)]: v for k, v in hits.items()},
            "map50": ap["map50"],
            "map50_95": ap["map50_95"],
        },
        "reference": ref,
    }


def assign_outcome(flags: dict[str, bool]) -> tuple[str, int, list[str]]:
    """Addendum 1 §2 first-match table; returns (outcome, row, every failing condition)."""
    if set(flags) != set(GUARD_ORDER) or any(not isinstance(v, bool) for v in flags.values()):
        raise ValueError("outcome needs exactly the boolean conditions " + ", ".join(GUARD_ORDER))
    failed = [key for key in GUARD_ORDER if not flags[key]]
    for row, outcome, keys in OUTCOME_ROWS:
        if any(not flags[key] for key in keys):
            return outcome, row, failed
    return GO, 5, failed


def help_harm(arm_a: Sequence[Frame], arm_b: Sequence[Frame], conf: float = CONF) -> dict[str, Any]:
    """Per-GT class-aware match change at ``conf``: help = miss→hit, harm = hit→miss."""
    total = {"help": 0, "harm": 0}
    bins = {name: {"help": 0, "harm": 0, "support": 0} for name, _, _ in SIZE_BINS}
    for fa, fb in zip(arm_a, arm_b, strict=True):
        aware_a, _ = match(fa, conf, class_aware=True)
        aware_b, _ = match(fb, conf, class_aware=True)
        for size, a, b in zip(gt_sizes(fa), aware_a, aware_b, strict=True):
            name = size_bin(size)
            bins[name]["support"] += 1
            if b and not a:
                total["help"] += 1
                bins[name]["help"] += 1
            elif a and not b:
                total["harm"] += 1
                bins[name]["harm"] += 1
    return {**total, "by_gt_size_bin": bins}


def gt_sizes(frame: Frame) -> np.ndarray:
    w = frame.gt_boxes[:, 2] - frame.gt_boxes[:, 0]
    h = frame.gt_boxes[:, 3] - frame.gt_boxes[:, 1]
    return np.sqrt(np.clip(w, 0, None) * np.clip(h, 0, None))


def size_bin(size: float) -> str:
    for name, low, high in SIZE_BINS:
        if size >= low and (high is None or size < high):
            return name
    raise ValueError("size outside every bin")


def size_recall(frames: Sequence[Frame], conf: float = CONF) -> dict[str, dict[str, Any]]:
    out = {name: {"support": 0, "correct_class": 0} for name, _, _ in SIZE_BINS}
    for frame in frames:
        aware, _ = match(frame, conf, class_aware=True)
        for size, hit in zip(gt_sizes(frame), aware, strict=True):
            out[size_bin(size)]["support"] += 1
            out[size_bin(size)]["correct_class"] += int(hit)
    return out


def same_class_overlaps(
    frames: Sequence[Frame], relabelled: Sequence[np.ndarray], conf: float
) -> int:
    """New same-class pairs at IoU ≥ 0.70 that involve a relabelled box (§4.2 item 5)."""
    count = 0
    for frame, moved in zip(frames, relabelled, strict=True):
        keep = frame.pred_scores >= conf
        boxes, classes, flag = frame.pred_boxes[keep], frame.pred_classes[keep], moved[keep]
        ious = iou_matrix(boxes, boxes)
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if classes[i] == classes[j] and (flag[i] or flag[j]) and ious[i, j] >= OVERLAP_IOU:
                    count += 1
    return count


def guards(
    arm_a: dict[str, Any],
    arm_b: dict[str, Any],
    boot: dict[str, Any],
    ap_a: dict[str, Any],
    ap_b: dict[str, Any],
    latency: dict[str, Any],
    names: Sequence[str],
    step0_passed: bool,
) -> dict[str, Any]:
    def hits(arm: dict[str, Any], cls: int) -> int:
        return int(arm["per_class"].get(str(cls), {}).get("hits", 0))

    delta_hits = arm_b["correct_class_hits"] - arm_a["correct_class_hits"]
    g4 = {
        str(c): {
            "derived_key": names[c],
            "arm_a": hits(arm_a, c),
            "arm_b": hits(arm_b, c),
            "minimum": m,
            "passed": hits(arm_b, c) >= m,
        }
        for c, m in G4_MIN_HITS.items()
    }
    g4b = {
        str(c): {
            "derived_key": names[c],
            "arm_a": hits(arm_a, c),
            "arm_b": hits(arm_b, c),
            "minimum": m,
            "passed": hits(arm_b, c) >= m,
        }
        for c, m in G4B_MIN_HITS.items()
    }
    g5: dict[str, Any] = {}
    for key, cls in g5_yolo_ids(names).items():
        support = int(arm_a["per_class"].get(str(cls), {}).get("support", 0))
        if support == 0:
            raise RuntimeError(f"G5 class DK {key} has no validation support")
        reference = (
            contract.GATES["critical_class_recall"]
            if key in contract.CRITICAL_KEYS
            else contract.GATES["other_class_recall"]
        )
        ha, hb = hits(arm_a, cls), hits(arm_b, cls)
        meets_a, meets_b = ha / support >= reference, hb / support >= reference
        g5[str(cls)] = {
            "derived_key": key,
            "support": support,
            "support_ge_20": support >= contract.GATES["min_support_for_class_gate"],
            "arm_a": ha,
            "arm_b": hb,
            "loss": ha - hb,
            "d05_reference": reference,
            "meets_reference_a": meets_a,
            "meets_reference_b": meets_b,
            "passed": (ha - hb) <= G5_MAX_LOSS and (meets_b or not meets_a),
        }
    lower = boot["correct_class_recall"]["paired_ci95"][0]
    flags = {
        "S0": bool(step0_passed),
        "L": bool(latency["L"]),
        "delta_positive": delta_hits > 0,
        "G1": arm_b["correct_class_hits"] >= G1_MIN_HITS,
        "G2": lower > 0,
        "G3": arm_b["false_positives"] <= STEP0_REFERENCE["false_positives"]
        and arm_b["true_positives"] == STEP0_REFERENCE["true_positives"]
        and arm_b["false_positives"] == arm_a["false_positives"]
        and arm_b["true_positives"] == arm_a["true_positives"],
        "G4": all(v["passed"] for v in g4.values()),
        "G4b": all(v["passed"] for v in g4b.values()),
        "G5": all(v["passed"] for v in g5.values()),
        "G6": ap_b["map50"] - ap_a["map50"] >= 0 and ap_b["map50_95"] - ap_a["map50_95"] >= 0,
        "G7": bool(latency["L"]) and latency["arm_b"]["p95_ms"] <= G7_P95_MS,
    }
    outcome, row, failed = assign_outcome(flags)
    return {
        "flags": flags,
        "failed_guards": failed,
        "outcome": outcome,
        "outcome_row": row,
        "detail": {
            "delta_correct_class_hits": delta_hits,
            "G1_minimum_hits": G1_MIN_HITS,
            "G2_paired_ci95": boot["correct_class_recall"]["paired_ci95"],
            "G3": {
                "tp_a": arm_a["true_positives"],
                "tp_b": arm_b["true_positives"],
                "fp_a": arm_a["false_positives"],
                "fp_b": arm_b["false_positives"],
            },
            "G4": g4,
            "G4b": g4b,
            "G5": g5,
            "G6": {
                "delta_map50": ap_b["map50"] - ap_a["map50"],
                "delta_map50_95": ap_b["map50_95"] - ap_a["map50_95"],
            },
            "G7": {
                "arm_b_p95_ms": latency["arm_b"]["p95_ms"] if latency["L"] else None,
                "maximum_ms": G7_P95_MS,
            },
        },
    }


# --------------------------------------------------------------------------------- latency


def latency_schedule(n_images: int, warmup: int = WARMUP, iterations: int = ITERATIONS):
    """C3 + Q2: (phase, iteration, image index, order); measured j uses image (warmup+j) % n."""
    plan = []
    for phase, count, offset in (("warmup", warmup, 0), ("measured", iterations, warmup)):
        for j in range(count):
            plan.append((phase, j, (offset + j) % n_images, "AB" if j % 2 == 0 else "BA"))
    return plan


def latency_protocol(
    images: Sequence[Path],
    arm_a: Callable[[Path], Any],
    arm_b: Callable[[Path], Any],
    *,
    sync: Callable[[], None],
    clock: Callable[[], float] = time.perf_counter,
    warmup: int = WARMUP,
    iterations: int = ITERATIONS,
) -> dict[str, Any]:
    """Counterbalanced within-iteration timing; each arm's span includes its own image read."""
    arms = {"A": arm_a, "B": arm_b}
    samples: list[dict[str, Any]] = []
    warmup_errors = 0
    for phase, j, index, order in latency_schedule(len(images), warmup, iterations):
        path = images[index]
        for position, arm in zip(("first", "second"), order, strict=True):
            error, ms = None, None
            try:
                start = clock()
                arms[arm](path)
                sync()
                ms = (clock() - start) * 1000.0
            except Exception as exc:  # noqa: BLE001 - recorded, makes the sample invalid (Q1)
                error = f"{type(exc).__name__}: {exc}"
            valid = error is None and ms is not None and math.isfinite(ms) and ms > 0
            if phase == "warmup":
                warmup_errors += int(not valid)
                continue
            samples.append(
                {
                    "iteration": j,
                    "image_index": index,
                    "image": path.name,
                    "order": order,
                    "position": position,
                    "arm": arm,
                    "ms": ms if (ms is not None and math.isfinite(ms)) else None,
                    "valid": bool(valid),
                    "error": error,
                }
            )
    return {"completed": True, "samples": samples, "warmup_invalid": warmup_errors}


def summarize_latency(doc: dict[str, Any]) -> dict[str, Any]:
    """Model-free statistics from the raw samples; L per Addendum 1 §2 with Q1 validity."""
    samples = doc.get("samples", []) if doc.get("completed") else []
    out: dict[str, Any] = {}
    valid_all = True
    for arm in ("A", "B"):
        rows = [s for s in samples if s["arm"] == arm]
        good = [s for s in rows if s["valid"] and s["ms"] is not None and s["ms"] > 0]
        valid_all &= len(rows) == ITERATIONS and len(good) == ITERATIONS
        entry: dict[str, Any] = {"samples": len(rows), "valid_samples": len(good)}
        if good:
            entry.update(latency_stats([s["ms"] for s in good]))
            entry["by_position_diagnostic"] = {
                pos: latency_stats([s["ms"] for s in good if s["position"] == pos])
                for pos in ("first", "second")
                if any(s["position"] == pos for s in good)
            }
        out[f"arm_{arm.lower()}"] = entry
    orders = [s["order"] for s in samples if s["arm"] == "A"]
    balanced = orders.count("AB") == ITERATIONS // 2 and orders.count("BA") == ITERATIONS // 2
    out["L"] = bool(doc.get("completed")) and valid_all and balanced
    out["counterbalanced_ab_ba"] = [orders.count("AB"), orders.count("BA")]
    if out["L"]:
        out["delta_p50_ms"] = out["arm_b"]["p50_ms"] - out["arm_a"]["p50_ms"]
        out["delta_p95_ms"] = out["arm_b"]["p95_ms"] - out["arm_a"]["p95_ms"]
    return out


def _read_rgb(path: Path) -> Any:
    from PIL import Image

    with Image.open(path) as source:
        return source.convert("RGB")


def measure_latency(repo_root: Path, state: State) -> dict[str, Any]:
    """Live MPS arm (authorization §3.B). Only ever called from ``run`` after Step 0 passed."""
    images = [state.images[f.stem] for f in state.frames]
    base: dict[str, Any] = {
        "package": PACKAGE,
        "protocol": "SAHI R1 §1.5 setup plus order control (Addendum 1 §3)",
        "device": "mps",
        "batch_images": 1,
        "warmup": WARMUP,
        "iterations": ITERATIONS,
        "conf": CONF,
        "iou": NMS_IOU,
        "imgsz": IMGSZ,
        "max_det": MAX_DET,
        "measured_image_index": "(warmup + j) % 376 (continues the cycle, as SAHI R1)",
        "valid_sample": "returned without exception, finite and > 0 ms (Q1)",
        "image_roster_sha256": state.checks["image_roster_sha256"],
        "timed_sequence_sha256": sha256_bytes(
            json.dumps(
                [[p, j, images[i].name, o] for p, j, i, o in latency_schedule(len(images))]
            ).encode()
        ),
        **FLAGS,
    }
    try:
        import torch
        from ultralytics import YOLO

        contract.bind_run_weights(str(repo_root / PILOT_WEIGHTS))
        contract.disable_telemetry()
        evaluator = load_evaluator(repo_root)
        env = contract.environment()
        sahi_env = json.loads(regular_file(repo_root, SAHI_LATENCY).read_text())["environment"]
        base["environment"] = env
        base["versions_match_sahi_r1"] = (
            env["torch"] == sahi_env["torch"] and env["ultralytics"] == sahi_env["ultralytics"]
        )
        with tempfile.TemporaryDirectory(prefix="cpv301-fusion-r1-lat-") as directory:
            weight_copy = Path(directory) / "best.pt"
            shutil.copyfile(regular_file(repo_root, PILOT_WEIGHTS), weight_copy)
            if sha256_file(weight_copy) != PINS[PILOT_WEIGHTS]:
                raise RuntimeError("private pilot weight copy differs")
            yolo = YOLO(str(weight_copy))
            classifier = load_classifier(repo_root, "mps")

            def predict(image: Any) -> Any:
                bgr = np.ascontiguousarray(np.asarray(image)[..., ::-1])
                return yolo.predict(
                    source=bgr,
                    conf=CONF,
                    iou=NMS_IOU,
                    imgsz=IMGSZ,
                    device="mps",
                    max_det=MAX_DET,
                    verbose=False,
                )[0]

            def arm_a(path: Path) -> None:
                predict(_read_rgb(path))

            def arm_b(path: Path) -> list[int]:
                image = _read_rgb(path)
                result = predict(image)
                boxes = result.boxes.xyxy.cpu().numpy().astype(float).reshape(-1, 4)
                classes = result.boxes.cls.cpu().numpy().astype(int)
                fused = classes.tolist()
                crops, where = [], []
                for i, cls in enumerate(classes.tolist()):
                    if cls in SOURCE_PAIR:
                        crop = crop_input(image, boxes[i], evaluator.crop_prediction)
                        if crop is not None:
                            crops.append(crop)
                            where.append(i)
                if crops:
                    probs = classify(classifier, np.stack(crops), "mps")
                    for i, p in zip(where, probs, strict=True):
                        if relabel(p, int(classes[i]), TAU):
                            fused[i] = SOURCE_PAIR[int(classes[i])][1]
                return fused

            base.update(latency_protocol(images, arm_a, arm_b, sync=torch.mps.synchronize))
    except Exception as exc:  # noqa: BLE001 - L false -> INVALID (Addendum 1 §2), still recorded
        base.setdefault("samples", [])
        base["completed"] = False
        base["error"] = f"{type(exc).__name__}: {exc}"
    return base


# ------------------------------------------------------------------------------ classifier


def load_classifier(repo_root: Path, device: str) -> Any:
    """``torch.load(weights_only=True)`` with the SHA-256 re-verified before and after (§3)."""
    import torch

    from d1_cascade_classifier.model import CompactCNN

    path = regular_file(repo_root, CLASSIFIER)
    if sha256_file(path) != CLASSIFIER_SHA256:
        raise RuntimeError("classifier best.pt differs before load")
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if sha256_file(path) != CLASSIFIER_SHA256:
        raise RuntimeError("classifier best.pt differs after load")
    config = json.loads(regular_file(repo_root, CLASSIFIER_CONTRACT).read_text(encoding="utf-8"))
    if payload.get("epoch") != CLASSIFIER_EPOCH or payload.get("config") != config:
        raise RuntimeError(
            "classifier payload epoch/config differs from the pinned R2 combined run"
        )
    model = CompactCNN()
    model.load_state_dict(payload["model"], strict=True)
    return model.to(device).eval()


CropPlan = tuple[dict[str, tuple[list[tuple[str, int]], np.ndarray]], set[tuple[str, int]]]


def crop_plan(
    state: State,
    crop_fn: Callable[..., np.ndarray],
    image_loader: Callable[[Path], Any] = _read_rgb,
) -> CropPlan:
    """C4 crop of every source-class candidate (all scores), computed once and model-free.
    ``run`` builds it before any classifier is loaded and feeds the same plan to the CPU and
    MPS passes, so the two crop sets are identical by construction (QA R4)."""
    by_stem: dict[str, list[Row]] = {}
    for row in state.rows:
        if row.yolo_id in SOURCE_PAIR:
            by_stem.setdefault(row.stem, []).append(row)
    crops_by_stem: dict[str, tuple[list[tuple[str, int]], np.ndarray]] = {}
    invalid: set[tuple[str, int]] = set()
    for frame in state.frames:
        rows = by_stem.get(frame.stem)
        if not rows:
            continue
        image = image_loader(state.images[frame.stem])
        crops, keys = [], []
        for row in rows:
            crop = crop_input(image, row.box, crop_fn)
            if crop is None:
                invalid.add(row.key)
            else:
                crops.append(crop)
                keys.append(row.key)
        if crops:
            crops_by_stem[frame.stem] = (keys, np.stack(crops))
    return crops_by_stem, invalid


def classify_candidates(
    state: State,
    model: Any,
    device: str,
    crop_fn: Callable[..., np.ndarray] | None = None,
    image_loader: Callable[[Path], Any] = _read_rgb,
    *,
    plan: CropPlan | None = None,
) -> tuple[dict[tuple[str, int], np.ndarray], set[tuple[str, int]]]:
    """Classify every cropped source-class candidate with one forward per image."""
    if plan is None:
        if crop_fn is None:
            raise ValueError("classify_candidates needs a crop function or a crop plan")
        plan = crop_plan(state, crop_fn, image_loader)
    crops_by_stem, invalid = plan
    probs: dict[tuple[str, int], np.ndarray] = {}
    for frame in state.frames:
        entry = crops_by_stem.get(frame.stem)
        if entry is None:
            continue
        keys, crops = entry
        for key, p in zip(keys, classify(model, crops, device), strict=True):
            probs[key] = p
    return probs, set(invalid)


def precheck_g5_support(state: State) -> dict[str, int]:
    """Model-free pre-check of the G5 zero-support raise in ``guards`` (QA R4). The support
    there is arm A's per-class GT count, which depends only on GT, so it is known here."""
    support: dict[str, int] = {}
    for key, cls in g5_yolo_ids(state.names).items():
        support[key] = int(sum(int((f.gt_classes == cls).sum()) for f in state.frames))
        if support[key] == 0:
            raise RuntimeError(f"refused: G5 class DK {key} has no validation support")
    return support


@contextmanager
def deterministic_cpu() -> Iterator[None]:
    """§5: one thread and deterministic algorithms for the CPU verdict pass only; restored after
    so the MPS recompute and the latency arm run under the SAHI R1 defaults."""
    import torch

    threads, deterministic = torch.get_num_threads(), torch.are_deterministic_algorithms_enabled()
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    try:
        yield
    finally:
        torch.use_deterministic_algorithms(deterministic)
        torch.set_num_threads(threads)


def latency_preflight(repo_root: Path) -> dict[str, Any]:
    """Checks that need no inference, done before Step 0 so a broken environment refuses the run
    instead of consuming it (an unmeasurable latency arm would make the run ``INVALID``)."""
    import torch

    if not torch.backends.mps.is_available():
        raise RuntimeError("refused: MPS is unavailable for the latency arm and the recompute")
    binding = contract.bind_run_weights(str(repo_root / PILOT_WEIGHTS))
    env = contract.environment()
    sahi_env = json.loads(regular_file(repo_root, SAHI_LATENCY).read_text())["environment"]
    return {
        "run_registry_sha256": binding.get("run_registry_sha256"),
        "torch": env["torch"],
        "ultralytics": env["ultralytics"],
        "versions_match_sahi_r1": env["torch"] == sahi_env["torch"]
        and env["ultralytics"] == sahi_env["ultralytics"],
    }


# -------------------------------------------------------------------------------- evaluate


def build_eval(
    state: State,
    evaluator: Any,
    probs: dict[tuple[str, int], np.ndarray],
    invalid: set[tuple[str, int]],
    latency_doc: dict[str, Any],
    mps_relabel_rows: Sequence[Sequence[Any]],
    step0: dict[str, Any],
    *,
    rounds: int = ROUNDS,
    pred_bytes: bytes,
    probs_bytes: bytes,
) -> dict[str, Any]:
    """Every §6 metric from the frames, the crop probabilities and the two measured inputs."""
    names, rows = state.names, state.rows
    original = [r.yolo_id for r in rows]
    fused = decide(rows, probs, invalid, TAU)
    frames_a = arm_frames(state.frames, rows, original)
    frames_b = arm_frames(state.frames, rows, fused)
    arm_a, arm_b = point(frames_a, names), point(frames_b, names)
    ap_a, ap_b = common_ap(evaluator, frames_a), common_ap(evaluator, frames_b)
    samples = resample_indices(frames_a, rounds, SEED)
    boot = paired_bootstrap(frames_a, frames_b, samples)
    latency = summarize_latency(latency_doc)
    g = guards(arm_a, arm_b, boot, ap_a, ap_b, latency, names, step0["passed"])

    moved = {r.key for r, f in zip(rows, fused, strict=True) if f != r.yolo_id}
    per_pair: dict[str, Any] = {}
    for name, source, target in PAIRS:
        pair_rows = [r for r in rows if r.yolo_id == source]
        only = decide(rows, probs, invalid, TAU, pairs=(name,))
        hh = help_harm(frames_a, arm_frames(state.frames, rows, only))
        per_pair[name] = {
            "source_yolo_id": source,
            "source_derived_key": names[source],
            "target_yolo_id": target,
            "target_derived_key": names[target],
            "candidates_all_scores": len(pair_rows),
            "candidates_conf_ge_020": sum(r.conf >= CONF for r in pair_rows),
            "cropped": sum(r.key in probs for r in pair_rows),
            "crop_invalid": sum(r.key in invalid for r in pair_rows),
            "relabelled_all_scores": sum(r.key in moved for r in pair_rows),
            "relabelled_conf_ge_020": sum(r.key in moved and r.conf >= CONF for r in pair_rows),
            "isolated_help": hh["help"],
            "isolated_harm": hh["harm"],
        }
    box_bins = {name: {"all_scores": 0, "conf_ge_020": 0} for name, _, _ in SIZE_BINS}
    for r in rows:
        if r.key in moved:
            name = size_bin(math.sqrt(max(r.box[2] - r.box[0], 0) * max(r.box[3] - r.box[1], 0)))
            box_bins[name]["all_scores"] += 1
            box_bins[name]["conf_ge_020"] += int(r.conf >= CONF)
    flags_by_frame = []
    by_stem: dict[str, list[bool]] = {f.stem: [] for f in state.frames}
    for r in rows:
        by_stem[r.stem].append(r.key in moved)
    for f in state.frames:
        flags_by_frame.append(np.asarray(by_stem[f.stem], dtype=bool))
    cpu_relabel = sorted([list(k) for k in moved])
    mps_relabel = sorted([[str(s), int(k)] for s, k in mps_relabel_rows])
    cpu_set = {tuple(k) for k in cpu_relabel}
    mps_set = {tuple(k) for k in mps_relabel}
    if not mps_set <= set(probs):
        raise RuntimeError("MPS relabel rows must be cropped source candidates")

    sensitivity: dict[str, Any] = {"label": SENSITIVITY_LABEL, "tau_grid": {}, "leave_one_out": {}}

    def variant(classes: list[int]) -> dict[str, Any]:
        fb = arm_frames(state.frames, rows, classes)
        pb, apb = point(fb, names), common_ap(evaluator, fb)
        guard_classes = sorted({*G4_MIN_HITS, *G4B_MIN_HITS, *g5_yolo_ids(names).values()})
        return {
            "label": SENSITIVITY_LABEL,
            "relabelled_all_scores": sum(
                c != r.yolo_id for c, r in zip(classes, rows, strict=True)
            ),
            "correct_class_hits": pb["correct_class_hits"],
            "delta_correct_class_hits": pb["correct_class_hits"] - arm_a["correct_class_hits"],
            "true_positives": pb["true_positives"],
            "false_positives": pb["false_positives"],
            "guard_class_hits": {
                str(c): pb["per_class"].get(str(c), {}).get("hits", 0) for c in guard_classes
            },
            "delta_map50": apb["map50"] - ap_a["map50"],
            "delta_map50_95": apb["map50_95"] - ap_a["map50_95"],
        }

    for tau in TAU_GRID:
        sensitivity["tau_grid"][repr(tau)] = variant(decide(rows, probs, invalid, tau))
    for name in PAIR_NAMES:
        keep = tuple(p for p in PAIR_NAMES if p != name)
        sensitivity["leave_one_out"][f"without_{name}"] = variant(
            decide(rows, probs, invalid, TAU, pairs=keep)
        )

    per_class_ap = {
        c: {
            "derived_key": names[int(c)],
            "arm_a": ap_a["per_class_ap50"].get(c),
            "arm_b": ap_b["per_class_ap50"].get(c),
        }
        for c in sorted(set(ap_a["per_class_ap50"]) | set(ap_b["per_class_ap50"]), key=int)
    }
    return {
        "package": PACKAGE,
        "boundary": BOUNDARY,
        "split": "val",
        "frames": FRAMES,
        "gt_boxes": GT_BOXES,
        "groups": GROUPS,
        "flags": FLAGS,
        "rule": {
            "pairs": [
                {
                    "pair": n,
                    "source_yolo_id": s,
                    "source_derived_key": names[s],
                    "target_yolo_id": t,
                    "target_derived_key": names[t],
                }
                for n, s, t in PAIRS
            ],
            "tau": TAU,
            "comparison": "top1 == target and float(float32 p[target]) >= 0.80 (inclusive, C5)",
            "chaining": False,
            "relabel_only": True,
            "nms_rerun": False,
            "verdict_device": "cpu_float32",
        },
        "inputs": {
            "pins": {str(k): v for k, v in sorted(PINS.items(), key=lambda kv: str(kv[0]))},
            "image_roster_sha256": IMAGE_ROSTER_SHA256,
            "label_roster_sha256": LABEL_ROSTER_SHA256,
            "predictions_csv_sha256": sha256_bytes(pred_bytes),
            "crop_probs_csv_sha256": sha256_bytes(probs_bytes),
            "latency_json_sha256": sha256_bytes(canonical(latency_doc)),
        },
        "step0": step0,
        "arm_a": arm_a,
        "arm_b": arm_b,
        "primary_endpoint": {
            "name": "correct-class recall at conf 0.20",
            "arm_a": arm_a["correct_class_recall"],
            "arm_b": arm_b["correct_class_recall"],
            "delta_b_minus_a": arm_b["correct_class_recall"] - arm_a["correct_class_recall"],
            "delta_hits": arm_b["correct_class_hits"] - arm_a["correct_class_hits"],
        },
        "bootstrap": {
            "rounds": rounds,
            "seed": SEED,
            "unit": "intact D-02 validation group (9), resampled with replacement, same draws "
            "for both arms",
            "interval": "95% percentile (numpy linear)",
            "fixed_conf_020": boot,
        },
        "exact_class_ap_common_path": {
            "arm_a": {"map50": ap_a["map50"], "map50_95": ap_a["map50_95"]},
            "arm_b": {"map50": ap_b["map50"], "map50_95": ap_b["map50_95"]},
            "delta_map50": ap_b["map50"] - ap_a["map50"],
            "delta_map50_95": ap_b["map50_95"] - ap_a["map50_95"],
            "paired_bootstrap": paired_map_bootstrap(frames_a, frames_b, samples),
            "per_class_ap50": per_class_ap,
        },
        "latency": latency,
        "guards": g,
        "outcome": g["outcome"],
        "outcome_row": g["outcome_row"],
        "failed_guards": g["failed_guards"],
        "reported": {
            "per_pair": per_pair,
            "help_harm_total_conf_020": help_harm(frames_a, frames_b),
            "relabels_by_box_size_bin": box_bins,
            "size_bins_correct_class": {
                "arm_a": size_recall(frames_a),
                "arm_b": size_recall(frames_b),
            },
            "crop_invalid": len(invalid),
            "cropped": len(probs),
            "same_class_overlaps_iou_070": {
                "all_scores": same_class_overlaps(frames_b, flags_by_frame, 0.0),
                "conf_ge_020": same_class_overlaps(frames_b, flags_by_frame, CONF),
            },
        },
        "cpu_mps": {
            "mps_relabel_rows": mps_relabel,
            "cpu_relabel_count": len(cpu_set),
            "mps_relabel_count": len(mps_set),
            "differences": sorted([list(k) for k in cpu_set ^ mps_set]),
            "note": "verdict uses CPU only; MPS rows are a measured input carried into verify",
        },
        "sensitivity": sensitivity,
        "claim_scope": (
            "in-sample validation ablation on frames reused for many selections (contract §7, "
            "Addendum 1 §8); a GO is only a candidate, never a D-05 pass, threshold lock or app "
            "decision; behaviour output is simulation only"
        ),
    }


# ------------------------------------------------------------------------------ write-once


def check_source_qa(
    repo_root: Path, record: str | None, expected_sha256: str | None
) -> dict[str, str]:
    """Refuse unless a pinned record has exactly one PASS / PASS giới hạn verdict line that
    quotes this module's, the contract's and the addendum's SHA-256."""
    if not record or not expected_sha256:
        raise RuntimeError("refused: run needs --source-qa-record and --source-qa-sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise RuntimeError("refused: --source-qa-sha256 must be 64 lowercase hex digits")
    path = regular_file(repo_root, Path(record))
    data = path.read_bytes()
    if sha256_bytes(data) != expected_sha256:
        raise RuntimeError("refused: source-QA record SHA-256 differs from --source-qa-sha256")
    text = unicodedata.normalize("NFC", data.decode("utf-8"))
    verdicts = [line.strip() for line in text.splitlines() if line.strip().startswith("Verdict:")]
    if len(verdicts) != 1 or not VERDICT_RE.match(verdicts[0]):
        raise RuntimeError("refused: the source-QA record needs one PASS / PASS giới hạn verdict")
    required = {
        "module": sha256_file(regular_file(repo_root, MODULE)),
        "contract": sha256_file(regular_file(repo_root, CONTRACT_DOC)),
        "addendum": sha256_file(regular_file(repo_root, ADDENDUM_DOC)),
    }
    missing = [label for label, digest in required.items() if digest not in text]
    if missing:
        raise RuntimeError("refused: the source-QA record does not quote " + ", ".join(missing))
    return {"verdict": VERDICT_RE.match(verdicts[0]).group(1), **required}  # type: ignore[union-attr]


def refuse_existing_outputs(repo_root: Path) -> None:
    out = repo_root / OUT_DIR
    if os.path.lexists(out) or any(os.path.lexists(out / name) for name in OUTPUT_NAMES):
        raise RuntimeError(f"refused: fusion R1 output already exists: {OUT_DIR}")


def publish(parent: Path, out: Path, files: dict[str, bytes]) -> list[dict[str, Any]]:
    """Stage every output with O_CREAT|O_EXCL|O_NOFOLLOW, then rename the directory exclusively."""
    if parent.is_symlink() or not parent.is_dir():
        raise RuntimeError("refused output parent")
    if os.path.lexists(out):
        raise RuntimeError(f"refused to overwrite existing output: {out.name}")
    staging = parent / f".{out.name}.{secrets.token_hex(8)}.partial"
    staging.mkdir(mode=0o755)
    try:
        written = [vre.write_exclusive(staging, name, data) for name, data in files.items()]
        vre._rename_exclusive(staging, out)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    for row in written:
        if sha256_file(out / row["name"]) != row["sha256"]:
            raise RuntimeError(f"published output differs on read-back: {row['name']}")
    return written


def recheck_before_write(repo_root: Path, sources: dict[str, str]) -> dict[str, Any]:
    """Contract §8 "re-verified before the write" (QA R2): every pin, the module and test SHAs
    captured at the start of ``run``, the classifier and the used bundle members. Any mismatch
    raises, so nothing is written."""
    pins = verify_pins(repo_root)
    if source_hashes(repo_root) != sources:
        raise RuntimeError("refused write: the fusion R1 module or tests changed during the run")
    if sha256_file(regular_file(repo_root, CLASSIFIER)) != CLASSIFIER_SHA256:
        raise RuntimeError("refused write: classifier best.pt changed during the run")
    bundle = verify_bundle(repo_root, full=False)
    return {"pins_verified": len(pins), "sources": sources, "bundle": bundle}


def stop_invalid(
    repo_root: Path,
    sources: dict[str, str],
    stage: str,
    detail: dict[str, Any],
    step0: dict[str, Any],
    qa: dict[str, str],
    preflight: dict[str, Any],
) -> dict[str, Any]:
    """QA R4: a post-Step-0 stop is recorded as ``INVALID`` in a write-once stop report, with
    no result file. The output directory then exists, so the run cannot be repeated."""
    report = {
        "package": PACKAGE,
        "boundary": BOUNDARY,
        "outcome": "INVALID",
        "outcome_row": 1,
        "stage": stage,
        "detail": detail,
        "step0": step0,
        "source_qa": qa,
        "sources": sources,
        "preflight": preflight,
        "result_files_written": False,
        "fusion_metric_computed": False,
        "flags": FLAGS,
    }
    recheck_before_write(repo_root, sources)
    refuse_existing_outputs(repo_root)
    stop = publish(
        guard(repo_root, RUN_DIR), repo_root / OUT_DIR, {STOP_REPORT_NAME: canonical(report)}
    )
    return {
        "outcome": "INVALID",
        "outcome_row": 1,
        "stage": stage,
        "detail": detail,
        "written": [],
        "stop_report": stop,
        "source_qa": qa,
        "preflight": preflight,
    }


def manifest(
    repo_root: Path, files: dict[str, bytes], sources: dict[str, str] | None = None
) -> dict[str, Any]:
    """Module, tests, contract, addendum, authorization, input pins, outputs. Never a QA record.
    ``sources`` defaults to fresh hashes via the allow-listed ``_source_file`` (QA R1)."""
    if sources is None:
        sources = source_hashes(repo_root)
    return {
        "package": PACKAGE,
        "sources": sources,
        "documents": {
            str(CONTRACT_DOC): CONTRACT_SHA256,
            str(ADDENDUM_DOC): ADDENDUM_SHA256,
            str(AUTH_DOC): AUTH_SHA256,
        },
        "inputs": {str(k): v for k, v in sorted(PINS.items(), key=lambda kv: str(kv[0]))},
        "outputs": {name: sha256_bytes(data) for name, data in files.items()},
        "flags": FLAGS,
    }


# ------------------------------------------------------------------------------- commands


def step0(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    state = load_state(repo_root, full_bundle=True)
    result = step0_check(state, load_evaluator(repo_root))
    return {
        "package": PACKAGE,
        "command": "step0",
        "inputs": state.checks,
        "step0": result,
        "fusion_metric_computed": False,
        "classifier_loaded": False,
        **FLAGS,
    }


def run(
    repo_root: Path,
    source_qa_record: str | None,
    source_qa_sha256: str | None,
    *,
    rounds: int = ROUNDS,
) -> dict[str, Any]:
    """The single authorized execution (contract §8 step 4). Gates come before any input read."""
    qa = check_source_qa(repo_root, source_qa_record, source_qa_sha256)
    # QA R1: hash the module and tests now, so a path error refuses before any metric exists.
    sources = source_hashes(repo_root)
    if sources[str(MODULE)] != qa["module"]:
        raise RuntimeError("refused: module SHA-256 differs from the source-QA gate's hash")
    refuse_existing_outputs(repo_root)
    state = load_state(repo_root, full_bundle=True)
    evaluator = load_evaluator(repo_root)
    preflight = latency_preflight(repo_root)
    # QA R4 pre-checks: model-free, before Step 0, so a failure refuses instead of consuming.
    preflight["g5_support"] = precheck_g5_support(state)
    plan = crop_plan(state, evaluator.crop_prediction)
    s0 = step0_check(state, evaluator)
    if not s0["passed"]:
        return {
            "outcome": "INVALID",
            "outcome_row": 1,
            "stage": "step0",
            "step0": s0,
            "written": [],
            "source_qa": qa,
        }
    with deterministic_cpu():
        probs_cpu, invalid = classify_candidates(
            state, load_classifier(repo_root, "cpu"), "cpu", plan=plan
        )
    bad = softmax_violations(probs_cpu)
    if bad:  # QA R4: would otherwise raise in parse_probs_csv after the classifier ran
        detail = {"reason": "CPU crop probabilities are not a float32 softmax", "rows": bad}
        return stop_invalid(repo_root, sources, "crop_probabilities", detail, s0, qa, preflight)
    probs_bytes = probs_csv(state.rows, probs_cpu, state.names)
    probs = parse_probs_csv(probs_bytes, state.rows)  # decisions use the written text (C5 item 7)
    mps_model = load_classifier(repo_root, "mps")
    probs_mps, invalid_mps = classify_candidates(state, mps_model, "mps", plan=plan)
    if invalid_mps != invalid or set(probs_mps) != set(probs):  # unreachable: one shared plan
        detail = {
            "reason": "CPU and MPS crop sets differ",
            "symmetric_difference": sorted(
                [k[0], k[1]] for k in (invalid_mps ^ invalid) | (set(probs_mps) ^ set(probs))
            ),
        }
        return stop_invalid(repo_root, sources, "cpu_mps_crop_set", detail, s0, qa, preflight)
    rows_by_key = {r.key: r for r in state.rows}
    mps_rows = [[k[0], k[1]] for k, p in probs_mps.items() if relabel(p, rows_by_key[k].yolo_id)]
    latency_doc = measure_latency(repo_root, state)
    fused = decide(state.rows, probs, invalid)
    pred_bytes = predictions_csv(state.rows, probs, invalid, fused, state.names)
    latency_bytes = canonical(latency_doc)
    document = build_eval(
        state,
        evaluator,
        probs,
        invalid,
        latency_doc,
        mps_rows,
        s0,
        rounds=rounds,
        pred_bytes=pred_bytes,
        probs_bytes=probs_bytes,
    )
    files = {
        PREDICTIONS_NAME: pred_bytes,
        PROBS_NAME: probs_bytes,
        EVAL_NAME: canonical(document),
        LATENCY_NAME: latency_bytes,
    }
    files[MANIFEST_NAME] = canonical(manifest(repo_root, files, sources))
    recheck = recheck_before_write(repo_root, sources)  # QA R2: raises (no write) on a mismatch
    refuse_existing_outputs(repo_root)
    written = publish(guard(repo_root, RUN_DIR), repo_root / OUT_DIR, files)
    return {
        "outcome": document["outcome"],
        "outcome_row": document["outcome_row"],
        "failed_guards": document["failed_guards"],
        "written": written,
        "source_qa": qa,
        "preflight": preflight,
        "recheck_before_write": recheck,
    }


def verify_documents(
    state: State, evaluator: Any, files: dict[str, bytes], *, rounds: int = ROUNDS
) -> list[str]:
    """Rebuild the predictions CSV and eval JSON from the two CSVs plus measured inputs."""
    errors: list[str] = []
    probs = parse_probs_csv(files[PROBS_NAME], state.rows)
    reader = csv.DictReader(io.StringIO(files[PREDICTIONS_NAME].decode("utf-8"), newline=""))
    stored_rows = list(reader)
    if reader.fieldnames != PREDICTION_FIELDS or len(stored_rows) != len(state.rows):
        return ["predictions CSV schema or row count"]
    invalid = {
        r.key for r, s in zip(state.rows, stored_rows, strict=True) if s["crop_invalid"] == "1"
    }
    fused = decide(state.rows, probs, invalid)
    if predictions_csv(state.rows, probs, invalid, fused, state.names) != files[PREDICTIONS_NAME]:
        errors.append("predictions CSV")
    stored = json.loads(files[EVAL_NAME].decode("utf-8"))
    latency_doc = json.loads(files[LATENCY_NAME].decode("utf-8"))
    if canonical(latency_doc) != files[LATENCY_NAME]:
        errors.append("latency JSON is not canonical")
    step = step0_check(state, evaluator)
    rebuilt = build_eval(
        state,
        evaluator,
        probs,
        invalid,
        latency_doc,
        stored["cpu_mps"]["mps_relabel_rows"],
        step,
        rounds=rounds,
        pred_bytes=files[PREDICTIONS_NAME],
        probs_bytes=files[PROBS_NAME],
    )
    if canonical(rebuilt) != files[EVAL_NAME]:
        errors.append("eval JSON")
    return errors


def verify(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    out = guard(repo_root, OUT_DIR)
    if not out.is_dir():
        raise RuntimeError("no fusion R1 output to verify")
    if os.path.lexists(out / STOP_REPORT_NAME):
        return {"verified": False, "errors": ["run stopped INVALID before results (stop report)"]}
    files = {name: regular_file(repo_root, OUT_DIR / name).read_bytes() for name in OUTPUT_NAMES}
    errors = []
    recorded = json.loads(files[MANIFEST_NAME].decode("utf-8"))["outputs"]
    for name, digest in recorded.items():
        if sha256_bytes(files[name]) != digest:
            errors.append(f"manifest hash {name}")
    state = load_state(repo_root, full_bundle=True)
    errors += verify_documents(state, load_evaluator(repo_root), files)
    return {"verified": not errors, "errors": errors}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m m1.classifier_fusion_r1")
    parser.add_argument("command", choices=("step0", "latency", "run", "verify"))
    parser.add_argument("--source-qa-record")
    parser.add_argument("--source-qa-sha256")
    args = parser.parse_args(argv)
    if args.command == "step0":
        result = step0()
        code = 0 if result["step0"]["passed"] else 2
    elif args.command == "latency":
        plan = latency_schedule(FRAMES)
        result = {
            "measures": False,
            "note": "the live latency arm runs only inside `run`, after Step 0 (Addendum 1 §2)",
            "first_measured": plan[WARMUP : WARMUP + 4],
            "orders_measured": [
                sum(o == "AB" for p, _, _, o in plan if p == "measured"),
                sum(o == "BA" for p, _, _, o in plan if p == "measured"),
            ],
        }
        code = 0
    elif args.command == "run":
        result = run(REPO_ROOT, args.source_qa_record, args.source_qa_sha256)
        code = 0 if result.get("written") else 2
    else:
        result = verify()
        code = 0 if result["verified"] else 1
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
