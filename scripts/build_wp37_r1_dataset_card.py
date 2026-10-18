#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and verify M0-WP37-R1: the revised G0.9 dataset card.

WP37 passed independent QA with one P2 and four P3 (`docs/review/wp37_independent_qa_record.md`).
WP37 stays byte-identical and pinned; `render` first re-derives WP37 and fails if it no longer
reproduces. R1 writes `docs/dataset01_card_r1.md`, the WP37 card with exact, asserted text
replacements, plus a per-frame decode table:

- P2-1: luminance buckets are scene content + exposure, not lighting; the DARK frames are daylight
  foliage scenes; the dataset has no frame verified as low-light or night; the split caution is a
  luminance/resolution distribution shift.
- P3-1: actual decode sizes per resolution and edge strength reported per resolution.
- P3-2: small boxes are ≈37 %, not a majority.
- P3-3: the mandated attribution is exactly D-01's; the creator name is an unverified claim; the
  augmentation parent of any image is UNKNOWN.
- P3-4: the reviewer observation covers most frames, not all; device type UNKNOWN.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("wp37_r1_base", Path(__file__).with_name("build_wp37_dataset_card.py"))
assert _SPEC is not None and _SPEC.loader is not None
wp37 = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = wp37
_SPEC.loader.exec_module(wp37)

DEFAULT_RAW_ROOT = wp37.DEFAULT_RAW_ROOT
PACKAGE_STATUS = "WP37_R1_AWAITING_QA_REVIEW"
PINNED_SOURCES = {
    "scripts/build_wp37_dataset_card.py": "e9dbeb40937c64679676e5803b8a20dc482738ba966e7be1cfe17ff56d45dcd5",
    "tests/test_wp37_dataset_card.py": "ac129231569686dcad7a8233b165962c13fc3695c9535f71df97320b9dae36d6",
    "docs/dataset01_card.md": "564d3cd6e572fa81d5b70b7388c590c78dba2cf411808f8eb7d678d3cb114723",
    "docs/review/generated/wp37_capture_conditions.csv": "ef0932dc736192553e22a229e6bab8978a4357b53d4a539dc9e073528056ec7d",
    "docs/review/generated/wp37_class_card.csv": "e9909ea5401f239f08077ba41e89488f6bd9c2918bef2befc381405437a34a62",
    "docs/review/generated/wp37_group_lineage.csv": "91270c9ae9d6d37cd073bce7c20c38b781432e40cfee2452bdaed231605e5b10",
    "docs/review/generated/wp37_manifest.json": "f455b32750953a40272524c747cc6c1b3c2a5da7e7a7491a8bab88d7f04010a0",
    "docs/review/wp37_independent_qa_record.md": "0bedaf5f48cfe36849a6932751654f74c483ae33e8eb6003ca039350ba931fb5",
}
DECODE_PATH = wp37.GENERATED / "wp37_r1_decode_sizes.csv"
MANIFEST_PATH = wp37.GENERATED / "wp37_r1_manifest.json"
CARD_PATH = Path("docs/dataset01_card_r1.md")
D01_ATTRIBUTION = (
    "huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign@d869116, CC-BY-SA, archive SHA-256 "
    "052bc980a7206f8ddd1ec2e59098dbd60a42036d3c7f7384ace4fe6416cbaa76"
)


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        if wp37.sha256_bytes((repo_root / relative).read_bytes()) != expected:
            raise ValueError(f"pinned source changed: {relative}")


def decode_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        image.draft("L", wp37.DRAFT_SIZE)
        return image.size


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"WP37 card text not found exactly once: {old[:60]!r}")
    return text.replace(old, new)


def render(repo_root: Path, raw_root: Path) -> dict[Path, bytes]:
    verify_pins(repo_root)
    base = wp37.render(repo_root, raw_root)
    for path, payload in base.items():
        if (repo_root / path).read_bytes() != payload:
            raise ValueError(f"WP37 no longer reproduces: {path}")
    capture = wp37.read_csv(repo_root / wp37.CAPTURE_PATH)
    images = raw_root / "archive/images"
    with ThreadPoolExecutor(max_workers=8) as pool:
        sizes = list(pool.map(lambda row: decode_size(images / f"{row['stem']}.jpg"), capture))
    decode_rows = [
        {"stem": row["stem"], "resolution": f"{row['width']}x{row['height']}", "decode_width": w, "decode_height": h,
         "mean_luma": row["mean_luma"], "luma_bucket": row["luma_bucket"], "edge_strength": row["edge_strength"]}
        for row, (w, h) in zip(capture, sizes, strict=True)
    ]
    usable = {r["stem"] for r in capture if r["use"] in ("TRAIN", "VAL", "TEST", "BACKGROUND")}
    split_of = {r["stem"]: r["split"] for r in capture}
    decode_by_res = defaultdict(Counter)
    edges: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in decode_rows:
        decode_by_res[row["resolution"]][f"{row['decode_width']}x{row['decode_height']}"] += 1
        if row["stem"] in usable:
            edges[(row["resolution"], split_of[row["stem"]])].append(float(row["edge_strength"]))
    resolutions = sorted(decode_by_res)
    dark = [r for r in capture if r["luma_bucket"] == "DARK" and r["stem"] in usable]

    card = base[wp37.CARD_PATH].decode("utf-8")
    card = replace_once(card, "# DATASET01 — dataset card (M0-WP37, G0.9)", "# DATASET01 — dataset card (M0-WP37-R1, G0.9)")
    card = replace_once(card, f"Trạng thái: `{wp37.PACKAGE_STATUS}`", f"Trạng thái: `{PACKAGE_STATUS}`")
    card = replace_once(
        card,
        "Card này thay phần \"dataset card\" của `docs/dataset01_audit.md`",
        "Bản R1 sửa WP37 theo QA (`docs/review/wp37_independent_qa_record.md`: P2-1, P3-1…P3-4); WP37\n"
        "giữ nguyên làm hồ sơ. Card này thay phần \"dataset card\" của `docs/dataset01_audit.md`",
    )
    card = replace_once(
        card,
        f"- Ghi công bắt buộc: {wp37.ATTRIBUTION}.",
        f"- Ghi công bắt buộc (đúng văn bản D-01): {D01_ATTRIBUTION}.\n"
        "- Tên người tạo \"Data Palpating Team\" chỉ có trong mô tả upload (WP3), **chưa được xác minh**.",
    )
    card = replace_once(
        card,
        "- Dataset gốc có liên kết tới một repo augmentation (blur/noise/brightness/contrast); không có\n"
        "  bằng chứng ảnh nào là bản tăng cường của ảnh khác ngoài các cặp gần trùng đã gộp nhóm (WP32).",
        "- Dataset gốc có liên kết tới một repo augmentation (blur/noise/brightness/contrast). Ảnh nào là\n"
        "  bản tăng cường, và của ảnh gốc nào, là **UNKNOWN** (WP3). Các cặp gần trùng WP32 là frame từ\n"
        "  các chuyến đi xen kẽ, không phải bằng chứng tăng cường.",
    )
    card = replace_once(
        card,
        "Ảnh là camera hành trình/cầm tay trên đường đô thị có xe máy dày đặc (quan sát\n"
        "  của reviewer khi duyệt nhóm, không phải metadata).",
        "Phần lớn ảnh là đường có xe máy đông, một số là đường vắng/thoáng\n"
        "  (ví dụ 0150, 0181, 0543) — quan sát của reviewer, không phải metadata; loại thiết bị UNKNOWN.",
    )
    decode_text = "; ".join(
        f"{res} → " + ", ".join(f"{size} ({n})" for size, n in sorted(decode_by_res[res].items())) for res in resolutions
    )
    card = replace_once(
        card,
        "- Độ sáng = trung bình luminance trên ảnh decode nháp 480×270 xám; bucket\n"
        "  DARK < 60 ≤ DIM < 100 ≤ BRIGHT. Độ nét = trung bình FIND_EDGES (proxy, không phải đo blur chuẩn).",
        "- **Bucket độ sáng trung bình (nội dung cảnh + phơi sáng), không phải điều kiện chiếu sáng.**\n"
        "  Luminance trung bình trên ảnh xám decode nháp JPEG (yêu cầu 480×270; kích thước thực:\n"
        f"  {decode_text}); bucket DARK < 60 ≤ DIM < 100 ≤ BRIGHT. Độ nét = trung bình FIND_EDGES —\n"
        "  proxy phụ thuộc độ phân giải, xem bảng theo độ phân giải bên dưới.",
    )
    card = replace_once(
        card,
        f"- Ảnh DARK dùng được: {len(dark)} ({', '.join(r['stem'] for r in dark)}). Không có\n"
        "  tập ban đêm riêng: hiệu năng ban đêm/mưa lớn là **UNKNOWN**.",
        f"- {len(dark)} ảnh bucket DARK ({', '.join(r['stem'] for r in dark)}) là **cảnh ban ngày chụp ngược tán cây**,\n"
        "  không phải ảnh thiếu sáng. Dataset **không có ảnh nào được xác minh là thiếu sáng hay ban đêm**:\n"
        "  hiệu năng ban đêm/mưa lớn là **UNKNOWN**.",
    )
    card = replace_once(card, "- **Lệch điều kiện chụp giữa các split** (hệ quả của chia theo nhóm):",
                        "- **Lệch phân bố độ sáng trung bình và độ phân giải giữa các split** (hệ quả của chia theo nhóm):")
    card = replace_once(card, "  Val tối hơn train/test (median luma", "  Val có độ sáng trung bình thấp hơn train/test (median luma")
    card = replace_once(
        card,
        "theo độ phân giải; kết quả trên ảnh dọc và ảnh tối chỉ có ở val, không có test niêm phong.",
        "theo độ phân giải; kết quả trên ảnh dọc và ảnh bucket DARK chỉ có ở val, không có test niêm phong.",
    )
    edge_rows = "\n".join(
        f"| {res} | " + " | ".join(
            f"{len(edges[(res, s)])}: {wp37.quartiles(edges[(res, s)])}" if edges[(res, s)] else "—" for s in wp37.SPLITS
        ) + " |"
        for res in resolutions
    )
    card = replace_once(
        card,
        f"- Chi tiết từng ảnh: `{wp37.CAPTURE_PATH}`.",
        "\nĐộ nét (edge Q1 / median / Q3) theo độ phân giải — so sánh chỉ có nghĩa trong cùng độ phân giải:\n\n"
        "| Độ phân giải | train | val | test |\n| --- | --- | --- | --- |\n"
        f"{edge_rows}\n\n"
        f"- Chi tiết từng ảnh: `{wp37.CAPTURE_PATH}`; kích thước decode: `{DECODE_PATH}`.",
    )
    card = replace_once(card, "- Box nhỏ chiếm đa số (WP1: 3.088 box có diện tích < 0,1 % ảnh).",
                        "- Box nhỏ nhiều: ≈37 % box (WP1: 3.088/8.334) có diện tích < 0,1 % ảnh.")
    card = replace_once(card, "- Val nhỏ (376 ảnh) và lệch điều kiện chụp so với train/test (mục 4)",
                        "- Val nhỏ (376 ảnh) và lệch phân bố độ sáng/độ phân giải so với train/test (mục 4)")
    card = replace_once(card, "uv run python scripts/build_wp37_dataset_card.py verify",
                        "uv run python scripts/build_wp37_r1_dataset_card.py verify")
    card = replace_once(card, "| Điều kiện chụp | WP37 capture proxy | VERIFIED proxy; metadata UNKNOWN |",
                        "| Điều kiện chụp | WP37 capture proxy, R1 wording + decode sizes | VERIFIED proxy; metadata UNKNOWN; không có ảnh đêm đã xác minh |")

    artifacts: dict[Path, bytes] = {
        DECODE_PATH: wp37.csv_bytes(list(decode_rows[0]), decode_rows),
        CARD_PATH: card.encode("utf-8"),
    }
    manifest = {
        "package": "M0-WP37-R1", "status": PACKAGE_STATUS, "boundary": wp37.BOUNDARY,
        "supersedes": "M0-WP37 card (QA PASS with P2-1; kept byte-identical)",
        "decode_sizes": {res: dict(sorted(decode_by_res[res].items())) for res in resolutions},
        "edge_median_by_resolution_split": {
            f"{res}/{s}": round(statistics.median(edges[(res, s)]), 2) for res in resolutions for s in wp37.SPLITS if edges[(res, s)]
        },
        "dark_bucket_stems": [r["stem"] for r in dark],
        "pinned_sources": PINNED_SOURCES,
        "wp37_artifacts": {str(p): wp37.sha256_bytes(b) for p, b in sorted(base.items())},
        "artifacts": {str(p): wp37.sha256_bytes(b) for p, b in sorted(artifacts.items())},
        "training_authorized": False,
    }
    artifacts[MANIFEST_PATH] = (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    return artifacts


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    artifacts = render(repo_root, raw_root)
    for path, payload in artifacts.items():
        (repo_root / path).write_bytes(payload)
    return {"status": PACKAGE_STATUS, "artifacts": len(artifacts)}


def verify(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    artifacts: dict[Path, bytes] = {}
    try:
        artifacts = render(repo_root, raw_root)
        for path, payload in artifacts.items():
            if not (repo_root / path).is_file() or (repo_root / path).read_bytes() != payload:
                errors.append(f"artifact differs: {path}")
    except (ValueError, OSError, KeyError) as error:
        errors.append(str(error))
    return {"status": PACKAGE_STATUS, "valid": not errors, "artifact_count": len(artifacts), "errors": errors}


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        command.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    args = root.parse_args(argv)
    repo_root, raw_root = args.repo_root.resolve(), args.raw_root.resolve()
    result = build(repo_root, raw_root) if args.command == "build" else verify(repo_root, raw_root)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if args.command == "build" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
