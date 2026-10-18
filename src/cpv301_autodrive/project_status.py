"""Project-status snapshot shown in the Streamlit app.

Mirrors `docs/product_roadmap.md` (Gate 0, decisions D-01…D-05, milestones M0…M6). The roadmap is
the canonical source: update both together. Nothing here approves a decision or authorizes training.
"""

from __future__ import annotations

STATUS_AS_OF = "2026-10-18"
CURRENT_PHASE = "Gate 0 đã mở — M1 (gói train detector VN) đang làm"
TRAINING_STATUS = "Được phép (D-05)"

# (stage, what it does, status)
PIPELINE: tuple[tuple[str, str, str], ...] = (
    ("Camera", "Ảnh tải lên hoặc snapshot webcam", "Đã có"),
    ("Detector", "Tìm và phân lớp biển VN trong khung hình đầy đủ (YOLO)", "M4 · ưu tiên kế tiếp"),
    ("Classifier", "E0 GTSRB 43 lớp; crop classifier VN làm sau detector", "E0 tham chiếu"),
    ("Temporal voting", "Ổn định kết quả qua nhiều frame", "M5 · đề xuất"),
    ("Hành vi", "Luật mô phỏng xe, không điều khiển xe thật", "Đã có (mô phỏng)"),
)

# (id, criterion, status)
GATE0: tuple[tuple[str, str, str], ...] = (
    (
        "G0.1",
        "Nguồn và license: owner chấp nhận rủi ro, áp dụng điều kiện CC-BY-SA chặt nhất",
        "PASS",
    ),
    ("G0.2", "Staging bất biến theo hash, nguồn không bị thay đổi", "PASS"),
    ("G0.3", "3.216 ảnh và 3.216 label ghép 1:1, decode 100%", "PASS"),
    ("G0.4", "Cách ly toàn bộ stem 0248 (bbox vượt mép ảnh)", "PASS"),
    ("G0.5", "Taxonomy: D-03 đã duyệt, nhãn dẫn xuất WP33 (54 lớp) QA PASS", "PASS"),
    ("G0.6", "Mỗi ảnh có group_id (D02-P1: 54 nhóm capture)", "PASS"),
    ("G0.7", "WP36-R1 owner chấp nhận: 59,9/11,8/28,3 %, test niêm phong afa03d4b", "PASS"),
    (
        "G0.8",
        "D-04: cả 54 lớp có quyết định owner (12 làm giàu, 27 đủ, 6 không val, 9 chỉ train)",
        "PASS",
    ),
    (
        "G0.9",
        "WP37-R1 dataset card (docs/dataset01_card_r1.md), QA PASS",
        "PASS",
    ),
)

# (id, decision, what is needed from the owner)
DECISIONS: tuple[tuple[str, str, str], ...] = (
    ("D-01", "Provenance / license", "Đã duyệt 2026-10-17: chấp nhận rủi ro, CC-BY-SA chặt nhất"),
    ("D-02", "Group identity", "Đã duyệt 2026-10-17: D02-P1, 54 nhóm capture"),
    ("D-03", "Taxonomy", "Đã duyệt 2026-10-17; WP33: 54 lớp train, lớp 31 → UNKNOWN"),
    (
        "D-04",
        "Lớp hiếm",
        "Đã duyệt: part 1 (12 lớp làm giàu WP35) và part 2 (42 lớp theo WP34-R1); nền chỉ ảnh 0544",
    ),
    (
        "D-05",
        "Ngưỡng và compute",
        "Đã duyệt 2026-10-18: D05-B, mAP50 ≥ 0,60, recall ≥ 0,85, p95 ≤ 100 ms",
    ),
)

# (milestone, scope, status)
MILESTONES: tuple[tuple[str, str, str], ...] = (
    ("M0", "Quản trị dữ liệu DATASET01, mở Gate 0", "Hoàn thành · Gate 0 mở"),
    ("M1", "Gói train tái lập (PyTorch/Ultralytics), loader kiểm hash split", "Đang làm"),
    ("M2", "E1 retrain, E2 VGG16 transfer, E3 xử lý mất cân bằng", "Đề xuất"),
    ("M3", "E4 calibration và phát hiện ảnh lạ (OOD)", "Đề xuất"),
    ("M4", "Detector VN trên khung hình đầy đủ (D1)", "Ưu tiên kế tiếp"),
    ("M5", "Detector + classifier + tracking trên video", "Đề xuất"),
    ("M6", "Hoàn thiện Streamlit, E2E, hiệu năng", "Một phần"),
)

# Edge-review coverage for D-02, from the WP30 report and the dataset graph.
REVIEW_PROGRESS = {
    "edges_total": 3178,
    "edges_reviewed": 3176,
    "edges_pending": 0,
    "edges_quarantined": 2,
    "awaiting_qa": (),
}
