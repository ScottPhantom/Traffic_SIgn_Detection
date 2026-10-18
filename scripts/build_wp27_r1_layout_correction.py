# ruff: noqa: E501
"""Build and verify the append-only M0-WP27-R1 layout-status correction."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

INITIAL_BUILDER_PATH = Path(__file__).with_name("build_wp27_remaining_edge_review_batch.py")
INITIAL_SPEC = importlib.util.spec_from_file_location("wp27_r1_immutable_initial", INITIAL_BUILDER_PATH)
assert INITIAL_SPEC is not None and INITIAL_SPEC.loader is not None
initial = importlib.util.module_from_spec(INITIAL_SPEC)
sys.modules[INITIAL_SPEC.name] = initial
INITIAL_SPEC.loader.exec_module(initial)

PACKAGE = "M0-WP27-R1-LAYOUT-STATUS-CORRECTION"
STATUS = "WP27_R1_AWAITING_INDEPENDENT_QA"
EVIDENCE_BOUNDARY = (
    "WP27_R1_LAYOUT_STATUS_ONLY_CORRECTION_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_"
    "NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING"
)
EXPECTED_LAYOUT_STATUS = "PASS_COMPLETE_250_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"
STALE_LAYOUT_STATUS = "PASS_COMPLETE_176_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT"

INITIAL_MANIFEST_RELATIVE_PATH = "docs/review/generated/wp27_remaining_edge_batch_f_manifest.json"
INITIAL_LAYOUT_RELATIVE_PATH = "docs/review/generated/wp27_remaining_edge_batch_f_layout_audit.json"
INITIAL_BUILDER_RELATIVE_PATH = "scripts/build_wp27_remaining_edge_review_batch.py"
INITIAL_TEST_RELATIVE_PATH = "tests/test_wp27_remaining_edge_review_batch.py"
QA_RECORD_RELATIVE_PATH = "docs/review/wp27_r1_qa_correction_record.md"
R1_BUILDER_RELATIVE_PATH = "scripts/build_wp27_r1_layout_correction.py"
R1_TEST_RELATIVE_PATH = "tests/test_wp27_r1_layout_correction.py"

MANIFEST_RELATIVE_PATH = "docs/review/generated/wp27_r1_layout_correction_manifest.json"
LAYOUT_RELATIVE_PATH = "docs/review/generated/wp27_r1_remaining_edge_batch_f_layout_audit.json"
DELTA_RELATIVE_PATH = "docs/review/generated/wp27_r1_layout_semantic_delta.csv"
EFFECTIVE_ROSTER_RELATIVE_PATH = "docs/review/generated/wp27_r1_effective_artifact_roster.csv"
REPORT_RELATIVE_PATH = "docs/review/wp27_r1_layout_correction_report.md"

INITIAL_MANIFEST_SHA256 = "9f45437cbe47ec5968955dac4471eb0f33b8e43debd973428208facd431628e8"
INITIAL_LAYOUT_SHA256 = "5b0c938465b5af1c44cf276f0633692a2769b8db49eaac9cd9dbc221dc19c506"
INITIAL_BUILDER_SHA256 = "831ad27ab3fba6fc2f78b121db752654306586a8bbfffc315f5a6c6869b2ab73"
INITIAL_TEST_SHA256 = "fe73fc42df74a99ea0b20f24f9622d54f01c1338f3c48150042ab20471e7b9ce"
QA_RECORD_SHA256 = "8f87d72140d5e91d3f5c9142d3262044c92a9b1c03e57db4f54559616bb82c21"
README_SHA256 = "9005addc5b9952b36fca7f744489270cc7507bfaad0c6a02f305954915de01a7"
MODEL_SHA256 = "745cf3f6e9f5edfe32954866d93f07d9504f6bc2d4f3667c8b8f99f1c924b565"
PRESERVATION_SHA256 = "5ca3e769b9197cad19bcb75f553dd59fee6e3035e0cc86cd9693737f84a713d7"

EXPECTED_INITIAL_SOURCE_COUNT = 88
EXPECTED_INITIAL_ARTIFACT_COUNT = 56
EXPECTED_EFFECTIVE_ARTIFACT_COUNT = 56
EXPECTED_CHANGED_ARTIFACT_COUNT = 1
EXPECTED_PAIR_COUNT = 250
EXPECTED_PAGE_COUNT = 50
EXPECTED_PAIRS_PER_PAGE = 5
EXPECTED_PAGE_ROW_COUNTS = (5,) * 50

DELTA_FIELDS = ["json_pointer", "initial_value", "effective_value", "change_type"]
ROSTER_FIELDS = [
    "artifact_id",
    "initial_path",
    "initial_sha256",
    "effective_path",
    "effective_sha256",
    "relationship",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def safe_child(root: Path, relative_value: str) -> Path:
    if not isinstance(relative_value, str) or not relative_value or "\\" in relative_value:
        raise ValueError("manifest path must be a non-empty POSIX relative path")
    relative = Path(relative_value)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError(f"unsafe manifest path: {relative_value}")
    root_resolved = root.resolve()
    candidate = root / relative
    resolved = candidate.resolve(strict=False)
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValueError(f"manifest path escapes repository root: {relative_value}")
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"symlink is forbidden in package path: {relative_value}")
    return candidate


def _initial_manifest(repo_root: Path) -> dict[str, Any]:
    path = repo_root / INITIAL_MANIFEST_RELATIVE_PATH
    if sha256_file(path) != INITIAL_MANIFEST_SHA256:
        raise ValueError("immutable initial WP27 manifest hash mismatch")
    payload = read_json(path)
    if (
        payload.get("source_count") != EXPECTED_INITIAL_SOURCE_COUNT
        or payload.get("artifact_count") != EXPECTED_INITIAL_ARTIFACT_COUNT
        or len(payload.get("sources", [])) != EXPECTED_INITIAL_SOURCE_COUNT
        or len(payload.get("artifacts", [])) != EXPECTED_INITIAL_ARTIFACT_COUNT
    ):
        raise ValueError("immutable initial WP27 manifest roster/count mismatch")
    return payload


def source_contract(repo_root: Path) -> list[tuple[str, Path, str | None]]:
    manifest = _initial_manifest(repo_root)
    rows: list[tuple[str, Path, str | None]] = [
        (
            "wp27_initial_manifest",
            repo_root / INITIAL_MANIFEST_RELATIVE_PATH,
            INITIAL_MANIFEST_SHA256,
        )
    ]
    rows.extend(
        (f"wp27_initial_source__{record['id']}", repo_root / record["path"], record["sha256"])
        for record in manifest["sources"]
    )
    rows.extend(
        (f"wp27_initial_artifact__{record['id']}", repo_root / record["path"], record["sha256"])
        for record in manifest["artifacts"]
    )
    rows.extend(
        [
            (
                "wp27_initial_test",
                repo_root / INITIAL_TEST_RELATIVE_PATH,
                INITIAL_TEST_SHA256,
            ),
            ("readme_preservation_anchor", repo_root / "README.md", README_SHA256),
            (
                "model_preservation_anchor",
                repo_root / "models/VGG16_model.h5",
                MODEL_SHA256,
            ),
            ("wp27_r1_qa_record", repo_root / QA_RECORD_RELATIVE_PATH, QA_RECORD_SHA256),
            ("wp27_r1_builder", repo_root / R1_BUILDER_RELATIVE_PATH, None),
            ("wp27_r1_test", repo_root / R1_TEST_RELATIVE_PATH, None),
        ]
    )
    ids = [item_id for item_id, _path, _digest in rows]
    paths = [path.relative_to(repo_root).as_posix() for _item_id, path, _digest in rows]
    if len(ids) != len(set(ids)) or len(paths) != len(set(paths)):
        raise ValueError("WP27-R1 source contract IDs and paths must be unique")
    return rows


def artifact_contract(repo_root: Path) -> list[tuple[str, Path]]:
    return [
        ("corrected_layout_audit", repo_root / LAYOUT_RELATIVE_PATH),
        ("layout_semantic_delta", repo_root / DELTA_RELATIVE_PATH),
        ("effective_artifact_roster", repo_root / EFFECTIVE_ROSTER_RELATIVE_PATH),
        ("correction_report", repo_root / REPORT_RELATIVE_PATH),
    ]


def relative_record(path: Path, repo_root: Path, item_id: str) -> dict[str, Any]:
    checked = safe_child(repo_root, path.relative_to(repo_root).as_posix())
    if not checked.is_file():
        raise ValueError(f"package member is not a regular file: {path}")
    return {
        "id": item_id,
        "path": path.relative_to(repo_root).as_posix(),
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
    }


def validate_initial_package(repo_root: Path, raw_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _initial_manifest(repo_root)
    anchors = {
        INITIAL_LAYOUT_RELATIVE_PATH: INITIAL_LAYOUT_SHA256,
        INITIAL_BUILDER_RELATIVE_PATH: INITIAL_BUILDER_SHA256,
        INITIAL_TEST_RELATIVE_PATH: INITIAL_TEST_SHA256,
        "README.md": README_SHA256,
        "models/VGG16_model.h5": MODEL_SHA256,
        "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json": PRESERVATION_SHA256,
    }
    for relative, expected in anchors.items():
        if sha256_file(repo_root / relative) != expected:
            raise ValueError(f"immutable preservation anchor mismatch: {relative}")
    proof = read_json(
        repo_root
        / "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json"
    )
    if proof.get("unchanged") is not True:
        raise ValueError("raw source-preservation proof is not unchanged=true")
    for collection in ("sources", "artifacts"):
        for record in manifest[collection]:
            path = safe_child(repo_root, record["path"])
            if not path.is_file() or path.stat().st_size != record["size"]:
                raise ValueError(f"immutable WP27 {collection} member missing/size mismatch: {record['id']}")
            if sha256_file(path) != record["sha256"]:
                raise ValueError(f"immutable WP27 {collection} member hash mismatch: {record['id']}")
    initial_result = initial.verify(repo_root / INITIAL_MANIFEST_RELATIVE_PATH, repo_root, raw_root)
    if initial_result.get("valid") is not True or initial_result.get("errors") != []:
        raise ValueError(f"historical WP27 verifier no longer accepts its immutable package: {initial_result}")
    layout = read_json(repo_root / INITIAL_LAYOUT_RELATIVE_PATH)
    if (
        layout.get("status") != STALE_LAYOUT_STATUS
        or layout.get("pair_count") != EXPECTED_PAIR_COUNT
        or layout.get("page_count") != EXPECTED_PAGE_COUNT
    ):
        raise ValueError("initial WP27 layout no longer reproduces the exact QA finding")
    return manifest, layout


def corrected_layout(initial_layout: dict[str, Any]) -> dict[str, Any]:
    corrected = deepcopy(initial_layout)
    corrected["status"] = EXPECTED_LAYOUT_STATUS
    return corrected


def semantic_diff(before: Any, after: Any, pointer: str = "") -> list[tuple[str, Any, Any]]:
    if isinstance(before, dict) and isinstance(after, dict):
        if set(before) != set(after):
            return [(pointer or "/", before, after)]
        rows: list[tuple[str, Any, Any]] = []
        for key in sorted(before):
            rows.extend(semantic_diff(before[key], after[key], f"{pointer}/{key}"))
        return rows
    if isinstance(before, list) and isinstance(after, list):
        if len(before) != len(after):
            return [(pointer or "/", before, after)]
        rows = []
        for index, (left, right) in enumerate(zip(before, after, strict=True)):
            rows.extend(semantic_diff(left, right, f"{pointer}/{index}"))
        return rows
    return [] if before == after else [(pointer or "/", before, after)]


def expected_delta_rows(initial_layout: dict[str, Any], effective_layout: dict[str, Any]) -> list[dict[str, str]]:
    diff = semantic_diff(initial_layout, effective_layout)
    if diff != [("/status", STALE_LAYOUT_STATUS, EXPECTED_LAYOUT_STATUS)]:
        raise ValueError("WP27-R1 corrected layout must differ from initial layout only at /status")
    return [
        {
            "json_pointer": "/status",
            "initial_value": STALE_LAYOUT_STATUS,
            "effective_value": EXPECTED_LAYOUT_STATUS,
            "change_type": "REPLACE_STALE_INHERITED_COUNT_WITH_EXACT_PAIR_COUNT",
        }
    ]


def expected_effective_roster(
    initial_manifest: dict[str, Any], effective_layout_sha256: str
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for record in initial_manifest["artifacts"]:
        if record["id"] == "layout_audit":
            rows.append(
                {
                    "artifact_id": record["id"],
                    "initial_path": record["path"],
                    "initial_sha256": record["sha256"],
                    "effective_path": LAYOUT_RELATIVE_PATH,
                    "effective_sha256": effective_layout_sha256,
                    "relationship": "CORRECTED_STATUS_FIELD_ONLY",
                }
            )
        else:
            rows.append(
                {
                    "artifact_id": record["id"],
                    "initial_path": record["path"],
                    "initial_sha256": record["sha256"],
                    "effective_path": record["path"],
                    "effective_sha256": record["sha256"],
                    "relationship": "BYTE_IDENTICAL_IMMUTABLE_INITIAL_ARTIFACT",
                }
            )
    if len(rows) != EXPECTED_EFFECTIVE_ARTIFACT_COUNT:
        raise ValueError("effective WP27-R1 roster must contain exactly 56 artifacts")
    if sum(row["relationship"] == "CORRECTED_STATUS_FIELD_ONLY" for row in rows) != 1:
        raise ValueError("effective WP27-R1 roster must contain exactly one corrected artifact")
    return rows


def validate_effective_layout(layout: dict[str, Any]) -> None:
    if set(layout) != {
        "all_bbox_context_rendered",
        "all_bounds_fit",
        "all_decisions_recorded",
        "all_headers_complete",
        "all_text_complete",
        "evidence_boundary",
        "page_count",
        "pages",
        "pair_count",
        "pairs_per_page",
        "schema_version",
        "status",
    }:
        raise ValueError("WP27-R1 layout top-level schema mismatch")
    if (
        layout.get("schema_version") != 1
        or layout.get("status") != EXPECTED_LAYOUT_STATUS
        or not isinstance(layout.get("status"), str)
        or layout.get("pair_count") != EXPECTED_PAIR_COUNT
        or isinstance(layout.get("pair_count"), bool)
        or layout.get("page_count") != EXPECTED_PAGE_COUNT
        or isinstance(layout.get("page_count"), bool)
        or layout.get("pairs_per_page") != EXPECTED_PAIRS_PER_PAGE
        or layout.get("evidence_boundary") != initial.EVIDENCE_BOUNDARY
        or layout.get("all_headers_complete") is not True
        or layout.get("all_text_complete") is not True
        or layout.get("all_bounds_fit") is not True
        or layout.get("all_bbox_context_rendered") is not True
        or layout.get("all_decisions_recorded") is not True
        or not isinstance(layout.get("pages"), list)
        or len(layout["pages"]) != EXPECTED_PAGE_COUNT
    ):
        raise ValueError("WP27-R1 exact 250-pair layout contract mismatch")
    seen: list[str] = []
    for page_number, page in enumerate(layout["pages"], start=1):
        if (
            not isinstance(page, dict)
            or page.get("page") != page_number
            or page.get("path")
            != f"docs/review/assets/wp27/remaining_edge_batch_f/page_{page_number:03d}.jpg"
            or page.get("row_count") != EXPECTED_PAGE_ROW_COUNTS[page_number - 1]
            or not isinstance(page.get("rows"), list)
            or len(page["rows"]) != EXPECTED_PAGE_ROW_COUNTS[page_number - 1]
        ):
            raise ValueError(f"WP27-R1 layout page {page_number} identity/coverage mismatch")
        for slot, row in enumerate(page["rows"], start=1):
            if (
                not isinstance(row, dict)
                or row.get("slot") != slot
                or row.get("batch_position") != (page_number - 1) * EXPECTED_PAIRS_PER_PAGE + slot
                or row.get("decision_recorded") is not True
                or row.get("all_bounds_fit") is not True
                or row.get("text_complete") is not True
                or row.get("bbox_overlay_rendered") is not True
                or not isinstance(row.get("edge_id"), str)
            ):
                raise ValueError(f"WP27-R1 layout page {page_number} slot {slot} mismatch")
            seen.append(row["edge_id"])
    if len(seen) != EXPECTED_PAIR_COUNT or len(set(seen)) != EXPECTED_PAIR_COUNT:
        raise ValueError("WP27-R1 layout must cover 250 unique edge IDs exactly once")


def render_report(
    initial_manifest: dict[str, Any],
    effective_layout_sha256: str,
    delta_sha256: str,
    roster_sha256: str,
) -> str:
    return f"""# M0-WP27-R1 — layout-status correction

Status: `{STATUS}`  
Boundary: `{EVIDENCE_BOUNDARY}`

Independent QA failed the initial WP27 package with exactly one `P2` finding and zero
`P0`/`P1`/`P3` findings. The initial layout correctly records 250 pairs over 50 pages, but its
status retained the inherited WP15 value `{STALE_LAYOUT_STATUS}`. The historical WP27 verifier
also explicitly accepted and required that stale value.

## Append-only correction

- Initial WP27 manifest remains immutable at SHA-256 `{INITIAL_MANIFEST_SHA256}`.
- Initial WP27 layout remains immutable at SHA-256 `{INITIAL_LAYOUT_SHA256}`.
- Initial builder/test remain immutable at SHA-256 `{INITIAL_BUILDER_SHA256}` and
  `{INITIAL_TEST_SHA256}`.
- Effective layout SHA-256 is `{effective_layout_sha256}` and its exact status is
  `{EXPECTED_LAYOUT_STATUS}` with `pair_count=250` and `page_count=50`.
- Semantic delta SHA-256 is `{delta_sha256}`; it proves the only JSON-value change is `/status`.
- Effective 56-artifact roster SHA-256 is `{roster_sha256}`; 55 artifacts retain their exact
  initial path/hash and only `layout_audit` resolves to the corrected layout evidence.

The immutable semantic decisions, selection, source lineage, annotations, atlas index and all 50
atlas JPEGs are the same initial files and hashes. No pixel, edge decision, rationale, source path,
raw image, raw label or provenance artifact was changed.

## Governance boundary

- Canonical WP5 remains 3,172 PENDING edges and all 589 sequences remain PENDING.
- 646 residual PENDING edges remain outside the provisional overlays; two touch quarantined stem
  `0248`, leaving 644 review-eligible residual edges.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.
- This correction does not create final/transitive group truth and does not authorize WP28,
  upload, deploy, publish or real-vehicle control.

Initial package roster: {initial_manifest['source_count']} sources and
{initial_manifest['artifact_count']} non-manifest artifacts.
"""


def build_manifest(repo_root: Path) -> dict[str, Any]:
    sources = [
        relative_record(path, repo_root, item_id)
        for item_id, path, _digest in source_contract(repo_root)
    ]
    artifacts = [
        relative_record(path, repo_root, item_id)
        for item_id, path in artifact_contract(repo_root)
    ]
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
        "initial_manifest_sha256": INITIAL_MANIFEST_SHA256,
        "initial_layout_sha256": INITIAL_LAYOUT_SHA256,
        "initial_source_count": EXPECTED_INITIAL_SOURCE_COUNT,
        "initial_artifact_count": EXPECTED_INITIAL_ARTIFACT_COUNT,
        "effective_artifact_count": EXPECTED_EFFECTIVE_ARTIFACT_COUNT,
        "changed_artifact_count": EXPECTED_CHANGED_ARTIFACT_COUNT,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE",
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "total_artifact_bytes": sum(record["size"] for record in artifacts),
        "sources": sources,
        "artifacts": artifacts,
    }


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    initial_manifest, initial_layout = validate_initial_package(repo_root, raw_root)
    effective_layout = corrected_layout(initial_layout)
    validate_effective_layout(effective_layout)
    write_json(repo_root / LAYOUT_RELATIVE_PATH, effective_layout)
    delta_rows = expected_delta_rows(initial_layout, effective_layout)
    write_csv(repo_root / DELTA_RELATIVE_PATH, delta_rows, DELTA_FIELDS)
    effective_layout_sha256 = sha256_file(repo_root / LAYOUT_RELATIVE_PATH)
    roster = expected_effective_roster(initial_manifest, effective_layout_sha256)
    write_csv(repo_root / EFFECTIVE_ROSTER_RELATIVE_PATH, roster, ROSTER_FIELDS)
    delta_sha256 = sha256_file(repo_root / DELTA_RELATIVE_PATH)
    roster_sha256 = sha256_file(repo_root / EFFECTIVE_ROSTER_RELATIVE_PATH)
    (repo_root / REPORT_RELATIVE_PATH).write_text(
        render_report(initial_manifest, effective_layout_sha256, delta_sha256, roster_sha256),
        encoding="utf-8",
    )
    manifest = build_manifest(repo_root)
    write_json(repo_root / MANIFEST_RELATIVE_PATH, manifest)
    return {
        "status": STATUS,
        "manifest_sha256": sha256_file(repo_root / MANIFEST_RELATIVE_PATH),
        "corrected_layout_sha256": effective_layout_sha256,
        "source_count": manifest["source_count"],
        "artifact_count": manifest["artifact_count"],
        "effective_artifact_count": EXPECTED_EFFECTIVE_ARTIFACT_COUNT,
        "changed_artifact_count": EXPECTED_CHANGED_ARTIFACT_COUNT,
    }


def _expected_records(
    contract: list[tuple[str, Path, str | None]] | list[tuple[str, Path]], repo_root: Path
) -> list[tuple[str, str]]:
    return [(row[0], row[1].relative_to(repo_root).as_posix()) for row in contract]


def _validate_collection(
    payload: dict[str, Any],
    name: str,
    expected: list[tuple[str, str]],
    repo_root: Path,
    errors: list[str],
) -> list[dict[str, Any]]:
    records = payload.get(name)
    if not isinstance(records, list):
        errors.append(f"manifest {name} must be a list")
        return []
    if [(record.get("id"), record.get("path")) for record in records if isinstance(record, dict)] != expected:
        errors.append(f"manifest {name} exact ID/path roster mismatch")
    if len(records) != len(expected) or any(not isinstance(record, dict) for record in records):
        errors.append(f"manifest {name} count/type mismatch")
        return [record for record in records if isinstance(record, dict)]
    for record in records:
        if set(record) != {"id", "path", "sha256", "size"}:
            errors.append(f"manifest {name} record schema mismatch: {record.get('id')}")
            continue
        if (
            not isinstance(record.get("id"), str)
            or not isinstance(record.get("path"), str)
            or not isinstance(record.get("sha256"), str)
            or len(record["sha256"]) != 64
            or not isinstance(record.get("size"), int)
            or isinstance(record.get("size"), bool)
            or record["size"] < 0
        ):
            errors.append(f"manifest {name} record type mismatch: {record.get('id')}")
            continue
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
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        return {"valid": False, "errors": [f"manifest unreadable: {exc}"]}
    expected_top = {
        "schema_version",
        "package",
        "status",
        "evidence_boundary",
        "gate0",
        "d02_status",
        "canonical_wp5_pending_unchanged",
        "all_wp5_sequences_pending",
        "residual_pending_edges",
        "review_eligible_residual_edges",
        "quarantined_residual_edges",
        "split_authorized",
        "training_authorized",
        "final_group_truth_created",
        "transitive_grouping_created",
        "wp28_started",
        "initial_manifest_sha256",
        "initial_layout_sha256",
        "initial_source_count",
        "initial_artifact_count",
        "effective_artifact_count",
        "changed_artifact_count",
        "manifest_path",
        "manifest_self_in_artifact_count",
        "artifact_count_semantics",
        "source_count",
        "artifact_count",
        "total_artifact_bytes",
        "sources",
        "artifacts",
    }
    if set(payload) != expected_top:
        errors.append("manifest top-level schema mismatch")
    constants = {
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
        "initial_manifest_sha256": INITIAL_MANIFEST_SHA256,
        "initial_layout_sha256": INITIAL_LAYOUT_SHA256,
        "initial_source_count": EXPECTED_INITIAL_SOURCE_COUNT,
        "initial_artifact_count": EXPECTED_INITIAL_ARTIFACT_COUNT,
        "effective_artifact_count": EXPECTED_EFFECTIVE_ARTIFACT_COUNT,
        "changed_artifact_count": EXPECTED_CHANGED_ARTIFACT_COUNT,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": "EXCLUDES_MANIFEST_FILE",
    }
    for field, expected in constants.items():
        if payload.get(field) != expected:
            errors.append(f"invalid manifest {field}")
    try:
        source_rows = source_contract(repo_root)
        artifact_rows = artifact_contract(repo_root)
    except (FileNotFoundError, KeyError, OSError, TypeError, ValueError) as exc:
        return {
            "valid": False,
            "errors": [*errors, f"source/artifact contract unavailable: {exc}"],
        }
    sources = _validate_collection(
        payload, "sources", _expected_records(source_rows, repo_root), repo_root, errors
    )
    artifacts = _validate_collection(
        payload, "artifacts", _expected_records(artifact_rows, repo_root), repo_root, errors
    )
    if payload.get("source_count") != len(source_rows) or len(sources) != len(source_rows):
        errors.append("source_count mismatch")
    if payload.get("artifact_count") != len(artifact_rows) or len(artifacts) != len(artifact_rows):
        errors.append("artifact_count mismatch")
    recorded_bytes = sum(
        record.get("size", -1)
        for record in artifacts
        if isinstance(record.get("size"), int) and not isinstance(record.get("size"), bool)
    )
    if payload.get("total_artifact_bytes") != recorded_bytes:
        errors.append("total_artifact_bytes mismatch")
    pinned = {item_id: digest for item_id, _path, digest in source_rows}
    for record in sources:
        if pinned.get(record.get("id")) is not None and record.get("sha256") != pinned[record["id"]]:
            errors.append(f"pinned source hash mismatch: {record.get('id')}")
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "source_count": len(sources),
            "artifact_count": len(artifacts),
        }
    try:
        # Reject an invalid effective correction before paying the cost of the historical
        # verifier's 50-page clean regeneration. The immutable initial hashes are still checked
        # first, and every valid R1 package must subsequently pass the historical verifier.
        initial_manifest = _initial_manifest(repo_root)
        if sha256_file(repo_root / INITIAL_LAYOUT_RELATIVE_PATH) != INITIAL_LAYOUT_SHA256:
            raise ValueError("immutable initial WP27 layout hash mismatch")
        initial_layout = read_json(repo_root / INITIAL_LAYOUT_RELATIVE_PATH)
        effective_layout = read_json(repo_root / LAYOUT_RELATIVE_PATH)
        validate_effective_layout(effective_layout)
        expected_delta = expected_delta_rows(initial_layout, effective_layout)
        if expected_delta != read_csv(
            repo_root / DELTA_RELATIVE_PATH
        ):
            raise ValueError("layout semantic-delta record mismatch")
        verified_manifest, verified_layout = validate_initial_package(repo_root, raw_root)
        if verified_manifest != initial_manifest or verified_layout != initial_layout:
            raise ValueError("initial WP27 package changed during R1 verification")
        expected_roster = expected_effective_roster(
            initial_manifest, sha256_file(repo_root / LAYOUT_RELATIVE_PATH)
        )
        actual_roster = read_csv(repo_root / EFFECTIVE_ROSTER_RELATIVE_PATH)
        if actual_roster != expected_roster:
            raise ValueError("effective 56-artifact roster mismatch")
        if sum(
            row["relationship"] == "BYTE_IDENTICAL_IMMUTABLE_INITIAL_ARTIFACT"
            for row in actual_roster
        ) != 55:
            raise ValueError("effective roster must preserve exactly 55 byte-identical artifacts")
        for row in actual_roster:
            initial_path = safe_child(repo_root, row["initial_path"])
            effective_path = safe_child(repo_root, row["effective_path"])
            if sha256_file(initial_path) != row["initial_sha256"]:
                raise ValueError(f"initial effective-roster hash mismatch: {row['artifact_id']}")
            if sha256_file(effective_path) != row["effective_sha256"]:
                raise ValueError(f"effective-roster hash mismatch: {row['artifact_id']}")
            if row["relationship"] == "BYTE_IDENTICAL_IMMUTABLE_INITIAL_ARTIFACT" and (
                row["initial_path"] != row["effective_path"]
                or row["initial_sha256"] != row["effective_sha256"]
            ):
                raise ValueError(f"unaffected artifact is not byte-identical: {row['artifact_id']}")
        report = render_report(
            initial_manifest,
            sha256_file(repo_root / LAYOUT_RELATIVE_PATH),
            sha256_file(repo_root / DELTA_RELATIVE_PATH),
            sha256_file(repo_root / EFFECTIVE_ROSTER_RELATIVE_PATH),
        )
        if (repo_root / REPORT_RELATIVE_PATH).read_text(encoding="utf-8") != report:
            raise ValueError("WP27-R1 report differs from verified evidence")
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        errors.append(f"semantic verification failed: {exc}")
    return {
        "valid": not errors,
        "errors": errors,
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "effective_artifact_count": EXPECTED_EFFECTIVE_ARTIFACT_COUNT,
        "changed_artifact_count": EXPECTED_CHANGED_ARTIFACT_COUNT,
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
