"""Synthetic-only tests for the fusion R1 scorer (contract §8 step 3).

No real validation frame, pilot prediction, classifier weight or crop is used: every frame, box
and probability below is synthetic. The pinned evaluator module is imported for its code only
(crop rule and Ultralytics AP), never run on real data.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import unicodedata
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from m1 import classifier_fusion_r1 as fusion
from m1.metrics import Frame, group_bootstrap, match, operating_point

ROOT = fusion.REPO_ROOT
W, H = 200, 100


# ------------------------------------------------------------------------------- helpers


def names54() -> list[str]:
    names = [f"k{i}" for i in range(fusion.CLASSES)]
    for yolo_id, key in fusion.EXPECTED_DERIVED_KEYS.items():
        names[yolo_id] = key
    return names


def vec(top: int, p_top: float, second: int | None = None, p_second: float = 0.0) -> np.ndarray:
    p = np.zeros(fusion.CLASSES, dtype=np.float64)
    rest = 1.0 - p_top - p_second
    others = [k for k in range(fusion.CLASSES) if k not in (top, second)]
    p[others] = rest / len(others)
    p[top] = p_top
    if second is not None:
        p[second] = p_second
    return p.astype(np.float32)


def row(index: int, stem: str, rank: int, cls: int, conf: float, box) -> fusion.Row:
    box = tuple(float(v) for v in box)
    raw = {
        "stem": stem,
        "rank": str(rank),
        "yolo_id": str(cls),
        "conf": repr(conf),
        "x1": repr(box[0]),
        "y1": repr(box[1]),
        "x2": repr(box[2]),
        "y2": repr(box[3]),
    }
    return fusion.Row(index, stem, rank, cls, conf, box, raw)


# GT class -> class the synthetic "pilot" predicts for it (pair confusions and correct ones).
CONFUSED = {48: 10, 8: 12, 42: 40, 33: 7, 7: 19}
GT_CYCLE = [7, 8, 10, 12, 25, 35, 48, 33, 42, 40, 6, 7, 48]


def synthetic_state(groups: int = 9, per_group: int = 2) -> fusion.State:
    frames, rows = [], []
    k = 0
    for g in range(groups):
        for f in range(per_group):
            stem = f"s{g:02d}{f}"
            gt_boxes, gt_classes = [], []
            for slot in range(3):
                cls = GT_CYCLE[k % len(GT_CYCLE)]
                k += 1
                x = 10 + 60 * slot
                gt_boxes.append([x, 20, x + 40, 60])
                gt_classes.append(cls)
            frames.append(
                Frame(
                    stem,
                    f"G{g}",
                    np.asarray(gt_boxes, dtype=float),
                    np.asarray(gt_classes, dtype=int),
                    np.zeros((0, 4)),
                    np.zeros(0, dtype=int),
                    np.zeros(0),
                    W,
                    H,
                )
            )
            rank = 0
            for slot, (box, cls) in enumerate(zip(gt_boxes, gt_classes, strict=True)):
                pred = CONFUSED.get(cls, cls) if (g + slot) % 2 == 0 else cls
                conf = 0.9 - 0.1 * slot
                shifted = [box[0] + 1, box[1] + 1, box[2] + 1, box[3] + 1]
                rows.append(row(len(rows), stem, rank, pred, conf, shifted))
                rank += 1
            # one background FP with a source class and one low-score duplicate
            rows.append(row(len(rows), stem, rank, 41, 0.3, [185, 80, 199, 95]))
            rank += 1
            rows.append(row(len(rows), stem, rank, 10, 0.05, [11, 21, 51, 61]))
    return fusion.State(frames, rows, names54(), {}, {})


def synthetic_probs(state: fusion.State) -> dict[tuple[str, int], np.ndarray]:
    """Deterministic float32 softmaxes: some confident targets, some confident sources."""
    probs = {}
    for r in state.rows:
        if r.yolo_id not in fusion.SOURCE_PAIR:
            continue
        target = fusion.SOURCE_PAIR[r.yolo_id][1]
        if r.rank % 2 == 0:
            probs[r.key] = vec(target, 0.85, r.yolo_id, 0.10)
        else:
            probs[r.key] = vec(r.yolo_id, 0.70, target, 0.20)
    return probs


def synthetic_latency(fail_at: int | None = None, zero_at: int | None = None) -> dict:
    """Fake arms and clock: each sample lasts 1 ms, except sample ``zero_at`` (0 ms); arm call
    number ``fail_at`` (1-based, warm-up included) raises."""
    images = [Path(f"img{i:03d}.png") for i in range(fusion.FRAMES)]
    calls = {"clock": 0, "arm": 0}

    def clock() -> float:
        sample, is_end = divmod(calls["clock"], 2)
        calls["clock"] += 1
        if not is_end:
            return float(sample)
        return float(sample) + (0.0 if sample == zero_at else 0.001)

    def arm(path: Path) -> None:
        calls["arm"] += 1
        if fail_at is not None and calls["arm"] == fail_at:
            raise RuntimeError("synthetic failure")

    return fusion.latency_protocol(images, arm, arm, sync=lambda: None, clock=clock)


@pytest.fixture(scope="module")
def evaluator():
    return fusion.load_evaluator(ROOT)


# ----------------------------------------------------------------------- constants (§3, §4)


def test_pairs_tau_and_translation_are_the_preregistered_values():
    assert fusion.PAIRS == (
        ("P1", 10, 48),
        ("P2", 19, 7),
        ("P3", 40, 42),
        ("P4", 7, 33),
        ("P5", 41, 42),
        ("P6", 12, 8),
    )
    assert fusion.TAU == 0.80 and fusion.TAU_GRID == (0.50, 0.95)
    assert (fusion.ROUNDS, fusion.SEED, fusion.CONF) == (1000, 20261018, 0.20)
    # contract §3 translation table (derived key reported, yolo_id used by CSV / classifier)
    table = {
        7: "7",
        8: "8",
        10: "10",
        12: "12",
        19: "17",
        20: "18",
        33: "32",
        40: "39",
        41: "40",
        42: "41",
        48: "46",
    }
    assert all(fusion.EXPECTED_DERIVED_KEYS[k] == v for k, v in table.items())
    assert fusion.G4_MIN_HITS == {7: 66, 33: 18, 42: 12}
    assert fusion.G4B_MIN_HITS == {40: 14}
    assert fusion.G1_MIN_HITS == 467 and fusion.G5_MAX_LOSS == 2 and fusion.G7_P95_MS == 100.0
    assert fusion.STEP0_REFERENCE["per_class_hits_yolo"] == {
        "7": 66,
        "33": 18,
        "42": 12,
        "48": 55,
        "40": 14,
    }
    assert fusion.OUTPUT_NAMES == (
        "fusion_r1_predictions_conf0001.csv",
        "fusion_r1_crop_probs.csv",
        "fusion_r1_eval.json",
        "fusion_r1_latency_mps.json",
        "fusion_r1_manifest.json",
    )
    assert fusion.FLAGS["sealed_test_accessed"] is False


def test_class_map_translation_is_checked(tmp_path):
    rows = ["yolo_id,derived_key,derived_code,name_vi,name"]
    sign = ["ClassId,SignName,DerivedKey,QCVN"]
    for i, key in enumerate(names54()):
        rows.append(f"{i},{key},C{i},n{i},{key} C{i}")
        sign.append(f"{i},n{i},{key},C{i}")
    for relative, lines in ((fusion.CLASS_MAP, rows), (fusion.SIGNNAMES, sign)):
        (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / relative).write_text("\n".join(lines) + "\n", encoding="utf-8")
    names = fusion.class_names(tmp_path)
    assert names[33] == "32" and names[40] == "39" and names[48] == "46"
    assert fusion.g5_yolo_ids(names) == {
        "6": 6,
        "8": 8,
        "10": 10,
        "12": 12,
        "23": 25,
        "34": 35,
        "46": 48,
    }
    sign[34] = "33,n33,33,C33"  # yolo 33 must translate to DK 32
    rows[34] = "33,33,C33,n33,33 C33"
    (tmp_path / fusion.SIGNNAMES).write_text("\n".join(sign) + "\n", encoding="utf-8")
    (tmp_path / fusion.CLASS_MAP).write_text("\n".join(rows) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="translation differs for yolo_id 33"):
        fusion.class_names(tmp_path)


# ------------------------------------------------------------------------ rule F1 (C5)


def test_tau_boundary_is_inclusive_on_float32_values():
    at = np.float32(0.8)
    below = np.nextafter(at, np.float32(0))
    assert float(at) == 0.800000011920928955078125
    assert float(below) == 0.7999999523162841796875
    for source, target in ((10, 48), (19, 7), (40, 42), (7, 33), (41, 42), (12, 8)):
        p = vec(target, float(at), source, float(1 - at) / 2)
        p[target] = at
        assert fusion.relabel(p, source)
        q = p.copy()
        q[target] = below
        assert not fusion.relabel(q, source)


def test_argmax_clause_binds_only_in_an_exact_tie_on_the_grid():
    # tau 0.50: exact two-way tie at 0.5; numpy argmax takes the first index
    p = np.zeros(fusion.CLASSES, dtype=np.float32)
    p[7], p[19] = 0.5, 0.5  # P2 source 19 -> target 7, target has the lower index
    assert fusion.relabel(p, 19, 0.50)
    q = np.zeros(fusion.CLASSES, dtype=np.float32)
    q[10], q[48] = 0.5, 0.5  # P1 source 10 -> target 48, source has the lower index
    assert not fusion.relabel(q, 10, 0.50)
    assert not fusion.relabel(vec(48, 0.94, 10, 0.05), 10, 0.95)
    with pytest.raises(ValueError, match="float32"):
        fusion.relabel(vec(48, 0.9).astype(np.float64), 10)


def test_no_chaining_and_p2_p4_overlap():
    rows = [
        row(0, "a", 0, 19, 0.9, [1, 1, 20, 20]),  # P2 -> 7; never re-examined under P4
        row(1, "a", 1, 7, 0.9, [30, 1, 50, 20]),  # P4 -> 33
        row(2, "a", 2, 19, 0.9, [60, 1, 80, 20]),  # top1 33 is not P2's target
        row(3, "a", 3, 7, 0.9, [90, 1, 110, 20]),  # classifier agrees with source
        row(4, "a", 4, 5, 0.9, [120, 1, 140, 20]),  # not a source class
    ]
    probs = {
        ("a", 0): vec(7, 0.90, 33, 0.09),
        ("a", 1): vec(33, 0.95),
        ("a", 2): vec(33, 0.99),
        ("a", 3): vec(7, 0.99),
    }
    assert fusion.decide(rows, probs, set()) == [7, 33, 19, 7, 5]
    # leave-one-out of P4 leaves the class-7 box alone; P2 still applies by original class
    assert fusion.decide(rows, probs, set(), pairs=("P2",)) == [7, 7, 19, 7, 5]
    with pytest.raises(RuntimeError, match="non-source candidate was cropped"):
        fusion.decide(rows, {**probs, ("a", 4): vec(5, 0.9)}, set())
    with pytest.raises(RuntimeError, match="xor crop_invalid"):
        fusion.decide(rows, probs, {("a", 0)})


def test_invalid_crop_predicate_and_backstop(evaluator):
    image = Image.new("RGB", (W, H), (10, 20, 30))
    calls = []

    def spy(img, box):
        calls.append(box.copy())
        return evaluator.crop_prediction(img, box)

    crop = fusion.crop_input(image, [-5.0, -3.0, 40.0, 30.0], spy)
    assert crop.shape == (32, 32, 3) and crop.dtype == np.uint8
    assert calls[-1].tolist() == [0.0, 0.0, 40.0, 30.0]  # clipped copy is the crop input only
    for bad in (
        [float("nan"), 1, 20, 20],
        [10, 10, 10, 20],  # zero width
        [10, 10, 20, 10],  # zero height
        [250, 10, 300, 20],  # outside -> clipped to zero width
        [20, 10, 10, 20],  # inverted
    ):
        assert fusion.crop_input(image, bad, spy) is None
    inf_box = [float("-inf"), 1, 20, 20]  # numpy clip turns -inf into the bound
    assert fusion.crop_input(image, inf_box, spy) is not None

    def raises(img, box):
        raise ValueError("invalid predicted box")

    assert fusion.crop_input(image, [1, 1, 20, 20], raises) is None

    rows = [row(0, "a", 0, 10, 0.9, [1, 1, 20, 20]), row(1, "a", 1, 10, 0.9, [30, 1, 50, 20])]
    probs = {("a", 1): vec(48, 0.9)}
    fused = fusion.decide(rows, probs, {("a", 0)})
    assert fused == [10, 48]
    text = fusion.predictions_csv(rows, probs, {("a", 0)}, fused, names54()).decode()
    lines = text.splitlines()
    assert lines[0].split(",") == fusion.PREDICTION_FIELDS
    first = dict(zip(fusion.PREDICTION_FIELDS, lines[1].split(","), strict=True))
    assert first["crop_invalid"] == "1" and first["relabelled"] == "0"
    assert first["p_target"] == first["p_source"] == first["top1_id"] == ""
    assert first["pair"] == "P1" and first["fused_id"] == "10"
    second = dict(zip(fusion.PREDICTION_FIELDS, lines[2].split(","), strict=True))
    assert second["relabelled"] == "1" and second["fused_derived_key"] == "46"
    assert second["derived_key"] == "10" and second["p_target"] == repr(float(np.float32(0.9)))


def test_classify_candidates_one_forward_per_image_and_float32():
    import torch

    state = synthetic_state(groups=1, per_group=2)
    bad = replace(state.rows[0], box=(5.0, 5.0, 5.0, 30.0))
    rows = [bad, *state.rows[1:]]
    state = replace(state, rows=rows, images={f.stem: Path(f.stem) for f in state.frames})

    class Fake(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def forward(self, x):
            self.calls += 1
            logits = torch.zeros(x.shape[0], fusion.CLASSES)
            logits[:, 48] = 5.0
            return logits

    model = Fake().eval()
    probs, invalid = fusion.classify_candidates(
        state,
        model,
        "cpu",
        lambda image, box: np.zeros((32, 32, 3), dtype=np.uint8),
        image_loader=lambda path: Image.new("RGB", (W, H)),
    )
    sources = [r for r in rows if r.yolo_id in fusion.SOURCE_PAIR]
    assert model.calls == 2  # one batched forward per image with source candidates
    assert bad.yolo_id in fusion.SOURCE_PAIR and invalid == {bad.key}
    assert set(probs) | invalid == {r.key for r in sources}
    assert all(p.dtype == np.float32 and p.shape == (54,) for p in probs.values())


# ------------------------------------------------------------------ FP invariant (§2, G3)


def test_relabel_only_preserves_tp_fp_and_agnostic_recall():
    state = synthetic_state()
    rng = np.random.default_rng(7)
    base = fusion.arm_frames(state.frames, state.rows, [r.yolo_id for r in state.rows])
    a = operating_point(base, fusion.CONF)
    for _ in range(25):
        classes = rng.integers(0, fusion.CLASSES, size=len(state.rows)).tolist()
        b = operating_point(fusion.arm_frames(state.frames, state.rows, classes), fusion.CONF)
        assert (b.true_positives, b.false_positives) == (a.true_positives, a.false_positives)
        assert b.agnostic_recall == a.agnostic_recall and b.fp_per_image == a.fp_per_image
    probs = synthetic_probs(state)
    fused = fusion.decide(state.rows, probs, set())
    assert fused != [r.yolo_id for r in state.rows]
    b = operating_point(fusion.arm_frames(state.frames, state.rows, fused), fusion.CONF)
    assert (b.true_positives, b.false_positives) == (a.true_positives, a.false_positives)


def test_a_moved_box_breaks_g3_and_is_invalid():
    state = synthetic_state()
    classes = [r.yolo_id for r in state.rows]
    arm_a = fusion.point(fusion.arm_frames(state.frames, state.rows, classes), state.names)
    moved_rows = [
        replace(r, box=(150.0, 0.0, 160.0, 10.0)) if i == 0 else r for i, r in enumerate(state.rows)
    ]
    arm_b = fusion.point(fusion.arm_frames(state.frames, moved_rows, classes), state.names)
    boot = {"correct_class_recall": {"paired_ci95": [0.01, 0.02]}}
    ap = {"map50": 0.5, "map50_95": 0.3}
    latency = {"L": True, "arm_b": {"p95_ms": 10.0}}
    g = fusion.guards(arm_a, arm_b, boot, ap, ap, latency, state.names, True)
    assert g["flags"]["G3"] is False
    assert (g["outcome"], g["outcome_row"]) == ("INVALID", 1)


# ---------------------------------------------------------------- outcome table (C2)


def flags(**overrides) -> dict[str, bool]:
    base = {key: True for key in fusion.GUARD_ORDER}
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    ("overrides", "outcome", "row"),
    [
        ({"S0": False}, "INVALID", 1),
        ({"G3": False}, "INVALID", 1),
        ({"L": False, "G7": False}, "INVALID", 1),
        ({"L": False, "delta_positive": False, "G4": False}, "INVALID", 1),
        ({"delta_positive": False, "G1": False, "G2": False}, "NO_GO", 2),
        ({"G4": False}, "NO_GO", 2),
        ({"G4b": False}, "NO_GO", 2),
        ({"G5": False}, "NO_GO", 2),
        ({"G6": False}, "NO_GO", 2),
        ({"G1": False, "G5": False}, "NO_GO", 2),  # the contract's overlap case
        ({"G1": False}, "NO_GO_UNCERTAIN", 3),
        ({"G2": False}, "NO_GO_UNCERTAIN", 3),
        ({"G2": False, "G7": False}, "NO_GO_UNCERTAIN", 3),
        ({"G7": False}, "NO_GO_LATENCY", 4),
        ({}, "GO_CANDIDATE_FOR_CONFIRMATION", 5),
    ],
)
def test_every_outcome_row(overrides, outcome, row):
    got, got_row, failed = fusion.assign_outcome(flags(**overrides))
    assert (got, got_row) == (outcome, row)
    assert failed == [k for k in fusion.GUARD_ORDER if k in overrides and not overrides[k]]


def test_outcome_mapping_is_total_unique_and_follows_precedence():
    precedence = ["INVALID", "NO_GO", "NO_GO_UNCERTAIN", "NO_GO_LATENCY", fusion.GO]
    seen = set()
    for values in itertools.product((False, True), repeat=len(fusion.GUARD_ORDER)):
        f = dict(zip(fusion.GUARD_ORDER, values, strict=True))
        outcome, row, failed = fusion.assign_outcome(f)
        candidates = set()
        if not (f["S0"] and f["G3"] and f["L"]):
            candidates.add("INVALID")
        if not (f["delta_positive"] and f["G4"] and f["G4b"] and f["G5"] and f["G6"]):
            candidates.add("NO_GO")
        if not (f["G1"] and f["G2"]):
            candidates.add("NO_GO_UNCERTAIN")
        if not f["G7"]:
            candidates.add("NO_GO_LATENCY")
        expected = min(candidates, key=precedence.index) if candidates else fusion.GO
        assert outcome == expected and row == precedence.index(expected) + 1
        assert failed == [k for k in fusion.GUARD_ORDER if not f[k]]
        seen.add(outcome)
    assert seen == set(precedence)
    with pytest.raises(ValueError):
        fusion.assign_outcome({**flags(), "extra": True})
    with pytest.raises(ValueError):
        fusion.assign_outcome({**flags(), "G1": 1})


# ---------------------------------------------------------------- paired bootstrap (C6, Q3)


def heterogeneous_frames() -> list[Frame]:
    """Groups differ (k extra background FPs in group Gk) and frames are not in group order, so
    any change to the draw sequence (unsorted names, other seed) changes the intervals."""
    state = synthetic_state()
    extra = list(state.rows)
    for frame in state.frames:
        k = int(frame.group_id[1:])
        for j in range(k):
            extra.append(row(len(extra), frame.stem, 100 + j, 5, 0.5, [150, 70 + j, 160, 80 + j]))
    frames = fusion.arm_frames(state.frames, extra, [r.yolo_id for r in extra])
    order = np.random.default_rng(3).permutation(len(frames))
    return [frames[i] for i in order]


def test_bootstrap_draws_equal_group_bootstrap_and_zero_delta_is_exact():
    a = heterogeneous_frames()
    assert [f.group_id for f in a] != sorted(f.group_id for f in a)
    rounds = 200
    samples = fusion.resample_indices(a, rounds, fusion.SEED)
    boot = fusion.paired_bootstrap(a, a, samples)
    reference = group_bootstrap(a, fusion.CONF, rounds, fusion.SEED)
    assert boot["agnostic_recall"]["arm_a_marginal_ci95"] == list(reference["agnostic_recall"])
    assert boot["fp_per_image"]["arm_a_marginal_ci95"] == list(reference["fp_per_image"])
    other = group_bootstrap(a, fusion.CONF, rounds, fusion.SEED + 1)
    assert list(other["fp_per_image"]) != boot["fp_per_image"]["arm_a_marginal_ci95"]
    assert boot["correct_class_recall"]["paired_ci95"] == [0.0, 0.0]
    assert boot["correct_class_recall"]["delta_b_minus_a"] == 0.0
    assert len({f.group_id for f in a}) == 9


def test_paired_bootstrap_nonzero_delta_has_known_sign_and_pairing():
    """Q3: B gains exactly 2 class-aware hits, both inside group G4; Δ per round is known."""
    state = synthetic_state()
    a = fusion.arm_frames(state.frames, state.rows, [r.yolo_id for r in state.rows])
    gain_group = "G4"
    b = []
    for frame in a:
        if frame.group_id == gain_group:
            aware, _ = match(frame, fusion.CONF, class_aware=True)
            miss = int(np.flatnonzero(~aware)[0])  # prediction `miss` overlaps GT `miss`
            classes = frame.pred_classes.copy()
            classes[miss] = frame.gt_classes[miss]
            frame = replace(frame, pred_classes=classes)
        b.append(frame)
    rounds = 300
    samples = fusion.resample_indices(a, rounds, fusion.SEED)
    boot = fusion.paired_bootstrap(a, b, samples)["correct_class_recall"]
    sa, sb = fusion.frame_stats(a), fusion.frame_stats(b)
    assert sb["aware_hits"].sum() - sa["aware_hits"].sum() == 2
    groups = np.asarray([f.group_id for f in a])
    members = np.flatnonzero(groups == gain_group)
    expected = []
    for s in samples:
        copies = int(np.isin(s, members).sum()) // len(members)
        expected.append(2 * copies / sa["gt"][s].sum())
    reference = fusion.ci95(expected)
    assert np.allclose(boot["paired_ci95"], reference, rtol=0, atol=1e-15)
    assert (boot["paired_ci95"][0] == 0.0) == (reference[0] == 0.0)
    assert boot["delta_b_minus_a"] == pytest.approx(2 / sa["gt"].sum(), abs=1e-15)
    assert boot["delta_b_minus_a"] > 0 and boot["paired_ci95"][1] > 0
    misses = float(np.mean([e == 0 for e in expected]))
    assert 0 < misses < 1  # some resamples omit G4 entirely (Δ = 0 exactly), most do not
    assert boot["share_rounds_delta_gt_0"] == pytest.approx(1 - misses)
    # swapping the arms flips the sign of every paired difference
    swapped = fusion.paired_bootstrap(b, a, samples)["correct_class_recall"]
    assert np.allclose(swapped["paired_ci95"], [-reference[1], -reference[0]], atol=1e-15)


# ----------------------------------------------------------------- probabilities (C5 item 7)


def test_crop_probs_round_trip_is_bit_exact_and_strict():
    state = synthetic_state(groups=2, per_group=1)
    probs = synthetic_probs(state)
    data = fusion.probs_csv(state.rows, probs, state.names)
    back = fusion.parse_probs_csv(data, state.rows)
    assert back.keys() == probs.keys()
    assert all(np.array_equal(back[k], probs[k]) and back[k].dtype == np.float32 for k in probs)
    lines = data.decode().splitlines()
    tampered = lines[1].split(",")
    tampered[5] = "0.1"  # not an exact float32 value
    with pytest.raises(RuntimeError, match="exact float32"):
        fusion.parse_probs_csv(
            "\n".join([lines[0], ",".join(tampered), *lines[2:]]).encode(), state.rows
        )
    with pytest.raises(RuntimeError, match="pilot CSV order"):
        fusion.parse_probs_csv(
            "\n".join([lines[0], lines[2], lines[1], *lines[3:]]).encode(), state.rows
        )
    with pytest.raises(RuntimeError, match="unique source candidate"):
        fusion.parse_probs_csv("\n".join([lines[0], lines[1], lines[1]]).encode(), state.rows)


# --------------------------------------------------------------------- latency (C3, Q1, Q2)


def test_latency_protocol_is_counterbalanced_and_valid():
    doc = synthetic_latency()
    samples = doc["samples"]
    assert len(samples) == 2 * fusion.ITERATIONS
    for j in range(fusion.ITERATIONS):
        pair = [s for s in samples if s["iteration"] == j]
        assert [s["arm"] for s in pair] == (["A", "B"] if j % 2 == 0 else ["B", "A"])
        assert [s["position"] for s in pair] == ["first", "second"]
        assert {s["image_index"] for s in pair} == {(fusion.WARMUP + j) % fusion.FRAMES}
        assert {s["order"] for s in pair} == {"AB" if j % 2 == 0 else "BA"}
    summary = fusion.summarize_latency(doc)
    assert summary["L"] is True and summary["counterbalanced_ab_ba"] == [150, 150]
    assert summary["arm_b"]["valid_samples"] == 300 and summary["arm_b"]["p95_ms"] > 0
    plan = fusion.latency_schedule(fusion.FRAMES)
    assert plan[0] == ("warmup", 0, 0, "AB") and plan[49] == ("warmup", 49, 49, "BA")
    assert plan[50] == ("measured", 0, 50, "AB") and plan[-1] == ("measured", 299, 349, "BA")


def test_latency_invalid_samples_make_l_false_and_invalid():
    failed = fusion.summarize_latency(synthetic_latency(fail_at=2 * fusion.WARMUP + 7))
    assert (
        failed["L"] is False
        and failed["arm_b"]["valid_samples"] + failed["arm_a"]["valid_samples"] == 599
    )
    zero = fusion.summarize_latency(synthetic_latency(zero_at=2 * fusion.WARMUP + 3))
    assert zero["L"] is False
    assert fusion.summarize_latency({"completed": False, "samples": []})["L"] is False
    outcome, row, _ = fusion.assign_outcome(flags(L=False, G7=False))
    assert (outcome, row) == ("INVALID", 1)


# ------------------------------------------------------------------- eval and verify rebuild


def test_build_eval_and_model_free_rebuild_are_byte_identical(evaluator):
    state = synthetic_state()
    probs = synthetic_probs(state)
    invalid: set = set()
    probs_bytes = fusion.probs_csv(state.rows, probs, state.names)
    parsed = fusion.parse_probs_csv(probs_bytes, state.rows)
    fused = fusion.decide(state.rows, parsed, invalid)
    pred_bytes = fusion.predictions_csv(state.rows, parsed, invalid, fused, state.names)
    latency_doc = synthetic_latency()
    mps_rows = [
        [k[0], k[1]]
        for k, p in parsed.items()
        if fusion.relabel(p, dict((r.key, r) for r in state.rows)[k].yolo_id)
    ][1:]
    step = fusion.step0_check(state, evaluator)
    assert step["passed"] is False  # synthetic frames cannot meet the real references
    doc = fusion.build_eval(
        state,
        evaluator,
        parsed,
        invalid,
        latency_doc,
        mps_rows,
        step,
        rounds=30,
        pred_bytes=pred_bytes,
        probs_bytes=probs_bytes,
    )
    files = {
        fusion.PREDICTIONS_NAME: pred_bytes,
        fusion.PROBS_NAME: probs_bytes,
        fusion.EVAL_NAME: fusion.canonical(doc),
        fusion.LATENCY_NAME: fusion.canonical(latency_doc),
    }
    assert fusion.verify_documents(state, evaluator, files, rounds=30) == []
    # FP invariant holds; S0 false makes the synthetic run INVALID by row 1
    assert doc["guards"]["flags"]["G3"] is False  # synthetic TP/FP differ from 547/150
    assert doc["arm_a"]["true_positives"] == doc["arm_b"]["true_positives"]
    assert doc["arm_a"]["false_positives"] == doc["arm_b"]["false_positives"]
    assert (doc["outcome"], doc["outcome_row"]) == ("INVALID", 1)
    assert doc["sensitivity"]["label"] == "SENSITIVITY_NOT_DECISION"
    assert set(doc["sensitivity"]["tau_grid"]) == {"0.5", "0.95"}
    assert set(doc["sensitivity"]["leave_one_out"]) == {f"without_P{i}" for i in range(1, 7)}
    assert len(doc["cpu_mps"]["differences"]) == 1
    assert doc["flags"] == fusion.FLAGS
    assert doc["primary_endpoint"]["delta_hits"] == (
        doc["arm_b"]["correct_class_hits"] - doc["arm_a"]["correct_class_hits"]
    )
    for pair in doc["reported"]["per_pair"].values():
        assert pair["relabelled_conf_ge_020"] <= pair["relabelled_all_scores"]
    # any tampering is detected
    other = dict(parsed)
    key = next(iter(other))
    other[key] = vec(int(np.argmax(parsed[key])), 0.5)
    tampered = dict(files)
    tampered[fusion.PROBS_NAME] = fusion.probs_csv(state.rows, other, state.names)
    assert fusion.verify_documents(state, evaluator, tampered, rounds=30)
    edited = json.loads(files[fusion.EVAL_NAME])
    edited["outcome"] = fusion.GO
    tampered = dict(files)
    tampered[fusion.EVAL_NAME] = fusion.canonical(edited)
    assert fusion.verify_documents(state, evaluator, tampered, rounds=30) == ["eval JSON"]


def test_same_class_overlaps_and_help_harm():
    gt = np.asarray([[10, 10, 50, 50]], dtype=float)
    frame = Frame(
        "x",
        "G0",
        gt,
        np.asarray([48]),
        np.asarray([[10, 10, 50, 50], [11, 11, 51, 51]], dtype=float),
        np.asarray([10, 48]),
        np.asarray([0.9, 0.8]),
        W,
        H,
    )
    b = replace(frame, pred_classes=np.asarray([48, 48]))
    assert fusion.same_class_overlaps([b], [np.asarray([True, False])], 0.2) == 1
    assert fusion.same_class_overlaps([b], [np.asarray([False, False])], 0.2) == 0
    hh = fusion.help_harm([frame], [b])
    assert (hh["help"], hh["harm"]) == (0, 0)  # GT 48 already hit by the second box
    c = replace(frame, pred_classes=np.asarray([10, 10]))
    hh = fusion.help_harm([frame], [c])
    assert (hh["help"], hh["harm"]) == (0, 1)
    assert hh["by_gt_size_bin"]["32_64"]["harm"] == 1


# -------------------------------------------------------- write-once, gates, paths (Q4)


def test_publish_is_write_once_and_refuses_symlinks(tmp_path):
    parent = tmp_path / "run"
    parent.mkdir()
    out = parent / "classifier_fusion_r1"
    written = fusion.publish(parent, out, {"a.json": b"{}\n", "b.csv": b"x\n"})
    assert [w["name"] for w in written] == ["a.json", "b.csv"]
    assert (out / "a.json").read_bytes() == b"{}\n"
    with pytest.raises(RuntimeError, match="refused to overwrite"):
        fusion.publish(parent, out, {"a.json": b"other"})
    assert (out / "a.json").read_bytes() == b"{}\n"
    assert not list(parent.glob(".*partial"))
    with pytest.raises(FileExistsError):
        fusion.vre.write_exclusive(out, "a.json", b"again")
    link_parent = tmp_path / "linkrun"
    link_parent.symlink_to(parent)
    with pytest.raises(RuntimeError, match="refused output parent"):
        fusion.publish(link_parent, link_parent / "new", {"a": b""})
    dangling = parent / "dangling"
    dangling.symlink_to(tmp_path / "nowhere")
    with pytest.raises(RuntimeError, match="refused to overwrite"):
        fusion.publish(parent, dangling, {"a": b""})


def write_gate_files(root: Path) -> dict[str, str]:
    hashes = {}
    for relative, text in (
        (fusion.MODULE, "module"),
        (fusion.TESTS, "tests"),  # hashed at the start of run since QA R1
        (fusion.CONTRACT_DOC, "contract"),
        (fusion.ADDENDUM_DOC, "addendum"),
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        hashes[text] = hashlib.sha256(text.encode()).hexdigest()
    return hashes


def write_record(root: Path, text: str, name: str = "qa.md") -> tuple[str, str]:
    path = root / "docs/review" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return f"docs/review/{name}", hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_run_refuses_without_a_source_qa_pass(tmp_path):
    hashes = write_gate_files(tmp_path)
    quoted = "\n".join(hashes.values())
    with pytest.raises(RuntimeError, match="needs --source-qa-record"):
        fusion.run(tmp_path, None, None)
    rel, digest = write_record(tmp_path, f"Verdict: PASS\n{quoted}\n")
    with pytest.raises(RuntimeError, match="needs --source-qa-record"):
        fusion.run(tmp_path, rel, None)
    with pytest.raises(RuntimeError, match="64 lowercase hex"):
        fusion.run(tmp_path, rel, "abc")
    with pytest.raises(RuntimeError, match="SHA-256 differs"):
        fusion.run(tmp_path, rel, "0" * 64)
    for bad in (
        f"Verdict: FAIL\n{quoted}",
        f"Verdict: NOT PASS\n{quoted}",
        f"Verdict: PASSED\n{quoted}",
        f"Verdict: PASS_WITH_NOTES\n{quoted}",
        f"Verdict: PASS\nVerdict: FAIL\n{quoted}",
        f"No verdict line\n{quoted}",
    ):
        r, d = write_record(tmp_path, bad, "bad.md")
        with pytest.raises(RuntimeError, match="one PASS / PASS giới hạn verdict"):
            fusion.run(tmp_path, r, d)
    r, d = write_record(tmp_path, f"Verdict: PASS giới hạn — fine\n{hashes['module']}\n", "m.md")
    with pytest.raises(RuntimeError, match="does not quote contract, addendum"):
        fusion.run(tmp_path, r, d)
    with pytest.raises(RuntimeError, match="non-relative"):
        fusion.run(tmp_path, str(tmp_path / rel), digest)
    link = tmp_path / "docs/review/link.md"
    link.symlink_to(tmp_path / rel)
    with pytest.raises(RuntimeError, match="symlink"):
        fusion.run(tmp_path, "docs/review/link.md", digest)


@pytest.mark.parametrize(
    "verdict",
    [
        "Verdict: PASS",
        "Verdict: **PASS**",
        "Verdict: PASS giới hạn — no correction required",
        unicodedata.normalize("NFD", "Verdict: PASS giới hạn"),
    ],
)
def test_run_gate_accepts_pass_forms_then_refuses_existing_output(tmp_path, verdict):
    hashes = write_gate_files(tmp_path)
    rel, digest = write_record(tmp_path, verdict + "\n" + "\n".join(hashes.values()) + "\n")
    out = tmp_path / fusion.OUT_DIR
    out.mkdir(parents=True)
    with pytest.raises(RuntimeError, match="output already exists"):
        fusion.run(tmp_path, rel, digest)
    out.rmdir()
    (out.parent / "classifier_fusion_r1").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(RuntimeError, match="output already exists"):
        fusion.run(tmp_path, rel, digest)
    os.unlink(out)
    # past both gates the run reaches the pinned inputs, which this synthetic root lacks
    with pytest.raises(RuntimeError, match="missing input|pinned fusion R1 input differs"):
        fusion.run(tmp_path, rel, digest)
    assert not os.path.lexists(out)


def test_test_paths_and_symlinks_are_refused(tmp_path):
    for bad in ("data/test/x.png", "data/images/Test/x.png", "a/latest/b", "../x", "/abs"):
        with pytest.raises(RuntimeError, match="refused"):
            fusion.guard(tmp_path, Path(bad))
    folder = tmp_path / fusion.BUNDLE_IMAGES
    folder.mkdir(parents=True)
    for i in range(fusion.FRAMES):
        (folder / f"{i:04d}.png").write_bytes(b"x")
    assert len(fusion.bundle_images(tmp_path)) == fusion.FRAMES
    target = tmp_path / "raw/0000.png"
    target.parent.mkdir()
    target.write_bytes(b"x")
    (folder / "0000.png").unlink()
    (folder / "0000.png").symlink_to(target)  # the R4-export pattern (link into raw data)
    with pytest.raises(RuntimeError, match="symlink"):
        fusion.bundle_images(tmp_path)
    # a symlinked directory in the middle of the chain is refused too
    real = tmp_path / "realdata"
    real.mkdir()
    (real / "f.txt").write_text("x")
    (tmp_path / "linked").symlink_to(real)
    with pytest.raises(RuntimeError, match="symlink"):
        fusion.regular_file(tmp_path, Path("linked/f.txt"))
    with pytest.raises(RuntimeError, match="missing input"):
        fusion.regular_file(tmp_path, Path("realdata/none.txt"))


def test_bundle_manifest_with_test_member_or_bad_member_is_refused(tmp_path):
    bundle = tmp_path / fusion.BUNDLE
    data = b"stem,rank\n"
    (bundle / "data").mkdir(parents=True)
    (bundle / "data/yolo54_predictions_val.csv").write_bytes(data)
    members = {
        fusion.BUNDLE_CSV_MEMBER: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    }

    def write(manifest: dict) -> str:
        text = json.dumps(manifest).encode()
        (bundle / "manifest.json").write_bytes(text)
        return hashlib.sha256(text).hexdigest()

    good = {
        "test_included": False,
        "sealed_test_accessed": False,
        "counts": {"val": {"images": 376, "boxes": 624}},
        "members": members,
    }
    digest = write(good)
    with pytest.raises(RuntimeError, match="not byte-identical"):
        fusion.verify_bundle(tmp_path, manifest_sha256=digest)
    digest = write(
        {
            **good,
            "members": {**members, "data/images/test/1.png": members[fusion.BUNDLE_CSV_MEMBER]},
        }
    )
    with pytest.raises(RuntimeError, match="test member"):
        fusion.verify_bundle(tmp_path, manifest_sha256=digest)
    digest = write({**good, "test_included": True})
    with pytest.raises(RuntimeError, match="validation-only"):
        fusion.verify_bundle(tmp_path, manifest_sha256=digest)
    digest = write(good)
    (bundle / "data/images/test").mkdir(parents=True)
    with pytest.raises(RuntimeError, match="test directory"):
        fusion.verify_bundle(tmp_path, manifest_sha256=digest)
    with pytest.raises(RuntimeError, match="manifest differs"):
        fusion.verify_bundle(tmp_path)


def test_pilot_csv_parser_refuses_out_of_scope_rows():
    frames = synthetic_state(groups=1, per_group=1).frames
    header = "stem,rank,yolo_id,conf,x1,y1,x2,y2\n"
    ok = fusion.parse_pilot_csv((header + "s000,0,10,0.5,1,1,20,20\n").encode(), frames)
    assert ok[0].raw["conf"] == "0.5" and ok[0].key == ("s000", 0)
    for body, message in (
        ("other,0,10,0.5,1,1,20,20\n", "non-validation stem"),
        ("s000,0,54,0.5,1,1,20,20\n", "invalid prediction"),
        ("s000,0,10,0.5,1,1,201,20\n", "invalid prediction"),
        ("s000,0,10,nan,1,1,20,20\n", "invalid prediction"),
        ("s000,0,10,0.5,1,1,20,20\ns000,0,10,0.5,1,1,20,20\n", "repeats"),
    ):
        with pytest.raises(RuntimeError, match=message):
            fusion.parse_pilot_csv((header + body).encode(), frames)
    with pytest.raises(RuntimeError, match="schema"):
        fusion.parse_pilot_csv(b"stem,rank\n", frames)


def test_latency_cli_measures_nothing(capsys):
    assert fusion.main(["latency"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["measures"] is False and out["orders_measured"] == [150, 150]
    assert out["first_measured"][0] == ["measured", 0, 50, "AB"]


# ------------------------------------------- QA R1: manifest hashes its own test file


def test_manifest_hashes_module_and_tests_on_the_real_checkout():
    """R1 regression: ``manifest(REPO_ROOT, {})`` raised ``refused sealed-test path``."""
    m = fusion.manifest(ROOT, {})
    assert m["sources"] == {
        str(fusion.MODULE): hashlib.sha256((ROOT / fusion.MODULE).read_bytes()).hexdigest(),
        str(fusion.TESTS): hashlib.sha256((ROOT / fusion.TESTS).read_bytes()).hexdigest(),
    }
    assert m["sources"] == fusion.source_hashes(ROOT)
    assert m["outputs"] == {} and m["flags"] == fusion.FLAGS
    # the data-input guard is unchanged: it still refuses the test path
    with pytest.raises(RuntimeError, match="sealed-test"):
        fusion.regular_file(ROOT, fusion.TESTS)


def test_source_file_is_allow_listed_and_keeps_symlink_and_regular_checks(tmp_path):
    hashes = write_gate_files(tmp_path)
    m = fusion.manifest(tmp_path, {"a.json": b"{}\n"})
    assert m["sources"] == {
        str(fusion.MODULE): hashes["module"],
        str(fusion.TESTS): hashes["tests"],
    }
    assert m["outputs"] == {"a.json": hashlib.sha256(b"{}\n").hexdigest()}
    other = Path("detector/tests/test_other.py")
    (tmp_path / other).write_text("x")
    with pytest.raises(RuntimeError, match="not an allow-listed"):
        fusion._source_file(tmp_path, other)
    with pytest.raises(RuntimeError, match="not an allow-listed"):
        fusion._source_file(tmp_path, fusion.CONTRACT_DOC)
    with pytest.raises(RuntimeError, match="sealed-test"):
        fusion.regular_file(tmp_path, fusion.TESTS)
    tests = tmp_path / fusion.TESTS
    real = tmp_path / "elsewhere.py"
    real.write_text("tests")
    tests.unlink()
    tests.symlink_to(real)  # symlinked file
    with pytest.raises(RuntimeError, match="symlink"):
        fusion.manifest(tmp_path, {})
    tests.unlink()
    with pytest.raises(RuntimeError, match="missing source file"):
        fusion.source_hashes(tmp_path)
    tests.mkdir()  # not a regular file
    with pytest.raises(RuntimeError, match="non-regular"):
        fusion.source_hashes(tmp_path)
    tests.rmdir()
    folder = tmp_path / "detector/tests"
    folder.rename(tmp_path / "real_tests")
    folder.symlink_to(tmp_path / "real_tests")  # symlinked directory in the chain
    (tmp_path / "real_tests" / fusion.TESTS.name).write_text("tests")
    with pytest.raises(RuntimeError, match="symlink"):
        fusion.source_hashes(tmp_path)


def test_run_hashes_sources_before_any_input_is_read(tmp_path, monkeypatch):
    hashes = write_gate_files(tmp_path)
    (tmp_path / fusion.TESTS).unlink()
    rel, digest = write_record(tmp_path, "Verdict: PASS\n" + "\n".join(hashes.values()) + "\n")

    def never(*args, **kwargs):
        raise AssertionError("load_state must not run")

    monkeypatch.setattr(fusion, "load_state", never)
    with pytest.raises(RuntimeError, match="missing source file"):
        fusion.run(tmp_path, rel, digest)
    assert not os.path.lexists(tmp_path / fusion.OUT_DIR)


# ------------------------------------- QA R2–R4: end-to-end synthetic run (gap G-a)


class E2E:
    """A synthetic repository root on which ``run`` reaches ``publish``. Injected: the state
    (synthetic frames, real PNG files), a fake evaluator (crop + AP), a fake classifier, fake
    latency and a forced Step 0 pass. Everything else, including the source-QA gate, the source
    hashes, ``verify_pins``, the shared crop plan, ``build_eval``, ``manifest``,
    ``recheck_before_write``, ``publish`` and ``verify``, is the real code."""

    def __init__(self, root: Path, monkeypatch) -> None:
        import torch

        self.root, self.calls = root, []
        self.hashes = write_gate_files(root)
        self.record, self.digest = write_record(
            root, "Verdict: PASS\n" + "\n".join(self.hashes.values()) + "\n"
        )
        (root / fusion.RUN_DIR).mkdir(parents=True)
        self.classifier = root / fusion.CLASSIFIER
        self.classifier.parent.mkdir(parents=True)
        self.classifier.write_bytes(b"synthetic classifier")
        self.pinned = root / "docs/review/generated/pinned_input.txt"
        self.pinned.parent.mkdir(parents=True)
        self.pinned.write_text("pinned")
        digest = hashlib.sha256(b"synthetic classifier").hexdigest()
        self.pins = {
            fusion.CLASSIFIER: digest,
            Path("docs/review/generated/pinned_input.txt"): hashlib.sha256(b"pinned").hexdigest(),
        }
        monkeypatch.setattr(fusion, "PINS", self.pins)
        monkeypatch.setattr(fusion, "CLASSIFIER_SHA256", digest)
        state = synthetic_state()
        images = {}
        for frame in state.frames:
            path = root / "images" / f"{frame.stem}.png"
            path.parent.mkdir(exist_ok=True)
            Image.new("RGB", (W, H), (40, 80, 120)).save(path)
            images[frame.stem] = path
        self.state = replace(state, images=images)
        self.during_latency = lambda: None

        def fake_ap(frames):
            op = operating_point(frames, fusion.CONF)
            r = sum(op.per_class_hits.values()) / op.ground_truth
            return {"map50": r, "map50_95": r / 2, "per_class_ap50": {"7": r}}

        self.evaluator = type(
            "FakeEvaluator",
            (),
            {
                "crop_prediction": staticmethod(
                    lambda image, box: np.full((32, 32, 3), int(box[0]) % 256, dtype=np.uint8)
                ),
                "average_precision": staticmethod(fake_ap),
            },
        )()

        class FakeClassifier(torch.nn.Module):
            def forward(self, x):
                logits = torch.zeros(x.shape[0], fusion.CLASSES)
                logits[:, 48] = 10.0  # P1 10 -> 48 relabels (p ≈ 0.998); other pairs do not
                return logits

        def load_state(repo_root, full_bundle=True):
            self.calls.append(("load_state", full_bundle))
            return self.state

        def load_classifier(repo_root, device):
            self.calls.append(("load_classifier", device))
            return FakeClassifier().eval()

        real_classify, real_plan = fusion.classify, fusion.crop_plan
        real_step0, real_verify_docs = fusion.step0_check, fusion.verify_documents

        def classify(model, crops, device):
            self.calls.append(("classify", device))
            return real_classify(model, crops, "cpu")  # MPS pass runs on CPU in the test

        def crop_plan(state, crop_fn, image_loader=fusion._read_rgb):
            self.calls.append(("crop_plan",))
            return real_plan(state, crop_fn, image_loader)

        def step0_check(state, evaluator):
            self.calls.append(("step0",))
            return {**real_step0(state, evaluator), "passed": True}

        def measure_latency(repo_root, state):
            self.calls.append(("latency",))
            self.during_latency()
            return synthetic_latency()

        def verify_bundle(repo_root=None, *, full=True, manifest_sha256=None):
            self.calls.append(("verify_bundle", full))
            return {"full": full, "synthetic": True}

        monkeypatch.setattr(fusion, "load_state", load_state)
        monkeypatch.setattr(fusion, "load_evaluator", lambda repo_root: self.evaluator)
        monkeypatch.setattr(fusion, "latency_preflight", lambda repo_root: {"synthetic": True})
        monkeypatch.setattr(fusion, "load_classifier", load_classifier)
        monkeypatch.setattr(fusion, "classify", classify)
        monkeypatch.setattr(fusion, "crop_plan", crop_plan)
        monkeypatch.setattr(fusion, "step0_check", step0_check)
        monkeypatch.setattr(fusion, "measure_latency", measure_latency)
        monkeypatch.setattr(fusion, "verify_bundle", verify_bundle)
        monkeypatch.setattr(
            fusion,
            "verify_documents",
            lambda state, evaluator, files: real_verify_docs(state, evaluator, files, rounds=30),
        )

    def run(self):
        return fusion.run(self.root, self.record, self.digest, rounds=30)

    @property
    def out(self) -> Path:
        return self.root / fusion.OUT_DIR

    def names(self) -> list[str]:
        return [c[0] for c in self.calls]


def test_end_to_end_run_publishes_and_verifies(tmp_path, monkeypatch):
    """QA R3 / gap G-a: run → build_eval → manifest → recheck → publish → verify, no errors."""
    e = E2E(tmp_path, monkeypatch)
    result = e.run()
    assert [w["name"] for w in result["written"]] == list(fusion.OUTPUT_NAMES)
    assert sorted(os.listdir(e.out)) == sorted(fusion.OUTPUT_NAMES)
    assert fusion.verify(tmp_path) == {"verified": True, "errors": []}
    manifest = json.loads((e.out / fusion.MANIFEST_NAME).read_bytes())
    assert manifest["sources"] == {
        str(fusion.MODULE): e.hashes["module"],
        str(fusion.TESTS): e.hashes["tests"],
    }
    assert manifest["inputs"] == {str(k): v for k, v in e.pins.items()}
    for name in fusion.OUTPUT_NAMES[:-1]:
        digest = hashlib.sha256((e.out / name).read_bytes()).hexdigest()
        assert manifest["outputs"][name] == digest
    # R4: the crop plan is built once, before Step 0 and before any classifier is loaded
    names = e.names()
    assert names.index("crop_plan") < names.index("step0") < names.index("load_classifier")
    assert names.count("crop_plan") == 1
    assert [c for c in e.calls if c[0] == "load_classifier"] == [
        ("load_classifier", "cpu"),
        ("load_classifier", "mps"),
    ]
    # R2: the used bundle members are re-verified (full=False) after the latency arm
    assert [c for c in e.calls if c[0] == "verify_bundle"] == [("verify_bundle", False)]
    assert names.index("latency") < names.index("verify_bundle")
    assert result["recheck_before_write"]["pins_verified"] == len(e.pins)
    doc = json.loads((e.out / fusion.EVAL_NAME).read_bytes())
    assert doc["reported"]["per_pair"]["P1"]["relabelled_all_scores"] > 0
    assert doc["arm_a"]["false_positives"] == doc["arm_b"]["false_positives"]
    assert doc["latency"]["L"] is True
    # a tampered output after publication is detected by verify
    path = e.out / fusion.PREDICTIONS_NAME
    os.chmod(path, 0o644)
    path.write_bytes(path.read_bytes() + b"x")
    assert fusion.verify(tmp_path)["verified"] is False
    with pytest.raises(RuntimeError, match="output already exists"):
        e.run()


def _mutate(path: Path) -> None:
    path.write_bytes(path.read_bytes() + b" changed")


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("pin", "pinned fusion R1 input differs"),
        ("classifier_pinned", "pinned fusion R1 input differs"),
        ("classifier_explicit", "classifier best.pt changed"),
        ("module", "module or tests changed"),
        ("tests", "module or tests changed"),
        ("bundle", "bundle member differs"),
    ],
)
def test_a_pin_changed_mid_run_blocks_every_write(tmp_path, monkeypatch, case, message):
    """QA R2 / gap G-c: a mismatch found by the pre-write re-check aborts with no output."""
    e = E2E(tmp_path, monkeypatch)
    if case == "classifier_explicit":  # exercise the explicit classifier check on its own
        del e.pins[fusion.CLASSIFIER]
    targets = {
        "pin": e.pinned,
        "classifier_pinned": e.classifier,
        "classifier_explicit": e.classifier,
        "module": tmp_path / fusion.MODULE,
        "tests": tmp_path / fusion.TESTS,
    }
    if case == "bundle":

        def bad_bundle(repo_root=None, *, full=True, manifest_sha256=None):
            raise RuntimeError("bundle member differs from its manifest: data/val_groups.json")

        e.during_latency = lambda: monkeypatch.setattr(fusion, "verify_bundle", bad_bundle)
    else:
        e.during_latency = lambda: _mutate(targets[case])
    with pytest.raises(RuntimeError, match=message):
        e.run()
    assert "latency" in e.names()  # the change happened after the metrics inputs existed
    assert not os.path.lexists(e.out)
    assert not [p for p in (tmp_path / fusion.RUN_DIR).iterdir()]  # no staging left either


def test_cpu_softmax_violation_is_invalid_with_a_stop_report_only(tmp_path, monkeypatch):
    """QA R4: the parse_probs_csv sum tolerance becomes INVALID, recorded, no result files."""
    e = E2E(tmp_path, monkeypatch)
    real = fusion.classify

    def off_by_more_than_tolerance(model, crops, device):
        p = real(model, crops, device)
        return (p * np.float32(1.001)).astype(np.float32) if device == "cpu" else p

    monkeypatch.setattr(fusion, "classify", off_by_more_than_tolerance)
    result = e.run()
    assert (result["outcome"], result["outcome_row"], result["stage"]) == (
        "INVALID",
        1,
        "crop_probabilities",
    )
    assert result["written"] == []  # main() maps an empty `written` to exit code 2
    assert os.listdir(e.out) == [fusion.STOP_REPORT_NAME]
    report = json.loads((e.out / fusion.STOP_REPORT_NAME).read_bytes())
    assert report["outcome"] == "INVALID" and report["result_files_written"] is False
    assert report["detail"]["rows"] and report["flags"] == fusion.FLAGS
    assert report["sources"] == fusion.source_hashes(tmp_path)
    assert ("load_classifier", "mps") not in e.calls and "latency" not in e.names()
    assert [c for c in e.calls if c[0] == "verify_bundle"] == [("verify_bundle", False)]
    assert fusion.verify(tmp_path)["verified"] is False
    with pytest.raises(RuntimeError, match="output already exists"):
        e.run()


def test_cpu_mps_crop_set_mismatch_is_invalid_with_a_stop_report_only(tmp_path, monkeypatch):
    """QA R4: both passes share one crop plan; a mismatch anyway is INVALID, not a raise."""
    e = E2E(tmp_path, monkeypatch)
    real = fusion.classify_candidates
    plans = []

    def drop_one_on_mps(state, model, device, crop_fn=None, image_loader=None, *, plan=None):
        plans.append(plan)
        probs, invalid = real(state, model, device, plan=plan)
        if device == "mps":
            probs.pop(next(iter(probs)))
        return probs, invalid

    monkeypatch.setattr(fusion, "classify_candidates", drop_one_on_mps)
    result = e.run()
    assert (result["outcome"], result["stage"], result["written"]) == (
        "INVALID",
        "cpu_mps_crop_set",
        [],
    )
    assert len(plans) == 2 and plans[0] is plans[1] and plans[0] is not None
    assert len(result["detail"]["symmetric_difference"]) == 1
    assert os.listdir(e.out) == [fusion.STOP_REPORT_NAME]
    assert "latency" not in e.names()


def test_g5_zero_support_refuses_before_step0_and_the_classifier(tmp_path, monkeypatch):
    """QA R4: the G5 zero-support raise is pre-checked model-free, before Step 0."""
    e = E2E(tmp_path, monkeypatch)
    frames = [
        replace(f, gt_classes=np.where(f.gt_classes == 6, 5, f.gt_classes)) for f in e.state.frames
    ]
    e.state = replace(e.state, frames=frames)
    with pytest.raises(RuntimeError, match="G5 class DK 6 has no validation support"):
        e.run()
    assert "step0" not in e.names() and "load_classifier" not in e.names()
    assert not os.path.lexists(e.out)
    support = fusion.precheck_g5_support(synthetic_state())
    assert set(support) == set(fusion.G5_DERIVED_KEYS) and min(support.values()) > 0


def test_softmax_predicate_matches_parse_probs_csv():
    state = synthetic_state(groups=1, per_group=1)
    probs = synthetic_probs(state)
    assert fusion.softmax_violations(probs) == []
    key = next(iter(probs))
    for factor, ok in ((1.0 + 5e-6, True), (1.0 + 5e-5, False)):
        bad = dict(probs)
        bad[key] = (probs[key].astype(np.float64) * factor).astype(np.float32)
        data = fusion.probs_csv(state.rows, bad, state.names)
        assert (fusion.softmax_violations(bad) == []) is ok
        if ok:
            fusion.parse_probs_csv(data, state.rows)
        else:
            assert fusion.softmax_violations(bad) == [[key[0], key[1]]]
            with pytest.raises(RuntimeError, match="exact float32 softmax"):
                fusion.parse_probs_csv(data, state.rows)
    nan = dict(probs)
    nan[key] = probs[key].copy()
    nan[key][0] = np.nan
    assert fusion.softmax_violations(nan) == [[key[0], key[1]]]
    assert fusion.softmax_violations({key: probs[key].astype(np.float64)}) == [[key[0], key[1]]]
