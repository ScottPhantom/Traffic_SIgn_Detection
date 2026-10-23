from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from m1 import val_relabel_r1 as vrl
from m1.metrics import Frame


def _frame(gt: list[list[float]], preds: list[list[float]], scores: list[float]) -> Frame:
    return Frame(
        "a",
        "G",
        np.asarray(gt, float).reshape(-1, 4),
        np.zeros(len(gt), int),
        np.asarray(preds, float).reshape(-1, 4),
        np.zeros(len(preds), int),
        np.asarray(scores, float),
        100,
        80,
    )


def test_components_are_eight_connected() -> None:
    mask = np.zeros((6, 6), bool)
    mask[0, 0] = mask[1, 1] = True  # diagonal neighbours: one component
    mask[4, 4] = mask[4, 5] = True
    assert vrl.components(mask) == [(0, 0, 2, 2), (4, 4, 6, 5)]


def test_refine_box_fits_red_disc_and_refuses_without_colour() -> None:
    rgb = np.full((60, 60, 3), 128, np.uint8)
    rgb[20:36, 22:40] = (220, 30, 30)
    image = Image.fromarray(rgb)
    assert vrl.refine_box(image, (18.0, 18.0, 38.0, 38.0)) == (22, 20, 40, 36)
    assert (
        vrl.refine_box(Image.fromarray(np.full((60, 60, 3), 128, np.uint8)), (18, 18, 38, 38))
        is None
    )


def test_unmatched_predictions_follow_greedy_score_order() -> None:
    frame = _frame(
        [[0, 0, 10, 10]], [[0, 0, 10, 10], [1, 0, 10, 10], [50, 50, 60, 60]], [0.5, 0.9, 0.1]
    )
    out = vrl.unmatched_predictions(frame, 0.2)
    # the higher-scored duplicate takes the ground truth; the 0.1 box is below conf
    assert [b.tolist() for b in out] == [[0.0, 0.0, 10.0, 10.0]]


def test_verify_pins_and_append_only(tmp_path) -> None:
    for relative in vrl.PINNED:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="pinned D1-VRL-R1 source differs"):
        vrl.verify_pins(tmp_path)
    (tmp_path / vrl.MANIFEST_PATH).write_text("{}")
    with pytest.raises(RuntimeError, match="append-only"):
        vrl.build(tmp_path)


def test_official_package_verifies_and_counts() -> None:
    result = vrl.verify()
    assert result["valid"], result["errors"]
    added = vrl._read_csv(vrl.REPO_ROOT / vrl.ADDED_PATH)
    ignored = vrl._read_csv(vrl.REPO_ROOT / vrl.IGNORE_PATH)
    assert (len(added), len(ignored)) == (26, 78)
    # QA L2 of D1-VLA-R1: ids are YOLO ids, not derived keys
    assert {
        (r["derived_key"], r["yolo_id"]) for r in added if r["derived_key"] in {"23", "39", "41"}
    } <= {
        ("23", "25"),
        ("39", "40"),
        ("41", "42"),
    }
