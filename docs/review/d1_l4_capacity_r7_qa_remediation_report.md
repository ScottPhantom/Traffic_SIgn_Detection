# D1 L4 capacity successor R7 — QA remediation report

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
Status: **REMEDIATION IMPLEMENTED — AWAITING NEW INDEPENDENT QA**  
Predecessor verdict: R6 **FAIL** with 0 Critical, 1 High and 1 Medium at
`docs/review/d1_l4_capacity_r6_independent_qa_record.md` (SHA-256
`0522077771ddd2c81ef1570ac3eca71584104d1e3c1817917b1a640743fbd6c8`).

## Append-only boundary

R7 adds only its runner, verifier, tests and this report. R1–R6 implementation and QA records stay
unchanged. No Colab execution, training, Pilot interaction, upload, commit/push or sealed-test
access occurred.

## H-1 — portable pinned Torch/CUDA identity

R7 no longer compares Colab evidence with the verifier host's installed wheel metadata. It checks
the recorded public Torch version against detector pin `2.14.1`, then independently requires the
local CUDA build suffix to match the recorded runtime (`CUDA 13.0` → `+cu130`). The canonical
observed Colab identity `2.14.1+cu130` is therefore portable to M1 QA, while a missing, wrong-public
or wrong-CUDA suffix fails. Python remains constrained to numeric `3.12.x`; Ultralytics remains
exactly pinned to `8.4.172`.

## M-1 — chronological and physical telemetry replay

R7 additionally requires:

- measured batch indexes to be consecutive from the governed warm-up offset (`11..N`);
- attempt start strictly before finish;
- GPU samples strictly increasing and within the attempt interval;
- stable GPU UUID and total VRAM, both equal to the frozen plan;
- utilization in `[0,100]`, used VRAM in `[0,total]`, positive total VRAM, nonnegative power and
  temperature in `[0,125]` Celsius.

Regression tests reproduce the combined R6 attack: impossible batch order, reversed/duplicate or
out-of-range sample times, negative power/temperature and invalid memory/utilization/UUID now fail.
The source-at-commit roster extends append-only through the R7 runner/verifier.

## Remaining gate

R7 remains a source candidate pending a new independent QA session. A PASS would not itself run the
profile: Owner authorization, commit/push, a clean commit-pinned notebook and an idle L4 after the
current pilot are still required. The result remains `PROPOSAL_NOT_OWNER_APPROVED` and is not model
quality evidence.
