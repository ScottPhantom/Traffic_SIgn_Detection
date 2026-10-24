# VGG16-54 R1 R3 fresh-smoke launcher independent QA record

Status: `QA_PASS_FRESH_EPOCH_1_ONLY`

Reviewed: `2026-10-24T19:52:06+07:00`

Reviewer boundary: independent delta QA. The reviewer did not train, upload, download, commit,
push or access the sealed test. This append-only record reviews only the R3 launch repair.

## Reviewed files and anchors

- Builder SHA-256:
  `155ee86863cb3110b2cac64e594d2f48b39815a341a7a88946745dd82c6ff7de`.
- Notebook SHA-256:
  `d0913e2269c69068faa3f7232c6d5ebcf226ff24a25368a18e3c57ec750d7c86`.
- Notebook-test SHA-256:
  `e155eaf5c5ab432cd31d4a75ea92fda6a239bd4d324d8b14af6f987737e38b0f`.
- R2 live-failure-record SHA-256:
  `998fdc17ee78ec0a24aca361f679204c831e8a1a732799cdcb20fd65ccea0e02`.
- QA-PASS R2 notebook SHA-256:
  `79bed40e4854717872cf6be0037e3e20e29bacda95e2ce49611899357be03aa4`.
- Immutable source commit:
  `2e1d981e70e02b19d1998fa17be8c8a0de033df0`, present on
  `origin/codex/vgg16-54-r1`.
- Owner proof SHA-256:
  `f09c7707263b52337957de5dd9ac2bf22712bb9135df8a84880633718ade06af`.
- Base source-QA proof SHA-256:
  `10f0ca69e32aed906d0bf8cad36aaacf3d40ea069faec51fb084de0d7ecfb216`.
- Runtime-successor source-QA proof SHA-256:
  `cbd531302429908354858640ac501e8c0d1805c5dec5462bf5e6a1e611b044f5`.

The immutable commit contains `detector/colab/run_vgg16_54_r1_r1.py`; its commit-object file
SHA-256 is `46eddeab153f8c775a44a1cc3e3cae5340c2cd4d4c5e5dc68f47b5ba556b259e`.

## Failure reproduction boundary and R3 delta

The pinned R2 failure record establishes that the exact QA-approved R2 notebook reached the
reviewed immutable checkout after all proof/hash checks and bundle extraction, then failed before
state creation with `ModuleNotFoundError: No module named 'colab'`. It also establishes that
`M1_D1_Colab/runs/vgg16_54_seed_20261018_r2` did not exist afterward, no ATTEMPT, checkpoint or
epoch was created, and the sealed test was not accessed.

An independent structural comparison found the R3 notebook identical to R2 except for exactly
three declared cells:

1. the title identifies R3;
2. the runner invocation changes from `python colab/run_vgg16_54_r1_r1.py` to
   `python -m colab.run_vgg16_54_r1_r1`;
3. the final gate explains the module-resolution repair and retains the epoch-1 stop boundary.

Cell count, notebook metadata, every configuration/proof/source/state anchor, and every other cell
remain byte-equivalent at the parsed-cell level. The private Drive state intentionally remains the
unused R2 state path because the recorded R2 terminal failure created no state.

## Reproduced evidence

- Independent temporary generation was byte-identical to the reviewed R3 notebook and reproduced
  its exact SHA-256.
- All nine cells are clean; every code cell has `execution_count=null`, no output, and compiles.
- The notebook requests Colab L4, checks out the immutable commit detached, reads back the commit,
  and hash-reads all three proof files before invoking the governed runner.
- Defaults remain exactly `MODE='fresh'`, `STOP_AFTER=1`, and the isolated state
  `M1_D1_Colab/runs/vgg16_54_seed_20261018_r2`.
- From the real `detector/` working directory,
  `uv run python -m colab.run_vgg16_54_r1_r1 --help` returned zero and exposed the governed proof,
  mode and stop arguments. This directly closes the observed script-path import failure.
- The governed runner refuses existing local-run or Drive recovery state in fresh mode, restricts
  a fresh smoke to epoch 1, requires CUDA, persists runtime/GPU and binding evidence, and exposes no
  sealed-test or test-split route.
- Post-run readback still requires `SMOKE_STOP`, epoch `1`, `sealed_test_accessed=false`, exact
  `NVIDIA L4`, a 64-character runtime digest, and equal run/checkpoint binding hashes.
- Targeted root gate: Ruff PASS, root lock PASS, and R2+R3 notebook tests `8 passed`.
- Targeted detector gate: detector lock PASS and Ruff PASS for the invoked successor/runtime
  contract files.
- Final `graft check .`: OK, 4,938 nodes; the optional unbuilt meaning layer is non-blocking.

## Adversarial delta checks

In-memory mutations of the immutable commit, Owner proof hash, base-QA proof hash, runtime-QA
proof hash, state path, mode, stop boundary, module invocation and a hidden final-evaluation route
all differed from the deterministic reviewed output and were rejected. Direct R2/R3 comparison
also found no hidden source, proof, configuration, state, metadata or output change. The exact R3
notebook contains no `export-test`, `--final-eval`, test-split route or sealed-test access-log path.

## Verdict and boundary

`PASS`, zero blockers, for uploading and executing **only the exact reviewed R3 notebook** on a
fresh NVIDIA L4 through epoch 1. Independent artifact QA must then verify the R3 checkpoint,
execution JSON, SQLite/text logs, runtime/GPU evidence, binding hashes and
`sealed_test_accessed=false`. This PASS does not authorize resume, long training, sealed-test
access or model publication.
