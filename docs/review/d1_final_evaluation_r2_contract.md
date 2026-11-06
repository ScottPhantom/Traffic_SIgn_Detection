# D1 final evaluation R2 — fixed successor contract

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Status: `CONTRACT_FIXED_TEST_OPEN_UNAUTHORIZED`. `sealed_test_accessed=false`.

`FINAL_EVALUATION_CONTRACT: APPROVED` is the fixed contract marker required by the prepared scorer. It does **not** grant permission to open the sealed test; independent contract QA, a separate Owner opening approval tied to this contract hash and the exact plan reason, and every runtime preflight gate remain mandatory. This document does not report a test result or claim real-vehicle safety.

## Authority and immutable inputs

The D-05 Q1 amendment changes the final candidate to the mean of two fixed seeds, 20261018 and 20261019. The R3 lock and proof are independently QA-passed and Owner-approved. Q4 uses the single pre-test gate recalibration: FP/image ≤ 0.40, with the original 0.30 marker reported alongside it; recall stays ≥ 0.85. The Owner chose current test labels without a blind label review. The source delta QA passed after the seed-to-weight binding repair. All source and decision bytes below were hash-checked in this checkout.

| Evidence | Path | SHA-256 |
| --- | --- | --- |
| D-05 Owner decision | `docs/review/d05_owner_decision_record.md` | `c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702` |
| Q1 two-seed amendment | `docs/review/d05_q1_two_seed_owner_amendment_2026-11-06.md` | `4d451a3a4174d1b2ff34c5acc9d6683e10062e1672f01104ce76edd12585e807` |
| Final draft and two-seed addendum | `docs/review/d1_final_evaluation_r1_contract_draft.md` | `17a0bf3df57de66dd6369a7da78c58ad4b9df52f195fbd3a0aa1933f1cab1d71` |
| Draft two-seed addendum | `docs/review/d1_final_evaluation_r1_contract_draft_addendum_1_two_seeds.md` | `97ffd3f49c2cb44691fc41bf3af9c8c9832296eb9df341644a05323f7bedc8a7` |
| Threshold lock contract | `docs/review/d1_threshold_lock_r1_contract.md` | `726932dbcd32842658477c9d36f4dc7c240d412d92119e76e5b3536a4d278f0f` |
| Threshold lock two-seed addendum | `docs/review/d1_threshold_lock_r1_contract_addendum_1_two_seeds.md` | `cefbdc627266588735e0369c42b1fe426e85e78c38b3eaddef2f61ac9484a82b` |
| R3 lock result QA | `docs/review/d1_threshold_lock_r1_result_independent_qa_record.md` | `c113a80ef295c3ec43ef86ad07e28ad95d3a6ce2ab61fe30b5cae1392b308261` |
| Owner lock approval | `docs/review/d1_threshold_lock_r1_owner_approval_2026-11-06.md` | `1acb4d61e59f6b6a4f504a3e273c69e6fbc2ad6cdb6b15a93db2a1cb42c05edb` |
| Q4 Owner gate decision | `docs/review/d05_q4_gate_recalibration_owner_decision_2026-11-06.md` | `53e26091dc9da6081143ca6239e3df75cd04d1403d66e02cce2e601d0a52927b` |
| Q4 machine-readable decision | `docs/review/generated/d05_q4_gate_recalibration_r1.json` | `ba8cfe55349416ad72abfc40fc65297f6c3c2e75844b422365dacfee92e6c9bb` |
| Owner test-label decision | `docs/review/d1_final_test_label_owner_decision_2026-11-06.md` | `402a19965d700c4d6ad9ef74aed4843c4ef86741f5a03fd0f32b51ffa725926f` |
| Machine-readable test-label decision | `docs/review/generated/d1_final_test_label_decision_r1.json` | `369399b80c7b4e72757150557e60a8249b96d9da2f3668596d5a50c9b49b2eae` |
| Final scorer source delta QA | `docs/review/d1_final_evaluation_r2_source_delta_independent_qa_record.md` | `56a5e0954549d046bc744b444389cde5d4a5afd5196f30c9ec3e095e66bd4df4` |

### Two R3-locked candidates

| Seed | Weight path | Weight SHA-256 | Archived run contract SHA-256 |
| --- | --- | --- | --- |
| 20261018 | `results/experiments/D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2/weights/best.pt` | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` | `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88` |
| 20261019 | `tmp/d1_two_seed_lock_r1_inputs/s2/best.pt` | `046cfea22e6daf45342063b58cd9082aa4b0b0528a3a6d9af7ac23bbac015bce` | `1f1c3f7f2fdeb15467aa69ddbe012b880b10324b5b505d772058ebd7e96c2050` |

The shared, frozen setting is `conf=0.19`, class-aware NMS `iou=0.70`, `agnostic_nms=false`; inference candidate floor is `conf=0.001`, `imgsz=1280`, `max_det=300`. The two weights are not stored in Git. The seed-19 weight and both R3 seed reports remain in Git-ignored `tmp/` and must retain their pinned bytes.

| Lock or plan artifact | Path | SHA-256 |
| --- | --- | --- |
| R3 lock | `docs/review/generated/d1_threshold_lock_r1.json` | `d39b0466a5285979c3da63546ebbd56d26d0030081f4df9fa6c75fc8ee96167d` |
| R3 proof | `docs/review/generated/d1_threshold_lock_r1_r3_proof.json` | `2d2fbd7cf99ee9e8b1349a55cf40b0182764efe9f7d4cd5078c06c5f8aa72e77` |
| Execution plan | `docs/review/generated/d1_final_evaluation_r2_plan.json` | `69f54ee3f6e6d10914d5347fa445d5457df43954dad063dbb0b90bb725b914a0` |
| Validation-only bundle manifest | `tmp/yolo11n_n1_extract_r2/manifest.json` | `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da` |

The plan has exactly two candidate identities, uses the Owner-approved lock/QA/decisions, pins `imgsz=1280`, `device=mps`, the output directory `results/experiments/d1_final_evaluation_r1`, and this immutable reason:

> One-time D1 final evaluation of seeds 20261018 and 20261019 under the approved R3 lock and D-05 gates.

Its `owner_open_approval` field names `docs/review/d1_final_evaluation_r2_owner_open_approval.md`, which **does not exist** at contract writing. No such approval is created here. The plan also records `sealed_test_accessed=false`.

### Executable source pins

| Source or environment lock | SHA-256 |
| --- | --- |
| `detector/colab/evaluate_cascade_b0_r1.py` | `8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42` |
| `detector/m1/contract.py` | `901e7e372d9660cd79e6bfcab43684b1693f0a4aafad9f4c331fd8f04ba6bbbf` |
| `detector/m1/d1_final_evaluation_r1.py` | `edf4ba5cc7a9aaccb648cf9daad0a9e6343234e55da4065cee50040601238ea3` |
| `detector/m1/d1_threshold_lock_r3_successor.py` | `6e15865a7fe4bcbad27cbd5c66ff74eeb0f8d8df9b8070e6777f6ca2a845c454` |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` |
| `detector/uv.lock` | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |

The scorer source hash above is the path-binding successor reviewed by `docs/review/d1_final_evaluation_r2_source_delta_independent_qa_record.md` (`Verdict: PASS`). It also retains the seed-to-weight map fix reviewed in R1. The evaluator and R3 lock reader are separate, pinned modules.

## R1 refusal and R2 preflight evidence

The committed R1 attempt record `docs/review/d1_final_evaluation_r1_run_attempt_1_preflight_refusal.md` documents the exact gate-1 refusal `lock or proof binding differs`: the R3 lock stores a detector-CWD-relative proof path, while the scorer passed an absolute path. R2 checks `samefile` and SHA-256 against the plan, then passes the lock's own relative proof path to the R3 reader. It refuses any CWD other than the checkout's `detector/`. The source-delta independent QA reran the real R2 preflight from that CWD with `committed=False` while the R2 files were uncommitted: gate 1 returned the shared `conf=0.19`, `nms_iou=0.70`, `agnostic_nms=false` setting for both seeds, and preflight stopped at `RuntimeError: final contract is absent`. The access log was absent before and after. This proves only the pre-opening gates tested in that run; no sealed data was read. `sealed_test_accessed=false`.

The R1 opening approval binds the predecessor contract and does not authorize R2. The R2 opening approval path in the plan is deliberately absent; a separate Owner decision tied to this contract hash and the exact plan reason is required before a future run.

## Acceptance and reporting rules

Evaluate the **arithmetic mean of the two seeds**, report each seed and the seed-19 minus seed-18 difference. Do not present a two-point standard deviation as uncertainty. A 95% bootstrap over intact D-02 image groups keeps both weights fixed and does not measure training-seed variation. The future one-time final report must include:

- mAP50 ≥ 0.60 over classes with boxes in the approved test labels; mAP50–95 ≥ 0.40.
- Class-agnostic recall ≥ 0.85 at IoU 0.5 and the locked confidence.
- FP/image ≤ 0.40 under the one allowed Q4 recalibration. Also show the original ≤ 0.30 marker and both verdicts. The 0.40 decision was made after validation results were known and must be disclosed.
- Recall ≥ 0.70 for each critical D-05 Q3 class with at least 20 boxes. For another class with at least 20 boxes, recall below 0.50 excludes that class from simulated behavior but does not fail the overall gate. Classes below 20 boxes are report-only.
- AP-small, per-resolution results, error analysis, and class-level results as report-only diagnostics. No class-support count is newly asserted from the sealed payload here.
- Q5 latency on Apple M1 Pro MPS, batch 1, 50 warm-ups and 300 measured iterations per weight, including preprocessing, inference and NMS. Two-seed mean p95 ≤ 100 ms. CPU is report-only. Q5 uses validation images.

The Owner chose current test labels. R3 validation labels had a targeted correction (64 boxes and 40 ignore regions), while test labels have not had that review. The final report must state this asymmetry beside FP/image; it must not attribute any miss to label noise without separate evidence. All behavior is simulation only.

The pinned scorer currently writes the recalibrated FP gate verdict to its automatic Markdown report, but does not write a separate verdict for the original 0.30 marker or the current-label asymmetry. After the one-time run, the final report must compute that original verdict from the same already-produced two-seed mean FP/image in its JSON, show both 0.30 and 0.40 verdicts, and add the current-label asymmetry beside the FP result. The supplemented report must undergo independent result QA before publication. This reporting step must not re-open the test or change a gate. If it cannot be completed and QA-passed, do not publish an acceptance claim.

## Exact future command and one-time gate

**Do not run this command under this contract-writing task.** It is fixed here for a later, separately authorized final evaluation:

```bash
cd detector/
PYTHONPATH=. uv run --no-sync python -m m1.d1_final_evaluation_r1 \
  --plan docs/review/generated/d1_final_evaluation_r2_plan.json
```

The command starts at the checkout root, then changes into `detector/`. `m1.contract.REPO_ROOT` is an absolute path, and the scorer requires the current working directory to equal `REPO_ROOT / "detector"`. The CLI has no `--repo-root` flag. Its `--plan` argument is deliberately **repo-root-relative** (`docs/...`, without `../`) because scorer preflight resolves it against `REPO_ROOT`. The R3 lock/proof itself stores `../docs/...` and `../tmp/...` paths, which the lock verifier resolves relative to the **current working directory**; running the command outside `detector/` would fail that binding.

Before any payload access, scorer preflight must verify the committed plan, approved R3 lock/proof/result QA, Owner lock approval, validation-only bundle, this committed contract and its plan hash, a **separate** Owner opening record with the exact marker `OWNER_AUTHORIZES_TEST_OPEN: D1-FINAL-EVALUATION-R1`, this contract SHA-256 and the plan reason, the Q4 and label decisions, exact source and weight hashes, and unused one-time access log. It then measures latency on validation images, repeats preflight, appends the access event, and only then reads the sealed roster. A failed gate stops before access; no parameter may be retuned after observing test results. Independent result QA is required before publishing any claim.

## Remaining operational prerequisites

1. Independent QA of this finalized contract and its plan must PASS.
2. Commit the R2 plan, R2 contract, corrected scorer, tests and QA records before any future authorized run; verify every executable source pin remains unchanged. The current preflight used `committed=False` solely because the new R2 plan and contract were uncommitted during preparation. A later authorized run must use the default committed check.
3. Obtain a separate, explicit Owner opening approval bound to the final contract SHA-256 and exact plan reason. This task does not create it.
4. Recheck all local artifacts, hardware, plan/output destination and one-time access log at execution time. Do not open, list, count, hash or score the sealed test during preparation.

No inference, training, test payload access, gate recalibration or push occurred while writing this contract. `sealed_test_accessed=false`.
