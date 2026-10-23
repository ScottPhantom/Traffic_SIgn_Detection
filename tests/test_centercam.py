"""Image-position contract, independent of model and road heading."""

import math

import pytest

from cpv301_autodrive import centercam as cam


@pytest.mark.parametrize(
    "cx,side",
    [
        (10, "trái"),
        (99, "trái"),
        (100, "giữa"),
        (150, "giữa"),
        (200, "giữa"),
        (201, "phải"),
        (290, "phải"),
    ],
)
def test_equal_thirds_and_inclusive_middle_boundaries(cx, side):
    position = cam.image_position((cx - 1, 5, cx + 1, 15), 300, 100)
    assert position.side == side
    assert position.normalized_x == pytest.approx(cx / 300)


def test_position_is_invariant_under_resize_and_portrait():
    for w, h in [(960, 540), (540, 960), (1920, 1080), (100, 100)]:
        box = (0.75 * w, 0.1 * h, 0.85 * w, 0.2 * h)
        assert cam.image_position(box, w, h).side == "phải"
        assert cam.image_position(box, w, h).normalized_x == pytest.approx(0.8)


@pytest.mark.parametrize(
    "box,w,h",
    [
        ((0, 0, 0, 2), 10, 10),
        ((-1, 0, 2, 2), 10, 10),
        ((0, 0, 11, 2), 10, 10),
        ((0, 0, 2, 2), 0, 10),
        ((0, 0, math.nan, 2), 10, 10),
    ],
)
def test_invalid_geometry_fails_closed(box, w, h):
    with pytest.raises(ValueError):
        cam.image_position(box, w, h)


def test_image_scene_keeps_region_and_identity_across_pole_boundary():
    # Adjacent wide boxes may straddle a third; pole grouping must not rewrite the region.
    boxes = [(70, 10, 120, 30), (90, 31, 140, 51), (240, 20, 270, 40)]
    places = cam.layout(boxes, 300, 100, 150, image_regions=True)
    assert [p.side for p in places] == ["trái", "giữa", "phải"]
    assert places[1].pole_of is None
    assert cam.layout([], 300, 100, 150, image_regions=True) == []
