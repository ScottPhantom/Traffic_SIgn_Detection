# D1 L4 capacity successor R6 — QA remediation report

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
Status: **REMEDIATION IMPLEMENTED — AWAITING NEW INDEPENDENT QA**  
Predecessor verdict: R5 **FAIL** with 0 Critical, 1 High, 2 Medium and 1 Low at
`docs/review/d1_l4_capacity_r5_independent_qa_record.md`.

## Append-only boundary

R6 adds only its runner, verifier, tests and this report. R1–R5 implementation and QA records stay
unchanged. No Colab execution, training, Pilot interaction, upload, commit/push or sealed-test
access occurred.

## H-1 — exact environment and independent runtime identities

R6 requires the environment to contain exactly the canonical detector environment keys plus L4
UUID and total VRAM. It delegates the base record to `contract.validate_environment_record` with
`require_clean=true`, which enforces exact strings, exact booleans and exact integer dirty count.
It then independently checks:

- plan/report Git commit equality;
- current pinned Python, Torch and Ultralytics versions;
- `machine=x86_64`, `hardware_chip=UNKNOWN`, Linux platform;
- exact `NVIDIA L4`/CUDA runtime, non-placeholder CUDA/driver;
- valid GPU UUID and positive finite total VRAM.

Extra keys, `git_dirty_files=false`, blank/non-string or forged version identities now fail.

## M-1 — exact raw timing and GPU telemetry

Every step now requires exact integer `batch_index`, image count, planned batch and trainer batch;
all timing fields must be finite non-boolean numbers. Every GPU sample has an exact seven-key
schema, timezone-aware timestamp, valid UUID and finite non-boolean utilization/memory/power/
temperature. Missing time/temperature, boolean numerics, string indexes and float batch identities
fail before inherited replay.

## M-2 — exact manifest governance

The evidence manifest must use the exact six-key schema, exact string status
`EVIDENCE_PACKAGED`, a non-empty file list and exact path/size/hash record schemas. Existing
canonical hash, disk inventory and archive-member replay remain active.

## L-1 — boolean zero aggregates

R6 type-checks report count fields as exact integers and every other aggregate as a finite
non-boolean number for candidates and repetitions. Boolean `false` can no longer substitute for a
zero aggregate, even in the bounded downstream-hash case.

The source-at-commit roster extends append-only through the R6 runner/verifier.

## Remaining gate

R6 remains a source candidate pending a new independent QA session. A PASS would not itself run the
profile: Owner authorization, commit/push, a clean commit-pinned notebook and an idle L4 after the
current pilot are still required.
