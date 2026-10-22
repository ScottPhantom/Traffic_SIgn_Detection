from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load():
    path = REPO_ROOT / "scripts/build_m1_colab_bundle_wp38_r1_r2.py"
    spec = importlib.util.spec_from_file_location("m1_colab_wp38_r1_r4_r2_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


builder = load()


def valid_manifest() -> dict:
    record = {
        "path": "data/raw/train.jpg",
        "sha256": "a" * 64,
        "source_split": "train",
        "kind": "raw_image",
        "size": 1,
    }
    files = [record, *[dict(record, path=f"data/raw/{index}.jpg") for index in range(5926)]]
    return {
        "schema_version": builder.SCHEMA_VERSION,
        "package": builder.PACKAGE,
        "status": builder.STATUS,
        "allowed_splits": ["train", "val"],
        "test_included": False,
        "sealed_test_accessed": False,
        "regular_files_only": True,
        "repo_git_commit": "b" * 40,
        **{field: "c" * 64 for field in builder.SHA_FIELDS},
        "counts": dict(builder.COUNT_VALUES),
        "file_count": 5927,
        "files": files,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("counts", True),
        ("repo_git_commit", 123),
        ("integration_manifest_sha256", 123),
        ("integration_manifest_sha256", "A" * 64),
    ],
)
def test_manifest_rejects_qa_reported_type_confusion(field: str, value: object) -> None:
    manifest = valid_manifest()
    manifest[field] = value
    with pytest.raises(RuntimeError):
        builder._validate_manifest(REPO_ROOT, manifest)


@pytest.mark.parametrize("value", [123, True, "unknown", "raw_image "])
def test_manifest_rejects_invalid_kind(value: object) -> None:
    manifest = valid_manifest()
    manifest["files"][0]["kind"] = value
    with pytest.raises(RuntimeError):
        builder._validate_manifest(REPO_ROOT, manifest)


@pytest.mark.parametrize("value", [True, 1911, 1912.0, "1912", -1])
def test_manifest_rejects_invalid_count(value: object) -> None:
    manifest = valid_manifest()
    manifest["counts"]["raw_train_images"] = value
    with pytest.raises(RuntimeError):
        builder._validate_manifest(REPO_ROOT, manifest)


def test_valid_typed_manifest_passes() -> None:
    builder._validate_manifest(REPO_ROOT, valid_manifest())


def test_contract_verifies_and_remains_train_val_only() -> None:
    result = builder.verify_contract(REPO_ROOT)
    assert result["valid"] is True
    assert result["file_count"] == 5927
    assert result["test_included"] is False
    assert result["sealed_test_accessed"] is False
    assert result["training_authorized"] is False


def test_manifest_copy_does_not_alias_counts() -> None:
    manifest = valid_manifest()
    copied = copy.deepcopy(manifest)
    copied["counts"]["raw_train_images"] = 0
    assert manifest["counts"] == builder.COUNT_VALUES
