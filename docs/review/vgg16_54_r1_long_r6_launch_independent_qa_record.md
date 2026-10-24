# VGG16-54 R1 long-run R6 command-contract independent QA record

Status: `QA_PASS_LONG_RUN_R6_COMMAND_ONLY`

Reviewed: `2026-10-24T20:36:33+07:00`

Reviewer boundary: independent read-only successor QA. The reviewer did not train, resume the
model, alter source or Drive state, upload, download, commit, push or access the sealed test. This
append-only record authorizes only the exact R6 contract bytes reviewed below.

## Reviewed files and anchors

- R6 command-contract SHA-256:
  `387cd10073e0192fcb014b3372e9e3f7615c7eae08ed9874d4c0a38dd637974f`.
- R6 implementation-record SHA-256:
  `3c20d592e5fa9757d5d33fcee81ef3e6244dbf955849c1c7e8b6a2b87c21b182`.
- R6 contract-test SHA-256:
  `e52ecabf9757131bb135e373a87cd0ad5050d1fc1c5337d6f17ce6b24d92a1f0`.
- QA-PASS R5 contract SHA-256:
  `0c6840281d0f53e52610e392ceca4aacbd40996db4e8ca8865c3cbd57088c372`.
- R5 independent-QA record SHA-256:
  `c4b05b195495ecbf743e5c0d4a848725af30ac81b1470795fe7b23697879b3ff`.
- Two-runtime smoke proof SHA-256:
  `898a440709dd477b9ec70569b52464047adb55de8ed48325eeef091f3e759132`.
- Immutable source commit:
  `2e1d981e70e02b19d1998fa17be8c8a0de033df0`.

## Exact R5 to R6 delta

Independent JSON and command comparison found exactly three semantic changes:

1. package changes from `VGG16-54-R1-LONG-R5` to `VGG16-54-R1-LONG-R6`;
2. one top-level `work_root` field is added with exact value
   `/content/vgg16_54_long_r6_work`;
3. the command adds exactly `--work-root /content/vgg16_54_long_r6_work` immediately after the
   existing state argument.

All other contract fields are exactly equal to R5. The remaining command elements are identical
and retain the same immutable source, state, resume-runtime digest, configuration, bundle, Owner,
base source-QA, runtime source-QA and two-runtime smoke-proof anchors.

The R6 work root is an absolute sibling-style path distinct from the R4/R5 default
`/content/vgg16_54_work`; neither is an ancestor of the other. R6 contains no deletion, rename,
reuse or overwrite instruction for the prior R4 local restore.

## Production parser and long-run boundary

The production parser accepted the exact R6 command with:

- runner module `colab.run_vgg16_54_r1_r1`;
- input root `/content/vgg16_54_input`;
- state path
  `/content/drive/MyDrive/CPV301/Traffic_Sign_Detector/M1_D1_Colab/runs/vgg16_54_seed_20261018_r2`;
- work root `/content/vgg16_54_long_r6_work`;
- `mode=resume`;
- `stop_after=None`.

The command omits `--stop-after`, so the existing production long-run path still requires and
verifies the exact two-runtime smoke proof. Production prior-smoke validation accepted the current
epoch-2 state only with the QA-reviewed resume runtime digest
`648af06dd95af878657f2f041dd78a18cdf3137c27858176454204065a3e1ff5`.
The locally synced execution remains `SMOKE_STOP` at epoch 2 with exactly two attempts and
`sealed_test_accessed=false`; the R5 fail-closed collision did not append an ATTEMPT.

There is no `--split`, `--final-eval`, `export-test`, sealed-test path or test-data route in the
exact R6 command or contract.

## Work-root and adversarial checks

- A new empty absolute work root restored a synthetic verified checkpoint successfully.
- A pre-existing `work_root/RUN_NAME` destination raised `resume destination already exists`.
  Sentinel bytes and the complete pre-existing destination roster remained unchanged; no delete,
  rename or overwrite occurred.
- A symlinked work root and a regular-file work root were rejected before restore, without changing
  their targets.
- The shared checkpoint store performs component-wise no-symlink directory checks, verifies Drive
  telemetry and checkpoint bytes before restore, creates a destination only when absent and copies
  each artifact atomically with size/hash readback.
- Relative work-root inputs are normalized lexically to an absolute path by the production helper;
  the exact R6 contract does not rely on that behavior because it pins an absolute `/content` path.
- Mutating work root, mode, stop boundary, state, sealed flag or resume digest changed the pinned
  R6 contract hash. Any command mutation likewise changes the reviewed contract bytes.
- The production same-runtime, Owner, source-QA, runtime-source-QA and smoke-proof guards are
  inherited unchanged from QA-PASS R5.

## Reproduced commands and results

```text
graft check .
graft ask "Locate VGG16-54 R1 long-run R6 command contract, its R5 delta, --work-root parser/default behavior, restore destination collision handling, safe-directory guards, tests, and sealed-test boundaries." --source .
cd detector && uv run ruff check tests/test_vgg16_54_r1_long_r5_contract.py tests/test_vgg16_54_r1_long_r6_contract.py colab/run_vgg16_54_r1_r1.py colab/run_vgg16_54_r1.py m1/checkpoint_store.py m1/checkpoint_store_r2.py vgg16_54/contract.py vgg16_54/contract_r1.py
cd detector && uv lock --check
cd detector && uv run pytest -q tests/test_vgg16_54_r1_long_r5_contract.py tests/test_vgg16_54_r1_long_r6_contract.py tests/test_vgg16_54_r1_r1.py tests/test_vgg16_54_r1.py tests/test_checkpoint_store.py tests/test_checkpoint_store_r2.py
uv lock --check
```

Results: Ruff PASS; detector and root lock PASS; targeted R5/R6, runtime and checkpoint suite
`39 passed`; direct delta/parser/state/work-root adversarial harness PASS. Final `graft check .`:
OK, 4,959 nodes; the optional unbuilt meaning layer is non-blocking.

## Verdict and boundary

`PASS`, zero blockers, for executing **only the exact pinned R6 command contract** on the still
running QA-reviewed resume runtime. Before execution, the exact destination
`/content/vgg16_54_long_r6_work/D1_VGG16_54_R1` must be absent. If it exists, the safe outcome is a
terminal fail-closed result; do not delete or overwrite it under this authorization.

This verdict authorizes no alternate work root, runtime, state, proof or command. It is not
evidence that long training started or completed. Packaging, validation evaluation, result QA and
model comparison remain separate gates. Sealed-test access remains forbidden.
