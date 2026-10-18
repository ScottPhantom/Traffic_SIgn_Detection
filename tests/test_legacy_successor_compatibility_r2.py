"""R2 regression attacks for no-follow, descriptor-bound successor proof validation."""

from __future__ import annotations

import os
from pathlib import Path

import conftest
import pytest

NODEID = sorted(conftest.LEGACY_SUCCESSOR_XFAILS)[0]
RELATIVE_PROOF, EXPECTED_SHA256 = conftest.LEGACY_SUCCESSOR_XFAILS[NODEID]
SOURCE_PROOF = conftest.REPO_ROOT / RELATIVE_PROOF


class _FakeItem:
    def __init__(self, nodeid: str = NODEID) -> None:
        self.nodeid = nodeid
        self.markers: list[pytest.MarkDecorator] = []

    def add_marker(self, marker: pytest.MarkDecorator) -> None:
        self.markers.append(marker)


def _stage_regular_proof(root: Path) -> Path:
    proof = root / RELATIVE_PROOF
    proof.parent.mkdir(parents=True)
    proof.write_bytes(SOURCE_PROOF.read_bytes())
    return proof


def test_exact_regular_proof_is_descriptor_bound_and_strictly_marked(tmp_path: Path) -> None:
    _stage_regular_proof(tmp_path)
    reason = conftest.legacy_successor_xfail_reason(NODEID, tmp_path)
    assert reason is not None
    assert RELATIVE_PROOF in reason
    assert EXPECTED_SHA256 in reason

    item = _FakeItem()
    conftest.apply_legacy_successor_xfail(item, tmp_path)
    assert len(item.markers) == 1
    assert item.markers[0].mark.name == "xfail"
    assert item.markers[0].mark.kwargs["strict"] is True


def test_missing_directory_fifo_and_tampered_proofs_fail_closed(tmp_path: Path) -> None:
    proof = tmp_path / RELATIVE_PROOF
    assert conftest.legacy_successor_xfail_reason(NODEID, tmp_path) is None

    proof.mkdir(parents=True)
    assert conftest.legacy_successor_xfail_reason(NODEID, tmp_path) is None
    proof.rmdir()

    os.mkfifo(proof)
    assert conftest.legacy_successor_xfail_reason(NODEID, tmp_path) is None
    proof.unlink()

    proof.write_bytes(SOURCE_PROOF.read_bytes() + b"\n")
    assert conftest.legacy_successor_xfail_reason(NODEID, tmp_path) is None


def test_final_symlink_to_valid_proof_is_unmarked(tmp_path: Path) -> None:
    proof = tmp_path / RELATIVE_PROOF
    proof.parent.mkdir(parents=True)
    proof.symlink_to(SOURCE_PROOF)

    assert conftest.legacy_successor_xfail_reason(NODEID, tmp_path) is None
    item = _FakeItem()
    conftest.apply_legacy_successor_xfail(item, tmp_path)
    assert item.markers == []


def test_parent_symlink_to_valid_tree_is_unmarked(tmp_path: Path) -> None:
    real_root = tmp_path / "real"
    _stage_regular_proof(real_root)
    (tmp_path / "docs").symlink_to(real_root / "docs", target_is_directory=True)

    assert conftest.legacy_successor_xfail_reason(NODEID, tmp_path) is None
    item = _FakeItem()
    conftest.apply_legacy_successor_xfail(item, tmp_path)
    assert item.markers == []


def test_root_symlink_is_unmarked(tmp_path: Path) -> None:
    real_root = tmp_path / "real"
    _stage_regular_proof(real_root)
    linked_root = tmp_path / "linked"
    linked_root.symlink_to(real_root, target_is_directory=True)

    assert conftest.legacy_successor_xfail_reason(NODEID, linked_root) is None


def test_same_byte_file_replacement_during_hash_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proof = _stage_regular_proof(tmp_path)
    original_read = conftest.os.read
    replaced = False

    def replace_after_read(descriptor: int, size: int) -> bytes:
        nonlocal replaced
        chunk = original_read(descriptor, size)
        if not replaced:
            replaced = True
            proof.rename(proof.with_name(f"{proof.name}.original"))
            proof.write_bytes(SOURCE_PROOF.read_bytes())
        return chunk

    monkeypatch.setattr(conftest.os, "read", replace_after_read)
    assert conftest.legacy_successor_xfail_reason(NODEID, tmp_path) is None
    assert replaced is True


def test_parent_replacement_during_hash_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stage_regular_proof(tmp_path)
    original_read = conftest.os.read
    replaced = False

    def replace_parent_after_read(descriptor: int, size: int) -> bytes:
        nonlocal replaced
        chunk = original_read(descriptor, size)
        if not replaced:
            replaced = True
            docs = tmp_path / "docs"
            moved = tmp_path / "docs.original"
            docs.rename(moved)
            docs.symlink_to(moved, target_is_directory=True)
        return chunk

    monkeypatch.setattr(conftest.os, "read", replace_parent_after_read)
    assert conftest.legacy_successor_xfail_reason(NODEID, tmp_path) is None
    assert replaced is True


def test_unknown_nodeid_remains_unmarked_with_valid_proof(tmp_path: Path) -> None:
    _stage_regular_proof(tmp_path)
    item = _FakeItem("tests/test_unknown.py::test_unrelated")
    conftest.apply_legacy_successor_xfail(item, tmp_path)
    assert item.markers == []
