"""Shared pytest configuration.

The WP9, WP10 and WP11 suites call ``build(REPO_ROOT, ...)`` and rewrite hash-pinned repository
artifacts that later packages read as sources. Running them on pytest-xdist workers next to other
suites could expose a half-written file to a concurrent verifier, so they must run serially.
``scripts/run_parallel_checks.py tests`` runs them first without xdist, then parallelizes the rest.
"""

from __future__ import annotations

import pytest

SERIAL_REPO_WRITER_FILES = frozenset(
    {
        "test_wp9_bbox_0248_adjudication.py",
        "test_wp10_g04_quarantine.py",
        "test_wp11_d04_rare_class_review.py",
    }
)


@pytest.fixture(autouse=True)
def _reject_repo_writers_under_xdist(request: pytest.FixtureRequest) -> None:
    # Fail before the test body runs, so no repository artifact is rewritten concurrently.
    if hasattr(request.config, "workerinput") and request.path.name in SERIAL_REPO_WRITER_FILES:
        pytest.fail(
            f"{request.path.name} rewrites repository artifacts and must not run under "
            "pytest-xdist; use `uv run python scripts/run_parallel_checks.py tests`.",
            pytrace=False,
        )
