from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).parents[1] / "src" / "cpv301_autodrive" / "web_app.py"


def test_webapp_opens_on_project_status() -> None:
    app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
    assert not app.exception
    assert "Tiến độ dự án" in app.session_state["main_view"]
    labels = [metric.label for metric in app.metric]
    assert "Gate 0" in labels and "Huấn luyện" in labels
    training = next(metric for metric in app.metric if metric.label == "Huấn luyện")
    assert training.value == "Được phép (D-05)"


def test_webapp_simulator_tab_renders_without_exception() -> None:
    app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
    app.session_state["main_view"] = next(tab.label for tab in app.tabs if "Mô phỏng" in tab.label)
    app.run(timeout=30)
    assert not app.exception
    assert any("bắt đầu mô phỏng" in message.value for message in app.info)
