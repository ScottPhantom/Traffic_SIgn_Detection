# Legacy successor-test compatibility R1 — implementation record

Status: `PM_COMPLETE_AWAITING_INDEPENDENT_QA`

Date: `2026-10-19` (Asia/Ho_Chi_Minh)  
Baseline commit: `fd9823df6253d2e07d11f6fa2dd29b613710777e`  
Boundary: pytest collection compatibility only; no runtime, dataset, model, package verifier,
sealed-test, upload, download, commit or push action.

## Problem and decision

Seven immutable historical tests assert that the next WP did not exist when their predecessor was
sealed. Those assertions were correct at that historical checkpoint, but the authorized successor
packages now exist. Editing those seven tests would break their pinned hashes. Leaving them as
ordinary failures made the current full suite red even though the failures described legitimate
forward progress rather than a product regression.

R1 adds an exact, fail-closed compatibility layer in `tests/conftest.py`:

- only seven full pytest nodeids are eligible;
- each nodeid is bound to one exact successor manifest path and SHA-256;
- a missing, non-file or byte-changed proof receives no marker and the historical assertion fails
  normally;
- a valid proof receives `pytest.mark.xfail(strict=True)`, so an unexpected pass remains a suite
  failure;
- every unrelated/unknown nodeid receives no marker.

This is test routing only. It does not reinterpret any package decision, authorize training or
weaken the successor verifier contracts.

## Exact nodeid-to-proof contract

| Historical nodeid group | Exact successor proof | SHA-256 |
| --- | --- | --- |
| WP26 no-WP27 assertion | `docs/review/generated/wp27_r2_verifier_hardening_manifest.json` | `01e2993888761793943bdfe0ea3c0d96d58c00b1965fc8cabcc402b7fa77b426` |
| both WP27/R1 no-WP28 assertions | `docs/review/generated/wp28_r2_remaining_edge_batch_g_manifest.json` | `63af3feb4caae868837afcca024e53ada31b6f436ffe3d769016d1b6b465fd7b` |
| all three WP28/R1/R2 no-WP29 assertions | `docs/review/generated/wp29_remaining_edge_batch_h_manifest.json` | `e7b56820d4dca24e54dc7f58f3e94d929f3d626b9ddb753d0e176c9de5b59a63` |
| WP29 no-WP30 assertion | `docs/review/generated/wp30_r1_remaining_edge_batch_i_manifest.json` | `6de144e898dcc6b48f6a4629237afe2964595deff7d514a2e85c28b55c45e2fd` |

The complete seven-nodeid roster is executable and asserted in
`tests/test_legacy_successor_compatibility.py`; no filename glob, substring match or generic test
name is used by the collection hook.

## Pinned predecessor preservation

The new regression test re-hashes every immutable predecessor test and requires these exact values:

| File | SHA-256 |
| --- | --- |
| `tests/test_wp26_remaining_edge_review_batch.py` | `99d60ffa317f2f3a566a8f3768fb907b8728240051c3c77f8754c492d12c5d1d` |
| `tests/test_wp27_r1_layout_correction.py` | `f406d316b6068d28f724a4e9f5e19ee2b61364b362cf647902760952f310f36e` |
| `tests/test_wp27_remaining_edge_review_batch.py` | `fe73fc42df74a99ea0b20f24f9622d54f01c1338f3c48150042ab20471e7b9ce` |
| `tests/test_wp28_r1_remaining_edge_review_batch.py` | `094dff55efe3ba86c1b3014339baf3140dd0b49ae7f7ee7242e4c8e42c1052f5` |
| `tests/test_wp28_r2_remaining_edge_review_batch.py` | `cbb2b02424dbe7ee830e5dbef4b2f2029e8b1fc626066db64fd0003926586122` |
| `tests/test_wp28_remaining_edge_review_batch.py` | `cc6cdcbf92da82e8f250368a17cbd0dbae1f8eee3fbdc9b1bebdea501445c5da` |
| `tests/test_wp29_remaining_edge_review_batch.py` | `34a3b9d95014fd27d970069999c3b96430db127051fd076bc22cb47d9a5ceb15` |

No predecessor byte changed.

## Files changed by R1

- Modified: `tests/conftest.py` — exact mapping, SHA-256 check, strict collection marker.
- Added: `tests/test_legacy_successor_compatibility.py` — exact mapping, proof, predecessor,
  tamper and unknown-nodeid regressions.
- Added: this implementation record.
- Updated routing only: `PROJECT_MEMORY.md`, `docs/product_roadmap.md`.

Final source/test hashes before independent QA:

- `tests/conftest.py`: `6b1bf9aa7dca4c4b46e5911f3b5dae51f218c49e315473081383be89f35c170f`
- `tests/test_legacy_successor_compatibility.py`:
  `9ac9acb7e3949d86e7eced8bc34ab75deca47b153e4725165f16e72922bc5f99`

## PM verification

- Targeted final-byte run: `4 passed, 7 xfailed`; every xfail reason names its exact proof path
  and SHA-256.
- `uv run pytest --lf -q -rxX`: exit `0`, reached 100%, exactly the seven mapped historical tests
  were strict XFAIL. This run preceded only Ruff's import-order-only rewrite of the new regression
  test, after which the targeted run was repeated.
- `uv run python scripts/run_parallel_checks.py tests`: serial repo-writers `126 passed`; parallel
  remainder `1413 passed, 7 xfailed`; both stages exit `0` (`1539 passed, 7 xfailed` total).
- `uv run python scripts/run_parallel_checks.py verifiers`: `52/52` PASS.
- Root Ruff (`src tests`), root lock (168 packages), detector Ruff, detector lock (66 packages) and
  `git diff --check`: PASS.
- No sealed-test access log was created or used by this work.

## QA request

Independent QA should reproduce the exact seven-nodeid mapping, mutate/copy a successor proof to
confirm the helper returns no reason on hash mismatch, confirm an unknown nodeid is unmarked,
re-hash all seven predecessor tests, inspect `strict=True`, and run the targeted plus full suite.
Until that independent verdict is recorded, this package remains
`PM_COMPLETE_AWAITING_INDEPENDENT_QA`.
