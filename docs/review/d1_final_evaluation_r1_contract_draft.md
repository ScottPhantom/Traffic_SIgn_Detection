# D1 final evaluation R1 — draft contract for the sealed test

Status: `DRAFT_NOT_AUTHORIZED`  
Date: 2026-11-06 (`Asia/Ho_Chi_Minh`)  
Scope: preparation **c** in `docs/codex_handoff_s2_eval_lock_final_2026-11-06.md`.  
`sealed_test_accessed=false`; no sealed-test file was opened, listed, counted, exported or scored to write this draft.

This draft is **not** an authorization, threshold-lock record or executable evaluation plan. It records the decision sequence and the successor work needed before a one-time final evaluation. Behavior remains simulation only; a validation or test score does not establish real-vehicle safety.

## Authority and evidence boundary

- D-05 Owner decision: `docs/review/d05_owner_decision_record.md`, SHA-256 `c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702`; the approved proposal remains binding. Test quantities below are quoted from that existing record, **not observed in this task**.
- Three-seed validation threshold-selection contract: `docs/review/d1_threshold_lock_r1_contract.md`, status `FROZEN_BEFORE_SEED_RESULTS`, committed in `9d3f230ad4efd6010037815cac633c5ea9e22852`. It specifies corrected validation R3, a shared confidence/NMS setting and independent QA gates. No threshold value has been chosen.
- Prepared S2 common evaluator and paired seed-CI source: commit `29e1562` with source QA PASS. This is source preparation only; no S2 score or result QA is claimed here.
- Seed `20261020` has no training permission from this draft. The three-seed final candidate is **unknown** until all three completed-run result QAs and validation comparisons exist.

## Ordered prerequisites before any sealed-test access

1. Complete the three predeclared candidate seeds `20261018`, `20261019` and `20261020` under their respective Owner-authorized run contracts. Each run must pass **independent result QA** of its archive/manifest, weights, checkpoint, SQLite/text logs, runtime and seal evidence. A third seed requires its own approval; do not infer it from D-05 alone.
2. Execute the frozen corrected-validation-R3 selection contract only after its separate inference permissions and source/result QAs. Implement and independently QA an **R3 lock writer, verifier and compatible final reader** that bind the exact 376-image/624-box/nine-group roster, scoring version, all three candidate weight/run/report hashes, and one shared `(confidence, nms_iou, agnostic_nms)` across seeds. The produced lock record and proof must pass independent QA and receive explicit Owner approval. No threshold is selected or locked by this draft.
3. The Owner decides **once**, before test access, whether to use D-05 Q4's one allowed recalibration of acceptance gate values. If used, the revised gates require a separate append-only decision and approval. No gate may be lowered after the test has been seen. This draft proposes no revised values.
4. Replace this draft with a finalized, hash-pinned final-evaluation contract covering the actual three weights, lock/proof and scoring implementation; obtain independent source/contract QA. Resolve the R3-versus-original-export mismatch described below before finalization.
5. Obtain **explicit Owner approval to open the sealed test once**. Approval of training, validation, this draft or the threshold-selection contract does not satisfy this step.

If any prerequisite or pin is absent, differs or fails QA, stop before access. Do not quietly substitute another roster, weight, threshold or gate.

## D-05 Q1/Q2/Q5 acceptance specification (to be applied only after approval)

All gates are evaluated on the **mean of three seeds**, with their sample standard deviation reported (Q1). Q2, as recorded in the approved D-05 decision:

| Measure | Gate / treatment |
| --- | --- |
| mAP50 | ≥ 0.60, averaged over classes that have test boxes; the D-05 record cites 32 such classes as a historical contract fact, not a count made here |
| mAP50-95 | ≥ 0.40 |
| Class-agnostic sign recall | ≥ 0.85 at IoU 0.5 and the validation-locked confidence |
| False positives per image | ≤ 0.30 |
| Each critical class with ≥ 20 test boxes | Recall ≥ 0.70 |
| Each other class with ≥ 20 test boxes | Recall ≥ 0.50; a miss marks that class not passed and excludes it from simulated behavior, but does not fail the overall gate |
| AP-small, resolution breakdown and classes with < 20 test boxes | Report only |
| Uncertainty | 95% CI from bootstrap over D-02 groups |

Critical classes and their derived-key mapping must follow D-05 Q3 and the locked taxonomy. Do not derive a new class set from the sealed payload during preparation.

Q5 latency uses **Apple M1 Pro with PyTorch MPS**, batch size 1, **50 warm-up and 300 measured iterations**, including preprocessing, inference and NMS. The acceptance gate is **p95 ≤ 100 ms**; CPU is report-only. The measurement implementation, hardware evidence, three candidate identities and QA must be pinned in the finalized contract.

## Existing command and required successor

The repository has `m1.cli evaluate --split test --final-eval --reason ... --threshold-lock ...` and the access logger `contract.log_test_access` in `detector/m1/contract.py`. These are existing mechanisms, **not a command to run now**. The current `m1.cli lock-thresholds`/`contract.bind_threshold_lock` read the original export's validation reports and schema-1 lock; they do not prove the corrected R3 roster or the common three-seed selection. Therefore using that legacy path alone would not satisfy the frozen R3 contract.

Before any final evaluation, a separately implemented and independently QA-passed successor must verify the R3 lock record/proof and three candidate bindings, then either adapt the existing `m1.cli evaluate` to a proven equivalent scorer/roster or provide a new final-evaluation entrypoint. It must preserve `contract.log_test_access` or an independently verified append-only equivalent, enforce one-time access, record reason/Owner approval, and fail closed on hash drift. The exact command, code SHA and QA must be written into the finalized contract. **No successor code is implemented by this draft.**

## One-time execution and publication boundary

After all five prerequisites: open and evaluate the sealed test **once** using the fixed three weights, the common locked threshold/NMS, the fixed acceptance gates and the pinned scorer. Do not change model, class map, threshold, NMS, roster or gates after observing the test. A failed gate is reported as failed, without a second tune-and-retest cycle. Log the access, preserve raw artifacts, and obtain **independent result QA before publishing or claiming a result**. Any hash drift or access-log failure stops the procedure without retrying against a changed configuration.

Current state: `DRAFT_NOT_AUTHORIZED`; no final-candidate result, lock, test score or safety claim exists in this document. `sealed_test_accessed=false`.
