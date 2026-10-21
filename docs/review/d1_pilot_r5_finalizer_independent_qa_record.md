# D1 Pilot R5 finalizer — independent QA record

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
QA role: independent, read-only source and artifact review  
Verdict: **PASS**

## Scope and authorization boundary

This review covers only the append-only Pilot R5 finalizer package:

- `detector/colab/run_d1_colab_pilot_r5.py`;
- `tests/test_d1_pilot_r5.py`;
- `docs/review/d1_pilot_r5_finalizer_implementation_record.md`.

The review did not train a model, package a model, upload data, commit, push, or access the sealed
test. It does not authorize the next training batch, sealed-test access, final evaluation, model
acceptance, deployment, or publication.

## Reviewed source identities

| File | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_colab_pilot_r3.py` | `8c9b23472091f6c677d635a54e4f4e8b896e1fcf204d627ba56eb208db00c49c` |
| `detector/colab/run_d1_colab_pilot_r4.py` | `ffcc88e2339b349775ca34e5e30531a102d0bcab1d45fa0dff9b1ea8bead25ad` |
| `detector/colab/run_d1_colab_pilot_r5.py` | `d4c7ab9b96fe92dd3eb6034fd1fb1144df7de35fbda88138f9b1d938f167d13b` |
| `tests/test_d1_pilot_r5.py` | `812e5e497379b06e38068d7b29d9a1611c4b73a510ef787173e8452b3c44fd56` |
| `docs/review/d1_pilot_r5_finalizer_implementation_record.md` | `ea43c0dcc2763a38738cb8ce4e3af2d1f22431619639267f3a25b54ffa63a7ae` |

The reviewed training checkout commit remains
`939f6bbce9f5c955b13ebcc84addd5083d242355`.

## Final findings

### 1. R5 cannot retrain or repackage

PASS. Static inspection and an exact source scan found no model-training call, resumable-training
entry point, archive creation, `export-test`, `--final-eval`, or sealed-test data path. R5 only
authenticates the already completed state, conditionally removes one exact reconstructed local run
directory, and invokes predecessor verification logic. It cannot resume from an earlier checkpoint
or create a new checkpoint/archive.

### 2. Exact artifacts are authenticated before the sole cleanup

PASS. `verify_packaged_state` now performs the operations in this fail-closed order:

1. require exact size and SHA-256 for the five live files;
2. require exactly one result archive and authenticate the archive and its manifest;
3. strictly parse the manifest and bind its execution-record and SQLite entries to the exact live
   bytes;
4. load the exact SHA-pinned R4 and R3 predecessor sidecars;
5. run the narrowly scoped ephemeral-run cleanup;
6. invoke the R3 dependency loader, including its clean-Git guard;
7. verify exact retry-aware runtime evidence, R6 checkpoint/archive state, `epoch-0100`, and the
   retry-aware SQLite/text logs.

The cleanup accepts only the exact sole Git status
`?? results/experiments/<reviewed-run>/`, requires the terminal reviewed execution outcome, checks
the pinned training commit, rejects a linked or missing target, compares the exact `git clean -nd`
preview, and requires a clean checkout afterward. Extra dirty state, a target symlink, a mismatched
run path, a different commit, an unauthenticated live artifact, an unauthenticated archive, or a
sidecar hash mismatch fails before deletion or verification success.

The end-to-end dirty-checkout regression proves that this exact cleanup is reachable before the
predecessor clean-Git guard, while the guard itself is reached only after deletion. This closes the
ordering regression in the earlier candidate.

### 3. Retry history and validator shadowing

PASS. R5 requires type-strict integers with exactly six attempts and exactly four failed resume
attempts, distinct runtime digests, and `sealed_test_accessed=false`. Counterexamples with 2, 5,
or 7 attempts and Boolean values are rejected. R5 replaces the R6 wrapper's old two-attempt
validator only for the R6 verification call, compares the returned runtime evidence with the
independently computed retry-aware evidence, and restores the original validator in `finally`.

The four failed attempts remain evidence, not terminal failure: the exact authenticated execution
record must report `SUCCEEDED`, contain the reviewed `COMPLETED_FROM_FINAL_CHECKPOINT` outcome at
epoch 100, and pass the R3/R4/R6 semantic checks. R5 does not write or promote the execution status,
so it cannot manufacture a successful terminal record.

### 4. Symlink and tamper resistance

PASS for the stated package boundary. The execution record, attempt journal, SQLite database, text
log, latest pointer, archive, and archive manifest must be regular files reached through
symlink-free lexical paths and must match exact observed sizes and SHA-256 values. The R3 and R4
sidecars are separately SHA-pinned and reject a linked sidecar file. Focused regressions cover live
file symlinks, archive/manifest tampering, predecessor tampering, extra dirty paths, cleanup-target
symlinks, incorrect counters, and validator shadowing.

## Independent current-artifact reproduction

QA copied the current synced Drive directory
`M1_D1_Colab/runs/pilot_seed_20261018_r2` into a temporary local snapshot, used a clean detached
clone of training commit `939f6bbce9f5c955b13ebcc84addd5083d242355`, and executed the reviewed
R5 sidecar with its exact R3/R4 siblings. The Drive originals were not modified.

Observed result:

- status: `D1_PILOT_R5_PACKAGED_STATE_VERIFIED`;
- cleanup: `CHECKOUT_ALREADY_CLEAN`;
- latest generation: `epoch-0100`;
- attempts: `6`;
- failed resume attempts: `4`;
- distinct runtime digests: `true`;
- archive SHA-256:
  `6ae2e6a29e1712ff5372764d5cc1eb6bb7ae9c9d06d7a08de8aab3e3c2f6778f`;
- manifest SHA-256:
  `0ecac47986d946ed83dfbac1e203f60b4e6055e5054ed9c52476db128b7f7796`;
- `sealed_test_accessed=false`.

The authenticated live-file identities were:

| Artifact | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `colab_execution.json` | 6,848 | `0f3f6bb9d96d4b852a97966f37048b659ffaa424868af05834e482c9ae01ccbc` |
| `execution_attempts.jsonl` | 3,584 | `eeedb9a8954ad4445b1ee65484d2b69cf30d106fa486f93c815b9241e7882b84` |
| `DB_logger.db` | 32,940,032 | `57e93f1c78365b4396600136ab16887d9bc6731a3343fe65787fd7390abd9bb8` |
| `colab_train.log` | 16,324,955 | `a3bdec9a5eb31b33126c75f20bdb9d9376b5e6ecc22ba422f54ecdb70107defe` |
| `recovery/latest.json` | 233 | `252b889a7b4136cba12609b11766e29e217f5ef1c93a2073d0e7dc9d2991eaf5` |
| result archive | 144,369,956 | `6ae2e6a29e1712ff5372764d5cc1eb6bb7ae9c9d06d7a08de8aab3e3c2f6778f` |
| result manifest | 2,140 | `0ecac47986d946ed83dfbac1e203f60b4e6055e5054ed9c52476db128b7f7796` |

## Validation evidence

- Targeted Ruff for R5 source/tests: PASS.
- R5 focused tests: **17/17 PASS**.
- Combined Pilot R3/R4/R5 and R3/R4 notebook tests: **51 PASS, 1 SKIP**. The skip is an existing
  environment-dependent notebook test, not an R5 failure.
- Root Ruff (`src`, `tests`): PASS.
- Root lock check: PASS, 168 packages resolved.
- Parallel verifier gate: **52/52 PASS** in 86.6 seconds wall time.
- Detector Ruff (`m1`, `tests`): PASS.
- Detector lock check: PASS, 66 packages resolved.
- Detector tests: **105/105 PASS** in 4.96 seconds.
- Graft: `graft check .` reported `STALE` only for the uncommitted R5 source/test graph changes;
  a freshness-aware `graft ask ... --source .` refreshed those files and confirmed the reviewed
  flow. QA did not run `graft build` because this review was constrained against modifying governed
  project state; the release owner must rebuild/check Graft before committing source changes.

The full root pytest suite was not used as PASS evidence: an earlier long run was operator-stopped
after reaching approximately 43% without an observed failure and before the final R5 ordering
change. The task-specific suites, all 52 verifiers, and all detector tests above were rerun against
the final source hashes.

## Verdict

**PASS** for the R5 source package and the independently reproduced packaged-state verification.
The two earlier QA blockers—non-exact retry counts and linked/unpinned live artifacts—and the later
cleanup-ordering regressions are resolved in the reviewed hashes. There is no remaining blocker in
the stated R5 scope.

This PASS permits the owner/PM to proceed with the separate source-release and notebook-pin gates.
It does **not** by itself authorize R5 execution in Colab, accept model quality, start another train,
open the sealed test, commit, push, upload, deploy, or publish.
