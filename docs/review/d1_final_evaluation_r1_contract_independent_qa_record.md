# D1 final evaluation R1 — independent contract and plan QA

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Reviewer: a Codex agent separate from the contract/plan author. Scope: item 3 of `docs/codex_handoff_final_eval_scorer_2026-11-06.md`, static source and document review plus synthetic scorer tests. No real plan was executed; no sealed-test payload was opened, listed, counted, read, hashed or scored. `sealed_test_accessed=false`.

Verdict: PASS giới hạn — the fixed two-seed contract and plan bind the approved decisions and exact future command; this is contract preparation only, not authorization or readiness to open the sealed test.

## Reviewed bytes

| Artifact | SHA-256 |
| --- | --- |
| `docs/review/d1_final_evaluation_r1_contract.md` | `de92d8c61599e60989438765f372d8b4bbbb4d801b9f565a46dc69557f1f05d8` |
| `docs/review/generated/d1_final_evaluation_r1_plan.json` | `9c90ee71f5106ab1d28bdeb46ef4877d1028333e5e6532198337e0f451c96f77` |
| `docs/review/generated/d1_threshold_lock_r1.json` | `d39b0466a5285979c3da63546ebbd56d26d0030081f4df9fa6c75fc8ee96167d` |
| `docs/review/generated/d1_threshold_lock_r1_r3_proof.json` | `2d2fbd7cf99ee9e8b1349a55cf40b0182764efe9f7d4cd5078c06c5f8aa72e77` |
| `docs/review/d1_threshold_lock_r1_result_independent_qa_record.md` | `c113a80ef295c3ec43ef86ad07e28ad95d3a6ce2ab61fe30b5cae1392b308261` |
| `docs/review/d1_threshold_lock_r1_owner_approval_2026-11-06.md` | `1acb4d61e59f6b6a4f504a3e273c69e6fbc2ad6cdb6b15a93db2a1cb42c05edb` |
| `docs/review/generated/d05_q4_gate_recalibration_r1.json` | `ba8cfe55349416ad72abfc40fc65297f6c3c2e75844b422365dacfee92e6c9bb` |
| `docs/review/generated/d1_final_test_label_decision_r1.json` | `369399b80c7b4e72757150557e60a8249b96d9da2f3668596d5a50c9b49b2eae` |
| `detector/m1/d1_final_evaluation_r1.py` | `d154132733c24e6a63a81e7dc1014497202fe1aa72dbd46eeb2e57e1a6a804c8` |
| `docs/review/d1_final_evaluation_r1_source_delta_independent_qa_record.md` | `50b46479f81d7e65ce91174e9a2c8a80323aab71164aed6456038e0c2d85e638` |

I independently recalculated every SHA-256 in the contract's evidence/source tables, its plan pin, all plan file bindings, and both real weight files. They match the current bytes. The plan's six source hashes and two weight hashes also match the approved R3 lock's two distinct seed identities. The validation-only bundle manifest hash matches its pin. The four handoff entry gates are present in HEAD ancestry: `82e6b6f` Owner lock approval, `8726d8c` Q4 decision, `00578c2` current-label decision and `4e53f4f` scorer source delta QA. The result and delta QA records each have PASS findings; the initial scorer source QA FAIL remains retained.

## Contract and command checks

- The lock is `LOCKED_ON_VAL` with `sealed_test_seen=false`, two candidates (20261018, 20261019), and one shared `conf=0.19`, class-aware `nms_iou=0.70`. The contract and plan pin both lock and proof hashes. No third seed or unapproved weight was inserted.
- The Q4 machine-readable record says `RECALIBRATE_ONCE`, FP/image ≤ 0.40, recall ≥ 0.85, and leaves the other D-05 gates unchanged. The label record says `CURRENT_LABELS`. The contract discloses the original FP/image ≤ 0.30 marker and the validation/test label asymmetry.
- The plan has exactly the keys required by `d1_final_evaluation_r1.preflight`, with `imgsz=1280`, `device=mps`, the reason fixed in the contract, a new experiment output path, and `sealed_test_accessed=false`. Its future Owner opening approval path is absent; no approval was fabricated.
- The pinned command starts at the checkout root, changes to `detector/`, and uses `PYTHONPATH=. uv run --no-sync python -m m1.d1_final_evaluation_r1 --plan docs/review/generated/d1_final_evaluation_r1_plan.json`. `m1.contract.REPO_ROOT` resolves to `..` from there. The plan argument is intentionally repository-relative because scorer preflight resolves it against `REPO_ROOT`; the lock's stored proof path is `../docs/review/generated/d1_threshold_lock_r1_r3_proof.json`, resolved by the R3 verifier relative to the process CWD. The CLI has no `--repo-root` option. This command was documented, not executed.
- Source inspection confirms the fail-closed sequence: committed plan and lock/QA/Owner-lock approval, committed contract bound to plan SHA, absent/present separate Owner opening approval, Q4 and label decisions, source/weight hashes, one-time access check; then validation-only latency, repeated preflight, access-log append, and only then the future sealed roster loader. No static check here establishes real-run success.

## Required future gates and limitations

1. The Owner opening approval record does not exist. It must be a separate committed record containing the scorer's exact opening marker, this contract SHA-256 and the plan's reason before the command may run. The marker `FINAL_EVALUATION_CONTRACT: APPROVED` in the contract is a parser requirement and does not grant that opening permission.
2. The plan and contract are not yet committed. Additionally, `detector/colab/evaluate_cascade_b0_r1.py` matches its pinned SHA-256 `8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42` but is currently **untracked**. Since preflight requires committed source bytes, the future command would refuse until that dependency is committed unchanged. This QA did not stage or commit it.
3. The prepared scorer's automatic Markdown reports the recalibrated FP verdict but omits a separate original-0.30 verdict and the current-label asymmetry. The contract explicitly requires a post-run supplement derived from the same output JSON, both FP verdicts and asymmetry beside FP, followed by independent result QA before publication. No second test read or parameter change is authorized. This is a bounded reporting obligation, not a claim that the automatic output already meets it.
4. The QA uses static checks and 21 synthetic scorer tests only. The focused suite passed; Ruff on scorer and its test, root `uv lock --check`, and `graft check .` passed. No real weight inference, latency measurement or final evaluation was run. Every artifact must be rechecked at the later, separately approved execution gate.

`sealed_test_accessed=false`. No approval to open the test, deploy or claim driving safety follows from this record.
