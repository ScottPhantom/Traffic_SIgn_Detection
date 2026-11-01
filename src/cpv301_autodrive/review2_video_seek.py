"""Review-only event navigation for the front-camera video preview."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import streamlit as st

from cpv301_autodrive.review2_frame_pair import event_frame_indices, exact_video_frame


@dataclass(frozen=True)
class EventSelection:
    start_time: timedelta
    event: Mapping[str, object] | None


def selected_event_outcome(
    selection: EventSelection, *, behavior_enabled: bool
) -> tuple[str, str]:
    """Describe the selected prediction without presenting a vehicle command."""
    event = selection.event
    if event is None:
        return ("Kết quả mô phỏng", "Chọn một sự kiện để xem giải thích có điều kiện.")
    if event.get("vehicle_action") != "none":
        raise ValueError("Sự kiện demo không được chứa lệnh điều khiển xe.")
    label = f"{event['stable_code']} · {event['stable_name_vi']} · track {event['track_id']}"
    if not behavior_enabled:
        return (label, "Cascade B0 chỉ hiển thị dự đoán; không mô phỏng hành vi từ nhãn clip.")
    if event.get("road_applicability") != "unverified":
        raise ValueError("Trạng thái áp dụng cho làn xe chưa được kiểm chứng.")
    reason = str(event.get("simulation_reason", "")).strip()
    if not reason:
        raise ValueError("Sự kiện thiếu giải thích mô phỏng.")
    return (label, f"{reason} Không phát lệnh điều khiển xe.")


def render_selected_event_outcome(
    selection: EventSelection, *, behavior_enabled: bool
) -> None:
    """Show the conditional result next to the event selector."""
    title, description = selected_event_outcome(
        selection, behavior_enabled=behavior_enabled
    )
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.info(description)


def event_seek_time(event: Mapping[str, object], *, duration_ms: int) -> timedelta:
    """Return an event's nominal video time, rejecting out-of-range rows."""
    time_ms = int(event["time_ms_nominal"])
    if not 0 <= time_ms < duration_ms:
        raise ValueError("Thời điểm sự kiện nằm ngoài clip đã xuất.")
    return timedelta(milliseconds=time_ms)


def render_event_seek(
    events: Sequence[Mapping[str, object]], *, duration_ms: int, key: str
) -> EventSelection:
    """Select a review event and return its nominal video time and source row."""
    if not events:
        return EventSelection(timedelta(0), None)
    times = [event_seek_time(event, duration_ms=duration_ms) for event in events]
    labels = ["Từ đầu clip"]
    for index, (event, time) in enumerate(zip(events, times, strict=True), start=1):
        labels.append(
            f"{index} · {time.total_seconds():.1f} giây · "
            f"{event['stable_code']} {event['stable_name_vi']} · track {event['track_id']}"
        )
    selected = st.selectbox(
        "Chuyển video tới sự kiện", range(len(labels)),
        format_func=lambda index: labels[index], key=key,
    )
    st.caption(
        "Chọn mốc để mở video gần thời điểm của dự đoán lặp lại. "
        "Trình phát Streamlit làm tròn thời điểm tới giây; các video không đồng bộ "
        "liên tục khi phát. Đây không phải nhãn biển đã kiểm chứng."
    )
    if selected is None or selected == 0:
        return EventSelection(timedelta(0), None)
    return EventSelection(times[selected - 1], events[selected - 1])


def render_exact_event_pair(
    selection: EventSelection,
    *,
    source_video: bytes | Path,
    output_video: bytes | Path,
    source_sha256: str,
    output_sha256: str,
    source_frames: int,
    output_frames: int,
    sample_step: int,
) -> None:
    """Show matching decoded frames when an event is selected."""
    if selection.event is None:
        return
    with st.expander("Đối chiếu đúng frame của sự kiện", expanded=True):
        try:
            source_index, output_index = event_frame_indices(
                selection.event, source_frames=source_frames,
                output_frames=output_frames, sample_step=sample_step,
            )
            source_image = exact_video_frame(
                source_video, source_index, expected_sha256=source_sha256,
            )
            output_image = exact_video_frame(
                output_video, output_index, expected_sha256=output_sha256,
            )
        except (OSError, ValueError) as exc:
            st.error(f"Không thể đối chiếu frame sự kiện: {exc}")
            return
        source_column, output_column = st.columns(2)
        source_column.image(
            source_image, width="stretch", alt=f"Frame nguồn {source_index} chưa chú giải",
        )
        output_column.image(
            output_image, width="stretch", alt=f"Frame chú giải {output_index}",
        )
        st.caption(
            f"Cùng một mốc: frame nguồn {source_index} → frame chú giải {output_index}, "
            f"{selection.start_time.total_seconds():.1f} giây danh nghĩa. "
            "Ảnh giải mã đúng frame; hai trình phát video vẫn chỉ nhảy gần đúng tới giây. "
            "Đây là dự đoán chưa có nhãn biển xác minh."
        )
