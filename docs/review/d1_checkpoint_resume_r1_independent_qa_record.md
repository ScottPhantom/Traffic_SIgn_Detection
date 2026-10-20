# D1 checkpoint/resume R1 independent QA record

Status: `INDEPENDENT_QA_FAIL`

Date: 2026-10-20 (`Asia/Ho_Chi_Minh`)

Reviewer: `Codex independent QA session (did not author the implementation)`

Reviewed checkpoint: `9c0484d921281a53f0d7804fdaa39c827fc7fc07` plus the current uncommitted
checkpoint/resume R1 worktree.

Boundary: `READ_ONLY_ADVERSARIAL_QA_NO_GPU_NO_DRIVE_NO_TRAINING_NO_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL — 0 Critical, 4 High, 1 Medium and 1 Low finding.**

The package must not be committed as the smoke-ready successor and must not be used for the L4
recovery drill or the 100-epoch pilot. The local happy-path tests pass, but the actual interruption
case can make the next resumed epoch impossible to checkpoint, two writable path surfaces follow
symlinks outside their requested roots, and a normal early-stopped run is misclassified as an
interruption. A successor repair and a new independent QA session are required.

No Colab cell, GPU training, Drive operation, sealed-test access, upload, commit or push occurred
during this review.

## Findings

### H-1 — an interrupted generation permanently blocks the same epoch after resume

`CheckpointStore.save()` intentionally leaves an incomplete `epoch-NNNN` directory for forensic
review. On the new runtime, the valid pointer correctly restores epoch `N-1`, but when resumed
training completes epoch `N`, `save()` refuses the already-existing incomplete generation before
it can write a replacement:

```text
INTERRUPTION= simulated reset
LATEST_AFTER_INTERRUPTION= 1
RESUME_EPOCH2_SAVE= RuntimeError checkpoint generation already exists: .../snapshots/epoch-0002
PARTIAL_EXISTS= True
```

This reproduces the exact failure the package is meant to recover from. The existing regression
test avoids it by proceeding from an interrupted epoch 2 directly to epoch 3; real Ultralytics
resume proceeds from epoch 1 to epoch 2 and therefore stops at the collision.

Required remediation: use attempt-unique staging names which cannot collide with the canonical
generation, or explicitly quarantine a fully verified incomplete generation before retry. The
canonical `epoch-NNNN` name and `latest.json` may advance only after a complete verified copy.
Add a regression that interrupts epoch 2, deletes all local runtime state, restores epoch 1 and
successfully checkpoints resumed epoch 2.

### H-2 — `--results-dir` symlinks are resolved and accepted as external write targets

`resumable_train.execute()` calls `.resolve()` on `args.results_dir` before applying any lexical or
`lstat()` guard. An adversarial test supplied a repository-local `results_link` symlink to a temp
directory outside the repository. Fresh training returned `PAUSED_FOR_RESUME` and created the run
under that external target:

```text
OUTCOME_STATUS= PAUSED_FOR_RESUME
RUN_DIR= .../outside/D1_yolo11s_wp33_ffffffff_20261018_..._qa
EXTERNAL_WRITE= True True
```

Required remediation: preserve the lexical path, reject a symlink in every existing component
before resolving or writing, require the local results root to be the intended repository results
directory, then re-check containment and component types immediately before every write/restore.
Add fresh and resume regression attacks for root, ancestor and nested symlinks.

### H-3 — resume logging and attempt records follow child symlinks outside `state-dir`

The runner guards only the `state_dir` path itself. Existing `colab_train.log`, `DB_logger.db` and
`execution_attempts.jsonl` children are opened by APIs that follow symlinks. A read-only temp-dir
attack placed `colab_train.log` and `execution_attempts.jsonl` symlinks to external sentinel files,
then invoked resume with an invalid bundle. The runner failed as expected on the bundle but had
already modified both external files:

```text
RC= 1
OUTSIDE_LOG_CHANGED= True
OUTSIDE_ATTEMPT_CHANGED= True
```

Required remediation: guard every writable child with lexical containment plus component-wise
`lstat()`, reject all symlink/non-regular targets, and use exclusive/atomic no-follow writes where
applicable. Add attacks for all state/log/result outputs in both fresh and resume modes.

### H-4 — legitimate Ultralytics early stopping is recorded as an interruption

After `model.train()` returns normally, the code treats every `latest.completed_epoch < epochs`
case as `PAUSED_FOR_RESUME`, regardless of whether `--stop-after-epoch` caused the stop. A fake
trainer that returned normally after an early-stop epoch, with `stop_after_epoch=None`, produced:

```text
NORMAL_TRAIN_RETURN_WITH_EARLY_STOP_OUTCOME= PAUSED_FOR_RESUME COMPLETED_EPOCH= 1
RUN_CONTRACT_STATUS= STARTED
```

The long-run configuration retains `patience=30`, so early stopping is a normal possible terminal
outcome. This implementation would withhold the result package and direct the operator into an
invalid resume instead of finalizing the trained run.

Required remediation: distinguish an intentional recovery-drill pause from a normal return due to
early stopping. A normal terminal train return must finalize the run and record the actual terminal
epoch/status; only the explicit `--stop-after-epoch` path may emit `PAUSED_FOR_RESUME`. Add a
regression for early stopping before the configured maximum.

### M-1 — production resume does not enforce the required contiguous first epoch

The fake test itself chooses `start = 2 if resume else 1`; it does not demonstrate that production
code derives and enforces the first resumed epoch from the verified manifest. The callback accepts
any `trainer.epoch + 1` that has a free generation name. A resumed trainer that skips from epoch 1
to epoch 3 can advance the pointer without an explicit continuity failure.

Required remediation: retain the verified `completed_epoch`, require the first resume callback to
equal `completed_epoch + 1`, require every later callback to be contiguous, and fail before pointer
advancement on a gap or replay. Add fake resume cases for the exact next epoch, repeated epoch and
skipped epoch.

### L-1 — the successor notebook fails Ruff with five findings

`uv run ruff check detector/colab/d1_train_checkpoint_r1.ipynb` reports three `I001` import-block
findings and two `E501` long-line findings. Earlier Colab packages use notebook Ruff as an explicit
quality gate.

Required remediation: format the notebook code cells without executing them, preserve empty
outputs/execution counts, rerun Ruff and re-read the JSON.

## Controls that passed

- The supplied detector tests pass: checkpoint interruption/tamper/binding/retention/callback and
  fake fresh/resume happy path.
- Independent tamper attacks against pointer generation, manifest bytes, `last.pt` and `best.pt`
  all fail closed.
- Interrupting each of the five artifact copies leaves `latest.json` selecting the prior complete
  generation.
- Normal retention keeps the active and previous complete generations. A corrupted older rollback
  is not selected; the active pointer remains verifiable.
- The historical bundle is accepted with separate provenance identities:
  source commit `ffc2b448f06c45dae597de5b565cab64c0377573`, current code commit
  `9c0484d921281a53f0d7804fdaa39c827fc7fc07`, 5,888 files and
  `test_included=false`.
- A synthetic successful successor package has the exact eight-file roster and passes the unchanged
  base `verify_result_archive()` contract with `terminal_outcome=SUCCEEDED` and
  `sealed_test_accessed=false`.
- The notebook is valid JSON, unexecuted, has zero outputs, retains the fail-closed
  `PENDING_AFTER_QA` commit placeholder, uses the exact approved bundle pins and does not contain
  `export-test`, `--final-eval` or a materialized test path.
- The pinned predecessor files are byte-unchanged against their latest approved pins:
  `run_d1_colab.py` =
  `6a508eebcb83915201569bc74913a3dd546b288caf2331a9b3e4bd7a567500bc` and
  `d1_train.ipynb` =
  `12b29493ec69c38adc4de9443756d8dbe5a548a38edaf7cab4641b757b74d52f`.
- `results/experiments/sealed_test_access_log.jsonl` remains absent.

## Reviewed artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/checkpoint_store.py` | `a74d4f63172e03393484fbb5f9511efc4e712698dbc2bd9019cc46e6323f3d2e` |
| `detector/m1/resumable_train.py` | `5de5096d100d156e4dd8b5e78ca3dd13bc3ed2cec76d9e3d6427c68a87b03e6e` |
| `detector/colab/run_d1_colab_checkpoint_r1.py` | `580e0f37f65a804a5065353f47bf91a4c95854e5821f8d0e99624fa1445eae42` |
| `detector/colab/d1_train_checkpoint_r1.ipynb` | `a36c33d6e1b3d3fa0b56a2cf0c0ea378a61ac806c89b7ce77a24c69f2e5cac3b` |
| `detector/tests/test_checkpoint_store.py` | `eb052800b7e7a254494bd50844065278f7128bb367ef78ef302a3d456b95385f` |
| `detector/tests/test_resumable_train.py` | `82ac3e475c974f51c1cf6e9f918f0628930a7446b9940191f278185b06a471d5` |
| `tests/test_d1_checkpoint_colab.py` | `180b8dbe3585ec87f3cee3f7076b5a3cb5156309826addfeaa45b8fd5f9e4555` |
| `docs/d1_colab_checkpoint_r1_operator_guide.md` | `14258b1835595f23bdb5b7a623869b4c7735af8c1440745cacf6a23a6ec73ef4` |
| `docs/review/d1_long_train_checkpoint_plan_r1.md` | `807e91f03d405b8fe03b0a9bc684eb59d40c38da4db2de1310f15a986fe90ff7` |
| `docs/review/d1_checkpoint_resume_r1_implementation_record.md` | `0bd0369dafcccd4ba98f612bacf02950665941e6f1fe74ec89e1349d070825c8` |

## Mechanical validation

| Gate | Result |
| --- | --- |
| Supplied targeted checkpoint/resume tests | PASS, **10/10** (`7 detector + 3 root`) |
| Existing primary/cascade plus successor Colab tests | PASS, **60/60** |
| Complete detector pytest | PASS, **86/86** |
| Detector Ruff (`m1 tests`) and lock | PASS; lock resolves **66 packages** |
| Root Ruff (`src tests`) and lock | PASS; lock resolves **168 packages** |
| Repository verifier matrix | PASS, **52/52** |
| Successor notebook Ruff | **FAIL, 5 findings** |
| `git diff --check` | PASS |
| Graft | `graft check .` reports **STALE** for the new successor files; QA did not rebuild the shared graph because this session is implementation-read-only |

## Gate disposition

| Gate | QA disposition |
| --- | --- |
| C1 — crash-safe store and interruption recovery | **FAIL** (H-1) |
| C2 — executable successor CLI/runner/notebook | **FAIL** (H-2, H-3, H-4, M-1, L-1) |
| C3 — independent QA | **FAIL** (this record) |
| C4 — one-epoch L4 smoke and Drive readback | **BLOCKED; not run** |
| C5 — Owner authorization for 100 epochs | **BLOCKED; not requested** |

Current operational verdict: **NO-GO for the L4 smoke and NO-GO for long training.** Preserve this
FAIL record, implement an append-only R2 repair, rebuild/check Graft, and request a new independent
QA session before any commit/push or Colab execution.
