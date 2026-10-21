from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from cpv301_autodrive import dataset01_view as view

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = REPO_ROOT / "src" / "cpv301_autodrive" / "web_app.py"


def test_graph_uses_vendor_splits_and_d02_groups() -> None:
    payload = view.graph_payload(REPO_ROOT)
    summary = payload["summary"]
    assert (summary["train"], summary["test"], summary["unassigned"]) == (2552, 639, 25)
    assert summary["groups"] == len(payload["groups"]) == 54
    stems = [node[0] for node in payload["nodes"]]
    assert payload["comp"][stems.index("0248")] == -1
    assert payload["comp"][stems.index("0247")] == payload["comp"][stems.index("0249")]


def test_class_table_matches_buckets_and_enrichment() -> None:
    rows = view.class_rows(REPO_ROOT)
    assert len(rows) == 54
    enriched = [row for row in rows if row["Ảnh làm giàu"]]
    assert len(enriched) == 12
    assert all(row["bucket"] == "DROP_FROM_V1_COLLECT_MORE" for row in enriched)
    assert all(row["Trạng thái"].startswith("Owner duyệt") for row in enriched)


def test_group_table_covers_every_grouped_frame() -> None:
    rows = view.group_rows(REPO_ROOT)
    assert len(rows) == 54
    assert sum(row["Ảnh"] for row in rows) == 3215


@pytest.mark.parametrize("render", [view.render_graph_html, view.render_pipeline_html])
def test_html_views_embed_valid_json(render) -> None:
    html = render(REPO_ROOT)
    assert "__DATA__" not in html
    data = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
    assert data is not None
    json.loads(data.group(1))


def test_pipeline_has_all_eight_steps_and_real_numbers() -> None:
    payload = view.pipeline_payload(REPO_ROOT)
    assert payload["stats"]["augmented"] == 1800
    assert payload["stats"]["groups"] == 54
    assert len(payload["buckets"]) == 4
    assert view.PIPELINE_TEMPLATE.read_text(encoding="utf-8").count('["') >= 8


@pytest.mark.parametrize(
    "section", [":material/hub: Đồ thị", ":material/category: Lớp", ":material/workspaces: Nhóm"]
)
def test_dataset01_sections_render(section: str) -> None:
    app = AppTest.from_file(str(APP_PATH)).run(timeout=60)
    app.switch_page("app_pages/04_du_lieu.py").run(timeout=60)
    app.session_state["dataset01_view"] = section
    app.run(timeout=120)
    assert not app.exception
