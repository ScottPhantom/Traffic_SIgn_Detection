from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_d01_owner_decision", REPO_ROOT / "scripts/build_d01_owner_decision.py"
)
assert SPEC is not None and SPEC.loader is not None
d01 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = d01
SPEC.loader.exec_module(d01)


def test_decision_package_verifies_and_keeps_boundary() -> None:
    assert d01.verify(REPO_ROOT)["valid"] is True
    overlay = json.loads((REPO_ROOT / d01.OVERLAY_PATH).read_text(encoding="utf-8"))
    assert overlay["decision"]["status"] == "OWNER_APPROVED_RISK_ACCEPTED"
    assert overlay["governance"]["public_redistribution_authorized"] is False
    assert overlay["governance"]["training_authorized"] is False
    assert overlay["governance"]["gate0"] == "BLOCKED"


def test_changed_provenance_evidence_fails_closed(tmp_path: Path) -> None:
    for relative in d01.PINNED_SOURCES:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / relative).read_bytes())
    d01.verify_pins(tmp_path)
    report = tmp_path / "docs/review/wp3_provenance_and_fallback_report.md"
    report.write_text(report.read_text(encoding="utf-8") + "\nedited\n", encoding="utf-8")
    with pytest.raises(ValueError, match="pinned D-01 source changed"):
        d01.verify_pins(tmp_path)
