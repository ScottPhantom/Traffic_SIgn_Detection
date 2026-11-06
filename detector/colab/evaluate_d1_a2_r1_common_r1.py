"""Validation-only common-score check of the completed D1-A2-R1 YOLO11s-54 candidate.

Append-only successor of ``evaluate_d1_a3_r2_common_r1.py`` (SHA-256 ``5d8e49bf…``). Only the
candidate side changes: the A2 result archive, its manifest and ``best.pt`` replace the A3 pins.
The pilot side, the corrected train/val-only bundle ``8e6ffe77…``, the 376-frame/624-box roster,
inference (``conf=0.001``, NMS IoU ``0.70``, ``imgsz=1280``), the Ultralytics IoU matching/AP and
the ``m1`` D-05 operating points are the predecessor's own objects, reused by import.

The A2 archive hashes are unknown until the run finishes, so the candidate pins are required CLI
inputs. They are verified before anything else; the archive is then accepted only after the
inherited R1/R4/R6 result-archive verifier, the offline recomputation of the A2 run attestation
(``run_d1_colab_a2_r1.inspect_a2_run_weights`` formula) and the A2 execution, training-log, Owner
authorization and live-state checks all pass. There is no training or sealed-test path.

Contract: ``docs/review/d1_a2_r1_run_contract.md`` §4.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import re
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

import evaluate_d1_a3_r2_common_r1 as a3eval
import yaml

from m1 import contract
from m1 import resumable_train_a2_r1 as a2t

PACKAGE = "D1-A2-R1-COMMON-VALIDATION-R1"
EXPERIMENT = "D1-A2-R1"
COLAB_DIR = Path(a3eval.__file__).resolve().parent

# ---- predecessors reused unchanged (verified again at run time) ---------------------------------
A3_EVALUATOR_SHA256 = "5d8e49bfafc1343ff1cc3fd4064410914ab6e75c23a1108240b09c36dc3ecca6"
A2_LAUNCHER = COLAB_DIR / "run_d1_colab_a2_r1.py"
A2_LAUNCHER_SHA256 = "a6bb6e684701b5a95bd03b71bac777693ec08f1ccb853c98edb2cefdcec2d6de"
A2_TRAINER_SHA256 = "c3823eefb9777912fc76302a642427a64869c9097274fc4d5841966c07d42ace"

# ---- pilot side: identical to the A3 evaluator --------------------------------------------------
common = a3eval.common
BUNDLE_SHA256 = a3eval.BUNDLE_SHA256
FRAMES, GT_BOXES = 376, 624

# ---- candidate side: frozen A2 identity (contract §2, §2.1, §6) ---------------------------------
EPOCHS = 100
TERMINAL_OUTCOMES = {"COMPLETED", "COMPLETED_FROM_FINAL_CHECKPOINT"}
EARLY_STOPPED = "COMPLETED_EARLY_STOPPED"
RUN_PATTERN = r"D1_yolo11s_wp33_afa03d4b_20261018_[0-9]{8}T[0-9]{6}_a2_r1"
REPEATED = {"repeated_images": 975, "repeated_raw_frames": 339, "repeated_wp35_images": 636}
GPU_NAME = "NVIDIA L4"
# The governed M1 export binding, equal to the pilot run_contract.json (`9f8fc94c…`) `contract`.
GOVERNED_DATA_CONTRACT = {
    "export_manifest_sha256": "8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71",
    "class_map_sha256": "7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242",
    "split_stem_sha256": {
        "test": "afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc",
        "train": "6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372",
        "val": "ae3f3509319fbb301012e9fbeb7431caacfcd4035c9d2f9167f24e3ed2b8f593",
    },
}
SMALL_MEMBERS = ("run_contract.json", "results.csv", "args.yaml")
EXECUTION_MEMBER = "colab_logs/colab_execution.json"
MAX_SMALL_MEMBER = 16 * 1024 * 1024


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned predecessor: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


launcher = _load("d1_a2_r1_common_eval_pinned_launcher", A2_LAUNCHER)
if launcher.EXPERIMENT != EXPERIMENT or launcher.FROZEN["epochs"] != EPOCHS:
    raise RuntimeError("pinned A2 launcher identity differs")


def sha256_file(path: Path) -> str:
    return a3eval.sha256_file(path)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _strict_json_bytes(payload: bytes, label: str) -> Any:
    try:
        return launcher.r2.strict_json_bytes(payload)
    except (ValueError, UnicodeDecodeError) as error:
        raise RuntimeError(f"{label} is not strict JSON") from error


def verify_predecessors() -> dict[str, str]:
    """The reused predecessor files must be the QA-passed bytes."""
    pins = {
        "a3_common_evaluator": (Path(a3eval.__file__), A3_EVALUATOR_SHA256),
        "a2_launcher": (A2_LAUNCHER, A2_LAUNCHER_SHA256),
        "a2_trainer": (Path(a2t.__file__), A2_TRAINER_SHA256),
    }
    for label, (path, expected) in pins.items():
        if path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned predecessor differs: {label}")
    return {label: expected for label, (_, expected) in pins.items()}


# ------------------------------------------------------------------------------- archive binding


def verify_candidate_pins(args: argparse.Namespace) -> dict[str, Any]:
    """Hash checks on the CLI-pinned candidate inputs; nothing else is read before these pass."""
    for label in ("archive_sha256", "manifest_sha256", "owner_authorization_sha256"):
        if not _is_sha256(getattr(args, label)):
            raise RuntimeError(f"--{label.replace('_', '-')} must be 64 lowercase hex digits")
    if re.fullmatch(r"[0-9a-f]{40}", args.expected_checkout or "") is None:
        raise RuntimeError("--expected-checkout must be a full 40-hex commit SHA")
    for path in (args.archive, args.manifest):
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"A2 result input is missing or linked: {path}")
    if sha256_file(args.manifest) != args.manifest_sha256:
        raise RuntimeError("A2 result manifest SHA-256 differs")
    if sha256_file(args.archive) != args.archive_sha256:
        raise RuntimeError("A2 result archive SHA-256 differs")
    manifest = _strict_json_bytes(args.manifest.read_bytes(), "A2 result manifest")
    if not isinstance(manifest, dict) or manifest.get("archive_sha256") != args.archive_sha256:
        raise RuntimeError("A2 result manifest does not bind the pinned archive")
    return manifest


def verify_archive(archive: Path, manifest_path: Path) -> dict[str, Any]:
    """Inherited R1 eight-file roster + R4/R6 two-runtime evidence verifier, unchanged."""
    verified = launcher.r6.verify_r4_result_archive(archive, manifest_path)
    run = verified["run"]
    if re.fullmatch(RUN_PATTERN, run) is None:
        raise RuntimeError(f"A2 result run identity differs: {run}")
    return verified


def read_small_members(archive: Path, run: str) -> dict[str, bytes]:
    names = {f"{run}/{name}": name for name in SMALL_MEMBERS}
    names[EXECUTION_MEMBER] = "colab_execution.json"
    found: dict[str, bytes] = {}
    with tarfile.open(archive, "r:gz") as source:
        for member in source.getmembers():
            if member.name not in names:
                continue
            if not member.isreg() or member.size > MAX_SMALL_MEMBER:
                raise RuntimeError(f"unsafe A2 archive member: {member.name}")
            stream = source.extractfile(member)
            if stream is None:
                raise RuntimeError(f"unreadable A2 archive member: {member.name}")
            found[names[member.name]] = stream.read()
    if set(found) != set(names.values()):
        raise RuntimeError("A2 archive lacks a required member")
    return found


# --------------------------------------------------------------------------- run attestation


def verify_run_contract(
    record: Any, run: str, expected_checkout: str, authorization_sha256: str
) -> dict[str, Any]:
    """Offline counterpart of ``inspect_a2_run_weights``: same schema, same attestation.

    The Colab-only runtime paths (``/content/...``) cannot be re-read here; their hashes are
    bound inside ``run_contract.json``, whose own hash is part of the attestation.
    """
    launcher._exact_keys(record, launcher.A2_RUN_CONTRACT_KEYS, "A2 run contract")
    a2 = record["a2_data"]
    launcher._exact_keys(a2, launcher.A2_DATA_KEYS, "A2 run contract a2_data")
    authorization = record["owner_authorization"]
    launcher._exact_keys(authorization, {"path", "sha256"}, "A2 run owner_authorization")
    if authorization["sha256"] != authorization_sha256:
        raise RuntimeError("A2 run contract owner authorization SHA-256 differs")
    if a2["train_list_sha256"] != launcher.A2_TRAIN_LIST_SHA256:
        raise RuntimeError("A2 run contract train list SHA-256 differs")
    if record["sealed_test_accessed"] is not False:
        raise RuntimeError("A2 run contract does not record sealed_test_accessed=false")
    if (
        record["experiment"] != EXPERIMENT
        or record["run"] != run
        or record["seed"] != launcher.FROZEN["seed"]
        or record["status"] != "TRAINED"
        or record["pilot_run"] != launcher.PILOT_RUN
        or record["single_change"] != "data"
        or a2["rule_id"] != launcher.A2_RULE_ID
        or a2["repeated_roster_sha256"] != launcher.A2_REPEATED_ROSTER_SHA256
        or a2["train_list_entries"] != launcher.A2_TRAIN_LIST_ENTRIES
        or any(a2[key] != value for key, value in REPEATED.items())
        or a2["data_yaml_changed_keys"] != ["train"]
        or not all(_is_sha256(a2[key]) for key in a2 if key.endswith("_sha256"))
    ):
        raise RuntimeError("A2 run contract invariants differ")
    artifacts = record["artifacts"]
    launcher._exact_keys(artifacts, {"weights"}, "A2 run artifacts")
    weights = artifacts["weights"]
    launcher._exact_keys(weights, {"best.pt", "last.pt"}, "A2 run weights")
    run_dirs = set()
    for name in sorted(weights):
        item = weights[name]
        launcher._exact_keys(item, {"path", "sha256"}, f"A2 weight {name}")
        path = Path(item["path"])
        if path.name != name or path.parent.name != "weights" or not _is_sha256(item["sha256"]):
            raise RuntimeError(f"A2 weight binding differs: {name}")
        run_dirs.add(path.parent.parent)
    if len(run_dirs) != 1:
        raise RuntimeError("A2 weights do not share one run directory")
    run_dir = run_dirs.pop()
    if run_dir.name != run or run_dir.parent.as_posix().split("/")[-2:] != [
        "results",
        "experiments",
    ]:
        raise RuntimeError("A2 run directory is not <repo>/results/experiments/<run>")
    if record["train_args"] != launcher.expected_train_args(run_dir, a2["runtime_data_yaml"]):
        raise RuntimeError("A2 train_args differ from the pilot plus the single data change")
    if record["train_args"]["epochs"] != EPOCHS or record["train_args"]["patience"] != 0:
        raise RuntimeError("A2 run contract is not the frozen 100-epoch, patience-0 run")
    model = record["model"]
    launcher._exact_keys(model, {"path", "sha256", "origin"}, "A2 run model")
    if model["sha256"] != contract.PRETRAINED_WEIGHTS_SHA256:
        raise RuntimeError("A2 run contract does not bind the approved pretrained model")
    run_data = record["contract"]
    launcher._exact_keys(
        run_data,
        {"export_manifest_sha256", "class_map_sha256", "split_stem_sha256", "data_yaml"},
        "A2 run data contract",
    )
    if any(run_data[key] != value for key, value in GOVERNED_DATA_CONTRACT.items()):
        raise RuntimeError("A2 run contract data binding differs from the governed contract")
    if record["d05_gates"] != contract.GATES:
        raise RuntimeError("A2 run contract D-05 gates differ")
    environment = record["environment"]
    contract.validate_environment_record(environment, "A2 run environment", require_clean=True)
    if (
        environment["runtime_backend"] != "cuda"
        or environment["gpu_name"] != GPU_NAME
        or environment["git_commit"] != expected_checkout
    ):
        raise RuntimeError("A2 run environment is not the bound CUDA L4 checkout")
    return {
        "experiment": EXPERIMENT,
        "run": run,
        "seed": launcher.FROZEN["seed"],
        "approved_pretrained_sha256": contract.PRETRAINED_WEIGHTS_SHA256,
        "export_manifest_sha256": GOVERNED_DATA_CONTRACT["export_manifest_sha256"],
        "detector_lock_sha256": contract.DETECTOR_LOCK_SHA256,
        "owner_authorization_sha256": authorization["sha256"],
        "a2_train_list_sha256": launcher.A2_TRAIN_LIST_SHA256,
        "a2_repeated_roster_sha256": launcher.A2_REPEATED_ROSTER_SHA256,
        "weights": {name: weights[name]["sha256"] for name in sorted(weights)},
    }


def verify_attestation(
    manifest: dict[str, Any],
    record_bytes: bytes,
    expected_checkout: str,
    authorization_sha256: str,
) -> dict[str, Any]:
    record = _strict_json_bytes(record_bytes, "A2 run contract")
    attestation = verify_run_contract(
        record, manifest["run"], expected_checkout, authorization_sha256
    )
    attestation["run_contract_sha256"] = hashlib.sha256(record_bytes).hexdigest()
    by_path = {item["path"]: item["sha256"] for item in manifest["files"]}
    for name, sha in attestation["weights"].items():
        if by_path.get(f"{manifest['run']}/weights/{name}") != sha:
            raise RuntimeError(f"A2 archived weight differs from the run contract: {name}")
    sha = contract.canonical_sha256(attestation)
    if sha != manifest["run_attestation_sha256"]:
        raise RuntimeError("A2 run attestation does not verify")
    return {"record": record, "attestation": attestation, "run_attestation_sha256": sha}


# ---------------------------------------------------------------------- execution and logs


def _check_outcome(outcome: Any, run: str, label: str) -> None:
    if not isinstance(outcome, dict):
        raise RuntimeError(f"{label} has no training outcome")
    if outcome.get("status") == EARLY_STOPPED:
        raise RuntimeError(f"{label} is early-stopped; an early-stopped A2 result is rejected")
    if outcome.get("status") not in TERMINAL_OUTCOMES or outcome.get("completed_epoch") != EPOCHS:
        raise RuntimeError(f"{label} did not complete the frozen 100 epochs")
    if outcome.get("sealed_test_accessed") is not False or outcome.get("run") != run:
        raise RuntimeError(f"{label} training outcome identity differs")


def verify_execution(
    execution: Any, run: str, record: dict[str, Any], expected_checkout: str
) -> dict[str, Any]:
    """The archived execution record (already runtime-evidence-verified) must be this A2 run."""
    if not isinstance(execution, dict):
        raise RuntimeError("A2 execution record is not an object")
    if execution.get("experiment") != EXPERIMENT or execution.get("package") != launcher.PACKAGE:
        raise RuntimeError("A2 execution record experiment differs")
    if execution.get("status") != "SUCCEEDED" or execution.get("error") is not None:
        raise RuntimeError("A2 execution status is not SUCCEEDED")
    if execution.get("sealed_test_accessed") is not False:
        raise RuntimeError("A2 execution does not record sealed_test_accessed=false")
    if execution.get("epochs") != EPOCHS:
        raise RuntimeError("A2 execution is not a 100-epoch run")
    _check_outcome(execution.get("training_outcome"), run, "A2 execution")
    if execution.get("a2_train_list_sha256") != launcher.A2_TRAIN_LIST_SHA256:
        raise RuntimeError("A2 execution train list SHA-256 differs")
    if not isinstance(execution.get("owner_authorization"), dict) or not _is_sha256(
        execution["owner_authorization"].get("sha256")
    ):
        raise RuntimeError("A2 execution authorization SHA-256 is missing")
    if (
        execution["owner_authorization"] != record["owner_authorization"]
        or execution.get("a2_repeated_roster_sha256") != launcher.A2_REPEATED_ROSTER_SHA256
        or execution.get("checkout_commit") != expected_checkout
        or execution.get("seed") != launcher.FROZEN["seed"]
        or execution.get("tag") != launcher.FROZEN["tag"]
        or Path(str(execution.get("run_dir"))).name != run
        or not str(execution.get("state_path", "")).endswith(f"/{launcher.EXPECTED_STATE_SUFFIX}")
    ):
        raise RuntimeError("A2 execution binding differs from the run contract")
    return execution


def verify_training_log(results_csv: bytes, args_yaml: bytes) -> None:
    rows = list(csv.reader(io.StringIO(results_csv.decode("utf-8"))))
    if len(rows) < 2 or rows[0][0].strip() != "epoch":
        raise RuntimeError("A2 results.csv has no epoch table")
    epochs = [int(float(row[0])) for row in rows[1:] if row and row[0].strip()]
    if not epochs or epochs[-1] != EPOCHS or set(epochs) != set(range(1, EPOCHS + 1)):
        raise RuntimeError("A2 results.csv does not hold epochs 1..100")
    effective = yaml.safe_load(args_yaml.decode("utf-8"))
    if (
        not isinstance(effective, dict)
        or effective.get("epochs") != EPOCHS
        or effective.get("patience") != 0
    ):
        raise RuntimeError("A2 args.yaml is not the frozen 100-epoch, patience-0 run")


def verify_live_state(state: Path, archived: dict[str, Any], run: str) -> None:
    """A3 parity: the live Drive state must be the completed run the archive was packaged from."""
    live = contract.strict_json(state / "colab_execution.json")
    latest = contract.strict_json(state / "recovery/latest.json")
    if not isinstance(live, dict) or live.get("status") != "SUCCEEDED":
        raise RuntimeError("A2 live execution status is not SUCCEEDED")
    _check_outcome(live.get("training_outcome"), run, "A2 live execution")
    if (
        live.get("experiment") != EXPERIMENT
        or live.get("epochs") != EPOCHS
        or live.get("sealed_test_accessed") is not False
        or live.get("run_binding_sha256") != archived["run_binding_sha256"]
        or live.get("checkpoint_binding_sha256") != archived["checkpoint_binding_sha256"]
        or live.get("owner_authorization") != archived["owner_authorization"]
        or not isinstance(latest, dict)
        or latest.get("generation") != f"epoch-{EPOCHS:04d}"
        or latest.get("binding_sha256") != archived["checkpoint_binding_sha256"]
    ):
        raise RuntimeError("A2 live run is not the completed sealed-test-free 100-epoch run")


def verify_candidate(args: argparse.Namespace) -> dict[str, Any]:
    manifest = verify_candidate_pins(args)
    verified = verify_archive(args.archive, args.manifest)
    run = verified["run"]
    members = read_small_members(args.archive, run)
    claim = verify_attestation(
        verified,
        members["run_contract.json"],
        args.expected_checkout,
        args.owner_authorization_sha256,
    )
    execution = _strict_json_bytes(members["colab_execution.json"], "A2 execution record")
    verify_execution(execution, run, claim["record"], args.expected_checkout)
    verify_training_log(members["results.csv"], members["args.yaml"])
    authorization = claim["record"]["owner_authorization"]
    try:
        a2t.verify_owner_authorization(
            args.repo_root, authorization["path"], authorization["sha256"], a2t.SPEC
        )
    except (OSError, UnicodeDecodeError) as error:
        raise RuntimeError("A2 Owner authorization record is missing or unreadable") from error
    verify_live_state(args.state, execution, run)
    return {
        "run": run,
        "manifest": manifest,
        "best_sha256": claim["attestation"]["weights"]["best.pt"],
        "run_attestation_sha256": claim["run_attestation_sha256"],
        "run_contract_sha256": claim["attestation"]["run_contract_sha256"],
        "owner_authorization": dict(authorization),
        "checkout_commit": args.expected_checkout,
        "training_outcome": execution["training_outcome"]["status"],
    }


def extract_best(archive: Path, manifest: dict[str, Any], destination: Path, best: str) -> Path:
    """The A3 extractor's member checks, with the A2 run name and best.pt hash."""
    declared = manifest["files"]
    by_name = {item["path"]: item for item in declared}
    if len(declared) != 8 or len(by_name) != 8:
        raise RuntimeError("A2 result member roster differs")
    best_name = f"{manifest['run']}/weights/best.pt"
    if by_name.get(best_name, {}).get("sha256") != best:
        raise RuntimeError("A2 best.pt binding differs")
    target = destination / "best.pt"
    with tarfile.open(archive, "r:gz") as source:
        members = source.getmembers()
        if len(members) != 8 or {member.name for member in members} != set(by_name):
            raise RuntimeError("A2 archive roster differs")
        for member in members:
            relative = Path(member.name)
            record = by_name[member.name]
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or not member.isfile()
                or member.size != record.get("size")
            ):
                raise RuntimeError("unsafe A2 archive member")
            stream = source.extractfile(member)
            if stream is None:
                raise RuntimeError("unreadable A2 archive member")
            digest = hashlib.sha256()
            sink = target.open("xb") if member.name == best_name else None
            try:
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
                    if sink is not None:
                        sink.write(chunk)
            finally:
                if sink is not None:
                    sink.close()
            if digest.hexdigest() != record.get("sha256"):
                raise RuntimeError(f"A2 archive member hash differs: {member.name}")
    if sha256_file(target) != best:
        raise RuntimeError("extracted A2 best.pt differs")
    return target


# ---------------------------------------------------------------------------------------- run


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--bundle", type=Path, required=True)
    result.add_argument("--state", type=Path, required=True)
    result.add_argument("--archive", type=Path, required=True)
    result.add_argument("--archive-sha256", required=True)
    result.add_argument("--manifest", type=Path, required=True)
    result.add_argument("--manifest-sha256", required=True)
    result.add_argument("--owner-authorization-sha256", required=True)
    result.add_argument("--expected-checkout", required=True)
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument("--repo-root", type=Path, default=contract.REPO_ROOT)
    result.add_argument("--device", default="mps")
    return result


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.output_dir.exists():
        raise RuntimeError("refuse overwriting A2 comparison")
    predecessors = verify_predecessors()
    candidate = verify_candidate(args)
    root = args.bundle.resolve(strict=True)
    a3eval.verify_package(root, BUNDLE_SHA256)
    common.verify_evaluation_scope(
        root, root / common.PINNED_YOLO54_PREDICTIONS, common.PINNED_YOLO54_SHA256
    )
    with tempfile.TemporaryDirectory(prefix="d1-a2-val-") as temporary:
        weights = extract_best(
            args.archive, candidate["manifest"], Path(temporary), candidate["best_sha256"]
        )
        frames = a3eval.infer(root, weights, args.device)
    if len(frames) != FRAMES or sum(len(frame.gt_boxes) for frame in frames) != GT_BOXES:
        raise RuntimeError("A2 validation roster differs")
    baseline = common.load_pinned_baseline(frames, root / common.PINNED_YOLO54_PREDICTIONS)
    args.output_dir.mkdir(mode=0o700, parents=True)
    csv_path = args.output_dir / "a2_predictions.csv"
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
        "frames": FRAMES,
        "gt_boxes": GT_BOXES,
        "a2_common_method": common.report(frames),
        "pilot_common_method": common.report(baseline),
        "a2_run": candidate["run"],
        "a2_best_weight_sha256": candidate["best_sha256"],
        "a2_result_manifest_sha256": args.manifest_sha256,
        "a2_result_archive_sha256": args.archive_sha256,
        "a2_run_attestation_sha256": candidate["run_attestation_sha256"],
        "a2_run_contract_sha256": candidate["run_contract_sha256"],
        "a2_train_list_sha256": launcher.A2_TRAIN_LIST_SHA256,
        "a2_training_outcome": candidate["training_outcome"],
        "owner_authorization": candidate["owner_authorization"],
        "checkout_commit": candidate["checkout_commit"],
        "predecessor_sha256": predecessors,
        "bundle_manifest_sha256": BUNDLE_SHA256,
        "prediction_csv_sha256": sha256_file(csv_path),
        "sealed_test_accessed": False,
    }
    with (args.output_dir / "comparison_a2_r1.json").open("x", encoding="utf-8") as sink:
        json.dump(result, sink, indent=2, allow_nan=False)
        sink.write("\n")
    return result


def main(argv: list[str] | None = None) -> None:
    run(parser().parse_args(argv))


if __name__ == "__main__":
    main()
