from pathlib import Path

import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

from cpv301_autodrive import detector_d1 as d1

APP_PATH = Path(__file__).parents[1] / "src" / "cpv301_autodrive" / "web_app.py"
HAS_WEIGHTS = d1.weights_available()
needs_weights = pytest.mark.skipif(not HAS_WEIGHTS, reason="D1 best.pt is local-only")


def _det(code: str, key: str = "0", name: str = "", conf: float = 0.9) -> d1.Detection:
    sign = d1.SignClass(yolo_id=0, key=key, code=code, name_vi=name or code)
    return d1.Detection(sign, conf, (10.0, 10.0, 60.0, 60.0))


def test_class_map_is_dense_and_keyed_by_derived_key() -> None:
    classes = d1.load_classes()
    assert len(classes) == 54
    by_key = {c.key: c for c in classes}
    assert by_key["7"].code == "P.123a" and by_key["32"].code == "P.123b"
    assert by_key["41"].name_vi.endswith("(40 km/h)")
    assert by_key["7"].verified and not by_key["1"].verified
    assert len(d1.UNVERIFIED_KEYS) == 22 and d1.UNVERIFIED_KEYS <= set(by_key)


def test_behavior_uses_most_restrictive_verified_sign() -> None:
    assert d1.plan_vn_behavior([], 50).action == "continue"
    stop = d1.plan_vn_behavior([_det("P.102", "2"), _det("P.127", "41", "Tốc độ (40 km/h)")], 50)
    assert stop.action == "stop" and stop.target_speed_kmh == 0
    limit = d1.plan_vn_behavior([_det("P.127", "41", "Tốc độ tối đa cho phép (40 km/h)")], 50)
    assert limit.action == "set_speed_limit" and limit.target_speed_kmh == 40
    warning = d1.plan_vn_behavior([_det("W.224", "0")], 50)
    assert warning.target_speed_kmh == 15 and "giảm tốc" in warning.reason
    turn = d1.plan_vn_behavior([_det("P.123a", "7")], 50)
    assert turn.steering == "straight" and "cấm rẽ trái" in turn.reason


def test_unverified_classes_never_change_the_command() -> None:
    unverified = _det("P.127", "38", "Tốc độ tối đa cho phép (50 km/h)")
    command = d1.plan_vn_behavior([unverified], 60)
    assert command.action == "continue" and command.target_speed_kmh == 60
    assert "chưa kiểm chứng" in command.reason


def test_drawing_keeps_image_size() -> None:
    image = Image.new("RGB", (320, 180), "white")
    drawn = d1.draw_detections(image, [_det("P.102", "2"), _det("P.127", "38")])
    assert drawn.size == image.size and drawn.getpixel((10, 30)) != (255, 255, 255)


def test_wrong_weights_are_refused(tmp_path) -> None:
    fake = tmp_path / "best.pt"
    fake.write_bytes(b"not the registered checkpoint")
    with pytest.raises(RuntimeError, match="differ from the registered"):
        d1.D1Detector(fake)
    with pytest.raises(FileNotFoundError):
        d1.D1Detector(tmp_path / "missing.pt")


@needs_weights
def test_d1_detects_signs_on_a_sample_frame() -> None:
    samples = d1.sample_images()
    assert samples, "validation sample frames are not materialised"
    detector = d1.D1Detector()
    frame = next(p for p in samples if p.stem == "1951")
    detections = detector.detect(Image.open(frame))
    assert any(d.sign.key == "41" for d in detections)
    assert d1.plan_vn_behavior(detections, 50).target_speed_kmh <= 40


@needs_weights
def test_demo_slide_runs_d1_by_default() -> None:
    app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
    app.switch_page("app_pages/07_demo.py").run(timeout=300)
    assert not app.exception
    assert app.segmented_control(key="demo_model").value.startswith("D1")
    labels = [metric.label for metric in app.metric]
    assert "Số biển phát hiện" in labels and "Tốc độ mục tiêu" in labels


def test_scene_places_signs_by_image_position_and_size() -> None:
    left_far = d1.Detection(d1.SignClass(0, "7", "P.123a", "x"), 0.9, (50, 100, 70, 120))
    right_near = d1.Detection(d1.SignClass(1, "41", "P.127", "x"), 0.8, (800, 100, 900, 200))
    centre = d1.Detection(d1.SignClass(2, "2", "P.102", "x"), 0.7, (470, 100, 490, 120))
    positions = d1.scene_positions([left_far, right_near, centre], 960, 540)
    assert positions[0]["x"] < positions[2]["x"] < positions[1]["x"]
    assert positions[1]["y"] > positions[0]["y"] and positions[1]["r"] > positions[0]["r"]
    rows = d1.scene_rows([left_far, right_near, centre], 960, 540)
    assert [r["Vị trí"] for r in rows] == ["bên trái", "bên phải", "bên giữa"]
    assert rows[1]["Khoảng cách (ước lượng từ cỡ khung)"] == "gần"
    svg = d1.scene_svg([left_far, right_near, centre], 960, 540, d1.plan_vn_behavior([], 30))
    assert svg.startswith("<svg") and svg.count("<circle") == 3
    assert all(f">{n}</text>" in svg for n in (1, 2, 3))


def test_same_board_twins_are_flagged() -> None:
    a = d1.Detection(d1.SignClass(0, "12", "R.415a", "x"), 0.9, (312, 149, 426, 223))
    b = d1.Detection(d1.SignClass(1, "30", "S.505a", "x"), 0.8, (312, 149, 428, 223))
    c = d1.Detection(d1.SignClass(2, "10", "P.130", "x"), 0.7, (102, 56, 135, 87))
    assert d1.same_board([a, b, c]) == {1: 0}
    notes = [row["Ghi chú"] for row in d1.scene_rows([a, b, c], 960, 540)]
    assert notes[0] == "" and "#1" in notes[1] and notes[2] == ""
