"""The public checkout must start without private model and video files."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from cpv301_autodrive.dataset01_authority import authenticate_authorities
from cpv301_autodrive.dataset_graph import build_graph_payload
from cpv301_autodrive.detector_d1 import load_classes

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src/cpv301_autodrive/web_app.py"


def test_public_evidence_matches_app_contract() -> None:
    assert len(load_classes()) == 54
    assert authenticate_authorities()["sealed_test_accessed"] is False
    assert build_graph_payload()["summary"]["nodes"] == 3216


def test_clean_checkout_renders_every_page() -> None:
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    pages = (
        "01_tong_quan", "02_bai_toan", "03_pipeline", "04_du_lieu",
        "05_quan_tri", "06_mo_hinh", "07_demo", "08_buoc_tiep",
    )
    for page in pages:
        app.switch_page(f"app_pages/{page}.py").run()
        assert not app.exception, page
    # Without private weights, the demo must explain the missing artifact.
    app.switch_page("app_pages/07_demo.py").run()
    assert any("trọng số" in error.value.lower() for error in app.error)
