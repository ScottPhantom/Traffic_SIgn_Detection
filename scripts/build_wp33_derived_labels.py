#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and verify M0-WP33: the D-03 derived label set for DATASET01 (raw labels immutable).

Applies the owner's D-03 decisions (parts 1 and 2, the policies table, and the 2026-10-17 WP33
answers) to every raw YOLO box and writes a box-level derived label table plus a derived taxonomy.

- Class 23: one renamed class "P.111a+P.111b" (combined sign). The owner's earlier "split into
  P.111a–d" decision was revised because every reviewed box shows the combined design.
- Classes 16 (P.117) and 43 (W.239b): split by the height value read in
  `docs/review/wp33_height_value_decisions.csv`; unreadable values are excluded from training.
- Stem 0776 line 7: raw class 18 is a mislabelled height-limit sign with an unreadable value; it
  is removed from class 18 and excluded from training.
- Class 31: routed to UNKNOWN, kept for out-of-taxonomy evaluation only.
- Stem 0248 stays quarantined (all boxes excluded).

The raw label files are only read and are hash-checked against the WP1 inventory. Class index
assignment for training is left to the split package, because D-04 may still remove classes.
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
DEFAULT_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"
PACKAGE_STATUS = "WP33_DERIVED_LABELS_AWAITING_QA"
QUARANTINED_STEM = "0248"
COMBINED_23 = ("P.111a+P.111b", "Cấm xe gắn máy và xe ba bánh có động cơ (biển ghép)", "No Mopeds and Motorised Three-Wheelers (combined sign)")
HEIGHT_NAMES = {
    "16": ("P.117", "Hạn chế chiều cao", "Height Limit"),
    "43": ("W.239b", "Chiều cao tĩnh không thực tế", "Actual Clearance Height"),
}

INVENTORY = Path("results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
PART1 = Path("docs/review/generated/d03_owner_decisions_part1.csv")
PART2 = Path("docs/review/generated/d03_owner_decisions_part2.csv")
HEIGHTS = Path("docs/review/wp33_height_value_decisions.csv")
PINNED_SOURCES = {
    INVENTORY.as_posix(): "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022",
    PART1.as_posix(): "24a2695fe3ea39669970179f7b34297e1f0fa686b299e5b901c6f0d5563e7091",
    PART2.as_posix(): "8d976868108820f8504ccfc96a5a72ac182abbe91288a171a3b3879be3a4e7b9",
    "docs/review/generated/d03_owner_policies.csv": "f0593804cba228e5f6b30c6fe6fe84de52e34d2384aa38c53a9355220cfd7671",
    HEIGHTS.as_posix(): "329ff96518e1a0b8c4702a14a11ad6e8a7446d227e01976cf1a344fac0fdc163",
    "docs/review/d03_owner_decision_part1_record.md": "54c2cf2b42a1230e2c66dfef4d9388ed3159ca3dfe077fa77a70751c0c3b96e5",
    "docs/review/d03_owner_decision_part2_record.md": "93044c877b517ecb063895ed2da0ece9daa8660cba2f662dcc0bd9927944dc7a",
}

GENERATED = Path("docs/review/generated")
BOXES_PATH = GENERATED / "wp33_derived_boxes.csv"
TAXONOMY_PATH = GENERATED / "wp33_derived_taxonomy.csv"
MANIFEST_PATH = GENERATED / "wp33_derived_labels_manifest.json"
REPORT_PATH = Path("docs/review/wp33_derived_labels_report.md")
BOX_FIELDS = [
    "stem", "line", "raw_class", "x", "y", "w", "h", "derived_key", "derived_code",
    "derived_name_vi", "train_eligible", "eval_role", "reason",
]
TAXONOMY_FIELDS = ["derived_key", "source_raw_class", "derived_code", "derived_name_vi", "derived_name_en", "train_boxes", "excluded_boxes", "role"]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def to_csv(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def verify_pins(repo_root: Path) -> None:
    for relative, digest in PINNED_SOURCES.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or sha256_bytes(path.read_bytes()) != digest:
            raise ValueError(f"pinned WP33 source changed: {relative}")


def class_names(repo_root: Path) -> dict[str, tuple[str, str, str, str]]:
    """raw class -> (code, name_vi, name_en, role) from D-03 parts 1 and 2."""
    names: dict[str, tuple[str, str, str, str]] = {}
    for row in read_csv(repo_root / PART1):
        names[row["class_id"]] = (row["approved_code"], row["approved_name_vi"], row["approved_name_en"], "CLASS")
    for row in read_csv(repo_root / PART2):
        if row["owner_choice"] == "ROUTE_TO_UNKNOWN":
            names[row["class_id"]] = ("UNKNOWN", "Ngoài taxonomy", "Out of taxonomy", "UNKNOWN_EVAL_ONLY")
        elif row["class_id"] == "23":
            names["23"] = (*COMBINED_23, "CLASS")
        else:
            names[row["class_id"]] = (row["approved_code"], row["approved_name_vi"], row["approved_name_en"], "CLASS")
    if set(names) != {str(i) for i in range(52)}:
        raise ValueError("D-03 decisions must cover exactly classes 0..51")
    return names


def derive(repo_root: Path, raw_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    verify_pins(repo_root)
    names = class_names(repo_root)
    heights = {row["box_id"]: row for row in read_csv(repo_root / HEIGHTS)}
    boxes: list[dict[str, Any]] = []
    for record in read_csv(repo_root / INVENTORY):
        label_path = raw_root / record["label_path"]
        payload = label_path.read_bytes()
        if sha256_bytes(payload) != record["label_sha256"]:
            raise ValueError(f"raw label hash mismatch for stem {record['stem']}")
        for number, line in enumerate(payload.decode("utf-8").splitlines(), start=1):
            parts = line.split()
            if len(parts) != 5:
                continue
            raw_class, x, y, w, h = parts
            box_id = f"{record['stem']}:{number}"
            code, name_vi, _name_en, role = names[raw_class]
            key, eligible, eval_role, reason = raw_class, True, "CLASS", ""
            if record["stem"] == QUARANTINED_STEM:
                eligible, eval_role, reason = False, "QUARANTINED", "G0.4 quarantined stem"
            elif box_id in heights:
                value = heights[box_id]["height_value_m"]
                target = "16" if raw_class == "18" else raw_class
                code, name_vi, _en = HEIGHT_NAMES[target]
                if value == "UNREADABLE":
                    key, eligible, eval_role = f"{target}:UNREADABLE", False, "EXCLUDED"
                    reason = heights[box_id]["note"]
                    name_vi = f"{name_vi} (không rõ giá trị)"
                else:
                    key, name_vi = f"{target}:{value}", f"{name_vi} {value.replace('.', ',')} m"
                    code = f"{code}*{value}"
            elif raw_class in HEIGHT_NAMES:
                raise ValueError(f"height box without a reviewed value: {box_id}")
            elif role == "UNKNOWN_EVAL_ONLY":
                key, eligible, eval_role, reason = "UNKNOWN", False, "UNKNOWN_EVAL_ONLY", "class 31 routed to UNKNOWN"
            boxes.append(
                {
                    "stem": record["stem"], "line": number, "raw_class": raw_class, "x": x, "y": y, "w": w, "h": h,
                    "derived_key": key, "derived_code": code, "derived_name_vi": name_vi,
                    "train_eligible": eligible, "eval_role": eval_role, "reason": reason,
                }
            )
    if len(heights) != sum(box_id in heights for box_id in (f"{b['stem']}:{b['line']}" for b in boxes)):
        raise ValueError("every reviewed height decision must match a raw box")
    train = Counter(b["derived_key"] for b in boxes if b["train_eligible"])
    excluded = Counter(b["derived_key"] for b in boxes if not b["train_eligible"])
    taxonomy = []
    for key in sorted(set(train) | set(excluded), key=lambda k: (int(k.split(":")[0]) if k[0].isdigit() else 99, k)):
        sample = next(b for b in boxes if b["derived_key"] == key)
        source = key.split(":")[0]
        en = names[source][2] if source in names else ""
        if ":" in key and source in HEIGHT_NAMES:
            en = f"{HEIGHT_NAMES[source][2]} {key.split(':')[1]} m" if not key.endswith("UNREADABLE") else f"{HEIGHT_NAMES[source][2]} (unreadable value)"
        taxonomy.append(
            {
                "derived_key": key, "source_raw_class": source, "derived_code": sample["derived_code"],
                "derived_name_vi": sample["derived_name_vi"], "derived_name_en": en,
                "train_boxes": train.get(key, 0), "excluded_boxes": excluded.get(key, 0),
                "role": "CLASS" if train.get(key) else sample["eval_role"],
            }
        )
    return boxes, taxonomy


def render(repo_root: Path, raw_root: Path) -> dict[Path, bytes]:
    boxes, taxonomy = derive(repo_root, raw_root)
    classes = [row for row in taxonomy if row["role"] == "CLASS"]
    lines = "\n".join(
        f"| `{r['derived_key']}` | {r['derived_code']} | {r['derived_name_vi']} | {r['train_boxes']} | {r['excluded_boxes']} |"
        for r in taxonomy
    )
    report = f"""# M0-WP33 — D-03 derived label set

Status: `{PACKAGE_STATUS}`

Applies the owner's D-03 decisions to all {len(boxes)} raw boxes. Raw labels are read only and
hash-checked; nothing in the staging copy or the iCloud original is modified.

## Changes against the raw labels

- Class 23 → one class `P.111a+P.111b` "Cấm xe gắn máy và xe ba bánh có động cơ (biển ghép)".
  The owner first chose to split it into P.111a–d; review of all 465 boxes showed the same combined
  design (moped and motorised three-wheeler in one circle), so the owner revised the decision.
- Class 16 (P.117) and class 43 (W.239b) → one class per height value
  (`docs/review/wp33_height_value_decisions.csv`). Unreadable values are excluded from training.
- Stem 0776 line 7 → removed from class 18 (it is a height-limit sign); value unreadable, excluded.
- Class 31 → UNKNOWN, evaluation only.
- Stem 0248 → all boxes quarantined (G0.4).

## Derived taxonomy ({len(classes)} trainable keys before D-04)

| Key | Code | Name | Train boxes | Excluded |
| --- | --- | --- | --- | --- |
{lines}

## Governance

This package does not assign training class indices, generate a split, or authorize training.
D-04 (rare classes) and D-05 remain pending; Gate 0 remains BLOCKED.
"""
    artifacts = {
        BOXES_PATH: to_csv(boxes, BOX_FIELDS),
        TAXONOMY_PATH: to_csv(taxonomy, TAXONOMY_FIELDS),
        REPORT_PATH: report.encode("utf-8"),
    }
    manifest = {
        "schema_version": 1,
        "package": "M0-WP33",
        "status": PACKAGE_STATUS,
        "box_count": len(boxes),
        "train_eligible_boxes": sum(b["train_eligible"] for b in boxes),
        "trainable_keys": len(classes),
        "pinned_sources": PINNED_SOURCES,
        "builder_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "artifacts": [{"path": p.as_posix(), "sha256": sha256_bytes(b)} for p, b in artifacts.items()],
        "raw_labels_mutated": False,
        "gate0": "BLOCKED",
        "split_authorized": False,
        "training_authorized": False,
    }
    artifacts[MANIFEST_PATH] = (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    return artifacts


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    artifacts = render(repo_root, raw_root)
    for path, payload in artifacts.items():
        (repo_root / path).parent.mkdir(parents=True, exist_ok=True)
        (repo_root / path).write_bytes(payload)
    manifest = json.loads(artifacts[MANIFEST_PATH])
    return {k: manifest[k] for k in ("status", "box_count", "train_eligible_boxes", "trainable_keys")}


def verify(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    try:
        expected = render(repo_root, raw_root)
    except (OSError, KeyError, ValueError, StopIteration) as exc:
        return {"valid": False, "errors": [str(exc)], "status": PACKAGE_STATUS}
    errors = [
        f"artifact differs from deterministic re-derivation: {p.as_posix()}"
        for p, payload in expected.items()
        if not (repo_root / p).is_file() or (repo_root / p).read_bytes() != payload
    ]
    return {"valid": not errors, "errors": errors, "artifact_count": len(expected), "status": PACKAGE_STATUS}


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        command.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    args = root.parse_args(argv)
    repo_root, raw_root = args.repo_root.resolve(), args.raw_root.resolve()
    result = build(repo_root, raw_root) if args.command == "build" else verify(repo_root, raw_root)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if args.command == "build" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
