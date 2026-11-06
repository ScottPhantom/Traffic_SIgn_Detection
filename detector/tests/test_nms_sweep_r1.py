"""Regression tests for the validation-only NMS sweep selection and baseline gate."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from m1.metrics import Frame
from m1.nms_sweep_r1 import BASE, CONFIGS, GRID, adjacent_votes, baseline_gate, choose, key, select


def test_grid_and_configuration_scope() -> None:
    assert len(CONFIGS) == 11
    assert len(set(CONFIGS)) == 11
    assert BASE in CONFIGS
    assert GRID == tuple(round(i / 100, 2) for i in range(5, 101, 5))
    assert len(GRID) * len(CONFIGS) == 220


def test_selection_requires_recall_and_uses_fp_then_highest_confidence() -> None:
    cells = [
        {"confidence": 0.05, "agnostic_recall": 0.84, "fp_per_image": 0.01},
        {"confidence": 0.10, "agnostic_recall": 0.85, "fp_per_image": 0.30},
        {"confidence": 0.15, "agnostic_recall": 0.86, "fp_per_image": 0.30},
        {"confidence": 0.20, "agnostic_recall": 0.85, "fp_per_image": 0.35},
    ]
    assert select(cells) == cells[2]
    assert select(cells[:1]) is None


def test_configuration_ties_use_map_then_distance_to_baseline() -> None:
    settings = {
        "a": {
            "selected": {"fp_per_image": 0.25},
            "ap": {"map50_95": 0.61},
            "iou": 0.65,
            "agnostic_nms": False,
        },
        "b": {
            "selected": {"fp_per_image": 0.25},
            "ap": {"map50_95": 0.62},
            "iou": 0.45,
            "agnostic_nms": False,
        },
        "c": {
            "selected": {"fp_per_image": 0.25},
            "ap": {"map50_95": 0.62},
            "iou": 0.70,
            "agnostic_nms": False,
        },
        "d": {"selected": None, "ap": {"map50_95": 1.0}, "iou": 0.75, "agnostic_nms": False},
    }
    assert choose(settings) == "c"


def test_adjacent_votes_do_not_cross_nms_modes() -> None:
    winner = key((0.80, True))
    folds = [
        {"selection": name}
        for name in (
            key((0.80, True)),
            key((0.85, True)),
            key((0.80, False)),
            None,
        )
    ]
    assert adjacent_votes(folds, winner) == 2


def test_baseline_equivalence_fails_closed_on_count_or_map() -> None:
    frame = Frame(
        "sample",
        "group",
        np.array([[0.0, 0.0, 10.0, 10.0]]),
        np.array([0]),
        np.array([[0.0, 0.0, 10.0, 10.0]]),
        np.array([0]),
        np.array([0.9]),
        10,
        10,
    )
    scorer = SimpleNamespace(average_precision=lambda _: {"map50": 0.8521, "map50_95": 0.6089})
    with pytest.raises(RuntimeError, match="baseline equivalence failed"):
        baseline_gate([frame], [frame], scorer)
