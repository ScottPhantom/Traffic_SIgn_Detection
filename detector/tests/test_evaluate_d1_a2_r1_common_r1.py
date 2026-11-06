"""D1-A2-R1 common evaluator: candidate pins, run attestation, refusal paths, single change.

Synthetic fixtures only: no model is loaded, no inference runs, the bundle is never opened and the
sealed test is never touched.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import io
import json
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from m1 import a2_repeat_list_r1 as a2list
from m1 import contract
from m1 import resumable_train_a2_r1 as a2t

# The predecessor colab modules live next to the evaluator in the checkout; `contract` resolves
# that checkout even when this test file is staged elsewhere.
sys.path.insert(0, str(contract.DETECTOR_ROOT / "colab"))
HERE = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ev = _load("test_d1_a2_common_eval_r1", HERE / "colab/evaluate_d1_a2_r1_common_r1.py")
a3eval = ev.a3eval
launcher = ev.launcher

CHECKOUT = "c" * 40
RUN = "D1_yolo11s_wp33_afa03d4b_20261018_20261106T013000_a2_r1"
STATE_SUFFIX = "M1_D1_Colab/runs/d1_a2_seed_20261018_r1"
AUTH_RELATIVE = "docs/review/d1_a2_r1_owner_authorization_r1.md"
ENVIRONMENT = {
    "cuda_available": True,
    "cuda_version": "13.0",
    "detector_lock_sha256": contract.DETECTOR_LOCK_SHA256,
    "git_commit": CHECKOUT,
    "git_dirty_files": 0,
    "gpu_name": "NVIDIA L4",
    "hardware_chip": "UNKNOWN",
    "machine": "x86_64",
    "mps_available": False,
    "nvidia_driver": "580.82.07",
    "platform": "Linux-6.6.122+-x86_64-with-glibc2.39",
    "python": "3.12.3",
    "runtime_backend": "cuda",
    "torch": "2.14.1+cu130",
    "ultralytics": "8.4.172",
}


def write_authorization(repo: Path) -> str:
    text = (
        "# Synthetic Owner authorization (unit test)\n\n"
        f"{a2t.AUTHORIZATION_LINE}\n\n"
        f"{a2t.EXPERIMENT} list {a2list.A2_TRAIN_LIST_SHA256} "
        f"roster {a2list.SPEC.repeated_roster_sha256}\n"
    )
    path = repo / AUTH_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def attestation_for(record: dict[str, Any], record_bytes: bytes) -> str:
    """Test-local copy of the launcher's attestation formula (cross-checked below)."""
    return contract.canonical_sha256(
        {
            "experiment": "D1-A2-R1",
            "run": record["run"],
            "seed": 20261018,
            "run_contract_sha256": sha(record_bytes),
            "approved_pretrained_sha256": contract.PRETRAINED_WEIGHTS_SHA256,
            "export_manifest_sha256": ev.GOVERNED_DATA_CONTRACT["export_manifest_sha256"],
            "detector_lock_sha256": contract.DETECTOR_LOCK_SHA256,
            "owner_authorization_sha256": record["owner_authorization"]["sha256"],
            "a2_train_list_sha256": launcher.A2_TRAIN_LIST_SHA256,
            "a2_repeated_roster_sha256": launcher.A2_REPEATED_ROSTER_SHA256,
            "weights": {
                name: record["artifacts"]["weights"][name]["sha256"]
                for name in ("best.pt", "last.pt")
            },
        }
    )


def make_record(colab_root: Path, authorization: dict[str, str]) -> dict[str, Any]:
    run_dir = colab_root / "results/experiments" / RUN
    runtime = colab_root / "data/processed/d1_a2_r1/runtime"
    weights = {
        name: {"path": str(run_dir / "weights" / name), "sha256": sha(name.encode() * 7)}
        for name in ("best.pt", "last.pt")
    }
    return {
        "experiment": "D1-A2-R1",
        "run": RUN,
        "seed": 20261018,
        "model": {
            "path": str(colab_root / "models/pretrained/yolo11s.pt"),
            "sha256": contract.PRETRAINED_WEIGHTS_SHA256,
            "origin": "approved",
        },
        "train_args": launcher.expected_train_args(run_dir, str(runtime / "a2_data.yaml")),
        "contract": {
            **ev.GOVERNED_DATA_CONTRACT,
            "data_yaml": str(colab_root / "data/processed/m1_yolo/data.yaml"),
        },
        "environment": dict(ENVIRONMENT),
        "d05_gates": dict(contract.GATES),
        "status": "TRAINED",
        "artifacts": {"weights": weights},
        "pilot_run": launcher.PILOT_RUN,
        "single_change": "data",
        "sealed_test_accessed": False,
        "owner_authorization": dict(authorization),
        "a2_data": {
            "rule_id": launcher.A2_RULE_ID,
            "train_list_sha256": launcher.A2_TRAIN_LIST_SHA256,
            "manifest_sha256": "6" * 64,
            "repeated_roster_sha256": launcher.A2_REPEATED_ROSTER_SHA256,
            "train_list_entries": 4687,
            "repeated_images": 975,
            "repeated_raw_frames": 339,
            "repeated_wp35_images": 636,
            "pilot_data_yaml_sha256": "7" * 64,
            "runtime_data_yaml": str(runtime / "a2_data.yaml"),
            "runtime_data_yaml_sha256": "8" * 64,
            "runtime_train_list": str(runtime / "a2_train_list.txt"),
            "runtime_train_list_sha256": "9" * 64,
            "data_yaml_changed_keys": ["train"],
        },
    }


def attempt(mode: str, status: str, start: str, end: str, digest: str) -> dict[str, Any]:
    return {
        "mode": mode,
        "started_at": start,
        "finished_at": end,
        "status": status,
        "error": None,
        "runtime_identity": {"schema": launcher.r2.RUNTIME_SCHEMA, "digest": digest},
        "run_binding_sha256": "a" * 64,
        "checkpoint_binding_sha256": "b" * 64,
    }


def make_execution(colab_root: Path, authorization: dict[str, str]) -> dict[str, Any]:
    attempts = [
        attempt(
            "fresh",
            "PAUSED_FOR_RESUME",
            "2026-11-05T20:00:00+07:00",
            "2026-11-05T20:10:00+07:00",
            "d" * 64,
        ),
        attempt(
            "resume",
            "SUCCEEDED",
            "2026-11-05T20:30:00+07:00",
            "2026-11-06T01:30:00+07:00",
            "e" * 64,
        ),
    ]
    run_dir = colab_root / "results/experiments" / RUN
    return {
        "schema_version": 2,
        "status": "SUCCEEDED",
        "mode": "resume",
        "started_at": attempts[1]["started_at"],
        "finished_at": attempts[1]["finished_at"],
        "error": None,
        "sealed_test_accessed": False,
        "seed": 20261018,
        "epochs": 100,
        "imgsz": 1280,
        "batch": 4,
        "device": "0",
        "tag": "a2_r1",
        "run_dir": str(run_dir),
        "training_outcome": {
            "status": "COMPLETED",
            "run": RUN,
            "run_dir": str(run_dir),
            "completed_epoch": 100,
            "resumed": True,
            "sealed_test_accessed": False,
        },
        "runtime_identity": attempts[1]["runtime_identity"],
        "run_binding_sha256": "a" * 64,
        "checkpoint_binding_sha256": "b" * 64,
        "execution_attempts": attempts,
        "experiment": "D1-A2-R1",
        "package": "D1-A2-R1",
        "owner_authorization": dict(authorization),
        "a2_train_list_sha256": launcher.A2_TRAIN_LIST_SHA256,
        "a2_repeated_roster_sha256": launcher.A2_REPEATED_ROSTER_SHA256,
        "checkout_commit": CHECKOUT,
        "state_path": f"/content/drive/MyDrive/{STATE_SUFFIX}",
    }


def results_csv(epochs: int = 100) -> bytes:
    rows = ["epoch,time,metrics/mAP50(B)"]
    rows += [f"{epoch},{epoch * 10.0},0.5" for epoch in range(1, epochs + 1)]
    return ("\n".join(rows) + "\n").encode()


ARGS_YAML = b"task: detect\ndata: /content/x/a2_data.yaml\nepochs: 100\npatience: 0\n"


def build(
    tmp_path: Path,
    *,
    record_edit=None,
    execution_edit=None,
    members_edit=None,
    manifest_edit=None,
    live_edit=None,
    latest_edit=None,
    attest: str | None = None,
) -> argparse.Namespace:
    """Write a synthetic A2 result archive, manifest, live state and repo; return CLI args."""
    repo = tmp_path / "repo"
    auth_sha = write_authorization(repo)
    authorization = {"path": AUTH_RELATIVE, "sha256": auth_sha}
    colab_root = Path("/content/Traffic_Sign_Detector")
    record = make_record(colab_root, authorization)
    if record_edit:
        record_edit(record)
    record_bytes = json.dumps(record, indent=2, sort_keys=True).encode()
    execution = make_execution(colab_root, authorization)
    if execution_edit:
        execution_edit(execution)
    members = {
        f"{RUN}/weights/best.pt": b"best.pt" * 7,
        f"{RUN}/weights/last.pt": b"last.pt" * 7,
        f"{RUN}/results.csv": results_csv(),
        f"{RUN}/args.yaml": ARGS_YAML,
        f"{RUN}/run_contract.json": record_bytes,
        "colab_logs/colab_execution.json": json.dumps(execution, sort_keys=True).encode(),
        "colab_logs/colab_train.log": b"D1 Colab workflow started\nTraining end\n",
        "colab_logs/DB_logger.db": b"sqlite-placeholder",
    }
    if members_edit:
        members_edit(members)
    out = tmp_path / "drive" / STATE_SUFFIX
    out.mkdir(parents=True)
    archive = out / f"{RUN}_result.tar.gz"
    with tarfile.open(archive, "x:gz") as sink:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            sink.addfile(info, io.BytesIO(data))
    manifest = {
        "status": "D1_COLAB_RESULT_PACKAGE",
        "run": RUN,
        "archive_name": archive.name,
        "archive_sha256": sha(archive.read_bytes()),
        "files": [
            {"path": name, "size": len(data), "sha256": sha(data)} for name, data in members.items()
        ],
        "terminal_outcome": "SUCCEEDED",
        "sealed_test_accessed": False,
        "run_attestation_sha256": attest or attestation_for(record, record_bytes),
    }
    if manifest_edit:
        manifest_edit(manifest)
    manifest_path = archive.with_name(f"{archive.name}.manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    live = copy.deepcopy(execution)
    if live_edit:
        live_edit(live)
    (out / "colab_execution.json").write_text(json.dumps(live))
    latest = {
        "schema_version": 1,
        "generation": "epoch-0100",
        "manifest_sha256": "f" * 64,
        "binding_sha256": "b" * 64,
    }
    if latest_edit:
        latest_edit(latest)
    (out / "recovery").mkdir()
    (out / "recovery/latest.json").write_text(json.dumps(latest))
    (tmp_path / "bundle-not-read").mkdir()
    return argparse.Namespace(
        bundle=tmp_path / "bundle-not-read",
        state=out,
        archive=archive,
        archive_sha256=sha(archive.read_bytes()),
        manifest=manifest_path,
        manifest_sha256=sha(manifest_path.read_bytes()),
        owner_authorization_sha256=auth_sha,
        expected_checkout=CHECKOUT,
        output_dir=tmp_path / "out",
        repo_root=repo,
        device="cpu",
    )


# ------------------------------------------------------------------------------- acceptance


def test_candidate_verifies_a_conforming_a2_result(tmp_path: Path) -> None:
    args = build(tmp_path)
    candidate = ev.verify_candidate(args)
    assert candidate["run"] == RUN
    assert candidate["best_sha256"] == sha(b"best.pt" * 7)
    assert candidate["training_outcome"] == "COMPLETED"
    assert candidate["checkout_commit"] == CHECKOUT


def test_offline_attestation_equals_the_launcher_packager_attestation(tmp_path: Path) -> None:
    """The launcher's own `inspect_a2_run_weights` on a local mirror gives the same SHA-256."""
    authorization = {"path": AUTH_RELATIVE, "sha256": "8" * 64}
    colab_root = tmp_path / "content"
    record = make_record(colab_root, authorization)
    run_dir = colab_root / "results/experiments" / RUN
    (run_dir / "weights").mkdir(parents=True)
    for name in ("best.pt", "last.pt"):
        (run_dir / "weights" / name).write_bytes(name.encode() * 7)
    for key in ("runtime_data_yaml", "runtime_train_list"):
        path = Path(record["a2_data"][key])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(key)
        record["a2_data"][f"{key}_sha256"] = contract.sha256_file(path)
    record_bytes = json.dumps(record, indent=2).encode()
    (run_dir / "run_contract.json").write_bytes(record_bytes)
    real = SimpleNamespace(
        RESULTS_DIR=colab_root / "results/experiments",
        strict_json=contract.strict_json,
        sha256_file=contract.sha256_file,
        canonical_sha256=contract.canonical_sha256,
        PRETRAINED_WEIGHTS_SHA256=contract.PRETRAINED_WEIGHTS_SHA256,
        DETECTOR_LOCK_SHA256=contract.DETECTOR_LOCK_SHA256,
        GATES=contract.GATES,
        check_contract=lambda: dict(record["contract"]),
        validate_environment_record=contract.validate_environment_record,
    )
    claim = launcher.inspect_a2_run_weights(
        real, str(run_dir / "weights/best.pt"), authorization, CHECKOUT
    )
    manifest = {
        "run": RUN,
        "files": [
            {"path": f"{RUN}/weights/{n}", "sha256": sha(n.encode() * 7)}
            for n in ("best.pt", "last.pt")
        ],
        "run_attestation_sha256": claim["run_attestation_sha256"],
    }
    offline = ev.verify_attestation(manifest, record_bytes, CHECKOUT, "8" * 64)
    assert offline["run_attestation_sha256"] == claim["run_attestation_sha256"]
    assert offline["attestation"] == claim["attestation"]
    assert attestation_for(record, record_bytes) == claim["run_attestation_sha256"]


def test_training_log_check_accepts_the_real_pilot_log_shape() -> None:
    run_dir = contract.RESULTS_DIR / launcher.PILOT_RUN
    if not (run_dir / "results.csv").is_file():
        pytest.skip("pilot run directory not present locally")
    ev.verify_training_log(
        (run_dir / "results.csv").read_bytes(), (run_dir / "args.yaml").read_bytes()
    )


# ---------------------------------------------------------------------------------- refusals


def _set(path: tuple, value: Any):
    def edit(payload: dict[str, Any]) -> None:
        target = payload
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    return edit


def _drop(path: tuple):
    def edit(payload: dict[str, Any]) -> None:
        target = payload
        for key in path[:-1]:
            target = target[key]
        del target[path[-1]]

    return edit


REFUSALS = {
    # CLI-pinned hashes
    "archive_sha_differs": ({}, "archive_sha256", "0" * 64, "archive SHA-256 differs"),
    "manifest_sha_differs": ({}, "manifest_sha256", "0" * 64, "manifest SHA-256 differs"),
    "archive_sha_malformed": ({}, "archive_sha256", "ABC", "64 lowercase hex"),
    "authorization_sha_absent": ({}, "owner_authorization_sha256", None, "64 lowercase hex"),
    "checkout_malformed": ({}, "expected_checkout", "abc", "40-hex"),
    "authorization_sha_other": (
        {},
        "owner_authorization_sha256",
        "1" * 64,
        "owner authorization SHA-256 differs",
    ),
    "checkout_other": ({}, "expected_checkout", "d" * 40, "bound CUDA L4 checkout|binding"),
    # manifest / archive
    "manifest_unbound": (
        {"manifest_edit": _set(("archive_sha256",), "0" * 64)},
        None,
        None,
        "does not bind",
    ),
    "manifest_sealed_true": (
        {"manifest_edit": _set(("sealed_test_accessed",), True)},
        None,
        None,
        "identity/outcome differs",
    ),
    "attestation_wrong": ({"attest": "0" * 64}, None, None, "attestation does not verify"),
    "run_name_other": (
        {"manifest_edit": _set(("run",), "D1_yolo11s_wp33_afa03d4b_20261018_x_pilot")},
        None,
        None,
        "differs",
    ),
    # run contract
    "record_experiment_other": (
        {"record_edit": _set(("experiment",), "D1-A3-R1")},
        None,
        None,
        "invariants differ",
    ),
    "record_list_other": (
        {"record_edit": _set(("a2_data", "train_list_sha256"), "0" * 64)},
        None,
        None,
        "train list SHA-256 differs",
    ),
    "record_339_variant_list": (
        {
            "record_edit": _set(
                ("a2_data", "train_list_sha256"),
                "c953d458b087f80939422d6d2d8a7243b4505ce7e1f270289b36bb95b88c6b95",
            )
        },
        None,
        None,
        "train list SHA-256 differs",
    ),
    "record_git_dirty": (
        {"record_edit": _set(("environment", "git_dirty_files"), 1)},
        None,
        None,
        "clean Git checkout",
    ),
    "record_sealed_true": (
        {"record_edit": _set(("sealed_test_accessed",), True)},
        None,
        None,
        "sealed_test_accessed=false",
    ),
    "record_authorization_sha_missing": (
        {"record_edit": _drop(("owner_authorization", "sha256")), "attest": "0" * 64},
        None,
        None,
        "owner_authorization schema differs",
    ),
    "record_epochs_40": (
        {"record_edit": _set(("train_args", "epochs"), 40)},
        None,
        None,
        "single data change",
    ),
    "record_patience_30": (
        {"record_edit": _set(("train_args", "patience"), 30)},
        None,
        None,
        "single data change",
    ),
    "record_pilot_data": (
        {"record_edit": _set(("train_args", "data"), "/content/x/data.yaml")},
        None,
        None,
        "single data change",
    ),
    "record_extra_key": ({"record_edit": _set(("note",), "x")}, None, None, "schema differs"),
    "record_not_l4": (
        {"record_edit": _set(("environment", "gpu_name"), "NVIDIA A100")},
        None,
        None,
        "CUDA L4",
    ),
    "record_gates_changed": (
        {"record_edit": _set(("d05_gates", "fp_per_image"), 0.5)},
        None,
        None,
        "D-05 gates",
    ),
    "record_export_other": (
        {"record_edit": _set(("contract", "export_manifest_sha256"), "1" * 64)},
        None,
        None,
        "governed contract",
    ),
    # execution record (archived)
    "execution_experiment_other": (
        {"execution_edit": _set(("experiment",), "D1-A3-R1")},
        None,
        None,
        "experiment differs",
    ),
    "execution_status_failed": (
        {"execution_edit": _set(("status",), "FAILED")},
        None,
        None,
        "two-runtime evidence|not SUCCEEDED",
    ),
    "execution_epochs_40": (
        {"execution_edit": _set(("epochs",), 40)},
        None,
        None,
        "not a 100-epoch run",
    ),
    "execution_early_stopped": (
        {
            "execution_edit": lambda e: e["training_outcome"].update(
                status="COMPLETED_EARLY_STOPPED", completed_epoch=73
            )
        },
        None,
        None,
        "early-stopped",
    ),
    "execution_outcome_epoch_99": (
        {"execution_edit": _set(("training_outcome", "completed_epoch"), 99)},
        None,
        None,
        "did not complete the frozen 100 epochs",
    ),
    "execution_sealed_true": (
        {"execution_edit": _set(("sealed_test_accessed",), True)},
        None,
        None,
        "two-runtime evidence|sealed_test_accessed=false",
    ),
    "execution_list_other": (
        {"execution_edit": _set(("a2_train_list_sha256",), "0" * 64)},
        None,
        None,
        "execution train list",
    ),
    "execution_authorization_missing": (
        {"execution_edit": _set(("owner_authorization",), None)},
        None,
        None,
        "authorization SHA-256 is missing",
    ),
    "execution_single_attempt": (
        {"execution_edit": lambda e: e.update(execution_attempts=e["execution_attempts"][1:])},
        None,
        None,
        "two attempts",
    ),
    # training log
    "results_99_epochs": (
        {"members_edit": lambda m: m.update({f"{RUN}/results.csv": results_csv(99)})},
        None,
        None,
        "epochs 1..100",
    ),
    "args_yaml_patience": (
        {
            "members_edit": lambda m: m.update(
                {f"{RUN}/args.yaml": ARGS_YAML.replace(b"patience: 0", b"patience: 30")}
            )
        },
        None,
        None,
        "args.yaml",
    ),
    "archived_best_not_bound": (
        {"members_edit": lambda m: m.update({f"{RUN}/weights/best.pt": b"other"})},
        None,
        None,
        "archived weight differs",
    ),
    # live state
    "live_not_succeeded": (
        {"live_edit": _set(("status",), "FAILED")},
        None,
        None,
        "live execution status",
    ),
    "live_epoch_40": (
        {"latest_edit": _set(("generation",), "epoch-0040")},
        None,
        None,
        "live run",
    ),
    "live_other_binding": (
        {"latest_edit": _set(("binding_sha256",), "0" * 64)},
        None,
        None,
        "live run",
    ),
}


@pytest.mark.parametrize("case", sorted(REFUSALS))
def test_candidate_refusals(tmp_path: Path, case: str) -> None:
    build_kwargs, field, value, message = REFUSALS[case]
    args = build(tmp_path, **build_kwargs)
    if field is not None:
        setattr(args, field, value)
    with pytest.raises(RuntimeError, match=message):
        ev.verify_candidate(args)


def test_missing_local_owner_authorization_record_is_refused(tmp_path: Path) -> None:
    args = build(tmp_path)
    (args.repo_root / AUTH_RELATIVE).unlink()
    with pytest.raises(RuntimeError, match="Owner authorization record"):
        ev.verify_candidate(args)


def test_tampered_local_owner_authorization_record_is_refused(tmp_path: Path) -> None:
    args = build(tmp_path)
    (args.repo_root / AUTH_RELATIVE).write_text("OWNER_AUTHORIZES_TRAINING: D1-A2-R1\n")
    with pytest.raises(RuntimeError, match="SHA-256 differs"):
        ev.verify_candidate(args)


def test_tampered_archive_member_is_refused(tmp_path: Path) -> None:
    def edit(manifest: dict[str, Any]) -> None:
        manifest["files"][0]["sha256"] = "0" * 64

    args = build(tmp_path, manifest_edit=edit)
    with pytest.raises(RuntimeError, match="member differs"):
        ev.verify_candidate(args)


def test_renamed_archive_is_refused(tmp_path: Path) -> None:
    args = build(tmp_path)
    renamed = args.archive.with_name("renamed.tar.gz")
    args.archive.rename(renamed)
    args.archive = renamed
    with pytest.raises(RuntimeError, match="identity/outcome differs"):
        ev.verify_candidate(args)


def test_extract_best_refuses_a_best_pt_not_in_the_run_contract(tmp_path: Path) -> None:
    args = build(tmp_path)
    manifest = json.loads(args.manifest.read_text())
    out = tmp_path / "x"
    out.mkdir()
    with pytest.raises(RuntimeError, match="best.pt binding differs"):
        ev.extract_best(args.archive, manifest, out, "0" * 64)
    best = ev.extract_best(args.archive, manifest, out, sha(b"best.pt" * 7))
    assert best.read_bytes() == b"best.pt" * 7


# ------------------------------------------------------------------- run order and output


def _patch_common_path(monkeypatch: pytest.MonkeyPatch, calls: list) -> None:
    frames = [SimpleNamespace(gt_boxes=[0] * 2)] * 248 + [SimpleNamespace(gt_boxes=[0])] * 128

    def verify_package(root: Path, sha256: str) -> None:
        calls.append(("verify_package", sha256))

    def scope(root: Path, csv_path: Path, sha256: str) -> None:
        calls.append(("scope", csv_path.name, sha256))

    def infer(root: Path, weights: Path, device: str) -> list:
        calls.append(("infer", contract.sha256_file(weights), device))
        return frames

    def baseline(got: list, path: Path) -> list:
        calls.append(("baseline", path.name))
        return ["pilot-frames"]

    def report(got: list) -> dict:
        return {"report_of": "pilot" if got == ["pilot-frames"] else "candidate"}

    monkeypatch.setattr(a3eval, "verify_package", verify_package)
    monkeypatch.setattr(ev.common, "verify_evaluation_scope", scope)
    monkeypatch.setattr(a3eval, "infer", infer)
    monkeypatch.setattr(ev.common, "load_pinned_baseline", baseline)
    monkeypatch.setattr(ev.common, "report", report)
    for frame in frames:
        frame.pred_boxes, frame.pred_classes, frame.pred_scores, frame.stem = [], [], [], "s"


def test_candidate_refusal_happens_before_any_bundle_or_model_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list = []
    _patch_common_path(monkeypatch, calls)
    args = build(tmp_path)
    args.archive_sha256 = "0" * 64
    with pytest.raises(RuntimeError, match="archive SHA-256 differs"):
        ev.run(args)
    assert calls == [] and not args.output_dir.exists()


def test_refuses_existing_output_dir(tmp_path: Path) -> None:
    args = build(tmp_path)
    args.output_dir.mkdir()
    with pytest.raises(RuntimeError, match="refuse overwriting"):
        ev.run(args)


def test_run_uses_the_predecessor_common_path_and_writes_bound_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list = []
    _patch_common_path(monkeypatch, calls)
    args = build(tmp_path)
    result = ev.run(args)
    assert calls == [
        ("verify_package", "8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da"),
        ("scope", "yolo54_predictions_val.csv", a3eval.common.PINNED_YOLO54_SHA256),
        ("infer", sha(b"best.pt" * 7), "cpu"),
        ("baseline", "yolo54_predictions_val.csv"),
    ]
    written = json.loads((args.output_dir / "comparison_a2_r1.json").read_text())
    assert written == result
    assert written["sealed_test_accessed"] is False
    assert written["a2_common_method"] == {"report_of": "candidate"}
    assert written["pilot_common_method"] == {"report_of": "pilot"}
    assert written["a2_result_archive_sha256"] == args.archive_sha256
    assert written["a2_result_manifest_sha256"] == args.manifest_sha256
    assert written["owner_authorization"]["sha256"] == args.owner_authorization_sha256
    assert written["a2_train_list_sha256"] == a2list.A2_TRAIN_LIST_SHA256
    assert written["prediction_csv_sha256"] == contract.sha256_file(
        args.output_dir / "a2_predictions.csv"
    )
    assert written["predecessor_sha256"]["a3_common_evaluator"] == ev.A3_EVALUATOR_SHA256


# --------------------------------------------------------------------- single-change property


def test_pilot_side_and_inference_are_the_predecessor_objects() -> None:
    assert a3eval.__name__ == "evaluate_d1_a3_r2_common_r1"
    assert contract.sha256_file(Path(a3eval.__file__)) == ev.A3_EVALUATOR_SHA256
    assert ev.common is a3eval.common
    assert ev.BUNDLE_SHA256 == a3eval.BUNDLE_SHA256
    assert (ev.FRAMES, ev.GT_BOXES) == (376, 624)
    # No inference, matching, AP or operating-point code of its own.
    for name in ("infer", "report", "operating_point", "average_precision", "verify_package"):
        assert name not in vars(ev)


def test_output_schema_differs_from_a3_only_on_the_candidate_side(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list = []
    _patch_common_path(monkeypatch, calls)
    a2 = set(ev.run(build(tmp_path)))
    a3_keys = {
        "package",
        "split",
        "frames",
        "gt_boxes",
        "a3_common_method",
        "pilot_common_method",
        "a3_best_weight_sha256",
        "a3_result_manifest_sha256",
        "a3_result_archive_sha256",
        "bundle_manifest_sha256",
        "prediction_csv_sha256",
        "sealed_test_accessed",
    }
    stored = contract.REPO_ROOT / (
        "results/experiments/d1_a3_seed_20261018_r2/evaluation_common_r1/comparison_a3_r1.json"
    )
    if stored.is_file():
        assert set(json.loads(stored.read_text())) == a3_keys
    renamed = {key.replace("a3_", "a2_") for key in a3_keys}
    assert renamed <= a2
    assert a2 - renamed == {
        "experiment",
        "a2_run",
        "a2_run_attestation_sha256",
        "a2_run_contract_sha256",
        "a2_train_list_sha256",
        "a2_training_outcome",
        "owner_authorization",
        "checkout_commit",
        "predecessor_sha256",
    }


def test_predecessor_pins_match_the_checkout() -> None:
    pins = ev.verify_predecessors()
    assert pins["a2_launcher"] == launcher_sha() == ev.A2_LAUNCHER_SHA256


def launcher_sha() -> str:
    return contract.sha256_file(ev.A2_LAUNCHER)


def test_cli_requires_every_candidate_pin() -> None:
    required = {
        "--bundle",
        "--state",
        "--archive",
        "--archive-sha256",
        "--manifest",
        "--manifest-sha256",
        "--owner-authorization-sha256",
        "--expected-checkout",
        "--output-dir",
    }
    for flag in required:
        argv = []
        for other in sorted(required - {flag}):
            argv += [other, "x"]
        with pytest.raises(SystemExit):
            ev.parser().parse_args(argv)
