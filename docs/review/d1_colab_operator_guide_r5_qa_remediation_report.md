# D1 Colab operator guide R5 QA remediation report

Status: `R5_AWAITING_INDEPENDENT_QA`

Date: `2026-10-19` (`Asia/Ho_Chi_Minh`)

R4 independent QA verdict: `FAIL — 0 Critical, 0 High, 1 Medium, 0 Low`

## Remediation

R5 adds the mandatory run-registry gate between every governed result and validation evaluation.
For the pilot, the complete verified run must be placed below `<repo>/results/experiments/`,
registered, independently reviewed, committed unchanged and proven clean before pilot validation
evaluation. The committed pilot registry is preserved and extended rather than manually deleted.

For the final three-seed stage, the guide requires the operator to:

1. place each complete verified run below `<repo>/results/experiments/` and address it as
   `../results/experiments/...` from the `detector/` working directory;
2. invoke `m1.cli register-runs --weights` with the three final `best.pt` files;
3. independently review, git-track and commit the generated `d1_run_registry.json` unchanged;
4. prove the registry path is clean before evaluating any final weight;
5. run three validation evaluations, which produce one `eval_val.json` per governed run;
6. invoke `m1.cli lock-thresholds` exactly once with those three reports, then independently
   review and commit the threshold lock unchanged before any sealed-test access.

The guide explains that `register-runs` intentionally returns `ready_for_evaluation=false` until
the review/commit gate is complete. It also states the fail-closed placement and complete-run
requirements and uses the actual generated report name `eval_val.json`. R5 changes no notebook,
runner, dataset, bundle, model, test seal, gate or Owner decision. The R1 through R4 QA FAIL
records remain immutable.
