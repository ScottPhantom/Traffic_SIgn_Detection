"""Source-only checks for the two-seed R3 successor; no training or inference."""

import json
import sys
import tarfile
from io import BytesIO
from pathlib import Path

import pytest

from m1 import d1_threshold_lock_r3_successor as lock
from m1 import nms_sweep_r1 as sweep


def _row(seed, binding=None, weight=None):
    binding = binding or {
        "bundle": "a",
        "roster": "b",
        "GT": "c",
        "groups": "d",
        "classes": "e",
        "scorer": "f",
    }
    weight = weight or str(seed)
    return {
        "schema_version": 1,
        "seed": seed,
        "split": "val",
        "sealed_test_accessed": False,
        "binding": binding,
        "confidence_grid": list(lock.GRID),
        "configurations": dict.fromkeys(lock.CONFIGS, {}),
        "identity": {"weight": {"sha256": weight}},
        "predictions": {},
    }


def _load_synthetic(tmp_path, monkeypatch, rows):
    paths = []
    for i, row in enumerate(rows):
        path = tmp_path / f"report-{i}.json"
        path.write_text(json.dumps(row))
        paths.append(path)
    monkeypatch.setattr(
        lock,
        "build_seed_report",
        lambda seed, identity, predictions, *args: next(
            row
            for row in rows
            if row["seed"] == seed and row["identity"]["weight"] == identity["weight"]
        ),
    )
    return paths


def test_seed_set_and_binding_refusals(tmp_path, monkeypatch):
    a, b = _row(20261018), _row(20261019)
    for rows, message in [
        ([a], "exactly two"),
        ([a, b, b], "exactly two"),
        ([a, _row(20261020)], "two-seed set"),
        ([a, _row(20261018, weight="other")], "two-seed set"),
        ([a, _row(20261019, weight="20261018")], "distinct weights"),
        ([a, _row(20261019, binding={**a["binding"], "GT": "changed"})], "roster"),
    ]:
        paths = _load_synthetic(tmp_path, monkeypatch, rows)
        with pytest.raises(RuntimeError, match=message):
            lock._load_reports(paths, tmp_path, tmp_path)


def test_report_grid_qa_and_seal_refusals(tmp_path, monkeypatch):
    a, b = _row(20261018), _row(20261019)
    for change, message in [
        ({"confidence_grid": [0.2]}, "grid"),
        ({"configurations": {}}, "grid"),
        ({"sealed_test_accessed": True}, "seal"),
    ]:
        broken = {**a, **change}
        paths = _load_synthetic(tmp_path, monkeypatch, [broken, b])
        with pytest.raises(RuntimeError, match=message):
            lock._load_reports(paths, tmp_path, tmp_path)
    monkeypatch.undo()
    with pytest.raises(RuntimeError, match="incomplete"):
        lock.build_seed_report(20261018, {"inference_conf": 0.001}, {}, tmp_path, tmp_path)
    with pytest.raises(RuntimeError, match="floor"):
        lock.build_seed_report(20261018, {"inference_conf": 0.05}, {}, tmp_path, tmp_path)


def test_qa_must_pass_and_hashes_must_match(tmp_path):
    qa = tmp_path / "qa.md"
    qa.write_text("Verdict: PARTIAL\n")
    row = {"path": str(qa), "sha256": lock.sha256(qa)}
    with pytest.raises(RuntimeError, match="not PASS"):
        lock._qa(row)
    qa.write_text("Verdict: PASS\nVerdict: PASS\n")
    row["sha256"] = lock.sha256(qa)
    with pytest.raises(RuntimeError, match="not PASS"):
        lock._qa(row)
    qa.write_text("Verdict: PASS\n")
    with pytest.raises(RuntimeError, match="hash differs"):
        lock._qa(row)
    qa.write_text("Verdict: **PASS** — independent pilot run QA\n")
    row["sha256"] = lock.sha256(qa)
    lock._qa(row)
    qa.write_text("Verdict: PASS_PENDING\n")
    row["sha256"] = lock.sha256(qa)
    with pytest.raises(RuntimeError, match="not PASS"):
        lock._qa(row)


def test_archive_run_and_inference_qa_binding(tmp_path, monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "colab"))
    import run_d1_colab as packager

    seed, run = 20261018, "D1_synthetic"
    weight = tmp_path / "best.pt"
    weight.write_bytes(b"synthetic weight")
    contract = {
        "seed": seed,
        "run": run,
        "status": "TRAINED",
        "sealed_test_accessed": False,
        "artifacts": {"weights": {"best.pt": {"sha256": lock.sha256(weight)}}},
    }
    contract_path = tmp_path / "run_contract.json"
    contract_path.write_text(json.dumps(contract))
    archive = tmp_path / "result.tar.gz"
    with tarfile.open(archive, "w:gz") as sink:
        payload = contract_path.read_bytes()
        entry = tarfile.TarInfo(f"{run}/run_contract.json")
        entry.size = len(payload)
        sink.addfile(entry, BytesIO(payload))
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}")
    authorization = tmp_path / "authorization.md"
    authorization.write_text(f"Owner permits {lock.sha256(weight)} at conf=0.001")
    prediction = tmp_path / "pred.csv"
    prediction.write_text("synthetic CSV")
    inference_qa = tmp_path / "inference-qa.md"
    inference_qa.write_text(
        f"Verdict: PASS\n{lock.sha256(authorization)}\n{lock.sha256(weight)}\n"
        f"{lock.sha256(prediction)}\n"
    )
    run_qa = tmp_path / "run-qa.md"
    run_qa.write_text(
        f"Verdict: PASS\n{lock.sha256(archive)}\n{lock.sha256(manifest_path)}\n"
        f"{lock.sha256(weight)}\n{lock.sha256(contract_path)}\n{'a' * 64}\n"
    )

    def ref(path):
        return {"path": str(path), "sha256": lock.sha256(path)}

    identity = {
        "weight": ref(weight),
        "run_contract": ref(contract_path),
        "result_archive": ref(archive),
        "result_manifest": ref(manifest_path),
        "run_attestation_sha256": "a" * 64,
        "inference_authorization": ref(authorization),
        "inference_result_qa": ref(inference_qa),
        "run_result_qa": ref(run_qa),
    }
    predictions = {"classaware_0.70": ref(prediction)}
    monkeypatch.setitem(
        lock.RUN_PINS,
        seed,
        {
            "weight": identity["weight"]["sha256"],
            "run_contract": identity["run_contract"]["sha256"],
            "attestation": identity["run_attestation_sha256"],
            "run_qa": identity["run_result_qa"]["sha256"],
        },
    )
    monkeypatch.setitem(lock.RUN_PINS, 20261019, lock.RUN_PINS[seed])
    manifest = {
        "run": run,
        "run_attestation_sha256": "a" * 64,
        "files": [
            {"path": f"{run}/weights/best.pt", "sha256": lock.sha256(weight)},
            {"path": f"{run}/run_contract.json", "sha256": lock.sha256(contract_path)},
        ],
    }
    monkeypatch.setattr(packager, "verify_result_archive", lambda *args: manifest)
    lock._run_binding(seed, identity, predictions, tmp_path)
    with pytest.raises(RuntimeError, match="run contract identity"):
        lock._run_binding(20261019, identity, predictions, tmp_path)
    altered = {**manifest, "run_attestation_sha256": "b" * 64}
    monkeypatch.setattr(packager, "verify_result_archive", lambda *args: altered)
    with pytest.raises(RuntimeError, match="attestation binding"):
        lock._run_binding(seed, identity, predictions, tmp_path)
    monkeypatch.setattr(packager, "verify_result_archive", lambda *args: manifest)
    other = tmp_path / "other.csv"
    other.write_text("not in QA")
    with pytest.raises(RuntimeError, match="does not bind all CSVs"):
        lock._run_binding(seed, identity, {"classaware_0.70": ref(other)}, tmp_path)


def test_mean_and_frozen_ties():
    # Pure selection uses both seeds, not the best seed alone.
    bad = {
        "configuration": lock.BASE,
        "iou": 0.70,
        "agnostic_nms": False,
        "confidence": 0.25,
        "mean_agnostic_recall": 0.84,
        "mean_fp_per_image": 0.1,
        "mean_map50_95": 0.9,
    }
    good = {**bad, "confidence": 0.20, "mean_agnostic_recall": 0.85, "mean_fp_per_image": 0.2}
    assert lock.provisional.choose([bad, good]) == good
    assert lock.provisional.choose([bad]) is None
    candidates = [
        {**good, "confidence": 0.19, "mean_fp_per_image": 0.2, "mean_map50_95": 0.99},
        {**good, "configuration": "classaware_0.65", "iou": 0.65, "mean_map50_95": 0.89},
        {**good, "configuration": "agnostic_0.80", "iou": 0.80, "agnostic_nms": True},
    ]
    assert lock.provisional.choose([good, *candidates]) == good


def test_change_needs_all_three_conditions(monkeypatch, tmp_path):
    a, b = _row(20261018), _row(20261019)
    # Select the unrestricted different-IoU cell; baseline remains eligible.
    baseline = {
        "configuration": lock.BASE,
        "iou": 0.70,
        "agnostic_nms": False,
        "confidence": 0.19,
        "mean_agnostic_recall": 0.86,
        "mean_fp_per_image": 0.4,
        "mean_map50_95": 0.6,
        "by_seed": {str(s): {"agnostic_recall": 0.86} for s in lock.SEEDS},
    }
    chosen = {**baseline, "configuration": "classaware_0.65", "iou": 0.65, "mean_fp_per_image": 0.2}
    monkeypatch.setattr(lock, "_aggregate", lambda _: [baseline, chosen])
    folds = [{"selected_configuration": "classaware_0.65"}] * 9
    change = {"fp_per_image_ci95": [-0.3, -0.01], "map50_95_ci95": [-0.1, 0.01]}
    monkeypatch.setattr(lock, "_ci_and_folds", lambda *args: (change, folds))
    assert lock.select_lock([a, b], tmp_path)["selected"] == chosen
    for altered_change, altered_folds in [
        ({**change, "fp_per_image_ci95": [-0.3, 0.01]}, folds),
        ({**change, "map50_95_ci95": [-0.1, -0.01]}, folds),
        (change, folds[:6] + [{"selected_configuration": None}] * 3),
    ]:
        monkeypatch.setattr(
            lock,
            "_ci_and_folds",
            lambda *args, c=altered_change, f=altered_folds: (c, f),
        )
        assert lock.select_lock([a, b], tmp_path)["selected"] == baseline


def test_same_draw_bootstrap_is_repeatable(monkeypatch):
    # The pinned helper uses the same sampled frame indices for both weights/settings.
    import numpy as np

    from m1 import two_seed_provisional_threshold_r1 as provisional

    base, new = lock.BASE, "classaware_0.65"
    frames = {f"seed_{s}": {base: f"{s}-base", new: f"{s}-new"} for s in lock.SEEDS}
    seen = []
    monkeypatch.setattr(provisional.ci, "resample_indices", lambda *args: [np.array([0, 1])] * 2)
    monkeypatch.setattr(
        provisional.ci,
        "frame_stats",
        lambda value, conf: {
            "gt": np.ones(2),
            "agnostic_hits": np.ones(2),
            "fp": np.ones(2) if "base" in value else np.zeros(2),
        },
    )
    monkeypatch.setattr(provisional.ci, "_correct_matrices", lambda value: None)
    monkeypatch.setattr(
        provisional.ci,
        "_map50_95",
        lambda value, correct, index: (
            seen.append((value, tuple(index))) or (0.5 if "base" in value else 0.6)
        ),
    )
    monkeypatch.setattr(provisional, "ROUNDS", 2)
    selected = {
        "configuration": new,
        "confidence": 0.2,
        "mean_fp_per_image": 0,
        "mean_map50_95": 0.6,
    }
    reference = {
        "configuration": base,
        "confidence": 0.2,
        "mean_fp_per_image": 1,
        "mean_map50_95": 0.5,
    }
    result = provisional.bootstrap_change(frames, selected, reference)
    assert result["fp_per_image_ci95"] == [-1, -1]
    assert len(seen) == 8 and {draw for _, draw in seen} == {(0, 1)}


def test_leave_one_group_out_is_nine_fold_and_repeatable():
    import numpy as np

    from m1 import two_seed_provisional_threshold_r1 as provisional
    from m1.metrics import Frame

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "colab"))
    import evaluate_cascade_b0_r1 as common

    frames = [
        Frame(
            f"frame-{i}",
            f"group-{i}",
            np.array([[0.0, 0.0, 10.0, 10.0]]),
            np.array([0]),
            np.array([[0.0, 0.0, 10.0, 10.0]]),
            np.array([0]),
            np.array([0.9]),
            20,
            20,
        )
        for i in range(9)
    ]
    paired = {f"seed_{seed}": {name: frames for name in lock.CONFIGS} for seed in lock.SEEDS}
    first = provisional.leave_one_group_out(paired, common)
    second = provisional.leave_one_group_out(paired, common)
    assert first == second and len(first) == 9
    assert {fold["held_out_group"] for fold in first} == {f"group-{i}" for i in range(9)}
    assert all(fold["selected_configuration"] == lock.BASE for fold in first)
    assert all(fold["held_out"]["mean_agnostic_recall"] == 1 for fold in first)


def test_reader_rejects_record_or_proof_tamper(tmp_path, monkeypatch):
    proof_path, out = tmp_path / "proof.json", tmp_path / "lock.json"
    selected = {"confidence": 0.19, "iou": 0.70, "agnostic_nms": False}
    proof = {
        "schema_version": 2,
        "status": "R3_VALIDATION_PROOF",
        "seeds": list(lock.SEEDS),
        "report_sha256": {},
        "decision": {"selected": selected},
        "sealed_test_accessed": False,
    }
    monkeypatch.setattr(lock, "_proof", lambda *args: proof)
    report_paths = []
    for seed in lock.SEEDS:
        path = tmp_path / f"{seed}.json"
        path.write_text(
            json.dumps(
                {
                    "seed": seed,
                    "identity": {
                        "weight": {"sha256": str(seed)},
                        "run_contract": {},
                        "run_attestation_sha256": "a" * 64,
                    },
                }
            )
        )
        report_paths.append(path)
    proof["report_sha256"] = {str(path): lock.sha256(path) for path in report_paths}
    lock.write(report_paths, tmp_path, tmp_path, out, proof_path)
    assert lock.verify(out, proof_path, tmp_path, tmp_path)["selection"]["conf"] == 0.19
    with pytest.raises(RuntimeError, match="hash differs"):
        lock.read_for_final(
            out,
            proof_path,
            tmp_path,
            tmp_path,
            str(lock.SEEDS[0]),
            {"path": str(out), "sha256": "wrong"},
            {"path": str(out), "sha256": "wrong"},
        )
    original = out.read_bytes()
    out.write_bytes(original + b" ")
    with pytest.raises(RuntimeError, match="bytes differ"):
        lock.verify(out, proof_path, tmp_path, tmp_path)
    out.write_bytes(original)
    record = json.loads(original)
    record["candidates"][1]["conf"] = 0.20
    out.write_bytes(lock._canonical(record))
    with pytest.raises(RuntimeError, match="candidate setting"):
        lock.verify(out, proof_path, tmp_path, tmp_path)
    out.write_bytes(original)
    other = tmp_path / "other-report.json"
    other.write_bytes(report_paths[0].read_bytes())
    record = json.loads(original)
    record["candidates"][0]["val_report"] = {
        "path": str(other),
        "sha256": lock.sha256(other),
    }
    out.write_bytes(lock._canonical(record))
    with pytest.raises(RuntimeError, match="candidate reports"):
        lock.verify(out, proof_path, tmp_path, tmp_path)
    out.write_bytes(original)
    proof_path.write_bytes(proof_path.read_bytes() + b" ")
    with pytest.raises(RuntimeError, match="bytes differ"):
        lock.verify(out, proof_path, tmp_path, tmp_path)


def test_pilot_csv_reproduces_qa_cells_without_inference(monkeypatch):
    root = Path(__file__).resolve().parents[2]
    bundle = root / "tmp/yolo11n_n1_extract_r2"
    pilot_json_path = root / "docs/review/generated/d1_nms_sweep_r1.json"
    assert (
        lock.sha256(pilot_json_path)
        == "6be704d21edacd92aeb142f9fc4a5ffb6988686f24ebda9321224634f5460057"
    )
    recorded = json.loads(pilot_json_path.read_text())
    base, binding = lock._bundle(bundle)
    assert binding["images"] == 376 and binding["gt_boxes"] == 624 and binding["groups"] == 9
    predictions = {
        name: {"path": str(sweep.OUT / f"predictions_{name}.csv"), "sha256": digest}
        for name, digest in recorded["prediction_csv_sha256"].items()
    }
    # The pilot is only one seed. Bypass future authorization checks, then
    # exercise the actual seed-report builder on its 11 already-pinned CSVs.
    dummy = {"path": str(pilot_json_path), "sha256": lock.sha256(pilot_json_path)}
    identity = {
        **{
            name: dummy
            for name in (
                "weight",
                "run_contract",
                "result_archive",
                "result_manifest",
                "run_result_qa",
                "inference_authorization",
                "inference_result_qa",
            )
        },
        "run_attestation_sha256": "a" * 64,
        "inference_conf": 0.001,
    }
    monkeypatch.setattr(lock, "_qa", lambda row: None)
    monkeypatch.setattr(lock, "_run_binding", lambda *args: None)
    report = lock.build_seed_report(20261018, identity, predictions, bundle, root)
    assert report["sealed_test_accessed"] is False and len(report["configurations"]) == 11
    frames = lock._frames_by_config(base, predictions)
    anchor = sweep.point(frames[lock.BASE], 0.20)
    assert (anchor["tp"], anchor["fp"], anchor["correct_class_hits"]) == (547, 150, 457)
    sys.path.insert(0, str(root / "detector/colab"))
    import evaluate_cascade_b0_r1 as common

    for name in lock.CONFIGS:
        assert report["configurations"][name]["map50_95"] == pytest.approx(
            recorded["configurations"][name]["ap"]["map50_95"]
        )
        assert common.average_precision(frames[name])["map50_95"] == pytest.approx(
            recorded["configurations"][name]["ap"]["map50_95"]
        )
        for conf in (value for value in sweep.GRID if value in lock.GRID):
            actual = sweep.point(frames[name], conf)
            expected = next(
                c for c in recorded["configurations"][name]["cells"] if c["confidence"] == conf
            )
            assert (actual["tp"], actual["fp"], actual["correct_class_hits"]) == (
                expected["tp"],
                expected["fp"],
                expected["correct_class_hits"],
            )
            built = next(
                c for c in report["configurations"][name]["cells"] if c["confidence"] == conf
            )
            assert (built["tp"], built["fp"], built["correct_class_hits"]) == (
                expected["tp"],
                expected["fp"],
                expected["correct_class_hits"],
            )
    fine = lock._per_frame(frames[lock.BASE], 0.19)
    assert (
        sum(f["gt"] for f in fine),
        sum(f["tp"] for f in fine),
        sum(f["fp"] for f in fine),
        sum(f["correct_class_hits"] for f in fine),
    ) == (624, 555, 155, 461)
    built_fine = next(
        c for c in report["configurations"][lock.BASE]["cells"] if c["confidence"] == 0.19
    )
    assert (built_fine["tp"], built_fine["fp"], built_fine["correct_class_hits"]) == (555, 155, 461)
    assert min(f.pred_scores.min() for f in frames[lock.BASE] if len(f.pred_scores)) >= 0.001
