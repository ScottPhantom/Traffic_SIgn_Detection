"""Model-independent filtering of traffic-sign proposals after inference.

The caller supplies boxes that survived the detector's input floor and NMS.
This module cannot restore proposals that the detector did not return. Policies
with class-specific behavior must be bound to the evaluated checkpoint and map.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    class_id: int
    score: float
    box: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        x1, y1, x2, y2 = self.box
        if (
            type(self.class_id) is not int
            or self.class_id < 0
            or not math.isfinite(self.score)
            or not 0 <= self.score <= 1
            or not all(math.isfinite(value) for value in self.box)
            or x2 <= x1
            or y2 <= y1
        ):
            raise ValueError("invalid candidate class, score or box")


@dataclass(frozen=True)
class DuplicateRule:
    """Remove a lower-scored overlapping box, including within one output class."""

    winner: int
    loser: int
    min_iou: float = 0.9

    def __post_init__(self) -> None:
        if (
            type(self.winner) is not int
            or type(self.loser) is not int
            or self.winner < 0
            or self.loser < 0
            or not math.isfinite(self.min_iou)
            or not 0 < self.min_iou <= 1
        ):
            raise ValueError("invalid directed duplicate rule")


@dataclass(frozen=True)
class PolicyBinding:
    checkpoint_sha256: str
    class_map_sha256: str

    def __post_init__(self) -> None:
        for digest in (self.checkpoint_sha256, self.class_map_sha256):
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError("policy binding requires lowercase SHA-256 digests")


@dataclass(frozen=True)
class ThresholdPolicy:
    name: str
    default_conf: float
    class_conf: tuple[tuple[int, float], ...] = ()
    duplicates: tuple[DuplicateRule, ...] = ()
    binding: PolicyBinding | None = None

    def __post_init__(self) -> None:
        if (
            not self.name.strip()
            or not math.isfinite(self.default_conf)
            or not 0 < self.default_conf <= 1
        ):
            raise ValueError("policy name and confidence floor are required")
        classes = [class_id for class_id, _ in self.class_conf]
        if len(classes) != len(set(classes)) or any(
            type(class_id) is not int or class_id < 0 for class_id in classes
        ):
            raise ValueError("class_conf requires distinct nonnegative integer class IDs")
        if any(not math.isfinite(conf) or not 0 < conf <= 1 for _, conf in self.class_conf):
            raise ValueError("class confidence floors must be in (0, 1]")
        if (self.class_conf or self.duplicates) and self.binding is None:
            raise ValueError("class-specific policy requires checkpoint and class-map binding")


@dataclass(frozen=True)
class PolicyResult:
    kept: tuple[Candidate, ...]
    below_threshold: tuple[int, ...]
    duplicate_suppressed: tuple[int, ...]


def candidate_input_floor(policy: ThresholdPolicy) -> float:
    """Lowest postprocessing floor; the detector may use a lower supported floor."""
    return min(policy.default_conf, *(conf for _, conf in policy.class_conf))


def _iou(a: Candidate, b: Candidate) -> float:
    ax1, ay1, ax2, ay2 = a.box
    bx1, by1, bx2, by2 = b.box
    intersection = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(
        0.0, min(ay2, by2) - max(ay1, by1)
    )
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - intersection
    return intersection / union


def apply_policy(
    candidates: Iterable[Candidate],
    policy: ThresholdPolicy,
    *,
    checkpoint_sha256: str | None = None,
    class_map_sha256: str | None = None,
) -> PolicyResult:
    """Apply confidence floors, then directed duplicate rules in source order."""
    if policy.binding is not None and (
        checkpoint_sha256 != policy.binding.checkpoint_sha256
        or class_map_sha256 != policy.binding.class_map_sha256
    ):
        raise ValueError("policy does not match this checkpoint and class map")
    source = tuple(candidates)
    if any(not isinstance(candidate, Candidate) for candidate in source):
        raise TypeError("candidates must be Candidate values")
    floors = dict(policy.class_conf)
    eligible = tuple(
        index
        for index, candidate in enumerate(source)
        if candidate.score >= floors.get(candidate.class_id, policy.default_conf)
    )
    eligible_set = set(eligible)
    below = tuple(index for index in range(len(source)) if index not in eligible_set)
    removed = tuple(
        index
        for index in eligible
        if any(
            source[index].class_id == rule.loser
            and any(
                source[winner].class_id == rule.winner
                and source[winner].score > source[index].score
                and _iou(source[winner], source[index]) >= rule.min_iou
                for winner in eligible
            )
            for rule in policy.duplicates
        )
    )
    removed_set = set(removed)
    return PolicyResult(
        kept=tuple(source[index] for index in eligible if index not in removed_set),
        below_threshold=below,
        duplicate_suppressed=removed,
    )
