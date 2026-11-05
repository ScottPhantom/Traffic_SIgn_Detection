"""D1-A2-R1 Colab launcher tests: freeze, authorization gate, chain entry, A2 packaging schema."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from m1 import a2_repeat_list_r1 as a2list
from m1 import contract
from m1 import resumable_train_a2_r1 as a2t

DETECTOR_ROOT = Path(__file__).parents[1]
CHECKOUT = "c" * 40


def load_runner() -> Any:
    path = DETECTOR_ROOT / "colab/run_d1_colab_a2_r1.py"
    spec = importlib.util.spec_from_file_location("test_d1_a2_colab_r1_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_authorization(repo: Path, text: str | None = None) -> str:
    text = text or (
        "# Synthetic Owner authorization\n\n"
        f"{a2t.AUTHORIZATION_LINE}\n\n"
        f"{a2t.EXPERIMENT} list {a2list.A2_TRAIN_LIST_SHA256} "
        f"roster {a2list.SPEC.repeated_roster_sha256}\n"
    )
    path = repo / "docs/review/d1_a2_r1_owner_authorization_test.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def argv(tmp_path: Path, sha: str, *, mode: str = "fresh") -> list[str]:
    values = [
        "--repo-root",
        str(tmp_path / "repo"),
        "--bundle",
        str(tmp_path / "bundle.tar.gz"),
        "--state-dir",
        str(tmp_path / "M1_D1_Colab/runs/d1_a2_seed_20261018_r1"),
        "--mode",
        mode,
        "--device",
        "0",
        "--owner-authorization",
        "docs/review/d1_a2_r1_owner_authorization_test.md",
        "--owner-authorization-sha256",
        sha,
        "--expected-checkout",
        CHECKOUT,
    ]
    if mode == "fresh":
        values.extend(("--stop-after-epoch", "1"))
    return values


def test_launcher_constants_match_the_trainer_and_list_module() -> None:
    runner = load_runner()
    assert runner.FROZEN == a2t.FROZEN
    assert runner.A2_TRAIN_LIST_SHA256 == a2list.A2_TRAIN_LIST_SHA256
    assert runner.A2_REPEATED_ROSTER_SHA256 == a2list.SPEC.repeated_roster_sha256
    assert runner.A2_TRAIN_LIST_ENTRIES == a2list.SPEC.train_list_entries == 4687
    assert runner.A2_RULE_ID == a2list.RULE_ID
    assert runner.AUTHORIZATION_LINE == a2t.AUTHORIZATION_LINE
    assert runner.PILOT_RUN == a2t.PILOT_RUN
    assert runner.TRAINING_AUTHORIZED is False


def test_parser_requires_authorization_and_checkout(tmp_path: Path) -> None:
    runner = load_runner()
    full = argv(tmp_path, "a" * 64)
    for flag in ("--owner-authorization", "--owner-authorization-sha256", "--expected-checkout"):
        index = full.index(flag)
        with pytest.raises(SystemExit):
            runner.parser().parse_args(full[:index] + full[index + 2 :])
    parsed = runner.parser().parse_args(full)
    assert {key: getattr(parsed, key) for key in runner.FROZEN} == runner.FROZEN


def test_parser_uses_captured_predecessor_during_patch(tmp_path: Path) -> None:
    runner = load_runner()
    original = runner.r1.parser
    runner.r1.parser = runner.parser
    try:
        args = runner.parser().parse_args(argv(tmp_path, "a" * 64))
    finally:
        runner.r1.parser = original
    assert args.epochs == 100 and args.patience == 0
    assert runner.BASE_PARSER is original


@pytest.mark.parametrize(
    ("field", "value"),
    (("epochs", 40), ("patience", 30), ("batch", 8), ("seed", 20261019), ("tag", "x")),
)
def test_frozen_rejects_changed_argument(tmp_path: Path, field: str, value: object) -> None:
    runner = load_runner()
    args = runner.parser().parse_args(argv(tmp_path, "a" * 64))
    setattr(args, field, value)
    with pytest.raises(RuntimeError, match="frozen arguments differ"):
        runner.validate_frozen(args)


def test_smoke_boundary_and_resume_stop_are_constrained(tmp_path: Path) -> None:
    runner = load_runner()
    args = runner.parser().parse_args(argv(tmp_path, "a" * 64))
    args.stop_after_epoch = 2
    with pytest.raises(RuntimeError, match="smoke boundary"):
        runner.validate_frozen(args)
    resumed = runner.parser().parse_args(argv(tmp_path, "a" * 64, mode="resume"))
    runner.validate_frozen(resumed)
    resumed.stop_after_epoch = 1
    with pytest.raises(RuntimeError, match="resume forbids"):
        runner.validate_frozen(resumed)


def test_authorization_accepts_the_bound_record(tmp_path: Path) -> None:
    runner = load_runner()
    sha = write_authorization(tmp_path / "repo")
    args = runner.parser().parse_args(argv(tmp_path, sha))
    assert runner.validate_owner_authorization(args) == {
        "path": "docs/review/d1_a2_r1_owner_authorization_test.md",
        "sha256": sha,
    }


@pytest.mark.parametrize(
    ("case", "message"),
    (
        ("missing", "missing"),
        ("wrong_sha", "SHA-256 differs"),
        ("no_line", "lacks the line"),
        ("other_list", "does not name"),
        ("absolute", "repo-relative"),
        ("symlink", "symlink"),
    ),
)
def test_authorization_gate_refusals(tmp_path: Path, case: str, message: str) -> None:
    runner = load_runner()
    repo = tmp_path / "repo"
    sha = "a" * 64
    if case == "no_line":
        sha = write_authorization(repo, f"{a2t.EXPERIMENT} {a2list.A2_TRAIN_LIST_SHA256}\n")
    elif case == "other_list":
        sha = write_authorization(repo, f"{a2t.AUTHORIZATION_LINE}\n{a2t.EXPERIMENT} 339 only\n")
    elif case in {"wrong_sha", "absolute"}:
        write_authorization(repo)
    elif case == "symlink":
        real = tmp_path / "elsewhere"
        sha = write_authorization(real)
        (repo / "docs").mkdir(parents=True)
        os.symlink(real / "docs/review", repo / "docs/review")
    args = runner.parser().parse_args(argv(tmp_path, sha))
    if case == "absolute":
        args.owner_authorization = str(repo / "docs/review/d1_a2_r1_owner_authorization_test.md")
    with pytest.raises(RuntimeError, match=message):
        runner.validate_owner_authorization(args)


def test_main_refuses_without_authorization_and_writes_no_state(tmp_path: Path) -> None:
    runner = load_runner()
    (tmp_path / "repo").mkdir()
    assert runner.main(argv(tmp_path, "a" * 64)) == 1
    assert not (tmp_path / "M1_D1_Colab").exists()


def test_real_predecessor_entry_reaches_launch_without_recursion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = load_runner()
    sha = write_authorization(tmp_path / "repo")
    monkeypatch.setattr(runner, "observed_checkout", lambda _root: CHECKOUT)
    (tmp_path / "bundle.tar.gz").write_bytes(b"bundle")
    boot_id = tmp_path / "boot_id"
    boot_id.write_text("12345678-1234-1234-1234-123456789abc\n", encoding="ascii")
    monkeypatch.setattr(runner.r2, "BOOT_ID_PATH", boot_id)
    observed: dict[str, Any] = {}
    original_loader = runner.r1.base.load_detector_contract

    def fake_execute(args: Any) -> int:
        observed["argv"] = args
        observed["parser"] = runner.r1.parser
        observed["loader"] = runner.r1.base.load_detector_contract
        return 23

    monkeypatch.setattr(runner.r1, "main", fake_execute)
    assert runner.main(argv(tmp_path, sha)) == 23
    assert observed["argv"] == argv(tmp_path, sha)
    assert observed["parser"] is runner.parser
    assert observed["loader"] is not original_loader
    assert runner.r1.base.load_detector_contract is original_loader  # restored


def test_main_refuses_a_different_checkout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = load_runner()
    sha = write_authorization(tmp_path / "repo")
    monkeypatch.setattr(runner, "observed_checkout", lambda _root: "d" * 40)
    assert runner.main(argv(tmp_path, sha)) == 1
    assert not (tmp_path / "M1_D1_Colab").exists()


def test_run_binding_binds_authorization_list_and_checkout(tmp_path: Path) -> None:
    runner = load_runner()
    args = runner.parser().parse_args(argv(tmp_path, "a" * 64))
    first = runner.run_binding(args, "b" * 64)
    args.owner_authorization_sha256 = "e" * 64
    assert runner.run_binding(args, "b" * 64) != first
    args.owner_authorization_sha256 = "a" * 64
    args.expected_checkout = "f" * 40
    assert runner.run_binding(args, "b" * 64) != first


def test_train_command_uses_the_a2_trainer_with_authorization(tmp_path: Path) -> None:
    runner = load_runner()
    args = runner.parser().parse_args(argv(tmp_path, "a" * 64))
    command = runner.build_train_command(args, Path("/m/yolo11s.pt"), tmp_path / "state")
    assert command[:5] == ["uv", "run", "python", "-m", "m1.resumable_train_a2_r1"]
    assert command[command.index("--patience") + 1] == "0"
    assert command[command.index("--epochs") + 1] == "100"
    assert command[command.index("--owner-authorization-sha256") + 1] == "a" * 64
    assert command[-2:] == ["--stop-after-epoch", "1"]
    resumed = runner.parser().parse_args(argv(tmp_path, "a" * 64, mode="resume"))
    assert runner.build_train_command(resumed, Path("/m"), tmp_path)[-1] == "--resume"


# ------------------------------------------------------------------- A2 packaging validator


def fake_real(results: Path) -> SimpleNamespace:
    return SimpleNamespace(
        RESULTS_DIR=results,
        strict_json=contract.strict_json,
        sha256_file=contract.sha256_file,
        canonical_sha256=contract.canonical_sha256,
        PRETRAINED_WEIGHTS_SHA256=contract.PRETRAINED_WEIGHTS_SHA256,
        DETECTOR_LOCK_SHA256=contract.DETECTOR_LOCK_SHA256,
        GATES=contract.GATES,
        check_contract=lambda: {
            "export_manifest_sha256": "1" * 64,
            "class_map_sha256": "2" * 64,
            "split_stem_sha256": {"train": "3" * 64, "val": "4" * 64, "test": "5" * 64},
            "data_yaml": "/x/data.yaml",
        },
        validate_environment_record=lambda *_a, **_k: None,
        marker="forwarded",
    )


def make_run(tmp_path: Path, runner: Any, authorization: dict[str, str]) -> tuple[Path, dict]:
    results = tmp_path / "results/experiments"
    run_dir = results / "D1_yolo11s_a2_run"
    (run_dir / "weights").mkdir(parents=True)
    weights = {}
    for name in ("best.pt", "last.pt"):
        path = run_dir / "weights" / name
        path.write_bytes(name.encode())
        weights[name] = {"path": str(path), "sha256": contract.sha256_file(path)}
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "a2_data.yaml").write_text("train: list\n")
    (runtime / "list.txt").write_text("images/train/a.jpg\n")
    record = {
        "experiment": "D1-A2-R1",
        "run": run_dir.name,
        "seed": 20261018,
        "model": {"path": "/m", "sha256": contract.PRETRAINED_WEIGHTS_SHA256, "origin": "x"},
        "train_args": runner.expected_train_args(run_dir, str(runtime / "a2_data.yaml")),
        "contract": {**fake_real(results).check_contract()},
        "environment": {"runtime_backend": "cuda", "git_commit": CHECKOUT},
        "d05_gates": contract.GATES,
        "status": "TRAINED",
        "artifacts": {"weights": weights},
        "pilot_run": runner.PILOT_RUN,
        "single_change": "data",
        "sealed_test_accessed": False,
        "owner_authorization": authorization,
        "a2_data": {
            "rule_id": runner.A2_RULE_ID,
            "train_list_sha256": runner.A2_TRAIN_LIST_SHA256,
            "manifest_sha256": "6" * 64,
            "repeated_roster_sha256": runner.A2_REPEATED_ROSTER_SHA256,
            "train_list_entries": 4687,
            "repeated_images": 975,
            "repeated_raw_frames": 339,
            "repeated_wp35_images": 636,
            "pilot_data_yaml_sha256": "7" * 64,
            "runtime_data_yaml": str(runtime / "a2_data.yaml"),
            "runtime_data_yaml_sha256": contract.sha256_file(runtime / "a2_data.yaml"),
            "runtime_train_list": str(runtime / "list.txt"),
            "runtime_train_list_sha256": contract.sha256_file(runtime / "list.txt"),
            "data_yaml_changed_keys": ["train"],
        },
    }
    (run_dir / "run_contract.json").write_text(json.dumps(record))
    return run_dir, record


def test_a2_packaging_validator_accepts_the_a2_schema(tmp_path: Path) -> None:
    runner = load_runner()
    authorization = {"path": "docs/review/a.md", "sha256": "8" * 64}
    run_dir, _ = make_run(tmp_path, runner, authorization)
    real = fake_real(tmp_path / "results/experiments")
    shim = runner.A2ContractShim(real, authorization, CHECKOUT)
    claim = shim.inspect_run_weights(str(run_dir / "weights/best.pt"))
    assert claim["attestation"]["a2_train_list_sha256"] == runner.A2_TRAIN_LIST_SHA256
    assert claim["attestation"]["owner_authorization_sha256"] == "8" * 64
    assert len(claim["run_attestation_sha256"]) == 64
    assert shim.marker == "forwarded"


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("base_schema_only", "schema differs"),
        ("extra_key", "schema differs"),
        ("patience_30", "single data change"),
        ("pilot_data", "single data change"),
        ("other_authorization", "invariants differ"),
        ("other_list", "invariants differ"),
        ("sealed_true", "invariants differ"),
        ("runtime_tampered", "runtime file SHA-256 differs"),
        ("other_checkout", "bound CUDA checkout"),
    ),
)
def test_a2_packaging_validator_rejects(tmp_path: Path, mutation: str, message: str) -> None:
    runner = load_runner()
    authorization = {"path": "docs/review/a.md", "sha256": "8" * 64}
    run_dir, record = make_run(tmp_path, runner, authorization)
    if mutation == "base_schema_only":
        record = {k: v for k, v in record.items() if k in runner.BASE_RUN_CONTRACT_KEYS}
    elif mutation == "extra_key":
        record["note"] = "x"
    elif mutation == "patience_30":
        record["train_args"]["patience"] = 30
    elif mutation == "pilot_data":
        record["train_args"]["data"] = "/x/data.yaml"
    elif mutation == "other_authorization":
        record["owner_authorization"] = {"path": "docs/review/a.md", "sha256": "9" * 64}
    elif mutation == "other_list":
        record["a2_data"]["train_list_sha256"] = "0" * 64
    elif mutation == "sealed_true":
        record["sealed_test_accessed"] = True
    elif mutation == "runtime_tampered":
        Path(record["a2_data"]["runtime_data_yaml"]).write_text("train: other\n")
    elif mutation == "other_checkout":
        record["environment"]["git_commit"] = "d" * 40
    (run_dir / "run_contract.json").write_text(json.dumps(record))
    real = fake_real(tmp_path / "results/experiments")
    with pytest.raises(RuntimeError, match=message):
        runner.inspect_a2_run_weights(
            real, str(run_dir / "weights/best.pt"), authorization, CHECKOUT
        )
