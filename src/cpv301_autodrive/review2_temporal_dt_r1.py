"""Experimental Temporal DT R1 switch for the Review 2 front-camera views.

Display-only comparison of fixed 0.20 against `temporal_threshold` (locked
0.35 / 0.15 / N=5 / max_miss=2). It never changes raw predictions, the default
threshold, pinned manifests or the exported video, and it never creates a
vehicle action: the callers disable conditional behavior while it is on.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from cpv301_autodrive.detector_d1_r3 import DEFAULT_CONF, load_classes
from cpv301_autodrive.review2_temporal_r1 import track_prediction_rows
from cpv301_autodrive.temporal_threshold import (
    PRIMARY,
    Candidate,
    SequenceFrame,
    run_sequence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_CONF = 0.001
PRECOMPUTED_TOGGLE_KEY = "review2_temporal_dt_r1_precomputed"
UPLOAD_TOGGLE_KEY = "review2_temporal_dt_r1_upload"
TOGGLE_LABEL = "Ngưỡng động theo thời gian (thử nghiệm)"
NOTE = (
    "Thử nghiệm, chẩn đoán offline trên val (QA PASS), không phải nghiệm thu D-05; "
    "trên val giảm FP 150→125 nhưng mất 28 GT định vị."
)
BEHAVIOR_DISABLED_REASON = (
    "Mô phỏng hành vi tạm tắt vì công tắc Temporal DT (thử nghiệm) đang bật; "
    "không phát lệnh điều khiển xe."
)
BEHAVIOR_NOTE = (
    "Khi bật công tắc, mô phỏng hành vi có điều kiện bị tắt để Temporal DT không thể tạo "
    "thêm hành động xe; video, CSV và manifest dự đoán vẫn là ngưỡng cố định 0,20."
)
MINI_DIR = REPO_ROOT / "data/processed/temporal_threshold_r1_mini"
MINI_CANDIDATES = MINI_DIR / "ROUNDABOUT_CAM_P_F_D1_conf0001_step2.csv"
MINI_CANDIDATES_MANIFEST = MINI_DIR / "ROUNDABOUT_CAM_P_F_D1_conf0001_step2.manifest.json"
MINI_CANDIDATES_SHA256 = "67b714a7763a46afb5fa21467dcd8d6f930809b09527d5b66877104cbb9327c0"
MINI_CANDIDATES_MANIFEST_SHA256 = (
    "8145ef272917893d65b50ab9a1bec6ca7c0f14d0a59cab82d05265c8f0d80b8a"
)
MINI_SOURCE_SHA256 = "1fab75937ceba286abbc308138a814a7d9548b722184d4735b802f29d4b1f5ac"
MINI_STEP = 2


@dataclass(frozen=True)
class FrameCandidates:
    frame: int
    candidates: tuple[Candidate, ...]


def temporal_toggle(key: str, *, disabled: bool = False, help_text: str | None = None) -> bool:
    """Default-off toggle. A disabled switch, or a stale non-bool value, is forced off first."""
    if disabled or not isinstance(st.session_state.get(key, False), bool):
        st.session_state[key] = False
    value = st.toggle(TOGGLE_LABEL, key=key, disabled=disabled, help=help_text)
    return bool(value) and not disabled


def hold_samples(source_fps: float, step: int) -> int:
    """Same bounded hold as the app's R12 track CSV: 0.4 s at the sampled frame rate."""
    if not source_fps > 0 or step < 1:
        raise ValueError("fps và bước lấy mẫu phải dương")
    return max(1, round(source_fps / step * 0.4))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_mini_candidates() -> tuple[FrameCandidates, ...]:
    """Hash-checked conf-0.001 D1 candidates of the Mini clip (every second frame)."""
    if _sha256(MINI_CANDIDATES_MANIFEST) != MINI_CANDIDATES_MANIFEST_SHA256:
        raise ValueError("manifest candidate Mini khác bản đã pin")
    if _sha256(MINI_CANDIDATES) != MINI_CANDIDATES_SHA256:
        raise ValueError("CSV candidate Mini khác bản đã pin")
    manifest = json.loads(MINI_CANDIDATES_MANIFEST.read_text(encoding="utf-8"))
    if (
        manifest.get("source_sha256") != MINI_SOURCE_SHA256
        or manifest.get("sample_every_n_frames") != MINI_STEP
        or manifest.get("sealed_test_accessed") is not False
    ):
        raise ValueError("manifest candidate Mini không khớp clip hoặc seal")
    by_frame: dict[int, list[Candidate]] = {
        frame: [] for frame in range(0, manifest["source_frames_decoded"], MINI_STEP)
    }
    with MINI_CANDIDATES.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            by_frame[int(row["source_frame"])].append(
                Candidate(
                    int(row["yolo_id"]), float(row["score"]),
                    tuple(float(row[k]) for k in ("x1", "y1", "x2", "y2")),
                )
            )
    return tuple(FrameCandidates(f, tuple(c)) for f, c in sorted(by_frame.items()))


def _segments(
    frames: Sequence[FrameCandidates], scene_breaks: Sequence[int]
) -> list[list[FrameCandidates]]:
    breaks = set(scene_breaks)
    out: list[list[FrameCandidates]] = []
    for item in frames:
        if not out or item.frame in breaks:
            out.append([])
        out[-1].append(item)
    return out


def compare(
    frames: Sequence[FrameCandidates], *, step: int, source_fps: float,
    scene_breaks: Sequence[int] = (),
) -> dict:
    """Fixed 0.20 vs Temporal DT R1 on the same candidate pool (display statistics only)."""
    codes = {sign.yolo_id: sign.code for sign in load_classes()}
    hold = hold_samples(source_fps, step)
    fixed_rows = [
        {
            "source_frame": item.frame,
            "time_ms_nominal": round(item.frame / source_fps * 1000),
            "code": str(c.class_id), "name_vi": "",
            "x1": c.box[0], "y1": c.box[1], "x2": c.box[2], "y2": c.box[3],
        }
        for item in frames for c in item.candidates
        if c.score >= DEFAULT_CONF and c.box[2] > c.box[0] and c.box[3] > c.box[1]
    ]
    tracked, _ = track_prediction_rows(
        fixed_rows, sample_step=step, scene_break_frames=tuple(scene_breaks),
        iou_min=0.30, max_missing_samples=hold, predict_motion=True,
    )
    fixed_labels: dict[int, list[str]] = {}
    for row in tracked:
        if not row["same_frame_duplicate"]:
            fixed_labels.setdefault(int(row["track_id"]), []).append(row["code"])
    fixed_switches = sum(
        sum(a != b for a, b in zip(labels, labels[1:], strict=False))
        for labels in fixed_labels.values()
    )
    reasons: Counter[str] = Counter()
    table: list[dict] = []
    tracks = switches = emitted = 0
    for offset, segment in enumerate(_segments(frames, scene_breaks)):
        result = run_sequence(
            [SequenceFrame(str(item.frame), item.candidates) for item in segment], PRIMARY
        )
        tracks += sum(t.emitted_frames > 0 for t in result.tracks)
        switches += sum(t.label_switches for t in result.tracks)
        for t, item in enumerate(segment):
            for decision in result.decisions[t]:
                reasons[decision.reason] += 1
                emitted += decision.emitted
                table.append({
                    "frame": item.frame,
                    "giữ/bỏ": "GIỮ" if decision.emitted else "BỎ",
                    "nhãn_thô": codes.get(decision.candidate.class_id, "?"),
                    "điểm_thô": round(decision.candidate.score, 4),
                    "fixed_0.20": "GIỮ" if decision.candidate.score >= DEFAULT_CONF else "BỎ",
                    "lý_do_temporal": decision.reason,
                    "track": (
                        f"{offset}.{decision.track_id}" if decision.track_id is not None else ""
                    ),
                    "trạng_thái": decision.state or "",
                    "nhãn_track": (
                        codes.get(decision.label, "?") if decision.label is not None else ""
                    ),
                    "điểm_track": (
                        round(decision.track_score, 4) if decision.track_score is not None else None
                    ),
                })
    return {
        "hold_samples": hold,
        "frames": len(frames),
        "candidates": sum(len(item.candidates) for item in frames),
        "fixed": {"boxes": len(fixed_rows), "tracks": len(fixed_labels),
                  "label_switches": fixed_switches},
        "temporal": {"boxes": emitted, "tracks": tracks, "label_switches": switches},
        "reasons": dict(sorted(reasons.items())),
        "table": table,
    }


def render_comparison(summary: dict, *, source_caption: str) -> None:
    """Side-by-side counts plus a keep/drop reason table."""
    with st.container(border=True):
        st.markdown("**Temporal DT R1 · so sánh trước/sau (chỉ hiển thị)**")
        st.warning(NOTE)
        st.caption(BEHAVIOR_NOTE)
        heads = st.columns(2)
        heads[0].markdown("Trước · ngưỡng cố định 0,20")
        heads[1].markdown("Sau · Temporal DT R1 (0,35 / 0,15 / N=5 / max_miss=2)")
        rows = (("Box", "boxes"), ("Track", "tracks"), ("Lần đổi nhãn", "label_switches"))
        for label, key in rows:
            fixed, temporal = summary["fixed"][key], summary["temporal"][key]
            row = st.columns(2)
            row[0].metric(label, fixed)
            row[1].metric(label, temporal, delta=temporal - fixed, delta_color="off")
        st.caption(
            f"{source_caption} {summary['frames']} frame, {summary['candidates']} candidate "
            f"từ conf {CANDIDATE_CONF}. Lý do: "
            + ", ".join(f"{k}={v}" for k, v in summary["reasons"].items())
            + f". Track trước = liên kết R12 trên box ≥0,20 (giữ tối đa "
            f"{summary['hold_samples']} frame lấy mẫu); đổi nhãn trước = đổi nhãn thô "
            "giữa hai quan sát liên tiếp của một track. Không phải độ chính xác."
        )
        st.dataframe(
            summary["table"], hide_index=True, width="stretch",
            alt="Bảng giữ/bỏ từng candidate theo Temporal DT R1",
        )
