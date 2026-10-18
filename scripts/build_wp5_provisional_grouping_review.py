# ruff: noqa: E501
"""Build and verify the fail-closed M0-WP5 provisional grouping review package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from PIL import Image, ImageDraw, ImageFont

PACKAGE_STATUS = "WP5_READY_FOR_RE_REVIEW_PARTIAL_VISUAL_REVIEW"
EVIDENCE_BOUNDARY = "PROVISIONAL_REVIEW_ONLY_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT"
COMPONENT_LABEL = "PROVISIONAL_COMPONENT_NOT_GROUP_TRUTH"
MANIFEST_SCHEMA_VERSION = 2
MANIFEST_COUNT_SEMANTICS = "EXCLUDES_MANIFEST_FILE"
MANIFEST_RELATIVE_PATH = "docs/review/generated/wp5_evidence_manifest.json"
EXPECTED_EDGE_COUNT = 3178
EXPECTED_SEQUENCE_COUNT = 589
EXPECTED_CROSS_SPLIT_COUNT = 1031
EXPECTED_PROXY_COUNTS = {
    "strong_candidate": 1691,
    "uncertain": 1172,
    "adjacency_only": 315,
}
ALLOWED_OUTCOMES = (
    "SAME_CAPTURE_CANDIDATE",
    "SAME_PHYSICAL_SIGN_CANDIDATE",
    "VISUALLY_RELATED_UNCERTAIN",
    "NOT_RELATED",
    "INSUFFICIENT_EVIDENCE",
)
CAPTURE_HYPOTHESES = (
    "SAME_CAPTURE_CANDIDATE",
    "VISUALLY_RELATED_UNCERTAIN",
    "NOT_RELATED",
    "INSUFFICIENT_EVIDENCE",
)
PHYSICAL_SIGN_HYPOTHESES = (
    "SAME_PHYSICAL_SIGN_CANDIDATE",
    "VISUALLY_RELATED_UNCERTAIN",
    "NOT_RELATED",
    "INSUFFICIENT_EVIDENCE",
)
CONFIDENCE_VALUES = ("HIGH", "MEDIUM", "LOW")
PAIRS_PER_PAGE = 25
EXPECTED_ATLAS_PAGE_COUNT = math.ceil(EXPECTED_EDGE_COUNT / PAIRS_PER_PAGE)
EXPECTED_SOURCE_COUNT = 11
EXPECTED_NON_MANIFEST_ARTIFACT_COUNT = 8 + 1 + EXPECTED_ATLAS_PAGE_COUNT
THUMBNAIL_SIZE = (200, 112)
CANVAS_WIDTH = 1000
ROW_HEIGHT = 142
PAGE_HEADER_HEIGHT = 58
DECISION_FIELDS = [
    "edge_id",
    "review_order",
    "review_status",
    "left_stem",
    "left_split",
    "right_stem",
    "right_split",
    "cross_split",
    "same_dimensions",
    "thumbnail_mae",
    "dhash_distance",
    "rgb_histogram_cosine",
    "proxy_status",
    "proxy_sequence_id",
    "left_class_ids",
    "right_class_ids",
    "left_image_sha256",
    "right_image_sha256",
    "left_label_sha256",
    "right_label_sha256",
    "provisional_outcome",
    "capture_hypothesis",
    "physical_sign_hypothesis",
    "confidence",
    "reviewer",
    "reviewed_at",
    "rationale",
    "evidence_ref",
    "atlas_page",
    "atlas_slot",
    "evidence_boundary",
]
SEQUENCE_FIELDS = [
    "proxy_sequence_id",
    "review_status",
    "member_count",
    "first_stem",
    "last_stem",
    "members",
    "strong_edge_count",
    "cross_split_strong_edges",
    "contact_sheet",
    "source_stems",
    "reviewer",
    "reviewed_at",
    "confidence",
    "rationale",
    "evidence_boundary",
]
COMPONENT_FIELDS = [
    "component_id",
    "hypothesis",
    "component_label",
    "confidence",
    "member_count",
    "members",
    "cross_split",
    "supporting_edge_ids",
    "incompatible_not_related_edge_ids",
]
CONFLICT_FIELDS = [
    "conflict_id",
    "hypothesis",
    "component_id",
    "not_related_edge_id",
    "left_stem",
    "right_stem",
    "reason",
    "component_label",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def bool_text(value: str) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"invalid boolean text: {value!r}")


def reviewer_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ):
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def fit_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    result = Image.new("RGB", size, "#111827")
    copy = image.convert("RGB")
    copy.thumbnail(size, Image.Resampling.LANCZOS)
    x = (size[0] - copy.width) // 2
    y = (size[1] - copy.height) // 2
    result.paste(copy, (x, y))
    return result


def validate_inputs(
    edges: list[dict[str, str]],
    sequences: list[dict[str, str]],
    sequence_index: list[dict[str, str]],
    inventory_rows: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    if len(edges) != EXPECTED_EDGE_COUNT:
        raise ValueError(f"expected {EXPECTED_EDGE_COUNT} edges, found {len(edges)}")
    if len(sequences) != EXPECTED_SEQUENCE_COUNT:
        raise ValueError(
            f"expected {EXPECTED_SEQUENCE_COUNT} proxy sequences, found {len(sequences)}"
        )
    if len(sequence_index) != EXPECTED_SEQUENCE_COUNT:
        raise ValueError("WP3 sequence index does not cover all proxy sequences")
    edge_pairs = [(row["left_stem"], row["right_stem"]) for row in edges]
    if len(set(edge_pairs)) != len(edge_pairs):
        raise ValueError("duplicate edge endpoints found")
    proxy_counts = Counter(row["proxy_status"] for row in edges)
    if dict(proxy_counts) != EXPECTED_PROXY_COUNTS:
        raise ValueError(f"unexpected proxy counts: {dict(proxy_counts)}")
    cross_split_count = sum(bool_text(row["cross_split"]) for row in edges)
    if cross_split_count != EXPECTED_CROSS_SPLIT_COUNT:
        raise ValueError(
            f"expected {EXPECTED_CROSS_SPLIT_COUNT} cross-split edges, found {cross_split_count}"
        )
    inventory = {row["stem"]: row for row in inventory_rows}
    if len(inventory) != len(inventory_rows):
        raise ValueError("inventory contains duplicate stems")
    missing = sorted({stem for pair in edge_pairs for stem in pair} - set(inventory))
    if missing:
        raise ValueError(f"edge endpoints missing from inventory: {missing[:10]}")
    sequence_ids = {row["proxy_sequence_id"] for row in sequences}
    index_ids = {row["proxy_sequence_id"] for row in sequence_index}
    if len(sequence_ids) != EXPECTED_SEQUENCE_COUNT or sequence_ids != index_ids:
        raise ValueError("WP2/WP3 proxy sequence IDs do not reconcile")
    for row in edges:
        if row["left_split"] != inventory[row["left_stem"]]["split"]:
            raise ValueError(f"left split mismatch for {row['left_stem']}")
        if row["right_split"] != inventory[row["right_stem"]]["split"]:
            raise ValueError(f"right split mismatch for {row['right_stem']}")
        expected_cross = row["left_split"] != row["right_split"]
        if bool_text(row["cross_split"]) != expected_cross:
            raise ValueError("cross_split is inconsistent with endpoint splits")
    return inventory


def load_annotations(path: Path, edges_by_id: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("evidence_boundary") != EVIDENCE_BOUNDARY:
        raise ValueError("annotation evidence boundary is invalid")
    annotations: dict[str, dict[str, str]] = {}
    for raw in payload.get("decisions", []):
        edge_id = raw.get("edge_id", "")
        if edge_id in annotations or edge_id not in edges_by_id:
            raise ValueError(f"unknown or duplicate annotation edge: {edge_id}")
        edge = edges_by_id[edge_id]
        if (raw.get("left_stem"), raw.get("right_stem")) != (
            edge["left_stem"],
            edge["right_stem"],
        ):
            raise ValueError(f"annotation endpoints do not match {edge_id}")
        if raw.get("provisional_outcome") not in ALLOWED_OUTCOMES:
            raise ValueError(f"invalid outcome for {edge_id}")
        if raw.get("capture_hypothesis") not in CAPTURE_HYPOTHESES:
            raise ValueError(f"invalid capture hypothesis for {edge_id}")
        if raw.get("physical_sign_hypothesis") not in PHYSICAL_SIGN_HYPOTHESES:
            raise ValueError(f"invalid physical-sign hypothesis for {edge_id}")
        if raw.get("confidence") not in CONFIDENCE_VALUES:
            raise ValueError(f"invalid confidence for {edge_id}")
        if not str(raw.get("rationale", "")).strip():
            raise ValueError(f"missing rationale for {edge_id}")
        annotations[edge_id] = {
            **raw,
            "reviewer": payload["reviewer"],
            "reviewed_at": payload["reviewed_at"],
        }
    return annotations


def verify_inventory_sources(
    inventory: dict[str, dict[str, str]], raw_root: Path
) -> dict[str, dict[str, str]]:
    cache: dict[str, dict[str, str]] = {}
    for stem in sorted(inventory):
        row = inventory[stem]
        image_path = raw_root / row["image_path"]
        label_path = raw_root / row["label_path"]
        if not image_path.is_file() or not label_path.is_file():
            raise FileNotFoundError(f"source pair missing for {stem}")
        image_hash = sha256_file(image_path)
        label_hash = sha256_file(label_path)
        if image_hash != row["image_sha256"] or label_hash != row["label_sha256"]:
            raise ValueError(f"source hash mismatch for {stem}")
        cache[stem] = {
            "image_path": str(image_path),
            "label_path": str(label_path),
            "image_sha256": image_hash,
            "label_sha256": label_hash,
        }
    return cache


def build_decision_rows(
    edges: list[dict[str, str]],
    inventory: dict[str, dict[str, str]],
    annotations: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    source_rows: list[tuple[str, dict[str, str]]] = [
        (f"edge_{index:06d}", row) for index, row in enumerate(edges, start=1)
    ]
    review_order = sorted(
        source_rows,
        key=lambda item: (not bool_text(item[1]["cross_split"]), int(item[0].split("_")[1])),
    )
    decisions: list[dict[str, Any]] = []
    for order, (edge_id, edge) in enumerate(review_order, start=1):
        page = math.ceil(order / PAIRS_PER_PAGE)
        slot = (order - 1) % PAIRS_PER_PAGE + 1
        annotation = annotations.get(edge_id)
        left = inventory[edge["left_stem"]]
        right = inventory[edge["right_stem"]]
        row: dict[str, Any] = {
            "edge_id": edge_id,
            "review_order": order,
            "review_status": "REVIEWED" if annotation else "PENDING",
            "left_stem": edge["left_stem"],
            "left_split": edge["left_split"],
            "right_stem": edge["right_stem"],
            "right_split": edge["right_split"],
            "cross_split": edge["cross_split"],
            "same_dimensions": edge["same_dimensions"],
            "thumbnail_mae": edge["thumbnail_mae"],
            "dhash_distance": edge["dhash_distance"],
            "rgb_histogram_cosine": edge["rgb_histogram_cosine"],
            "proxy_status": edge["proxy_status"],
            "proxy_sequence_id": edge["proxy_sequence_id"],
            "left_class_ids": left["class_ids"],
            "right_class_ids": right["class_ids"],
            "left_image_sha256": left["image_sha256"],
            "right_image_sha256": right["image_sha256"],
            "left_label_sha256": left["label_sha256"],
            "right_label_sha256": right["label_sha256"],
            "provisional_outcome": "",
            "capture_hypothesis": "",
            "physical_sign_hypothesis": "",
            "confidence": "",
            "reviewer": "",
            "reviewed_at": "",
            "rationale": "",
            "evidence_ref": f"docs/review/assets/wp5/pairs/index.html#{edge_id}",
            "atlas_page": f"docs/review/assets/wp5/pairs/page_{page:03d}.jpg",
            "atlas_slot": slot,
            "evidence_boundary": EVIDENCE_BOUNDARY,
        }
        if annotation:
            for field in (
                "provisional_outcome",
                "capture_hypothesis",
                "physical_sign_hypothesis",
                "confidence",
                "reviewer",
                "reviewed_at",
                "rationale",
            ):
                row[field] = annotation[field]
        decisions.append(row)
    return decisions


def decision_schema() -> dict[str, Any]:
    string_fields = {field: {"type": "string"} for field in DECISION_FIELDS}
    string_fields["review_order"] = {"type": "integer", "minimum": 1}
    string_fields["atlas_slot"] = {"type": "integer", "minimum": 1, "maximum": PAIRS_PER_PAGE}
    string_fields["review_status"] = {"enum": ["PENDING", "REVIEWED"]}
    string_fields["evidence_boundary"] = {"const": EVIDENCE_BOUNDARY}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "wp5_provisional_decision.schema.json",
        "title": "WP5 fail-closed provisional edge decision",
        "type": "object",
        "additionalProperties": False,
        "required": DECISION_FIELDS,
        "properties": string_fields,
        "allOf": [
            {
                "if": {"properties": {"review_status": {"const": "PENDING"}}},
                "then": {
                    "properties": {
                        field: {"const": ""}
                        for field in (
                            "provisional_outcome",
                            "capture_hypothesis",
                            "physical_sign_hypothesis",
                            "confidence",
                            "reviewer",
                            "reviewed_at",
                            "rationale",
                        )
                    }
                },
                "else": {
                    "properties": {
                        "provisional_outcome": {"enum": list(ALLOWED_OUTCOMES)},
                        "capture_hypothesis": {"enum": list(CAPTURE_HYPOTHESES)},
                        "physical_sign_hypothesis": {"enum": list(PHYSICAL_SIGN_HYPOTHESES)},
                        "confidence": {"enum": list(CONFIDENCE_VALUES)},
                        "reviewer": {"type": "string", "minLength": 1},
                        "reviewed_at": {"type": "string", "minLength": 1},
                        "rationale": {"type": "string", "minLength": 1},
                    }
                },
            }
        ],
    }


def validate_decisions(rows: list[dict[str, Any]], schema: dict[str, Any]) -> None:
    validator = Draft202012Validator(schema)
    errors = [
        f"{row['edge_id']}: {error.message}"
        for row in rows
        for error in validator.iter_errors(row)
    ]
    if errors:
        raise ValueError("decision schema validation failed: " + "; ".join(errors[:5]))
    if len(rows) != EXPECTED_EDGE_COUNT or len({row["edge_id"] for row in rows}) != len(rows):
        raise ValueError("decision rows must cover every edge exactly once")
    if [row["review_order"] for row in rows] != list(range(1, EXPECTED_EDGE_COUNT + 1)):
        raise ValueError("review order is not contiguous")
    first_non_cross = next(
        (index for index, row in enumerate(rows) if row["cross_split"] == "False"),
        len(rows),
    )
    if first_non_cross != EXPECTED_CROSS_SPLIT_COUNT:
        raise ValueError("cross-split edges are not prioritized exactly first")


def build_sequence_rows(
    sequences: list[dict[str, str]], sequence_index: list[dict[str, str]]
) -> list[dict[str, Any]]:
    index = {row["proxy_sequence_id"]: row for row in sequence_index}
    rows: list[dict[str, Any]] = []
    for sequence in sorted(sequences, key=lambda row: row["proxy_sequence_id"]):
        linked = index[sequence["proxy_sequence_id"]]
        rows.append(
            {
                "proxy_sequence_id": sequence["proxy_sequence_id"],
                "review_status": "PENDING",
                "member_count": sequence["member_count"],
                "first_stem": sequence["first_stem"],
                "last_stem": sequence["last_stem"],
                "members": sequence["members"],
                "strong_edge_count": sequence["strong_edge_count"],
                "cross_split_strong_edges": sequence["cross_split_strong_edges"],
                "contact_sheet": f"docs/review/{linked['contact_sheet']}",
                "source_stems": linked["source_stems"],
                "reviewer": "",
                "reviewed_at": "",
                "confidence": "",
                "rationale": "",
                "evidence_boundary": EVIDENCE_BOUNDARY,
            }
        )
    return rows


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, item: str) -> str:
        self.parent.setdefault(item, item)
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[max(left_root, right_root)] = min(left_root, right_root)


def build_components(
    decisions: list[dict[str, Any]], hypothesis: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    field = "capture_hypothesis" if hypothesis == "capture" else "physical_sign_hypothesis"
    target = "SAME_CAPTURE_CANDIDATE" if hypothesis == "capture" else "SAME_PHYSICAL_SIGN_CANDIDATE"
    supporting = [
        row
        for row in decisions
        if row["review_status"] == "REVIEWED"
        and row["confidence"] == "HIGH"
        and row[field] == target
    ]
    union = UnionFind()
    for row in supporting:
        union.union(row["left_stem"], row["right_stem"])
    members_by_root: dict[str, set[str]] = defaultdict(set)
    for item in union.parent:
        members_by_root[union.find(item)].add(item)
    components: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    reviewed_not_related = [
        row
        for row in decisions
        if row["review_status"] == "REVIEWED" and row[field] == "NOT_RELATED"
    ]
    for number, members in enumerate(
        sorted(members_by_root.values(), key=lambda group: sorted(group)), start=1
    ):
        component_id = f"provisional_{hypothesis}_component_{number:04d}"
        support_ids = [
            row["edge_id"]
            for row in supporting
            if row["left_stem"] in members and row["right_stem"] in members
        ]
        incompatible = [
            row
            for row in reviewed_not_related
            if row["left_stem"] in members and row["right_stem"] in members
        ]
        split_values = {
            split
            for row in supporting
            if row["edge_id"] in support_ids
            for split in (row["left_split"], row["right_split"])
        }
        components.append(
            {
                "component_id": component_id,
                "hypothesis": hypothesis,
                "component_label": COMPONENT_LABEL,
                "confidence": "HIGH",
                "member_count": len(members),
                "members": ";".join(sorted(members)),
                "cross_split": str(len(split_values) > 1),
                "supporting_edge_ids": ";".join(sorted(support_ids)),
                "incompatible_not_related_edge_ids": ";".join(
                    sorted(row["edge_id"] for row in incompatible)
                ),
            }
        )
        for row in incompatible:
            conflicts.append(
                {
                    "conflict_id": f"conflict_{len(conflicts) + 1:04d}",
                    "hypothesis": hypothesis,
                    "component_id": component_id,
                    "not_related_edge_id": row["edge_id"],
                    "left_stem": row["left_stem"],
                    "right_stem": row["right_stem"],
                    "reason": "Reviewed NOT_RELATED edge falls within a provisional connected component.",
                    "component_label": COMPONENT_LABEL,
                }
            )
    return components, conflicts


def render_pair_atlas(
    decisions: list[dict[str, Any]],
    inventory: dict[str, dict[str, str]],
    raw_root: Path,
    assets_dir: Path,
) -> tuple[list[Path], dict[str, Any]]:
    if assets_dir.exists():
        shutil.rmtree(assets_dir)
    assets_dir.mkdir(parents=True)
    font = reviewer_font(12)
    title_font = reviewer_font(18)
    thumbnail_cache: dict[str, Image.Image] = {}
    page_paths: list[Path] = []
    page_audits: list[dict[str, Any]] = []
    page_count = math.ceil(len(decisions) / PAIRS_PER_PAGE)
    for page_number in range(1, page_count + 1):
        page_rows = decisions[(page_number - 1) * PAIRS_PER_PAGE : page_number * PAIRS_PER_PAGE]
        canvas = Image.new(
            "RGB", (CANVAS_WIDTH, PAGE_HEADER_HEIGHT + ROW_HEIGHT * len(page_rows)), "white"
        )
        draw = ImageDraw.Draw(canvas)
        header_title = (
            f"WP5 provisional pair review | page {page_number:03d}/{page_count:03d}"
        )
        draw.text((16, 6), header_title, fill="#111827", font=title_font)
        draw.text((16, 32), EVIDENCE_BOUNDARY, fill="#374151", font=font)
        if (
            draw.textlength(header_title, font=title_font) > CANVAS_WIDTH - 32
            or draw.textlength(EVIDENCE_BOUNDARY, font=font) > CANVAS_WIDTH - 32
        ):
            raise RuntimeError("atlas page header does not fit")
        audited_rows: list[dict[str, Any]] = []
        for local_index, row in enumerate(page_rows):
            top = PAGE_HEADER_HEIGHT + local_index * ROW_HEIGHT
            if local_index % 2:
                draw.rectangle((0, top, CANVAS_WIDTH, top + ROW_HEIGHT), fill="#f3f4f6")
            for stem, x in ((row["left_stem"], 16), (row["right_stem"], 228)):
                if stem not in thumbnail_cache:
                    with Image.open(raw_root / inventory[stem]["image_path"]) as source:
                        thumbnail_cache[stem] = fit_image(source, THUMBNAIL_SIZE)
                canvas.paste(thumbnail_cache[stem], (x, top + 16))
                draw.text((x, top + 2), stem, fill="#111827", font=font)
            status_color = "#047857" if row["review_status"] == "REVIEWED" else "#b45309"
            line1 = (
                f"{row['edge_id']} | order {row['review_order']} | slot {row['atlas_slot']} | "
                f"{row['left_split']} -> {row['right_split']} | cross={row['cross_split']}"
            )
            line2 = (
                f"proxy={row['proxy_status']} | MAE={row['thumbnail_mae']} | "
                f"dHash={row['dhash_distance']} | hist={row['rgb_histogram_cosine']}"
            )
            line3 = (
                f"classes {row['left_class_ids']} / {row['right_class_ids']} | "
                f"status={row['review_status']}"
            )
            line4 = (
                f"outcome={row['provisional_outcome'] or 'PENDING'} | "
                f"capture={row['capture_hypothesis'] or 'PENDING'}"
            )
            line5 = f"physical_sign={row['physical_sign_hypothesis'] or 'PENDING'} | confidence={row['confidence'] or 'PENDING'}"
            text_lines = [line1, line2, line3, line4, line5]
            for line_number, text in enumerate(text_lines):
                draw.text(
                    (444, top + 10 + line_number * 22),
                    text,
                    fill=status_color if line_number >= 2 else "#111827",
                    font=font,
                )
                if draw.textlength(text, font=font) > CANVAS_WIDTH - 456:
                    raise RuntimeError(f"atlas text overflow for {row['edge_id']}: {text}")
            audited_rows.append(
                {
                    "edge_id": row["edge_id"],
                    "review_order": row["review_order"],
                    "slot": row["atlas_slot"],
                    "left_image_bounds": [16, top + 16, 216, top + 128],
                    "right_image_bounds": [228, top + 16, 428, top + 128],
                    "text_bounds": [444, top + 10, CANVAS_WIDTH - 8, top + 120],
                    "text_complete": True,
                    "all_bounds_fit": top + ROW_HEIGHT <= canvas.height,
                }
            )
        page_path = assets_dir / f"page_{page_number:03d}.jpg"
        canvas.save(page_path, format="JPEG", quality=82, optimize=True, subsampling=1)
        page_paths.append(page_path)
        page_audits.append(
            {
                "page": page_number,
                "path": page_path.as_posix(),
                "width": canvas.width,
                "height": canvas.height,
                "row_count": len(page_rows),
                "rows": audited_rows,
            }
        )
    index_path = assets_dir / "index.html"
    body = [
        "<!doctype html><meta charset='utf-8'><title>WP5 provisional pair atlas</title>",
        "<style>body{font-family:system-ui;margin:2rem;max-width:1100px} table{border-collapse:collapse;width:100%} td,th{border:1px solid #bbb;padding:.35rem} .pending{color:#92400e}.reviewed{color:#047857}</style>",
        f"<h1>WP5 provisional pair atlas</h1><p>{html.escape(EVIDENCE_BOUNDARY)}</p>",
        f"<p>Cross-split pairs are first: {EXPECTED_CROSS_SPLIT_COUNT}. Total pairs: {EXPECTED_EDGE_COUNT}. A blank decision is PENDING, never approval.</p>",
        "<table><thead><tr><th>Edge</th><th>Page/slot</th><th>Endpoints</th><th>Relation</th><th>Review</th><th>Outcome</th></tr></thead><tbody>",
    ]
    for row in decisions:
        css = row["review_status"].lower()
        body.append(
            f"<tr id='{row['edge_id']}'><td>{row['edge_id']}</td>"
            f"<td><a href='page_{int(str(row['atlas_page']).split('_')[-1].split('.')[0]):03d}.jpg'>{int(str(row['atlas_page']).split('_')[-1].split('.')[0]):03d}/{row['atlas_slot']}</a></td>"
            f"<td>{row['left_stem']} / {row['right_stem']}</td><td>{row['proxy_status']}; cross={row['cross_split']}</td>"
            f"<td class='{css}'>{row['review_status']}</td><td>{html.escape(row['provisional_outcome'] or 'PENDING')}</td></tr>"
        )
    body.append("</tbody></table>")
    index_path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return [index_path, *page_paths], {
        "schema_version": 1,
        "status": "PASS_COMPLETE_PAIR_COVERAGE_TEXT_AND_BOUNDS",
        "page_count": page_count,
        "pair_count": len(decisions),
        "cross_split_first_count": EXPECTED_CROSS_SPLIT_COUNT,
        "all_headers_complete": True,
        "all_text_complete": True,
        "all_bounds_fit": all(
            row["all_bounds_fit"] and row["text_complete"]
            for page in page_audits
            for row in page["rows"]
        ),
        "pages": page_audits,
    }


def build_summary(
    decisions: list[dict[str, Any]],
    sequences: list[dict[str, Any]],
    components: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
) -> dict[str, Any]:
    reviewed = [row for row in decisions if row["review_status"] == "REVIEWED"]
    pending = [row for row in decisions if row["review_status"] == "PENDING"]
    cross_split = [row for row in decisions if row["cross_split"] == "True"]
    proxy_outcomes: dict[str, Counter[str]] = defaultdict(Counter)
    for row in reviewed:
        proxy_outcomes[row["proxy_status"]][row["provisional_outcome"]] += 1
    capture_components = [row for row in components if row["hypothesis"] == "capture"]
    physical_components = [row for row in components if row["hypothesis"] == "physical_sign"]
    return {
        "schema_version": 1,
        "package": "M0-WP5",
        "status": PACKAGE_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "manifest_contract": {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "source_count": EXPECTED_SOURCE_COUNT,
            "non_manifest_artifact_count": EXPECTED_NON_MANIFEST_ARTIFACT_COUNT,
            "atlas_page_count": EXPECTED_ATLAS_PAGE_COUNT,
            "count_semantics": MANIFEST_COUNT_SEMANTICS,
        },
        "scope": {
            "edge_count": len(decisions),
            "sequence_count": len(sequences),
            "proxy_status_counts": dict(Counter(row["proxy_status"] for row in decisions)),
            "cross_split_edge_count": len(cross_split),
            "cross_split_edges_prioritized_first": True,
        },
        "review_progress": {
            "reviewed_edge_count": len(reviewed),
            "pending_edge_count": len(pending),
            "reviewed_sequence_count": sum(row["review_status"] == "REVIEWED" for row in sequences),
            "pending_sequence_count": sum(row["review_status"] == "PENDING" for row in sequences),
            "cross_split_reviewed_edge_count": sum(row["cross_split"] == "True" for row in reviewed),
            "cross_split_pending_edge_count": sum(row["cross_split"] == "True" for row in pending),
            "outcome_counts": dict(Counter(row["provisional_outcome"] for row in reviewed)),
            "outcomes_by_proxy_status": {
                status: dict(counts) for status, counts in sorted(proxy_outcomes.items())
            },
        },
        "provisional_components": {
            "component_label": COMPONENT_LABEL,
            "capture_component_count": len(capture_components),
            "capture_image_count": len(
                {stem for row in capture_components for stem in row["members"].split(";")}
            ),
            "capture_cross_split_component_count": sum(row["cross_split"] == "True" for row in capture_components),
            "physical_sign_component_count": len(physical_components),
            "physical_sign_image_count": len(
                {stem for row in physical_components for stem in row["members"].split(";")}
            ),
            "physical_sign_cross_split_component_count": sum(row["cross_split"] == "True" for row in physical_components),
            "conflict_count": len(conflicts),
        },
        "unresolved_workload": {
            "pending_edges": len(pending),
            "pending_cross_split_edges": sum(row["cross_split"] == "True" for row in pending),
            "pending_sequences": sum(row["review_status"] == "PENDING" for row in sequences),
            "complete_visual_adjudication_achieved": False,
        },
        "d02_recommendation": {
            "preferred": "D02-A",
            "preferred_reason": "Creator/session metadata is the only available route that can directly establish capture grouping rather than infer it from visual similarity.",
            "manual_fallback": "D02-B",
            "manual_fallback_requirements": "Review all 3178 edges and 589 proxy sequences, resolve all 1031 cross-split pairs, use an independent second reviewer for positive/conflict cases, then approve a separate final grouping artifact.",
            "current_decision_status": "PENDING",
        },
        "safety_boundary": {
            "final_group_ids_created": False,
            "split_assignment_changed": False,
            "taxonomy_changed": False,
            "training_authorized": False,
            "gate0": "BLOCKED",
        },
    }


def report_markdown(summary: dict[str, Any]) -> str:
    progress = summary["review_progress"]
    components = summary["provisional_components"]
    unresolved = summary["unresolved_workload"]
    return f"""# M0-WP5 provisional grouping leakage review

Status: `{summary['status']}`  
Boundary: `{summary['evidence_boundary']}`

This package is a deterministic reviewer queue and partial visual adjudication. It is **not** creator metadata, group truth, a final split, taxonomy approval, or training authorization.

## Coverage and observed review

- Exact edge coverage: {summary['scope']['edge_count']} adjacency edges.
- Cross-split priority queue: {summary['scope']['cross_split_edge_count']} edges, all placed before same-split edges.
- Exact proxy-sequence coverage: {summary['scope']['sequence_count']} sequences linked to the 24 QA-approved WP3 contact sheets.
- Actually visually reviewed: {progress['reviewed_edge_count']} edges ({progress['cross_split_reviewed_edge_count']} cross-split).
- Still `PENDING`: {progress['pending_edge_count']} edges, including {progress['cross_split_pending_edge_count']} cross-split edges, plus {progress['pending_sequence_count']} sequences.
- Reviewed outcomes: `{json.dumps(progress['outcome_counts'], sort_keys=True)}`.

## Provisional leakage hypotheses

- High-confidence capture components: {components['capture_component_count']} components across {components['capture_image_count']} images; {components['capture_cross_split_component_count']} cross split.
- High-confidence physical-sign components: {components['physical_sign_component_count']} components across {components['physical_sign_image_count']} images; {components['physical_sign_cross_split_component_count']} cross split.
- Conflicts detected inside these provisional components: {components['conflict_count']}.
- Every component is labeled `{components['component_label']}` and cannot be consumed as a final `group_id`.

## Decision D-02 recommendation

Prefer **D02-A**: obtain creator/session metadata, because visual similarity cannot establish true capture sessions. If that is unavailable, **D02-B** remains a funded manual fallback only after all {unresolved['pending_edges']} pending edges and {unresolved['pending_sequences']} pending sequences are reviewed, all cross-split pairs are resolved, and a second reviewer checks positive/conflict cases. D-02 remains `PENDING`.

## Fail-closed manifest contract

- Manifest schema: v{summary['manifest_contract']['schema_version']}.
- Canonical source/control roster: {summary['manifest_contract']['source_count']} exact ID/path records.
- Canonical non-manifest artifact roster: {summary['manifest_contract']['non_manifest_artifact_count']} exact ID/path records, including {summary['manifest_contract']['atlas_page_count']} JPEG pages plus the atlas index and required tables/reports/schema/layout.
- Count semantics: `{summary['manifest_contract']['count_semantics']}`; the manifest cannot hash or count itself recursively.
- Verification rejects missing, duplicate or extra records; wrong paths/types; forged counts/bytes; missing first/middle/last atlas pages; path escape; and valid-but-unexpected files.

## Safety state

Gate 0 remains `BLOCKED`; training remains unauthorized. No split, taxonomy, source image, source label, model, or runtime artifact is changed by this package.
"""


def relative_record(path: Path, repo_root: Path, item_id: str) -> dict[str, Any]:
    relative = path.resolve().relative_to(repo_root.resolve())
    return {
        "id": item_id,
        "path": relative.as_posix(),
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
    }


def canonical_source_contract(repo_root: Path) -> list[tuple[str, Path]]:
    """Return the exact WP5 source/control roster independently of manifest contents."""
    generated = repo_root / "docs/review/generated"
    review = repo_root / "docs/review"
    audit_dir = repo_root / "results/data_audit/DATASET01_052bc980a7206f8d"
    return [
        ("wp2_grouping_edges", generated / "grouping_proxy_edges.csv"),
        ("wp2_grouping_clusters", generated / "grouping_proxy_clusters.csv"),
        ("wp2_manifest", generated / "wp2_generated_manifest.json"),
        ("wp3_grouping_index", generated / "wp3_grouping_review_index.csv"),
        ("wp3_layout_audit", generated / "wp3_render_layout_audit.json"),
        ("wp3_manifest", generated / "wp3_evidence_manifest.json"),
        ("wp4_manifest", generated / "wp4_qcvn_manifest.json"),
        ("image_inventory", audit_dir / "image_inventory.csv"),
        ("source_preservation_proof", audit_dir / "source_preservation_proof.json"),
        ("decision_status", review / "decision_status.json"),
        ("visual_annotations", review / "wp5_visual_review_annotations.json"),
    ]


def canonical_artifact_contract(repo_root: Path) -> list[tuple[str, Path]]:
    """Return the exact non-manifest artifact roster derived from the WP5 contract."""
    generated = repo_root / "docs/review/generated"
    review = repo_root / "docs/review"
    assets = review / "assets/wp5/pairs"
    contract = [
        ("edge_decisions", generated / "wp5_provisional_edge_decisions.csv"),
        ("sequence_review_queue", generated / "wp5_sequence_review_queue.csv"),
        ("provisional_components", generated / "wp5_provisional_components.csv"),
        ("component_conflicts", generated / "wp5_component_conflicts.csv"),
        ("decision_schema", generated / "wp5_provisional_decision.schema.json"),
        ("layout_audit", generated / "wp5_pair_layout_audit.json"),
        ("leakage_report", generated / "wp5_leakage_report.json"),
        ("review_report", review / "wp5_provisional_grouping_report.md"),
        ("pair_atlas_000", assets / "index.html"),
    ]
    contract.extend(
        (f"pair_atlas_{page:03d}", assets / f"page_{page:03d}.jpg")
        for page in range(1, EXPECTED_ATLAS_PAGE_COUNT + 1)
    )
    return contract


def contract_signature(
    records: list[tuple[str, Path]], repo_root: Path
) -> list[tuple[str, str]]:
    return [
        (item_id, path.resolve().relative_to(repo_root.resolve()).as_posix())
        for item_id, path in records
    ]


def build_manifest(
    repo_root: Path,
    source_paths: list[tuple[str, Path]],
    artifact_paths: list[tuple[str, Path]],
    decision_status_sha256: str,
    source_tree_manifest_sha256: str,
) -> dict[str, Any]:
    expected_sources = canonical_source_contract(repo_root)
    expected_artifacts = canonical_artifact_contract(repo_root)
    if contract_signature(source_paths, repo_root) != contract_signature(
        expected_sources, repo_root
    ):
        raise ValueError("source roster does not match the canonical WP5 contract")
    if contract_signature(artifact_paths, repo_root) != contract_signature(
        expected_artifacts, repo_root
    ):
        raise ValueError("artifact roster does not match the canonical WP5 contract")
    sources = [relative_record(path, repo_root, item_id) for item_id, path in source_paths]
    artifacts = [relative_record(path, repo_root, item_id) for item_id, path in artifact_paths]
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "package": "M0-WP5",
        "status": PACKAGE_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "gate0": "BLOCKED",
        "training_authorized": False,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": MANIFEST_COUNT_SEMANTICS,
        "edge_count": EXPECTED_EDGE_COUNT,
        "sequence_count": EXPECTED_SEQUENCE_COUNT,
        "cross_split_edge_count": EXPECTED_CROSS_SPLIT_COUNT,
        "atlas_page_count": EXPECTED_ATLAS_PAGE_COUNT,
        "decision_status_sha256": decision_status_sha256,
        "source_tree_manifest_sha256": source_tree_manifest_sha256,
        "sources": sources,
        "artifacts": artifacts,
        "source_count": len(sources),
        "artifact_count": len(artifacts),
        "total_artifact_bytes": sum(record["size"] for record in artifacts),
    }


def assert_decision_boundary(decision_status_path: Path) -> None:
    payload = json.loads(decision_status_path.read_text(encoding="utf-8"))
    if payload.get("gate0") != "BLOCKED" or payload.get("training_authorized") is not False:
        raise ValueError("Gate 0 must remain blocked and training unauthorized")
    if payload.get("decisions", {}).get("D-02", {}).get("status") != "PENDING":
        raise ValueError("D-02 must remain PENDING")


def build_package(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = args.repo_root.resolve()
    generated = repo_root / "docs/review/generated"
    review = repo_root / "docs/review"
    assets_dir = review / "assets/wp5/pairs"
    audit_dir = repo_root / "results/data_audit/DATASET01_052bc980a7206f8d"
    source_paths = canonical_source_contract(repo_root)
    for _, path in source_paths:
        if not path.is_file():
            raise FileNotFoundError(path)
    decision_path = review / "decision_status.json"
    decision_before = sha256_file(decision_path)
    assert_decision_boundary(decision_path)
    proof = json.loads((audit_dir / "source_preservation_proof.json").read_text(encoding="utf-8"))
    if proof.get("unchanged") is not True:
        raise ValueError("source preservation proof is not unchanged=true")
    edges = read_csv(generated / "grouping_proxy_edges.csv")
    clusters = read_csv(generated / "grouping_proxy_clusters.csv")
    wp3_index = read_csv(generated / "wp3_grouping_review_index.csv")
    inventory_rows = read_csv(audit_dir / "image_inventory.csv")
    inventory = validate_inputs(edges, clusters, wp3_index, inventory_rows)
    edges_by_id = {
        f"edge_{index:06d}": row for index, row in enumerate(edges, start=1)
    }
    annotations = load_annotations(
        review / "wp5_visual_review_annotations.json", edges_by_id
    )
    source_cache = verify_inventory_sources(inventory, args.raw_root.resolve())
    decisions = build_decision_rows(edges, inventory, annotations)
    schema = decision_schema()
    validate_decisions(decisions, schema)
    for row in decisions:
        for stem, prefix in ((row["left_stem"], "left"), (row["right_stem"], "right")):
            cached = source_cache[stem]
            if row[f"{prefix}_image_sha256"] != cached["image_sha256"] or row[f"{prefix}_label_sha256"] != cached["label_sha256"]:
                raise RuntimeError(f"decision source hashes did not reconcile for {row['edge_id']}")
    sequence_rows = build_sequence_rows(clusters, wp3_index)
    capture_components, capture_conflicts = build_components(decisions, "capture")
    physical_components, physical_conflicts = build_components(decisions, "physical_sign")
    components = [*capture_components, *physical_components]
    conflicts = [*capture_conflicts, *physical_conflicts]

    decisions_path = generated / "wp5_provisional_edge_decisions.csv"
    sequences_path = generated / "wp5_sequence_review_queue.csv"
    components_path = generated / "wp5_provisional_components.csv"
    conflicts_path = generated / "wp5_component_conflicts.csv"
    schema_path = generated / "wp5_provisional_decision.schema.json"
    layout_path = generated / "wp5_pair_layout_audit.json"
    summary_path = generated / "wp5_leakage_report.json"
    report_path = review / "wp5_provisional_grouping_report.md"
    manifest_path = generated / "wp5_evidence_manifest.json"
    write_csv(decisions_path, decisions, DECISION_FIELDS)
    write_csv(sequences_path, sequence_rows, SEQUENCE_FIELDS)
    write_csv(components_path, components, COMPONENT_FIELDS)
    write_csv(conflicts_path, conflicts, CONFLICT_FIELDS)
    write_json(schema_path, schema)
    atlas_paths, layout = render_pair_atlas(
        decisions, inventory, args.raw_root.resolve(), assets_dir
    )
    # Store repository-relative paths so the layout is deterministic across checkouts.
    for page in layout["pages"]:
        page["path"] = Path(page["path"]).resolve().relative_to(repo_root).as_posix()
    write_json(layout_path, layout)
    summary = build_summary(decisions, sequence_rows, components, conflicts)
    summary["source_reconciliation"] = {
        "unique_inventory_sources_verified": len(source_cache),
        "edge_endpoint_occurrences_reconciled": len(decisions) * 2,
        "all_image_hashes_match_inventory": True,
        "all_label_hashes_match_inventory": True,
        "source_tree_unchanged": True,
    }
    write_json(summary_path, summary)
    report_path.write_text(report_markdown(summary), encoding="utf-8")
    if sha256_file(decision_path) != decision_before:
        raise RuntimeError("decision_status.json changed during WP5 build")
    assert_decision_boundary(decision_path)

    artifact_paths = canonical_artifact_contract(repo_root)
    if [path.resolve() for path in atlas_paths] != [
        path.resolve() for _, path in artifact_paths[8:]
    ]:
        raise RuntimeError("rendered atlas roster does not match its canonical contract")
    manifest = build_manifest(
        repo_root,
        source_paths,
        artifact_paths,
        decision_before,
        proof["source_tree_manifest_sha256"],
    )
    write_json(manifest_path, manifest)
    return {
        "status": PACKAGE_STATUS,
        "reviewed_edges": summary["review_progress"]["reviewed_edge_count"],
        "pending_edges": summary["review_progress"]["pending_edge_count"],
        "cross_split_edges": summary["scope"]["cross_split_edge_count"],
        "sequence_count": summary["scope"]["sequence_count"],
        "atlas_pages": layout["page_count"],
        "component_count": len(components),
        "artifact_count": manifest["artifact_count"],
        "decision_status_sha256": decision_before,
    }


def resolve_manifest_path(repo_root: Path, value: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe manifest path: {value}")
    target = (repo_root / relative).resolve()
    target.relative_to(repo_root.resolve())
    return target


def validate_manifest_collection(
    payload: dict[str, Any],
    collection: str,
    expected_contract: list[tuple[str, Path]],
    repo_root: Path,
    errors: list[str],
) -> list[dict[str, Any]]:
    """Validate exact membership, record types, order, roots, IDs and paths."""
    raw_records = payload.get(collection)
    if not isinstance(raw_records, list):
        errors.append(f"{collection} must be a list")
        return []
    expected = contract_signature(expected_contract, repo_root)
    expected_by_id = dict(expected)
    records: list[dict[str, Any]] = []
    ids: list[str] = []
    paths: list[str] = []
    required_fields = {"id", "path", "sha256", "size"}
    for index, record in enumerate(raw_records):
        if not isinstance(record, dict):
            errors.append(f"{collection}[{index}] must be an object")
            continue
        if set(record) != required_fields:
            errors.append(
                f"{collection}[{index}] fields must be exactly {sorted(required_fields)}"
            )
        item_id = record.get("id")
        path_value = record.get("path")
        digest = record.get("sha256")
        size = record.get("size")
        if not isinstance(item_id, str) or not item_id:
            errors.append(f"{collection}[{index}].id must be a non-empty string")
        else:
            ids.append(item_id)
        if not isinstance(path_value, str) or not path_value:
            errors.append(f"{collection}[{index}].path must be a non-empty string")
        else:
            paths.append(path_value)
            try:
                resolve_manifest_path(repo_root, path_value)
            except (ValueError, OSError) as exc:
                errors.append(str(exc))
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            errors.append(f"{collection}[{index}].sha256 must be lowercase hex64")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            errors.append(f"{collection}[{index}].size must be a non-negative integer")
        records.append(record)
    duplicate_ids = sorted(item for item, count in Counter(ids).items() if count > 1)
    duplicate_paths = sorted(item for item, count in Counter(paths).items() if count > 1)
    if duplicate_ids:
        errors.append(f"duplicate {collection} IDs: {duplicate_ids}")
    if duplicate_paths:
        errors.append(f"duplicate {collection} paths: {duplicate_paths}")
    actual_pairs = [
        (record.get("id"), record.get("path"))
        for record in records
        if isinstance(record.get("id"), str) and isinstance(record.get("path"), str)
    ]
    actual_ids = {item_id for item_id, _ in actual_pairs}
    expected_ids = set(expected_by_id)
    missing = sorted(expected_ids - actual_ids)
    extra = sorted(actual_ids - expected_ids)
    if missing:
        errors.append(f"missing canonical {collection} IDs: {missing}")
    if extra:
        errors.append(f"unexpected {collection} IDs: {extra}")
    for item_id, path_value in actual_pairs:
        if item_id in expected_by_id and path_value != expected_by_id[item_id]:
            errors.append(
                f"unexpected {collection} path for {item_id}: {path_value}"
            )
    if actual_pairs != expected:
        errors.append(f"{collection} roster/order differs from canonical contract")
    return records


def verify_manifest(manifest_path: Path, repo_root: Path, raw_root: Path) -> dict[str, Any]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {
            "valid": False,
            "errors": [f"manifest unreadable: {exc}"],
            "source_count": 0,
            "artifact_count": 0,
        }
    if not isinstance(payload, dict):
        return {
            "valid": False,
            "errors": ["manifest root must be an object"],
            "source_count": 0,
            "artifact_count": 0,
        }
    errors: list[str] = []
    expected_top_level_fields = {
        "schema_version",
        "package",
        "status",
        "evidence_boundary",
        "gate0",
        "training_authorized",
        "manifest_path",
        "manifest_self_in_artifact_count",
        "artifact_count_semantics",
        "edge_count",
        "sequence_count",
        "cross_split_edge_count",
        "atlas_page_count",
        "decision_status_sha256",
        "source_tree_manifest_sha256",
        "sources",
        "artifacts",
        "source_count",
        "artifact_count",
        "total_artifact_bytes",
    }
    if set(payload) != expected_top_level_fields:
        errors.append("manifest top-level fields differ from schema v2 contract")
    constants = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "package": "M0-WP5",
        "status": PACKAGE_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "gate0": "BLOCKED",
        "training_authorized": False,
        "manifest_path": MANIFEST_RELATIVE_PATH,
        "manifest_self_in_artifact_count": False,
        "artifact_count_semantics": MANIFEST_COUNT_SEMANTICS,
        "edge_count": EXPECTED_EDGE_COUNT,
        "sequence_count": EXPECTED_SEQUENCE_COUNT,
        "cross_split_edge_count": EXPECTED_CROSS_SPLIT_COUNT,
        "atlas_page_count": EXPECTED_ATLAS_PAGE_COUNT,
    }
    for field, expected_value in constants.items():
        if payload.get(field) != expected_value:
            errors.append(
                f"invalid manifest {field}: expected {expected_value!r}, got {payload.get(field)!r}"
            )
    source_records = validate_manifest_collection(
        payload,
        "sources",
        canonical_source_contract(repo_root),
        repo_root,
        errors,
    )
    artifact_records = validate_manifest_collection(
        payload,
        "artifacts",
        canonical_artifact_contract(repo_root),
        repo_root,
        errors,
    )
    all_ids = [record.get("id") for record in [*source_records, *artifact_records]]
    all_paths = [record.get("path") for record in [*source_records, *artifact_records]]
    duplicate_global_ids = sorted(
        item
        for item, count in Counter(item for item in all_ids if isinstance(item, str)).items()
        if count > 1
    )
    duplicate_global_paths = sorted(
        item
        for item, count in Counter(item for item in all_paths if isinstance(item, str)).items()
        if count > 1
    )
    if duplicate_global_ids:
        errors.append(f"duplicate global manifest IDs: {duplicate_global_ids}")
    if duplicate_global_paths:
        errors.append(f"duplicate global manifest paths: {duplicate_global_paths}")
    if payload.get("source_count") != len(source_records) or payload.get(
        "source_count"
    ) != EXPECTED_SOURCE_COUNT:
        errors.append("source_count does not equal the canonical 11-source roster")
    if payload.get("artifact_count") != len(artifact_records) or payload.get(
        "artifact_count"
    ) != EXPECTED_NON_MANIFEST_ARTIFACT_COUNT:
        errors.append("artifact_count does not equal the canonical 137-artifact roster")
    declared_total_bytes = payload.get("total_artifact_bytes")
    if isinstance(declared_total_bytes, bool) or not isinstance(
        declared_total_bytes, int
    ):
        errors.append("total_artifact_bytes must be an integer")
    elif declared_total_bytes != sum(
        record.get("size", -1)
        for record in artifact_records
        if isinstance(record.get("size"), int)
        and not isinstance(record.get("size"), bool)
    ):
        errors.append("total_artifact_bytes does not equal artifact record sizes")
    for collection, records in (
        ("sources", source_records),
        ("artifacts", artifact_records),
    ):
        for record in records:
            key = record.get("path")
            if not isinstance(key, str) or not key:
                continue
            try:
                path = resolve_manifest_path(repo_root, key)
            except (ValueError, OSError):
                continue
            if not path.is_file():
                errors.append(f"missing {collection} file: {key}")
                continue
            if sha256_file(path) != record.get("sha256") or path.stat().st_size != record.get("size"):
                errors.append(f"tampered {collection} file: {key}")
    actual_artifact_bytes = 0
    for record in artifact_records:
        if not isinstance(record.get("path"), str):
            continue
        try:
            artifact_path = resolve_manifest_path(repo_root, record["path"])
        except (ValueError, OSError):
            continue
        if artifact_path.is_file():
            actual_artifact_bytes += artifact_path.stat().st_size
    if isinstance(declared_total_bytes, int) and not isinstance(
        declared_total_bytes, bool
    ) and declared_total_bytes != actual_artifact_bytes:
        errors.append("total_artifact_bytes does not equal actual artifact bytes")
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "source_count": len(source_records),
            "artifact_count": len(artifact_records),
        }
    decision_path = repo_root / "docs/review/decision_status.json"
    try:
        assert_decision_boundary(decision_path)
        if sha256_file(decision_path) != payload.get("decision_status_sha256"):
            errors.append("decision_status hash differs from manifest")
        source_proof = json.loads(
            (
                repo_root
                / "results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json"
            ).read_text(encoding="utf-8")
        )
        if source_proof.get("unchanged") is not True:
            errors.append("source preservation proof is not unchanged=true")
        if source_proof.get("source_tree_manifest_sha256") != payload.get(
            "source_tree_manifest_sha256"
        ):
            errors.append("source tree manifest hash differs from preservation proof")
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        errors.append(f"decision boundary invalid: {exc}")
    try:
        decisions = read_csv(repo_root / "docs/review/generated/wp5_provisional_edge_decisions.csv")
        typed: list[dict[str, Any]] = []
        for row in decisions:
            row["review_order"] = int(row["review_order"])
            row["atlas_slot"] = int(row["atlas_slot"])
            typed.append(row)
        schema = json.loads(
            (repo_root / "docs/review/generated/wp5_provisional_decision.schema.json").read_text(encoding="utf-8")
        )
        validate_decisions(typed, schema)
        inventory_rows = read_csv(
            repo_root / "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv"
        )
        inventory = {row["stem"]: row for row in inventory_rows}
        source_cache = verify_inventory_sources(inventory, raw_root)
        for row in typed:
            for stem, prefix in ((row["left_stem"], "left"), (row["right_stem"], "right")):
                if row[f"{prefix}_image_sha256"] != source_cache[stem]["image_sha256"]:
                    raise ValueError(f"image hash mismatch in decision row {row['edge_id']}")
                if row[f"{prefix}_label_sha256"] != source_cache[stem]["label_sha256"]:
                    raise ValueError(f"label hash mismatch in decision row {row['edge_id']}")
        layout = json.loads(
            (repo_root / "docs/review/generated/wp5_pair_layout_audit.json").read_text(encoding="utf-8")
        )
        if (
            layout.get("page_count") != EXPECTED_ATLAS_PAGE_COUNT
            or not isinstance(layout.get("pages"), list)
            or len(layout["pages"]) != EXPECTED_ATLAS_PAGE_COUNT
            or layout.get("pair_count") != EXPECTED_EDGE_COUNT
            or layout.get("cross_split_first_count") != EXPECTED_CROSS_SPLIT_COUNT
            or not layout.get("all_bounds_fit")
            or not layout.get("all_text_complete")
            or not layout.get("all_headers_complete")
        ):
            raise ValueError("layout audit does not prove complete pair coverage")
        for page_number, page in enumerate(layout["pages"], start=1):
            expected_row_count = min(
                PAIRS_PER_PAGE,
                EXPECTED_EDGE_COUNT - (page_number - 1) * PAIRS_PER_PAGE,
            )
            expected_path = (
                f"docs/review/assets/wp5/pairs/page_{page_number:03d}.jpg"
            )
            if page.get("page") != page_number or page.get("path") != expected_path:
                raise ValueError(f"layout page {page_number} identity/path mismatch")
            if page.get("row_count") != expected_row_count or len(
                page.get("rows", [])
            ) != expected_row_count:
                raise ValueError(f"layout page {page_number} row coverage mismatch")
        layout_ids = [row["edge_id"] for page in layout["pages"] for row in page["rows"]]
        if layout_ids != [row["edge_id"] for row in typed]:
            raise ValueError("layout edge order does not match decisions")
        summary = json.loads(
            (repo_root / "docs/review/generated/wp5_leakage_report.json").read_text(encoding="utf-8")
        )
        if summary.get("scope") != {
            "cross_split_edge_count": EXPECTED_CROSS_SPLIT_COUNT,
            "cross_split_edges_prioritized_first": True,
            "edge_count": EXPECTED_EDGE_COUNT,
            "proxy_status_counts": EXPECTED_PROXY_COUNTS,
            "sequence_count": EXPECTED_SEQUENCE_COUNT,
        }:
            raise ValueError("summary scope/count contract is invalid")
        if summary["safety_boundary"] != {
            "final_group_ids_created": False,
            "gate0": "BLOCKED",
            "split_assignment_changed": False,
            "taxonomy_changed": False,
            "training_authorized": False,
        }:
            raise ValueError("summary safety boundary is invalid")
        forbidden_headers = {
            "group_id",
            "final_group_id",
            "assigned_split",
            "approved_split",
        }
        for candidate in (
            repo_root / "docs/review/generated/wp5_provisional_edge_decisions.csv",
            repo_root / "docs/review/generated/wp5_sequence_review_queue.csv",
            repo_root / "docs/review/generated/wp5_provisional_components.csv",
        ):
            header = set(read_csv(candidate)[0]) if candidate.name != "wp5_provisional_components.csv" or read_csv(candidate) else set(COMPONENT_FIELDS)
            if forbidden_headers & header:
                raise ValueError(f"final grouping/split field found in {candidate.name}")
    except (
        ValueError,
        TypeError,
        FileNotFoundError,
        KeyError,
        IndexError,
        json.JSONDecodeError,
    ) as exc:
        errors.append(f"semantic verification failed: {exc}")
    return {
        "valid": not errors,
        "errors": errors,
        "source_count": len(source_records),
        "artifact_count": len(artifact_records),
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--repo-root", type=Path, required=True)
    build.add_argument("--raw-root", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--repo-root", type=Path, required=True)
    verify.add_argument("--raw-root", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "build":
        result = build_package(args)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    result = verify_manifest(args.manifest, args.repo_root.resolve(), args.raw_root.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
