"""Visual Streamlit lesson for YOLO11s one-class sign detection on selected images."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

from cpv301_autodrive import detector_d1, detector_s1
from cpv301_autodrive.dynamic_threshold import Candidate, ThresholdPolicy, apply_policy
from cpv301_autodrive.dynamic_threshold_comparison import (
    compare,
    decision_rows,
    draw_decisions,
)
from cpv301_autodrive.views import read_uploaded_image

MAX_IMAGES = 8
MAX_PIXELS = 12_000_000


@st.cache_resource(show_spinner="Đang nạp YOLO11s một lớp…", max_entries=1)
def get_s1_detector() -> detector_s1.S1Detector:
    return detector_s1.S1Detector()


@st.cache_data(show_spinner=False, max_entries=32)
def detect_s1_frame(image_bytes: bytes, conf: float) -> list[tuple[float, tuple[float, ...]]]:
    """Cache primitive boxes; model objects remain in the resource cache only."""
    with Image.open(BytesIO(image_bytes)) as source:
        return [
            (d.confidence, d.box)
            for d in get_s1_detector().detect(source.convert("RGB"), conf=conf)
        ]


def _selected_samples() -> list[tuple[str, Image.Image]]:
    samples = detector_d1.sample_images()
    if not samples:
        st.info("Không có ảnh mẫu validation trên máy này; hãy tải ảnh lên.")
        return []
    by_stem = {path.stem: path for path in samples}
    selected = st.multiselect(
        "Chọn ảnh mẫu",
        options=list(by_stem),
        default=list(by_stem)[:1],
        max_selections=MAX_IMAGES,
        key="s1_samples",
        help="Ảnh validation dùng để minh họa, không đại diện cho tỷ lệ đúng của model.",
    )
    images = []
    for stem in selected:
        path: Path = by_stem[stem]
        try:
            with Image.open(path) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
            if image.width * image.height > MAX_PIXELS:
                st.error(f"{path.name}: ảnh vượt giới hạn 12 triệu pixel.")
                continue
            images.append((path.name, image))
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
            st.error(f"Không thể đọc {path.name}: {exc}")
    return images


def _uploaded_images() -> list[tuple[str, Image.Image]]:
    uploads = st.file_uploader(
        "Chọn tối đa 8 ảnh toàn cảnh",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        max_upload_size=15,
        key="s1_uploads",
    )
    if len(uploads) > MAX_IMAGES:
        st.error(f"Chỉ xử lý tối đa {MAX_IMAGES} ảnh mỗi lần; hãy bỏ bớt ảnh.")
        return []
    images = []
    for upload in uploads:
        try:
            image = read_uploaded_image(upload)
            if image.width * image.height > MAX_PIXELS:
                st.error(f"{upload.name}: ảnh vượt giới hạn 12 triệu pixel.")
                continue
            images.append((upload.name, image))
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
            st.error(f"Không thể đọc {upload.name}: {exc}")
    return images


def render_s1_demo() -> None:
    """Let users select several still images and inspect each one-class detection."""
    st.subheader("YOLO11s một lớp · tìm vị trí biển báo")
    st.caption(
        "Input: ảnh toàn cảnh đã chọn. Output: khung bao và điểm tin cậy của từng biển "
        "trên từng ảnh. "
        "Model chỉ trả lời 'có biển ở đâu', chưa cho biết đó là loại biển nào. "
        "Trọng số Cascade B0, 100 epoch; demo trên ảnh, chưa nghiệm thu an toàn."
    )
    if not detector_s1.weights_available():
        st.error(
            "Không tìm thấy trọng số YOLO11s một lớp trên máy này; trọng số không có trong Git.",
            icon=":material/error:",
        )
        return
    mode = st.segmented_control(
        "Xử lý kết quả",
        ["Ngưỡng cố định", "Dynamic Threshold", "So sánh hai chế độ"],
        default="Ngưỡng cố định",
        key="s1_threshold_mode",
    )
    dt_policy = ThresholdPolicy("YOLO11s một lớp · baseline", detector_s1.DEFAULT_CONF)
    with st.container(horizontal=True, vertical_alignment="bottom"):
        source = st.segmented_control(
            "Nguồn ảnh",
            ["Ảnh mẫu (val)", "Tải ảnh lên"],
            default="Ảnh mẫu (val)",
            key="s1_source",
        )
        conf = (
            st.slider("Ngưỡng tin cậy", 0.05, 0.95, detector_s1.DEFAULT_CONF, 0.05, key="s1_conf")
            if mode in {"Ngưỡng cố định", "So sánh hai chế độ"}
            else dt_policy.default_conf
        )
    if mode == "Dynamic Threshold":
        st.info(
            "DT xử lý các box YOLO một lớp đã trả về: lọc điểm và có thể xử lý box trùng. "
            "Policy hiện tại chỉ dùng ngưỡng 0,20; chưa có rule trùng box được đánh giá để bật. "
            "YOLO một lớp chưa biết mã biển, nên không thể áp dụng rule riêng cho R.415a."
        )
    images = _uploaded_images() if source == "Tải ảnh lên" else _selected_samples()
    if not images:
        st.info("Chọn một hoặc nhiều ảnh để xem model phát hiện biển.")
        return
    st.caption(f"{len(images)} ảnh được chọn · xử lý riêng từng ảnh · không phân loại mã biển")
    for number, (name, image) in enumerate(images, start=1):
        with st.container(border=True):
            st.markdown(f"**Ảnh {number}: {name}**")
            try:
                buffer = BytesIO()
                image.save(buffer, format="PNG")
                with st.spinner(f"Đang phát hiện biển trong ảnh {number}…"):
                    input_conf = conf if mode == "Ngưỡng cố định" else 0.001
                    raw = detect_s1_frame(buffer.getvalue(), input_conf)
                    if mode == "So sánh hai chế độ":
                        comparison = compare(
                            tuple(Candidate(0, score, tuple(box)) for score, box in raw),
                            conf,
                            dt_policy,
                        )
                    elif mode == "Dynamic Threshold":
                        filtered = apply_policy(
                            (Candidate(0, score, tuple(box)) for score, box in raw), dt_policy
                        )
                        detections = [
                            detector_s1.SignBox(item.score, item.box) for item in filtered.kept
                        ]
                    else:
                        detections = [
                            detector_s1.SignBox(score, tuple(box)) for score, box in raw
                        ]
            except (OSError, RuntimeError, ValueError, ImportError) as exc:
                st.error(f"Không thể chạy YOLO11s một lớp trên {name}: {exc}")
                continue
            if mode == "So sánh hai chế độ":
                st.caption(
                    "Một lượt YOLO ở ngưỡng ứng viên 0,001, cùng box sau NMS cho cả hai nhánh. "
                    "Nét xanh liền: giữ; nét cam đứt: loại. "
                    "Policy S1 hiện chỉ là ngưỡng demo 0,20, chưa chứng minh cải thiện."
                )
                picked_box = st.selectbox(
                    "Xem quyết định cho box",
                    [None, *range(1, len(comparison.proposals) + 1)],
                    format_func=lambda value: (
                        "Tất cả box" if value is None else f"Box #{value}"
                    ),
                    key=f"s1_compare_box_{number}",
                )
                highlighted = None if picked_box is None else picked_box - 1
                fixed_col, dynamic_col = st.columns(2, gap="medium")
                for col, title, result in (
                    (fixed_col, f"Ngưỡng cố định {conf:.2f}", comparison.fixed),
                    (dynamic_col, "Dynamic Threshold · policy 0,20", comparison.dynamic),
                ):
                    with col:
                        st.image(
                            draw_decisions(image, comparison, result, highlighted),
                            caption=f"{title}: giữ {len(result.kept)}/{len(raw)} box",
                            alt=f"Ảnh {name}, {title}, box giữ màu xanh và box loại nét cam",
                            width="stretch",
                        )
                rows = decision_rows(comparison, ["Biển báo"])
                if picked_box is not None:
                    rows = [rows[highlighted]]
                st.dataframe(
                    rows,
                    hide_index=True,
                    alt="Quyết định giữ hoặc loại box trong hai chế độ YOLO một lớp",
                )
                st.caption(
                    "S1 chỉ xác định vị trí, chưa biết mã biển; ảnh tải lên không có nhãn "
                    "đối chứng. Chưa có đánh giá validation riêng cho policy DT của S1."
                )
                continue
            original, detected = st.columns(2, gap="medium")
            with original:
                st.image(image, caption="Ảnh đầu vào", alt=f"Ảnh gốc {name}", width="stretch")
            with detected:
                st.image(
                    detector_s1.draw_boxes(image, detections),
                    caption=f"{len(detections)} biển tại ngưỡng {conf:.2f}",
                    alt=f"Ảnh {name} với {len(detections)} khung biển do YOLO11s một lớp phát hiện",
                    width="stretch",
                )
            if mode == "Dynamic Threshold":
                st.caption(
                    f"YOLO trả {len(raw)} box ở ngưỡng 0,001; DT giữ {len(detections)}, "
                    f"lọc {len(filtered.below_threshold)} theo điểm và "
                    f"{len(filtered.duplicate_suppressed)} box trùng. NMS chạy trước DT."
                )
            if detections:
                st.dataframe(
                    detector_s1.detection_rows(detections),
                    hide_index=True,
                    alt=f"Vị trí và điểm tin cậy của biển trong {name}",
                )
            else:
                st.info("Không có biển nào trên ngưỡng tin cậy trong ảnh này.")
