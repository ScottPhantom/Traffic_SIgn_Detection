#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and verify M0-WP34-R1: corrected D-04 decision support and negative audit.

WP34 failed independent QA (`docs/review/wp34_independent_qa_record.md`: 1 P1, 1 P2, 4 P3). The
initial WP34 package stays byte-identical as an immutable QA-fail record. R1:

- P1-1 / P3-1 / P3-2 / P3-4: re-reviews the 25 empty-label frames on an atlas that shows each
  negative at 1,600 px width next to its labelled neighbours, and records corrected decisions and
  classes; `UNCLEAR` is no longer allowed.
- P2-1: groups the parameterised height classes into families (P.117, W.239b) and marks the whole
  family's value reading as unverified, so no value class is trained alone.
- P3-3: states that the dominance column counts boxes and flags classes whose largest group holds
  more than 80 % of the boxes.
- Applies the owner's D-04 part 1 decision (12 rare classes trained with WP35 enrichment).

Commands: `prepare` writes the zoomed atlas without decisions; `build` requires the pinned notes;
`verify` re-derives every artifact byte-for-byte.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("wp34_r1_initial", Path(__file__).with_name("build_wp34_d04_support_and_negatives.py"))
assert _SPEC is not None and _SPEC.loader is not None
wp34 = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = wp34
_SPEC.loader.exec_module(wp34)

DEFAULT_RAW_ROOT = wp34.DEFAULT_RAW_ROOT
PACKAGE_STATUS = "WP34_R1_AWAITING_QA_REVIEW"
BOUNDARY = wp34.BOUNDARY
DOMINANCE_LIMIT = 0.8
FAMILIES = {"16": "P.117 hạn chế chiều cao", "43": "W.239b chiều cao tĩnh không thực tế"}
DECISIONS = {"TRUE_NEGATIVE", "UNLABELLED_SIGN_PRESENT"}

PINNED_SOURCES = {
    "scripts/build_wp34_d04_support_and_negatives.py": "3d631195adb20bad6a54b901820e1639e7263ede9ff50eb13a5a2d4eb8839da7",
    "tests/test_wp34_d04_support_and_negatives.py": "9704f88fac42d765bde327d297b66097b7134ff9718e187e70ee633ca4f4d3d0",
    "docs/review/wp34_negative_review_notes.csv": "5a6dbdb96ad6639c16f5b50934a2e884684201dba323124fc2f3af07cffa8a5f",
    "docs/review/generated/wp34_d04_class_support.csv": "52ad55e363615c958086ec462e1578dc3f3d38e94199cd5a9b2927d000d6ce42",
    "docs/review/generated/wp34_negative_audit.csv": "261d8f2de516dd0a1f910c9732807fd1b8eee4a9c797ffcb7a41c27c743f239a",
    "docs/review/generated/wp34_manifest.json": "0bc6d1707273f84b6b79e949e844cc0011a5d7587d1a78fc0062831077acc28c",
    "docs/review/wp34_d04_support_and_negative_audit_report.md": "d7d65d9d78a9c060e7b7cb313b2fce56e979a83d94abc7781ca4fa32cc68ff17",
    "docs/review/wp34_independent_qa_record.md": "2e9a72b105ef736a0c42a2843ef3acb8172861db1d8f34e7964d5a0ca700b3ff",
    "docs/review/generated/d04_owner_decisions_part1.csv": "62de39245a22292a9404702427d8b6bf3a9f746e081163d12198263815bc5409",
    "docs/review/d04_owner_decision_part1_record.md": "0b8ff5b9b73e1aaf8d4efc78ab2eeab83d7d5a87d891988f687656771c854230",
}
NOTES_PATH = Path("docs/review/wp34_r1_negative_review_notes.csv")
EXPECTED_NOTES_SHA256 = "487b78e43f4d7374ddbb24799a2928cadd49ca59927a6ab4103b3fd4e537dc4d"
GENERATED = Path("docs/review/generated")
MATRIX_PATH = GENERATED / "wp34_r1_d04_class_support.csv"
NEGATIVES_PATH = GENERATED / "wp34_r1_negative_audit.csv"
MANIFEST_PATH = GENERATED / "wp34_r1_manifest.json"
REPORT_PATH = Path("docs/review/wp34_r1_d04_support_and_negative_audit_report.md")
ASSETS = Path("docs/review/assets/wp34_r1/negatives")
MATRIX_FIELDS = [
    "derived_key", "derived_code", "derived_name_vi", "family", "train_boxes", "images", "groups",
    "largest_group_box_share", "dominated", "proposed_option", "proposal_reason", "owner_status",
]
NOTE_FIELDS = ["stem", "decision", "visible_classes_if_any", "confidence", "rationale"]
NEGATIVE_FIELDS = ["stem", "group_id", "previous_labelled_stem", "next_labelled_stem", *NOTE_FIELDS[1:], "proposed_use"]


def verify_pins(repo_root: Path) -> None:
    for relative, digest in PINNED_SOURCES.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or wp34.sha256_bytes(path.read_bytes()) != digest:
            raise ValueError(f"pinned WP34-R1 source changed: {relative}")


def class_matrix(repo_root: Path) -> list[dict[str, Any]]:
    initial = wp34.class_matrix(repo_root)
    owner = {row["derived_key"]: row["owner_decision"] for row in wp34.read_csv(repo_root / "docs/review/generated/d04_owner_decisions_part1.csv")}
    rows = []
    for row in initial:
        key = row["derived_key"]
        family = FAMILIES.get(key.split(":")[0], "") if ":" in key else ""
        dominated = row["groups"] >= 2 and float(row["largest_group_share"]) > DOMINANCE_LIMIT
        option, reason = row["proposed_option"], row["proposal_reason"]
        if family:
            reason += "; value read inside the family is unverified until every value is evaluated on real data"
        if dominated:
            reason += f"; one group holds {float(row['largest_group_share']):.0%} of the boxes, so the other groups give little independent support"
        status = "PENDING"
        if owner.get(key) == "TRAIN_WITH_ENRICHMENT":
            option, status = "OWNER_TRAIN_WITH_ENRICHMENT", "OWNER_APPROVED_D04_PART1"
            reason = "owner decision D-04 part 1: train with WP35 real-frame augmentation; evaluation pending real independent data"
        rows.append(
            {
                "derived_key": key, "derived_code": row["derived_code"], "derived_name_vi": row["derived_name_vi"],
                "family": family, "train_boxes": row["train_boxes"], "images": row["images"], "groups": row["groups"],
                "largest_group_box_share": row["largest_group_share"], "dominated": dominated,
                "proposed_option": option, "proposal_reason": reason, "owner_status": status,
            }
        )
    return rows


def zoomed_atlas(repo_root: Path, raw_root: Path, rows: list[dict[str, str]], notes: dict[str, dict[str, str]] | None) -> dict[Path, bytes]:
    """One page per negative: both labelled neighbours small, the negative itself at large size."""
    inventory = {r["stem"]: r for r in wp34.read_csv(repo_root / wp34.INVENTORY)}
    pages: dict[Path, bytes] = {}
    small, large = 520, 1600
    for number, row in enumerate(rows, start=1):
        with Image.open(raw_root / inventory[row["stem"]]["image_path"]) as image:
            negative = image.convert("RGB")
        big = negative.resize((large, round(negative.height * large / negative.width)), Image.Resampling.LANCZOS)
        neighbour_height = round(small * negative.height / negative.width)
        page = Image.new("RGB", (large + 20, 70 + neighbour_height + 30 + big.height + 10), (255, 255, 255))
        draw = ImageDraw.Draw(page)
        verdict = ""
        if notes is not None:
            note = notes[row["stem"]]
            verdict = f" | {note['decision']} {note['visible_classes_if_any']} ({note['confidence']})"
        draw.text((10, 8), f"M0-WP34-R1 negative audit | {number:02d}/{len(rows)} | NEGATIVE {row['stem']} | {row['group_id']}{verdict}", fill=(0, 0, 0), font=wp34.font(20))
        for column, stem, label in ((0, row["previous_labelled_stem"], "previous labelled"), (1, row["next_labelled_stem"], "next labelled")):
            x = 10 + column * (small + 20)
            draw.text((x, 40), f"{label} {stem}", fill=(30, 70, 170), font=wp34.font(14))
            if stem:
                page.paste(wp34.frame(raw_root, inventory, stem, small), (x, 60))
        top = 70 + neighbour_height + 10
        draw.text((10, top), f"NEGATIVE {row['stem']} at {large} px wide (no labels)", fill=(150, 30, 30), font=wp34.font(16))
        page.paste(big, (10, top + 24))
        buffer = io.BytesIO()
        page.save(buffer, format="JPEG", quality=90)
        pages[ASSETS / f"neg_{row['stem']}.jpg"] = buffer.getvalue()
    return pages


def load_notes(repo_root: Path, rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    if wp34.sha256_bytes((repo_root / NOTES_PATH).read_bytes()) != EXPECTED_NOTES_SHA256:
        raise ValueError("trusted WP34-R1 negative-review notes anchor mismatch")
    notes = wp34.read_csv(repo_root / NOTES_PATH)
    if [n["stem"] for n in notes] != [r["stem"] for r in rows]:
        raise ValueError("WP34-R1 notes must cover the 25 negatives in order")
    for note in notes:
        if list(note) != NOTE_FIELDS or note["decision"] not in DECISIONS or not note["rationale"].strip():
            raise ValueError(f"invalid WP34-R1 note for {note['stem']}")
        if (note["decision"] == "UNLABELLED_SIGN_PRESENT") != bool(note["visible_classes_if_any"]):
            raise ValueError(f"WP34-R1 note {note['stem']} must name visible classes exactly when a sign is present")
    return {note["stem"]: note for note in notes}


def render_report(matrix: list[dict[str, Any]], audit: list[dict[str, Any]]) -> str:
    options = Counter(row["proposed_option"] for row in matrix)
    sections = defaultdict(list)
    for row in matrix:
        flag = " ⚠dominated" if row["dominated"] else ""
        sections[row["proposed_option"]].append(f"{row['derived_key']} {row['derived_code']} ({row['images']} img/{row['groups']} grp{flag})")
    lines = "\n".join(f"- **{option}** ({len(items)}): {', '.join(items)}" for option, items in sections.items())
    background = [row["stem"] for row in audit if row["proposed_use"] == "DETECTOR_BACKGROUND"]
    unlabelled = [row for row in audit if row["decision"] == "UNLABELLED_SIGN_PRESENT"]
    table = "\n".join(f"| {row['stem']} | {row['visible_classes_if_any']} | {row['rationale']} |" for row in unlabelled)
    dominated = [f"{row['derived_key']} {row['derived_code']} ({float(row['largest_group_box_share']):.0%})" for row in matrix if row["dominated"]]
    return f"""# M0-WP34-R1 — corrected D-04 decision support and negative audit

Status: `{PACKAGE_STATUS}`
Boundary: `{BOUNDARY}`

Corrects the QA-failed WP34 (`docs/review/wp34_independent_qa_record.md`: 1 P1, 1 P2, 4 P3). The
initial WP34 package stays byte-identical. Nothing here is an owner decision for the 42 pending
classes, a split or a training authorization.

## Part A — D-04 support (54 WP33 classes × 54 D-02 groups)

| Option | Classes |
| --- | --- |
{chr(10).join(f"| `{option}` | {count} |" for option, count in options.items())}

{lines}

- `largest_group_box_share` is the share of the class's **boxes** in its largest group (QA P3-3).
  Classes above {DOMINANCE_LIMIT:.0%} are flagged `dominated`: their extra groups add little
  independent evidence: {', '.join(dominated) or 'none'}.
- **Height families (QA P2-1).** P.117 (2,0 / 2,2 / 2,5 m) and W.239b (2,5 / 2,7 m) are each
  one physical sign shape with a printed value. All their value classes are now trained
  (2,0 m as train-only, the others under D-04 part 1), so no single value class can absorb the
  others. The value reading stays **unverified** for the whole family until each value is
  evaluated on real independent images; behaviour must not use the value before that.
- The 12 classes approved in D-04 part 1 show `OWNER_TRAIN_WITH_ENRICHMENT`.

## Part B — negative audit (zoomed re-review)

Each negative was re-reviewed on its own page: both labelled neighbours, then the negative at
1,600 px width so that small distant signs are visible (`{ASSETS.as_posix()}/`). `UNCLEAR` is no longer allowed.

- True negatives usable as detector background: {len(background)} ({', '.join(background)}).
- Frames with an unlabelled visible sign: {len(unlabelled)}. They must never be used as
  background; proposed handling is quarantine from detector training until relabelled in a
  derived label set (owner decision).

| Stem | Visible classes | Rationale |
| --- | --- | --- |
{table}

## Artifacts

- Class support `{MATRIX_PATH.as_posix()}`, negative audit `{NEGATIVES_PATH.as_posix()}`, notes
  `{NOTES_PATH.as_posix()}` (pinned), manifest `{MANIFEST_PATH.as_posix()}`.
"""


def render(repo_root: Path, raw_root: Path, with_notes: bool) -> dict[Path, bytes]:
    verify_pins(repo_root)
    wp34.verify_pins(repo_root)
    matrix = class_matrix(repo_root)
    rows = wp34.negatives(repo_root)
    artifacts: dict[Path, bytes] = {MATRIX_PATH: wp34.to_csv(matrix, MATRIX_FIELDS)}
    if not with_notes:
        artifacts.update(zoomed_atlas(repo_root, raw_root, rows, None))
        return artifacts
    notes = load_notes(repo_root, rows)
    audit = []
    for row in rows:
        note = notes[row["stem"]]
        use = "DETECTOR_BACKGROUND" if note["decision"] == "TRUE_NEGATIVE" else "QUARANTINE_UNTIL_RELABELLED"
        audit.append({**row, **{k: note[k] for k in NOTE_FIELDS[1:]}, "proposed_use": use})
    artifacts[NEGATIVES_PATH] = wp34.to_csv(audit, NEGATIVE_FIELDS)
    artifacts[REPORT_PATH] = render_report(matrix, audit).encode("utf-8")
    artifacts.update(zoomed_atlas(repo_root, raw_root, rows, notes))
    manifest = {
        "schema_version": 1, "package": "M0-WP34-R1", "status": PACKAGE_STATUS, "evidence_boundary": BOUNDARY,
        "pinned_sources": PINNED_SOURCES, "notes_sha256": EXPECTED_NOTES_SHA256,
        "builder_sha256": wp34.sha256_bytes(Path(__file__).read_bytes()),
        "proposed_options": dict(Counter(row["proposed_option"] for row in matrix)),
        "negative_decisions": dict(Counter(row["decision"] for row in audit)),
        "artifacts": [{"path": p.as_posix(), "sha256": wp34.sha256_bytes(b)} for p, b in artifacts.items()],
        "d04_status": "PART1_APPROVED_42_CLASSES_PENDING", "gate0": "BLOCKED",
        "split_authorized": False, "training_authorized": False,
    }
    artifacts[MANIFEST_PATH] = (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    return artifacts


def verify(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    try:
        expected = render(repo_root, raw_root, with_notes=True)
    except (OSError, KeyError, ValueError) as exc:
        return {"valid": False, "errors": [str(exc)], "status": PACKAGE_STATUS}
    errors = [f"artifact differs: {p.as_posix()}" for p, b in expected.items() if not (repo_root / p).is_file() or (repo_root / p).read_bytes() != b]
    if (repo_root / ASSETS).is_dir():
        errors += [f"unexpected atlas file: {f.name}" for f in (repo_root / ASSETS).iterdir() if ASSETS / f.name not in expected]
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
        result, ok = {"status": PACKAGE_STATUS, "artifacts": len(artifacts)}, True
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
