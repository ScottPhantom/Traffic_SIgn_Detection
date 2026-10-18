# D1 dual-baseline owner decision

Status: `OWNER_APPROVED_D1_DUAL_BASELINE`
Decision date: `2026-10-18` (`Asia/Ho_Chi_Minh`)

The owner selected option C: run both proposed D1 baselines.

1. A 54-class YOLO detector remains the primary D-05 track and is evaluated under the existing
   detector gates.
2. A one-class sign detector plus classifier is authorized as a comparison baseline.

The second baseline does not silently inherit the 54-class D-05 per-class gates. Its classifier
taxonomy, acceptance metrics, threshold protocol and sealed-test eligibility require an explicit
append-only addendum before final evaluation. Until that addendum exists, it may be built and
validated on train/validation data but may not open or use the sealed test.

Relevant inputs:

- D-05 proposal SHA-256: `3b0e9bcac0f0af55bf10885cf8b1fa4793c835275bb89817f72ca1b5717e277f`
- D-05 owner record SHA-256: `c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702`
- Dataset01 crop builder SHA-256: `8096de4ffadd31ac31869f072a997a21c31eb2275a16c852fe5204bc1ad4429d`
