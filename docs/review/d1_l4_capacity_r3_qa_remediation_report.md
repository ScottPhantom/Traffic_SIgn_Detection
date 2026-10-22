# D1 L4 capacity successor R3 — QA remediation report

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
Status: **REMEDIATION IMPLEMENTED — AWAITING NEW INDEPENDENT QA**  
Predecessor verdict: R2 **FAIL** with 0 Critical, 1 High and 1 Medium at
`docs/review/d1_l4_capacity_r2_independent_qa_record.md`.

## Append-only boundary

R3 adds only:

- `detector/colab/run_d1_l4_capacity_r3.py`;
- `detector/colab/verify_d1_l4_capacity_r3.py`;
- `tests/test_d1_l4_capacity_r3.py`;
- this remediation record.

It preserves the R1 and R2 implementation/review bytes and inherits their controls through explicit
successor imports. It does not run Colab/training, touch Pilot R3, upload, commit/push or access the
sealed test.

## R2 finding closure

### H-1 — multiple non-final partial measured batches

R3 keeps R2's explicit planned/effective trainer-batch checks, then adds the missing sequence rule:
every measured step except the last must contain exactly the full planned batch. Only the final
measured step may be partial because dataset cardinality may not divide the batch size. Evidence
`16,4,4` for planned batch 16 now fails at the first non-final four-image step; `16,4` remains a
valid full batch plus final partial batch.

The rule runs both immediately after a successful candidate subprocess and again in the standalone
R3 verifier.

### M-1 — boolean accepted as integer schema version

Before delegating to the strict R2 execution schema/chronology verifier, R3 requires
`type(schema_version) is int` for every execution row. It also explicitly requires
`type(sealed_test_accessed) is bool`, closing the symmetric Python equality ambiguity for governance
markers. Before semantic replay, the same exact-type policy covers plan/report/proposal/manifest,
telemetry/result identity and OOM markers, and every boolean/integer training control. Regression
probes include booleans, floats, strings and null values.

## Source and result binding

R3 extends the reviewed source roster with its new runner and verifier, recomputes the frozen plan
hash and requires all seven sources to match both the working checkout and exact bytes stored at the
claimed Git commit. All R2 independent anchors and R1 raw replay remain active.

## Remaining gate

R3 is a source candidate only. A separate independent QA session must replay every R1/R2 attack and
issue a new verdict. Commit/push, notebook creation, Colab capacity profiling and configuration
selection remain NO-GO until that PASS and later Owner authorization. The capacity runtime must
also wait until the current pilot releases the L4.
