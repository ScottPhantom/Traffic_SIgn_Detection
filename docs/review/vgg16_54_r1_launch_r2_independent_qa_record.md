# VGG16-54 R1 R2 fresh-smoke launcher independent QA record

Status: `QA_PASS_FRESH_EPOCH_1_ONLY`

Reviewed: `2026-10-24T19:40:41+07:00`

Reviewer boundary: independent delta QA. The reviewer did not train, upload, download, commit,
push or access the sealed test. This append-only record reviews only the R2 launch successor.

## Reviewed files and anchors

- Builder SHA-256:
  `fceeb708844e1bfabc4e333f613afbe2fe821626e3a3dcce4defc724af7108cb`.
- Notebook SHA-256:
  `79bed40e4854717872cf6be0037e3e20e29bacda95e2ce49611899357be03aa4`.
- Notebook-test SHA-256:
  `53f289a9f77ebab1e5f5c003334b061e9387e2d807b0e30b2dce9d9a29eb21e8`.
- Implementation-record SHA-256:
  `dc3ee0e6716ce8853571292d40aaddd27a1def206639f9bf77f6c3f5f8fd1492`.
- Immutable source commit:
  `2e1d981e70e02b19d1998fa17be8c8a0de033df0`, present on
  `origin/codex/vgg16-54-r1`.
- Owner proof SHA-256:
  `f09c7707263b52337957de5dd9ac2bf22712bb9135df8a84880633718ade06af`.
- Base source-QA proof SHA-256:
  `10f0ca69e32aed906d0bf8cad36aaacf3d40ea069faec51fb084de0d7ecfb216`.
- Runtime-successor source-QA proof SHA-256:
  `cbd531302429908354858640ac501e8c0d1805c5dec5462bf5e6a1e611b044f5`.

The immutable commit contains all three proof files at the exact hashes above and contains
`detector/colab/run_vgg16_54_r1_r1.py`.

## Reproduced evidence

- Independent temporary generation was byte-identical to the reviewed notebook and reproduced
  its exact SHA-256.
- All nine cells are clean; every code cell has `execution_count=null` and no output.
- The notebook requests Colab L4, while the successor runner independently requires the exact
  persisted device name `NVIDIA L4`.
- Checkout is detached at the pinned commit and the observed commit is compared exactly.
- All three private Drive proof files are hash-read before checkout/training and are also passed to
  the governed successor runner.
- State is isolated at `M1_D1_Colab/runs/vgg16_54_seed_20261018_r2`.
- Defaults are exactly `MODE='fresh'` and `STOP_AFTER=1`; the command invokes
  `colab/run_vgg16_54_r1_r1.py` with `--stop-after 1`.
- Post-run readback requires `SMOKE_STOP`, epoch `1`, `sealed_test_accessed=false`, exact
  `NVIDIA L4`, a 64-character runtime digest, and equal run/checkpoint binding hashes.
- No `export-test`, `--final-eval`, test-split route or sealed-test access-log path exists.
- Root launcher gate: Ruff PASS, lock PASS, `4 passed`.
- Detector successor gate: Ruff PASS, lock PASS, `9 passed`.
- Final `graft check .`: OK, 4,926 nodes; the optional unbuilt meaning layer is non-blocking.

## Adversarial delta checks

In-memory mutations of the commit, Owner proof hash, base-QA proof hash, runtime-QA proof hash,
state suffix, mode, stop boundary, hidden final-evaluation route, sealed-test export route and stale
cell output all changed the reviewed notebook hash and were rejected. The exact reviewed notebook
contains none of the forbidden routes or stale outputs. The successor regression tests also reject
non-L4 GPU evidence, same-runtime resume, fresh long-run mode, failed-R1 state reuse and invalid
successor source proof semantics.

## Verdict and boundary

`PASS`, zero blockers, for uploading and executing **only the exact reviewed notebook** on a fresh
NVIDIA L4 through epoch 1. Independent artifact QA must then verify the R2 checkpoint, execution
JSON, SQLite/text logs, runtime/GPU evidence, binding hashes and
`sealed_test_accessed=false`. This PASS does not authorize resume, long training, sealed-test
access or model publication.
