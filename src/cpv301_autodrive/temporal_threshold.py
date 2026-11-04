"""Temporal dynamic threshold R1: hysteresis plus per-track evidence accumulation.

Offline, pure Python. Association is delegated unchanged to the Review 2 R1
linker (R12 settings: motion-aware, IoU 0.30). Raw candidates are never
modified; every input candidate receives one decision with a reason. This is
a validation experiment, not an app feature, a calibrated OOD gate or a
vehicle-control signal.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

from cpv301_autodrive.review2_temporal_r1 import track_prediction_rows

TENTATIVE = "TENTATIVE"
CONFIRMED = "CONFIRMED"
CLOSED = "CLOSED"

KEPT_CONFIRMED = "kept_confirmed_track"
DROP_BELOW_FLOOR = "below_keep_floor"
DROP_INVALID = "invalid_box"
DROP_TENTATIVE = "tentative_evidence_below_enter"
DROP_DUPLICATE = "same_frame_duplicate_in_track"

_EPS = 1e-6


@dataclass(frozen=True)
class TemporalParams:
    enter: float = 0.35
    keep: float = 0.15
    window: int = 5
    max_miss: int = 2
    link_iou: float = 0.30
    predict_motion: bool = True

    def __post_init__(self) -> None:
        if not 0 < self.keep <= self.enter < 1:
            raise ValueError("thresholds must satisfy 0 < keep <= enter < 1")
        if self.window < 1 or self.max_miss < 1 or not 0 < self.link_iou <= 1:
            raise ValueError("window, max_miss and link_iou must be positive")


PRIMARY = TemporalParams()


@dataclass(frozen=True)
class Candidate:
    class_id: int
    score: float
    box: tuple[float, float, float, float]  # xyxy pixels


@dataclass(frozen=True)
class SequenceFrame:
    key: str  # stem or timestamp, unique within the sequence
    candidates: tuple[Candidate, ...]


@dataclass(frozen=True)
class Decision:
    frame_index: int
    candidate_index: int
    candidate: Candidate
    emitted: bool
    reason: str
    track_id: int | None = None
    state: str | None = None
    label: int | None = None
    track_score: float | None = None


@dataclass
class TrackSummary:
    track_id: int
    first_frame: int
    last_frame: int
    state: str = TENTATIVE
    confirmed_frame: int | None = None
    label: int | None = None
    label_switches: int = 0
    emitted_frames: int = 0
    observed_frames: int = 0


@dataclass(frozen=True)
class SequenceResult:
    decisions: tuple[tuple[Decision, ...], ...]  # per frame, in input candidate order
    tracks: tuple[TrackSummary, ...]

    def emitted(self, frame_index: int) -> tuple[Decision, ...]:
        return tuple(item for item in self.decisions[frame_index] if item.emitted)


def _logit(p: float) -> float:
    p = min(max(p, _EPS), 1 - _EPS)
    return math.log(p / (1 - p))


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def accumulated_score(scores: Sequence[float], keep: float) -> float:
    """Sum log-odds relative to ``keep``; one observation returns its own score."""
    base = _logit(keep)
    return _sigmoid(base + sum(_logit(s) - base for s in scores))


@dataclass
class _Live:
    summary: TrackSummary
    observed: dict[int, float] = field(default_factory=dict)
    class_mass: dict[int, float] = field(default_factory=dict)
    misses: int = 0
    last_emitted_label: int | None = None


def _valid(candidate: Candidate) -> bool:
    values = (*candidate.box, candidate.score)
    x1, y1, x2, y2 = candidate.box
    return (
        all(math.isfinite(v) for v in values) and 0 <= candidate.score <= 1 and x2 > x1 and y2 > y1
    )


def run_sequence(
    frames: Sequence[SequenceFrame], params: TemporalParams = PRIMARY
) -> SequenceResult:
    """Apply the temporal threshold to one ordered sequence (no scene cuts inside)."""
    if len({frame.key for frame in frames}) != len(frames):
        raise ValueError("frame keys must be unique within a sequence")
    pending: dict[tuple[int, int], Decision] = {}
    rows = []
    for t, frame in enumerate(frames):
        for j, candidate in enumerate(frame.candidates):
            if not _valid(candidate):
                pending[t, j] = Decision(t, j, candidate, False, DROP_INVALID)
            elif candidate.score < params.keep:
                pending[t, j] = Decision(t, j, candidate, False, DROP_BELOW_FLOOR)
            else:
                x1, y1, x2, y2 = candidate.box
                rows.append(
                    {
                        "source_frame": t,
                        "time_ms_nominal": t,
                        "code": str(candidate.class_id),
                        "name_vi": "",
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "_candidate": j,
                    }
                )
    linked, _events = track_prediction_rows(
        rows,
        sample_step=1,
        iou_min=params.link_iou,
        max_missing_samples=params.max_miss - 1,
        predict_motion=params.predict_motion,
    )
    by_frame: dict[int, list[dict]] = {}
    for row in linked:
        by_frame.setdefault(int(row["source_frame"]), []).append(row)

    live: dict[int, _Live] = {}  # linker track id -> live temporal track
    summaries: list[TrackSummary] = []
    for t, frame in enumerate(frames):
        current = by_frame.get(t, [])
        observed_links = {int(row["track_id"]) for row in current}
        for link_id in list(live):
            if link_id in observed_links:
                continue
            track = live[link_id]
            track.misses += 1
            if track.misses >= params.max_miss:
                track.summary.state = CLOSED
                del live[link_id]
        for row in current:
            j = int(row["_candidate"])
            candidate = frame.candidates[j]
            link_id = int(row["track_id"])
            if link_id not in live:
                summary = TrackSummary(len(summaries) + 1, t, t)
                summaries.append(summary)
                live[link_id] = _Live(summary)
            track = live[link_id]
            if row["same_frame_duplicate"]:
                pending[t, j] = Decision(
                    t,
                    j,
                    candidate,
                    False,
                    DROP_DUPLICATE,
                    track.summary.track_id,
                    track.summary.state,
                )
                continue
            track.misses = 0
            track.observed[t] = candidate.score
            track.class_mass[candidate.class_id] = (
                track.class_mass.get(candidate.class_id, 0.0) + candidate.score
            )
            summary = track.summary
            summary.last_frame = t
            summary.observed_frames += 1
            window = [s for f, s in track.observed.items() if f > t - params.window]
            score = accumulated_score(window, params.keep)
            if summary.state == TENTATIVE and score >= params.enter:
                summary.state = CONFIRMED
                summary.confirmed_frame = t
            label = min(track.class_mass, key=lambda c: (-track.class_mass[c], c))
            summary.label = label
            if summary.state == CONFIRMED and score >= params.keep:
                if track.last_emitted_label is not None and label != track.last_emitted_label:
                    summary.label_switches += 1
                track.last_emitted_label = label
                summary.emitted_frames += 1
                pending[t, j] = Decision(
                    t,
                    j,
                    candidate,
                    True,
                    KEPT_CONFIRMED,
                    summary.track_id,
                    CONFIRMED,
                    label,
                    score,
                )
            else:
                pending[t, j] = Decision(
                    t,
                    j,
                    candidate,
                    False,
                    DROP_TENTATIVE,
                    summary.track_id,
                    summary.state,
                    label,
                    score,
                )
    decisions = tuple(
        tuple(pending[t, j] for j in range(len(frame.candidates))) for t, frame in enumerate(frames)
    )
    return SequenceResult(decisions, tuple(summaries))
