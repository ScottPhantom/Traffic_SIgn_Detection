#!/usr/bin/env python3
# ruff: noqa: E501
"""Record and verify the owner's D-01 provenance/license decision (append-only).

On 2026-10-17 the owner chose to accept the license risk instead of waiting for the dataset
author. The source candidate (Hugging Face `thanhhiepvos/vietnam_traffic_sign@d869116`) declares
CC-BY-SA 3.0 in repository metadata and CC-BY-SA 4.0 in card prose, and image ownership is
unknown. The decision applies the stricter, compatible obligations of both versions. It does not
modify the WP3 provenance package, the historical decision template or raw data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DECISION_DATE = "2026-10-17"
SELECTED_OPTION = "D01-RISK_ACCEPTED_CC_BY_SA_STRICTEST_TERMS"
SOURCE = "huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign@d869116"
ARCHIVE_SHA256 = "052bc980a7206f8ddd1ec2e59098dbd60a42036d3c7f7384ace4fe6416cbaa76"

PINNED_SOURCES = {
    "results/data_audit/DATASET01_052bc980a7206f8d/provenance_evidence.json": "e61ecf927d0ec13b8a79570c50ee6f4b37dfa11369ee3398054987339814549a",
    "docs/review/wp3_provenance_and_fallback_report.md": "02cefe6478da62f0524f74ff3684f0a7d60e05c3e1a23a72516c7febc2b16a26",
    "docs/review/dataset_owner_outreach_draft.md": "1765ea8c0f74e9be93e9e0d073c6f2f4c25a67e4cfea843da1cdd9a0ef5afd25",
}
OVERLAY_PATH = Path("docs/review/generated/d01_owner_decision_overlay.json")
RECORD_PATH = Path("docs/review/d01_owner_decision_record.md")

CONDITIONS = [
    "Use DATASET01 for this project's research, coursework and simulation only.",
    "Attribute the source in every report, dataset card, model card and release: "
    f"{SOURCE}, CC-BY-SA, with the archive SHA-256.",
    "Share-alike: any redistributed derivative of the images or labels (crops, relabels, splits) "
    "is released only under CC-BY-SA 4.0, which satisfies both declared versions.",
    "Do not redistribute the raw images or labels outside the project until ownership is clarified.",
    "Treat trained model weights as possibly subject to share-alike; attribute the dataset in any "
    "model release and re-check before any public or commercial release.",
    "Re-open D-01 immediately if the author answers, the source changes, or a takedown or "
    "ownership claim is received.",
]
RESIDUAL_RISKS = [
    "License version conflict (3.0 metadata vs 4.0 card prose) is unresolved by the author.",
    "Ownership of the original images and the author's authority to license them are unknown.",
    "Share-alike scope for trained model weights is legally uncertain.",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verify_pins(repo_root: Path) -> None:
    for relative, digest in PINNED_SOURCES.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or sha256_bytes(path.read_bytes()) != digest:
            raise ValueError(f"pinned D-01 source changed: {relative}")
    evidence = json.loads((repo_root / "results/data_audit/DATASET01_052bc980a7206f8d/provenance_evidence.json").read_text(encoding="utf-8"))
    text = json.dumps(evidence)
    if "cc-by-sa-3.0" not in text or "CC-BY-SA-4.0" not in text:
        raise ValueError("provenance evidence no longer records the 3.0/4.0 conflict")


def render(repo_root: Path) -> dict[Path, bytes]:
    verify_pins(repo_root)
    overlay = {
        "schema_version": 1,
        "overlay_type": "APPEND_ONLY_OWNER_DECISION_RESOLUTION",
        "decision": {
            "decision_id": "D-01",
            "topic": "Provenance / license",
            "selected_option": SELECTED_OPTION,
            "status": "OWNER_APPROVED_RISK_ACCEPTED",
            "authority": "DIRECT_OWNER_APPROVAL_IN_PM_SESSION",
            "decision_date": DECISION_DATE,
            "decision_timezone": "Asia/Ho_Chi_Minh",
        },
        "source": {"candidate": SOURCE, "archive_sha256": ARCHIVE_SHA256, "declared_licenses": ["CC-BY-SA-3.0", "CC-BY-SA-4.0"]},
        "conditions": CONDITIONS,
        "residual_risks": RESIDUAL_RISKS,
        "lineage": PINNED_SOURCES,
        "governance": {
            "g01_license": "OWNER_RISK_ACCEPTED",
            "gate0": "BLOCKED",
            "remaining_pending_decisions": ["D-03", "D-04", "D-05"],
            "public_redistribution_authorized": False,
            "split_authorized": False,
            "training_authorized": False,
        },
        "historical_decision_file_mutated": False,
    }
    conditions = "\n".join(f"{index}. {item}" for index, item in enumerate(CONDITIONS, start=1))
    risks = "\n".join(f"- {item}" for item in RESIDUAL_RISKS)
    record = f"""# D-01 owner decision — provenance and license

Status: `OWNER_APPROVED_RISK_ACCEPTED`
Decision date: `{DECISION_DATE}` (`Asia/Ho_Chi_Minh`)
Selected option: `{SELECTED_OPTION}`

The owner chose to accept the license risk for DATASET01 instead of waiting for the dataset
author. Source candidate: `{SOURCE}`, archive SHA-256 `{ARCHIVE_SHA256}`. The repository
metadata declares CC-BY-SA 3.0 and the card prose declares CC-BY-SA 4.0; image ownership is unknown
(`docs/review/wp3_provenance_and_fallback_report.md`). The decision applies the stricter,
compatible obligations of both versions.

## Conditions

{conditions}

## Residual risks accepted by the owner

{risks}

## Governance

G0.1 is satisfied by owner risk acceptance, not by author confirmation. Gate 0 remains BLOCKED
because D-03, D-04 and D-05 are pending and no group-aware split (G0.7) exists yet. Public
redistribution, split generation and training are not authorized by this record.
"""
    return {
        OVERLAY_PATH: (json.dumps(overlay, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"),
        RECORD_PATH: record.encode("utf-8"),
    }


def build(repo_root: Path) -> dict[str, Any]:
    artifacts = render(repo_root)
    for path, payload in artifacts.items():
        (repo_root / path).parent.mkdir(parents=True, exist_ok=True)
        (repo_root / path).write_bytes(payload)
    return {"status": "D01_OWNER_RISK_ACCEPTED_RECORDED", "artifacts": len(artifacts)}


def verify(repo_root: Path) -> dict[str, Any]:
    try:
        expected = render(repo_root)
    except (OSError, KeyError, ValueError) as exc:
        return {"valid": False, "errors": [str(exc)], "status": "D01_OWNER_RISK_ACCEPTED"}
    errors = [
        f"artifact differs from deterministic re-derivation: {path.as_posix()}"
        for path, payload in expected.items()
        if not (repo_root / path).is_file() or (repo_root / path).read_bytes() != payload
    ]
    return {"valid": not errors, "errors": errors, "artifact_count": len(expected), "status": "D01_OWNER_RISK_ACCEPTED"}


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        commands.add_parser(name).add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = root.parse_args(argv)
    result = build(args.repo_root.resolve()) if args.command == "build" else verify(args.repo_root.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command == "build" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
