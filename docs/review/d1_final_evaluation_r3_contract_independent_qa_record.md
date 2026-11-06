# D1 final evaluation R3 — independent contract QA

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Reviewer: a Codex agent separate from the R3 scorer, plan, and contract author. Scope: preparation only.

Verdict: PASS

## Byte bindings and predecessor check

- R3 contract `docs/review/d1_final_evaluation_r3_contract.md`: SHA-256 `7f1f1d95188980ba91ffc5594d46eec2df35c97842632eba2187a3cd9047a60c`.
- R3 plan `docs/review/generated/d1_final_evaluation_r3_plan.json`: SHA-256 `2a8462225b88cbc4d32c0f359fe83d81bb49528f3b70d9f6616b8e9bd7c48c5f`. The contract contains that exact digest and `FINAL_EVALUATION_CONTRACT: APPROVED`; the marker is not an opening approval.
- Scorer source `detector/m1/d1_final_evaluation_r1.py`: SHA-256 `b6b4cf678663080b2096b48d4a8662514592f86ab700a37544d6544db93bc1da`, matching the plan. R3 source delta QA: `docs/review/d1_final_evaluation_r3_source_delta_independent_qa_record.md`, SHA-256 `72574be8bd72ed05e1d8e865e5ef2cbe46bd9df4c2360be1e1ddfbe7d176dbc6`, with one `Verdict: PASS` line. `graft check .` reported the graph in sync.
- Field-by-field comparison with the R2 plan found only `final_contract`, `owner_open_approval`, and the scorer source SHA changed. Lock, proof, QA and lock approval, validation bundle, two weights, Q4 and label decisions, package ID, reason, output destination and `sealed_test_accessed=false` are unchanged. The plan-pinned lock, proof, QA, bundle, Q4, label, and source hashes match the current files.

## Contract and static export review

- Reviewed the recovery Owner authorization, the handoff, both predecessor attempt records, and R2 contract. R3 states that attempt 1 refused at preflight and that attempt 2 recorded a formal opening but stopped before reading test images or labels. It requires both attempts to appear in a later report. R2 opening approval does not authorize R3; `docs/review/d1_final_evaluation_r3_owner_open_approval.md` is absent.
- The contract pins the future sequence from the checkout root: `scripts/build_m1_yolo_dataset.py export-test --final-eval --reason` with the exact plan reason, then `cd detector/` and the scorer with the repository-root-relative R3 plan path. It correctly identifies `m1.contract.REPO_ROOT` as absolute and the scorer CWD as `detector/`. The default raw and WP35 roots both exist; no path override is needed for this pinned command.
- Static review of `scripts/build_m1_yolo_dataset.py` found that the `export-test` branch appends `action=export-test` to the same access log before calling `materialise(..., ("test",))`. That loop writes only `images/test/`, `labels/test/` and `data_test.yaml` under the default export root; it does not write or remove `data.yaml` or train/val images and labels. Neither future command was run.
- R3 retains two-seed arithmetic-mean scoring, the locked confidence and NMS, D-05 gates, validation-only latency, and independent result QA. It explicitly requires both FP/image verdicts at 0.30 and 0.40 and disclosure of the current-test-label versus corrected-validation-label asymmetry beside FP. The separate R3 Owner opening approval must bind the contract hash and exact plan reason and cover both export and scorer execution.

## Independent preparation-only preflight

From `detector/`, called only `preflight(Path('docs/review/generated/d1_final_evaluation_r3_plan.json'), committed=False)` on the real validation lock/proof. It passed the preceding lock/proof checks and refused exactly `RuntimeError: Owner has not approved opening`. The access log `results/experiments/sealed_test_access_log.jsonl` had exactly one line and SHA-256 `ffef1b183ec8b4a20661c4bca71efa3cab64692c445432bc38eb3b3f2773b369` both before and after. `committed=False` is limited to the uncommitted R3 preparation files; it does not certify the later committed-file gate. The R3 export file is currently absent, and this real preflight stops at the earlier missing-Owner gate; the export-presence refusal is covered by synthetic source QA.

This PASS covers R3 contract and plan consistency, static export scope and pre-opening refusal only. It grants no permission to run `export-test`, open or score the sealed test, and does not establish model performance. No access-log or `.lock` modification, real-weight inference, training, scorer execution, or sealed-payload access occurred in this QA; `sealed_test_accessed=false`.
