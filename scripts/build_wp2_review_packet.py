"""Build reproducible, non-authoritative evidence for the M0-WP2 review packet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

STRONG_THRESHOLDS = {
    "thumbnail_mae_max": 12.0,
    "dhash_distance_max": 8,
    "rgb_histogram_cosine_min": 0.98,
}
UNCERTAIN_THRESHOLDS = {
    "thumbnail_mae_max": 28.0,
    "dhash_distance_max": 18,
    "rgb_histogram_cosine_min": 0.94,
}
EXPECTED_CLASS_IDS = frozenset(range(52))
RARE_SCOPE_BOX_COUNT_MAX_EXCLUSIVE = 50
D04_ALLOWED_OPTIONS = (
    "collect_more",
    "merge_after_semantic_approval",
    "report_only",
    "out_of_scope",
)
D04_CLASS_REQUIRED_FIELDS = frozenset(
    {
        "class_id",
        "sign_code",
        "image_count",
        "box_count",
        "risk_band",
        "status",
        "selected_option",
        "reviewer",
        "decided_at",
        "rationale",
        "evidence_links",
        "history",
    }
)
D04_HISTORY_ITEM_REQUIRED_FIELDS = frozenset({"changed_at", "changed_by", "previous"})
D04_HISTORY_PREVIOUS_REQUIRED_FIELDS = frozenset(
    {"status", "selected_option", "reviewer", "decided_at", "rationale", "evidence_links"}
)
TRIMMED_NONEMPTY_PATTERN = r"^\S(?:.*\S)?$"
AUDIT_TIMESTAMP_PATTERN_TEXT = (
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
AUDIT_TIMESTAMP_PATTERN = re.compile(AUDIT_TIMESTAMP_PATTERN_TEXT)


@dataclass(frozen=True)
class ImageSignature:
    thumbnail: np.ndarray
    dhash: np.ndarray
    histogram: np.ndarray
    dimensions: tuple[int, int]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_exact_class_ids(
    rows: list[dict[str, Any]],
    *,
    source_name: str,
    id_key: str = "class_id",
) -> None:
    class_ids: list[int] = []
    for row_number, row in enumerate(rows, start=1):
        if id_key not in row or row[id_key] in {None, ""}:
            raise ValueError(f"{source_name} row {row_number} is missing {id_key}")
        try:
            class_ids.append(int(row[id_key]))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{source_name} row {row_number} has invalid {id_key}: {row[id_key]!r}"
            ) from exc

    counts = Counter(class_ids)
    duplicates = sorted(class_id for class_id, count in counts.items() if count > 1)
    observed = set(class_ids)
    missing = sorted(EXPECTED_CLASS_IDS - observed)
    extra = sorted(observed - EXPECTED_CLASS_IDS)
    if duplicates or missing or extra or len(class_ids) != len(EXPECTED_CLASS_IDS):
        raise ValueError(
            f"{source_name} must contain each class_id 0..51 exactly once; "
            f"duplicates={duplicates}, missing={missing}, extra={extra}, rows={len(class_ids)}"
        )


def validate_support_rows(rows: list[dict[str, Any]], *, source_name: str) -> None:
    validate_exact_class_ids(rows, source_name=source_name)
    required_fields = {
        "class_id",
        "sign_code",
        "name_en",
        "name_vi",
        "image_count",
        "box_count",
        "train_image_count",
        "test_image_count",
        "unsplit_image_count",
    }
    for row in rows:
        missing_fields = sorted(required_fields - row.keys())
        if missing_fields:
            raise ValueError(
                f"{source_name} class_id {row.get('class_id')} is missing fields {missing_fields}"
            )
        for field in (
            "image_count",
            "box_count",
            "train_image_count",
            "test_image_count",
            "unsplit_image_count",
        ):
            try:
                value = int(row[field])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"{source_name} class_id {row['class_id']} has invalid {field}"
                ) from exc
            if value < 0:
                raise ValueError(
                    f"{source_name} class_id {row['class_id']} has negative {field}"
                )


def require_trimmed_nonempty_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be trimmed and non-empty")
    return value


def parse_audit_timestamp(value: Any, *, field_name: str) -> datetime:
    timestamp = require_trimmed_nonempty_string(value, field_name=field_name)
    if not AUDIT_TIMESTAMP_PATTERN.fullmatch(timestamp):
        raise ValueError(f"{field_name} must be an RFC 3339 timestamp with timezone")
    normalized = timestamp[:-1] + "+00:00" if timestamp.endswith("Z") else timestamp
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} is not a valid calendar timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must include an explicit timezone")
    return parsed


def validate_evidence_links(
    value: Any,
    *,
    field_name: str,
    require_nonempty: bool,
) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    if require_nonempty and not value:
        raise ValueError(f"{field_name} must contain at least one reference")
    for index, reference in enumerate(value):
        require_trimmed_nonempty_string(
            reference,
            field_name=f"{field_name}[{index}]",
        )


def validate_previous_d04_snapshot(snapshot: Any, *, field_name: str) -> None:
    if not isinstance(snapshot, dict):
        raise ValueError(f"{field_name} must be an object")
    observed_fields = set(snapshot)
    if observed_fields != D04_HISTORY_PREVIOUS_REQUIRED_FIELDS:
        raise ValueError(
            f"{field_name} must contain exactly {sorted(D04_HISTORY_PREVIOUS_REQUIRED_FIELDS)}; "
            f"missing={sorted(D04_HISTORY_PREVIOUS_REQUIRED_FIELDS - observed_fields)}, "
            f"extra={sorted(observed_fields - D04_HISTORY_PREVIOUS_REQUIRED_FIELDS)}"
        )
    status = snapshot["status"]
    if status not in {"PENDING", "RESOLVED"}:
        raise ValueError(f"{field_name}.status must be PENDING or RESOLVED")
    selected_option = snapshot["selected_option"]
    if selected_option is not None and selected_option not in D04_ALLOWED_OPTIONS:
        raise ValueError(f"{field_name}.selected_option is invalid")
    for text_field in ("reviewer", "rationale"):
        value = snapshot[text_field]
        if value is not None:
            require_trimmed_nonempty_string(
                value,
                field_name=f"{field_name}.{text_field}",
            )
    if snapshot["decided_at"] is not None:
        parse_audit_timestamp(
            snapshot["decided_at"],
            field_name=f"{field_name}.decided_at",
        )
    validate_evidence_links(
        snapshot["evidence_links"],
        field_name=f"{field_name}.evidence_links",
        require_nonempty=status == "RESOLVED",
    )
    if status == "RESOLVED":
        if selected_option is None:
            raise ValueError(f"{field_name}.selected_option is required when RESOLVED")
        require_trimmed_nonempty_string(
            snapshot["reviewer"],
            field_name=f"{field_name}.reviewer",
        )
        parse_audit_timestamp(
            snapshot["decided_at"],
            field_name=f"{field_name}.decided_at",
        )
        require_trimmed_nonempty_string(
            snapshot["rationale"],
            field_name=f"{field_name}.rationale",
        )


def validate_d04_history(history: Any, *, class_id: str) -> None:
    if not isinstance(history, list):
        raise ValueError(f"D-04 class {class_id} history must be a list")
    previous_changed_at: datetime | None = None
    for index, item in enumerate(history):
        field_name = f"D-04 class {class_id} history[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} must be an object")
        observed_fields = set(item)
        if observed_fields != D04_HISTORY_ITEM_REQUIRED_FIELDS:
            raise ValueError(
                f"{field_name} must contain exactly "
                f"{sorted(D04_HISTORY_ITEM_REQUIRED_FIELDS)}; "
                f"missing={sorted(D04_HISTORY_ITEM_REQUIRED_FIELDS - observed_fields)}, "
                f"extra={sorted(observed_fields - D04_HISTORY_ITEM_REQUIRED_FIELDS)}"
            )
        changed_at = parse_audit_timestamp(
            item["changed_at"],
            field_name=f"{field_name}.changed_at",
        )
        if previous_changed_at is not None and changed_at <= previous_changed_at:
            raise ValueError(f"{field_name}.changed_at must be strictly append-ordered")
        previous_changed_at = changed_at
        require_trimmed_nonempty_string(
            item["changed_by"],
            field_name=f"{field_name}.changed_by",
        )
        validate_previous_d04_snapshot(
            item["previous"],
            field_name=f"{field_name}.previous",
        )


def image_signature(path: Path) -> ImageSignature:
    with Image.open(path) as image:
        rgb_image = image.convert("RGB")
        thumbnail = np.asarray(
            rgb_image.resize((32, 18), Image.Resampling.BILINEAR),
            dtype=np.float32,
        )
        gray = np.asarray(
            rgb_image.convert("L").resize((9, 8), Image.Resampling.BILINEAR),
            dtype=np.float32,
        )
        dhash = (gray[:, 1:] > gray[:, :-1]).ravel()
        histogram_parts = []
        for channel in range(3):
            histogram, _ = np.histogram(
                thumbnail[:, :, channel], bins=16, range=(0, 256)
            )
            histogram_parts.extend(histogram)
        histogram_array = np.asarray(histogram_parts, dtype=np.float64)
        norm = float(np.linalg.norm(histogram_array))
        if norm:
            histogram_array /= norm
        return ImageSignature(thumbnail, dhash, histogram_array, image.size)


def similarity_metrics(left: ImageSignature, right: ImageSignature) -> dict[str, Any]:
    return {
        "same_dimensions": left.dimensions == right.dimensions,
        "thumbnail_mae": float(np.mean(np.abs(left.thumbnail - right.thumbnail))),
        "dhash_distance": int(np.count_nonzero(left.dhash != right.dhash)),
        "rgb_histogram_cosine": float(np.dot(left.histogram, right.histogram)),
    }


def classify_similarity(metrics: dict[str, Any]) -> str:
    if not metrics["same_dimensions"]:
        return "adjacency_only"
    if (
        metrics["thumbnail_mae"] <= STRONG_THRESHOLDS["thumbnail_mae_max"]
        and metrics["dhash_distance"] <= STRONG_THRESHOLDS["dhash_distance_max"]
        and metrics["rgb_histogram_cosine"]
        >= STRONG_THRESHOLDS["rgb_histogram_cosine_min"]
    ):
        return "strong_candidate"
    if (
        metrics["thumbnail_mae"] <= UNCERTAIN_THRESHOLDS["thumbnail_mae_max"]
        and metrics["dhash_distance"] <= UNCERTAIN_THRESHOLDS["dhash_distance_max"]
        and metrics["rgb_histogram_cosine"]
        >= UNCERTAIN_THRESHOLDS["rgb_histogram_cosine_min"]
    ):
        return "uncertain"
    return "adjacency_only"


def build_candidate_clusters(
    edge_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    parent: dict[str, str] = {}

    def find(stem: str) -> str:
        parent.setdefault(stem, stem)
        if parent[stem] != stem:
            parent[stem] = find(parent[stem])
        return parent[stem]

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for row in edge_rows:
        if row["proxy_status"] == "strong_candidate":
            union(row["left_stem"], row["right_stem"])

    members_by_root: dict[str, list[str]] = defaultdict(list)
    for stem in parent:
        members_by_root[find(stem)].append(stem)

    ordered_members = sorted(
        (sorted(members) for members in members_by_root.values()), key=lambda item: item[0]
    )
    cluster_by_stem: dict[str, str] = {}
    cluster_rows: list[dict[str, Any]] = []
    for index, members in enumerate(ordered_members, start=1):
        cluster_id = f"proxy_sequence_{index:04d}"
        for stem in members:
            cluster_by_stem[stem] = cluster_id
        strong_edges = [
            row
            for row in edge_rows
            if row["proxy_status"] == "strong_candidate"
            and row["left_stem"] in members
            and row["right_stem"] in members
        ]
        cluster_rows.append(
            {
                "proxy_sequence_id": cluster_id,
                "evidence_status": "PROXY_ONLY_NOT_GROUP_TRUTH",
                "member_count": len(members),
                "first_stem": members[0],
                "last_stem": members[-1],
                "members": ";".join(members),
                "strong_edge_count": len(strong_edges),
                "cross_split_strong_edges": sum(
                    row["cross_split"] == "True" for row in strong_edges
                ),
            }
        )
    return cluster_rows, cluster_by_stem


def build_grouping_evidence(
    audit_dir: Path,
    images_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    adjacency_rows = read_csv(audit_dir / "adjacent_pair_leakage.csv")
    signature_cache: dict[str, ImageSignature] = {}

    def signature(stem: str) -> ImageSignature:
        if stem not in signature_cache:
            signature_cache[stem] = image_signature(images_dir / f"{stem}.jpg")
        return signature_cache[stem]

    edge_rows: list[dict[str, Any]] = []
    for row in adjacency_rows:
        metrics = similarity_metrics(signature(row["left_stem"]), signature(row["right_stem"]))
        edge_rows.append(
            {
                "left_stem": row["left_stem"],
                "left_split": row["left_split"],
                "right_stem": row["right_stem"],
                "right_split": row["right_split"],
                "cross_split": row["cross_split"],
                "same_dimensions": str(metrics["same_dimensions"]),
                "thumbnail_mae": f"{metrics['thumbnail_mae']:.6f}",
                "dhash_distance": metrics["dhash_distance"],
                "rgb_histogram_cosine": f"{metrics['rgb_histogram_cosine']:.8f}",
                "proxy_status": classify_similarity(metrics),
                "proxy_sequence_id": "",
                "reviewer_decision": "PENDING",
                "reviewer_notes": "",
            }
        )

    cluster_rows, cluster_by_stem = build_candidate_clusters(edge_rows)
    for row in edge_rows:
        if row["proxy_status"] == "strong_candidate":
            row["proxy_sequence_id"] = cluster_by_stem[row["left_stem"]]

    write_csv(
        output_dir / "grouping_proxy_edges.csv",
        list(edge_rows[0]),
        edge_rows,
    )
    cluster_fields = [
        "proxy_sequence_id",
        "evidence_status",
        "member_count",
        "first_stem",
        "last_stem",
        "members",
        "strong_edge_count",
        "cross_split_strong_edges",
    ]
    write_csv(output_dir / "grouping_proxy_clusters.csv", cluster_fields, cluster_rows)

    status_counts = Counter(row["proxy_status"] for row in edge_rows)
    cross_split_counts = Counter(
        row["proxy_status"] for row in edge_rows if row["cross_split"] == "True"
    )
    cluster_sizes = [int(row["member_count"]) for row in cluster_rows]
    strong_minutes = (len(cluster_rows), len(cluster_rows) * 3)
    uncertain_minutes = (
        status_counts["uncertain"] * 20 / 60,
        status_counts["uncertain"] * 45 / 60,
    )
    adjacency_minutes = (
        status_counts["adjacency_only"] * 15 / 60,
        status_counts["adjacency_only"] * 30 / 60,
    )
    workload_hours = {
        "minimum": round(
            (strong_minutes[0] + uncertain_minutes[0] + adjacency_minutes[0]) / 60,
            1,
        ),
        "maximum": round(
            (strong_minutes[1] + uncertain_minutes[1] + adjacency_minutes[1]) / 60,
            1,
        ),
    }
    summary = {
        "schema_version": 1,
        "status": "PROXY_ONLY_NOT_APPROVED_FOR_SPLITTING",
        "method": {
            "candidate_universe": "numeric filename adjacency n -> n+1",
            "visual_cues": [
                "same image dimensions",
                "32x18 RGB thumbnail mean absolute error",
                "64-bit difference-hash Hamming distance",
                "16-bin-per-channel RGB histogram cosine similarity",
            ],
            "strong_thresholds": STRONG_THRESHOLDS,
            "uncertain_thresholds": UNCERTAIN_THRESHOLDS,
        },
        "counts": {
            "adjacent_edges": len(edge_rows),
            "strong_candidate_edges": status_counts["strong_candidate"],
            "uncertain_edges": status_counts["uncertain"],
            "adjacency_only_edges": status_counts["adjacency_only"],
            "cross_split_strong_candidate_edges": cross_split_counts["strong_candidate"],
            "cross_split_uncertain_edges": cross_split_counts["uncertain"],
            "cross_split_adjacency_only_edges": cross_split_counts["adjacency_only"],
            "candidate_sequences": len(cluster_rows),
            "images_in_candidate_sequences": sum(cluster_sizes),
            "largest_candidate_sequence": max(cluster_sizes, default=0),
        },
        "manual_review_workload": {
            "estimated_hours": workload_hours,
            "assumptions": [
                "1-3 minutes per strong candidate sequence using a contact sheet",
                "20-45 seconds per uncertain edge",
                "15-30 seconds per adjacency-only edge",
                "estimate excludes creator contact and taxonomy adjudication",
            ],
        },
        "review_workflow": [
            (
                "Review each strong sequence as a contact sheet and split it when "
                "scene/sign identity changes."
            ),
            "Review every uncertain edge pair and decide join, split, or needs-source-metadata.",
            "Spot-check adjacency-only boundaries for missed gradual transitions.",
            (
                "Record reviewer, date, decision, evidence and confidence; never copy "
                "proxy IDs into final group_id automatically."
            ),
            "Create final group-aware split only after all accepted groups are adjudicated.",
        ],
        "evidence_boundary": (
            "Candidate sequence IDs are review queue identifiers only. They are not video, scene, "
            "capture-session or physical-sign ground truth and cannot authorize a split or "
            "training."
        ),
    }
    write_json(output_dir / "grouping_proxy_summary.json", summary)
    return summary


def rare_risk_band(box_count: int) -> str:
    if box_count < 10:
        return "CRITICAL_LOW"
    if box_count < 20:
        return "VERY_LOW"
    if box_count < 50:
        return "LOW"
    if box_count < 100:
        return "LIMITED"
    return "MODERATE_OR_HIGH"


def build_rare_class_table(audit_dir: Path, output_dir: Path) -> list[dict[str, Any]]:
    support_rows = read_csv(audit_dir / "per_class_counts.csv")
    validate_support_rows(support_rows, source_name="per_class_counts.csv")
    rows: list[dict[str, Any]] = []
    for row in support_rows:
        box_count = int(row["box_count"])
        rows.append(
            {
                **row,
                "risk_band": rare_risk_band(box_count),
                "decision_status": "PENDING",
                "allowed_options": (
                    "collect_more|merge_after_semantic_approval|report_only|out_of_scope"
                ),
                "risk_note": (
                    "No reliable class-level holdout estimate"
                    if box_count < 20
                    else "Support must be checked after group-aware splitting"
                ),
            }
        )
    write_csv(output_dir / "rare_class_risk.csv", list(rows[0]), rows)
    return rows


def build_d04_decision_template(rare_rows: list[dict[str, Any]]) -> dict[str, Any]:
    validate_exact_class_ids(rare_rows, source_name="rare_class_risk rows")
    in_scope_rows = sorted(
        (
            row
            for row in rare_rows
            if int(row["box_count"]) < RARE_SCOPE_BOX_COUNT_MAX_EXCLUSIVE
        ),
        key=lambda row: int(row["class_id"]),
    )
    class_decisions = {
        str(row["class_id"]): {
            "class_id": int(row["class_id"]),
            "sign_code": row["sign_code"],
            "image_count": int(row["image_count"]),
            "box_count": int(row["box_count"]),
            "risk_band": row["risk_band"],
            "status": "PENDING",
            "selected_option": None,
            "reviewer": None,
            "decided_at": None,
            "rationale": None,
            "evidence_links": [],
            "history": [],
        }
        for row in in_scope_rows
    }
    return {
        "schema_version": 1,
        "decision_id": "D-04",
        "question": (
            "For each in-scope rare class, collect more, merge after semantic approval, "
            "report-only, or out-of-scope?"
        ),
        "status": "PENDING",
        "scope_rule": {
            "field": "box_count",
            "operator": "<",
            "value": RARE_SCOPE_BOX_COUNT_MAX_EXCLUSIVE,
        },
        "in_scope_class_ids": [int(row["class_id"]) for row in in_scope_rows],
        "allowed_options": list(D04_ALLOWED_OPTIONS),
        "aggregation_rule": (
            "D-04 may be RESOLVED only when every in-scope class record is RESOLVED, "
            "has an allowed selected_option, trimmed reviewer/rationale, RFC 3339 decided_at "
            "with timezone, at least one non-blank evidence link and a structured append-only "
            "history transition. Otherwise D-04 must remain PENDING."
        ),
        "class_decisions": class_decisions,
        "history": [],
    }


def validate_d04_decision_payload(
    payload: dict[str, Any],
    rare_rows: list[dict[str, Any]],
) -> str:
    template = build_d04_decision_template(rare_rows)
    if payload.get("scope_rule") != template["scope_rule"]:
        raise ValueError("D-04 scope_rule does not match the generated rare-class scope")
    if payload.get("in_scope_class_ids") != template["in_scope_class_ids"]:
        raise ValueError("D-04 in_scope_class_ids do not match the generated rare-class scope")
    if payload.get("aggregation_rule") != template["aggregation_rule"]:
        raise ValueError("D-04 aggregation_rule does not match the generated contract")
    allowed_options = payload.get("allowed_options")
    if not isinstance(allowed_options, list) or set(allowed_options) != set(D04_ALLOWED_OPTIONS):
        raise ValueError("D-04 allowed_options must contain the four approved dispositions")
    if len(allowed_options) != len(set(allowed_options)):
        raise ValueError("D-04 allowed_options must not contain duplicates")
    if not isinstance(payload.get("history"), list):
        raise ValueError("D-04 history must be a list")

    class_decisions = payload.get("class_decisions")
    if not isinstance(class_decisions, dict):
        raise ValueError("D-04 class_decisions must be an object keyed by class_id")
    expected_keys = set(template["class_decisions"])
    observed_keys = set(class_decisions)
    if observed_keys != expected_keys:
        raise ValueError(
            "D-04 class_decisions must cover every in-scope class exactly once; "
            f"missing={sorted(expected_keys - observed_keys)}, "
            f"extra={sorted(observed_keys - expected_keys)}"
        )

    all_resolved = True
    for class_id in sorted(expected_keys, key=int):
        record = class_decisions[class_id]
        if not isinstance(record, dict):
            raise ValueError(f"D-04 class {class_id} record must be an object")
        missing_fields = sorted(D04_CLASS_REQUIRED_FIELDS - record.keys())
        if missing_fields:
            raise ValueError(f"D-04 class {class_id} record is missing {missing_fields}")
        expected_evidence = template["class_decisions"][class_id]
        for field in ("class_id", "sign_code", "image_count", "box_count", "risk_band"):
            if record[field] != expected_evidence[field]:
                raise ValueError(f"D-04 class {class_id} has stale or invalid {field}")
        validate_d04_history(record["history"], class_id=class_id)
        validate_evidence_links(
            record["evidence_links"],
            field_name=f"D-04 class {class_id} evidence_links",
            require_nonempty=record["status"] == "RESOLVED",
        )
        selected_option = record["selected_option"]
        if selected_option is not None and selected_option not in D04_ALLOWED_OPTIONS:
            raise ValueError(f"D-04 class {class_id} has invalid selected_option")
        if record["status"] not in {"PENDING", "RESOLVED"}:
            raise ValueError(f"D-04 class {class_id} has invalid status")
        for text_field in ("reviewer", "rationale"):
            if record[text_field] is not None:
                require_trimmed_nonempty_string(
                    record[text_field],
                    field_name=f"D-04 class {class_id} {text_field}",
                )
        if record["decided_at"] is not None:
            parse_audit_timestamp(
                record["decided_at"],
                field_name=f"D-04 class {class_id} decided_at",
            )
        if record["status"] == "RESOLVED":
            if selected_option is None:
                raise ValueError(
                    f"D-04 class {class_id} selected_option is required when RESOLVED"
                )
            require_trimmed_nonempty_string(
                record["reviewer"],
                field_name=f"D-04 class {class_id} reviewer",
            )
            parse_audit_timestamp(
                record["decided_at"],
                field_name=f"D-04 class {class_id} decided_at",
            )
            require_trimmed_nonempty_string(
                record["rationale"],
                field_name=f"D-04 class {class_id} rationale",
            )
            if not record["history"]:
                raise ValueError(
                    f"D-04 class {class_id} history requires an auditable prior snapshot"
                )
        else:
            all_resolved = False

    aggregate_status = payload.get("status")
    if aggregate_status not in {"PENDING", "RESOLVED"}:
        raise ValueError("D-04 aggregate status must be PENDING or RESOLVED")
    if aggregate_status == "RESOLVED" and not all_resolved:
        raise ValueError("D-04 cannot be RESOLVED while any in-scope class remains unresolved")
    return "RESOLVED" if all_resolved else "PENDING"


def build_decision_status_schema(d04_template: dict[str, Any]) -> dict[str, Any]:
    class_ids = [str(class_id) for class_id in d04_template["in_scope_class_ids"]]
    optional_trimmed_string = {
        "oneOf": [
            {"type": "null"},
            {"$ref": "#/$defs/trimmedNonEmptyString"},
        ]
    }
    optional_timestamp = {
        "oneOf": [
            {"type": "null"},
            {"$ref": "#/$defs/auditTimestamp"},
        ]
    }
    previous_record = {
        "type": "object",
        "required": sorted(D04_HISTORY_PREVIOUS_REQUIRED_FIELDS),
        "properties": {
            "status": {"enum": ["PENDING", "RESOLVED"]},
            "selected_option": {
                "oneOf": [{"type": "null"}, {"enum": list(D04_ALLOWED_OPTIONS)}]
            },
            "reviewer": optional_trimmed_string,
            "decided_at": optional_timestamp,
            "rationale": optional_trimmed_string,
            "evidence_links": {
                "type": "array",
                "items": {"$ref": "#/$defs/trimmedNonEmptyString"},
            },
        },
        "allOf": [
            {
                "if": {"properties": {"status": {"const": "RESOLVED"}}},
                "then": {
                    "properties": {
                        "selected_option": {"enum": list(D04_ALLOWED_OPTIONS)},
                        "reviewer": {"$ref": "#/$defs/trimmedNonEmptyString"},
                        "decided_at": {"$ref": "#/$defs/auditTimestamp"},
                        "rationale": {"$ref": "#/$defs/trimmedNonEmptyString"},
                        "evidence_links": {
                            "type": "array",
                            "minItems": 1,
                            "items": {"$ref": "#/$defs/trimmedNonEmptyString"},
                        },
                    }
                },
            }
        ],
        "additionalProperties": False,
    }
    history_item = {
        "type": "object",
        "required": sorted(D04_HISTORY_ITEM_REQUIRED_FIELDS),
        "properties": {
            "changed_at": {"$ref": "#/$defs/auditTimestamp"},
            "changed_by": {"$ref": "#/$defs/trimmedNonEmptyString"},
            "previous": previous_record,
        },
        "additionalProperties": False,
    }
    class_record = {
        "type": "object",
        "required": sorted(D04_CLASS_REQUIRED_FIELDS),
        "properties": {
            "class_id": {"type": "integer", "minimum": 0, "maximum": 51},
            "sign_code": {"type": "string", "minLength": 1},
            "image_count": {"type": "integer", "minimum": 0},
            "box_count": {"type": "integer", "minimum": 0},
            "risk_band": {"type": "string", "minLength": 1},
            "status": {"enum": ["PENDING", "RESOLVED"]},
            "selected_option": {
                "oneOf": [{"type": "null"}, {"enum": list(D04_ALLOWED_OPTIONS)}]
            },
            "reviewer": optional_trimmed_string,
            "decided_at": optional_timestamp,
            "rationale": optional_trimmed_string,
            "evidence_links": {
                "type": "array",
                "items": {"$ref": "#/$defs/trimmedNonEmptyString"},
            },
            "history": {"type": "array", "items": history_item},
        },
        "allOf": [
            {
                "if": {"properties": {"status": {"const": "RESOLVED"}}},
                "then": {
                    "properties": {
                        "selected_option": {"enum": list(D04_ALLOWED_OPTIONS)},
                        "reviewer": {"$ref": "#/$defs/trimmedNonEmptyString"},
                        "decided_at": {"$ref": "#/$defs/auditTimestamp"},
                        "rationale": {"$ref": "#/$defs/trimmedNonEmptyString"},
                        "evidence_links": {
                            "type": "array",
                            "minItems": 1,
                            "items": {"$ref": "#/$defs/trimmedNonEmptyString"},
                        },
                        "history": {
                            "type": "array",
                            "minItems": 1,
                            "items": history_item,
                        },
                    }
                },
            }
        ],
        "additionalProperties": False,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "decision_status.schema.json",
        "title": "M0-WP2 decision status",
        "type": "object",
        "$defs": {
            "trimmedNonEmptyString": {
                "type": "string",
                "minLength": 1,
                "pattern": TRIMMED_NONEMPTY_PATTERN,
            },
            "auditTimestamp": {
                "type": "string",
                "format": "date-time",
                "pattern": AUDIT_TIMESTAMP_PATTERN_TEXT,
            },
        },
        "required": ["gate0", "training_authorized", "decisions"],
        "properties": {
            "gate0": {"const": "BLOCKED"},
            "training_authorized": {"const": False},
            "decisions": {
                "type": "object",
                "required": ["D-04"],
                "properties": {
                    "D-04": {
                        "type": "object",
                        "required": [
                            "status",
                            "scope_rule",
                            "in_scope_class_ids",
                            "allowed_options",
                            "aggregation_rule",
                            "class_decisions",
                            "history",
                        ],
                        "properties": {
                            "question": {"$ref": "#/$defs/trimmedNonEmptyString"},
                            "status": {"enum": ["PENDING", "RESOLVED"]},
                            "scope_rule": {"const": d04_template["scope_rule"]},
                            "in_scope_class_ids": {
                                "const": d04_template["in_scope_class_ids"]
                            },
                            "allowed_options": {"const": list(D04_ALLOWED_OPTIONS)},
                            "aggregation_rule": {
                                "const": d04_template["aggregation_rule"]
                            },
                            "class_decisions": {
                                "type": "object",
                                "required": class_ids,
                                "properties": {
                                    class_id: class_record for class_id in class_ids
                                },
                                "additionalProperties": False,
                            },
                            "history": {"type": "array"},
                        },
                        "allOf": [
                            {
                                "if": {"properties": {"status": {"const": "RESOLVED"}}},
                                "then": {
                                    "properties": {
                                        "class_decisions": {
                                            "properties": {
                                                class_id: {
                                                    "properties": {
                                                        "status": {"const": "RESOLVED"}
                                                    }
                                                }
                                                for class_id in class_ids
                                            }
                                        }
                                    }
                                },
                            }
                        ],
                    }
                },
            },
        },
    }


def taxonomy_conflict_flags(class_id: int, code: str, relation: str, support: int) -> list[str]:
    flags = ["domain_reviewer_not_approved"]
    if relation.startswith("Direct") or relation.startswith("Partial"):
        flags.append("cross_jurisdiction_gtsrb_semantics_unapproved")
    if relation.startswith("None"):
        flags.append("no_gtsrb_equivalent_proposed")
    if "*" in code:
        flags.append("dataset_code_contains_modifier")
    if code.startswith("S."):
        flags.append("supplementary_plate_used_as_class")
    if class_id in {12, 19, 35, 36, 49}:
        flags.append("composite_or_multi_symbol_semantics")
    special_flags = {
        3: "english_right_turn_only_vs_obstacle_bypass_semantics",
        22: "english_uneven_road_vs_speed_hump_semantics",
        24: "english_customs_translation_not_confirmed",
        28: "vi_en_vehicle_wording_unclear",
        31: "non_qcvn_camera_code",
        34: "annex_section_B8a_used_instead_of_sign_code_P108a",
        47: "dataset_code_P124b1_not_confirmed_in_qcvn",
        51: "dataset_family_mandatory_but_qcvn_code_is_warning",
    }
    if class_id in special_flags:
        flags.append(special_flags[class_id])
    if support < 20:
        flags.append("rare_support")
    return flags


def build_taxonomy_review_table(
    taxonomy_doc: Path,
    audit_dir: Path,
    output_dir: Path,
) -> list[dict[str, Any]]:
    support_rows = read_csv(audit_dir / "per_class_counts.csv")
    validate_support_rows(support_rows, source_name="per_class_counts.csv")
    support_by_id = {int(row["class_id"]): row for row in support_rows}
    taxonomy_source_rows: list[dict[str, Any]] = []
    for line in taxonomy_doc.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or not cells[0].isdigit() or len(cells) != 9:
            continue
        class_id = int(cells[0])
        taxonomy_source_rows.append({"class_id": class_id, "cells": cells})
    validate_exact_class_ids(taxonomy_source_rows, source_name="taxonomy mapping table")

    rows: list[dict[str, Any]] = []
    for source_row in taxonomy_source_rows:
        class_id = int(source_row["class_id"])
        cells = source_row["cells"]
        support = support_by_id[class_id]
        family = "warning-obstacle" if class_id == 51 else cells[3]
        flags = taxonomy_conflict_flags(
            class_id,
            cells[1],
            cells[5],
            int(support["box_count"]),
        )
        rows.append(
            {
                "class_id": class_id,
                "dataset_code": cells[1],
                "dataset_name_vi_en": cells[2],
                "semantic_family_proposal": family,
                "gtsrb_mapping_proposal": cells[4],
                "gtsrb_relation_proposal": cells[5],
                "criticality_proposal": cells[6],
                "image_count": support["image_count"],
                "box_count": support["box_count"],
                "conflict_flags": ";".join(flags),
                "authoritative_review_target": "QCVN 41:2024/BGTVT",
                "review_status": "UNAPPROVED",
                "reviewer": "",
                "review_date": "",
                "decision_notes": "",
            }
        )
    write_csv(output_dir / "taxonomy_review.csv", list(rows[0]), rows)
    return rows


def bbox_pixel_geometry(
    x_center: float,
    y_center: float,
    width: float,
    height: float,
    image_width: int,
    image_height: int,
) -> dict[str, float]:
    x_min = (x_center - width / 2) * image_width
    x_max = (x_center + width / 2) * image_width
    y_min = (y_center - height / 2) * image_height
    y_max = (y_center + height / 2) * image_height
    return {
        "x_min": x_min,
        "y_min": y_min,
        "x_max": x_max,
        "y_max": y_max,
        "overflow_left_px": max(0.0, -x_min),
        "overflow_top_px": max(0.0, -y_min),
        "overflow_right_px": max(0.0, x_max - image_width),
        "overflow_bottom_px": max(0.0, y_max - image_height),
    }


def review_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def render_bbox_review(
    image_path: Path,
    label_path: Path,
    output_image: Path,
    output_json: Path,
) -> dict[str, Any]:
    source_image_hash = sha256_file(image_path)
    source_label_hash = sha256_file(label_path)
    with Image.open(image_path) as image:
        source = image.convert("RGB")
    image_width, image_height = source.size
    margin_left = 32
    margin_top = 74
    margin_right = 520
    margin_bottom = 56
    canvas = Image.new(
        "RGB",
        (margin_left + image_width + margin_right, margin_top + image_height + margin_bottom),
        "white",
    )
    canvas.paste(source, (margin_left, margin_top))
    draw = ImageDraw.Draw(canvas, "RGBA")
    font = review_font(18)
    small_font = review_font(15)
    draw.text(
        (margin_left, 18),
        "G0.4 reviewer view - source 0248.jpg with original YOLO boxes",
        fill="black",
        font=font,
    )
    source_right = margin_left + image_width
    draw.rectangle(
        (margin_left, margin_top, source_right, margin_top + image_height),
        outline=(0, 0, 0, 255),
        width=3,
    )
    for y in range(margin_top, margin_top + image_height, 16):
        draw.line(
            (source_right, y, source_right, min(y + 8, margin_top + image_height)),
            fill="blue",
            width=3,
        )

    boxes: list[dict[str, Any]] = []
    lines = label_path.read_text(encoding="utf-8").splitlines()
    colors = [(220, 20, 60, 255), (0, 128, 0, 255)]
    for line_number, line in enumerate(lines, start=1):
        fields = line.split()
        class_id = int(fields[0])
        x_center, y_center, width, height = map(float, fields[1:])
        geometry = bbox_pixel_geometry(
            x_center,
            y_center,
            width,
            height,
            image_width,
            image_height,
        )
        color = colors[(line_number - 1) % len(colors)]
        rect = (
            margin_left + geometry["x_min"],
            margin_top + geometry["y_min"],
            margin_left + geometry["x_max"],
            margin_top + geometry["y_max"],
        )
        draw.rectangle(rect, outline=color, width=4)
        if geometry["overflow_right_px"]:
            draw.rectangle(
                (source_right, rect[1], rect[2], rect[3]),
                fill=(255, 0, 0, 72),
                outline=color,
                width=3,
            )
        label = f"line {line_number}, class {class_id}"
        draw.text((rect[0], max(margin_top, rect[1] - 20)), label, fill=color, font=small_font)
        boxes.append(
            {
                "line": line_number,
                "class_id": class_id,
                "normalized": {
                    "x_center": x_center,
                    "y_center": y_center,
                    "width": width,
                    "height": height,
                },
                "pixels": geometry,
                "review_status": "PENDING",
            }
        )

    first = boxes[0]
    annotation_x = source_right + 28
    annotation_y = margin_top + 24
    notes = [
        "Blue dashed line = image border",
        "Red = original line 1 bbox",
        f"Original x_max = {first['pixels']['x_max']:.3f}px",
        f"Right overflow = {first['pixels']['overflow_right_px']:.3f}px",
        "Raw label is not clipped or edited.",
    ]
    for offset, note in enumerate(notes):
        draw.text(
            (annotation_x, annotation_y + offset * 26),
            note,
            fill=(20, 20, 20, 255),
            font=small_font,
        )

    output_image.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_image)
    payload = {
        "schema_version": 1,
        "status": "REVIEW_REQUIRED_RAW_UNCHANGED",
        "source": {
            "image_path": str(image_path),
            "image_sha256": source_image_hash,
            "label_path": str(label_path),
            "label_sha256": source_label_hash,
            "width": image_width,
            "height": image_height,
        },
        "boxes": boxes,
        "decision_options": [
            "keep_raw_as_warning",
            "create_separate_clipped_derived_annotation",
            "quarantine_image_from_approved_dataset",
        ],
        "decision_status": "PENDING",
        "evidence_boundary": (
            "The overlay visualizes original coordinates; it does not alter or approve the raw "
            "label."
        ),
    }
    write_json(output_json, payload)
    if sha256_file(image_path) != source_image_hash or sha256_file(label_path) != source_label_hash:
        raise RuntimeError("Source image or label changed while rendering bbox review")
    return payload


def build_manifest(output_dir: Path) -> dict[str, Any]:
    manifest_path = output_dir / "wp2_generated_manifest.json"
    artifacts = []
    for path in sorted(output_dir.parent.rglob("*")):
        if path.is_file() and path != manifest_path:
            artifacts.append(
                {
                    "path": path.relative_to(output_dir.parent).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    payload = {
        "schema_version": 1,
        "status": "REVIEW_EVIDENCE_ONLY_NO_TRAINING_AUTHORIZATION",
        "artifacts": artifacts,
    }
    write_json(manifest_path, payload)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, required=True)
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--taxonomy-doc", type=Path, required=True)
    parser.add_argument("--review-dir", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    generated_dir = args.review_dir / "generated"
    assets_dir = args.review_dir / "assets"
    dataset_root = args.staging_root / "raw" / "archive"

    grouping = build_grouping_evidence(
        args.audit_dir,
        dataset_root / "images",
        generated_dir,
    )
    rare_rows = build_rare_class_table(args.audit_dir, generated_dir)
    d04_template = build_d04_decision_template(rare_rows)
    write_json(generated_dir / "d04_rare_class_decision_template.json", d04_template)
    decision_status_path = args.review_dir / "decision_status.json"
    decision_status = json.loads(decision_status_path.read_text(encoding="utf-8"))
    d04_aggregate = validate_d04_decision_payload(
        decision_status["decisions"]["D-04"],
        rare_rows,
    )
    write_json(
        generated_dir / "decision_status.schema.json",
        build_decision_status_schema(d04_template),
    )
    taxonomy_rows = build_taxonomy_review_table(
        args.taxonomy_doc,
        args.audit_dir,
        generated_dir,
    )
    bbox = render_bbox_review(
        dataset_root / "images" / "0248.jpg",
        dataset_root / "labels" / "0248.txt",
        assets_dir / "bbox_0248_review.png",
        generated_dir / "bbox_0248_review.json",
    )
    manifest = build_manifest(generated_dir)
    print(
        json.dumps(
            {
                "status": "REVIEW_EVIDENCE_ONLY_NO_TRAINING_AUTHORIZATION",
                "candidate_sequences": grouping["counts"]["candidate_sequences"],
                "taxonomy_rows": len(taxonomy_rows),
                "rare_rows": len(rare_rows),
                "d04_class_records": len(d04_template["class_decisions"]),
                "d04_aggregate": d04_aggregate,
                "bbox_review": bbox["status"],
                "manifest_artifacts": len(manifest["artifacts"]),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
