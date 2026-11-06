"""Tests for the paired A2 − pilot validation bootstrap (D1-A2-PILOT-PAIRED-CI-R1).

Synthetic fixtures only: no model, no inference, no sealed test. The end-to-end test builds a
synthetic 376-frame / 624-box / 9-group validation bundle so that the predecessor's roster checks
run unchanged.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image

from m1 import a3_pilot_paired_ci_r1 as a3ci
from m1 import contract
from m1.metrics import Frame

sys.path.insert(0, str(contract.DETECTOR_ROOT / "colab"))
HERE = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


paired = _load("m1.a2_pilot_paired_ci_r1", HERE / "m1/a2_pilot_paired_ci_r1.py")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frame(stem: str, group: str, gt: list[int], preds: list[tuple[int, float, bool]]) -> Frame:
    gt_boxes = np.asarray([[10 * i, 10 * i, 10 * i + 8, 10 * i + 8] for i in range(len(gt))])
    boxes, classes, scores = [], [], []
    for index, (cls, score, hit) in enumerate(preds):
        boxes.append(gt_boxes[index] if hit else [500, 500, 508, 508])
        classes.append(cls)
        scores.append(score)
    return Frame(
        stem,
        group,
        gt_boxes.reshape(-1, 4).astype(float),
        np.asarray(gt, dtype=int),
        np.asarray(boxes, dtype=float).reshape(-1, 4),
        np.asarray(classes, dtype=int),
        np.asarray(scores, dtype=float),
        600,
        600,
    )


def _synthetic(shift: float = 0.0, seed: int = 7) -> list[Frame]:
    rng = np.random.default_rng(seed)
    frames = []
    for i in range(36):
        gt = [int(rng.choice([7, 33, 42])), int(rng.integers(0, 3))]
        preds = [
            (gt[0] if rng.random() > 0.3 else 5, float(min(1.0, rng.random() + shift)), True),
            (gt[1], float(rng.random()), bool(rng.random() > 0.4)),
        ]
        frames.append(_frame(f"{i:04d}", f"G{i % 9}", gt, preds))
    return frames


FOCUS = {"7": 7, "32": 33, "41": 42, "46": 46}


# ------------------------------------------------------------------------- unit: statistics


def test_paired_ci_is_deterministic_for_the_fixed_seed():
    a2, pilot = _synthetic(0.2), _synthetic()
    stats = paired.a3ci.frame_stats(a2, 0.20), paired.a3ci.frame_stats(pilot, 0.20)
    first = paired.paired_block(*stats, paired.a3ci.resample_indices(a2, 300, 20261018), FOCUS)
    second = paired.paired_block(*stats, paired.a3ci.resample_indices(a2, 300, 20261018), FOCUS)
    other = paired.paired_block(*stats, paired.a3ci.resample_indices(a2, 300, 1), FOCUS)
    assert paired.canonical(first) == paired.canonical(second)
    assert paired.canonical(first) != paired.canonical(other)


def test_both_models_share_identical_draws():
    a2, pilot = _synthetic(0.2), _synthetic()
    samples = paired.a3ci.resample_indices(a2, 50, 20261018)
    assert [s.tolist() for s in samples] == [
        s.tolist() for s in paired.a3ci.resample_indices(pilot, 50, 20261018)
    ]


def test_block_is_the_predecessor_block_relabelled():
    a2, pilot = _synthetic(0.2), _synthetic()
    stats = paired.a3ci.frame_stats(a2, 0.20), paired.a3ci.frame_stats(pilot, 0.20)
    samples = paired.a3ci.resample_indices(a2, 200, 20261018)
    old = a3ci.paired_block(*stats, samples, FOCUS)
    new = paired.paired_block(*stats, samples, FOCUS)
    for metric in paired.METRICS:
        assert new[metric]["a2"] == old[metric]["a3"]
        assert new[metric]["difference_a2_minus_pilot"] == old[metric]["difference_a3_minus_pilot"]
        assert new[metric]["paired_ci95"] == old[metric]["paired_ci95"]
        assert new[metric]["a2_marginal_ci95"] == old[metric]["a3_marginal_ci95"]
    for key in FOCUS:
        old_entry = old["per_class_correct_class_recall"][key]
        new_entry = new["per_class_correct_class_recall"][key]
        assert new_entry["status"] == old_entry["status"]
        assert new_entry.get("paired_ci95") == old_entry.get("paired_ci95")
    assert "a3" not in json.dumps(new)


def test_identical_models_are_flagged_degenerate():
    frames = _synthetic()
    stats = paired.a3ci.frame_stats(frames, 0.20)
    block = paired.paired_block(stats, stats, paired.a3ci.resample_indices(frames, 100, 3), FOCUS)
    for metric in paired.METRICS:
        assert block[metric]["paired_ci95"] == [0.0, 0.0]
        assert block[metric]["ci_degenerate"] is True
    assert set(paired.METRICS) <= set(block["degenerate_ci_flags"])


def test_single_group_and_unsupported_classes_are_degenerate():
    frames = [
        _frame("a", "G0", [33, 0], [(33, 0.9, True), (0, 0.9, True)]),
        _frame("b", "G1", [0, 7], [(0, 0.9, True), (7, 0.9, True)]),
        _frame("c", "G2", [0, 7], [(0, 0.1, True), (7, 0.1, True)]),
    ]
    other = [
        _frame("a", "G0", [33, 0], [(33, 0.1, True), (0, 0.9, True)]),
        _frame("b", "G1", [0, 7], [(0, 0.9, True), (7, 0.1, True)]),
        _frame("c", "G2", [0, 7], [(0, 0.1, True), (7, 0.9, True)]),
    ]
    stats = paired.a3ci.frame_stats(frames, 0.20), paired.a3ci.frame_stats(other, 0.20)
    block = paired.paired_block(*stats, paired.a3ci.resample_indices(frames, 100, 5), FOCUS)
    classes = block["per_class_correct_class_recall"]
    assert classes["32"]["status"] == "DEGENERATE_SINGLE_GROUP_CI_NOT_INFORMATIVE"
    assert classes["32"]["ci_degenerate"] is True and classes["32"]["yolo_id"] == 33
    assert classes["41"]["status"] == "UNKNOWN_NO_VALIDATION_SUPPORT"
    assert classes["41"]["ci_degenerate"] is True
    assert classes["7"]["groups_with_support"] == 2
    assert {"class_32", "class_41", "class_46"} <= set(block["degenerate_ci_flags"])
    readout = paired.criteria_readout(block)
    assert readout["per_class"]["41"]["meets_gain_0_05"] is None
    assert readout["all_point_criteria_met"] is False


def _names(identity: bool = False) -> list[str]:
    names = [str(i) for i in range(54)]
    if not identity:  # derived key 32 -> yolo 33, 41 -> 42 (as in the pinned class map)
        names[32], names[33] = names[33], names[32]
        names[41], names[42] = names[42], names[41]
    return names


def test_focus_ids_translate_derived_keys_through_the_class_map():
    ids = paired.focus_ids(_names())
    assert (ids["7"], ids["32"], ids["41"]) == (7, 33, 42)
    assert paired.CRITERIA_KEYS == ("7", "32", "41")


def test_focus_ids_refuse_an_identity_class_map():
    with pytest.raises(RuntimeError, match="derived-key/yolo_id mapping differs"):
        paired.focus_ids(_names(identity=True))


def test_criteria_readout_thresholds():
    a2, pilot = _synthetic(0.3), _synthetic()
    stats = paired.a3ci.frame_stats(a2, 0.20), paired.a3ci.frame_stats(pilot, 0.20)
    block = paired.paired_block(*stats, paired.a3ci.resample_indices(a2, 100, 9), FOCUS)
    readout = paired.criteria_readout(block)
    for key in ("7", "32", "41"):
        diff = block["per_class_correct_class_recall"][key]["difference_a2_minus_pilot"]
        assert readout["per_class"][key]["meets_gain_0_05"] is (diff >= 0.05)
    fp = block["fp_per_image"]["difference_a2_minus_pilot"]
    assert readout["fp_per_image_increase_within_0_03"] is (fp <= 0.03)
    assert readout["a2_overall_recall"] == block["agnostic_recall"]["a2"]
    assert readout["label"].endswith("NOT_ACCEPTANCE")


def test_map_block_matches_the_common_average_precision():
    import evaluate_cascade_b0_r1 as common

    a2, pilot = _synthetic(0.2), _synthetic()
    block = paired.map_block(a2, pilot, paired.a3ci.resample_indices(a2, 5, 20261018))
    for label, frames in (("a2", a2), ("pilot", pilot)):
        reference = common.average_precision(frames)
        assert abs(block["map50"][label] - reference["map50"]) <= 1e-12
        assert abs(block["map50_95"][label] - reference["map50_95"]) <= 1e-12


# ----------------------------------------------------------------------------- end to end


def _bundle(tmp_path: Path) -> tuple[Path, list[Frame]]:
    """Synthetic 376-frame / 624-box / 9-group validation bundle (no test split, no pixels)."""
    bundle = tmp_path / "bundle"
    images, labels = bundle / "data/images/val", bundle / "data/labels54/val"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    rng = np.random.default_rng(3)
    groups = {}
    for i in range(376):
        stem = f"f{i:04d}"
        Image.new("RGB", (100, 100)).save(images / f"{stem}.png")
        count = 2 if i < 248 else 1
        classes = [int(rng.choice([7, 33, 42, 0, 1])) for _ in range(count)]
        lines = [f"{c} {0.2 + 0.4 * k} 0.5 0.1 0.1" for k, c in enumerate(classes)]
        (labels / f"{stem}.txt").write_text("\n".join(lines) + "\n")
        groups[stem] = f"G{i % 9}"
    (bundle / "data/val_groups.json").write_text(json.dumps(groups))
    with (bundle / "data/classes.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["yolo_id", "derived_key"])
        for yolo_id, key in enumerate(_names()):
            writer.writerow([yolo_id, key])
    base = a3ci.gt_frames(bundle)
    return bundle, base


def _predictions(base: list[Frame], seed: int) -> list[list[Any]]:
    rng = np.random.default_rng(seed)
    rows = []
    for frame in base:
        for box, cls in zip(frame.gt_boxes, frame.gt_classes, strict=True):
            if rng.random() < 0.85:
                label = int(cls) if rng.random() < 0.8 else 5
                rows.append([frame.stem, label, round(float(rng.random()), 4), *map(float, box)])
        if rng.random() < 0.3:
            rows.append([frame.stem, 9, round(float(rng.random()), 4), 1.0, 1.0, 6.0, 6.0])
    return rows


def _write_csv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


@pytest.fixture(scope="module")
def synthetic(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """Bundle, CSVs and the evaluator's ``common.report`` output, built once per module."""
    import evaluate_cascade_b0_r1 as common

    base_dir = tmp_path_factory.mktemp("a2ci")
    bundle, base = _bundle(base_dir)
    pilot_rows = [[r[0], i, r[1], r[2], *r[3:]] for i, r in enumerate(_predictions(base, 1))]
    _write_csv(
        bundle / paired.PILOT_CSV,
        ["stem", "rank", "yolo_id", "conf", "x1", "y1", "x2", "y2"],
        pilot_rows,
    )
    a2_csv = base_dir / paired.A2_CSV_NAME
    _write_csv(
        a2_csv,
        ["stem", "class_id", "confidence", "x1", "y1", "x2", "y2"],
        _predictions(base, 2),
    )
    a2 = a3ci.with_predictions(base, a2_csv, "class_id", "confidence")
    pilot = a3ci.with_predictions(base, bundle / paired.PILOT_CSV, "yolo_id", "conf")
    return {
        "bundle": bundle,
        "a2_csv": a2_csv,
        "a2_report": json.loads(json.dumps(common.report(a2), allow_nan=False)),
        "pilot_report": json.loads(json.dumps(common.report(pilot), allow_nan=False)),
    }


def _root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, synthetic: dict[str, Any], *, tamper=None
) -> dict[str, Any]:
    root = tmp_path / "repo"
    a2_csv = root / paired.A2_DIR / paired.A2_CSV_NAME
    a2_csv.parent.mkdir(parents=True)
    shutil.copyfile(synthetic["a2_csv"], a2_csv)
    pilot_report = copy.deepcopy(synthetic["pilot_report"])
    # The real pilot anchor selects 0.20; the synthetic pilot's own selection stands in for it.
    monkeypatch.setattr(paired, "PILOT_SELECTED_CONF", pilot_report["selected_on_val"]["conf"])
    a3_json = root / a3ci.A3_JSON
    a3_json.parent.mkdir(parents=True, exist_ok=True)
    a3_json.write_text(json.dumps({"pilot_common_method": pilot_report}))
    result = {
        "package": paired.EVALUATOR_PACKAGE,
        "experiment": "D1-A2-R1",
        "split": "val",
        "frames": 376,
        "gt_boxes": 624,
        "a2_common_method": copy.deepcopy(synthetic["a2_report"]),
        "pilot_common_method": copy.deepcopy(pilot_report),
        "a2_result_archive_sha256": "1" * 64,
        "a2_best_weight_sha256": "2" * 64,
        "bundle_manifest_sha256": paired.BUNDLE_MANIFEST_SHA256,
        "prediction_csv_sha256": sha(a2_csv),
        "sealed_test_accessed": False,
    }
    if tamper:
        tamper(result)
    json_path = root / paired.A2_DIR / paired.A2_JSON_NAME
    json_path.write_text(json.dumps(result, indent=2))
    for relative, source in (
        (paired.EVALUATOR, HERE / "colab/evaluate_d1_a2_r1_common_r1.py"),
        (paired.PREDECESSOR, Path(a3ci.__file__)),
    ):
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, root / relative)
    # The predecessor's own pins (real bundle, A3 anchors) are covered by its own tests.
    monkeypatch.setattr(paired.a3ci, "verify_pins", lambda root, bundle: {"bundle_manifest": "x"})
    return {
        "root": root,
        "bundle": synthetic["bundle"],
        "csv_sha": sha(a2_csv),
        "json_sha": sha(json_path),
    }


def test_evaluator_pin_equals_the_sibling_evaluator_source():
    assert sha(HERE / "colab/evaluate_d1_a2_r1_common_r1.py") == paired.EVALUATOR_SHA256
    assert sha(Path(a3ci.__file__)) == paired.PREDECESSOR_SHA256


def test_end_to_end_is_deterministic_and_reproduces_point_estimates(
    tmp_path, monkeypatch, synthetic
):
    env = _root(tmp_path, monkeypatch, synthetic)
    kwargs = {"bundle": env["bundle"], "with_map": False}
    first = paired.evaluate(env["root"], env["csv_sha"], env["json_sha"], **kwargs)
    second = paired.evaluate(env["root"], env["csv_sha"], env["json_sha"], **kwargs)
    assert paired.canonical(first) == paired.canonical(second)
    assert first["sealed_test_accessed"] is False and first["inference_run"] is False
    assert first["bootstrap"] == {**first["bootstrap"], "rounds": 1000, "seed": 20261018}
    assert first["focus_derived_key_to_yolo_id"] == FOCUS
    assert first["reproduction_check"]["a2"]["operating_points_reproduced"] is True
    assert set(first["fixed_conf_020"]["per_class_correct_class_recall"]) == set(FOCUS)


def test_point_estimate_mismatch_aborts_before_any_ci(tmp_path, monkeypatch, synthetic):
    def tamper(result: dict[str, Any]) -> None:
        result["a2_common_method"]["fixed_conf_020"]["true_positives"] += 1

    env = _root(tmp_path, monkeypatch, synthetic, tamper=tamper)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("a CI was computed before the point estimates were checked")

    monkeypatch.setattr(paired.a3ci, "resample_indices", forbidden)
    with pytest.raises(RuntimeError, match="does not reproduce"):
        paired.evaluate(
            env["root"], env["csv_sha"], env["json_sha"], bundle=env["bundle"], with_map=False
        )


PIN_REFUSALS = {
    "csv_sha_other": ("csv", "pinned input differs: A2 prediction CSV"),
    "json_sha_other": ("json", "pinned input differs: A2 result JSON"),
    "sha_malformed": ("malformed", "64 lowercase hex"),
    "sealed_true": (lambda r: r.update(sealed_test_accessed=True), "sealed_test_accessed=false"),
    "package_other": (lambda r: r.update(package="D1-A3-R2-COMMON-VALIDATION-R1"), "binding"),
    "experiment_other": (lambda r: r.update(experiment="D1-A3-R1"), "binding"),
    "csv_binding_other": (lambda r: r.update(prediction_csv_sha256="0" * 64), "binding"),
    "bundle_other": (lambda r: r.update(bundle_manifest_sha256="0" * 64), "binding"),
    "pilot_side_changed": (
        lambda r: r["pilot_common_method"]["fixed_conf_020"].update(true_positives=-1),
        "pilot side differs",
    ),
}


@pytest.mark.parametrize("case", sorted(PIN_REFUSALS))
def test_a2_pin_refusals(tmp_path, monkeypatch, synthetic, case):
    change, message = PIN_REFUSALS[case]
    tamper = change if callable(change) else None
    env = _root(tmp_path, monkeypatch, synthetic, tamper=tamper)
    csv_sha, json_sha = env["csv_sha"], env["json_sha"]
    if change == "csv":
        csv_sha = "0" * 64
    elif change == "json":
        json_sha = "0" * 64
    elif change == "malformed":
        csv_sha = "XYZ"
    with pytest.raises(RuntimeError, match=message):
        paired.evaluate(env["root"], csv_sha, json_sha, bundle=env["bundle"], with_map=False)


def test_changed_evaluator_source_is_refused(tmp_path, monkeypatch, synthetic):
    env = _root(tmp_path, monkeypatch, synthetic)
    (env["root"] / paired.EVALUATOR).write_text("# edited\n")
    with pytest.raises(RuntimeError, match="A2 common evaluator"):
        paired.evaluate(
            env["root"], env["csv_sha"], env["json_sha"], bundle=env["bundle"], with_map=False
        )


def test_cli_requires_the_a2_hashes():
    with pytest.raises(SystemExit):
        paired.main(["write"])
