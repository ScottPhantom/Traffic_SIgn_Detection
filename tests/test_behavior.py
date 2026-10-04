from cpv301_autodrive.behavior import plan_behavior
from cpv301_autodrive.inference import Prediction


def make_prediction(label: str, accepted: bool = True) -> Prediction:
    return Prediction(class_id=0, label=label, confidence=0.95, accepted=accepted)


def test_stop_sign_stops_simulated_vehicle() -> None:
    command = plan_behavior(make_prediction("Stop"), cruise_speed_kmh=30)
    assert command.action == "stop"
    assert command.target_speed_kmh == 0


def test_speed_limit_updates_target_speed() -> None:
    command = plan_behavior(make_prediction("Speed limit (50km/h)"), cruise_speed_kmh=70)
    assert command.action == "set_speed_limit"
    assert command.target_speed_kmh == 50


def test_unaccepted_prediction_uses_review_mode() -> None:
    command = plan_behavior(make_prediction("Stop", accepted=False), cruise_speed_kmh=30)
    assert command.action == "review"
    assert command.target_speed_kmh == 10
