from __future__ import annotations

import numpy as np
import pytest

from m1 import nms_045_paired_test_r1 as t
from m1.metrics import Frame


def _frame(stem, group, gt, gt_cls, pred, pred_cls, scores):
    return Frame(
        stem,
        group,
        np.asarray(gt, dtype=float).reshape(-1, 4),
        np.asarray(gt_cls, dtype=int),
        np.asarray(pred, dtype=float).reshape(-1, 4),
        np.asarray(pred_cls, dtype=int),
        np.asarray(scores, dtype=float),
        100,
        100,
    )


def _passing_inputs():
    test = {
        "fp_per_image": {"ci95": [-0.06, -0.01]},
        "agnostic_recall": {"candidate": 0.8766, "difference": 0.0},
        "map50_95": {"ci95": [-0.002, 0.003]},
    }
    groups = [{"correct": {"difference": 0}, "fp": {"difference": -1}} for _ in range(9)]
    folds = [{"selection": t.CANDIDATE} for _ in range(9)]
    exposure = {"matched_at_0_70_but_not_0_45": 0}
    return test, groups, folds, exposure


def test_decide_supported_only_when_every_condition_holds():
    out = t.decide(*_passing_inputs())
    assert out["decision"] == "SUPPORTED_ON_VALIDATION"
    assert out["failed"] == []


@pytest.mark.parametrize(
    "mutate, failed",
    [
        (lambda a: a[0]["fp_per_image"].update(ci95=[-0.05, 0.0]), "c1_fp_ci_upper_below_zero"),
        (lambda a: a[1][3]["correct"].update(difference=-1), "c2_no_group_loses_correct_hits"),
        (lambda a: a[0]["agnostic_recall"].update(candidate=0.84), "c3_agnostic_recall_ok"),
        (lambda a: a[0]["agnostic_recall"].update(difference=-0.002), "c3_agnostic_recall_ok"),
        (
            lambda a: a[0]["map50_95"].update(ci95=[-0.02, -0.001]),
            "c4_map50_95_ci_not_wholly_below_zero",
        ),
        (
            lambda a: [f.update(selection=t.BASELINE) for f in a[2][:3]],
            "c5_logo_selects_0_45_in_7_of_9",
        ),
        (lambda a: a[1][0]["fp"].update(difference=1), "c6_no_group_gains_fp"),
        (lambda a: a[3].update(matched_at_0_70_but_not_0_45=1), "c7_no_paired_gt_lost"),
    ],
)
def test_decide_each_condition_can_fail(mutate, failed):
    args = _passing_inputs()
    mutate(args)
    out = t.decide(*args)
    assert out["decision"] == "NOT_SUPPORTED"
    assert failed in out["failed"]


def test_logo_two_of_nine_baseline_still_passes_c5():
    args = _passing_inputs()
    for fold in args[2][:2]:
        fold["selection"] = t.BASELINE
    assert t.decide(*args)["conditions"]["c5_logo_selects_0_45_in_7_of_9"]


def test_gt_pair_exposure_detects_lost_neighbour():
    gt = [[10, 10, 30, 30], [12, 12, 32, 32]]  # IoU about 0.68
    base = _frame("a", "g", gt, [1, 1], gt, [1, 1], [0.9, 0.8])
    cand = _frame("a", "g", gt, [1, 1], gt[:1], [1], [0.9])  # second sign suppressed
    out = t.gt_pair_exposure([cand], [base])
    assert out["pairs"] == 1
    assert out["gt_in_pairs"] == 2
    assert out["matched_at_0_70_but_not_0_45"] == 1


def test_gt_pair_exposure_ignores_separate_signs():
    gt = [[0, 0, 10, 10], [50, 50, 60, 60]]
    frame = _frame("a", "g", gt, [1, 2], gt, [1, 2], [0.9, 0.9])
    out = t.gt_pair_exposure([frame], [frame])
    assert out["pairs"] == 0 and out["detail"] == []


def test_box_audit_counts_removed_boxes_and_changed_frames():
    gt = [[10, 10, 30, 30]]
    base = _frame("a", "g", gt, [1], [[10, 10, 30, 30], [11, 11, 31, 31]], [1, 1], [0.9, 0.5])
    cand = _frame("a", "g", gt, [1], [[10, 10, 30, 30]], [1], [0.9])
    out = t.box_audit([cand], [base])
    assert out["boxes_at_conf_020_removed_by_0_45"] == 1
    assert out["boxes_at_conf_020_added_by_0_45"] == 0
    assert out["frames_with_changed_gt_matches"] == []


def test_box_audit_ignores_boxes_below_operating_confidence():
    gt = [[10, 10, 30, 30]]
    base = _frame("a", "g", gt, [1], [[10, 10, 30, 30], [60, 60, 70, 70]], [1, 2], [0.9, 0.1])
    cand = _frame("a", "g", gt, [1], [[10, 10, 30, 30]], [1], [0.9])
    assert t.box_audit([cand], [base])["boxes_at_conf_020_removed_by_0_45"] == 0


def test_pins_cover_both_csvs_and_reused_modules():
    assert {t.CANDIDATE, t.BASELINE, "nms_sweep_module", "paired_ci_module"} <= set(t.PINS)
    assert t.CONF == 0.20 and t.ROUNDS == 1000 and t.SEED == 20261018


def test_check_pins_refuses_a_changed_csv(monkeypatch, tmp_path):
    fake = tmp_path / "x.csv"
    fake.write_text("stem\n")
    monkeypatch.setitem(t.PINS, t.CANDIDATE, (fake, "0" * 64))
    with pytest.raises(RuntimeError, match="pinned input differs"):
        t.check_pins()
