"""Exact decoded frame pairs for the local Review 2 video event viewer."""

from __future__ import annotations

import hashlib
import tempfile
from collections.abc import Mapping
from pathlib import Path

import cv2
from PIL import Image


def event_frame_indices(
    event: Mapping[str, object], *, source_frames: int, output_frames: int,
    sample_step: int,
) -> tuple[int, int]:
    """Map a sampled event to exact source and output frame indices."""
    source = int(event["source_frame"])
    if source_frames <= 0 or output_frames <= 0 or sample_step <= 0:
        raise ValueError("Metadata số frame hoặc bước lấy mẫu không hợp lệ.")
    if output_frames != (source_frames + sample_step - 1) // sample_step:
        raise ValueError("Số frame video chú giải không khớp bước lấy mẫu.")
    if not 0 <= source < source_frames or source % sample_step:
        raise ValueError("Frame sự kiện không nằm trên lưới lấy mẫu.")
    output = source // sample_step
    if output >= output_frames:
        raise ValueError("Frame sự kiện vượt khỏi video chú giải.")
    return source, output


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decode_frame(path: Path, frame_index: int, expected_sha256: str) -> Image.Image:
    if frame_index < 0 or _file_sha256(path) != expected_sha256:
        raise ValueError("Video hoặc frame không khớp manifest đã kiểm.")
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError("Không thể giải mã video để đối chiếu frame.")
    try:
        frame = None
        for _ in range(frame_index + 1):
            ok, frame = capture.read()
            if not ok:
                raise ValueError("Frame sự kiện không tồn tại trong video.")
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        capture.release()


def exact_video_frame(
    video: bytes | Path, frame_index: int, *, expected_sha256: str,
) -> Image.Image:
    """Verify the video hash, then decode sequentially to an exact frame."""
    if isinstance(video, Path):
        return _decode_frame(video, frame_index, expected_sha256)
    with tempfile.TemporaryDirectory(prefix="cpv301_review2_frame_") as folder:
        path = Path(folder) / "clip.mp4"
        path.write_bytes(video)
        return _decode_frame(path, frame_index, expected_sha256)
