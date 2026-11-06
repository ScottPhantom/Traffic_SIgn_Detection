# D1 final evaluation R2 — independent source delta QA

Date: 2026-11-06 (Asia/Ho_Chi_Minh). Reviewer: separate Codex agent from the source author. Checkout HEAD at review: `1f1cc2219d94386ba8d13549389b9f8bbb45226a`.

Verdict: PASS

## Scope and byte bindings

- Reviewed the handoff `docs/codex_handoff_final_eval_path_fix_2026-11-06.md`, the source and test diff, and the new R2 plan. `graft check .` reported the wiring graph in sync.
- Scorer source `detector/m1/d1_final_evaluation_r1.py`: SHA-256 `edf4ba5cc7a9aaccb648cf9daad0a9e6343234e55da4065cee50040601238ea3`.
- Focused tests `detector/tests/test_d1_final_evaluation_r1.py`: SHA-256 `4eec77a5cfd3b97bbf9cfe5bba9da30efa83e95539e6e0906ddec1b72a5a64f2`.
- R2 plan `docs/review/generated/d1_final_evaluation_r2_plan.json`: SHA-256 `69f54ee3f6e6d10914d5347fa445d5457df43954dad063dbb0b90bb725b914a0`. Its scorer-source pin matches current bytes. Relative to R1, only scorer source hash, final contract path, and Owner opening approval path changed. Lock, proof, QA, lock approval, validation bundle, Q4, label decision, weights, reason, output directory, runtime settings, package ID and `sealed_test_accessed=false` remain equal.
- Existing R3 lock SHA-256 `d39b0466a5285979c3da63546ebbd56d26d0030081f4df9fa6c75fc8ee96167d`; proof SHA-256 `2d2fbd7cf99ee9e8b1349a55cf40b0182764efe9f7d4cd5078c06c5f8aa72e77`. Neither was edited.

## Independent checks

- Source requires CWD equal to absolute `REPO_ROOT/detector`, checks the lock-stored detector-relative proof with `samefile` and SHA-256 against the plan, and passes the stored proof string to the real R3 reader. It keeps `PACKAGE=D1-FINAL-EVALUATION-R1` for the existing Q4 and label decisions and points `CONTRACT_PATH` at R2. The absolute bundle path is accepted by the real reader in the dry run.
- `cd detector && PYTHONPATH=. uv run --no-sync pytest -q tests/test_d1_final_evaluation_r1.py`: 22 passed, including the real R3 reader on a synthetic `../docs/...` lock and refusal from a different CWD.
- `cd detector && uv run ruff check m1/d1_final_evaluation_r1.py tests/test_d1_final_evaluation_r1.py`: all checks passed.
- From `detector/`, independently called only `preflight(Path('docs/review/generated/d1_final_evaluation_r2_plan.json'), committed=False)` on the real validation lock/proof/bundle. Exact refusal: `RuntimeError: final contract is absent`. Thus gate 1 completed, including the R3 reader for both candidates. The lock selection was read as `conf=0.19`, `nms_iou=0.70`, `agnostic_nms=false`.
- The access log `results/experiments/sealed_test_access_log.jsonl` was absent before and after the call. The R2 Owner opening approval was absent. No scorer CLI, `execute`, inference, training or sealed payload access occurred; `sealed_test_accessed=false`.

`committed=False` was necessary because the new R2 plan and source delta are not committed yet. This QA establishes a real preflight gate-1 pass and the expected contract gate refusal; it does not grant test-opening authority or certify the future committed-file gate. The R2 contract and separate Owner opening approval remain subsequent gates.
