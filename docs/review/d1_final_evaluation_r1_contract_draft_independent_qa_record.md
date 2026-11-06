# Independent QA — D1 final evaluation R1 draft contract

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`)  
Reviewer: separate Codex sub-agent; did not write the draft.  
Scope: document review only; no source edits, inference, training, threshold lock, S2 live-state access or sealed-test access.  
Draft SHA-256: `17a0bf3df57de66dd6369a7da78c58ad4b9df52f195fbd3a0aa1933f1cab1d71`.

Verdict: PASS — draft preparation only; final evaluation remains unauthorized.

## Evidence and checks

1. The draft has the required status `DRAFT_NOT_AUTHORIZED` and keeps `sealed_test_accessed=false`. It distinguishes a document proposal from an executable test procedure or approved threshold lock.
2. Its five prerequisites match the handoff order: three independently QA-passed run results; independently QA-passed R3 lock record with Owner approval; separate Owner decision on the one allowable pre-test gate recalibration; finalized contract and QA; then explicit Owner approval for the single test opening. It does not grant seed-20261020 training permission.
3. D-05 Q1/Q2/Q5 were checked against `docs/review/d05_owner_decision_record.md` (SHA-256 `c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702`). The draft carries the three-seed mean/SD; mAP50 0.60, mAP50-95 0.40, class-agnostic recall 0.85, FP/image 0.30, supported critical/other class recalls 0.70/0.50, report-only small/low-support breakdown and D-02 bootstrap CI. The 32-class phrase is explicitly attributed to the prior D-05 record, not a new count. Latency specifies M1 Pro MPS, batch 1, 50 warm-ups, 300 measured iterations and p95 100 ms including preprocessing/inference/NMS.
4. The draft names the existing `m1.cli evaluate --split test --final-eval --reason ... --threshold-lock ...` and `contract.log_test_access` only as mechanisms. It explicitly rejects use of legacy schema-1 lock alone for corrected validation R3, consistent with the QA-passed `docs/review/d1_threshold_lock_r1_contract.md` (SHA-256 `726932dbcd32842658477c9d36f4dc7c240d412d92119e76e5b3536a4d278f0f`). It requires a separately implemented and QA-passed R3 writer/verifier/final reader or proven equivalent scorer before an executable command is fixed.
5. The one-time rule, immutable weights/thresholds/gates after seeing test, stop on hash drift, and independent result QA before publication are present. The draft makes no acceptance or real-vehicle safety claim.

## Limits

This QA is a **document conformance check**. It did not validate future code, any completed S2 run, three-seed results, the future lock/proof or test performance. A later independent QA of the finalized contract and implementation is still required. `sealed_test_accessed=false`.
