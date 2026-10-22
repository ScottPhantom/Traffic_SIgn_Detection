# D1 L4 capacity successor R4 — QA remediation report

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
Status: **REMEDIATION IMPLEMENTED — AWAITING NEW INDEPENDENT QA**  
Predecessor verdict: R3 **FAIL** with 0 Critical, 0 High and 1 Medium at
`docs/review/d1_l4_capacity_r3_independent_qa_record.md`.

## Append-only boundary

R4 adds a new runner, verifier, regression file and this record. R1–R3 bytes and their independent
FAIL records remain unchanged. R4 has not run Colab/training, accessed Pilot R3 or the sealed test,
uploaded data, or committed/pushed.

## M-1 closure — nested plan/telemetry type and value

R4 applies an exact four-key schema to every frozen plan roster identity and every telemetry
attempt identity. `attempt_id` must be an exact string; `batch`, `workers` and `repeat` must each be
exact integers, so Python booleans and floats cannot compare through as IDs. The telemetry identity
must then equal its corresponding plan row.

Telemetry `schema_version` was already required to have exact integer type in R3; R4 additionally
requires its value to equal `1`. The R3 top-level type checks, non-final full-batch sequence rule,
and all R2/R1 trust, timing, OOM, SQLite, JSONL, archive and selection controls remain active.

The reviewed source-at-commit roster is extended append-only with the R4 runner/verifier, for nine
source files total.

## Remaining gate

R4 is still only a source candidate. A new independent QA session must run all prior attacks and
issue PASS before any Owner request to commit/push or create a commit-pinned notebook. Colab capacity
profiling remains NO-GO while the live pilot owns the L4 and until explicit later authorization.
