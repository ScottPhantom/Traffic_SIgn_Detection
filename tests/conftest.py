"""Shared pytest configuration.

The WP9, WP10 and WP11 suites call ``build(REPO_ROOT, ...)`` and rewrite hash-pinned repository
artifacts that later packages read as sources. Running them on pytest-xdist workers next to other
suites could expose a half-written file to a concurrent verifier, so they must run serially.
``scripts/run_parallel_checks.py tests`` runs them first without xdist, then parallelizes the rest.
"""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path, PurePosixPath

import pytest

SERIAL_REPO_WRITER_FILES = frozenset(
    {
        "test_wp9_bbox_0248_adjudication.py",
        "test_wp10_g04_quarantine.py",
        "test_wp11_d04_rare_class_review.py",
    }
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# These seven immutable historical assertions were correct when their predecessor packages were
# sealed: each asserted that the next work package did not yet exist.  The successor packages now
# exist legitimately.  Keep the compatibility exception exact, fail closed if a reviewed successor
# proof changes, and use strict xfail so a stale assertion that unexpectedly passes is still
# visible.
LEGACY_SUCCESSOR_XFAILS: dict[str, tuple[str, str]] = {
    "tests/test_wp26_remaining_edge_review_batch.py::"
    "test_no_wp27_artifacts_or_authorization_are_created": (
        "docs/review/generated/wp27_r2_verifier_hardening_manifest.json",
        "01e2993888761793943bdfe0ea3c0d96d58c00b1965fc8cabcc402b7fa77b426",
    ),
    "tests/test_wp27_r1_layout_correction.py::"
    "test_no_wp28_artifact_or_authorization_is_created": (
        "docs/review/generated/wp28_r2_remaining_edge_batch_g_manifest.json",
        "63af3feb4caae868837afcca024e53ada31b6f436ffe3d769016d1b6b465fd7b",
    ),
    "tests/test_wp27_remaining_edge_review_batch.py::"
    "test_no_wp28_artifacts_or_authorization_are_created": (
        "docs/review/generated/wp28_r2_remaining_edge_batch_g_manifest.json",
        "63af3feb4caae868837afcca024e53ada31b6f436ffe3d769016d1b6b465fd7b",
    ),
    "tests/test_wp28_r1_remaining_edge_review_batch.py::"
    "test_no_wp29_artifacts_or_authorization_are_created": (
        "docs/review/generated/wp29_remaining_edge_batch_h_manifest.json",
        "e7b56820d4dca24e54dc7f58f3e94d929f3d626b9ddb753d0e176c9de5b59a63",
    ),
    "tests/test_wp28_r2_remaining_edge_review_batch.py::"
    "test_no_wp29_artifacts_or_authorization_are_created": (
        "docs/review/generated/wp29_remaining_edge_batch_h_manifest.json",
        "e7b56820d4dca24e54dc7f58f3e94d929f3d626b9ddb753d0e176c9de5b59a63",
    ),
    "tests/test_wp28_remaining_edge_review_batch.py::"
    "test_no_wp29_artifacts_or_authorization_are_created": (
        "docs/review/generated/wp29_remaining_edge_batch_h_manifest.json",
        "e7b56820d4dca24e54dc7f58f3e94d929f3d626b9ddb753d0e176c9de5b59a63",
    ),
    "tests/test_wp29_remaining_edge_review_batch.py::"
    "test_no_wp30_artifacts_or_authorization_are_created": (
        "docs/review/generated/wp30_r1_remaining_edge_batch_i_manifest.json",
        "6de144e898dcc6b48f6a4629237afe2964595deff7d514a2e85c28b55c45e2fd",
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _same_file_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev,
        left.st_ino,
        stat.S_IFMT(left.st_mode),
    ) == (
        right.st_dev,
        right.st_ino,
        stat.S_IFMT(right.st_mode),
    )


def _same_regular_file_state(left: os.stat_result, right: os.stat_result) -> bool:
    return _same_file_identity(left, right) and (
        left.st_size,
        left.st_mtime_ns,
        left.st_ctime_ns,
    ) == (
        right.st_size,
        right.st_mtime_ns,
        right.st_ctime_ns,
    )


def _secure_regular_file_sha256(repo_root: Path, relative_path: str) -> str | None:
    """Hash an exact regular file without following symlinks or accepting path replacement."""
    relative = PurePosixPath(relative_path)
    parts = relative.parts
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if (
        relative.is_absolute()
        or not parts
        or any(part in {"", ".", ".."} for part in parts)
        or nofollow is None
        or directory is None
    ):
        return None

    root_path = Path(os.path.abspath(repo_root))
    descriptors: list[int] = []
    parent_bindings: list[tuple[int, str, os.stat_result]] = []
    try:
        root_lstat = os.lstat(root_path)
        if not stat.S_ISDIR(root_lstat.st_mode) or stat.S_ISLNK(root_lstat.st_mode):
            return None
        directory_flags = os.O_RDONLY | nofollow | directory | getattr(os, "O_CLOEXEC", 0)
        current_fd = os.open(root_path, directory_flags)
        descriptors.append(current_fd)
        root_fstat = os.fstat(current_fd)
        if not stat.S_ISDIR(root_fstat.st_mode) or not _same_file_identity(
            root_lstat, root_fstat
        ):
            return None

        for component in parts[:-1]:
            child_fd = os.open(component, directory_flags, dir_fd=current_fd)
            descriptors.append(child_fd)
            child_fstat = os.fstat(child_fd)
            child_lstat = os.stat(component, dir_fd=current_fd, follow_symlinks=False)
            if (
                not stat.S_ISDIR(child_fstat.st_mode)
                or stat.S_ISLNK(child_lstat.st_mode)
                or not _same_file_identity(child_lstat, child_fstat)
            ):
                return None
            parent_bindings.append((current_fd, component, child_fstat))
            current_fd = child_fd

        file_flags = (
            os.O_RDONLY
            | nofollow
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        proof_fd = os.open(parts[-1], file_flags, dir_fd=current_fd)
        descriptors.append(proof_fd)
        before = os.fstat(proof_fd)
        if not stat.S_ISREG(before.st_mode):
            return None

        digest = hashlib.sha256()
        while chunk := os.read(proof_fd, 1024 * 1024):
            digest.update(chunk)

        after = os.fstat(proof_fd)
        named_after = os.stat(parts[-1], dir_fd=current_fd, follow_symlinks=False)
        if (
            not stat.S_ISREG(named_after.st_mode)
            or not _same_regular_file_state(before, after)
            or not _same_regular_file_state(after, named_after)
        ):
            return None
        for parent_fd, component, expected in parent_bindings:
            observed = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            if not stat.S_ISDIR(observed.st_mode) or not _same_file_identity(
                expected, observed
            ):
                return None
        root_after = os.lstat(root_path)
        if not stat.S_ISDIR(root_after.st_mode) or not _same_file_identity(
            root_fstat, root_after
        ):
            return None
        return digest.hexdigest()
    except (OSError, TypeError, ValueError):
        return None
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def legacy_successor_xfail_reason(nodeid: str, repo_root: Path = REPO_ROOT) -> str | None:
    """Return an exact successor-backed reason, or fail closed with no compatibility mark."""
    proof = LEGACY_SUCCESSOR_XFAILS.get(nodeid)
    if proof is None:
        return None
    relative_path, expected_sha256 = proof
    if _secure_regular_file_sha256(repo_root, relative_path) != expected_sha256:
        return None
    return (
        "historical absence assertion superseded by pinned successor proof "
        f"{relative_path}@sha256:{expected_sha256}"
    )


def apply_legacy_successor_xfail(item: pytest.Item, repo_root: Path = REPO_ROOT) -> None:
    reason = legacy_successor_xfail_reason(item.nodeid, repo_root)
    if reason is not None:
        item.add_marker(pytest.mark.xfail(reason=reason, strict=True))


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        apply_legacy_successor_xfail(item)


@pytest.fixture(autouse=True)
def _reject_repo_writers_under_xdist(request: pytest.FixtureRequest) -> None:
    # Fail before the test body runs, so no repository artifact is rewritten concurrently.
    if hasattr(request.config, "workerinput") and request.path.name in SERIAL_REPO_WRITER_FILES:
        pytest.fail(
            f"{request.path.name} rewrites repository artifacts and must not run under "
            "pytest-xdist; use `uv run python scripts/run_parallel_checks.py tests`.",
            pytrace=False,
        )
