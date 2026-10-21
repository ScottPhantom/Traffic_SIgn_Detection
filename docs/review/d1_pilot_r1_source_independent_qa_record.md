# D1 single-seed 100-epoch pilot R1 source independent QA record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_FAIL`  
Reviewer: `Codex independent source-QA session`  
Boundary: `READ_ONLY_SOURCE_QA_NO_TRAINING_NO_UPLOAD_NO_DOWNLOAD_NO_COLAB_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**FAIL.** The notebook is unexecuted, deterministic, train/validation-only, and correctly binds the
reviewed R6 runner and most of the intended pilot configuration. However, one **High** finding
prevents live use: the notebook leaves early stopping enabled while requiring an exact
`epoch-0100` result. The inherited runner converts an early-stopped result into durable
`SUCCEEDED` state, publishes the result archive, and consumes the only allowed resume attempt
before the notebook notices that epoch 100 was not reached.

Finding count: **0 Critical, 1 High, 0 Medium, 0 Low**.

This record does not authorize commit/push or a live pilot. The D1 pilot remains **NO-GO** until an
append-only R2 repair receives a new independent QA PASS. Sealed-test export/access, final
evaluation, model acceptance and deployment remain **NO-GO**.

## Reviewed scope and pinned bytes

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/d1_train_pilot_r1.ipynb` | `58261e981940e7e7c0b43ecab6ee09a63e37e57341c57a88440213c965904881` |
| `scripts/build_d1_pilot_notebook.py` | `ab05d0a9b57a9f930d7e1af73649d28acb207e9d0edc57b6703215436e21e5ca` |
| `tests/test_d1_pilot_colab.py` | `635a2b1bdf36ad11eb1aaeb05fc648ec3ee0ce3a575ed0500e3ed5e6f75affe8` |
| `docs/review/d1_pilot_r1_implementation_record.md` | `8d3d6ddf6cbe7ece68cb64f6eb82101b3825d40aaaa96da39699cb66ddcac161` |
| reviewed R6 runner, current and commit `47c86d17430808ceeee6e1a1a553cf6fef88e5ed` | `71a9f4a9f8efaa81f657dd414ab8a7d3354ae13a7fcd024e04b42ef2ccce8a35` |
| R6 smoke notebook used as generator input | `e42716fad4eb7b8d651565b611f11936d6a7b8b624832dccad8e513c55263fa6` |
| `detector/uv.lock` | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |

Git object `47c86d17430808ceeee6e1a1a553cf6fef88e5ed` exists and is a commit. Its R6
runner bytes match the current reviewed runner hash above.

## Verified properties

- The notebook has seven cells; every code cell has `execution_count=null` and empty outputs.
- An independent in-memory reconstruction from the R6 notebook and `REPLACEMENTS` reproduced the
  notebook byte-for-byte at SHA-256 `58261e98...04881`; every code cell parsed as Python.
- The command fixes `MODE="fresh"`, code commit `47c86d...`, state label
  `pilot_seed_20261018_r1`, seed `20261018`, epochs `100`, image size `1280`, batch `4`, device
  `0`, and tag `pilot_100e_seed_20261018_r1`.
- Fresh mode adds `--stop-after-epoch 1`; resume mode omits it and therefore uses the real R6
  `--resume` path. The final notebook assertion requires `epoch-0100`.
- The notebook retains the R6 Drive bundle/sidecar/part hashes, clean checkout assertion,
  approved-weight verification/download switch, archive existence check and strict live-state
  verifier. The R6 verifier requires fresh `PAUSED_FOR_RESUME`, resume `SUCCEEDED`, exactly two
  distinct runtime digests, common run/checkpoint bindings and `sealed_test_accessed=false`.
- The notebook contains no `export-test`, `--final-eval`, or processed test-directory reference.
  The exact sealed-test access-log path was absent before and after this review.
- No notebook cell, Colab runtime, Drive operation, training, upload, download or sealed-test
  operation was performed by this QA.

## Finding

### QA-D1-PILOT-R1-001 — High — exact 100 epochs can become a durable false success

The pilot command does not pass `--patience`, so the inherited parser supplies `30`. Ultralytics
8.4.172 treats patience 30 as enabled early stopping; its installed `EarlyStopping` implementation
explicitly states that `0` disables early stopping.

If validation fitness fails to improve for 30 epochs, `m1.resumable_train` returns
`COMPLETED_EARLY_STOPPED` with `completed_epoch < 100` (`detector/m1/resumable_train.py`, lines
204-218). The R6 inheritance chain reaches the R1 outer runner, whose accepted terminal statuses
include `COMPLETED_EARLY_STOPPED`; it then writes `execution.status="SUCCEEDED"`, creates the
archive, and appends a `SUCCEEDED` resume attempt (`detector/colab/run_d1_colab_checkpoint_r1.py`,
lines 455-476).

Only after those durable mutations does notebook cell 6 assert that the latest generation is
`epoch-0100`. That assertion correctly turns the visible cell red, but recovery is already blocked:
the strict R4 runtime-evidence path permits exactly one completed fresh attempt before resume and
exactly two terminal attempts overall. A second resume on the same state is rejected.

Consequences:

1. The package can publish a result archive and durable `SUCCEEDED` claim that violates its own
   exact-100-epoch success criterion.
2. The failed notebook assertion cannot roll back that archive or terminal attempt.
3. The claimed checkpoint/retry plan cannot continue that state to epoch 100.
4. The current tests all pass because none asserts the reviewed pilot patience or attacks the
   early-stopped terminal path.

Required append-only repair:

- create Pilot R2 rather than modifying this reviewed R1 snapshot;
- explicitly pass `--patience 0` in both fresh and resume command construction so early stopping
  is disabled for the exact-100-epoch pilot, and record that fixed value in the implementation
  record;
- add a notebook test that requires the exact `--patience 0` pair, plus a regression test proving
  that an outcome below epoch 100 cannot be written/packaged as pilot `SUCCEEDED`;
- make the builder fail if any expected replacement has zero or multiple matches, and pin the
  R6 source-notebook hash, so regeneration cannot silently drift;
- rerun targeted tests, all repository verifiers, the detector gate and independent source QA.

## Mechanical checks

```text
graft check .
graft map .
graft ask "Trace the D1 pilot R1 notebook generation and execution contract..." --source .
graft ask "For detector/colab/run_d1_colab_checkpoint_r6.py and inherited runners..." --source .
uv run ruff check scripts/build_d1_pilot_notebook.py tests/test_d1_pilot_colab.py
uv run pytest -q tests/test_d1_pilot_colab.py tests/test_d1_checkpoint_runtime_evidence_r4.py \
  tests/test_d1_checkpoint_runtime_evidence_r4_r3.py \
  tests/test_d1_checkpoint_runtime_evidence_r4_r4.py \
  tests/test_d1_checkpoint_runtime_evidence_r4_r5.py \
  tests/test_d1_checkpoint_runtime_evidence_r4_r6.py
uv lock --check
uv run python scripts/run_parallel_checks.py verifiers
cd detector && uv run ruff check m1 tests && uv run pytest -q && uv lock --check
```

Observed results:

- targeted pilot/runtime tests: **52/52 PASS**;
- repository verifiers: **52/52 PASS** in 97.2 s wall time;
- detector Ruff: **PASS**;
- detector tests: **93/93 PASS**;
- root and detector lock checks: **PASS**;
- Graft: graph in sync.

These green mechanical checks do not close QA-D1-PILOT-R1-001 because the present tests do not
exercise or forbid the early-stopped false-success path.

## Authorization boundary

| Action | QA disposition |
| --- | --- |
| Preserve R1 as failed review evidence | **YES** |
| Implement append-only Pilot R2 repair | **YES** |
| Commit/push Pilot R1 for live use | **NO-GO** |
| Start the live 100-epoch pilot | **NO-GO** |
| Upload/access sealed test | **NO-GO** |
| Final evaluation/model acceptance/deployment | **NO-GO** |
