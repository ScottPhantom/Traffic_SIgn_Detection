# D-05 owner decision — acceptance thresholds, latency and seeds for the VN detector

Status: `OWNER_APPROVED_D05`
Decision date: `2026-10-18` (`Asia/Ho_Chi_Minh`)
Approved proposal: `docs/review/d05_proposal.md`
(SHA-256 `3b0e9bcac0f0af55bf10885cf8b1fa4793c835275bb89817f72ca1b5717e277f`)

The owner approved every recommendation of the proposal, Q1 to Q6, without overrides. The proposal
file is the binding text. This record summarises it and must not be read as a replacement.

## Approved terms

- **Q1 Seeds (D05-B).**
  - A 1-seed pilot first.
  - Then the final candidate with 3 seeds: `20261018`, `20261019`, `20261020`.
  - Gates are judged on the 3-seed mean, reported with the standard deviation.
- **Q2 Gates on the sealed test.** The test runs once, in the final evaluation.
  - mAP50 ≥ 0.60, averaged over the 32 classes that have test boxes.
  - mAP50-95 ≥ 0.40.
  - Class-agnostic sign recall ≥ 0.85, at IoU 0.5 and the confidence threshold chosen on val.
  - FP per image ≤ 0.30.
  - Every critical class with ≥ 20 test boxes: recall ≥ 0.70.
  - Every other class with ≥ 20 test boxes: recall ≥ 0.50. A miss marks the class "not passed"
    and removes it from simulated behaviour, but does not fail the gate.
  - AP-small, the per-resolution breakdown and classes with < 20 test boxes are reported only.
  - 95 % confidence intervals come from a bootstrap over D-02 groups.
- **Q3 Critical classes.** 0 W.224, 2 P.102, 7 P.123a, 32 P.123b, 13 W.245a, 22 W.221b, 45 I.407a,
  39/40/41 P.127 (60/80/40 km/h). Class 38 (P.127 50 km/h) has no test and stays unverified.
- **Q4 Use of val.**
  - Model selection uses the pooled val mAP50-95, averaged over seeds.
  - Confidence and NMS thresholds are chosen on val (recall ≥ 0.85 with the fewest FP per image)
    and locked before the test opens.
  - The 13 classes without val are not used for selection or tuning.
  - The gates may be recalibrated **once**, after the pilot and before the test opens, with a new
    owner approval. Gates are never lowered after the test has been seen.
- **Q5 Latency.**
  - Reference hardware: Apple M1 Pro with PyTorch MPS. CPU is reported only.
  - Measurement: batch 1, 50 warm-up and 300 measured iterations, including pre-processing,
    inference and NMS.
  - **p95 ≤ 100 ms**.
- **Q6 Reports.** Every run produces the full report listed in the proposal and follows the
  reproducibility contract in `docs/product_roadmap.md`.

## Data contract bound to this decision

| Item | Reference |
| --- | --- |
| Split | WP36-R1, `docs/review/g07_owner_acceptance_record.md` (SHA-256 `88d5c16e…`); test seal `afa03d4b…` |
| Labels | `wp33_derived_boxes.csv` (`4b930700…`), taxonomy `wp33_derived_taxonomy.csv` (`199ddd32…`) |
| Dataset card | `docs/dataset01_card_r1.md` (`8e616bcb…`) |

## Gate status

With G0.1–G0.9 PASS and D-05 approved, **Gate 0 is OPEN** for the full-frame VN detector track
(M1 → M4/D1). This authorizes building the M1 training package and running the pilot under the
terms above.

It does **not** authorize the following:

- adding PyTorch/Ultralytics to the lock. That dependency change needs its own owner approval.
- opening the sealed test before the final evaluation;
- classifier (E1–E4) or OOD gates, which are decided at M2/M3;
- deployment, publication, or any real-vehicle use. Behaviour stays simulation only.
