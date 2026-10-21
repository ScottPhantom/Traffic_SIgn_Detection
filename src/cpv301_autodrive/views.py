"""Reusable Streamlit views of the CPV301 presentation app.

Moved out of `web_app.py` (2026-10-21, presentation redesign phase 1) so that each slide page can
reuse them. `web_app.py` is now only the navigation shell.
"""

from __future__ import annotations

import html
from collections import Counter
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from typing import Any

import altair as alt
import streamlit as st
from PIL import Image, UnidentifiedImageError

from cpv301_autodrive import dataset01_view, palette
from cpv301_autodrive.behavior import VehicleCommand, plan_behavior
from cpv301_autodrive.config import get_settings
from cpv301_autodrive.inference import ModelService, Prediction
from cpv301_autodrive.project_status import (
    CURRENT_PHASE,
    DECISIONS,
    GATE0,
    MILESTONES,
    PIPELINE,
    REVIEW_PROGRESS,
    STATUS_AS_OF,
    TRAINING_STATUS,
)


@st.cache_resource(show_spinner=False)
def get_model_service(model_path: str) -> ModelService:
    """Cache the heavy TensorFlow model across Streamlit reruns."""

    return ModelService(Path(model_path), confidence_threshold=0.0)


def read_uploaded_image(uploaded_file: Any) -> Image.Image:
    """Read an uploaded or camera file and detach it from Streamlit's buffer."""

    return Image.open(BytesIO(uploaded_file.getvalue())).convert("RGB")


def predict_frame(image: Image.Image, threshold: float, cruise_speed: int) -> dict[str, Any]:
    settings = get_settings()
    raw_prediction = get_model_service(str(settings.model_path)).predict(image)
    prediction = replace(
        raw_prediction,
        accepted=raw_prediction.confidence >= threshold,
    )
    command = plan_behavior(prediction, cruise_speed)
    return {
        "prediction": prediction,
        "command": command,
    }


def render_pipeline() -> None:
    """Five pipeline stages as native cards (overview slide)."""
    from cpv301_autodrive.project_status import PIPELINE_STAGES, STAGE_STATE_LABEL

    details = {stage: detail for stage, detail, _ in PIPELINE}
    with st.container(horizontal=True):
        for index, stage in enumerate(PIPELINE_STAGES, start=1):
            label, color = STAGE_STATE_LABEL[stage.state]
            with st.container(border=True, width=210):
                st.markdown(f"**{index} · {stage.icon} {stage.name}**")
                st.caption(details[stage.name])
                st.badge(label, color=color)


def render_project_status() -> None:
    st.subheader("Hướng đi hiện tại")
    st.markdown(
        f"Dự án đang ở **{CURRENT_PHASE}**. DATASET01 (biển báo Việt Nam, 3.216 ảnh, 54 lớp "
        "train) đã có license, nhóm, taxonomy, quyết định lớp hiếm, split train/val/test với "
        "test niêm phong và dataset card. Ngưỡng D-05 đã duyệt nên Gate 0 đã mở. Bước kế tiếp "
        "theo ưu tiên của chủ dự án: gói train M1 rồi **detector biển báo VN trên ảnh toàn "
        "cảnh** (M4); prototype làm sau. Model E0 (CNN 43 lớp GTSRB) chỉ là baseline tham chiếu."
    )
    passed = sum(1 for _, _, status in GATE0 if status == "PASS")
    review = REVIEW_PROGRESS
    with st.container(horizontal=True):
        st.metric("Gate 0", f"{passed}/{len(GATE0)} PASS", border=True)
        st.metric("Huấn luyện", TRAINING_STATUS, border=True)
        st.metric(
            "Cạnh đã review (D-02)",
            f"{review['edges_reviewed']:,}/{review['edges_total']:,}".replace(",", "."),
            border=True,
        )
        st.metric("Cạnh còn chờ review", review["edges_pending"], border=True)
    awaiting = review["awaiting_qa"]
    qa_note = (
        f"{' và '.join(awaiting)} đang chờ QA độc lập; "
        if awaiting
        else "Mọi batch review cạnh đã qua QA độc lập; "
    )
    st.caption(
        f"Số liệu theo docs/product_roadmap.md, cập nhật {STATUS_AS_OF}. {qa_note}"
        f"{review['edges_quarantined']} cạnh chạm stem 0248 bị cách ly."
    )

    st.markdown("**Gate 0 — hợp đồng dữ liệu**")
    st.dataframe(
        [{"Mã": code, "Trạng thái": status, "Tiêu chí": text} for code, text, status in GATE0],
        hide_index=True,
        alt="Bảng tiêu chí Gate 0 và trạng thái",
    )
    st.markdown("**Quyết định cần chủ dự án duyệt**")
    st.dataframe(
        [{"Mã": code, "Chủ đề": topic, "Cần gì": need} for code, topic, need in DECISIONS],
        hide_index=True,
        alt="Bảng quyết định D-01 đến D-05",
    )
    st.markdown("**Milestone**")
    st.dataframe(
        [
            {"Mốc": code, "Trạng thái": status, "Phạm vi": scope}
            for code, scope, status in MILESTONES
        ],
        hide_index=True,
        alt="Bảng milestone M0 đến M6",
    )


def render_road(command: VehicleCommand, prediction: Prediction) -> None:
    steering_icons = {
        "left": "↙",
        "right": "↘",
        "straight": "↑",
        "stop": "■",
    }
    label = html.escape(prediction.label)
    reason = html.escape(command.reason)
    steering = steering_icons.get(command.steering, "↑")
    st.markdown(ROAD_STYLES, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="road">
          <div class="road-line"></div>
          <div class="detected-sign">{label}</div>
          <div class="car">🚙<span>{steering}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(horizontal=True):
        st.metric("Tốc độ mục tiêu", f"{command.target_speed_kmh} km/h", border=True)
        st.metric("Điều khiển", command.action, border=True)
        st.metric("Góc lái", command.steering, border=True)
    st.caption(reason)


def render_result(image: Image.Image, result: dict[str, Any], frame_name: str) -> None:
    prediction: Prediction = result["prediction"]
    command: VehicleCommand = result["command"]
    camera_col, result_col = st.columns([1.1, 0.9], gap="large")
    with camera_col:
        st.image(image, caption=f"Camera frame · {frame_name}", width="stretch")
    with result_col:
        status = "Đã chấp nhận" if prediction.accepted else "Chưa chấp nhận"
        st.metric("Biển báo nhận diện", prediction.label)
        st.metric("Độ tin cậy", f"{prediction.confidence:.2%}")
        if prediction.accepted:
            st.success(status)
        else:
            st.warning(f"{status} — đây chưa phải kết luận UNKNOWN/OOD đã kiểm chứng.")
    render_road(command, prediction)


def render_history() -> None:
    history = st.session_state.get("history", [])
    if not history:
        return
    st.subheader("Nhật ký hành trình mô phỏng")
    st.dataframe(history, width="stretch", hide_index=True)


@st.cache_data(show_spinner="Đang dựng đồ thị DATASET01...", ttl=600, max_entries=1)
def load_dataset01_graph_html() -> str:
    """Graph with vendor splits and D-02 groups, rebuilt at most once per 10 minutes."""
    return dataset01_view.render_graph_html()


@st.cache_data(show_spinner="Đang chuẩn bị hoạt hình...", ttl=600, max_entries=1)
def load_dataset01_pipeline_html() -> str:
    return dataset01_view.render_pipeline_html()


@st.cache_data(ttl=600, max_entries=1)
def load_dataset01_tables() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return dataset01_view.class_rows(), dataset01_view.group_rows()


def render_dataset01() -> None:
    st.subheader("DATASET01 — biển báo Việt Nam")
    st.caption(
        "3.216 khung hình đường phố, 52 lớp gốc. Mọi số liệu đọc trực tiếp từ các gói review "
        "trong repo (WP5–WP37-R1, D-01–D-04, split WP36-R1). Gate 0 đã mở (D-05 "
        "duyệt 2026-10-18); chưa có model VN nào được train."
    )
    view = st.segmented_control(
        "Phần",
        [
            ":material/movie: Quy trình",
            ":material/hub: Đồ thị",
            ":material/category: Lớp",
            ":material/workspaces: Nhóm",
        ],
        default=":material/movie: Quy trình",
        key="dataset01_view",
        label_visibility="collapsed",
    )
    try:
        if view == ":material/movie: Quy trình":
            st.iframe(
                load_dataset01_pipeline_html(),
                height="content",
                alt="Hoạt hình quá trình xử lý DATASET01",
            )
        elif view == ":material/hub: Đồ thị":
            st.caption(
                "Mỗi ô là một ảnh theo thứ tự stem; vạch nối là cạnh proxy WP5 tô theo kết "
                "quả review. Chọn **Nhóm D-02** để tô màu theo 54 nhóm group_id owner đã duyệt."
            )
            st.iframe(
                load_dataset01_graph_html(), height="content", alt="Đồ thị nhóm ảnh DATASET01"
            )
        elif view == ":material/category: Lớp":
            render_dataset01_classes()
        elif view == ":material/workspaces: Nhóm":
            render_dataset01_groups()
    except (OSError, KeyError, ValueError) as exc:
        st.error(f"Không đọc được dữ liệu DATASET01 trong repo: {exc}")


def render_dataset01_classes() -> None:
    classes, _groups = load_dataset01_tables()
    counts = Counter(row["Nhóm D-04"] for row in classes)
    with st.container(horizontal=True):
        for label, _bucket in ((label, b) for b, label in dataset01_view.BUCKETS):
            st.metric(label, counts[label], border=True)
    st.caption(
        "Nhóm D-04 dựa trên số nhóm D-02 độc lập chứa lớp đó. 12 lớp ít ảnh nhất được owner duyệt "
        "train kèm làm giàu dữ liệu (WP35); các lớp khác vẫn là đề xuất, chờ WP34-R1."
    )
    # Same colours as the pipeline animation; altair keeps the legend in bucket order.
    palette = {
        "KEEP_FULL": "#1e8a4a",
        "KEEP_TRAIN_AND_TEST_NO_VAL": "#2f6fd0",
        "KEEP_TRAIN_ONLY_UNVERIFIED": "#d98a00",
        "DROP_FROM_V1_COLLECT_MORE": "#d0342c",
    }
    labels = dict(dataset01_view.BUCKETS)
    chart = (
        alt.Chart(
            alt.Data(
                values=[
                    {
                        "Lớp": f"{row['Mã QCVN']} ({row['Lớp']})",
                        "Ảnh": row["Ảnh"],
                        "Nhóm D-04": row["Nhóm D-04"],
                    }
                    for row in classes
                ]
            )
        )
        .mark_bar()
        .encode(
            x=alt.X("Lớp:N", sort="-y", title=None),
            y=alt.Y("Ảnh:Q"),
            color=alt.Color(
                "Nhóm D-04:N",
                scale=alt.Scale(domain=[labels[k] for k in palette], range=list(palette.values())),
                legend=alt.Legend(orient="bottom", columns=2),
            ),
            tooltip=["Lớp:N", "Ảnh:Q", "Nhóm D-04:N"],
        )
    )
    st.altair_chart(chart, height=380, alt="Số ảnh mỗi lớp, tô theo nhóm D-04")
    st.dataframe(
        [{k: v for k, v in row.items() if k != "bucket"} for row in classes],
        hide_index=True,
        column_config={
            "Ảnh": st.column_config.ProgressColumn(
                "Ảnh", min_value=0, max_value=max(r["Ảnh"] for r in classes), format="%d"
            ),
            "Nhóm D-02": st.column_config.NumberColumn(
                "Nhóm D-02", help="Số nhóm group_id độc lập chứa lớp"
            ),
            "Ảnh làm giàu": st.column_config.NumberColumn(
                "Ảnh làm giàu", help="Ảnh train tạo bởi WP35"
            ),
        },
        alt="Bảng 54 lớp WP33 với số ảnh, số nhóm và nhóm D-04",
    )


def render_dataset01_groups() -> None:
    _classes, groups = load_dataset01_tables()
    sizes = sorted((row["Ảnh"] for row in groups), reverse=True)
    with st.container(horizontal=True):
        st.metric("Nhóm group_id", len(groups), border=True)
        st.metric("Nhóm lớn nhất", f"{sizes[0]} ảnh", border=True)
        st.metric(
            "Bị split gốc chia chéo",
            f"{sum(r['Chéo split gốc'] for r in groups)}/{len(groups)}",
            border=True,
        )
    st.caption(
        "Nhóm = các khung hình cùng một lần chụp (D02-P1, owner duyệt 2026-10-17). Khi chia "
        "train/val/test, cả nhóm phải nằm trọn trong một tập; split gốc của nhà cung cấp vi phạm "
        "điều này ở mọi nhóm."
    )
    st.bar_chart(
        [
            {
                "Nhóm": r["Nhóm"],
                "Train (gốc)": r["Train"],
                "Test (gốc)": r["Test"],
                "Chưa xếp": r["Unassigned"],
            }
            for r in groups
        ],
        x="Nhóm",
        y=["Train (gốc)", "Test (gốc)", "Chưa xếp"],
        color=["#1f5fbf", "#d99a00", "#9aa4b2"],
        height=320,
        alt="Số ảnh mỗi nhóm D-02 theo split gốc",
    )
    st.dataframe(
        groups, hide_index=True, alt="Bảng 54 nhóm D-02 với số ảnh, split gốc và biển chính"
    )


def render_simulator() -> None:
    settings = get_settings()
    with st.sidebar:
        st.header("Thiết lập mô phỏng E0")
        source = st.radio("Nguồn camera", ["Tải ảnh", "Camera webcam"])
        threshold = st.slider(
            "Ngưỡng chấp nhận demo",
            min_value=0.0,
            max_value=1.0,
            value=float(settings.confidence_threshold),
            step=0.05,
        )
        cruise_speed = st.slider("Tốc độ hành trình", 10, 80, 30, 5)
        st.divider()
        if settings.model_path.is_file():
            st.success("Model artifact: sẵn sàng")
        else:
            st.error(f"Không tìm thấy model: {settings.model_path}")
        st.caption(
            "MVP hiện phân loại ảnh biển báo đã crop. Detection biển trong toàn cảnh "
            "và điều khiển xe thật chưa thuộc milestone này."
        )

    frames: list[tuple[str, Image.Image]] = []
    try:
        if source == "Tải ảnh":
            uploads = st.file_uploader(
                "Chọn một hoặc nhiều camera frame",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                help="Bản MVP cho kết quả tốt nhất khi mỗi ảnh chứa một biển báo đã crop.",
            )
            frames = [(item.name, read_uploaded_image(item)) for item in uploads]
        else:
            camera_file = st.camera_input("Chụp một camera frame")
            if camera_file is not None:
                frames = [("webcam-frame.jpg", read_uploaded_image(camera_file))]
    except (UnidentifiedImageError, OSError) as exc:
        st.error(f"Không thể đọc ảnh: {exc}")

    if not frames:
        st.info("Hãy tải ảnh biển báo hoặc chụp một frame để bắt đầu mô phỏng.")
        render_history()
        return

    selected_index = 0
    if len(frames) > 1:
        selected_index = st.slider("Camera frame đang xem", 1, len(frames), 1) - 1

    analyze_one, analyze_all, clear = st.columns([1, 1, 1])
    if analyze_one.button("Phân tích frame này", type="primary", width="stretch"):
        name, image = frames[selected_index]
        with st.spinner("Đang nạp model và nhận diện..."):
            result = predict_frame(image, threshold, cruise_speed)
        st.session_state["current_result"] = (name, image, result)

    if analyze_all.button(
        "Chạy toàn bộ hành trình",
        disabled=len(frames) < 2,
        width="stretch",
    ):
        history: list[dict[str, Any]] = []
        last_result: dict[str, Any] | None = None
        progress = st.progress(0, text="Đang xử lý camera frames...")
        for index, (name, image) in enumerate(frames, start=1):
            result = predict_frame(image, threshold, cruise_speed)
            last_result = result
            prediction: Prediction = result["prediction"]
            command: VehicleCommand = result["command"]
            history.append(
                {
                    "Frame": index,
                    "Tên": name,
                    "Biển báo": prediction.label,
                    "Tin cậy": f"{prediction.confidence:.2%}",
                    "Chấp nhận": prediction.accepted,
                    "Hành vi": command.action,
                    "Tốc độ km/h": command.target_speed_kmh,
                }
            )
            progress.progress(index / len(frames), text=f"Đã xử lý {index}/{len(frames)}")
        st.session_state["history"] = history
        last_name, last_image = frames[-1]
        if last_result is not None:
            st.session_state["current_result"] = (last_name, last_image, last_result)
        progress.empty()

    if clear.button("Xóa kết quả", width="stretch"):
        st.session_state.pop("current_result", None)
        st.session_state.pop("history", None)

    current = st.session_state.get("current_result")
    if current is not None:
        render_result(current[1], current[2], current[0])
    else:
        st.image(
            frames[selected_index][1],
            caption=f"Camera preview · {frames[selected_index][0]}",
            width="stretch",
        )
    render_history()


# The only custom HTML left: the simulated road drawing on the Demo slide.
ROAD_STYLES = """
<style>
.road { height: 150px; position: relative; overflow: hidden; border-radius: 12px; margin-top: .5rem;
        background: linear-gradient(90deg, #7d9a74 0 16%, #4b5152 16% 84%, #7d9a74 84%); }
.road-line { position: absolute; height: 100%; left: 50%; border-left: 5px dashed #f8e282; }
.car { position: absolute; bottom: 14px; left: calc(50% - 34px); font-size: 2.8rem; }
.car span { color: white; font-size: 1.3rem; margin-left: .3rem; }
.detected-sign { position: absolute; top: 14px; right: 5%; background: #fff; color: #0f172a;
                 border: 4px solid #c2410c; border-radius: 10px; padding: .4rem .65rem;
                 font-weight: 700; max-width: 60%; }
</style>
"""


def render_hero() -> None:
    """Project title card of the overview slide: pitch, status badges, calls to action, key figures.

    Native elements only (no custom CSS).
    """
    from cpv301_autodrive.presentation import SLIDES, go_to

    passed = sum(1 for _, _, status in GATE0 if status == "PASS")
    with st.container(border=True, gap="medium"):
        st.markdown(
            f":blue-badge[:material/traffic: CPV301 AutoDrive] "
            f":green-badge[:material/check: Gate 0 {passed}/{len(GATE0)}] "
            ":orange-badge[:material/model_training: Detector đang train] "
            ":gray-badge[Chỉ mô phỏng]"
        )
        st.header("Nhận diện biển báo Việt Nam trên ảnh toàn cảnh", anchor=False)
        st.markdown(
            ":gray[Từ khung hình camera đến hành vi xe mô phỏng: detector YOLO cho **54 lớp** "
            "biển theo QCVN 41:2024, dữ liệu chia theo nhóm và test niêm phong.]"
        )
        with st.container(horizontal=True):
            if st.button(
                "Xem pipeline", icon=":material/account_tree:", type="primary", key="hero_pipeline"
            ):
                go_to(SLIDES[2])
            if st.button("Thử demo", icon=":material/directions_car:", key="hero_demo"):
                go_to(SLIDES[6])
        with st.container(horizontal=True):
            st.metric("Khung hình DATASET01", "3.216", border=True)
            st.metric("Lớp biển báo train", "54", border=True)
            st.metric("Gate 0", f"{passed}/{len(GATE0)} PASS", border=True)
            st.metric("Huấn luyện", TRAINING_STATUS, border=True)


def pipeline_dot(selected: str, vertical: bool = False) -> str:
    """Graphviz DOT of the target pipeline plus the current E0 demo path (dashed)."""
    from cpv301_autodrive.project_status import PIPELINE_STAGES, STAGE_STATE_LABEL

    colors = palette.current()
    font = 'fontname="Be Vietnam Pro,Helvetica"'
    lines = [
        "digraph pipeline {",
        f"  rankdir={'TB' if vertical else 'LR'};",
        '  bgcolor="transparent"; nodesep=0.35; ranksep=0.55;',
        f'  node [shape=box, style="rounded,filled", {font}, fontsize=12,'
        f' fontcolor="{colors.stage_ink}", color="{colors.border}", penwidth=1.2,'
        ' margin="0.22,0.14"];',
        f'  edge [color="{colors.muted}", fontcolor="{colors.muted}", {font}, fontsize=10];',
    ]
    for stage in PIPELINE_STAGES:
        status = STAGE_STATE_LABEL[stage.state][0]
        border = f'color="{colors.accent}", penwidth=3' if stage.name == selected else ""
        lines.append(
            f'  "{stage.name}" [label="{stage.name}\\n{status}", '
            f'fillcolor="{colors.stage_fills[stage.state]}" {("," + border) if border else ""}];'
        )
    lines += [
        '  "Camera" -> "Detector" [label="khung hình"];',
        '  "Detector" -> "Temporal voting" [label="khung + lớp"];',
        '  "Temporal voting" -> "Hành vi" [label="sự kiện"];',
        '  "Detector" -> "Classifier" [style=dotted, label="crop (tùy chọn)"];',
        '  "Camera" -> "Classifier" [style=dashed, label="demo E0: ảnh crop"];',
        '  "Classifier" -> "Hành vi" [style=dashed, label="demo E0"];',
        "}",
    ]
    return "\n".join(lines)


def is_phone() -> bool:
    """True for phone browsers (user agent), used to lay the pipeline diagram out vertically."""
    agent = st.context.headers.get("User-Agent", "")
    return "Mobile" in agent or "Android" in agent or "iPhone" in agent


def render_pipeline_explorer() -> None:
    from cpv301_autodrive.project_status import PIPELINE_STAGES, STAGE_STATE_LABEL

    stages = {stage.name: stage for stage in PIPELINE_STAGES}
    choice = st.segmented_control(
        "Chọn một bước để xem chi tiết",
        list(stages),
        default="Detector",
        required=True,
        key="pipeline_stage",
        bind="query-params",
    )
    stage = stages[choice]
    st.graphviz_chart(
        pipeline_dot(stage.name, vertical=is_phone()),
        width="stretch",
        alt="Sơ đồ pipeline: camera, detector, classifier, temporal voting, hành vi",
    )
    st.caption(
        "Nét liền: pipeline mục tiêu. Nét chấm: crop sang classifier (tùy chọn, sau detector). "
        "Nét đứt xám: đường đi của demo E0 hiện tại."
    )

    label, color = STAGE_STATE_LABEL[stage.state]
    with st.container(border=True):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.markdown(f"### {stage.icon} {stage.name}")
            st.badge(label, color=color)
        inputs, outputs, method = st.columns(3, gap="medium")
        with inputs:
            st.markdown("**:material/input: Đầu vào**")
            st.markdown("\n".join(f"- {item}" for item in stage.inputs))
        with outputs:
            st.markdown("**:material/output: Đầu ra**")
            st.markdown("\n".join(f"- {item}" for item in stage.outputs))
        with method:
            st.markdown("**:material/memory: Model / phương pháp**")
            st.markdown("\n".join(f"- {item}" for item in stage.method))
        with st.container(horizontal=True):
            for name, value, note in stage.numbers:
                st.metric(name, value, help=note, border=True)
        st.caption("Nguồn: " + " · ".join(f"`{path}`" for path in stage.evidence))


def render_data_overview() -> None:
    from cpv301_autodrive.project_status import SPLIT_FRAMES

    with st.container(horizontal=True):
        st.metric("Khung hình gốc", "3.216", border=True)
        st.metric(
            "Dùng được",
            "3.191",
            help="Bỏ stem 0248 và 24 ảnh âm có biển chưa gán nhãn",
            border=True,
        )
        st.metric("Lớp biển báo", "54", help="Nhãn dẫn xuất WP33 theo QCVN 41:2024", border=True)
        st.metric(
            "Nhóm capture", "54", help="D-02: khung hình cùng chuyến đi được gom nhóm", border=True
        )
        st.metric("Box train-eligible", "8.290", border=True)
        st.metric(
            "Ảnh làm giàu WP35", "1.800", help="Biến đổi ảnh thật, chỉ dùng cho train", border=True
        )

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown("**Chia dữ liệu theo nhóm (WP36-R1)**")
        data = [{"Split": name, "Ảnh": count} for name, count in SPLIT_FRAMES]
        base = alt.Chart(alt.Data(values=data)).encode(
            y=alt.Y("Split:N", sort=None, title=None, axis=alt.Axis(labelLimit=320)),
            x=alt.X("Ảnh:Q", title="Số khung hình dùng được"),
            tooltip=["Split:N", "Ảnh:Q"],
        )
        colors = palette.current()
        bars = base.mark_bar(color=colors.data, cornerRadiusEnd=6, height=26)
        labels = base.mark_text(align="left", dx=6, color=colors.ink).encode(text="Ảnh:Q")
        st.altair_chart((bars + labels).properties(height=alt.Step(40)), width="stretch")
    with right:
        st.markdown("**Vì sao chia theo nhóm?**")
        st.markdown(
            "Khung hình liền nhau trong cùng chuyến đi gần như giống hệt. Nếu chia ngẫu nhiên, "
            "test sẽ chứa bản sao của ảnh train và điểm số bị thổi phồng. Mỗi nhóm D-02 chỉ "
            "nằm trong **một** split, và test được niêm phong bằng SHA-256."
        )


def render_governance_timeline() -> None:
    from cpv301_autodrive.project_status import GATE0, GOVERNANCE_TIMELINE

    passed = sum(1 for _, _, status in GATE0 if status == "PASS")
    st.progress(
        passed / len(GATE0),
        text=f"Gate 0: {passed}/{len(GATE0)} tiêu chí PASS · "
        "D-05 đã duyệt → được phép train detector",
    )
    dates: dict[str, list[tuple[str, tuple[str, ...]]]] = {}
    for date, event, codes in GOVERNANCE_TIMELINE:
        dates.setdefault(date, []).append((event, codes))
    columns = st.columns(len(dates), gap="small")
    for column, (date, events) in zip(columns, dates.items(), strict=True):
        with column, st.container(border=True, height="stretch"):
            day, month = date[8:10], date[5:7]
            st.markdown(f"#### :material/event: {day}/{month}")
            for event, codes in events:
                badges = " ".join(
                    f":green-badge[{code}]" if code.startswith("G0") else f":blue-badge[{code}]"
                    for code in codes
                )
                st.markdown(f"{badges}  \n{event}")
    st.caption(
        ":green-badge[G0.x] tiêu chí Gate 0 · :blue-badge[D-0x] quyết định của chủ dự án. "
        "Mỗi quyết định được ghi append-only và kiểm tra bởi QA độc lập."
    )

    st.markdown("**Chín tiêu chí Gate 0**")
    with st.container(horizontal=True):
        for code, text, status in GATE0:
            with st.container(border=True, width=260):
                st.markdown(
                    f":green-badge[{status}] **{code}**"
                    if status == "PASS"
                    else f":orange-badge[{status}] **{code}**"
                )
                st.caption(text)


def render_d05_gates() -> None:
    gates = (
        ("mAP50", "≥ 0,60", "Độ chính xác trung bình, IoU 0,5"),
        ("mAP50-95", "≥ 0,40", "Độ chính xác trên nhiều mức IoU"),
        ("Recall phát hiện", "≥ 0,85", "Tỉ lệ biển được tìm thấy, bỏ qua lớp"),
        ("False positive / ảnh", "≤ 0,30", "Báo nhầm có biển"),
        ("Recall lớp quan trọng", "≥ 0,70", "10 lớp, mỗi lớp có ≥ 20 box test"),
        ("Recall các lớp khác", "≥ 0,50", "Lớp có ≥ 20 box test"),
        ("Latency p95", "≤ 100 ms", "M1 Pro, batch 1"),
    )
    with st.container(horizontal=True):
        for name, value, note in gates:
            st.metric(name, value, help=note, border=True)
    st.caption(
        "Đo trên test niêm phong, trung bình 3 seed; khoảng tin cậy 95 % bằng bootstrap "
        "theo nhóm D-02. Val chỉ dùng để chọn model và ngưỡng."
    )


def render_speed_chart() -> None:
    from cpv301_autodrive.project_status import LATENCY_MEASURED_MS

    data = [
        {"Pipeline": name, "ms": ms, "FPS": round(1000 / ms)} for name, ms in LATENCY_MEASURED_MS
    ]
    base = alt.Chart(alt.Data(values=data)).encode(
        y=alt.Y("Pipeline:N", sort=None, title=None, axis=alt.Axis(labelLimit=320)),
        x=alt.X("ms:Q", title="Thời gian mỗi khung hình (ms)", scale=alt.Scale(domain=[0, 130])),
        tooltip=["Pipeline:N", alt.Tooltip("ms:Q", format=".1f"), "FPS:Q"],
    )
    colors = palette.current()
    bars = base.mark_bar(color=colors.data, cornerRadiusEnd=6, height=22)
    labels = (
        base.mark_text(align="left", dx=6, color=colors.ink)
        .encode(text=alt.Text("label:N"))
        .transform_calculate(label="format(datum.ms, '.0f') + ' ms · ' + datum.FPS + ' FPS'")
    )
    gate = (
        alt.Chart(alt.Data(values=[{"ms": 100}]))
        .mark_rule(color=colors.accent, strokeDash=[5, 4], strokeWidth=2)
        .encode(x="ms:Q")
    )
    gate_label = (
        alt.Chart(alt.Data(values=[{"ms": 100, "t": "Gate D-05: 100 ms"}]))
        .mark_text(color=colors.accent, align="right", dx=-4, dy=-6, baseline="bottom")
        .encode(x="ms:Q", y=alt.value(0), text="t:N")
    )
    st.altair_chart(
        (bars + labels + gate + gate_label).properties(height=alt.Step(38)), width="stretch"
    )
    st.caption(
        "Đo trên M1 Pro (MPS, ảnh 1280 px, batch 1) với trọng số ngẫu nhiên, khung hình "
        "có 3 biển; chưa tính tiền xử lý. Pipeline hai bước chậm thêm khi có nhiều biển."
    )


def render_train_time_chart() -> None:
    from cpv301_autodrive.project_status import TRAIN_HOURS_YOLO11N

    data = [
        {
            "Nơi train": where,
            "low": low,
            "high": high,
            "Loại": "Đo thật" if measured else "Ước tính",
            "label": f"{low:g} giờ" if low == high else f"{low:g}–{high:g} giờ",
        }
        for where, low, high, measured in TRAIN_HOURS_YOLO11N
    ]
    base = alt.Chart(alt.Data(values=data)).encode(
        y=alt.Y("Nơi train:N", sort=None, title=None, axis=alt.Axis(labelLimit=320)),
        tooltip=["Nơi train:N", "label:N", "Loại:N"],
    )
    colors = palette.current()
    bars = base.mark_bar(color=colors.data, cornerRadiusEnd=6, height=22).encode(
        x=alt.X("high:Q", title="Giờ cho 100 epoch YOLO11n (1280 px)"),
        opacity=alt.Opacity(
            "Loại:N",
            scale=alt.Scale(domain=["Đo thật", "Ước tính"], range=[1.0, 0.45]),
            legend=alt.Legend(title=None, orient="bottom"),
        ),
    )
    labels = base.mark_text(align="left", dx=6, color=colors.ink).encode(
        x="high:Q", text="label:N"
    )
    st.altair_chart((bars + labels).properties(height=alt.Step(38)), width="stretch")
    st.caption(
        "M1 Pro: đo 5,2 ảnh/giây (batch 4). Colab: ước tính theo thông lượng điển hình của "
        "GPU, chưa đo trên dữ liệu này. Theo D-05 cần 4 lần train (pilot + 3 seed)."
    )
