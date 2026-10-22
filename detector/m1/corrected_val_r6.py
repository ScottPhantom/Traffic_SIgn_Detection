"""Descriptor-first report-publication successor for QA-failed evaluator R5.

R5 closed the unsafe cleanup paths but retained a named staging candidate.  R6 removes that
candidate path entirely: it reserves the final name with ``O_EXCL`` and mode ``000``, writes and
verifies through the retained descriptor, then makes the verified inode readable as the final
publication step.  Failures never unlink a pathname and force the owned descriptor back to mode
``000`` before it is closed.
"""

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
PREDECESSOR = Path("detector/m1/corrected_val_r5.py")
PREDECESSOR_TEST = Path("detector/tests/test_corrected_val_r5.py")
PREDECESSOR_REMEDIATION = Path("docs/review/d1_corrected_val_r5_qa_remediation_report.md")
PREDECESSOR_QA = Path("docs/review/d1_corrected_val_r5_independent_qa_record.md")
REPORT_NAME = "eval_val_wp38_r1_r4_r6.json"
PINNED = {
    PREDECESSOR: "8d726cbdb31b610ca406e65d3231123d2099a8762cbdf300699dc188a17b1e40",
    PREDECESSOR_TEST: "9e8cce57d7a9ef4c42fc11aa016e4a692dbcb433e2ed9e59d8dd543086e4fde5",
    PREDECESSOR_REMEDIATION: "a8cac472e75843323a8c2a959c12058bdd59689e9f42eed4f1a26f0eb3f2c03d",
    PREDECESSOR_QA: "0544ebcaf84675a17ba23f71fddbac560e432ad66059926b6e035a93caa38660",
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
    return _load(REPO_ROOT / PREDECESSOR, "m1_corrected_val_r6_predecessor")


def verify_pins() -> None:
    for relative, expected in PINNED.items():
        path = REPO_ROOT / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned corrected-validation R5 evidence differs: {relative}")


def _same_inode(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _hash_fd(fd: int) -> str:
    os.lseek(fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    while chunk := os.read(fd, 1024 * 1024):
        digest.update(chunk)
    os.lseek(fd, 0, os.SEEK_SET)
    return digest.hexdigest()


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("short write while creating corrected-validation report")
        view = view[written:]


def _report_integration() -> ModuleType:
    module = load_predecessor()
    while not hasattr(module, "load_integration"):
        if not hasattr(module, "load_predecessor"):
            raise RuntimeError("cannot locate report directory authority")
        module = module.load_predecessor()
    return module.load_integration()


def _require_owned_final(root_fd: int, report_fd: int, owned: os.stat_result) -> None:
    descriptor = os.fstat(report_fd)
    path_info = os.stat(REPORT_NAME, dir_fd=root_fd, follow_symlinks=False)
    if not stat.S_ISREG(descriptor.st_mode) or descriptor.st_nlink != 1:
        raise RuntimeError("corrected-validation report descriptor is unsafe")
    if not stat.S_ISREG(path_info.st_mode) or path_info.st_nlink != 1:
        raise RuntimeError("corrected-validation report path is unsafe")
    if not _same_inode(descriptor, owned) or not _same_inode(path_info, owned):
        raise RuntimeError("corrected-validation report binding differs")


def _safe_write_report(run_dir: Path, payload: dict[str, Any]) -> Path:
    integration = _report_integration()
    root_fd, retained_fds, relations = integration._open_directory_chain(run_dir)
    report_fd: int | None = None
    primary_error: BaseException | None = None
    published = False
    try:
        integration._validate_relations(relations)
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        report_fd = os.open(REPORT_NAME, flags, 0o000, dir_fd=root_fd)
        owned = os.fstat(report_fd)
        if not stat.S_ISREG(owned.st_mode) or owned.st_nlink != 1:
            raise RuntimeError("corrected-validation report reservation is unsafe")
        data = (
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
            + "\n"
        ).encode()
        expected_hash = hashlib.sha256(data).hexdigest()
        _write_all(report_fd, data)
        os.fsync(report_fd)
        _require_owned_final(root_fd, report_fd, owned)
        if _hash_fd(report_fd) != expected_hash:
            raise RuntimeError("corrected-validation report hash differs")
        integration._validate_relations(relations)
        _require_owned_final(root_fd, report_fd, owned)

        # This permission transition is the publication event: until it succeeds, other normal
        # processes cannot read a partial report through the final pathname.
        os.fchmod(report_fd, 0o400)
        os.fsync(report_fd)
        _require_owned_final(root_fd, report_fd, owned)
        if _hash_fd(report_fd) != expected_hash:
            raise RuntimeError("published corrected-validation report hash differs")
        published = True
        return run_dir / REPORT_NAME
    except BaseException as error:
        primary_error = error
        if report_fd is not None:
            try:
                os.fchmod(report_fd, 0o000)
                os.fsync(report_fd)
            except OSError:
                pass
        raise
    finally:
        close_errors: list[BaseException] = []
        if report_fd is not None:
            try:
                os.close(report_fd)
            except OSError as error:
                close_errors.append(error)
        for fd in reversed(retained_fds):
            try:
                os.close(fd)
            except OSError as error:
                close_errors.append(error)
        if close_errors and primary_error is None and not published:
            raise RuntimeError("corrected-validation descriptor close failed") from close_errors[0]


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
    original_writer = predecessor._safe_write_report
    original_name = predecessor.REPORT_NAME
    predecessor._safe_write_report = _safe_write_report
    predecessor.REPORT_NAME = REPORT_NAME
    try:
        return predecessor.evaluate(
            weights,
            imgsz=imgsz,
            device=device,
            nms_iou=nms_iou,
            bootstrap=bootstrap,
        )
    finally:
        predecessor._safe_write_report = original_writer
        predecessor.REPORT_NAME = original_name


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
