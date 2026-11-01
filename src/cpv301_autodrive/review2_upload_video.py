"""Local-only, bounded MP4 upload preview for the Review 2 front-camera demo.

This path samples a clip at about five frames per second. It is a visual
simulation, not a validated video test or a temporal sign-recognition system.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import cv2
import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

from cpv301_autodrive.centercam import center_cam, side_of
from cpv301_autodrive.detector_d1 import (
    CLASS_MAP_SHA256,
    DEFAULT_CONF,
    WEIGHTS_SHA256,
    D1Detector,
    draw_detections,
    load_classes,
)
from cpv301_autodrive.review2_behavior import POLICY_NAME, explain_events
from cpv301_autodrive.review2_cascade import (
    CLASSIFIER_SHA256 as CASCADE_CLASSIFIER_SHA256,
)
from cpv301_autodrive.review2_cascade import (
    DETECTOR_SHA256 as CASCADE_DETECTOR_SHA256,
)
from cpv301_autodrive.review2_cascade import (
    CascadeB0Detector,
)
from cpv301_autodrive.review2_cascade import (
    weights_available as cascade_weights_available,
)
from cpv301_autodrive.review2_scene_cut import (
    SCENE_CUT_SCORE_MIN,
    scene_change_score,
    scene_thumbnail,
)
from cpv301_autodrive.review2_temporal import track_prediction_rows
from cpv301_autodrive.review2_temporal_overlay import render_temporal_overlay_video
from cpv301_autodrive.review2_video_seek import (
    render_event_seek,
    render_exact_event_pair,
    render_selected_event_outcome,
)

MAX_BYTES = 40 * 1024 * 1024
MAX_SECONDS = 30
TARGET_FPS = 5
MAX_PIXELS = 1920 * 1536
MINI_SOURCE_SHA256 = "1fab75937ceba286abbc308138a814a7d9548b722184d4735b802f29d4b1f5ac"


def _is_local_preview_url(url: str | None) -> bool:
    parsed = urlsplit(url or "")
    return parsed.scheme in {"http", "https"} and parsed.hostname in {
        "localhost", "127.0.0.1", "::1",
    }


@dataclass(frozen=True)
class UploadResult:
    source_sha256: str
    video: bytes
    csv_text: str
    tracks_csv_text: str
    events_csv_text: str
    manifest: dict


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _draw_centercam_sides(
    image: Image.Image, detections: list, heading_x: float,
) -> Image.Image:
    """Show the estimated road side beside each numbered prediction on video."""
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("Arial.ttf", max(18, canvas.width // 55))
    except OSError:
        font = ImageFont.load_default()
    names = {"trái": "TRAI", "giữa": "GIUA", "phải": "PHAI"}
    for number, detection in enumerate(detections, start=1):
        x1, y1, x2, y2 = detection.box
        label = f"#{number} {names[side_of(detection.box, heading_x, canvas.width)]}"
        box = draw.textbbox((0, 0), label, font=font)
        text_w, text_h = box[2] - box[0], box[3] - box[1]
        x = max(0, min(int(x2) + 5, canvas.width - text_w - 8))
        y = max(0, min(int(y1), canvas.height - text_h - 8))
        draw.rectangle((x, y, x + text_w + 8, y + text_h + 8), fill="#0f172a")
        draw.text((x + 4, y + 4), label, fill="white", font=font)
    return canvas


def _csv_text(rows: list[dict], columns: tuple[str, ...]) -> str:
    stream = io.StringIO()
    writer_csv = csv.DictWriter(stream, fieldnames=columns)
    writer_csv.writeheader()
    writer_csv.writerows(rows)
    return stream.getvalue()


def _video_properties(capture: cv2.VideoCapture) -> tuple[float, int, int, int, int]:
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    codec = int(capture.get(cv2.CAP_PROP_FOURCC))
    if not math.isfinite(fps) or not 1 <= fps <= 60:
        raise ValueError("Video cần FPS hợp lệ trong khoảng 1–60.")
    if not 1 <= count <= MAX_SECONDS * fps:
        raise ValueError("Video cần dài tối đa 30 giây và có số frame đọc được.")
    if (
        width <= height
        or width <= 0
        or height <= 0
        or width > 1920
        or height > 1536
        or width * height > MAX_PIXELS
    ):
        raise ValueError("Video cần khung ngang với tối đa 1920×1536 pixel.")
    fourcc = "".join(chr((codec >> 8 * i) & 255) for i in range(4)).lower()
    if fourcc not in {"avc1", "h264", "x264"}:
        raise ValueError(f"Chỉ hỗ trợ video MP4/H.264; codec hiện tại là {fourcc!r}.")
    step = max(1, round(fps / TARGET_FPS))
    return fps, count, width, height, step


def _draw_track_ids(
    video: bytes, tracked_rows: list[dict], *, step: int, fps: float,
    width: int, height: int, expected_frames: int,
) -> bytes:
    """Burn heuristic track IDs into an already verified preview MP4."""
    if not tracked_rows:
        return video
    by_sample: dict[int, list[dict]] = {}
    for row in tracked_rows:
        frame = int(row["source_frame"])
        if frame % step or not 0 <= frame // step < expected_frames:
            raise RuntimeError("Track nằm ngoài lưới frame đã xuất.")
        if not row["same_frame_duplicate"]:
            by_sample.setdefault(frame // step, []).append(row)
    with tempfile.TemporaryDirectory(prefix="cpv301_review2_tracks_") as temporary:
        folder = Path(temporary)
        source = folder / "base.mp4"
        output = folder / "tracks.mp4"
        source.write_bytes(video)
        capture = cv2.VideoCapture(str(source))
        writer = cv2.VideoWriter(
            str(output), cv2.VideoWriter_fourcc(*"avc1"), fps, (width, height)
        )
        if not capture.isOpened() or not writer.isOpened():
            capture.release()
            writer.release()
            raise RuntimeError("Không thể mở MP4 để vẽ track ID.")
        count = 0
        try:
            while count < expected_frames:
                ok, frame = capture.read()
                if not ok or frame.shape[:2] != (height, width):
                    raise RuntimeError("MP4 chú giải thiếu frame trước khi vẽ track ID.")
                for row in by_sample.get(count, []):
                    label = f"ID {int(row['track_id'])}"
                    x = max(0, min(width - 1, round(float(row["x1"]))))
                    y = max(0, min(height - 1, round(float(row["y1"]))))
                    (text_width, text_height), baseline = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2
                    )
                    top = max(0, y - text_height - baseline - 8)
                    right = min(width - 1, x + text_width + 10)
                    bottom = min(height - 1, top + text_height + baseline + 8)
                    cv2.rectangle(frame, (x, top), (right, bottom), (20, 20, 20), -1)
                    cv2.putText(
                        frame, label, (x + 5, top + text_height + 3),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2,
                        cv2.LINE_AA,
                    )
                writer.write(frame)
                count += 1
            if capture.read()[0]:
                raise RuntimeError("MP4 chú giải có frame dư khi vẽ track ID.")
        finally:
            capture.release()
            writer.release()
        check = cv2.VideoCapture(str(output))
        try:
            verified = 0
            while check.isOpened() and check.read()[0]:
                verified += 1
        finally:
            check.release()
        if verified != expected_frames:
            raise RuntimeError("MP4 có track ID không đủ frame.")
        return output.read_bytes()


def process_uploaded_video(
    payload: bytes, original_name: str,
    detector: D1Detector | CascadeB0Detector | None = None,
    *, architecture: str = "d1_54",
) -> UploadResult:
    """Hash input, decode all frames, infer sampled frames and verify the exported MP4."""
    if architecture not in {"d1_54", "cascade_b0_r1"}:
        raise ValueError("Kiến trúc video chưa được hỗ trợ.")
    if not original_name.lower().endswith(".mp4") or not 0 < len(payload) <= MAX_BYTES:
        raise ValueError("Chỉ nhận MP4 khác rỗng, tối đa 40 MiB.")
    source_hash = _sha256(payload)
    with tempfile.TemporaryDirectory(prefix="cpv301_review2_") as temporary:
        folder = Path(temporary)
        source = folder / "input.mp4"
        output = folder / "preview.mp4"
        source.write_bytes(payload)
        capture = cv2.VideoCapture(str(source))
        if not capture.isOpened():
            raise ValueError("Không giải mã được video MP4.")
        writer = None
        rows: list[dict] = []
        scene_break_frames: list[int] = []
        previous_scene_thumbnail: np.ndarray | None = None
        maximum_scene_change_score = 0.0
        sampled = 0
        decoded = 0
        try:
            fps, count, width, height, step = _video_properties(capture)
            output_fps = fps / step
            writer = cv2.VideoWriter(
                str(output), cv2.VideoWriter_fourcc(*"avc1"), output_fps, (width, height)
            )
            if not writer.isOpened():
                raise RuntimeError("Không thể mã hóa MP4/H.264 trên máy này.")
            model = detector if detector is not None else (
                D1Detector() if architecture == "d1_54" else CascadeB0Detector()
            )
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                if frame.shape[:2] != (height, width):
                    raise ValueError("Kích thước frame thay đổi trong video.")
                frame_index = decoded
                decoded += 1
                if decoded > count + 2:
                    raise ValueError("Số frame thực vượt metadata của video.")
                if frame_index % step:
                    continue
                thumbnail = scene_thumbnail(frame)
                if previous_scene_thumbnail is not None:
                    score = scene_change_score(previous_scene_thumbnail, thumbnail)
                    maximum_scene_change_score = max(maximum_scene_change_score, score)
                    if score >= SCENE_CUT_SCORE_MIN:
                        scene_break_frames.append(frame_index)
                previous_scene_thumbnail = thumbnail
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                detections = model.detect(image, conf=DEFAULT_CONF)
                heading = center_cam(image)
                render_image = image
                annotated = draw_detections(
                    render_image, detections, heading.x if heading.estimated else None
                )
                annotated = _draw_centercam_sides(annotated, detections, heading.x)
                writer.write(cv2.cvtColor(np.asarray(annotated), cv2.COLOR_RGB2BGR))
                for detection in detections:
                    rows.append(
                        {
                            "source_frame": frame_index,
                            "time_ms_nominal": round(frame_index / fps * 1000),
                            "code": detection.sign.code,
                            "name_vi": detection.sign.name_vi,
                            "score": round(detection.confidence, 6),
                            "x1": round(detection.box[0], 2),
                            "y1": round(detection.box[1], 2),
                            "x2": round(detection.box[2], 2),
                            "y2": round(detection.box[3], 2),
                            "side_of_road_estimate": side_of(
                                detection.box, heading.x, image.width
                            ),
                            "heading_source": heading.source,
                            "validation_status": detection.sign.status,
                        }
                    )
                sampled += 1
            if decoded != count or sampled == 0:
                raise ValueError("Video kết thúc khác metadata hoặc không có frame để suy luận.")
        finally:
            capture.release()
            if writer is not None:
                writer.release()
        check = cv2.VideoCapture(str(output))
        verified_frames = 0
        try:
            if not check.isOpened():
                raise RuntimeError("Không đọc lại được MP4 chú giải.")
            while True:
                ok, _ = check.read()
                if not ok:
                    break
                verified_frames += 1
        finally:
            check.release()
        if verified_frames != sampled:
            raise RuntimeError("Số frame MP4 chú giải không khớp số frame đã suy luận.")
        video = output.read_bytes()
    columns = (
        "source_frame", "time_ms_nominal", "code", "name_vi", "score", "x1", "y1",
        "x2", "y2", "side_of_road_estimate", "heading_source", "validation_status",
    )
    csv_text = _csv_text(rows, columns)
    hold_samples = max(1, round(output_fps * 0.4))
    tracked_rows, events = track_prediction_rows(
        rows, sample_step=step, scene_break_frames=scene_break_frames,
        iou_min=0.30, max_missing_samples=hold_samples, predict_motion=True,
    )
    video = _draw_track_ids(
        video, tracked_rows, step=step, fps=output_fps,
        width=width, height=height, expected_frames=verified_frames,
    )
    video, temporal_visual = render_temporal_overlay_video(
        video, payload, tracked_rows,
        step=step, fps=output_fps, width=width, height=height,
        expected_frames=verified_frames,
        scene_break_frames=tuple(scene_break_frames),
        max_missing_samples=hold_samples,
    )
    # The D1 behavior gate is not an acceptance verdict for Cascade B0 classes.
    explained_events = explain_events(
        events, tracked_rows, load_classes() if architecture == "d1_54" else []
    )
    tracks_csv_text = _csv_text(
        tracked_rows,
        (*columns, "track_id", "stable_code", "stable_name_vi", "confirmed",
         "same_frame_duplicate"),
    )
    events_csv_text = _csv_text(
        explained_events,
        (
            "source_frame", "time_ms_nominal", "track_id", "stable_code", "stable_name_vi",
            "event", "vehicle_action", "evidence", "road_side_estimate",
            "road_applicability", "class_validation_status", "simulation_gate",
            "simulation_if_applicable", "target_speed_kmh_if_applicable",
            "simulation_reason",
        ),
    )
    manifest = {
        "package": (
            "REVIEW2_UPLOADED_FRONT_CASCADE_B0_R1"
            if architecture == "cascade_b0_r1"
            else "REVIEW2_UPLOADED_FRONT_D1_R1"
        ),
        "status": "DEMO_ONLY",
        "source_name": Path(original_name).name,
        "source_sha256": source_hash,
        "display_source_sha256": source_hash,
        "display_source_kind": (
            "raw_mini_internal_only" if source_hash == MINI_SOURCE_SHA256 else
            "uploaded_frames_unreviewed"
        ),
        "source_bytes": len(payload),
        "source_fps_nominal": fps,
        "source_frames_decoded": decoded,
        "source_width": width,
        "source_height": height,
        "sample_every_n_frames": step,
        "output_fps": output_fps,
        "output_frames_verified": verified_frames,
        "output_sha256": _sha256(video),
        "prediction_rows": len(rows),
        "prediction_csv_sha256": _sha256(csv_text.encode("utf-8")),
        "tracks_csv_sha256": _sha256(tracks_csv_text.encode("utf-8")),
        "events_csv_sha256": _sha256(events_csv_text.encode("utf-8")),
        "temporal_event_rows": len(events),
        "conditional_simulation_rows": sum(
            event["simulation_gate"] == "conditional_on_road_applicability"
            for event in explained_events
        ),
        "model_verified": detector is None,
        "model_sha256": (
            WEIGHTS_SHA256 if detector is None and architecture == "d1_54" else None
        ),
        "architecture": architecture,
        "detector_sha256": (
            (WEIGHTS_SHA256 if architecture == "d1_54" else CASCADE_DETECTOR_SHA256)
            if detector is None else None
        ),
        "classifier_sha256": (
            CASCADE_CLASSIFIER_SHA256 if detector is None and architecture == "cascade_b0_r1"
            else None
        ),
        "class_map_sha256": CLASS_MAP_SHA256,
        "confidence": DEFAULT_CONF,
        "timestamp_semantics": "nominal frame_index / source_fps; not measured wall-clock time",
        "audio": "not retained",
        "tracking": "heuristic_motion_iou_vote_r2_demo_only",
        "track_iou_min": 0.30,
        "track_hold_max_samples": hold_samples,
        "track_id_overlay": "visible_on_nonduplicate_predicted_boxes_r1_demo_only",
        "temporal_display": "bounded_hold_and_spatial_conflict_panel_r3_demo_only",
        "temporal_display_counts": temporal_visual,
        "centercam_overlay": "heading_line_and_estimated_left_middle_right_r1",
        "scene_cut_signal": "sampled_grayscale_mean_absolute_change_r1_demo_only",
        "scene_cut_score_threshold": SCENE_CUT_SCORE_MIN,
        "scene_cut_max_observed_score": round(maximum_scene_change_score, 6),
        "scene_break_source_frames": scene_break_frames,
        "simulation_policy": (
            POLICY_NAME if architecture == "d1_54" else "disabled_for_cascade_b0_r1"
        ),
        "vehicle_actions": False,
        "ground_truth_sign_labels": False,
        "accuracy_claim": None,
        "privacy_clearance": False,
        "presentation_rights_confirmed": False,
        "sealed_test_accessed": False,
    }
    return UploadResult(source_hash, video, csv_text, tracks_csv_text, events_csv_text, manifest)


def render_upload_demo() -> None:
    """Let the Owner run a short front-camera clip through the local D1 demo."""
    st.divider()
    st.subheader("Tải clip camera trước của bạn")
    st.caption(
        "MP4/H.264, khung ngang, tối đa 40 MiB và 30 giây. Bản thử nghiệm lấy mẫu khoảng 5 "
        "frame/giây, bỏ âm thanh. Không lưu clip lên Drive "
        "hoặc đưa vào train/validation. Kiểm tra quyền sử dụng và mặt/biển số trước khi "
        "trình chiếu."
    )
    options = ["d1_54"]
    if cascade_weights_available():
        options.append("cascade_b0_r1")
    architecture = st.selectbox(
        "Kiến trúc suy luận",
        options,
        format_func=lambda choice: {
            "d1_54": "YOLO11s-54 · một model",
            "cascade_b0_r1": "Cascade B0 · YOLO11s-1 + CompactCNN-54",
        }[choice],
        key="review2_video_architecture",
    )
    if architecture == "cascade_b0_r1":
        st.caption(
            "Cascade B0 dùng trọng số đã QA trên validation, crop 32×32 và tích điểm "
            "detector × classifier. Sự kiện chỉ để quan sát; không mô phỏng hành vi từ "
            "lớp Cascade vì chưa đánh giá riêng tính áp dụng cho đường/làn trong clip."
        )
    uploaded = st.file_uploader(
        "Chọn clip hành trình", type=["mp4"], max_upload_size=40, key="review2_front_video"
    )
    if uploaded is None:
        st.session_state.pop("review2_upload_result", None)
        return
    if uploaded.size > MAX_BYTES:
        st.error("Clip vượt 40 MiB; hãy cắt một đoạn ngắn trước khi tải lên.")
        return
    payload = uploaded.getvalue()
    digest = _sha256(payload)
    if digest == MINI_SOURCE_SHA256 and not _is_local_preview_url(st.context.url):
        st.error("Clip Mini rõ nét chỉ được xem nội bộ qua localhost.")
        return
    if st.button("Tạo video chú giải", type="primary", key="review2_process_video"):
        with st.spinner("Đang giải mã và nhận diện từng frame được lấy mẫu…"):
            try:
                st.session_state["review2_upload_result"] = process_uploaded_video(
                    payload, uploaded.name, architecture=architecture
                )
            except (ValueError, RuntimeError, OSError) as exc:
                st.session_state.pop("review2_upload_result", None)
                st.error(str(exc))
                return
    result = st.session_state.get("review2_upload_result")
    if (
        result is None
        or result.source_sha256 != digest
        or result.manifest["source_name"] != Path(uploaded.name).name
        or result.manifest["architecture"] != architecture
        or (
            digest == MINI_SOURCE_SHA256
            and (
                result.manifest.get("display_source_kind")
                != "raw_mini_internal_only"
                or result.manifest.get("display_source_sha256")
                != MINI_SOURCE_SHA256
            )
        )
    ):
        return
    st.warning(
        "DEMO_ONLY · Chưa có nhãn biển báo cho clip này; số dự đoán không phải độ chính xác."
    )
    if digest == MINI_SOURCE_SHA256:
        st.warning(
            "Clip PHENIKAA Mini rõ nét, không làm mờ hoặc che phương tiện. "
            "Chỉ dùng nội bộ trên máy này; chưa duyệt trình chiếu hay chia sẻ bản xuất."
        )
        st.caption(
            "Nguồn: [PHENIKAA OPEN DATASET]"
            "(https://github.com/phenikaa-dataset/phenikaa-devkit), "
            "`ROUNDABOUT/CAM_P_F`, [CC BY-NC-SA 4.0]"
            "(https://creativecommons.org/licenses/by-nc-sa/4.0/). "
            "Nhóm CPV301 AutoDrive dựng video từ frame theo timestamp, thêm dự đoán "
            "và vị trí trái/giữa/phải ước lượng bằng CenterCam; "
            "PHENIKAA không xác nhận kết quả model."
        )
    st.caption(
        "CenterCam: đường đứt màu cam là hướng đường ước lượng; đường xám là tâm ảnh "
        "khi không ước lượng được. Nhãn TRAI/GIUA/PHAI cạnh từng box là vị trí tương đối."
    )
    st.caption(
        "Ô góc trên trái giữ ảnh crop của biển đang theo dõi. LIVE là box model vừa thấy; "
        "HELD và khung xanh nét đứt là ước lượng tối đa 0,4 giây khi model hụt. "
        "CONFLICT là hai nhãn trên cùng một box và không được đưa vào mô phỏng hành vi. "
        "P.127 chưa xác minh trị số tốc độ; đây không phải nhận diện đúng được QA."
    )
    cascade = architecture == "cascade_b0_r1"
    export_stem = "review2_front_cascade_b0" if cascade else "review2_front_d1"
    event_rows = list(csv.DictReader(io.StringIO(result.events_csv_text)))
    selection = render_event_seek(
        event_rows,
        duration_ms=round(
            result.manifest["output_frames_verified"] / result.manifest["output_fps"] * 1000
        ),
        key=f"review2_uploaded_event_seek_{architecture}_{digest[:16]}",
    )
    render_selected_event_outcome(selection, behavior_enabled=not cascade)
    st.video(
        result.video, format="video/mp4", start_time=selection.start_time,
        alt="Clip camera trước với dự đoán Cascade B0" if cascade
            else "Clip camera trước với dự đoán D1",
    )
    render_exact_event_pair(
        selection,
        source_video=payload,
        output_video=result.video,
        source_sha256=result.manifest["display_source_sha256"],
        output_sha256=result.manifest["output_sha256"],
        source_frames=result.manifest["source_frames_decoded"],
        output_frames=result.manifest["output_frames_verified"],
        sample_step=result.manifest["sample_every_n_frames"],
    )
    a, b = st.columns(2)
    a.metric("Frame đã suy luận", result.manifest["output_frames_verified"])
    b.metric("Dòng dự đoán", result.manifest["prediction_rows"])
    st.metric("Sự kiện nhãn lặp (heuristic)", result.manifest["temporal_event_rows"])
    st.caption(
        "ID trên video khớp cột track_id trong CSV; ghép box bằng IoU và bình chọn nhãn "
        "trên các frame lấy mẫu; "
        f"đã reset track tại {len(result.manifest['scene_break_source_frames'])} "
        "mốc thay đổi cảnh mạnh theo tín hiệu ảnh thử nghiệm. "
        + (
            "Cascade B0 không tạo mô phỏng hành vi từ nhãn của clip. "
            if cascade else
            "Mô phỏng chỉ là giả định nếu biển áp dụng cho làn đang đi. "
        )
        + "Không phát lệnh xe."
    )
    event_title = (
        "Sự kiện nhãn lặp · không mô phỏng hành vi" if cascade
        else "Sự kiện và mô phỏng có điều kiện"
    )
    with st.expander(event_title, expanded=False):
        st.dataframe(event_rows, hide_index=True, width="stretch")
    st.download_button(
        "Tải MP4 chú giải", result.video, file_name=f"{export_stem}.mp4", mime="video/mp4"
    )
    st.download_button(
        "Tải CSV dự đoán", result.csv_text, file_name=f"{export_stem}.csv", mime="text/csv"
    )
    st.download_button(
        "Tải CSV track", result.tracks_csv_text,
        file_name=f"{export_stem}.tracks.csv", mime="text/csv"
    )
    st.download_button(
        "Tải CSV sự kiện", result.events_csv_text,
        file_name=f"{export_stem}.events.csv", mime="text/csv"
    )
    st.download_button(
        "Tải manifest", json.dumps(result.manifest, ensure_ascii=False, indent=2),
        file_name=f"{export_stem}.manifest.json", mime="application/json",
    )
    st.caption(
        "Tracking heuristic chỉ phục vụ demo; không phát lệnh xe. "
        "sealed_test_accessed=false."
    )
