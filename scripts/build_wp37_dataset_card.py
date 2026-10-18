#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and verify M0-WP37: the G0.9 dataset card of DATASET01.

G0.9 was PARTIAL because the WP1 card (`docs/dataset01_audit.md`) lacked capture conditions, the
license decision and group lineage. WP37 assembles one card from the approved and QA-passed
records (D-01…D-04, WP33, WP36-R1, G0.7 acceptance, WP35) and measures image-level capture proxies
from the raw frames:

- resolution and orientation (from the WP1 inventory);
- mean luminance and an edge-strength sharpness proxy, computed on a JPEG draft decode in grey.

The proxies are measurements, not metadata: DATASET01 has no EXIF, GPS, time or camera fields, so
place, date, weather and device stay UNKNOWN. Every number in the card is re-derived by `verify`.
No image is written, no label is changed, nothing is trained.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import PIL
from PIL import Image, ImageFilter, ImageStat

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"
PACKAGE_STATUS = "WP37_AWAITING_QA_REVIEW"
BOUNDARY = "DATASET_CARD_DOCUMENTATION_ONLY_NO_LABEL_CHANGE_NO_TRAINING"
DRAFT_SIZE = (480, 270)
LUMA_BUCKETS = ((60.0, "DARK"), (100.0, "DIM"), (float("inf"), "BRIGHT"))
SPLITS = ("train", "val", "test")
ATTRIBUTION = (
    "DATASET01 = huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign@d869116 "
    "(creator: Data Palpating Team), CC-BY-SA, archive SHA-256 "
    "052bc980a7206f8ddd1ec2e59098dbd60a42036d3c7f7384ace4fe6416cbaa76"
)

GENERATED = Path("docs/review/generated")
INVENTORY = Path("results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
TAXONOMY = GENERATED / "wp33_derived_taxonomy.csv"
BOXES = GENERATED / "wp33_derived_boxes.csv"
REGISTRY = GENERATED / "d02_group_id_registry.csv"
D04_PART1 = GENERATED / "d04_owner_decisions_part1.csv"
D04_PART2 = GENERATED / "d04_owner_decisions_part2.csv"
SPLIT_FRAMES = GENERATED / "wp36_r1_split_frames.csv"
SPLIT_MANIFEST = GENERATED / "wp36_r1_split_manifest.json"
COVERAGE = GENERATED / "wp36_r1_class_coverage.csv"
WP35_LINEAGE = GENERATED / "wp35_enrichment_lineage.csv"
PINNED_SOURCES = {
    str(INVENTORY): "d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022",
    str(TAXONOMY): "199ddd322aa05d4875af809c1c7c1459198ebf91ada24f406cbf039c406fa5ad",
    str(BOXES): "4b9307003ce8fd3c1d50763a5950d3d57cf6b2ee6df3aeef74621707067501c0",
    str(REGISTRY): "c3b11f4c143627fd777270b34e40486bf92fd6e82e4c306187165fef4f7155d3",
    str(D04_PART1): "62de39245a22292a9404702427d8b6bf3a9f746e081163d12198263815bc5409",
    str(D04_PART2): "8030f4fd7098b971009dd86831b877701dedbc24c8901fe938a352615f959c6d",
    str(SPLIT_FRAMES): "8e197d9c7103ac5dc6b7ffc8a3d1aeb30bb6034048d470e4887dd868df95823a",
    str(SPLIT_MANIFEST): "064259941895d35054e87a550bf69199c4cae8ffeb4c83b4d7cdf608673438d9",
    str(COVERAGE): "598309eb0c02307c2b19a6846745e2ad840b177dc62008309649b50b3edf5851",
    str(WP35_LINEAGE): "e802fc264feff5168c28b531801af04051a36accc3c893ad5ab2e72975d38fed",
    "docs/dataset01_audit.md": "6cb1ccaca832847fe8614f7b86aaca6fc5f8613c807e1d981fd63227bec77478",
    "docs/review/d01_owner_decision_record.md": "8b400faf68b2805c8116362226c0d1e61e507b8957a8308c552dc6a1accc3d2b",
    "docs/review/d02_owner_decision_record.md": "2b071cbff4a15c3b1c96b418ad9c8c56a12ec9bbf8ce7155c16baed41a412e85",
    "docs/review/d03_owner_decision_part1_record.md": "54c2cf2b42a1230e2c66dfef4d9388ed3159ca3dfe077fa77a70751c0c3b96e5",
    "docs/review/d03_owner_decision_part2_record.md": "93044c877b517ecb063895ed2da0ece9daa8660cba2f662dcc0bd9927944dc7a",
    "docs/review/d04_owner_decision_part1_record.md": "0b8ff5b9b73e1aaf8d4efc78ab2eeab83d7d5a87d891988f687656771c854230",
    "docs/review/d04_owner_decision_part2_record.md": "984ce4d758483e5996443b0c25b0c391ca0cd11b1607ae501393b68e6c72562e",
    "docs/review/g07_owner_acceptance_record.md": "88d5c16e2041b23e43e5381b7107d9de2d4a11635124c876263802abc2dce32a",
    "docs/review/wp36_r1_independent_qa_record.md": "a71d1894093c3a2ca4ff060658596c06458891f9dd4740e7b6c9abf2ef4f9056",
}

CAPTURE_PATH = GENERATED / "wp37_capture_conditions.csv"
LINEAGE_PATH = GENERATED / "wp37_group_lineage.csv"
CLASSES_PATH = GENERATED / "wp37_class_card.csv"
MANIFEST_PATH = GENERATED / "wp37_manifest.json"
CARD_PATH = Path("docs/dataset01_card.md")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def csv_bytes(fields: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        if sha256_bytes((repo_root / relative).read_bytes()) != expected:
            raise ValueError(f"pinned source changed: {relative}")


def luma_bucket(value: float) -> str:
    return next(name for limit, name in LUMA_BUCKETS if value < limit)


def measure(path: Path) -> tuple[float, float]:
    """Mean luminance and mean edge strength on a deterministic grey draft decode."""
    with Image.open(path) as image:
        image.draft("L", DRAFT_SIZE)
        grey = image.convert("L")
        luma = ImageStat.Stat(grey).mean[0]
        edges = ImageStat.Stat(grey.filter(ImageFilter.FIND_EDGES)).mean[0]
    return round(luma, 2), round(edges, 2)


def quartiles(values: list[float]) -> str:
    if len(values) < 2:
        return f"{values[0]:.1f}" if values else "—"
    q = statistics.quantiles(values, n=4, method="inclusive")
    return f"{q[0]:.1f} / {statistics.median(values):.1f} / {q[2]:.1f}"


def render(repo_root: Path, raw_root: Path) -> dict[Path, bytes]:
    verify_pins(repo_root)
    inventory = read_csv(repo_root / INVENTORY)
    split_rows = {row["stem"]: row for row in read_csv(repo_root / SPLIT_FRAMES)}
    taxonomy = read_csv(repo_root / TAXONOMY)
    boxes = read_csv(repo_root / BOXES)
    coverage = {row["derived_key"]: row for row in read_csv(repo_root / COVERAGE)}
    split_manifest = json.loads((repo_root / SPLIT_MANIFEST).read_text(encoding="utf-8"))
    lineage = read_csv(repo_root / WP35_LINEAGE)

    images_dir = raw_root / "archive/images"
    stems = [row["stem"] for row in inventory]
    with ThreadPoolExecutor(max_workers=8) as pool:
        measured = dict(zip(stems, pool.map(lambda s: measure(images_dir / f"{s}.jpg"), stems), strict=True))

    capture = []
    for row in inventory:
        stem = row["stem"]
        split = split_rows.get(stem)
        luma, edges = measured[stem]
        width, height = int(row["width"]), int(row["height"])
        capture.append({
            "stem": stem,
            "group_id": split["group_id"] if split else "",
            "split": split["split"] if split else "",
            "use": split["use"] if split else "QUARANTINED_G04",
            "width": width, "height": height,
            "orientation": "PORTRAIT" if height > width else "LANDSCAPE",
            "mean_luma": f"{luma:.2f}", "luma_bucket": luma_bucket(luma),
            "edge_strength": f"{edges:.2f}",
            "has_exif": row["has_exif"], "has_gps": row["has_gps"],
        })

    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in capture:
        if row["group_id"]:
            by_group[row["group_id"]].append(row)
    box_groups: dict[str, Counter[str]] = defaultdict(Counter)
    for box in boxes:
        if box["train_eligible"] == "True" and box["stem"] in split_rows:
            box_groups[split_rows[box["stem"]]["group_id"]][box["derived_key"]] += 1
    wp35_groups = Counter(row["source_group_id"] for row in lineage)
    group_rows = []
    for group in sorted(by_group):
        rows = by_group[group]
        resolutions = Counter(f"{r['width']}x{r['height']}" for r in rows)
        lumas = [float(r["mean_luma"]) for r in rows]
        group_rows.append({
            "group_id": group,
            "frames": len(rows),
            "first_stem": rows[0]["stem"], "last_stem": rows[-1]["stem"],
            "split": rows[0]["split"],
            "quarantined_negatives": sum(1 for r in rows if r["use"] == "QUARANTINED"),
            "resolutions": " ".join(f"{k}:{v}" for k, v in sorted(resolutions.items())),
            "median_luma": f"{statistics.median(lumas):.1f}",
            "luma_buckets": " ".join(f"{k}:{v}" for k, v in sorted(Counter(r["luma_bucket"] for r in rows).items())),
            "classes": len(box_groups[group]),
            "train_eligible_boxes": sum(box_groups[group].values()),
            "wp35_enriched_images": wp35_groups.get(group, 0),
            "lineage": "WP5 edges → WP7–WP30-R1 reviews → WP31-R2 capture groups → D-02 (owner 2026-10-17)",
        })

    decision = {row["derived_key"]: "TRAIN_WITH_ENRICHMENT" for row in read_csv(repo_root / D04_PART1)}
    decision.update({row["derived_key"]: row["owner_decision"] for row in read_csv(repo_root / D04_PART2)})
    class_rows = []
    for row in taxonomy:
        key = row["derived_key"]
        cov = coverage.get(key)
        class_rows.append({
            "derived_key": key, "derived_code": row["derived_code"], "name_vi": row["derived_name_vi"],
            "role": row["role"], "train_boxes": row["train_boxes"], "excluded_boxes": row["excluded_boxes"],
            "d04_decision": cov["d04_decision"] if cov else "",
            "split_boxes_train_val_test": f"{cov['train_boxes']}/{cov['val_boxes']}/{cov['test_boxes']}" if cov else "",
            "sealed_test": bool(cov and int(cov["test_groups"]) > 0),
            "tuning_allowed": bool(cov and cov["usable_for_tuning"] == "True"),
            "wp35_enriched_images": sum(1 for r in lineage if r["derived_key"] == key),
            "evaluation_status": (
                "TEST_ON_HELD_OUT_GROUPS" if cov and int(cov["test_groups"]) > 0
                else "EVAL_PENDING_REAL_INDEPENDENT_DATA" if cov else "NOT_TRAINED"
            ),
        })
    if set(decision) != {r["derived_key"] for r in class_rows if r["role"] == "CLASS"}:
        raise ValueError("D-04 decisions do not cover the WP33 classes")

    artifacts: dict[Path, bytes] = {
        CAPTURE_PATH: csv_bytes(list(capture[0]), capture),
        LINEAGE_PATH: csv_bytes(list(group_rows[0]), group_rows),
        CLASSES_PATH: csv_bytes(list(class_rows[0]), class_rows),
    }
    stats = summarise(capture, split_manifest)
    reasons = Counter(f"{box['eval_role']} ({box['reason']})" for box in boxes if box["train_eligible"] != "True")
    stats["boxes"] = {
        "total": len(boxes),
        "train_eligible": sum(1 for box in boxes if box["train_eligible"] == "True"),
        "not_trained": "; ".join(f"{k}: {v}" for k, v in sorted(reasons.items())),
    }
    manifest = {
        "package": "M0-WP37", "status": PACKAGE_STATUS, "boundary": BOUNDARY,
        "pillow_version": PIL.__version__, "draft_size": list(DRAFT_SIZE),
        "luma_buckets": [[limit if limit != float("inf") else None, name] for limit, name in LUMA_BUCKETS],
        "summary": stats,
        "pinned_sources": PINNED_SOURCES,
        "artifacts": {str(path): sha256_bytes(payload) for path, payload in sorted(artifacts.items())},
        "training_authorized": False,
    }
    artifacts[MANIFEST_PATH] = (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    artifacts[CARD_PATH] = render_card(stats, capture, group_rows, class_rows, split_manifest, len(lineage)).encode("utf-8")
    return artifacts


def summarise(capture: list[dict[str, Any]], split_manifest: dict[str, Any]) -> dict[str, Any]:
    usable = [r for r in capture if r["use"] in ("TRAIN", "VAL", "TEST", "BACKGROUND")]
    per_split: dict[str, Any] = {}
    for split in SPLITS:
        rows = [r for r in usable if r["split"] == split]
        per_split[split] = {
            "frames": len(rows),
            "resolutions": dict(sorted(Counter(f"{r['width']}x{r['height']}" for r in rows).items())),
            "luma_buckets": dict(sorted(Counter(r["luma_bucket"] for r in rows).items())),
            "luma_quartiles": quartiles([float(r["mean_luma"]) for r in rows]),
            "edge_quartiles": quartiles([float(r["edge_strength"]) for r in rows]),
        }
    return {
        "raw_frames": len(capture),
        "usable_frames": len(usable),
        "quarantined_negatives": sum(1 for r in capture if r["use"] == "QUARANTINED"),
        "quarantined_g04": sum(1 for r in capture if r["use"] == "QUARANTINED_G04"),
        "exif_frames": sum(1 for r in capture if r["has_exif"] == "True"),
        "gps_frames": sum(1 for r in capture if r["has_gps"] == "True"),
        "per_split": per_split,
        "test_seal_sha256": split_manifest["test_seal_sha256"],
        "split_list_sha256": split_manifest["split_list_sha256"],
    }


def render_card(stats: dict[str, Any], capture: list[dict[str, Any]], groups: list[dict[str, Any]],
                classes: list[dict[str, Any]], split_manifest: dict[str, Any], enriched: int) -> str:
    per = stats["per_split"]
    res_keys = sorted({k for s in SPLITS for k in per[s]["resolutions"]})
    bucket_keys = [name for _limit, name in LUMA_BUCKETS]
    split_table = "\n".join(
        f"| {s} | {per[s]['frames']} | "
        + " | ".join(str(per[s]["resolutions"].get(k, 0)) for k in res_keys)
        + " | " + " | ".join(str(per[s]["luma_buckets"].get(k, 0)) for k in bucket_keys)
        + f" | {per[s]['luma_quartiles']} | {per[s]['edge_quartiles']} |"
        for s in SPLITS
    )
    class_table = "\n".join(
        f"| {c['derived_key']} | {c['derived_code']} | {c['name_vi']} | {c['role']} | {c['train_boxes']} | "
        f"{c['d04_decision'] or '—'} | {c['split_boxes_train_val_test'] or '—'} | "
        f"{'có' if c['sealed_test'] else 'không'} | {'có' if c['tuning_allowed'] else 'không'} | {c['wp35_enriched_images']} |"
        for c in classes
    )
    group_table = "\n".join(
        f"| {g['group_id']} | {g['frames']} | {g['first_stem']}–{g['last_stem']} | {g['split']} | {g['resolutions']} | "
        f"{g['median_luma']} | {g['classes']} | {g['train_eligible_boxes']} | {g['wp35_enriched_images']} |"
        for g in groups
    )
    dark = [r["stem"] for r in capture if r["luma_bucket"] == "DARK" and r["use"] in ("TRAIN", "VAL", "TEST", "BACKGROUND")]
    shift = []
    for key in res_keys:
        where = [sp for sp in SPLITS if per[sp]["resolutions"].get(key)]
        if len(where) < len(SPLITS):
            shift.append(f"{key} chỉ có ở {', '.join(where)}")
    for name in bucket_keys:
        where = [sp for sp in SPLITS if per[sp]["luma_buckets"].get(name)]
        if 0 < len(where) < len(SPLITS):
            shift.append(f"{name} chỉ có ở {', '.join(where)}")
    no_test = [c["derived_key"] for c in classes if c["role"] == "CLASS" and not c["sealed_test"]]
    no_tune = [c["derived_key"] for c in classes if c["role"] == "CLASS" and c["sealed_test"] and not c["tuning_allowed"]]
    return f"""# DATASET01 — dataset card (M0-WP37, G0.9)

Trạng thái: `{PACKAGE_STATUS}` · Boundary: `{BOUNDARY}`

Card này thay phần "dataset card" của `docs/dataset01_audit.md` (WP1, giữ nguyên làm hồ sơ audit
kỹ thuật). Mỗi con số được sinh lại bởi `scripts/build_wp37_dataset_card.py verify`. Nhãn phân loại
thông tin: **VERIFIED** (đo/đối chiếu được), **OWNER DECISION** (đã duyệt), **UNKNOWN** (không có
nguồn).

## 1. Mục đích và giới hạn sử dụng

- Dùng cho: huấn luyện và đánh giá detector/classifier biển báo Việt Nam trong **mô phỏng** hỗ trợ
  lái của dự án CPV301 (nghiên cứu, học tập).
- Không dùng cho: điều khiển xe thật, tuyên bố an toàn, phát hành công khai ảnh/nhãn gốc.
- Hành vi tự động trong mô phỏng chỉ được dùng cho lớp có test niêm phong; lớp chỉ train hiển thị
  "chưa kiểm chứng" (D-04).

## 2. Nguồn, license, ghi công — OWNER DECISION (D-01)

- Ghi công bắt buộc: {ATTRIBUTION}.
- License: metadata ghi CC-BY-SA 3.0, mô tả ghi 4.0; chủ sở hữu ảnh gốc UNKNOWN. Owner chấp nhận
  rủi ro (2026-10-17) và áp điều khoản chặt hơn: share-alike CC-BY-SA 4.0 cho mọi bản phái sinh
  được phân phối, không phân phối lại ảnh/nhãn gốc, coi trọng số model có thể chịu share-alike,
  mở lại D-01 nếu có phản hồi/khiếu nại (`docs/review/d01_owner_decision_record.md`).
- Dataset gốc có liên kết tới một repo augmentation (blur/noise/brightness/contrast); không có
  bằng chứng ảnh nào là bản tăng cường của ảnh khác ngoài các cặp gần trùng đã gộp nhóm (WP32).

## 3. Thành phần — VERIFIED

- {stats['raw_frames']} ảnh và nhãn YOLO; stem 0248 cách ly (G0.4) → {stats['raw_frames'] - stats['quarantined_g04']} ảnh có
  nhóm D-02; {stats['quarantined_negatives']} ảnh âm có biển chưa gán nhãn bị cách ly → **{stats['usable_frames']} ảnh dùng được**.
- Nhãn huấn luyện chỉ lấy từ bộ dẫn xuất WP33 (`wp33_derived_boxes.csv`), không dùng class id gốc:
  {stats['boxes']['train_eligible']} box train-eligible trong 54 lớp; không train: {stats['boxes']['not_trained']}.
- Ảnh tăng cường WP35: {enriched} ảnh biến đổi từ frame thật, **chỉ dùng cho train**, không phải
  instance mới (cùng biển vật lý với ảnh nguồn).

## 4. Điều kiện chụp — VERIFIED proxy / UNKNOWN metadata

- EXIF: {stats['exif_frames']} ảnh; GPS: {stats['gps_frames']} ảnh. Địa điểm, ngày giờ, thời tiết, thiết
  bị: **UNKNOWN**. Ảnh là camera hành trình/cầm tay trên đường đô thị có xe máy dày đặc (quan sát
  của reviewer khi duyệt nhóm, không phải metadata).
- Độ sáng = trung bình luminance trên ảnh decode nháp {DRAFT_SIZE[0]}×{DRAFT_SIZE[1]} xám; bucket
  DARK < 60 ≤ DIM < 100 ≤ BRIGHT. Độ nét = trung bình FIND_EDGES (proxy, không phải đo blur chuẩn).
  Quartile ghi dạng Q1 / median / Q3.

| Split | Ảnh | {' | '.join(res_keys)} | {' | '.join(bucket_keys)} | Luma Q1/med/Q3 | Edge Q1/med/Q3 |
| --- | ---: | {' | '.join('---:' for _ in res_keys)} | {' | '.join('---:' for _ in bucket_keys)} | --- | --- |
{split_table}

- Ảnh DARK dùng được: {len(dark)}{(' (' + ', '.join(dark[:20]) + ('…' if len(dark) > 20 else '') + ')') if dark else ''}. Không có
  tập ban đêm riêng: hiệu năng ban đêm/mưa lớn là **UNKNOWN**.
- **Lệch điều kiện chụp giữa các split** (hệ quả của chia theo nhóm): {'; '.join(shift) or 'không'}.
  Val tối hơn train/test (median luma {per['val']['luma_quartiles'].split(' / ')[1]} so với train
  {per['train']['luma_quartiles'].split(' / ')[1]}, test {per['test']['luma_quartiles'].split(' / ')[1]}). Khi so sánh val với test phải báo cáo
  theo độ phân giải; kết quả trên ảnh dọc và ảnh tối chỉ có ở val, không có test niêm phong.
- Chi tiết từng ảnh: `{CAPTURE_PATH}`.

## 5. Nhóm D-02 và nguồn gốc nhóm — OWNER DECISION (D-02)

Chuỗi: cạnh ứng viên WP5 → review cạnh WP7–WP30-R1 (AI review hai lượt, QA độc lập) → nối khối
WP32 → đề xuất nhóm WP31-R2 → owner duyệt D02-P1 (54 nhóm capture, 2026-10-17). Giới hạn: không có
metadata của tác giả; nhóm là suy luận thị giác, chưa chứng minh không rò rỉ.

| Nhóm | Ảnh | Stem | Split | Độ phân giải | Luma median | Lớp | Box train-eligible | WP35 |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: |
{group_table}

## 6. Split — OWNER DECISION (G0.7, WP36-R1)

- Ảnh dùng được: train {split_manifest['usable_frames']['train']} / val {split_manifest['usable_frames']['val']} /
  test {split_manifest['usable_frames']['test']}; không nhóm nào nằm ở hai split.
- Hash danh sách (sha256 của stem đã sort nối bằng `\\n`): train `{stats['split_list_sha256']['train']}`,
  val `{stats['split_list_sha256']['val']}`, **test niêm phong** `{stats['test_seal_sha256']}`.
- Test chỉ dùng trong lần đánh giá cuối có log; loader kiểm hash + cột `use` (`g07_owner_acceptance_record.md`).
- Lớp không có test niêm phong ({len(no_test)}): {', '.join(no_test)}.
- Lớp có test nhưng không được dùng để chọn model/chỉnh ngưỡng (không có val): {', '.join(no_tune)}.

## 7. Lớp (D-03 taxonomy, D-04 quyết định, phân bố box theo split)

| Key | Mã QCVN | Tên | Vai trò | Box train-eligible | D-04 | Box train/val/test | Test niêm phong | Dùng tuning | WP35 |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | ---: |
{class_table}

## 8. Rủi ro và giới hạn đã biết

- License/ownership chưa được tác giả xác nhận (D-01 rủi ro đã chấp nhận).
- Nhóm D-02 do AI suy luận; cùng một biển vật lý có thể xuất hiện ở hai nhóm → điểm test có thể lạc quan.
- Một địa bàn/khoảng thời gian không rõ; không có dữ liệu độc lập từ nơi khác → chưa có claim triển khai.
- Box nhỏ chiếm đa số (WP1: 3.088 box có diện tích < 0,1 % ảnh).
- Val nhỏ ({split_manifest['usable_frames']['val']} ảnh) và lệch điều kiện chụp so với train/test (mục 4); chỉ dùng metric gộp để chọn model.
- Ảnh tăng cường WP35 không thêm instance mới; box sau xoay lỏng ~8 % (WP35 QA).

## 9. Kiểm chứng

```bash
uv run python scripts/build_wp37_dataset_card.py verify --repo-root . --raw-root {DEFAULT_RAW_ROOT.relative_to(REPO_ROOT)}
uv run python scripts/build_wp36_r1_group_split.py verify --repo-root .
```

## 10. G0.9 checklist

| Hạng mục | Nguồn | Trạng thái |
| --- | --- | --- |
| Nguồn, hash, staging | WP1 audit | VERIFIED |
| License + ghi công | D-01 | OWNER DECISION |
| Điều kiện chụp | WP37 capture proxy | VERIFIED proxy; metadata UNKNOWN |
| Taxonomy + nhãn dẫn xuất | D-03, WP33 | OWNER DECISION + QA PASS |
| Group lineage | D-02, WP31-R2, WP37 lineage | OWNER DECISION + QA PASS |
| Lớp hiếm / trạng thái đánh giá | D-04 part 1+2 | OWNER DECISION |
| Split + niêm phong test | G0.7, WP36-R1 | OWNER DECISION + QA PASS |
"""


def build(repo_root: Path, raw_root: Path) -> dict[str, Any]:
    artifacts = render(repo_root, raw_root)
    for path, payload in artifacts.items():
        (repo_root / path).parent.mkdir(parents=True, exist_ok=True)
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
