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

from cpv301_autodrive import dataset01_view
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
    cards = "".join(
        f"<div><b>{index} · {html.escape(stage)}</b><span>{html.escape(detail)}</span>"
        f"<em>{html.escape(status)}</em></div>"
        for index, (stage, detail, status) in enumerate(PIPELINE, start=1)
    )
    st.markdown(f'<div class="pipeline">{cards}</div>', unsafe_allow_html=True)


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
    st.markdown(
        f"""
        <div class="road-card">
          <div class="road">
            <div class="road-line"></div>
            <div class="detected-sign">{label}</div>
            <div class="car">🚙<span>{steering}</span></div>
          </div>
          <div class="telemetry">
            <div><small>Tốc độ mục tiêu</small>
              <strong>{command.target_speed_kmh} km/h</strong>
            </div>
            <div><small>Điều khiển</small><strong>{html.escape(command.action)}</strong></div>
            <div><small>Góc lái</small><strong>{html.escape(command.steering)}</strong></div>
          </div>
          <p class="reason">{reason}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def render_app() -> None:
    st.set_page_config(
        page_title="CPV301 AutoDrive",
        page_icon="🚦",
        layout="wide",
        initial_sidebar_state="auto",
    )
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(145deg, #f7f8f4 0%, #edf2ef 100%); }
        .block-container { max-width: 1180px; padding-top: 2rem; }
        .hero { padding: 1.5rem 1.7rem; border-radius: 22px; color: white;
                background: linear-gradient(125deg, #102c2a, #176153 62%, #d9782d); }
        .hero h1 { margin: 0; font-size: 2.4rem; }
        .hero p { margin: .5rem 0 0; color: #e8f5ef; max-width: 760px; }
        .pipeline { display: grid; grid-template-columns: repeat(5, 1fr); gap: .75rem;
                    margin: 1.2rem 0 1.6rem; }
        .pipeline div { background: white; border: 1px solid #d9e4df; border-radius: 14px;
                        padding: .8rem 1rem; box-shadow: 0 8px 24px rgba(16,44,42,.05); }
        .pipeline b, .pipeline span { display: block; }
        .pipeline span { color: #63736d; font-size: .82rem; margin-top: .25rem; }
        .pipeline em { display: inline-block; margin-top: .45rem; font-style: normal;
                       font-size: .72rem; font-weight: 600; color: #176153;
                       background: #e3efe9; border-radius: 999px; padding: .1rem .5rem; }
        .road-card { background: #fff; border: 1px solid #d9e4df; border-radius: 18px;
                     padding: 1rem; margin-top: 1rem; }
        .road { height: 150px; position: relative; overflow: hidden; border-radius: 12px;
                background: linear-gradient(90deg, #7d9a74 0 16%, #4b5152 16% 84%, #7d9a74 84%); }
        .road-line { position: absolute; height: 100%; left: 50%; border-left: 5px dashed #f8e282; }
        .car { position: absolute; bottom: 14px; left: calc(50% - 34px); font-size: 2.8rem; }
        .car span { color: white; font-size: 1.3rem; margin-left: .3rem; }
        .detected-sign { position: absolute; top: 14px; right: 5%; background: #fff;
                         border: 4px solid #d34b3f; border-radius: 10px; padding: .4rem .65rem;
                         font-weight: 700; max-width: 230px; color: #172724; }
        .telemetry { display: grid; grid-template-columns: repeat(3, 1fr);
                     gap: .7rem; margin-top: .8rem; }
        .telemetry div { background: #f2f6f3; border-radius: 10px; padding: .7rem; }
        .telemetry small, .telemetry strong { display: block; }
        .telemetry small { color: #63736d; }
        .reason { margin: .8rem .2rem .1rem; color: #43534e; }
        @media (max-width: 800px) {
          .pipeline, .telemetry { grid-template-columns: 1fr 1fr; }
        }
        </style>
        <section class="hero">
          <h1>CPV301 AutoDrive</h1>
          <p>Nhận diện biển báo giao thông Việt Nam cho mô phỏng xe tự hành. Giai đoạn hiện tại:
             Gate 0 đã mở (dữ liệu DATASET01 đạt 9/9, ngưỡng D-05 đã duyệt); đang chuẩn bị
             train detector biển báo VN; mô phỏng bên dưới vẫn dùng baseline CNN GTSRB (E0) làm
             tham chiếu.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    render_pipeline()
    st.warning(
        "Gate 0 đã mở nhưng chưa có model Việt Nam nào được train. Model hiện tại chỉ được "
        "đo trên ảnh crop GTSRB của Đức. Không dùng lệnh mô phỏng để điều khiển phương tiện "
        "thật."
    )

    status_tab, graph_tab, simulator_tab = st.tabs(
        [
            ":material/flag: Tiến độ dự án",
            ":material/hub: DATASET01",
            ":material/directions_car: Mô phỏng (baseline E0)",
        ],
        key="main_view",
        on_change="rerun",
    )
    with status_tab:
        if status_tab.open:
            render_project_status()
    with graph_tab:
        if graph_tab.open:
            render_dataset01()
    with simulator_tab:
        if simulator_tab.open:
            render_simulator()


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


if __name__ == "__main__":
    render_app()
