from __future__ import annotations

import html
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from typing import Any

import streamlit as st
from PIL import Image, UnidentifiedImageError

from cpv301_autodrive.behavior import VehicleCommand, plan_behavior
from cpv301_autodrive.config import get_settings
from cpv301_autodrive.inference import ModelService, Prediction


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
    st.markdown(
        """
        <div class="pipeline">
          <div><b>1 · Camera</b><span>Ảnh hoặc snapshot</span></div>
          <div><b>2 · Tiền xử lý</b><span>RGB · 32 × 32 · /255</span></div>
          <div><b>3 · CNN</b><span>43 lớp GTSRB</span></div>
          <div><b>4 · Hành vi</b><span>Luật mô phỏng xe</span></div>
        </div>
        """,
        unsafe_allow_html=True,
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


def render_app() -> None:
    st.set_page_config(
        page_title="CPV301 AutoDrive",
        page_icon="🚦",
        layout="wide",
        initial_sidebar_state="expanded",
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
        .pipeline { display: grid; grid-template-columns: repeat(4, 1fr); gap: .75rem;
                    margin: 1.2rem 0 1.6rem; }
        .pipeline div { background: white; border: 1px solid #d9e4df; border-radius: 14px;
                        padding: .8rem 1rem; box-shadow: 0 8px 24px rgba(16,44,42,.05); }
        .pipeline b, .pipeline span { display: block; }
        .pipeline span { color: #63736d; font-size: .82rem; margin-top: .25rem; }
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
          <p>Mô phỏng luồng camera → nhận diện biển báo → quyết định hành vi xe bằng
             mô hình CNN 43 lớp đã huấn luyện trên GTSRB.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    render_pipeline()
    st.warning(
        "Baseline nghiên cứu: model chỉ được đo trên ảnh crop GTSRB của Đức và chưa được "
        "kiểm chứng với biển báo/camera giao thông Việt Nam. Không dùng lệnh mô phỏng này "
        "để điều khiển phương tiện thật."
    )

    settings = get_settings()
    with st.sidebar:
        st.header("Thiết lập mô phỏng")
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
