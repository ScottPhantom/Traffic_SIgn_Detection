"""Experimental Temporal DT R1 switch: default off, display-only, no behavior."""

import cv2
import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from cpv301_autodrive import review2_front_demo_r1 as front
from cpv301_autodrive import review2_temporal_dt_r1 as tdt
from cpv301_autodrive.detector_d1_r3 import Detection, SignClass
from cpv301_autodrive.review2_upload_video_r1 import process_uploaded_video
from cpv301_autodrive.temporal_threshold import Candidate

SIGN = SignClass(10, "10", "P.130", "Mock")
NOISE = SignClass(48, "48", "W.224", "Mock")


class PoolDetector:
    """Returns a strong sign plus a weak box; honours the requested floor like D1."""

    def __init__(self):
        self.calls = []

    def detect(self, _image, *, conf):
        self.calls.append(conf)
        pool = [
            Detection(SIGN, 0.9, (100, 100, 140, 140)),
            Detection(NOISE, 0.05, (300, 50, 330, 80)),
        ]
        return [d for d in pool if d.confidence >= conf]


def _clip(tmp_path, frames=6):
    path = tmp_path / "clip.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"avc1"), 10, (640, 360))
    assert writer.isOpened()
    for _ in range(frames):
        writer.write(np.zeros((360, 640, 3), dtype=np.uint8))
    writer.release()
    return path


def test_upload_switch_off_keeps_fixed_pipeline_and_on_only_adds_display_pool(tmp_path):
    path = _clip(tmp_path)
    off_detector, on_detector = PoolDetector(), PoolDetector()
    off = process_uploaded_video(path.read_bytes(), path.name, detector=off_detector)
    on = process_uploaded_video(
        path.read_bytes(), path.name, detector=on_detector, temporal_candidates=True
    )
    assert set(off_detector.calls) == {0.20}
    assert set(on_detector.calls) == {0.001}
    assert off.temporal_candidates == ()
    assert "temporal_dt_r1_display" not in off.manifest
    assert (on.video, on.csv_text, on.tracks_csv_text, on.events_csv_text) == (
        off.video, off.csv_text, off.tracks_csv_text, off.events_csv_text
    )
    extra = {k: v for k, v in on.manifest.items() if k != "temporal_dt_r1_display"}
    assert extra == off.manifest
    assert on.manifest["temporal_dt_r1_display"]["behavior_simulation_disabled"] is True
    assert sum(len(f.candidates) for f in on.temporal_candidates) == 2 * len(
        on.temporal_candidates
    )


def test_cascade_cannot_request_temporal_candidates(tmp_path):
    path = _clip(tmp_path, frames=2)
    with pytest.raises(ValueError, match="YOLO11s-54"):
        process_uploaded_video(
            path.read_bytes(), path.name, detector=PoolDetector(),
            architecture="cascade_b0_r1", temporal_candidates=True,
        )


def test_compare_drops_single_frame_noise_and_keeps_persistent_sign():
    frames = [
        tdt.FrameCandidates(2 * i, (Candidate(10, 0.9, (100 + i, 100, 140 + i, 140)),))
        for i in range(5)
    ]
    frames[2] = tdt.FrameCandidates(
        4, frames[2].candidates + (Candidate(48, 0.3, (400, 50, 430, 80)),)
    )
    summary = tdt.compare(frames, step=2, source_fps=10)
    assert summary["fixed"] == {"boxes": 6, "tracks": 2, "label_switches": 0}
    assert summary["temporal"] == {"boxes": 5, "tracks": 1, "label_switches": 0}
    assert summary["reasons"]["tentative_evidence_below_enter"] == 1
    assert {row["giữ/bỏ"] for row in summary["table"]} == {"GIỮ", "BỎ"}


def test_pinned_mini_candidates_load_when_present():
    if not tdt.MINI_CANDIDATES.is_file():
        pytest.skip("pinned Mini conf-0.001 candidates are local-only")
    frames = tdt.load_mini_candidates()
    assert len(frames) == 103
    assert sum(len(f.candidates) for f in frames) == 246
    assert tdt.compare(frames, step=2, source_fps=10)["fixed"]["boxes"] == 54


def _front_app(monkeypatch, state=None) -> AppTest:
    if not front.OVERLAY_VIDEO.is_file():
        pytest.skip("local Mini demo clip absent")
    monkeypatch.setattr(front, "_is_local_preview_url", lambda _: True)
    monkeypatch.setattr(
        front, "_temporal_clear_preview",
        lambda *_args: (
            front.OVERLAY_VIDEO.read_bytes(), front.sha256_file(front.OVERLAY_VIDEO),
            {"panel_frames": 1, "held_box_frames": 0},
        ),
    )
    at = AppTest.from_string(
        "from cpv301_autodrive.review2_front_demo_r1 import render_review2_front_demo\n"
        "render_review2_front_demo()"
    )
    for key, value in (state or {}).items():
        at.session_state[key] = value
    return at.run(timeout=60)


def _has_note(at) -> bool:
    return any(tdt.NOTE in item.value for item in at.warning)


def test_precomputed_switch_defaults_off_and_shows_nothing_new(monkeypatch):
    at = _front_app(monkeypatch)
    assert not at.exception
    toggle = at.toggle(key=tdt.PRECOMPUTED_TOGGLE_KEY)
    assert toggle.value is False and toggle.label == tdt.TOGGLE_LABEL
    assert at.toggle(key=tdt.UPLOAD_TOGGLE_KEY).value is False
    assert not _has_note(at)
    assert len(at.get("video")) == 2


def test_precomputed_switch_on_shows_comparison_and_disables_behavior(monkeypatch):
    if not tdt.MINI_CANDIDATES.is_file():
        pytest.skip("pinned Mini conf-0.001 candidates are local-only")
    at = _front_app(monkeypatch)
    at.toggle(key=tdt.PRECOMPUTED_TOGGLE_KEY).set_value(True).run(timeout=60)
    assert not at.exception
    assert _has_note(at)
    labels = [metric.label for metric in at.metric]
    assert labels.count("Box") == 2 and labels.count("Lần đổi nhãn") == 2
    assert any(tdt.BEHAVIOR_NOTE in item.value for item in at.caption)
    assert len(at.get("video")) == 2


@pytest.mark.parametrize("stale", ["on", 1, None, ["x"]])
def test_stale_session_values_do_not_crash(monkeypatch, stale):
    at = _front_app(
        monkeypatch,
        {tdt.PRECOMPUTED_TOGGLE_KEY: stale, tdt.UPLOAD_TOGGLE_KEY: stale},
    )
    assert not at.exception
    assert at.toggle(key=tdt.PRECOMPUTED_TOGGLE_KEY).value is False
    assert not _has_note(at)


def test_disabled_behavior_reason_is_temporal_not_cascade():
    from datetime import timedelta

    from cpv301_autodrive.review2_video_seek_r1 import (
        CASCADE_DISABLED_REASON,
        EventSelection,
        selected_event_outcome,
    )

    event = {"stable_code": "P.130", "stable_name_vi": "Mock", "track_id": 5,
             "vehicle_action": "none", "road_applicability": "unverified",
             "simulation_reason": "Nếu biển áp dụng cho làn xe: mock."}
    selection = EventSelection(timedelta(0), event)
    _, off = selected_event_outcome(selection, behavior_enabled=True,
                                    disabled_reason=tdt.BEHAVIOR_DISABLED_REASON)
    _, on = selected_event_outcome(selection, behavior_enabled=False,
                                   disabled_reason=tdt.BEHAVIOR_DISABLED_REASON)
    _, cascade = selected_event_outcome(selection, behavior_enabled=False)
    assert off.startswith("Nếu biển áp dụng")
    assert on == tdt.BEHAVIOR_DISABLED_REASON and "Cascade" not in on
    assert cascade == CASCADE_DISABLED_REASON


class GappedSign:
    """A sign on sampled calls 0, 1 and 4; absent on 2 and 3 (two missed samples)."""

    def __init__(self):
        self.calls = 0

    def detect(self, _image, *, conf):
        index, self.calls = self.calls, self.calls + 1
        return [Detection(SIGN, 0.9, (100, 100, 140, 140))] if index in (0, 1, 4) else []


def _clip_fps(tmp_path, fps, frames):
    path = tmp_path / f"clip_{fps}.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"avc1"), fps, (640, 360))
    assert writer.isOpened()
    for _ in range(frames):
        writer.write(np.zeros((360, 640, 3), dtype=np.uint8))
    writer.release()
    return path


def test_hold_matches_app_formula_for_any_fps():
    assert tdt.hold_samples(10, 2) == 2
    assert tdt.hold_samples(30, 6) == 2  # the old 10-fps assumption gave 1
    assert tdt.hold_samples(60, 12) == 2
    assert tdt.hold_samples(25, 5) == 2
    with pytest.raises(ValueError):
        tdt.hold_samples(0, 2)


def test_30fps_before_tracks_match_the_app_track_csv(tmp_path):
    import csv
    import io

    path = _clip_fps(tmp_path, 30, 30)
    result = process_uploaded_video(
        path.read_bytes(), path.name, detector=GappedSign(), temporal_candidates=True
    )
    manifest = result.manifest
    assert (manifest["source_fps_nominal"], manifest["sample_every_n_frames"]) == (30, 6)
    summary = tdt.compare(
        result.temporal_candidates, step=manifest["sample_every_n_frames"],
        source_fps=manifest["source_fps_nominal"],
        scene_breaks=manifest["scene_break_source_frames"],
    )
    assert summary["hold_samples"] == manifest["track_hold_max_samples"] == 2
    app_tracks = {
        row["track_id"] for row in csv.DictReader(io.StringIO(result.tracks_csv_text))
    }
    assert summary["fixed"]["tracks"] == len(app_tracks) == 1
    assert summary["fixed"]["boxes"] == manifest["prediction_rows"] == 3


def _upload_app(state) -> AppTest:
    at = AppTest.from_string(
        "from cpv301_autodrive.review2_upload_video_r1 import render_upload_demo\n"
        "render_upload_demo()"
    )
    for key, value in state.items():
        at.session_state[key] = value
    return at.run(timeout=60)


def test_cascade_with_stale_true_renders_switch_off_and_disabled(monkeypatch):
    from cpv301_autodrive import review2_upload_video_r1 as upload

    monkeypatch.setattr(upload, "cascade_weights_available", lambda: True)
    at = _upload_app({
        "review2_video_architecture": "cascade_b0_r1", tdt.UPLOAD_TOGGLE_KEY: True,
    })
    assert not at.exception
    toggle = at.toggle(key=tdt.UPLOAD_TOGGLE_KEY)
    assert toggle.disabled is True and toggle.value is False
    assert at.session_state[tdt.UPLOAD_TOGGLE_KEY] is False
    assert not at.warning or not any("Session State" in w.value for w in at.warning)


def test_switching_d1_on_then_cascade_turns_switch_off_and_back_stays_off(monkeypatch):
    from cpv301_autodrive import review2_upload_video_r1 as upload

    monkeypatch.setattr(upload, "cascade_weights_available", lambda: True)
    at = _upload_app({})
    at.toggle(key=tdt.UPLOAD_TOGGLE_KEY).set_value(True).run(timeout=60)
    assert at.toggle(key=tdt.UPLOAD_TOGGLE_KEY).value is True
    at.selectbox(key="review2_video_architecture").select("cascade_b0_r1").run(timeout=60)
    assert not at.exception
    toggle = at.toggle(key=tdt.UPLOAD_TOGGLE_KEY)
    assert (toggle.disabled, toggle.value) == (True, False)
    at.selectbox(key="review2_video_architecture").select("d1_54").run(timeout=60)
    toggle = at.toggle(key=tdt.UPLOAD_TOGGLE_KEY)
    assert (toggle.disabled, toggle.value) == (False, False)
