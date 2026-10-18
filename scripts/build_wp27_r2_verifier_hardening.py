# ruff: noqa: E501
"""Build and verify the append-only M0-WP27-R2 type-strict verifier hardening."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

R1_BUILDER_PATH = Path(__file__).with_name("build_wp27_r1_layout_correction.py")
R1_SPEC = importlib.util.spec_from_file_location("wp27_r2_immutable_r1", R1_BUILDER_PATH)
assert R1_SPEC is not None and R1_SPEC.loader is not None
r1 = importlib.util.module_from_spec(R1_SPEC)
sys.modules[R1_SPEC.name] = r1
R1_SPEC.loader.exec_module(r1)

sha256_file = r1.sha256_file
read_json = r1.read_json
write_json = r1.write_json
safe_child = r1.safe_child

PACKAGE = "M0-WP27-R2-TYPE-STRICT-VERIFIER-HARDENING"
STATUS = "WP27_R2_AWAITING_INDEPENDENT_QA"
EVIDENCE_BOUNDARY = (
    "WP27_R2_VERIFIER_HARDENING_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_"
    "NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
AUDIT_STATUS = "PASS_TYPE_STRICT_CANONICAL_R1_LAYOUT_EXACTLY_ONE_STATUS_CHANGE"

R1_MANIFEST_RELATIVE_PATH = r1.MANIFEST_RELATIVE_PATH
R1_LAYOUT_RELATIVE_PATH = r1.LAYOUT_RELATIVE_PATH
R1_DELTA_RELATIVE_PATH = r1.DELTA_RELATIVE_PATH
R1_ROSTER_RELATIVE_PATH = r1.EFFECTIVE_ROSTER_RELATIVE_PATH
R1_REPORT_RELATIVE_PATH = r1.REPORT_RELATIVE_PATH
R1_BUILDER_RELATIVE_PATH = r1.R1_BUILDER_RELATIVE_PATH
R1_TEST_RELATIVE_PATH = r1.R1_TEST_RELATIVE_PATH
INITIAL_LAYOUT_RELATIVE_PATH = r1.INITIAL_LAYOUT_RELATIVE_PATH
QA_RECORD_RELATIVE_PATH = "docs/review/wp27_r2_qa_correction_record.md"
R2_BUILDER_RELATIVE_PATH = "scripts/build_wp27_r2_verifier_hardening.py"
R2_TEST_RELATIVE_PATH = "tests/test_wp27_r2_verifier_hardening.py"

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp27_r2_verifier_hardening_manifest.json"
AUDIT_RELATIVE_PATH = "docs/review/generated/wp27_r2_type_strict_layout_audit.json"
REPORT_RELATIVE_PATH = "docs/review/wp27_r2_verifier_hardening_report.md"

R1_MANIFEST_SHA256 = "6992625b062649ba979a39eb7e4ef8fd00eadad666558fb40886d520390d96fc"
R1_LAYOUT_SHA256 = "d7af4b260985215ff70ca8567369f75f96bc63f4bfe8b58f6d5849b77e00e7f3"
R1_DELTA_SHA256 = "a3bb4ced80bae9b3c4124af7e53e16fe1673ca3f1794fdd249f9218accc8fe6e"
R1_ROSTER_SHA256 = "c4b25036ea12820f7d0a9434d93bcea1b2e0461f7dc83878964a69255c8bc741"
R1_REPORT_SHA256 = "b20719298e8efe95d136f38b3024f0b4edb3bb1ee6bff22d601687b3385c1e44"
R1_BUILDER_SHA256 = "9bfc963f207876cbd431e48e2184252e962a8f473182a70148e026033314cdd7"
R1_TEST_SHA256 = "f406d316b6068d28f724a4e9f5e19ee2b61364b362cf647902760952f310f36e"
QA_RECORD_SHA256 = "6a7fecffe0e09d5c82ceeb24ab5da3fe6f5f618ef83782d60ff4434011d8e2c1"

R1_PINNED_FILES = (
    ("wp27_r1_manifest", R1_MANIFEST_RELATIVE_PATH, R1_MANIFEST_SHA256),
    ("wp27_r1_corrected_layout_audit", R1_LAYOUT_RELATIVE_PATH, R1_LAYOUT_SHA256),
    ("wp27_r1_layout_semantic_delta", R1_DELTA_RELATIVE_PATH, R1_DELTA_SHA256),
    ("wp27_r1_effective_artifact_roster", R1_ROSTER_RELATIVE_PATH, R1_ROSTER_SHA256),
    ("wp27_r1_correction_report", R1_REPORT_RELATIVE_PATH, R1_REPORT_SHA256),
    ("wp27_r1_builder", R1_BUILDER_RELATIVE_PATH, R1_BUILDER_SHA256),
    ("wp27_r1_test", R1_TEST_RELATIVE_PATH, R1_TEST_SHA256),
)
R1_EXPECTED_ARTIFACTS = (
    ("corrected_layout_audit", R1_LAYOUT_RELATIVE_PATH, R1_LAYOUT_SHA256),
    ("layout_semantic_delta", R1_DELTA_RELATIVE_PATH, R1_DELTA_SHA256),
    ("effective_artifact_roster", R1_ROSTER_RELATIVE_PATH, R1_ROSTER_SHA256),
    ("correction_report", R1_REPORT_RELATIVE_PATH, R1_REPORT_SHA256),
)
R1_EXPECTED_VERIFY = {
    "valid": True,
    "errors": [],
    "source_count": 151,
    "artifact_count": 4,
    "effective_artifact_count": 56,
    "changed_artifact_count": 1,
    "status": r1.STATUS,
}

# Every count/position field must be an exact JSON integer (never bool or float).
TOP_LEVEL_INT_FIELDS = ("schema_version", "pair_count", "page_count", "pairs_per_page")
PAGE_INT_FIELDS = ("page", "row_count", "width", "height")
ROW_INT_FIELDS = ("slot", "batch_position")
ROW_BOUNDS_FIELDS = ("left_bounds", "right_bounds", "text_bounds")
TYPE_CONFUSION_PROBES = (
    "pair_count_float",
    "page_count_float",
    "pairs_per_page_float",
    "page_number_bool",
    "row_count_float",
    "slot_bool",
    "batch_position_bool",
    "bounds_float",
)


def canonical_json_text(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def strict_semantic_diff(before: Any, after: Any, pointer: str = "") -> list[tuple[str, Any, Any]]:
    if type(before) is not type(after):
        return [(pointer or "/", before, after)]
    if isinstance(before, dict):
        if set(before) != set(after):
            return [(pointer or "/", before, after)]
        rows: list[tuple[str, Any, Any]] = []
        for key in sorted(before):
            rows.extend(strict_semantic_diff(before[key], after[key], f"{pointer}/{key}"))
        return rows
    if isinstance(before, list):
        if len(before) != len(after):
            return [(pointer or "/", before, after)]
        rows = []
        for index, (left, right) in enumerate(zip(before, after, strict=True)):
            rows.extend(strict_semantic_diff(left, right, f"{pointer}/{index}"))
        return rows
    return [] if before == after else [(pointer or "/", before, after)]


def leaf_type_counts(payload: Any) -> dict[str, int]:
    counts: Counter[str] = Counter()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        else:
            counts[type(value).__name__] += 1

    walk(payload)
    return dict(sorted(counts.items()))


def _require_int(value: Any, label: str) -> int:
    if type(value) is not int:
        raise ValueError(f"WP27-R2 type-strict layout field must be int: {label}")
    return value


def validate_strict_layout(initial_layout: dict[str, Any], effective_layout: dict[str, Any]) -> int:
    """Validate the effective layout type-strictly and return the number of int fields checked."""
    r1.validate_effective_layout(effective_layout)
    checked = 0
    for field in TOP_LEVEL_INT_FIELDS:
        _require_int(effective_layout.get(field), f"/{field}")
        checked += 1
    if type(effective_layout.get("status")) is not str:
        raise ValueError("WP27-R2 type-strict layout status must be str")
    for page_index, page in enumerate(effective_layout["pages"]):
        for field in PAGE_INT_FIELDS:
            _require_int(page.get(field), f"/pages/{page_index}/{field}")
            checked += 1
        for row_index, row in enumerate(page["rows"]):
            for field in ROW_INT_FIELDS:
                _require_int(row.get(field), f"/pages/{page_index}/rows/{row_index}/{field}")
                checked += 1
            for field in ROW_BOUNDS_FIELDS:
                bounds = row.get(field)
                if not isinstance(bounds, list) or len(bounds) != 4:
                    raise ValueError(
                        f"WP27-R2 type-strict bounds must be 4-int list: /pages/{page_index}/rows/{row_index}/{field}"
                    )
                for bound_index, value in enumerate(bounds):
                    _require_int(value, f"/pages/{page_index}/rows/{row_index}/{field}/{bound_index}")
                    checked += 1
    diff = strict_semantic_diff(initial_layout, effective_layout)
    if diff != [("/status", r1.STALE_LAYOUT_STATUS, r1.EXPECTED_LAYOUT_STATUS)]:
        raise ValueError("WP27-R2 type-strict diff must contain exactly the /status replacement")
    return checked


def validate_canonical_layout_bytes(repo_root: Path, initial_layout: dict[str, Any]) -> str:
    layout_path = safe_child(repo_root, R1_LAYOUT_RELATIVE_PATH)
    expected_text = canonical_json_text(r1.corrected_layout(initial_layout))
    if layout_path.read_bytes() != expected_text.encode("utf-8"):
        raise ValueError("effective layout is not the canonical serialization of corrected_layout(initial)")
    digest = sha256_file(layout_path)
    if digest != R1_LAYOUT_SHA256:
        raise ValueError("effective layout SHA-256 differs from the pinned WP27-R1 corrected layout")
    return expected_text


def validate_pinned_r1_files(repo_root: Path) -> dict[str, Any]:
    for item_id, relative, expected in R1_PINNED_FILES:
        path = safe_child(repo_root, relative)
        if not path.is_file():
            raise ValueError(f"pinned WP27-R1 file missing: {item_id}")
        if sha256_file(path) != expected:
            raise ValueError(f"pinned WP27-R1 file hash mismatch: {item_id}")
    manifest = read_json(repo_root / R1_MANIFEST_RELATIVE_PATH)
    actual = [
        (record.get("id"), record.get("path"), record.get("sha256"))
        for record in manifest.get("artifacts", [])
        if isinstance(record, dict)
    ]
    if actual != list(R1_EXPECTED_ARTIFACTS):
        raise ValueError("pinned WP27-R1 manifest artifact roster mismatch")
    return manifest


def build_audit(repo_root: Path) -> dict[str, Any]:
    initial_path = safe_child(repo_root, INITIAL_LAYOUT_RELATIVE_PATH)
    if sha256_file(initial_path) != r1.INITIAL_LAYOUT_SHA256:
        raise ValueError("immutable initial WP27 layout hash mismatch")
    initial_layout = read_json(initial_path)
    validate_pinned_r1_files(repo_root)
    validate_canonical_layout_bytes(repo_root, initial_layout)
    effective_layout = read_json(repo_root / R1_LAYOUT_RELATIVE_PATH)
    checked = validate_strict_layout(initial_layout, effective_layout)
    return {
        "schema_version": 1,
        "package": PACKAGE,
        "status": AUDIT_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "r1_finding": "P2-1_TYPE_CONFUSION_FAIL_OPEN_UNDER_COHERENT_REFRESH",
        "initial_layout_path": INITIAL_LAYOUT_RELATIVE_PATH,
        "initial_layout_sha256": r1.INITIAL_LAYOUT_SHA256,
        "effective_layout_path": R1_LAYOUT_RELATIVE_PATH,
        "effective_layout_sha256": R1_LAYOUT_SHA256,
        "effective_layout_reused_unchanged_from_r1": True,
        "canonical_serialization_match": True,
        "serialization": "json.dumps(indent=2, sort_keys=True, ensure_ascii=False) + LF",
        "initial_leaf_type_counts": leaf_type_counts(initial_layout),
        "effective_leaf_type_counts": leaf_type_counts(effective_layout),
        "exact_int_fields_checked": checked,
        "type_strict_diff": [
            {
                "json_pointer": pointer,
                "initial_type": type(before).__name__,
                "initial_value": before,
                "effective_type": type(after).__name__,
                "effective_value": after,
            }
            for pointer, before, after in strict_semantic_diff(initial_layout, effective_layout)
        ],
        "pair_count": effective_layout["pair_count"],
        "page_count": effective_layout["page_count"],
        "rejected_type_confusion_probes": list(TYPE_CONFUSION_PROBES),
        "pinned_r1_files": [
            {"id": item_id, "path": relative, "sha256": digest}
            for item_id, relative, digest in R1_PINNED_FILES
        ],
    }


def render_report(audit_sha256: str, exact_int_fields_checked: int) -> str:
    return f"""# M0-WP27-R2 — type-strict verifier hardening

Status: `{STATUS}`
Boundary: `{EVIDENCE_BOUNDARY}`

Independent QA failed WP27-R1 with exactly one `P2` finding and zero `P0`/`P1`/`P3` findings:
the R1 verifier compared JSON leaves with `==` and did not pin the corrected-layout bytes, so a
type-confused layout (for example `pair_count=250.0` or `slot=true`) plus a coherent refresh of
the R1 delta, roster, report and manifest verified as valid. The shipped R1 bytes were correct.

## Append-only correction

- WP27-R1 remains immutable at manifest SHA-256 `{R1_MANIFEST_SHA256}`; its builder, test,
  layout, delta, roster and report are pinned by exact SHA-256 constants in the R2 verifier.
- The effective WP27 Batch F layout is reused unchanged at SHA-256 `{R1_LAYOUT_SHA256}` with
  status `{r1.EXPECTED_LAYOUT_STATUS}`, `pair_count=250` and `page_count=50`.
- R2 requires the effective layout bytes to equal the canonical serialization of
  `corrected_layout(initial_layout)`, a type-strict diff of exactly `/status`, and exact `int`
  type for {exact_int_fields_checked} count/position/bounds fields.
- Type-strict audit SHA-256 is `{audit_sha256}`; it records {len(TYPE_CONFUSION_PROBES)} type-confusion
  probe classes that the R2 verifier rejects even after a coherent refresh.
- R2 also requires the immutable WP27-R1 verifier, and through it the initial WP27 verifier, to
  return `valid=true` on the pinned predecessor packages.

No semantic decision, selection row, source-lineage row, annotation, atlas index, atlas JPEG,
raw image, raw label or provenance artifact was changed.

## Governance boundary

- Canonical WP5 remains 3,172 PENDING edges and all 589 sequences remain PENDING.
- 646 residual PENDING edges remain outside the provisional overlays; two touch quarantined stem
  `0248`, leaving 644 review-eligible residual edges.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.
- This correction does not create final/transitive group truth and does not authorize WP28,
  upload, deploy, publish or real-vehicle control.
"""


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    rows: list[tuple[str, Path, str | None]] = [
        ("wp27_initial_layout_audit", repo_root / INITIAL_LAYOUT_RELATIVE_PATH, r1.INITIAL_LAYOUT_SHA256),
        *((item_id, repo_root / relative, digest) for item_id, relative, digest in R1_PINNED_FILES),
        ("wp27_r2_qa_record", repo_root / QA_RECORD_RELATIVE_PATH, QA_RECORD_SHA256),
        ("wp27_r2_builder", repo_root / R2_BUILDER_RELATIVE_PATH, None),
        ("wp27_r2_test", repo_root / R2_TEST_RELATIVE_PATH, None),
    ]
    paths = [path.relative_to(repo_root).as_posix() for _item_id, path, _digest in rows]
    if len({row[0] for row in rows}) != len(rows) or len(set(paths)) != len(paths):
        raise ValueError("WP27-R2 source contract IDs and paths must be unique")
    return rows


def artifact_contract(repo_root: Path) -> list[tuple[str, Path]]:
    return [
        ("type_strict_layout_audit", repo_root / AUDIT_RELATIVE_PATH),
        ("hardening_report", repo_root / REPORT_RELATIVE_PATH),
    ]


def manifest_constants() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "package": PACKAGE,
        "status": STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "gate0": "BLOCKED",
        "d02_status": "PENDING",
        "canonical_wp5_pending_unchanged": 3172,
        "all_wp5_sequences_pending": 589,
        "residual_pending_edges": 646,
        "review_eligible_residual_edges": 644,
        "quarantined_residual_edges": 2,
        "split_authorized": False,
        "training_authorized": False,
        "final_group_truth_created": False,
        "transitive_grouping_created": False,
        "wp28_started": False,
        "r1_manifest_sha256": R1_MANIFEST_SHA256,
        "effective_layout_sha256": R1_LAYOUT_SHA256,
        "effective_layout_reused_unchanged_from_r1": True,
        "changed_predecessor_bytes": 0,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE",
    }


def build_manifest(repo_root: Path) -> dict[str, Any]:
    sources = [
        r1.relative_record(path, repo_root, item_id)
        for item_id, path, _digest in source_contract(repo_root)
    ]
    artifacts = [
        r1.relative_record(path, repo_root, item_id)
        for item_id, path in artifact_contract(repo_root)
    ]
    return {
        **manifest_constants(),
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "total_artifact_bytes": sum(record["size"] for record in artifacts),
        "sources": sources,
        "artifacts": artifacts,
    }


def _verify_r1_chain(repo_root: Path, raw_root: Path) -> None:
    result = r1.verify(repo_root / R1_MANIFEST_RELATIVE_PATH, repo_root, raw_root)
    if result != R1_EXPECTED_VERIFY:
        raise ValueError(f"immutable WP27-R1 verifier no longer accepts its pinned package: {result}")


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    audit = build_audit(repo_root)
    _verify_r1_chain(repo_root, raw_root)
    write_json(repo_root / AUDIT_RELATIVE_PATH, audit)
    audit_sha256 = sha256_file(repo_root / AUDIT_RELATIVE_PATH)
    (repo_root / REPORT_RELATIVE_PATH).write_text(
        render_report(audit_sha256, audit["exact_int_fields_checked"]), encoding="utf-8"
    )
    manifest = build_manifest(repo_root)
    write_json(repo_root / MANIFEST_RELATIVE_PATH, manifest)
    return {
        "status": STATUS,
        "manifest_sha256": sha256_file(repo_root / MANIFEST_RELATIVE_PATH),
        "audit_sha256": audit_sha256,
        "effective_layout_sha256": R1_LAYOUT_SHA256,
        "source_count": manifest["source_count"],
        "artifact_count": manifest["artifact_count"],
    }


def _validate_collection(
    payload: dict[str, Any],
    name: str,
    contract: list[tuple[str, Path, str | None]] | list[tuple[str, Path]],
    repo_root: Path,
    errors: list[str],
) -> list[dict[str, Any]]:
    records = payload.get(name)
    if not isinstance(records, list) or any(not isinstance(record, dict) for record in records):
        errors.append(f"manifest {name} must be a list of objects")
        return []
    expected = [(row[0], row[1].relative_to(repo_root).as_posix()) for row in contract]
    if [(record.get("id"), record.get("path")) for record in records] != expected:
        errors.append(f"manifest {name} exact ID/path roster mismatch")
        return records
    for record, row in zip(records, contract, strict=True):
        if set(record) != {"id", "path", "sha256", "size"}:
            errors.append(f"manifest {name} record schema mismatch: {record.get('id')}")
            continue
        if (
            type(record.get("sha256")) is not str
            or len(record["sha256"]) != 64
            or type(record.get("size")) is not int
            or record["size"] < 0
        ):
            errors.append(f"manifest {name} record type mismatch: {record.get('id')}")
            continue
        pinned = row[2] if len(row) == 3 else None
        if pinned is not None and record["sha256"] != pinned:
            errors.append(f"pinned {name} hash mismatch: {record['id']}")
        try:
            path = safe_child(repo_root, record["path"])
            if not path.is_file():
                errors.append(f"missing {name} file: {record['path']}")
            elif path.stat().st_size != record["size"] or sha256_file(path) != record["sha256"]:
                errors.append(f"tampered {name} file: {record['path']}")
        except (OSError, ValueError) as exc:
            errors.append(f"unsafe {name} path {record['path']}: {exc}")
    return records


def verify(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        payload = read_json(manifest_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError) as exc:
        return {"valid": False, "errors": [f"manifest unreadable: {exc}"]}
    constants = manifest_constants()
    if set(payload) != {*constants, "source_count", "artifact_count", "total_artifact_bytes", "sources", "artifacts"}:
        errors.append("manifest top-level schema mismatch")
    for field, expected in constants.items():
        if type(payload.get(field)) is not type(expected) or payload.get(field) != expected:
            errors.append(f"invalid manifest {field}")
    source_rows = source_contract(repo_root)
    artifact_rows = artifact_contract(repo_root)
    sources = _validate_collection(payload, "sources", source_rows, repo_root, errors)
    artifacts = _validate_collection(payload, "artifacts", artifact_rows, repo_root, errors)
    for field, expected in (("source_count", len(source_rows)), ("artifact_count", len(artifact_rows))):
        if type(payload.get(field)) is not int or payload.get(field) != expected:
            errors.append(f"{field} mismatch")
    recorded_bytes = sum(
        record["size"] for record in artifacts if type(record.get("size")) is int
    )
    if type(payload.get("total_artifact_bytes")) is not int or payload.get("total_artifact_bytes") != recorded_bytes:
        errors.append("total_artifact_bytes mismatch")
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "source_count": len(sources),
            "artifact_count": len(artifacts),
        }
    try:
        # Cheap pinned/type-strict checks run before the expensive historical regeneration.
        audit = build_audit(repo_root)
        if (repo_root / AUDIT_RELATIVE_PATH).read_text(encoding="utf-8") != canonical_json_text(audit):
            raise ValueError("WP27-R2 type-strict audit differs from regenerated evidence")
        report = render_report(sha256_file(repo_root / AUDIT_RELATIVE_PATH), audit["exact_int_fields_checked"])
        if (repo_root / REPORT_RELATIVE_PATH).read_text(encoding="utf-8") != report:
            raise ValueError("WP27-R2 report differs from verified evidence")
        _verify_r1_chain(repo_root, raw_root)
        # Re-check pins after the long historical verification to catch mid-run substitution.
        validate_pinned_r1_files(repo_root)
    except (FileNotFoundError, json.JSONDecodeError, KeyError, OSError, TypeError, ValueError) as exc:
        errors.append(f"semantic verification failed: {exc}")
    return {
        "valid": not errors,
        "errors": errors,
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "effective_layout_sha256": R1_LAYOUT_SHA256,
        "status": payload.get("status"),
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, required=True)
        command.add_argument("--raw-root", type=Path, required=True)
    commands.choices["verify"].add_argument(
        "--manifest", type=Path, default=Path(MANIFEST_RELATIVE_PATH)
    )
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    raw_root = args.raw_root.resolve()
    if args.command == "build":
        result = build(repo_root, raw_root)
    else:
        manifest = args.manifest
        if not manifest.is_absolute():
            manifest = repo_root / manifest
        result = verify(manifest, repo_root, raw_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command != "verify" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
