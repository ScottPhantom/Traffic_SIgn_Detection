import math
import sys
from pathlib import Path

import numpy as np
import pytest

from cpv301_autodrive.temporal_threshold import (
    CLOSED,
    CONFIRMED,
    DROP_BELOW_FLOOR,
    DROP_TENTATIVE,
    PRIMARY,
    Candidate,
    SequenceFrame,
    TemporalParams,
    accumulated_score,
    run_sequence,
)

ROOT = Path(__file__).resolve().parents[1]


def _box(x: float, y: float = 100.0, size: float = 40.0) -> tuple[float, float, float, float]:
    return (x, y, x + size, y + size)


def _seq(per_frame: list[list[Candidate]]) -> list[SequenceFrame]:
    return [SequenceFrame(f"{i:04d}", tuple(c)) for i, c in enumerate(per_frame)]


def test_primary_parameters_are_the_preregistered_ones():
    assert (PRIMARY.enter, PRIMARY.keep, PRIMARY.window, PRIMARY.max_miss) == (0.35, 0.15, 5, 2)
    assert (PRIMARY.link_iou, PRIMARY.predict_motion) == (0.30, True)


def test_single_frame_score_is_unchanged_by_accumulation():
    assert math.isclose(accumulated_score([0.3], 0.15), 0.3, rel_tol=1e-9)
    assert accumulated_score([0.2, 0.2, 0.2, 0.2], 0.15) > 0.35 > accumulated_score([0.2] * 3, 0.15)


def test_one_frame_false_positive_below_enter_is_never_emitted():
    frames = _seq([[], [], [Candidate(48, 0.34, _box(500))], [], []])
    result = run_sequence(frames)
    decision = result.decisions[2][0]
    assert not decision.emitted and decision.reason == DROP_TENTATIVE
    assert all(not d.emitted for frame in result.decisions for d in frame)
    assert result.tracks[0].state == CLOSED and result.tracks[0].confirmed_frame is None


def test_persistent_sign_oscillating_around_020_is_kept():
    scores = [0.21, 0.19, 0.22, 0.18, 0.21, 0.20, 0.19, 0.22]
    frames = _seq([[Candidate(10, s, _box(300 + 3 * i))] for i, s in enumerate(scores)])
    result = run_sequence(frames)
    emitted = [bool(result.emitted(i)) for i in range(len(scores))]
    assert emitted[:2] == [False, False]  # evidence still accumulating
    assert all(emitted[2:])
    assert len(result.tracks) == 1 and result.tracks[0].state == CONFIRMED
    # fixed 0.20 would drop the 0.19/0.18 frames
    assert sum(s >= 0.20 for s in scores[4:]) < sum(emitted[4:])


def test_flipping_label_resolves_to_weighted_majority():
    pattern = [(10, 0.6), (11, 0.4), (10, 0.6), (11, 0.4), (10, 0.6), (11, 0.4)]
    frames = _seq([[Candidate(c, s, _box(300 + 2 * i))] for i, (c, s) in enumerate(pattern)])
    result = run_sequence(frames)
    labels = {d.label for i in range(len(pattern)) for d in result.emitted(i)}
    assert labels == {10}
    assert result.tracks[0].label_switches == 0
    assert len(result.tracks) == 1


def test_two_missed_frames_close_the_track_and_one_miss_does_not():
    one_gap = _seq([[Candidate(10, 0.5, _box(300))], [], [Candidate(10, 0.5, _box(302))]])
    assert len(run_sequence(one_gap).tracks) == 1
    two_gap = _seq(
        [
            [Candidate(10, 0.5, _box(300))],
            [],
            [],
            [Candidate(10, 0.5, _box(302))],
        ]
    )
    result = run_sequence(two_gap)
    assert [t.state for t in result.tracks] == [CLOSED, CONFIRMED]


def test_below_floor_candidates_are_reported_and_raw_input_unchanged():
    candidate = Candidate(10, 0.05, _box(300))
    frames = _seq([[candidate]])
    result = run_sequence(frames)
    assert result.decisions[0][0].reason == DROP_BELOW_FLOOR
    assert result.decisions[0][0].candidate is candidate
    assert frames[0].candidates == (candidate,)


def test_invalid_parameters_are_rejected():
    with pytest.raises(ValueError):
        TemporalParams(enter=0.1, keep=0.2)
    with pytest.raises(ValueError):
        run_sequence([SequenceFrame("a", ()), SequenceFrame("a", ())])


def test_baseline_fixed_020_reproduces_pinned_d1_validation():
    sys.path.insert(0, str(ROOT / "detector"))
    try:
        from m1 import dynamic_threshold_r2_r1 as inputs
        from m1.metrics import match, operating_point

        frames, _pins = inputs.load_frames(ROOT)
    except (FileNotFoundError, RuntimeError) as error:  # pinned private artifacts absent
        pytest.skip(f"pinned D1 validation inputs unavailable: {error}")
    point = operating_point(frames, 0.20)
    correct = sum(int(match(frame, 0.20, class_aware=True)[0].sum()) for frame in frames)
    assert (point.true_positives, point.false_positives, correct) == (547, 150, 457)
    assert point.ground_truth == 624 and len(frames) == 376
    assert np.isclose(point.agnostic_recall, 0.8766, atol=1e-4)
    assert np.isclose(point.fp_per_image, 0.3989, atol=1e-4)
