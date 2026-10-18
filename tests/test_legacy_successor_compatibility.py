"""Regression tests for the exact successor-aware historical-test compatibility layer."""

from __future__ import annotations

from pathlib import Path

import conftest
import pytest

EXPECTED_NODEIDS = frozenset(
    {
        "tests/test_wp26_remaining_edge_review_batch.py::"
        "test_no_wp27_artifacts_or_authorization_are_created",
        "tests/test_wp27_r1_layout_correction.py::"
        "test_no_wp28_artifact_or_authorization_is_created",
        "tests/test_wp27_remaining_edge_review_batch.py::"
        "test_no_wp28_artifacts_or_authorization_are_created",
        "tests/test_wp28_r1_remaining_edge_review_batch.py::"
        "test_no_wp29_artifacts_or_authorization_are_created",
        "tests/test_wp28_r2_remaining_edge_review_batch.py::"
        "test_no_wp29_artifacts_or_authorization_are_created",
        "tests/test_wp28_remaining_edge_review_batch.py::"
        "test_no_wp29_artifacts_or_authorization_are_created",
        "tests/test_wp29_remaining_edge_review_batch.py::"
        "test_no_wp30_artifacts_or_authorization_are_created",
    }
)

PINNED_PREDECESSOR_TESTS = {
    "tests/test_wp26_remaining_edge_review_batch.py": (
        "99d60ffa317f2f3a566a8f3768fb907b8728240051c3c77f8754c492d12c5d1d"
    ),
    "tests/test_wp27_r1_layout_correction.py": (
        "f406d316b6068d28f724a4e9f5e19ee2b61364b362cf647902760952f310f36e"
    ),
    "tests/test_wp27_remaining_edge_review_batch.py": (
        "fe73fc42df74a99ea0b20f24f9622d54f01c1338f3c48150042ab20471e7b9ce"
    ),
    "tests/test_wp28_r1_remaining_edge_review_batch.py": (
        "094dff55efe3ba86c1b3014339baf3140dd0b49ae7f7ee7242e4c8e42c1052f5"
    ),
    "tests/test_wp28_r2_remaining_edge_review_batch.py": (
        "cbb2b02424dbe7ee830e5dbef4b2f2029e8b1fc626066db64fd0003926586122"
    ),
    "tests/test_wp28_remaining_edge_review_batch.py": (
        "cc6cdcbf92da82e8f250368a17cbd0dbae1f8eee3fbdc9b1bebdea501445c5da"
    ),
    "tests/test_wp29_remaining_edge_review_batch.py": (
        "34a3b9d95014fd27d970069999c3b96430db127051fd076bc22cb47d9a5ceb15"
    ),
}


class _FakeItem:
    def __init__(self, nodeid: str) -> None:
        self.nodeid = nodeid
        self.markers: list[pytest.MarkDecorator] = []

    def add_marker(self, marker: pytest.MarkDecorator) -> None:
        self.markers.append(marker)


def test_mapping_is_exact_and_every_successor_proof_is_pinned() -> None:
    assert frozenset(conftest.LEGACY_SUCCESSOR_XFAILS) == EXPECTED_NODEIDS
    for nodeid, (relative_path, expected_sha256) in conftest.LEGACY_SUCCESSOR_XFAILS.items():
        proof = conftest.REPO_ROOT / relative_path
        assert proof.is_file(), nodeid
        assert conftest._sha256(proof) == expected_sha256, nodeid
        reason = conftest.legacy_successor_xfail_reason(nodeid)
        assert reason is not None
        assert relative_path in reason
        assert expected_sha256 in reason


def test_hash_pinned_predecessor_tests_are_unchanged() -> None:
    for relative_path, expected_sha256 in PINNED_PREDECESSOR_TESTS.items():
        assert conftest._sha256(conftest.REPO_ROOT / relative_path) == expected_sha256


def test_unknown_nodeid_is_not_marked() -> None:
    item = _FakeItem("tests/test_unrelated.py::test_no_successor")
    conftest.pytest_collection_modifyitems([item])
    assert item.markers == []
    assert conftest.legacy_successor_xfail_reason(item.nodeid) is None


def test_known_nodeid_is_strict_xfail_only_with_exact_proof(tmp_path: Path) -> None:
    nodeid = next(iter(sorted(EXPECTED_NODEIDS)))
    relative_path, expected_sha256 = conftest.LEGACY_SUCCESSOR_XFAILS[nodeid]
    source = conftest.REPO_ROOT / relative_path
    staged = tmp_path / relative_path
    staged.parent.mkdir(parents=True)
    staged.write_bytes(source.read_bytes())

    reason = conftest.legacy_successor_xfail_reason(nodeid, tmp_path)
    assert reason is not None and expected_sha256 in reason

    staged.write_bytes(staged.read_bytes() + b"\n")
    assert conftest.legacy_successor_xfail_reason(nodeid, tmp_path) is None

    item = _FakeItem(nodeid)
    conftest.pytest_collection_modifyitems([item])
    assert len(item.markers) == 1
    mark = item.markers[0].mark
    assert mark.name == "xfail"
    assert mark.kwargs["strict"] is True
    assert expected_sha256 in mark.kwargs["reason"]
