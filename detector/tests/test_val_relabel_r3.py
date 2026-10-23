from __future__ import annotations

import pytest

from m1 import val_relabel_r1 as r1
from m1 import val_relabel_r3 as vrl


def _hand(stem: str, box: list[int], eye: list[int | str]) -> dict:
    row = {"proposal_id": "R001", "stem": stem, "box_decision": "HAND_DRAWN", "note": "seen"}
    row.update(zip(("x1", "y1", "x2", "y2"), (str(v) for v in box), strict=True))
    row.update(zip(vrl.EYE, (str(v) for v in eye), strict=True))
    return row


def test_hand_rows_need_eye_columns_within_one_px() -> None:
    vrl.check_notes([_hand("1223", [6, 44, 36, 70], [6, 43, 37, 70])])
    with pytest.raises(RuntimeError, match="more than 1 px"):
        vrl.check_notes([_hand("1223", [0, 44, 36, 70], [6, 44, 36, 70])])
    with pytest.raises(RuntimeError, match="integer box and eye"):
        vrl.check_notes([_hand("1223", [6, 44, 36, 70], ["", "", "", ""])])


def test_dark_frames_allow_no_snap() -> None:
    vrl.check_notes([_hand("1823", [332, 439, 362, 469], [332, 439, 362, 469])])
    with pytest.raises(RuntimeError, match="more than 0 px"):
        vrl.check_notes([_hand("1823", [332, 439, 362, 470], [332, 439, 362, 469])])


def test_malformed_field_count_is_refused() -> None:
    row = {"proposal_id": "R097", "box_decision": "ACCEPT_REFINED", None: ["extra"]}
    with pytest.raises(RuntimeError, match="malformed field count"):
        vrl.check_notes([row])


def test_verify_pins_and_append_only(tmp_path) -> None:
    for relative in vrl.PINNED:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="pinned D1-VRL-R3 source differs"):
        vrl.verify_pins(tmp_path)
    (tmp_path / vrl.OUT_DIR).mkdir(parents=True)
    with pytest.raises(RuntimeError, match="append-only"):
        vrl.build(tmp_path)


def test_official_package_verifies_with_r039_r046_redrawn() -> None:
    result = vrl.verify()
    assert result["valid"], result["errors"]
    added = {r["proposal_id"]: r for r in r1._read_csv(vrl.REPO_ROOT / vrl.ADDED_PATH)}
    assert len(added) == 64
    assert len(r1._read_csv(vrl.REPO_ROOT / vrl.IGNORE_PATH)) == 40
    assert (added["R039"]["x1"], added["R046"]["y2"]) == ("6", "28")
    notes = r1._read_csv(vrl.REPO_ROOT / vrl.NOTES)
    assert all(None not in n for n in notes)
