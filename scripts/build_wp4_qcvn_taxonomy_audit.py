# ruff: noqa: E501
"""Build and verify the evidence-only M0-WP4 QCVN taxonomy audit package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader

EXPECTED_CLASS_IDS = frozenset(range(52))
MATCH_STATUSES = frozenset({"EXACT", "PARTIAL", "MISMATCH", "NOT_FOUND", "NON_SIGN_CATEGORY"})
KNOWN_CONFLICT_EXPECTATIONS = {
    3: "PARTIAL",
    22: "PARTIAL",
    25: "MISMATCH",
    28: "MISMATCH",
    30: "MISMATCH",
    31: "NOT_FOUND",
    34: "MISMATCH",
    47: "MISMATCH",
    51: "EXACT",
}
REVIEWER_STATUS = "UNAPPROVED"
PACKAGE_STATUS = "READY_FOR_RE_REVIEW_EVIDENCE_ONLY_NO_APPROVAL"
EVIDENCE_INDEX_RELATIVE_PATH = Path(
    "references/qcvn41_2024/qcvn_taxonomy_evidence_index.json"
)
EXPECTED_EVIDENCE_INDEX_SHA256 = (
    "62233e56a47c9c7116805d2b9d38846f2a20696b952507752810a83192abd7aa"
)
QCVN_SHA256 = "b6b99d0a0aeb13fe79072831857ece15bb254d8fb7817e80e4a2739a0d2145ce"
QCVN_PAGE_COUNT = 403
PDF_RENDER_DPI = 72
NEGATIVE_SCOPE = {
    "pages": "80-154",
    "queries": ["camera", "giám sát", "surveillance"],
    "description": "QCVN sign appendices B-F; absence is scoped to these pages and queries.",
}
RESERVED_REPRESENTATIVE_STEMS = {49: ("0248",)}
SAMPLING_POLICY = (
    "Known audited boundary case 0248 is reserved first for class 49; remaining slots "
    "preserve the existing deterministic WP3 source-stem order after removing duplicates."
)
REQUIRED_BOUNDARY_CASE_0248 = {
    "class_id": 49,
    "slot_index": 1,
    "stem": "0248",
    "image_sha256": "07eab2035dc10b7b08be71d76c3c32ffdb960722839414f1e474da20c3ad0cbd",
    "label_sha256": "f4ec410f7bff3ee03f6110308e8e95f57c92bcc7ebf45ff3affcfd885b419c77",
    "label_line_number": 1,
    "label_index": 0,
    "source_width": 960,
    "source_height": 540,
    "source_bbox": [927.00048, 158.99976, 978.00048, 213.99984],
    "source_bbox_right_overflow": 18.00048,
}
EVIDENCE_FIELDS = [
    "official_code_candidate",
    "official_name_vi",
    "official_pdf_page",
    "official_section",
    "official_figure",
    "match_status",
    "reason",
    "composite_or_parameterized",
    "evidence_confidence",
    "evidence_method",
]
LINEAGE_FIELDS = [
    "class_id",
    "dataset_code",
    "stem",
    "split",
    "atlas_page",
    "slot_index",
    "image_path",
    "image_sha256",
    "label_path",
    "label_sha256",
    "label_line_number",
    "label_index",
    "normalized_x_center",
    "normalized_y_center",
    "normalized_width",
    "normalized_height",
    "source_width",
    "source_height",
    "source_bbox_within_image",
    "source_bbox_overflow_left",
    "source_bbox_overflow_top",
    "source_bbox_overflow_right",
    "source_bbox_overflow_bottom",
    "source_bbox_x_min",
    "source_bbox_y_min",
    "source_bbox_x_max",
    "source_bbox_y_max",
    "context_crop_left",
    "context_crop_top",
    "context_crop_right",
    "context_crop_bottom",
    "context_padding_left",
    "context_padding_top",
    "context_padding_right",
    "context_padding_bottom",
    "render_scale",
    "render_offset_x",
    "render_offset_y",
    "sample_bbox_x_min",
    "sample_bbox_y_min",
    "sample_bbox_x_max",
    "sample_bbox_y_max",
    "sample_source_frame_x_min",
    "sample_source_frame_y_min",
    "sample_source_frame_x_max",
    "sample_source_frame_y_max",
    "atlas_image_x",
    "atlas_image_y",
    "atlas_bbox_x_min",
    "atlas_bbox_y_min",
    "atlas_bbox_x_max",
    "atlas_bbox_y_max",
    "atlas_source_frame_x_min",
    "atlas_source_frame_y_min",
    "atlas_source_frame_x_max",
    "atlas_source_frame_y_max",
    "overlay_color",
    "overlay_width",
]
TRACKED_SOURCE_NAMES = (
    "qcvn_pdf",
    "circular_pdf",
    "source_provenance",
    "evidence_index",
    "taxonomy_review",
    "wp3_atlas",
    "wp3_manifest",
    "wp2_manifest",
    "wp1_manifest",
    "source_preservation",
    "inventory",
    "decision_status",
    "canonical_taxonomy",
)
WORKSHEET_FIELDS = [
    "class_id",
    "dataset_code",
    "dataset_name_vi_en",
    "image_count",
    "box_count",
    "official_code_candidate",
    "official_name_vi",
    "official_pdf_page",
    "official_section",
    "official_figure",
    "match_status",
    "reason",
    "composite_or_parameterized",
    "gtsrb_mapping_proposal",
    "gtsrb_relation_proposal",
    "reviewer_status",
    "evidence_confidence",
    "evidence_method",
    "representative_source_stems",
    "atlas_page",
]


def evidence(
    class_id: int,
    code: str,
    name: str,
    page: str,
    section: str,
    figure: str,
    status: str,
    reason: str,
    kind: str = "NO",
    confidence: str = "HIGH",
    method: str = "TEXT_LAYER_AND_VISUAL",
) -> dict[str, str | int]:
    return {
        "class_id": class_id,
        "official_code_candidate": code,
        "official_name_vi": name,
        "official_pdf_page": page,
        "official_section": section,
        "official_figure": figure,
        "match_status": status,
        "reason": reason,
        "composite_or_parameterized": kind,
        "evidence_confidence": confidence,
        "evidence_method": method,
    }


# Short names and references are transcribed from the official QCVN PDF. These are evidence
# candidates, not accepted labels. Visual checks cover the high-risk rows and the extractor checks
# the cited code token on every cited page range.
OFFICIAL_EVIDENCE = [
    evidence(0, "W.224", "Đường người đi bộ cắt ngang", "107", "C.24", "C.26", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(1, "W.205c", "Đường giao nhau (nhánh phải)", "100", "C.5", "C.5", "EXACT", "Đúng biến thể hình W.205c."),
    evidence(2, "P.102", "Cấm đi ngược chiều", "80", "B.2", "B.2", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(3, "R.302a", "Hướng phải đi vòng chướng ngại vật", "117", "D.2", "D.4", "PARTIAL", "Mã/hình đúng; nhãn EN 'Right Turn Only' làm mất nghĩa vòng chướng ngại vật."),
    evidence(4, "W.205a", "Đường giao nhau", "100", "C.5", "C.5", "EXACT", "Đúng biến thể hình W.205a."),
    evidence(5, "W.207", "Giao nhau với đường không ưu tiên", "100-102", "C.7", "C.7", "EXACT", "Mã và nghĩa trùng họ biển QCVN."),
    evidence(6, "W.201a", "Chỗ ngoặt nguy hiểm vòng bên trái", "98", "C.1", "C.1", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(7, "P.123a", "Cấm rẽ trái", "87", "B.23", "B.23", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(8, "I.434a", "Bến xe buýt", "142-143", "E.36", "E.36", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(9, "R.303", "Nơi giao nhau chạy theo vòng xuyến", "117", "D.3", "D.5", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(10, "P.130", "Cấm dừng xe và đỗ xe", "93-94", "B.30", "B.30", "EXACT", "Khác rất nhẹ về trật tự từ, không đổi nghĩa."),
    evidence(11, "I.409", "Chỗ quay xe", "132-133", "E.9", "E.9", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(12, "R.415a", "Biển gộp làn đường theo phương tiện", "126", "D.16", "D.18a", "EXACT", "Mã và nghĩa trùng QCVN.", "COMPOSITE"),
    evidence(13, "W.245a", "Đi chậm", "113", "C.45", "C.47", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(14, "P.106a", "Cấm xe ô tô tải", "81-82", "B.6", "B.6", "PARTIAL", "Ứng viên chính thức là P.106a; hậu tố '*Xe tải' không phải cú pháp mã QCVN.", "PARAMETERIZED"),
    evidence(15, "W.203c", "Đường bị thu hẹp về phía phải", "99", "C.3", "C.3", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(16, "P.117", "Hạn chế chiều cao", "85-86", "B.17", "B.17", "PARTIAL", "Biển có trị số; dấu '*' trong mã dataset không phải cú pháp QCVN.", "PARAMETERIZED"),
    evidence(17, "P.124a", "Cấm quay đầu xe", "87-88", "B.24", "B.24", "PARTIAL", "Ứng viên P.124a đúng; dấu '*' trong mã dataset không phải cú pháp QCVN.", "PARAMETERIZED"),
    evidence(18, "P.107", "Cấm xe ô tô khách và xe ô tô tải", "82", "B.7", "B.7", "PARTIAL", "Nhãn VI gần đúng; 'Passenger Cars' không tương đương 'ô tô khách'."),
    evidence(19, "P.124d", "Cấm rẽ phải và quay đầu xe", "87-88", "B.24", "B.24", "EXACT", "Mã và nghĩa trùng QCVN.", "COMPOSITE"),
    evidence(20, "P.103a", "Cấm xe ô tô", "80-81", "B.3", "B.3", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(21, "W.203b", "Đường bị thu hẹp về phía trái", "99", "C.3", "C.3", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(22, "W.221b", "Đường có gồ giảm tốc", "106", "C.21", "C.23", "PARTIAL", "Mã/hình đúng; nhãn EN 'Uneven Road' rộng hơn gồ giảm tốc."),
    evidence(23, "P.111a-d", "Các biến thể cấm xe gắn máy hoặc xe ba bánh", "84", "B.11", "B.11", "MISMATCH", "QCVN không có một biển P.111 chung cho cả xe hai và ba bánh; phải chọn biến thể a-d."),
    evidence(24, "P.129", "Kiểm tra", "93", "B.29", "B.29", "PARTIAL", "Mã/VI đúng; 'Customs Checkpoint' hẹp hơn nghĩa kiểm tra chung của QCVN."),
    evidence(25, "S.505a", "Loại xe", "152", "F.5", "F.5", "MISMATCH", "S.505a là biển phụ chỉ loại xe chịu hiệu lực của biển chính, không có nghĩa 'Motorcycles Only'.", "SUPPLEMENTARY"),
    evidence(26, "W.246a", "Chú ý chướng ngại vật - Vòng tránh ra hai bên", "114", "C.46", "C.48", "PARTIAL", "Mã đúng; nhãn dataset có lỗi chính tả và lược bỏ hướng vòng tránh."),
    evidence(27, "W.225", "Trẻ em", "107-108", "C.25", "C.27", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(28, "S.505a", "Loại xe", "152", "F.5", "F.5", "MISMATCH", "S.505a là biển phụ; nhãn 'Trucks and Containers' không phải tên/nghĩa QCVN.", "SUPPLEMENTARY"),
    evidence(29, "P.104", "Cấm xe máy", "81", "B.4", "B.4", "PARTIAL", "Mã đúng; nhãn dataset mở rộng thành 'mô tô và xe máy' so với tên QCVN."),
    evidence(30, "S.505a", "Loại xe", "152", "F.5", "F.5", "MISMATCH", "S.505a là biển phụ chỉ phạm vi của biển chính, không có nghĩa độc lập 'Trucks Only'.", "SUPPLEMENTARY"),
    evidence(31, "", "", "", "", "", "NOT_FOUND", "Không tìm thấy mã/tên camera giám sát tương ứng trong QCVN; kết luận chỉ giới hạn trong nguồn này.", "NO", "MEDIUM", "TEXT_QUERY_AND_VISUAL_SAMPLE"),
    evidence(32, "P.123b", "Cấm rẽ phải", "87", "B.23", "B.23", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(33, "W.202b", "Nhiều chỗ ngoặt nguy hiểm liên tiếp, đầu tiên sang phải", "99", "C.2", "C.2", "EXACT", "Mã và hướng biến thể trùng QCVN."),
    evidence(34, "P.108a", "Cấm xe sơ-mi rơ-moóc", "83", "B.8a", "B.8a", "MISMATCH", "B.8a là số mục/hình; mã biển chính thức là P.108a. Nhãn EN 'Containers' cũng sai loại xe."),
    evidence(35, "P.137", "Cấm rẽ trái, rẽ phải", "96", "B.37", "B.37", "EXACT", "Mã và nghĩa trùng QCVN.", "COMPOSITE"),
    evidence(36, "P.139", "Cấm đi thẳng, rẽ phải", "96-97", "B.39", "B.39", "EXACT", "Mã và nghĩa trùng QCVN.", "COMPOSITE"),
    evidence(37, "W.205b", "Đường giao nhau (nhánh trái)", "100", "C.5", "C.5", "EXACT", "Đúng biến thể hình W.205b."),
    evidence(38, "P.127", "Tốc độ tối đa cho phép (50 km/h)", "89-90", "B.27", "B.27", "PARTIAL", "Trị số 50 hợp lệ trên biển P.127; '*50' không phải cú pháp mã QCVN.", "PARAMETERIZED"),
    evidence(39, "P.127", "Tốc độ tối đa cho phép (60 km/h)", "89-90", "B.27", "B.27", "PARTIAL", "Trị số 60 hợp lệ trên biển P.127; '*60' không phải cú pháp mã QCVN.", "PARAMETERIZED"),
    evidence(40, "P.127", "Tốc độ tối đa cho phép (80 km/h)", "89-90", "B.27", "B.27", "PARTIAL", "Trị số 80 hợp lệ trên biển P.127; '*80' không phải cú pháp mã QCVN.", "PARAMETERIZED"),
    evidence(41, "P.127", "Tốc độ tối đa cho phép (40 km/h)", "89-90", "B.27", "B.27", "PARTIAL", "Trị số 40 hợp lệ trên biển P.127; '*40' không phải cú pháp mã QCVN.", "PARAMETERIZED"),
    evidence(42, "R.301e", "Hướng đi phải theo - rẽ trái", "115-116", "D.1a", "D.3", "EXACT", "Mã, hình và hướng trùng QCVN."),
    evidence(43, "W.239b", "Chiều cao tĩnh không thực tế", "111-112", "C.39", "C.41", "PARTIAL", "Ứng viên đúng; dấu '*' biểu thị tham số nhưng không phải cú pháp mã QCVN.", "PARAMETERIZED"),
    evidence(44, "W.233", "Nguy hiểm khác", "110", "C.33", "C.35", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(45, "I.407a", "Đường một chiều", "131-132", "E.7", "E.7", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(46, "P.131a", "Cấm đỗ xe", "94", "B.31", "B.31", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(47, "P.124b", "Cấm ô tô quay đầu xe", "87-88", "B.24", "B.24", "MISMATCH", "Không có mã P.124b1 trong QCVN; ứng viên chính thức theo hình/nghĩa là P.124b."),
    evidence(48, "W.210", "Giao nhau với đường sắt có rào chắn", "102-103", "C.10", "C.12", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(49, "P.124c", "Cấm rẽ trái và quay đầu xe", "87-88", "B.24", "B.24", "EXACT", "Mã và nghĩa trùng QCVN.", "COMPOSITE"),
    evidence(50, "W.201b", "Chỗ ngoặt nguy hiểm vòng bên phải", "98", "C.1", "C.1", "EXACT", "Mã và nghĩa trùng QCVN."),
    evidence(51, "W.246c", "Chú ý chướng ngại vật - Vòng tránh sang bên phải", "114", "C.46", "C.48", "EXACT", "Mã và nghĩa trùng QCVN; ánh xạ GTSRB vẫn chỉ là đề xuất khác họ warning/mandatory."),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def page_numbers(value: str) -> list[int]:
    if not value:
        return []
    if "-" not in value:
        return [int(value)]
    start, end = map(int, value.split("-", maxsplit=1))
    return list(range(start, end + 1))


def compact_text(value: str) -> str:
    return "".join(value.replace("\x00", "").split()).casefold()


def validate_evidence_table() -> None:
    ids = [int(row["class_id"]) for row in OFFICIAL_EVIDENCE]
    if len(ids) != 52 or set(ids) != EXPECTED_CLASS_IDS or len(set(ids)) != len(ids):
        raise ValueError("OFFICIAL_EVIDENCE must contain class_id 0..51 exactly once")
    for row in OFFICIAL_EVIDENCE:
        if row["match_status"] not in MATCH_STATUSES:
            raise ValueError(f"invalid match status for class {row['class_id']}")
        for page in page_numbers(str(row["official_pdf_page"])):
            if not 1 <= page <= 403:
                raise ValueError(f"official page out of range for class {row['class_id']}")


def evidence_tokens_for_row(row: dict[str, Any]) -> list[str]:
    class_id = int(row["class_id"])
    if class_id == 31:
        return []
    code = str(row["official_code_candidate"])
    code_token = "P.111a" if code == "P.111a-d" else code
    name_overrides = {
        1: "Đường giao nhau",
        4: "Đường giao nhau",
        15: "Đường bị thu hẹp",
        23: "Cấm xe gắn máy",
        33: "Nhiều chỗ ngoặt nguy hiểm liên tiếp",
        37: "Đường giao nhau",
        38: "Tốc độ tối đa cho phép",
        39: "Tốc độ tối đa cho phép",
        40: "Tốc độ tối đa cho phép",
        41: "Tốc độ tối đa cho phép",
        42: "Hướng đi phải theo",
    }
    name_token = name_overrides.get(class_id, str(row["official_name_vi"]))
    if " - " in name_token:
        name_token = name_token.split(" - ", maxsplit=1)[0]
    if " (" in name_token:
        name_token = name_token.split(" (", maxsplit=1)[0]
    return [
        compact_text(code_token),
        compact_text(name_token),
        compact_text(f"Hình {row['official_figure']}"),
    ]


def pdftoppm_binary() -> Path:
    candidates = [
        shutil.which("pdftoppm"),
        "/Users/nguyentantai/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    raise RuntimeError("pdftoppm is required to verify QCVN page render fingerprints")


_PAGE_FINGERPRINT_CACHE: dict[tuple[str, int], dict[str, Any]] = {}


def page_fingerprints(qcvn_pdf: Path, pages: list[int]) -> dict[str, dict[str, Any]]:
    pdf_hash = sha256_file(qcvn_pdf)
    reader = PdfReader(str(qcvn_pdf))
    result: dict[str, dict[str, Any]] = {}
    for page_number in sorted(set(pages)):
        if not 1 <= page_number <= len(reader.pages):
            raise ValueError(f"page fingerprint request is out of range: {page_number}")
        cache_key = (pdf_hash, page_number)
        cached = _PAGE_FINGERPRINT_CACHE.get(cache_key)
        if cached is None:
            normalized_text = compact_text(reader.pages[page_number - 1].extract_text() or "")
            with tempfile.TemporaryDirectory(prefix="wp4-qcvn-page-") as temp_dir:
                prefix = Path(temp_dir) / "page"
                subprocess.run(
                    [
                        str(pdftoppm_binary()),
                        "-f",
                        str(page_number),
                        "-l",
                        str(page_number),
                        "-singlefile",
                        "-png",
                        "-r",
                        str(PDF_RENDER_DPI),
                        str(qcvn_pdf),
                        str(prefix),
                    ],
                    check=True,
                    capture_output=True,
                )
                with Image.open(prefix.with_suffix(".png")) as opened:
                    rendered = opened.convert("RGB")
                    pixel_digest = hashlib.sha256()
                    pixel_digest.update(
                        f"RGB|{rendered.width}x{rendered.height}|{PDF_RENDER_DPI}dpi|".encode()
                    )
                    pixel_digest.update(rendered.tobytes())
                    render_sha256 = pixel_digest.hexdigest()
                    render_size = [rendered.width, rendered.height]
            cached = {
                "text_sha256": hashlib.sha256(normalized_text.encode()).hexdigest(),
                "render_pixel_sha256": render_sha256,
                "render_size": render_size,
                "render_dpi": PDF_RENDER_DPI,
            }
            _PAGE_FINGERPRINT_CACHE[cache_key] = cached
        result[str(page_number)] = cached
    return result


def negative_scope_evidence(qcvn_pdf: Path, scope: dict[str, Any]) -> dict[str, Any]:
    pages = page_numbers(str(scope["pages"]))
    reader = PdfReader(str(qcvn_pdf))
    normalized_by_page = [
        f"{page}:{compact_text(reader.pages[page - 1].extract_text() or '')}"
        for page in pages
    ]
    combined = "\n".join(normalized_by_page)
    present = [query for query in scope["queries"] if compact_text(query) in combined]
    return {
        **scope,
        "scope_text_sha256": hashlib.sha256(combined.encode()).hexdigest(),
        "query_hits": present,
    }


def build_evidence_index_payload(qcvn_pdf: Path) -> dict[str, Any]:
    validate_evidence_table()
    cited_pages = sorted(
        {
            page
            for row in OFFICIAL_EVIDENCE
            for page in page_numbers(str(row["official_pdf_page"]))
        }
    )
    rows: list[dict[str, Any]] = []
    for row in OFFICIAL_EVIDENCE:
        output = {key: row[key] for key in ("class_id", *EVIDENCE_FIELDS)}
        output["evidence_tokens"] = evidence_tokens_for_row(row)
        output["fingerprint_pages"] = page_numbers(str(row["official_pdf_page"]))
        if int(row["class_id"]) == 31:
            output["negative_search_scope"] = negative_scope_evidence(
                qcvn_pdf, NEGATIVE_SCOPE
            )
        rows.append(output)
    return {
        "schema_version": 2,
        "status": "CANONICAL_EVIDENCE_INDEX_NOT_TAXONOMY_APPROVAL",
        "qcvn_pdf_sha256": QCVN_SHA256,
        "qcvn_page_count": QCVN_PAGE_COUNT,
        "fingerprint_contract": {
            "text": "sha256(compact_text(pypdf.extract_text))",
            "render": "sha256(RGB|widthxheight|72dpi| + raster pixel bytes)",
        },
        "page_fingerprints": page_fingerprints(qcvn_pdf, cited_pages),
        "rows": rows,
    }


def resolve_control_path(path: Path, repo_root: Path, expected: Path) -> Path:
    resolved = path.resolve()
    expected_resolved = (repo_root.resolve() / expected).resolve()
    if resolved != expected_resolved:
        raise ValueError(f"control path must be {expected.as_posix()}; path escape rejected")
    if not resolved.is_file():
        raise ValueError(f"required control is missing: {expected.as_posix()}")
    return resolved


def load_and_verify_evidence_index(
    index_path: Path,
    qcvn_pdf: Path,
    repo_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    resolved = resolve_control_path(index_path, repo_root, EVIDENCE_INDEX_RELATIVE_PATH)
    actual_hash = sha256_file(resolved)
    if actual_hash != EXPECTED_EVIDENCE_INDEX_SHA256:
        raise ValueError("canonical QCVN evidence index hash mismatch")
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 2:
        raise ValueError("canonical QCVN evidence index schema mismatch")
    if payload.get("qcvn_pdf_sha256") != QCVN_SHA256:
        raise ValueError("evidence index QCVN hash mismatch")
    if payload.get("qcvn_page_count") != QCVN_PAGE_COUNT:
        raise ValueError("evidence index QCVN page count mismatch")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("evidence index rows must be a list")
    ids = [int(row.get("class_id", -1)) for row in rows if isinstance(row, dict)]
    if len(rows) != 52 or set(ids) != EXPECTED_CLASS_IDS or len(set(ids)) != len(ids):
        raise ValueError("evidence index must contain class_id 0..51 exactly once")
    embedded = {int(row["class_id"]): row for row in OFFICIAL_EVIDENCE}
    indexed = {int(row["class_id"]): row for row in rows}
    cited_pages: set[int] = set()
    reader = PdfReader(str(qcvn_pdf))
    for class_id in range(52):
        row = indexed[class_id]
        expected = embedded[class_id]
        for field in EVIDENCE_FIELDS:
            if row.get(field) != expected[field]:
                raise ValueError(f"evidence index {field} mismatch for class {class_id}")
        expected_tokens = evidence_tokens_for_row(expected)
        if row.get("evidence_tokens") != expected_tokens:
            raise ValueError(f"evidence index token mismatch for class {class_id}")
        expected_pages = page_numbers(str(expected["official_pdf_page"]))
        if row.get("fingerprint_pages") != expected_pages:
            raise ValueError(f"evidence index page binding mismatch for class {class_id}")
        if class_id == 31:
            negative = row.get("negative_search_scope")
            if not isinstance(negative, dict):
                raise ValueError("class 31 negative-search scope is missing")
            for key, value in NEGATIVE_SCOPE.items():
                if negative.get(key) != value:
                    raise ValueError(f"class 31 negative-search scope mismatch: {key}")
            recomputed_negative = negative_scope_evidence(qcvn_pdf, NEGATIVE_SCOPE)
            if negative.get("scope_text_sha256") != recomputed_negative["scope_text_sha256"]:
                raise ValueError("class 31 negative-search scope fingerprint mismatch")
            if recomputed_negative["query_hits"]:
                raise ValueError("class 31 negative-search query unexpectedly matched")
            if negative.get("query_hits") != []:
                raise ValueError("class 31 negative-search hit list must be empty")
            continue
        cited_pages.update(expected_pages)
        combined_text = "".join(
            compact_text(reader.pages[page - 1].extract_text() or "")
            for page in expected_pages
        )
        missing_tokens = [token for token in expected_tokens if token not in combined_text]
        if missing_tokens:
            raise ValueError(
                f"evidence token missing from pinned page for class {class_id}: {missing_tokens}"
            )
    expected_fingerprints = page_fingerprints(qcvn_pdf, sorted(cited_pages))
    indexed_fingerprints = payload.get("page_fingerprints")
    if indexed_fingerprints != expected_fingerprints:
        raise ValueError("canonical page text/render fingerprint mismatch")
    return rows, {
        "index_sha256": actual_hash,
        "row_count": len(rows),
        "positive_row_count": 51,
        "not_found_row_count": 1,
        "fingerprinted_page_count": len(expected_fingerprints),
        "negative_scope": NEGATIVE_SCOPE,
    }


def compare_worksheet_to_index(
    worksheet: list[dict[str, str]], index_rows: list[dict[str, Any]]
) -> None:
    index_by_id = {int(row["class_id"]): row for row in index_rows}
    for row in worksheet:
        class_id = int(row["class_id"])
        expected = index_by_id[class_id]
        for field in EVIDENCE_FIELDS:
            if row[field] != str(expected[field]):
                raise ValueError(f"worksheet/index semantic mismatch: class {class_id} {field}")


def verify_pdf_sources(qcvn_pdf: Path, circular_pdf: Path, provenance_path: Path) -> dict[str, Any]:
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    by_role = {record["role"]: record for record in provenance["documents"]}
    results: dict[str, Any] = {}
    for role, path in (("qcvn", qcvn_pdf), ("circular", circular_pdf)):
        record = by_role[role]
        actual_hash = sha256_file(path)
        reader = PdfReader(str(path))
        actual_pages = len(reader.pages)
        if actual_hash != record["sha256"] or actual_pages != int(record["page_count"]):
            raise ValueError(f"{role} PDF does not match pinned provenance")
        results[role] = {
            "sha256": actual_hash,
            "page_count": actual_pages,
            "size_bytes": path.stat().st_size,
            "url": record["url"],
        }
    controls = provenance.get("evidence_controls")
    if not isinstance(controls, list) or len(controls) != 1:
        raise ValueError("pinned provenance evidence control is missing")
    control = controls[0]
    expected_control = {
        "role": "canonical_taxonomy_evidence_index",
        "path": EVIDENCE_INDEX_RELATIVE_PATH.name,
        "sha256": EXPECTED_EVIDENCE_INDEX_SHA256,
        "schema_version": 2,
        "row_count": 52,
        "fingerprinted_page_count": 39,
    }
    if control != expected_control:
        raise ValueError("pinned provenance evidence control mismatch")
    results["evidence_index_control"] = control
    return results


def verify_page_tokens(qcvn_pdf: Path) -> dict[str, Any]:
    reader = PdfReader(str(qcvn_pdf))
    checked_pages: set[int] = set()
    failures: list[dict[str, Any]] = []
    for row in OFFICIAL_EVIDENCE:
        code = str(row["official_code_candidate"])
        pages = page_numbers(str(row["official_pdf_page"]))
        if not code:
            continue
        base_code = code.split("-")[0]
        token = compact_text(base_code)
        matched = False
        for page in pages:
            checked_pages.add(page)
            text = reader.pages[page - 1].extract_text() or ""
            if token in compact_text(text):
                matched = True
                break
        if not matched:
            failures.append({"class_id": row["class_id"], "token": base_code, "pages": pages})
    if failures:
        raise ValueError(f"official code token missing from cited page range: {failures}")
    return {
        "checked_cited_pages": sorted(checked_pages),
        "checked_row_count": 51,
        "not_found_row": 31,
        "not_found_scope_note": "No positive QCVN candidate asserted; absence is scoped to this source.",
    }


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ):
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def wrap_lines(draw: ImageDraw.ImageDraw, value: str, text_font: Any, width: int) -> list[str]:
    if not value:
        return [""]
    words = value.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        proposal = word if not current else f"{current} {word}"
        if draw.textlength(proposal, font=text_font) <= width:
            current = proposal
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    value: str,
    x: int,
    y: int,
    text_font: Any,
    width: int,
    fill: tuple[int, int, int] = (20, 20, 20),
) -> tuple[int, list[list[int]]]:
    line_height = text_font.getbbox("Ag")[3] - text_font.getbbox("Ag")[1] + 5
    bounds: list[list[int]] = []
    for index, line in enumerate(wrap_lines(draw, value, text_font, width)):
        line_y = y + index * line_height
        draw.text((x, line_y), line, font=text_font, fill=fill)
        box = draw.textbbox((x, line_y), line or " ", font=text_font)
        bounds.append([box[0], box[1], box[2], box[3]])
    return y + len(bounds) * line_height, bounds


def parse_boxes(path: Path) -> list[dict[str, Any]]:
    boxes: list[dict[str, Any]] = []
    label_index = 0
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f"invalid YOLO row in {path}")
        class_id = int(fields[0])
        x_center, y_center, width, height = map(float, fields[1:])
        if not all(0.0 <= value <= 1.0 for value in (x_center, y_center, width, height)):
            raise ValueError(f"YOLO coordinate outside [0,1] in {path} line {line_number}")
        boxes.append(
            {
                "class_id": class_id,
                "x_center": x_center,
                "y_center": y_center,
                "width": width,
                "height": height,
                "label_line_number": line_number,
                "label_index": label_index,
            }
        )
        label_index += 1
    return boxes


def select_target_box(label_path: Path, class_id: int) -> dict[str, Any]:
    candidates = [
        box for box in parse_boxes(label_path) if int(box["class_id"]) == class_id
    ]
    if not candidates:
        raise ValueError(f"target class {class_id} missing from {label_path}")
    return max(
        candidates,
        key=lambda box: (
            float(box["width"]) * float(box["height"]),
            -int(box["label_index"]),
        ),
    )


def overlay_geometry(
    image_width: int,
    image_height: int,
    box: dict[str, Any],
) -> dict[str, Any]:
    x_center = float(box["x_center"])
    y_center = float(box["y_center"])
    width = float(box["width"])
    height = float(box["height"])
    x_min = (x_center - width / 2) * image_width
    x_max = (x_center + width / 2) * image_width
    y_min = (y_center - height / 2) * image_height
    y_max = (y_center + height / 2) * image_height
    if not (x_min < x_max and y_min < y_max):
        raise ValueError("target bbox geometry is degenerate")
    if x_max <= 0 or y_max <= 0 or x_min >= image_width or y_min >= image_height:
        raise ValueError("target bbox has no intersection with the source image")
    source_bbox_within_image = (
        0 <= x_min < x_max <= image_width and 0 <= y_min < y_max <= image_height
    )
    source_bbox_overflow = [
        max(0.0, -x_min),
        max(0.0, -y_min),
        max(0.0, x_max - image_width),
        max(0.0, y_max - image_height),
    ]
    box_width = x_max - x_min
    box_height = y_max - y_min
    margin_x = max(12.0, box_width * 0.75)
    margin_y = max(12.0, box_height * 0.75)
    # Keep the annotation's full geometry even when a known raw label crosses the source edge.
    # PIL pads the out-of-image portion of this virtual crop; no raw image or label is changed.
    crop_left = math.floor(x_min - margin_x)
    crop_top = math.floor(y_min - margin_y)
    crop_right = math.ceil(x_max + margin_x)
    crop_bottom = math.ceil(y_max + margin_y)
    crop_width = crop_right - crop_left
    crop_height = crop_bottom - crop_top
    if crop_width < 2 or crop_height < 2:
        raise ValueError("target bbox context crop is degenerate")
    scale = min(250 / crop_width, 150 / crop_height)
    rendered_width = max(1, round(crop_width * scale))
    rendered_height = max(1, round(crop_height * scale))
    offset_x = (250 - rendered_width) // 2
    offset_y = (150 - rendered_height) // 2
    source_left = max(0, crop_left)
    source_top = max(0, crop_top)
    source_right = min(image_width, crop_right)
    source_bottom = min(image_height, crop_bottom)
    context_padding = [
        source_left - crop_left,
        source_top - crop_top,
        crop_right - source_right,
        crop_bottom - source_bottom,
    ]
    sample_source_frame = [
        offset_x + (source_left - crop_left) * scale,
        offset_y + (source_top - crop_top) * scale,
        offset_x + (source_right - crop_left) * scale,
        offset_y + (source_bottom - crop_top) * scale,
    ]
    sample_bbox = [
        offset_x + (x_min - crop_left) * scale,
        offset_y + (y_min - crop_top) * scale,
        offset_x + (x_max - crop_left) * scale,
        offset_y + (y_max - crop_top) * scale,
    ]
    if not (
        0 <= sample_bbox[0] < sample_bbox[2] <= 250
        and 0 <= sample_bbox[1] < sample_bbox[3] <= 150
    ):
        raise ValueError("rendered target bbox is outside sample canvas")
    if sample_bbox[2] - sample_bbox[0] < 4 or sample_bbox[3] - sample_bbox[1] < 4:
        raise ValueError("rendered target bbox is too small for a legible overlay")
    return {
        "source_bbox": [x_min, y_min, x_max, y_max],
        "source_bbox_within_image": source_bbox_within_image,
        "source_bbox_overflow": source_bbox_overflow,
        "context_crop": [crop_left, crop_top, crop_right, crop_bottom],
        "context_source_intersection": [
            source_left,
            source_top,
            source_right,
            source_bottom,
        ],
        "context_padding": context_padding,
        "render_scale": scale,
        "render_offset": [offset_x, offset_y],
        "render_size": [rendered_width, rendered_height],
        "sample_bbox": sample_bbox,
        "sample_source_frame": sample_source_frame,
    }


def render_overlay_sample(
    image: Image.Image,
    geometry: dict[str, Any],
    class_id: int,
    dataset_code: str,
    stem: str,
) -> Image.Image:
    crop_left, crop_top, crop_right, crop_bottom = geometry["context_crop"]
    source_left, source_top, source_right, source_bottom = geometry[
        "context_source_intersection"
    ]
    virtual = Image.new(
        "RGB", (crop_right - crop_left, crop_bottom - crop_top), (62, 62, 62)
    )
    virtual_draw = ImageDraw.Draw(virtual)
    for diagonal in range(-virtual.height, virtual.width, 12):
        virtual_draw.line(
            (diagonal, 0, diagonal + virtual.height, virtual.height),
            fill=(102, 102, 102),
            width=3,
        )
    source_crop = image.crop((source_left, source_top, source_right, source_bottom))
    virtual.paste(source_crop, (source_left - crop_left, source_top - crop_top))
    rendered = virtual.resize(tuple(geometry["render_size"]), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (250, 150), "white")
    canvas.paste(rendered, tuple(geometry["render_offset"]))
    draw = ImageDraw.Draw(canvas)
    if any(int(value) > 0 for value in geometry["context_padding"]):
        source_frame = tuple(round(value) for value in geometry["sample_source_frame"])
        draw.rectangle(source_frame, outline=(0, 205, 235), width=3)
    tag = f"ID {class_id} | {dataset_code} | {stem}"
    tag_font = font(12)
    tag_box = draw.textbbox((5, 4), tag, font=tag_font)
    draw.rectangle((2, 2, min(248, tag_box[2] + 8), tag_box[3] + 7), fill=(15, 15, 15))
    draw.text((5, 4), tag, font=tag_font, fill=(255, 235, 80))
    bbox = tuple(round(value) for value in geometry["sample_bbox"])
    draw.rectangle(bbox, outline=(255, 255, 255), width=7)
    draw.rectangle(bbox, outline=(220, 20, 60), width=4)
    return canvas


def verified_sample(
    inventory_row: dict[str, str],
    raw_root: Path,
    class_id: int,
    dataset_code: str,
) -> tuple[Image.Image, dict[str, Any]]:
    image_path = raw_root / inventory_row["image_path"]
    label_path = raw_root / inventory_row["label_path"]
    image_hash = sha256_file(image_path)
    label_hash = sha256_file(label_path)
    if image_hash != inventory_row["image_sha256"] or label_hash != inventory_row["label_sha256"]:
        raise ValueError(f"source hash mismatch for stem {inventory_row['stem']}")
    with Image.open(image_path) as opened:
        image = opened.convert("RGB")
    if image.width != int(inventory_row["width"]) or image.height != int(
        inventory_row["height"]
    ):
        raise ValueError(f"inventory dimensions mismatch for stem {inventory_row['stem']}")
    target = select_target_box(label_path, class_id)
    geometry = overlay_geometry(image.width, image.height, target)
    sample = render_overlay_sample(
        image, geometry, class_id, dataset_code, inventory_row["stem"]
    )
    source_bbox = geometry["source_bbox"]
    source_bbox_overflow = geometry["source_bbox_overflow"]
    context_crop = geometry["context_crop"]
    context_padding = geometry["context_padding"]
    render_offset = geometry["render_offset"]
    sample_bbox = geometry["sample_bbox"]
    sample_source_frame = geometry["sample_source_frame"]
    return sample, {
        "class_id": class_id,
        "dataset_code": dataset_code,
        "stem": inventory_row["stem"],
        "split": inventory_row["split"],
        "image_path": inventory_row["image_path"],
        "image_sha256": image_hash,
        "label_path": inventory_row["label_path"],
        "label_sha256": label_hash,
        "label_line_number": target["label_line_number"],
        "label_index": target["label_index"],
        "normalized_x_center": target["x_center"],
        "normalized_y_center": target["y_center"],
        "normalized_width": target["width"],
        "normalized_height": target["height"],
        "source_width": image.width,
        "source_height": image.height,
        "source_bbox_within_image": geometry["source_bbox_within_image"],
        "source_bbox_overflow_left": source_bbox_overflow[0],
        "source_bbox_overflow_top": source_bbox_overflow[1],
        "source_bbox_overflow_right": source_bbox_overflow[2],
        "source_bbox_overflow_bottom": source_bbox_overflow[3],
        "source_bbox_x_min": source_bbox[0],
        "source_bbox_y_min": source_bbox[1],
        "source_bbox_x_max": source_bbox[2],
        "source_bbox_y_max": source_bbox[3],
        "context_crop_left": context_crop[0],
        "context_crop_top": context_crop[1],
        "context_crop_right": context_crop[2],
        "context_crop_bottom": context_crop[3],
        "context_padding_left": context_padding[0],
        "context_padding_top": context_padding[1],
        "context_padding_right": context_padding[2],
        "context_padding_bottom": context_padding[3],
        "render_scale": geometry["render_scale"],
        "render_offset_x": render_offset[0],
        "render_offset_y": render_offset[1],
        "sample_bbox_x_min": sample_bbox[0],
        "sample_bbox_y_min": sample_bbox[1],
        "sample_bbox_x_max": sample_bbox[2],
        "sample_bbox_y_max": sample_bbox[3],
        "sample_source_frame_x_min": sample_source_frame[0],
        "sample_source_frame_y_min": sample_source_frame[1],
        "sample_source_frame_x_max": sample_source_frame[2],
        "sample_source_frame_y_max": sample_source_frame[3],
        "overlay_color": "220,20,60",
        "overlay_width": 4,
    }


def render_atlas_page(
    rows: list[dict[str, Any]],
    page_number: int,
    inventory: dict[str, dict[str, str]],
    raw_root: Path,
    output_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    width = 1200
    block_height = 440
    canvas = Image.new("RGB", (width, 58 + block_height * len(rows)), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = font(20)
    body_font = font(15)
    small_font = font(13)
    draw.text(
        (18, 14),
        f"M0-WP4 QCVN evidence atlas {page_number:03d} | ALL ROWS UNAPPROVED",
        font=title_font,
        fill=(0, 0, 0),
    )
    audits: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        y = 58 + row_index * block_height
        draw.rectangle((8, y, width - 8, y + block_height - 6), outline=(140, 140, 140))
        cursor, header_bounds = draw_wrapped(
            draw,
            f"class {row['class_id']} | {row['dataset_code']} | {row['dataset_name_vi_en']} | support {row['image_count']} images / {row['box_count']} boxes | {REVIEWER_STATUS}",
            18,
            y + 10,
            body_font,
            width - 36,
        )
        cursor, official_bounds = draw_wrapped(
            draw,
            f"QCVN candidate: {row['official_code_candidate'] or 'NOT FOUND'} | {row['official_name_vi'] or '—'} | PDF p.{row['official_pdf_page'] or '—'}, §{row['official_section'] or '—'}, Hình {row['official_figure'] or '—'} | {row['match_status']} ({row['evidence_confidence']})",
            18,
            cursor + 2,
            small_font,
            width - 36,
            (0, 45, 105),
        )
        cursor, reason_bounds = draw_wrapped(
            draw,
            f"Reason: {row['reason']}",
            18,
            cursor + 2,
            small_font,
            width - 36,
            (120, 0, 0),
        )
        cursor, gtsrb_bounds = draw_wrapped(
            draw,
            f"GTSRB proposal only: {row['gtsrb_mapping_proposal']} | relation: {row['gtsrb_relation_proposal']} | kind: {row['composite_or_parameterized']}",
            18,
            cursor + 2,
            small_font,
            width - 36,
        )
        image_y = max(cursor + 8, y + 205)
        sample_bounds: list[dict[str, Any]] = []
        for sample_index, stem in enumerate(row["representative_source_stems"].split(";")):
            source = inventory[stem]
            crop, record = verified_sample(
                source,
                raw_root,
                int(row["class_id"]),
                str(row["dataset_code"]),
            )
            x = 18 + sample_index * 385
            canvas.paste(crop, (x, image_y))
            _, label_bounds = draw_wrapped(
                draw,
                f"source {stem} [{source['split']}] | bbox line {record['label_line_number']}",
                x,
                image_y + 154,
                small_font,
                250,
            )
            sample_bbox = [
                x + float(record["sample_bbox_x_min"]),
                image_y + float(record["sample_bbox_y_min"]),
                x + float(record["sample_bbox_x_max"]),
                image_y + float(record["sample_bbox_y_max"]),
            ]
            source_frame = [
                x + float(record["sample_source_frame_x_min"]),
                image_y + float(record["sample_source_frame_y_min"]),
                x + float(record["sample_source_frame_x_max"]),
                image_y + float(record["sample_source_frame_y_max"]),
            ]
            if not (
                x <= sample_bbox[0] < sample_bbox[2] <= x + 250
                and image_y <= sample_bbox[1] < sample_bbox[3] <= image_y + 150
            ):
                raise RuntimeError(f"overlay overflow on class {row['class_id']} slot {sample_index + 1}")
            record.update(
                {
                    "atlas_page": f"assets/wp4/qcvn_taxonomy_atlas/{output_path.name}",
                    "slot_index": sample_index + 1,
                    "atlas_image_x": x,
                    "atlas_image_y": image_y,
                    "atlas_bbox_x_min": sample_bbox[0],
                    "atlas_bbox_y_min": sample_bbox[1],
                    "atlas_bbox_x_max": sample_bbox[2],
                    "atlas_bbox_y_max": sample_bbox[3],
                    "atlas_source_frame_x_min": source_frame[0],
                    "atlas_source_frame_y_min": source_frame[1],
                    "atlas_source_frame_x_max": source_frame[2],
                    "atlas_source_frame_y_max": source_frame[3],
                }
            )
            lineage.append(record)
            sample_bounds.append(
                {
                    "stem": stem,
                    "slot_index": sample_index + 1,
                    "image_bounds": [x, image_y, x + 250, image_y + 150],
                    "overlay_bounds": sample_bbox,
                    "source_frame_bounds": source_frame,
                    "label_bounds": label_bounds,
                    "label_line_number": record["label_line_number"],
                    "target_class": int(row["class_id"]),
                    "overlay_present": True,
                    "out_of_frame_background": "GRAY_HATCH",
                    "source_boundary_style": "CYAN_0_205_235_WIDTH_3",
                }
            )
        all_bounds = header_bounds + official_bounds + reason_bounds + gtsrb_bounds
        if any(box[0] < 0 or box[2] > width or box[1] < y or box[3] > y + block_height for box in all_bounds):
            raise RuntimeError(f"text overflow on class {row['class_id']}")
        if image_y + 185 > y + block_height:
            raise RuntimeError(f"image overflow on class {row['class_id']}")
        audits.append(
            {
                "class_id": int(row["class_id"]),
                "row_bounds": [8, y, width - 8, y + block_height - 6],
                "text_bounds": all_bounds,
                "sample_bounds": sample_bounds,
                "all_bounds_fit": True,
                "all_text_complete": True,
            }
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="JPEG", quality=88, optimize=True, progressive=False)
    return {
        "page": f"assets/wp4/qcvn_taxonomy_atlas/{output_path.name}",
        "canvas_size": list(canvas.size),
        "rows": audits,
    }, lineage


def require_close(actual: str, expected: float, field: str, slot: str) -> None:
    if not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-6):
        raise ValueError(f"overlay geometry mismatch for {slot}: {field}")


def overlay_pixels_present(image: Image.Image, bbox: list[float]) -> bool:
    left, top, right, bottom = [round(value) for value in bbox]
    candidates: set[tuple[int, int]] = set()
    for x in range(max(0, left - 3), min(image.width, right + 4)):
        for y in (*range(max(0, top - 3), min(image.height, top + 4)), *range(max(0, bottom - 3), min(image.height, bottom + 4))):
            candidates.add((x, y))
    for y in range(max(0, top - 3), min(image.height, bottom + 4)):
        for x in (*range(max(0, left - 3), min(image.width, left + 4)), *range(max(0, right - 3), min(image.width, right + 4))):
            candidates.add((x, y))
    red_pixels = 0
    rgb = image.convert("RGB")
    for x, y in candidates:
        red, green, blue = rgb.getpixel((x, y))
        if red >= 140 and red >= green + 45 and red >= blue + 35:
            red_pixels += 1
    return red_pixels >= max(16, len(candidates) // 12)


def source_boundary_pixels_present(image: Image.Image, bbox: list[float]) -> bool:
    left, top, right, bottom = [round(value) for value in bbox]
    candidates: set[tuple[int, int]] = set()
    for x in range(max(0, left - 4), min(image.width, right + 5)):
        for y in (
            *range(max(0, top - 4), min(image.height, top + 5)),
            *range(max(0, bottom - 4), min(image.height, bottom + 5)),
        ):
            candidates.add((x, y))
    for y in range(max(0, top - 4), min(image.height, bottom + 5)):
        for x in (
            *range(max(0, left - 4), min(image.width, left + 5)),
            *range(max(0, right - 4), min(image.width, right + 5)),
        ):
            candidates.add((x, y))
    rgb = image.convert("RGB")
    cyan_pixels = 0
    for x, y in candidates:
        red, green, blue = rgb.getpixel((x, y))
        if blue >= 130 and green >= 110 and blue >= red + 45 and green >= red + 35:
            cyan_pixels += 1
    return cyan_pixels >= 8


def verify_overlay_lineage(
    lineage_path: Path,
    layout_path: Path,
    inventory_path: Path,
    raw_root: Path,
    repo_root: Path,
    worksheet: list[dict[str, Any]],
) -> dict[str, Any]:
    lineage = read_csv(lineage_path)
    if not lineage or list(lineage[0]) != LINEAGE_FIELDS:
        raise ValueError("overlay lineage schema mismatch")
    if len(lineage) != 156:
        raise ValueError("overlay lineage must contain exactly 156 slots")
    slot_keys = [(int(row["class_id"]), int(row["slot_index"])) for row in lineage]
    expected_slots = [(class_id, slot) for class_id in range(52) for slot in range(1, 4)]
    if sorted(slot_keys) != expected_slots or len(set(slot_keys)) != 156:
        raise ValueError("overlay lineage must contain three unique slots per class")
    worksheet_by_id = {int(row["class_id"]): row for row in worksheet}
    if set(worksheet_by_id) != EXPECTED_CLASS_IDS or len(worksheet) != 52:
        raise ValueError("overlay worksheet control must contain class_id 0..51")
    expected_metadata = {
        (class_id, slot_index): {
            "dataset_code": str(worksheet_by_id[class_id]["dataset_code"]),
            "stem": str(worksheet_by_id[class_id]["representative_source_stems"]).split(";")[
                slot_index - 1
            ],
            "atlas_page": f"assets/wp4/qcvn_taxonomy_atlas/page_{class_id // 4 + 1:03d}.jpg",
        }
        for class_id in range(52)
        for slot_index in range(1, 4)
    }
    inventory_rows = read_csv(inventory_path)
    inventory = {row["stem"]: row for row in inventory_rows}
    if len(inventory) != len(inventory_rows):
        raise ValueError("inventory contains duplicate stems")
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    layout_slots = {
        (int(row["class_id"]), int(sample["slot_index"])): sample
        for page in layout["pages"]
        for row in page["rows"]
        for sample in row["sample_bounds"]
    }
    if set(layout_slots) != set(expected_slots):
        raise ValueError("layout audit overlay coverage mismatch")
    atlas_cache: dict[str, Image.Image] = {}
    for row in lineage:
        class_id = int(row["class_id"])
        slot_index = int(row["slot_index"])
        slot = f"class {class_id} slot {slot_index}"
        stem = row["stem"]
        expected = expected_metadata[(class_id, slot_index)]
        if any(row[field] != expected[field] for field in expected):
            raise ValueError(f"overlay class/code/stem/page binding mismatch for {slot}")
        if stem not in inventory:
            raise ValueError(f"overlay lineage stem missing from inventory: {stem}")
        source = inventory[stem]
        if row["dataset_code"] == "" or row["split"] != source["split"]:
            raise ValueError(f"overlay lineage metadata mismatch for {slot}")
        if int(row["source_width"]) != int(source["width"]) or int(
            row["source_height"]
        ) != int(source["height"]):
            raise ValueError(f"source dimension mismatch for {slot}")
        if row["overlay_color"] != "220,20,60" or int(row["overlay_width"]) != 4:
            raise ValueError(f"overlay style mismatch for {slot}")
        image_path = raw_root / source["image_path"]
        label_path = raw_root / source["label_path"]
        if sha256_file(image_path) != row["image_sha256"] or row["image_sha256"] != source["image_sha256"]:
            raise ValueError(f"raw image hash mismatch for {slot}")
        if sha256_file(label_path) != row["label_sha256"] or row["label_sha256"] != source["label_sha256"]:
            raise ValueError(f"raw label hash mismatch for {slot}")
        target = select_target_box(label_path, class_id)
        if int(row["label_line_number"]) != int(target["label_line_number"]):
            raise ValueError(f"label line mismatch for {slot}")
        if int(row["label_index"]) != int(target["label_index"]):
            raise ValueError(f"label index mismatch for {slot}")
        for field, target_field in (
            ("normalized_x_center", "x_center"),
            ("normalized_y_center", "y_center"),
            ("normalized_width", "width"),
            ("normalized_height", "height"),
        ):
            require_close(row[field], float(target[target_field]), field, slot)
        geometry = overlay_geometry(int(source["width"]), int(source["height"]), target)
        if row["source_bbox_within_image"] != str(geometry["source_bbox_within_image"]):
            raise ValueError(f"source bbox boundary flag mismatch for {slot}")
        expected_values = {
            "source_bbox_overflow_left": geometry["source_bbox_overflow"][0],
            "source_bbox_overflow_top": geometry["source_bbox_overflow"][1],
            "source_bbox_overflow_right": geometry["source_bbox_overflow"][2],
            "source_bbox_overflow_bottom": geometry["source_bbox_overflow"][3],
            "source_bbox_x_min": geometry["source_bbox"][0],
            "source_bbox_y_min": geometry["source_bbox"][1],
            "source_bbox_x_max": geometry["source_bbox"][2],
            "source_bbox_y_max": geometry["source_bbox"][3],
            "context_crop_left": geometry["context_crop"][0],
            "context_crop_top": geometry["context_crop"][1],
            "context_crop_right": geometry["context_crop"][2],
            "context_crop_bottom": geometry["context_crop"][3],
            "context_padding_left": geometry["context_padding"][0],
            "context_padding_top": geometry["context_padding"][1],
            "context_padding_right": geometry["context_padding"][2],
            "context_padding_bottom": geometry["context_padding"][3],
            "render_scale": geometry["render_scale"],
            "render_offset_x": geometry["render_offset"][0],
            "render_offset_y": geometry["render_offset"][1],
            "sample_bbox_x_min": geometry["sample_bbox"][0],
            "sample_bbox_y_min": geometry["sample_bbox"][1],
            "sample_bbox_x_max": geometry["sample_bbox"][2],
            "sample_bbox_y_max": geometry["sample_bbox"][3],
            "sample_source_frame_x_min": geometry["sample_source_frame"][0],
            "sample_source_frame_y_min": geometry["sample_source_frame"][1],
            "sample_source_frame_x_max": geometry["sample_source_frame"][2],
            "sample_source_frame_y_max": geometry["sample_source_frame"][3],
        }
        for field, expected in expected_values.items():
            require_close(row[field], float(expected), field, slot)
        layout_slot = layout_slots[(class_id, slot_index)]
        if (
            layout_slot["stem"] != stem
            or int(layout_slot["target_class"]) != class_id
            or int(layout_slot["label_line_number"]) != int(row["label_line_number"])
            or layout_slot.get("overlay_present") is not True
        ):
            raise ValueError(f"layout target mismatch for {slot}")
        image_bounds = [float(value) for value in layout_slot["image_bounds"]]
        atlas_image_x = int(float(row["atlas_image_x"]))
        atlas_image_y = int(float(row["atlas_image_y"]))
        if image_bounds != [atlas_image_x, atlas_image_y, atlas_image_x + 250, atlas_image_y + 150]:
            raise ValueError(f"atlas image geometry mismatch for {slot}")
        atlas_bbox = [
            float(row["atlas_bbox_x_min"]),
            float(row["atlas_bbox_y_min"]),
            float(row["atlas_bbox_x_max"]),
            float(row["atlas_bbox_y_max"]),
        ]
        expected_atlas_bbox = [
            atlas_image_x + geometry["sample_bbox"][0],
            atlas_image_y + geometry["sample_bbox"][1],
            atlas_image_x + geometry["sample_bbox"][2],
            atlas_image_y + geometry["sample_bbox"][3],
        ]
        atlas_source_frame = [
            float(row["atlas_source_frame_x_min"]),
            float(row["atlas_source_frame_y_min"]),
            float(row["atlas_source_frame_x_max"]),
            float(row["atlas_source_frame_y_max"]),
        ]
        expected_atlas_source_frame = [
            atlas_image_x + geometry["sample_source_frame"][0],
            atlas_image_y + geometry["sample_source_frame"][1],
            atlas_image_x + geometry["sample_source_frame"][2],
            atlas_image_y + geometry["sample_source_frame"][3],
        ]
        for actual, expected in zip(atlas_bbox, expected_atlas_bbox, strict=True):
            if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-6):
                raise ValueError(f"atlas bbox geometry mismatch for {slot}")
        if [float(value) for value in layout_slot["overlay_bounds"]] != atlas_bbox:
            raise ValueError(f"layout overlay bbox mismatch for {slot}")
        for actual, expected in zip(
            atlas_source_frame, expected_atlas_source_frame, strict=True
        ):
            if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-6):
                raise ValueError(f"atlas source-frame geometry mismatch for {slot}")
        if [float(value) for value in layout_slot["source_frame_bounds"]] != (
            atlas_source_frame
        ):
            raise ValueError(f"layout source-frame mismatch for {slot}")
        if (
            layout_slot.get("out_of_frame_background") != "GRAY_HATCH"
            or layout_slot.get("source_boundary_style") != "CYAN_0_205_235_WIDTH_3"
        ):
            raise ValueError(f"layout boundary-style mismatch for {slot}")
        atlas_relative = Path(row["atlas_page"])
        if atlas_relative.is_absolute() or ".." in atlas_relative.parts:
            raise ValueError(f"atlas path escape for {slot}")
        atlas_path = repo_root / "docs/review" / atlas_relative
        cache_key = atlas_path.as_posix()
        if cache_key not in atlas_cache:
            with Image.open(atlas_path) as opened:
                atlas_cache[cache_key] = opened.convert("RGB")
        atlas_image = atlas_cache[cache_key]
        if not (
            0 <= atlas_bbox[0] < atlas_bbox[2] <= atlas_image.width
            and 0 <= atlas_bbox[1] < atlas_bbox[3] <= atlas_image.height
        ):
            raise ValueError(f"atlas overlay outside page for {slot}")
        if not overlay_pixels_present(atlas_image, atlas_bbox):
            raise ValueError(f"visible red overlay missing for {slot}")
        if any(value > 0 for value in geometry["context_padding"]) and not (
            source_boundary_pixels_present(atlas_image, atlas_source_frame)
        ):
            raise ValueError(f"visible source boundary missing for {slot}")
    required_rows = [
        row
        for row in lineage
        if int(row["class_id"]) == REQUIRED_BOUNDARY_CASE_0248["class_id"]
        and int(row["slot_index"]) == REQUIRED_BOUNDARY_CASE_0248["slot_index"]
    ]
    if len(required_rows) != 1 or required_rows[0]["stem"] != "0248":
        raise ValueError("required class-49 boundary case 0248 must occupy slot 1")
    required = required_rows[0]
    for field in (
        "image_sha256",
        "label_sha256",
        "label_line_number",
        "label_index",
        "source_width",
        "source_height",
    ):
        if str(required[field]) != str(REQUIRED_BOUNDARY_CASE_0248[field]):
            raise ValueError(f"required boundary case 0248 {field} mismatch")
    for field, expected in zip(
        (
            "source_bbox_x_min",
            "source_bbox_y_min",
            "source_bbox_x_max",
            "source_bbox_y_max",
        ),
        REQUIRED_BOUNDARY_CASE_0248["source_bbox"],
        strict=True,
    ):
        require_close(required[field], float(expected), field, "class 49 slot 1")
    require_close(
        required["source_bbox_overflow_right"],
        float(REQUIRED_BOUNDARY_CASE_0248["source_bbox_right_overflow"]),
        "source_bbox_overflow_right",
        "class 49 slot 1",
    )
    if required["source_bbox_within_image"] != "False":
        raise ValueError("required boundary case 0248 must remain outside the source image")
    if float(required["sample_bbox_x_max"]) <= float(
        required["sample_source_frame_x_max"]
    ):
        raise ValueError("required boundary case 0248 overlay must cross the source boundary")
    return {
        "slot_count": len(lineage),
        "class_count": 52,
        "visible_overlay_count": len(lineage),
        "geometry_reconciled_count": len(lineage),
        "raw_source_hashes_unchanged": True,
        "required_boundary_case": {
            "class_id": 49,
            "slot_index": 1,
            "stem": "0248",
            "label_line_number": 1,
            "label_index": 0,
            "source_bbox": REQUIRED_BOUNDARY_CASE_0248["source_bbox"],
            "right_overflow_px": REQUIRED_BOUNDARY_CASE_0248[
                "source_bbox_right_overflow"
            ],
            "source_bbox_within_image": False,
            "raw_hashes_unchanged": True,
        },
    }


def representative_stems_for_class(class_id: int, inherited: str) -> str:
    inherited_stems = inherited.split(";")
    if len(inherited_stems) != 3 or len(set(inherited_stems)) != 3:
        raise ValueError(f"class {class_id} must inherit exactly three unique WP3 stems")
    reserved = list(RESERVED_REPRESENTATIVE_STEMS.get(class_id, ()))
    selected = [*reserved, *(stem for stem in inherited_stems if stem not in reserved)][:3]
    if len(selected) != 3 or len(set(selected)) != 3:
        raise ValueError(f"class {class_id} deterministic representative selection failed")
    return ";".join(selected)


def build_worksheet(
    taxonomy_rows: list[dict[str, str]],
    atlas_rows: list[dict[str, str]],
    evidence_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {int(row["class_id"]): row for row in taxonomy_rows}
    atlas_by_id = {int(row["class_id"]): row for row in atlas_rows}
    if set(by_id) != EXPECTED_CLASS_IDS or set(atlas_by_id) != EXPECTED_CLASS_IDS:
        raise ValueError("WP2/WP3 taxonomy inputs must contain class_id 0..51")
    evidence_by_id = {int(row["class_id"]): row for row in evidence_rows}
    if set(evidence_by_id) != EXPECTED_CLASS_IDS:
        raise ValueError("canonical evidence index must contain class_id 0..51")
    worksheet: list[dict[str, Any]] = []
    for class_id in range(52):
        source = by_id[class_id]
        official = evidence_by_id[class_id]
        stems = representative_stems_for_class(
            class_id, atlas_by_id[class_id]["source_stems"]
        )
        worksheet.append(
            {
                "class_id": class_id,
                "dataset_code": source["dataset_code"],
                "dataset_name_vi_en": source["dataset_name_vi_en"],
                "image_count": int(source["image_count"]),
                "box_count": int(source["box_count"]),
                **{key: official[key] for key in (
                    "official_code_candidate", "official_name_vi", "official_pdf_page",
                    "official_section", "official_figure", "match_status", "reason",
                    "composite_or_parameterized",
                )},
                "gtsrb_mapping_proposal": source["gtsrb_mapping_proposal"],
                "gtsrb_relation_proposal": source["gtsrb_relation_proposal"],
                "reviewer_status": REVIEWER_STATUS,
                "evidence_confidence": official["evidence_confidence"],
                "evidence_method": official["evidence_method"],
                "representative_source_stems": stems,
                "atlas_page": f"assets/wp4/qcvn_taxonomy_atlas/page_{class_id // 4 + 1:03d}.jpg",
            }
        )
    return worksheet


def render_html_index(rows: list[dict[str, Any]], path: Path) -> None:
    table_rows = "\n".join(
        "<tr>"
        f"<td>{row['class_id']}</td><td>{html.escape(str(row['dataset_code']))}</td>"
        f"<td>{html.escape(str(row['official_code_candidate']) or 'NOT FOUND')}</td>"
        f"<td>{row['match_status']}</td><td>{html.escape(str(row['reason']))}</td>"
        f"<td><a href=\"page_{int(row['class_id']) // 4 + 1:03d}.jpg\">atlas page</a></td>"
        f"<td>{REVIEWER_STATUS}</td></tr>"
        for row in rows
    )
    path.write_text(
        "<!doctype html><meta charset=\"utf-8\"><title>M0-WP4 QCVN taxonomy evidence</title>"
        f"<h1>{PACKAGE_STATUS}</h1><p>D-03 remains PENDING. No relabel or approval.</p>"
        "<table border=\"1\"><tr><th>ID</th><th>Dataset</th><th>QCVN candidate</th>"
        "<th>Status</th><th>Reason</th><th>Evidence</th><th>Reviewer</th></tr>"
        f"{table_rows}</table>",
        encoding="utf-8",
    )


def report_markdown(rows: list[dict[str, Any]], pdf_info: dict[str, Any]) -> str:
    counts = Counter(str(row["match_status"]) for row in rows)
    known_rows = [rows[class_id] for class_id in KNOWN_CONFLICT_EXPECTATIONS]
    conflict_table = "\n".join(
        f"| {row['class_id']} | `{row['dataset_code']}` | `{row['official_code_candidate'] or 'NOT_FOUND'}` | {row['match_status']} | {row['reason']} | p.{row['official_pdf_page'] or '—'} |"
        for row in known_rows
    )
    return f"""# M0-WP4 — QCVN 41:2024 taxonomy evidence audit

**Status:** `{PACKAGE_STATUS}`  
**Decision boundary:** toàn bộ 52 dòng vẫn `{REVIEWER_STATUS}`; D-03 `PENDING`; Gate 0 `BLOCKED`; `training_authorized=false`. Báo cáo này không relabel dữ liệu và không phê duyệt mapping GTSRB.

## Nguồn chính thức đã khóa

- QCVN 41:2024/BGTVT: 403 trang, SHA-256 `{pdf_info['qcvn']['sha256']}`.
- Thông tư 51/2024/TT-BGTVT: 1 trang, SHA-256 `{pdf_info['circular']['sha256']}`.
- URL, thời điểm tải và kích thước nằm trong `references/qcvn41_2024/source_provenance.json`.
- Evidence index độc lập `references/qcvn41_2024/qcvn_taxonomy_evidence_index.json` khóa code/name/section/figure/token và fingerprint text + render của từng trang được trích dẫn; class 31 có negative-search scope riêng.
- Đã kiểm tra text layer theo từng khoảng trang được trích dẫn và kiểm tra trực quan các trang 1, 83, 87, 88, 106, 114, 117, 152.

## Kết quả 52 lớp

| Trạng thái | Số dòng |
|---|---:|
| EXACT | {counts['EXACT']} |
| PARTIAL | {counts['PARTIAL']} |
| MISMATCH | {counts['MISMATCH']} |
| NOT_FOUND | {counts['NOT_FOUND']} |
| NON_SIGN_CATEGORY | {counts['NON_SIGN_CATEGORY']} |

`NOT_FOUND` chỉ có nghĩa chưa tìm được ứng viên trong QCVN 41:2024 ở nguồn đã khóa, không phải kết luận rằng biển/biểu tượng đó không tồn tại trong mọi văn bản khác.

## Các xung đột bắt buộc kiểm tra

| ID | Dataset | Ứng viên QCVN | Kết quả | Lý do ngắn | Nguồn |
|---:|---|---|---|---|---|
{conflict_table}

## Tệp reviewer

- `docs/review/generated/wp4_qcvn_taxonomy_worksheet.csv`: worksheet 52 dòng, một dòng mỗi class ID.
- `docs/review/assets/wp4/qcvn_taxonomy_atlas/index.html`: atlas 13 trang, ba crop đại diện/dòng; đủ 156 bbox overlay có lineage tái dựng được về raw label/image.
- Sampling deterministic: `{SAMPLING_POLICY}`
- Boundary case bắt buộc `0248` nằm ở class 49 / slot 1. Raw 960x540, label line 1/index 0; bbox pixel `(927.00048, 158.99976, 978.00048, 213.99984)`, vượt mép phải `18.00048 px`. Atlas giữ nguyên bbox bằng virtual padding nền hatch xám và đường biên ảnh cyan; không clamp hay sửa raw.
- `docs/review/wp4_taxonomy_vnext_proposal.md`: đề xuất riêng; không sửa taxonomy hiện hành.
- `docs/review/generated/wp4_qcvn_manifest.json`: hash nguồn, PDF và artifacts.

## Blocker / quyết định còn mở

1. Reviewer chuyên môn phải quyết định từng dòng và D-03; script cố ý không có chức năng approve.
2. ID 31 cần nguồn pháp lý khác nếu muốn giữ claim camera; hiện là `NOT_FOUND` trong QCVN đã kiểm tra.
3. ID 23 và các lớp `S.505a` cần quyết định ontology trước relabel vì đây không phải quan hệ một-mã-một-nhãn đơn giản.
4. GTSRB proposal vẫn là cross-jurisdiction proposal; không được biến thành target training trước Gate 0.
"""


def proposal_markdown(rows: list[dict[str, Any]]) -> str:
    proposed = [row for row in rows if row["match_status"] != "EXACT"]
    body = "\n".join(
        f"| {row['class_id']} | `{row['dataset_code']}` | `{row['official_code_candidate'] or 'NOT_FOUND'}` | {row['match_status']} | {row['reason']} |"
        for row in proposed
    )
    return f"""# Taxonomy vNext proposal — M0-WP4

**PROPOSAL ONLY — DO NOT APPLY.** D-03 remains `PENDING`; every row remains `{REVIEWER_STATUS}`. This file is intentionally separate from the canonical taxonomy and contains no relabel operation.

## Candidate changes requiring domain review

| ID | Current code | Candidate code | Evidence status | Proposed review question |
|---:|---|---|---|---|
{body}

## Suggested reviewer actions

- Confirm official code/name against the cited page and figure.
- Inspect all three representative crops plus the full class corpus before accepting any semantic change.
- Decide whether parameterized values belong in one class, subclasses, or structured attributes.
- For S.505a, decide how the main sign and supplementary plate must be represented together.
- Record any approval only through the future D-03 workflow; do not edit this evidence file into an approval.
"""


def artifact_record(path: Path, root: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(root).as_posix(),
        "sha256": sha256_file(resolved),
        "size": resolved.stat().st_size,
    }


def source_record(name: str, path: Path, repo_root: Path) -> dict[str, Any]:
    try:
        logical = path.relative_to(repo_root).as_posix()
    except ValueError:
        logical = path.as_posix()
    return {"name": name, "path": logical, "sha256": sha256_file(path), "size": path.stat().st_size}


def resolve_manifest_path(repo_root: Path, value: str, collection: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{collection} path escape rejected: {value}")
    resolved_root = repo_root.resolve()
    resolved = (resolved_root / relative).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(f"{collection} path escape rejected: {value}") from error
    if not resolved.is_file():
        raise ValueError(f"required {collection} is missing: {value}")
    return resolved


def validate_decision_boundary(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("gate0") != "BLOCKED" or payload.get("training_authorized") is not False:
        raise ValueError("Gate 0/training boundary unexpectedly changed")
    if payload["decisions"]["D-03"]["status"] != "PENDING":
        raise ValueError("D-03 must remain PENDING")
    return {"gate0": "BLOCKED", "training_authorized": False, "D-03": "PENDING"}


def build(args: argparse.Namespace) -> dict[str, Any]:
    validate_evidence_table()
    repo_root = args.repo_root.resolve()
    tracked_inputs = {
        "qcvn_pdf": args.qcvn_pdf,
        "circular_pdf": args.circular_pdf,
        "source_provenance": args.source_provenance,
        "evidence_index": args.evidence_index,
        "taxonomy_review": args.taxonomy_csv,
        "wp3_atlas": args.wp3_atlas_csv,
        "wp3_manifest": args.wp3_manifest,
        "wp2_manifest": args.wp2_manifest,
        "wp1_manifest": args.wp1_manifest,
        "source_preservation": args.source_preservation,
        "inventory": args.inventory_csv,
        "decision_status": args.decision_status,
        "canonical_taxonomy": args.canonical_taxonomy,
    }
    before = {name: sha256_file(path) for name, path in tracked_inputs.items()}
    pdf_info = verify_pdf_sources(args.qcvn_pdf, args.circular_pdf, args.source_provenance)
    token_audit = verify_page_tokens(args.qcvn_pdf)
    evidence_rows, evidence_index_audit = load_and_verify_evidence_index(
        args.evidence_index, args.qcvn_pdf, repo_root
    )
    boundary = validate_decision_boundary(args.decision_status)
    taxonomy_rows = read_csv(args.taxonomy_csv)
    atlas_rows = read_csv(args.wp3_atlas_csv)
    worksheet = build_worksheet(taxonomy_rows, atlas_rows, evidence_rows)
    inventory = {row["stem"]: row for row in read_csv(args.inventory_csv)}
    output_dir = args.output_dir
    assets_dir = args.assets_dir
    report_path = args.report_path
    proposal_path = args.proposal_path
    if assets_dir.exists():
        shutil.rmtree(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)
    layout_pages: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    for offset in range(0, len(worksheet), 4):
        page_number = offset // 4 + 1
        page_path = assets_dir / f"page_{page_number:03d}.jpg"
        audit, page_lineage = render_atlas_page(
            worksheet[offset : offset + 4], page_number, inventory, args.raw_root, page_path
        )
        layout_pages.append(audit)
        lineage.extend(page_lineage)
    render_html_index(worksheet, assets_dir / "index.html")
    output_dir.mkdir(parents=True, exist_ok=True)
    worksheet_path = output_dir / "wp4_qcvn_taxonomy_worksheet.csv"
    lineage_path = output_dir / "wp4_qcvn_source_lineage.csv"
    layout_path = output_dir / "wp4_qcvn_layout_audit.json"
    summary_path = output_dir / "wp4_qcvn_summary.json"
    manifest_path = output_dir / "wp4_qcvn_manifest.json"
    write_csv(worksheet_path, worksheet, WORKSHEET_FIELDS)
    lineage = sorted(
        lineage, key=lambda row: (int(row["class_id"]), int(row["slot_index"]))
    )
    if len(lineage) != 156:
        raise RuntimeError("atlas must produce exactly 156 overlay lineage records")
    write_csv(lineage_path, lineage, LINEAGE_FIELDS)
    write_json(
        layout_path,
        {
            "schema_version": 2,
            "page_count": len(layout_pages),
            "row_count": len(worksheet),
            "overlay_count": len(lineage),
            "all_bounds_fit": True,
            "all_text_complete": True,
            "all_overlays_within_canvas": True,
            "all_overlays_visible": True,
            "pages": layout_pages,
        },
    )
    overlay_audit = verify_overlay_lineage(
        lineage_path,
        layout_path,
        args.inventory_csv,
        args.raw_root,
        repo_root,
        worksheet,
    )
    counts = Counter(str(row["match_status"]) for row in worksheet)
    summary = {
        "schema_version": 2,
        "status": PACKAGE_STATUS,
        "class_count": len(worksheet),
        "reviewer_status_counts": {REVIEWER_STATUS: len(worksheet)},
        "match_status_counts": dict(sorted(counts.items())),
        "known_conflict_expectations": {str(key): value for key, value in KNOWN_CONFLICT_EXPECTATIONS.items()},
        "qcvn_pdf": pdf_info["qcvn"],
        "circular_pdf": pdf_info["circular"],
        "page_token_audit": token_audit,
        "evidence_index_audit": evidence_index_audit,
        "overlay_audit": overlay_audit,
        "sampling_policy": {
            "description": SAMPLING_POLICY,
            "reserved_examples": {"49": ["0248"]},
        },
        "decision_boundary": boundary,
        "atlas_page_count": len(layout_pages),
        "overlay_slot_count": len(lineage),
        "representative_source_count": len({row["stem"] for row in lineage}),
        "mutation_count": 0,
    }
    write_json(summary_path, summary)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_markdown(worksheet, pdf_info), encoding="utf-8")
    proposal_path.parent.mkdir(parents=True, exist_ok=True)
    proposal_path.write_text(proposal_markdown(worksheet), encoding="utf-8")
    after = {name: sha256_file(path) for name, path in tracked_inputs.items()}
    if before != after:
        raise RuntimeError("source/control input mutation detected")
    artifacts = [
        worksheet_path,
        lineage_path,
        layout_path,
        summary_path,
        report_path,
        proposal_path,
        assets_dir / "index.html",
        *sorted(assets_dir.glob("page_*.jpg")),
    ]
    manifest = {
        "schema_version": 2,
        "status": PACKAGE_STATUS,
        "artifact_count": len(artifacts),
        "artifacts": [artifact_record(path, repo_root) for path in artifacts],
        "sources": [source_record(name, path, repo_root) for name, path in tracked_inputs.items()],
        "source_hashes_unchanged": True,
        "pdf_sources": pdf_info,
        "decision_boundary": boundary,
    }
    write_json(manifest_path, manifest)
    return {"manifest": manifest_path.as_posix(), **summary}


def verify(args: argparse.Namespace) -> dict[str, Any]:
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    repo_root = args.repo_root.resolve()
    if manifest.get("schema_version") != 2 or manifest.get("status") != PACKAGE_STATUS:
        raise ValueError("manifest schema/status mismatch")
    source_records = manifest.get("sources")
    artifact_records = manifest.get("artifacts")
    if not isinstance(source_records, list) or not isinstance(artifact_records, list):
        raise ValueError("manifest sources/artifacts must be lists")
    source_names = [record.get("name") for record in source_records]
    if len(source_names) != len(set(source_names)) or set(source_names) != set(
        TRACKED_SOURCE_NAMES
    ):
        raise ValueError("manifest source controls mismatch")
    resolved_sources: dict[str, Path] = {}
    for record in source_records:
        source_path = resolve_manifest_path(repo_root, str(record["path"]), "source")
        if sha256_file(source_path) != record["sha256"] or source_path.stat().st_size != record["size"]:
            raise ValueError(f"source hash/size mismatch: {record['name']}")
        resolved_sources[str(record["name"])] = source_path
    artifact_paths = [str(record.get("path")) for record in artifact_records]
    if len(artifact_paths) != len(set(artifact_paths)):
        raise ValueError("manifest artifact paths must be unique")
    if manifest.get("artifact_count") != len(artifact_records):
        raise ValueError("manifest artifact count mismatch")
    for record in artifact_records:
        artifact = resolve_manifest_path(repo_root, str(record["path"]), "artifact")
        if sha256_file(artifact) != record["sha256"] or artifact.stat().st_size != record["size"]:
            raise ValueError(f"artifact hash/size mismatch: {record['path']}")
    if resolved_sources["evidence_index"] != resolve_control_path(
        args.evidence_index, repo_root, EVIDENCE_INDEX_RELATIVE_PATH
    ):
        raise ValueError("manifest evidence-index path mismatch")
    if resolved_sources["qcvn_pdf"] != args.qcvn_pdf.resolve():
        raise ValueError("manifest QCVN path mismatch")
    if resolved_sources["circular_pdf"] != args.circular_pdf.resolve():
        raise ValueError("manifest circular path mismatch")
    if resolved_sources["source_provenance"] != args.source_provenance.resolve():
        raise ValueError("manifest provenance path mismatch")
    pdf_info = verify_pdf_sources(args.qcvn_pdf, args.circular_pdf, args.source_provenance)
    evidence_rows, evidence_index_audit = load_and_verify_evidence_index(
        args.evidence_index, args.qcvn_pdf, repo_root
    )
    worksheet = read_csv(args.worksheet)
    if list(worksheet[0]) != WORKSHEET_FIELDS:
        raise ValueError("worksheet schema mismatch")
    ids = [int(row["class_id"]) for row in worksheet]
    if len(ids) != 52 or set(ids) != EXPECTED_CLASS_IDS or len(set(ids)) != len(ids):
        raise ValueError("worksheet must contain class_id 0..51 exactly once")
    if any(row["reviewer_status"] != REVIEWER_STATUS for row in worksheet):
        raise ValueError("all worksheet rows must remain UNAPPROVED")
    compare_worksheet_to_index(worksheet, evidence_rows)
    by_id = {int(row["class_id"]): row for row in worksheet}
    for class_id, expected in KNOWN_CONFLICT_EXPECTATIONS.items():
        if by_id[class_id]["match_status"] != expected:
            raise ValueError(f"known conflict status mismatch for class {class_id}")
    for row in worksheet:
        pages = page_numbers(row["official_pdf_page"])
        if int(row["class_id"]) == 31:
            if pages or row["official_code_candidate"]:
                raise ValueError("class 31 NOT_FOUND row must not invent a page/code")
        elif not pages or any(page < 1 or page > 403 for page in pages):
            raise ValueError(f"invalid official page range for class {row['class_id']}")
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    if (
        summary.get("status") != PACKAGE_STATUS
        or summary["class_count"] != 52
        or summary["mutation_count"] != 0
        or summary.get("overlay_slot_count") != 156
        or summary.get("evidence_index_audit") != evidence_index_audit
    ):
        raise ValueError("summary control count mismatch")
    overlay_audit = verify_overlay_lineage(
        args.lineage,
        args.layout_audit,
        args.inventory_csv,
        args.raw_root,
        repo_root,
        worksheet,
    )
    if summary.get("overlay_audit") != overlay_audit:
        raise ValueError("summary overlay audit mismatch")
    validate_decision_boundary(args.decision_status)
    return {
        "status": "PASS",
        "class_count": 52,
        "artifact_count": manifest["artifact_count"],
        "evidence_index_sha256": evidence_index_audit["index_sha256"],
        "overlay_slot_count": overlay_audit["slot_count"],
        "visible_overlay_count": overlay_audit["visible_overlay_count"],
        "qcvn_page_count": pdf_info["qcvn"]["page_count"],
        "known_conflicts_checked": len(KNOWN_CONFLICT_EXPECTATIONS),
        "source_hashes_checked": len(source_records),
        "artifact_hashes_checked": len(artifact_records),
    }


def default_paths(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--qcvn-pdf", type=Path, default=Path("references/qcvn41_2024/qcvn-41-2024-bgtvt.pdf"))
    parser.add_argument("--circular-pdf", type=Path, default=Path("references/qcvn41_2024/51-2024-tt-bgtvt.pdf"))
    parser.add_argument("--source-provenance", type=Path, default=Path("references/qcvn41_2024/source_provenance.json"))
    parser.add_argument("--evidence-index", type=Path, default=EVIDENCE_INDEX_RELATIVE_PATH)
    parser.add_argument("--taxonomy-csv", type=Path, default=Path("docs/review/generated/taxonomy_review.csv"))
    parser.add_argument("--wp3-atlas-csv", type=Path, default=Path("docs/review/generated/wp3_taxonomy_reviewer_atlas.csv"))
    parser.add_argument("--wp3-manifest", type=Path, default=Path("docs/review/generated/wp3_evidence_manifest.json"))
    parser.add_argument("--wp2-manifest", type=Path, default=Path("docs/review/generated/wp2_generated_manifest.json"))
    parser.add_argument("--wp1-manifest", type=Path, default=Path("results/data_audit/DATASET01_052bc980a7206f8d/wp1_artifact_manifest.json"))
    parser.add_argument("--source-preservation", type=Path, default=Path("results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json"))
    parser.add_argument("--inventory-csv", type=Path, default=Path("results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv"))
    parser.add_argument("--decision-status", type=Path, default=Path("docs/review/decision_status.json"))
    parser.add_argument("--canonical-taxonomy", type=Path, default=Path("docs/vietnam_taxonomy_mapping.md"))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    default_paths(build_parser)
    build_parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"),
    )
    build_parser.add_argument("--output-dir", type=Path, default=Path("docs/review/generated"))
    build_parser.add_argument("--assets-dir", type=Path, default=Path("docs/review/assets/wp4/qcvn_taxonomy_atlas"))
    build_parser.add_argument("--report-path", type=Path, default=Path("docs/review/m0_wp4_qcvn_taxonomy_report.md"))
    build_parser.add_argument("--proposal-path", type=Path, default=Path("docs/review/wp4_taxonomy_vnext_proposal.md"))
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    verify_parser.add_argument("--manifest", type=Path, default=Path("docs/review/generated/wp4_qcvn_manifest.json"))
    verify_parser.add_argument("--worksheet", type=Path, default=Path("docs/review/generated/wp4_qcvn_taxonomy_worksheet.csv"))
    verify_parser.add_argument("--summary", type=Path, default=Path("docs/review/generated/wp4_qcvn_summary.json"))
    verify_parser.add_argument("--qcvn-pdf", type=Path, default=Path("references/qcvn41_2024/qcvn-41-2024-bgtvt.pdf"))
    verify_parser.add_argument("--circular-pdf", type=Path, default=Path("references/qcvn41_2024/51-2024-tt-bgtvt.pdf"))
    verify_parser.add_argument("--source-provenance", type=Path, default=Path("references/qcvn41_2024/source_provenance.json"))
    verify_parser.add_argument("--evidence-index", type=Path, default=EVIDENCE_INDEX_RELATIVE_PATH)
    verify_parser.add_argument("--lineage", type=Path, default=Path("docs/review/generated/wp4_qcvn_source_lineage.csv"))
    verify_parser.add_argument("--layout-audit", type=Path, default=Path("docs/review/generated/wp4_qcvn_layout_audit.json"))
    verify_parser.add_argument("--inventory-csv", type=Path, default=Path("results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv"))
    verify_parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"),
    )
    verify_parser.add_argument("--decision-status", type=Path, default=Path("docs/review/decision_status.json"))
    return root


def main() -> None:
    args = parser().parse_args()
    result = build(args) if args.command == "build" else verify(args)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
