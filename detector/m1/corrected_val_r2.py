"""Use-time-bound successor for the QA-failed corrected-validation evaluator R1."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from m1 import contract

REPO_ROOT = contract.REPO_ROOT
PREDECESSOR = Path("detector/m1/corrected_val_r1.py")
PREDECESSOR_QA = Path("docs/review/d1_corrected_val_r1_independent_qa_record.md")
INTEGRATION_EXPORTER = Path(
    "scripts/build_m1_yolo_dataset_wp38_r1_integration_r4.py"
)
REPORT_NAME = "eval_val_wp38_r1_r4.json"
PINNED = {
    PREDECESSOR: "0e56949d4a8e01b01a3de509f982ecbb4d0fd4ec1b44ef51975b47621289b8e5",
    PREDECESSOR_QA: "cda54add52e2cd2c672446f92e8cb1380a1bd30110c7fb86e33011146f2248ab",
    INTEGRATION_EXPORTER: "0ef217775c7dcab70fddda8d5a4f89a5ab260d63a2407b85544f387774844426",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_predecessor() -> ModuleType:
    return _load(REPO_ROOT / PREDECESSOR, "m1_corrected_val_r2_predecessor")


def load_integration() -> ModuleType:
    return _load(REPO_ROOT / INTEGRATION_EXPORTER, "m1_corrected_val_r2_integration")


def verify_pins() -> None:
    for relative, expected in PINNED.items():
        path = REPO_ROOT / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned corrected-validation R1 evidence differs: {relative}")


def _same_inode(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _read_fd_hash(fd: int) -> str:
    os.lseek(fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    while chunk := os.read(fd, 1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def _open_weight_guard(path: Path, expected_hash: str) -> tuple[int, os.stat_result]:
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise RuntimeError("registered best.pt is not a single-link regular file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    opened = os.fstat(fd)
    if (
        not _same_inode(before, opened)
        or opened.st_nlink != 1
        or _read_fd_hash(fd) != expected_hash
    ):
        os.close(fd)
        raise RuntimeError("registered best.pt changed while opening")
    return fd, opened


def _validate_weight_guard(
    path: Path, fd: int, opened: os.stat_result, expected_hash: str
) -> None:
    retained = os.fstat(fd)
    current = path.lstat()
    if (
        not stat.S_ISREG(retained.st_mode)
        or retained.st_nlink != 1
        or not _same_inode(opened, retained)
        or not _same_inode(current, retained)
        or _read_fd_hash(fd) != expected_hash
    ):
        raise RuntimeError("registered best.pt binding changed during evaluation")


def _input_fingerprint(export_dir: Path) -> str:
    records: list[dict[str, Any]] = []
    yaml_path = export_dir / "data.yaml"
    yaml_info = yaml_path.lstat()
    if not stat.S_ISREG(yaml_info.st_mode) or yaml_info.st_nlink != 1:
        raise RuntimeError("corrected-validation data.yaml is not a single-link regular file")
    records.append(
        {
            "path": "data.yaml",
            "inode": [yaml_info.st_dev, yaml_info.st_ino],
            "sha256": sha256_file(yaml_path),
        }
    )
    for split_dir, expected_count in (("images/val", 376), ("labels/val", 376)):
        directory = export_dir / split_dir
        names = sorted(directory.iterdir())
        if len(names) != expected_count:
            raise RuntimeError(f"corrected-validation roster differs: {split_dir}")
        for path in names:
            info = path.lstat()
            relative = path.relative_to(export_dir).as_posix()
            if split_dir.startswith("images"):
                if not stat.S_ISLNK(info.st_mode):
                    raise RuntimeError(f"corrected-validation image is not a symlink: {relative}")
                target_text = os.readlink(path)
                after = path.lstat()
                if not _same_inode(info, after):
                    raise RuntimeError(f"image link changed during fingerprint: {relative}")
                target = Path(target_text)
                if not target.is_absolute():
                    target = path.parent / target
                target_info = target.lstat()
                if not stat.S_ISREG(target_info.st_mode):
                    raise RuntimeError(f"image target is not regular: {relative}")
                records.append(
                    {
                        "path": relative,
                        "inode": [info.st_dev, info.st_ino],
                        "target": target_text,
                        "target_inode": [target_info.st_dev, target_info.st_ino],
                        "sha256": sha256_file(target),
                    }
                )
            else:
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise RuntimeError(f"label is not a single-link regular file: {relative}")
                records.append(
                    {
                        "path": relative,
                        "inode": [info.st_dev, info.st_ino],
                        "sha256": sha256_file(path),
                    }
                )
    payload = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _safe_write_report(run_dir: Path, payload: dict[str, Any]) -> Path:
    integration = load_integration()
    root_fd, retained_fds, relations = integration._open_directory_chain(run_dir)
    temporary = f".{REPORT_NAME}.partial"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    temp_fd: int | None = None
    linked = False
    try:
        temp_fd = os.open(temporary, flags, 0o644, dir_fd=root_fd)
        data = (
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
            + "\n"
        ).encode()
        offset = 0
        while offset < len(data):
            offset += os.write(temp_fd, data[offset:])
        os.fsync(temp_fd)
        info = os.fstat(temp_fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RuntimeError("corrected-validation report partial is unsafe")
        os.link(
            temporary,
            REPORT_NAME,
            src_dir_fd=root_fd,
            dst_dir_fd=root_fd,
            follow_symlinks=False,
        )
        linked = True
        os.unlink(temporary, dir_fd=root_fd)
        final = os.stat(REPORT_NAME, dir_fd=root_fd, follow_symlinks=False)
        if not _same_inode(info, final) or final.st_nlink != 1:
            raise RuntimeError("corrected-validation report binding differs")
        integration._validate_relations(relations)
        return run_dir / REPORT_NAME
    finally:
        if temp_fd is not None:
            os.close(temp_fd)
        if not linked:
            try:
                os.unlink(temporary, dir_fd=root_fd)
            except FileNotFoundError:
                pass
        for fd in reversed(retained_fds):
            os.close(fd)


def verify_corrected_data() -> dict[str, Any]:
    verify_pins()
    return load_predecessor().verify_corrected_data()


def evaluate(
    weights: str,
    *,
    imgsz: int = 1280,
    device: str = "mps",
    nms_iou: float = 0.70,
    bootstrap: bool = True,
) -> dict[str, Any]:
    verify_pins()
    predecessor = load_predecessor()
    pre_data = predecessor.verify_corrected_data()
    pre_weights = contract.bind_run_weights(weights)
    weight_path = Path(pre_weights["path"])
    report_path = Path(pre_weights["run_dir"]) / REPORT_NAME
    if report_path.exists() or report_path.is_symlink():
        raise RuntimeError(f"refused to overwrite corrected-validation report: {report_path}")
    integration = load_integration()
    _root_fd, data_fds, data_relations = integration._open_directory_chain(
        predecessor.EXPORT_DIR
    )
    weight_fd, weight_opened = _open_weight_guard(weight_path, pre_weights["sha256"])
    before_fingerprint = _input_fingerprint(predecessor.EXPORT_DIR)
    captured: dict[str, Any] = {}
    original_write = predecessor.cli.write_json

    def capture_report(path: Path, payload: dict[str, Any]) -> None:
        if path != report_path or captured:
            raise RuntimeError("corrected-validation predecessor attempted an unexpected write")
        captured["payload"] = payload

    predecessor.cli.write_json = capture_report
    try:
        result = predecessor.evaluate(
            weights,
            imgsz=imgsz,
            device=device,
            nms_iou=nms_iou,
            bootstrap=bootstrap,
        )
        post_data = predecessor.verify_corrected_data()
        post_weights = contract.bind_run_weights(weights)
        after_fingerprint = _input_fingerprint(predecessor.EXPORT_DIR)
        _validate_weight_guard(
            weight_path, weight_fd, weight_opened, pre_weights["sha256"]
        )
        integration._validate_relations(data_relations)
        if (
            pre_data != post_data
            or pre_weights != post_weights
            or before_fingerprint != after_fingerprint
            or "payload" not in captured
        ):
            raise RuntimeError("corrected-validation input binding changed during evaluation")
        payload = captured["payload"]
        payload["use_time_binding"] = {
            "input_fingerprint_sha256": before_fingerprint,
            "weight_inode": [weight_opened.st_dev, weight_opened.st_ino],
            "weight_sha256": pre_weights["sha256"],
            "pre_post_authority_equal": True,
        }
        output = _safe_write_report(Path(pre_weights["run_dir"]), payload)
        return {**result, "report": str(output), "use_time_binding_verified": True}
    finally:
        predecessor.cli.write_json = original_write
        os.close(weight_fd)
        for fd in reversed(data_fds):
            os.close(fd)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    run = commands.add_parser("evaluate")
    run.add_argument("--weights", required=True)
    run.add_argument("--imgsz", type=int, default=1280)
    run.add_argument("--device", default="mps")
    run.add_argument("--nms-iou", type=float, default=0.70)
    run.add_argument("--no-bootstrap", action="store_true")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = (
            verify_corrected_data()
            if args.command == "check"
            else evaluate(
                args.weights,
                imgsz=args.imgsz,
                device=args.device,
                nms_iou=args.nms_iou,
                bootstrap=not args.no_bootstrap,
            )
        )
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
