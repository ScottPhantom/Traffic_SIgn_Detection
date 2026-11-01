"""Conditional, review-only behavior explanation for stabilized video events."""

from __future__ import annotations

from typing import Any

from cpv301_autodrive.detector_d1 import Detection, SignClass, plan_vn_behavior
from cpv301_autodrive.review2_temporal import coincident_conflicting_track_ids

CRUISE_SPEED_KMH = 50
POLICY_NAME = "review2_conditional_behavior_r1"


def explain_events(
    events: list[dict[str, Any]],
    tracked_rows: list[dict[str, Any]],
    classes: list[SignClass],
    *,
    cruise_speed_kmh: int = CRUISE_SPEED_KMH,
) -> list[dict[str, Any]]:
    """Attach a hypothetical response only when a unique class passes the static gate.

    No event is dispatched to a vehicle. Road and lane applicability are
    unverified; even eligible classes produce a conditional explanation only.
    """
    if cruise_speed_kmh <= 0:
        raise ValueError("cruise_speed_kmh must be positive")
    classes_by_code: dict[str, list[SignClass]] = {}
    for sign in classes:
        classes_by_code.setdefault(sign.code, []).append(sign)
    rows_by_event: dict[tuple[int, int], dict[str, Any]] = {}
    for row in tracked_rows:
        key = (int(row["source_frame"]), int(row["track_id"]))
        if (
            row["code"] == row["stable_code"]
            and row.get("name_vi", "") == row.get("stable_name_vi", "")
            and key not in rows_by_event
        ):
            rows_by_event[key] = row
    conflicted_tracks = coincident_conflicting_track_ids(tracked_rows)
    explained: list[dict[str, Any]] = []
    for event in events:
        key = (int(event["source_frame"]), int(event["track_id"]))
        source = rows_by_event.get(key)
        if (
            source is None
            or source["code"] != event["stable_code"]
            or source.get("name_vi", "") != event.get("stable_name_vi", "")
        ):
            raise ValueError("stable event has no matching source prediction")
        matches = classes_by_code.get(str(event["stable_code"]), [])
        if len(matches) > 1 and source.get("name_vi"):
            matches = [sign for sign in matches if sign.name_vi == source["name_vi"]]
        result = {
            **event,
            "road_side_estimate": source.get(
                "side_of_road_estimate", source.get("side", "")
            ),
            "road_applicability": "unverified",
            "class_validation_status": source.get("validation_status", ""),
            "simulation_gate": "",
            "simulation_if_applicable": "",
            "target_speed_kmh_if_applicable": None,
            "simulation_reason": "",
            "vehicle_action": "none",
        }
        if int(event["track_id"]) in conflicted_tracks:
            result["simulation_gate"] = "spatial_class_conflict"
            result["simulation_reason"] = (
                "Các nhãn khác nhau cùng phủ một biển trong clip; "
                "không suy ra hành vi từ track này."
            )
        elif len(matches) != 1:
            result["simulation_gate"] = "unknown_or_ambiguous_class"
            result["simulation_reason"] = "Không ánh xạ duy nhất được mã biển đã ổn định."
        elif not matches[0].behavior_eligible:
            result["simulation_gate"] = "class_not_eligible"
            result["simulation_reason"] = (
                "Lớp thiếu kiểm chứng hoặc chưa đạt validation; chỉ hiển thị dự đoán."
            )
        else:
            box = tuple(float(source[field]) for field in ("x1", "y1", "x2", "y2"))
            detection = Detection(matches[0], float(source["score"]), box)
            command = plan_vn_behavior([detection], cruise_speed_kmh)
            result["simulation_gate"] = "conditional_on_road_applicability"
            result["simulation_if_applicable"] = command.action
            result["target_speed_kmh_if_applicable"] = command.target_speed_kmh
            result["simulation_reason"] = (
                f"Nếu biển áp dụng cho làn xe: {command.reason} "
                "Chưa xác minh biển áp dụng cho làn đang đi."
            )
        explained.append(result)
    return explained
