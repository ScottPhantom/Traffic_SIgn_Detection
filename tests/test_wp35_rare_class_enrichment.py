from __future__ import annotations

import csv
import importlib.util
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_wp35_rare_class_enrichment", REPO_ROOT / "scripts/build_wp35_rare_class_enrichment.py"
)
assert SPEC is not None and SPEC.loader is not None
wp35 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp35
SPEC.loader.exec_module(wp35)

needs_raw = pytest.mark.skipif(
    not wp35.DEFAULT_RAW_ROOT.is_dir(), reason="local DATASET01 copy not present"
)


def lineage() -> list[dict[str, str]]:
    with (REPO_ROOT / wp35.LINEAGE_PATH).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@needs_raw
def test_package_regenerates_byte_identically() -> None:
    result = wp35.verify(REPO_ROOT, wp35.DEFAULT_RAW_ROOT)
    assert result["valid"] is True, result["errors"]


def test_every_owner_class_gets_the_planned_volume_from_its_own_frames() -> None:
    rows = lineage()
    assert Counter(row["derived_key"] for row in rows) == Counter(
        {key: wp35.IMAGES_PER_CLASS for key in {row["derived_key"] for row in rows}}
    )
    assert len({row["derived_key"] for row in rows}) == 12
    with (REPO_ROOT / wp35.WP33_BOXES).open(newline="", encoding="utf-8") as handle:
        holders = {(b["stem"], b["derived_key"]) for b in csv.DictReader(handle)}
    assert all((row["source_stem"], row["derived_key"]) in holders for row in rows)


def test_geometry_stays_within_the_declared_bounds() -> None:
    for row in lineage():
        assert abs(float(row["angle_deg"])) <= wp35.MAX_ANGLE
        assert wp35.CROP_SCALE[0] <= float(row["crop_scale"]) <= 1.0
        assert "flip" not in row["photometric"]
        x, y, w, h = (float(v) for v in row["target_box"].split())
        eps = 1e-5
        assert -eps <= x - w / 2 and x + w / 2 <= 1 + eps
        assert -eps <= y - h / 2 and y + h / 2 <= 1 + eps


def test_a_window_that_cuts_a_sign_is_rejected() -> None:
    width, height = 1000, 500
    box = {
        "x": "0.5",
        "y": "0.5",
        "w": "0.6",
        "h": "0.4",
        "derived_key": "44",
        "train_eligible": "True",
    }
    boxes = wp35.pixel_boxes([box], width, height)
    rng = random.Random(1)
    # The 60 %-wide box cannot fit fully inside any 55–95 % window without rotation exceeding it,
    # and must never be returned half-cut.
    for _ in range(200):
        plan = wp35.plan_geometry(rng, width, height, boxes, box, max_angle=0.0)
        if plan is not None:
            _m, _a, _s, _cx, _cy, kept = plan
            (_box, (x0, y0, x1, y1)) = kept[0]
            assert x0 >= 0 and y0 >= 0 and x1 <= width and y1 <= height


def test_box_transform_matches_the_image_transform() -> None:
    width, height = 800, 400
    box = {
        "x": "0.5",
        "y": "0.5",
        "w": "0.05",
        "h": "0.1",
        "derived_key": "44",
        "train_eligible": "True",
    }
    plan = None
    rng = random.Random(7)
    while plan is None:
        plan = wp35.plan_geometry(rng, width, height, wp35.pixel_boxes([box], width, height), box)
    out_to_src, *_rest, kept = plan
    (_b, (x0, y0, x1, y1)) = kept[0]
    centre_out = np.array([(x0 + x1) / 2, (y0 + y1) / 2, 1.0])
    assert np.allclose(out_to_src @ centre_out, [400, 200], atol=1.0)


def test_changed_owner_record_fails_closed(tmp_path: Path) -> None:
    for relative in wp35.PINNED_SOURCES:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / relative).read_bytes())
    wp35.verify_pins(tmp_path)
    record = tmp_path / wp35.D04_RECORD
    record.write_text(record.read_text(encoding="utf-8") + "\nedited\n", encoding="utf-8")
    with pytest.raises(ValueError, match="pinned WP35 source changed"):
        wp35.verify_pins(tmp_path)
