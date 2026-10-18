"""Read-only DATASET01 views for the Streamlit app: graph with D-02 groups, class and group tables,
and the data for the animated pipeline.

`dataset_graph.py` is hash-pinned by WP31-R1/R2 and stays unchanged; this module wraps it. Every
number comes from files already in the repository (inventory, WP5 edges and overlays, WP33 labels,
D-02 registry, WP34 support, D-04 part 1 decisions, WP35 lineage). Nothing here is an owner
decision, a split or a training run.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from cpv301_autodrive.config import PROJECT_ROOT
from cpv301_autodrive.dataset_graph import _read_csv, build_graph_payload

ASSETS = Path(__file__).with_name("assets")
GRAPH_TEMPLATE = ASSETS / "dataset01_graph.html"
PIPELINE_TEMPLATE = ASSETS / "dataset01_pipeline.html"
INVENTORY = Path("results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
D02_REGISTRY = Path("docs/review/generated/d02_group_id_registry.csv")
WP33_BOXES = Path("docs/review/generated/wp33_derived_boxes.csv")
WP33_TAXONOMY = Path("docs/review/generated/wp33_derived_taxonomy.csv")
WP34_SUPPORT = Path("docs/review/generated/wp34_d04_class_support.csv")
D04_PART1 = Path("docs/review/generated/d04_owner_decisions_part1.csv")
WP35_LINEAGE = Path("docs/review/generated/wp35_enrichment_lineage.csv")
SPLIT_CODE = {"train": 0, "test": 1, "unassigned": 2}

# The four D-04 buckets in display order, with the owner decision applied to the last one.
BUCKETS = (
    ("KEEP_FULL", "≥ 3 nhóm — đủ train/val/test"),
    ("KEEP_TRAIN_AND_TEST_NO_VAL", "2 nhóm — train và test, không có val"),
    ("KEEP_TRAIN_ONLY_UNVERIFIED", "1 nhóm, ≥ 30 ảnh — chỉ train"),
    ("DROP_FROM_V1_COLLECT_MORE", "1 nhóm, < 30 ảnh — làm giàu dữ liệu (WP35)"),
)


def _json(payload: Any) -> str:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")


def graph_payload(repo_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Graph payload with vendor splits from the inventory and components = D-02 groups."""
    payload = build_graph_payload(repo_root)
    split = {row["stem"]: row["split"] for row in _read_csv(repo_root / INVENTORY)}
    group_of = {row["stem"]: row["group_id"] for row in _read_csv(repo_root / D02_REGISTRY)}
    groups = sorted(set(group_of.values()))
    index = {name: position for position, name in enumerate(groups)}
    for node in payload["nodes"]:
        node[1] = SPLIT_CODE[split[node[0]]]
    payload["comp"] = [index.get(group_of.get(node[0], ""), -1) for node in payload["nodes"]]
    payload["groups"] = groups
    members: dict[int, set[int]] = defaultdict(set)
    for node, group in zip(payload["nodes"], payload["comp"], strict=True):
        if group >= 0:
            members[group].add(node[1])
    summary = payload["summary"]
    counts = Counter(node[1] for node in payload["nodes"])
    summary.update(
        train=counts[0],
        test=counts[1],
        unassigned=counts[2],
        groups=len(groups),
        mixedGroups=sum(1 for splits in members.values() if {0, 1} <= splits),
    )
    return payload


def class_rows(repo_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    support = _read_csv(repo_root / WP34_SUPPORT)
    decided = {row["derived_key"]: row for row in _read_csv(repo_root / D04_PART1)}
    augmented = (
        Counter(row["derived_key"] for row in _read_csv(repo_root / WP35_LINEAGE))
        if (repo_root / WP35_LINEAGE).is_file()
        else Counter()
    )
    labels = dict(BUCKETS)
    rows = []
    for row in support:
        key = row["derived_key"]
        owner = decided.get(key, {}).get("owner_decision", "")
        rows.append(
            {
                "Lớp": key,
                "Mã QCVN": row["derived_code"],
                "Tên biển": row["derived_name_vi"],
                "Ảnh": int(row["images"]),
                "Box": int(row["train_boxes"]),
                "Nhóm D-02": int(row["groups"]),
                "Nhóm D-04": labels[row["proposed_option"]],
                "bucket": row["proposed_option"],
                "Ảnh làm giàu": augmented.get(key, 0),
                "Trạng thái": "Owner duyệt: train + làm giàu"
                if owner == "TRAIN_WITH_ENRICHMENT"
                else "Đề xuất, chờ owner",
            }
        )
    return rows


def group_rows(repo_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    registry = _read_csv(repo_root / D02_REGISTRY)
    classes_of: dict[str, Counter[str]] = defaultdict(Counter)
    for box in _read_csv(repo_root / WP33_BOXES):
        if box["train_eligible"] == "True":
            classes_of[box["stem"]][box["derived_code"]] += 1
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in registry:
        grouped[row["group_id"]].append(row)
    rows = []
    for group_id in sorted(grouped):
        frames = grouped[group_id]
        splits = Counter(frame["vendor_split"] for frame in frames)
        codes: Counter[str] = Counter()
        for frame in frames:
            codes.update(classes_of[frame["stem"]])
        rows.append(
            {
                "Nhóm": group_id,
                "Ảnh": len(frames),
                "Train": splits["train"],
                "Test": splits["test"],
                "Unassigned": splits["unassigned"],
                "Stem": f"{frames[0]['stem']}–{frames[-1]['stem']}",
                "Số lớp": len(codes),
                "Biển nhiều nhất": ", ".join(code for code, _n in codes.most_common(3)),
                "Chéo split gốc": splits["train"] > 0 and splits["test"] > 0,
            }
        )
    return rows


def pipeline_payload(repo_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    graph = graph_payload(repo_root)
    nodes, comp = graph["nodes"], graph["comp"]
    step = 12  # one dot per 12 frames keeps the animation readable
    dots = [[node[0], node[1], comp[i]] for i, node in enumerate(nodes) if i % step == 0]
    sizes = Counter(c for c in comp if c >= 0)
    taxonomy = _read_csv(repo_root / WP33_TAXONOMY)
    classes = [
        {
            "key": row["Lớp"],
            "code": row["Mã QCVN"],
            "images": row["Ảnh"],
            "groups": row["Nhóm D-02"],
            "bucket": row["bucket"],
            "aug": row["Ảnh làm giàu"],
        }
        for row in class_rows(repo_root)
    ]
    summary = graph["summary"]
    return {
        "dots": dots,
        "step": step,
        "groupSizes": [sizes[i] for i in range(len(graph["groups"]))],
        "classes": classes,
        "buckets": [list(bucket) for bucket in BUCKETS],
        "stats": {
            "frames": summary["nodes"],
            "edges": summary["edges"],
            "same": summary["cap"].get("S", 0),
            "notRelated": summary["cap"].get("N", 0),
            "unresolved": summary["cap"].get("U", 0),
            "quarantined": summary["cap"].get("Q", 0),
            "groups": summary["groups"],
            "mixedGroups": summary["mixedGroups"],
            "boxes": sum(int(row["train_boxes"]) + int(row["excluded_boxes"]) for row in taxonomy),
            "trainBoxes": sum(int(row["train_boxes"]) for row in taxonomy),
            "trainClasses": sum(1 for row in taxonomy if row["role"] == "CLASS"),
            "augmented": sum(c["aug"] for c in classes),
        },
    }


def render_graph_html(repo_root: Path = PROJECT_ROOT) -> str:
    return GRAPH_TEMPLATE.read_text(encoding="utf-8").replace(
        "__DATA__", _json(graph_payload(repo_root))
    )


def render_pipeline_html(repo_root: Path = PROJECT_ROOT) -> str:
    return PIPELINE_TEMPLATE.read_text(encoding="utf-8").replace(
        "__DATA__", _json(pipeline_payload(repo_root))
    )
