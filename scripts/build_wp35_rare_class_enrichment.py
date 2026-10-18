#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and verify M0-WP35: real-frame augmentation for the 12 rare WP33 classes (D-04 part 1).

The owner kept the 12 one-group rare classes for training with enriched data and, in the
2026-10-17 revision of `docs/review/d04_owner_decision_part1_record.md`, limited enrichment to
transformations of the original DATASET01 frames: no sign is pasted or synthesised.

For each class, WP35 repeatedly takes a real frame that contains the class and applies:
- geometry: small rotation (±5°) and a zoom-in crop window (55–95 % of the frame) with a random
  offset, resized back to the original resolution. Boxes are transformed with the image. A window
  is accepted only if every labelled box is either fully inside or fully outside it, the target
  rare box is inside, and no part of the window leaves the rotated frame (no padding, no mirror).
- photometry: brightness, contrast, saturation, gamma, small hue shift, haze, Gaussian noise,
  Gaussian or motion blur, and JPEG re-compression (quality 50–95).
No horizontal flip, because several rare classes are directional.

Labels keep every train-eligible WP33 box that stays in the window, as `derived_key x y w h`.
Excluded and UNKNOWN boxes stay unlabelled, as in the source frame. Augmented images are
training-only and inherit the source frame's D-02 group, which must be in the training split.

Commands: `generate` writes images and labels under `data/processed/wp35_enrichment/` (git-ignored)
plus lineage, preview and manifest; `verify` regenerates everything and compares bytes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import shutil
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"
PACKAGE_STATUS = "WP35_REAL_FRAME_AUGMENTATION_AWAITING_QA"
BOUNDARY = "TRAIN_ONLY_AUGMENTED_REAL_FRAMES_NOT_EVALUATION_EVIDENCE_NO_SPLIT_NO_TRAINING_RUN"
SEED = 20261017
IMAGES_PER_CLASS = 150
MAX_ANGLE = 5.0
CROP_SCALE = (0.55, 0.95)
MIN_TARGET_PX = 12

INVENTORY = Path("results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
WP33_BOXES = Path("docs/review/generated/wp33_derived_boxes.csv")
D02_REGISTRY = Path("docs/review/generated/d02_group_id_registry.csv")
D04_DECISIONS = Path("docs/review/generated/d04_owner_decisions_part1.csv")
D04_RECORD = Path("docs/review/d04_owner_decision_part1_record.md")
PINNED_SOURCES = {
    INVENTORY.as_posix(): "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022",
    WP33_BOXES.as_posix(): "4b9307003ce8fd3c1d50763a5950d3d57cf6b2ee6df3aeef74621707067501c0",
    D02_REGISTRY.as_posix(): "c3b11f4c143627fd777270b34e40486bf92fd6e82e4c306187165fef4f7155d3",
    D04_DECISIONS.as_posix(): "62de39245a22292a9404702427d8b6bf3a9f746e081163d12198263815bc5409",
    D04_RECORD.as_posix(): "0b8ff5b9b73e1aaf8d4efc78ab2eeab83d7d5a87d891988f687656771c854230",
}

OUT_ROOT = Path("data/processed/wp35_enrichment")
LINEAGE_PATH = Path("docs/review/generated/wp35_enrichment_lineage.csv")
MANIFEST_PATH = Path("docs/review/generated/wp35_enrichment_manifest.json")
REPORT_PATH = Path("docs/review/wp35_rare_class_enrichment_report.md")
ASSETS = Path("docs/review/assets/wp35")
LINEAGE_FIELDS = [
    "augmented_id", "derived_key", "source_stem", "source_group_id", "angle_deg", "crop_scale",
    "crop_x", "crop_y", "photometric", "kept_boxes", "target_box", "image_sha256", "label_sha256",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify_pins(repo_root: Path) -> None:
    for relative, digest in PINNED_SOURCES.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or sha256_bytes(path.read_bytes()) != digest:
            raise ValueError(f"pinned WP35 source changed: {relative}")


def load_context(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    verify_pins(repo_root)
    inventory = {row["stem"]: row for row in read_csv(repo_root / INVENTORY)}
    group_of = {row["stem"]: row["group_id"] for row in read_csv(repo_root / D02_REGISTRY)}
    classes = sorted(row["derived_key"] for row in read_csv(repo_root / D04_DECISIONS) if row["owner_decision"] == "TRAIN_WITH_ENRICHMENT")
    if len(classes) != 12:
        raise ValueError("WP35 expects the 12 classes of the D-04 part 1 owner decision")
    boxes: dict[str, list[dict[str, str]]] = defaultdict(list)
    for box in read_csv(repo_root / WP33_BOXES):
        if box["stem"] in group_of:
            boxes[box["stem"]].append(box)
    sources = {
        key: sorted({stem for stem in boxes for b in boxes[stem] if b["derived_key"] == key and b["train_eligible"] == "True"})
        for key in classes
    }
    return {"inventory": inventory, "group_of": group_of, "boxes": boxes, "sources": sources, "classes": classes, "raw_root": raw_root}


def pixel_boxes(boxes: list[dict[str, str]], width: int, height: int) -> list[tuple[dict[str, str], np.ndarray]]:
    result = []
    for box in boxes:
        x, y, w, h = (float(box[k]) for k in "xywh")
        corners = np.array([
            [(x - w / 2) * width, (y - h / 2) * height], [(x + w / 2) * width, (y - h / 2) * height],
            [(x + w / 2) * width, (y + h / 2) * height], [(x - w / 2) * width, (y + h / 2) * height],
        ])
        result.append((box, corners))
    return result


def plan_geometry(rng: random.Random, width: int, height: int, boxes: list[tuple[dict[str, str], np.ndarray]], target: dict[str, str], max_angle: float = MAX_ANGLE, identity: bool = False) -> tuple[np.ndarray, float, float, float, float, list[tuple[dict[str, str], tuple[float, float, float, float]]]] | None:
    if identity:
        angle, scale, cx, cy = 0.0, 1.0, width / 2, height / 2
    else:
        angle = rng.uniform(-max_angle, max_angle)
        scale = rng.uniform(*CROP_SCALE)
        cw, ch = width * scale, height * scale
        cx, cy = rng.uniform(cw / 2, width - cw / 2), rng.uniform(ch / 2, height - ch / 2)
    # Output pixel (u, v) samples the source at centre + R(angle) * scale * ((u, v) - out_centre).
    theta = math.radians(angle)
    cos, sin = math.cos(theta), math.sin(theta)
    out_to_src = np.array([[cos * scale, -sin * scale, 0.0], [sin * scale, cos * scale, 0.0]])
    out_to_src[:, 2] = np.array([cx, cy]) - out_to_src[:, :2] @ np.array([width / 2, height / 2])
    src_corners = np.array([[0, 0, 1], [width, 0, 1], [width, height, 1], [0, height, 1]], dtype=float) @ out_to_src.T
    if src_corners[:, 0].min() < 0 or src_corners[:, 1].min() < 0 or src_corners[:, 0].max() > width or src_corners[:, 1].max() > height:
        return None
    src_to_out = cv2.invertAffineTransform(out_to_src)
    kept = []
    target_inside = False
    for box, corners in boxes:
        out = np.c_[corners, np.ones(4)] @ src_to_out.T
        x0, y0, x1, y1 = out[:, 0].min(), out[:, 1].min(), out[:, 0].max(), out[:, 1].max()
        if identity:
            x0, y0, x1, y1 = max(0.0, x0), max(0.0, y0), min(float(width), x1), min(float(height), y1)
        inside = identity or (x0 >= 0 and y0 >= 0 and x1 <= width and y1 <= height)
        outside = x1 <= 0 or y1 <= 0 or x0 >= width or y0 >= height
        if not inside and not outside:
            return None  # never cut a sign: a half-visible unlabelled sign is wrong supervision
        if inside:
            if box is target:
                if max(x1 - x0, y1 - y0) < MIN_TARGET_PX and not identity:
                    return None
                target_inside = True
            kept.append((box, (x0, y0, x1, y1)))
    if not target_inside:
        return None
    return out_to_src, angle, scale, cx, cy, kept


def photometric(image: np.ndarray, rng: random.Random) -> tuple[np.ndarray, list[str]]:
    applied = []
    data = image.astype(np.float32)
    brightness, contrast = rng.uniform(0.6, 1.3), rng.uniform(0.7, 1.3)
    data = (data - 127.5) * contrast + 127.5 * brightness
    applied += [f"brightness:{brightness:.2f}", f"contrast:{contrast:.2f}"]
    gamma = rng.uniform(0.75, 1.35)
    data = 255.0 * np.power(np.clip(data, 0, 255) / 255.0, gamma)
    applied.append(f"gamma:{gamma:.2f}")
    hsv = cv2.cvtColor(np.clip(data, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    saturation, hue = rng.uniform(0.6, 1.3), rng.uniform(-4, 4)
    hsv[..., 1] = np.clip(hsv[..., 1] * saturation, 0, 255)
    hsv[..., 0] = (hsv[..., 0] + hue) % 180
    data = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)
    applied += [f"saturation:{saturation:.2f}", f"hue:{hue:.1f}"]
    if rng.random() < 0.25:
        haze = rng.uniform(0.1, 0.35)
        data = data * (1 - haze) + 200.0 * haze
        applied.append(f"haze:{haze:.2f}")
    blur = rng.random()
    if blur < 0.3:
        sigma = rng.uniform(0.5, 1.6)
        data = cv2.GaussianBlur(data, (0, 0), sigma)
        applied.append(f"gaussian_blur:{sigma:.1f}")
    elif blur < 0.5:
        length = rng.randint(3, 9)
        kernel = np.zeros((length, length), np.float32)
        kernel[length // 2, :] = 1.0 / length
        data = cv2.filter2D(data, -1, kernel)
        applied.append(f"motion_blur:{length}")
    if rng.random() < 0.4:
        sigma = rng.uniform(3, 10)
        data = data + np.random.default_rng(rng.randint(0, 2**31)).normal(0, sigma, data.shape)
        applied.append(f"noise:{sigma:.1f}")
    return np.clip(data, 0, 255).astype(np.uint8), applied


def augment(context: dict[str, Any], key: str, index: int) -> tuple[bytes, bytes, dict[str, Any]]:
    rng = random.Random(f"{SEED}:{key}:{index}")
    sources = context["sources"][key]
    stem = sources[index % len(sources)]
    record = context["inventory"][stem]
    with Image.open(context["raw_root"] / record["image_path"]) as image:
        frame = np.asarray(image.convert("RGB"))
    height, width = frame.shape[:2]
    all_boxes = pixel_boxes(context["boxes"][stem], width, height)
    targets = [box for box, _c in all_boxes if box["derived_key"] == key and box["train_eligible"] == "True"]
    target = targets[rng.randrange(len(targets))]
    # Fall back step by step when a sign sits at the frame edge: rotation + zoom, then zoom only,
    # then photometry only (identity geometry).
    plan = None
    for max_angle, attempts in ((MAX_ANGLE, 300), (0.0, 300)):
        for _attempt in range(attempts):
            plan = plan_geometry(rng, width, height, all_boxes, target, max_angle=max_angle)
            if plan is not None:
                break
        if plan is not None:
            break
    if plan is None:
        plan = plan_geometry(rng, width, height, all_boxes, target, identity=True)
    if plan is None:
        raise RuntimeError(f"no valid geometry for {key}#{index} on {stem}")
    out_to_src, angle, scale, cx, cy, kept = plan
    warped = cv2.warpAffine(frame, out_to_src, (width, height), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
    pixels, applied = photometric(warped, rng)
    quality = rng.randint(50, 95)
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="JPEG", quality=quality)
    applied.append(f"jpeg:{quality}")
    lines, target_box = [], ""
    for box, (x0, y0, x1, y1) in kept:
        if box["train_eligible"] != "True":
            continue
        values = f"{(x0 + x1) / 2 / width:.6f} {(y0 + y1) / 2 / height:.6f} {(x1 - x0) / width:.6f} {(y1 - y0) / height:.6f}"
        lines.append(f"{box['derived_key']} {values}")
        if box is target:
            target_box = values
    label = ("\n".join(lines) + "\n").encode("utf-8")
    image_bytes = buffer.getvalue()
    augmented_id = f"wp35_{key.replace(':', '_').replace('.', 'p')}_{index:04d}"
    row = {
        "augmented_id": augmented_id, "derived_key": key, "source_stem": stem,
        "source_group_id": context["group_of"][stem], "angle_deg": f"{angle:.2f}",
        "crop_scale": f"{scale:.3f}", "crop_x": f"{cx:.1f}", "crop_y": f"{cy:.1f}",
        "photometric": ";".join(applied), "kept_boxes": str(len(lines)), "target_box": target_box,
        "image_sha256": sha256_bytes(image_bytes), "label_sha256": sha256_bytes(label),
    }
    return image_bytes, label, row


def generate(context: dict[str, Any]) -> list[tuple[bytes, bytes, dict[str, Any]]]:
    jobs = [(key, index) for key in context["classes"] for index in range(IMAGES_PER_CLASS)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(lambda job: augment(context, *job), jobs))


def preview(context: dict[str, Any], results: list[tuple[bytes, bytes, dict[str, Any]]]) -> bytes:
    """Per class: the original frame, then three augmented variants; target box in green."""
    tile_w, tile_h = 400, 225
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 15)
    by_class: dict[str, list[tuple[bytes, dict[str, Any]]]] = defaultdict(list)
    for image_bytes, _label, row in results:
        by_class[row["derived_key"]].append((image_bytes, row))
    sheet = Image.new("RGB", (tile_w * 4, (tile_h + 24) * len(by_class)), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    for row_index, key in enumerate(context["classes"]):
        items = by_class[key]
        first = items[0][1]
        record = context["inventory"][first["source_stem"]]
        original = Image.open(context["raw_root"] / record["image_path"]).convert("RGB")
        source_box = next(b for b in context["boxes"][first["source_stem"]] if b["derived_key"] == key)
        panels = [(original, f"{source_box['x']} {source_box['y']} {source_box['w']} {source_box['h']}", f"{key} · ORIGINAL {first['source_stem']}")]
        for image_bytes, row in (items[0], items[len(items) // 3], items[2 * len(items) // 3]):
            panels.append((Image.open(io.BytesIO(image_bytes)).convert("RGB"), row["target_box"], f"{key} · {row['source_stem']} · {row['angle_deg']}° · ×{row['crop_scale']}"))
        for col, (frame, box, caption) in enumerate(panels):
            x, y, w, h = (float(v) for v in box.split())
            ImageDraw.Draw(frame).rectangle(
                ((x - w / 2) * frame.width - 4, (y - h / 2) * frame.height - 4, (x + w / 2) * frame.width + 4, (y + h / 2) * frame.height + 4),
                outline=(0, 255, 0), width=max(2, frame.width // 320),
            )
            sheet.paste(frame.resize((tile_w, tile_h)), (col * tile_w, row_index * (tile_h + 24) + 24))
            draw.text((col * tile_w + 4, row_index * (tile_h + 24) + 4), caption, fill=(0, 0, 0), font=font)
    buffer = io.BytesIO()
    sheet.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


def render_docs(context: dict[str, Any], results: list[tuple[bytes, bytes, dict[str, Any]]]) -> dict[Path, bytes]:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=LINEAGE_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(row for _i, _l, row in results)
    lineage = buffer.getvalue().encode("utf-8")
    groups = sorted({row["source_group_id"] for _i, _l, row in results})
    table = "\n".join(f"| `{key}` | {len(context['sources'][key])} | {IMAGES_PER_CLASS} |" for key in context["classes"])
    report = f"""# M0-WP35 — real-frame augmentation for the 12 rare classes

Status: `{PACKAGE_STATUS}`
Boundary: `{BOUNDARY}`

Implements D-04 part 1 as revised on 2026-10-17 (`{D04_RECORD.as_posix()}`): the 12 one-group rare
classes are enriched only by transforming the original DATASET01 frames that contain them. No sign
is pasted or synthesised.

## Method

- **Geometry**: rotation ±{MAX_ANGLE:.0f}° and a zoom-in crop window of {int(CROP_SCALE[0] * 100)}–{int(CROP_SCALE[1] * 100)} % of the frame at a
  random offset, resized back to the original resolution. The window must stay inside the rotated
  frame (no padding or mirroring), must contain the target box (≥ {MIN_TARGET_PX} px) and must not cut
  any labelled sign: each box is fully inside or fully outside.
- **Photometry**: brightness, contrast, gamma, saturation, small hue shift (±4), haze (25 %),
  Gaussian or motion blur (50 %), Gaussian noise (40 %), JPEG quality 50–95.
- **No horizontal flip.** Boxes are transformed with the image and re-fitted axis-aligned.
- Labels keep every train-eligible WP33 box inside the window; excluded and UNKNOWN boxes stay
  unlabelled, exactly as in the source frame.
- When a sign sits at the frame edge and no window fits, the generator first drops the rotation
  and then falls back to photometry only (crop scale 1.000 in the lineage).
- Deterministic: seed `{SEED}`; `verify` regenerates every image and label byte-for-byte.

## Output

{len(results)} augmented images, written to `{OUT_ROOT.as_posix()}/` (git-ignored).

| Class | Real source frames | Augmented images |
| --- | --- | --- |
{table}

Source groups ({len(groups)}): {', '.join(groups)}.
Preview: `{ASSETS.as_posix()}/preview.jpg` (original frame, then three augmented variants; target box in green).

## Limits

- Every augmented image shows the same physical sign as its source frame; augmentation widens
  viewing conditions but adds no new sign instance. Classes with 3–5 source frames (W.233,
  W.246c, W.239b 2,7 m) remain weak.
- Augmented images are **training only** and must never be used for validation, test, thresholds
  or any reported accuracy.
- The source groups above must be in the training split.
- The 12 classes stay `EVAL_PENDING_REAL_INDEPENDENT_DATA` and must not trigger automatic
  simulated vehicle behaviour until evaluated on real images from another location.

## Governance

D-04 part 1 only. Gate 0 remains BLOCKED (D-04 for the other 42 classes, G0.7, G0.9, D-05).
No split was generated and no training was run.
"""
    manifest = {
        "schema_version": 2,
        "package": "M0-WP35",
        "status": PACKAGE_STATUS,
        "evidence_boundary": BOUNDARY,
        "method": "REAL_FRAME_AUGMENTATION_ONLY_NO_SIGN_INSERTION",
        "seed": SEED,
        "images_per_class": IMAGES_PER_CLASS,
        "pinned_sources": PINNED_SOURCES,
        "source_groups": groups,
        "lineage_sha256": sha256_bytes(lineage),
        "builder_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "training_only": True,
        "gate0": "BLOCKED",
        "split_authorized": False,
        "training_authorized": False,
    }
    return {
        LINEAGE_PATH: lineage,
        REPORT_PATH: report.encode("utf-8"),
        ASSETS / "preview.jpg": preview(context, results),
        MANIFEST_PATH: (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"),
    }


def run_generate(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    context = load_context(repo_root, raw_root)
    results = generate(context)
    out = repo_root / OUT_ROOT
    if out.exists():
        shutil.rmtree(out)
    (out / "images").mkdir(parents=True)
    (out / "labels").mkdir(parents=True)
    for image_bytes, label, row in results:
        (out / "images" / f"{row['augmented_id']}.jpg").write_bytes(image_bytes)
        (out / "labels" / f"{row['augmented_id']}.txt").write_bytes(label)
    for path, payload in render_docs(context, results).items():
        (repo_root / path).parent.mkdir(parents=True, exist_ok=True)
        (repo_root / path).write_bytes(payload)
    return {"status": PACKAGE_STATUS, "images": len(results)}


def verify(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    try:
        context = load_context(repo_root, raw_root)
        results = generate(context)
        expected = render_docs(context, results)
    except (OSError, KeyError, ValueError, RuntimeError) as exc:
        return {"valid": False, "errors": [str(exc)], "status": PACKAGE_STATUS}
    errors = [f"doc differs: {path.as_posix()}" for path, payload in expected.items() if not (repo_root / path).is_file() or (repo_root / path).read_bytes() != payload]
    out = repo_root / OUT_ROOT
    if out.is_dir():
        names = set()
        for image_bytes, label, row in results:
            for sub, payload, suffix in (("images", image_bytes, ".jpg"), ("labels", label, ".txt")):
                target = out / sub / f"{row['augmented_id']}{suffix}"
                names.add(target.name)
                if not target.is_file() or target.read_bytes() != payload:
                    errors.append(f"augmented file differs: {sub}/{target.name}")
        errors += [f"unexpected file: {p.name}" for sub in ("images", "labels") for p in (out / sub).iterdir() if p.name not in names]
    if (repo_root / ASSETS).is_dir():
        errors += [f"unexpected asset: {p.name}" for p in (repo_root / ASSETS).iterdir() if ASSETS / p.name not in expected]
    return {"valid": not errors, "errors": errors[:20], "images": len(results), "status": PACKAGE_STATUS}


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("generate", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        command.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    args = root.parse_args(argv)
    repo_root, raw_root = args.repo_root.resolve(), args.raw_root.resolve()
    if args.command == "generate":
        result, ok = run_generate(repo_root, raw_root), True
    else:
        result = verify(repo_root, raw_root)
        ok = result["valid"]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
