from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from cpv301_autodrive import dataset01_view_r1 as view

REPO_ROOT = Path(__file__).resolve().parents[1]


def _authority_copy(tmp_path: Path) -> Path:
    for relative in view.PINNED_AUTHORITIES:
        source = REPO_ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return tmp_path


def test_authenticated_graph_contract_and_payload() -> None:
    contract = view.authenticate_authorities(REPO_ROOT)
    assert contract["split_rows"] == 3215
    assert len(contract["corrected_stems"]) == 39
    assert contract["sealed_test_accessed"] is False
    payload = view.graph_payload(REPO_ROOT)
    assert payload["summary"]["splitAuthority"] == "WP36-R1"
    assert payload["summary"]["correctionAuthority"] == "WP38-R1 QA PASS"
    assert payload["summary"]["orientationCorrected"] == 39


@pytest.mark.parametrize(
    ("relative", "mutator"),
    [
        (
            view.WP38_MANIFEST,
            lambda text: text.replace('"1319",', '"0001",', 1),
        ),
        (
            view.WP36_SPLIT,
            lambda text: text.replace("0072,D02-C0002,train,TRAIN", "0072,D02-C0002,val,VAL", 1),
        ),
        (
            view.WP36_SPLIT,
            lambda text: text + text.splitlines(keepends=True)[1],
        ),
        (
            view.D02_REGISTRY,
            lambda text: text.replace("1319,D02-C0034", "1319,D02-C0001", 1),
        ),
    ],
)
def test_authenticated_graph_rejects_forged_authority(
    tmp_path: Path, relative: Path, mutator
) -> None:
    root = _authority_copy(tmp_path)
    target = root / relative
    target.write_text(mutator(target.read_text(encoding="utf-8")), encoding="utf-8")
    with pytest.raises(RuntimeError, match="Dataset Graph authority differs"):
        view.authenticate_authorities(root)
