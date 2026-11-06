"""D1-S2-R1 launcher gates and package attestation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from m1 import contract
from m1 import resumable_train_s2_r1 as s2

CHECKOUT = "c" * 40


def runner() -> Any:
    path = Path(__file__).parents[1] / "colab/run_d1_colab_s2_r1.py"
    spec = importlib.util.spec_from_file_location("s2_colab_test_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def argv(tmp_path: Path, sha: str, mode: str = "fresh") -> list[str]:
    values = [
        "--repo-root",
        str(tmp_path / "repo"),
        "--bundle",
        str(tmp_path / "bundle.tar.gz"),
        "--state-dir",
        str(tmp_path / "M1_D1_Colab/runs/d1_s2_seed_20261019_r1"),
        "--mode",
        mode,
        "--device",
        "0",
        "--owner-authorization",
        "docs/review/auth.md",
        "--owner-authorization-sha256",
        sha,
        "--expected-checkout",
        CHECKOUT,
    ]
    return values + (["--stop-after-epoch", "1"] if mode == "fresh" else [])


def write_authorization(repo: Path) -> str:
    path = repo / "docs/review/auth.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        f"{s2.AUTHORIZATION_LINE}\n{s2.EXPERIMENT}\n{s2.PILOT_CONTRACT_SHA256}\n20261019\n",
        encoding="utf-8",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_launcher_freeze_and_command(tmp_path: Path) -> None:
    launch = runner()
    args = launch.parser().parse_args(argv(tmp_path, "a" * 64))
    assert launch.FROZEN == s2.FROZEN
    assert launch.BASE_PARSER is not launch.parser
    launch.validate_frozen(args)
    command = launch.build_train_command(args, Path("/m/yolo11s.pt"), tmp_path)
    assert command[:5] == ["uv", "run", "python", "-m", "m1.resumable_train_s2_r1"]
    assert command[-2:] == ["--stop-after-epoch", "1"]
    assert command[command.index("--seed") + 1] == "20261019"
    args.seed = 20261020
    with pytest.raises(RuntimeError, match="frozen arguments differ"):
        launch.validate_frozen(args)


def test_launcher_authorization_and_checkout_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launch = runner()
    repo = tmp_path / "repo"
    sha = write_authorization(repo)
    args = launch.parser().parse_args(argv(tmp_path, sha))
    assert launch.validate_owner_authorization(args)["sha256"] == sha
    monkeypatch.setattr(launch, "observed_checkout", lambda _root: CHECKOUT)
    assert launch.validate_launch_context(args)[1] == CHECKOUT
    args.expected_checkout = "d" * 40
    with pytest.raises(RuntimeError, match="checkout differs"):
        launch.validate_launch_context(args)
    args.expected_checkout = CHECKOUT
    args.owner_authorization_sha256 = "b" * 64
    with pytest.raises(RuntimeError, match="SHA-256 differs"):
        launch.validate_owner_authorization(args)


def test_main_enters_predecessor_without_recursion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launch = runner()
    sha = write_authorization(tmp_path / "repo")
    monkeypatch.setattr(launch, "observed_checkout", lambda _root: CHECKOUT)
    before = (
        launch.r1.parser,
        launch.r1.build_train_command,
        launch.r2.run_binding,
        launch.r1.base.write_json,
        launch.r1.base.load_detector_contract,
    )

    def fake_main(_argv: list[str]) -> int:
        assert launch.r1.parser is launch.parser
        assert launch.r1.build_train_command is launch.build_train_command
        return 23

    monkeypatch.setattr(launch.r6, "main", fake_main)
    assert launch.main(argv(tmp_path, sha)) == 23
    assert (
        launch.r1.parser,
        launch.r1.build_train_command,
        launch.r2.run_binding,
        launch.r1.base.write_json,
        launch.r1.base.load_detector_contract,
    ) == before


def make_run(tmp_path: Path, launch: Any, auth: dict[str, str]) -> tuple[Path, dict[str, Any]]:
    root = tmp_path / "results/experiments"
    run = root / "D1_yolo11s_s2_run"
    (run / "weights").mkdir(parents=True)
    weights = {}
    for name in ("best.pt", "last.pt"):
        file = run / "weights" / name
        file.write_bytes(name.encode())
        weights[name] = {"path": str(file), "sha256": contract.sha256_file(file)}
    bound = {
        "export_manifest_sha256": launch.PILOT_EXPORT_SHA256,
        "class_map_sha256": "2" * 64,
        "split_stem_sha256": {"train": "3" * 64, "val": "4" * 64, "test": "5" * 64},
        "data_yaml": "/content/Traffic_Sign_Detector/data/processed/m1_yolo/data.yaml",
    }
    record = {
        "experiment": launch.EXPERIMENT,
        "run": run.name,
        "seed": 20261019,
        "model": {"path": "/m", "sha256": contract.PRETRAINED_WEIGHTS_SHA256, "origin": "x"},
        "train_args": launch.expected_train_args(run, bound["data_yaml"]),
        "contract": bound,
        "environment": {"runtime_backend": "cuda", "gpu_name": "NVIDIA L4", "git_commit": CHECKOUT},
        "d05_gates": contract.GATES,
        "status": "TRAINED",
        "artifacts": {"weights": weights},
        "pilot_run": launch.PILOT_RUN,
        "single_change": "seed",
        "pilot_contract_sha256": launch.PILOT_CONTRACT_SHA256,
        "owner_authorization": auth,
        "sealed_test_accessed": False,
    }
    (run / "run_contract.json").write_text(json.dumps(record))
    return run, record


def fake_contract(tmp_path: Path, bound: dict[str, Any], launch: Any) -> SimpleNamespace:
    return SimpleNamespace(
        RESULTS_DIR=tmp_path / "results/experiments",
        strict_json=contract.strict_json,
        sha256_file=contract.sha256_file,
        canonical_sha256=contract.canonical_sha256,
        PRETRAINED_WEIGHTS_SHA256=contract.PRETRAINED_WEIGHTS_SHA256,
        DETECTOR_LOCK_SHA256=contract.DETECTOR_LOCK_SHA256,
        GATES=contract.GATES,
        check_contract=lambda: bound,
        validate_environment_record=lambda *_a, **_k: None,
    )


@pytest.mark.parametrize("mutation", ["none", "seed", "data", "seal", "export", "gpu", "auth"])
def test_package_validator(tmp_path: Path, mutation: str) -> None:
    launch = runner()
    auth = {"path": "docs/review/auth.md", "sha256": "a" * 64}
    run, record = make_run(tmp_path, launch, auth)
    bound = json.loads(json.dumps(record["contract"]))
    if mutation == "seed":
        record["train_args"]["seed"] = 20261020
    elif mutation == "data":
        record["train_args"]["data"] = "/a2/list.yaml"
    elif mutation == "seal":
        record["sealed_test_accessed"] = True
    elif mutation == "export":
        record["contract"]["export_manifest_sha256"] = "0" * 64
    elif mutation == "gpu":
        record["environment"]["gpu_name"] = "T4"
    elif mutation == "auth":
        record["owner_authorization"] = {**auth, "sha256": "b" * 64}
    (run / "run_contract.json").write_text(json.dumps(record))
    real = fake_contract(tmp_path, bound, launch)
    if mutation == "none":
        result = launch.inspect_s2_run_weights(real, str(run / "weights/best.pt"), auth, CHECKOUT)
        assert result["attestation"]["pilot_contract_sha256"] == launch.PILOT_CONTRACT_SHA256
    else:
        with pytest.raises(RuntimeError):
            launch.inspect_s2_run_weights(real, str(run / "weights/best.pt"), auth, CHECKOUT)
