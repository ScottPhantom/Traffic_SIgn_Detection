# D1 single-seed 100-epoch pilot R2 source independent QA record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_PASS_SOURCE_ONLY_NO_LIVE_PILOT`  
Reviewer: `Codex independent source-QA session`  
Boundary: `READ_ONLY_SOURCE_QA_NO_TRAINING_NO_UPLOAD_NO_DOWNLOAD_NO_COLAB_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**PASS for the final source package identified below.** Pilot R2 closes the Pilot R1 High finding
before the inherited runner can write a successful execution, append a successful resume attempt or
package an archive. It also fails closed on configuration drift, non-integer epoch values, an early
stop, every resume outcome other than exact epoch 100 and every sealed-test marker.

Finding count on the final reviewed bytes: **0 Critical, 0 High, 0 Medium, 0 Low**.

This PASS authorizes an implementation commit/push followed by a separate, narrowly scoped notebook
code-pin commit. It does **not** authorize a live pilot from the present notebook because
`CODE_COMMIT` is intentionally `PENDING_AFTER_QA`. The pinned notebook must be regenerated and
verified against the exact implementation commit before any Colab execution. Sealed-test
export/access, final evaluation, model acceptance and deployment remain **NO-GO**.

## Reviewed state and pinned bytes

The review used repository HEAD `56c971f2b5ff34cb182dfb9249f89b14e9978af7` plus the uncommitted
append-only Pilot R1/R2 package. R1 remains immutable failed-review evidence.

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/d1_train_pilot_r2.ipynb` | `9d9b9f2e92fde81c68f85fdf436e123d709af6da47ed61c0055114ef479728b0` |
| `detector/colab/run_d1_colab_pilot_r2.py` | `608fa1e6a173a2bd06f32c0e15a2759ea5709aa666bcce0beb35e0a1b4d0b11c` |
| `scripts/build_d1_pilot_notebook_r2.py` | `df356fda8a0af3c0a190b3708afbb360da7bcfb7797f6024ebcc87cc7dc1c40d` |
| `tests/test_d1_pilot_r2.py` | `810362f097930f328b96ffcd49466f922e676eac2ea28a281f65f1a7680b77e4` |
| `docs/review/d1_pilot_r2_implementation_record.md` | `5a1f86024e3f0fea525378c4714c3a92658591f913701a8add9d2fac77458f0f` |
| frozen R6 source notebook | `e42716fad4eb7b8d651565b611f11936d6a7b8b624832dccad8e513c55263fa6` |
| inherited R6 runner | `71a9f4a9f8efaa81f657dd414ab8a7d3354ae13a7fcd024e04b42ef2ccce8a35` |
| `detector/uv.lock` | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |

The predecessor hashes remain those recorded by the R1 FAIL review:

| Immutable predecessor artifact | SHA-256 |
| --- | --- |
| `detector/colab/d1_train_pilot_r1.ipynb` | `58261e981940e7e7c0b43ecab6ee09a63e37e57341c57a88440213c965904881` |
| `scripts/build_d1_pilot_notebook.py` | `ab05d0a9b57a9f930d7e1af73649d28acb207e9d0edc57b6703215436e21e5ca` |
| `tests/test_d1_pilot_colab.py` | `635a2b1bdf36ad11eb1aaeb05fc648ec3ee0ce3a575ed0500e3ed5e6f75affe8` |
| `docs/review/d1_pilot_r1_implementation_record.md` | `8d3d6ddf6cbe7ece68cb64f6eb82101b3825d40aaaa96da39699cb66ddcac161` |

## R1 finding reproduction and R2 closure

R1 omits `--patience`, so the inherited parser uses `30`. Its inherited terminal-status set accepts
`COMPLETED_EARLY_STOPPED`, writes `execution.status="SUCCEEDED"`, packages the result and appends a
successful attempt before the notebook checks for `epoch-0100`. This reproduces
`QA-D1-PILOT-R1-001`.

On the final R2 bytes:

- the notebook passes exact `--patience 0`;
- the runner rejects any epochs other than 100, patience other than 0, seed other than `20261018`,
  image size other than `1280`, batch other than `4`, device other than `0` and tag other than
  `pilot_100e_seed_20261018_r2` before delegation;
- fresh requires `--stop-after-epoch 1`, while resume forbids every stop target and therefore uses
  the inherited real `--resume` path;
- the guard intercepts `training_outcome.json` through the inherited R2/R1 `strict_json` chain
  before the R1 success mutation and packaging branch;
- fresh accepts only `PAUSED_FOR_RESUME` at exact integer epoch 1; resume accepts only `COMPLETED`
  or `COMPLETED_FROM_FINAL_CHECKPOINT` at exact integer epoch 100;
- `COMPLETED_EARLY_STOPPED`, below/above-100 values, `100.0`, booleans and a non-false
  `sealed_test_accessed` value fail before successful packaging;
- an abrupt resume-runtime loss before a terminal attempt is appended can be retried against the
  retained fresh pause. A recorded failure is deliberately preserved and blocks silent reuse of the
  strict two-attempt evidence chain.

During review, adversarial probing found that an earlier candidate accepted `100.0` as equal to
`100`, and PM separately identified missing runner-level guards for the reviewed configuration.
Both were repaired before this verdict; the final hashes and regression results above include the
exact-integer and configuration-drift guards.

## Notebook and deterministic-builder verification

- The notebook has seven cells; all six code cells have `execution_count=null` and empty outputs.
- Every code cell parses as Python. `CODE_COMMIT="PENDING_AFTER_QA"` makes the current notebook fail
  before clone/checkout and prevents premature live use.
- The reviewed command fixes run label `pilot_seed_20261018_r2`, seed `20261018`, epochs `100`,
  image size `1280`, batch `4`, patience `0`, device `0` and tag
  `pilot_100e_seed_20261018_r2`.
- The notebook uses the reviewed train/validation bundle and contains no `export-test`,
  `--final-eval` or processed-test-directory reference.
- An independent in-memory R2 build reproduced the notebook byte-for-byte. The builder pins the
  exact frozen R6 notebook hash and rejected a duplicated source replacement after its expected
  cardinality changed from one to two.
- Fresh mode asserts `epoch-0001`; resume asserts execution `SUCCEEDED`, exact epoch 100,
  `epoch-0100`, one result archive, distinct runtime digests and
  `sealed_test_accessed=false`.
- The exact sealed-test access-log path was absent throughout this review.

## Mechanical checks

```text
uv run ruff check src tests scripts/build_d1_pilot_notebook_r2.py \
  detector/colab/run_d1_colab_pilot_r2.py
uv run pytest -q tests/test_d1_pilot_colab.py tests/test_d1_pilot_r2.py \
  tests/test_d1_checkpoint_runtime_evidence_r4.py \
  tests/test_d1_checkpoint_runtime_evidence_r4_r3.py \
  tests/test_d1_checkpoint_runtime_evidence_r4_r4.py \
  tests/test_d1_checkpoint_runtime_evidence_r4_r5.py \
  tests/test_d1_checkpoint_runtime_evidence_r4_r6.py
uv lock --check
uv run python scripts/run_parallel_checks.py verifiers
cd detector && uv run ruff check m1 tests && uv run pytest -q && uv lock --check
graft check .
```

Observed results on the final reviewed tree:

- root Ruff: **PASS**;
- targeted Pilot/R4-R6 tests: **71/71 PASS**;
- repository verifiers: **52/52 PASS** in 97.9 s wall time;
- detector Ruff: **PASS**;
- detector tests: **93/93 PASS**;
- root and detector lock checks: **PASS**;
- Graft wiring graph: **OK, in sync**.

These are source/package checks. No live L4 runtime, pilot epoch, archive, metric or model checkpoint
was produced or claimed by this review.

## Authorization boundary

| Action | QA disposition |
| --- | --- |
| Preserve Pilot R1 and its FAIL record unchanged | **YES** |
| Commit/push the final R2 implementation bytes above | **YES, source QA PASS** |
| Replace only `PENDING_AFTER_QA` with that implementation commit and create a separate code-pin commit | **YES, then re-verify exact pinned bytes** |
| Start the live 100-epoch pilot from the current unpinned notebook | **NO-GO** |
| Start the live pilot after the pinned notebook is regenerated and independently verified | **PENDING PIN VERIFICATION** |
| Upload/access sealed test | **NO-GO** |
| Final evaluation/model acceptance/deployment | **NO-GO** |
