from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load():
    path = REPO_ROOT / "scripts/build_m1_colab_bundle_wp38_r1_r1.py"
    spec = importlib.util.spec_from_file_location("m1_colab_wp38_r1_r4_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


builder = load()


def test_expected_records_bind_r4_qa_and_exclude_test() -> None:
    records, metadata = builder.expected_records(REPO_ROOT)
    assert len(records) == 5927
    assert {record["source_split"] for record in records} == {"train", "val"}
    assert all("/test/" not in f"/{record['path']}/" for record in records)
    assert metadata["integration_manifest_sha256"] == builder.PINNED_SOURCES[
        str(builder.INTEGRATION_MANIFEST)
    ]
    assert metadata["successor_exporter_sha256"] == builder.PINNED_SOURCES[
        str(builder.INTEGRATION_EXPORTER)
    ]
    assert metadata["integration_qa_record_sha256"] == builder.PINNED_SOURCES[
        str(builder.INTEGRATION_QA)
    ]
    assert metadata["sealed_test_stem_list_sha256"].startswith("afa03d4b")


def test_expected_record_counts_are_exact() -> None:
    records, _metadata = builder.expected_records(REPO_ROOT)
    assert Counter(record["kind"] for record in records) == {
        "raw_image": 2249,
        "wp38_r1_image": 39,
        "wp38_r1_label": 39,
        "wp35_image": 1800,
        "wp35_label": 1800,
    }


def test_build_refuses_dirty_checkout_before_archive_write(tmp_path: Path) -> None:
    archive = tmp_path / "bundle.tar.gz"
    with pytest.raises(RuntimeError, match="clean committed checkout"):
        builder.build_archive(REPO_ROOT, archive)
    assert not archive.exists()
    assert not archive.with_name(f"{archive.name}.manifest.json").exists()


def test_cli_has_no_test_export_path() -> None:
    assert set(builder.parser()._subparsers._group_actions[0].choices) == {
        "contract",
        "build",
        "verify",
    }
    source = (REPO_ROOT / "scripts/build_m1_colab_bundle_wp38_r1_r1.py").read_text()
    assert "export-test" not in source
    assert "--final-eval" not in source


def test_contract_verifier_is_sealed_safe() -> None:
    result = builder.verify_contract(REPO_ROOT)
    assert result["valid"] is True
    assert result["file_count"] == 5927
    assert result["test_included"] is False
    assert result["sealed_test_accessed"] is False
    assert result["training_authorized"] is False
