# D1 Colab operator guide R4 QA remediation report

Status: `R4_AWAITING_INDEPENDENT_QA`

Date: `2026-10-19` (`Asia/Ho_Chi_Minh`)

R3 independent QA verdict: `FAIL — 0 Critical, 0 High, 1 Medium, 0 Low`

## Remediation

R4 removes the contradictory threshold-lock step before final-seed training. The operator sequence
now requires:

1. pilot validation review and, only if needed, an append-only gate-successor record with explicit
   Owner approval;
2. a final training-configuration lock that does not claim to lock confidence or NMS;
3. all three approved seeds trained with the same configuration;
4. standalone verification of every result package and one validation evaluation report per seed;
5. exactly one `m1.cli lock-thresholds` invocation consuming those three governed validation
   reports;
6. independent QA and a clean commit of the unchanged threshold lock before any sealed-test
   access.

The guide includes the executable CLI shape and explicitly forbids a pilot-only threshold lock or
a second threshold-lock operation after test access. R4 changes no notebook, runner, dataset,
bundle, model, test seal, gate or Owner decision. The R1, R2 and R3 QA FAIL records remain
immutable.
