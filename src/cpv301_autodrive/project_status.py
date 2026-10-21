"""Project-status snapshot shown in the Streamlit app.

Mirrors `docs/product_roadmap.md` (Gate 0, decisions D-01…D-05, milestones M0…M6). The roadmap is
the canonical source: update both together. Nothing here approves a decision or authorizes training.
"""

from __future__ import annotations

from dataclasses import dataclass

STATUS_AS_OF = "2026-10-18"
CURRENT_PHASE = "M4/D1 — chạy thử train detector trên Colab L4; pilot chưa chạy"
# Short D1 status shown on the Model and Next-steps slides (see PROJECT_MEMORY.md, M4/D1).
D1_STATUS = (
    "Gói train M1 đã QA PASS; trọng số pretrained `yolo11s.pt` đã pin hash. Lần chạy thử 2 epoch "
    "trên Colab L4 (tạm dừng rồi khôi phục ở runtime mới) đã chạy, đang sửa theo QA. Pilot 100 "
    "epoch chưa chạy, chưa có model Việt Nam đạt chuẩn và test niêm phong chưa được mở."
)
TRAINING_STATUS = "Được phép (D-05)"

# (stage, what it does, status)
PIPELINE: tuple[tuple[str, str, str], ...] = (
    ("Camera", "Ảnh tải lên hoặc snapshot webcam", "Đã có"),
    ("Detector", "Tìm và phân lớp biển VN trong khung hình đầy đủ (YOLO)", "M4 · ưu tiên kế tiếp"),
    ("Classifier", "E0 GTSRB 43 lớp; crop classifier VN làm sau detector", "E0 tham chiếu"),
    ("Temporal voting", "Ổn định kết quả qua nhiều frame", "M5 · đề xuất"),
    ("Hành vi", "Luật mô phỏng xe, không điều khiển xe thật", "Đã có (mô phỏng)"),
)


@dataclass(frozen=True)
class StageDetail:
    """One pipeline stage as shown on the interactive Pipeline slide."""

    name: str
    icon: str
    state: str  # READY | NEXT | REFERENCE | PLANNED
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    method: tuple[str, ...]
    numbers: tuple[tuple[str, str, str], ...]  # (label, value, source/measurement note)
    evidence: tuple[str, ...]


# Badge colour per state; READY = available now, NEXT = owner priority, PLANNED = roadmap only.
STAGE_STATE_LABEL = {
    "READY": ("Đã có", "green"),
    "NEXT": ("Ưu tiên kế tiếp", "orange"),
    "REFERENCE": ("Tham chiếu", "blue"),
    "PLANNED": ("Đề xuất", "gray"),
}

PIPELINE_STAGES: tuple[StageDetail, ...] = (
    StageDetail(
        name="Camera",
        icon=":material/photo_camera:",
        state="READY",
        inputs=("Ảnh tải lên (PNG/JPG/WebP) hoặc snapshot webcam trong app",),
        outputs=("Khung hình RGB",),
        method=("Đọc ảnh bằng Pillow, chuyển về RGB; chưa có luồng video liên tục",),
        numbers=(
            ("Khung hình DATASET01", "3.216", "WP1 audit"),
            ("Độ phân giải", "960×540 · 1920×1080 · 540×960", "2.364 / 813 / 39 ảnh"),
            ("EXIF / GPS", "0 / 0", "không có metadata nơi chụp, thời gian"),
        ),
        evidence=("docs/dataset01_card_r1.md",),
    ),
    StageDetail(
        name="Detector",
        icon=":material/center_focus_strong:",
        state="NEXT",
        inputs=("Khung hình toàn cảnh, letterbox 1280 px",),
        outputs=("Khung bao biển báo", "Lớp trong 54 lớp WP33", "Độ tin cậy"),
        method=(
            "YOLO11s 54 lớp từ trọng số pretrained COCO, PyTorch + Ultralytics (`detector/`)",
            "Train trên Colab GPU L4, có checkpoint để khôi phục khi runtime bị ngắt",
            "Không lật ngang ảnh; train trên split WP36-R1; test niêm phong",
        ),
        numbers=(
            ("Dữ liệu train / val", "3.712 / 376 ảnh", "1.912 ảnh thật + 1.800 ảnh WP35"),
            ("Test niêm phong", "903 ảnh", "chỉ mở một lần ở đánh giá cuối"),
            ("Tốc độ YOLO11n", "~23 ms (~43 FPS)", "đo trên M1 Pro, trọng số ngẫu nhiên"),
            ("Gate D-05", "mAP50 ≥ 0,60 · recall ≥ 0,85", "p95 ≤ 100 ms"),
        ),
        evidence=("docs/review/d05_owner_decision_record.md", "detector/m1/cli.py"),
    ),
    StageDetail(
        name="Classifier",
        icon=":material/category:",
        state="REFERENCE",
        inputs=("Ảnh biển báo đã crop, 32×32 RGB",),
        outputs=("Một trong 43 lớp GTSRB (Đức)", "Độ tin cậy Softmax"),
        method=(
            "E0: CNN nhỏ kiểu VGG (2,2 triệu tham số), không phải VGG16 chuẩn",
            "Gói crop Việt Nam kiểu GTSRB đã sẵn cho E1–E4, làm sau detector",
        ),
        numbers=(
            ("Accuracy GTSRB test", "0,8682", "12.630 ảnh, E0 đóng băng"),
            ("Macro-F1 GTSRB", "0,7921", "chưa kiểm chứng cho Việt Nam"),
            ("Gói crop Việt Nam", "12.621 / 560", "train.p / valid.p"),
        ),
        evidence=(
            "results/experiments/E0_GTSRB_baseline/manifest.json",
            "docs/review/generated/dataset01_crops_manifest.json",
        ),
    ),
    StageDetail(
        name="Temporal voting",
        icon=":material/timeline:",
        state="PLANNED",
        inputs=("Chuỗi kết quả detector qua nhiều khung hình liên tiếp",),
        outputs=("Sự kiện biển báo đã ổn định",),
        method=("Theo dõi đối tượng và bỏ phiếu theo thời gian (M5)",),
        numbers=(("Trạng thái", "Chưa làm", "sau khi detector đạt D-05"),),
        evidence=("docs/product_roadmap.md",),
    ),
    StageDetail(
        name="Hành vi",
        icon=":material/directions_car:",
        state="READY",
        inputs=("Nhãn biển báo, cờ chấp nhận, tốc độ hành trình",),
        outputs=("Lệnh xe mô phỏng: hành động và tốc độ mục tiêu",),
        method=(
            "Luật cố định trong `behavior.py`, 8 hành động: tiếp tục, giảm tốc, đặt giới hạn tốc "
            "độ, dừng, nhường đường, rẽ trái, rẽ phải, cần xem lại",
            "Chỉ mô phỏng, không điều khiển xe thật",
        ),
        numbers=(
            ("Ngưỡng chấp nhận demo", "0,50", "chưa hiệu chỉnh, không phải ngưỡng OOD"),
            ("Lớp chưa kiểm chứng", "22", "không kích hoạt hành vi tự động (D-04, D-05)"),
        ),
        evidence=("src/cpv301_autodrive/behavior.py",),
    ),
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
    ("M1", "Gói train tái lập (PyTorch/Ultralytics), loader kiểm hash split", "QA PASS"),
    ("M2", "E1 retrain, E2 VGG16 transfer, E3 xử lý mất cân bằng", "Đề xuất"),
    ("M3", "E4 calibration và phát hiện ảnh lạ (OOD)", "Đề xuất"),
    ("M4", "Detector VN trên khung hình đầy đủ (D1)", "Đang làm · chạy thử Colab"),
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

# Gate 0 timeline: (date, event, gate/decision codes). Dates from the owner records and audits.
GOVERNANCE_TIMELINE: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("2026-10-10", "Staging bất biến theo hash, audit kỹ thuật DATASET01 (WP1)", ("G0.2", "G0.3")),
    ("2026-10-11", "Cách ly toàn bộ stem 0248 có khung vượt mép ảnh (WP10)", ("G0.4",)),
    ("2026-10-17", "Chấp nhận rủi ro license, áp điều khoản CC-BY-SA chặt nhất", ("D-01", "G0.1")),
    ("2026-10-17", "Duyệt 54 nhóm capture làm group_id (WP31-R2)", ("D-02", "G0.6")),
    ("2026-10-17", "Duyệt taxonomy; nhãn dẫn xuất WP33 54 lớp QA PASS", ("D-03", "G0.5")),
    ("2026-10-17", "12 lớp hiếm được train kèm làm giàu bằng biến đổi ảnh thật (WP35)", ("D-04",)),
    ("2026-10-18", "Quyết định cho 42 lớp còn lại; chỉ ảnh 0544 làm nền", ("D-04", "G0.8")),
    ("2026-10-18", "Chấp nhận split train/val/test WP36-R1, test niêm phong", ("G0.7",)),
    ("2026-10-18", "Dataset card WP37-R1 QA PASS", ("G0.9",)),
    ("2026-10-18", "Duyệt ngưỡng nghiệm thu D-05 → Gate 0 mở", ("D-05",)),
)

# WP36-R1 usable frames per split.
SPLIT_FRAMES = (("Train", 1912), ("Val", 376), ("Test (niêm phong)", 903))

# Inference time per frame on M1 Pro (MPS, 1280 px, batch 1), measured 2026-10-18 with random
# weights (speed does not depend on weights); typical frame = 3 signs. (pipeline, ms)
LATENCY_MEASURED_MS = (
    ("YOLO11n 54 lớp", 23.2),
    ("YOLO11s 54 lớp", 38.8),
    ("YOLO11n 1 lớp + CNN E0", 29.6),
    ("YOLO11n 1 lớp + VGG16 chuẩn", 53.8),
    ("YOLO11s 1 lớp + VGG16 chuẩn", 70.7),
)

# Hours for 100 epochs of YOLO11n at 1280 px. (where, low, high, measured?)
TRAIN_HOURS_YOLO11N = (
    ("M1 Pro (máy hiện tại)", 21.0, 21.0, True),
    ("Colab T4", 5.0, 6.0, False),
    ("Colab L4", 2.5, 3.5, False),
    ("Colab A100", 1.2, 1.5, False),
)
