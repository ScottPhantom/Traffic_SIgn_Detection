#!/usr/bin/env python3
"""Build the train/val-only one-class detector dataset for the D1 cascade baseline.

This is a successor package. It does not modify the QA-pinned M1 54-class exporter. It uses the
same governed images, boxes and split bindings, but rewrites every train-eligible box class to the
single detector class ``0 traffic_sign``. WP35 stays train-only. There is intentionally no test
export command: the cascade baseline needs an Owner-approved gate addendum before sealed-test use.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import stat
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "d1_cascade_m1_source", Path(__file__).with_name("build_m1_yolo_dataset.py")
)
assert _SPEC is not None and _SPEC.loader is not None
m1 = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = m1
_SPEC.loader.exec_module(m1)

STATUS = "D1_CASCADE_ONE_CLASS_DETECTOR_DATASET"
DEFAULT_OUT = REPO_ROOT / "data/processed/d1_cascade_yolo"
MANIFEST_PATH = Path("docs/review/generated/d1_cascade_detector_manifest.json")
M1_MANIFEST = Path("docs/review/generated/m1_yolo_export_manifest.json")
M1_CLASSES = Path("docs/review/generated/m1_yolo_classes.csv")
OWNER_DECISION = Path("docs/review/d1_dual_baseline_owner_decision_record.md")
PINNED_INPUTS = {
    str(M1_MANIFEST): "8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71",
    str(M1_CLASSES): "7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242",
    str(OWNER_DECISION): "39f26b0e29a2a60a5972ea07e6e0dcf04ce5e53f722a3c92b3a69b267934a0b2",
}
ALLOWED_SPLITS = ("train", "val")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def absolute_lexical(path: Path) -> Path:
    """Return an absolute normalized path without resolving symlink components."""
    return Path(os.path.abspath(os.fspath(path)))


def reject_symlink_components(path: Path) -> None:
    """Fail before I/O when any existing component of an output path is a symlink."""
    target = absolute_lexical(path)
    current = Path(target.anchor)
    for part in target.parts[1:]:
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            break
        if stat.S_ISLNK(mode):
            raise ValueError(f"refused symlink component in output path: {current}")


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_INPUTS.items():
        path = repo_root / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"cascade pinned input differs: {relative}")
    source = m1.verify(repo_root)
    if source["valid"] is not True:
        raise ValueError(f"M1 source export contract is invalid: {source['errors']}")


def collapse_label_text(text: str) -> str:
    """Preserve normalized box coordinates exactly while replacing the class with zero."""
    output: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f"invalid YOLO label field count on line {line_no}")
        try:
            class_id = int(fields[0])
            coords = [float(value) for value in fields[1:]]
        except ValueError as error:
            raise ValueError(f"invalid YOLO label token on line {line_no}") from error
        if class_id not in range(54):
            raise ValueError(f"unexpected M1 class id on line {line_no}: {class_id}")
        if any(not math.isfinite(value) or value < 0.0 or value > 1.0 for value in coords):
            raise ValueError(f"invalid YOLO coordinate on line {line_no}")
        output.append(f"0 {' '.join(fields[1:])}\n")
    return "".join(output)


def manifest_payload(repo_root: Path) -> dict[str, Any]:
    verify_pins(repo_root)
    source = json.loads((repo_root / M1_MANIFEST).read_text(encoding="utf-8"))
    return {
        "package": "D1-CASCADE-ONE-CLASS-DETECTOR",
        "status": STATUS,
        "classes": {"count": 1, "names": {"0": "traffic_sign"}},
        "allowed_splits": list(ALLOWED_SPLITS),
        "test_included": False,
        "sealed_test_policy": (
            "No test export route. Owner-approved cascade gate addendum is required before "
            "sealed-test eligibility."
        ),
        "transform": {
            "source": "M1 54-class train/val labels",
            "class_rewrite": "every train-eligible box class -> 0; coordinates byte-preserved",
            "horizontal_flip": 0.0,
            "wp35": "train only",
        },
        "source_bindings": {
            "m1_manifest_sha256": PINNED_INPUTS[str(M1_MANIFEST)],
            "m1_class_map_sha256": PINNED_INPUTS[str(M1_CLASSES)],
            "owner_decision_sha256": PINNED_INPUTS[str(OWNER_DECISION)],
            "train_stem_list_sha256": source["splits"]["train"]["stem_list_sha256"],
            "val_stem_list_sha256": source["splits"]["val"]["stem_list_sha256"],
            "sealed_test_stem_list_sha256": source["splits"]["test"]["stem_list_sha256"],
        },
        "counts": {
            "raw_train_frames": source["splits"]["train"]["frames"],
            "raw_train_boxes": source["splits"]["train"]["boxes"],
            "raw_val_frames": source["splits"]["val"]["frames"],
            "raw_val_boxes": source["splits"]["val"]["boxes"],
            "wp35_train_images": source["wp35_train_only"]["images"],
        },
        "validation_boundary": (
            "Detector localization may be selected on val. Classifier taxonomy, thresholds, "
            "cascade metrics and sealed-test gates remain unapproved."
        ),
    }


def manifest_bytes(repo_root: Path) -> bytes:
    return (
        json.dumps(manifest_payload(repo_root), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def build_manifest(repo_root: Path) -> dict[str, Any]:
    path = repo_root / MANIFEST_PATH
    path.write_bytes(manifest_bytes(repo_root))
    return {"status": STATUS, "manifest": str(path), "sha256": sha256_file(path)}


def verify_manifest(repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        path = repo_root / MANIFEST_PATH
        if (
            not path.is_file()
            or path.is_symlink()
            or path.read_bytes() != manifest_bytes(repo_root)
        ):
            errors.append(f"cascade manifest differs: {MANIFEST_PATH}")
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        errors.append(str(error))
    return {"status": STATUS, "valid": not errors, "errors": errors}


def expected_records(
    repo_root: Path, raw_root: Path, wp35_root: Path
) -> dict[str, dict[str, dict[str, Any]]]:
    data = m1.derive(repo_root)
    inventory = {row["stem"]: row for row in m1.read_csv(repo_root / m1.IMAGE_INVENTORY)}
    result: dict[str, dict[str, dict[str, Any]]] = {split: {} for split in ALLOWED_SPLITS}
    for split in ALLOWED_SPLITS:
        for stem, text in data["labels"][split].items():
            result[split][stem] = {
                "image": raw_root / "archive/images" / f"{stem}.jpg",
                "image_sha256": inventory[stem]["image_sha256"],
                "label": collapse_label_text(text),
            }
    for augmented_id, hashes in sorted(data["wp35"].items()):
        image = wp35_root / "images" / f"{augmented_id}.jpg"
        label = wp35_root / "labels" / f"{augmented_id}.txt"
        if not image.is_file() or sha256_file(image) != hashes["image_sha256"]:
            raise ValueError(f"WP35 source image differs from lineage: {augmented_id}")
        if not label.is_file() or sha256_file(label) != hashes["label_sha256"]:
            raise ValueError(f"WP35 source label differs from lineage: {augmented_id}")
        source_text = m1._wp35_label_text(label, data["ids"])
        result["train"][augmented_id] = {
            "image": image,
            "image_sha256": hashes["image_sha256"],
            "label": collapse_label_text(source_text),
        }
    return result


def dataset_yaml(out: Path) -> bytes:
    return (
        "# Generated by scripts/build_d1_cascade_detector_dataset.py — do not edit.\n"
        f"path: {absolute_lexical(out)}\n"
        "train: images/train\n"
        "val: images/val\n"
        "names:\n"
        '  0: "traffic_sign"\n'
    ).encode()


def _write_exact(path: Path, payload: bytes) -> str:
    reject_symlink_components(path.parent)
    if path.is_symlink():
        raise ValueError(f"refused output symlink: {path}")
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise ValueError(f"refused to overwrite differing output: {path}")
        return "reused"
    path.write_bytes(payload)
    return "written"


def _link_exact(source: Path, destination: Path, expected_sha256: str) -> str:
    reject_symlink_components(destination.parent)
    if not source.is_file() or sha256_file(source) != expected_sha256:
        raise ValueError(f"source image differs: {source}")
    if destination.is_symlink():
        if destination.resolve() != source.resolve() or sha256_file(destination) != expected_sha256:
            raise ValueError(f"refused differing output symlink: {destination}")
        return "reused"
    if destination.exists():
        raise ValueError(f"refused to overwrite output image: {destination}")
    os.symlink(source.resolve(), destination)
    return "written"


def _require_output_directory(path: Path) -> None:
    reject_symlink_components(path)
    path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir() or path.is_symlink():
        raise ValueError(f"invalid output directory: {path}")


def verify_export(
    repo_root: Path, raw_root: Path, wp35_root: Path, out: Path = DEFAULT_OUT
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        reject_symlink_components(out)
        manifest = verify_manifest(repo_root)
        if manifest["valid"] is not True:
            raise ValueError(f"cascade manifest is invalid: {manifest['errors']}")
        expected = expected_records(repo_root, raw_root, wp35_root)
        yaml_path = out / "data.yaml"
        if (
            not yaml_path.is_file()
            or yaml_path.is_symlink()
            or yaml_path.read_bytes() != dataset_yaml(out)
        ):
            errors.append("cascade data.yaml differs")
        allowed_roots = {out / "data.yaml", out / "images", out / "labels"}
        if out.is_dir() and {path for path in out.iterdir()} != allowed_roots:
            errors.append("cascade output root roster differs")
        expected_split_dirs = set(ALLOWED_SPLITS)
        for kind in ("images", "labels"):
            kind_dir = out / kind
            if kind_dir.is_symlink():
                errors.append(f"cascade {kind} directory is a symlink")
                continue
            actual_split_dirs = (
                {path.name for path in kind_dir.iterdir()} if kind_dir.is_dir() else set()
            )
            if actual_split_dirs != expected_split_dirs:
                errors.append(f"cascade {kind} split roster differs")
        for split, records in expected.items():
            image_dir = out / "images" / split
            label_dir = out / "labels" / split
            if image_dir.is_symlink() or label_dir.is_symlink():
                errors.append(f"cascade {split} split directory is a symlink")
                continue
            expected_images = {f"{stem}.jpg" for stem in records}
            expected_labels = {f"{stem}.txt" for stem in records}
            actual_images = (
                {path.name for path in image_dir.iterdir()} if image_dir.is_dir() else set()
            )
            actual_labels = (
                {path.name for path in label_dir.iterdir()} if label_dir.is_dir() else set()
            )
            if actual_images != expected_images:
                errors.append(f"cascade {split} image roster differs")
            if actual_labels != expected_labels:
                errors.append(f"cascade {split} label roster differs")
            for stem, record in records.items():
                image = image_dir / f"{stem}.jpg"
                label = label_dir / f"{stem}.txt"
                if (
                    not image.is_file()
                    or not image.is_symlink()
                    or image.resolve() != record["image"].resolve()
                    or sha256_file(image) != record["image_sha256"]
                ):
                    errors.append(f"cascade image differs: {split}/{stem}.jpg")
                if (
                    not label.is_file()
                    or label.is_symlink()
                    or label.read_bytes() != record["label"].encode("utf-8")
                ):
                    errors.append(f"cascade label differs: {split}/{stem}.txt")
    except (KeyError, OSError, ValueError) as error:
        errors.append(str(error))
    return {"status": STATUS, "valid": not errors, "errors": errors[:50]}


def export(
    repo_root: Path, raw_root: Path, wp35_root: Path, out: Path
) -> dict[str, Any]:
    if verify_manifest(repo_root)["valid"] is not True:
        raise ValueError("cascade manifest does not verify; run `manifest` after review")
    reject_symlink_components(out)
    expected = expected_records(repo_root, raw_root, wp35_root)
    actions: Counter[str] = Counter()
    for split, records in expected.items():
        image_dir = out / "images" / split
        label_dir = out / "labels" / split
        for directory in (out, out / "images", out / "labels", image_dir, label_dir):
            _require_output_directory(directory)
        for stem, record in records.items():
            image_action = _link_exact(
                record["image"], image_dir / f"{stem}.jpg", record["image_sha256"]
            )
            actions[image_action] += 1
            actions[_write_exact(label_dir / f"{stem}.txt", record["label"].encode("utf-8"))] += 1
    actions[_write_exact(out / "data.yaml", dataset_yaml(out))] += 1
    verification = verify_export(repo_root, raw_root, wp35_root, out)
    if verification["valid"] is not True:
        raise ValueError(f"cascade export failed verification: {verification['errors']}")
    return {
        "status": "EXPORTED",
        "out": str(out),
        "test_included": False,
        "frames": {split: len(records) for split, records in expected.items()},
        "boxes": {
            split: sum(len(record["label"].splitlines()) for record in records.values())
            for split, records in expected.items()
        },
        "actions": dict(actions),
        "verified": True,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("manifest", "verify", "export", "verify-export"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        if name in {"export", "verify-export"}:
            command.add_argument("--raw-root", type=Path, default=m1.DEFAULT_RAW_ROOT)
            command.add_argument("--wp35-root", type=Path, default=m1.DEFAULT_WP35_ROOT)
            command.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    try:
        if args.command == "manifest":
            result = build_manifest(repo_root)
        elif args.command == "verify":
            result = verify_manifest(repo_root)
        elif args.command == "export":
            result = export(
                repo_root,
                args.raw_root.resolve(),
                args.wp35_root.resolve(),
                absolute_lexical(args.out),
            )
        else:
            result = verify_export(
                repo_root,
                args.raw_root.resolve(),
                args.wp35_root.resolve(),
                absolute_lexical(args.out),
            )
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("valid", result.get("verified", True)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
