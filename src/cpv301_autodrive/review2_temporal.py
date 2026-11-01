"""Deterministic, review-only association of front-camera sign predictions.

This heuristic groups nearby boxes across sampled frames. It is not a
validated traffic-sign tracker and does not authorize vehicle actions.
"""

from __future__ import annotations

from collections import Counter, deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

IOU_MIN = 0.5
SAME_FRAME_IOU_MIN = 0.9
COINCIDENT_TRACK_IOU_MIN = 0.9
MAX_MISSING_SAMPLES = 2
VOTE_WINDOW = 5
MIN_CONFIRMATIONS = 2


def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    left = max(a[0], b[0])
    top = max(a[1], b[1])
    right = min(a[2], b[2])
    bottom = min(a[3], b[3])
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - intersection
    return intersection / union if union > 0 else 0.0


def coincident_conflicting_track_ids(
    tracked_rows: list[dict[str, Any]], *, iou_min: float = COINCIDENT_TRACK_IOU_MIN,
) -> set[int]:
    """Find track IDs assigned different labels to nearly identical same-frame boxes.

    This is an abstention signal for the video demo, not a relabeling or an
    accuracy claim. Raw predictions and track IDs are left intact.
    """
    if not 0 < iou_min <= 1:
        raise ValueError("Invalid coincident-track IoU")
    by_frame: dict[int, list[dict[str, Any]]] = {}
    for row in tracked_rows:
        if row.get("same_frame_duplicate") in (True, "True", "true", "1", 1):
            continue
        by_frame.setdefault(int(row["source_frame"]), []).append(row)
    conflicted: set[int] = set()
    for rows in by_frame.values():
        for index, first in enumerate(rows):
            first_label = (str(first["code"]), str(first.get("name_vi", "")))
            first_box = tuple(float(first[key]) for key in ("x1", "y1", "x2", "y2"))
            for second in rows[index + 1:]:
                if int(first["track_id"]) == int(second["track_id"]):
                    continue
                second_label = (str(second["code"]), str(second.get("name_vi", "")))
                if first_label == second_label:
                    continue
                second_box = tuple(float(second[key]) for key in ("x1", "y1", "x2", "y2"))
                if _iou(first_box, second_box) >= iou_min:
                    conflicted.update((int(first["track_id"]), int(second["track_id"])))
    return conflicted


@dataclass
class _Track:
    id: int
    box: tuple[float, float, float, float]
    last_sample: int
    votes: deque[tuple[str, str]] = field(default_factory=lambda: deque(maxlen=VOTE_WINDOW))
    stable_label: tuple[str, str] | None = None
    event_emitted: bool = False
    previous_box: tuple[float, float, float, float] | None = None
    previous_sample: int | None = None

    def predicted_box(self, sample: int) -> tuple[float, float, float, float]:
        """Estimate displacement from the two latest observations for association."""
        if self.previous_box is None or self.previous_sample is None:
            return self.box
        elapsed = self.last_sample - self.previous_sample
        if elapsed <= 0:
            return self.box
        age = sample - self.last_sample
        return tuple(
            current + (current - previous) * age / elapsed
            for current, previous in zip(self.box, self.previous_box, strict=True)
        )

    def update_label(self, code: str, name_vi: str) -> bool:
        self.votes.append((code, name_vi))
        counts = Counter(self.votes)
        winner, votes = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
        if votes < MIN_CONFIRMATIONS or votes <= len(self.votes) / 2:
            return False
        if self.stable_label is None and len(self.votes) >= 2 and list(self.votes)[-2:] == [
            winner,
            winner,
        ]:
            self.stable_label = winner
            return True
        if (
            self.stable_label is not None
            and winner != self.stable_label
            and votes >= 3
            and len(self.votes) >= 3
            and list(self.votes)[-3:] == [winner, winner, winner]
        ):
            self.stable_label = winner
            self.event_emitted = False
            return True
        return False


def track_prediction_rows(
    rows: list[dict[str, Any]], *, sample_step: int,
    scene_break_frames: Sequence[int] = (),
    iou_min: float = IOU_MIN,
    max_missing_samples: int = MAX_MISSING_SAMPLES,
    predict_motion: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return raw rows with track/stable labels and one event per confirmed label.

    Tracks expire after two missing sampled frames. The source rows are not
    modified. A label event means only that the heuristic saw repeated model
    predictions; it is not ground truth or a vehicle command.
    """
    if sample_step < 1:
        raise ValueError("sample_step must be positive")
    if not 0 < iou_min <= 1 or max_missing_samples < 0:
        raise ValueError("Invalid track association settings")
    if any(
        type(frame) is not int or frame < 0 or frame % sample_step
        for frame in scene_break_frames
    ) or len(set(scene_break_frames)) != len(scene_break_frames):
        raise ValueError("scene break frame does not match sample grid")
    pending_breaks = sorted(scene_break_frames)
    break_index = 0
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        frame = int(row["source_frame"])
        if frame < 0 or frame % sample_step:
            raise ValueError("prediction frame does not match sample grid")
        box = tuple(float(row[key]) for key in ("x1", "y1", "x2", "y2"))
        if len(box) != 4 or box[2] <= box[0] or box[3] <= box[1]:
            raise ValueError("prediction box is invalid")
        grouped.setdefault(frame, []).append(row)
    tracks: dict[int, _Track] = {}
    next_id = 1
    annotated: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for frame in sorted(grouped):
        while break_index < len(pending_breaks) and pending_breaks[break_index] <= frame:
            tracks.clear()
            break_index += 1
        sample = frame // sample_step
        tracks = {
            track_id: track
            for track_id, track in tracks.items()
            if sample - track.last_sample <= max_missing_samples + 1
        }
        current = grouped[frame]
        boxes = [tuple(float(row[key]) for key in ("x1", "y1", "x2", "y2")) for row in current]
        groups: list[list[int]] = []
        for index, row in enumerate(current):
            duplicate_of = next(
                (
                    group
                    for group in groups
                    if (
                        row["code"],
                        row.get("name_vi", ""),
                    ) == (
                        current[group[0]]["code"],
                        current[group[0]].get("name_vi", ""),
                    )
                    and _iou(boxes[index], boxes[group[0]]) >= SAME_FRAME_IOU_MIN
                ),
                None,
            )
            if duplicate_of is None:
                groups.append([index])
            else:
                duplicate_of.append(index)
        candidates = []
        for track in tracks.values():
            for group_index, group in enumerate(groups):
                representative = group[0]
                reference = track.predicted_box(sample) if predict_motion else track.box
                overlap = _iou(reference, boxes[representative])
                if overlap >= iou_min:
                    same_label = (
                        str(current[representative]["code"]),
                        str(current[representative].get("name_vi", "")),
                    ) in track.votes
                    candidates.append((-overlap, -int(same_label), track.id, group_index))
        assigned: dict[int, int] = {}
        used_tracks: set[int] = set()
        for _overlap, _same_label, track_id, group_index in sorted(candidates):
            if group_index not in assigned and track_id not in used_tracks:
                assigned[group_index] = track_id
                used_tracks.add(track_id)
        frame_rows: dict[int, dict[str, Any]] = {}
        for group_index, group in enumerate(groups):
            representative = group[0]
            row = current[representative]
            track_id = assigned.get(group_index)
            if track_id is None:
                track_id = next_id
                next_id += 1
                tracks[track_id] = _Track(track_id, boxes[representative], sample)
            track = tracks[track_id]
            if track.last_sample != sample:
                track.previous_box = track.box
                track.previous_sample = track.last_sample
            track.box = boxes[representative]
            track.last_sample = sample
            track.update_label(str(row["code"]), str(row.get("name_vi", "")))
            for index in group:
                frame_rows[index] = {
                    **current[index],
                    "track_id": track_id,
                    "stable_code": track.stable_label[0] if track.stable_label else "",
                    "stable_name_vi": track.stable_label[1] if track.stable_label else "",
                    "confirmed": track.stable_label is not None,
                    "same_frame_duplicate": index != representative,
                }
            if track.stable_label == (
                row["code"],
                row.get("name_vi", ""),
            ) and not track.event_emitted:
                label_votes = Counter(track.votes)[track.stable_label]
                events.append(
                    {
                        "source_frame": frame,
                        "time_ms_nominal": row["time_ms_nominal"],
                        "track_id": track_id,
                        "stable_code": track.stable_label[0],
                        "stable_name_vi": track.stable_label[1],
                        "event": "repeated_model_prediction",
                        "vehicle_action": "none",
                        "evidence": f"{label_votes}/{len(track.votes)} label votes",
                    }
                )
                track.event_emitted = True
        annotated.extend(frame_rows[index] for index in range(len(current)))
    return annotated, events
