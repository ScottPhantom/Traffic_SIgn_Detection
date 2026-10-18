#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and verify M0-WP32: cross-block link candidates and their visual review.

WP31 independent QA (docs/review/wp31_independent_qa_record.md) showed that DATASET01 filename
blocks from different rides interleave, so linking only numerically adjacent stems splits one ride
and one physical sign across several capture groups. WP32 generates candidate links between
frames in DIFFERENT WP31 capture groups and records a PM visual decision for each candidate group
pair. It also re-reviews the C0079 interleaved cls23 sub-sequence edges that QA flagged.

Candidate signals (deterministic):
- near-duplicate thumbnail: 32x18 grayscale, per-image z-normalized, mean absolute difference
  below THUMB_THRESHOLD to a frame in another capture group;
- label geometry: a box of the same class with centre within GEO_CENTER and width/height ratio
  within GEO_RATIO, plus thumbnail difference below GEO_THUMB_THRESHOLD.
Each candidate capture-group pair is represented by its single most similar frame pair.

Commands: `prepare` writes candidates and an unannotated atlas; `build` requires the pinned
review notes and writes decisions, links, annotated atlas and manifest; `verify` re-derives every
artifact byte-for-byte. Nothing here approves D-02, writes a split or authorizes training.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"

PACKAGE_STATUS = "WP32_AWAITING_QA_REVIEW"
EVIDENCE_BOUNDARY = (
    "CROSS_BLOCK_LINK_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_"
    "NO_SPLIT_NO_TRAINING"
)
REVIEWER = "PM/Codex provisional visual reviewer"
REVIEWED_AT = "2026-10-17T20:00:00+07:00"
THUMB_THRESHOLD = 0.35
GEO_THUMB_THRESHOLD = 0.6
GEO_CENTER = 0.02
GEO_RATIO = 1.25
PAIRS_PER_PAGE = 4

INVENTORY = Path("results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
WP31_FRAMES = Path("docs/review/generated/wp31_group_id_frames.csv")
WP31_QA_RECORD = Path("docs/review/wp31_independent_qa_record.md")
# Trusted inputs: the QA-failed WP31 frame partition and the QA record that motivates WP32.
PINNED_SOURCES = {
    INVENTORY: "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022",
    WP31_FRAMES: "5ec635d891b95848a4b1fd246ca3ecd3d1c344b8408135d79997cb42c4fb319c",
    WP31_QA_RECORD: "5639265731217e77dc7b04cecb0133a1f43c78497e18f11ae412b7a160f9d4d9",
}

GENERATED = Path("docs/review/generated")
CANDIDATES_PATH = GENERATED / "wp32_cross_block_candidates.csv"
DECISIONS_PATH = GENERATED / "wp32_cross_block_decisions.csv"
LINKS_PATH = GENERATED / "wp32_cross_block_links.csv"
MANIFEST_PATH = GENERATED / "wp32_cross_block_manifest.json"
NOTES_PATH = Path("docs/review/wp32_cross_block_review_notes.csv")
# Trusted PM review notes, pinned after direct readback of all 18 pages / 71 pairs.
EXPECTED_NOTES_SHA256 = "2dd0d8a9931eede639b470511cb8badcb0c64904e809cee55b0b27ea3efc38a2"
REPORT_PATH = Path("docs/review/wp32_cross_block_review_report.md")
ASSETS = Path("docs/review/assets/wp32/cross_block")

# C0079 interleaved cls23-only sub-sequence (one frame roughly every 11 stems) and the WP14/WP27-R2
# edges that join it to the main ride, flagged by WP31 QA P1-2.
C0079_SUBSEQUENCE = ("2068", "2069", "2070", "2081", "2092", "2103", "2112", "2122", "2133", "2144", "2155")
C0079_EDGES = (
    ("edge_002045", "2070", "2071"),
    ("edge_002055", "2080", "2081"),
    ("edge_002056", "2081", "2082"),
    ("edge_002066", "2091", "2092"),
    ("edge_002067", "2092", "2093"),
    ("edge_002077", "2102", "2103"),
    ("edge_002078", "2103", "2104"),
    ("edge_002086", "2111", "2112"),
    ("edge_002087", "2112", "2113"),
)

CANDIDATE_FIELDS = [
    "row_id", "kind", "left_stem", "right_stem", "left_capture_group_id",
    "right_capture_group_id", "left_class_ids", "right_class_ids", "signal", "thumb_mae",
    "atlas_page", "atlas_slot",
]
NOTE_FIELDS = ["row_id", "capture_decision", "physical_sign_decision", "confidence", "rationale"]
DECISION_FIELDS = [*CANDIDATE_FIELDS, "capture_decision", "physical_sign_decision", "confidence", "rationale"]
LINK_FIELDS = ["row_id", "kind", "left_stem", "right_stem", "level", "relation"]
CAPTURE_VALUES = {"SAME_CAPTURE_CANDIDATE", "NOT_RELATED", "UNRESOLVED"}
PHYSICAL_VALUES = {"SAME_PHYSICAL_SIGN_CANDIDATE", "NOT_RELATED", "UNRESOLVED"}


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


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ):
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def verify_sources(repo_root: Path) -> None:
    for path, expected in PINNED_SOURCES.items():
        actual = sha256_bytes((repo_root / path).read_bytes())
        if actual != expected:
            raise ValueError(f"pinned WP32 source changed: {path.as_posix()}")


def thumbnail(path: str) -> np.ndarray:
    with Image.open(path) as image:
        small = image.convert("L").resize((32, 18), Image.Resampling.BILINEAR)
    values = np.asarray(small, dtype=np.float64).ravel()
    return (values - values.mean()) / (values.std() + 1e-9)


def load_boxes(path: Path) -> list[tuple[str, float, float, float, float]]:
    boxes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 5:
            boxes.append((parts[0], *(float(value) for value in parts[1:])))
    return boxes


def geometry_match(left: list[tuple], right: list[tuple]) -> bool:
    for cls, x, y, w, h in left:
        for cls2, x2, y2, w2, h2 in right:
            if (
                cls == cls2
                and abs(x - x2) < GEO_CENTER
                and abs(y - y2) < GEO_CENTER
                and 1 / GEO_RATIO < w / w2 < GEO_RATIO
                and 1 / GEO_RATIO < h / h2 < GEO_RATIO
            ):
                return True
    return False


def derive_candidates(repo_root: Path, raw_root: Path) -> list[dict[str, Any]]:
    verify_sources(repo_root)
    inventory = {row["stem"]: row for row in read_csv(repo_root / INVENTORY)}
    frames = [row for row in read_csv(repo_root / WP31_FRAMES) if row["capture_group_id"]]
    for row in frames:
        record = inventory[row["stem"]]
        if sha256_bytes((raw_root / record["image_path"]).read_bytes()) != record["image_sha256"]:
            raise ValueError(f"raw image hash mismatch for stem {row['stem']}")
    paths = [str(raw_root / inventory[row["stem"]]["image_path"]) for row in frames]
    # Threads: Pillow releases the GIL while decoding, and threads work when the module is imported by path.
    with ThreadPoolExecutor(max_workers=8) as pool:
        thumbs = np.stack(list(pool.map(thumbnail, paths)))
    groups = np.array([row["capture_group_id"] for row in frames])
    boxes = [load_boxes(raw_root / inventory[row["stem"]]["label_path"]) for row in frames]

    best: dict[tuple[str, str], tuple[float, int, int, str]] = {}

    def offer(i: int, j: int, mae: float, signal: str) -> None:
        a, b = (i, j) if groups[i] < groups[j] else (j, i)
        key = (str(groups[a]), str(groups[b]))
        current = best.get(key)
        if current is None:
            best[key] = (mae, a, b, signal)
            return
        signals = "+".join(sorted(set(current[3].split("+")) | {signal}))
        if mae < current[0] or (mae == current[0] and (a, b) < (current[1], current[2])):
            best[key] = (mae, a, b, signals)
        else:
            best[key] = (current[0], current[1], current[2], signals)

    for i in range(len(frames)):
        distances = np.abs(thumbs - thumbs[i]).mean(axis=1)
        for j in np.flatnonzero(groups != groups[i]):
            if j <= i:
                continue
            mae = float(distances[j])
            if mae < THUMB_THRESHOLD:
                offer(i, j, mae, "thumbnail")
            if mae < GEO_THUMB_THRESHOLD and geometry_match(boxes[i], boxes[j]):
                offer(i, j, mae, "label_geometry")

    rows: list[dict[str, Any]] = []
    for (left_group, right_group), (mae, a, b, signal) in sorted(best.items(), key=lambda item: item[0]):
        rows.append(
            {
                "kind": "CROSS_GROUP",
                "left_stem": frames[a]["stem"],
                "right_stem": frames[b]["stem"],
                "left_capture_group_id": left_group,
                "right_capture_group_id": right_group,
                "left_class_ids": frames[a]["class_ids"],
                "right_class_ids": frames[b]["class_ids"],
                "signal": signal,
                "thumb_mae": f"{mae:.4f}",
            }
        )
    by_stem = {row["stem"]: row for row in frames}
    index = {row["stem"]: position for position, row in enumerate(frames)}
    for edge_id, left, right in C0079_EDGES:
        rows.append(
            {
                "kind": f"C0079_EDGE_{edge_id}",
                "left_stem": left,
                "right_stem": right,
                "left_capture_group_id": by_stem[left]["capture_group_id"],
                "right_capture_group_id": by_stem[right]["capture_group_id"],
                "left_class_ids": by_stem[left]["class_ids"],
                "right_class_ids": by_stem[right]["class_ids"],
                "signal": "wp31_qa_p1_2_reReview",
                "thumb_mae": f"{float(np.abs(thumbs[index[left]] - thumbs[index[right]]).mean()):.4f}",
            }
        )
    for left, right in zip(C0079_SUBSEQUENCE[2:-1], C0079_SUBSEQUENCE[3:], strict=True):
        rows.append(
            {
                "kind": "C0079_SUBSEQUENCE",
                "left_stem": left,
                "right_stem": right,
                "left_capture_group_id": by_stem[left]["capture_group_id"],
                "right_capture_group_id": by_stem[right]["capture_group_id"],
                "left_class_ids": by_stem[left]["class_ids"],
                "right_class_ids": by_stem[right]["class_ids"],
                "signal": "wp31_qa_p1_2_subsequence",
                "thumb_mae": f"{float(np.abs(thumbs[index[left]] - thumbs[index[right]]).mean()):.4f}",
            }
        )
    for position, row in enumerate(rows, start=1):
        row["row_id"] = f"x{position:03d}"
        row["atlas_page"] = f"{ASSETS.as_posix()}/page_{math.ceil(position / PAIRS_PER_PAGE):03d}.jpg"
        row["atlas_slot"] = (position - 1) % PAIRS_PER_PAGE + 1
    return rows


def draw_frame(raw_root: Path, inventory: dict[str, dict[str, str]], stem: str, width: int) -> Image.Image:
    record = inventory[stem]
    with Image.open(raw_root / record["image_path"]) as image:
        frame = image.convert("RGB")
    scale = width / frame.width
    frame = frame.resize((width, round(frame.height * scale)), Image.Resampling.BILINEAR)
    draw = ImageDraw.Draw(frame)
    label_font = font(14)
    for cls, x, y, w, h in load_boxes(raw_root / record["label_path"]):
        left = (x - w / 2) * frame.width
        top = (y - h / 2) * frame.height
        right = (x + w / 2) * frame.width
        bottom = (y + h / 2) * frame.height
        draw.rectangle((left, top, right, bottom), outline=(230, 20, 60), width=2)
        draw.rectangle((left, top - 16, left + 46, top), fill=(230, 20, 60))
        draw.text((left + 2, top - 15), f"cls {cls}", fill=(255, 255, 255), font=label_font)
    return frame


def render_atlas(
    repo_root: Path,
    raw_root: Path,
    rows: list[dict[str, Any]],
    decisions: dict[str, dict[str, str]] | None,
) -> dict[Path, bytes]:
    inventory = {row["stem"]: row for row in read_csv(repo_root / INVENTORY)}
    pages: dict[Path, bytes] = {}
    title_font, text_font = font(22), font(15)
    image_width, slot_height, page_width = 620, 420, 1600
    for start in range(0, len(rows), PAIRS_PER_PAGE):
        chunk = rows[start : start + PAIRS_PER_PAGE]
        page_number = start // PAIRS_PER_PAGE + 1
        page = Image.new("RGB", (page_width, 70 + slot_height * len(chunk)), (255, 255, 255))
        draw = ImageDraw.Draw(page)
        total = math.ceil(len(rows) / PAIRS_PER_PAGE)
        draw.text((16, 12), f"M0-WP32 cross-block link review | page {page_number:03d}/{total:03d}", fill=(0, 0, 0), font=title_font)
        draw.text((16, 42), EVIDENCE_BOUNDARY, fill=(60, 60, 60), font=font(12))
        for slot, row in enumerate(chunk):
            top = 70 + slot * slot_height
            if slot % 2:
                draw.rectangle((0, top, page_width, top + slot_height), fill=(242, 244, 247))
            draw.text(
                (16, top + 6),
                f"{row['row_id']} {row['kind']} | {row['left_capture_group_id']} -> {row['right_capture_group_id']}",
                fill=(0, 0, 0),
                font=text_font,
            )
            for column, stem_key, class_key in ((0, "left_stem", "left_class_ids"), (1, "right_stem", "right_class_ids")):
                x = 16 + column * (image_width + 10)
                draw.text((x, top + 26), f"{row[stem_key]} | classes {row[class_key] or '-'}", fill=(30, 70, 170), font=text_font)
                page.paste(draw_frame(raw_root, inventory, row[stem_key], image_width), (x, top + 46))
            info_x = 16 + 2 * (image_width + 10)
            lines = [f"signal: {row['signal']}", f"thumbnail MAE: {row['thumb_mae']}"]
            if decisions is None:
                lines.append("decision: AWAITING_PM_VISUAL_REVIEW")
            else:
                note = decisions[row["row_id"]]
                lines += [
                    f"capture: {note['capture_decision']}",
                    f"physical sign: {note['physical_sign_decision']}",
                    f"confidence: {note['confidence']}",
                ]
                words, line = note["rationale"].split(), ""
                for word in words:
                    if len(line) + len(word) > 34:
                        lines.append(line)
                        line = word
                    else:
                        line = f"{line} {word}".strip()
                lines.append(line)
            for offset, text in enumerate(lines[:20]):
                draw.text((info_x, top + 26 + offset * 19), text, fill=(20, 110, 70) if decisions else (60, 60, 60), font=text_font)
        buffer = io.BytesIO()
        page.save(buffer, format="JPEG", quality=85, optimize=False)
        pages[ASSETS / f"page_{page_number:03d}.jpg"] = buffer.getvalue()
    return pages


def load_notes(repo_root: Path, rows: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    if sha256_bytes((repo_root / NOTES_PATH).read_bytes()) != EXPECTED_NOTES_SHA256:
        raise ValueError("trusted WP32 review-notes anchor mismatch")
    notes = read_csv(repo_root / NOTES_PATH)
    if [note["row_id"] for note in notes] != [row["row_id"] for row in rows]:
        raise ValueError("WP32 review notes must cover every candidate row in order")
    for note in notes:
        if list(note) != NOTE_FIELDS:
            raise ValueError("WP32 review-note columns differ from contract")
        if note["capture_decision"] not in CAPTURE_VALUES or note["physical_sign_decision"] not in PHYSICAL_VALUES:
            raise ValueError(f"invalid WP32 decision for {note['row_id']}")
        if note["confidence"] not in {"HIGH", "MEDIUM"} or not note["rationale"].strip():
            raise ValueError(f"incomplete WP32 decision for {note['row_id']}")
    return {note["row_id"]: note for note in notes}


def derive_links(rows: list[dict[str, Any]], notes: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    """Leak-conservative: SAME and UNRESOLVED both link; NOT_RELATED never links."""
    links = []
    for row in rows:
        note = notes[row["row_id"]]
        for level, decision, same in (
            ("capture", note["capture_decision"], "SAME_CAPTURE_CANDIDATE"),
            ("scene", note["physical_sign_decision"], "SAME_PHYSICAL_SIGN_CANDIDATE"),
        ):
            links.append(
                {
                    "row_id": row["row_id"],
                    "kind": row["kind"],
                    "left_stem": row["left_stem"],
                    "right_stem": row["right_stem"],
                    "level": level,
                    "relation": "LINK" if decision in {same, "UNRESOLVED"} else "NO_LINK",
                }
            )
    return links


def render_report(rows: list[dict[str, Any]], notes: dict[str, dict[str, str]], links: list[dict[str, Any]]) -> str:
    cross = [row for row in rows if row["kind"] == "CROSS_GROUP"]
    capture_links = sum(link["relation"] == "LINK" and link["level"] == "capture" and link["kind"] == "CROSS_GROUP" for link in links)
    scene_links = sum(link["relation"] == "LINK" and link["level"] == "scene" and link["kind"] == "CROSS_GROUP" for link in links)
    c0079 = [row for row in rows if row["kind"] != "CROSS_GROUP"]
    c0079_lines = "\n".join(
        f"| `{row['row_id']}` | {row['kind']} | {row['left_stem']}/{row['right_stem']} | "
        f"{notes[row['row_id']]['capture_decision']} | {notes[row['row_id']]['physical_sign_decision']} |"
        for row in c0079
    )
    return f"""# M0-WP32 — cross-block link review

Status: `{PACKAGE_STATUS}`
Boundary: `{EVIDENCE_BOUNDARY}`

WP31 independent QA failed because DATASET01 filename blocks from different rides interleave:
linking only numerically adjacent stems put one ride and one physical sign into several capture
groups. WP32 generates candidate links between frames in different WP31 capture groups, records a
PM visual decision for each, and re-reviews the C0079 interleaved cls23 sub-sequence.

## Candidate generation

- Near-duplicate thumbnail: 32×18 grayscale, per-image z-normalized, mean absolute difference
  < {THUMB_THRESHOLD} to a frame in another capture group (same-group adjacent median ≈ 0.21).
- Label geometry: same class, box centre within {GEO_CENTER}, width/height ratio within
  {GEO_RATIO}, and thumbnail difference < {GEO_THUMB_THRESHOLD}.
- Each candidate capture-group pair is represented by its most similar frame pair:
  {len(cross)} group pairs.
- Limitation: both signals favour near-identical viewpoints. The same sign seen from a clearly
  different distance or angle in another block can still be missed, so WP32 lowers the leak risk
  but does not prove its absence.

## Decisions

- Cross-group pairs reviewed: {len(cross)}. Capture links: {capture_links}. Physical-sign links:
  {scene_links}.
- Links are leak-conservative: `SAME` and `UNRESOLVED` both link; only `NOT_RELATED` keeps groups
  apart.

## C0079 sub-sequence re-review

| Row | Kind | Stems | Capture | Physical sign |
| --- | --- | --- | --- | --- |
{c0079_lines}

## Governance

Reviewer `{REVIEWER}` at `{REVIEWED_AT}`. Decisions are provisional. They change no earlier package
and no canonical WP5 row. D-02 remains PENDING, Gate 0 remains BLOCKED,
`split_authorized=false` and `training_authorized=false`.

## Artifacts

- Candidates: `{CANDIDATES_PATH.as_posix()}`; decisions: `{DECISIONS_PATH.as_posix()}`;
  links: `{LINKS_PATH.as_posix()}`.
- Review notes (trusted input): `{NOTES_PATH.as_posix()}`.
- Atlas: `{ASSETS.as_posix()}/` ({math.ceil(len(rows) / PAIRS_PER_PAGE)} pages).
- Manifest: `{MANIFEST_PATH.as_posix()}`.
"""


def render(repo_root: Path, raw_root: Path, with_decisions: bool) -> dict[Path, bytes]:
    rows = derive_candidates(repo_root, raw_root)
    artifacts: dict[Path, bytes] = {CANDIDATES_PATH: to_csv(rows, CANDIDATE_FIELDS)}
    if not with_decisions:
        artifacts.update(render_atlas(repo_root, raw_root, rows, None))
        return artifacts
    notes = load_notes(repo_root, rows)
    decisions = [{**row, **{key: notes[row["row_id"]][key] for key in NOTE_FIELDS[1:]}} for row in rows]
    links = derive_links(rows, notes)
    artifacts[DECISIONS_PATH] = to_csv(decisions, DECISION_FIELDS)
    artifacts[LINKS_PATH] = to_csv(links, LINK_FIELDS)
    artifacts[REPORT_PATH] = render_report(rows, notes, links).encode("utf-8")
    artifacts.update(render_atlas(repo_root, raw_root, rows, notes))
    manifest = {
        "schema_version": 1,
        "package": "M0-WP32",
        "status": PACKAGE_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "candidate_rows": len(rows),
        "sources": [
            {"path": path.as_posix(), "sha256": sha256_bytes((repo_root / path).read_bytes())}
            for path in [*PINNED_SOURCES, NOTES_PATH, Path("scripts/build_wp32_cross_block_link_review.py")]
        ],
        "artifacts": [{"path": path.as_posix(), "sha256": sha256_bytes(payload)} for path, payload in artifacts.items()],
        "d02_status": "PENDING",
        "gate0": "BLOCKED",
        "split_authorized": False,
        "training_authorized": False,
        "final_group_truth_created": False,
    }
    artifacts[MANIFEST_PATH] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return artifacts


def write(repo_root: Path, artifacts: dict[Path, bytes]) -> None:
    for path, payload in artifacts.items():
        target = repo_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


def verify(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    try:
        expected = render(repo_root, raw_root, with_decisions=True)
    except (OSError, KeyError, ValueError) as exc:
        return {"valid": False, "errors": [f"cannot re-derive WP32: {exc}"], "status": PACKAGE_STATUS}
    errors = []
    for path, payload in expected.items():
        target = repo_root / path
        if not target.is_file() or target.is_symlink() or target.read_bytes() != payload:
            errors.append(f"artifact differs from deterministic re-derivation: {path.as_posix()}")
    extra = sorted(
        p.name for p in (repo_root / ASSETS).iterdir() if ASSETS / p.name not in expected
    ) if (repo_root / ASSETS).is_dir() else []
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
    else:
        artifacts = render(repo_root, raw_root, with_decisions=args.command == "build")
        write(repo_root, artifacts)
        result = {"status": PACKAGE_STATUS if args.command == "build" else "WP32_PREPARED_AWAITING_PM_VISUAL_REVIEW", "artifacts": len(artifacts)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command != "verify" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
