from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "audit_dataset01.py"
SPEC = importlib.util.spec_from_file_location("audit_dataset01", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
audit_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_module)


def write_archive(staging_root: Path, archive_path: Path) -> None:
    with zipfile.ZipFile(archive_path, "w") as archive:
        for path in sorted((staging_root / "raw").rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(staging_root / "raw").as_posix())


def make_fixture(root: Path) -> tuple[Path, Path]:
    staging_root = root / "staging"
    dataset_root = staging_root / "raw" / "archive"
    images = dataset_root / "images"
    labels = dataset_root / "labels"
    splits = dataset_root / "split_dataset"
    images.mkdir(parents=True)
    labels.mkdir()
    splits.mkdir()

    Image.new("RGB", (100, 80), "white").save(images / "0001.jpg")
    Image.new("RGB", (120, 90), "black").save(images / "0002.jpg")
    label_rows = "\r\n".join(f"{class_id} 0.5 0.5 0.2 0.2" for class_id in range(52))
    (labels / "0001.txt").write_bytes((label_rows + "\r\n").encode())
    (labels / "0002.txt").write_bytes(b"")
    classes = [f"C{i}" for i in range(52)]
    (dataset_root / "classes.txt").write_bytes(("\r\n".join(classes) + "\r\n").encode())
    (dataset_root / "classes_en.txt").write_bytes(
        ("\r\n".join(f"English {i}" for i in range(52)) + "\r\n").encode()
    )
    (dataset_root / "classes_vie.txt").write_bytes(
        ("\r\n".join(f"Vietnamese {i}" for i in range(52)) + "\r\n").encode()
    )
    (splits / "train_files.txt").write_bytes(b"0001.jpg\r\n")
    (splits / "test_files.txt").write_bytes(b"0002.jpg\r\n")

    archive_path = root / "archive.zip"
    write_archive(staging_root, archive_path)
    return staging_root, archive_path


def audit_cli_args(
    staging_root: Path,
    archive_path: Path,
    output_dir: Path,
    *,
    write_normalized: bool = False,
) -> list[str]:
    args = [
        "audit",
        "--staging-root",
        str(staging_root),
        "--archive-zip",
        str(archive_path),
        "--output-dir",
        str(output_dir),
        "--expected-archive-sha256",
        hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "--expected-images",
        "2",
        "--expected-labels",
        "2",
        "--expected-classes",
        "52",
        "--expected-boxes",
        "52",
        "--expected-empty-labels",
        "1",
    ]
    if write_normalized:
        args.append("--write-normalized")
    return args


def test_audit_dataset_writes_reproducible_artifacts_without_changing_raw(tmp_path: Path) -> None:
    staging_root, archive_path = make_fixture(tmp_path)
    output_dir = tmp_path / "audit"
    raw_label = staging_root / "raw" / "archive" / "labels" / "0001.txt"
    raw_before = raw_label.read_bytes()
    archive_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()

    summary = audit_module.audit_dataset(
        staging_root=staging_root,
        archive_zip=archive_path,
        output_dir=output_dir,
        expected_archive_sha256=archive_sha,
        expected_images=2,
        expected_labels=2,
        expected_classes=52,
        expected_boxes=52,
        expected_empty_labels=1,
        write_normalized=True,
    )

    assert summary["status"] == {
        "technical_audit": "PASS",
        "gate0": "BLOCKED",
        "training_authorized": False,
    }, [key for key, value in summary["checks"].items() if not value]
    assert summary["counts"]["paired_stems"] == 2
    assert summary["splits"]["negative_excluded"] == 0
    assert summary["leakage_proxy"]["numeric_consecutive_pairs"] == 1
    assert summary["leakage_proxy"]["cross_split_pairs"] == 1
    assert raw_label.read_bytes() == raw_before
    normalized = (
        staging_root / "generated" / "normalized" / "archive" / "labels" / "0001.txt"
    )
    assert normalized.read_bytes().startswith(b"0 0.5 0.5 0.2 0.2\n")
    assert (output_dir / "audit_summary.json").is_file()
    assert (output_dir / "output_manifest.json").is_file()


def test_source_snapshot_is_stable_when_source_is_unchanged(tmp_path: Path) -> None:
    staging_root, archive_path = make_fixture(tmp_path)
    source_root = tmp_path / "source"
    source_root.mkdir()
    archive_path.replace(source_root / "archive.zip")
    (staging_root / "raw" / "archive").replace(source_root / "archive")

    first = audit_module.snapshot_source(source_root)
    second = audit_module.snapshot_source(source_root)

    assert first["archive"]["sha256"] == second["archive"]["sha256"]
    assert (
        first["extracted_source"]["tree_manifest_sha256"]
        == second["extracted_source"]["tree_manifest_sha256"]
    )
    assert audit_module.compare_source_snapshots(first, second)["unchanged"] is True


def test_manifest_directory_excludes_its_own_output(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    output = tmp_path / "manifest.json"

    payload = audit_module.manifest_directory(tmp_path, output)

    assert payload["artifact_count"] == 1
    assert payload["artifacts"][0]["path"] == "a.txt"


def test_raw_staging_zip_mismatch_fails_audit_and_cli(tmp_path: Path) -> None:
    staging_root, archive_path = make_fixture(tmp_path)
    raw_label = staging_root / "raw" / "archive" / "labels" / "0001.txt"
    raw_label.write_bytes(raw_label.read_bytes() + b"\n")
    output_dir = tmp_path / "audit"

    exit_code = audit_module.main(audit_cli_args(staging_root, archive_path, output_dir))
    summary = json.loads((output_dir / "audit_summary.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert summary["status"]["technical_audit"] == "FAIL"
    assert summary["checks"]["raw_bytes_match_zip"] is False
    assert summary["archive"]["byte_mismatches"] == ["archive/labels/0001.txt"]


def test_corrupt_image_fails_decode_and_cli(tmp_path: Path) -> None:
    staging_root, archive_path = make_fixture(tmp_path)
    corrupt_image = staging_root / "raw" / "archive" / "images" / "0001.jpg"
    corrupt_image.write_bytes(b"not-a-jpeg")
    write_archive(staging_root, archive_path)
    output_dir = tmp_path / "audit"

    exit_code = audit_module.main(audit_cli_args(staging_root, archive_path, output_dir))
    summary = json.loads((output_dir / "audit_summary.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert summary["status"]["technical_audit"] == "FAIL"
    assert summary["checks"]["raw_bytes_match_zip"] is True
    assert summary["checks"]["all_images_decode"] is False
    assert summary["image_decode"]["errors"][0]["stem"] == "0001"


@pytest.mark.parametrize(
    ("invalid_row", "case_name"),
    [
        ("52 0.5 0.5 0.2 0.2", "class_out_of_range"),
        ("0 1.2 0.5 0.2 0.2", "coordinate_out_of_range"),
        ("0 0.5 0.5 0 0.2", "size_out_of_range"),
        ("0 nan 0.5 0.2 0.2", "non_finite"),
        ("0 0.5 0.5 0.2", "wrong_field_count"),
    ],
)
def test_invalid_yolo_rows_fail_audit_and_cli(
    tmp_path: Path, invalid_row: str, case_name: str
) -> None:
    staging_root, archive_path = make_fixture(tmp_path)
    label_path = staging_root / "raw" / "archive" / "labels" / "0001.txt"
    rows = label_path.read_text(encoding="utf-8").splitlines()
    rows[0] = invalid_row
    label_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    write_archive(staging_root, archive_path)
    output_dir = tmp_path / case_name

    exit_code = audit_module.main(audit_cli_args(staging_root, archive_path, output_dir))
    summary = json.loads((output_dir / "audit_summary.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert summary["status"]["technical_audit"] == "FAIL"
    assert summary["checks"]["all_yolo_rows_valid"] is False
    assert summary["labels"]["validation_errors"]


def test_bbox_boundary_overflow_warns_without_clamping_or_dropping(tmp_path: Path) -> None:
    staging_root, archive_path = make_fixture(tmp_path)
    label_path = staging_root / "raw" / "archive" / "labels" / "0001.txt"
    rows = label_path.read_text(encoding="utf-8").splitlines()
    rows[0] = "0 0.99 0.5 0.1 0.2"
    raw_payload = ("\r\n".join(rows) + "\r\n").encode()
    label_path.write_bytes(raw_payload)
    write_archive(staging_root, archive_path)
    output_dir = tmp_path / "audit"

    summary = audit_module.audit_dataset(
        staging_root=staging_root,
        archive_zip=archive_path,
        output_dir=output_dir,
        expected_archive_sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        expected_images=2,
        expected_labels=2,
        expected_classes=52,
        expected_boxes=52,
        expected_empty_labels=1,
        write_normalized=True,
    )

    assert summary["status"]["technical_audit"] == "PASS"
    assert summary["counts"]["boxes"] == 52
    assert summary["labels"]["bbox_boundary_warnings"][0]["stem"] == "0001"
    assert label_path.read_bytes() == raw_payload
    normalized = (
        staging_root / "generated" / "normalized" / "archive" / "labels" / "0001.txt"
    )
    assert normalized.read_text(encoding="utf-8").splitlines()[0] == "0 0.99 0.5 0.1 0.2"


def test_source_mutation_fails_preservation_and_compare_cli(tmp_path: Path) -> None:
    staging_root, archive_path = make_fixture(tmp_path)
    source_root = tmp_path / "source"
    source_root.mkdir()
    archive_path.replace(source_root / "archive.zip")
    (staging_root / "raw" / "archive").replace(source_root / "archive")
    before = audit_module.snapshot_source(source_root)
    label_path = source_root / "archive" / "labels" / "0001.txt"
    label_path.write_bytes(label_path.read_bytes() + b"mutation")
    after = audit_module.snapshot_source(source_root)
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    output_path = tmp_path / "proof.json"
    before_path.write_text(json.dumps(before), encoding="utf-8")
    after_path.write_text(json.dumps(after), encoding="utf-8")

    comparison = audit_module.compare_source_snapshots(before, after)
    exit_code = audit_module.main(
        [
            "compare-source",
            "--before",
            str(before_path),
            "--after",
            str(after_path),
            "--output",
            str(output_path),
        ]
    )

    assert comparison["unchanged"] is False
    assert comparison["checks"]["source_tree_hash_unchanged"] is False
    assert exit_code == 1
    assert json.loads(output_path.read_text(encoding="utf-8"))["unchanged"] is False


def test_normalization_rerun_is_idempotent_and_refuses_different_content(
    tmp_path: Path,
) -> None:
    staging_root, archive_path = make_fixture(tmp_path)
    output_dir = tmp_path / "audit"
    kwargs = {
        "staging_root": staging_root,
        "archive_zip": archive_path,
        "output_dir": output_dir,
        "expected_archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "expected_images": 2,
        "expected_labels": 2,
        "expected_classes": 52,
        "expected_boxes": 52,
        "expected_empty_labels": 1,
        "write_normalized": True,
    }

    first = audit_module.audit_dataset(**kwargs)
    second = audit_module.audit_dataset(**kwargs)
    normalized = (
        staging_root / "generated" / "normalized" / "archive" / "labels" / "0001.txt"
    )

    assert first["status"]["technical_audit"] == second["status"]["technical_audit"] == "PASS"
    normalized.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        audit_module.audit_dataset(**kwargs)


def test_manifest_verifier_detects_tampered_artifact_and_cli_returns_nonzero(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("original", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest = audit_module.manifest_directory(tmp_path, manifest_path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert audit_module.verify_artifact_manifest(manifest_path)["valid"] is True

    artifact.write_text("tampered", encoding="utf-8")
    verification = audit_module.verify_artifact_manifest(manifest_path)
    exit_code = audit_module.main(["verify-manifest", "--manifest", str(manifest_path)])

    assert verification["valid"] is False
    assert verification["mismatches"][0]["reason"] == "size_or_sha256_mismatch"
    assert exit_code == 1
