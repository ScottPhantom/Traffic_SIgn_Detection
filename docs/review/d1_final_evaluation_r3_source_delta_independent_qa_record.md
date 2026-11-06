# D1 final evaluation R3 — independent source delta QA

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Reviewer: separate Codex agent from the R3 scorer and plan author. Scope: preparation only.

Verdict: PASS

## Reviewed byte bindings

- Scorer `detector/m1/d1_final_evaluation_r1.py`: SHA-256 `b6b4cf678663080b2096b48d4a8662514592f86ab700a37544d6544db93bc1da`.
- Synthetic tests `detector/tests/test_d1_final_evaluation_r1.py`: SHA-256 `1fd715c77884ae134d07cdce40cd4fd8265e1c037beade660e97575641920379`.
- R3 plan `docs/review/generated/d1_final_evaluation_r3_plan.json`: SHA-256 `2a8462225b88cbc4d32c0f359fe83d81bb49528f3b70d9f6616b8e9bd7c48c5f`. Its scorer pin matches current bytes.
- Relative to R2, the plan changes only the scorer source SHA, final contract path and Owner opening approval path. The lock, proof, bundle, weights, Q4 and label decisions, output destination, reason, package ID and `sealed_test_accessed=false` remain unchanged.
- `graft check .` reported the source graph in sync at review time.

## Independent checks

- Compared the source delta against `docs/codex_handoff_final_eval_recovery_r3_2026-11-06.md`, `docs/review/d1_final_evaluation_recovery_owner_authorization_2026-11-06.md` and the recorded R2 attempt. The scorer checks only file presence for `data_test.yaml` in preflight and immediately before logging in `_open_once`. No test payload is read by this check.
- The access-log allowlist accepts no opening or the exact attempt-2 entry once, with time `20261106T231301` and the pinned R2 plan and contract SHA-256 in its reason. It permits `export-test` entries. Other opening entries, a duplicate attempt-2 entry and the new `d1-final-evaluation-r3-open` action are refused in both preflight and `_open_once`. `PACKAGE` and `OPEN_MARKER` remain unchanged; `CONTRACT_PATH` is R3.
- `cd detector && PYTHONPATH=. uv run --no-sync pytest -q tests/test_d1_final_evaluation_r1.py`: 29 passed. The synthetic cases cover absent export with unchanged log, exact attempt 2, different or duplicate openings, prior R3 opening, and the `_open_once` one-time append.
- `cd detector && uv run ruff check m1/d1_final_evaluation_r1.py tests/test_d1_final_evaluation_r1.py`: all checks passed.
- Independently called only `preflight(Path('docs/review/generated/d1_final_evaluation_r3_plan.json'), committed=False)` from `detector/` on the real validation lock and proof. Exact refusal: `RuntimeError: final contract is absent`. This proves the earlier lock/proof gate completed; because the R3 contract did not yet exist, it does **not** verify the later Owner-approval, export-presence or access-log gate on real files. The handoff's later-gate dry-run expectation must be checked again after the R3 contract is written.
- Access log `results/experiments/sealed_test_access_log.jsonl` had one line and SHA-256 `ffef1b183ec8b4a20661c4bca71efa3cab64692c445432bc38eb3b3f2773b369` before and after the real preflight. The R3 Owner opening approval is absent.

This PASS is limited to the source delta, synthetic refusal behavior, pin consistency and the real gate-1 pass. It is not an authorization to export or open the sealed test and does not replace independent R3 contract or result QA. No `export-test`, scorer `execute`, inference, training or sealed payload access occurred; `sealed_test_accessed=false`.
