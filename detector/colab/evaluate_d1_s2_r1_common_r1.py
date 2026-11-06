"""Prepared validation-R3 evaluator for a completed, independently QA-passed D1-S2-R1 run.

Only the candidate identity differs from the QA-passed A2 common evaluator. This file is
source preparation, not permission to infer. Use it only after S2 result QA and the committed
three-seed threshold-selection contract; never on the sealed test.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import evaluate_d1_a2_r1_common_r1 as predecessor

from m1 import contract
from m1 import resumable_train_s2_r1 as s2train

PACKAGE = "D1-S2-R1-COMMON-VALIDATION-R1"
EXPERIMENT = "D1-S2-R1"
EPOCHS = 100
RUN_PATTERN = r"D1_yolo11s_wp33_afa03d4b_20261019_[0-9]{8}T[0-9]{6}_s2_r1"
PREDECESSOR_SHA256 = "c08f5de603037aa3289dfc91d44bb2d67b3a29f7e94eba5f2967815fb0c08317"
S2_LAUNCHER_SHA256 = "f69b071a42e2193948cd2406528cd646d3046e18ffdd1c0e9930103b13ebada1"
S2_TRAINER_SHA256 = "a7025fd0ebaad0e0cdee5113d7f72c5f17606485e5a05da7b5cb2f99b6b98936"
A3_EVALUATOR_SHA256 = "5d8e49bfafc1343ff1cc3fd4064410914ab6e75c23a1108240b09c36dc3ecca6"
COMMON_SHA256 = "8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42"
METRICS_SHA256 = "d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f"
VERIFIER_SHA256 = "b60e829104f644248912acddf4397fe07ff647e709feefef6dd0443c393e5753"
R6_SHA256 = "71a9f4a9f8efaa81f657dd414ab8a7d3354ae13a7fcd024e04b42ef2ccce8a35"
LOCK_CONTRACT_SHA256 = "726932dbcd32842658477c9d36f4dc7c240d412d92119e76e5b3536a4d278f0f"
LOCK_QA_SHA256 = "e85c1ac36973f82b85bc28842afd01aa0c286b83db388f065f72115cac11d4a6"
BUNDLE_SHA256 = predecessor.BUNDLE_SHA256
common = predecessor.common
a3eval = predecessor.a3eval


def _load_launcher() -> Any:
    path = Path(__file__).with_name("run_d1_colab_s2_r1.py")
    spec = importlib.util.spec_from_file_location("d1_s2_common_eval_launcher", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load S2 launcher")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


launcher = _load_launcher()


def sha256(path: Path) -> str:
    return a3eval.sha256_file(path)


def verify_predecessors() -> dict[str, str]:
    paths = {
        "a2_evaluator": (Path(predecessor.__file__), PREDECESSOR_SHA256),
        "a3_evaluator": (Path(a3eval.__file__), A3_EVALUATOR_SHA256),
        "s2_launcher": (Path(launcher.__file__), S2_LAUNCHER_SHA256),
        "s2_trainer": (Path(s2train.__file__), S2_TRAINER_SHA256),
        "common_scorer": (Path(common.__file__), COMMON_SHA256),
        "metrics": (Path(contract.__file__).with_name("metrics.py"), METRICS_SHA256),
        "bundle_verifier": (Path(a3eval.verify_package.__code__.co_filename), VERIFIER_SHA256),
        "archive_verifier": (Path(launcher.r6.__file__), R6_SHA256),
    }
    for label, (path, expected) in paths.items():
        if path.is_symlink() or not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"pinned predecessor differs: {label}")
    if launcher.EXPERIMENT != EXPERIMENT or s2train.EXPERIMENT != EXPERIMENT:
        raise RuntimeError("S2 predecessor experiment differs")
    if launcher.FROZEN != s2train.FROZEN:
        raise RuntimeError("S2 frozen launcher/trainer settings differ")
    return {label: expected for label, (_, expected) in paths.items()}


def verify_execution_prerequisites(args: argparse.Namespace) -> dict[str, str]:
    """Require committed contract b and a separate, hash-pinned S2 result-QA PASS."""
    root = contract.REPO_ROOT
    for relative, expected in (
        ("docs/review/d1_threshold_lock_r1_contract.md", LOCK_CONTRACT_SHA256),
        ("docs/review/d1_threshold_lock_r1_contract_independent_qa_record.md", LOCK_QA_SHA256),
    ):
        path = root / relative
        if path.is_symlink() or not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"committed threshold-selection contract differs: {relative}")
        committed = subprocess.run(
            ["git", "show", f"HEAD:{relative}"], cwd=root, capture_output=True, check=False
        )
        if committed.returncode != 0 or hashlib.sha256(committed.stdout).hexdigest() != expected:
            raise RuntimeError(f"threshold-selection contract is not committed: {relative}")
    qa_path = args.s2_result_qa_record
    if (
        qa_path is None
        or qa_path.is_absolute()
        or qa_path.parent.as_posix() != "docs/review"
        or qa_path.suffix != ".md"
        or "test" in qa_path.name.lower()
        or re.fullmatch(r"[0-9a-f]{64}", args.s2_result_qa_sha256 or "") is None
    ):
        raise RuntimeError("S2 result QA record path/hash is invalid")
    target = root / qa_path
    if target.is_symlink() or not target.is_file() or sha256(target) != args.s2_result_qa_sha256:
        raise RuntimeError("S2 result QA record hash differs")
    text = target.read_text(encoding="utf-8")
    verdicts = [line for line in text.splitlines() if line.startswith("Verdict:")]
    if (
        len(verdicts) != 1
        or re.fullmatch(r"Verdict: PASS(?:\s+.*)?", verdicts[0]) is None
        or EXPERIMENT not in text
        or args.archive_sha256 not in text
        or args.manifest_sha256 not in text
        or "sealed_test_accessed=false" not in text
    ):
        raise RuntimeError("S2 result QA does not bind the completed sealed-test-free archive")
    return {
        "contract_b": LOCK_CONTRACT_SHA256,
        "contract_b_qa": LOCK_QA_SHA256,
        "s2_result_qa": args.s2_result_qa_sha256,
    }


def verify_run_contract(
    record: Any, run: str, checkout: str, authorization_sha256: str
) -> dict[str, Any]:
    """Offline counterpart of the S2 launcher's inspect_s2_run_weights attestation."""
    launcher._exact_keys(record, launcher.S2_RUN_CONTRACT_KEYS, "S2 run contract")
    authorization = record["owner_authorization"]
    launcher._exact_keys(authorization, {"path", "sha256"}, "S2 owner authorization")
    if authorization["sha256"] != authorization_sha256:
        raise RuntimeError("S2 owner authorization hash differs")
    if (
        record["experiment"] != EXPERIMENT
        or record["run"] != run
        or record["seed"] != 20261019
        or record["status"] != "TRAINED"
        or record["pilot_run"] != launcher.PILOT_RUN
        or record["single_change"] != "seed"
        or record["pilot_contract_sha256"] != launcher.PILOT_CONTRACT_SHA256
        or record["sealed_test_accessed"] is not False
    ):
        raise RuntimeError("S2 run contract identity differs")
    run_data = record["contract"]
    launcher._exact_keys(
        run_data,
        {"export_manifest_sha256", "class_map_sha256", "split_stem_sha256", "data_yaml"},
        "S2 governed data",
    )
    if (
        run_data["export_manifest_sha256"] != launcher.PILOT_EXPORT_SHA256
        or run_data["class_map_sha256"] != predecessor.GOVERNED_DATA_CONTRACT["class_map_sha256"]
        or run_data["split_stem_sha256"] != predecessor.GOVERNED_DATA_CONTRACT["split_stem_sha256"]
    ):
        raise RuntimeError("S2 governed export differs from pilot")
    data_yaml = Path(run_data["data_yaml"])
    if (
        not data_yaml.is_absolute()
        or ".." in data_yaml.parts
        or data_yaml.parts[-4:] != ("data", "processed", "m1_yolo", "data.yaml")
    ):
        raise RuntimeError("S2 governed data.yaml path differs from pilot")
    artifacts = record["artifacts"]
    launcher._exact_keys(artifacts, {"weights"}, "S2 artifacts")
    weights = artifacts["weights"]
    launcher._exact_keys(weights, {"best.pt", "last.pt"}, "S2 weights")
    roots: set[Path] = set()
    for name, item in weights.items():
        launcher._exact_keys(item, {"path", "sha256"}, f"S2 {name}")
        path = Path(item["path"])
        if (
            path.name != name
            or path.parent.name != "weights"
            or not predecessor._is_sha256(item["sha256"])
        ):
            raise RuntimeError(f"S2 weight binding differs: {name}")
        roots.add(path.parent.parent)
    if len(roots) != 1:
        raise RuntimeError("S2 weights do not share a run directory")
    run_dir = roots.pop()
    if (
        run_dir.name != run
        or run_dir.parent.as_posix().split("/")[-2:] != ["results", "experiments"]
        or record["train_args"] != launcher.expected_train_args(run_dir, run_data["data_yaml"])
    ):
        raise RuntimeError("S2 train args differ from pilot except seed/run identity")
    model = record["model"]
    launcher._exact_keys(model, {"path", "sha256", "origin"}, "S2 pretrained model")
    if model["sha256"] != contract.PRETRAINED_WEIGHTS_SHA256:
        raise RuntimeError("S2 pretrained model differs")
    if record["d05_gates"] != contract.GATES:
        raise RuntimeError("S2 D-05 gates differ")
    environment = record["environment"]
    contract.validate_environment_record(environment, "S2 environment", require_clean=True)
    if (
        environment["runtime_backend"] != "cuda"
        or environment["gpu_name"] != "NVIDIA L4"
        or environment["git_commit"] != checkout
        or environment["git_dirty_files"] != 0
    ):
        raise RuntimeError("S2 clean L4 checkout differs")
    return {
        "experiment": EXPERIMENT,
        "run": run,
        "seed": 20261019,
        "run_contract_sha256": None,
        "approved_pretrained_sha256": contract.PRETRAINED_WEIGHTS_SHA256,
        "export_manifest_sha256": run_data["export_manifest_sha256"],
        "detector_lock_sha256": contract.DETECTOR_LOCK_SHA256,
        "owner_authorization_sha256": authorization_sha256,
        "pilot_contract_sha256": launcher.PILOT_CONTRACT_SHA256,
        "weights": {name: weights[name]["sha256"] for name in sorted(weights)},
    }


def verify_candidate(args: argparse.Namespace) -> dict[str, Any]:
    manifest = predecessor.verify_candidate_pins(args)
    verified = launcher.r6.verify_r4_result_archive(args.archive, args.manifest)
    run = verified["run"]
    if re.fullmatch(RUN_PATTERN, run) is None:
        raise RuntimeError("S2 result run name differs")
    members = predecessor.read_small_members(args.archive, run)
    record_bytes = members["run_contract.json"]
    record = predecessor._strict_json_bytes(record_bytes, "S2 run contract")
    attestation = verify_run_contract(
        record, run, args.expected_checkout, args.owner_authorization_sha256
    )
    attestation["run_contract_sha256"] = hashlib.sha256(record_bytes).hexdigest()
    by_path = {item["path"]: item["sha256"] for item in verified["files"]}
    for name, digest in attestation["weights"].items():
        if by_path.get(f"{run}/weights/{name}") != digest:
            raise RuntimeError(f"S2 archived weight differs: {name}")
    if contract.canonical_sha256(attestation) != verified["run_attestation_sha256"]:
        raise RuntimeError("S2 run attestation differs")
    execution = predecessor._strict_json_bytes(members["colab_execution.json"], "S2 execution")
    _verify_execution(execution, record, run, args.expected_checkout)
    predecessor.verify_training_log(members["results.csv"], members["args.yaml"])
    s2train.verify_owner_authorization(
        args.repo_root,
        Path(record["owner_authorization"]["path"]),
        record["owner_authorization"]["sha256"],
    )
    _verify_live(args.state, execution, run)
    return {
        "run": run,
        "manifest": manifest,
        "best_sha256": attestation["weights"]["best.pt"],
        "attestation_sha256": verified["run_attestation_sha256"],
        "run_contract_sha256": attestation["run_contract_sha256"],
        "training_outcome": execution["training_outcome"]["status"],
        "owner_authorization": record["owner_authorization"],
    }


def _verify_execution(execution: Any, record: dict, run: str, checkout: str) -> None:
    if not isinstance(execution, dict):
        raise RuntimeError("S2 execution is not an object")
    if (
        execution.get("experiment") != EXPERIMENT
        or execution.get("package") != launcher.PACKAGE
        or execution.get("status") != "SUCCEEDED"
        or execution.get("error") is not None
        or execution.get("epochs") != EPOCHS
        or execution.get("seed") != 20261019
        or execution.get("tag") != launcher.FROZEN["tag"]
        or execution.get("sealed_test_accessed") is not False
        or execution.get("owner_authorization") != record["owner_authorization"]
        or execution.get("checkout_commit") != checkout
        or execution.get("pilot_contract_sha256") != launcher.PILOT_CONTRACT_SHA256
        or Path(str(execution.get("run_dir"))).name != run
        or not str(execution.get("state_path", "")).endswith(f"/{launcher.EXPECTED_STATE_SUFFIX}")
    ):
        raise RuntimeError("S2 archived execution binding differs")
    predecessor._check_outcome(execution.get("training_outcome"), run, "S2 execution")


def _verify_live(state: Path, execution: dict, run: str) -> None:
    live = contract.strict_json(state / "colab_execution.json")
    latest = contract.strict_json(state / "recovery/latest.json")
    if not isinstance(live, dict) or not isinstance(latest, dict):
        raise RuntimeError("S2 live state is malformed")
    predecessor._check_outcome(live.get("training_outcome"), run, "S2 live execution")
    if (
        live.get("status") != "SUCCEEDED"
        or live.get("experiment") != EXPERIMENT
        or live.get("epochs") != EPOCHS
        or live.get("sealed_test_accessed") is not False
        or live.get("owner_authorization") != execution["owner_authorization"]
        or live.get("run_binding_sha256") != execution["run_binding_sha256"]
        or live.get("checkpoint_binding_sha256") != execution["checkpoint_binding_sha256"]
        or latest.get("generation") != "epoch-0100"
        or latest.get("binding_sha256") != execution["checkpoint_binding_sha256"]
    ):
        raise RuntimeError("S2 live state is not the completed sealed-test-free run")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    for name in ("bundle", "state", "archive", "manifest", "output-dir", "repo-root"):
        result.add_argument(f"--{name}", type=Path, required=name != "repo-root")
    for name in (
        "archive-sha256",
        "manifest-sha256",
        "owner-authorization-sha256",
        "expected-checkout",
    ):
        result.add_argument(f"--{name}", required=True)
    result.add_argument("--s2-result-qa-record", type=Path, required=True)
    result.add_argument("--s2-result-qa-sha256", required=True)
    result.add_argument("--device", default="mps")
    return result


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.output_dir.exists():
        raise RuntimeError("refuse overwriting S2 comparison")
    if not (args.repo_root or contract.REPO_ROOT).resolve() == contract.REPO_ROOT.resolve():
        raise RuntimeError("S2 repository root differs")
    args.repo_root = contract.REPO_ROOT
    prerequisites = verify_execution_prerequisites(args)
    predecessor_hashes = verify_predecessors()
    candidate = verify_candidate(args)
    bundle = args.bundle.resolve(strict=True)
    a3eval.verify_package(bundle, BUNDLE_SHA256)
    common.verify_evaluation_scope(
        bundle, bundle / common.PINNED_YOLO54_PREDICTIONS, common.PINNED_YOLO54_SHA256
    )
    with tempfile.TemporaryDirectory(prefix="d1-s2-val-") as directory:
        weight = predecessor.extract_best(
            args.archive, candidate["manifest"], Path(directory), candidate["best_sha256"]
        )
        frames = a3eval.infer(bundle, weight, args.device)
    if len(frames) != 376 or sum(len(frame.gt_boxes) for frame in frames) != 624:
        raise RuntimeError("S2 validation R3 roster differs")
    pilot = common.load_pinned_baseline(frames, bundle / common.PINNED_YOLO54_PREDICTIONS)
    args.output_dir.mkdir(mode=0o700, parents=True)
    csv_path = args.output_dir / "s2_predictions.csv"
    with csv_path.open("x", newline="", encoding="utf-8") as sink:
        writer = csv.writer(sink)
        writer.writerow(["stem", "class_id", "confidence", "x1", "y1", "x2", "y2"])
        for frame in frames:
            for box, cls, score in zip(
                frame.pred_boxes, frame.pred_classes, frame.pred_scores, strict=True
            ):
                writer.writerow([frame.stem, int(cls), float(score), *map(float, box)])
    result = {
        "package": PACKAGE,
        "experiment": EXPERIMENT,
        "split": "val",
        "frames": 376,
        "gt_boxes": 624,
        "s2_common_method": common.report(frames),
        "pilot_common_method": common.report(pilot),
        "s2_run": candidate["run"],
        "s2_best_weight_sha256": candidate["best_sha256"],
        "s2_result_manifest_sha256": args.manifest_sha256,
        "s2_result_archive_sha256": args.archive_sha256,
        "s2_run_attestation_sha256": candidate["attestation_sha256"],
        "s2_run_contract_sha256": candidate["run_contract_sha256"],
        "s2_training_outcome": candidate["training_outcome"],
        "owner_authorization": candidate["owner_authorization"],
        "checkout_commit": args.expected_checkout,
        "predecessor_sha256": predecessor_hashes,
        "prerequisite_sha256": prerequisites,
        "bundle_manifest_sha256": BUNDLE_SHA256,
        "prediction_csv_sha256": sha256(csv_path),
        "sealed_test_accessed": False,
    }
    with (args.output_dir / "comparison_s2_r1.json").open("x", encoding="utf-8") as sink:
        json.dump(result, sink, indent=2, allow_nan=False)
        sink.write("\n")
    return result


def main(argv: list[str] | None = None) -> None:
    run(parser().parse_args(argv))


if __name__ == "__main__":
    main()
