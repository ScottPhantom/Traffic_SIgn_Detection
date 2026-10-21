from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from cpv301_autodrive.presentation import SLIDES, page_path

APP_PATH = Path(__file__).parents[1] / "src" / "cpv301_autodrive" / "web_app.py"


def test_webapp_opens_on_overview_slide() -> None:
    app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "Tổng quan"
    assert "Trang 1/8" in app.caption[0].value
    labels = [metric.label for metric in app.metric]
    assert "Gate 0" in labels and "Huấn luyện" in labels
    training = next(metric for metric in app.metric if metric.label == "Huấn luyện")
    assert training.value == "Được phép (D-05)"


@pytest.mark.parametrize("slide", SLIDES, ids=[slide.file for slide in SLIDES])
def test_every_slide_renders(slide) -> None:
    app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
    app.switch_page(page_path(slide)).run(timeout=120)
    assert not app.exception
    assert app.title[0].value == slide.title
    number = SLIDES.index(slide) + 1
    assert f"Trang {number}/{len(SLIDES)}" in app.caption[0].value


def test_demo_slide_prompts_for_an_image() -> None:
    app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
    app.switch_page("app_pages/07_demo.py").run(timeout=30)
    assert not app.exception
    assert any("bắt đầu mô phỏng" in message.value for message in app.info)


def test_pipeline_stages_match_overview_cards() -> None:
    from cpv301_autodrive.project_status import PIPELINE, PIPELINE_STAGES, STAGE_STATE_LABEL

    assert [stage.name for stage in PIPELINE_STAGES] == [name for name, _, _ in PIPELINE]
    for stage in PIPELINE_STAGES:
        assert stage.state in STAGE_STATE_LABEL
        assert stage.inputs and stage.outputs and stage.method and stage.numbers


def test_pipeline_dot_highlights_only_the_selected_stage() -> None:
    from cpv301_autodrive.palette import LIGHT
    from cpv301_autodrive.views import pipeline_dot

    dot = pipeline_dot("Classifier")
    assert dot.count(f'color="{LIGHT.accent}", penwidth=3') == 1
    highlighted = next(line for line in dot.splitlines() if "penwidth=3" in line)
    assert highlighted.strip().startswith('"Classifier"')


@pytest.mark.parametrize(
    "stage", ["Camera", "Detector", "Classifier", "Temporal voting", "Hành vi"]
)
def test_pipeline_slide_shows_each_stage(stage: str) -> None:
    app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
    app.switch_page("app_pages/03_pipeline.py").run(timeout=30)
    assert app.session_state["pipeline_stage"] == "Detector"
    app.session_state["pipeline_stage"] = stage
    app.run(timeout=30)
    assert not app.exception
    assert any(stage in block.value for block in app.markdown if block.value.startswith("###"))
    assert len(app.metric) >= 1


def test_governance_timeline_covers_every_gate_criterion() -> None:
    from cpv301_autodrive.project_status import GATE0, GOVERNANCE_TIMELINE

    codes = {code for _, _, tags in GOVERNANCE_TIMELINE for code in tags}
    assert {code for code, _, _ in GATE0} <= codes
    assert {"D-01", "D-02", "D-03", "D-04", "D-05"} <= codes
    dates = [date for date, _, _ in GOVERNANCE_TIMELINE]
    assert dates == sorted(dates)


def test_split_and_benchmark_figures_are_consistent() -> None:
    from cpv301_autodrive.project_status import (
        LATENCY_MEASURED_MS,
        SPLIT_FRAMES,
        TRAIN_HOURS_YOLO11N,
    )

    assert sum(count for _, count in SPLIT_FRAMES) == 3191
    assert all(0 < ms < 100 for _, ms in LATENCY_MEASURED_MS)
    assert sum(1 for *_, measured in TRAIN_HOURS_YOLO11N if measured) == 1


@pytest.mark.parametrize("page", ["04_du_lieu.py", "05_quan_tri.py", "06_mo_hinh.py"])
def test_presentation_slides_render_charts_or_timeline(page: str) -> None:
    app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
    app.switch_page(f"app_pages/{page}").run(timeout=120)
    assert not app.exception
    assert len(app.metric) >= 1 or len(app.get("progress")) == 1


def test_presentation_mode_from_url_shows_progress_and_keyboard_buttons() -> None:
    app = AppTest.from_file(str(APP_PATH))
    app.query_params["present"] = "true"
    app.run(timeout=30)
    assert not app.exception
    assert app.toggle(key="present").value is True
    assert len(app.get("progress")) == 1
    assert app.button(key="slide_next").label.startswith("Trang sau")


def test_next_button_moves_to_the_following_slide() -> None:
    app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
    app.button(key="slide_next").click().run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "Bài toán"


@pytest.mark.parametrize("key", ["slide_next", "slide_previous"])
def test_slide_buttons_switch_page_after_choosing_a_pipeline_stage(key: str) -> None:
    # A shared link such as /pipeline?pipeline_stage=Classifier binds the param to the widget;
    # switching pages must not try to clear it (StreamlitAPIException before the fix).
    app = AppTest.from_file(str(APP_PATH))
    app.query_params["pipeline_stage"] = "Classifier"
    app.run(timeout=30)
    app.switch_page("app_pages/03_pipeline.py").run(timeout=30)
    app.button(key=key).click().run(timeout=30)
    assert not app.exception
    assert app.title[0].value == ("Dữ liệu" if key == "slide_next" else "Bài toán")


def test_slide_buttons_keep_presentation_mode() -> None:
    app = AppTest.from_file(str(APP_PATH))
    app.query_params["present"] = "true"
    app.run(timeout=30)
    app.button(key="slide_next").click().run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "Bài toán"
    assert app.toggle(key="present").value is True
    assert len(app.get("progress")) == 1
