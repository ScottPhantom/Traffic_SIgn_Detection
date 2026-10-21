# D1 single-seed 100-epoch pilot R2 implementation record

Date: 2026-10-21  
Status: `IMPLEMENTED_LOCALLY_QA_PENDING_NO_LIVE_PILOT`  
Predecessor: Pilot R1 independent QA FAIL, finding `QA-D1-PILOT-R1-001`

## Remediation

Pilot R2 is append-only. It preserves the R1 notebook, builder, tests, implementation record and
independent FAIL record unchanged.

- The notebook now passes exact `--patience 0`.
- `run_d1_colab_pilot_r2.py` requires 100 epochs, patience 0, a fresh stop at epoch 1 and no stop
  target in resume mode before delegating to the QA-passed R6 runner. It also rejects drift from
  seed 20261018, image size 1280, batch 4, device 0 and the Pilot R2 tag.
- The successor intercepts `training_outcome.json` before the inherited runner can mark the
  execution `SUCCEEDED` or package results. Resume accepts only `COMPLETED` or
  `COMPLETED_FROM_FINAL_CHECKPOINT` at exactly epoch 100. `COMPLETED_EARLY_STOPPED`, every result
  below epoch 100, non-exact-integer epoch values and any sealed-test marker fail closed.
- The R2 builder pins SHA-256
  `e42716fad4eb7b8d651565b611f11936d6a7b8b624832dccad8e513c55263fa6` for the frozen R6 source
  notebook and checks the exact cardinality of every replacement before writing output.
- Regression tests cover the planned fresh pause, early-stop and below-100 rejection, complete
  epoch-100 acceptance, sealed-boundary rejection, unexecuted notebook state, exact patience/config
  and builder hash/cardinality controls.

`CODE_COMMIT` remains `PENDING_AFTER_QA`. No Pilot R2 Colab run, upload, sealed-test access, commit
or push is authorized until independent source QA PASSes this package.
