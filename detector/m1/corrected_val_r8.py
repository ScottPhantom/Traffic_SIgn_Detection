"""Content-bound corrected-validation successor for QA-failed evaluator R7.

R8 stops returning a filesystem path as report authority.  Publication still inherits R7's
defences, but the public contract is a strict content binding.  The evaluator reopens the locator,
verifies that binding and consumes the JSON through the same descriptor before returning metrics.
Any later consumer must repeat that operation; the locator alone is never evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from m1 import contract

REPO_ROOT = contract.REPO_ROOT
PREDECESSOR = Path("detector/m1/corrected_val_r7.py")
PREDECESSOR_TEST = Path("detector/tests/test_corrected_val_r7.py")
PREDECESSOR_REMEDIATION = Path("docs/review/d1_corrected_val_r7_qa_remediation_report.md")
PREDECESSOR_QA = Path("docs/review/d1_corrected_val_r7_independent_qa_record.md")
REPORT_NAME = "eval_val_wp38_r1_r4_r8.json"
BINDING_KEYS = {
    "bytes",
    "content_uri",
    "device",
    "inode",
    "is_regular",
    "locator",
    "locator_policy",
    "mode",
    "nlink",
    "schema_version",
    "sealed_test_accessed",
    "sha256",
}
PINNED = {
    PREDECESSOR: "3ec7a92fc49817af71273575f36df3471bc3d28276f3dc11f37ccd7f40a9ac29",
    PREDECESSOR_TEST: "2e8962702e60e60f644945334dedef5950375618211731836bd083a5f17f7290",
    PREDECESSOR_REMEDIATION: "8fd4faf0fe9a066c79ec497f130d45667104f190563f942b953011b4b1ffdfcf",
    PREDECESSOR_QA: "b14e70ea8cd3dade7a4f2f5528c59435204f2f3e3a7e38ee4ff3cd70d9950b3c",
}


@dataclass(frozen=True)
class ReportBinding:
    """Immutable identity returned instead of a mutable path authority."""

    schema_version: int
    content_uri: str
    sha256: str
    bytes: int
    locator: str
    locator_policy: str
    device: int
    inode: int
    mode: int
    nlink: int
    is_regular: bool
    sealed_test_accessed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __str__(self) -> str:
        return self.content_uri


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
    return _load(REPO_ROOT / PREDECESSOR, "m1_corrected_val_r8_predecessor")


def verify_pins() -> None:
    for relative, expected in PINNED.items():
        path = REPO_ROOT / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned corrected-validation R7 evidence differs: {relative}")


def _integration() -> ModuleType:
    predecessor_r7 = load_predecessor()
    predecessor_r6 = predecessor_r7.load_predecessor()
    return predecessor_r6._report_integration()


def _read_all(fd: int) -> bytes:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while chunk := os.read(fd, 1024 * 1024):
        chunks.append(chunk)
    os.lseek(fd, 0, os.SEEK_SET)
    return b"".join(chunks)


def _same_inode(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _validate_binding(binding: dict[str, Any]) -> None:
    if set(binding) != BINDING_KEYS:
        raise RuntimeError("corrected-validation report binding schema differs")
    integer_fields = ("schema_version", "bytes", "device", "inode", "mode", "nlink")
    if any(type(binding[field]) is not int for field in integer_fields):
        raise RuntimeError("corrected-validation report binding integer type differs")
    string_fields = ("content_uri", "sha256", "locator", "locator_policy")
    if any(type(binding[field]) is not str for field in string_fields):
        raise RuntimeError("corrected-validation report binding string type differs")
    if type(binding["is_regular"]) is not bool or binding["is_regular"] is not True:
        raise RuntimeError("corrected-validation regular-file binding differs")
    if (
        type(binding["sealed_test_accessed"]) is not bool
        or binding["sealed_test_accessed"] is not False
    ):
        raise RuntimeError("corrected-validation sealed-test binding differs")
    digest = binding["sha256"]
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise RuntimeError("corrected-validation report digest differs")
    if (
        binding["schema_version"] != 1
        or binding["content_uri"] != f"sha256:{digest}"
        or binding["bytes"] <= 0
        or binding["locator"] != REPORT_NAME
        or binding["locator_policy"] != "REOPEN_AND_VERIFY_BEFORE_USE"
        or binding["device"] < 0
        or binding["inode"] <= 0
        or binding["mode"] != 0o400
        or binding["nlink"] != 1
    ):
        raise RuntimeError("corrected-validation report binding value differs")


def _open_bound_report(run_dir: Path, binding: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    _validate_binding(binding)
    integration = _integration()
    root_fd, retained_fds, relations = integration._open_directory_chain(run_dir)
    report_fd: int | None = None
    try:
        integration._validate_relations(relations)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        report_fd = os.open(binding["locator"], flags, dir_fd=root_fd)
        info = os.fstat(report_fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RuntimeError("bound corrected-validation report is unsafe")
        if (
            info.st_dev != binding["device"]
            or info.st_ino != binding["inode"]
            or stat.S_IMODE(info.st_mode) != binding["mode"]
            or info.st_nlink != binding["nlink"]
        ):
            raise RuntimeError("corrected-validation descriptor binding differs")
        payload = _read_all(report_fd)
        if len(payload) != binding["bytes"]:
            raise RuntimeError("corrected-validation bound size differs")
        if hashlib.sha256(payload).hexdigest() != binding["sha256"]:
            raise RuntimeError("corrected-validation bound hash differs")
        final = os.stat(binding["locator"], dir_fd=root_fd, follow_symlinks=False)
        if not _same_inode(info, final):
            raise RuntimeError("corrected-validation bound locator differs")
        integration._validate_relations(relations)
        document = json.loads(payload)
        if not isinstance(document, dict):
            raise RuntimeError("corrected-validation report payload is not an object")
        if document.get("test_included") is not False:
            raise RuntimeError("corrected-validation report includes test")
        if document.get("sealed_test_accessed") is not False:
            raise RuntimeError("corrected-validation report accessed sealed test")
        return payload, document
    finally:
        if report_fd is not None:
            os.close(report_fd)
        for fd in reversed(retained_fds):
            os.close(fd)


def _bind_report(run_dir: Path) -> ReportBinding:
    integration = _integration()
    root_fd, retained_fds, relations = integration._open_directory_chain(run_dir)
    report_fd: int | None = None
    try:
        integration._validate_relations(relations)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        report_fd = os.open(REPORT_NAME, flags, dir_fd=root_fd)
        info = os.fstat(report_fd)
        payload = _read_all(report_fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RuntimeError("corrected-validation report cannot be bound")
        if stat.S_IMODE(info.st_mode) != 0o400:
            raise RuntimeError("corrected-validation report mode cannot be bound")
        digest = hashlib.sha256(payload).hexdigest()
        binding = ReportBinding(
            schema_version=1,
            content_uri=f"sha256:{digest}",
            sha256=digest,
            bytes=len(payload),
            locator=REPORT_NAME,
            locator_policy="REOPEN_AND_VERIFY_BEFORE_USE",
            device=info.st_dev,
            inode=info.st_ino,
            mode=stat.S_IMODE(info.st_mode),
            nlink=info.st_nlink,
            is_regular=True,
            sealed_test_accessed=False,
        )
        _validate_binding(binding.to_dict())
        final = os.stat(REPORT_NAME, dir_fd=root_fd, follow_symlinks=False)
        if not _same_inode(info, final):
            raise RuntimeError("corrected-validation report binding locator differs")
        integration._validate_relations(relations)
        return binding
    finally:
        if report_fd is not None:
            os.close(report_fd)
        for fd in reversed(retained_fds):
            os.close(fd)


def _safe_write_report(run_dir: Path, payload: dict[str, Any]) -> ReportBinding:
    predecessor = load_predecessor()
    original_name = predecessor.REPORT_NAME
    predecessor.REPORT_NAME = REPORT_NAME
    try:
        predecessor._safe_write_report(run_dir, payload)
    finally:
        predecessor.REPORT_NAME = original_name
    return _bind_report(run_dir)


def consume_report(run_dir: Path, binding: dict[str, Any]) -> dict[str, Any]:
    """Reopen, verify and parse the locator through one retained descriptor."""
    _payload, document = _open_bound_report(run_dir, binding)
    return document


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
    captured: dict[str, Any] = {}

    def writer(run_dir: Path, payload: dict[str, Any]) -> ReportBinding:
        binding = _safe_write_report(run_dir, payload)
        captured["run_dir"] = run_dir
        captured["binding"] = binding.to_dict()
        return binding

    original_writer = predecessor._safe_write_report
    original_name = predecessor.REPORT_NAME
    predecessor._safe_write_report = writer
    predecessor.REPORT_NAME = REPORT_NAME
    try:
        inherited = predecessor.evaluate(
            weights,
            imgsz=imgsz,
            device=device,
            nms_iou=nms_iou,
            bootstrap=bootstrap,
        )
    finally:
        predecessor._safe_write_report = original_writer
        predecessor.REPORT_NAME = original_name
    if set(captured) != {"run_dir", "binding"}:
        raise RuntimeError("corrected-validation report binding was not captured")
    binding = captured["binding"]
    if inherited.get("report") != binding["content_uri"]:
        raise RuntimeError("inherited corrected-validation report authority differs")
    report = consume_report(captured["run_dir"], binding)
    return {
        "status": report["status"],
        "report": binding["content_uri"],
        "report_binding": binding,
        "map50": report["map50"],
        "map50_95": report["map50_95"],
        "operating_point": report["operating_point"],
        "single_seed_checks_passed": report["gates"]["single_seed_checks_passed"],
        "report_consumed_from_verified_descriptor": True,
        "use_time_binding_verified": True,
        "sealed_test_accessed": False,
    }


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
