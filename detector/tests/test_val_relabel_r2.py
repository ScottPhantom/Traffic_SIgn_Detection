from __future__ import annotations

import pytest

from m1 import val_relabel_r1 as r1
from m1 import val_relabel_r2 as vrl

SMALL = (10.0, 10.0, 25.0, 24.0)  # longer side 15 px
LARGE = (10.0, 10.0, 40.0, 38.0)  # longer side 30 px


def _note(decision: str, box: tuple[int, int, int, int] | None = None) -> dict[str, str]:
    x1, y1, x2, y2 = (str(v) for v in box) if box else ("", "", "", "")
    return {
        "proposal_id": "R001",
        "box_decision": decision,
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "note": "seen",
    }


def test_size_rule_separates_ignore_from_hand_drawn() -> None:
    assert vrl.check_box_decision(_note("IGNORE_REGION"), SMALL, None, (100, 80)) is None
    with pytest.raises(RuntimeError, match="only for locators <="):
        vrl.check_box_decision(_note("IGNORE_REGION"), LARGE, None, (100, 80))
    assert vrl.check_box_decision(
        _note("HAND_DRAWN", (11, 10, 39, 37)), LARGE, None, (100, 80)
    ) == (
        "HAND_DRAWN",
        (11, 10, 39, 37),
    )
    with pytest.raises(RuntimeError, match="only for locators >"):
        vrl.check_box_decision(_note("HAND_DRAWN", (11, 10, 24, 23)), SMALL, None, (100, 80))
    with pytest.raises(RuntimeError, match="outside the frame"):
        vrl.check_box_decision(_note("HAND_DRAWN", (11, 10, 120, 37)), LARGE, None, (100, 80))


def test_adjustment_may_only_tighten_the_refit() -> None:
    refit = (10, 10, 40, 38)
    assert vrl.check_box_decision(
        _note("ACCEPT_REFINED_ADJUSTED", (10, 10, 36, 38)), LARGE, refit, (100, 80)
    )
    with pytest.raises(RuntimeError, match="only tighten"):
        vrl.check_box_decision(
            _note("ACCEPT_REFINED_ADJUSTED", (10, 10, 42, 38)), LARGE, refit, (100, 80)
        )
    with pytest.raises(RuntimeError, match="only tighten"):
        vrl.check_box_decision(
            _note("ACCEPT_REFINED_ADJUSTED", (10, 10, 30, 38)), LARGE, refit, (100, 80)
        )
    with pytest.raises(RuntimeError, match="re-fitting finds no box"):
        vrl.check_box_decision(_note("ACCEPT_REFINED"), LARGE, None, (100, 80))


def test_stray_paths_cover_the_whole_derived_root(tmp_path) -> None:
    expected = {vrl.OUT_LABELS / "0001.txt": b"", vrl.ATLAS_DIR / "added_page_01.jpg": b""}
    for path in expected:
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_bytes(b"")
    assert vrl.stray_paths(tmp_path, expected) == []
    (tmp_path / vrl.OUT_DIR / "labels/train").mkdir(parents=True)
    (tmp_path / vrl.OUT_DIR / "labels/train/0001.txt").write_text("0 0.5 0.5 0.1 0.1\n")
    (tmp_path / vrl.OUT_LABELS / ".DS_Store").write_bytes(b"x")
    stray = vrl.stray_paths(tmp_path, expected)
    assert str(vrl.OUT_DIR / "labels/train/0001.txt") in stray
    assert str(vrl.OUT_LABELS / ".DS_Store") in stray


def test_verify_pins_and_append_only(tmp_path) -> None:
    for relative in vrl.PINNED:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="pinned D1-VRL-R2 source differs"):
        vrl.verify_pins(tmp_path)
    (tmp_path / vrl.OUT_DIR).mkdir(parents=True)
    with pytest.raises(RuntimeError, match="append-only"):
        vrl.build(tmp_path)


def test_official_package_verifies_counts_and_maps_ids() -> None:
    result = vrl.verify()
    assert result["valid"], result["errors"]
    assert vrl.r4_val_labels_sha256(vrl.REPO_ROOT) == vrl.R4_VAL_LABELS_SHA256
    added = r1._read_csv(vrl.REPO_ROOT / vrl.ADDED_PATH)
    ignored = r1._read_csv(vrl.REPO_ROOT / vrl.IGNORE_PATH)
    assert (len(added), len(ignored)) == (64, 40)
    # QA L4 of D1-VRL-R1: the mapping test must see real rows for keys 23, 39 and 41
    pairs = {
        (r["derived_key"], r["yolo_id"]) for r in added if r["derived_key"] in {"23", "39", "41"}
    }
    assert pairs == {("23", "25"), ("39", "40"), ("41", "42")}
