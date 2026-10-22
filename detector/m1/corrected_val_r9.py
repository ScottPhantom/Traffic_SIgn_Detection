"""Intended-payload-bound successor for QA-failed corrected-validation R8.

R9 preserves R8's descriptor-bound content authority and adds the missing authority: the
canonical bytes requested by the evaluator.  A report is accepted only when the binding issued
after publication and the bytes consumed through that binding both match the intended payload.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from m1 import contract

REPO_ROOT = contract.REPO_ROOT
PREDECESSOR = Path("detector/m1/corrected_val_r8.py")
PREDECESSOR_TEST = Path("detector/tests/test_corrected_val_r8.py")
PREDECESSOR_REMEDIATION = Path("docs/review/d1_corrected_val_r8_qa_remediation_report.md")
PREDECESSOR_QA = Path("docs/review/d1_corrected_val_r8_independent_qa_record.md")
REPORT_NAME = "eval_val_wp38_r1_r4_r9.json"
PINNED = {
    PREDECESSOR: "8240f42a82e6ce9712e3e130413d986ed5c8cb83d6bd1de821b40713b6e2dc13",
    PREDECESSOR_TEST: "e2b999364d763a8a9f20dc57b80adac7c0e524021f24eebcffc67e931b6294bc",
    PREDECESSOR_REMEDIATION: "d09abc164d7edbd8f9ae337107ff3e50e9a0c95e2701f56c8209fe1498294c3b",
    PREDECESSOR_QA: "a616a232690f607bb528308b428d55c9c1595c82461078a74cc6327a1a7c3684",
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
    return _load(REPO_ROOT / PREDECESSOR, "m1_corrected_val_r9_predecessor")


def verify_pins() -> None:
    for relative, expected in PINNED.items():
        path = REPO_ROOT / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned corrected-validation R8 evidence differs: {relative}")


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()


def _safe_write_report(run_dir: Path, payload: dict[str, Any]) -> Any:
    """Publish via R8, then bind the publication to the exact requested bytes."""
    verify_pins()
    intended = _canonical_bytes(payload)
    intended_hash = hashlib.sha256(intended).hexdigest()
    predecessor = load_predecessor()
    original_name = predecessor.REPORT_NAME
    predecessor.REPORT_NAME = REPORT_NAME
    try:
        binding = predecessor._safe_write_report(run_dir, payload)
        binding_dict = binding.to_dict()
        expected_authority = {
            "bytes": len(intended),
            "content_uri": f"sha256:{intended_hash}",
            "locator": REPORT_NAME,
            "sha256": intended_hash,
        }
        if any(binding_dict.get(key) != value for key, value in expected_authority.items()):
            raise RuntimeError(
                "corrected-validation published binding differs from intended payload"
            )
        consumed_bytes, consumed_document = predecessor._open_bound_report(
            run_dir, binding_dict
        )
        if consumed_bytes != intended:
            raise RuntimeError(
                "corrected-validation consumed bytes differ from intended payload"
            )
        if consumed_document != payload:
            raise RuntimeError(
                "corrected-validation consumed document differs from intended payload"
            )
        return binding
    finally:
        predecessor.REPORT_NAME = original_name


def consume_report(run_dir: Path, binding: dict[str, Any]) -> dict[str, Any]:
    """Consume only through R8's strict binding while using R9's locator contract."""
    verify_pins()
    predecessor = load_predecessor()
    original_name = predecessor.REPORT_NAME
    predecessor.REPORT_NAME = REPORT_NAME
    try:
        return predecessor.consume_report(run_dir, binding)
    finally:
        predecessor.REPORT_NAME = original_name


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

    def writer(run_dir: Path, payload: dict[str, Any]) -> Any:
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
        raise RuntimeError("corrected-validation intended-payload binding was not captured")
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
        "report_matches_intended_payload": True,
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
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
