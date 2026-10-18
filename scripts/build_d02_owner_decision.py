#!/usr/bin/env python3
# ruff: noqa: E501
"""Record and verify the owner's D-02 group-identity decision (append-only).

On 2026-10-17 the owner approved option D02-P1: the 54 WP31-R2 capture groups are the DATASET01
`group_id`. This builder writes an append-only decision overlay and a stem -> group_id registry
derived from the pinned, QA-passed WP31-R2 frames file. It does not modify any earlier package, the
historical decision template, or raw data, and it writes no split.

`check-candidate` rejects a candidate split (JSON object `{"splits": {"train": [...], ...}}`) whose
splits share a group_id, contain stem 0248, or reference an unknown stem.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DECISION_DATE = "2026-10-17"
SELECTED_OPTION = "D02-P1_WP31_R2_CAPTURE_GROUPS"
QUARANTINED_STEM = "0248"
EXPECTED_GROUPS = 54
EXPECTED_FRAMES = 3215

# Pinned, QA-passed WP31-R2 lineage (docs/review/wp31_r2_independent_qa_record.md).
PINNED_SOURCES = {
    "docs/review/generated/wp31_r2_group_id_frames.csv": "aea7ea144f4ec389cab8cca70b28ae21d4b21918ef089af16cf3580e828fca7e",
    "docs/review/generated/wp31_r2_group_id_groups.csv": "dbb0cc1a02d4256856b3cecb4f7d811e15c91951e4888f54aa43e89df3b87f27",
    "docs/review/generated/wp31_r2_group_id_manifest.json": "c17f794c33dbaf0a5ffaa3433dea1ff5c2353cb0a253420b92a21a3cc918815b",
    "docs/review/wp31_r2_group_id_proposal_report.md": "2c3db0e17144f198fb58c50835c94a2d3a8300a80ecee997bab2dca01651d0e6",
    "docs/review/wp31_r2_independent_qa_record.md": "95327e0ad97822d7f5212ef2267a5441848794a5f182f3e00dca8b7f77993c4d",
    "scripts/build_wp31_r2_group_id_proposal.py": "bde68d64b07a13b82ef07706fb2459ce185c5744a9281cabc7600ac1f7ec3796",
    "tests/test_wp31_r2_group_id_proposal.py": "0dca3e2b3774c1d7dc7732f45d2e61ef421829e41928ce77f05580d92dee5ea5",
}
FRAMES = Path("docs/review/generated/wp31_r2_group_id_frames.csv")
OVERLAY_PATH = Path("docs/review/generated/d02_owner_decision_overlay.json")
REGISTRY_PATH = Path("docs/review/generated/d02_group_id_registry.csv")
RECORD_PATH = Path("docs/review/d02_owner_decision_record.md")
REGISTRY_FIELDS = ["stem", "group_id", "vendor_split", "class_ids", "box_count"]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verify_pins(repo_root: Path) -> None:
    for relative, digest in PINNED_SOURCES.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or sha256_bytes(path.read_bytes()) != digest:
            raise ValueError(f"pinned D-02 source changed: {relative}")


def registry_rows(repo_root: Path) -> list[dict[str, Any]]:
    with (repo_root / FRAMES).open(newline="", encoding="utf-8") as handle:
        frames = list(csv.DictReader(handle))
    rows = [
        {
            "stem": frame["stem"],
            "group_id": frame["capture_group_id"],
            "vendor_split": frame["split"],
            "class_ids": frame["class_ids"],
            "box_count": frame["box_count"],
        }
        for frame in frames
        if frame["stem"] != QUARANTINED_STEM
    ]
    if any(not row["group_id"] for row in rows):
        raise ValueError("every non-quarantined stem must have a group_id")
    if len(rows) != EXPECTED_FRAMES or len({row["group_id"] for row in rows}) != EXPECTED_GROUPS:
        raise ValueError("D-02 registry must hold 3,215 stems in exactly 54 groups")
    return rows


def render(repo_root: Path) -> dict[Path, bytes]:
    verify_pins(repo_root)
    rows = registry_rows(repo_root)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=REGISTRY_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    registry = buffer.getvalue().encode("utf-8")
    sizes = sorted(Counter(row["group_id"] for row in rows).values(), reverse=True)
    overlay = {
        "schema_version": 1,
        "overlay_type": "APPEND_ONLY_OWNER_DECISION_RESOLUTION",
        "decision": {
            "decision_id": "D-02",
            "topic": "Group identity",
            "selected_option": SELECTED_OPTION,
            "status": "OWNER_APPROVED",
            "authority": "DIRECT_OWNER_APPROVAL_IN_PM_SESSION",
            "decision_date": DECISION_DATE,
            "decision_timezone": "Asia/Ho_Chi_Minh",
        },
        "scope": {
            "group_level": "capture",
            "group_count": len(sizes),
            "grouped_stems": len(rows),
            "largest_group_sizes": sizes[:5],
            "quarantined_stem_without_group": QUARANTINED_STEM,
            "scene_level_adopted": False,
        },
        "known_limits": [
            "Groups come from provisional AI visual review (PM plus independent QA sessions), not human review or creator metadata.",
            "Cross-block linking covered near-identical views only; neither level is proven leak-free.",
            "The 12 negative runs are bridged at capture level but were never reviewed visually.",
        ],
        "lineage": PINNED_SOURCES,
        "registry_sha256": sha256_bytes(registry),
        "enforcement": {
            "split_unit": "group_id",
            "same_group_across_splits": "REJECT",
            "quarantined_stem_in_candidate": "REJECT",
            "missing_or_invalid_overlay_policy": "FAIL_CLOSED",
        },
        "governance": {
            "g06_group_id": "OWNER_APPROVED_D02_P1",
            "gate0": "BLOCKED",
            "remaining_pending_decisions": ["D-01", "D-03", "D-04", "D-05"],
            "split_authorized": False,
            "training_authorized": False,
        },
        "historical_decision_file_mutated": False,
    }
    record = f"""# D-02 owner decision — group identity

Status: `OWNER_APPROVED`
Decision date: `{DECISION_DATE}` (`Asia/Ho_Chi_Minh`)
Selected option: `{SELECTED_OPTION}`

The owner approved option D02-P1: the {len(sizes)} capture groups of M0-WP31-R2 (independent QA
PASS, `docs/review/wp31_r2_independent_qa_record.md`) are the DATASET01 `group_id`. Scene groups
(D02-P2) were not adopted.

## Registry

- `{REGISTRY_PATH.as_posix()}`: one row per stem, {len(rows)} stems, {len(sizes)} groups
  (largest {sizes[:5]}). Stem `{QUARANTINED_STEM}` stays quarantined and has no group.
- Overlay: `{OVERLAY_PATH.as_posix()}`. Lineage pins the WP31-R2 package, its QA record, builder
  and test by SHA-256.

## Enforcement

`scripts/build_d02_owner_decision.py check-candidate --candidate <file>` rejects a candidate split
that places one `group_id` in two splits, contains stem `{QUARANTINED_STEM}`, or references an
unknown stem. Missing or tampered inputs fail closed.

## Known limits accepted by the owner

- Groups come from provisional AI visual review, not human review or creator metadata.
- Cross-block linking covered near-identical views only; the grouping is not proven leak-free.
- The 12 negative runs are bridged at capture level but were never reviewed visually.

## Governance

D-02 is resolved and G0.6 is satisfied by this decision. Gate 0 remains BLOCKED because D-01,
D-03, D-04 and D-05 are still pending and no group-aware split (G0.7) exists yet.
`split_authorized=false` and `training_authorized=false`. No earlier package, the historical
decision template or raw data was changed.
"""
    return {
        REGISTRY_PATH: registry,
        OVERLAY_PATH: (json.dumps(overlay, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        RECORD_PATH: record.encode("utf-8"),
    }


def build(repo_root: Path) -> dict[str, Any]:
    artifacts = render(repo_root)
    for path, payload in artifacts.items():
        (repo_root / path).parent.mkdir(parents=True, exist_ok=True)
        (repo_root / path).write_bytes(payload)
    return {"status": "D02_OWNER_APPROVED_RECORDED", "artifacts": len(artifacts)}


def verify(repo_root: Path) -> dict[str, Any]:
    try:
        expected = render(repo_root)
    except (OSError, KeyError, ValueError) as exc:
        return {"valid": False, "errors": [str(exc)], "status": "D02_OWNER_APPROVED"}
    errors = [
        f"artifact differs from deterministic re-derivation: {path.as_posix()}"
        for path, payload in expected.items()
        if not (repo_root / path).is_file() or (repo_root / path).read_bytes() != payload
    ]
    return {"valid": not errors, "errors": errors, "artifact_count": len(expected), "status": "D02_OWNER_APPROVED"}


def check_candidate(repo_root: Path, candidate: Path) -> dict[str, Any]:
    result = verify(repo_root)
    if not result["valid"]:
        return {"accepted": False, "errors": ["D-02 decision package invalid", *result["errors"]]}
    with (repo_root / REGISTRY_PATH).open(newline="", encoding="utf-8") as handle:
        group_of = {row["stem"]: row["group_id"] for row in csv.DictReader(handle)}
    splits = json.loads(candidate.read_text(encoding="utf-8")).get("splits")
    if not isinstance(splits, dict) or not splits:
        return {"accepted": False, "errors": ["candidate must be an object with non-empty 'splits'"]}
    errors: list[str] = []
    owner: dict[str, str] = {}
    for split, stems in splits.items():
        for stem in stems:
            if stem == QUARANTINED_STEM:
                errors.append(f"quarantined stem {stem} in split {split}")
                continue
            group = group_of.get(stem)
            if group is None:
                errors.append(f"unknown stem {stem} in split {split}")
                continue
            if owner.setdefault(group, split) != split:
                errors.append(f"group {group} appears in both {owner[group]} and {split}")
    return {"accepted": not errors, "errors": sorted(set(errors))[:50]}


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify", "check-candidate"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    commands.choices["check-candidate"].add_argument("--candidate", type=Path, required=True)
    args = root.parse_args(argv)
    repo_root = args.repo_root.resolve()
    if args.command == "build":
        result = build(repo_root)
        ok = True
    elif args.command == "verify":
        result = verify(repo_root)
        ok = result["valid"]
    else:
        result = check_candidate(repo_root, args.candidate)
        ok = result["accepted"]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
