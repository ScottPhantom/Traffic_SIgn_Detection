#!/usr/bin/env python3
# ruff: noqa: E501
"""M1 — export DATASET01 as a YOLO detection dataset under the D-05 / G0.7 contract.

`manifest` derives a committed, byte-reproducible export manifest from the pinned inputs:
- the class map: the 54 WP33 `CLASS` keys mapped to YOLO ids in taxonomy order;
- per-split stem lists checked against the WP36-R1 `split_list_sha256` and the `use` column;
- the label text of every exported frame, built from WP33 `train_eligible` boxes;
- WP35 enriched images (train only), checked against the WP35 lineage hashes.

`export --out DIR` materialises train and val (raw images as symlinks, labels as files, data.yaml)
and checks the result against the manifest. The sealed test split is never exported by `export`;
only `export-test --final-eval --reason TEXT` writes it, after appending a line to the sealed-test
access log (D-05 Q2, G0.7 acceptance). `verify` re-derives the manifest byte for byte.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"
DEFAULT_WP35_ROOT = REPO_ROOT / "data/processed/wp35_enrichment"
DEFAULT_OUT = REPO_ROOT / "data/processed/m1_yolo"
STATUS = "M1_YOLO_EXPORT_CONTRACT"
SPLITS = ("train", "val", "test")

GENERATED = Path("docs/review/generated")
TAXONOMY = GENERATED / "wp33_derived_taxonomy.csv"
BOXES = GENERATED / "wp33_derived_boxes.csv"
SPLIT_FRAMES = GENERATED / "wp36_r1_split_frames.csv"
SPLIT_MANIFEST = GENERATED / "wp36_r1_split_manifest.json"
WP35_LINEAGE = GENERATED / "wp35_enrichment_lineage.csv"
IMAGE_INVENTORY = Path("results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
PINNED_SOURCES = {
    str(TAXONOMY): "199ddd322aa05d4875af809c1c7c1459198ebf91ada24f406cbf039c406fa5ad",
    str(BOXES): "4b9307003ce8fd3c1d50763a5950d3d57cf6b2ee6df3aeef74621707067501c0",
    str(SPLIT_FRAMES): "8e197d9c7103ac5dc6b7ffc8a3d1aeb30bb6034048d470e4887dd868df95823a",
    str(SPLIT_MANIFEST): "064259941895d35054e87a550bf69199c4cae8ffeb4c83b4d7cdf608673438d9",
    str(WP35_LINEAGE): "e802fc264feff5168c28b531801af04051a36accc3c893ad5ab2e72975d38fed",
    str(IMAGE_INVENTORY): "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022",
    "docs/review/g07_owner_acceptance_record.md": "88d5c16e2041b23e43e5381b7107d9de2d4a11635124c876263802abc2dce32a",
    "docs/review/d05_owner_decision_record.md": "c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702",
}
CLASSES_PATH = GENERATED / "m1_yolo_classes.csv"
MANIFEST_PATH = GENERATED / "m1_yolo_export_manifest.json"
TEST_ACCESS_LOG = Path("results/experiments/sealed_test_access_log.jsonl")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def list_sha256(stems: list[str]) -> str:
    return sha256_bytes("\n".join(sorted(stems)).encode("utf-8"))


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        if sha256_bytes((repo_root / relative).read_bytes()) != expected:
            raise ValueError(f"pinned source changed: {relative}")


def class_map(repo_root: Path) -> list[dict[str, Any]]:
    rows = [row for row in read_csv(repo_root / TAXONOMY) if row["role"] == "CLASS"]
    if len(rows) != 54:
        raise ValueError(f"expected 54 trainable WP33 classes, found {len(rows)}")
    return [
        {"yolo_id": index, "derived_key": row["derived_key"], "derived_code": row["derived_code"],
         "name_vi": row["derived_name_vi"], "name": f"{row['derived_key']} {row['derived_code']}"}
        for index, row in enumerate(rows)
    ]


def split_lists(repo_root: Path) -> tuple[dict[str, list[str]], list[dict[str, str]]]:
    """Split stems with the G0.7 guard: list hashes and `use` must match WP36-R1."""
    frames = read_csv(repo_root / SPLIT_FRAMES)
    manifest = json.loads((repo_root / SPLIT_MANIFEST).read_text(encoding="utf-8"))
    lists = {s: sorted(r["stem"] for r in frames if r["split"] == s and r["use"] != "QUARANTINED") for s in SPLITS}
    for split, stems in lists.items():
        if list_sha256(stems) != manifest["split_list_sha256"][split]:
            raise ValueError(f"{split} list differs from the WP36-R1 manifest")
    if manifest["test_seal_sha256"] != list_sha256(lists["test"]):
        raise ValueError("test seal mismatch")
    for row in frames:
        if row["use"] == "BACKGROUND" and row["split"] != "train":
            raise ValueError(f"background frame {row['stem']} outside train")
    return lists, frames


def label_text(boxes: list[dict[str, str]], ids: dict[str, int]) -> str:
    lines = [
        f"{ids[b['derived_key']]} {b['x']} {b['y']} {b['w']} {b['h']}"
        for b in sorted(boxes, key=lambda b: int(b["line"]))
    ]
    return "".join(f"{line}\n" for line in lines)


def derive(repo_root: Path) -> dict[str, Any]:
    verify_pins(repo_root)
    classes = class_map(repo_root)
    ids = {c["derived_key"]: c["yolo_id"] for c in classes}
    lists, _frames = split_lists(repo_root)
    by_stem: dict[str, list[dict[str, str]]] = defaultdict(list)
    untrained: Counter[str] = Counter()
    for box in read_csv(repo_root / BOXES):
        if box["train_eligible"] == "True":
            by_stem[box["stem"]].append(box)
        else:
            untrained[box["stem"]] += 1
    labels: dict[str, dict[str, str]] = {}
    for split in SPLITS:
        labels[split] = {stem: label_text(by_stem.get(stem, []), ids) for stem in lists[split]}
    lineage = read_csv(repo_root / WP35_LINEAGE)
    wp35 = {}
    for row in lineage:
        if row["source_stem"] not in lists["train"]:
            raise ValueError(f"WP35 source {row['source_stem']} is not a train frame")
        wp35[row["augmented_id"]] = {"image_sha256": row["image_sha256"], "label_sha256": row["label_sha256"]}
    return {"classes": classes, "ids": ids, "lists": lists, "labels": labels, "wp35": wp35, "untrained": untrained}


def render(repo_root: Path) -> dict[Path, bytes]:
    data = derive(repo_root)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(data["classes"][0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(data["classes"])
    per_split = {}
    for split in SPLITS:
        labels = data["labels"][split]
        box_counts = Counter(int(line.split()[0]) for text in labels.values() for line in text.splitlines())
        per_split[split] = {
            "frames": len(labels),
            "empty_label_frames": sum(1 for text in labels.values() if not text),
            "boxes": sum(box_counts.values()),
            "classes_with_boxes": len(box_counts),
            "frames_with_untrained_boxes": sum(1 for stem in labels if data["untrained"][stem]),
            "stem_list_sha256": list_sha256(list(labels)),
            "labels_sha256": sha256_bytes("".join(f"{stem}\n{labels[stem]}" for stem in sorted(labels)).encode("utf-8")),
        }
    manifest = {
        "package": "M1-YOLO-EXPORT", "status": STATUS,
        "classes": len(data["classes"]),
        "class_map_sha256": sha256_bytes(buffer.getvalue().encode("utf-8")),
        "splits": per_split,
        "wp35_train_only": {"images": len(data["wp35"]), "lineage_sha256": PINNED_SOURCES[str(WP35_LINEAGE)]},
        "test_export": "sealed: only `export-test --final-eval`, logged in " + str(TEST_ACCESS_LOG),
        "training_contract": {
            "horizontal_flip": 0.0,
            "labels": "WP33 train_eligible boxes only; UNKNOWN/EXCLUDED boxes stay unlabelled (reported per split)",
            "selection": "val only (D-05 Q4); 13 no-val classes never drive selection",
        },
        "pinned_sources": PINNED_SOURCES,
    }
    return {
        CLASSES_PATH: buffer.getvalue().encode("utf-8"),
        MANIFEST_PATH: (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"),
    }


def build(repo_root: Path) -> dict[str, Any]:
    artifacts = render(repo_root)
    for path, payload in artifacts.items():
        (repo_root / path).write_bytes(payload)
    return {"status": STATUS, "artifacts": len(artifacts)}


def verify(repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        for path, payload in render(repo_root).items():
            if not (repo_root / path).is_file() or (repo_root / path).read_bytes() != payload:
                errors.append(f"artifact differs: {path}")
    except (ValueError, OSError, KeyError) as error:
        errors.append(str(error))
    return {"status": STATUS, "valid": not errors, "errors": errors}


def _link(target: Path, link: Path) -> None:
    if link.is_symlink() or link.exists():
        link.unlink()
    os.symlink(target, link)


def _wp35_label_text(path: Path, ids: dict[str, int]) -> str:
    rows = [line.split() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return "".join(f"{ids[row[0]]} {' '.join(row[1:])}\n" for row in rows)


def dataset_yaml(out: Path, splits: tuple[str, ...], names: dict[int, str]) -> bytes:
    yaml_splits = "".join(f"{split}: images/{split}\n" for split in splits)
    names_yaml = "".join(f'  {index}: "{names[index]}"\n' for index in sorted(names))
    return (
        "# Generated by scripts/build_m1_yolo_dataset.py — do not edit.\n"
        f"path: {out.resolve()}\n{yaml_splits}names:\n{names_yaml}"
    ).encode()


def verify_materialised(
    repo_root: Path,
    raw_root: Path,
    wp35_root: Path,
    out: Path,
    splits: tuple[str, ...],
) -> dict[str, Any]:
    """Verify every exported YAML, label and image byte against the governed sources."""
    errors: list[str] = []
    try:
        data = derive(repo_root)
        names = {c["yolo_id"]: c["name"] for c in data["classes"]}
        yaml_name = "data_test.yaml" if "test" in splits else "data.yaml"
        yaml_path = out / yaml_name
        expected_yaml = dataset_yaml(out, splits, names)
        if not yaml_path.is_file() or yaml_path.read_bytes() != expected_yaml:
            errors.append(f"exported YAML differs: {yaml_path}")

        inventory = {row["stem"]: row for row in read_csv(repo_root / IMAGE_INVENTORY)}
        for split in splits:
            image_dir, label_dir = out / "images" / split, out / "labels" / split
            expected_labels = dict(data["labels"][split])
            expected_images: dict[str, tuple[Path, str]] = {
                stem: (
                    raw_root / "archive/images" / f"{stem}.jpg",
                    inventory[stem]["image_sha256"],
                )
                for stem in data["labels"][split]
            }
            if split == "train":
                for augmented_id, hashes in data["wp35"].items():
                    source_image = wp35_root / "images" / f"{augmented_id}.jpg"
                    source_label = wp35_root / "labels" / f"{augmented_id}.txt"
                    if not source_image.is_file() or sha256_bytes(source_image.read_bytes()) != hashes["image_sha256"]:
                        errors.append(f"WP35 source image differs from lineage: {augmented_id}")
                    if not source_label.is_file() or sha256_bytes(source_label.read_bytes()) != hashes["label_sha256"]:
                        errors.append(f"WP35 source label differs from lineage: {augmented_id}")
                    expected_images[augmented_id] = (source_image, hashes["image_sha256"])
                    expected_labels[augmented_id] = _wp35_label_text(source_label, data["ids"])

            actual_image_names = {
                path.name for path in image_dir.iterdir() if path.is_file() or path.is_symlink()
            } if image_dir.is_dir() else set()
            actual_label_names = {
                path.name for path in label_dir.iterdir() if path.is_file() or path.is_symlink()
            } if label_dir.is_dir() else set()
            expected_image_names = {f"{stem}.jpg" for stem in expected_images}
            expected_label_names = {f"{stem}.txt" for stem in expected_labels}
            if actual_image_names != expected_image_names:
                errors.append(f"exported {split} image roster differs")
            if actual_label_names != expected_label_names:
                errors.append(f"exported {split} label roster differs")

            for stem, text in expected_labels.items():
                path = label_dir / f"{stem}.txt"
                if not path.is_file() or path.is_symlink() or path.read_bytes() != text.encode("utf-8"):
                    errors.append(f"exported label differs: {split}/{stem}.txt")
            for stem, (source, expected_hash) in expected_images.items():
                path = image_dir / f"{stem}.jpg"
                if not path.is_file():
                    errors.append(f"exported image missing: {split}/{stem}.jpg")
                    continue
                if path.is_symlink() and path.resolve() != source.resolve():
                    errors.append(f"exported image symlink target differs: {split}/{stem}.jpg")
                if sha256_bytes(path.read_bytes()) != expected_hash:
                    errors.append(f"exported image bytes differ: {split}/{stem}.jpg")
    except (KeyError, OSError, ValueError) as error:
        errors.append(str(error))
    return {"status": STATUS, "valid": not errors, "errors": errors[:50]}


def materialise(repo_root: Path, raw_root: Path, wp35_root: Path, out: Path, splits: tuple[str, ...]) -> dict[str, Any]:
    if verify(repo_root)["valid"] is not True:
        raise ValueError("M1 export manifest does not verify; run `manifest` after reviewing inputs")
    data = derive(repo_root)
    names = {c["yolo_id"]: c["name"] for c in data["classes"]}
    written = Counter()
    for split in splits:
        image_dir, label_dir = out / "images" / split, out / "labels" / split
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        for stem, text in data["labels"][split].items():
            source = raw_root / "archive/images" / f"{stem}.jpg"
            if not source.is_file():
                raise ValueError(f"missing raw image {source}")
            _link(source.resolve(), image_dir / f"{stem}.jpg")
            (label_dir / f"{stem}.txt").write_text(text, encoding="utf-8")
            written[split] += 1
        if split == "train":
            for augmented_id, hashes in sorted(data["wp35"].items()):
                image = wp35_root / "images" / f"{augmented_id}.jpg"
                label = wp35_root / "labels" / f"{augmented_id}.txt"
                if sha256_bytes(image.read_bytes()) != hashes["image_sha256"] or sha256_bytes(label.read_bytes()) != hashes["label_sha256"]:
                    raise ValueError(f"WP35 file does not match lineage: {augmented_id}")
                text = _wp35_label_text(label, data["ids"])
                _link(image.resolve(), image_dir / f"{augmented_id}.jpg")
                (label_dir / f"{augmented_id}.txt").write_text(text, encoding="utf-8")
                written["train_wp35"] += 1
    (out / ("data.yaml" if "test" not in splits else "data_test.yaml")).write_bytes(
        dataset_yaml(out, splits, names)
    )
    verification = verify_materialised(repo_root, raw_root, wp35_root, out, splits)
    if not verification["valid"]:
        raise ValueError(f"materialised export failed verification: {verification['errors']}")
    return {
        "status": "EXPORTED",
        "out": str(out),
        "written": dict(written),
        "verified": True,
    }


def log_test_access(repo_root: Path, reason: str) -> None:
    path = repo_root / TEST_ACCESS_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "time": datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).isoformat(timespec="seconds"),
        "action": "export-test", "reason": reason,
        "test_seal_sha256": json.loads((repo_root / SPLIT_MANIFEST).read_text(encoding="utf-8"))["test_seal_sha256"],
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("manifest", "verify", "export", "export-test"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        if name.startswith("export"):
            command.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
            command.add_argument("--wp35-root", type=Path, default=DEFAULT_WP35_ROOT)
            command.add_argument("--out", type=Path, default=DEFAULT_OUT)
    commands.choices["export-test"].add_argument("--final-eval", action="store_true")
    commands.choices["export-test"].add_argument("--reason", default="")
    args = root.parse_args(argv)
    repo_root = args.repo_root.resolve()
    if args.command == "manifest":
        result, ok = build(repo_root), True
    elif args.command == "verify":
        result = verify(repo_root)
        ok = result["valid"]
    elif args.command == "export":
        result, ok = materialise(repo_root, args.raw_root, args.wp35_root, args.out, ("train", "val")), True
    else:
        if not args.final_eval or not args.reason.strip():
            print("refused: the sealed test is exported only with --final-eval and a --reason (D-05)", file=sys.stderr)
            return 2
        log_test_access(repo_root, args.reason.strip())
        result, ok = materialise(repo_root, args.raw_root, args.wp35_root, args.out, ("test",)), True
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
