# D1 L4 capacity successor R2 — independent QA record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: **INDEPENDENT_QA_FAIL — APPEND-ONLY SUCCESSOR REQUIRED**  
Reviewer: `Codex independent source-QA session`  
Boundary: `SOURCE_AND_SYNTHETIC_ATTACK_QA_NO_COLAB_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**FAIL: 0 Critical, 1 High, 1 Medium, 0 Low.**

R2 closes the R1 attacks against Ultralytics effective-batch mutation at the live callback,
loader-wait omission, fake Git/model/data roots, extra train arguments, generic-as-OOM evidence,
SQLite symlink/hard-link substitution, duplicate/non-finite JSON, and malformed or reversed
timestamps. The fixed 24-attempt design, CV/headroom eligibility and deterministic no-cherry-pick
selection remain intact.

Two independent negative cases still pass the R2 verifier. First, effective-batch replay accepts an
arbitrary number and ordering of partial measured batches as long as one measured batch is full.
Second, execution JSONL accepts boolean `true` as schema version `1`. R2 therefore cannot authorize
a Colab capacity run, configuration selection, commit/push or notebook pin. Repair must be a new
append-only successor; R1 and R2 remain immutable audit evidence.

## Frozen bytes reviewed

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_l4_capacity_r2.py` | `c9cb41d723824c842bb210069bf23d347589cdd48613937a3ed35dbc52c8b508` |
| `detector/colab/verify_d1_l4_capacity_r2.py` | `77aa7610e1a82f95fbce2c01d768e36cbee33cf0f3b7c000263a8aacee2e6274` |
| `tests/test_d1_l4_capacity_r2.py` | `6aafd15d002f3dfbf9c588b853199e9bf19bbd8f70ed96ac438a6386bf7d2e7f` |
| `docs/review/d1_l4_capacity_r2_qa_remediation_report.md` | `37b0fbfa4dcc26e97b94ddf021f1a8ac0b17906293965c8780d12e65edea1ee9` |

The immutable R1 source and FAIL record hashes were re-read and still match the hashes frozen in
`d1_l4_capacity_r1_independent_qa_record.md`. Pre-existing PM edits to `PROJECT_MEMORY.md` and
`docs/product_roadmap.md`, plus unrelated untracked handoff material, were outside this QA scope and
were not changed.

## Findings

### H-1 — Effective-batch replay permits non-final partial batches

`run_d1_l4_capacity_r2.py:127-161` validates every step's planned and trainer batch fields, but the
actual `images` value may be any positive integer up to the planned batch. The only cross-step rule
is `full_batches > 0`. There is no rule that all non-final measured steps are full, that at most one
partial step exists, or that a partial step is last.

The real R2 replay function produced:

```text
all_full ACCEPTED {'effective_batch': 16, 'full_batch_count': 5}
one_full_then_four_partial ACCEPTED {'effective_batch': 16, 'full_batch_count': 1}
partial_before_full ACCEPTED {'effective_batch': 16, 'full_batch_count': 1}
all_partial REJECTED RuntimeError capacity attempt observed no full planned batch
```

Thus a package can retain a batch-16 identity and pass independent effective-batch replay with one
16-image step plus arbitrary 4-image non-final steps. This is narrower than R1 C-1 because the live
R2 callback rejects a changed `trainer.batch_size`, but it still violates the R1 required repair and
leaves the evidence verifier unable to prove that the measured window used the fixed candidate
batch.

**Required successor repair:** require every measured step except at most the final step to have
`images == planned_batch == trainer_batch_size`; if the final step is partial, require it to be the
only partial step. Add attacks for full-then-partials, partial-before-full and multiple partials.

### M-1 — Execution JSONL accepts a boolean schema version

`verify_d1_l4_capacity_r2.py:113-114` compares `row["schema_version"] != 1` without an exact type
check. In Python, `True == 1`, so both execution rows with JSON `"schema_version": true` pass the
supposed exact schema replay:

```text
valid ACCEPTED
wrong_type_schema_bool ACCEPTED
wrong_type_status_int REJECTED RuntimeError capacity execution journal is not a clean success
extra_key REJECTED RuntimeError capacity execution journal schema differs
reversed REJECTED RuntimeError capacity execution chronology differs
duplicate REJECTED ValueError duplicate JSON key is forbidden: schema_version
nonfinite REJECTED ValueError non-finite JSON constant is forbidden: NaN
```

The sealed-test marker itself is correctly checked with `is not False`; this finding does not show
sealed-test access. It shows that the declared strict JSONL schema is not type-strict.

**Required successor repair:** require `type(row["schema_version"]) is int` and value `1`, and add
wrong-type cases for every execution field alongside the existing duplicate, non-finite, extra-key
and chronology attacks.

## Reproduction of the six R1 attack classes

| R1 attack class | Independent R2 result |
| --- | --- |
| Pinned Ultralytics automatic batch reduction / effective batch | Live callback rejects `trainer.batch_size != planned_batch`; all-partial replay rejects, but mixed non-final partial evidence is **accepted** — H-1 |
| Loader-wait timing | PASS: injected clock showed second step `compute=2.0`, inter-batch gap `3.0`, total `5.0`; replay requires the exact sum |
| Full self-consistent forged package | PASS for the stated R1 attack: a complete 24-attempt/56-file package with fake commit/model/data, extra optimizer and batch-16 four-image steps was accepted by R1 but R2 rejected the nonexistent commit anchor |
| Fake alternate Git root with copied exact source | PASS: current R2 requires `plan.repo_root == contract.REPO_ROOT.absolute()` and rejects the alternate checkout before trusting it |
| Extra optimizer | PASS: exact train-argument key set rejects `forged_extra_optimizer=SGD` |
| Generic failure relabelled OOM | PASS: `RuntimeError: data loader failed` is rejected; controlled CUDA OOM evidence replays |
| SQLite root/ancestor/file symlink and hard link | PASS: all four attacks reject before an outside write; external attempt count remains zero |
| Duplicate/non-finite/extra/wrong-type/chronology JSONL | Duplicate, non-finite, extra-key and chronology attacks reject; boolean schema version is **accepted** — M-1 |

The source-hash-at-commit design binds an exact five-file roster to both current bytes and
`git show <commit>:<path>`. Because R2 is not yet committed, the positive clean-commit artifact path
cannot be executed at this gate; it is correctly deferred until after a source-QA PASS. The current
FAIL prevents reaching that gate.

## Controls that passed

- The inherited roster is exactly `batch {4,8,12,16} × workers {4,8} × repeats {1,2,3}` in fixed
  order: 24 isolated attempts.
- Three repetitions are mandatory; missing, duplicate or reordered candidates cannot be hidden.
- Eligibility retains throughput CV ≤ 5% and peak VRAM ≤ 80%, providing at least 20% measured
  headroom.
- Selection remains deterministic: candidates within 95% of best median throughput are ordered by
  smaller batch, fewer workers, then lower peak VRAM. Tests reject above-headroom grids and
  incomplete grids, preventing benchmark cherry-pick.
- The OOM predicate is fail-closed to `OutOfMemoryError` or the three enumerated CUDA allocation
  markers. Generic loader/bundle/hash failures remain `FAILED`.
- Database creation uses `O_EXCL | O_NOFOLLOW`; every later open checks safe components, regular
  file type, one hard link and stable device/inode identity.
- Static search of both R2 production files found no `export-test`, `--final-eval`, Pilot R3 import,
  pilot notebook reference or test-export route. `sealed_test_accessed=false` remains explicit.
- R2 does not import, mutate or compete with the live Pilot R3 workflow.

## Mechanical and adversarial evidence

| Check | Result |
| --- | --- |
| Root R1+R2 targeted tests | PASS, `27 passed, 1 skipped`; skip is root env without Torch |
| Complete detector tests | PASS, `105 passed` |
| Scoped Ruff over reviewed R1/R2 source and tests | PASS |
| Root lock | PASS, `66 packages` |
| Detector lock | PASS, `66 packages` |
| `git diff --check` before this record | PASS |
| Graft freshness/source trace before record | PASS, graph in sync |
| Full fake 24-attempt package | R1 accepted; R2 rejected at fake Git anchor |
| Effective-batch mixed-partial attack | **ACCEPTED — High blocker** |
| Boolean JSONL schema-version attack | **ACCEPTED — Medium blocker** |
| Generic-as-OOM attack | Rejected |
| SQLite root/ancestor/file symlink and hard-link attacks | Rejected; no external row/write |

Broad green checks cannot reverse the two executable negative-test failures.

## Gate disposition

| Gate | Disposition |
| --- | --- |
| L4 capacity R2 source candidate | **FAIL** |
| Commit/push or notebook pin | **NO-GO** |
| Colab capacity execution | **NO-GO** |
| Capacity result/configuration selection | **NO-GO** |
| Owner final-config approval | **NO-GO pending append-only successor + independent QA PASS** |
| Current Pilot R3 | Unchanged; continue independently |
| Sealed-test access/final evaluation | **NO-GO / not accessed** |

