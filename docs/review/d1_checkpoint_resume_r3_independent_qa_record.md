# D1 checkpoint/resume R3 independent QA record

Status: `INDEPENDENT_QA_PASS`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Reviewer: `Codex independent QA R3 session (read-only implementation review)`

Reviewed checkout: committed base `910465aca421e2150474f498c5ef4e6fc4409b39` plus the current
uncommitted R3 worktree.

Boundary: `READ_ONLY_NO_COLAB_NO_GPU_NO_DRIVE_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**PASS — 0 Critical, 0 High, 0 Medium and 0 Low findings.**

The R3 extraction repair closes the pre-training performance failure recorded by the aborted R2
L4 smoke. The reviewed successor runner processes payload members in archive order, invokes
`extractfile` once for each payload during extraction, hashes the same stream it writes, publishes
only a verified sibling partial through atomic replacement, and removes that partial on a content
mismatch. Existing roster, metadata, regular-member, path, symlink, size and SHA-256 controls stay
fail-closed.

This PASS authorizes only the next governed two-runtime L4 checkpoint/recovery smoke after the R3
source and new notebook pin are committed and pushed. It is not evidence that the smoke succeeded,
does not authorize the 100-epoch pilot, and does not authorize sealed-test access.

No Colab cell, GPU/Drive operation, model training, sealed-test access, upload, commit or push
occurred during this review.

## Scope reviewed

- `detector/colab/run_d1_colab_checkpoint_r1.py`;
- `tests/test_d1_checkpoint_colab.py`;
- `detector/colab/d1_train_checkpoint_r1.ipynb` (append-only run label changed to
  `checkpoint_smoke_seed_20261018_r2`);
- `docs/d1_colab_checkpoint_r1_operator_guide.md`;
- `docs/review/d1_checkpoint_resume_r2_l4_smoke_incident.md`.

The prior R1/R2 QA records were left unchanged.

## Independent technical findings

### Archive-order and single-read behavior

`extract_historical_bundle` derives `ordered_names` by sorting governed payload members on their
tar `offset_data`. It then opens the gzip tar once for the payload pass and calls `extractfile`
once before either the existing-file verification branch or the new-file write branch. There is no
second extraction call for a missing destination.

The new regression test instruments the archive and proves the call order is exactly the payload
archive order. The complete primary/cascade/successor Colab suite passes with the regression
included.

### Integrity and fail-closed behavior

- Manifest metadata other than the intentionally different historical Git commit must equal the
  current governed metadata before extraction.
- Manifest and governed record path sets must match exactly, and the tar roster must equal that
  set plus the embedded manifest.
- The unchanged bundle reader rejects duplicate, unsafe or non-regular members and validates the
  train/val-only manifest schema.
- Each record's SHA-256, split and kind must match the current governed record. Member size and
  streamed SHA-256 must match the manifest before a new file is published.
- The unchanged `_safe_destination` guard rejects path escape and symlink ancestors; the successor
  runner also rejects a linked destination and any pre-existing partial, including a symlink.
- Existing files are fully re-hashed from the archive and from disk and cannot be overwritten when
  either differs.
- New payloads are written with exclusive creation to `.<name>.partial`. A content size/hash
  mismatch deletes the partial and leaves the final destination absent; a verified partial is
  published with `os.replace`.

Independent adversarial harness results:

- `CONTENT_MISMATCH_FAIL_CLOSED=PASS partial_clean=true`;
- `METADATA_MISMATCH_FAIL_CLOSED=PASS`;
- `SYMLINK_ANCESTOR_FAIL_CLOSED=PASS external_write=false`;
- `ROSTER_MISMATCH_FAIL_CLOSED=PASS`.

### Notebook, incident and sealed-test boundary

The notebook remains valid unexecuted nbformat JSON with empty outputs and null execution counts.
Only the run label changes, preserving the aborted R1 Drive state as evidence. The operator guide
and incident record consistently state that R3 QA and a two-runtime L4 recovery drill are required
before the 100-epoch pilot.

The runner/notebook do not contain `export-test`, `--final-eval` or a materialized test path.
`results/experiments/sealed_test_access_log.jsonl` remained absent after QA.

## Mechanical validation

| Gate | Result |
| --- | --- |
| R3 root checkpoint/notebook tests | PASS, **9/9** |
| Detector checkpoint/resume tests | PASS, **14/14** |
| Combined checkpoint/resume scope | PASS, **23/23** |
| Primary, cascade and successor Colab tests | PASS, **66/66** |
| Complete detector pytest | PASS, **93/93** |
| Detector Ruff (`m1 tests`) and lock | PASS; lock resolves **66 packages** |
| Root Ruff (`src tests`) and lock | PASS; lock resolves **168 packages** |
| Repository verifier matrix | PASS, **52/52** |
| Successor runner/test and notebook Ruff | PASS |
| Notebook JSON readback | PASS |
| `git diff --check` | PASS |
| Graft freshness-aware review | PASS; graph refreshed for the two changed Python files before review |

## Reviewed artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_colab_checkpoint_r1.py` | `e3193ad71e4376149d925958cc8c3d415e7ca912f7adfeae86973548db701336` |
| `tests/test_d1_checkpoint_colab.py` | `3a470b2c20ee3b396303535a42b515cfd34a66a7436fc1aab6a13b1eb4aa998d` |
| `detector/colab/d1_train_checkpoint_r1.ipynb` | `55dc6a19e0f850d349cc232737083172202024d0e815886c7aaad5627fb397d9` |
| `docs/d1_colab_checkpoint_r1_operator_guide.md` | `079a183faca23fdb01078da4c7b2fda4f43a2fa238a7992fab8ec1192e360956` |
| `docs/review/d1_checkpoint_resume_r2_l4_smoke_incident.md` | `379e7946e549d5999418561c27bef5fefcb2d67fd47b35f77277f12213b9cd90` |

## Gate disposition

| Gate | QA disposition |
| --- | --- |
| R3 gzip extraction performance repair | **PASS locally** |
| R3 integrity/path/symlink/fail-closed controls | **PASS** |
| Independent QA | **PASS** (this record, 0 findings) |
| R3 commit/push and exact notebook code pin | **PENDING Owner-authorized release action** |
| C4 two-runtime L4 checkpoint/recovery smoke | **PENDING after release pin** |
| C5 100-epoch pilot | **NO-GO until C4 evidence and Owner approval** |

Current operational verdict: **GO for the R3 release commit/push and exact notebook pin, then the
governed two-runtime L4 smoke only. NO-GO for 100 epochs and NO-GO for sealed-test access.**
