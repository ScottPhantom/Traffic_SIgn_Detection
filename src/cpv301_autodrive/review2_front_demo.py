"""Read-only Review 2 preview of a PHENIKAA front-camera demo clip."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

import streamlit as st

from cpv301_autodrive.detector_d1 import load_classes, sha256_file
from cpv301_autodrive.review2_behavior import explain_events
from cpv301_autodrive.review2_temporal import _iou, track_prediction_rows
from cpv301_autodrive.review2_temporal_overlay import (
    ClipReview,
    render_temporal_overlay_video,
)
from cpv301_autodrive.review2_upload_video import render_upload_demo
from cpv301_autodrive.review2_video_seek import (
    render_event_seek,
    render_exact_event_pair,
    render_selected_event_outcome,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
VIDEO_DIR = REPO_ROOT / "data/processed/phenikaa_front_demo_r1"
RAW_VIDEO = VIDEO_DIR / "ROUNDABOUT_CAM_P_F.mp4"
RAW_MANIFEST = VIDEO_DIR / "ROUNDABOUT_CAM_P_F.manifest.json"
OVERLAY_VIDEO = VIDEO_DIR / "ROUNDABOUT_CAM_P_F_D1.mp4"
OVERLAY_MANIFEST = VIDEO_DIR / "ROUNDABOUT_CAM_P_F_D1.manifest.json"
PREDICTIONS = VIDEO_DIR / "ROUNDABOUT_CAM_P_F_D1.predictions.csv"
RAW_MANIFEST_SHA256 = "8348a988a5ab09a3b99fe966aabdd60e67af1e9ce5b2a8e703b134d378d2374c"
OVERLAY_MANIFEST_SHA256 = "d0061a1faf7c8ab1c1c2a3f2779bac7f6e6f7c88446c8ae2a0ec61c35f12c086"
# The Owner reviewed this exact Mini clip: tracks 1 and 3 are one W.207 sign;
# W.224 is a false model label here. Never apply this review to uploaded clips.
MINI_OWNER_REVIEW = (ClipReview((1, 3), "W.207"),)


def _verify_mini_owner_review(tracks: list[dict]) -> None:
    """Reject a stale track-ID annotation if the tracker output changes."""
    first = [
        row for row in tracks
        if int(row["source_frame"]) == 0 and int(row["track_id"]) == 1
    ]
    pair = {
        int(row["track_id"]): row for row in tracks
        if int(row["source_frame"]) == 23 and int(row["track_id"]) in (1, 3)
    }
    if len(first) != 1 or first[0]["code"] != "W.224" or set(pair) != {1, 3}:
        raise ValueError("Mini Owner review no longer matches track identities")
    if {pair[1]["code"], pair[3]["code"]} != {"W.207", "W.224"}:
        raise ValueError("Mini Owner review no longer matches class conflict")
    boxes = [
        tuple(float(row[key]) for key in ("x1", "y1", "x2", "y2"))
        for row in (pair[1], pair[3])
    ]
    if _iou(*boxes) < 0.90:
        raise ValueError("Mini Owner review no longer matches the same box")


def _is_local_preview_url(url: str | None) -> bool:
    """Keep the unapproved clear Mini preview on a loopback browser URL."""
    parsed = urlsplit(url or "")
    return parsed.scheme in {"http", "https"} and parsed.hostname in {
        "localhost", "127.0.0.1", "::1",
    }


@st.cache_data(show_spinner="Đang dựng bản video giữ biển và ô góc trái…", max_entries=1)
def _temporal_clear_preview(
    source_sha256: str, overlay_sha256: str, tracked_json: str,
    frame_count: int, fps: float, width: int, height: int, hold_samples: int,
    render_version: str,
) -> tuple[bytes, str, dict[str, int]]:
    """Build an internal-only successor from the hash-verified clear R1 pair."""
    if render_version != "r14_manual_label_w207":
        raise ValueError("Unexpected Review 2 preview version")
    if sha256_file(RAW_VIDEO) != source_sha256 or sha256_file(OVERLAY_VIDEO) != overlay_sha256:
        raise ValueError("Nguồn R1 đã thay đổi; không dựng video giữ biển.")
    tracks = json.loads(tracked_json)
    _verify_mini_owner_review(tracks)
    video, counts = render_temporal_overlay_video(
        OVERLAY_VIDEO, RAW_VIDEO, tracks, step=1, fps=fps,
        width=width, height=height, expected_frames=frame_count,
        draw_observed_ids=True, max_missing_samples=hold_samples,
        clip_reviews=MINI_OWNER_REVIEW,
    )
    return video, hashlib.sha256(video).hexdigest(), counts


def _verified_preview() -> tuple[dict, dict, list[dict[str, str]]] | None:
    paths = (RAW_VIDEO, RAW_MANIFEST, OVERLAY_VIDEO, OVERLAY_MANIFEST, PREDICTIONS)
    if not all(path.is_file() for path in paths):
        return None
    if sha256_file(RAW_MANIFEST) != RAW_MANIFEST_SHA256:
        raise ValueError("Review 2 raw manifest differs from the reviewed artifact")
    if sha256_file(OVERLAY_MANIFEST) != OVERLAY_MANIFEST_SHA256:
        raise ValueError("Review 2 overlay manifest differs from the reviewed artifact")
    raw = json.loads(RAW_MANIFEST.read_text(encoding="utf-8"))
    overlay = json.loads(OVERLAY_MANIFEST.read_text(encoding="utf-8"))
    if raw.get("status") != "DEMO_ONLY" or overlay.get("status") != "DEMO_ONLY":
        raise ValueError("Review 2 preview is missing DEMO_ONLY status")
    if raw.get("sealed_test_accessed") is not False:
        raise ValueError("raw preview seal marker is invalid")
    if overlay.get("sealed_test_accessed") is not False:
        raise ValueError("overlay preview seal marker is invalid")
    checks = (
        (RAW_VIDEO, raw["output_sha256"]),
        (RAW_MANIFEST, overlay["source_manifest_sha256"]),
        (OVERLAY_VIDEO, overlay["video_sha256"]),
        (PREDICTIONS, overlay["prediction_csv_sha256"]),
    )
    for path, expected in checks:
        if sha256_file(path) != expected:
            raise ValueError(f"Review 2 preview hash mismatch: {path.name}")
    if raw["camera"] != "CAM_P_F" or raw["output_frames"] != overlay["encoded_video_frames"]:
        raise ValueError("Review 2 source/overlay frame contract differs")
    with PREDICTIONS.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != overlay["prediction_rows"]:
        raise ValueError("Review 2 prediction row count differs")
    return raw, overlay, rows



def render_review2_front_demo() -> None:
    """Present one locally verified, front-camera-only demo without accuracy claims."""
    st.subheader("Review 2 · camera trước xe (bản thử nghiệm)")
    st.caption(
        "PHENIKAA Mini Dataset · ROUNDABOUT · CAM_P_F. Clip được ghép từ ảnh theo timestamp "
        "và dùng YOLO11s 54 lớp đã pin để vẽ dự đoán. Có thể tải clip MP4 ngắn ở bên dưới; "
        "bảng track/sự kiện dùng ghép box và bình chọn nhãn heuristic. Chỉ mô phỏng; "
        "model chưa đạt D-05."
    )
    try:
        preview = _verified_preview()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        st.error(f"Không thể kiểm chứng video demo: {exc}")
        render_upload_demo()
        return
    if preview is None:
        st.info("Chưa có clip camera trước và manifest hợp lệ trên máy này.")
        render_upload_demo()
        return
    raw, overlay, rows = preview
    if not _is_local_preview_url(st.context.url):
        st.error("Clip Mini rõ nét chỉ được xem nội bộ trên localhost.")
        render_upload_demo()
        return
    st.warning(
        "DEMO_ONLY: bộ dữ liệu cung cấp nhãn 3D Car/Rider/Pedestrian, không có ground truth "
        "biển báo trong clip này. Số box bên dưới là dự đoán, không phải độ chính xác. "
        "Không dùng clip để chọn model hoặc ngưỡng."
    )
    with st.expander("Nguồn, giấy phép và thay đổi của clip", expanded=False):
        st.markdown(
            "Ảnh camera trước: [PHENIKAA Open Dataset]"
            "(https://github.com/phenikaa-dataset/phenikaa-devkit), "
            "công bố theo [CC BY-NC-SA 4.0]"
            "(https://creativecommons.org/licenses/by-nc-sa/4.0/). "
            "Bản demo này ghép ảnh `ROUNDABOUT/CAM_P_F` thành MP4 theo timestamp, "
            "lặp sáu slot thiếu và tạo một bản video chú giải bằng dự đoán YOLO11s-54. "
            "Đây là bản dẫn xuất phi thương mại; khi chia sẻ cần ghi nguồn, nêu thay đổi "
            "và giữ điều kiện ShareAlike. PHENIKAA không bảo trợ kết quả dự đoán."
        )
        st.caption(
            "Quyền riêng tư của người hoặc biển số có thể xuất hiện trong cảnh chưa được "
            "xác minh riêng. Không phát hành video/ảnh ra ngoài nhóm khi chưa rà soát; "
            "yêu cầu truy cập full dataset vẫn đang chờ phản hồi."
        )
    a, b, c = st.columns(3)
    a.metric("Ảnh gốc", raw["source_count"])
    b.metric("Frame video", raw["output_frames"])
    c.metric("Frame nguồn có dự đoán", overlay["unique_frames_with_predictions"])
    st.caption(
        f"{raw['source_duration_seconds']:.1f} giây theo timestamp · 10 fps · "
        f"{raw['repeated_slots']} frame lặp để giữ thời gian · "
        f"{overlay['prediction_rows']} dòng dự đoán"
    )
    temporal_input = [
        {
            **row,
            "source_frame": int(row["first_video_frame"]),
            "time_ms_nominal": round(
                int(row["first_video_frame"]) / raw["output_fps"] * 1000
            ),
        }
        for row in rows
    ]
    tracks_r1, events_r1 = track_prediction_rows(temporal_input, sample_step=1)
    hold_samples = max(1, round(raw["output_fps"] * 0.4))
    tracks_r14, events_r14 = track_prediction_rows(
        temporal_input, sample_step=1, iou_min=0.30,
        max_missing_samples=hold_samples, predict_motion=True,
    )
    source_video, output_video = RAW_VIDEO, OVERLAY_VIDEO
    source_hash, output_hash = raw["output_sha256"], overlay["video_sha256"]
    preview_options = (
        "R14 · rõ nét + biển W.207 đã rà soát",
        "R1 · video gốc rõ nét + CenterCam",
    )
    selected_preview = st.selectbox(
        "Bản video xem nội bộ",
        preview_options,
        key="review2_precomputed_preview_r14",
    )
    tracks, events = (
        (tracks_r14, events_r14) if selected_preview.startswith("R14")
        else (tracks_r1, events_r1)
    )
    if selected_preview.startswith("R14"):
        try:
            output_video, output_hash, visual_counts = _temporal_clear_preview(
                raw["output_sha256"], overlay["video_sha256"],
                json.dumps(tracks, ensure_ascii=False, sort_keys=True),
                raw["output_frames"], raw["output_fps"], raw["width"], raw["height"],
                hold_samples, "r14_manual_label_w207",
            )
        except (OSError, RuntimeError, ValueError) as exc:
            st.error(f"Không dựng được bản R14: {exc}")
            render_upload_demo()
            return
        source_video = RAW_VIDEO
        source_hash = raw["output_sha256"]
        st.warning(
            "R14 là demo nội bộ rõ nét. Qua rà soát thủ công clip Mini, ID 1/3 "
            "là cùng một biển W.207; W.224 là nhãn model dự đoán sai. Ô góc trái "
            "hiện W.207 [MANUAL] cho biển này, không coi đó là dự đoán đúng của model. "
            "Khung xanh nét đứt chỉ giữ biển tối đa 0,4 giây khi hụt detection. "
            "Chưa có QA độc lập hoặc quyền trình chiếu bản R14."
        )
        st.caption(
            f"R14 có {visual_counts['panel_frames']} frame hiện ô biển và "
            f"{visual_counts['held_box_frames']} lượt khung giữ tạm. "
            "Box xung đột không tạo hành vi mô phỏng; P.127 chưa xác minh trị số tốc độ."
        )
    elif selected_preview.startswith("R1"):
        source_video, output_video = RAW_VIDEO, OVERLAY_VIDEO
        source_hash, output_hash = raw["output_sha256"], overlay["video_sha256"]
        st.warning(
            "Video rõ nét không làm mờ hoặc che phương tiện. Chỉ xem nội bộ trên localhost; "
            "Chưa duyệt trình chiếu hoặc chia sẻ bản này."
        )
    transformation = (
        "giữ nguyên cảnh rõ nét, thêm dự đoán YOLO11s-54, CenterCam, "
        "ô crop biển và khung giữ tạm."
        if selected_preview.startswith("R14") else
        "giữ nguyên cảnh rõ nét và thêm dự đoán YOLO11s-54 cùng CenterCam."
    )
    st.caption(
        "Nguồn: [PHENIKAA OPEN DATASET](https://github.com/phenikaa-dataset/phenikaa-devkit), "
        "`ROUNDABOUT/CAM_P_F`, [CC BY-NC-SA 4.0]"
        "(https://creativecommons.org/licenses/by-nc-sa/4.0/). "
        "Nhóm CPV301 AutoDrive dựng frame theo timestamp, "
        + transformation + " PHENIKAA không xác nhận kết quả model."
    )
    st.caption(
        "CenterCam trên video chú giải: đường cam ước lượng hướng đường; đường xám "
        "là tâm ảnh khi không ước lượng được. Vị trí trái/giữa/phải của từng biển "
        "chỉ là ước lượng hình học."
    )
    st.caption(
        "P.127 là mã biển chung. Bản đồ lớp hiện tại phân biệt riêng 40, 50, 60 và "
        "80 km/h, nhưng chữ trên khung video chỉ hiện mã P.127; chưa có lớp 30 hoặc "
        "70 km/h. Không suy ra trị số tốc độ chỉ từ mã trên khung."
    )
    explained_events = explain_events(events, tracks, load_classes())
    selection = render_event_seek(
        explained_events,
        duration_ms=round(raw["output_frames"] / raw["output_fps"] * 1000),
        key="review2_precomputed_event_seek",
    )
    render_selected_event_outcome(selection, behavior_enabled=True)
    original_col, prediction_col = st.columns(2)
    with original_col:
        st.video(
            str(source_video), start_time=selection.start_time,
            alt="Clip camera trước xe PHENIKAA chưa có chú giải",
        )
    with prediction_col:
        st.video(
            str(output_video) if isinstance(output_video, Path) else output_video,
            start_time=selection.start_time,
            alt="Clip camera trước với box, mã biển YOLO11s và hướng đường CenterCam",
        )
    render_exact_event_pair(
        selection,
        source_video=source_video,
        output_video=output_video,
        source_sha256=source_hash,
        output_sha256=output_hash,
        source_frames=raw["output_frames"],
        output_frames=overlay["encoded_video_frames"],
        sample_step=1,
    )
    with st.expander("Dự đoán từng ảnh nguồn và nguồn gốc", expanded=False):
        st.dataframe(rows, hide_index=True, width="stretch", alt="Dự đoán biển trên từng ảnh nguồn")
        st.caption(
            "Nguồn: PHENIKAA Perception Dataset, CC BY-NC-SA 4.0. "
            "Video chỉ dùng cho nghiên cứu/học tập không thương mại. "
            f"SHA-256 video đang phát (nền): {source_hash} · "
            f"video đang phát (chú giải): {output_hash}. "
            f"SHA-256 clip nguồn trước xử lý: {raw['output_sha256']}. "
            "sealed_test_accessed=false."
        )
    with st.expander("Track và sự kiện nhãn lặp · thử nghiệm", expanded=False):
        st.caption(
            "Chỉ nhóm dự đoán theo vị trí và bình chọn nhãn. "
            "Hành vi mô phỏng chỉ có ý nghĩa nếu biển thực sự áp dụng cho làn xe; "
            "điều đó chưa được xác minh. Không phát lệnh xe."
        )
        st.metric("Sự kiện nhãn lặp", len(events))
        st.caption(
            "Track có hai nhãn trên gần cùng một box được đánh dấu "
            "spatial_class_conflict; mọi mô phỏng điều kiện của track đó bị chặn. "
            "Bảng sự kiện là lịch sử dự đoán, không phải biển đang hiện diện ở frame hiện tại."
        )
        st.dataframe(explained_events, hide_index=True, width="stretch")
        st.dataframe(
            [
                {
                    "frame": row["source_frame"],
                    "track_id": row["track_id"],
                    "nhãn_gốc": row["code"],
                    "nhãn_ổn_định": row["stable_code"],
                    "tên_ổn_định": row["stable_name_vi"],
                    "xác_nhận_lặp": row["confirmed"],
                    "trùng_trong_frame": row["same_frame_duplicate"],
                }
                for row in tracks
            ],
            hide_index=True,
            width="stretch",
        )
    render_upload_demo()

