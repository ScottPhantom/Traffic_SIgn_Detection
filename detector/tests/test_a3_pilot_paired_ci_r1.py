"""Tests for the paired A3 − pilot validation bootstrap (D1-A3-PILOT-PAIRED-CI-R1)."""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from m1 import a3_pilot_paired_ci_r1 as paired
from m1.metrics import Frame, group_bootstrap, operating_point


def _frame(stem: str, group: str, gt: list[int], preds: list[tuple[int, float, bool]]) -> Frame:
    """GT boxes sit on a diagonal; a prediction either overlaps its GT box exactly or misses."""
    gt_boxes = np.asarray([[10 * i, 10 * i, 10 * i + 8, 10 * i + 8] for i in range(len(gt))])
    boxes, classes, scores = [], [], []
    for index, (cls, score, hit) in enumerate(preds):
        boxes.append(gt_boxes[index] if hit else [500, 500, 508, 508])
        classes.append(cls)
        scores.append(score)
    return Frame(
        stem,
        group,
        gt_boxes.reshape(-1, 4).astype(float),
        np.asarray(gt, dtype=int),
        np.asarray(boxes, dtype=float).reshape(-1, 4),
        np.asarray(classes, dtype=int),
        np.asarray(scores, dtype=float),
        600,
        600,
    )


def _synthetic(shift: float = 0.0) -> list[Frame]:
    rng = np.random.default_rng(7)
    frames = []
    for i in range(30):
        group = f"G{i % 5}"
        gt = [int(rng.integers(0, 3)), int(rng.integers(0, 3))]
        preds = [
            (gt[0] if rng.random() > 0.3 else 5, float(min(1.0, rng.random() + shift)), True),
            (gt[1], float(rng.random()), bool(rng.random() > 0.4)),
        ]
        frames.append(_frame(f"{i:04d}", group, gt, preds))
    return frames


def test_frame_stats_sum_equals_operating_point():
    frames = _synthetic()
    stats = paired.frame_stats(frames, 0.20)
    summary = paired.summarize(stats, np.arange(len(frames)))
    point = operating_point(frames, 0.20)
    assert summary["agnostic_recall"] == point.agnostic_recall
    assert summary["fp_per_image"] == point.fp_per_image
    assert summary["correct_class_recall"] == sum(point.per_class_hits.values()) / len(
        [c for f in frames for c in f.gt_classes]
    )


def test_identical_models_have_zero_width_paired_interval():
    frames = _synthetic()
    stats = paired.frame_stats(frames, 0.20)
    samples = paired.resample_indices(frames, 200, 20261018)
    block = paired.paired_block(stats, stats, samples)
    for metric in paired.METRICS:
        assert block[metric]["paired_ci95"] == [0.0, 0.0]
        assert block[metric]["ci_excludes_zero"] is False


def test_marginals_reproduce_per_model_group_bootstrap():
    a3, pilot = _synthetic(), _synthetic(shift=0.2)
    samples = paired.resample_indices(a3, 300, 11)
    block = paired.paired_block(
        paired.frame_stats(a3, 0.20), paired.frame_stats(pilot, 0.20), samples
    )
    for label, frames in (("a3", a3), ("pilot", pilot)):
        reference = group_bootstrap(frames, 0.20, rounds=300, seed=11)
        for metric in ("agnostic_recall", "fp_per_image"):
            got = block[metric][f"{label}_marginal_ci95"]
            pairs = zip(got, reference[metric], strict=True)
            assert all(math.isclose(g, w, abs_tol=1e-12) for g, w in pairs)


def test_resampling_unit_is_whole_group():
    frames = _synthetic()
    by_group = {}
    for index, frame in enumerate(frames):
        by_group.setdefault(frame.group_id, set()).add(index)
    for sample in paired.resample_indices(frames, 50, 3):
        drawn = [frames[i].group_id for i in sample]
        for group in set(drawn):
            assert drawn.count(group) % len(by_group[group]) == 0


@pytest.mark.parametrize(
    ("interval", "expected"),
    [([-0.2, 0.003], False), ([-0.1, -0.01], True), ([0.0, 0.1], False), ([0.01, 0.2], True)],
)
def test_excludes_zero(interval, expected):
    assert paired.excludes_zero(interval) is expected


def test_focus_class_support_flags():
    # class 1 lives only in group G0; class 2 has no support at all.
    frames = [
        _frame("a", "G0", [1, 0], [(1, 0.9, True), (0, 0.9, True)]),
        _frame("b", "G1", [0], [(0, 0.9, True)]),
        _frame("c", "G2", [0], [(0, 0.1, True)]),
    ]
    stats = paired.frame_stats(frames, 0.20)
    samples = paired.resample_indices(frames, 100, 5)
    block = paired.paired_block(stats, stats, samples, {"one": 1, "two": 2, "zero": 0})
    classes = block["per_class_correct_class_recall"]
    assert classes["two"]["status"] == "UNKNOWN_NO_VALIDATION_SUPPORT"
    assert classes["two"]["ci_interpretable"] is False
    assert classes["one"]["status"] == "DEGENERATE_SINGLE_GROUP_CI_NOT_INFORMATIVE"
    assert classes["one"]["low_support"] is True
    assert classes["zero"]["status"] == "ESTIMATED"
    assert classes["zero"]["groups_with_support"] == 3


def test_require_rejects_changed_file(tmp_path):
    target = tmp_path / "x.csv"
    target.write_text("stem\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="pinned input differs"):
        paired._require(target, "0" * 64, "x")


def test_canonical_json_is_sorted_and_finite():
    text = paired.canonical({"b": 1.0, "a": [0.5, None]})
    assert text.index('"a"') < text.index('"b"') and text.endswith("\n")
    with pytest.raises(ValueError):
        paired.canonical({"a": float("nan")})


BUNDLE_PRESENT = (paired.REPO_ROOT / paired.BUNDLE / "manifest.json").is_file()


@pytest.mark.skipif(not BUNDLE_PRESENT, reason="pinned validation bundle not extracted locally")
def test_published_json_recomputes_byte_for_byte():
    assert paired.main(["verify"]) == 0
    payload = json.loads((paired.REPO_ROOT / paired.OUT).read_text(encoding="utf-8"))
    assert payload["sealed_test_accessed"] is False
    assert payload["inference_run"] is False
    assert payload["bootstrap"]["rounds"] == 1000 and payload["bootstrap"]["seed"] == 20261018
    assert payload["groups"] == 9
    pilot = payload["reproduction_check"]["pilot"]
    assert (pilot["true_positives_020"], pilot["false_positives_020"]) == (547, 150)
    assert pilot["correct_class_hits_020"] == 457
    a3 = payload["reproduction_check"]["a3"]
    assert (a3["true_positives_020"], a3["false_positives_020"]) == (489, 86)
    assert payload["validation_selected_recall_085"]["label"] == (
        "VALIDATION_SELECTED_DIAGNOSTIC_ONLY"
    )
