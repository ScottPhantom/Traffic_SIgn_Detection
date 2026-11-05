#!/usr/bin/env python3
"""D1-A2-R1 Colab launcher: pilot arguments plus the A2 repeat list, through the R6 controls.

Contract: `docs/review/d1_a2_r1_run_contract.md`. Append-only successor that follows
`run_d1_colab_a3_r2.py` (captured predecessor parser, patched command/binding/JSON writers) and
adds three things:

1. An Owner authorization gate before any state is written: the record path (repo-relative,
   `docs/review/`) and its SHA-256 are required, and the record must name this experiment, the
   frozen A2 list and roster hashes and contain the exact authorization line.
2. The expected checkout commit is an argument (the source is not yet committed when this file is
   frozen); the launcher refuses a different `HEAD` and binds the commit into the run binding.
3. An A2-aware result-package validator. The inherited R1 packager calls
   `contract.inspect_run_weights`, whose exact-key schema rejected the extra A3 run-contract fields
   after the D1-A3-R2 run finished (`docs/review/d1_a3_r2_packaging_repair_r1_record.md`). Here the
   packager receives a contract shim whose `inspect_run_weights` validates the A2 run-contract
   schema instead; everything else in the packager is unchanged.

This file never trains by itself: it builds the `m1.resumable_train_a2_r1` command, which repeats
the authorization check and verifies the A2 list before training.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPERIMENT = "D1-A2-R1"
PACKAGE = "D1-A2-R1"
PILOT_RUN = "D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2"
EXPECTED_STATE_SUFFIX = "M1_D1_Colab/runs/d1_a2_seed_20261018_r1"
AUTHORIZATION_DIR = "docs/review"
AUTHORIZATION_LINE = "OWNER_AUTHORIZES_TRAINING: D1-A2-R1"
A2_RULE_ID = "A2_ALL_975_RAW_AND_WP35"
A2_TRAIN_LIST_SHA256 = "90d735d67bde2bf736b5fc8570110561f0184747f3fb25c8f42a3a599d0fdec2"
A2_REPEATED_ROSTER_SHA256 = "0ce6afdc84ffab0db361920c4c7817517353fd8b1b901e51770d2f3f4eb69aa3"
A2_TRAIN_LIST_ENTRIES = 4687
TRAINING_AUTHORIZED = False
FROZEN = {
    "seed": 20261018,
    "epochs": 100,
    "imgsz": 1280,
    "batch": 4,
    "workers": 4,
    "fraction": 1.0,
    "patience": 0,
    "tag": "a2_r1",
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
A2_RUN_CONTRACT_KEYS = BASE_RUN_CONTRACT_KEYS | {
    "pilot_run",
    "single_change",
    "a2_data",
    "owner_authorization",
    "sealed_test_accessed",
}
A2_DATA_KEYS = {
    "rule_id",
    "train_list_sha256",
    "manifest_sha256",
    "repeated_roster_sha256",
    "train_list_entries",
    "repeated_images",
    "repeated_raw_frames",
    "repeated_wp35_images",
    "pilot_data_yaml_sha256",
    "runtime_data_yaml",
    "runtime_data_yaml_sha256",
    "runtime_train_list",
    "runtime_train_list_sha256",
    "data_yaml_changed_keys",
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
    "d1_a2_r1_pinned_checkpoint_r6",
    Path(__file__).with_name("run_d1_colab_checkpoint_r6.py"),
)
r5 = r6.r5
r2 = r5.r2
r1 = r2.r1

# Captured once: during execution r1.parser is replaced by this successor's parser, so calling
# r1.parser from inside parser() would recurse (the D1-A3-R1 live failure).
BASE_PARSER = r1.parser


def parser() -> argparse.ArgumentParser:
    root = BASE_PARSER()
    root.description = __doc__
    root.set_defaults(
        seed=FROZEN["seed"],
        epochs=FROZEN["epochs"],
        imgsz=FROZEN["imgsz"],
        batch=FROZEN["batch"],
        workers=FROZEN["workers"],
        fraction=FROZEN["fraction"],
        patience=FROZEN["patience"],
        tag=FROZEN["tag"],
    )
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
    if args.mode == "fresh" and args.stop_after_epoch not in {None, 1}:
        raise RuntimeError(f"{EXPERIMENT} smoke boundary must be --stop-after-epoch 1")


def validate_owner_authorization(args: argparse.Namespace) -> dict[str, str]:
    relative = Path(args.owner_authorization)
    sha = args.owner_authorization_sha256
    if (
        relative.is_absolute()
        or relative.parent.as_posix() != AUTHORIZATION_DIR
        or not relative.name.endswith(".md")
        or relative.name == "d1_a2_r1_run_contract.md"
    ):
        raise RuntimeError(
            f"Owner authorization must be a repo-relative docs/review record: {relative}"
        )
    if re.fullmatch(r"[0-9a-f]{64}", sha or "") is None:
        raise RuntimeError("Owner authorization SHA-256 must be 64 lowercase hex digits")
    repo_root = args.repo_root.expanduser().absolute()
    current = repo_root
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
        raise RuntimeError(f"Owner authorization record lacks the line {AUTHORIZATION_LINE!r}")
    for required in (EXPERIMENT, A2_TRAIN_LIST_SHA256, A2_REPEATED_ROSTER_SHA256):
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
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
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
            "schema": "d1-a2-r1-run-binding-v1",
            "experiment": EXPERIMENT,
            "package": PACKAGE,
            "owner_authorization_sha256": args.owner_authorization_sha256,
            "checkout_commit": args.expected_checkout,
            "state_path": normalized_state_path(args),
            "bundle_sha256": bundle_sha256,
            "a2_rule_id": A2_RULE_ID,
            "a2_train_list_sha256": A2_TRAIN_LIST_SHA256,
            "a2_repeated_roster_sha256": A2_REPEATED_ROSTER_SHA256,
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
        "m1.resumable_train_a2_r1",
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
    """The pilot's `run_contract.json` train_args with only `data` (and run identity) changed."""
    return {
        "batch": FROZEN["batch"],
        "data": data_yaml,
        "deterministic": True,
        "device": "0",
        "epochs": FROZEN["epochs"],
        "exist_ok": True,
        "fliplr": 0.0,
        "fraction": FROZEN["fraction"],
        "imgsz": FROZEN["imgsz"],
        "name": run_dir.name,
        "patience": FROZEN["patience"],
        "plots": False,
        "pretrained": True,
        "project": str(run_dir.parent),
        "seed": FROZEN["seed"],
        "workers": FROZEN["workers"],
    }


def inspect_a2_run_weights(
    real: Any, weights: str, authorization: dict[str, str], checkout: str
) -> dict[str, Any]:
    """A2 counterpart of `contract.inspect_run_weights` for the A2 run-contract schema."""
    path = Path(weights).expanduser().resolve()
    if (
        not path.is_file()
        or path.parent.name != "weights"
        or path.name not in {"best.pt", "last.pt"}
    ):
        raise RuntimeError("A2 weights must be <run>/weights/best.pt or last.pt")
    run_dir = path.parent.parent
    if not run_dir.is_relative_to(Path(real.RESULTS_DIR).resolve()):
        raise RuntimeError(f"A2 run directory must be under {real.RESULTS_DIR}")
    contract_path = run_dir / "run_contract.json"
    record = real.strict_json(contract_path)
    _exact_keys(record, A2_RUN_CONTRACT_KEYS, "A2 run contract")
    a2 = record["a2_data"]
    _exact_keys(a2, A2_DATA_KEYS, "A2 run contract a2_data")
    if (
        record["experiment"] != EXPERIMENT
        or record["run"] != run_dir.name
        or record["seed"] != FROZEN["seed"]
        or record["status"] != "TRAINED"
        or record["pilot_run"] != PILOT_RUN
        or record["single_change"] != "data"
        or record["sealed_test_accessed"] is not False
        or record["owner_authorization"] != authorization
        or a2["rule_id"] != A2_RULE_ID
        or a2["train_list_sha256"] != A2_TRAIN_LIST_SHA256
        or a2["repeated_roster_sha256"] != A2_REPEATED_ROSTER_SHA256
        or a2["train_list_entries"] != A2_TRAIN_LIST_ENTRIES
        or a2["data_yaml_changed_keys"] != ["train"]
    ):
        raise RuntimeError("A2 run contract invariants differ")
    for key in ("runtime_data_yaml", "runtime_train_list"):
        runtime = Path(a2[key])
        if not runtime.is_file() or runtime.is_symlink():
            raise RuntimeError(f"A2 runtime file is missing or linked: {key}")
        if real.sha256_file(runtime) != a2[f"{key}_sha256"]:
            raise RuntimeError(f"A2 runtime file SHA-256 differs: {key}")
    if record["train_args"] != expected_train_args(run_dir, a2["runtime_data_yaml"]):
        raise RuntimeError("A2 train_args differ from the pilot plus the single data change")
    model = record["model"]
    _exact_keys(model, {"path", "sha256", "origin"}, "A2 run model")
    if model["sha256"] != real.PRETRAINED_WEIGHTS_SHA256:
        raise RuntimeError("A2 run contract does not bind the approved pretrained model")
    bound = real.check_contract()
    run_data = record["contract"]
    _exact_keys(
        run_data,
        {"export_manifest_sha256", "class_map_sha256", "split_stem_sha256", "data_yaml"},
        "A2 run data contract",
    )
    for key in ("export_manifest_sha256", "class_map_sha256", "split_stem_sha256"):
        if run_data[key] != bound[key]:
            raise RuntimeError("A2 run contract data binding differs from the governed contract")
    if record["d05_gates"] != real.GATES:
        raise RuntimeError("A2 run contract D-05 gates differ")
    environment = record["environment"]
    real.validate_environment_record(environment, "A2 run environment", require_clean=True)
    if environment.get("runtime_backend") != "cuda" or environment.get("git_commit") != checkout:
        raise RuntimeError("A2 run environment is not the bound CUDA checkout")
    artifacts = record["artifacts"]
    _exact_keys(artifacts, {"weights"}, "A2 run artifacts")
    weight_records = artifacts["weights"]
    _exact_keys(weight_records, {"best.pt", "last.pt"}, "A2 run weights")
    for name in sorted(weight_records):
        item = weight_records[name]
        _exact_keys(item, {"path", "sha256"}, f"A2 weight {name}")
        canonical = run_dir / "weights" / name
        if (
            Path(item["path"]).name != name
            or not canonical.is_file()
            or canonical.is_symlink()
            or real.sha256_file(canonical) != item["sha256"]
        ):
            raise RuntimeError(f"A2 weight binding differs: {name}")
    attestation = {
        "experiment": EXPERIMENT,
        "run": run_dir.name,
        "seed": FROZEN["seed"],
        "run_contract_sha256": real.sha256_file(contract_path),
        "approved_pretrained_sha256": real.PRETRAINED_WEIGHTS_SHA256,
        "export_manifest_sha256": bound["export_manifest_sha256"],
        "detector_lock_sha256": real.DETECTOR_LOCK_SHA256,
        "owner_authorization_sha256": authorization["sha256"],
        "a2_train_list_sha256": A2_TRAIN_LIST_SHA256,
        "a2_repeated_roster_sha256": A2_REPEATED_ROSTER_SHA256,
        "weights": {name: weight_records[name]["sha256"] for name in sorted(weight_records)},
    }
    return {
        "path": str(path),
        "sha256": real.sha256_file(path),
        "run_dir": str(run_dir),
        "run_contract": str(contract_path),
        "seed": FROZEN["seed"],
        "run": run_dir.name,
        "attestation": attestation,
        "run_attestation_sha256": real.canonical_sha256(attestation),
    }


class A2ContractShim:
    """Forwards to the real detector contract except `inspect_run_weights`."""

    def __init__(self, real: Any, authorization: dict[str, str], checkout: str) -> None:
        self._real = real
        self._authorization = authorization
        self._checkout = checkout

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)

    def inspect_run_weights(self, weights: str) -> dict[str, Any]:
        return inspect_a2_run_weights(self._real, weights, self._authorization, self._checkout)


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

    def write_a2_json(path: Path, payload: dict[str, Any]) -> None:
        if path.name == "colab_execution.json":
            payload = {
                **payload,
                "experiment": EXPERIMENT,
                "package": PACKAGE,
                "owner_authorization": authorization,
                "a2_train_list_sha256": A2_TRAIN_LIST_SHA256,
                "a2_repeated_roster_sha256": A2_REPEATED_ROSTER_SHA256,
                "checkout_commit": checkout,
                "state_path": state_path,
            }
        original_write_json(path, payload)

    def load_a2_contract(repo_root: Path) -> A2ContractShim:
        return A2ContractShim(original_loader(repo_root), authorization, checkout)

    r1.parser = parser
    r1.build_train_command = build_train_command
    r2.run_binding = run_binding
    r1.base.write_json = write_a2_json
    r1.base.load_detector_contract = load_a2_contract
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
