import json
import re
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from cpv301_autodrive import dataset_graph
from cpv301_autodrive.dataset_graph import build_graph_payload, render_graph_html

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def payload() -> dict:
    return build_graph_payload(REPO_ROOT)


def test_payload_covers_every_audited_frame_and_proxy_edge(payload: dict) -> None:
    summary = payload["summary"]
    assert (summary["nodes"], summary["edges"]) == (3216, 3178)
    assert (summary["train"], summary["test"]) == (2552, 664)
    assert summary["cross"] == 1031
    assert len(payload["comp"]) == len(payload["nodes"])
    assert all(edge[1] == edge[0] + 1 for edge in payload["edges"])


def test_review_states_partition_all_edges(payload: dict) -> None:
    summary = payload["summary"]
    assert sum(summary["cap"].values()) == summary["edges"]
    assert summary["cap"]["Q"] == 2
    reviewed = sum(summary["bySource"].values())
    assert reviewed + summary["cap"].get("P", 0) + summary["cap"]["Q"] == summary["edges"]
    assert summary["cap"].get("P", 0) == 0  # WP30 covered every review-eligible edge
    quarantine = [edge for edge in payload["edges"] if edge[6] == "Q"]
    assert {edge[2] for edge in quarantine} == {242, 243}


def test_unreviewed_overlays_are_not_marked_qa_passed(payload: dict) -> None:
    assert payload["qa"]["WP28-R2"] == "pass"
    assert payload["qa"]["WP29"] == "pass"
    assert payload["qa"]["WP30-R1"] == "pass"
    assert payload["qa"]["WP7"] == "pass"


def test_overlapping_overlay_fails_closed(tmp_path: Path) -> None:
    for relative in (dataset_graph.INVENTORY_PATH, dataset_graph.EDGE_DECISIONS_PATH):
        (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, tmp_path / relative)
    shutil.copytree(
        REPO_ROOT / dataset_graph.REVIEW_DIR,
        tmp_path / dataset_graph.REVIEW_DIR,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("assets", "generated"),
    )
    target = tmp_path / dataset_graph.REVIEW_DIR / dataset_graph.EDGE_OVERLAYS[-1].annotations
    payload = json.loads(target.read_text("utf-8"))
    payload["decisions"][0]["edge_id"] = "edge_000006"  # already reviewed by WP7
    target.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="re-reviews edge_000006"):
        build_graph_payload(tmp_path)


def test_rendered_html_inlines_safe_payload(payload: dict) -> None:
    html = render_graph_html(payload, embedded=True)
    assert "__DATA__" not in html and "__EMBED__" not in html
    assert 'data-embed="1"' in html
    data = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
    assert data is not None
    assert json.loads(data.group(1))["summary"] == payload["summary"]


def test_webapp_graph_tab_renders_without_exception() -> None:
    app_path = REPO_ROOT / "src" / "cpv301_autodrive" / "web_app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=60)
    assert not app.exception
    labels = [tab.label for tab in app.tabs]
    assert any("DATASET01" in label for label in labels)
