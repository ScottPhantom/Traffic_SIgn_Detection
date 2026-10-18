from __future__ import annotations

import numpy as np
import pytest

from m1 import cli, contract
from m1.metrics import Frame, latency_stats, match, operating_point, select_threshold


def frame(
    gt: list[list[float]],
    gt_cls: list[int],
    pred: list[list[float]],
    pred_cls: list[int],
    scores: list[float],
    group: str = "G1",
) -> Frame:
    return Frame(
        stem="x",
        group_id=group,
        gt_boxes=np.array(gt, dtype=float).reshape(-1, 4),
        gt_classes=np.array(gt_cls, dtype=int),
        pred_boxes=np.array(pred, dtype=float).reshape(-1, 4),
        pred_classes=np.array(pred_cls, dtype=int),
        pred_scores=np.array(scores, dtype=float),
    )


def test_class_aware_match_rejects_wrong_class_but_agnostic_accepts() -> None:
    f = frame([[0, 0, 10, 10]], [3], [[0, 0, 10, 10]], [5], [0.9])
    aware, aware_fp = match(f, 0.5, class_aware=True)
    agnostic, agnostic_fp = match(f, 0.5, class_aware=False)
    assert not aware[0] and aware_fp == 1
    assert agnostic[0] and agnostic_fp == 0


def test_duplicate_prediction_counts_as_false_positive() -> None:
    f = frame([[0, 0, 10, 10]], [1], [[0, 0, 10, 10], [1, 1, 10, 10]], [1, 1], [0.9, 0.8])
    matched, false_positives = match(f, 0.5, class_aware=True)
    assert matched.all() and false_positives == 1


def test_operating_point_and_threshold_selection() -> None:
    frames = [
        frame([[0, 0, 10, 10]], [1], [[0, 0, 10, 10]], [1], [0.9]),
        frame([[0, 0, 10, 10]], [2], [[0, 0, 10, 10], [50, 50, 60, 60]], [2, 2], [0.3, 0.2]),
    ]
    low = operating_point(frames, 0.1)
    assert low.agnostic_recall == 1.0 and low.fp_per_image == 0.5
    chosen = select_threshold(frames, 0.85, grid=[0.1, 0.25, 0.5])
    assert chosen.conf == 0.25 and chosen.fp_per_image == 0.0
    fallback = select_threshold(frames, 0.99, grid=[0.5, 0.95])
    assert fallback.agnostic_recall == 0.5


def test_latency_stats() -> None:
    stats = latency_stats(list(range(1, 101)))
    assert stats["n"] == 100 and stats["p95_ms"] == pytest.approx(95.05)


def test_contract_binds_d05_and_export() -> None:
    bound = contract.check_contract()
    assert bound["split_stem_sha256"]["test"].startswith("afa03d4b")
    assert contract.FORBIDDEN_OVERRIDES == {"fliplr": 0.0}
    assert set(contract.CRITICAL_KEYS) <= set(contract.class_ids())


def test_train_refuses_non_d05_seed() -> None:
    with pytest.raises(SystemExit, match="not one of the D-05 seeds"):
        cli.main(["train", "--seed", "1"])


def test_evaluate_test_refused_without_final_eval() -> None:
    with pytest.raises(SystemExit, match="refused"):
        cli.main(["evaluate", "--weights", "missing.pt", "--split", "test"])
