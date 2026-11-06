# D1 final evaluation R4 — scorer recovery contract

Date: 2026-11-07 (`Asia/Ho_Chi_Minh`). Status: `CONTRACT_FIXED_TEST_OPEN_UNAUTHORIZED`.

`FINAL_EVALUATION_CONTRACT: APPROVED` fixes the preparation, inputs, method,
reporting and gate sequence below. It **does not** authorize another opening of
the sealed test. A separate Owner approval bound to this contract's SHA-256 and
the exact plan reason remains required. No test result or vehicle-safety claim
is made here.

## Authority and bindings

- Owner's R4 preparation authorization:
  `docs/review/d1_final_evaluation_r4_owner_authorization_2026-11-07.md`.
- R4 plan: `docs/review/generated/d1_final_evaluation_r4_plan.json`, SHA-256
  `2c463b61bbe73e482e28b1454023db438cc7d363f2ebc3525da942d37e74fc6f`.
  The plan keeps the R3-approved lock, proof, two weight hashes, validation-only
  bundle, Q4 decision, current-label decision, image size 1280, MPS device and
  output directory. Its `final_contract` path names this file. Its immutable
  reason is:

  > One-time D1 final evaluation of seeds 20261018 and 20261019 under the approved R3 lock and D-05 gates, after R4 scorer recovery and validation rehearsal.

- The plan's `owner_open_approval` path is
  `docs/review/d1_final_evaluation_r4_owner_open_approval.md`. This file is
  **absent** at contract writing; this contract does not create it.
- The R3 lock is `docs/review/generated/d1_threshold_lock_r1.json`, SHA-256
  `d39b0466a5285979c3da63546ebbd56d26d0030081f4df9fa6c75fc8ee96167d`.
  Its proof is `docs/review/generated/d1_threshold_lock_r1_r3_proof.json`,
  SHA-256 `2d2fbd7cf99ee9e8b1349a55cf40b0182764efe9f7d4cd5078c06c5f8aa72e77`.
  The lock result QA and Owner lock approval are independently pinned in the
  plan. The locked setting remains confidence 0.19, class-aware NMS IoU 0.70;
  inference candidate floor 0.001, `imgsz=1280`, `max_det=300`.
- Seed 20261018 pilot `best.pt` SHA-256:
  `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633`.
  Seed 20261019 S2 `best.pt` SHA-256:
  `046cfea22e6daf45342063b58cd9082aa4b0b0528a3a6d9af7ac23bbac015bce`.
  Their paths are fixed by the plan; weights are not committed to Git.
- Validation-only bundle manifest SHA-256:
  `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`.
  The R4 scorer SHA-256 is
  `2be9ad7da62268f418d1138bb01d2f81a2dfb20aa7c711ddcda4237a927ce75a`;
  the other five executable source/lock SHA-256 pins are in the plan.
- Independent source QA: `docs/review/d1_final_evaluation_r4_source_delta_independent_qa_record.md`,
  SHA-256 `49513374d67ce39d58c68313f2554efaf6c6be7b0389896b3f675601f9ec27c3`,
  `Verdict: PASS`. The validation rehearsal record is
  `docs/review/d1_final_evaluation_r4_val_rehearsal_record.md`.

## Recovery history and one-time access boundary

Attempt 1 stopped in preflight before an opening. Attempt 2 logged an opening
but stopped before any test payload was read. A subsequent, separately approved
`export-test` operation created the test export. Attempt 3 opened the test and
ran predictions for both weights, then crashed in scoring on the noninteger
derived class key `16:2.0`; its in-memory predictions were lost, and no metric,
verdict or result was seen. The three existing access-log lines are retained
unchanged, with SHA-256
`a8f45f5092ff7c7f8dea66bde0620b9108d7f61174d885bb3c424a8cdf477e45`.
The R4 scorer accepts **only** those exact three lines in order and records a
new `d1-final-evaluation-r4-open` action if a future run passes every gate.
There is no access-log reset or deletion. The test export is not run again.

The R4 validation rehearsal used both real weights on all 376 R3 validation
images (337 `.jpg`, 39 `.png`) and 624 GT boxes, with no test access. It exited
0 after predicting, saving raw predictions, scoring and writing JSON/Markdown.
At the locked point it reproduced TP 555/512, FP 155/131, mean recall
0.85496795 and FP/image 0.38031915. Its six output hashes are in the
append-only rehearsal record. Two earlier failed rehearsal attempts and their
empty output directories remain disclosed in
`docs/review/d1_final_evaluation_r4_val_rehearsal_failure_record.md`.
The rehearsal and source QA demonstrate execution consistency on validation;
they do not establish test performance or safety.

## Fixed future method and reporting

Only after a separate Owner opening approval, independent contract QA PASS,
commit of this contract, plan, scorer, tests and QA records, and a fresh
preflight, the one-time scorer command is:

```bash
cd detector/
PYTHONPATH=. uv run --no-sync python -m m1.d1_final_evaluation_r1 \
  --plan docs/review/generated/d1_final_evaluation_r4_plan.json
```

The command runs from `detector/` because the R3 proof binding is relative to
that directory. It uses the already exported test, measures Q5 latency on
validation, repeats preflight, appends the R4 access event before reading the
test, then predicts each seed. Each seed's raw predictions and hash/weight
manifest are written atomically **before** `score_two_seeds`. There is no
approved path to re-score saved predictions. The test result JSON and Markdown
are written atomically to the plan's output directory. A refusal or crash is
not an invitation to adjust the thresholds, labels, weights or gates.

The two-seed arithmetic mean is the final candidate; each seed and seed-19
minus seed-18 difference must also be reported. D-02 group bootstrap holds
both weights fixed and does not estimate training-seed uncertainty. D-05/Q4
requires mAP50 ≥ 0.60, mAP50–95 ≥ 0.40, class-agnostic recall ≥ 0.85,
and the one-time recalibrated FP/image ≤ 0.40. The final report must show
**both** FP/image verdicts against the original ≤ 0.30 marker and the
recalibrated ≤ 0.40 gate. The latter was chosen after validation results were
known and must be disclosed. Supported critical classes (at least 20 GT boxes)
require recall ≥ 0.70; other supported classes with recall below 0.50 are
excluded from simulated behavior. Lower-support classes are report-only.
Q5 uses Apple M1 Pro MPS, batch 1, 50 warm-ups and 300 measured iterations
per weight, with preprocessing, inference and NMS; the two-seed mean p95 must
be ≤ 100 ms. AP-small, per-resolution, per-class and error diagnostics are
report-only.

The Owner chose current test labels. R3 validation labels had a targeted
correction (64 boxes and 40 ignore regions); test labels did not undergo that
review. The final report must place this label asymmetry beside FP/image and
must not attribute a miss to label noise without separate evidence. It must
also disclose attempts 1–3, including the full unseen test prediction pass
in attempt 3. The scorer's automatic Markdown is not by itself a complete
publication report: the original 0.30 verdict, asymmetry and attempt history
must be added from the already-produced JSON without another test opening.
Independent result QA must PASS before any result or acceptance claim is
published. Behavior remains simulation only.

## Current gate

This preparation task has not created an opening approval and does not run the
command above. A preparation-only preflight must stop at
`Owner has not approved opening`; the three-line access log must stay unchanged.
No threshold, weight, label or Q4 gate may change after any test observation.
