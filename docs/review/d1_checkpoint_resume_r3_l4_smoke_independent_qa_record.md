# D1 checkpoint/resume R3 live L4 smoke independent QA record

Status: `INDEPENDENT_QA_CONDITIONAL_FAIL`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Reviewer: `Codex independent QA live-smoke session`

Reviewed code pin: `b9ce31f7278e41f51f6bd7430c2f97f653321618`

Boundary: `READ_ONLY_DRIVE_ARTIFACT_AUDIT_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**CONDITIONAL FAIL / NO-GO for the 100-epoch pilot — one blocking evidence gap.**

The synchronized Google Drive artifacts independently prove a valid fresh epoch-1 checkpoint,
verified restoration and continuation to epoch 2, a terminal `SUCCEEDED` result package, the exact
eight-file archive roster, valid SQLite and text logs, CUDA/L4 execution, and
`sealed_test_accessed=false`. All local implementation and repository gates passed.

However, the retained artifacts do not record a runtime/session identity for either attempt. The
PM report states that the prior runtime was absent and that Colab allocated a new L4 before resume,
but no durable screenshot or fresh-runtime identifier is available to this QA session. The two
attempt timestamps, separated by about six hours, do not independently prove that the resume leg
ran on a distinct runtime. Because a new-runtime recovery demonstration was an explicit acceptance
criterion, QA cannot promote the complete smoke to PASS from PM-attested UI observation alone.

This verdict does not claim that recovery failed. It means the distinct-runtime gate is not
independently reproducible from the preserved evidence. The 100-epoch pilot remains **NO-GO**.

## Evidence boundary

### Directly verified from synchronized Drive artifacts

Read-only source:

`M1_D1_Colab/runs/checkpoint_smoke_seed_20261018_r2/`

- `execution_attempts.jsonl` contains exactly two ordered attempts:
  `fresh / PAUSED_FOR_RESUME` from `2026-10-20T18:11:36Z` to `18:15:20Z`, then
  `resume / SUCCEEDED` from `2026-10-21T00:10:15Z` to `00:14:20Z`.
- `epoch-0001` and `epoch-0002` each contain the exact five-file checkpoint roster. Every file was
  independently re-hashed against its checkpoint manifest; both bindings equal
  `7174618c578953e2c144700403c0652efaa508c61272c7fbaaac4a76e901c393`.
- `recovery/latest.json` selects `epoch-0002`; its manifest SHA-256
  `c46213dcc34ac6072fce91b5e4d60df7edc5696b82a2318556d81644bc275072` and binding hash match the
  verified epoch-2 manifest.
- The preserved log records the fresh command with `--stop-after-epoch 1`, followed by
  `PAUSED_FOR_RESUME`. The resume command contains `--resume` and no stop argument. Ultralytics
  reports `Resuming training ... from epoch 2 to 2 total epochs` before the epoch-2 completion.
- `training_outcome.json` reports `resumed=true`, `completed_epoch=2`, `status=COMPLETED`, and
  `sealed_test_accessed=false`.
- `colab_execution.json` reports `status=SUCCEEDED`, `mode=resume`, the complete seven-step
  workflow roster, `error=null`, and `sealed_test_accessed=false`.
- The packaged `run_contract.json` binds commit `b9ce31f...`, a clean worktree, CUDA runtime,
  NVIDIA L4, CUDA `13.0`, driver `580.82.07`, PyTorch `2.14.1+cu130`, and Ultralytics `8.4.172`.
- `DB_logger.db` passes SQLite integrity, has the exact expected `logs` schema, and contains 2,476
  ordered records spanning both attempts. The text log is non-empty and includes both workflow
  starts, pause, true resume, training end, and terminal success.
- Neither log contains `export-test`, `--final-eval`, or a materialized test path. The local sealed
  access log remains absent.

### PM-attested but not independently preserved

- Colab UI showed the old runtime absent and subsequently allocated a new L4.
- Only the current resume backend host remained visible after completion; there is no retained
  fresh-runtime ID or screenshot with which QA can compare it.

## Result-package audit

The repository verifier accepted the archive and independently recomputed every member hash.

| Item | Verified value |
| --- | --- |
| Archive size | `35,686,597` bytes |
| Archive SHA-256 | `eae79b0dbf808be95d74b6d119c6e5e42a122fb40daf334700acf92283c186ba` |
| Manifest SHA-256 | `c3972f0be87e4a9666d91f8120d6d05718f2b76209a6398a10eadadb76cd5971` |
| Manifest outcome | `SUCCEEDED` |
| Manifest sealed flag | `false` |
| Archive roster | exact canonical eight files; all non-empty |
| SQLite integrity/schema | PASS |
| Text-log lifecycle | PASS |

The canonical roster contains `best.pt`, `last.pt`, `results.csv`, `args.yaml`,
`run_contract.json`, `colab_execution.json`, `colab_train.log`, and `DB_logger.db`.

## Mechanical validation

| Gate | Result |
| --- | --- |
| Root checkpoint/notebook tests | PASS, **9/9** |
| Complete detector pytest | PASS, **93/93** |
| Root Ruff and lock | PASS; lock resolves **168 packages** |
| Detector Ruff and lock | PASS; lock resolves **66 packages** |
| Repository verifier matrix | PASS, **52/52** |
| `git diff --check` | PASS |
| Result archive verifier | PASS; exact eight-file roster and hashes |
| Epoch-1/epoch-2 checkpoint byte verification | PASS; all **10/10** governed files |
| SQLite direct readback | PASS; integrity `ok`, **2,476** log rows |
| Graft freshness-aware source review | COMPLETE; `graft check` reported the committed test symbol index stale, so the read-only QA used a freshness-aware `graft ask` and did not rebuild repository state |

## Reviewed hashes

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_colab_checkpoint_r1.py` | `e3193ad71e4376149d925958cc8c3d415e7ca912f7adfeae86973548db701336` |
| `detector/m1/checkpoint_store.py` | `e1f8f00c036d6407d327164d907f3641427864cc35cf817336209ae5da76891c` |
| `tests/test_d1_checkpoint_colab.py` | `c691404e334f023d177df1997fcef92236785b1eb602f52feb24a18f12874cd6` |
| `detector/tests/test_checkpoint_store.py` | `b69839a4c09fc640a47c89464b274a49e552d00f2060dd349c319182e2594481` |
| `detector/colab/d1_train_checkpoint_r1.ipynb` | `546e60d9e980b64ef3a0c1fb535ad0cb23e6c2444c91fd358253797762eb9ccc` |
| PM live-smoke report | `4d13c84190dd7ba1e416bc358b6ed8eaf0d57aee56525a9f826dc9e91724f77a` |

## Required successor repair

Create an append-only R4 evidence package; do not modify the pinned R3 records.

1. At the start of each attempt, derive a privacy-preserving runtime identity, for example SHA-256
   over a run-scoped label plus `/proc/sys/kernel/random/boot_id`. Persist only the digest and the
   derivation schema, never a raw backend hostname, account token, cookie, or Colab URL parameter.
2. Bind that digest into each `execution_attempts.jsonl` entry and `colab_execution.json`.
3. Make the verifier require exactly two attempts and require the fresh and resume runtime digests
   to differ, while all checkpoint/training bindings remain identical.
4. Add positive and fail-closed tests for equal, missing, malformed, reordered, and tampered
   runtime digests.
5. Run a new two-runtime, two-epoch smoke under a new run label. Preserve both runtime digests,
   epoch checkpoints, logs, and the result package, then submit that package to a new independent
   QA session.

## Gate disposition

| Gate | QA disposition |
| --- | --- |
| Fresh epoch-1 checkpoint on Drive | **PASS — directly verified** |
| Restore and real resume to epoch 2 | **PASS — directly verified** |
| `SUCCEEDED` result package | **PASS — directly verified** |
| Exact archive/manifest roster | **PASS — directly verified** |
| SQLite and text logs | **PASS — directly verified** |
| Sealed-test boundary | **PASS — directly verified; no access observed** |
| Distinct/new runtime identity | **FAIL — PM-attested only, not independently preserved** |
| Complete independent QA | **CONDITIONAL FAIL** |
| 100-epoch D1 pilot | **NO-GO pending R4 evidence and independent QA PASS** |

