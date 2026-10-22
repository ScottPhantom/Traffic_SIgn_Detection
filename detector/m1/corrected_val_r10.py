"""JSON-normalized intended-payload successor for corrected-validation R9.

R10 preserves R9's intended canonical-byte authority while comparing parsed documents only after
the intended bytes have undergone the same JSON normalization as the descriptor-consumed bytes.
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
PREDECESSOR = Path("detector/m1/corrected_val_r9.py")
PREDECESSOR_TEST = Path("detector/tests/test_corrected_val_r9.py")
PREDECESSOR_REMEDIATION = Path("docs/review/d1_corrected_val_r9_qa_remediation_report.md")
PREDECESSOR_QA = Path("docs/review/d1_corrected_val_r9_independent_qa_record.md")
PREDECESSOR_LIVE_FAILURE = Path(
    "docs/review/d1_corrected_val_r9_live_execution_failure_record.md"
)
REPORT_NAME = "eval_val_wp38_r1_r4_r10.json"
PINNED = {
    PREDECESSOR: "008a8d335ce2a05a886c69ca2fc3e54d5265338138ec75786d11317206009fa2",
    PREDECESSOR_TEST: "7d57209a63538f2713296ecfbd82e325b3531f27f98997d1e195440f9e9b3a34",
    PREDECESSOR_REMEDIATION: "85f977903ebd5fe770c4ed941b02068d6297f56697bb664f3b20b8b674195f0c",
    PREDECESSOR_QA: "22b487b9504e622c2850902f6512b4ea4a641aabbca239bfd3c97b52ea26878e",
    PREDECESSOR_LIVE_FAILURE: "35c9e218c5783c674a339eb7679ee8534ed13b534d386281b95fb4126b052193",
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
    return _load(REPO_ROOT / PREDECESSOR, "m1_corrected_val_r10_predecessor")


def verify_pins() -> None:
    for relative, expected in PINNED.items():
        path = REPO_ROOT / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned corrected-validation R9 evidence differs: {relative}")


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
    """Bind exact intended bytes and compare documents in canonical JSON space."""
    verify_pins()
    intended = _canonical_bytes(payload)
    intended_hash = hashlib.sha256(intended).hexdigest()
    intended_document = json.loads(intended)
    predecessor_r9 = load_predecessor()
    predecessor_r8 = predecessor_r9.load_predecessor()
    original_name = predecessor_r8.REPORT_NAME
    predecessor_r8.REPORT_NAME = REPORT_NAME
    try:
        binding = predecessor_r8._safe_write_report(run_dir, payload)
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
        consumed_bytes, consumed_document = predecessor_r8._open_bound_report(
            run_dir, binding_dict
        )
        if consumed_bytes != intended:
            raise RuntimeError(
                "corrected-validation consumed bytes differ from intended payload"
            )
        if consumed_document != intended_document:
            raise RuntimeError(
                "corrected-validation consumed document differs from normalized intended payload"
            )
        return binding
    finally:
        predecessor_r8.REPORT_NAME = original_name


def consume_report(run_dir: Path, binding: dict[str, Any]) -> dict[str, Any]:
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
        raise RuntimeError("corrected-validation normalized binding was not captured")
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
        "report_compared_in_json_space": True,
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
