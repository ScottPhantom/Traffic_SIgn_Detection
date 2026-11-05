"""D1-A2-R1: deterministic A2 repeat-factor train list (train split only, no training).

Contract: `docs/review/d1_a2_r1_run_contract.md`. Binding spec: the A2 row of
`docs/review/d1_yolo54_improvement_r3_contract.md` §5 (SHA-256 `3382de28…`). A2 changes exactly
one thing from the pilot: every train image whose exported label holds derived-key class 7, 32 or
41 is listed twice in the train list. No new pixels, no validation data, no test data.

Derived keys are not YOLO ids. The R3 class map translates them: derived key 7 is yolo_id 7,
derived key 32 is yolo_id 33 and derived key 41 is yolo_id 42. The repeat keys are taken from the
QA-passed R3 module (`A2_REPEAT_KEYS`, a subset of `FOCUS_KEYS`) and translated through the pinned
class map; the translation is checked against `EXPECTED_YOLO_IDS`.

Commands (from `detector/`)::

    uv run python -m m1.a2_repeat_list_r1 build    # write-once list + manifest
    uv run python -m m1.a2_repeat_list_r1 verify   # recompute and byte-compare

The list and manifest go to the Git-ignored `data/processed/d1_a2_r1/`. Every list line is
relative to the M1 export root (`images/train/<stem>.jpg`), so the list hash is machine-independent.
The trainer (`m1.resumable_train_a2_r1`) materialises a runtime copy with absolute paths and a data
YAML that differs from the pilot `data.yaml` only in its `train:` line.

Inputs come only from the pinned M1 export (manifest `8a8df5f2…`) and the authorities that manifest
pins (class map, WP35 lineage, WP36-R1 split frames, raw image inventory). The module refuses:

- an export manifest, class map, lineage, split-frame or inventory file whose SHA-256 differs;
- any list entry outside `images/train/`, any `val` component and any component containing `test`;
- a raw stem that is not a WP36-R1 `train` frame, and a WP35 image whose source frame is not train;
- symlinks in the input chain other than the export's own image links, and an image link whose
  target escapes the governed raw/WP35 image roots or differs from the exact governed source;
- train image bytes that differ from the inventory/lineage hashes;
- an existing output (write-once; `O_CREAT | O_EXCL | O_NOFOLLOW`).
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
from collections import Counter
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from m1 import contract
from m1 import yolo54_improvement_r3 as r3

PACKAGE = "D1-A2-R1-REPEAT-LIST"
SCHEMA = "d1-a2-r1-repeat-list-v1"
STATUS = "A2_TRAIN_LIST_DERIVED_NO_TRAINING"
RULE_ID = "A2_ALL_975_RAW_AND_WP35"
RULE = (
    "every train image (raw WP36-R1 frame or WP35 train-only image) whose exported label holds "
    "derived-key class 7, 32 or 41 is listed 2x; every other train image once; no new pixels"
)

REPEAT_KEYS: tuple[str, ...] = tuple(r3.A2_REPEAT_KEYS)
REPEAT_FACTOR: int = r3.A2_REPEAT_FACTOR
# Derived key -> YOLO id, as the pinned class map must translate it (R3 hazard: 32->33, 41->42).
EXPECTED_YOLO_IDS = {"7": 7, "32": 33, "41": 42}
if not set(REPEAT_KEYS) <= set(r3.FOCUS_KEYS) or set(REPEAT_KEYS) != set(EXPECTED_YOLO_IDS):
    raise RuntimeError("A2 repeat keys differ from the R3 focus-key subset")
if REPEAT_FACTOR != 2:
    raise RuntimeError("A2 repeat factor differs from the frozen R3 value 2")

LIST_NAME = "a2_train_list.txt"
MANIFEST_NAME = "a2_train_list_manifest.json"
RUNTIME_DIR = "runtime"
RUNTIME_YAML = "a2_data.yaml"
RUNTIME_LIST = "a2_train_list_runtime.txt"
LIST_PREFIX = "images/train/"
R3_MODULE_SHA256 = "548144b107714d95427b1704700a2ff8cd879143d8f2366e931afecf6777a639"
# Computed by this module from the pinned export on 2026-11-05 (see the run contract).
A2_TRAIN_LIST_SHA256 = "90d735d67bde2bf736b5fc8570110561f0184747f3fb25c8f42a3a599d0fdec2"


@dataclass(frozen=True)
class Spec:
    """Every expected input and output; the default is the frozen R3 §5 A2 specification."""

    export_dir: Path = Path("data/processed/m1_yolo")
    out_dir: Path = Path("data/processed/d1_a2_r1")
    export_manifest: Path = r3.EXPORT_MANIFEST
    export_manifest_sha256: str = r3.PINNED[r3.EXPORT_MANIFEST]
    class_map: Path = r3.CLASS_MAP
    class_map_sha256: str = r3.PINNED[r3.CLASS_MAP]
    lineage: Path = r3.WP35_LINEAGE
    lineage_sha256: str = r3.PINNED[r3.WP35_LINEAGE]
    split_frames: Path = r3.SPLIT_FRAMES
    split_frames_sha256: str = r3.PINNED[r3.SPLIT_FRAMES]
    inventory: Path = Path("results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
    inventory_sha256: str = "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022"
    wp35_source_labels: Path = r3.WP35_SOURCE_LABELS
    raw_image_root: Path = Path("data/raw/DATASET01/staging/052bc980a7206f8d/raw/archive/images")
    wp35_image_root: Path = Path("data/processed/wp35_enrichment/images")
    train_stem_list_sha256: str = r3.TRAIN_STEM_LIST_SHA256
    train_labels_sha256: str = r3.TRAIN_LABELS_SHA256
    classes: int = r3.CLASSES
    train_images: int = 3712
    raw_train_frames: int = r3.TRAIN_FRAMES
    wp35_images: int = r3.WP35_IMAGES
    repeated_images: int = 975
    repeated_raw_frames: int = 339
    repeated_wp35_images: int = 636
    train_list_entries: int = 4687
    train_boxes_per_class: dict[str, dict[str, int]] = field(
        default_factory=lambda: {
            "7": {"raw": 83, "wp35": 145},
            "32": {"raw": 86, "wp35": 52},
            "41": {"raw": 171, "wp35": 439},
        }
    )
    repeated_roster_sha256: str = "0ce6afdc84ffab0db361920c4c7817517353fd8b1b901e51770d2f3f4eb69aa3"
    train_list_sha256: str = A2_TRAIN_LIST_SHA256
    yolo_ids: dict[str, int] = field(default_factory=lambda: dict(EXPECTED_YOLO_IDS))
    r3_module_sha256: str | None = R3_MODULE_SHA256
    r3_cross_check: bool = True


SPEC = Spec()


# ------------------------------------------------------------------------------------- helpers


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _strict_json_bytes(payload: bytes, label: str) -> Any:
    def reject_constant(value: str) -> None:
        raise RuntimeError(f"{label} contains non-finite JSON constant {value}")

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise RuntimeError(f"{label} contains duplicate key {key}")
            result[key] = value
        return result

    return json.loads(
        payload.decode("utf-8"), object_pairs_hook=unique, parse_constant=reject_constant
    )


def _read_pinned(root: Path, relative: Path, expected: str) -> bytes:
    data = r3.guard(root, relative).read_bytes()
    if sha256_bytes(data) != expected:
        raise RuntimeError(f"pinned input differs: {relative}")
    return data


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def refuse_non_train_entry(line: str) -> None:
    """Refuse anything but `images/train/<name>.jpg` (no val, no test, no escape)."""
    parts = line.split("/")
    if (
        not line.startswith(LIST_PREFIX)
        or len(parts) != 3
        or not parts[2].endswith(".jpg")
        or parts[2] in {".jpg", "..jpg"}
        or any(part in {"", ".", ".."} for part in parts)
        or any(part.lower() == "val" or "test" in part.lower() for part in parts)
        or "\\" in line
    ):
        raise RuntimeError(f"refused non-train list entry: {line!r}")


def _yolo_ids(root: Path, spec: Spec) -> dict[str, int]:
    rows = _csv_rows(_read_pinned(root, spec.class_map, spec.class_map_sha256))
    names = [""] * len(rows)
    for row in rows:
        index = int(row["yolo_id"])
        if not 0 <= index < len(rows) or names[index]:
            raise RuntimeError("class map yolo ids are not a dense unique range")
        names[index] = row["derived_key"]
    if len(names) != spec.classes or "" in names or len(set(names)) != spec.classes:
        raise RuntimeError("class map is not a dense unique YOLO range")
    ids = {key: index for index, key in enumerate(names)}
    translated = {key: ids[key] for key in REPEAT_KEYS}
    if translated != spec.yolo_ids:
        raise RuntimeError(f"derived-key/yolo_id translation differs: {translated!r}")
    return ids


def _check_image(
    root: Path, spec: Spec, stem: str, wp35: bool, expected_sha: str, hash_bytes: bool
) -> None:
    relative = spec.export_dir / "images/train" / f"{stem}.jpg"
    link = root / relative
    info = os.lstat(link)
    source_root = (root / (spec.wp35_image_root if wp35 else spec.raw_image_root)).resolve()
    if stat.S_ISLNK(info.st_mode):
        target = link.resolve(strict=True)
        if not target.is_relative_to(source_root) or target != source_root / f"{stem}.jpg":
            raise RuntimeError(f"refused image link escaping its governed source: {relative}")
        if not stat.S_ISREG(os.stat(target).st_mode):
            raise RuntimeError(f"image link target is not a regular file: {relative}")
    elif not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"refused non-regular image entry: {relative}")
    if hash_bytes and contract.sha256_file(link) != expected_sha:
        raise RuntimeError(f"train image bytes differ from the governed hash: {relative}")


# ------------------------------------------------------------------------------------ derive


def derive(root: Path, spec: Spec = SPEC, *, hash_images: bool = True) -> dict[str, Any]:
    """Recompute the A2 list from the pinned export; refuse on any deviation from `spec`."""
    root = root.absolute()
    if spec.r3_module_sha256 is not None:
        if contract.sha256_file(Path(r3.__file__)) != spec.r3_module_sha256:
            raise RuntimeError("imported R3 module differs from the QA-passed pin")
    manifest_bytes = _read_pinned(root, spec.export_manifest, spec.export_manifest_sha256)
    manifest = _strict_json_bytes(manifest_bytes, "export manifest")
    train = manifest["splits"]["train"]
    if (train["stem_list_sha256"], train["labels_sha256"]) != (
        spec.train_stem_list_sha256,
        spec.train_labels_sha256,
    ):
        raise RuntimeError("export manifest train binding differs from the pilot")
    if manifest["class_map_sha256"] != spec.class_map_sha256:
        raise RuntimeError("export manifest class map differs")
    if manifest["wp35_train_only"] != {
        "images": spec.wp35_images,
        "lineage_sha256": spec.lineage_sha256,
    }:
        raise RuntimeError("export manifest WP35 binding differs")
    if manifest["pinned_sources"].get(spec.inventory.as_posix()) != spec.inventory_sha256:
        raise RuntimeError("export manifest does not pin the raw image inventory")

    ids = _yolo_ids(root, spec)
    targets = {spec.yolo_ids[key] for key in REPEAT_KEYS}

    lineage_rows = _csv_rows(_read_pinned(root, spec.lineage, spec.lineage_sha256))
    lineage = {row["augmented_id"]: row for row in lineage_rows}
    if len(lineage) != len(lineage_rows) or len(lineage) != spec.wp35_images:
        raise RuntimeError("WP35 lineage is not the expected unique roster")
    split = {
        row["stem"]: row["split"]
        for row in _csv_rows(_read_pinned(root, spec.split_frames, spec.split_frames_sha256))
    }
    for augmented_id, row in lineage.items():
        if split.get(row["source_stem"]) != "train":
            raise RuntimeError(f"WP35 image does not come from a train frame: {augmented_id}")

    blobs = r3._regular_files(root, spec.export_dir / "labels/train")
    texts = {name[:-4]: data.decode("utf-8") for name, data in blobs.items()}
    raw = {stem: text for stem, text in texts.items() if stem not in lineage}
    if set(texts) - set(raw) != set(lineage):
        raise RuntimeError("exported WP35 train labels differ from the lineage roster")
    for stem in raw:
        if split.get(stem) != "train":
            raise RuntimeError(f"refused non-train raw frame in the train export: {stem}")
    if len(raw) != spec.raw_train_frames or len(texts) != spec.train_images:
        raise RuntimeError("train export roster size differs")
    if sha256_bytes("\n".join(sorted(raw)).encode("utf-8")) != spec.train_stem_list_sha256:
        raise RuntimeError("raw train label roster differs from the export manifest")
    if r3._label_hash(raw) != spec.train_labels_sha256:
        raise RuntimeError("raw train labels differ from the export manifest")
    sources = r3._regular_files(root, spec.wp35_source_labels)
    if set(sources) != {f"{stem}.txt" for stem in lineage}:
        raise RuntimeError("WP35 source label roster differs from the lineage")
    for stem, row in lineage.items():
        source = sources[f"{stem}.txt"]
        if sha256_bytes(source) != row["label_sha256"]:
            raise RuntimeError(f"WP35 source label differs from its lineage: {stem}")
        source_rows = [row.split() for row in source.decode("utf-8").splitlines() if row.strip()]
        if texts[stem] != "".join(f"{ids[r[0]]} {' '.join(r[1:])}\n" for r in source_rows):
            raise RuntimeError(f"exported WP35 label differs from its lineage source: {stem}")

    parsed = {stem: r3._parse_label(stem, text) for stem, text in texts.items()}
    repeated = sorted(stem for stem, rows in parsed.items() if targets & {c for c, _ in rows})
    repeated_set = set(repeated)
    boxes = {
        key: {
            part: sum(
                1
                for stem, rows in parsed.items()
                if (stem in lineage) == (part == "wp35")
                for cls, _ in rows
                if cls == spec.yolo_ids[key]
            )
            for part in ("raw", "wp35")
        }
        for key in REPEAT_KEYS
    }

    image_folder = r3.guard(root, spec.export_dir / "images/train", directory=True)
    names = sorted(entry.name for entry in os.scandir(image_folder))
    if names != sorted(f"{stem}.jpg" for stem in texts):
        raise RuntimeError("exported train image roster differs from the train labels")
    inventory: dict[str, str] = {}
    if hash_images:
        inventory = {
            row["stem"]: row["image_sha256"]
            for row in _csv_rows(_read_pinned(root, spec.inventory, spec.inventory_sha256))
        }
    for stem in sorted(texts):
        wp35 = stem in lineage
        expected = lineage[stem]["image_sha256"] if wp35 else inventory.get(stem, "")
        _check_image(root, spec, stem, wp35, expected, hash_images)

    lines: list[str] = []
    for stem in sorted(texts):
        copies = REPEAT_FACTOR if stem in repeated_set else 1
        lines.extend([f"{LIST_PREFIX}{stem}.jpg"] * copies)
    for line in lines:
        refuse_non_train_entry(line)
    list_bytes = "".join(f"{line}\n" for line in lines).encode("utf-8")

    summary = {
        "train_images": len(texts),
        "raw_train_frames": len(raw),
        "wp35_images": len(lineage),
        "repeated_images": len(repeated),
        "repeated_raw_frames": sum(1 for stem in repeated if stem not in lineage),
        "repeated_wp35_images": sum(1 for stem in repeated if stem in lineage),
        "train_list_entries": len(lines),
        "train_boxes_per_class": boxes,
        "repeated_roster_sha256": sha256_bytes("\n".join(repeated).encode("utf-8")),
        "train_list_sha256": sha256_bytes(list_bytes),
    }
    expected = {
        "train_images": spec.train_images,
        "raw_train_frames": spec.raw_train_frames,
        "wp35_images": spec.wp35_images,
        "repeated_images": spec.repeated_images,
        "repeated_raw_frames": spec.repeated_raw_frames,
        "repeated_wp35_images": spec.repeated_wp35_images,
        "train_list_entries": spec.train_list_entries,
        "train_boxes_per_class": spec.train_boxes_per_class,
        "repeated_roster_sha256": spec.repeated_roster_sha256,
        "train_list_sha256": spec.train_list_sha256,
    }
    differences = sorted(key for key in expected if summary[key] != expected[key])
    if differences:
        detail = {key: (summary[key], expected[key]) for key in differences}
        raise RuntimeError(f"A2 list differs from the frozen specification: {detail!r}")

    r3_check = "SKIPPED_SYNTHETIC_SPEC"
    if spec.r3_cross_check:
        _, r3_ids = r3.class_map(root)
        independent = r3.a2_repeat_roster(root, r3_ids)
        for key in (
            "train_images",
            "raw_train_frames",
            "wp35_images",
            "repeated_images",
            "repeated_raw_frames",
            "repeated_roster_sha256",
            "train_list_entries",
            "train_boxes_per_class",
        ):
            if independent[key] != summary[key]:
                raise RuntimeError(f"A2 list disagrees with the R3 roster on {key}")
        r3_check = "MATCH"

    document = {
        "schema": SCHEMA,
        "package": PACKAGE,
        "status": STATUS,
        "rule_id": RULE_ID,
        "rule": RULE,
        "repeat_derived_keys": list(REPEAT_KEYS),
        "repeat_yolo_ids": dict(spec.yolo_ids),
        "repeat_factor": REPEAT_FACTOR,
        **summary,
        "train_list": LIST_NAME,
        "train_list_line_format": "images/train/<stem>.jpg, relative to the M1 export root",
        "export_dir": spec.export_dir.as_posix(),
        "pins": {
            spec.export_manifest.as_posix(): spec.export_manifest_sha256,
            spec.class_map.as_posix(): spec.class_map_sha256,
            spec.lineage.as_posix(): spec.lineage_sha256,
            spec.split_frames.as_posix(): spec.split_frames_sha256,
            spec.inventory.as_posix(): spec.inventory_sha256,
            "detector/m1/yolo54_improvement_r3.py": spec.r3_module_sha256,
        },
        "r3_roster_cross_check": r3_check,
        "image_bytes_verified": hash_images,
        "validation_used": False,
        "test_included": False,
        "sealed_test_accessed": False,
        "training_authorized": False,
    }
    return {"list_bytes": list_bytes, "lines": lines, "summary": summary, "document": document}


# ------------------------------------------------------------------------------------ output


def _safe_out_dir(root: Path, spec: Spec, *, create: bool) -> Path:
    relative = spec.out_dir
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise RuntimeError(f"refused output directory: {relative}")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeError(f"refused symlink in output chain: {current}")
        if not current.exists():
            if not create:
                raise RuntimeError(f"output directory is missing: {current}")
            current.mkdir()
        elif not current.is_dir():
            raise RuntimeError(f"output path is not a directory: {current}")
    return current


def write_once(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _read_output(path: Path) -> bytes:
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RuntimeError(f"refused non-regular or linked output: {path}")
    return path.read_bytes()


def build(root: Path, spec: Spec = SPEC, *, hash_images: bool = True) -> dict[str, Any]:
    root = root.absolute()
    derived = derive(root, spec, hash_images=hash_images)
    out = _safe_out_dir(root, spec, create=True)
    list_path, manifest_path = out / LIST_NAME, out / MANIFEST_NAME
    if any(os.path.lexists(path) for path in (list_path, manifest_path)):
        raise RuntimeError(f"refused to overwrite an existing A2 list output in {out}")
    write_once(list_path, derived["list_bytes"])
    write_once(manifest_path, r3.canonical(derived["document"]))
    return verify(root, spec, hash_images=hash_images, derived=derived)


def verify(
    root: Path,
    spec: Spec = SPEC,
    *,
    hash_images: bool = True,
    derived: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = root.absolute()
    derived = derived or derive(root, spec, hash_images=hash_images)
    out = _safe_out_dir(root, spec, create=False)
    list_bytes = _read_output(out / LIST_NAME)
    manifest_bytes = _read_output(out / MANIFEST_NAME)
    for line in list_bytes.decode("utf-8").splitlines():
        refuse_non_train_entry(line)
    if list_bytes != derived["list_bytes"]:
        raise RuntimeError("written A2 list differs from the recomputed list")
    if manifest_bytes != r3.canonical(derived["document"]):
        raise RuntimeError("written A2 manifest differs from the recomputed manifest")
    return {
        "status": "A2_TRAIN_LIST_VERIFIED",
        "train_list": str(out / LIST_NAME),
        "train_list_sha256": sha256_bytes(list_bytes),
        "manifest": str(out / MANIFEST_NAME),
        "manifest_sha256": sha256_bytes(manifest_bytes),
        **{key: derived["summary"][key] for key in sorted(derived["summary"])},
        "r3_roster_cross_check": derived["document"]["r3_roster_cross_check"],
        "validation_used": False,
        "test_included": False,
        "sealed_test_accessed": False,
        "training_authorized": False,
    }


def ensure(root: Path, spec: Spec = SPEC, *, hash_images: bool = True) -> dict[str, Any]:
    """Build when absent, verify when present; a partial output is refused."""
    out = root.absolute() / spec.out_dir
    present = [os.path.lexists(out / name) for name in (LIST_NAME, MANIFEST_NAME)]
    if all(present):
        return verify(root, spec, hash_images=hash_images)
    if any(present):
        raise RuntimeError(f"refused partial A2 list output in {out}")
    return build(root, spec, hash_images=hash_images)


def _write_or_match(path: Path, payload: bytes) -> None:
    if os.path.lexists(path):
        if _read_output(path) != payload:
            raise RuntimeError(f"existing runtime file differs; refusing to overwrite: {path}")
        return
    write_once(path, payload)


def materialize_runtime(root: Path, verified: dict[str, Any], spec: Spec = SPEC) -> dict[str, Any]:
    """Runtime list (absolute paths) and data YAML differing from the pilot only in `train:`."""
    root = root.absolute()
    out = _safe_out_dir(root, spec, create=False)
    canonical_bytes = _read_output(out / LIST_NAME)
    if sha256_bytes(canonical_bytes) != verified["train_list_sha256"] or (
        verified["train_list_sha256"] != spec.train_list_sha256
    ):
        raise RuntimeError("A2 list changed after verification")
    export_root = r3.guard(root, spec.export_dir, directory=True).resolve()
    pilot_yaml_bytes = r3.guard(root, spec.export_dir / "data.yaml").read_bytes()
    pilot_lines = pilot_yaml_bytes.decode("utf-8").splitlines(keepends=True)
    if (
        pilot_lines.count("train: images/train\n") != 1
        or pilot_lines.count("val: images/val\n") != 1
        or any(line.startswith("test:") for line in pilot_lines)
        or f"path: {export_root}\n" not in pilot_lines
    ):
        raise RuntimeError("pilot data.yaml is not the expected train/val-only export YAML")
    runtime = _safe_out_dir(root, replace(spec, out_dir=spec.out_dir / RUNTIME_DIR), create=True)
    runtime_list = runtime / RUNTIME_LIST
    entries = canonical_bytes.decode("utf-8").splitlines()
    for line in entries:
        refuse_non_train_entry(line)
    runtime_list_bytes = "".join(f"{export_root}/{line}\n" for line in entries).encode("utf-8")
    runtime_yaml_bytes = "".join(
        f"train: {runtime_list}\n" if line == "train: images/train\n" else line
        for line in pilot_lines
    ).encode("utf-8")
    _write_or_match(runtime_list, runtime_list_bytes)
    _write_or_match(runtime / RUNTIME_YAML, runtime_yaml_bytes)
    return {
        "rule_id": RULE_ID,
        "train_list_sha256": verified["train_list_sha256"],
        "manifest_sha256": verified["manifest_sha256"],
        "repeated_roster_sha256": verified["repeated_roster_sha256"],
        "train_list_entries": verified["train_list_entries"],
        "repeated_images": verified["repeated_images"],
        "repeated_raw_frames": verified["repeated_raw_frames"],
        "repeated_wp35_images": verified["repeated_wp35_images"],
        "pilot_data_yaml_sha256": sha256_bytes(pilot_yaml_bytes),
        "runtime_data_yaml": str(runtime / RUNTIME_YAML),
        "runtime_data_yaml_sha256": sha256_bytes(runtime_yaml_bytes),
        "runtime_train_list": str(runtime_list),
        "runtime_train_list_sha256": sha256_bytes(runtime_list_bytes),
        "data_yaml_changed_keys": ["train"],
    }


def runtime_entries(binding: dict[str, Any]) -> Counter[str]:
    """Multiset of absolute image paths the runtime list holds (for the dataset-size guard)."""
    data = Path(binding["runtime_train_list"]).read_bytes()
    if sha256_bytes(data) != binding["runtime_train_list_sha256"]:
        raise RuntimeError("runtime A2 list changed after materialisation")
    return Counter(os.path.normpath(line) for line in data.decode("utf-8").splitlines())


# -------------------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    root_parser = argparse.ArgumentParser(description=__doc__)
    root_parser.add_argument("command", choices=("build", "verify"))
    root_parser.add_argument("--root", type=Path, default=contract.REPO_ROOT)
    args = root_parser.parse_args(argv)
    try:
        result = (build if args.command == "build" else verify)(args.root)
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        print(json.dumps({"status": "FAILED", "error": f"{type(error).__name__}: {error}"}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
