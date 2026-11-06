#!/usr/bin/env python3
"""D1-S2-R1 Colab launcher through the unchanged R6 checkpoint/resume runner."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPERIMENT = "D1-S2-R1"
PACKAGE = EXPERIMENT
PILOT_RUN = "D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2"
PILOT_CONTRACT_SHA256 = "9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88"
PILOT_EXPORT_SHA256 = "8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71"
EXPECTED_STATE_SUFFIX = "M1_D1_Colab/runs/d1_s2_seed_20261019_r1"
AUTHORIZATION_DIR = "docs/review"
AUTHORIZATION_LINE = "OWNER_AUTHORIZES_TRAINING: D1-S2-R1"
FROZEN = {
    "seed": 20261019,
    "epochs": 100,
    "imgsz": 1280,
    "batch": 4,
    "workers": 4,
    "fraction": 1.0,
    "patience": 0,
    "tag": "s2_r1",
}
BASE_RUN_CONTRACT_KEYS = {
    "experiment",
    "run",
    "seed",
    "model",
    "train_args",
    "contract",
    "environment",
    "d05_gates",
    "status",
    "artifacts",
}
S2_RUN_CONTRACT_KEYS = BASE_RUN_CONTRACT_KEYS | {
    "pilot_run",
    "single_change",
    "pilot_contract_sha256",
    "owner_authorization",
    "sealed_test_accessed",
}


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned predecessor: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


r6 = _load(
    "d1_s2_r1_pinned_checkpoint_r6", Path(__file__).with_name("run_d1_colab_checkpoint_r6.py")
)
r5 = r6.r5
r2 = r5.r2
r1 = r2.r1
BASE_PARSER = r1.parser  # Capture before patching r1.parser, to avoid recursion.


def parser() -> argparse.ArgumentParser:
    root = BASE_PARSER()
    root.description = __doc__
    root.set_defaults(**FROZEN)
    root.add_argument("--owner-authorization", required=True)
    root.add_argument("--owner-authorization-sha256", required=True)
    root.add_argument("--expected-checkout", required=True)
    return root


def validate_frozen(args: argparse.Namespace) -> None:
    observed = {key: getattr(args, key) for key in FROZEN}
    if observed != FROZEN:
        raise RuntimeError(f"{EXPERIMENT} frozen arguments differ: {observed!r}")
    if str(args.device) != "0":
        raise RuntimeError(f"{EXPERIMENT} requires CUDA device 0")
    if args.mode == "resume" and args.stop_after_epoch is not None:
        raise RuntimeError(f"{EXPERIMENT} resume forbids --stop-after-epoch")
    if args.mode == "fresh" and args.stop_after_epoch != 1:
        raise RuntimeError(f"{EXPERIMENT} fresh smoke requires --stop-after-epoch 1")


def validate_owner_authorization(args: argparse.Namespace) -> dict[str, str]:
    relative = Path(args.owner_authorization)
    sha = args.owner_authorization_sha256
    if (
        relative.is_absolute()
        or relative.parent.as_posix() != AUTHORIZATION_DIR
        or relative.suffix != ".md"
        or "test" in relative.name.lower()
        or relative.name == "d1_s2_r1_run_contract.md"
    ):
        raise RuntimeError("Owner authorization must be a repo-relative docs/review record")
    if re.fullmatch(r"[0-9a-f]{64}", sha or "") is None:
        raise RuntimeError("Owner authorization SHA-256 must be 64 lowercase hex digits")
    current = args.repo_root.expanduser().absolute()
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeError("Owner authorization path contains a symlink")
    if not current.is_file():
        raise RuntimeError(f"Owner authorization record is missing: {relative}")
    data = current.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha:
        raise RuntimeError("Owner authorization record SHA-256 differs")
    text = data.decode("utf-8")
    if AUTHORIZATION_LINE not in {line.strip() for line in text.splitlines()}:
        raise RuntimeError("Owner authorization record lacks the exact authorization line")
    for required in (EXPERIMENT, PILOT_CONTRACT_SHA256, str(FROZEN["seed"])):
        if required not in text:
            raise RuntimeError(f"Owner authorization record does not name {required}")
    return {"path": relative.as_posix(), "sha256": sha}


def normalized_state_path(args: argparse.Namespace) -> str:
    state = args.state_dir.expanduser().absolute()
    if not state.as_posix().endswith(f"/{EXPECTED_STATE_SUFFIX}"):
        raise RuntimeError(f"{PACKAGE} requires Drive state suffix {EXPECTED_STATE_SUFFIX}")
    return str(state)


def observed_checkout(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def validate_launch_context(args: argparse.Namespace) -> tuple[str, str]:
    if re.fullmatch(r"[0-9a-f]{40}", args.expected_checkout) is None:
        raise RuntimeError("--expected-checkout must be a full 40-hex commit SHA")
    state_path = normalized_state_path(args)
    checkout = observed_checkout(args.repo_root)
    if checkout != args.expected_checkout:
        raise RuntimeError(
            f"{PACKAGE} checkout differs: expected {args.expected_checkout}, got {checkout}"
        )
    return state_path, checkout


def run_binding(args: argparse.Namespace, bundle_sha256: str) -> str:
    return r2.canonical_sha256(
        {
            "schema": "d1-s2-r1-run-binding-v1",
            "experiment": EXPERIMENT,
            "package": PACKAGE,
            "owner_authorization_sha256": args.owner_authorization_sha256,
            "checkout_commit": args.expected_checkout,
            "state_path": normalized_state_path(args),
            "bundle_sha256": bundle_sha256,
            "pilot_contract_sha256": PILOT_CONTRACT_SHA256,
            "seed": args.seed,
            "epochs": args.epochs,
            "imgsz": args.imgsz,
            "batch": args.batch,
            "device": str(args.device),
            "workers": args.workers,
            "fraction": args.fraction,
            "patience": args.patience,
            "tag": args.tag,
        }
    )


def build_train_command(args: argparse.Namespace, model: Path, state_dir: Path) -> list[str]:
    command = [
        "uv",
        "run",
        "python",
        "-m",
        "m1.resumable_train_s2_r1",
        "--model",
        str(model),
        "--checkpoint-dir",
        str(state_dir / "recovery"),
        "--seed",
        str(args.seed),
        "--epochs",
        str(args.epochs),
        "--imgsz",
        str(args.imgsz),
        "--batch",
        str(args.batch),
        "--device",
        str(args.device),
        "--workers",
        str(args.workers),
        "--fraction",
        str(args.fraction),
        "--patience",
        str(args.patience),
        "--tag",
        args.tag,
        "--owner-authorization",
        str(args.owner_authorization),
        "--owner-authorization-sha256",
        args.owner_authorization_sha256,
    ]
    if args.mode == "resume":
        command.append("--resume")
    if args.stop_after_epoch is not None:
        command.extend(("--stop-after-epoch", str(args.stop_after_epoch)))
    return command


def _exact_keys(value: Any, expected: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise RuntimeError(f"{label} schema differs: expected exactly {sorted(expected)}")


def expected_train_args(run_dir: Path, data_yaml: str) -> dict[str, Any]:
    return {
        "batch": 4,
        "data": data_yaml,
        "deterministic": True,
        "device": "0",
        "epochs": 100,
        "exist_ok": True,
        "fliplr": 0.0,
        "fraction": 1.0,
        "imgsz": 1280,
        "name": run_dir.name,
        "patience": 0,
        "plots": False,
        "pretrained": True,
        "project": str(run_dir.parent),
        "seed": 20261019,
        "workers": 4,
    }


def inspect_s2_run_weights(
    real: Any, weights: str, authorization: dict[str, str], checkout: str
) -> dict[str, Any]:
    path = Path(weights).expanduser().resolve()
    if (
        not path.is_file()
        or path.parent.name != "weights"
        or path.name not in {"best.pt", "last.pt"}
    ):
        raise RuntimeError("S2 weights must be <run>/weights/best.pt or last.pt")
    run_dir = path.parent.parent
    if not run_dir.is_relative_to(Path(real.RESULTS_DIR).resolve()):
        raise RuntimeError(f"S2 run directory must be under {real.RESULTS_DIR}")
    contract_path = run_dir / "run_contract.json"
    record = real.strict_json(contract_path)
    _exact_keys(record, S2_RUN_CONTRACT_KEYS, "S2 run contract")
    if (
        record["experiment"] != EXPERIMENT
        or record["run"] != run_dir.name
        or record["seed"] != 20261019
        or record["status"] != "TRAINED"
        or record["pilot_run"] != PILOT_RUN
        or record["single_change"] != "seed"
        or record["pilot_contract_sha256"] != PILOT_CONTRACT_SHA256
        or record["sealed_test_accessed"] is not False
        or record["owner_authorization"] != authorization
    ):
        raise RuntimeError("S2 run contract invariants differ")
    bound = real.check_contract()
    if bound["export_manifest_sha256"] != PILOT_EXPORT_SHA256:
        raise RuntimeError("S2 export binding differs from the pilot")
    if record["train_args"] != expected_train_args(run_dir, bound["data_yaml"]):
        raise RuntimeError("S2 train_args differ from pilot except seed/run identity")
    model = record["model"]
    _exact_keys(model, {"path", "sha256", "origin"}, "S2 run model")
    if model["sha256"] != real.PRETRAINED_WEIGHTS_SHA256:
        raise RuntimeError("S2 pretrained weight differs")
    run_data = record["contract"]
    _exact_keys(
        run_data,
        {"export_manifest_sha256", "class_map_sha256", "split_stem_sha256", "data_yaml"},
        "S2 run data contract",
    )
    if run_data != bound:
        raise RuntimeError("S2 run data binding differs from the governed contract")
    if record["d05_gates"] != real.GATES:
        raise RuntimeError("S2 D-05 gates differ")
    environment = record["environment"]
    real.validate_environment_record(environment, "S2 run environment", require_clean=True)
    if (
        environment.get("runtime_backend") != "cuda"
        or environment.get("gpu_name") != "NVIDIA L4"
        or environment.get("git_commit") != checkout
    ):
        raise RuntimeError("S2 environment is not the bound clean L4 checkout")
    artifacts = record["artifacts"]
    _exact_keys(artifacts, {"weights"}, "S2 run artifacts")
    weight_records = artifacts["weights"]
    _exact_keys(weight_records, {"best.pt", "last.pt"}, "S2 run weights")
    for name, item in weight_records.items():
        _exact_keys(item, {"path", "sha256"}, f"S2 weight {name}")
        canonical = run_dir / "weights" / name
        if (
            Path(item["path"]) != canonical
            or not canonical.is_file()
            or canonical.is_symlink()
            or real.sha256_file(canonical) != item["sha256"]
        ):
            raise RuntimeError(f"S2 weight binding differs: {name}")
    attestation = {
        "experiment": EXPERIMENT,
        "run": run_dir.name,
        "seed": 20261019,
        "run_contract_sha256": real.sha256_file(contract_path),
        "approved_pretrained_sha256": real.PRETRAINED_WEIGHTS_SHA256,
        "export_manifest_sha256": bound["export_manifest_sha256"],
        "detector_lock_sha256": real.DETECTOR_LOCK_SHA256,
        "owner_authorization_sha256": authorization["sha256"],
        "pilot_contract_sha256": PILOT_CONTRACT_SHA256,
        "weights": {name: weight_records[name]["sha256"] for name in sorted(weight_records)},
    }
    return {
        "path": str(path),
        "sha256": real.sha256_file(path),
        "run_dir": str(run_dir),
        "run_contract": str(contract_path),
        "seed": 20261019,
        "run": run_dir.name,
        "attestation": attestation,
        "run_attestation_sha256": real.canonical_sha256(attestation),
    }


class S2ContractShim:
    def __init__(self, real: Any, authorization: dict[str, str], checkout: str) -> None:
        self._real = real
        self._authorization = authorization
        self._checkout = checkout

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)

    def inspect_run_weights(self, weights: str) -> dict[str, Any]:
        return inspect_s2_run_weights(self._real, weights, self._authorization, self._checkout)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        validate_frozen(args)
        authorization = validate_owner_authorization(args)
        state_path, checkout = validate_launch_context(args)
    except (OSError, RuntimeError, UnicodeDecodeError, subprocess.CalledProcessError) as error:
        print(r1.json.dumps({"status": "FAILED", "error": str(error)}))
        return 1
    original_parser = r1.parser
    original_command = r1.build_train_command
    original_binding = r2.run_binding
    original_write_json = r1.base.write_json
    original_loader = r1.base.load_detector_contract

    def write_s2_json(path: Path, payload: dict[str, Any]) -> None:
        if path.name == "colab_execution.json":
            payload = {
                **payload,
                "experiment": EXPERIMENT,
                "package": PACKAGE,
                "owner_authorization": authorization,
                "pilot_contract_sha256": PILOT_CONTRACT_SHA256,
                "checkout_commit": checkout,
                "state_path": state_path,
            }
        original_write_json(path, payload)

    def load_s2_contract(repo_root: Path) -> S2ContractShim:
        return S2ContractShim(original_loader(repo_root), authorization, checkout)

    r1.parser = parser
    r1.build_train_command = build_train_command
    r2.run_binding = run_binding
    r1.base.write_json = write_s2_json
    r1.base.load_detector_contract = load_s2_contract
    try:
        return r6.main(argv)
    finally:
        r1.parser = original_parser
        r1.build_train_command = original_command
        r2.run_binding = original_binding
        r1.base.write_json = original_write_json
        r1.base.load_detector_contract = original_loader


if __name__ == "__main__":
    raise SystemExit(main())
