from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_wp37_r1_dataset_card", REPO_ROOT / "scripts/build_wp37_r1_dataset_card.py"
)
assert SPEC is not None and SPEC.loader is not None
wp37_r1 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wp37_r1
SPEC.loader.exec_module(wp37_r1)
RAW = wp37_r1.DEFAULT_RAW_ROOT


def card() -> str:
    return (REPO_ROOT / wp37_r1.CARD_PATH).read_text(encoding="utf-8")


@pytest.mark.skipif(not RAW.is_dir(), reason="no local DATASET01")
def test_package_verifies_and_wp37_reproduces() -> None:
    result = wp37_r1.verify(REPO_ROOT, RAW)
    assert result["valid"] is True, result["errors"]


def test_p2_dark_bucket_is_not_low_light() -> None:
    text = card()
    assert "không phải điều kiện chiếu sáng" in text
    assert "cảnh ban ngày chụp ngược tán cây" in text
    assert "không có ảnh nào được xác minh là thiếu sáng hay ban đêm" in text
    assert "Val tối hơn" not in text and "ảnh tối chỉ có ở val" not in text


def test_p3_wording_fixes() -> None:
    text = card()
    assert "(creator: Data Palpating Team)" not in text
    assert f"Ghi công bắt buộc (đúng văn bản D-01): {wp37_r1.D01_ATTRIBUTION}." in text
    assert "≈37 % box" in text and "chiếm đa số" not in text
    assert "camera hành trình" not in text and "loại thiết bị UNKNOWN" in text


def test_decode_sizes_cover_every_frame() -> None:
    with (REPO_ROOT / wp37_r1.DECODE_PATH).open(newline="", encoding="utf-8") as handle:
        decode = list(csv.DictReader(handle))
    assert len(decode) == 3216
    manifest = json.loads((REPO_ROOT / wp37_r1.MANIFEST_PATH).read_text(encoding="utf-8"))
    assert manifest["decode_sizes"]["540x960"] == {"540x960": 39}
    assert manifest["dark_bucket_stems"] == ["1843", "1844", "1845", "1848", "1849", "1850", "1851"]


def test_missing_replacement_fails_closed() -> None:
    with pytest.raises(ValueError, match="exactly once"):
        wp37_r1.replace_once("abc", "missing", "x")


def test_tampered_wp37_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    pins = dict(wp37_r1.PINNED_SOURCES)
    pins["docs/dataset01_card.md"] = "0" * 64
    monkeypatch.setattr(wp37_r1, "PINNED_SOURCES", pins)
    assert wp37_r1.verify(REPO_ROOT, RAW)["valid"] is False
