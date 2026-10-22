"""Authenticated Dataset01 view successor for WP36-R1 and WP38-R1 evidence.

The predecessor view is retained as QA-failed evidence.  Every authority badge exposed here is
gated by exact source pins plus schema and roster checks before the predecessor renderer runs.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from cpv301_autodrive import dataset01_view as _base
from cpv301_autodrive.config import PROJECT_ROOT

BUCKETS = _base.BUCKETS
GRAPH_TEMPLATE = _base.GRAPH_TEMPLATE
PIPELINE_TEMPLATE = _base.PIPELINE_TEMPLATE
WP36_SPLIT = Path("docs/review/generated/wp36_r1_split_frames.csv")
WP36_MANIFEST = Path("docs/review/generated/wp36_r1_split_manifest.json")
WP36_QA = Path("docs/review/wp36_r1_independent_qa_record.md")
D02_REGISTRY = Path("docs/review/generated/d02_group_id_registry.csv")
WP38_MANIFEST = Path("docs/review/generated/wp38_r1_orientation_correction_manifest.json")
WP38_QA = Path("docs/review/wp38_r1_orientation_correction_independent_qa_record.md")
PINNED_AUTHORITIES = {
    str(WP36_SPLIT): "8e197d9c7103ac5dc6b7ffc8a3d1aeb30bb6034048d470e4887dd868df95823a",
    str(WP36_MANIFEST): "064259941895d35054e87a550bf69199c4cae8ffeb4c83b4d7cdf608673438d9",
    str(WP36_QA): "a71d1894093c3a2ca4ff060658596c06458891f9dd4740e7b6c9abf2ef4f9056",
    str(D02_REGISTRY): "c3b11f4c143627fd777270b34e40486bf92fd6e82e4c306187165fef4f7155d3",
    str(WP38_MANIFEST): "d88f5eae525a4aa6d77cdf3f581b60328a441aec0ff091cd907af20e8405385a",
    str(WP38_QA): "2dbc362408895f2d7a53c68748d12cadbb58604bee14f99a8d329b404a5a7a0a",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pinned_file(repo_root: Path, relative: Path) -> Path:
    path = repo_root / relative
    expected = PINNED_AUTHORITIES[str(relative)]
    if not path.is_file() or path.is_symlink() or _sha256(path) != expected:
        raise RuntimeError(f"Dataset Graph authority differs: {relative}")
    return path


def _strict_csv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != fields:
            raise RuntimeError(f"Dataset Graph authority schema differs: {path.name}")
        rows = list(reader)
    if any(set(row) != set(fields) or None in row.values() for row in rows):
        raise RuntimeError(f"Dataset Graph authority row differs: {path.name}")
    return rows


def authenticate_authorities(repo_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Authenticate exact split/correction authorities before an evidence view is rendered."""
    for relative in PINNED_AUTHORITIES:
        _pinned_file(repo_root, Path(relative))

    split_rows = _strict_csv(
        repo_root / WP36_SPLIT, ("stem", "group_id", "split", "use")
    )
    registry_rows = _strict_csv(
        repo_root / D02_REGISTRY,
        ("stem", "group_id", "vendor_split", "class_ids", "box_count"),
    )
    if len(split_rows) != 3215 or len({row["stem"] for row in split_rows}) != 3215:
        raise RuntimeError("WP36-R1 split roster is not exact and unique")
    if len(registry_rows) != 3215 or len({row["stem"] for row in registry_rows}) != 3215:
        raise RuntimeError("D02 registry roster is not exact and unique")
    split_by_stem = {row["stem"]: row for row in split_rows}
    registry_by_stem = {row["stem"]: row for row in registry_rows}
    if set(split_by_stem) != set(registry_by_stem) or "0248" in split_by_stem:
        raise RuntimeError("WP36-R1 and D02 rosters differ")
    if any(
        row["group_id"] != registry_by_stem[stem]["group_id"]
        for stem, row in split_by_stem.items()
    ):
        raise RuntimeError("WP36-R1 group identity differs from D02")
    counts = Counter(
        "quarantined" if row["use"] == "QUARANTINED" else row["split"]
        for row in split_rows
    )
    if counts != {"train": 1912, "val": 376, "test": 903, "quarantined": 24}:
        raise RuntimeError(f"WP36-R1 split counts differ: {dict(counts)}")
    allowed = {
        ("train", "TRAIN"),
        ("train", "BACKGROUND"),
        ("val", "VAL"),
        ("test", "TEST"),
        ("train", "QUARANTINED"),
        ("val", "QUARANTINED"),
        ("test", "QUARANTINED"),
    }
    if any((row["split"], row["use"]) not in allowed for row in split_rows):
        raise RuntimeError("WP36-R1 split/use policy differs")

    split_manifest = json.loads((repo_root / WP36_MANIFEST).read_text(encoding="utf-8"))
    expected_lists = {
        "train": "6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372",
        "val": "ae3f3509319fbb301012e9fbeb7431caacfcd4035c9d2f9167f24e3ed2b8f593",
        "test": "afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc",
    }
    if (
        split_manifest.get("package") != "M0-WP36-R1"
        or split_manifest.get("usable_frames") != {"train": 1912, "val": 376, "test": 903}
        or split_manifest.get("split_list_sha256") != expected_lists
        or split_manifest.get("test_seal_sha256") != expected_lists["test"]
        or split_manifest.get("training_authorized") is not False
    ):
        raise RuntimeError("WP36-R1 manifest contract differs")

    correction = json.loads((repo_root / WP38_MANIFEST).read_text(encoding="utf-8"))
    corrected = [f"{number:04d}" for number in range(1319, 1358)]
    required = {
        "package": "M0-WP38-R1",
        "group_id": "D02-C0034",
        "split": "val",
        "rotation": "CCW_90",
        "frame_count": 39,
        "box_count": 29,
        "derived_size": [960, 540],
        "raw_mutated": False,
        "sealed_test_accessed": False,
        "training_authorized": False,
    }
    if any(correction.get(key) != value for key, value in required.items()):
        raise RuntimeError("WP38-R1 correction contract differs")
    if correction.get("stems") != corrected:
        raise RuntimeError("WP38-R1 corrected roster differs")
    if any(
        split_by_stem[stem]["split"] != "val"
        or split_by_stem[stem]["use"] != "VAL"
        or registry_by_stem[stem]["group_id"] != "D02-C0034"
        for stem in corrected
    ):
        raise RuntimeError("WP38-R1 correction is not validation-only D02-C0034")
    return {
        "split_rows": 3215,
        "corrected_stems": corrected,
        "sealed_test_stem_list_sha256": expected_lists["test"],
        "sealed_test_accessed": False,
    }


def graph_payload(repo_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    authenticate_authorities(repo_root)
    return _base.graph_payload(repo_root)


def class_rows(repo_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    return _base.class_rows(repo_root)


def group_rows(repo_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    authenticate_authorities(repo_root)
    return _base.group_rows(repo_root)


def pipeline_payload(repo_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    authenticate_authorities(repo_root)
    return _base.pipeline_payload(repo_root)


def render_graph_html(repo_root: Path = PROJECT_ROOT) -> str:
    payload = graph_payload(repo_root)
    return GRAPH_TEMPLATE.read_text(encoding="utf-8").replace(
        "__DATA__", _base._json(payload)
    )


def render_pipeline_html(repo_root: Path = PROJECT_ROOT) -> str:
    payload = pipeline_payload(repo_root)
    return PIPELINE_TEMPLATE.read_text(encoding="utf-8").replace(
        "__DATA__", _base._json(payload)
    )
