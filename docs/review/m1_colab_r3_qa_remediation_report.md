# M1-Colab-R3 QA remediation report

Status: `PM_READY_FOR_INDEPENDENT_RE_REVIEW`
Prepared: `2026-10-19` (`Asia/Ho_Chi_Minh`)
Supersedes M1-Colab-R2; preserves both earlier FAIL verdicts

## R2 independent QA verdict

M1-Colab-R2 received `FAIL — 0 Critical, 2 High, 1 Medium`. The R1 findings were confirmed
closed, but QA reproduced three additional trust gaps:

1. the standalone verifier trusted a manifest-authored roster instead of deriving the canonical
   eight result members;
2. `inspect_run_weights(best.pt)` did not independently re-hash `last.pt`;
3. the stored training command was checked only by prefix, so contradictory flags could pass.

No PASS record was created for R2. R3 closes all three findings without changing scope or gates.

## R3 changes

### Canonical result-package identity

`verify_result_archive()` now validates the run ID and derives exactly these eight paths from it:

1. `<run>/weights/best.pt`
2. `<run>/weights/last.pt`
3. `<run>/results.csv`
4. `<run>/args.yaml`
5. `<run>/run_contract.json`
6. `colab_logs/colab_execution.json`
7. `colab_logs/colab_train.log`
8. `colab_logs/DB_logger.db`

The manifest and tar rosters must both equal that allowlist exactly. A self-consistent archive that
omits a required member or adds an extra member now fails. The manifest stores the portable
`archive_name` rather than an absolute path, and the verifier requires it to equal the actual
archive filename. The run attestation and every member SHA-256 must be canonical lowercase
64-character hex strings; size fields must be non-negative integers.

### Independent hashing of both checkpoints

`inspect_run_weights()` now resolves both canonical checkpoint files under `<run>/weights/`,
rejects missing files and symlinks, and independently compares the bytes of both `best.pt` and
`last.pt` with their run-contract hashes. The attestation is constructed only after both checks.

### Exact training-command binding

`validate_execution_record()` now constructs the expected command token-for-token from
`run_contract.json` and the validated execution tag. It binds model path, seed, epochs, image size,
batch, device, workers, fraction, patience and tag; it also requires `plots=false`. Missing,
duplicate, unknown, reordered or contradictory flags fail. Tags are restricted to a safe
single-component character set before any workflow action.

## R3 regression coverage

New or extended tests reject:

- manifest+archive pairs containing only `best.pt`;
- self-consistent canonical packages with an extra ninth member;
- unrelated archive filename and malformed attestation hash;
- byte mutation of `last.pt` after writing its run contract;
- `--epochs 999` when execution and run contract bind one epoch.

The prior R1/R2 counterexamples remain covered: failed/sealed execution, invalid SQLite/log/CSV,
frozen-sync bypass, CUDA placeholders, sidecar/partial overwrite, traversal/link/duplicate/tamper,
and sealed-test routes.

No archive was uploaded, no Colab cell was executed, no model was trained, and no sealed-test
artifact was created or read. Independent QA must re-run the complete adversarial matrix and all
mechanical gates before R3 can be called PASS.
