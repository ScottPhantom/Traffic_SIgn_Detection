# D-05 Q4 — Owner decision on the single gate recalibration

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`).
Recorded by: Claude Code (Opus 5.5), coordinating session, on the Owner's instruction in chat.
Append-only once committed. `sealed_test_accessed=false`.

## Authority

`docs/review/d05_owner_decision_record.md` (SHA-256
`c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702`), Q4: "The gates may be
recalibrated **once**, after the pilot and before the test opens, with a new owner approval. Gates are
never lowered after the test has been seen."

This is that single recalibration. No earlier recalibration was recorded. The sealed test
`afa03d4b…` has not been opened, listed, counted or scored.

## Owner decision (verbatim)

1. The coordinating session asked: "Q4: do you use the one-time recalibration of the D-05 FP marker?"
   The Owner answered: "Có hiệu chỉnh".
2. A follow-up question offered three choices for the new FP marker: ≤ 0.40, ≤ 0.45, or keep 0.30.
   The Owner chose: "FP ≤ 0,40 (Recommended)".
3. A second question asked whether to also change the recall marker: keep 0.85, or ≥ 0.80.
   The Owner chose: "Giữ recall 0,85 (Recommended)".

The recommendation labels were written by the coordinating session.

## Gates for the final evaluation

| Gate (Q2) | Original | After this decision |
| --- | --- | --- |
| mAP50, mean of 2 seeds | ≥ 0.60 | ≥ 0.60 |
| mAP50-95 | ≥ 0.40 | ≥ 0.40 |
| Class-agnostic recall at the locked confidence | ≥ 0.85 | ≥ 0.85 |
| **FP per image** | **≤ 0.30** | **≤ 0.40** |
| Critical class with ≥ 20 test boxes, recall | ≥ 0.70 | ≥ 0.70 |
| Other class with ≥ 20 test boxes, recall (exclusion only) | ≥ 0.50 | ≥ 0.50 |
| Class support for a class gate | 20 boxes | 20 boxes |
| Latency p95 (Q5) | ≤ 100 ms | ≤ 100 ms |

Machine-readable record for the final scorer: `docs/review/generated/d05_q4_gate_recalibration_r1.json`,
SHA-256 `ba8cfe55349416ad72abfc40fc65297f6c3c2e75844b422365dacfee92e6c9bb`.
- `decision`: `RECALIBRATE_ONCE`; `package`: `D1-FINAL-EVALUATION-R1`.
- The coordinating session checked it with the scorer's own parser `_decision_gates` (accepted).

## Disclosure (must be repeated in the final report)

The new FP marker was chosen **after** the validation results were known. It was not set before the
pilot. At the approved threshold (confidence 0.19, class-aware NMS IoU 0.70; lock record
`docs/review/generated/d1_threshold_lock_r1.json`, SHA-256
`d39b0466a5285979c3da63546ebbd56d26d0030081f4df9fa6c75fc8ee96167d`), validation FP/image is:
- seed 20261018: 0.412;
- seed 20261019: 0.348;
- two-seed mean: 0.380.

The marker 0.40 sits just above that mean. Seed 20261018 alone is above it.
- A test result that passes the 0.40 marker but fails 0.30 must be reported as **passing the
  recalibrated gate, not the original one**.
- The final report states both markers and both verdicts.

## Limits

- This decision does not change the threshold lock, the selection rule, the app's demo threshold,
  or any gate other than FP per image.
- It does not decide the test-label handling and does not authorize opening the test.
- No further gate recalibration is allowed under D-05 Q4.
- Gates are never lowered after the test has been seen.
