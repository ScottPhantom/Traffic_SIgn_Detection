"""Public-path round-trip successor for QA-failed corrected-validation evaluator R6.

R7 preserves R6's descriptor-first publication, then independently reopens the published report
through both fresh retained-directory authority and the public lexical path.  It returns success
only when both descriptors identify the same single-link read-only inode with the exact payload
hash and the fresh directory relations still validate.
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
PREDECESSOR = Path("detector/m1/corrected_val_r6.py")
PREDECESSOR_TEST = Path("detector/tests/test_corrected_val_r6.py")
PREDECESSOR_REMEDIATION = Path("docs/review/d1_corrected_val_r6_qa_remediation_report.md")
PREDECESSOR_QA = Path("docs/review/d1_corrected_val_r6_independent_qa_record.md")
REPORT_NAME = "eval_val_wp38_r1_r4_r7.json"
PINNED = {
    PREDECESSOR: "fe7280b194f9f39da4db917717df7e3234fa083610c3dbd6e87f41f5cae389de",
    PREDECESSOR_TEST: "768ca31abc71f6f630c42fcfd9b37019f479089cd3768a75c687351b8dd31414",
    PREDECESSOR_REMEDIATION: "ee745b0ea8b801452ed00619a766e15271f0c9aa93973d311fbea3aa768eb136",
    PREDECESSOR_QA: "10605012f01234c7a1ac6bb7a4c72b61e0045daec6fb0d7780948e567f8d296b",
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
    return _load(REPO_ROOT / PREDECESSOR, "m1_corrected_val_r7_predecessor")


def verify_pins() -> None:
    for relative, expected in PINNED.items():
        path = REPO_ROOT / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned corrected-validation R6 evidence differs: {relative}")


def _same_inode(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _hash_fd(fd: int) -> str:
    os.lseek(fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    while chunk := os.read(fd, 1024 * 1024):
        digest.update(chunk)
    os.lseek(fd, 0, os.SEEK_SET)
    return digest.hexdigest()


def _expected_bytes(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode()


def _verify_public_round_trip(run_dir: Path, payload: dict[str, Any]) -> None:
    predecessor = load_predecessor()
    integration = predecessor._report_integration()
    root_fd, retained_fds, relations = integration._open_directory_chain(run_dir)
    retained_report_fd: int | None = None
    lexical_report_fd: int | None = None
    try:
        integration._validate_relations(relations)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        retained_report_fd = os.open(REPORT_NAME, flags, dir_fd=root_fd)
        lexical_report_fd = os.open(run_dir / REPORT_NAME, flags)
        retained = os.fstat(retained_report_fd)
        lexical = os.fstat(lexical_report_fd)
        expected_hash = hashlib.sha256(_expected_bytes(payload)).hexdigest()
        for info in (retained, lexical):
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise RuntimeError("public corrected-validation report is unsafe")
            if stat.S_IMODE(info.st_mode) != 0o400:
                raise RuntimeError("public corrected-validation report mode differs")
        if not _same_inode(retained, lexical):
            raise RuntimeError("public corrected-validation report path differs")
        if _hash_fd(retained_report_fd) != expected_hash:
            raise RuntimeError("retained corrected-validation report hash differs")
        if _hash_fd(lexical_report_fd) != expected_hash:
            raise RuntimeError("public corrected-validation report hash differs")
        integration._validate_relations(relations)
        final_path = os.stat(REPORT_NAME, dir_fd=root_fd, follow_symlinks=False)
        if not _same_inode(final_path, retained):
            raise RuntimeError("final corrected-validation report binding differs")
    finally:
        if lexical_report_fd is not None:
            os.close(lexical_report_fd)
        if retained_report_fd is not None:
            os.close(retained_report_fd)
        for fd in reversed(retained_fds):
            os.close(fd)


def _safe_write_report(run_dir: Path, payload: dict[str, Any]) -> Path:
    predecessor = load_predecessor()
    original_name = predecessor.REPORT_NAME
    predecessor.REPORT_NAME = REPORT_NAME
    try:
        output = predecessor._safe_write_report(run_dir, payload)
    finally:
        predecessor.REPORT_NAME = original_name
    _verify_public_round_trip(run_dir, payload)
    return output


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
