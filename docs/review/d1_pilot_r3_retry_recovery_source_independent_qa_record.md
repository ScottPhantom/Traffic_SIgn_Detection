# D1 Pilot R3 retry-recovery source independent QA record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_PASS_SOURCE_ONLY_NO_LIVE_RESUME`  
Reviewer: `Codex independent source-QA session`  
Boundary: `READ_ONLY_NO_DRIVE_NO_COLAB_NO_TRAINING_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**PASS with 0 findings on the final Repair R1 bytes.** This verdict authorizes only the next
append-only implementation commit and notebook pin stage. It does not authorize a Colab resume from
an unpinned notebook, sealed-test access, final evaluation, model acceptance or deployment.

| Reviewed artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_colab_pilot_r3.py` | `8c9b23472091f6c677d635a54e4f4e8b896e1fcf204d627ba56eb208db00c49c` |
| `tests/test_d1_pilot_r3.py` | `6130ddbe55860ef3b208a9fcb99a283c6b4a33b511588dbccae1df7226c0ea4b` |
| `docs/review/d1_pilot_r3_retry_recovery_implementation_record.md` | `9bf82fc018998a9b1b4ed4753d40e7171f027e46483cf99980fb043a199f8152` |

## Initial finding and closure

The first candidate failed with one High finding: it imported Python from the training checkout
before verifying the exact commit and clean worktree. A malicious predecessor module in a fake
checkout created a top-level marker before the old guard rejected it.

Repair R1 performs trusted lexical/no-symlink validation and verifies exact HEAD
`939f6bbce9f5c955b13ebcc84addd5083d242355` plus a clean worktree before any checkout import in
`load_dependencies`, `main` and `verify_live_state`. Independent wrong-commit, dirty-checkout and
symlink attacks were all rejected before their top-level marker side effect. A clean exact-commit
clone imported successfully.

## Retry and terminal controls

- The predecessor R2 guard reproduced the incident failure on the exact four-record history.
- R3 accepted one `fresh / PAUSED_FOR_RESUME` plus three `resume / FAILED` records as a retry
  prefix while preserving every record.
- Adversarial changes to order, run binding, checkpoint binding, runtime identity, chronology,
  failure error, sealed marker and history completeness failed closed.
- Existing tests confirmed checkpoint verification occurs before delegation and the complete
  attempt history is embedded/appended rather than truncated.
- The inherited Pilot R2 guard rejected failed, early-stopped, below-100 and sealed outcomes and
  accepted only exact epoch-100 `COMPLETED`/`COMPLETED_FROM_FINAL_CHECKPOINT` outcomes.

## Mechanical evidence

- Ruff: PASS.
- R3 targeted tests: `12 passed, 1 skipped`; the skip is the deliberately absent local Drive
  fixture.
- R2 + R3 targeted tests: `31 passed, 1 skipped`.
- Root lock check: PASS.
- Diff check: PASS.
- Graft graph: in sync.
- Sealed-test access log: absent in the reviewed source scope.

The reviewer did not access Drive or Colab and therefore did not independently re-read the live
checkpoint. Live execution remains pending a separately pinned notebook package and its independent
QA.
