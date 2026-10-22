#!/usr/bin/env python3
"""Build and verify the WP38 derived orientation-correction package.

The 39 source frames in D02-C0034 are stored as 540x960 JPEGs whose scene content is rotated
clockwise.  WP38 keeps every raw byte immutable and creates a lossless decoded-pixel derivative:
960x540 PNG after a 90-degree counter-clockwise rotation.  YOLO boxes are transformed with the
same operation.  This package is validation-only evidence; it does not change WP36-R1, authorize
training, or open the sealed test.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

PACKAGE = "M0-WP38"
STATUS = "WP38_AWAITING_INDEPENDENT_QA"
BUILDER_PATH = Path("scripts/build_wp38_orientation_correction.py")
BOUNDARY = (
    "DERIVED_ORIENTATION_CORRECTION_ONLY_RAW_IMMUTABLE_VAL_ONLY_"
    "NO_SPLIT_CHANGE_NO_TRAINING_AUTHORIZATION_NO_SEALED_TEST_ACCESS"
)
GROUP_ID = "D02-C0034"
ROTATION = "CCW_90"
EXPECTED_STEMS = tuple(f"{value:04d}" for value in range(1319, 1358))
EXPECTED_SOURCE_SIZE = (540, 960)
EXPECTED_DERIVED_SIZE = (960, 540)
EXPECTED_BOX_COUNT = 29
EXPECTED_YOLO_IDS = {12, 14}

GENERATED = Path("docs/review/generated")
PACKAGE_ROOT = Path("data/processed/wp38_orientation_corrected")
IMAGES_DIR = PACKAGE_ROOT / "images"
LABELS_DIR = PACKAGE_ROOT / "labels"
PREVIEW_DIR = Path("docs/review/assets/wp38/orientation_correction")
LINEAGE_PATH = GENERATED / "wp38_orientation_correction_lineage.csv"
MANIFEST_PATH = GENERATED / "wp38_orientation_correction_manifest.json"

PINNED_SOURCES = {
    "docs/review/generated/wp31_r2_group_id_frames.csv": (
        "aea7ea144f4ec389cab8cca70b28ae21d4b21918ef089af16cf3580e828fca7e"
    ),
    "docs/review/generated/wp33_derived_boxes.csv": (
        "4b9307003ce8fd3c1d50763a5950d3d57cf6b2ee6df3aeef74621707067501c0"
    ),
    "docs/review/generated/wp36_r1_split_frames.csv": (
        "8e197d9c7103ac5dc6b7ffc8a3d1aeb30bb6034048d470e4887dd868df95823a"
    ),
    "docs/review/generated/wp37_r1_decode_sizes.csv": (
        "5bcba8a4c58e9e5e063d6a70962f79bcc45bf56d44afd023dce7a8ef3ab2c969"
    ),
    "docs/review/generated/m1_yolo_export_manifest.json": (
        "8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71"
    ),
    "data/processed/m1_yolo/data.yaml": (
        "4cd8303540ecf7bf8ce461b440a07ae35b5ffb047348613c3cdbc8d9c1d78bd0"
    ),
}

LINEAGE_FIELDS = [
    "stem",
    "group_id",
    "split",
    "rotation",
    "source_image_path",
    "source_image_sha256",
    "source_label_path",
    "source_label_sha256",
    "source_width",
    "source_height",
    "derived_image_path",
    "derived_image_sha256",
    "derived_label_path",
    "derived_label_sha256",
    "derived_width",
    "derived_height",
    "box_count",
    "raw_immutable",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def csv_bytes(fields: list[str], rows: list[dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or path.lstat().st_nlink != 1:
            raise RuntimeError(f"pinned source is missing or not a regular file: {relative}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"pinned source hash differs: {relative}: {actual}")


def _strict_float(token: str, context: str) -> float:
    try:
        value = float(token)
    except ValueError as error:
        raise RuntimeError(f"invalid YOLO number in {context}") from error
    if not 0.0 <= value <= 1.0:
        raise RuntimeError(f"YOLO value outside [0,1] in {context}")
    return value


def parse_label(payload: bytes, context: str) -> list[tuple[int, float, float, float, float]]:
    text = payload.decode("utf-8")
    boxes = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        fields = line.split()
        if len(fields) != 5:
            raise RuntimeError(f"invalid YOLO row in {context}:{line_number}")
        try:
            class_id = int(fields[0])
        except ValueError as error:
            raise RuntimeError(f"invalid YOLO class in {context}:{line_number}") from error
        if class_id < 0:
            raise RuntimeError(f"negative YOLO class in {context}:{line_number}")
        x, y, width, height = (
            _strict_float(token, f"{context}:{line_number}") for token in fields[1:]
        )
        if width <= 0.0 or height <= 0.0:
            raise RuntimeError(f"non-positive YOLO size in {context}:{line_number}")
        if x - width / 2 < 0 or y - height / 2 < 0 or x + width / 2 > 1 or y + height / 2 > 1:
            raise RuntimeError(f"YOLO box escapes image in {context}:{line_number}")
        boxes.append((class_id, x, y, width, height))
    return boxes


def rotate_box_ccw90(
    box: tuple[int, float, float, float, float],
) -> tuple[int, float, float, float, float]:
    """Transform normalized YOLO geometry for a 90-degree counter-clockwise rotation."""

    class_id, x, y, width, height = box
    return class_id, y, 1.0 - x, height, width


def label_bytes(boxes: list[tuple[int, float, float, float, float]]) -> bytes:
    lines = [
        f"{class_id} {x:.6f} {y:.6f} {width:.6f} {height:.6f}"
        for class_id, x, y, width, height in boxes
    ]
    return (("\n".join(lines) + "\n") if lines else "").encode("utf-8")


def png_bytes(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, format="PNG", compress_level=9, optimize=False)
    return output.getvalue()


def discover_stems(repo_root: Path) -> tuple[str, ...]:
    group_rows = {
        row["stem"]: row
        for row in csv_rows(repo_root / "docs/review/generated/wp31_r2_group_id_frames.csv")
    }
    split_rows = {
        row["stem"]: row
        for row in csv_rows(repo_root / "docs/review/generated/wp36_r1_split_frames.csv")
    }
    size_rows = {
        row["stem"]: row
        for row in csv_rows(repo_root / "docs/review/generated/wp37_r1_decode_sizes.csv")
    }
    stems = tuple(
        sorted(
            stem
            for stem, row in group_rows.items()
            if row["capture_group_id"] == GROUP_ID
        )
    )
    if stems != EXPECTED_STEMS:
        raise RuntimeError("WP38 source roster differs from exact D02-C0034 stems 1319..1357")
    for stem in stems:
        split = split_rows.get(stem)
        size = size_rows.get(stem)
        if split is None or split != {
            "stem": stem,
            "group_id": GROUP_ID,
            "split": "val",
            "use": "VAL",
        }:
            raise RuntimeError(f"WP38 source split binding differs: {stem}")
        if size is None or (
            size["resolution"], size["decode_width"], size["decode_height"]
        ) != ("540x960", "540", "960"):
            raise RuntimeError(f"WP38 source orientation binding differs: {stem}")
    return stems


def _source_paths(repo_root: Path, raw_root: Path, stem: str) -> tuple[Path, Path]:
    image = raw_root / "archive/images" / f"{stem}.jpg"
    label = repo_root / "data/processed/m1_yolo/labels/val" / f"{stem}.txt"
    for path in (image, label):
        if not path.is_file() or path.is_symlink() or path.lstat().st_nlink != 1:
            raise RuntimeError(f"WP38 source is missing or unsafe: {path}")
    return image, label


def _preview_pages(
    image_payloads: dict[str, bytes], label_payloads: dict[str, bytes]
) -> dict[Path, bytes]:
    pages: dict[Path, bytes] = {}
    font = ImageFont.load_default()
    per_page = 5
    for page_index, start in enumerate(range(0, len(EXPECTED_STEMS), per_page), start=1):
        stems = EXPECTED_STEMS[start : start + per_page]
        canvas = Image.new("RGB", (520, 40 + len(stems) * 310), "white")
        draw = ImageDraw.Draw(canvas)
        draw.text((12, 12), f"WP38 CCW90 review page {page_index:02d}", fill="black", font=font)
        for offset, stem in enumerate(stems):
            image = Image.open(io.BytesIO(image_payloads[stem])).convert("RGB")
            image.thumbnail((480, 270))
            left, top = 20, 40 + offset * 310 + 22
            canvas.paste(image, (left, top))
            draw.text((left, top - 18), f"stem={stem}", fill="black", font=font)
            boxes = parse_label(label_payloads[stem], f"preview:{stem}")
            for class_id, x, y, width, height in boxes:
                x0 = left + (x - width / 2) * image.width
                y0 = top + (y - height / 2) * image.height
                x1 = left + (x + width / 2) * image.width
                y1 = top + (y + height / 2) * image.height
                draw.rectangle((x0, y0, x1, y1), outline=(255, 0, 0), width=3)
                draw.text((x0, max(top, y0 - 11)), str(class_id), fill=(255, 255, 0), font=font)
        pages[PREVIEW_DIR / f"page_{page_index:02d}.png"] = png_bytes(canvas)
    return pages


def render(repo_root: Path, raw_root: Path) -> dict[Path, bytes]:
    verify_pins(repo_root)
    stems = discover_stems(repo_root)
    artifacts: dict[Path, bytes] = {}
    image_payloads: dict[str, bytes] = {}
    label_payloads: dict[str, bytes] = {}
    source_records: dict[str, dict[str, Any]] = {}
    all_class_ids: set[int] = set()
    total_boxes = 0

    for stem in stems:
        source_image, source_label = _source_paths(repo_root, raw_root, stem)
        image_bytes = source_image.read_bytes()
        source_label_bytes = source_label.read_bytes()
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.load()
            if image.size != EXPECTED_SOURCE_SIZE:
                raise RuntimeError(f"WP38 source image size differs: {stem}: {image.size}")
            rotated = image.convert("RGB").transpose(Image.Transpose.ROTATE_90)
        if rotated.size != EXPECTED_DERIVED_SIZE:
            raise RuntimeError(f"WP38 derived image size differs: {stem}: {rotated.size}")
        boxes = parse_label(source_label_bytes, str(source_label))
        transformed = [rotate_box_ccw90(box) for box in boxes]
        for original, derived in zip(boxes, transformed, strict=True):
            if abs(original[3] * original[4] - derived[3] * derived[4]) > 1e-12:
                raise RuntimeError(f"WP38 box area changed: {stem}")
            all_class_ids.add(derived[0])
        total_boxes += len(transformed)
        image_payloads[stem] = png_bytes(rotated)
        label_payloads[stem] = label_bytes(transformed)
        image_relative = IMAGES_DIR / f"{stem}.png"
        label_relative = LABELS_DIR / f"{stem}.txt"
        artifacts[image_relative] = image_payloads[stem]
        artifacts[label_relative] = label_payloads[stem]
        source_records[stem] = {
            "source_image_path": str(source_image.relative_to(repo_root)),
            "source_image_sha256": sha256_bytes(image_bytes),
            "source_label_path": str(source_label.relative_to(repo_root)),
            "source_label_sha256": sha256_bytes(source_label_bytes),
            "derived_image_path": str(image_relative),
            "derived_label_path": str(label_relative),
        }

    if total_boxes != EXPECTED_BOX_COUNT or all_class_ids != EXPECTED_YOLO_IDS:
        raise RuntimeError(
            f"WP38 label roster differs: boxes={total_boxes}, classes={sorted(all_class_ids)}"
        )

    artifacts.update(_preview_pages(image_payloads, label_payloads))
    lineage = []
    for stem in stems:
        record = source_records[stem]
        image_relative = Path(record["derived_image_path"])
        label_relative = Path(record["derived_label_path"])
        lineage.append(
            {
                "stem": stem,
                "group_id": GROUP_ID,
                "split": "val",
                "rotation": ROTATION,
                **record,
                "source_width": EXPECTED_SOURCE_SIZE[0],
                "source_height": EXPECTED_SOURCE_SIZE[1],
                "derived_image_sha256": sha256_bytes(artifacts[image_relative]),
                "derived_label_sha256": sha256_bytes(artifacts[label_relative]),
                "derived_width": EXPECTED_DERIVED_SIZE[0],
                "derived_height": EXPECTED_DERIVED_SIZE[1],
                "box_count": len(parse_label(artifacts[label_relative], stem)),
                "raw_immutable": "true",
            }
        )
    artifacts[LINEAGE_PATH] = csv_bytes(LINEAGE_FIELDS, lineage)

    roster = [
        {
            "path": str(path),
            "sha256": sha256_bytes(payload),
            "size": len(payload),
        }
        for path, payload in sorted(artifacts.items(), key=lambda item: str(item[0]))
    ]
    source_image_binding = sha256_bytes(
        "\n".join(
            f"{stem}:{source_records[stem]['source_image_sha256']}" for stem in stems
        ).encode("utf-8")
    )
    source_label_binding = sha256_bytes(
        "\n".join(
            f"{stem}:{source_records[stem]['source_label_sha256']}" for stem in stems
        ).encode("utf-8")
    )
    manifest = {
        "schema_version": 1,
        "package": PACKAGE,
        "status": STATUS,
        "boundary": BOUNDARY,
        "group_id": GROUP_ID,
        "split": "val",
        "rotation": ROTATION,
        "source_size": list(EXPECTED_SOURCE_SIZE),
        "derived_size": list(EXPECTED_DERIVED_SIZE),
        "stems": list(stems),
        "frame_count": len(stems),
        "box_count": total_boxes,
        "yolo_class_ids": sorted(all_class_ids),
        "source_image_binding_sha256": source_image_binding,
        "source_label_binding_sha256": source_label_binding,
        "builder_path": str(BUILDER_PATH),
        "builder_sha256": sha256_file(repo_root / BUILDER_PATH),
        "pinned_sources": PINNED_SOURCES,
        "artifacts": roster,
        "artifact_count": len(roster),
        "raw_mutated": False,
        "sealed_test_accessed": False,
        "training_authorized": False,
        "note": (
            "Candidate derived correction. Use by an evaluator or dataset export requires "
            "independent QA and a separate owner-approved successor contract."
        ),
    }
    artifacts[MANIFEST_PATH] = (
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    return artifacts


def _assert_safe_target(repo_root: Path, relative: Path) -> None:
    target = repo_root / relative
    current = repo_root
    for part in relative.parts[:-1]:
        current = current / part
        if current.exists():
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                raise RuntimeError(f"unsafe WP38 output ancestor: {current}")
    if target.exists() or target.is_symlink():
        info = target.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RuntimeError(f"unsafe existing WP38 output: {target}")


def _write_atomic(repo_root: Path, relative: Path, payload: bytes) -> None:
    _assert_safe_target(repo_root, relative)
    target = repo_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(f".{target.name}.wp38.partial")
    if partial.exists() or partial.is_symlink():
        raise RuntimeError(f"unsafe WP38 partial output already exists: {partial}")
    with partial.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(partial, target)


def _actual_roster(repo_root: Path) -> set[Path]:
    paths: set[Path] = set()
    for root in (repo_root / PACKAGE_ROOT, repo_root / PREVIEW_DIR):
        if root.exists():
            if root.is_symlink() or not root.is_dir():
                raise RuntimeError(f"unsafe WP38 output root: {root}")
            for path in root.rglob("*"):
                if path.is_symlink():
                    raise RuntimeError(f"WP38 output contains symlink: {path}")
                if path.is_file():
                    if path.lstat().st_nlink != 1:
                        raise RuntimeError(f"WP38 output contains hardlink: {path}")
                    paths.add(path.relative_to(repo_root))
    for relative in (LINEAGE_PATH, MANIFEST_PATH):
        path = repo_root / relative
        if path.exists() or path.is_symlink():
            if path.is_symlink() or not path.is_file() or path.lstat().st_nlink != 1:
                raise RuntimeError(f"unsafe WP38 control artifact: {path}")
            paths.add(relative)
    return paths


def verify(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    expected = render(repo_root, raw_root)
    actual_roster = _actual_roster(repo_root)
    expected_roster = set(expected)
    missing = sorted(str(path) for path in expected_roster - actual_roster)
    extra = sorted(str(path) for path in actual_roster - expected_roster)
    mismatches = []
    for relative, payload in expected.items():
        path = repo_root / relative
        if path.is_file() and sha256_file(path) != sha256_bytes(payload):
            mismatches.append(str(relative))
    errors = []
    if missing:
        errors.append(f"missing artifacts: {missing}")
    if extra:
        errors.append(f"unexpected artifacts: {extra}")
    if mismatches:
        errors.append(f"byte mismatches: {mismatches}")
    return {
        "valid": not errors,
        "errors": errors,
        "package": PACKAGE,
        "status": STATUS,
        "frame_count": len(EXPECTED_STEMS),
        "box_count": EXPECTED_BOX_COUNT,
        "rotation": ROTATION,
        "raw_mutated": False,
        "sealed_test_accessed": False,
        "training_authorized": False,
        "manifest": str(MANIFEST_PATH),
    }


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    before = {
        stem: sha256_file(_source_paths(repo_root, raw_root, stem)[0])
        for stem in discover_stems(repo_root)
    }
    artifacts = render(repo_root, raw_root)
    existing = _actual_roster(repo_root)
    unexpected = existing - set(artifacts)
    if unexpected:
        raise RuntimeError(
            f"refusing to overwrite package with unexpected files: {sorted(unexpected)}"
        )
    for relative, payload in sorted(artifacts.items(), key=lambda item: item[0] == MANIFEST_PATH):
        _write_atomic(repo_root, relative, payload)
    after = {
        stem: sha256_file(_source_paths(repo_root, raw_root, stem)[0])
        for stem in discover_stems(repo_root)
    }
    if before != after:
        raise RuntimeError("raw WP38 source images changed during build")
    result = verify(repo_root, raw_root)
    if not result["valid"]:
        raise RuntimeError(f"WP38 post-build verification failed: {result['errors']}")
    return result


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("action", choices=("build", "verify"))
    command.add_argument("--repo-root", default=".")
    command.add_argument(
        "--raw-root",
        default="data/raw/DATASET01/staging/052bc980a7206f8d/raw",
    )
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    raw_root = Path(args.raw_root)
    if not raw_root.is_absolute():
        raw_root = repo_root / raw_root
    try:
        result = (
            build(repo_root, raw_root)
            if args.action == "build"
            else verify(repo_root, raw_root)
        )
    except (OSError, RuntimeError, ValueError) as error:
        print(
            json.dumps({"valid": False, "errors": [str(error)]}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
