# ruff: noqa: E501
"""Build, verify, and enforce the M0-WP10 G0.4 owner quarantine overlay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PACKAGE_STATUS = "M0_WP10_AWAITING_QA_OWNER_APPROVED_QUARANTINE_ENFORCEMENT"
DECISION_ID = "G0.4-bbox-0248"
DECISION_STATUS = "OWNER_APPROVED"
SELECTED_OPTION = "APPROVED_QUARANTINE"
QUARANTINED_STEM = "0248"
DERIVED_CLIP_USAGE = "REVIEW_EVIDENCE_ONLY_NOT_TRAINING_LABEL"
EVIDENCE_BOUNDARY = "OWNER_APPROVAL_OVERLAY_AND_FAIL_CLOSED_QUARANTINE_ONLY_NO_RAW_MUTATION_NO_FINAL_SPLIT_NO_TRAINING"

CONTRACT_RELATIVE_PATH = "references/dataset01/wp10_g04_owner_quarantine_contract.json"
OVERLAY_RELATIVE_PATH = "docs/review/generated/wp10_g04_owner_decision_overlay.json"
REGISTRY_RELATIVE_PATH = "docs/review/generated/wp10_quarantine_registry.json"
REPORT_RELATIVE_PATH = "docs/review/wp10_g04_quarantine_report.md"
MANIFEST_RELATIVE_PATH = "docs/review/generated/wp10_g04_quarantine_manifest.json"

EXPECTED_RAW_LINES = [
    "49 0.992188 0.345370 0.053125 0.101852",
    "49 0.333854 0.342593 0.046875 0.088889",
]

EXPECTED_PINNED_HASHES = {
    "contract": "2ebc5ffccc89a395cc7910811762421d7be6a0bb5c88448c550b9ad5146664a1",
    "raw_image_0248": "07eab2035dc10b7b08be71d76c3c32ffdb960722839414f1e474da20c3ad0cbd",
    "raw_label_0248": "f4ec410f7bff3ee03f6110308e8e95f57c92bcc7ebf45ff3affcfd885b419c77",
    "historical_decision_status": "87d81262e907bb1c479cfac6535e7b3f67a368c371e96b810aa02f2e92d0d72c",
    "source_preservation": "5ca3e769b9197cad19bcb75f553dd59fee6e3035e0cc86cd9693737f84a713d7",
    "wp8_manifest": "9d8fc460b8162874b4082940b0e7f3ceb174c068a92378974ebd93b55da20348",
    "wp9_manifest": "cea9423616de0bf4649d71e40f395b4cdc18ff3ea2f80e9829ea4063f009656f",
    "wp9_adjudication": "b600597496d5fbd2f16f554d320d84cf60928e909245a622dc34790ac5d954aa",
    "wp9_derived_candidate": "8fcdd25dce463d7c57ef5f9f95ce1810db056d7d02e260e2126e3656c4a691b6",
    "wp9_report": "e8af88cf6975d38a28a5f1bb07650a4e0431d479d28313247197ce96d458e81b",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def safe_child(root: Path, relative_value: str) -> Path:
    relative = Path(relative_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe relative path: {relative_value}")
    resolved_root = root.resolve()
    candidate = resolved_root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError(f"symlink path is not allowed: {relative_value}")
    resolved = candidate.resolve()
    resolved.relative_to(resolved_root)
    return resolved


def default_raw_root(repo_root: Path) -> Path:
    review_path = repo_root / "docs/review/generated/bbox_0248_review.json"
    payload = json.loads(review_path.read_text(encoding="utf-8"))
    image_path = Path(payload["source"]["image_path"])
    if image_path.name != "0248.jpg" or image_path.parent.name != "images" or image_path.parent.parent.name != "archive":
        raise ValueError("WP2 bbox evidence has an unexpected raw image path")
    return image_path.parents[2]


def source_contract(repo_root: Path, raw_root: Path) -> list[tuple[str, str, str, Path, str]]:
    audit = repo_root / "results/data_audit/DATASET01_052bc980a7206f8d"
    return [
        ("contract", "repo", CONTRACT_RELATIVE_PATH, repo_root / CONTRACT_RELATIVE_PATH, EXPECTED_PINNED_HASHES["contract"]),
        ("raw_image_0248", "raw", "archive/images/0248.jpg", raw_root / "archive/images/0248.jpg", EXPECTED_PINNED_HASHES["raw_image_0248"]),
        ("raw_label_0248", "raw", "archive/labels/0248.txt", raw_root / "archive/labels/0248.txt", EXPECTED_PINNED_HASHES["raw_label_0248"]),
        ("historical_decision_status", "repo", "docs/review/decision_status.json", repo_root / "docs/review/decision_status.json", EXPECTED_PINNED_HASHES["historical_decision_status"]),
        ("source_preservation", "repo", "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json", audit / "source_preservation_proof.json", EXPECTED_PINNED_HASHES["source_preservation"]),
        ("wp8_manifest", "repo", "docs/review/generated/wp8_taxonomy_manifest.json", repo_root / "docs/review/generated/wp8_taxonomy_manifest.json", EXPECTED_PINNED_HASHES["wp8_manifest"]),
        ("wp9_manifest", "repo", "docs/review/generated/wp9_bbox_0248_manifest.json", repo_root / "docs/review/generated/wp9_bbox_0248_manifest.json", EXPECTED_PINNED_HASHES["wp9_manifest"]),
        ("wp9_adjudication", "repo", "docs/review/generated/wp9_bbox_0248_adjudication.json", repo_root / "docs/review/generated/wp9_bbox_0248_adjudication.json", EXPECTED_PINNED_HASHES["wp9_adjudication"]),
        ("wp9_derived_candidate", "repo", "docs/review/generated/wp9_bbox_0248_derived_candidate.txt", repo_root / "docs/review/generated/wp9_bbox_0248_derived_candidate.txt", EXPECTED_PINNED_HASHES["wp9_derived_candidate"]),
        ("wp9_report", "repo", "docs/review/wp9_bbox_0248_adjudication_report.md", repo_root / "docs/review/wp9_bbox_0248_adjudication_report.md", EXPECTED_PINNED_HASHES["wp9_report"]),
    ]


def artifact_contract(repo_root: Path) -> list[tuple[str, str, Path]]:
    return [
        ("owner_decision_overlay", OVERLAY_RELATIVE_PATH, repo_root / OVERLAY_RELATIVE_PATH),
        ("quarantine_registry", REGISTRY_RELATIVE_PATH, repo_root / REGISTRY_RELATIVE_PATH),
        ("report", REPORT_RELATIVE_PATH, repo_root / REPORT_RELATIVE_PATH),
    ]


def verify_pinned_sources(repo_root: Path, raw_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item_id, root_id, relative, path, expected_hash in source_contract(repo_root, raw_root):
        if not path.is_file():
            raise FileNotFoundError(path)
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise ValueError(f"pinned source hash mismatch: {item_id}")
        records.append({"id": item_id, "root": root_id, "path": relative, "sha256": actual_hash, "size": path.stat().st_size})
    return records


def validate_contract(repo_root: Path) -> dict[str, Any]:
    contract = json.loads((repo_root / CONTRACT_RELATIVE_PATH).read_text(encoding="utf-8"))
    if contract.get("schema_version") != 1 or contract.get("package") != "M0-WP10" or contract.get("status") != "OWNER_APPROVED_QUARANTINE_AWAITING_WP10_QA":
        raise ValueError("WP10 contract identity/status mismatch")
    decision = contract.get("decision", {})
    if decision != {
        "decision_id": DECISION_ID,
        "status": DECISION_STATUS,
        "selected_option": SELECTED_OPTION,
        "decision_date": "2026-10-11",
        "decision_timezone": "Asia/Saigon",
        "authority": "DIRECT_OWNER_APPROVAL_ROUTED_QA_PM",
    }:
        raise ValueError("WP10 owner decision contract mismatch")
    scope = contract.get("scope", {})
    if scope != {
        "scope_type": "ENTIRE_IMAGE_STEM",
        "stem": QUARANTINED_STEM,
        "image_path": "archive/images/0248.jpg",
        "image_sha256": EXPECTED_PINNED_HASHES["raw_image_0248"],
        "label_path": "archive/labels/0248.txt",
        "label_sha256": EXPECTED_PINNED_HASHES["raw_label_0248"],
        "label_row_count": 2,
        "label_rows": [1, 2],
        "class_ids_present": [49],
        "class_49_taxonomy_excluded": False,
        "only_sample_0248_quarantined": True,
    }:
        raise ValueError("WP10 quarantine scope mismatch")
    enforcement = contract.get("enforcement", {})
    if enforcement != {
        "raw_immutable": True,
        "exclude_entire_stem_from_split_generation": True,
        "exclude_entire_stem_from_training": True,
        "derived_clip_usage": DERIVED_CLIP_USAGE,
        "missing_or_invalid_overlay_policy": "FAIL_CLOSED",
        "missing_or_invalid_registry_policy": "FAIL_CLOSED",
    }:
        raise ValueError("WP10 enforcement contract mismatch")
    lineage = contract.get("decision_lineage", {})
    expected_lineage = {
        "historical_decision_status_sha256": EXPECTED_PINNED_HASHES["historical_decision_status"],
        "wp8_manifest_sha256": EXPECTED_PINNED_HASHES["wp8_manifest"],
        "wp9_manifest_sha256": EXPECTED_PINNED_HASHES["wp9_manifest"],
        "wp9_adjudication_sha256": EXPECTED_PINNED_HASHES["wp9_adjudication"],
        "wp9_derived_candidate_sha256": EXPECTED_PINNED_HASHES["wp9_derived_candidate"],
    }
    if lineage != expected_lineage:
        raise ValueError("WP10 decision lineage mismatch")
    governance = contract.get("governance", {})
    if governance != {
        "g04_closure": "PENDING_WP10_QA_PASS",
        "remaining_pending_decisions": ["D-01", "D-02", "D-03", "D-04", "D-05"],
        "gate0": "BLOCKED",
        "relabel_authorized": False,
        "split_authorized": False,
        "training_authorized": False,
    } or contract.get("evidence_boundary") != EVIDENCE_BOUNDARY:
        raise ValueError("WP10 governance/evidence boundary mismatch")
    return contract


def validate_historical_lineage(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    verify_pinned_sources(repo_root, raw_root)
    contract = validate_contract(repo_root)
    historical = json.loads((repo_root / "docs/review/decision_status.json").read_text(encoding="utf-8"))
    historic_g04 = historical["decisions"][DECISION_ID]
    if historical.get("gate0") != "BLOCKED" or historical.get("training_authorized") is not False:
        raise ValueError("historical governance boundary changed")
    if historic_g04.get("status") != "PENDING" or historic_g04.get("selected_option") is not None:
        raise ValueError("historical decision status must remain immutable and PENDING")
    wp9_manifest = json.loads((repo_root / "docs/review/generated/wp9_bbox_0248_manifest.json").read_text(encoding="utf-8"))
    if wp9_manifest.get("decision_status") != "PENDING" or wp9_manifest.get("selected_option") is not None or wp9_manifest.get("raw_source_unchanged") is not True or wp9_manifest.get("training_authorized") is not False:
        raise ValueError("WP9 historical manifest boundary changed")
    wp9 = json.loads((repo_root / "docs/review/generated/wp9_bbox_0248_adjudication.json").read_text(encoding="utf-8"))
    if wp9["target"]["stem"] != QUARANTINED_STEM or wp9["target"]["label"]["sha256"] != EXPECTED_PINNED_HASHES["raw_label_0248"]:
        raise ValueError("WP9 target lineage mismatch")
    if wp9["recommendation"]["proposed_disposition"] != "QUARANTINE_FROM_TRAINING_PENDING_OWNER_DECISION":
        raise ValueError("WP9 quarantine recommendation lineage mismatch")
    if wp9["derived_clip_candidate"]["status"] != "REVIEW_ONLY_NOT_APPROVED_TRAINING_LABEL" or wp9["derived_clip_candidate"]["source_raw_label_overwritten"] is not False:
        raise ValueError("WP9 derived candidate boundary changed")
    raw_label = raw_root / "archive/labels/0248.txt"
    if raw_label.read_bytes() != ("\r\n".join(EXPECTED_RAW_LINES) + "\r\n").encode("ascii"):
        raise ValueError("raw 0248 label bytes/count/content changed")
    proof = json.loads((repo_root / "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json").read_text(encoding="utf-8"))
    if proof.get("unchanged") is not True:
        raise ValueError("source preservation proof is not unchanged=true")
    return {"contract": contract, "wp9": wp9}


def overlay_payload(contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "package": "M0-WP10",
        "status": "OWNER_APPROVED_QUARANTINE_RECORDED_AWAITING_WP10_QA",
        "overlay_type": "APPEND_ONLY_OWNER_DECISION_RESOLUTION",
        "historical_decision_file_mutated": False,
        "decision": contract["decision"],
        "scope": contract["scope"],
        "enforcement": contract["enforcement"],
        "reason": contract["reason"],
        "decision_lineage": contract["decision_lineage"],
        "governance": contract["governance"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }


def registry_payload(contract: dict[str, Any]) -> dict[str, Any]:
    scope = contract["scope"]
    return {
        "schema_version": 1,
        "package": "M0-WP10",
        "status": "ACTIVE_FAIL_CLOSED_OWNER_APPROVED_QUARANTINE_AWAITING_WP10_QA",
        "default_policy": "FAIL_CLOSED_IF_OWNER_OVERLAY_OR_REGISTRY_IS_MISSING_INVALID_OR_UNVERIFIED",
        "g04_formal_closure": "PENDING_WP10_QA_PASS",
        "entry_count": 1,
        "quarantined_stem_count": 1,
        "entries": [
            {
                "quarantine_id": "G0.4-bbox-0248:stem:0248",
                "decision_id": DECISION_ID,
                "decision_status": DECISION_STATUS,
                "selected_option": SELECTED_OPTION,
                "decision_date": "2026-10-11",
                "decision_timezone": "Asia/Saigon",
                "scope_type": "ENTIRE_IMAGE_STEM",
                "stem": QUARANTINED_STEM,
                "image_path": scope["image_path"],
                "image_sha256": scope["image_sha256"],
                "label_path": scope["label_path"],
                "label_sha256": scope["label_sha256"],
                "label_row_count": 2,
                "label_rows": [1, 2],
                "class_ids_present": [49],
                "exclude_entire_stem_from_split_generation": True,
                "exclude_entire_stem_from_training": True,
                "raw_immutable": True,
                "derived_clip_usage": DERIVED_CLIP_USAGE,
                "class_49_taxonomy_excluded": False,
                "reason": contract["reason"],
                "wp9_manifest_sha256": EXPECTED_PINNED_HASHES["wp9_manifest"],
            }
        ],
        "governance": {
            "gate0": "BLOCKED",
            "remaining_pending_decisions": ["D-01", "D-02", "D-03", "D-04", "D-05"],
            "split_authorized": False,
            "training_authorized": False,
        },
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }


def render_report(contract: dict[str, Any]) -> str:
    return f"""# M0-WP10 G0.4 owner quarantine resolution

Status: `{PACKAGE_STATUS}`  
Decision: `{DECISION_ID}` → `{SELECTED_OPTION}` (`{DECISION_STATUS}`)  
Decision date: `2026-10-11` (`Asia/Saigon`)  
Boundary: `{EVIDENCE_BOUNDARY}`

## Owner-approved operational rule

The owner approved quarantine for the entire image/stem `0248`. This decision applies to both raw
label rows, not only the out-of-bounds first box. Stem `0248` must be excluded from every candidate
split and from training input. The raw image and label remain immutable.

The WP9 clipped annotation remains `{DERIVED_CLIP_USAGE}`. It is not a replacement label and may
not be admitted to split generation or training.

Class `49` and its taxonomy remain in scope. The quarantine applies only to sample/stem `0248`.

## Fail-closed enforcement

`scripts/build_wp10_g04_quarantine.py check-candidate` validates the hash-bound WP10 package before
reading a candidate. If the overlay or registry is missing, invalid, re-hashed after semantic
tampering, or disconnected from the pinned raw/WP9 lineage, the candidate is rejected. If a valid
candidate list or split manifest contains stem `0248`, it is rejected. Candidates without `0248`
can pass this quarantine-specific check, but that result does **not** authorize a final split or
training.

Examples:

```bash
uv run python scripts/build_wp10_g04_quarantine.py verify --repo-root .
uv run python scripts/build_wp10_g04_quarantine.py check-candidate --repo-root . --candidate candidate.json
```

Accepted candidate formats are a JSON list of stems, a JSON object with `stems`, a JSON object with
`splits` containing stem lists, or a UTF-8 text file with one stem per nonblank line.

## Immutable lineage

- Raw image SHA-256: `{EXPECTED_PINNED_HASHES['raw_image_0248']}`.
- Raw label SHA-256: `{EXPECTED_PINNED_HASHES['raw_label_0248']}`.
- Historical decision-status SHA-256: `{EXPECTED_PINNED_HASHES['historical_decision_status']}`.
- WP8 manifest SHA-256: `{EXPECTED_PINNED_HASHES['wp8_manifest']}`.
- WP9 manifest SHA-256: `{EXPECTED_PINNED_HASHES['wp9_manifest']}`.
- WP9 derived-candidate SHA-256: `{EXPECTED_PINNED_HASHES['wp9_derived_candidate']}`.
- WP10 owner-decision contract SHA-256: `{EXPECTED_PINNED_HASHES['contract']}`.

## Governance boundary

WP10 is awaiting QA. G0.4 becomes formally closed only after WP10 QA PASS. D-01 through D-05 remain
`PENDING`; Gate 0 remains `BLOCKED`; `split_authorized=false`; `training_authorized=false`. This
package does not create a final split, relabel raw data, train a model, or change taxonomy class 49.
"""


def expected_artifacts(repo_root: Path, raw_root: Path) -> dict[str, bytes]:
    facts = validate_historical_lineage(repo_root, raw_root)
    contract = facts["contract"]
    return {
        OVERLAY_RELATIVE_PATH: json_bytes(overlay_payload(contract)),
        REGISTRY_RELATIVE_PATH: json_bytes(registry_payload(contract)),
        REPORT_RELATIVE_PATH: render_report(contract).encode("utf-8"),
    }


def build_manifest(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    sources = verify_pinned_sources(repo_root, raw_root)
    artifacts = [
        {"id": item_id, "root": "repo", "path": relative, "sha256": sha256_file(path), "size": path.stat().st_size}
        for item_id, relative, path in artifact_contract(repo_root)
    ]
    return {
        "schema_version": 1,
        "package": "M0-WP10",
        "status": PACKAGE_STATUS,
        "decision_id": DECISION_ID,
        "decision_status": DECISION_STATUS,
        "selected_option": SELECTED_OPTION,
        "decision_date": "2026-10-11",
        "decision_timezone": "Asia/Saigon",
        "quarantined_stem": QUARANTINED_STEM,
        "quarantine_scope": "ENTIRE_IMAGE_STEM_ALL_LABEL_ROWS",
        "g04_formal_closure": "PENDING_WP10_QA_PASS",
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE",
        "raw_source_unchanged": True,
        "exclude_entire_stem_from_split_generation": True,
        "exclude_entire_stem_from_training": True,
        "derived_clip_usage": DERIVED_CLIP_USAGE,
        "class_49_taxonomy_excluded": False,
        "gate0": "BLOCKED",
        "split_authorized": False,
        "training_authorized": False,
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "total_artifact_bytes": sum(record["size"] for record in artifacts),
        "sources": sources,
        "artifacts": artifacts,
    }


def validate_collection(payload: dict[str, Any], name: str, expected: list[tuple[str, str, str]], roots: dict[str, Path], errors: list[str]) -> list[dict[str, Any]]:
    value = payload.get(name)
    if not isinstance(value, list):
        errors.append(f"{name} must be a list")
        return []
    records: list[dict[str, Any]] = []
    roster: list[tuple[str, str, str]] = []
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            errors.append(f"{name}[{index}] must be an object")
            continue
        if set(record) != {"id", "root", "path", "sha256", "size"}:
            errors.append(f"{name}[{index}] fields differ from contract")
        item_id, root_id, path_value = record.get("id"), record.get("root"), record.get("path")
        if isinstance(item_id, str) and isinstance(root_id, str) and isinstance(path_value, str):
            roster.append((item_id, root_id, path_value))
            if root_id not in roots:
                errors.append(f"{name}[{index}].root invalid")
            else:
                try:
                    safe_child(roots[root_id], path_value)
                except (ValueError, OSError) as exc:
                    errors.append(str(exc))
        else:
            errors.append(f"{name}[{index}] identity/path invalid")
        digest = record.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            errors.append(f"{name}[{index}].sha256 invalid")
        size = record.get("size")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            errors.append(f"{name}[{index}].size invalid")
        records.append(record)
    if len({record[0] for record in roster}) != len(roster):
        errors.append(f"duplicate {name} IDs")
    if len({record[1:] for record in roster}) != len(roster):
        errors.append(f"duplicate {name} paths")
    if roster != expected:
        errors.append(f"{name} roster/order differs from canonical contract")
    return records


def verify_manifest(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {"valid": False, "errors": [f"manifest unreadable: {exc}"]}
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["manifest root must be an object"]}
    expected_top = {
        "schema_version", "package", "status", "decision_id", "decision_status", "selected_option",
        "decision_date", "decision_timezone", "quarantined_stem", "quarantine_scope",
        "g04_formal_closure", "evidence_boundary", "manifest_path", "manifest_self_in_artifact_count",
        "artifact_count_semantics", "raw_source_unchanged", "exclude_entire_stem_from_split_generation",
        "exclude_entire_stem_from_training", "derived_clip_usage", "class_49_taxonomy_excluded",
        "gate0", "split_authorized", "training_authorized", "source_count", "artifact_count",
        "total_artifact_bytes", "sources", "artifacts",
    }
    if set(payload) != expected_top:
        errors.append("manifest top-level fields differ from WP10 schema")
    constants = {
        "schema_version": 1, "package": "M0-WP10", "status": PACKAGE_STATUS,
        "decision_id": DECISION_ID, "decision_status": DECISION_STATUS,
        "selected_option": SELECTED_OPTION, "decision_date": "2026-10-11",
        "decision_timezone": "Asia/Saigon", "quarantined_stem": QUARANTINED_STEM,
        "quarantine_scope": "ENTIRE_IMAGE_STEM_ALL_LABEL_ROWS",
        "g04_formal_closure": "PENDING_WP10_QA_PASS", "evidence_boundary": EVIDENCE_BOUNDARY,
        "manifest_path": MANIFEST_RELATIVE_PATH, "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE", "raw_source_unchanged": True,
        "exclude_entire_stem_from_split_generation": True,
        "exclude_entire_stem_from_training": True, "derived_clip_usage": DERIVED_CLIP_USAGE,
        "class_49_taxonomy_excluded": False, "gate0": "BLOCKED",
        "split_authorized": False, "training_authorized": False,
    }
    for field, expected in constants.items():
        if payload.get(field) != expected:
            errors.append(f"invalid manifest {field}")

    roots = {"repo": repo_root, "raw": raw_root}
    expected_sources = [(item_id, root_id, relative) for item_id, root_id, relative, _path, _digest in source_contract(repo_root, raw_root)]
    expected_artifacts = [(item_id, "repo", relative) for item_id, relative, _path in artifact_contract(repo_root)]
    sources = validate_collection(payload, "sources", expected_sources, roots, errors)
    artifacts = validate_collection(payload, "artifacts", expected_artifacts, roots, errors)
    if payload.get("source_count") != len(expected_sources) or len(sources) != len(expected_sources):
        errors.append("source_count mismatch")
    if payload.get("artifact_count") != len(expected_artifacts) or len(artifacts) != len(expected_artifacts):
        errors.append("artifact_count mismatch")
    recorded_bytes = sum(record.get("size", -1) for record in artifacts if isinstance(record.get("size"), int) and not isinstance(record.get("size"), bool))
    if payload.get("total_artifact_bytes") != recorded_bytes:
        errors.append("total_artifact_bytes mismatch")

    for collection, records in (("sources", sources), ("artifacts", artifacts)):
        for record in records:
            root_id, path_value = record.get("root"), record.get("path")
            if root_id not in roots or not isinstance(path_value, str):
                continue
            try:
                path = safe_child(roots[root_id], path_value)
            except (ValueError, OSError):
                continue
            if not path.is_file():
                errors.append(f"missing {collection} file: {path_value}")
            elif path.stat().st_size != record.get("size") or sha256_file(path) != record.get("sha256"):
                errors.append(f"tampered {collection} file: {path_value}")
            if collection == "sources" and EXPECTED_PINNED_HASHES.get(str(record.get("id"))) is not None:
                if record.get("sha256") != EXPECTED_PINNED_HASHES[str(record["id"])]:
                    errors.append(f"pinned source hash mismatch: {record['id']}")

    if not errors:
        try:
            expected_payloads = expected_artifacts_payloads(repo_root, raw_root)
            for _item_id, relative, path in artifact_contract(repo_root):
                if path.read_bytes() != expected_payloads[relative]:
                    raise ValueError(f"semantic artifact mismatch: {relative}")
            registry = json.loads((repo_root / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))
            entry = registry["entries"][0]
            if registry["entry_count"] != 1 or entry["stem"] != QUARANTINED_STEM:
                raise ValueError("quarantine registry exact single-entry contract mismatch")
            if not entry["exclude_entire_stem_from_split_generation"] or not entry["exclude_entire_stem_from_training"]:
                raise ValueError("quarantine enforcement flags changed")
            if entry["derived_clip_usage"] != DERIVED_CLIP_USAGE:
                raise ValueError("derived clip became eligible for training")
            if sha256_file(raw_root / "archive/labels/0248.txt") != EXPECTED_PINNED_HASHES["raw_label_0248"]:
                raise ValueError("raw 0248 label changed")
        except (FileNotFoundError, json.JSONDecodeError, KeyError, OSError, TypeError, ValueError) as exc:
            errors.append(f"semantic verification failed: {exc}")
    return {
        "valid": not errors,
        "errors": errors,
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "status": payload.get("status"),
        "decision_status": payload.get("decision_status"),
        "selected_option": payload.get("selected_option"),
    }


def expected_artifacts_payloads(repo_root: Path, raw_root: Path) -> dict[str, bytes]:
    return expected_artifacts(repo_root, raw_root)


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    repo_root, raw_root = repo_root.resolve(), raw_root.resolve()
    payloads = expected_artifacts(repo_root, raw_root)
    for relative, payload in payloads.items():
        write_bytes(repo_root / relative, payload)
    manifest = build_manifest(repo_root, raw_root)
    write_bytes(repo_root / MANIFEST_RELATIVE_PATH, json_bytes(manifest))
    result = verify_manifest(repo_root / MANIFEST_RELATIVE_PATH, repo_root, raw_root)
    if not result["valid"]:
        raise RuntimeError(f"WP10 package verification failed: {result['errors']}")
    return {
        "status": PACKAGE_STATUS,
        "decision_status": DECISION_STATUS,
        "selected_option": SELECTED_OPTION,
        "quarantined_stem": QUARANTINED_STEM,
        "source_count": manifest["source_count"],
        "artifact_count": manifest["artifact_count"],
        "manifest_sha256": sha256_file(repo_root / MANIFEST_RELATIVE_PATH),
        "g04_formal_closure": "PENDING_WP10_QA_PASS",
        "gate0": "BLOCKED",
        "training_authorized": False,
    }


def validate_candidate_stems(stems: Any) -> list[str]:
    if not isinstance(stems, list) or not stems:
        raise ValueError("candidate stems must be a non-empty list")
    validated: list[str] = []
    for index, stem in enumerate(stems):
        if not isinstance(stem, str) or not stem or stem != stem.strip():
            raise ValueError(f"candidate stem at index {index} is invalid")
        if stem in {".", ".."} or "/" in stem or "\\" in stem or Path(stem).name != stem:
            raise ValueError(f"candidate stem path escape is not allowed: {stem}")
        validated.append(stem)
    if len(set(validated)) != len(validated):
        raise ValueError("candidate stems contain duplicates")
    return validated


def parse_candidate(path: Path) -> list[str]:
    if path.is_symlink():
        raise ValueError("candidate symlink is not allowed")
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return validate_candidate_stems(payload)
        if not isinstance(payload, dict):
            raise ValueError("candidate JSON must be a list or object")
        has_stems = "stems" in payload
        has_splits = "splits" in payload
        if has_stems == has_splits:
            raise ValueError("candidate JSON must contain exactly one of stems or splits")
        if has_stems:
            return validate_candidate_stems(payload["stems"])
        splits = payload["splits"]
        if not isinstance(splits, dict) or not splits:
            raise ValueError("candidate splits must be a non-empty object")
        flattened: list[str] = []
        for split_name in sorted(splits):
            if not isinstance(split_name, str) or not split_name.strip():
                raise ValueError("candidate split name is invalid")
            values = splits[split_name]
            if not isinstance(values, list):
                raise ValueError(f"candidate split {split_name} must be a list")
            flattened.extend(values)
        return validate_candidate_stems(flattened)
    return validate_candidate_stems([line for line in path.read_text(encoding="utf-8").splitlines() if line])


def verify_candidate_stems(stems: Any, manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    package = verify_manifest(manifest_path, repo_root, raw_root)
    if not package["valid"]:
        return {
            "allowed": False,
            "status": "REJECTED_PACKAGE_INVALID_FAIL_CLOSED",
            "candidate_passes_quarantine_check": False,
            "stems": [],
            "violations": [],
            "errors": package["errors"],
            "training_authorized": False,
        }
    try:
        validated = validate_candidate_stems(stems)
    except ValueError as exc:
        return {
            "allowed": False,
            "status": "REJECTED_CANDIDATE_INVALID_FAIL_CLOSED",
            "candidate_passes_quarantine_check": False,
            "stems": [],
            "violations": [],
            "errors": [str(exc)],
            "training_authorized": False,
        }
    violations = [
        {
            "stem": stem,
            "decision_id": DECISION_ID,
            "selected_option": SELECTED_OPTION,
            "scope": "ENTIRE_IMAGE_STEM_ALL_LABEL_ROWS",
            "reason": "owner-approved quarantine excludes stem 0248 from split generation and training",
        }
        for stem in validated
        if stem == QUARANTINED_STEM
    ]
    allowed = not violations
    return {
        "allowed": allowed,
        "status": "ACCEPTED_NO_QUARANTINED_STEMS" if allowed else "REJECTED_QUARANTINED_STEM",
        "candidate_passes_quarantine_check": allowed,
        "stems": validated,
        "violations": violations,
        "errors": [],
        "training_authorized": False,
    }


def verify_candidate_path(candidate_path: Path, manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    package = verify_manifest(manifest_path, repo_root, raw_root)
    if not package["valid"]:
        return {
            "allowed": False,
            "status": "REJECTED_PACKAGE_INVALID_FAIL_CLOSED",
            "candidate_passes_quarantine_check": False,
            "stems": [],
            "violations": [],
            "errors": package["errors"],
            "training_authorized": False,
        }
    try:
        stems = parse_candidate(candidate_path)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        return {
            "allowed": False,
            "status": "REJECTED_CANDIDATE_INVALID_FAIL_CLOSED",
            "candidate_passes_quarantine_check": False,
            "stems": [],
            "violations": [],
            "errors": [str(exc)],
            "training_authorized": False,
        }
    return verify_candidate_stems(stems, manifest_path, repo_root, raw_root)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify", "check-candidate"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, required=True)
        command.add_argument("--raw-root", type=Path)
    commands.choices["verify"].add_argument("--manifest", type=Path, default=Path(MANIFEST_RELATIVE_PATH))
    commands.choices["check-candidate"].add_argument("--manifest", type=Path, default=Path(MANIFEST_RELATIVE_PATH))
    commands.choices["check-candidate"].add_argument("--candidate", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    raw_root = args.raw_root.resolve() if args.raw_root else default_raw_root(repo_root)
    if args.command == "build":
        result = build(repo_root, raw_root)
        exit_code = 0
    elif args.command == "verify":
        manifest = args.manifest if args.manifest.is_absolute() else repo_root / args.manifest
        result = verify_manifest(manifest, repo_root, raw_root)
        exit_code = 0 if result["valid"] else 1
    else:
        manifest = args.manifest if args.manifest.is_absolute() else repo_root / args.manifest
        result = verify_candidate_path(args.candidate, manifest, repo_root, raw_root)
        exit_code = 0 if result["allowed"] else 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
