"""R1-R1 repair for the YOLO11n N1 detector checkpoint identity; no sealed-test route."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import random
import socket
import stat
import sys
from pathlib import Path
from typing import Any

os.environ.update(
    YOLO_OFFLINE="true",
    YOLO_AUTOINSTALL="false",
    MPLBACKEND="Agg",
    CUBLAS_WORKSPACE_CONFIG=":4096:8",
    WANDB_MODE="disabled",
)


def _load_base() -> Any:
    path = Path(__file__).with_name("run_cascade_b0_r1.py")
    spec = importlib.util.spec_from_file_location("yolo11n_n1_pinned_b0_runner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned B0 runner: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = _load_base()
PACKAGE = "YOLO11N-N1-R1"
EXPERIMENT = "YOLO11N-N1-R1"
REPAIR = "R1-R1"
RUN_NAME = "D1_yolo11n_n1_detector"
WEIGHT_NAME = "yolo11n.pt"
WEIGHT_SHA256 = "0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1"
OWNER_DECISION_SHA256 = "b2b40c5937e25316c6806d5bcb6babbdcf284860a2305f2fc7b5915a058e2b8c"
EXPECTED_STATE_SUFFIX = "M1_D1_Colab/runs/yolo11n_n1_seed_20261018_r1_r1"
CONFIG = {
    "experiment": EXPERIMENT,
    "architecture": "YOLO11n",
    "pretrained_weight_sha256": WEIGHT_SHA256,
    "owner_decision_sha256": OWNER_DECISION_SHA256,
    "seed": 20261018,
    "detector_epochs": 100,
    "classifier_epochs": 30,
    "imgsz": 1280,
    "detector_batch": 4,
    "classifier_batch": 128,
    "classifier_lr": 0.001,
    "fliplr": 0.0,
    "nms_iou": 0.70,
    "classifier": "reuse_existing_compactcnn_and_vgg16_54",
}


def require_source_qa(
    root: Path,
    record: Path | None,
    anchor: str | None,
) -> None:
    """Bind the inherited B0 sources and every N1 successor governance file."""
    base.require_source_qa(root, record, anchor)
    assert record is not None  # guarded by the inherited verifier
    text = record.read_text(encoding="utf-8")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    required = {
        name
        for name in manifest["members"]
        if name.startswith("detector/colab/")
        or name.startswith("docs/review/yolo11n_dual_track_r1_")
    }
    for relative in sorted(required):
        digest = base.sha256_file(root / relative)
        if digest not in text:
            raise RuntimeError(f"training blocked: N1 QA does not bind {relative}")
    repair_source = Path(__file__).resolve()
    repair_digest = base.sha256_file(repair_source)
    if repair_digest not in text:
        raise RuntimeError("training blocked: N1 R1-R1 QA does not bind the repair runner")


def require_long_run_qa(
    proof: Path | None,
    anchor: str | None,
    manifest_sha256: str,
    state: Path,
) -> None:
    """Extend the inherited smoke proof with the exact N1 state/checkpoint identity."""
    base.require_long_run_qa(proof, anchor, manifest_sha256, "detector")
    assert proof is not None  # guarded by the inherited verifier
    record = json.loads(proof.read_text(encoding="utf-8"))
    latest = state / "detector/recovery/latest.json"
    if latest.is_symlink() or not latest.is_file():
        raise RuntimeError("long run blocked: N1 epoch-2 checkpoint pointer is missing")
    binding = {"manifest": manifest_sha256, "config": CONFIG, "stage": "detector"}
    checkpoint = base.CheckpointStore(state / "detector/recovery", retention=1000).load_latest(
        binding
    )
    state_digest = hashlib.sha256(str(state).encode("utf-8")).hexdigest()
    if (
        checkpoint.get("completed_epoch") != 2
        or record.get("package") != PACKAGE
        or record.get("state_path_sha256") != state_digest
        or record.get("checkpoint_latest_sha256") != base.sha256_file(latest)
    ):
        raise RuntimeError("long run blocked: N1 smoke proof does not bind state/checkpoint")


def normalized_state(path: Path) -> Path:
    state = path.expanduser().absolute()
    if not state.as_posix().endswith(f"/{EXPECTED_STATE_SUFFIX}"):
        raise RuntimeError(f"{PACKAGE} requires state suffix {EXPECTED_STATE_SUFFIX}")
    return state


def verify_package(root: Path, expected_manifest_hash: str) -> dict[str, Any]:
    manifest_path = root / "manifest.json"
    if manifest_path.is_symlink() or base.sha256_file(manifest_path) != expected_manifest_hash:
        raise RuntimeError("linked or untrusted YOLO11n N1 manifest")
    manifest = json.loads(manifest_path.read_text())
    if (
        manifest.get("package") != PACKAGE
        or manifest.get("architecture") != "YOLO11n"
        or manifest.get("detector_classes") != 1
        or manifest.get("pretrained_weight_sha256") != WEIGHT_SHA256
        or manifest.get("counts") != base.EXPECTED_COUNTS
        or any(
            manifest.get(key) is not False
            for key in (
                "test_included",
                "sealed_test_accessed",
                "ignore_subtraction",
                "train_val_overlap",
            )
        )
    ):
        raise RuntimeError("invalid YOLO11n N1 manifest policy")
    expected = set(manifest["members"]) | {"manifest.json"}
    actual = set()
    for folder, dirs, files in os.walk(root, followlinks=False):
        for name in [*dirs, *files]:
            path = Path(folder) / name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise RuntimeError(f"linked bundle payload: {path}")
            if stat.S_ISREG(info.st_mode):
                if info.st_nlink != 1:
                    raise RuntimeError(f"hardlinked bundle payload: {path}")
                actual.add(path.relative_to(root).as_posix())
            elif not stat.S_ISDIR(info.st_mode):
                raise RuntimeError(f"nonregular bundle payload: {path}")
    if actual != expected:
        raise RuntimeError("YOLO11n N1 bundle roster differs")
    for name, record in manifest["members"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or "test" in relative.parts:
            raise RuntimeError("unsafe YOLO11n N1 bundle member")
        path = root / relative
        if path.stat().st_size != record["bytes"] or base.sha256_file(path) != record["sha256"]:
            raise RuntimeError(f"YOLO11n N1 bundle bytes differ: {name}")
    weight = root / "models" / WEIGHT_NAME
    if weight.is_symlink() or not weight.is_file() or base.sha256_file(weight) != WEIGHT_SHA256:
        raise RuntimeError("YOLO11n N1 weight binding differs")
    if (root / "models/yolo11s.pt").exists():
        raise RuntimeError("YOLO11n N1 bundle must not contain yolo11s.pt")
    return manifest


def train_detector(root: Path, state: Path, mode: str, stop_after: int | None) -> None:
    from ultralytics import YOLO, settings
    from ultralytics.utils import checks

    checks.AUTOINSTALL = checks.ONLINE = False
    settings.update({"sync": False, "wandb": False, "mlflow": False, "clearml": False})
    stage = "detector"
    binding = {
        "manifest": base.sha256_file(root / "manifest.json"),
        "config": CONFIG,
        "stage": stage,
    }
    store = base.CheckpointStore(state / stage / "recovery", retention=1000)
    run = Path("/content/yolo11n_n1_work") / RUN_NAME
    resume = None
    if mode == "resume":
        resume = store.restore_latest(run.parent, binding)
        latest = store.load_latest(binding)
        base.require_smoke_step(mode, stop_after, latest["completed_epoch"])
        if latest["completed_epoch"] == CONFIG["detector_epochs"]:
            base.event(
                state,
                stage,
                "TRAINING_COMPLETE",
                epoch=latest["completed_epoch"],
                already_complete=True,
            )
            return
    elif run.exists() or (store.root / "latest.json").exists():
        raise RuntimeError("fresh YOLO11n N1 detector refuses existing run/checkpoint")
    run.mkdir(parents=True, exist_ok=True)
    base.write_json_atomic(run / "run_contract.json", binding)
    local_data = run.parent / "detector_data"
    base.materialize_detector_data(root, local_data)
    data = run.parent / "data.yaml"
    data.write_text(
        f"path: {local_data}\ntrain: images/train\nval: images/val\nnames:\n  0: traffic_sign\n"
    )
    model = YOLO(str(resume or root / "models" / WEIGHT_NAME))

    def restore_random_state(trainer: Any) -> None:
        if resume is None:
            return
        saved = base.torch.load(resume, map_location="cpu", weights_only=False)
        recovery = base.validate_detector_recovery(saved, binding, int(trainer.start_epoch))
        random.setstate(recovery["python_rng"])
        base.np.random.set_state(recovery["numpy_rng"])
        base.torch.set_rng_state(recovery["torch_rng"])
        base.torch.cuda.set_rng_state_all(recovery["cuda_rng"])
        trainer.scheduler.load_state_dict(recovery["scheduler"])
        generator = getattr(trainer.train_loader, "generator", None)
        if recovery["loader_generator"] is not None:
            if generator is None:
                raise RuntimeError("detector loader generator missing on resume")
            generator.set_state(recovery["loader_generator"])
        base.event(
            state,
            stage,
            "RECOVERY_RESTORED",
            next_epoch=int(trainer.start_epoch) + 1,
            worker_rng_exact_replay=False,
        )

    def checkpoint(trainer: Any) -> None:
        epoch = int(trainer.epoch) + 1
        path = run / "weights/last.pt"
        saved = base.torch.load(path, map_location="cpu", weights_only=False)
        if saved.get("optimizer") is None or int(saved["epoch"]) + 1 != epoch:
            raise RuntimeError("detector snapshot has no resumable optimizer/epoch")
        generator = getattr(trainer.train_loader, "generator", None)
        saved["b0_recovery"] = {
            "binding": binding,
            "completed_epoch": epoch,
            "python_rng": random.getstate(),
            "numpy_rng": base.np.random.get_state(),
            "torch_rng": base.torch.get_rng_state(),
            "cuda_rng": base.torch.cuda.get_rng_state_all(),
            "scheduler": trainer.scheduler.state_dict(),
            "loader_generator": generator.get_state() if generator is not None else None,
            "sampler_epoch": getattr(trainer.train_loader.sampler, "epoch", None),
            "worker_rng_exact_replay": False,
        }
        temporary = path.with_name("last.n1.tmp")
        with temporary.open("xb") as handle:
            base.torch.save(saved, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        store.save(run, epoch=epoch, binding=binding)
        base.event(state, stage, "CHECKPOINT", epoch=epoch)
        if stop_after and epoch >= stop_after:
            trainer.stop = True

    model.add_callback("on_model_save", checkpoint)
    model.add_callback("on_train_start", restore_random_state)
    base.event(state, stage, "RESUMED" if resume else "FRESH")
    if resume:
        model.train(resume=str(resume), device=0)
    else:
        model.train(
            data=str(data),
            single_cls=True,
            epochs=100,
            patience=0,
            batch=4,
            imgsz=1280,
            workers=4,
            device=0,
            seed=CONFIG["seed"],
            deterministic=True,
            optimizer="AdamW",
            lr0=0.000172,
            fliplr=0.0,
            flipud=0.0,
            iou=0.70,
            amp=True,
            plots=False,
            project=str(run.parent),
            name=run.name,
            exist_ok=True,
            save=True,
        )
    latest = store.load_latest(binding)
    base.event(
        state,
        stage,
        "TRAINING_COMPLETE" if latest["completed_epoch"] == 100 else "SMOKE_STOP",
        epoch=latest["completed_epoch"],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("check", "detector"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--source-qa-sha256")
    parser.add_argument("--source-qa-record", type=Path)
    parser.add_argument("--mode", choices=("fresh", "resume"), default="fresh")
    parser.add_argument("--stop-after", type=int, choices=(1, 2))
    parser.add_argument("--smoke-qa-proof", type=Path)
    parser.add_argument("--smoke-qa-sha256")
    args = parser.parse_args(argv)
    root = base.require_safe_directory(args.root)
    manifest = verify_package(root, args.manifest_sha256)
    if args.stage == "check":
        print(
            json.dumps(
                {
                    "valid": True,
                    "counts": manifest["counts"],
                    "sealed_test_accessed": False,
                }
            )
        )
        return 0
    state = normalized_state(args.state)
    original_config = base.CONFIG
    base.CONFIG = CONFIG
    try:
        require_source_qa(root, args.source_qa_record, args.source_qa_sha256)
        if args.stop_after is None:
            if args.mode != "resume":
                raise RuntimeError("YOLO11n N1 long run requires MODE=resume")
            require_long_run_qa(
                args.smoke_qa_proof,
                args.smoke_qa_sha256,
                args.manifest_sha256,
                state,
            )
        else:
            base.require_smoke_step(args.mode, args.stop_after)
        if not base.torch.cuda.is_available() or "L4" not in base.torch.cuda.get_device_name(0):
            raise RuntimeError("YOLO11n N1 training requires the authorized Colab NVIDIA L4 GPU")
        state = base.require_safe_directory(state, create=True)
        random.seed(CONFIG["seed"])
        base.np.random.seed(CONFIG["seed"])
        base.torch.manual_seed(CONFIG["seed"])
        base.torch.cuda.manual_seed_all(CONFIG["seed"])
        base.torch.use_deterministic_algorithms(True)
        runtime = hashlib.sha256(
            (socket.gethostname() + Path("/proc/sys/kernel/random/boot_id").read_text()).encode()
        ).hexdigest()
        base.event(
            state,
            "detector",
            "ATTEMPT",
            mode=args.mode,
            runtime_digest=runtime,
            config=CONFIG,
        )
        try:
            train_detector(root, state, args.mode, args.stop_after)
            status = json.loads((state / "colab_execution.json").read_text())
            if status["status"] == "FINALIZING":
                base.package_stage(root, state, "detector")
                base.event(state, "detector", "SUCCEEDED", epoch=CONFIG["detector_epochs"])
        except BaseException as error:
            base.event(state, "detector", "FAILED", error=str(error))
            raise
    finally:
        base.CONFIG = original_config
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

