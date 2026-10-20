# D1 checkpoint/resume R2 independent QA record

Status: `INDEPENDENT_QA_PASS`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Reviewer: `Codex independent QA R2 session (did not author the implementation and did not reuse
the R1 verdict)`

Reviewed checkout: committed base `9c0484d921281a53f0d7804fdaa39c827fc7fc07` plus the current
uncommitted checkpoint/resume R2 worktree.

Boundary: `READ_ONLY_ADVERSARIAL_QA_NO_GPU_NO_DRIVE_NO_TRAINING_NO_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**PASS — 0 Critical, 0 High, 0 Medium and 0 Low findings.**

All four R1 High findings, the R1 Medium finding and the R1 Low finding were independently
reproduced against the R2 repair and are closed. The package is ready for the next local release
step and, after the reviewed source is committed and pushed and the fail-closed notebook
`CODE_COMMIT = "PENDING_AFTER_QA"` placeholder is replaced by that exact commit, for the governed
one-epoch L4 smoke/recovery drill. This PASS does not assert that the L4 smoke has run, does not
authorize the 100-epoch pilot and does not approve sealed-test access.

No Colab cell, GPU/Drive operation, real model training, sealed-test access, upload, commit or push
occurred during this review.

## R1 finding closure

### H-1 — interrupted epoch can be recovered and checkpointed again: closed

An independent harness saved epoch 1, interrupted the `best.pt` copy while saving epoch 2, deleted
the complete local runtime tree, restored epoch 1 into a new runtime and then saved the resumed
epoch 2. The old attempt-unique `.epoch-0002.<uuid>.partial` remained as forensic evidence;
`latest.json` stayed on epoch 1 until the resumed epoch 2 snapshot verified, then advanced to
`epoch-0002`. The leftover partial did not collide with the canonical generation.

Result: `H1_MATRIX=PASS`.

### H-2 — results-root links cannot redirect writes: closed

The real `resumable_train.execute()` path was attacked in both fresh and resume modes at root,
ancestor and nested run-directory positions, using both live and broken symlinks. All 24 cases
failed before an external target was created or modified. Resume attacks first created a valid
epoch-1 checkpoint, deleted the local run and then installed the attacked path, so they exercised
the actual restore path rather than only the path helper.

Result: `H2_MATRIX=PASS cases=24`.

### H-3 — state/log/result links cannot redirect writes: closed

The real successor runner entry point was attacked for all five governed top-level writable state
children in both fresh and resume modes, with live and broken symlinks:

- `colab_train.log`;
- `DB_logger.db`;
- `colab_execution.json`;
- `colab_execution.json.tmp`;
- `execution_attempts.jsonl`.

All 20 cases failed without changing or materialising the external target. The dynamic result
archive, manifest and both partial output names were separately attacked in fresh and resume
package modes with live and broken symlinks; all 16 cases failed without an external write. The
eight required package inputs are independently constrained to non-empty regular non-symlink
files.

Results: `H3_STATE_MATRIX=PASS cases=20`; `H3_RESULT_MATRIX=PASS cases=16`.

### H-4 — normal early stopping is terminal and packageable: closed

A fake Ultralytics trainer returned normally after epoch 1 while the configured maximum was three
epochs and no recovery-drill stop was requested. The actual executor returned
`COMPLETED_EARLY_STOPPED`, recorded completed epoch 1 and finalized `run_contract.json` as
`TRAINED`. The resulting run was passed through the successor packager; the unchanged base
`verify_result_archive()` accepted the canonical eight-file archive with
`terminal_outcome=SUCCEEDED` and `sealed_test_accessed=false`.

Result: `H4=PASS`, package file count `8`, base verifier `PASS`.

### M-1 — resume epoch continuity is enforced before pointer movement: closed

Three independent resume cases started from the same verified epoch-1 state. Exact epoch 2 was
accepted and advanced the pointer to `epoch-0002`. Replayed epoch 1 and skipped epoch 3 both raised
the non-contiguous-epoch error while `latest.json` remained byte-equivalent to the epoch-1 pointer.

Result: `M1_CONTINUITY=PASS`.

### L-1 — notebook quality and execution state: closed

Standalone Ruff passes for `detector/colab/d1_train_checkpoint_r1.ipynb`. JSON readback reports
nbformat 4.5, seven cells and six code cells; every code cell has null execution count and empty
outputs. The fail-closed `PENDING_AFTER_QA` placeholder remains, while `export-test`,
`--final-eval` and `data/processed/m1_yolo/test` are absent.

## Additional adversarial controls

- Tampering with `latest.json`, `checkpoint_manifest.json`, `weights/last.pt` or
  `weights/best.pt` independently failed closed.
- The historical train/val bundle was read and re-hashed. It is exactly 766,226,800 bytes with
  SHA-256 `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641`,
  contains 5,888 governed records plus its manifest, has `test_included=false`, and has no missing
  or differing destination records in the current checkout.
- The successor extraction contract accepted the intentional provenance separation: source bundle
  commit `ffc2b448f06c45dae597de5b565cab64c0377573`, reviewed code base commit
  `9c0484d921281a53f0d7804fdaa39c827fc7fc07`, 5,888 files and no test split.
- The pinned predecessor hashes remain unchanged:
  `run_d1_colab.py` =
  `6a508eebcb83915201569bc74913a3dd546b288caf2331a9b3e4bd7a567500bc` and
  `d1_train.ipynb` =
  `12b29493ec69c38adc4de9443756d8dbe5a548a38edaf7cab4641b757b74d52f`.
- `results/experiments/sealed_test_access_log.jsonl` remains absent after the review.

## Mechanical validation

| Gate | Result |
| --- | --- |
| R2 checkpoint/resume and notebook tests | PASS, **22/22** (`14 detector + 8 root`) |
| Primary, cascade and successor Colab tests | PASS, **65/65** |
| Complete detector pytest | PASS, **93/93** |
| Detector Ruff (`m1 tests`) and lock | PASS; lock resolves **66 packages** |
| Root Ruff (`src tests`) and lock | PASS; lock resolves **168 packages** |
| Repository verifier matrix | PASS, **52/52** |
| Successor notebook Ruff | PASS |
| `git diff --check` | PASS |
| Graft | `graft build .` completed; `graft check .` reports **OK**, 2,597/2,597 wiring nodes synchronized |

## Reviewed artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/checkpoint_store.py` | `e1f8f00c036d6407d327164d907f3641427864cc35cf817336209ae5da76891c` |
| `detector/m1/resumable_train.py` | `0a963d4bc246613402283531b6280836606ac1f5b35b5d215b3959a1354aa6e7` |
| `detector/colab/run_d1_colab_checkpoint_r1.py` | `97a053db0f83ea0b1a110b7dbca53f5f96b923448e8dab613a15c7a4790bf8e9` |
| `detector/colab/d1_train_checkpoint_r1.ipynb` | `9a56cae6ea20457cba5dd32c5fd51465f66c68cb26c7cf84a7a49a88c2f523b7` |
| `detector/tests/test_checkpoint_store.py` | `b69839a4c09fc640a47c89464b274a49e552d00f2060dd349c319182e2594481` |
| `detector/tests/test_resumable_train.py` | `a7579979dfeb2bb758bfff7f715329cf697ad50d0748aeccb32726ba2104d2fc` |
| `tests/test_d1_checkpoint_colab.py` | `1fa88335d9386a868295732a0b5db510d70655830030186fbdc52819591f0505` |
| `docs/d1_colab_checkpoint_r1_operator_guide.md` | `14258b1835595f23bdb5b7a623869b4c7735af8c1440745cacf6a23a6ec73ef4` |
| `docs/review/d1_long_train_checkpoint_plan_r1.md` | `a53f51d57c744d65cfcd1f68da9f41e7f0ee9065ddbd0eefd21738cde859dac9` |
| `docs/review/d1_checkpoint_resume_r1_implementation_record.md` | `0bd0369dafcccd4ba98f612bacf02950665941e6f1fe74ec89e1349d070825c8` |
| `docs/review/d1_checkpoint_resume_r2_qa_remediation_report.md` | `5531271cb334ed7f2873b8d26ae6b705135352c93a91156537d4b44cbe450c78` |

## Gate disposition

| Gate | QA disposition |
| --- | --- |
| C1 — crash-safe store and interruption recovery | **PASS** |
| C2 — executable successor CLI/runner/notebook | **PASS locally** |
| C3 — independent QA | **PASS** (this record, 0 findings) |
| C4 — one-epoch L4 smoke and Drive readback | **READY AFTER PINNED COMMIT/PUSH; not run** |
| C5 — Owner authorization for 100 epochs | **BLOCKED until C4 evidence and Owner approval** |

Current operational verdict: **GO for commit/push and the governed one-epoch L4 smoke/recovery
drill only after replacing the notebook placeholder with the exact reviewed pushed commit. NO-GO
for the 100-epoch pilot until C4 demonstrates a Drive checkpoint, local-runtime deletion, resume
and final package readback.**
