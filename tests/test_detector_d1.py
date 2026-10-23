import threading
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

from cpv301_autodrive import centercam
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
    assert limit.action == "continue" and limit.target_speed_kmh == 50
    assert "chưa đạt validation" in limit.reason
    warning = d1.plan_vn_behavior([_det("W.224", "0")], 50)
    assert warning.target_speed_kmh == 15 and "giảm tốc" in warning.reason
    turn = d1.plan_vn_behavior([_det("P.123a", "7")], 50)
    assert turn.steering == "straight" and "chưa đạt validation" in turn.reason


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
    from ultralytics.utils import checks

    assert not checks.AUTOINSTALL and not checks.ONLINE
    frame = next(p for p in samples if p.stem == "1951")
    detections = detector.detect(Image.open(frame))
    assert any(d.sign.key == "41" for d in detections)
    assert all(not d.sign.behavior_eligible for d in detections if d.sign.key == "41")


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
    places = centercam.layout([d.box for d in (left_far, right_near, centre)], 960, 540, 480)
    assert places[0].x < places[2].x < places[1].x
    assert places[1].y > places[0].y and places[1].r > places[0].r
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


def test_side_follows_the_road_vanishing_point_not_the_image_centre() -> None:
    board = d1.Detection(d1.SignClass(0, "12", "R.415a", "x"), 0.9, (312, 149, 426, 223))
    pole = d1.Detection(d1.SignClass(1, "10", "P.130", "x"), 0.8, (102, 56, 135, 87))
    centred = d1.scene_rows([board, pole], 960, 540)
    assert centred[0]["Vị trí"] == "bên trái"  # image-centre fallback
    rows = d1.scene_rows([board, pole], 960, 540, vanish_x=216.0)
    assert [r["Vị trí"] for r in rows] == ["bên phải", "bên trái"]


@needs_weights
def test_vanishing_point_puts_r415a_on_the_right_in_1231_and_1227() -> None:
    detector = d1.D1Detector()
    for stem in ("1231", "1227"):
        path = (
            next(p for p in d1.sample_images() if p.stem == stem)
            if stem == "1231"
            else (d1.SAMPLE_DIR / "1227.jpg")
        )
        image = Image.open(path)
        vanish_x = centercam.vanishing_x(image)[0]
        assert vanish_x is not None and vanish_x < 330
        detections = detector.detect(image)
        rows = d1.scene_rows(detections, image.width, image.height, vanish_x)
        sides = {r["Mã QCVN"]: r["Vị trí"] for r in rows}
        assert sides["R.415a"] == "bên phải" and sides["P.130"] == "bên trái"


def test_centercam_declines_frames_without_enough_road() -> None:
    for stem in ("1807", "1822"):
        path = d1.SAMPLE_DIR / f"{stem}.jpg"
        if not path.exists():
            pytest.skip("validation samples not materialised")
        heading = centercam.center_cam(Image.open(path))
        assert not heading.estimated and heading.x == 480
        assert heading.info["road_fraction"] < centercam.ROAD_MIN_FRACTION


@needs_weights
def test_1807_sign_falls_back_to_the_right_of_the_image_centre() -> None:
    image = Image.open(d1.SAMPLE_DIR / "1807.jpg")
    detections = d1.D1Detector().detect(image)
    rows = d1.scene_rows(detections, image.width, image.height, centercam.vanishing_x(image)[0])
    assert {r["Mã QCVN"]: r["Vị trí"] for r in rows}["P.123a"] == "bên phải"


def test_centercam_is_model_agnostic_and_stacks_only_adjacent_boxes() -> None:
    # 1822: P.102 and R.302a share one pole at the left edge; P.108a stands elsewhere.
    boxes = [(33, 411, 55, 432), (32, 433, 53, 453), (379, 374, 419, 411)]
    places = centercam.layout(boxes, 960, 540, 480.0)
    assert places[1].pole_of == 0 and places[2].pole_of is None
    assert abs(places[2].x - places[0].x) > places[0].r + places[2].r
    assert centercam.same_pole(boxes[0], boxes[1]) and not centercam.same_pole(boxes[0], boxes[2])
    assert [centercam.side_of(b, 480.0, 960) for b in boxes] == ["trái", "trái", "trái"]
    assert centercam.side_of((470, 0, 490, 20), 480.0, 960) == "giữa"


def test_centercam_imports_no_model_code() -> None:
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(centercam))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in getattr(node, "names", [])
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not imported & {"ultralytics", "torch", "tensorflow", "cpv301_autodrive"}


def test_detector_filters_invalid_model_geometry_and_preserves_pixel_coordinates():
    class Tensor:
        def __init__(self, values):
            self.values = np.asarray(values)

        def cpu(self):
            return self

        def numpy(self):
            return self.values

    boxes = SimpleNamespace(
        xyxy=Tensor(
            [[-2, 1, 30, 20], [70, 1, 90, 20], [0, 0, 0, 1], [0, 0, np.nan, 3], [1, 1, 3, 3]]
        ),
        cls=Tensor([0, 1, 0, 0, 99]),
        conf=Tensor([0.8, 0.9, 0.9, 0.9, 0.9]),
    )
    detector = object.__new__(d1.D1Detector)
    detector.classes = d1.load_classes()
    detector.device = "cpu"
    detector._lock = threading.Lock()
    calls = []

    def predict(**kwargs):
        calls.append(kwargs)
        return [SimpleNamespace(boxes=boxes)]

    detector.model = SimpleNamespace(predict=predict)
    found = detector.detect(Image.new("RGB", (100, 50)))
    assert [d.confidence for d in found] == [0.9, 0.8]
    assert found[1].box == (0, 1, 30, 20)
    assert [r["Vị trí trong ảnh"] for r in d1.detection_rows(found, 100, 50)] == ["phải", "trái"]
    assert calls[0]["imgsz"] == 1280 and calls[0]["iou"] == 0.70
    with pytest.raises(ValueError):
        detector.detect(Image.new("RGB", (100, 50)), float("nan"))


def test_upload_orientation_matches_displayed_coordinate_frame():
    from cpv301_autodrive.views import read_uploaded_image

    image = Image.new("RGB", (80, 40), "red")
    exif = Image.Exif()
    exif[274] = 6
    data = BytesIO()
    image.save(data, format="JPEG", exif=exif)
    assert read_uploaded_image(data).size == (40, 80)


def test_invalid_upload_after_ultralytics_patch_is_a_normal_image_error(monkeypatch):
    from cpv301_autodrive import views

    def patched_open(*args, **kwargs):
        raise ModuleNotFoundError("No module named pi_heif")

    monkeypatch.setattr(views.Image, "open", patched_open)
    with pytest.raises(views.UnidentifiedImageError, match="File ảnh bị hỏng"):
        views.read_uploaded_image(BytesIO(b"not an image"))


def test_demo_handles_empty_and_failed_inference_without_exception(monkeypatch, tmp_path):
    from cpv301_autodrive import views

    sample = tmp_path / "frame.png"
    Image.new("RGB", (300, 100), "white").save(sample)
    monkeypatch.setattr(d1, "weights_available", lambda: True)
    monkeypatch.setattr(d1, "sample_images", lambda: [sample])
    calls = []

    def detect(_image, conf):
        calls.append(conf)
        return []

    monkeypatch.setattr(views, "get_d1_detector", lambda: SimpleNamespace(detect=detect))
    views.detect_d1_frame.clear()
    app = AppTest.from_string(
        "from cpv301_autodrive.views import render_d1_demo\nrender_d1_demo()"
    ).run(timeout=30)
    assert not app.exception and any("Không có biển" in x.value for x in app.info)
    app.slider(key="d1_cruise").set_value(55).run()
    assert len(calls) == 1 and not app.exception
    views.detect_d1_frame.clear()

    def fail():
        raise RuntimeError("checkpoint test error")

    monkeypatch.setattr(views, "get_d1_detector", fail)
    app.run()
    assert not app.exception and "checkpoint test error" in app.error[0].value
    views.detect_d1_frame.clear()
