#!/usr/bin/env python3
"""Three-leg YOLO11n N54 Colab runner; train/val only and no sealed-test route."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tarfile
import uuid
from pathlib import Path
from typing import Any


def _load(name: str, filename: str) -> Any:
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned D1 runner: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


r1 = _load("yolo11n_n54_pinned_checkpoint_r1", "run_d1_colab_checkpoint_r1.py")
r2 = _load("yolo11n_n54_pinned_checkpoint_r2", "run_d1_colab_checkpoint_r2.py")
PACKAGE = "YOLO11N-N54-R1"
EXPERIMENT = "YOLO11N-N54-R1"
OWNER_DECISION_SHA256 = "b2b40c5937e25316c6806d5bcb6babbdcf284860a2305f2fc7b5915a058e2b8c"
WEIGHT_SHA256 = "0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1"
EXPECTED_STATE_SUFFIX = "M1_D1_Colab/runs/yolo11n_n54_seed_20261018_r1"
ATTEMPTS_NAME = "n54_execution_attempts.jsonl"
FROZEN = {
    "seed": 20261018,
    "epochs": 100,
    "imgsz": 1280,
    "batch": 4,
    "workers": 4,
    "fraction": 1.0,
    "patience": 30,
    "cos_lr": True,
    "tag": "n54_r1",
}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--repo-root", type=Path, required=True)
    root.add_argument("--bundle", type=Path, required=True)
    root.add_argument("--bundle-sha256", required=True)
    root.add_argument("--state-dir", type=Path, required=True)
    root.add_argument("--mode", choices=("fresh", "resume"), required=True)
    root.add_argument("--expected-checkout", required=True)
    root.add_argument("--source-qa-record", type=Path, required=True)
    root.add_argument("--source-qa-sha256", required=True)
    root.add_argument("--smoke-qa-proof", type=Path)
    root.add_argument("--smoke-qa-sha256")
    root.add_argument("--stop-after-epoch", type=int, choices=(1, 2))
    root.add_argument("--seed", type=int, default=FROZEN["seed"])
    root.add_argument("--epochs", type=int, default=FROZEN["epochs"])
    root.add_argument("--imgsz", type=int, default=FROZEN["imgsz"])
    root.add_argument("--batch", type=int, default=FROZEN["batch"])
    root.add_argument("--device", default="0")
    root.add_argument("--workers", type=int, default=FROZEN["workers"])
    root.add_argument("--fraction", type=float, default=FROZEN["fraction"])
    root.add_argument("--patience", type=int, default=FROZEN["patience"])
    root.add_argument("--tag", default=FROZEN["tag"])
    root.add_argument("--cos-lr", action="store_true", required=True)
    return root


def normalized_state(path: Path) -> Path:
    state = path.expanduser().absolute()
    if not state.as_posix().endswith(f"/{EXPECTED_STATE_SUFFIX}"):
        raise RuntimeError(f"{PACKAGE} requires Drive state suffix {EXPECTED_STATE_SUFFIX}")
    return r1.require_unlinked_path(state, directory=True)


def observed_checkout(repo_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def validate_frozen(args: argparse.Namespace) -> str:
    observed = {key: getattr(args, key) for key in FROZEN}
    if observed != FROZEN:
        raise RuntimeError(f"{EXPERIMENT} frozen arguments differ: {observed!r}")
    if str(args.device) != "0":
        raise RuntimeError(f"{EXPERIMENT} requires CUDA device 0")
    if not re.fullmatch(r"[0-9a-f]{40}", args.expected_checkout):
        raise RuntimeError("expected checkout must be a full immutable Git commit")
    if not re.fullmatch(r"[0-9a-f]{64}", args.bundle_sha256):
        raise RuntimeError("bundle SHA-256 is malformed")
    leg = (
        "fresh_epoch_1"
        if (args.mode, args.stop_after_epoch) == ("fresh", 1)
        else "resume_epoch_2"
        if (args.mode, args.stop_after_epoch) == ("resume", 2)
        else "long_resume"
        if (args.mode, args.stop_after_epoch) == ("resume", None)
        else None
    )
    if leg is None:
        raise RuntimeError("N54 workflow must be fresh-1, resume-2, or long-resume")
    return leg


def canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_binding(args: argparse.Namespace) -> str:
    return canonical_sha256(
        {
            "schema": "yolo11n-n54-r1-run-binding-v1",
            "package": PACKAGE,
            "owner_decision_sha256": OWNER_DECISION_SHA256,
            "checkout_commit": args.expected_checkout,
            "state_path": str(normalized_state(args.state_dir)),
            "bundle_sha256": args.bundle_sha256,
            "pretrained_weight_sha256": WEIGHT_SHA256,
            **FROZEN,
            "device": str(args.device),
        }
    )


def read_attempts(state: Path) -> list[dict[str, Any]]:
    path = state / ATTEMPTS_NAME
    if not path.exists():
        return []
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("N54 attempts log is missing or linked")
    attempts = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            raise RuntimeError("N54 attempts log contains a blank record")
        attempts.append(json.loads(line))
    return attempts


def append_attempt(state: Path, payload: dict[str, Any]) -> None:
    r1.append_jsonl(state / ATTEMPTS_NAME, payload)


def validate_attempts(
    attempts: list[dict[str, Any]], leg: str, runtime_digest: str, binding: str
) -> None:
    expected = []
    if leg in {"resume_epoch_2", "long_resume"}:
        expected.append(("fresh_epoch_1", 1))
    if leg == "long_resume":
        expected.append(("resume_epoch_2", 2))
    if len(attempts) < len(expected) or (leg != "long_resume" and len(attempts) != len(expected)):
        raise RuntimeError(f"{leg} has invalid completed-attempt count")
    observed_digests = set()
    for record, (expected_leg, epoch) in zip(
        attempts[: len(expected)], expected, strict=True
    ):
        if (
            record.get("leg") != expected_leg
            or record.get("status") != "PAUSED_FOR_RESUME"
            or record.get("completed_epoch") != epoch
            or record.get("run_binding_sha256") != binding
            or record.get("sealed_test_accessed") is not False
            or not re.fullmatch(r"[0-9a-f]{64}", str(record.get("runtime_digest")))
        ):
            raise RuntimeError("N54 prior attempt evidence differs")
        observed_digests.add(record["runtime_digest"])
    for record in attempts[len(expected) :]:
        if (
            record.get("leg") != "long_resume"
            or record.get("status") != "FAILED"
            or record.get("run_binding_sha256") != binding
            or record.get("sealed_test_accessed") is not False
            or not re.fullmatch(r"[0-9a-f]{64}", str(record.get("runtime_digest")))
        ):
            raise RuntimeError("N54 prior retry evidence differs")
        observed_digests.add(record["runtime_digest"])
    if len(observed_digests) != len(attempts) or runtime_digest in observed_digests:
        raise RuntimeError("N54 each leg requires a distinct runtime identity")


def require_l4() -> dict[str, str]:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,uuid,driver_version",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("N54 requires an available NVIDIA L4 runtime") from error
    rows = [row.strip() for row in completed.stdout.splitlines() if row.strip()]
    if len(rows) != 1:
        raise RuntimeError("N54 requires exactly one NVIDIA L4 GPU")
    fields = [field.strip() for field in rows[0].split(",", maxsplit=2)]
    if len(fields) != 3 or fields[0] != "NVIDIA L4":
        raise RuntimeError("N54 requires exactly one NVIDIA L4 GPU")
    return {"name": fields[0], "uuid": fields[1], "driver_version": fields[2]}


def require_source_qa(repo_root: Path, record: Path, expected_hash: str) -> None:
    record = record.expanduser().absolute()
    if (
        record.is_symlink()
        or not record.is_file()
        or r1.base.sha256_file(record) != expected_hash
    ):
        raise RuntimeError("training blocked: N54 source QA record is absent or differs")
    text = record.read_text(encoding="utf-8")
    if text.count("Verdict: **PASS**") != 1:
        raise RuntimeError("training blocked: N54 source QA is not a PASS")
    required = (
        "detector/m1/resumable_train_n54_r1.py",
        "detector/colab/run_yolo11n_n54_r1.py",
        "detector/tests/test_resumable_train_n54_r1.py",
        "detector/tests/test_yolo11n_n54_r1.py",
        "docs/review/yolo11n_dual_track_r1_owner_decision_record.md",
        "docs/review/yolo11n_dual_track_r1_run_contract.md",
    )
    for relative in required:
        path = repo_root / relative
        if path.is_symlink() or not path.is_file() or r1.base.sha256_file(path) not in text:
            raise RuntimeError(f"training blocked: N54 QA does not bind {relative}")


def verify_epoch_2_checkpoint(state: Path) -> str:
    latest_path = state / "recovery/latest.json"
    if latest_path.is_symlink() or not latest_path.is_file():
        raise RuntimeError("N54 epoch-2 checkpoint pointer is missing or linked")
    latest = r2.strict_json_bytes(latest_path.read_bytes())
    if (
        not isinstance(latest, dict)
        or latest.get("generation") != "epoch-0002"
        or not re.fullmatch(r"[0-9a-f]{64}", str(latest.get("binding_sha256")))
    ):
        raise RuntimeError("N54 smoke checkpoint is not generation epoch-0002")
    manifest = r2.verify_current_checkpoint(state, latest["binding_sha256"])
    if manifest.get("completed_epoch") != 2:
        raise RuntimeError("N54 smoke checkpoint manifest is not epoch 2")
    return r1.base.sha256_file(latest_path)


def require_smoke_qa(
    proof: Path | None,
    expected_hash: str | None,
    *,
    attempts: list[dict[str, Any]],
    binding: str,
    bundle_sha256: str,
    state: Path,
) -> None:
    if proof is None or expected_hash is None:
        raise RuntimeError("long N54 run requires an independent smoke QA proof")
    proof = proof.expanduser().absolute()
    if proof.is_symlink() or not proof.is_file() or r1.base.sha256_file(proof) != expected_hash:
        raise RuntimeError("N54 smoke QA proof is absent or differs")
    payload = json.loads(proof.read_text(encoding="utf-8"))
    latest_sha256 = verify_epoch_2_checkpoint(state)
    expected_digests = [record["runtime_digest"] for record in attempts[:2]]
    if (
        payload.get("schema") != "yolo11n-n54-r1-smoke-qa-v1"
        or payload.get("package") != PACKAGE
        or payload.get("verdict") != "PASS"
        or payload.get("bundle_sha256") != bundle_sha256
        or payload.get("run_binding_sha256") != binding
        or payload.get("state_path_sha256")
        != hashlib.sha256(str(state).encode("utf-8")).hexdigest()
        or payload.get("checkpoint_epoch") != 2
        or payload.get("checkpoint_latest_sha256") != latest_sha256
        or payload.get("runtime_digests") != expected_digests
        or len(set(expected_digests)) != 2
        or payload.get("sealed_test_accessed") is not False
    ):
        raise RuntimeError("N54 smoke QA proof does not bind the epoch-2 state")


def validate_outcome(outcome: dict[str, Any], stop_after: int | None) -> int:
    expected_epoch = stop_after or 100
    allowed = (
        {"PAUSED_FOR_RESUME"}
        if stop_after
        else {"COMPLETED", "COMPLETED_FROM_FINAL_CHECKPOINT"}
    )
    if outcome.get("completed_epoch") != expected_epoch or outcome.get("status") not in allowed:
        raise RuntimeError(f"N54 training outcome differs: {outcome!r}")
    return expected_epoch


def build_train_command(args: argparse.Namespace, model: Path, state: Path) -> list[str]:
    command = [
        "uv",
        "run",
        "python",
        "-m",
        "m1.resumable_train_n54_r1",
        "--model",
        str(model),
        "--checkpoint-dir",
        str(state / "recovery"),
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
        "--cos-lr",
    ]
    if args.mode == "resume":
        command.append("--resume")
    if args.stop_after_epoch is not None:
        command.extend(("--stop-after-epoch", str(args.stop_after_epoch)))
    return command


def package_result(
    state: Path,
    run_dir: Path,
    execution_path: Path,
    text_log: Path,
    database_log: Path,
) -> dict[str, Any]:
    required = (
        run_dir / "weights/best.pt",
        run_dir / "weights/last.pt",
        run_dir / "results.csv",
        run_dir / "args.yaml",
        run_dir / "run_contract.json",
        execution_path,
        text_log,
        database_log,
    )
    if any(
        not path.is_file() or path.is_symlink() or path.stat().st_size == 0
        for path in required
    ):
        raise RuntimeError("N54 result roster contains a missing, linked or empty artifact")
    contract = json.loads((run_dir / "run_contract.json").read_text(encoding="utf-8"))
    if (
        contract.get("experiment") != EXPERIMENT
        or contract.get("owner_decision_sha256") != OWNER_DECISION_SHA256
        or contract.get("model", {}).get("sha256") != WEIGHT_SHA256
        or contract.get("status") != "TRAINED"
        or contract.get("environment", {}).get("runtime_backend") != "cuda"
    ):
        raise RuntimeError("N54 trained run contract differs")
    r1.base.validate_sqlite_log(database_log, text_log, run_dir / "results.csv")
    output = r1.require_unlinked_path(state / "results", directory=True)
    output.mkdir(exist_ok=True)
    r1.require_unlinked_path(output, directory=True)
    archive = output / "result.tar.gz"
    manifest_path = output / "result_manifest.json"
    names = {
        required[0]: "weights/best.pt",
        required[1]: "weights/last.pt",
        required[2]: "results.csv",
        required[3]: "args.yaml",
        required[4]: "run_contract.json",
        required[5]: "colab_logs/colab_execution.json",
        required[6]: "colab_logs/colab_train.log",
        required[7]: "colab_logs/DB_logger.db",
    }
    members = {
        name: {"sha256": r1.base.sha256_file(path), "bytes": path.stat().st_size}
        for path, name in names.items()
    }

    def verify_archive(path: Path) -> None:
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("N54 result archive is missing or linked")
        with tarfile.open(path, "r:gz") as handle:
            entries = handle.getmembers()
            if len(entries) != len(members) or {entry.name for entry in entries} != set(members):
                raise RuntimeError("N54 result archive roster differs")
            for member in entries:
                reader = handle.extractfile(member)
                if not member.isfile() or reader is None:
                    raise RuntimeError("N54 result archive contains a nonregular member")
                digest = hashlib.sha256(reader.read()).hexdigest()
                if members[member.name] != {"sha256": digest, "bytes": member.size}:
                    raise RuntimeError("N54 result archive readback differs")

    if archive.exists() or archive.is_symlink():
        try:
            verify_archive(archive)
        except (OSError, RuntimeError, tarfile.TarError):
            quarantine = r1.require_unlinked_path(output / "quarantine", directory=True)
            quarantine.mkdir(exist_ok=True)
            r1.require_unlinked_path(quarantine, directory=True)
            os.replace(archive, quarantine / f"result.{uuid.uuid4().hex}.incomplete.tar.gz")
            if manifest_path.exists() and not manifest_path.is_symlink():
                os.replace(
                    manifest_path,
                    quarantine / f"manifest.{uuid.uuid4().hex}.incomplete.json",
                )
        else:
            recovered = {
                "schema": "yolo11n-n54-r1-result-v1",
                "package": PACKAGE,
                "completed_epoch": 100,
                "archive_sha256": r1.base.sha256_file(archive),
                "members": members,
                "sealed_test_accessed": False,
            }
            if manifest_path.exists():
                if manifest_path.is_symlink() or r1.base.strict_json(manifest_path) != recovered:
                    raise RuntimeError("existing N54 result manifest differs")
            else:
                r1.base.write_json(manifest_path, recovered)
            return {"archive": str(archive), "manifest": str(manifest_path), **recovered}
    elif manifest_path.exists() or manifest_path.is_symlink():
        quarantine = r1.require_unlinked_path(output / "quarantine", directory=True)
        quarantine.mkdir(exist_ok=True)
        r1.require_unlinked_path(quarantine, directory=True)
        os.replace(
            manifest_path,
            quarantine / f"manifest.{uuid.uuid4().hex}.orphaned.json",
        )

    partial = output / f"result.{uuid.uuid4().hex}.partial"
    with tarfile.open(partial, "x:gz", compresslevel=1) as handle:
        for path, name in names.items():
            handle.add(path, arcname=name, recursive=False)
    verify_archive(partial)
    os.replace(partial, archive)
    manifest = {
        "schema": "yolo11n-n54-r1-result-v1",
        "package": PACKAGE,
        "completed_epoch": 100,
        "archive_sha256": r1.base.sha256_file(archive),
        "members": members,
        "sealed_test_accessed": False,
    }
    r1.base.write_json(manifest_path, manifest)
    return {"archive": str(archive), "manifest": str(manifest_path), **manifest}


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    state = args.state_dir.expanduser().absolute()
    execution_path = state / "colab_execution.json"
    attempt: dict[str, Any] | None = None
    try:
        leg = validate_frozen(args)
        repo_root = r1.require_unlinked_path(args.repo_root, directory=True)
        state = normalized_state(args.state_dir)
        bundle = r1.require_unlinked_path(args.bundle, directory=False)
        if r1.base.sha256_file(bundle) != args.bundle_sha256:
            raise RuntimeError("N54 bundle SHA-256 differs")
        if observed_checkout(repo_root) != args.expected_checkout:
            raise RuntimeError("N54 checkout differs from the immutable commit")
        model = repo_root / "models/pretrained/yolo11n.pt"
        if model.is_symlink() or not model.is_file() or r1.base.sha256_file(model) != WEIGHT_SHA256:
            raise RuntimeError("official yolo11n.pt is absent, linked or differs")
        require_source_qa(repo_root, args.source_qa_record, args.source_qa_sha256)
        gpu_evidence = require_l4()
        identity = r2.derive_runtime_identity(args.tag, r2.BOOT_ID_PATH.read_text(encoding="ascii"))
        binding = run_binding(args)
        attempts = read_attempts(state)
        validate_attempts(attempts, leg, identity["digest"], binding)
        if leg == "long_resume":
            require_smoke_qa(
                args.smoke_qa_proof,
                args.smoke_qa_sha256,
                attempts=attempts,
                binding=binding,
                bundle_sha256=args.bundle_sha256,
                state=state,
            )
        state.mkdir(parents=True, exist_ok=True)
        if leg == "fresh_epoch_1" and any(state.iterdir()):
            raise RuntimeError("fresh N54 state must be empty")
        logger, text_log, database_log = r1.configure_safe_logging(state)
        started = r1.base.now()
        logger.info(
            "D1 Colab workflow started package=%s leg=%s epochs=%d",
            PACKAGE,
            leg,
            args.epochs,
        )
        attempt = {
            "leg": leg,
            "mode": args.mode,
            "status": "STARTED",
            "completed_epoch": None,
            "started_at": started,
            "finished_at": None,
            "runtime_digest": identity["digest"],
            "gpu_evidence": gpu_evidence,
            "run_binding_sha256": binding,
            "sealed_test_accessed": False,
            "error": None,
        }
        execution = {
            "schema": "yolo11n-n54-r1-execution-v1",
            "package": PACKAGE,
            "status": "STARTED",
            "leg": leg,
            "run_binding_sha256": binding,
            "gpu_evidence": gpu_evidence,
            "execution_attempts": [*attempts, attempt],
            "sealed_test_accessed": False,
            "error": None,
        }
        r1.base.write_json(execution_path, execution)
        r1.extract_historical_bundle(repo_root, bundle)
        r1.base.verify_split_bindings(repo_root, bundle)
        r1.base.run_command(
            logger,
            [
                sys.executable,
                "scripts/build_m1_yolo_dataset.py",
                "export",
                "--repo-root",
                str(repo_root),
            ],
            cwd=repo_root,
        )
        detector_root = repo_root / "detector"
        r1.base.run_command(logger, ["uv", "sync", "--frozen"], cwd=detector_root)
        if r1.base.sha256_file(model) != WEIGHT_SHA256:
            raise RuntimeError("official yolo11n.pt changed during preflight")
        environment = r1.base.colab_subprocess_environment()
        r1.base.run_command(
            logger,
            ["uv", "run", "python", "-m", "m1.cli", "check"],
            cwd=detector_root,
            env=environment,
        )
        command = build_train_command(args, model, state)
        logger.info("Training start")
        r1.base.run_command(logger, command, cwd=detector_root, env=environment)
        logger.info("Training end")
        outcome = r1.base.strict_json(state / "recovery/training_outcome.json")
        expected_epoch = validate_outcome(outcome, args.stop_after_epoch)
        expected_status = "PAUSED_FOR_RESUME" if args.stop_after_epoch else "SUCCEEDED"
        attempt.update(
            status=expected_status,
            completed_epoch=expected_epoch,
            finished_at=r1.base.now(),
        )
        attempts = [*attempts, attempt]
        execution.update(
            status=("SUCCEEDED" if leg == "long_resume" else "PAUSED_FOR_RESUME"),
            execution_attempts=attempts,
            training_outcome=outcome,
        )
        r1.base.write_json(execution_path, execution)
        if leg == "long_resume":
            logger.info("Terminal outcome SUCCEEDED; validated result packaging begins")
            package_result(
                state,
                Path(outcome["run_dir"]),
                execution_path,
                text_log,
                database_log,
            )
        append_attempt(state, attempt)
        print(json.dumps(execution, indent=2, sort_keys=True))
        return 0
    except Exception as error:
        if attempt is not None:
            attempt.update(
                status="FAILED",
                finished_at=r1.base.now(),
                error=f"{type(error).__name__}: {error}",
            )
            try:
                append_attempt(state, attempt)
                r1.base.write_json(
                    execution_path,
                    {
                        "schema": "yolo11n-n54-r1-execution-v1",
                        "package": PACKAGE,
                        "status": "FAILED",
                        "execution_attempts": [*read_attempts(state)[:-1], attempt],
                        "sealed_test_accessed": False,
                        "error": attempt["error"],
                    },
                )
            except Exception:
                pass
        print(json.dumps({"status": "FAILED", "error": f"{type(error).__name__}: {error}"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
