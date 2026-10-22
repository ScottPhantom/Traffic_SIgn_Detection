from __future__ import annotations

import numpy as np
import pytest

from m1 import val_label_audit_r1 as vla
from m1.metrics import Frame

NAMES = ["0", "10", "23"]


def _frame(stem: str, gt: list[list[float]], gt_cls: list[int]) -> Frame:
    return Frame(
        stem,
        "G",
        np.asarray(gt, float).reshape(-1, 4),
        np.asarray(gt_cls, int),
        np.zeros((0, 4)),
        np.zeros(0, int),
        np.zeros(0),
        100,
        80,
    )


def _pred(stem: str, rank: int, cls: str, conf: float, box: list[float], disp: str) -> dict:
    return {
        "stem": stem,
        "pred_rank": str(rank),
        "pred_class": cls,
        "conf": repr(conf),
        "x1": repr(box[0]),
        "y1": repr(box[1]),
        "x2": repr(box[2]),
        "y2": repr(box[3]),
        "disposition": disp,
    }


def _rows() -> list[dict]:
    return [
        _pred("a", 0, "10", 0.9, [10, 10, 30, 30], "PAIRED"),
        _pred("a", 1, "23", 0.8, [11, 10, 30, 31], "BACKGROUND"),  # duplicate of labelled box
        _pred("a", 2, "10", 0.7, [60, 40, 80, 60], "BACKGROUND"),  # no label nearby
        _pred("a", 3, "23", 0.6, [61, 40, 80, 61], "BACKGROUND"),  # same unlabelled sign
        _pred("b", 0, "0", 0.5, [5, 5, 15, 15], "BACKGROUND"),
    ]


def _frames() -> dict[str, Frame]:
    return {"a": _frame("a", [[10, 10, 30, 30]], [1]), "b": _frame("b", [], [])}


def _note(stem, rank, cls, decision, proposed="", conf="", note="seen") -> dict:
    return {
        "stem": stem,
        "pred_rank": rank,
        "pred_class": cls,
        "decision": decision,
        "proposed_class": proposed,
        "class_confidence": conf,
        "note": note,
    }


def test_stratify_separates_duplicates_from_missing_labels() -> None:
    strata = vla.stratify(_rows(), _frames())
    assert [s["stratum"] for s in strata] == [
        "OVERLAPS_LABELLED_IOU_GE_0_5",
        vla.NO_LABEL,
        vla.NO_LABEL,
        vla.NO_LABEL,
    ]


def test_load_notes_enforces_roster_and_vocabulary(tmp_path) -> None:
    cands = [s for s in vla.stratify(_rows(), _frames()) if s["stratum"] == vla.NO_LABEL]
    good = [
        _note("a", "2", "10", "UNLABELLED_IN_TAXONOMY", "10", "HIGH"),
        _note("a", "3", "23", "UNLABELLED_IN_TAXONOMY", "10", "MEDIUM"),
        _note("b", "0", "0", "NOT_A_SIGN"),
    ]

    def write(rows):
        path = tmp_path / vla.NOTES
        path.parent.mkdir(parents=True, exist_ok=True)
        fields = list(rows[0])
        path.write_text(
            ",".join(fields) + "\n" + "".join(",".join(r[f] for f in fields) + "\n" for r in rows)
        )

    write(good)
    assert len(vla.load_notes(tmp_path, cands, NAMES)) == 3
    write(good[:2])
    with pytest.raises(RuntimeError, match="exactly once"):
        vla.load_notes(tmp_path, cands, NAMES)
    write([*good[:2], _note("b", "0", "0", "NOT_A_SIGN", "0", "HIGH")])
    with pytest.raises(RuntimeError, match="only in-taxonomy"):
        vla.load_notes(tmp_path, cands, NAMES)
    write([*good[:2], _note("b", "0", "0", "MAYBE")])
    with pytest.raises(RuntimeError, match="invalid review decision"):
        vla.load_notes(tmp_path, cands, NAMES)
    write([_note("a", "2", "10", "UNLABELLED_IN_TAXONOMY", "99", "HIGH"), *good[1:]])
    with pytest.raises(RuntimeError, match="known class"):
        vla.load_notes(tmp_path, cands, NAMES)


def test_duplicates_merge_and_proposals_drop_low() -> None:
    rows = _rows()
    cands = [s for s in vla.stratify(rows, _frames()) if s["stratum"] == vla.NO_LABEL]
    notes = [
        _note("a", "2", "10", "UNLABELLED_IN_TAXONOMY", "10", "HIGH"),
        _note("a", "3", "23", "UNLABELLED_IN_TAXONOMY", "10", "MEDIUM"),
        _note("b", "0", "0", "UNLABELLED_IN_TAXONOMY", "0", "LOW"),
    ]
    decisions = vla.decision_rows(cands, notes, rows)
    assert [d["duplicate_of"] for d in decisions] == ["", "V001", ""]
    proposed = vla.proposed_labels(decisions, _frames())
    assert [(p["stem"], p["derived_key"], p["source_review_ids"]) for p in proposed] == [
        ("a", "10", "V001 V002")
    ]
    assert proposed[0]["x_center"] == f"{70 / 100:.6f}"


def test_what_if_adds_unique_boxes_only() -> None:
    rows = _rows()
    cands = [s for s in vla.stratify(rows, _frames()) if s["stratum"] == vla.NO_LABEL]
    notes = [
        _note("a", "2", "10", "UNLABELLED_IN_TAXONOMY", "10", "HIGH"),
        _note("a", "3", "23", "UNLABELLED_IN_TAXONOMY", "10", "MEDIUM"),
        _note("b", "0", "0", "UNLABELLED_IN_TAXONOMY", "0", "LOW"),
    ]
    decisions = vla.decision_rows(cands, notes, rows)
    frames = _frames()
    assert vla.what_if(frames, decisions, NAMES, include_low=False)["added_boxes"] == 1
    assert vla.what_if(frames, decisions, NAMES, include_low=True)["added_boxes"] == 2


def test_verify_pins_and_append_only(tmp_path) -> None:
    for relative in vla.PINNED:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="pinned D1-VLA-R1 source differs"):
        vla.verify_pins(tmp_path)
    (tmp_path / vla.MANIFEST_PATH).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / vla.MANIFEST_PATH).write_text("{}")
    with pytest.raises(RuntimeError, match="append-only"):
        vla.build(tmp_path)


def test_official_package_verifies() -> None:
    result = vla.verify()
    assert result["valid"], result["errors"]
