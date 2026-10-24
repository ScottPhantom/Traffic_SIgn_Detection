# VGG16-54 R1 long-run R5 command-contract independent QA record

Status: `QA_PASS_LONG_RUN_COMMAND_ONLY`

Reviewed: `2026-10-24T20:31:29+07:00`

Reviewer boundary: independent read-only launch-contract QA. The reviewer did not run training,
resume the model, modify source or Drive state, upload, download, commit, push or access the sealed
test. This append-only record authorizes only the exact command-contract bytes reviewed below.

## Reviewed files and anchors

- Long-run command contract SHA-256:
  `0c6840281d0f53e52610e392ceca4aacbd40996db4e8ca8865c3cbd57088c372`.
- Implementation record SHA-256:
  `0ba8f55295db4872fabf584beafd24984795c3f78359aee32a6f783cda46ccf1`.
- Contract-test SHA-256:
  `7bfcf58b37e847d3833c1962f66ddbb75b7f04fbd9d5c5cbcb43abc24b5a9692`.
- Two-runtime smoke proof SHA-256:
  `898a440709dd477b9ec70569b52464047adb55de8ed48325eeef091f3e759132`.
- Two-runtime artifact-QA record SHA-256:
  `bd9dd44387929cfca569140b528fdaeb6b372bfdc52b90482795a2ff461b9923`.
- Immutable source commit:
  `2e1d981e70e02b19d1998fa17be8c8a0de033df0`, present on
  `origin/codex/vgg16-54-r1`.

## Closed contract and pinned authority

The contract has exactly the reviewed 19-field schema, schema version 1, package
`VGG16-54-R1-LONG-R5`, and authorization
`OWNER_APPROVED_LONG_RUN_AFTER_TWO_RUNTIME_QA`. The following anchors are internally consistent
with the production contracts and exact Drive mirrors:

- configuration SHA-256:
  `b5275ca6635859f3eb2ae5d98e480da18f748667a96f92a36d1e2145b197c15a`;
- bundle-manifest SHA-256:
  `bae147b6f7c6f80ac973923df4b60fd31b6587221fe75eaa2d9ed4b93ee6a51b`;
- Owner approval SHA-256:
  `f09c7707263b52337957de5dd9ac2bf22712bb9135df8a84880633718ade06af`;
- base source-QA SHA-256:
  `10f0ca69e32aed906d0bf8cad36aaacf3d40ea069faec51fb084de0d7ecfb216`;
- runtime-successor source-QA SHA-256:
  `cbd531302429908354858640ac501e8c0d1805c5dec5462bf5e6a1e611b044f5`;
- run/checkpoint binding SHA-256:
  `fe334b1877454adb608628bde0c1a3287a31b861f5bb7b16635e96a8a1953bbe`;
- reviewed resume-runtime digest:
  `648af06dd95af878657f2f041dd78a18cdf3137c27858176454204065a3e1ff5`.

The exact two-runtime proof is present at the contract's private Drive path
`M1_D1_Colab/vgg16_54_r1_r4_two_runtime_smoke_qa_proof.json`. Its synced bytes are identical to
the repository proof and reproduce the pinned SHA-256. The Owner, source-QA and runtime-source-QA
files at their exact Drive paths also reproduce their contract hashes.

## Production command validation

The exact command begins with:

```text
uv run python -m colab.run_vgg16_54_r1_r1
```

The production parser accepted the frozen arguments with:

- working directory `/content/Traffic_Sign_Detector/detector`;
- input root `/content/vgg16_54_input`;
- state path
  `/content/drive/MyDrive/CPV301/Traffic_Sign_Detector/M1_D1_Colab/runs/vgg16_54_seed_20261018_r2`;
- `mode=resume`;
- `stop_after=None`, because the command contains no `--stop-after`;
- all four proof paths and hashes equal to the closed contract.

The production `verify_smoke_qa(...)` accepted the exact proof and bundle hash. Production Owner,
source and runtime-successor proof verifiers accepted the exact Drive mirrors. The production
prior-smoke verifier accepted the epoch-2 state only when the current runtime digest equalled the
reviewed resume digest above. It rejected both the fresh-runtime digest and an unrelated digest,
so the long run cannot migrate silently to another runtime.

There is no `--stop-after`, `--split`, `--final-eval`, `export-test`, sealed-test path or test-data
route in the exact command or contract. `sealed_test_accessed` is exactly `false` in both the
contract and the two-runtime proof.

## Adversarial checks

- Any change to command, state, mode, stop boundary, proof path/hash, config, bundle, source or
  runtime anchor changes the independently pinned R5 contract hash.
- Smoke-proof mutations covering `sealed_test_accessed=true`, wrong bundle hash, duplicated runtime
  digest and an extra schema key were rejected by the original hash pin. When re-pinned solely for
  the semantic attack, production `verify_smoke_qa(...)` still rejected every mutation.
- The same-runtime continuation rule accepted only the second, QA-reviewed digest and rejected the
  fresh and unrelated digests.
- Removing the smoke proof would leave `stop_after=None` without the required long-run QA inputs;
  the production train gate rejects that combination before model work.
- Unknown final-evaluation/test flags are absent and are not part of the production parser.
- Production proof-path validation rejects symlinked path components and non-regular proof files.

## Reproduced commands and results

```text
graft check .
graft ask "Locate the VGG16-54 R1 long-run R5 command contract, production parser and verify_smoke_qa flow, state/runtime same-runtime guards, tests, and any sealed-test or stop-after routes." --source .
cd detector && uv run ruff check tests/test_vgg16_54_r1_long_r5_contract.py colab/run_vgg16_54_r1_r1.py colab/run_vgg16_54_r1.py vgg16_54/contract.py vgg16_54/contract_r1.py
cd detector && uv lock --check
cd detector && uv run pytest -q tests/test_vgg16_54_r1_long_r5_contract.py tests/test_vgg16_54_r1_r1.py tests/test_vgg16_54_r1.py
uv lock --check
```

Results: Ruff PASS; detector and root lock PASS; targeted production/parser/runtime suite
`25 passed`; direct production verifier and adversarial harness PASS. Final `graft check .`: OK,
4,955 nodes; the optional unbuilt meaning layer is non-blocking.

## Verdict and boundary

`PASS`, zero blockers, for executing **only the exact pinned R5 command contract**, on the still
running QA-reviewed resume runtime whose digest is
`648af06dd95af878657f2f041dd78a18cdf3137c27858176454204065a3e1ff5`.

This is a command-contract authorization, not evidence that training has started or completed. If
the reviewed Colab runtime has been replaced or disconnected, the governed same-runtime check must
fail and this contract does not authorize substituting a new runtime. Completion, packaging,
validation evaluation, result QA and any later model comparison remain separate gates. Sealed-test
access remains forbidden.
