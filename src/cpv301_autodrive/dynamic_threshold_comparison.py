"""Explain two postprocessing policies over the same detector proposals.

This module only presents decisions made by the shared Dynamic Threshold engine.
It does not select a policy, score predictions against ground truth, or run YOLO.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from cpv301_autodrive.dynamic_threshold import (
    Candidate,
    PolicyResult,
    ThresholdPolicy,
    apply_policy,
)

_VALIDATION_RESULT = (
    Path(__file__).resolve().parents[2]
    / "docs/review/generated/dynamic_threshold_product_r3_val.json"
)
_VALIDATION_SHA256 = "e18b0750b3c230418d865160ad1d2c38a933fb87e7f521ba713b08b8b96f04da"
_VALIDATION_SCOPE = (
    "D1 validation only; pipeline postprocessing, not YOLO weight accuracy"
)


@dataclass(frozen=True)
class Comparison:
    proposals: tuple[Candidate, ...]
    fixed: PolicyResult
    dynamic: PolicyResult


def compare(
    proposals: tuple[Candidate, ...],
    fixed_conf: float,
    dynamic_policy: ThresholdPolicy,
    *,
    checkpoint_sha256: str | None = None,
    class_map_sha256: str | None = None,
) -> Comparison:
    """Apply both policies to one immutable, post-NMS proposal sequence."""
    fixed_policy = ThresholdPolicy("Ngưỡng cố định", fixed_conf)
    fixed = apply_policy(proposals, fixed_policy)
    dynamic = apply_policy(
        proposals,
        dynamic_policy,
        checkpoint_sha256=checkpoint_sha256,
        class_map_sha256=class_map_sha256,
    )
    return Comparison(proposals, fixed, dynamic)


def decision_rows(comparison: Comparison, labels: list[str]) -> list[dict[str, object]]:
    """Give every candidate a stable ID and the reason for each branch's decision."""

    def reason(index: int, result: PolicyResult) -> str:
        if index in result.below_threshold:
            return "Loại: dưới ngưỡng"
        if index in result.duplicate_suppressed:
            return "Loại: box trùng theo policy"
        return "Giữ"

    return [
        {
            "Box": index + 1,
            "Mã biển": labels[candidate.class_id],
            "Điểm": round(candidate.score, 4),
            "Ngưỡng cố định": reason(index, comparison.fixed),
            "Dynamic Threshold": reason(index, comparison.dynamic),
            "Khung (x1, y1, x2, y2)": ", ".join(f"{value:.0f}" for value in candidate.box),
        }
        for index, candidate in enumerate(comparison.proposals)
    ]


def draw_decisions(
    image: Image.Image,
    comparison: Comparison,
    result: PolicyResult,
    highlighted_index: int | None = None,
) -> Image.Image:
    """Solid green means kept; dashed amber means filtered after YOLO/NMS."""
    canvas = image.convert("RGB").copy()
    draw = ImageDraw.Draw(canvas)
    removed = set(result.below_threshold) | set(result.duplicate_suppressed)
    for index, candidate in enumerate(comparison.proposals):
        x1, y1, x2, y2 = candidate.box
        bounds = (round(x1), round(y1), round(x2), round(y2))
        width = 5 if index == highlighted_index else 3
        if index in removed:
            for offset in range(0, 4):
                # Pillow's dashed rectangle support differs by version; draw short segments.
                for start in range(bounds[0], bounds[2], 18):
                    for y in (bounds[1] + offset, bounds[3] - offset):
                        draw.line((start, y, min(start + 9, bounds[2]), y), fill="#b4541c")
                for start in range(bounds[1], bounds[3], 18):
                    for x in (bounds[0] + offset, bounds[2] - offset):
                        draw.line((x, start, x, min(start + 9, bounds[3])), fill="#b4541c")
        else:
            draw.rectangle(bounds, outline="#176153", width=width)
        draw.text((bounds[0], max(0, bounds[1] - 12)), f"#{index + 1}", fill="#111827")
    return canvas


def load_validation_result(
    *, checkpoint_sha256: str, class_map_sha256: str
) -> dict[str, object] | None:
    """Return the QA-pinned validation result only for the exact D1 model/map."""
    if not _VALIDATION_RESULT.is_file():
        return None
    content = _VALIDATION_RESULT.read_bytes()
    if hashlib.sha256(content).hexdigest() != _VALIDATION_SHA256:
        return None
    data = json.loads(content)
    pins = data.get("pins", {})
    if (
        data.get("sealed_test_accessed") is not False
        or data.get("scope") != _VALIDATION_SCOPE
        or checkpoint_sha256 not in pins.values()
        or class_map_sha256 not in pins.values()
    ):
        return None
    return data
