#!/usr/bin/env python3
# ruff: noqa: E501
"""Export DATASET01 as a GTSRB-style classification package (`train.p`, `valid.p`, `test.p`).

Layout follows the German GTSRB pickles already in `data/processed/`: a dict with
`features` (N, 32, 32, 3) uint8 RGB, `labels` (N,) uint8, `sizes` (N, 2) crop width/height and
`coords` (N, 4) sign box x1, y1, x2, y2 inside the crop. As in GTSRB, each crop keeps a border of
10 % of the sign size (at least 5 px) around the box, clipped to the frame, and is resized to 32×32
without keeping the aspect ratio. `sizes`/`coords` are uint16 because DATASET01 crops can exceed
255 px (GTSRB uses uint8).

Content and governance:
- labels are the 54 WP33 classes with the M1 class map ids (`m1_yolo_classes.csv`), named in
  `signnames.csv` like GTSRB; only `train_eligible` boxes are used;
- splits are WP36-R1 (group-aware), guarded by the M1 export split check (list hashes, `use`);
- `train.p` also holds crops of the WP35 enriched images (train only; `source=WP35` in the index);
- the sealed test is written only by `export-test --final-eval --reason`, logged like M1.

`export` writes the pickles to the git-ignored `data/processed/dataset01_crops/` plus a committed
manifest (`docs/review/generated/dataset01_crops_manifest.json`) with counts and SHA-256 of every
array; `verify` rebuilds the arrays from the raw frames and compares them with the manifest.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import pickle
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("dataset01_crops_m1", Path(__file__).with_name("build_m1_yolo_dataset.py"))
assert _SPEC is not None and _SPEC.loader is not None
m1 = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = m1
_SPEC.loader.exec_module(m1)

STATUS = "DATASET01_GTSRB_STYLE_CROPS"
SIZE = 32
BORDER_RATIO, BORDER_MIN = 0.10, 5
FILES = {"train": "train.p", "val": "valid.p", "test": "test.p"}
DEFAULT_OUT = REPO_ROOT / "data/processed/dataset01_crops"
MANIFEST_PATH = Path("docs/review/generated/dataset01_crops_manifest.json")
INDEX_FIELDS = ["index", "source", "stem", "line", "derived_key", "label", "group_id"]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def crop_one(image: Image.Image, cx: float, cy: float, w: float, h: float) -> tuple[np.ndarray, tuple[int, int], tuple[int, int, int, int]]:
    width, height = image.size
    x1, y1 = (cx - w / 2) * width, (cy - h / 2) * height
    x2, y2 = (cx + w / 2) * width, (cy + h / 2) * height
    bw, bh = x2 - x1, y2 - y1
    pad_x, pad_y = max(BORDER_MIN, BORDER_RATIO * bw), max(BORDER_MIN, BORDER_RATIO * bh)
    # Round to 6 decimals first so float noise (44.9999999) does not shift a whole pixel.
    left = max(0, int(np.floor(round(x1 - pad_x, 6))))
    top = max(0, int(np.floor(round(y1 - pad_y, 6))))
    right = min(width, int(np.ceil(round(x2 + pad_x, 6))))
    bottom = min(height, int(np.ceil(round(y2 + pad_y, 6))))
    patch = image.crop((left, top, right, bottom)).resize((SIZE, SIZE), Image.BILINEAR)
    coords = (
        max(0, int(round(x1 - left))), max(0, int(round(y1 - top))),
        min(right - left, int(round(x2 - left))), min(bottom - top, int(round(y2 - top))),
    )
    return np.asarray(patch, dtype=np.uint8), (right - left, bottom - top), coords


def samples(repo_root: Path, raw_root: Path, wp35_root: Path, split: str) -> list[dict[str, Any]]:
    """One record per train-eligible box of the split, in a fixed order."""
    lists, _frames = m1.split_lists(repo_root)
    ids = {c["derived_key"]: c["yolo_id"] for c in m1.class_map(repo_root)}
    groups = {r["stem"]: r["group_id"] for r in m1.read_csv(repo_root / m1.SPLIT_FRAMES)}
    stems = set(lists[split])
    boxes = [b for b in m1.read_csv(repo_root / m1.BOXES) if b["train_eligible"] == "True" and b["stem"] in stems]
    boxes.sort(key=lambda b: (b["stem"], int(b["line"])))
    records = [
        {"source": "DATASET01", "stem": b["stem"], "line": int(b["line"]), "derived_key": b["derived_key"],
         "label": ids[b["derived_key"]], "group_id": groups[b["stem"]],
         "path": raw_root / "archive/images" / f"{b['stem']}.jpg",
         "box": tuple(float(b[k]) for k in ("x", "y", "w", "h"))}
        for b in boxes
    ]
    if split == "train":
        for row in sorted(m1.read_csv(repo_root / m1.WP35_LINEAGE), key=lambda r: r["augmented_id"]):
            label = wp35_root / "labels" / f"{row['augmented_id']}.txt"
            image = wp35_root / "images" / f"{row['augmented_id']}.jpg"
            if sha256_bytes(label.read_bytes()) != row["label_sha256"] or sha256_bytes(image.read_bytes()) != row["image_sha256"]:
                raise ValueError(f"WP35 file does not match lineage: {row['augmented_id']}")
            for line_no, line in enumerate(label.read_text(encoding="utf-8").splitlines(), start=1):
                key, *values = line.split()
                records.append({"source": "WP35", "stem": row["augmented_id"], "line": line_no, "derived_key": key,
                                "label": ids[key], "group_id": row["source_group_id"], "path": image,
                                "box": tuple(float(v) for v in values)})
    return records


def build_split(records: list[dict[str, Any]]) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    features, labels, sizes, coords, index = [], [], [], [], []
    cache: dict[Path, Image.Image] = {}
    for position, record in enumerate(records):
        path = record["path"]
        if path not in cache:
            cache.clear()
            with Image.open(path) as handle:
                cache[path] = handle.convert("RGB")
        patch, size, box = crop_one(cache[path], *record["box"])
        features.append(patch)
        labels.append(record["label"])
        sizes.append(size)
        coords.append(box)
        index.append({"index": position, **{k: record[k] for k in INDEX_FIELDS if k != "index"}})
    arrays = {
        "features": np.stack(features).astype(np.uint8) if features else np.zeros((0, SIZE, SIZE, 3), np.uint8),
        "labels": np.asarray(labels, dtype=np.uint8),
        "sizes": np.asarray(sizes, dtype=np.uint16).reshape(-1, 2),
        "coords": np.asarray(coords, dtype=np.uint16).reshape(-1, 4),
    }
    return arrays, index


def index_csv(index: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=INDEX_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(index)
    return buffer.getvalue().encode("utf-8")


def signnames(repo_root: Path) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["ClassId", "SignName", "DerivedKey", "QCVN"])
    for c in m1.class_map(repo_root):
        writer.writerow([c["yolo_id"], c["name_vi"], c["derived_key"], c["derived_code"]])
    return buffer.getvalue().encode("utf-8")


def summarise(split: str, arrays: dict[str, np.ndarray], index: list[dict[str, Any]]) -> dict[str, Any]:
    small = int(np.sum(np.minimum(arrays["coords"][:, 2] - arrays["coords"][:, 0], arrays["coords"][:, 3] - arrays["coords"][:, 1]) < 16))
    return {
        "file": FILES[split],
        "samples": len(index),
        "sources": dict(sorted(Counter(r["source"] for r in index).items())),
        "classes": len(set(arrays["labels"].tolist())),
        "per_class": {str(k): v for k, v in sorted(Counter(arrays["labels"].tolist()).items())},
        "signs_under_16px": small,
        "sha256": {k: sha256_bytes(np.ascontiguousarray(v).tobytes()) for k, v in arrays.items()},
        "index_sha256": sha256_bytes(index_csv(index)),
    }


def render(repo_root: Path, raw_root: Path, wp35_root: Path, splits: tuple[str, ...]) -> tuple[dict[str, Any], dict[str, tuple[dict[str, np.ndarray], list[dict[str, Any]]]]]:
    built = {split: build_split(samples(repo_root, raw_root, wp35_root, split)) for split in splits}
    summary = {split: summarise(split, *built[split]) for split in splits}
    return summary, built


def manifest_payload(repo_root: Path, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "package": "DATASET01-GTSRB-STYLE", "status": STATUS,
        "format": {"features": "uint8 (N,32,32,3) RGB", "labels": "uint8 (N,) M1 class map id", "sizes": "uint16 (N,2) crop w,h",
                   "coords": "uint16 (N,4) sign x1,y1,x2,y2 in crop", "border": f"{BORDER_RATIO:.0%} of sign size, min {BORDER_MIN}px",
                   "resize": "PIL bilinear to 32x32, aspect not kept"},
        "classes": 54, "signnames_sha256": sha256_bytes(signnames(repo_root)),
        "splits": summary,
        "test": "sealed: only `export-test --final-eval --reason`, logged in " + str(m1.TEST_ACCESS_LOG),
        "use_limits": [
            "WP35 crops are train-only and repeat the same physical signs as their source frames",
            "22 classes have no test crops; 35 classes have no valid crops",
            "UNKNOWN (class 31) and EXCLUDED boxes are not included",
        ],
        "pinned_sources": m1.PINNED_SOURCES,
    }


def write(out: Path, built: dict[str, tuple[dict[str, np.ndarray], list[dict[str, Any]]]], repo_root: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for split, (arrays, index) in built.items():
        with (out / FILES[split]).open("wb") as handle:
            pickle.dump(arrays, handle, protocol=pickle.HIGHEST_PROTOCOL)
        (out / f"{Path(FILES[split]).stem}_index.csv").write_bytes(index_csv(index))
    (out / "signnames.csv").write_bytes(signnames(repo_root))


def export(repo_root: Path, raw_root: Path, wp35_root: Path, out: Path) -> dict[str, Any]:
    m1.verify_pins(repo_root)
    summary, built = render(repo_root, raw_root, wp35_root, ("train", "val"))
    write(out, built, repo_root)
    (repo_root / MANIFEST_PATH).write_text(json.dumps(manifest_payload(repo_root, summary), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"status": STATUS, "out": str(out), **{s: summary[s]["samples"] for s in summary}}


def verify(repo_root: Path, raw_root: Path, wp35_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        m1.verify_pins(repo_root)
        summary, _built = render(repo_root, raw_root, wp35_root, ("train", "val"))
        expected = (json.dumps(manifest_payload(repo_root, summary), indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        if not (repo_root / MANIFEST_PATH).is_file() or (repo_root / MANIFEST_PATH).read_bytes() != expected:
            errors.append(f"manifest differs: {MANIFEST_PATH}")
    except (ValueError, OSError, KeyError) as error:
        errors.append(str(error))
    return {"status": STATUS, "valid": not errors, "errors": errors}


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("export", "verify", "export-test"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        command.add_argument("--raw-root", type=Path, default=m1.DEFAULT_RAW_ROOT)
        command.add_argument("--wp35-root", type=Path, default=m1.DEFAULT_WP35_ROOT)
        command.add_argument("--out", type=Path, default=DEFAULT_OUT)
    commands.choices["export-test"].add_argument("--final-eval", action="store_true")
    commands.choices["export-test"].add_argument("--reason", default="")
    args = root.parse_args(argv)
    repo_root = args.repo_root.resolve()
    if args.command == "export":
        result, ok = export(repo_root, args.raw_root, args.wp35_root, args.out), True
    elif args.command == "verify":
        result = verify(repo_root, args.raw_root, args.wp35_root)
        ok = result["valid"]
    else:
        if not args.final_eval or not args.reason.strip():
            print("refused: the sealed test is exported only with --final-eval and a --reason (G0.7, D-05)", file=sys.stderr)
            return 2
        m1.log_test_access(repo_root, f"dataset01_crops test.p: {args.reason.strip()}")
        _summary, built = render(repo_root, args.raw_root, args.wp35_root, ("test",))
        write(args.out, built, repo_root)
        result, ok = {"status": "TEST_EXPORTED", "samples": len(built["test"][1])}, True
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
