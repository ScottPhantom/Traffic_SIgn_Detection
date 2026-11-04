from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path

import numpy as np
import pytest

from m1 import metrics
from m1 import yolo54_improvement_r3 as r3

KEYS = ("7", "32", "41", "46")


def _write(root: Path, relative: Path, data: bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _ids() -> dict[str, int]:
    return {str(i): i for i in range(r3.CLASSES)}


def _frame(stem: str, group: str, gt, preds) -> metrics.Frame:
    return metrics.Frame(
        stem=stem,
        group_id=group,
        gt_boxes=np.asarray([g[1] for g in gt], dtype=float).reshape(-1, 4),
        gt_classes=np.asarray([g[0] for g in gt], dtype=int),
        pred_boxes=np.asarray([p[2] for p in preds], dtype=float).reshape(-1, 4),
        pred_classes=np.asarray([p[0] for p in preds], dtype=int),
        pred_scores=np.asarray([p[1] for p in preds], dtype=float),
        image_width=960,
        image_height=540,
    )


def _toy_frames() -> list[metrics.Frame]:
    box = (10, 10, 50, 50)
    other = (200, 200, 240, 240)
    return [
        _frame("a", "g1", [(7, box)], [(7, 0.12, box)]),
        _frame("b", "g1", [(46, box)], [(46, 0.30, box), (10, 0.08, other)]),
        _frame("c", "g2", [(32, box)], [(32, 0.06, box), (46, 0.11, other)]),
        _frame("d", "g3", [(41, box)], [(41, 0.25, box)]),
        _frame("e", "g3", [], [(7, 0.50, other)]),
    ]


def _csv(rows: list[list[object]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(r3.PREDICTION_FIELDS)
    writer.writerows(rows)
    return buffer.getvalue().encode()


# ------------------------------------------------------------------- 1, 2, 6: path guards


@pytest.mark.parametrize(
    "relative",
    [
        Path("data/processed/m1_yolo/labels/test/0001.txt"),
        Path("results/sealed_TEST/report.json"),
        Path("docs/latest_pointer.json"),
    ],
)
def test_any_test_component_is_refused_before_reading(tmp_path, relative) -> None:
    with pytest.raises(RuntimeError, match="sealed-test"):
        r3.guard(tmp_path, relative)


def test_no_test_directory_is_ever_listed_or_created(tmp_path, monkeypatch) -> None:
    listed = []
    original = os.scandir
    monkeypatch.setattr(os, "scandir", lambda p: listed.append(str(p)) or original(p))
    folder = tmp_path / r3.R3_LABELS
    folder.mkdir(parents=True)
    (folder / "test_0001.txt").write_text("")
    with pytest.raises(RuntimeError, match="unexpected entry"):
        r3._regular_files(tmp_path, r3.R3_LABELS)
    inside = [Path(p).relative_to(tmp_path) for p in listed]
    assert inside == [r3.R3_LABELS]
    assert all(not any(r3._is_test_part(part) for part in p.parts) for p in r3.PINNED)
    assert not any(r3._is_test_part(part) for part in r3.OUTPUT.parts)
    assert not list(tmp_path.rglob("test"))


def test_symlink_hardlink_and_escape_are_refused(tmp_path) -> None:
    real = _write(tmp_path, Path("docs/real.json"), b"{}")
    (tmp_path / "docs/link.json").symlink_to(real)
    with pytest.raises(RuntimeError, match="symlink"):
        r3.guard(tmp_path, Path("docs/link.json"))
    os.link(real, tmp_path / "docs/hard.json")
    with pytest.raises(RuntimeError, match="hardlinked"):
        r3.guard(tmp_path, Path("docs/hard.json"))
    with pytest.raises(RuntimeError, match="non-relative"):
        r3.guard(tmp_path, Path("../outside.json"))
    with pytest.raises(RuntimeError, match="non-relative"):
        r3.guard(tmp_path, tmp_path / "docs/real.json")
    (tmp_path / "linked_dir").symlink_to(tmp_path / "docs")
    with pytest.raises(RuntimeError, match="symlink"):
        r3.guard(tmp_path, Path("linked_dir/real.json"))


# ------------------------------------------------------------------- 3, 4, 5: bindings


def test_changed_prediction_hash_fails(tmp_path) -> None:
    _write(tmp_path, r3.PREDICTIONS, b"stem,rank\n")
    with pytest.raises(RuntimeError, match="pinned input differs"):
        r3.read_pinned(tmp_path, r3.PREDICTIONS)
    with pytest.raises(RuntimeError, match="pinned input differs"):
        r3.verify_pins(tmp_path, {r3.PREDICTIONS: r3.PINNED[r3.PREDICTIONS]})


def test_validation_roster_must_be_exactly_376_frames_and_624_boxes(tmp_path) -> None:
    for index in range(375):
        _write(tmp_path, r3.R3_LABELS / f"{index:04d}.txt", b"7 0.5 0.5 0.1 0.1\n")
    with pytest.raises(RuntimeError, match="376 files"):
        r3.load_r3_labels(tmp_path)
    _write(tmp_path, r3.R3_LABELS / "0375.txt", b"")
    with pytest.raises(RuntimeError, match="376 files"):  # right count, wrong roster hash
        r3.load_r3_labels(tmp_path)


def test_changed_group_mapping_fails(tmp_path, monkeypatch) -> None:
    text = "stem,group_id,split,use\n0001,D02-C0001,val,VAL\n0002,D02-C0002,train,TRAIN\n"
    _write(tmp_path, r3.SPLIT_FRAMES, text.encode())
    with pytest.raises(RuntimeError, match="pinned input differs"):
        r3.load_groups(tmp_path, ["0001"])
    monkeypatch.setitem(r3.PINNED, r3.SPLIT_FRAMES, r3.sha256_bytes(text.encode()))
    assert r3.load_groups(tmp_path, ["0001"]) == {"0001": "D02-C0001"}
    with pytest.raises(RuntimeError, match="not a WP36-R1 validation frame"):
        r3.load_groups(tmp_path, ["0001", "0002"])


# ------------------------------------------------------------------- 7, 8, 9: output and schema


def test_source_change_between_preflight_and_write_fails(tmp_path, monkeypatch) -> None:
    evidence = tmp_path / "evidence"
    _write(evidence, Path("docs/a.md"), b"original")
    pins = {Path("docs/a.md"): r3.sha256_bytes(b"original")}
    monkeypatch.setattr(r3, "PINNED", pins)
    document = {"evidence_pins": r3.verify_pins(evidence), "value": 1}
    (evidence / "docs/a.md").write_bytes(b"changed")
    out = tmp_path / "out"
    (out / r3.OUTPUT.parent).mkdir(parents=True)
    with pytest.raises(RuntimeError, match="pinned input differs"):
        r3.publish(out, evidence, document)
    assert not (out / r3.OUTPUT).exists()


def test_publish_is_exclusive_and_canonical(tmp_path, monkeypatch) -> None:
    evidence = tmp_path / "evidence"
    _write(evidence, Path("docs/a.md"), b"x")
    monkeypatch.setattr(r3, "PINNED", {Path("docs/a.md"): r3.sha256_bytes(b"x")})
    document = {"evidence_pins": r3.verify_pins(evidence), "b": [1.5, 2], "a": "é"}
    out = tmp_path / "out"
    (out / r3.OUTPUT.parent).mkdir(parents=True)
    written = r3.publish(out, evidence, document)
    data = (out / r3.OUTPUT).read_bytes()
    assert data == r3.canonical(document) and written["sha256"] == r3.sha256_bytes(data)
    assert data.startswith(b'{"a":"\xc3\xa9","b":[1.5,2]')
    with pytest.raises(FileExistsError):
        r3.publish(out, evidence, document)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_nan_and_inf_never_reach_the_output(bad) -> None:
    with pytest.raises(RuntimeError, match="non-finite"):
        r3.canonical({"a": {"b": [1.0, bad]}})


def test_nan_and_inf_in_prediction_csv_fail() -> None:
    for value in ("nan", "inf"):
        data = _csv([["a", 0, 7, value, 1, 1, 2, 2]])
        with pytest.raises(RuntimeError, match="non-finite"):
            r3.parse_predictions(data, ["a"])


@pytest.mark.parametrize("value", [0, None, "false", [], 0.0])
def test_boolean_flags_reject_integer_and_other_false_like_values(value) -> None:
    with pytest.raises(RuntimeError, match="JSON boolean false"):
        r3._strict_bool_false(value, "sealed_test_accessed")
    r3._strict_bool_false(False, "sealed_test_accessed")


@pytest.mark.parametrize("value", [True, False, 3.0, "3"])
def test_integers_reject_booleans_and_floats(value) -> None:
    with pytest.raises(RuntimeError, match="must be an integer"):
        r3._strict_int(value, "images")


def test_finite_number_rejects_booleans() -> None:
    with pytest.raises(RuntimeError, match="finite number"):
        r3._strict_float(True, "nms_iou")


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ([["a", 0, "7.0", 0.5, 1, 1, 2, 2]], "rank/class"),
        ([["a", "True", 7, 0.5, 1, 1, 2, 2]], "rank/class"),
        ([["a", 0, 54, 0.5, 1, 1, 2, 2]], "rank/class"),
        ([["z", 0, 7, 0.5, 1, 1, 2, 2]], "outside the roster"),
        ([["a", 1, 7, 0.5, 1, 1, 2, 2]], "not contiguous"),
        ([["a", 0, 7, 0.2, 1, 1, 2, 2], ["a", 1, 7, 0.5, 1, 1, 2, 2]], "descending"),
        ([["a", 0, 7, 0.0001, 1, 1, 2, 2]], "out of range"),
        ([["a", 0, 7, 0.5, 3, 1, 2, 2]], "out of range"),
        ([["a", 0, 7, 0.5, 1, 1, 2]], "number of fields"),
    ],
)
def test_prediction_csv_schema_is_strict(monkeypatch, rows, message) -> None:
    monkeypatch.setattr(r3, "PREDICTION_ROWS", len(rows))
    with pytest.raises(RuntimeError, match=message):
        r3.parse_predictions(_csv(rows), ["a"])


def test_prediction_csv_refuses_wrong_header_count_and_max_det(monkeypatch) -> None:
    with pytest.raises(RuntimeError, match="header"):
        r3.parse_predictions(b"stem,rank,cls\n", ["a"])
    with pytest.raises(RuntimeError, match="1999"):
        r3.parse_predictions(_csv([["a", 0, 7, 0.5, 1, 1, 2, 2]]), ["a"])
    monkeypatch.setattr(r3, "PREDICTION_ROWS", 3)
    monkeypatch.setattr(r3, "MAX_DET", 3)
    rows = [["a", i, 7, 0.5, 1, 1, 2, 2] for i in range(3)]
    with pytest.raises(RuntimeError, match="max_det"):
        r3.parse_predictions(_csv(rows), ["a"])


# ------------------------------------------------------------------- 10: A0


def test_a0_never_claims_agnostic_nms_from_post_nms_predictions() -> None:
    settings = {"nms_iou": 0.7, "candidate_conf": 0.001}
    for stage in ("POST_CLASSWISE_NMS", "UNKNOWN", ""):
        result = r3.a0_assessment(settings, prediction_stage=stage)
        assert result["status"] == r3.A0_REINFERENCE
        assert result["agnostic_nms_verified"] is False
        assert result["nms_grid_evaluated"] is False
        assert result["reinference_authorized"] is False
    sufficient = r3.a0_assessment(settings, prediction_stage="PRE_NMS_CANDIDATES")
    assert (
        sufficient["agnostic_nms_verified"] is False and sufficient["nms_grid_evaluated"] is False
    )


# ------------------------------------------------------------------- 11: A0b


def test_classwise_thresholds_match_the_shared_matcher() -> None:
    frames = _toy_frames()
    table = [0.20] * r3.CLASSES
    table[7] = 0.10
    filtered = r3.apply_thresholds(frames, table)
    counts = r3.frame_counts(filtered)
    point = metrics.operating_point(filtered, 0.0)
    assert int(counts["hits"].sum()) == point.true_positives == 3
    assert int(counts["fps"].sum()) == point.false_positives == 1
    assert [len(f.pred_scores) for f in filtered] == [1, 1, 0, 1, 1]


def test_fast_bootstrap_draws_exactly_like_metrics_group_bootstrap() -> None:
    frames = _toy_frames()
    reference = metrics.group_bootstrap(frames, 0.20, rounds=200, seed=20261018)
    counts = r3.frame_counts(r3.apply_thresholds(frames, [0.20] * r3.CLASSES))
    samples = r3.bootstrap_samples(frames, 200, 20261018)
    recalls = [r3._summary(counts, s, len(s))["agnostic_recall"] for s in samples]
    fps = [r3._summary(counts, s, len(s))["fp_per_image"] for s in samples]
    assert r3._ci(recalls) == list(reference["agnostic_recall"])
    assert r3._ci(fps) == list(reference["fp_per_image"])


def test_a0b_never_issues_an_official_threshold_or_gate_pass(monkeypatch) -> None:
    monkeypatch.setattr(r3, "GLOBAL_GRID", (0.10, 0.20))
    result = r3.a0b_analysis(_toy_frames(), [str(i) for i in range(r3.CLASSES)], _ids(), rounds=50)
    assert result["status"] == "DIAGNOSTIC_PENDING_OWNER_D05_Q4_INTERPRETATION"
    assert result["official_threshold"] is None and result["selected_config"] is None
    assert result["gate_pass_claimed"] is False and result["threshold_lock_written"] is False
    assert set(result["global_grid"]) == {"0.10", "0.20"}
    assert len(result["classwise"]) == len(KEYS) * len(r3.CLASSWISE_GRID) + 1
    baseline = result["global_grid"]["0.20"]["paired_delta_vs_global_0_20"]
    assert baseline["agnostic_recall"] == 0.0 and baseline["fp_per_image_95ci"] == [0.0, 0.0]
    for config in result["classwise"].values():
        assert set(config["focus_classes"]) == set(KEYS)
        assert "paired_delta_vs_global_0_20" in config and "bootstrap_95ci" in config
    assert result["search_space"]["validation_support"] == {"7": 1, "32": 1, "41": 1, "46": 1}
    r3.canonical({"a0b": result})


def test_a0b_search_space_is_fixed() -> None:
    configs = r3.a0b_configs(_ids())
    assert len(configs) == 13
    for config in configs:
        assert set(config["overrides"]) <= set(KEYS)
        assert all(
            v in (*r3.CLASSWISE_GRID, r3.COMBINED_PROBE) for v in config["overrides"].values()
        )
        lowered = [i for i, v in enumerate(config["thresholds"]) if v != 0.20]
        assert lowered == sorted(int(k) for k in config["overrides"])


# ------------------------------------------------------------------- 12, 13: A1/A2/A3


def test_a2_and_a3_are_never_authorised_to_train() -> None:
    specs = r3.run_specs({"repeated_roster_sha256": "x"})
    assert set(specs) == {"A2_repeat_factor_7_32_41", "A3_schedule_40e_cos"}
    for spec in specs.values():
        assert spec["training_authorized"] is False and spec["sealed_test_accessed"] is False
        assert spec["status"] == "WAITING_FOR_L4_AND_OWNER_AUTHORIZATION"
        assert spec["train_args"]["fliplr"] == 0.0 and spec["train_args"]["imgsz"] == 1280
        assert spec["train_args"]["seed"] == 20261018 and spec["seed"] == 20261018
    a2, a3 = specs["A2_repeat_factor_7_32_41"], specs["A3_schedule_40e_cos"]
    assert a3["train_args"]["epochs"] == 40 and a3["train_args"]["cos_lr"] is True
    assert "cos_lr" not in a2["train_args"] and a2["train_args"]["epochs"] == 100
    changed = {k for k in a3["train_args"] if a3["train_args"][k] != r3.PILOT_TRAIN_ARGS.get(k)}
    assert changed == {"epochs", "cos_lr"}
    assert {k for k in a2["train_args"] if k not in r3.PILOT_TRAIN_ARGS} == {"data"}


def test_a1_is_always_blocked() -> None:
    for package in (None, Path("docs/review/some_review.md")):
        result = r3.a1_status(package)
        assert result["status"] == "A1_BLOCKED_PENDING_TRAIN_LABEL_COMPLETENESS_AND_HUMAN_REVIEW"
        assert result["training_data_written"] is False


def test_a2_roster_refuses_unverified_train_labels(tmp_path, monkeypatch) -> None:
    manifest = {"splits": {"train": {"stem_list_sha256": "x", "labels_sha256": "y"}}}
    data = json.dumps(manifest).encode()
    _write(tmp_path, r3.EXPORT_MANIFEST, data)
    monkeypatch.setitem(r3.PINNED, r3.EXPORT_MANIFEST, r3.sha256_bytes(data))
    with pytest.raises(RuntimeError, match="train binding differs"):
        r3.a2_repeat_roster(tmp_path, _ids())


# ------------------------------------------------------------------- evidence-backed run


EVIDENCE = Path(os.environ.get("CPV301_EVIDENCE_ROOT", "/nonexistent"))


@pytest.mark.skipif(not (EVIDENCE / r3.REPORT).is_file(), reason="D1-VRE-R2 evidence not present")
def test_real_evidence_reproduces_d1_vre_r2_exactly() -> None:
    names, _ids2 = r3.class_map(EVIDENCE)
    labels = r3.load_r3_labels(EVIDENCE)
    frames = r3.build_frames(
        labels,
        r3.load_groups(EVIDENCE, sorted(labels)),
        r3.parse_predictions(r3.read_pinned(EVIDENCE, r3.PREDICTIONS), sorted(labels)),
    )
    result = r3.reproduce(frames, r3.load_report(EVIDENCE), names)
    assert (result["true_positives"], result["false_positives"]) == (547, 150)
    assert result["d05_q4_conf"] == 0.20


def test_manifest_never_pins_a_qa_record_and_needs_the_analysis(tmp_path) -> None:
    assert not any("qa_record" in path.name for path in r3.PACKAGE_FILES)
    assert r3.OUTPUT in r3.PACKAGE_FILES
    with pytest.raises(FileNotFoundError):
        r3.write_manifest(tmp_path)


def test_package_source_exception_is_only_for_the_test_folder_name(tmp_path) -> None:
    source = _write(tmp_path, Path("detector/tests/test_x.py"), b"x")
    assert r3.guard(tmp_path, Path("detector/tests/test_x.py"), package_source=True) == source
    with pytest.raises(RuntimeError, match="sealed-test"):
        r3.guard(tmp_path, Path("detector/tests/test_x.py"))
    (tmp_path / "detector/tests/link.py").symlink_to(source)
    with pytest.raises(RuntimeError, match="symlink"):
        r3.guard(tmp_path, Path("detector/tests/link.py"), package_source=True)
