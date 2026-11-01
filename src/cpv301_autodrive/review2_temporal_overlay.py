"""Review-only video display of short-lived sign tracks.

Raw detector rows remain the evidence. A dashed box is only a short visual
prediction across missing sampled frames, never a new model detection.
"""

from __future__ import annotations

import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from cpv301_autodrive.review2_temporal import (
    COINCIDENT_TRACK_IOU_MIN,
    MAX_MISSING_SAMPLES,
    _iou,
)


@dataclass(frozen=True)
class DisplaySign:
    track_id: int
    box: tuple[float, float, float, float]
    code: str
    score: float
    observed: bool
    confirmed: bool
    age_samples: int = 0
    name_vi: str = ""
    related_track_ids: tuple[int, ...] = ()
    conflict_codes: tuple[str, ...] = ()
    reviewed_code: str = ""


@dataclass(frozen=True)
class ClipReview:
    """Human label for one hash-bound clip, never a model prediction."""

    track_ids: tuple[int, ...]
    accepted_code: str


@dataclass
class _Active:
    box: tuple[float, float, float, float]
    last_sample: int
    previous_box: tuple[float, float, float, float] | None
    previous_sample: int | None
    code: str
    score: float
    confirmed: bool
    name_vi: str


def _collapse_coincident_signs(
    signs: list[DisplaySign], *, clip_reviews: tuple[ClipReview, ...] = (),
) -> tuple[DisplaySign, ...]:
    """Show one object for coincident or clip-reviewed same-object tracks."""
    groups: list[list[DisplaySign]] = []
    for sign in signs:
        touching = [
            group for group in groups
            if any(
                _iou(sign.box, other.box) >= COINCIDENT_TRACK_IOU_MIN
                or any(
                    sign.track_id in review.track_ids and other.track_id in review.track_ids
                    for review in clip_reviews
                )
                for other in group
            )
        ]
        if not touching:
            groups.append([sign])
            continue
        primary = touching[0]
        primary.append(sign)
        for group in touching[1:]:
            primary.extend(group)
            groups.remove(group)
    collapsed = []
    for group in groups:
        live = [sign for sign in group if sign.observed]
        candidates = live or group
        chosen = min(candidates, key=lambda sign: sign.track_id)
        labels = {(sign.code, sign.name_vi) for sign in candidates}
        conflict = len(labels) > 1
        review = next(
            (
                item for item in clip_reviews
                if any(sign.track_id in item.track_ids for sign in group)
            ),
            None,
        )
        related_ids = (
            review.track_ids if review else
            tuple(sorted(sign.track_id for sign in candidates))
        )
        collapsed.append(DisplaySign(
            track_id=chosen.track_id,
            box=chosen.box,
            code=chosen.code,
            score=max(sign.score for sign in candidates),
            observed=chosen.observed,
            confirmed=chosen.confirmed,
            age_samples=chosen.age_samples,
            name_vi=chosen.name_vi,
            related_track_ids=related_ids,
            conflict_codes=tuple(sorted({sign.code for sign in candidates})) if conflict else (),
            reviewed_code=review.accepted_code if review else "",
        ))
    return tuple(sorted(collapsed, key=lambda sign: sign.track_id))


def _predicted_box(track: _Active, age: int) -> tuple[float, float, float, float]:
    if track.previous_box is None or track.previous_sample is None:
        return track.box
    elapsed = track.last_sample - track.previous_sample
    if elapsed <= 0:
        return track.box
    # A constant-velocity estimate is for display only; never used to label a sign.
    return tuple(
        current + (current - previous) * age / elapsed
        for current, previous in zip(track.box, track.previous_box, strict=True)
    )


def display_timeline(
    tracked_rows: list[dict[str, Any]], *, expected_frames: int, step: int,
    width: int, height: int, scene_break_frames: tuple[int, ...] = (),
    max_missing_samples: int = MAX_MISSING_SAMPLES,
    clip_reviews: tuple[ClipReview, ...] = (),
) -> list[tuple[DisplaySign, ...]]:
    """Include observed boxes and bounded dashed, confirmed missing samples."""
    if min(expected_frames, step, width, height) <= 0 or max_missing_samples < 0:
        raise ValueError("Invalid video display dimensions or sampling")
    if any(frame < 0 or frame % step for frame in scene_break_frames):
        raise ValueError("Scene breaks must match sampled frames")
    for review in clip_reviews:
        if (
            not review.track_ids
            or len(set(review.track_ids)) != len(review.track_ids)
            or any(track_id <= 0 for track_id in review.track_ids)
            or not review.accepted_code
        ):
            raise ValueError("Invalid clip review")
    by_sample: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in tracked_rows:
        frame = int(row["source_frame"])
        if frame < 0 or frame % step or frame // step >= expected_frames:
            raise ValueError("Tracked row lies outside the video sample grid")
        if row.get("same_frame_duplicate") not in (False, "False", "false", "0", 0):
            continue
        by_sample[frame // step].append(row)

    active: dict[int, _Active] = {}
    breaks = set(scene_break_frames)
    output: list[tuple[DisplaySign, ...]] = []
    for sample in range(expected_frames):
        if sample * step in breaks:
            active.clear()
        visible: list[DisplaySign] = []
        observed_ids: set[int] = set()
        for row in by_sample[sample]:
            track_id = int(row["track_id"])
            if track_id in observed_ids:
                raise ValueError("Two nonduplicate boxes share a track in one frame")
            observed_ids.add(track_id)
            box = tuple(float(row[key]) for key in ("x1", "y1", "x2", "y2"))
            if box[2] <= box[0] or box[3] <= box[1]:
                raise ValueError("Invalid tracked box")
            previous = active.get(track_id)
            confirmed = row["confirmed"] in (True, "True", "true", "1", 1)
            # A current-frame class conflict must not be hidden by an older
            # voted label. The panel reports the raw model code for this box.
            code = str(row["code"])
            score = float(row["score"])
            name_vi = str(row.get("name_vi", ""))
            active[track_id] = _Active(
                box, sample, previous.box if previous else None,
                previous.last_sample if previous else None, code, score, confirmed,
                name_vi,
            )
            visible.append(DisplaySign(
                track_id, box, code, score, True, confirmed, name_vi=name_vi,
            ))
        for track_id, track in list(active.items()):
            if track_id in observed_ids:
                continue
            age = sample - track.last_sample
            if age > max_missing_samples or not track.confirmed:
                del active[track_id]
                continue
            box = _predicted_box(track, age)
            # A sign beyond the visible frame has left the view; do not preserve a ghost.
            if box[2] <= 0 or box[0] >= width or box[3] <= 0 or box[1] >= height:
                del active[track_id]
                continue
            clipped = (
                max(0.0, box[0]), max(0.0, box[1]),
                min(float(width - 1), box[2]), min(float(height - 1), box[3]),
            )
            if clipped[2] <= clipped[0] or clipped[3] <= clipped[1]:
                del active[track_id]
                continue
            visible.append(DisplaySign(
                track_id, clipped, track.code, track.score, False, True, age,
                name_vi=track.name_vi,
            ))
        output.append(_collapse_coincident_signs(visible, clip_reviews=clip_reviews))
    return output


def _dashed_box(frame: np.ndarray, box: tuple[float, float, float, float]) -> None:
    x1, y1, x2, y2 = (round(value) for value in box)
    color = (255, 220, 0)  # cyan in BGR: this is a held estimate, not a model box.
    length = 12
    for x in range(x1, x2, length * 2):
        cv2.line(frame, (x, y1), (min(x + length, x2), y1), color, 2)
        cv2.line(frame, (x, y2), (min(x + length, x2), y2), color, 2)
    for y in range(y1, y2, length * 2):
        cv2.line(frame, (x1, y), (x1, min(y + length, y2)), color, 2)
        cv2.line(frame, (x2, y), (x2, min(y + length, y2)), color, 2)


def _crop(frame: np.ndarray, box: tuple[float, float, float, float]) -> np.ndarray | None:
    height, width = frame.shape[:2]
    x1, y1 = max(0, int(box[0])), max(0, int(box[1]))
    x2, y2 = min(width, int(box[2] + 1)), min(height, int(box[3] + 1))
    if x2 <= x1 or y2 <= y1:
        return None
    patch = frame[y1:y2, x1:x2]
    return cv2.resize(patch, (76, 76), interpolation=cv2.INTER_CUBIC)


def _panel(frame: np.ndarray, signs: tuple[DisplaySign, ...], crops: dict[int, np.ndarray]) -> bool:
    if not signs:
        return False
    height, width = frame.shape[:2]
    if width < 380 or height < 150:
        return False
    panel_width = min(366, width - 24)
    shown = signs[: min(3, max(0, (height - 58) // 88))]
    if not shown:
        return False
    panel_height = 42 + 88 * len(shown)
    region = frame[12:12 + panel_height, 12:12 + panel_width]
    dark = np.zeros_like(region)
    cv2.addWeighted(region, 0.25, dark, 0.75, 0, region)
    heading = (
        "MODEL BOXES / MANUAL LABEL" if any(sign.reviewed_code for sign in shown)
        else "MODEL SIGNS - UNVERIFIED"
    )
    cv2.putText(frame, heading, (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)
    for index, sign in enumerate(shown):
        top = 50 + index * 88
        patch = crops.get(sign.track_id)
        if patch is not None:
            frame[top:top + 76, 20:96] = patch
        codes = sign.conflict_codes or (sign.code,)
        code = (
            f"{sign.reviewed_code} [MANUAL]" if sign.reviewed_code else
            "/".join(codes) if len(codes) > 1 else
            "P.127 ?" if sign.code == "P.127" else sign.code
        )
        ids = "/".join(str(track_id) for track_id in sign.related_track_ids)
        ids = ids or str(sign.track_id)
        cv2.putText(frame, f"ID {ids}  {code}", (106, top + 27),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.44 if sign.conflict_codes or sign.reviewed_code else 0.55,
                    (255, 255, 255), 2, cv2.LINE_AA)
        wrong_codes = sorted({value for value in codes if value != sign.reviewed_code})
        status = (
            f"{'/'.join(wrong_codes)} FP / NO ACTION"
            if sign.reviewed_code and wrong_codes else
            "MANUAL LABEL - NO ACTION" if sign.reviewed_code else
            "CONFLICT - NO ACTION" if sign.conflict_codes else
            "LIVE" if sign.observed else f"HELD {sign.age_samples}"
        )
        cv2.putText(frame, status, (106, top + 54),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                    (0, 180, 255) if sign.conflict_codes or sign.reviewed_code else
                    (80, 255, 80) if sign.observed else (255, 220, 0), 1, cv2.LINE_AA)
    return True


def render_temporal_overlay_video(
    base_video: bytes | Path, source_video: bytes | Path,
    tracked_rows: list[dict[str, Any]], *, step: int, fps: float,
    width: int, height: int, expected_frames: int,
    scene_break_frames: tuple[int, ...] = (), draw_observed_ids: bool = False,
    max_missing_samples: int = MAX_MISSING_SAMPLES,
    clip_reviews: tuple[ClipReview, ...] = (),
) -> tuple[bytes, dict[str, int]]:
    """Add a top-left sign crop panel and bounded held boxes to an annotated MP4."""
    states = display_timeline(
        tracked_rows, expected_frames=expected_frames, step=step,
        width=width, height=height, scene_break_frames=scene_break_frames,
        max_missing_samples=max_missing_samples, clip_reviews=clip_reviews,
    )
    if not any(states):
        unchanged = base_video if isinstance(base_video, bytes) else base_video.read_bytes()
        return unchanged, {"held_box_frames": 0, "panel_frames": 0}
    with tempfile.TemporaryDirectory(prefix="cpv301_review2_temporal_r2_") as temporary:
        folder = Path(temporary)
        base_path = base_video if isinstance(base_video, Path) else folder / "base.mp4"
        source_path = source_video if isinstance(source_video, Path) else folder / "source.mp4"
        if isinstance(base_video, bytes):
            base_path.write_bytes(base_video)
        if isinstance(source_video, bytes):
            source_path.write_bytes(source_video)
        output_path = folder / "output.mp4"
        base = cv2.VideoCapture(str(base_path))
        source = cv2.VideoCapture(str(source_path))
        writer = cv2.VideoWriter(
            str(output_path), cv2.VideoWriter_fourcc(*"avc1"), fps, (width, height)
        )
        if not base.isOpened() or not source.isOpened() or not writer.isOpened():
            base.release()
            source.release()
            writer.release()
            raise RuntimeError("Cannot open temporal video inputs or H.264 writer")
        thumbnails: dict[int, np.ndarray] = {}
        held_count = 0
        panel_count = 0
        source_index = 0
        try:
            for sample, signs in enumerate(states):
                ok, frame = base.read()
                if not ok or frame.shape[:2] != (height, width):
                    raise RuntimeError("Annotated video differs from sampled grid")
                source_frame = None
                while source_index <= sample * step:
                    source_ok, source_frame = source.read()
                    if not source_ok or source_frame.shape[:2] != (height, width):
                        raise RuntimeError("Source video differs from sampled grid")
                    source_index += 1
                assert source_frame is not None
                if sample * step in scene_break_frames:
                    thumbnails.clear()
                for sign in signs:
                    if sign.observed:
                        patch = _crop(source_frame, sign.box)
                        if patch is not None:
                            thumbnails[sign.track_id] = patch
                        if draw_observed_ids:
                            x, y = round(sign.box[0]), max(20, round(sign.box[1]) - 8)
                            ids = sign.related_track_ids or (sign.track_id,)
                            text = "ID " + "/".join(str(track_id) for track_id in ids)
                            cv2.putText(frame, text, (x, y),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255),
                                        2, cv2.LINE_AA)
                    else:
                        _dashed_box(frame, sign.box)
                        held_count += 1
                if signs:
                    panel_count += int(_panel(frame, signs, thumbnails))
                writer.write(frame)
            if base.read()[0]:
                raise RuntimeError("Annotated video has extra frames")
        finally:
            base.release()
            source.release()
            writer.release()
        check = cv2.VideoCapture(str(output_path))
        decoded = 0
        try:
            while check.isOpened() and check.read()[0]:
                decoded += 1
        finally:
            check.release()
        if decoded != expected_frames:
            raise RuntimeError("Temporal video failed frame count readback")
        return output_path.read_bytes(), {
            "held_box_frames": held_count, "panel_frames": panel_count,
        }
