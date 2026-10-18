#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and verify M0-WP34: D-04 decision support on WP33 labels plus the 25-negative audit.

Part A (D-04 support): for each of the 54 WP33 trainable classes, count train-eligible boxes,
images and independent D-02 groups (stem 0248 excluded) and propose an option:
- KEEP_FULL                     >= 3 groups: train, validation and test can each hold a group.
- KEEP_TRAIN_AND_TEST_NO_VAL    2 groups: one group trains, one tests; no per-class validation.
- KEEP_TRAIN_ONLY_UNVERIFIED    1 group, >= 30 images: trained, never evaluated; reported as unverified.
- DROP_FROM_V1_COLLECT_MORE     1 group, < 30 images: not trained in v1; boxes become UNKNOWN
                                evaluation samples, following the D-03 UNKNOWN policy.
Proposals are not owner decisions.

Part B (negative audit): the 25 empty-label frames are rendered between their neighbouring
labelled frames and a pinned PM review records whether each one really has no traffic sign.

Commands: `prepare` writes the matrix and an unannotated negative atlas; `build` requires the
pinned review notes; `verify` re-derives every artifact byte-for-byte.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"
PACKAGE_STATUS = "WP34_AWAITING_QA_REVIEW"
BOUNDARY = "D04_DECISION_SUPPORT_AND_NEGATIVE_AUDIT_PROVISIONAL_NOT_OWNER_DECISION_NO_SPLIT_NO_TRAINING"
FULL_MIN_GROUPS = 3
TRAIN_ONLY_MIN_IMAGES = 30
ROWS_PER_PAGE = 3

INVENTORY = Path("results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
WP33_BOXES = Path("docs/review/generated/wp33_derived_boxes.csv")
WP33_TAXONOMY = Path("docs/review/generated/wp33_derived_taxonomy.csv")
D02_REGISTRY = Path("docs/review/generated/d02_group_id_registry.csv")
PINNED_SOURCES = {
    INVENTORY.as_posix(): "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022",
    WP33_BOXES.as_posix(): "4b9307003ce8fd3c1d50763a5950d3d57cf6b2ee6df3aeef74621707067501c0",
    WP33_TAXONOMY.as_posix(): "199ddd322aa05d4875af809c1c7c1459198ebf91ada24f406cbf039c406fa5ad",
    "docs/review/wp33_independent_qa_record.md": "ddc2159f9c3e57e3ba2f61165181bc598d4b5f7b1311822a0065210047ee0f5b",
    D02_REGISTRY.as_posix(): "c3b11f4c143627fd777270b34e40486bf92fd6e82e4c306187165fef4f7155d3",
    "docs/review/generated/d02_owner_decision_overlay.json": "e4e6719e223a6081498e144ef69b6239726ef537f41f16286c152e09c5dd197a",
}
NOTES_PATH = Path("docs/review/wp34_negative_review_notes.csv")
EXPECTED_NOTES_SHA256 = "5a6dbdb96ad6639c16f5b50934a2e884684201dba323124fc2f3af07cffa8a5f"

GENERATED = Path("docs/review/generated")
MATRIX_PATH = GENERATED / "wp34_d04_class_support.csv"
NEGATIVES_PATH = GENERATED / "wp34_negative_audit.csv"
MANIFEST_PATH = GENERATED / "wp34_manifest.json"
REPORT_PATH = Path("docs/review/wp34_d04_support_and_negative_audit_report.md")
ASSETS = Path("docs/review/assets/wp34/negatives")

MATRIX_FIELDS = [
    "derived_key", "derived_code", "derived_name_vi", "train_boxes", "images", "groups",
    "largest_group_share", "proposed_option", "proposal_reason", "owner_status",
]
NOTE_FIELDS = ["stem", "decision", "visible_classes_if_any", "confidence", "rationale"]
NEGATIVE_FIELDS = ["stem", "group_id", "previous_labelled_stem", "next_labelled_stem", *NOTE_FIELDS[1:]]
DECISIONS = {"TRUE_NEGATIVE", "UNLABELLED_SIGN_PRESENT", "UNCLEAR"}


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
            raise ValueError(f"pinned WP34 source changed: {relative}")


def propose(groups: int, images: int) -> tuple[str, str]:
    if groups >= FULL_MIN_GROUPS:
        return "KEEP_FULL", f"{groups} independent groups allow one group each in train, validation and test"
    if groups == 2:
        return "KEEP_TRAIN_AND_TEST_NO_VAL", "2 groups: one can train and one can test, none is left for validation"
    if images >= TRAIN_ONLY_MIN_IMAGES:
        return "KEEP_TRAIN_ONLY_UNVERIFIED", f"1 group with {images} images: trainable but cannot be evaluated independently"
    return "DROP_FROM_V1_COLLECT_MORE", f"1 group with only {images} images: too little independent support; evaluate as UNKNOWN"


def class_matrix(repo_root: Path) -> list[dict[str, Any]]:
    group_of = {row["stem"]: row["group_id"] for row in read_csv(repo_root / D02_REGISTRY)}
    taxonomy = [row for row in read_csv(repo_root / WP33_TAXONOMY) if row["role"] == "CLASS"]
    images: dict[str, set[str]] = defaultdict(set)
    boxes: Counter[str] = Counter()
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    for box in read_csv(repo_root / WP33_BOXES):
        if box["train_eligible"] != "True" or box["stem"] not in group_of:
            continue
        key = box["derived_key"]
        images[key].add(box["stem"])
        boxes[key] += 1
        groups[key][group_of[box["stem"]]] += 1
    rows = []
    for entry in taxonomy:
        key = entry["derived_key"]
        option, reason = propose(len(groups[key]), len(images[key]))
        total = sum(groups[key].values())
        rows.append(
            {
                "derived_key": key,
                "derived_code": entry["derived_code"],
                "derived_name_vi": entry["derived_name_vi"],
                "train_boxes": boxes[key],
                "images": len(images[key]),
                "groups": len(groups[key]),
                "largest_group_share": f"{max(groups[key].values()) / total:.2f}" if total else "",
                "proposed_option": option,
                "proposal_reason": reason,
                "owner_status": "PENDING",
            }
        )
    if len(rows) != 54 or any(row["images"] == 0 for row in rows):
        raise ValueError("WP34 expects 54 WP33 trainable classes, each with at least one image")
    return rows


def negatives(repo_root: Path) -> list[dict[str, str]]:
    inventory = read_csv(repo_root / INVENTORY)
    group_of = {row["stem"]: row["group_id"] for row in read_csv(repo_root / D02_REGISTRY)}
    labelled = [row["stem"] for row in inventory if int(row["box_count"]) > 0]
    rows = []
    for row in inventory:
        if int(row["box_count"]) != 0:
            continue
        before = [stem for stem in labelled if stem < row["stem"]]
        after = [stem for stem in labelled if stem > row["stem"]]
        rows.append(
            {
                "stem": row["stem"],
                "group_id": group_of[row["stem"]],
                "previous_labelled_stem": before[-1] if before else "",
                "next_labelled_stem": after[0] if after else "",
            }
        )
    if len(rows) != 25:
        raise ValueError("WP34 expects exactly 25 empty-label frames")
    return rows


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (Path("/System/Library/Fonts/Supplemental/Arial.ttf"), Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")):
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def frame(raw_root: Path, inventory: dict[str, dict[str, str]], stem: str, width: int) -> Image.Image:
    record = inventory[stem]
    with Image.open(raw_root / record["image_path"]) as image:
        picture = image.convert("RGB")
    picture = picture.resize((width, round(picture.height * width / picture.width)), Image.Resampling.BILINEAR)
    draw = ImageDraw.Draw(picture)
    for line in (raw_root / record["label_path"]).read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        x, y, w, h = (float(value) for value in parts[1:])
        box = ((x - w / 2) * picture.width, (y - h / 2) * picture.height, (x + w / 2) * picture.width, (y + h / 2) * picture.height)
        draw.rectangle(box, outline=(230, 20, 60), width=2)
        draw.text((box[0], box[1] - 14), f"cls {parts[0]}", fill=(230, 20, 60), font=font(12))
    return picture


def render_atlas(repo_root: Path, raw_root: Path, rows: list[dict[str, str]], notes: dict[str, dict[str, str]] | None) -> dict[Path, bytes]:
    inventory = {row["stem"]: row for row in read_csv(repo_root / INVENTORY)}
    width, slot = 520, 360
    pages: dict[Path, bytes] = {}
    total = (len(rows) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE
    for start in range(0, len(rows), ROWS_PER_PAGE):
        chunk = rows[start : start + ROWS_PER_PAGE]
        number = start // ROWS_PER_PAGE + 1
        page = Image.new("RGB", (3 * width + 40, 60 + slot * len(chunk)), (255, 255, 255))
        draw = ImageDraw.Draw(page)
        draw.text((10, 10), f"M0-WP34 negative audit | page {number:03d}/{total:03d}", fill=(0, 0, 0), font=font(22))
        draw.text((10, 38), BOUNDARY, fill=(60, 60, 60), font=font(11))
        for index, row in enumerate(chunk):
            top = 60 + index * slot
            verdict = ""
            if notes is not None:
                note = notes[row["stem"]]
                verdict = f" | {note['decision']} {note['visible_classes_if_any']} ({note['confidence']})"
            draw.text((10, top + 4), f"NEGATIVE {row['stem']} | {row['group_id']}{verdict}", fill=(0, 0, 0), font=font(15))
            for column, stem, label in ((0, row["previous_labelled_stem"], "previous"), (1, row["stem"], "NEGATIVE"), (2, row["next_labelled_stem"], "next")):
                x = 10 + column * (width + 10)
                draw.text((x, top + 24), f"{label} {stem}", fill=(30, 70, 170), font=font(13))
                if stem:
                    page.paste(frame(raw_root, inventory, stem, width), (x, top + 42))
        buffer = io.BytesIO()
        page.save(buffer, format="JPEG", quality=85)
        pages[ASSETS / f"page_{number:03d}.jpg"] = buffer.getvalue()
    return pages


def load_notes(repo_root: Path, rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    if sha256_bytes((repo_root / NOTES_PATH).read_bytes()) != EXPECTED_NOTES_SHA256:
        raise ValueError("trusted WP34 negative-review notes anchor mismatch")
    notes = read_csv(repo_root / NOTES_PATH)
    if [note["stem"] for note in notes] != [row["stem"] for row in rows]:
        raise ValueError("WP34 notes must cover the 25 negatives in order")
    for note in notes:
        if list(note) != NOTE_FIELDS or note["decision"] not in DECISIONS or not note["rationale"].strip():
            raise ValueError(f"invalid WP34 note for {note['stem']}")
    return {note["stem"]: note for note in notes}


def render_report(matrix: list[dict[str, Any]], audit: list[dict[str, str]]) -> str:
    options = Counter(row["proposed_option"] for row in matrix)
    by_option: dict[str, list[str]] = defaultdict(list)
    for row in matrix:
        by_option[row["proposed_option"]].append(f"{row['derived_key']} {row['derived_code']} ({row['images']} img/{row['groups']} grp)")
    decisions = Counter(row["decision"] for row in audit)
    flagged = [row for row in audit if row["decision"] != "TRUE_NEGATIVE"]
    flagged_lines = "\n".join(
        f"| {row['stem']} | {row['decision']} | {row['visible_classes_if_any'] or '-'} | {row['rationale']} |" for row in flagged
    ) or "| - | - | - | - |"
    sections = "\n".join(f"- **{option}** ({len(items)}): {', '.join(items)}" for option, items in by_option.items())
    return f"""# M0-WP34 — D-04 decision support on WP33 labels and negative audit

Status: `{PACKAGE_STATUS}`
Boundary: `{BOUNDARY}`

Inputs are pinned: WP33 derived boxes and taxonomy (independent QA PASS), the D-02 group registry
(owner approved D02-P1) and the inventory. Stem 0248 stays quarantined. Nothing here is an owner
decision, a split or a training authorization.

## Part A — D-04 proposal per class

Counts use train-eligible WP33 boxes and independent D-02 groups. A class needs at least three
groups so that train, validation and test can each receive one.

| Proposed option | Classes |
| --- | --- |
{chr(10).join(f"| `{option}` | {count} |" for option, count in options.items())}

{sections}

Option meanings:

- `KEEP_FULL`: normal train/validation/test treatment.
- `KEEP_TRAIN_AND_TEST_NO_VAL`: one group to train, one to test; thresholds for this class cannot
  be tuned on validation.
- `KEEP_TRAIN_ONLY_UNVERIFIED`: the whole group goes to train; the class is never evaluated and
  every report must label it unverified.
- `DROP_FROM_V1_COLLECT_MORE`: not trained in v1; its boxes are evaluated as UNKNOWN under the
  D-03 UNKNOWN policy until more independent data is collected.

The owner may override any row, for example by keeping a small class train-only.

## Part B — negative audit (25 empty-label frames)

Each negative was reviewed between its previous and next labelled frames
(`{ASSETS.as_posix()}/`). Decisions: {dict(decisions)}.

| Stem | Decision | Visible classes | Rationale |
| --- | --- | --- | --- |
{flagged_lines}

Proposed handling (owner decision): use `TRUE_NEGATIVE` frames as detector background images;
quarantine `UNLABELLED_SIGN_PRESENT` frames from detector training until they are relabelled in a
derived label set, and never use them as background.

## Artifacts

- Class support: `{MATRIX_PATH.as_posix()}`.
- Negative audit: `{NEGATIVES_PATH.as_posix()}`; notes `{NOTES_PATH.as_posix()}` (pinned).
- Manifest: `{MANIFEST_PATH.as_posix()}`.
"""


def render(repo_root: Path, raw_root: Path, with_notes: bool) -> dict[Path, bytes]:
    verify_pins(repo_root)
    matrix = class_matrix(repo_root)
    negative_rows = negatives(repo_root)
    artifacts: dict[Path, bytes] = {MATRIX_PATH: to_csv(matrix, MATRIX_FIELDS)}
    if not with_notes:
        artifacts.update(render_atlas(repo_root, raw_root, negative_rows, None))
        return artifacts
    notes = load_notes(repo_root, negative_rows)
    audit = [{**row, **{key: notes[row["stem"]][key] for key in NOTE_FIELDS[1:]}} for row in negative_rows]
    artifacts[NEGATIVES_PATH] = to_csv(audit, NEGATIVE_FIELDS)
    artifacts[REPORT_PATH] = render_report(matrix, audit).encode("utf-8")
    artifacts.update(render_atlas(repo_root, raw_root, negative_rows, notes))
    manifest = {
        "schema_version": 1,
        "package": "M0-WP34",
        "status": PACKAGE_STATUS,
        "evidence_boundary": BOUNDARY,
        "pinned_sources": PINNED_SOURCES,
        "notes_sha256": EXPECTED_NOTES_SHA256,
        "builder_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "proposed_options": dict(Counter(row["proposed_option"] for row in matrix)),
        "negative_decisions": dict(Counter(row["decision"] for row in audit)),
        "artifacts": [{"path": path.as_posix(), "sha256": sha256_bytes(payload)} for path, payload in artifacts.items()],
        "d04_status": "PENDING_OWNER_DECISION",
        "gate0": "BLOCKED",
        "split_authorized": False,
        "training_authorized": False,
    }
    artifacts[MANIFEST_PATH] = (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    return artifacts


def verify(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    try:
        expected = render(repo_root, raw_root, with_notes=True)
    except (OSError, KeyError, ValueError) as exc:
        return {"valid": False, "errors": [str(exc)], "status": PACKAGE_STATUS}
    errors = [
        f"artifact differs from deterministic re-derivation: {path.as_posix()}"
        for path, payload in expected.items()
        if not (repo_root / path).is_file() or (repo_root / path).is_symlink() or (repo_root / path).read_bytes() != payload
    ]
    extra = sorted(p.name for p in (repo_root / ASSETS).iterdir() if ASSETS / p.name not in expected) if (repo_root / ASSETS).is_dir() else []
    errors += [f"unexpected atlas file: {name}" for name in extra]
    return {"valid": not errors, "errors": errors, "artifact_count": len(expected), "status": PACKAGE_STATUS}


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("prepare", "build", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        command.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    args = root.parse_args(argv)
    repo_root, raw_root = args.repo_root.resolve(), args.raw_root.resolve()
    if args.command == "verify":
        result = verify(repo_root, raw_root)
        ok = result["valid"]
    else:
        artifacts = render(repo_root, raw_root, with_notes=args.command == "build")
        for path, payload in artifacts.items():
            (repo_root / path).parent.mkdir(parents=True, exist_ok=True)
            (repo_root / path).write_bytes(payload)
        result = {"status": PACKAGE_STATUS if args.command == "build" else "WP34_PREPARED_AWAITING_NEGATIVE_REVIEW", "artifacts": len(artifacts)}
        ok = True
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
