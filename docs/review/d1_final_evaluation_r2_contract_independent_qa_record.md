# D1 final evaluation R2 — independent contract QA

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Reviewer: separate Codex agent from the R2 contract author. Scope: contract and plan preparation only; no final evaluation.

Verdict: PASS

## Reviewed byte bindings

- R2 contract `docs/review/d1_final_evaluation_r2_contract.md`: SHA-256 `0f8bbf104e523f243f5f0e3c6b23b4e9545bf98a353a1f6b560c62cc3cfa86ff`.
- R2 plan `docs/review/generated/d1_final_evaluation_r2_plan.json`: SHA-256 `69f54ee3f6e6d10914d5347fa445d5457df43954dad063dbb0b90bb725b914a0`.
- Corrected scorer `detector/m1/d1_final_evaluation_r1.py`: SHA-256 `edf4ba5cc7a9aaccb648cf9daad0a9e6343234e55da4065cee50040601238ea3`; R2 source-delta QA record: SHA-256 `56a5e0954549d046bc744b444389cde5d4a5afd5196f30c9ec3e095e66bd4df4`, with one PASS verdict.
- `graft check .` reported the source graph in sync.

## Independent checks

- Compared R2 contract to the committed R1 predecessor and the handoff. R2 retains `FINAL_EVALUATION_CONTRACT: APPROVED` as a contract marker, the two-seed arithmetic-mean method, the fixed R3 setting `conf=0.19` and class-aware NMS IoU `0.70`, D-05 acceptance gates, validation-only latency method, and independent result QA obligation. It explicitly requires reporting both FP/image verdicts at 0.30 and 0.40 and the asymmetry between corrected validation labels and current test labels. The R1 attempt-1 refusal is cited; the R1 contract and opening approval were not edited.
- The contract pins the exact R2 plan hash above and correctly states that `m1.contract.REPO_ROOT` is absolute, the current working directory must be `REPO_ROOT / "detector"`, and `--plan docs/review/generated/d1_final_evaluation_r2_plan.json` remains repository-root-relative. Its future command is documented but was not executed in this review.
- Compared R1 and R2 plan JSON field by field. Only `final_contract`, `owner_open_approval`, and the corrected scorer source SHA changed. The lock, proof, lock QA and approval, validation bundle, Q4 and label decisions, both weights, package ID, reason, output directory, runtime configuration and `sealed_test_accessed=false` are identical. All plan-pinned lock, proof, QA, bundle, Q4, label and source hashes match current files.
- The R2 Owner opening approval `docs/review/d1_final_evaluation_r2_owner_open_approval.md` is absent. The R1 approval cannot authorize this R2 contract. The contract correctly requires a separate Owner decision tied to the R2 contract hash and exact plan reason.
- From `detector/`, called only `preflight(Path('docs/review/generated/d1_final_evaluation_r2_plan.json'), committed=False)` on the real validation evidence. It passed lock/proof gate 1 and refused exactly `RuntimeError: Owner has not approved opening`. `committed=False` was necessary because the R2 source, plan and contract were not yet committed. This check does not validate the future committed-file gate or authorize evaluation.
- `results/experiments/sealed_test_access_log.jsonl` was absent before and after the preflight. No scorer CLI, `execute`, inference, training or sealed payload access occurred. `sealed_test_accessed=false`.

## Boundary

This PASS covers consistency and preparedness of the R2 contract and plan. It does not approve opening the sealed test, certify final model performance, or replace a later independent result QA.
