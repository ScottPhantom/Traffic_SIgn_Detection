"""Build deterministic M0-WP3 reviewer assets without mutating decisions or source data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

PROXY_ONLY_STATUS = "PROXY_ONLY_NOT_GROUP_TRUTH"
UNAPPROVED_STATUS = "UNAPPROVED"
WP3_STATUS = "READY_FOR_RE_REVIEW_EVIDENCE_ONLY_NO_DECISION_APPROVAL"
EXPECTED_CLASS_IDS = frozenset(range(52))
GROUPING_BATCH_SIZE = 25
GROUPING_THUMBNAILS_PER_ROW = 8
TAXONOMY_CLASSES_PER_PAGE = 4
TAXONOMY_SAMPLE_COUNT = 3
THUMBNAIL_SIZE = (112, 63)
CANVAS_WIDTH = 1020
TEXT_LEFT = 18
TEXT_RIGHT = 1002
TEXT_MAX_WIDTH = TEXT_RIGHT - TEXT_LEFT


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def deterministic_sample(items: list[str], count: int, *, salt: str) -> list[str]:
    unique_items = sorted(set(items))
    ranked = sorted(
        unique_items,
        key=lambda item: (hashlib.sha256(f"{salt}:{item}".encode()).hexdigest(), item),
    )
    return ranked[:count]


def validate_exact_class_coverage(rows: list[dict[str, Any]]) -> None:
    class_ids = [int(row["class_id"]) for row in rows]
    counts = {class_id: class_ids.count(class_id) for class_id in set(class_ids)}
    duplicates = sorted(class_id for class_id, count in counts.items() if count > 1)
    missing = sorted(EXPECTED_CLASS_IDS - set(class_ids))
    extra = sorted(set(class_ids) - EXPECTED_CLASS_IDS)
    if duplicates or missing or extra or len(class_ids) != len(EXPECTED_CLASS_IDS):
        raise ValueError(
            "taxonomy reviewer input must contain class_id 0..51 exactly once; "
            f"duplicates={duplicates}, missing={missing}, extra={extra}"
        )


def validate_grouping_rows(rows: list[dict[str, str]]) -> None:
    sequence_ids: set[str] = set()
    for row in rows:
        if row.get("evidence_status") != PROXY_ONLY_STATUS:
            raise ValueError("every grouping sequence must remain PROXY_ONLY_NOT_GROUP_TRUTH")
        sequence_id = row.get("proxy_sequence_id", "")
        if not sequence_id or sequence_id in sequence_ids:
            raise ValueError("grouping sequence IDs must be non-empty and unique")
        sequence_ids.add(sequence_id)


def parse_class_ids(value: str) -> set[int]:
    return {int(part) for part in re.split(r"[;,\s]+", value.strip()) if part}


def parse_yolo_boxes(path: Path) -> list[tuple[int, float, float, float, float]]:
    boxes: list[tuple[int, float, float, float, float]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f"{path} line {line_number} is not a five-field YOLO label")
        boxes.append((int(fields[0]), *map(float, fields[1:])))
    return boxes


def reviewer_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def font_line_height(font: ImageFont.FreeTypeFont | ImageFont.ImageFont) -> int:
    box = font.getbbox("Ag")
    return box[3] - box[1] + 4


def wrap_text_to_width(
    text: str,
    *,
    draw: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    """Wrap without dropping or truncating any character from the source text."""
    if max_width <= 0:
        raise ValueError("max_width must be positive")
    if not text:
        return [""]
    lines: list[str] = []
    cursor = 0
    preferred_breaks = frozenset(" |;/,_-")
    while cursor < len(text):
        remaining = text[cursor:]
        if draw.textlength(remaining, font=font) <= max_width:
            lines.append(remaining)
            break
        low, high = 1, len(remaining)
        while low <= high:
            middle = (low + high) // 2
            if draw.textlength(remaining[:middle], font=font) <= max_width:
                low = middle + 1
            else:
                high = middle - 1
        fitting_length = high
        if fitting_length < 1:
            raise ValueError("max_width cannot fit one text glyph")
        preferred = [
            index + 1
            for index, character in enumerate(remaining[:fitting_length])
            if character in preferred_breaks
        ]
        take = preferred[-1] if preferred else fitting_length
        lines.append(remaining[:take])
        cursor += take
    if "".join(lines) != text:
        raise RuntimeError("wrapped text lost source characters")
    return lines


def measure_wrapped_text(
    text: str,
    *,
    draw: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> tuple[list[str], int]:
    lines = wrap_text_to_width(text, draw=draw, font=font, max_width=max_width)
    return lines, len(lines) * font_line_height(font)


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    x: int,
    y: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str | tuple[int, int, int],
    max_width: int,
    canvas_size: tuple[int, int],
) -> dict[str, Any]:
    lines = wrap_text_to_width(text, draw=draw, font=font, max_width=max_width)
    line_height = font_line_height(font)
    bounds: list[list[int]] = []
    for index, line in enumerate(lines):
        line_y = y + index * line_height
        draw.text((x, line_y), line, fill=fill, font=font)
        ink_box = draw.textbbox((x, line_y), line or " ", font=font)
        right = max(ink_box[2], x + math.ceil(draw.textlength(line, font=font)))
        bounds.append([min(x, ink_box[0]), min(line_y, ink_box[1]), right, ink_box[3]])
    fits = all(
        0 <= left <= right <= canvas_size[0] and 0 <= top <= bottom <= canvas_size[1]
        for left, top, right, bottom in bounds
    )
    complete = "".join(lines) == text
    if not fits or not complete:
        raise RuntimeError(f"rendered text did not fit or was incomplete: {text}")
    return {
        "full_text": text,
        "lines": lines,
        "bounds": bounds,
        "max_width": max_width,
        "complete": complete,
        "all_bounds_fit": fits,
    }


def grouping_summary(row: dict[str, Any]) -> str:
    return (
        f"{row['proxy_sequence_id']} | {PROXY_ONLY_STATUS} | members={row['member_count']} "
        f"| splits={row['splits']} | strong={row['strong_edge_count']} "
        f"| cross_split={row['cross_split_strong_edges']} | MAE="
        f"{row['thumbnail_mae_min']}..{row['thumbnail_mae_max']} | dHash<="
        f"{row['dhash_distance_max']} | cosine>={row['rgb_histogram_cosine_min']}"
    )


def verify_source_record(
    row: dict[str, str],
    *,
    raw_root: Path,
    cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    stem = row["stem"]
    if stem in cache:
        return cache[stem]
    image_path = raw_root / row["image_path"]
    label_path = raw_root / row["label_path"]
    image_sha = sha256_file(image_path)
    label_sha = sha256_file(label_path)
    if image_sha != row["image_sha256"] or label_sha != row["label_sha256"]:
        raise ValueError(f"source hash mismatch for stem {stem}")
    record = {
        "stem": stem,
        "image_path": row["image_path"],
        "image_sha256": image_sha,
        "label_path": row["label_path"],
        "label_sha256": label_sha,
        "split": row["split"],
        "class_ids": row["class_ids"],
    }
    cache[stem] = record
    return record


def annotated_thumbnail(
    inventory_row: dict[str, str],
    *,
    raw_root: Path,
    target_class: int | None,
) -> Image.Image:
    image_path = raw_root / inventory_row["image_path"]
    label_path = raw_root / inventory_row["label_path"]
    with Image.open(image_path) as image:
        scene = image.convert("RGB")
    draw = ImageDraw.Draw(scene)
    for class_id, x_center, y_center, width, height in parse_yolo_boxes(label_path):
        x_min = (x_center - width / 2) * scene.width
        x_max = (x_center + width / 2) * scene.width
        y_min = (y_center - height / 2) * scene.height
        y_max = (y_center + height / 2) * scene.height
        is_target = target_class is None or class_id == target_class
        color = (220, 20, 60) if is_target else (120, 120, 120)
        line_width = 5 if is_target else 2
        draw.rectangle((x_min, y_min, x_max, y_max), outline=color, width=line_width)
    scene.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", THUMBNAIL_SIZE, "white")
    canvas.paste(
        scene,
        ((THUMBNAIL_SIZE[0] - scene.width) // 2, (THUMBNAIL_SIZE[1] - scene.height) // 2),
    )
    return canvas


def grouping_metric_summary(edges: list[dict[str, str]]) -> dict[str, str]:
    if not edges:
        raise ValueError("proxy sequence is missing its strong candidate edges")
    maes = [float(edge["thumbnail_mae"]) for edge in edges]
    dhashes = [int(edge["dhash_distance"]) for edge in edges]
    cosines = [float(edge["rgb_histogram_cosine"]) for edge in edges]
    return {
        "thumbnail_mae_min": f"{min(maes):.6f}",
        "thumbnail_mae_max": f"{max(maes):.6f}",
        "dhash_distance_max": str(max(dhashes)),
        "rgb_histogram_cosine_min": f"{min(cosines):.8f}",
    }


def render_grouping_sheet(
    batch_rows: list[dict[str, Any]],
    *,
    inventory: dict[str, dict[str, str]],
    raw_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    font = reviewer_font(14)
    small_font = reviewer_font(12)
    title_font = reviewer_font(18)
    measure_draw = ImageDraw.Draw(Image.new("RGB", (1, 1), "white"))
    row_specs: list[dict[str, Any]] = []
    for row in batch_rows:
        summary = grouping_summary(row)
        summary_lines, summary_height = measure_wrapped_text(
            summary,
            draw=measure_draw,
            font=font,
            max_width=TEXT_MAX_WIDTH,
        )
        thumbnail_rows = math.ceil(
            len(row["member_stems"]) / GROUPING_THUMBNAILS_PER_ROW
        )
        row_specs.append(
            {
                "summary": summary,
                "summary_lines": summary_lines,
                "summary_height": summary_height,
                "thumbnail_rows": thumbnail_rows,
                "row_height": 10 + summary_height + 8 + thumbnail_rows * 88 + 10,
            }
        )
    canvas = Image.new(
        "RGB", (CANVAS_WIDTH, 62 + sum(spec["row_height"] for spec in row_specs)), "white"
    )
    draw = ImageDraw.Draw(canvas)
    title = (
        f"M0-WP3 grouping batch {batch_rows[0]['batch_number']:03d} | "
        f"{PROXY_ONLY_STATUS} | NO GROUP IDs"
    )
    title_layout = draw_wrapped_text(
        draw,
        title,
        x=TEXT_LEFT,
        y=14,
        font=title_font,
        fill="black",
        max_width=TEXT_MAX_WIDTH,
        canvas_size=canvas.size,
    )
    y = 62
    row_audits: list[dict[str, Any]] = []
    for row, spec in zip(batch_rows, row_specs, strict=True):
        row_height = spec["row_height"]
        draw.rectangle((8, y, 1012, y + row_height - 6), outline=(150, 150, 150), width=1)
        summary_layout = draw_wrapped_text(
            draw,
            spec["summary"],
            x=TEXT_LEFT,
            y=y + 10,
            font=font,
            fill="black",
            max_width=TEXT_MAX_WIDTH,
            canvas_size=canvas.size,
        )
        thumb_y_start = y + 10 + spec["summary_height"] + 8
        label_layouts: list[dict[str, Any]] = []
        for index, stem in enumerate(row["member_stems"]):
            column = index % GROUPING_THUMBNAILS_PER_ROW
            thumbnail_row = index // GROUPING_THUMBNAILS_PER_ROW
            x = TEXT_LEFT + column * 124
            thumb_y = thumb_y_start + thumbnail_row * 88
            thumbnail = annotated_thumbnail(
                inventory[stem], raw_root=raw_root, target_class=None
            )
            canvas.paste(thumbnail, (x, thumb_y))
            label_layout = draw_wrapped_text(
                draw,
                f"{stem} [{inventory[stem]['split']}]",
                x=x,
                y=thumb_y + THUMBNAIL_SIZE[1] + 2,
                fill="black",
                font=small_font,
                max_width=THUMBNAIL_SIZE[0],
                canvas_size=canvas.size,
            )
            label_layouts.append({"stem": stem, **label_layout})
        row_audits.append(
            {
                "proxy_sequence_id": row["proxy_sequence_id"],
                "summary": summary_layout,
                "thumbnail_labels": label_layouts,
                "row_bounds": [8, y, 1012, y + row_height - 6],
            }
        )
        y += row_height
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="JPEG", quality=82, optimize=True, progressive=False)
    return {
        "page": f"assets/wp3/grouping/{output_path.name}",
        "canvas_size": list(canvas.size),
        "title": title_layout,
        "rows": row_audits,
    }


def build_grouping_review(
    *,
    clusters_path: Path,
    edges_path: Path,
    inventory: dict[str, dict[str, str]],
    raw_root: Path,
    assets_dir: Path,
    generated_dir: Path,
    source_cache: dict[str, dict[str, Any]],
) -> tuple[list[Path], list[dict[str, Any]], list[dict[str, Any]]]:
    cluster_rows = read_csv(clusters_path)
    validate_grouping_rows(cluster_rows)
    edges_by_sequence: dict[str, list[dict[str, str]]] = defaultdict(list)
    for edge in read_csv(edges_path):
        sequence_id = edge["proxy_sequence_id"]
        if sequence_id:
            edges_by_sequence[sequence_id].append(edge)

    index_rows: list[dict[str, Any]] = []
    for index, cluster in enumerate(cluster_rows):
        members = cluster["members"].split(";")
        if int(cluster["member_count"]) != len(members):
            raise ValueError(f"member_count mismatch for {cluster['proxy_sequence_id']}")
        for stem in members:
            if stem not in inventory:
                raise ValueError(f"missing inventory row for grouping stem {stem}")
            verify_source_record(inventory[stem], raw_root=raw_root, cache=source_cache)
        metrics = grouping_metric_summary(edges_by_sequence[cluster["proxy_sequence_id"]])
        batch_number = index // GROUPING_BATCH_SIZE + 1
        index_rows.append(
            {
                "proxy_sequence_id": cluster["proxy_sequence_id"],
                "evidence_status": PROXY_ONLY_STATUS,
                "review_status": "PENDING",
                "batch_number": batch_number,
                "contact_sheet": f"assets/wp3/grouping/batch_{batch_number:03d}.jpg",
                "member_count": len(members),
                "member_stems": members,
                "source_stems": ";".join(members),
                "splits": ";".join(sorted({inventory[stem]["split"] for stem in members})),
                "strong_edge_count": int(cluster["strong_edge_count"]),
                "cross_split_strong_edges": int(cluster["cross_split_strong_edges"]),
                **metrics,
            }
        )

    sheet_paths: list[Path] = []
    page_audits: list[dict[str, Any]] = []
    for offset in range(0, len(index_rows), GROUPING_BATCH_SIZE):
        batch = index_rows[offset : offset + GROUPING_BATCH_SIZE]
        sheet_path = assets_dir / "grouping" / f"batch_{batch[0]['batch_number']:03d}.jpg"
        page_audits.append(
            render_grouping_sheet(
                batch,
                inventory=inventory,
                raw_root=raw_root,
                output_path=sheet_path,
            )
        )
        sheet_paths.append(sheet_path)

    csv_rows = [
        {key: value for key, value in row.items() if key != "member_stems"}
        for row in index_rows
    ]
    write_csv(generated_dir / "wp3_grouping_review_index.csv", csv_rows)
    html_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['proxy_sequence_id'])}</td>"
        f"<td>{PROXY_ONLY_STATUS}</td>"
        f"<td>{row['source_stems']}</td><td>{row['splits']}</td>"
        f"<td>{row['thumbnail_mae_min']}..{row['thumbnail_mae_max']}; "
        f"dHash≤{row['dhash_distance_max']}; cosine≥{row['rgb_histogram_cosine_min']}</td>"
        f"<td><a href=\"batch_{row['batch_number']:03d}.jpg\">batch "
        f"{row['batch_number']:03d}</a></td></tr>"
        for row in index_rows
    )
    (assets_dir / "grouping" / "index.html").write_text(
        "<!doctype html><meta charset=\"utf-8\"><title>M0-WP3 grouping review</title>"
        f"<h1>{PROXY_ONLY_STATUS}</h1><p>Reviewer queue only. No final group IDs.</p>"
        "<table border=\"1\"><tr><th>Sequence</th><th>Status</th><th>Source stems</th>"
        "<th>Splits</th><th>Proxy metrics</th><th>Contact sheet</th></tr>"
        f"{html_rows}</table>",
        encoding="utf-8",
    )
    return (
        sheet_paths + [assets_dir / "grouping" / "index.html"],
        index_rows,
        page_audits,
    )


def render_taxonomy_page(
    rows: list[dict[str, Any]],
    *,
    inventory: dict[str, dict[str, str]],
    raw_root: Path,
    page_number: int,
    output_path: Path,
) -> dict[str, Any]:
    title_font = reviewer_font(18)
    font = reviewer_font(14)
    small_font = reviewer_font(12)
    measure_draw = ImageDraw.Draw(Image.new("RGB", (1, 1), "white"))
    row_specs: list[dict[str, Any]] = []
    for row in rows:
        header = (
            f"class {row['class_id']} | {row['dataset_code']} | {row['dataset_name_vi_en']} "
            f"| support images/boxes={row['image_count']}/{row['box_count']} | "
            f"{UNAPPROVED_STATUS}"
        )
        flags = f"conflicts: {row['conflict_flags'] or 'none recorded'}"
        header_lines, header_height = measure_wrapped_text(
            header,
            draw=measure_draw,
            font=font,
            max_width=TEXT_MAX_WIDTH,
        )
        flag_lines, flag_height = measure_wrapped_text(
            flags,
            draw=measure_draw,
            font=small_font,
            max_width=TEXT_MAX_WIDTH,
        )
        sample_labels = [
            f"source stem {stem} [{inventory[stem]['split']}]"
            for stem in row["sample_stems"]
        ]
        sample_label_lines = [
            measure_wrapped_text(
                label,
                draw=measure_draw,
                font=small_font,
                max_width=280,
            )[0]
            for label in sample_labels
        ]
        sample_label_height = max(
            len(lines) * font_line_height(small_font) for lines in sample_label_lines
        )
        row_specs.append(
            {
                "header": header,
                "header_lines": header_lines,
                "header_height": header_height,
                "flags": flags,
                "flag_lines": flag_lines,
                "flag_height": flag_height,
                "sample_labels": sample_labels,
                "sample_label_lines": sample_label_lines,
                "block_height": (
                    10 + header_height + 4 + flag_height + 8 + 158 + 2
                    + sample_label_height + 10
                ),
            }
        )
    canvas = Image.new(
        "RGB", (CANVAS_WIDTH, 58 + sum(spec["block_height"] for spec in row_specs)), "white"
    )
    draw = ImageDraw.Draw(canvas)
    title = f"M0-WP3 taxonomy atlas page {page_number:03d} | ALL ROWS {UNAPPROVED_STATUS}"
    title_layout = draw_wrapped_text(
        draw,
        title,
        x=TEXT_LEFT,
        y=14,
        font=title_font,
        fill="black",
        max_width=TEXT_MAX_WIDTH,
        canvas_size=canvas.size,
    )
    y = 58
    row_audits: list[dict[str, Any]] = []
    for row, spec in zip(rows, row_specs, strict=True):
        block_height = spec["block_height"]
        draw.rectangle((8, y, 1012, y + block_height - 6), outline=(150, 150, 150))
        header_layout = draw_wrapped_text(
            draw,
            spec["header"],
            x=TEXT_LEFT,
            y=y + 10,
            font=font,
            fill="black",
            max_width=TEXT_MAX_WIDTH,
            canvas_size=canvas.size,
        )
        flags_y = y + 10 + spec["header_height"] + 4
        flags_layout = draw_wrapped_text(
            draw,
            spec["flags"],
            x=TEXT_LEFT,
            y=flags_y,
            font=small_font,
            fill=(90, 0, 0),
            max_width=TEXT_MAX_WIDTH,
            canvas_size=canvas.size,
        )
        image_y = flags_y + spec["flag_height"] + 8
        sample_layouts: list[dict[str, Any]] = []
        for sample_index, stem in enumerate(row["sample_stems"]):
            x = TEXT_LEFT + sample_index * 325
            thumbnail = annotated_thumbnail(
                inventory[stem], raw_root=raw_root, target_class=int(row["class_id"])
            )
            enlarged = thumbnail.resize((280, 158), Image.Resampling.NEAREST)
            canvas.paste(enlarged, (x, image_y))
            label_layout = draw_wrapped_text(
                draw,
                spec["sample_labels"][sample_index],
                x=x,
                y=image_y + 160,
                font=small_font,
                fill="black",
                max_width=280,
                canvas_size=canvas.size,
            )
            sample_layouts.append({"stem": stem, **label_layout})
        row_audits.append(
            {
                "class_id": row["class_id"],
                "header": header_layout,
                "conflict_flags": flags_layout,
                "sample_labels": sample_layouts,
                "row_bounds": [8, y, 1012, y + block_height - 6],
            }
        )
        y += block_height
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="JPEG", quality=84, optimize=True, progressive=False)
    return {
        "page": f"assets/wp3/taxonomy/{output_path.name}",
        "canvas_size": list(canvas.size),
        "title": title_layout,
        "rows": row_audits,
    }


def build_taxonomy_atlas(
    *,
    taxonomy_path: Path,
    inventory: dict[str, dict[str, str]],
    raw_root: Path,
    assets_dir: Path,
    generated_dir: Path,
    source_cache: dict[str, dict[str, Any]],
) -> tuple[list[Path], list[dict[str, Any]], list[dict[str, Any]]]:
    taxonomy_rows = read_csv(taxonomy_path)
    validate_exact_class_coverage(taxonomy_rows)
    if any(row.get("review_status") != UNAPPROVED_STATUS for row in taxonomy_rows):
        raise ValueError("taxonomy rows must remain UNAPPROVED")
    stems_by_class: dict[int, list[str]] = defaultdict(list)
    for stem, inventory_row in inventory.items():
        for class_id in parse_class_ids(inventory_row["class_ids"]):
            stems_by_class[class_id].append(stem)

    atlas_rows: list[dict[str, Any]] = []
    for taxonomy_row in sorted(taxonomy_rows, key=lambda row: int(row["class_id"])):
        class_id = int(taxonomy_row["class_id"])
        samples = deterministic_sample(
            stems_by_class[class_id], TAXONOMY_SAMPLE_COUNT, salt=f"taxonomy:{class_id}"
        )
        if not samples:
            raise ValueError(f"class {class_id} has no source sample")
        for stem in samples:
            verify_source_record(inventory[stem], raw_root=raw_root, cache=source_cache)
        page_number = class_id // TAXONOMY_CLASSES_PER_PAGE + 1
        atlas_rows.append(
            {
                "class_id": class_id,
                "dataset_code": taxonomy_row["dataset_code"],
                "dataset_name_vi_en": taxonomy_row["dataset_name_vi_en"],
                "semantic_family_proposal": taxonomy_row["semantic_family_proposal"],
                "gtsrb_mapping_proposal": taxonomy_row["gtsrb_mapping_proposal"],
                "gtsrb_relation_proposal": taxonomy_row["gtsrb_relation_proposal"],
                "image_count": int(taxonomy_row["image_count"]),
                "box_count": int(taxonomy_row["box_count"]),
                "conflict_flags": taxonomy_row["conflict_flags"],
                "review_status": UNAPPROVED_STATUS,
                "sample_stems": samples,
                "source_stems": ";".join(samples),
                "atlas_page": f"assets/wp3/taxonomy/page_{page_number:03d}.jpg",
            }
        )

    page_paths: list[Path] = []
    page_audits: list[dict[str, Any]] = []
    for offset in range(0, len(atlas_rows), TAXONOMY_CLASSES_PER_PAGE):
        page_rows = atlas_rows[offset : offset + TAXONOMY_CLASSES_PER_PAGE]
        page_number = offset // TAXONOMY_CLASSES_PER_PAGE + 1
        page_path = assets_dir / "taxonomy" / f"page_{page_number:03d}.jpg"
        page_audits.append(
            render_taxonomy_page(
                page_rows,
                inventory=inventory,
                raw_root=raw_root,
                page_number=page_number,
                output_path=page_path,
            )
        )
        page_paths.append(page_path)

    csv_rows = [
        {key: value for key, value in row.items() if key != "sample_stems"}
        for row in atlas_rows
    ]
    write_csv(generated_dir / "wp3_taxonomy_reviewer_atlas.csv", csv_rows)
    html_rows = "\n".join(
        "<tr>"
        f"<td>{row['class_id']}</td><td>{html.escape(row['dataset_code'])}</td>"
        f"<td>{html.escape(row['dataset_name_vi_en'])}</td><td>{row['image_count']}/"
        f"{row['box_count']}</td><td>{html.escape(row['conflict_flags'])}</td>"
        f"<td>{UNAPPROVED_STATUS}</td><td>{row['source_stems']}</td>"
        f"<td><a href=\"page_{int(row['class_id']) // TAXONOMY_CLASSES_PER_PAGE + 1:03d}.jpg\">"
        "atlas page</a></td></tr>"
        for row in atlas_rows
    )
    (assets_dir / "taxonomy" / "index.html").write_text(
        "<!doctype html><meta charset=\"utf-8\"><title>M0-WP3 taxonomy atlas</title>"
        f"<h1>Taxonomy reviewer atlas — {UNAPPROVED_STATUS}</h1>"
        "<p>Representative evidence only. No taxonomy approval or relabeling.</p>"
        "<table border=\"1\"><tr><th>ID</th><th>Code</th><th>Name</th><th>Images/boxes</th>"
        "<th>Conflict flags</th><th>Status</th><th>Source stems</th><th>Atlas</th></tr>"
        f"{html_rows}</table>",
        encoding="utf-8",
    )
    return (
        page_paths + [assets_dir / "taxonomy" / "index.html"],
        atlas_rows,
        page_audits,
    )


def relative_path_strict(path: Path, root: Path) -> str:
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"manifest input escapes its declared root: {path}") from error
    if not relative.parts or ".." in relative.parts:
        raise ValueError(f"manifest input has an invalid relative path: {path}")
    return relative.as_posix()


def manifest_record(path: Path, *, root: Path, root_id: str) -> dict[str, Any]:
    return {
        "root_id": root_id,
        "path": relative_path_strict(path, root),
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def build_wp3_manifest(
    *,
    review_dir: Path,
    repo_root: Path,
    source_inputs: list[tuple[str, Path]],
    control_inputs: list[tuple[str, Path]],
    source_cache: dict[str, dict[str, Any]],
    decision_sha256: str,
    source_tree_manifest_sha256: str,
) -> dict[str, Any]:
    manifest_path = review_dir / "generated" / "wp3_evidence_manifest.json"
    artifact_paths = [
        review_dir / "dataset_owner_outreach_draft.md",
        review_dir / "wp3_provenance_and_fallback_report.md",
        *sorted((review_dir / "generated").glob("wp3_*")),
        *sorted((review_dir / "assets" / "wp3").rglob("*")),
    ]
    artifacts = [
        manifest_record(path, root=review_dir, root_id="review")
        for path in artifact_paths
        if path.is_file() and path != manifest_path
    ]
    source_records = [
        {
            "input_id": input_id,
            **manifest_record(path, root=repo_root, root_id="repo"),
        }
        for input_id, path in source_inputs
    ]
    control_records = [
        {
            "control_id": control_id,
            **manifest_record(path, root=repo_root, root_id="repo"),
        }
        for control_id, path in control_inputs
    ]
    payload = {
        "schema_version": 2,
        "status": WP3_STATUS,
        "evidence_boundary": (
            "WP3 provides reviewer evidence only. It does not approve provenance, license, "
            "taxonomy, group IDs, splits, training or model changes."
        ),
        "logical_roots": {
            "repo": ".",
            "review": "docs/review",
        },
        "gate0": "BLOCKED",
        "training_authorized": False,
        "decision_status_sha256": decision_sha256,
        "source_tree_manifest_sha256": source_tree_manifest_sha256,
        "verified_source_files": len(source_cache),
        "source_inputs": source_records,
        "controls": control_records,
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "total_artifact_bytes": sum(record["size"] for record in artifacts),
    }
    write_json(manifest_path, payload)
    return payload


def resolve_manifest_record(
    record: dict[str, Any], *, allowed_roots: dict[str, Path]
) -> Path:
    root_id = record.get("root_id")
    relative_value = record.get("path")
    if root_id not in allowed_roots:
        raise ValueError("unknown_root_id")
    if not isinstance(relative_value, str) or not relative_value:
        raise ValueError("invalid_path_type")
    relative_path = Path(relative_value)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("path_escape")
    root = allowed_roots[root_id].resolve()
    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("path_escape") from error
    return resolved


def verify_record_collection(
    records: Any,
    *,
    collection: str,
    allowed_roots: dict[str, Path],
    identifier_key: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Path]]:
    mismatches: list[dict[str, Any]] = []
    resolved_records: dict[str, Path] = {}
    if not isinstance(records, list):
        return ([{"collection": collection, "reason": "wrong_type"}], resolved_records)
    seen_ids: set[str] = set()
    seen_locations: set[tuple[str, str]] = set()
    for index, raw_record in enumerate(records):
        if not isinstance(raw_record, dict):
            mismatches.append(
                {"collection": collection, "index": index, "reason": "wrong_type"}
            )
            continue
        identifier = str(index)
        if identifier_key is not None:
            identifier_value = raw_record.get(identifier_key)
            if not isinstance(identifier_value, str) or not identifier_value.strip():
                mismatches.append(
                    {
                        "collection": collection,
                        "index": index,
                        "reason": "invalid_identifier",
                    }
                )
                continue
            identifier = identifier_value
            if identifier in seen_ids:
                mismatches.append(
                    {
                        "collection": collection,
                        "id": identifier,
                        "reason": "duplicate_identifier",
                    }
                )
                continue
            seen_ids.add(identifier)
        location = (str(raw_record.get("root_id")), str(raw_record.get("path")))
        if location in seen_locations:
            mismatches.append(
                {
                    "collection": collection,
                    "id": identifier,
                    "reason": "duplicate_path",
                }
            )
            continue
        seen_locations.add(location)
        try:
            path = resolve_manifest_record(raw_record, allowed_roots=allowed_roots)
        except ValueError as error:
            mismatches.append(
                {
                    "collection": collection,
                    "id": identifier,
                    "path": raw_record.get("path"),
                    "reason": str(error),
                }
            )
            continue
        if not path.exists():
            mismatches.append(
                {
                    "collection": collection,
                    "id": identifier,
                    "path": str(path),
                    "reason": "missing",
                }
            )
            continue
        if not path.is_file():
            mismatches.append(
                {
                    "collection": collection,
                    "id": identifier,
                    "path": str(path),
                    "reason": "wrong_type",
                }
            )
            continue
        expected_sha = raw_record.get("sha256")
        expected_size = raw_record.get("size")
        if (
            not isinstance(expected_sha, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected_sha)
            or not isinstance(expected_size, int)
            or isinstance(expected_size, bool)
            or expected_size < 0
        ):
            mismatches.append(
                {
                    "collection": collection,
                    "id": identifier,
                    "path": str(path),
                    "reason": "invalid_hash_or_size_metadata",
                }
            )
            continue
        actual_sha = sha256_file(path)
        actual_size = path.stat().st_size
        if actual_sha != expected_sha or actual_size != expected_size:
            mismatches.append(
                {
                    "collection": collection,
                    "id": identifier,
                    "path": str(path),
                    "reason": "size_or_sha256_mismatch",
                    "actual_sha256": actual_sha,
                    "expected_sha256": expected_sha,
                    "actual_size": actual_size,
                    "expected_size": expected_size,
                }
            )
            continue
        resolved_records[identifier] = path
    return mismatches, resolved_records


def verify_wp3_manifest(
    manifest_path: Path,
    review_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    resolved_review_root = (review_root or manifest_path.parent.parent).resolve()
    resolved_repo_root = (repo_root or resolved_review_root.parents[1]).resolve()
    allowed_roots = {
        "review": resolved_review_root,
        "repo": resolved_repo_root,
    }
    mismatches: list[dict[str, Any]] = []
    if payload.get("schema_version") != 2:
        mismatches.append({"collection": "manifest", "reason": "unsupported_schema"})
    if payload.get("gate0") != "BLOCKED" or payload.get("training_authorized") is not False:
        mismatches.append({"collection": "manifest", "reason": "unsafe_gate_state"})
    artifact_mismatches, artifacts = verify_record_collection(
        payload.get("artifacts"),
        collection="artifacts",
        allowed_roots=allowed_roots,
        identifier_key=None,
    )
    source_mismatches, source_inputs = verify_record_collection(
        payload.get("source_inputs"),
        collection="source_inputs",
        allowed_roots=allowed_roots,
        identifier_key="input_id",
    )
    control_mismatches, controls = verify_record_collection(
        payload.get("controls"),
        collection="controls",
        allowed_roots=allowed_roots,
        identifier_key="control_id",
    )
    mismatches.extend(artifact_mismatches)
    mismatches.extend(source_mismatches)
    mismatches.extend(control_mismatches)

    required_sources = {
        "image_inventory",
        "source_preservation_proof",
        "wp1_artifact_manifest",
        "provenance_evidence",
        "wp2_grouping_clusters",
        "wp2_grouping_edges",
        "wp2_taxonomy_review",
        "wp2_generated_manifest",
        "decision_status",
    }
    for missing_source in sorted(required_sources - set(source_inputs)):
        mismatches.append(
            {
                "collection": "source_inputs",
                "id": missing_source,
                "reason": "required_source_missing_or_invalid",
            }
        )
    required_controls = {
        "decision_status",
        "source_preservation_proof",
        "wp1_artifact_manifest",
        "wp2_generated_manifest",
        "provenance_evidence",
    }
    for missing_control in sorted(required_controls - set(controls)):
        mismatches.append(
            {
                "collection": "controls",
                "id": missing_control,
                "reason": "required_control_missing_or_invalid",
            }
        )

    decision_path = controls.get("decision_status")
    if decision_path is not None:
        if sha256_file(decision_path) != payload.get("decision_status_sha256"):
            mismatches.append(
                {
                    "collection": "controls",
                    "id": "decision_status",
                    "reason": "control_hash_mismatch",
                }
            )
        try:
            decision_payload = json.loads(decision_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            mismatches.append(
                {"collection": "controls", "id": "decision_status", "reason": "invalid_json"}
            )
        else:
            if (
                decision_payload.get("gate0") != "BLOCKED"
                or decision_payload.get("training_authorized") is not False
            ):
                mismatches.append(
                    {
                        "collection": "controls",
                        "id": "decision_status",
                        "reason": "unsafe_gate_state",
                    }
                )

    source_proof_path = controls.get("source_preservation_proof")
    if source_proof_path is not None:
        try:
            source_proof = json.loads(source_proof_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            mismatches.append(
                {
                    "collection": "controls",
                    "id": "source_preservation_proof",
                    "reason": "invalid_json",
                }
            )
        else:
            if source_proof.get("unchanged") is not True:
                mismatches.append(
                    {
                        "collection": "controls",
                        "id": "source_preservation_proof",
                        "reason": "source_not_unchanged",
                    }
                )
            if source_proof.get("source_tree_manifest_sha256") != payload.get(
                "source_tree_manifest_sha256"
            ):
                mismatches.append(
                    {
                        "collection": "controls",
                        "id": "source_preservation_proof",
                        "reason": "source_tree_hash_mismatch",
                    }
                )

    artifact_records = payload.get("artifacts")
    if isinstance(artifact_records, list):
        expected_count = len(artifact_records)
        expected_bytes = sum(
            record.get("size", 0)
            for record in artifact_records
            if isinstance(record, dict) and isinstance(record.get("size"), int)
        )
        if payload.get("artifact_count") != expected_count:
            mismatches.append({"collection": "manifest", "reason": "artifact_count_mismatch"})
        if payload.get("total_artifact_bytes") != expected_bytes:
            mismatches.append({"collection": "manifest", "reason": "artifact_bytes_mismatch"})
    return {
        "valid": not mismatches,
        "artifact_count": len(artifacts),
        "source_input_count": len(source_inputs),
        "control_count": len(controls),
        "total_artifact_bytes": payload.get("total_artifact_bytes"),
        "mismatches": mismatches,
    }


def build_reviewer_assets(
    *,
    audit_dir: Path,
    staging_root: Path,
    wp2_generated_dir: Path,
    review_dir: Path,
) -> dict[str, Any]:
    generated_dir = review_dir / "generated"
    assets_dir = review_dir / "assets" / "wp3"
    raw_root = staging_root / "raw"
    decision_path = review_dir / "decision_status.json"
    decision_before = sha256_file(decision_path)
    source_proof_path = audit_dir / "source_preservation_proof.json"
    source_proof = json.loads(source_proof_path.read_text(encoding="utf-8"))
    if source_proof.get("unchanged") is not True:
        raise ValueError("WP1 source preservation proof is not unchanged=true")

    if assets_dir.exists():
        shutil.rmtree(assets_dir)
    assets_dir.mkdir(parents=True)
    inventory_rows = read_csv(audit_dir / "image_inventory.csv")
    inventory = {row["stem"]: row for row in inventory_rows}
    if len(inventory) != len(inventory_rows):
        raise ValueError("image inventory contains duplicate stems")
    source_cache: dict[str, dict[str, Any]] = {}

    grouping_paths, grouping_rows, grouping_page_audits = build_grouping_review(
        clusters_path=wp2_generated_dir / "grouping_proxy_clusters.csv",
        edges_path=wp2_generated_dir / "grouping_proxy_edges.csv",
        inventory=inventory,
        raw_root=raw_root,
        assets_dir=assets_dir,
        generated_dir=generated_dir,
        source_cache=source_cache,
    )
    taxonomy_paths, taxonomy_rows, taxonomy_page_audits = build_taxonomy_atlas(
        taxonomy_path=wp2_generated_dir / "taxonomy_review.csv",
        inventory=inventory,
        raw_root=raw_root,
        assets_dir=assets_dir,
        generated_dir=generated_dir,
        source_cache=source_cache,
    )
    write_csv(
        generated_dir / "wp3_source_lineage.csv",
        [source_cache[stem] for stem in sorted(source_cache)],
    )
    grouping_audits = {
        row["proxy_sequence_id"]: row
        for page in grouping_page_audits
        for row in page["rows"]
    }
    taxonomy_audits = {
        int(row["class_id"]): row
        for page in taxonomy_page_audits
        for row in page["rows"]
    }
    if set(grouping_audits) != {row["proxy_sequence_id"] for row in grouping_rows}:
        raise RuntimeError("grouping layout audit coverage does not match reviewer index")
    if set(taxonomy_audits) != {int(row["class_id"]) for row in taxonomy_rows}:
        raise RuntimeError("taxonomy layout audit coverage does not match reviewer atlas")
    for row in grouping_rows:
        audit = grouping_audits[row["proxy_sequence_id"]]
        if audit["summary"]["full_text"] != grouping_summary(row):
            raise RuntimeError("grouping summary layout audit lost reviewer text")
    for row in taxonomy_rows:
        audit = taxonomy_audits[int(row["class_id"])]
        expected_flags = f"conflicts: {row['conflict_flags'] or 'none recorded'}"
        if audit["conflict_flags"]["full_text"] != expected_flags:
            raise RuntimeError("taxonomy layout audit lost conflict flags")
    write_json(
        generated_dir / "wp3_render_layout_audit.json",
        {
            "schema_version": 1,
            "status": "PASS_COMPLETE_TEXT_AND_BOUNDS",
            "checks": {
                "grouping_rows_audited": len(grouping_audits),
                "taxonomy_rows_audited": len(taxonomy_audits),
                "all_text_complete": True,
                "all_text_bounds_fit": True,
            },
            "grouping_pages": grouping_page_audits,
            "taxonomy_pages": taxonomy_page_audits,
        },
    )
    if sha256_file(decision_path) != decision_before:
        raise RuntimeError("decision_status.json changed while building WP3 assets")

    provenance_path = audit_dir / "provenance_evidence.json"
    source_inputs = [
        ("image_inventory", audit_dir / "image_inventory.csv"),
        ("source_preservation_proof", source_proof_path),
        ("wp1_artifact_manifest", audit_dir / "wp1_artifact_manifest.json"),
        ("provenance_evidence", provenance_path),
        ("wp2_grouping_clusters", wp2_generated_dir / "grouping_proxy_clusters.csv"),
        ("wp2_grouping_edges", wp2_generated_dir / "grouping_proxy_edges.csv"),
        ("wp2_taxonomy_review", wp2_generated_dir / "taxonomy_review.csv"),
        ("wp2_generated_manifest", wp2_generated_dir / "wp2_generated_manifest.json"),
        ("decision_status", decision_path),
    ]
    control_inputs = [
        ("decision_status", decision_path),
        ("source_preservation_proof", source_proof_path),
        ("wp1_artifact_manifest", audit_dir / "wp1_artifact_manifest.json"),
        ("wp2_generated_manifest", wp2_generated_dir / "wp2_generated_manifest.json"),
        ("provenance_evidence", provenance_path),
    ]
    manifest = build_wp3_manifest(
        review_dir=review_dir,
        repo_root=review_dir.parents[1],
        source_inputs=source_inputs,
        control_inputs=control_inputs,
        source_cache=source_cache,
        decision_sha256=decision_before,
        source_tree_manifest_sha256=source_proof["source_tree_manifest_sha256"],
    )
    return {
        "status": WP3_STATUS,
        "grouping_sequences": len(grouping_rows),
        "grouping_contact_sheets": len(grouping_paths) - 1,
        "taxonomy_classes": len(taxonomy_rows),
        "taxonomy_pages": len(taxonomy_paths) - 1,
        "verified_source_files": len(source_cache),
        "artifact_count": manifest["artifact_count"],
        "total_artifact_bytes": manifest["total_artifact_bytes"],
        "decision_status_sha256": decision_before,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--audit-dir", type=Path, required=True)
    build.add_argument("--staging-root", type=Path, required=True)
    build.add_argument("--wp2-generated-dir", type=Path, required=True)
    build.add_argument("--review-dir", type=Path, required=True)
    verify = commands.add_parser("verify-manifest")
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--root", type=Path)
    verify.add_argument("--repo-root", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "verify-manifest":
        result = verify_wp3_manifest(args.manifest, args.root, args.repo_root)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1
    result = build_reviewer_assets(
        audit_dir=args.audit_dir,
        staging_root=args.staging_root,
        wp2_generated_dir=args.wp2_generated_dir,
        review_dir=args.review_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
