"""Frozen two-seed selection behavior, without model inference."""

import numpy as np
import pytest

from m1 import two_seed_provisional_threshold_r1 as provisional


def _cell(name, iou, agnostic, conf, recall, fp, ap):
    return {
        "configuration": name,
        "iou": iou,
        "agnostic_nms": agnostic,
        "confidence": conf,
        "mean_agnostic_recall": recall,
        "mean_fp_per_image": fp,
        "mean_map50_95": ap,
    }


def test_grid_is_frozen_union_with_no_duplicate():
    grid = provisional.selection_grid()
    assert grid == tuple(sorted(set(grid)))
    assert len(grid) == 31
    assert grid[0] == 0.05 and grid[-1] == 0.95
    assert all(x in grid for x in (0.15, 0.16, 0.17, 0.20, 0.25, 0.30))
    assert 0.31 not in grid


def test_selection_uses_mean_recall_and_frozen_ties():
    cells = [
        _cell("base", 0.70, False, 0.25, 0.84, 0.1, 0.8),
        _cell("low", 0.65, False, 0.20, 0.85, 0.2, 0.9),
        _cell("high", 0.75, False, 0.25, 0.85, 0.2, 0.8),
        _cell("more_ap", 0.70, False, 0.25, 0.85, 0.2, 0.9),
    ]
    assert provisional.choose(cells)["configuration"] == "more_ap"
    assert provisional.choose(cells[:1]) is None


def test_selection_final_nms_ties_and_adjacent_votes():
    cells = [
        _cell("classaware_0.80", 0.80, False, 0.20, 0.86, 0.3, 0.7),
        _cell("agnostic_0.80", 0.80, True, 0.20, 0.86, 0.3, 0.7),
    ]
    assert provisional.choose(cells)["configuration"] == "classaware_0.80"
    folds = [
        {"selected_configuration": "classaware_0.65"},
        {"selected_configuration": "classaware_0.70"},
        {"selected_configuration": "classaware_0.75"},
        {"selected_configuration": "agnostic_0.80"},
        {"selected_configuration": None},
    ]
    assert provisional.adjacent_votes(folds, "classaware_0.70") == 3


def test_mean_is_arithmetic_and_fallback_requires_all_three_conditions():
    a = {"agnostic_recall": 0.9, "fp_per_image": 0.4}
    b = {"agnostic_recall": 0.8, "fp_per_image": 0.2}
    cell = provisional.score_cell(a, b, 0.55, "classaware_0.65", 0.20)
    assert cell["mean_agnostic_recall"] == pytest.approx(0.85)
    assert cell["mean_fp_per_image"] == pytest.approx(0.3)
    assert cell["seed_difference_19_minus_18"]["agnostic_recall"] < 0
    selected = {"configuration": "classaware_0.65"}
    baseline = {"configuration": "classaware_0.70"}
    folds = [{"selected_configuration": "classaware_0.65"}] * 7 + [
        {"selected_configuration": None}
    ] * 2
    ci = {"fp_per_image_ci95": [-0.2, -0.01], "map50_95_ci95": [-0.1, 0.01]}
    assert provisional.decide_change(selected, baseline, ci, folds)["provisional"] is selected
    bad = {**ci, "fp_per_image_ci95": [-0.2, 0.01]}
    assert provisional.decide_change(selected, baseline, bad, folds)["provisional"] is baseline
    bad = {**ci, "map50_95_ci95": [-0.1, -0.01]}
    assert provisional.decide_change(selected, baseline, bad, folds)["provisional"] is baseline
    assert provisional.decide_change(selected, baseline, ci, folds[:6])["provisional"] is baseline


def test_bootstrap_uses_same_draw_for_two_seeds_and_both_settings(monkeypatch):
    base, new = "classaware_0.70", "classaware_0.65"
    frames = {
        seed: {base: f"{seed}-{base}", new: f"{seed}-{new}"}
        for seed in ("seed_20261018", "seed_20261019")
    }
    samples = [np.array([0, 1]), np.array([1, 1])]
    seen = []

    def fake_stats(value, confidence):
        fp = 1.0 if base in value else 0.0
        return {"gt": np.ones(2), "agnostic_hits": np.ones(2), "fp": np.full(2, fp)}

    def fake_map(value, correct, indices):
        seen.append((value, tuple(indices)))
        return (0.7 if base in value else 0.8) + float(indices.sum()) / 100

    monkeypatch.setattr(provisional.ci, "resample_indices", lambda *args: samples)
    monkeypatch.setattr(provisional.ci, "frame_stats", fake_stats)
    monkeypatch.setattr(provisional.ci, "_correct_matrices", lambda value: None)
    monkeypatch.setattr(provisional.ci, "_map50_95", fake_map)
    monkeypatch.setattr(provisional, "ROUNDS", 2)
    selected = {
        "configuration": new,
        "confidence": 0.2,
        "mean_fp_per_image": 0.0,
        "mean_map50_95": 0.8,
    }
    baseline = {
        "configuration": base,
        "confidence": 0.1,
        "mean_fp_per_image": 1.0,
        "mean_map50_95": 0.7,
    }
    result = provisional.bootstrap_change(frames, selected, baseline)
    assert result["rounds"] == 2
    assert result["fp_per_image_ci95"] == [-1.0, -1.0]
    assert [draw for _, draw in seen] == [
        (0, 1),
        (0, 1),
        (0, 1),
        (0, 1),
        (1, 1),
        (1, 1),
        (1, 1),
        (1, 1),
    ]
