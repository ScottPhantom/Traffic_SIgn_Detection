from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_webapp_initial_screen_renders_without_exception() -> None:
    app_path = Path(__file__).parents[1] / "src" / "cpv301_autodrive" / "web_app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=30)
    assert not app.exception
    assert any("bắt đầu mô phỏng" in message.value for message in app.info)
