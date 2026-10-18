#!/usr/bin/env python3
"""Reproducible, read-only audit for the external DATASET01 archive and staging copy."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import tempfile
import zipfile
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import ExifTags, Image

EXPECTED_ARCHIVE_SHA256 = (
    "052bc980a7206f8ddd1ec2e59098dbd60a42036d3c7f7384ace4fe6416cbaa76"
)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_stream(handle: Any, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: handle.read(chunk_size), b""):
        digest.update(chunk)
    return digest.hexdigest()


def detect_line_endings(data: bytes) -> str:
    crlf = data.count(b"\r\n")
    bare_lf = data.count(b"\n") - crlf
    bare_cr = data.count(b"\r") - crlf
    kinds = sum(value > 0 for value in (crlf, bare_lf, bare_cr))
    if kinds > 1:
        return "mixed"
    if crlf:
        return "crlf"
    if bare_lf:
        return "lf"
    if bare_cr:
        return "cr"
    return "none"


def normalize_utf8_text(data: bytes) -> bytes:
    text = data.decode("utf-8")
    if not text:
        return b""
    return ("\n".join(text.splitlines()) + "\n").encode("utf-8")


def write_bytes_atomic(path: Path, data: bytes, *, allow_replace: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() == data:
            return
        if not allow_replace:
            raise ValueError(f"Refusing to overwrite different generated file: {path}")
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def write_json_atomic(path: Path, payload: Any, *, allow_replace: bool = False) -> None:
    data = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    write_bytes_atomic(path, data, allow_replace=allow_replace)


def write_csv_atomic(
    path: Path,
    fieldnames: list[str],
    rows: Iterable[dict[str, Any]],
    *,
    allow_replace: bool = False,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        delete=False,
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(handle.name)
    data = temporary.read_bytes()
    temporary.unlink()
    write_bytes_atomic(path, data, allow_replace=allow_replace)


def canonical_tree_fingerprint(root: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    total_bytes = 0
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        stat = path.stat()
        file_sha = sha256_file(path)
        relative = path.relative_to(root).as_posix()
        record = f"{relative}\0{stat.st_size}\0{stat.st_mtime_ns}\0{file_sha}\n"
        digest.update(record.encode("utf-8"))
        total_bytes += stat.st_size
    return {
        "path": str(root),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "tree_manifest_sha256": digest.hexdigest(),
        "image_count": sum(path.suffix.lower() in {".jpg", ".jpeg", ".png"} for path in files),
        "label_count": sum(
            path.parent.name == "labels" and path.suffix.lower() == ".txt" for path in files
        ),
        "mtime_ns": root.stat().st_mtime_ns,
    }


def snapshot_source(source_root: Path) -> dict[str, Any]:
    archive_path = source_root / "archive.zip"
    extracted_path = source_root / "archive"
    archive_stat = archive_path.stat()
    return {
        "schema_version": 1,
        "captured_utc": datetime.now(UTC).isoformat(),
        "source_root": str(source_root),
        "archive": {
            "path": str(archive_path),
            "size": archive_stat.st_size,
            "mtime_ns": archive_stat.st_mtime_ns,
            "sha256": sha256_file(archive_path),
        },
        "extracted_source": canonical_tree_fingerprint(extracted_path),
    }


def compare_source_snapshots(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "archive_sha256_unchanged": before["archive"]["sha256"]
        == after["archive"]["sha256"],
        "archive_size_unchanged": before["archive"]["size"] == after["archive"]["size"],
        "archive_mtime_unchanged": before["archive"]["mtime_ns"]
        == after["archive"]["mtime_ns"],
        "source_tree_hash_unchanged": (
            before["extracted_source"]["tree_manifest_sha256"]
            == after["extracted_source"]["tree_manifest_sha256"]
        ),
        "source_file_count_unchanged": (
            before["extracted_source"]["file_count"]
            == after["extracted_source"]["file_count"]
        ),
        "source_total_bytes_unchanged": (
            before["extracted_source"]["total_bytes"]
            == after["extracted_source"]["total_bytes"]
        ),
        "source_mtime_unchanged": (
            before["extracted_source"]["mtime_ns"]
            == after["extracted_source"]["mtime_ns"]
        ),
        "source_image_count_unchanged": (
            before["extracted_source"]["image_count"]
            == after["extracted_source"]["image_count"]
        ),
        "source_label_count_unchanged": (
            before["extracted_source"]["label_count"]
            == after["extracted_source"]["label_count"]
        ),
    }
    return {
        "schema_version": 1,
        "compared_utc": datetime.now(UTC).isoformat(),
        "unchanged": all(checks.values()),
        "checks": checks,
        "before_captured_utc": before["captured_utc"],
        "after_captured_utc": after["captured_utc"],
        "archive_sha256": before["archive"]["sha256"],
        "source_tree_manifest_sha256": before["extracted_source"][
            "tree_manifest_sha256"
        ],
    }


def manifest_directory(root: Path, output: Path) -> dict[str, Any]:
    files = sorted(
        path for path in root.rglob("*") if path.is_file() and path.resolve() != output.resolve()
    )
    return {
        "schema_version": 1,
        "generated_utc": datetime.now(UTC).isoformat(),
        "root": str(root),
        "artifact_count": len(files),
        "artifacts": [
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
    }


def verify_artifact_manifest(
    manifest_path: Path, root: Path | None = None
) -> dict[str, Any]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = payload.get("artifacts", [])
    records = list(artifacts.values()) if isinstance(artifacts, dict) else list(artifacts)
    manifest_root = root or Path(payload.get("root", manifest_path.parent))
    mismatches: list[dict[str, Any]] = []
    for record in records:
        recorded_path = Path(record["path"])
        artifact_path = (
            recorded_path if recorded_path.is_absolute() else manifest_root / recorded_path
        )
        if not artifact_path.is_file():
            mismatches.append(
                {
                    "path": str(artifact_path),
                    "reason": "missing",
                    "expected_sha256": record["sha256"],
                }
            )
            continue
        actual_size = artifact_path.stat().st_size
        actual_sha = sha256_file(artifact_path)
        if actual_size != record["size"] or actual_sha != record["sha256"]:
            mismatches.append(
                {
                    "path": str(artifact_path),
                    "reason": "size_or_sha256_mismatch",
                    "expected_size": record["size"],
                    "actual_size": actual_size,
                    "expected_sha256": record["sha256"],
                    "actual_sha256": actual_sha,
                }
            )
    return {
        "schema_version": 1,
        "verified_utc": datetime.now(UTC).isoformat(),
        "manifest": str(manifest_path),
        "artifact_count": len(records),
        "valid": not mismatches,
        "mismatches": mismatches,
    }


def load_utf8_lines(path: Path) -> tuple[list[str], str]:
    data = path.read_bytes()
    return data.decode("utf-8").splitlines(), detect_line_endings(data)


def kind_for_path(relative_path: str) -> str:
    if "/images/" in f"/{relative_path}":
        return "image"
    if "/labels/" in f"/{relative_path}":
        return "label"
    if "/split_dataset/" in f"/{relative_path}":
        return "split"
    if Path(relative_path).name.startswith("classes"):
        return "class_list"
    return "other"


def area_ratio_bucket(area: float) -> str:
    if area < 0.001:
        return "lt_0.001"
    if area < 0.005:
        return "0.001_to_lt_0.005"
    if area < 0.02:
        return "0.005_to_lt_0.02"
    if area < 0.1:
        return "0.02_to_lt_0.1"
    return "ge_0.1"


def crop_min_side_bucket(min_side: float) -> str:
    if min_side < 16:
        return "lt_16px"
    if min_side < 32:
        return "16_to_lt_32px"
    if min_side < 64:
        return "32_to_lt_64px"
    return "ge_64px"


def parse_split(path: Path) -> tuple[list[str], str]:
    lines, endings = load_utf8_lines(path)
    return [Path(line.strip()).stem for line in lines if line.strip()], endings


def audit_dataset(
    *,
    staging_root: Path,
    archive_zip: Path,
    output_dir: Path,
    expected_archive_sha256: str = EXPECTED_ARCHIVE_SHA256,
    expected_images: int = 3216,
    expected_labels: int = 3216,
    expected_classes: int = 52,
    expected_boxes: int = 8334,
    expected_empty_labels: int = 25,
    write_normalized: bool = False,
) -> dict[str, Any]:
    raw_root = staging_root / "raw"
    dataset_root = raw_root / "archive"
    images_dir = dataset_root / "images"
    labels_dir = dataset_root / "labels"
    split_dir = dataset_root / "split_dataset"
    normalized_root = staging_root / "generated" / "normalized"

    archive_sha = sha256_file(archive_zip)
    file_rows: list[dict[str, Any]] = []
    text_line_endings: Counter[str] = Counter()
    raw_files = sorted(path for path in raw_root.rglob("*") if path.is_file())
    raw_by_relative = {path.relative_to(raw_root).as_posix(): path for path in raw_files}

    zip_hashes: dict[str, str] = {}
    zip_sizes: dict[str, int] = {}
    zip_crc_error: str | None = None
    with zipfile.ZipFile(archive_zip) as archive:
        for info in sorted(archive.infolist(), key=lambda item: item.filename):
            if info.is_dir():
                continue
            with archive.open(info) as handle:
                try:
                    zip_hashes[info.filename] = sha256_stream(handle)
                except zipfile.BadZipFile as exc:
                    zip_crc_error = str(exc)
                    break
            zip_sizes[info.filename] = info.file_size

    local_hashes: dict[str, str] = {}
    utf8_errors: list[str] = []
    for relative, path in raw_by_relative.items():
        data = path.read_bytes()
        local_hash = hashlib.sha256(data).hexdigest()
        local_hashes[relative] = local_hash
        endings = ""
        if path.suffix.lower() == ".txt":
            endings = detect_line_endings(data)
            text_line_endings[endings] += 1
            try:
                data.decode("utf-8")
            except UnicodeDecodeError:
                utf8_errors.append(relative)
        stat = path.stat()
        file_rows.append(
            {
                "path": relative,
                "kind": kind_for_path(relative),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": local_hash,
                "zip_sha256": zip_hashes.get(relative, ""),
                "zip_byte_match": local_hash == zip_hashes.get(relative),
                "line_endings": endings,
            }
        )

    zip_members = set(zip_hashes)
    raw_members = set(raw_by_relative)
    missing_from_staging = sorted(zip_members - raw_members)
    extra_in_staging = sorted(raw_members - zip_members)
    byte_mismatches = sorted(
        relative
        for relative in zip_members & raw_members
        if zip_hashes[relative] != local_hashes[relative]
    )

    class_codes, classes_line_endings = load_utf8_lines(dataset_root / "classes.txt")
    class_names_en, classes_en_line_endings = load_utf8_lines(
        dataset_root / "classes_en.txt"
    )
    class_names_vi, classes_vi_line_endings = load_utf8_lines(
        dataset_root / "classes_vie.txt"
    )

    image_paths = sorted(
        path
        for path in images_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    label_paths = sorted(
        path for path in labels_dir.iterdir() if path.is_file() and path.suffix == ".txt"
    )
    image_by_stem = {path.stem: path for path in image_paths}
    label_by_stem = {path.stem: path for path in label_paths}

    image_dimensions: dict[str, tuple[int, int]] = {}
    image_metadata: dict[str, dict[str, Any]] = {}
    decode_errors: list[dict[str, str]] = []
    exif_counts: Counter[str] = Counter()
    exif_values: dict[str, set[str]] = defaultdict(set)
    for stem, path in image_by_stem.items():
        try:
            with Image.open(path) as image:
                image.load()
                width, height = image.size
                exif = image.getexif()
                exif_named = {
                    ExifTags.TAGS.get(key, str(key)): str(value) for key, value in exif.items()
                }
                for key, value in exif_named.items():
                    exif_counts[key] += 1
                    if key in {"Make", "Model", "Software", "DateTime", "DateTimeOriginal"}:
                        exif_values[key].add(value)
                image_dimensions[stem] = (width, height)
                image_metadata[stem] = {
                    "width": width,
                    "height": height,
                    "format": image.format or "",
                    "mode": image.mode,
                    "has_exif": bool(exif),
                    "has_gps": "GPSInfo" in exif_named,
                }
        except Exception as exc:  # Pillow raises format-specific decode exceptions.
            decode_errors.append({"stem": stem, "error": f"{type(exc).__name__}: {exc}"})

    label_errors: list[dict[str, Any]] = []
    bbox_boundary_warnings: list[dict[str, Any]] = []
    boxes: list[dict[str, Any]] = []
    empty_label_stems: list[str] = []
    image_classes: dict[str, set[int]] = defaultdict(set)
    per_class_boxes: Counter[int] = Counter()
    per_class_images: dict[int, set[str]] = defaultdict(set)
    label_hash_by_stem: dict[str, str] = {}
    label_line_endings: Counter[str] = Counter()
    for stem, path in label_by_stem.items():
        data = path.read_bytes()
        label_hash_by_stem[stem] = hashlib.sha256(data).hexdigest()
        endings = detect_line_endings(data)
        label_line_endings[endings] += 1
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            label_errors.append({"stem": stem, "line": 0, "error": f"utf8: {exc}"})
            continue
        rows = [line for line in text.splitlines() if line.strip()]
        if not rows:
            empty_label_stems.append(stem)
            continue
        width, height = image_dimensions.get(stem, (0, 0))
        for line_number, line in enumerate(rows, start=1):
            fields = line.split()
            if len(fields) != 5:
                label_errors.append(
                    {
                        "stem": stem,
                        "line": line_number,
                        "error": f"expected 5 fields, got {len(fields)}",
                    }
                )
                continue
            try:
                class_id = int(fields[0])
                x_center, y_center, box_width, box_height = map(float, fields[1:])
            except ValueError as exc:
                label_errors.append(
                    {"stem": stem, "line": line_number, "error": f"parse: {exc}"}
                )
                continue
            values = (x_center, y_center, box_width, box_height)
            valid = (
                0 <= class_id < expected_classes
                and all(math.isfinite(value) for value in values)
                and 0 <= x_center <= 1
                and 0 <= y_center <= 1
                and 0 < box_width <= 1
                and 0 < box_height <= 1
            )
            if not valid:
                label_errors.append(
                    {
                        "stem": stem,
                        "line": line_number,
                        "error": "class or normalized bbox out of range",
                    }
                )
                continue
            within_frame = (
                x_center - box_width / 2 >= -1e-6
                and x_center + box_width / 2 <= 1 + 1e-6
                and y_center - box_height / 2 >= -1e-6
                and y_center + box_height / 2 <= 1 + 1e-6
            )
            if not within_frame:
                bbox_boundary_warnings.append(
                    {
                        "stem": stem,
                        "line": line_number,
                        "class_id": class_id,
                        "x_center": x_center,
                        "y_center": y_center,
                        "width": box_width,
                        "height": box_height,
                        "warning": "bbox extent crosses image boundary; preserve raw and review",
                    }
                )
            area_ratio = box_width * box_height
            crop_min_side = min(box_width * width, box_height * height)
            boxes.append(
                {
                    "stem": stem,
                    "class_id": class_id,
                    "area_ratio_bucket": area_ratio_bucket(area_ratio),
                    "crop_min_side_bucket": crop_min_side_bucket(crop_min_side),
                }
            )
            per_class_boxes[class_id] += 1
            per_class_images[class_id].add(stem)
            image_classes[stem].add(class_id)

    train_stems, train_line_endings = parse_split(split_dir / "train_files.txt")
    test_stems, test_line_endings = parse_split(split_dir / "test_files.txt")
    train_set = set(train_stems)
    test_set = set(test_stems)
    direct_overlap = sorted(train_set & test_set)
    split_of = {stem: "train" for stem in train_set}
    split_of.update({stem: "test" for stem in test_set})

    adjacent_rows: list[dict[str, Any]] = []
    numeric_to_stem = {int(stem): stem for stem in split_of if stem.isdigit()}
    for number in sorted(numeric_to_stem):
        if number + 1 not in numeric_to_stem:
            continue
        left = numeric_to_stem[number]
        right = numeric_to_stem[number + 1]
        adjacent_rows.append(
            {
                "left_stem": left,
                "left_split": split_of[left],
                "right_stem": right,
                "right_split": split_of[right],
                "cross_split": split_of[left] != split_of[right],
                "evidence_status": "proxy_only_not_group_ground_truth",
            }
        )
    cross_split_adjacent = sum(bool(row["cross_split"]) for row in adjacent_rows)

    per_class_rows: list[dict[str, Any]] = []
    for class_id in range(expected_classes):
        class_stems = per_class_images[class_id]
        per_class_rows.append(
            {
                "class_id": class_id,
                "sign_code": class_codes[class_id] if class_id < len(class_codes) else "",
                "name_en": class_names_en[class_id] if class_id < len(class_names_en) else "",
                "name_vi": class_names_vi[class_id] if class_id < len(class_names_vi) else "",
                "image_count": len(class_stems),
                "box_count": per_class_boxes[class_id],
                "train_image_count": len(class_stems & train_set),
                "test_image_count": len(class_stems & test_set),
                "unsplit_image_count": len(class_stems - train_set - test_set),
            }
        )

    area_buckets = Counter(box["area_ratio_bucket"] for box in boxes)
    crop_buckets = Counter(box["crop_min_side_bucket"] for box in boxes)
    bucket_rows = [
        {"dimension": "bbox_area_ratio", "bucket": bucket, "box_count": count}
        for bucket, count in sorted(area_buckets.items())
    ]
    bucket_rows.extend(
        {
            "dimension": "crop_min_side_px",
            "bucket": bucket,
            "box_count": count,
        }
        for bucket, count in sorted(crop_buckets.items())
    )

    image_rows: list[dict[str, Any]] = []
    for stem in sorted(image_by_stem):
        metadata = image_metadata.get(stem, {})
        image_relative = image_by_stem[stem].relative_to(raw_root).as_posix()
        image_rows.append(
            {
                "stem": stem,
                "image_path": image_relative,
                "image_sha256": local_hashes.get(image_relative, ""),
                "label_path": (
                    label_by_stem[stem].relative_to(raw_root).as_posix()
                    if stem in label_by_stem
                    else ""
                ),
                "label_sha256": label_hash_by_stem.get(stem, ""),
                "width": metadata.get("width", ""),
                "height": metadata.get("height", ""),
                "format": metadata.get("format", ""),
                "mode": metadata.get("mode", ""),
                "has_exif": metadata.get("has_exif", False),
                "has_gps": metadata.get("has_gps", False),
                "box_count": sum(stem == box["stem"] for box in boxes),
                "class_ids": " ".join(str(value) for value in sorted(image_classes[stem])),
                "split": split_of.get(stem, "unassigned"),
            }
        )

    transformation_rows: list[dict[str, Any]] = []
    if write_normalized:
        text_paths = [
            path
            for path in raw_files
            if path.suffix.lower() == ".txt"
            and kind_for_path(path.relative_to(raw_root).as_posix())
            in {"label", "split", "class_list"}
        ]
        for source_path in text_paths:
            relative = source_path.relative_to(raw_root)
            source_data = source_path.read_bytes()
            normalized_data = normalize_utf8_text(source_data)
            output_path = normalized_root / relative
            write_bytes_atomic(output_path, normalized_data)
            transformation_rows.append(
                {
                    "source_path": relative.as_posix(),
                    "source_sha256": hashlib.sha256(source_data).hexdigest(),
                    "source_line_endings": detect_line_endings(source_data),
                    "output_path": output_path.relative_to(staging_root).as_posix(),
                    "output_sha256": hashlib.sha256(normalized_data).hexdigest(),
                    "output_line_endings": detect_line_endings(normalized_data),
                    "transformation": "UTF-8 decode; CRLF/CR to LF; final LF for non-empty files",
                }
            )

    checks = {
        "archive_sha256_matches": archive_sha == expected_archive_sha256,
        "zip_crc_stream_read_ok": zip_crc_error is None,
        "raw_member_set_matches_zip": not missing_from_staging and not extra_in_staging,
        "raw_bytes_match_zip": not byte_mismatches,
        "image_count_matches": len(image_paths) == expected_images,
        "label_count_matches": len(label_paths) == expected_labels,
        "image_label_stems_match": set(image_by_stem) == set(label_by_stem),
        "all_images_decode": not decode_errors,
        "all_text_is_utf8": not utf8_errors,
        "class_lists_match_expected": (
            len(class_codes)
            == len(class_names_en)
            == len(class_names_vi)
            == expected_classes
        ),
        "all_yolo_rows_valid": not label_errors,
        "all_class_ids_observed": set(per_class_boxes) == set(range(expected_classes)),
        "box_count_matches": len(boxes) == expected_boxes,
        "empty_label_count_matches": len(empty_label_stems) == expected_empty_labels,
    }
    technical_audit_pass = all(checks.values())

    summary: dict[str, Any] = {
        "schema_version": 1,
        "generated_utc": datetime.now(UTC).isoformat(),
        "status": {
            "technical_audit": "PASS" if technical_audit_pass else "FAIL",
            "gate0": "BLOCKED",
            "training_authorized": False,
        },
        "paths": {
            "archive_zip": str(archive_zip),
            "staging_root": str(staging_root),
            "raw_dataset_root": str(dataset_root),
            "normalized_root": str(normalized_root) if write_normalized else None,
        },
        "archive": {
            "sha256": archive_sha,
            "size": archive_zip.stat().st_size,
            "zip_member_count": len(zip_hashes),
            "zip_crc_error": zip_crc_error,
            "missing_from_staging": missing_from_staging,
            "extra_in_staging": extra_in_staging,
            "byte_mismatches": byte_mismatches,
        },
        "counts": {
            "images": len(image_paths),
            "labels": len(label_paths),
            "paired_stems": len(set(image_by_stem) & set(label_by_stem)),
            "image_only_stems": sorted(set(image_by_stem) - set(label_by_stem)),
            "label_only_stems": sorted(set(label_by_stem) - set(image_by_stem)),
            "classes_expected": expected_classes,
            "classes_observed": len(per_class_boxes),
            "boxes": len(boxes),
            "empty_labels": len(empty_label_stems),
        },
        "image_decode": {
            "decoded": len(image_metadata),
            "errors": decode_errors,
            "dimension_counts": dict(
                sorted(
                    (
                        (f"{width}x{height}", count)
                        for (width, height), count in Counter(image_dimensions.values()).items()
                    ),
                    key=lambda item: item[0],
                )
            ),
        },
        "text": {
            "raw_file_line_endings": dict(sorted(text_line_endings.items())),
            "label_line_endings": dict(sorted(label_line_endings.items())),
            "classes_line_endings": {
                "classes.txt": classes_line_endings,
                "classes_en.txt": classes_en_line_endings,
                "classes_vie.txt": classes_vi_line_endings,
            },
            "split_line_endings": {
                "train_files.txt": train_line_endings,
                "test_files.txt": test_line_endings,
            },
            "utf8_errors": utf8_errors,
            "normalized_files_written": len(transformation_rows),
        },
        "labels": {
            "validation_errors": label_errors,
            "bbox_boundary_warnings": bbox_boundary_warnings,
            "empty_label_stems": empty_label_stems,
            "min_boxes_per_class": min(per_class_boxes.values(), default=0),
            "max_boxes_per_class": max(per_class_boxes.values(), default=0),
        },
        "splits": {
            "train_count": len(train_stems),
            "train_unique": len(train_set),
            "test_count": len(test_stems),
            "test_unique": len(test_set),
            "validation_present": (split_dir / "val_files.txt").exists()
            or (split_dir / "valid_files.txt").exists(),
            "direct_overlap_count": len(direct_overlap),
            "direct_overlap": direct_overlap,
            "split_missing_images": sorted(set(split_of) - set(image_by_stem)),
            "split_missing_labels": sorted(set(split_of) - set(label_by_stem)),
            "negative_total": len(empty_label_stems),
            "negative_in_train": len(set(empty_label_stems) & train_set),
            "negative_in_test": len(set(empty_label_stems) & test_set),
            "negative_excluded": len(set(empty_label_stems) - train_set - test_set),
        },
        "leakage_proxy": {
            "definition": (
                "Pairs of present numeric filename stems n and n+1. "
                "This is a proxy, not video/scene/physical-sign ground truth."
            ),
            "numeric_consecutive_pairs": len(adjacent_rows),
            "cross_split_pairs": cross_split_adjacent,
            "cross_split_percent": (
                100 * cross_split_adjacent / len(adjacent_rows) if adjacent_rows else 0.0
            ),
        },
        "exif": {
            "images_with_exif": sum(
                bool(metadata.get("has_exif")) for metadata in image_metadata.values()
            ),
            "images_with_gps": sum(
                bool(metadata.get("has_gps")) for metadata in image_metadata.values()
            ),
            "tag_counts": dict(sorted(exif_counts.items())),
            "selected_values": {
                key: sorted(values) for key, values in sorted(exif_values.items())
            },
        },
        "checks": checks,
        "blockers": [
            "Dataset license version conflicts between Hugging Face metadata and card prose.",
            "No verified video/scene/physical-sign group identifiers.",
            "Vietnam taxonomy mapping remains draft and requires domain review.",
            "No approved group-aware train/validation/test split.",
        ],
        "evidence_boundary": (
            "Technical integrity PASS does not approve license, taxonomy, grouping, final splits, "
            "training, Vietnamese-domain performance, or deployment."
        ),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "file_manifest.csv": output_dir / "file_manifest.csv",
        "image_inventory.csv": output_dir / "image_inventory.csv",
        "per_class_counts.csv": output_dir / "per_class_counts.csv",
        "box_size_buckets.csv": output_dir / "box_size_buckets.csv",
        "adjacent_pair_leakage.csv": output_dir / "adjacent_pair_leakage.csv",
        "transformation_manifest.csv": output_dir / "transformation_manifest.csv",
        "audit_summary.json": output_dir / "audit_summary.json",
    }
    write_csv_atomic(
        output_paths["file_manifest.csv"],
        [
            "path",
            "kind",
            "size",
            "mtime_ns",
            "sha256",
            "zip_sha256",
            "zip_byte_match",
            "line_endings",
        ],
        file_rows,
        allow_replace=True,
    )
    write_csv_atomic(
        output_paths["image_inventory.csv"],
        [
            "stem",
            "image_path",
            "image_sha256",
            "label_path",
            "label_sha256",
            "width",
            "height",
            "format",
            "mode",
            "has_exif",
            "has_gps",
            "box_count",
            "class_ids",
            "split",
        ],
        image_rows,
        allow_replace=True,
    )
    write_csv_atomic(
        output_paths["per_class_counts.csv"],
        [
            "class_id",
            "sign_code",
            "name_en",
            "name_vi",
            "image_count",
            "box_count",
            "train_image_count",
            "test_image_count",
            "unsplit_image_count",
        ],
        per_class_rows,
        allow_replace=True,
    )
    write_csv_atomic(
        output_paths["box_size_buckets.csv"],
        ["dimension", "bucket", "box_count"],
        bucket_rows,
        allow_replace=True,
    )
    write_csv_atomic(
        output_paths["adjacent_pair_leakage.csv"],
        [
            "left_stem",
            "left_split",
            "right_stem",
            "right_split",
            "cross_split",
            "evidence_status",
        ],
        adjacent_rows,
        allow_replace=True,
    )
    write_csv_atomic(
        output_paths["transformation_manifest.csv"],
        [
            "source_path",
            "source_sha256",
            "source_line_endings",
            "output_path",
            "output_sha256",
            "output_line_endings",
            "transformation",
        ],
        transformation_rows,
        allow_replace=True,
    )
    write_json_atomic(output_paths["audit_summary.json"], summary, allow_replace=True)
    output_manifest = {
        "schema_version": 1,
        "generated_utc": datetime.now(UTC).isoformat(),
        "artifacts": {
            name: {
                "path": str(path),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for name, path in output_paths.items()
        },
    }
    write_json_atomic(
        output_dir / "output_manifest.json", output_manifest, allow_replace=True
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    snapshot = commands.add_parser("snapshot-source")
    snapshot.add_argument("--source-root", type=Path, required=True)
    snapshot.add_argument("--output", type=Path, required=True)

    compare = commands.add_parser("compare-source")
    compare.add_argument("--before", type=Path, required=True)
    compare.add_argument("--after", type=Path, required=True)
    compare.add_argument("--output", type=Path)

    manifest = commands.add_parser("manifest-dir")
    manifest.add_argument("--root", type=Path, required=True)
    manifest.add_argument("--output", type=Path, required=True)

    verify = commands.add_parser("verify-manifest")
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--root", type=Path)
    verify.add_argument("--output", type=Path)

    audit = commands.add_parser("audit")
    audit.add_argument("--staging-root", type=Path, required=True)
    audit.add_argument("--archive-zip", type=Path, required=True)
    audit.add_argument("--output-dir", type=Path, required=True)
    audit.add_argument("--expected-archive-sha256", default=EXPECTED_ARCHIVE_SHA256)
    audit.add_argument("--expected-images", type=int, default=3216)
    audit.add_argument("--expected-labels", type=int, default=3216)
    audit.add_argument("--expected-classes", type=int, default=52)
    audit.add_argument("--expected-boxes", type=int, default=8334)
    audit.add_argument("--expected-empty-labels", type=int, default=25)
    audit.add_argument("--write-normalized", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "snapshot-source":
        payload = snapshot_source(args.source_root.resolve())
        write_json_atomic(args.output.resolve(), payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "compare-source":
        before = json.loads(args.before.read_text(encoding="utf-8"))
        after = json.loads(args.after.read_text(encoding="utf-8"))
        payload = compare_source_snapshots(before, after)
        if args.output:
            write_json_atomic(args.output.resolve(), payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["unchanged"] else 1

    if args.command == "manifest-dir":
        payload = manifest_directory(args.root.resolve(), args.output.resolve())
        write_json_atomic(args.output.resolve(), payload, allow_replace=True)
        print(json.dumps({"artifact_count": payload["artifact_count"]}, indent=2))
        return 0

    if args.command == "verify-manifest":
        payload = verify_artifact_manifest(
            args.manifest.resolve(),
            args.root.resolve() if args.root else None,
        )
        if args.output:
            write_json_atomic(args.output.resolve(), payload, allow_replace=True)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["valid"] else 1

    summary = audit_dataset(
        staging_root=args.staging_root.resolve(),
        archive_zip=args.archive_zip.resolve(),
        output_dir=args.output_dir.resolve(),
        expected_archive_sha256=args.expected_archive_sha256,
        expected_images=args.expected_images,
        expected_labels=args.expected_labels,
        expected_classes=args.expected_classes,
        expected_boxes=args.expected_boxes,
        expected_empty_labels=args.expected_empty_labels,
        write_normalized=args.write_normalized,
    )
    print(json.dumps(summary["status"], ensure_ascii=False, indent=2))
    return 0 if summary["status"]["technical_audit"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
