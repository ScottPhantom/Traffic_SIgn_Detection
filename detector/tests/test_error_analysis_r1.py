from __future__ import annotations

import csv
import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from m1 import error_analysis_r1 as ea
from m1.metrics import Frame, confusion_matrix, operating_point

NAMES = ["0", "1", "2"]


def _frame(
    stem: str, gt: list[tuple[int, list[float]]], preds: list[tuple[int, float, list[float]]]
) -> Frame:
    return Frame(
        stem=stem,
        group_id="G",
        gt_boxes=np.asarray([b for _c, b in gt], dtype=float).reshape(-1, 4),
        gt_classes=np.asarray([c for c, _b in gt], dtype=int),
        pred_boxes=np.asarray([b for _c, _s, b in preds], dtype=np.float32).reshape(-1, 4),
        pred_classes=np.asarray([c for c, _s, _b in preds], dtype=int),
        pred_scores=np.asarray([s for _c, s, _b in preds], dtype=np.float32),
        image_width=100,
        image_height=80,
    )


def _frames() -> list[Frame]:
    return [
        # correct pair, a wrong-class pair (2 -> 1), a background FP and a sub-threshold pred
        _frame(
            "0001",
            [(0, [10, 10, 30, 30]), (2, [50, 10, 70, 30])],
            [
                (0, 0.9, [10, 10, 30, 30]),
                (1, 0.6, [51, 10, 70, 31]),
                (2, 0.4, [80, 60, 95, 75]),
                (0, 0.05, [0, 0, 5, 5]),
            ],
        ),
        # one missed ground truth, no prediction above threshold
        _frame("0002", [(1, [20, 20, 40, 40])], [(1, 0.1, [20, 20, 40, 40])]),
    ]


def _report(frames: list[Frame]) -> dict:
    point = operating_point(frames, ea.CONF)
    return {
        "operating_point": {
            "images": point.images,
            "ground_truth": point.ground_truth,
            "true_positives": point.true_positives,
            "false_positives": point.false_positives,
        },
        "confusion_matrix": {
            "labels": [*NAMES, "BACKGROUND"],
            "rows_gt_cols_pred": confusion_matrix(frames, ea.CONF, len(NAMES)),
        },
        "gates": {
            "classes": {
                NAMES[c]: {"hits": point.per_class_hits[c], "support": point.per_class_support[c]}
                for c in point.per_class_support
            }
        },
    }


def _repo(tmp_path: Path, frames: list[Frame], monkeypatch: pytest.MonkeyPatch) -> Path:
    images = tmp_path / ea.EXPORT_DIR / "images/val"
    labels = tmp_path / ea.EXPORT_DIR / "labels/val"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    for frame in frames:
        Image.new("RGB", (frame.image_width, frame.image_height), (90, 90, 90)).save(
            images / f"{frame.stem}.jpg"
        )
        lines = []
        for cls, box in zip(frame.gt_classes, frame.gt_boxes, strict=True):
            x1, y1, x2, y2 = box
            w, h = frame.image_width, frame.image_height
            lines.append(
                f"{cls} {(x1 + x2) / 2 / w} {(y1 + y2) / 2 / h} {(x2 - x1) / w} {(y2 - y1) / h}"
            )
        (labels / f"{frame.stem}.txt").write_text("\n".join(lines) + "\n")
    monkeypatch.setattr(ea, "val_images", lambda repo_root=tmp_path: sorted(images.iterdir()))
    monkeypatch.setattr(ea.contract, "group_of", lambda: {f.stem: "G" for f in frames})
    monkeypatch.setattr(ea, "class_names", lambda repo_root=tmp_path: NAMES)
    return tmp_path


def test_prediction_rows_partition_retained_predictions() -> None:
    rows = ea.prediction_rows(_frames(), NAMES)
    assert [r["disposition"] for r in rows] == ["PAIRED", "PAIRED", "BACKGROUND"]
    assert rows[1]["gt_class"] == "2" and rows[1]["pred_class"] == "1"
    assert all(float(r["conf"]) >= ea.CONF for r in rows)


def test_missed_rows_list_unmatched_ground_truth() -> None:
    missed = ea.missed_rows(_frames(), NAMES)
    assert [(m["stem"], m["gt_class"], m["best_retained_class"]) for m in missed] == [
        ("0002", "1", "")
    ]


def test_round_trip_reproduces_counts_and_confusion(tmp_path, monkeypatch) -> None:
    frames = _frames()
    repo = _repo(tmp_path, frames, monkeypatch)
    table = ea.csv_bytes(ea.PREDICTION_FIELDS, ea.prediction_rows(frames, NAMES)).decode()
    rebuilt = ea.frames_from_rows(csv.DictReader(io.StringIO(table)), NAMES, repo)
    summary = ea.reproduction_check(rebuilt, _report(frames), NAMES)
    assert summary["retained_predictions"] == 3
    assert summary["background_false_positives"] == 1
    assert summary["unmatched_ground_truth"] == 1
    assert ea.csv_bytes(ea.PREDICTION_FIELDS, ea.prediction_rows(rebuilt, NAMES)).decode() == table


def test_reproduction_check_fails_closed_on_any_difference() -> None:
    frames = _frames()
    report = _report(frames)
    report["operating_point"]["false_positives"] += 1
    with pytest.raises(RuntimeError, match="does not reproduce R10"):
        ea.reproduction_check(frames, report, NAMES)
    report = _report(frames)
    report["confusion_matrix"]["rows_gt_cols_pred"][0][0] += 1
    with pytest.raises(RuntimeError, match="confusion matrix differs"):
        ea.reproduction_check(frames, report, NAMES)
    report = _report(frames)
    report["gates"]["classes"]["0"]["hits"] = 0
    with pytest.raises(RuntimeError, match="class 0 hits"):
        ea.reproduction_check(frames, report, NAMES)


def test_frames_from_rows_rejects_unknown_stems_and_size_drift(tmp_path, monkeypatch) -> None:
    frames = _frames()
    repo = _repo(tmp_path, frames, monkeypatch)
    rows = ea.prediction_rows(frames, NAMES)
    bad = [dict(rows[0], stem="9999")]
    with pytest.raises(RuntimeError, match="unknown stems"):
        ea.frames_from_rows(bad, NAMES, repo)
    drift = [dict(rows[0], image_width=101)]
    with pytest.raises(RuntimeError, match="image size differs"):
        ea.frames_from_rows(drift, NAMES, repo)


def test_atlas_is_deterministic_and_indexed(tmp_path, monkeypatch) -> None:
    frames = _frames()
    repo = _repo(tmp_path, frames, monkeypatch)
    rows = ea.prediction_rows(frames, NAMES)
    items = ea.atlas_items(frames, rows, NAMES)
    assert [i.category for i in items] == ["background_fp"]  # classes 7/32/41 absent here
    first, index = ea.render_atlas(items, repo)
    second, _ = ea.render_atlas(items, repo)
    assert first == second and len(first) == 1
    assert index[0]["category"] == "background_fp" and index[0]["slot"] == 1


def test_critical_and_pair_categories(monkeypatch) -> None:
    names = [str(i) for i in range(50)]
    frames = [
        _frame(
            "0003",
            [(7, [10, 10, 30, 30]), (46, [40, 10, 60, 30]), (7, [70, 50, 90, 70])],
            [(17, 0.8, [10, 10, 30, 30]), (10, 0.7, [40, 10, 60, 30])],
        ),
    ]
    rows = ea.prediction_rows(frames, names)
    categories = [i.category for i in ea.atlas_items(frames, rows, names)]
    assert categories.count("critical_7") == 2  # 7 -> 17 and one missed 7
    assert categories.count("pair_46_to_10") == 1


def test_verify_pins_rejects_tampering(tmp_path) -> None:
    for relative in ea.PINNED:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"not the pinned bytes")
    with pytest.raises(RuntimeError, match="pinned D1-EA-R1 source differs"):
        ea.verify_pins(tmp_path)


def test_build_is_append_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(ea, "verify_pins", lambda repo_root=tmp_path: None)
    monkeypatch.setattr(ea, "load_r10_report", lambda repo_root=tmp_path: {})
    (tmp_path / ea.MANIFEST_PATH).parent.mkdir(parents=True)
    (tmp_path / ea.MANIFEST_PATH).write_text("{}")
    with pytest.raises(RuntimeError, match="append-only"):
        ea.build(tmp_path)


def test_r10_report_must_be_validation_only(tmp_path) -> None:
    import json

    report = {"test_included": True, "sealed_test_accessed": False}
    target = tmp_path / ea.R10_REPORT
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(report))
    with pytest.raises(RuntimeError, match="validation-only"):
        ea.load_r10_report(tmp_path)
