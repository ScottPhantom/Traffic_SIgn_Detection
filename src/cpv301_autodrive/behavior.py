import re
from dataclasses import dataclass

from cpv301_autodrive.inference import Prediction

_SPEED_LIMIT_PATTERN = re.compile(r"Speed limit \((\d+)km/h\)")


@dataclass(frozen=True)
class VehicleCommand:
    """A small rule-based command used by the web simulation.

    This is presentation logic for the local demo, not a safety-certified
    autonomous-driving controller.
    """

    action: str
    target_speed_kmh: int
    steering: str
    reason: str


def plan_behavior(prediction: Prediction, cruise_speed_kmh: int = 30) -> VehicleCommand:
    """Map a classifier result to a deterministic simulated vehicle command."""

    if not prediction.accepted:
        return VehicleCommand(
            action="review",
            target_speed_kmh=min(cruise_speed_kmh, 10),
            steering="straight",
            reason="Độ tin cậy dưới ngưỡng demo; giảm tốc và chờ xác nhận.",
        )

    label = prediction.label
    speed_match = _SPEED_LIMIT_PATTERN.fullmatch(label)
    if speed_match:
        limit = int(speed_match.group(1))
        return VehicleCommand(
            action="set_speed_limit",
            target_speed_kmh=min(cruise_speed_kmh, limit),
            steering="straight",
            reason=f"Mô phỏng không vượt quá giới hạn {limit} km/h.",
        )

    if label in {"Stop", "No entry", "No vehicles"}:
        return VehicleCommand(
            action="stop",
            target_speed_kmh=0,
            steering="stop",
            reason=f"Mô phỏng dừng xe khi nhận diện biển {label}.",
        )

    if label == "Yield":
        return VehicleCommand(
            action="yield",
            target_speed_kmh=min(cruise_speed_kmh, 10),
            steering="straight",
            reason="Mô phỏng giảm tốc để nhường đường.",
        )

    if label in {"Turn left ahead", "Keep left"}:
        return VehicleCommand(
            action="turn_left",
            target_speed_kmh=min(cruise_speed_kmh, 20),
            steering="left",
            reason=f"Mô phỏng chuẩn bị đi về bên trái theo biển {label}.",
        )

    if label in {"Turn right ahead", "Keep right"}:
        return VehicleCommand(
            action="turn_right",
            target_speed_kmh=min(cruise_speed_kmh, 20),
            steering="right",
            reason=f"Mô phỏng chuẩn bị đi về bên phải theo biển {label}.",
        )

    caution_labels = {
        "General caution",
        "Dangerous curve to the left",
        "Dangerous curve to the right",
        "Double curve",
        "Bumpy road",
        "Slippery road",
        "Road narrows on the right",
        "Road work",
        "Traffic signals",
        "Pedestrians",
        "Children crossing",
        "Bicycles crossing",
        "Beware of ice/snow",
        "Wild animals crossing",
    }
    if label in caution_labels:
        return VehicleCommand(
            action="slow_down",
            target_speed_kmh=min(cruise_speed_kmh, 15),
            steering="straight",
            reason=f"Mô phỏng giảm tốc vì cảnh báo: {label}.",
        )

    return VehicleCommand(
        action="continue",
        target_speed_kmh=cruise_speed_kmh,
        steering="straight",
        reason=f"Chưa có luật đặc biệt cho {label}; tiếp tục tốc độ hành trình.",
    )
