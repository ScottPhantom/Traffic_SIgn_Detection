"""B0 local-GPU training with verified per-epoch Drive recovery. No sealed-test route."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import pickle
import random
import shutil
import socket
import sqlite3
import stat
import sys
import tarfile
import time
import uuid
from pathlib import Path
from typing import Any

os.environ.update(
    YOLO_OFFLINE="true",
    YOLO_AUTOINSTALL="false",
    MPLBACKEND="Agg",
    CUBLAS_WORKSPACE_CONFIG=":4096:8",
    WANDB_MODE="disabled",
)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.dont_write_bytecode = True

import numpy as np  # noqa: E402
import torch  # noqa: E402
from torch.utils.data import DataLoader  # noqa: E402

from d1_cascade_classifier.data import CropDataset  # noqa: E402
from d1_cascade_classifier.metrics import classification_metrics  # noqa: E402
from d1_cascade_classifier.model import CompactCNN  # noqa: E402
from m1.checkpoint_store import (  # noqa: E402
    CheckpointStore,
    require_safe_directory,
    sha256_file,
    write_json_atomic,
)

SEED = 20261018
CONFIG = {
    "seed": SEED,
    "detector_epochs": 100,
    "classifier_epochs": 30,
    "imgsz": 1280,
    "detector_batch": 4,
    "classifier_batch": 128,
    "classifier_lr": 0.001,
    "fliplr": 0.0,
    "nms_iou": 0.70,
    "classifier": "compact_cnn",
}
EXPECTED_COUNTS = {"train": {"images": 3712, "boxes": 12621}, "val": {"images": 376, "boxes": 624}}


def require_source_qa(root: Path, record: Path | None, anchor: str | None) -> None:
    if record is None:
        raise RuntimeError("training blocked: no independent B0 source QA")
    require_safe_directory(record.parent)
    if record.is_symlink() or not record.is_file() or not anchor or sha256_file(record) != anchor:
        raise RuntimeError("training blocked: no independent B0 source QA")
    text = record.read_text()
    if text.count("Verdict: **PASS**") != 1:
        raise RuntimeError("training blocked: B0 source QA is not a PASS")
    manifest = json.loads((root / "manifest.json").read_text())
    sources = {
        name
        for name in manifest["members"]
        if name.endswith((".py", ".ipynb", "pyproject.toml", "uv.lock"))
    } | {"docs/review/cascade_b0_execution_contract_r1.md"}
    for relative in sorted(sources):
        if sha256_file(root / relative) not in text:
            raise RuntimeError(f"training blocked: QA does not bind {relative}")


def verify_package(root: Path, expected_manifest_hash: str) -> dict[str, Any]:
    manifest_path = root / "manifest.json"
    if manifest_path.is_symlink() or sha256_file(manifest_path) != expected_manifest_hash:
        raise RuntimeError("linked or untrusted manifest")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("package") != "CASCADE-B0-R1" or any(
        manifest.get(k) is not False
        for k in (
            "test_included",
            "sealed_test_accessed",
            "ignore_subtraction",
            "train_val_overlap",
        )
    ):
        raise RuntimeError("invalid B0 manifest policy")
    if manifest.get("counts") != EXPECTED_COUNTS:
        raise RuntimeError("invalid B0 manifest counts")
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
        raise RuntimeError(
            f"bundle roster differs: missing{expected - actual}, extra{actual - expected}"
        )
    for name, record in manifest["members"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or "test" in relative.parts:
            raise RuntimeError("unsafe bundle member")
        path = root / name
        if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
            raise RuntimeError(f"bundle bytes differ: {name}")
    return manifest


def event(state: Path, stage: str, name: str, **values: Any) -> None:
    require_safe_directory(state)
    for filename in ("train.log", "DB_logger.db", "DB_logger.db-journal", "colab_execution.json"):
        target = state / filename
        if target.exists() or target.is_symlink():
            info = target.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise RuntimeError(f"unsafe mutable state file: {target}")
    record = {
        "time": time.time(),
        "stage": stage,
        "event": name,
        "sealed_test_accessed": False,
        **values,
    }
    text = json.dumps(record, sort_keys=True, allow_nan=False)
    with (state / "train.log").open("a") as handle:
        handle.write(text + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    with sqlite3.connect(state / "DB_logger.db") as database:
        database.execute(
            "CREATE TABLE IF NOT EXISTS logs(time REAL, stage TEXT, event TEXT, payload TEXT)"
        )
        database.execute("INSERT INTO logs VALUES (?,?,?,?)", (record["time"], stage, name, text))
        attempts = [
            json.loads(row[0])
            for row in database.execute(
                "SELECT payload FROM logs WHERE event='ATTEMPT' ORDER BY rowid"
            )
        ]
    status = (
        name
        if name in {"SUCCEEDED", "FAILED", "SMOKE_STOP"}
        else ("FINALIZING" if name == "TRAINING_COMPLETE" else "STARTED")
    )
    write_json_atomic(
        state / "colab_execution.json",
        {
            **record,
            "status": status,
            "execution_attempts": attempts,
        },
    )
    print(text, flush=True)


def package_stage(root: Path, state: Path, stage: str) -> None:
    """Package the verified optimizer-bearing Drive snapshot, not stripped local weights."""
    binding = {"manifest": sha256_file(root / "manifest.json"), "config": CONFIG, "stage": stage}
    store = CheckpointStore(state / stage / "recovery", retention=1000)
    checkpoint = store.load_latest(binding)
    expected = CONFIG[f"{stage}_epochs"]
    if checkpoint["completed_epoch"] != expected:
        raise RuntimeError("cannot finalize an incomplete stage")
    snapshot = store.snapshots / f"epoch-{expected:04d}"
    outputs = require_safe_directory(state / stage / "results", create=True)
    archive = outputs / "result.tar.gz"
    manifest_path = outputs / "result_manifest.json"
    members = {entry["path"]: snapshot / entry["path"] for entry in checkpoint["files"]}
    members.update(
        {
            "train.log": state / "train.log",
            "DB_logger.db": state / "DB_logger.db",
            "colab_execution.json": state / "colab_execution.json",
        }
    )
    if archive.exists() or archive.is_symlink():
        info = archive.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RuntimeError("unsafe existing result archive")
        recovered = {}
        with tarfile.open(archive, "r:gz") as tar:
            entries = tar.getmembers()
            if len(entries) != len(members) or {entry.name for entry in entries} != set(members):
                raise RuntimeError("existing result archive roster differs")
            for entry in entries:
                if not entry.isfile():
                    raise RuntimeError("existing result archive has nonregular entry")
                digest = hashlib.sha256()
                with tar.extractfile(entry) as reader:
                    for chunk in iter(lambda: reader.read(1024 * 1024), b""):
                        digest.update(chunk)
                recovered[entry.name] = {"sha256": digest.hexdigest(), "bytes": entry.size}
        for entry in checkpoint["files"]:
            record = recovered[entry["path"]]
            if record != {"sha256": entry["sha256"], "bytes": entry["size"]}:
                raise RuntimeError("existing archive differs from verified Drive snapshot")
        payload = {
            "stage": stage,
            "binding": binding,
            "completed_epoch": expected,
            "sealed_test_accessed": False,
            "archive_sha256": sha256_file(archive),
            "members": recovered,
        }
        if manifest_path.exists() or manifest_path.is_symlink():
            info = manifest_path.lstat()
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or json.loads(manifest_path.read_text()) != payload
            ):
                raise RuntimeError("existing final result manifest differs")
        else:
            write_json_atomic(manifest_path, payload)
        return
    if manifest_path.exists() or manifest_path.is_symlink():
        raise RuntimeError("result manifest exists without its archive")
    records = {}
    temporary = outputs / f"result.{uuid.uuid4().hex}.partial"
    with temporary.open("xb") as raw, tarfile.open(fileobj=raw, mode="w:gz") as tar:
        for name, path in sorted(members.items()):
            require_safe_directory(path.parent)
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise RuntimeError("unsafe result artifact")
            records[name] = {"sha256": sha256_file(path), "bytes": info.st_size}
            member = tarfile.TarInfo(name)
            member.size = info.st_size
            with path.open("rb") as reader:
                tar.addfile(member, reader)
            if sha256_file(path) != records[name]["sha256"]:
                raise RuntimeError("result changed during packaging")
    # Read every archived byte back before publishing its manifest.
    with tarfile.open(temporary, "r:gz") as tar:
        if set(tar.getnames()) != set(records):
            raise RuntimeError("result archive roster differs")
        for member in tar.getmembers():
            value = hashlib.sha256()
            with tar.extractfile(member) as reader:
                for chunk in iter(lambda: reader.read(1024 * 1024), b""):
                    value.update(chunk)
            if value.hexdigest() != records[member.name]["sha256"]:
                raise RuntimeError("result archive hash mismatch")
    os.replace(temporary, archive)
    write_json_atomic(
        manifest_path,
        {
            "stage": stage,
            "binding": binding,
            "completed_epoch": expected,
            "sealed_test_accessed": False,
            "archive_sha256": sha256_file(archive),
            "members": records,
        },
    )


def require_long_run_qa(proof: Path | None, anchor: str | None, manifest: str, stage: str) -> None:
    """Require externally pinned independent smoke evidence before any unrestricted run."""
    if proof is None or anchor is None:
        raise RuntimeError("long run blocked: smoke/resume independent QA proof required")
    require_safe_directory(proof.parent)
    info = proof.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or sha256_file(proof) != anchor:
        raise RuntimeError("long run blocked: untrusted smoke QA proof")
    record = json.loads(proof.read_text())
    digests = record.get("runtime_digests", [])
    if (
        record.get("verdict") != "PASS"
        or record.get("stage") != stage
        or record.get("manifest_sha256") != manifest
        or record.get("config") != CONFIG
        or record.get("sealed_test_accessed") is not False
        or record.get("fresh_completed_epoch") != 1
        or record.get("resume_started_epoch") != 2
        or record.get("resume_completed_epoch") != 2
        or len(digests) != 2
        or not all(isinstance(value, str) and len(value) == 64 for value in digests)
        or len(set(digests)) != 2
    ):
        raise RuntimeError("long run blocked: invalid smoke/resume QA evidence")


def require_smoke_step(mode: str, stop_after: int | None, completed_epoch: int = 0) -> None:
    if stop_after is None:
        return
    if (mode, stop_after) not in {("fresh", 1), ("resume", 2)}:
        raise RuntimeError("smoke workflow requires fresh epoch1 then resume epoch2")
    if completed_epoch >= stop_after:
        raise RuntimeError("smoke target must be after restored epoch")


def validate_classifier_payload(
    saved: dict[str, Any], binding: dict[str, Any], completed: int
) -> None:
    if saved.get("binding") != binding or saved.get("epoch") != completed:
        raise RuntimeError("classifier payload binding/epoch differs")


def validate_detector_recovery(
    saved: dict[str, Any], binding: dict[str, Any], start_epoch: int
) -> dict[str, Any]:
    recovery = saved.get("b0_recovery")
    required = {
        "binding",
        "completed_epoch",
        "python_rng",
        "numpy_rng",
        "torch_rng",
        "cuda_rng",
        "scheduler",
        "loader_generator",
        "sampler_epoch",
        "worker_rng_exact_replay",
    }
    if not isinstance(recovery, dict) or set(recovery) != required:
        raise RuntimeError("detector checkpoint lacks complete B0 recovery state")
    if recovery["binding"] != binding or recovery["completed_epoch"] != start_epoch:
        raise RuntimeError("detector checkpoint recovery binding/epoch differs")
    if recovery["worker_rng_exact_replay"] is not False:
        raise RuntimeError("detector recovery must disclose worker RNG replay limit")
    return recovery


def materialize_detector_data(root: Path, destination: Path) -> None:
    """Copy immutable inputs once, hash-read them, then atomically publish."""
    if destination.exists() or destination.is_symlink():
        raise RuntimeError("detector work data already exists; use a fresh runtime")
    staging = destination.parent / f".data-staging-{uuid.uuid4().hex}"
    for subdirectory in ("images", "labels"):
        shutil.copytree(root / "data" / subdirectory, staging / subdirectory)
    originals = []
    for original in (root / "data").rglob("*"):
        relative = original.relative_to(root / "data")
        if relative.parts[0] in {"images", "labels"} and original.is_file():
            originals.append((original, relative))
    copied_files = {path.relative_to(staging) for path in staging.rglob("*") if path.is_file()}
    if copied_files != {relative for _, relative in originals}:
        raise RuntimeError("detector work data roster differs")
    for original, relative in originals:
        copied = staging / relative
        info = copied.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or sha256_file(original) != sha256_file(copied)
        ):
            raise RuntimeError("detector work data copy differs")
    os.replace(staging, destination)


def train_classifier(root: Path, state: Path, mode: str, stop_after: int | None) -> None:
    stage = "classifier"
    binding = {"manifest": sha256_file(root / "manifest.json"), "config": CONFIG, "stage": stage}
    store = CheckpointStore(state / stage / "recovery", retention=1000)
    run = Path("/content/cascade_b0_work/D1_B0_classifier")
    resume = None
    if mode == "resume":
        resume = store.restore_latest(run.parent, binding)
    elif run.exists() or (store.root / "latest.json").exists():
        raise RuntimeError("fresh classifier refuses existing run/checkpoint")
    (run / "weights").mkdir(parents=True, exist_ok=True)
    write_json_atomic(run / "run_contract.json", binding)
    (run / "args.yaml").write_text(json.dumps(CONFIG))
    arrays = {}
    for split, name in (("train", "train.p"), ("val", "valid.p")):
        with (root / "data" / name).open("rb") as handle:
            arrays[split] = pickle.load(handle)  # bundle bytes verified before deserialization
    model = CompactCNN().cuda()
    optimizer = torch.optim.AdamW(model.parameters(), lr=CONFIG["classifier_lr"])
    start, best, history = 0, (-1.0, float("-inf")), []
    if resume is not None:
        saved = torch.load(resume, map_location="cpu", weights_only=False)
        validate_classifier_payload(saved, binding, store.load_latest(binding)["completed_epoch"])
        model.load_state_dict(saved["model"])
        optimizer.load_state_dict(saved["optimizer"])
        start, best, history = saved["epoch"], tuple(saved["best"]), saved["history"]
        random.setstate(saved["python_rng"])
        np.random.set_state(saved["numpy_rng"])
        torch.set_rng_state(saved["torch_rng"])
        torch.cuda.set_rng_state_all(saved["cuda_rng"])
    require_smoke_step(mode, stop_after, start)
    event(state, stage, "RESUMED" if resume else "FRESH", completed_epoch=start)
    epoch = start
    criterion = torch.nn.CrossEntropyLoss()
    for epoch in range(start + 1, CONFIG["classifier_epochs"] + 1):
        model.train()
        generator = torch.Generator().manual_seed(SEED + epoch)
        train = DataLoader(
            CropDataset(arrays["train"]),
            batch_size=128,
            shuffle=True,
            generator=generator,
            num_workers=0,
        )
        total, seen = 0.0, 0
        for inputs, targets in train:
            inputs, targets = inputs.cuda(), targets.cuda()
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(inputs), targets)
            loss.backward()
            optimizer.step()
            total += loss.item() * len(targets)
            seen += len(targets)
        model.eval()
        probs, targets_out, val_loss = [], [], 0.0
        with torch.inference_mode():
            for inputs, targets in DataLoader(CropDataset(arrays["val"]), batch_size=128):
                logits = model(inputs.cuda())
                val_loss += criterion(logits, targets.cuda()).item() * len(targets)
                probs.append(torch.softmax(logits, 1).cpu().numpy())
                targets_out.append(targets.numpy())
        labels, probabilities = np.concatenate(targets_out), np.concatenate(probs)
        metrics = classification_metrics(labels, probabilities)
        # Exact key is validated by unit tests before GPU execution.
        score = (float(metrics["macro_f1_supported_classes"]), -val_loss / len(labels))
        improved = score > best
        if improved:
            best = score
        history.append(
            {
                "epoch": epoch,
                "train_loss": total / seen,
                "val_loss": val_loss / len(labels),
                "macro_f1": score[0],
            }
        )
        saved = {
            "epoch": epoch,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "best": best,
            "history": history,
            "python_rng": random.getstate(),
            "numpy_rng": np.random.get_state(),
            "torch_rng": torch.get_rng_state(),
            "cuda_rng": torch.cuda.get_rng_state_all(),
            "binding": binding,
        }
        torch.save(saved, run / "weights/last.pt")
        if improved:
            shutil.copyfile(run / "weights/last.pt", run / "weights/best.pt")
        with (run / "results.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(history[0]))
            writer.writeheader()
            writer.writerows(history)
        store.save(run, epoch=epoch, binding=binding)
        event(state, stage, "CHECKPOINT", epoch=epoch, macro_f1=score[0])
        if stop_after and epoch >= stop_after:
            break
    event(
        state,
        stage,
        "TRAINING_COMPLETE" if epoch == CONFIG["classifier_epochs"] else "SMOKE_STOP",
        epoch=epoch,
    )


def train_detector(root: Path, state: Path, mode: str, stop_after: int | None) -> None:
    from ultralytics import YOLO, settings
    from ultralytics.utils import checks

    checks.AUTOINSTALL = checks.ONLINE = False
    settings.update({"sync": False, "wandb": False, "mlflow": False, "clearml": False})
    stage = "detector"
    binding = {"manifest": sha256_file(root / "manifest.json"), "config": CONFIG, "stage": stage}
    store = CheckpointStore(state / stage / "recovery", retention=1000)
    run = Path("/content/cascade_b0_work/D1_B0_detector")
    resume = None
    if mode == "resume":
        resume = store.restore_latest(run.parent, binding)
        latest = store.load_latest(binding)
        require_smoke_step(mode, stop_after, latest["completed_epoch"])
        if latest["completed_epoch"] == CONFIG["detector_epochs"]:
            event(
                state,
                stage,
                "TRAINING_COMPLETE",
                epoch=latest["completed_epoch"],
                already_complete=True,
            )
            return
    elif run.exists() or (store.root / "latest.json").exists():
        raise RuntimeError("fresh detector refuses existing run/checkpoint")
    run.mkdir(parents=True, exist_ok=True)
    write_json_atomic(run / "run_contract.json", binding)
    local_data = run.parent / "detector_data"
    materialize_detector_data(root, local_data)
    data = run.parent / "data.yaml"
    data.write_text(
        f"path: {local_data}\ntrain: images/train\nval: images/val\nnames:\n  0: traffic_sign\n"
    )
    model = YOLO(str(resume or root / "models/yolo11s.pt"))

    def restore_random_state(trainer):
        if resume is None:
            return
        saved = torch.load(resume, map_location="cpu", weights_only=False)
        recovery = validate_detector_recovery(saved, binding, int(trainer.start_epoch))
        random.setstate(recovery["python_rng"])
        np.random.set_state(recovery["numpy_rng"])
        torch.set_rng_state(recovery["torch_rng"])
        torch.cuda.set_rng_state_all(recovery["cuda_rng"])
        trainer.scheduler.load_state_dict(recovery["scheduler"])
        generator = getattr(trainer.train_loader, "generator", None)
        if recovery["loader_generator"] is not None:
            if generator is None:
                raise RuntimeError("detector loader generator missing on resume")
            generator.set_state(recovery["loader_generator"])
        event(
            state,
            stage,
            "RECOVERY_RESTORED",
            next_epoch=int(trainer.start_epoch) + 1,
            worker_rng_exact_replay=False,
        )

    def checkpoint(trainer):
        epoch = int(trainer.epoch) + 1
        path = run / "weights/last.pt"
        saved = torch.load(path, map_location="cpu", weights_only=False)
        if saved.get("optimizer") is None or int(saved["epoch"]) + 1 != epoch:
            raise RuntimeError("detector snapshot has no resumable optimizer/epoch")
        generator = getattr(trainer.train_loader, "generator", None)
        saved["b0_recovery"] = {
            "binding": binding,
            "completed_epoch": epoch,
            "python_rng": random.getstate(),
            "numpy_rng": np.random.get_state(),
            "torch_rng": torch.get_rng_state(),
            "cuda_rng": torch.cuda.get_rng_state_all(),
            "scheduler": trainer.scheduler.state_dict(),
            "loader_generator": generator.get_state() if generator is not None else None,
            "sampler_epoch": getattr(trainer.train_loader.sampler, "epoch", None),
            "worker_rng_exact_replay": False,
        }
        temporary = path.with_name("last.b0.tmp")
        with temporary.open("xb") as handle:
            torch.save(saved, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        store.save(run, epoch=epoch, binding=binding)
        event(state, stage, "CHECKPOINT", epoch=epoch)
        if stop_after and epoch >= stop_after:
            trainer.stop = True

    model.add_callback("on_model_save", checkpoint)
    model.add_callback("on_train_start", restore_random_state)
    event(state, stage, "RESUMED" if resume else "FRESH")
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
            seed=SEED,
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
    event(
        state,
        stage,
        "TRAINING_COMPLETE" if latest["completed_epoch"] == 100 else "SMOKE_STOP",
        epoch=latest["completed_epoch"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("check", "detector", "classifier"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--source-qa-sha256")
    parser.add_argument("--source-qa-record", type=Path)
    parser.add_argument("--mode", choices=("fresh", "resume"), default="fresh")
    parser.add_argument("--stop-after", type=int, choices=(1, 2))
    parser.add_argument("--smoke-qa-proof", type=Path)
    parser.add_argument("--smoke-qa-sha256")
    args = parser.parse_args()
    root = require_safe_directory(args.root)
    manifest = verify_package(root, args.manifest_sha256)
    if args.stage == "check":
        print(
            json.dumps({"valid": True, "counts": manifest["counts"], "sealed_test_accessed": False})
        )
        return
    require_source_qa(root, args.source_qa_record, args.source_qa_sha256)
    if args.stop_after is None:
        require_long_run_qa(
            args.smoke_qa_proof, args.smoke_qa_sha256, args.manifest_sha256, args.stage
        )
    else:
        require_smoke_step(args.mode, args.stop_after)
    if not torch.cuda.is_available() or "L4" not in torch.cuda.get_device_name(0):
        raise RuntimeError("B0 training requires the authorized Colab NVIDIA L4 GPU")
    state = require_safe_directory(args.state, create=True)
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.use_deterministic_algorithms(True)
    runtime = hashlib.sha256(
        (socket.gethostname() + Path("/proc/sys/kernel/random/boot_id").read_text()).encode()
    ).hexdigest()
    event(state, args.stage, "ATTEMPT", mode=args.mode, runtime_digest=runtime, config=CONFIG)
    try:
        (train_detector if args.stage == "detector" else train_classifier)(
            root, state, args.mode, args.stop_after
        )
        status = json.loads((state / "colab_execution.json").read_text())
        if status["status"] == "FINALIZING":
            package_stage(root, state, args.stage)
            event(state, args.stage, "SUCCEEDED", epoch=CONFIG[f"{args.stage}_epochs"])
    except BaseException as error:
        event(state, args.stage, "FAILED", error=str(error))
        raise


if __name__ == "__main__":
    main()
