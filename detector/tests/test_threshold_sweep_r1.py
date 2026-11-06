"""Validation-only confidence sweep guards; no model inference."""

from __future__ import annotations

import numpy as np

from m1.metrics import Frame, group_bootstrap
from m1.threshold_sweep_r1 import GRID, choose, grouped_bootstrap, interpolate, pilot_cells


def test_grid_includes_one_and_pilot_is_reused_from_qa_json() -> None:
    cells, result = pilot_cells()
    assert len(GRID) == len(cells) == 20
    assert GRID[0] == 0.05 and GRID[-1] == 1.0
    assert cells == result["configurations"]["classaware_0.70"]["cells"]
    assert (cells[3]["tp"], cells[3]["fp"], cells[3]["correct_class_hits"]) == (547, 150, 457)


def test_d05_selection_and_no_eligible_point() -> None:
    cells = [
        {"confidence": 0.05, "agnostic_recall": 0.90, "fp_per_image": 0.25},
        {"confidence": 0.10, "agnostic_recall": 0.85, "fp_per_image": 0.25},
        {"confidence": 0.15, "agnostic_recall": 0.80, "fp_per_image": 0.20},
    ]
    assert choose(cells)["cell"]["confidence"] == 0.10
    assert choose(cells[2:])["status"] == "NO_POINT_MEETS_RECALL_0_85"


def test_interpolation_never_extrapolates() -> None:
    cells = [
        {
            "confidence": 0.05,
            "fp_per_image": 0.30,
            "agnostic_recall": 0.90,
            "correct_class_recall": 0.70,
        },
        {
            "confidence": 0.10,
            "fp_per_image": 0.20,
            "agnostic_recall": 0.80,
            "correct_class_recall": 0.60,
        },
    ]
    assert interpolate(cells, 0.25) == {
        "agnostic_recall": 0.8500000000000001,
        "correct_class_recall": 0.6499999999999999,
        "between": [0.05, 0.10],
    }
    assert interpolate(cells, 0.35) is None


def test_grouped_bootstrap_matches_project_method() -> None:
    frames = [
        Frame(
            stem=str(i),
            group_id=f"G{i}",
            gt_boxes=np.array([[0, 0, 10, 10]], dtype=float),
            gt_classes=np.array([i % 2]),
            pred_boxes=np.array([[0, 0, 10, 10]], dtype=float),
            pred_classes=np.array([i % 2]),
            pred_scores=np.array([0.30 if i % 3 else 0.10]),
        )
        for i in range(9)
    ]
    fast = grouped_bootstrap(frames, 0.20)
    direct = group_bootstrap(frames, 0.20, rounds=1000, seed=20261018)
    assert fast == {key: list(value) for key, value in direct.items()}
