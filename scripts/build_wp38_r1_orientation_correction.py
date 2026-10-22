#!/usr/bin/env python3
"""Build and verify WP38-R1 with independently anchored image and label sources."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
import stat
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

PACKAGE = "M0-WP38-R1"
STATUS = "WP38_R1_AWAITING_INDEPENDENT_QA"
BOUNDARY = (
    "DERIVED_ORIENTATION_CORRECTION_ONLY_RAW_IMMUTABLE_VAL_ONLY_"
    "SOURCE_AUTHORITY_PINNED_NO_SPLIT_CHANGE_NO_TRAINING_AUTHORIZATION_"
    "NO_SEALED_TEST_ACCESS"
)
BUILDER_PATH = Path("scripts/build_wp38_r1_orientation_correction.py")
BASE_BUILDER_PATH = Path("scripts/build_wp38_orientation_correction.py")
RAW_ROOT_RELATIVE = Path("data/raw/DATASET01/staging/052bc980a7206f8d/raw")
IMAGE_INVENTORY = Path(
    "results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv"
)
TAXONOMY = Path("docs/review/generated/wp33_derived_taxonomy.csv")
BOXES = Path("docs/review/generated/wp33_derived_boxes.csv")
SPLIT_FRAMES = Path("docs/review/generated/wp36_r1_split_frames.csv")
DECODE_SIZES = Path("docs/review/generated/wp37_r1_decode_sizes.csv")

PACKAGE_ROOT = Path("data/processed/wp38_r1_orientation_corrected")
IMAGES_DIR = PACKAGE_ROOT / "images"
LABELS_DIR = PACKAGE_ROOT / "labels"
PREVIEW_DIR = Path("docs/review/assets/wp38_r1/orientation_correction")
GENERATED = Path("docs/review/generated")
LINEAGE_PATH = GENERATED / "wp38_r1_orientation_correction_lineage.csv"
MANIFEST_PATH = GENERATED / "wp38_r1_orientation_correction_manifest.json"

PINNED_SOURCES = {
    str(BASE_BUILDER_PATH): "c3b2726241b53be23a9e1b233d38b5dad3994d2f6fc073beabef82f6bd89c23e",
    str(IMAGE_INVENTORY): "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022",
    str(TAXONOMY): "199ddd322aa05d4875af809c1c7c1459198ebf91ada24f406cbf039c406fa5ad",
    str(BOXES): "4b9307003ce8fd3c1d50763a5950d3d57cf6b2ee6df3aeef74621707067501c0",
    str(SPLIT_FRAMES): "8e197d9c7103ac5dc6b7ffc8a3d1aeb30bb6034048d470e4887dd868df95823a",
    str(DECODE_SIZES): "5bcba8a4c58e9e5e063d6a70962f79bcc45bf56d44afd023dce7a8ef3ab2c969",
    "docs/review/generated/m1_yolo_export_manifest.json": (
        "8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71"
    ),
    "data/processed/m1_yolo/data.yaml": (
        "4cd8303540ecf7bf8ce461b440a07ae35b5ffb047348613c3cdbc8d9c1d78bd0"
    ),
}


def _load_base() -> Any:
    path = Path(__file__).with_name("build_wp38_orientation_correction.py")
    spec = importlib.util.spec_from_file_location("wp38_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load pinned WP38 base builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = _load_base()
EXPECTED_STEMS = BASE.EXPECTED_STEMS


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def csv_bytes(fields: list[str], rows: list[dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _require_safe_path(repo_root: Path, path: Path, *, directory: bool) -> Path:
    repo = _absolute_lexical(repo_root)
    candidate = _absolute_lexical(path)
    try:
        relative = candidate.relative_to(repo)
    except ValueError as error:
        raise RuntimeError(f"source escapes repository: {candidate}") from error
    current = repo
    if current.is_symlink() or not current.is_dir():
        raise RuntimeError(f"unsafe repository root: {current}")
    for part in relative.parts:
        current = current / part
        if not os.path.lexists(current):
            raise RuntimeError(f"source path is missing: {current}")
        info = current.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise RuntimeError(f"source path has symlink component: {current}")
    info = candidate.lstat()
    if directory:
        if not stat.S_ISDIR(info.st_mode):
            raise RuntimeError(f"source is not a directory: {candidate}")
    elif not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"source is not a regular file: {candidate}")
    return candidate


def canonical_raw_root(repo_root: Path, raw_root: Path) -> Path:
    expected = _absolute_lexical(repo_root / RAW_ROOT_RELATIVE)
    actual = _absolute_lexical(raw_root)
    if actual != expected:
        raise RuntimeError(f"raw root is not canonical: {actual}")
    return _require_safe_path(repo_root, actual, directory=True)


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        path = _require_safe_path(repo_root, repo_root / relative, directory=False)
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"pinned source hash differs: {relative}: {actual}")


def expected_materialized_labels(repo_root: Path) -> dict[str, bytes]:
    classes = [row for row in read_csv(repo_root / TAXONOMY) if row["role"] == "CLASS"]
    if len(classes) != 54:
        raise RuntimeError("WP33 taxonomy no longer has exactly 54 trainable classes")
    class_ids = {row["derived_key"]: index for index, row in enumerate(classes)}
    by_stem: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(repo_root / BOXES):
        if row["train_eligible"] == "True":
            by_stem[row["stem"]].append(row)
    labels: dict[str, bytes] = {}
    for stem in EXPECTED_STEMS:
        lines = [
            f"{class_ids[row['derived_key']]} {row['x']} {row['y']} {row['w']} {row['h']}"
            for row in sorted(by_stem.get(stem, []), key=lambda item: int(item["line"]))
        ]
        labels[stem] = ("".join(f"{line}\n" for line in lines)).encode("utf-8")
    return labels


def verify_exact_sources(repo_root: Path, raw_root: Path) -> dict[str, dict[str, str]]:
    verify_pins(repo_root)
    raw_root = canonical_raw_root(repo_root, raw_root)
    inventory_rows = read_csv(repo_root / IMAGE_INVENTORY)
    inventory = {row["stem"]: row for row in inventory_rows}
    expected_labels = expected_materialized_labels(repo_root)
    records: dict[str, dict[str, str]] = {}
    for stem in EXPECTED_STEMS:
        row = inventory.get(stem)
        if row is None:
            raise RuntimeError(f"image authority is missing stem: {stem}")
        if (row["image_path"], row["width"], row["height"]) != (
            f"archive/images/{stem}.jpg",
            "540",
            "960",
        ):
            raise RuntimeError(f"image authority metadata differs: {stem}")
        image_path = _require_safe_path(
            repo_root, raw_root / row["image_path"], directory=False
        )
        image_hash = sha256_file(image_path)
        if image_hash != row["image_sha256"]:
            raise RuntimeError(f"raw image hash mismatch against authority: {stem}")
        label_path = _require_safe_path(
            repo_root,
            repo_root / "data/processed/m1_yolo/labels/val" / f"{stem}.txt",
            directory=False,
        )
        label_payload = label_path.read_bytes()
        if label_payload != expected_labels[stem]:
            raise RuntimeError(f"materialized val label differs from WP33 rules: {stem}")
        records[stem] = {
            "source_image_path": str(image_path.relative_to(repo_root)),
            "source_image_sha256": image_hash,
            "source_label_path": str(label_path.relative_to(repo_root)),
            "source_label_sha256": sha256_bytes(label_payload),
        }
    return records


def _preview_pages(
    image_payloads: dict[str, bytes], label_payloads: dict[str, bytes]
) -> dict[Path, bytes]:
    pages: dict[Path, bytes] = {}
    font = ImageFont.load_default()
    for page_index, start in enumerate(range(0, len(EXPECTED_STEMS), 5), start=1):
        stems = EXPECTED_STEMS[start : start + 5]
        canvas = Image.new("RGB", (520, 40 + len(stems) * 310), "white")
        draw = ImageDraw.Draw(canvas)
        draw.text((12, 12), f"WP38-R1 CCW90 review page {page_index:02d}", fill="black", font=font)
        for offset, stem in enumerate(stems):
            image = Image.open(io.BytesIO(image_payloads[stem])).convert("RGB")
            image.thumbnail((480, 270))
            left, top = 20, 62 + offset * 310
            canvas.paste(image, (left, top))
            draw.text((left, top - 18), f"stem={stem}", fill="black", font=font)
            for class_id, x, y, width, height in BASE.parse_label(
                label_payloads[stem], f"preview:{stem}"
            ):
                x0, y0 = left + (x - width / 2) * image.width, top + (y - height / 2) * image.height
                x1, y1 = left + (x + width / 2) * image.width, top + (y + height / 2) * image.height
                draw.rectangle((x0, y0, x1, y1), outline=(255, 0, 0), width=3)
                draw.text((x0, max(top, y0 - 11)), str(class_id), fill=(255, 255, 0), font=font)
        buffer = io.BytesIO()
        canvas.save(buffer, format="PNG", compress_level=9, optimize=False)
        pages[PREVIEW_DIR / f"page_{page_index:02d}.png"] = buffer.getvalue()
    return pages


def render(repo_root: Path, raw_root: Path) -> dict[Path, bytes]:
    source_records = verify_exact_sources(repo_root, raw_root)
    base_artifacts = BASE.render(repo_root, canonical_raw_root(repo_root, raw_root))
    artifacts: dict[Path, bytes] = {}
    images: dict[str, bytes] = {}
    labels: dict[str, bytes] = {}
    lineage = []
    for stem in EXPECTED_STEMS:
        images[stem] = base_artifacts[BASE.IMAGES_DIR / f"{stem}.png"]
        labels[stem] = base_artifacts[BASE.LABELS_DIR / f"{stem}.txt"]
        image_path = IMAGES_DIR / f"{stem}.png"
        label_path = LABELS_DIR / f"{stem}.txt"
        artifacts[image_path] = images[stem]
        artifacts[label_path] = labels[stem]
        record = source_records[stem]
        lineage.append(
            {
                "stem": stem,
                "group_id": BASE.GROUP_ID,
                "split": "val",
                "rotation": BASE.ROTATION,
                **record,
                "source_width": BASE.EXPECTED_SOURCE_SIZE[0],
                "source_height": BASE.EXPECTED_SOURCE_SIZE[1],
                "derived_image_path": str(image_path),
                "derived_image_sha256": sha256_bytes(images[stem]),
                "derived_label_path": str(label_path),
                "derived_label_sha256": sha256_bytes(labels[stem]),
                "derived_width": BASE.EXPECTED_DERIVED_SIZE[0],
                "derived_height": BASE.EXPECTED_DERIVED_SIZE[1],
                "box_count": len(BASE.parse_label(labels[stem], stem)),
                "raw_immutable": "true",
            }
        )
    artifacts.update(_preview_pages(images, labels))
    artifacts[LINEAGE_PATH] = csv_bytes(BASE.LINEAGE_FIELDS, lineage)
    roster = [
        {"path": str(path), "sha256": sha256_bytes(payload), "size": len(payload)}
        for path, payload in sorted(artifacts.items(), key=lambda item: str(item[0]))
    ]
    manifest = {
        "schema_version": 1,
        "package": PACKAGE,
        "status": STATUS,
        "boundary": BOUNDARY,
        "group_id": BASE.GROUP_ID,
        "split": "val",
        "rotation": BASE.ROTATION,
        "source_size": list(BASE.EXPECTED_SOURCE_SIZE),
        "derived_size": list(BASE.EXPECTED_DERIVED_SIZE),
        "stems": list(EXPECTED_STEMS),
        "frame_count": len(EXPECTED_STEMS),
        "box_count": BASE.EXPECTED_BOX_COUNT,
        "yolo_class_ids": sorted(BASE.EXPECTED_YOLO_IDS),
        "source_authority": str(IMAGE_INVENTORY),
        "source_authority_sha256": PINNED_SOURCES[str(IMAGE_INVENTORY)],
        "label_authority": str(BOXES),
        "label_authority_sha256": PINNED_SOURCES[str(BOXES)],
        "taxonomy_authority": str(TAXONOMY),
        "taxonomy_authority_sha256": PINNED_SOURCES[str(TAXONOMY)],
        "builder_path": str(BUILDER_PATH),
        "builder_sha256": sha256_file(repo_root / BUILDER_PATH),
        "base_builder_path": str(BASE_BUILDER_PATH),
        "base_builder_sha256": PINNED_SOURCES[str(BASE_BUILDER_PATH)],
        "pinned_sources": PINNED_SOURCES,
        "artifacts": roster,
        "artifact_count": len(roster),
        "raw_mutated": False,
        "sealed_test_accessed": False,
        "training_authorized": False,
        "note": "Append-only QA remediation; candidate evidence only until independent QA PASS.",
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
                raise RuntimeError(f"unsafe WP38-R1 output ancestor: {current}")
    if target.exists() or target.is_symlink():
        info = target.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RuntimeError(f"unsafe existing WP38-R1 output: {target}")


def _write_atomic(repo_root: Path, relative: Path, payload: bytes) -> None:
    _assert_safe_target(repo_root, relative)
    target = repo_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(f".{target.name}.wp38-r1.partial")
    if partial.exists() or partial.is_symlink():
        raise RuntimeError(f"unsafe WP38-R1 partial exists: {partial}")
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
                raise RuntimeError(f"unsafe WP38-R1 output root: {root}")
            for path in root.rglob("*"):
                if path.is_symlink():
                    raise RuntimeError(f"WP38-R1 output contains symlink: {path}")
                if path.is_file():
                    if path.lstat().st_nlink != 1:
                        raise RuntimeError(f"WP38-R1 output contains hardlink: {path}")
                    paths.add(path.relative_to(repo_root))
    for relative in (LINEAGE_PATH, MANIFEST_PATH):
        path = repo_root / relative
        if path.exists() or path.is_symlink():
            if path.is_symlink() or not path.is_file() or path.lstat().st_nlink != 1:
                raise RuntimeError(f"unsafe WP38-R1 control artifact: {path}")
            paths.add(relative)
    return paths


def verify(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    expected = render(repo_root, raw_root)
    actual = _actual_roster(repo_root)
    missing = sorted(str(path) for path in set(expected) - actual)
    extra = sorted(str(path) for path in actual - set(expected))
    mismatches = [
        str(relative)
        for relative, payload in expected.items()
        if (repo_root / relative).is_file()
        and sha256_file(repo_root / relative) != sha256_bytes(payload)
    ]
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
        "box_count": BASE.EXPECTED_BOX_COUNT,
        "rotation": BASE.ROTATION,
        "raw_mutated": False,
        "sealed_test_accessed": False,
        "training_authorized": False,
        "manifest": str(MANIFEST_PATH),
    }


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    source_records = verify_exact_sources(repo_root, raw_root)
    before = {stem: record["source_image_sha256"] for stem, record in source_records.items()}
    artifacts = render(repo_root, raw_root)
    unexpected = _actual_roster(repo_root) - set(artifacts)
    if unexpected:
        raise RuntimeError(f"refusing unexpected WP38-R1 files: {sorted(unexpected)}")
    for relative, payload in sorted(artifacts.items(), key=lambda item: item[0] == MANIFEST_PATH):
        _write_atomic(repo_root, relative, payload)
    after = {
        stem: record["source_image_sha256"]
        for stem, record in verify_exact_sources(repo_root, raw_root).items()
    }
    if before != after:
        raise RuntimeError("raw WP38-R1 sources changed during build")
    result = verify(repo_root, raw_root)
    if not result["valid"]:
        raise RuntimeError(f"WP38-R1 post-build verification failed: {result['errors']}")
    return result


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("action", choices=("build", "verify"))
    command.add_argument("--repo-root", default=".")
    command.add_argument("--raw-root", default=str(RAW_ROOT_RELATIVE))
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = _absolute_lexical(Path(args.repo_root))
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
