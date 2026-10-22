# D1 L4 capacity successor R8 — QA remediation report

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
Status: **REMEDIATION IMPLEMENTED — AWAITING NEW INDEPENDENT QA**  
Predecessor verdict: R7 **FAIL** with 0 Critical, 1 High, 0 Medium and 2 Low at
`docs/review/d1_l4_capacity_r7_independent_qa_record.md` (SHA-256
`8efc7c0b6104a22cf7abaecbf6df9be7355e6149623e5bf6bfafaa46f1b21aa6`).

## Append-only boundary

R8 adds only its runner, verifier, tests and this report. R1–R7 implementation and QA records stay
unchanged. No Colab capacity execution, training, Pilot interaction, upload, commit/push or sealed-
test access occurred.

## H-1 — exact verified L4 runtime identity

R8 binds capacity evidence to the independently verified Colab L4 runtime: Torch
`2.14.1+cu130`, CUDA `13.0`, NVIDIA driver `580.82.07` and Ultralytics `8.4.172`. Numeric Python
`3.12.x`, Linux/x86_64 and `NVIDIA L4` controls remain inherited. Malformed/self-consistent CUDA,
suffix injection, alternate CUDA builds and arbitrary driver strings now fail. A legitimate future
runtime change requires an append-only, Owner-reviewed successor rather than implicit acceptance.

## L-1 — self-contained type helper

The R8 type helper installs its own R8 environment and telemetry callbacks across both predecessor
layers for the duration of the check and restores every callback in `finally`. Direct helper and
official package verification therefore execute the same runtime checks without relying on a
caller-installed global patch.

## L-2 — exact total-VRAM identity

GPU `memory_total_mib` must now equal the first sample and frozen plan value exactly after inherited
finite non-boolean validation. A difference of `0.00001 MiB` is rejected; tolerance remains only in
derived arithmetic where it is justified.

The source-at-commit roster extends append-only through the R8 runner/verifier.

## Remaining gate

R8 remains a source candidate pending a new independent QA session. PASS would authorize only the
next preparation gate: Owner-approved commit/push and a clean commit-pinned notebook. The 24-attempt
capacity run must wait until the current pilot releases L4. Its result remains
`PROPOSAL_NOT_OWNER_APPROVED`, is not model-quality evidence and cannot authorize a final training
configuration without Owner approval and a configuration-bound two-runtime resume smoke.
