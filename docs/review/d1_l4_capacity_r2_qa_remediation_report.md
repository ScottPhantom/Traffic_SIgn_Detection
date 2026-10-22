# D1 L4 capacity successor R2 — QA remediation report

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
Status: **REMEDIATION IMPLEMENTED — AWAITING NEW INDEPENDENT QA**  
Predecessor verdict: `d1_l4_capacity_r1_independent_qa_record.md`, immutable **FAIL** with
1 Critical and 5 High findings.

## Append-only boundary

R2 adds new runner, verifier and regression tests. It does not modify the six source/evidence files
hash-pinned by the R1 FAIL record. It does not touch the running Pilot R3, access Colab, train a
model, upload data, commit/push or read the sealed test.

New implementation:

- `detector/colab/run_d1_l4_capacity_r2.py`
- `detector/colab/verify_d1_l4_capacity_r2.py`
- `tests/test_d1_l4_capacity_r2.py`

## Finding closure

### C-1 — silent Ultralytics batch reduction

R2 records both planned batch and `trainer.batch_size` for every measured step. The callback fails
immediately when the effective trainer batch changes, including the pinned Ultralytics first-epoch
OOM retry path. Successful evidence also needs at least one full planned batch; a final partial
batch remains allowed. The R2 verifier independently replays the exact step schema and rejects a
planned batch 16 package containing only four-image steps.

### H-1 — loader wait omitted

R2 records the interval from the previous `on_train_batch_end` to the next
`on_train_batch_start`, then defines measured step seconds as compute seconds plus that inter-batch
gap. This steady-state interval includes DataLoader iterator wait and preprocessing before the next
callback. The raw evidence preserves both components; replay requires their exact sum.

### H-2 — self-consistent forged trust roots and extra train controls

The frozen plan now binds an exact five-file reviewed source roster. R2 verification requires:

- the claimed Git commit to exist;
- every current source hash to match the plan;
- `git show <commit>:<path>` bytes to match the same source hash;
- the approved local pretrained model binding;
- the current governed contract, which rechecks D-05, export/class/split hashes and train/val
  materialization;
- the approved detector lock and a clean NVIDIA L4 CUDA environment record;
- the exact train-argument key set, with no extra optimizer or other behavior-changing field.

### H-3 — generic failure relabelled OOM

R2 uses a closed predicate: exception type `OutOfMemoryError`, or an error containing one of
`cuda out of memory`, `cudnn_status_alloc_failed`, or `cublas_status_alloc_failed`. The live runner
and standalone verifier use the same predicate. Data-loader, bundle, hash and other runtime errors
remain `FAILED` and terminate the matrix.

### H-4 — SQLite symlink write

R2 creates the database with `O_EXCL | O_NOFOLLOW`, then checks every open/write with component-wise
safe-directory validation plus `lstat`: regular file, not a symlink, exactly one hard link. It
compares device/inode before and after opening and refuses replacement. Regression attacks cover a
database-file symlink to an external database and a hard-link substitute; neither receives a row.

### H-5 — permissive execution JSONL

R2 parses every journal line with duplicate-key and non-finite rejection, requires exact
STARTED/SUCCEEDED schemas, timezone-aware timestamps, strict chronology, exact plan/report hashes
and boolean `sealed_test_accessed=false`. Duplicate contradictory sealed markers, malformed or
naive timestamps, extra/missing fields and reversed chronology fail.

## Preserved capacity policy

The R1 experiment design remains unchanged: 24 isolated attempts for batch 4/8/12/16 × workers
4/8 × three repetitions, `imgsz=1280`, one epoch at 25% train data, deterministic seed, AMP,
`fliplr=0`, no validation/model-quality selection, CV ≤5%, peak VRAM ≤80%, and the deterministic
95%-throughput tie policy. Output remains `PROPOSAL_NOT_OWNER_APPROVED` and
`sealed_test_accessed=false`.

## Remaining gates

R2 is not approved merely because remediation tests pass. A separate QA session must reproduce the
six R1 attacks against the real R2 entry points and review the full source. Only a new QA PASS may
permit Owner review for commit/push. A clean commit-pinned notebook and an Owner-authorized idle-L4
run still come later; the live pilot must finish and release the GPU first.
