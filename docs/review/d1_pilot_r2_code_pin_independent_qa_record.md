# D1 Pilot R2 code-pin independent QA record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_PASS_CODE_PIN_ONLY`  
Reviewer: `Codex independent code-pin QA session`  
Boundary: `READ_ONLY_NO_TRAINING_NO_UPLOAD_NO_DOWNLOAD_NO_COLAB_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**PASS.** The code-pin change is limited to replacing `PENDING_AFTER_QA` with exact implementation
commit `939f6bbce9f5c955b13ebcc84addd5083d242355` in the deterministic builder and generated
notebook, plus the matching regression assertion. The generated notebook reproduces byte-for-byte,
remains unexecuted and retains the independently approved Pilot R2 configuration, outcome guards,
checkpoint/resume contract and sealed-test boundary.

Finding count: **0 Critical, 0 High, 0 Medium, 0 Low**.

This PASS authorizes committing and pushing the exact code-pin package identified below. It also
authorizes starting the live single-seed Pilot R2 after push readback confirms that the GitHub
remote can resolve the implementation commit and the final code-pin commit. At review time the
local branch was three commits ahead of its tracking ref, so that remote-reachability check remains
an operational precondition, not an observed fact. Sealed-test export/access, final evaluation,
model acceptance and deployment remain **NO-GO**.

## Reviewed lineage and hashes

| Artifact | SHA-256 |
| --- | --- |
| implementation commit | `939f6bbce9f5c955b13ebcc84addd5083d242355` |
| source-QA record at that commit | `b1bf79412382a966f3ac5e96f09011664bbcd14e58cf18751c4bbadb0c0ac00a` |
| unchanged Pilot R2 runner | `608fa1e6a173a2bd06f32c0e15a2759ea5709aa666bcce0beb35e0a1b4d0b11c` |
| pinned `detector/colab/d1_train_pilot_r2.ipynb` | `721c5c0f35eb58719bcc6b5a71ce24cce136388bb8060bc2393aec7a5da4b1ae` |
| pinned `scripts/build_d1_pilot_notebook_r2.py` | `f207a18c19d9c6915162ce323cab0c492a623c0ec3c8ff4855812bfab7cc8b99` |
| pinned `tests/test_d1_pilot_r2.py` | `84851f6c82208c346ef5d12f59e776f7dbd611d4794d72e18bc1787ac839d8dc` |
| `docs/review/d1_pilot_r2_code_pin_record.md` | `07cb4d291c01ef726e033d53328868d09f6053cb729334fcf21655360b608030` |

Git object `939f6bbce9f5c955b13ebcc84addd5083d242355` exists and is the current implementation
commit. Reading the runner and source-QA record from that object reproduces their reviewed hashes.
The local tracking ref `origin/DEV/Rroject_Pineline` was still
`f674946a15f7035a656404df05ee1bf23e6323e4` during this QA; no network push was performed.

## Exact change verification

Relative to implementation commit `939f6bb...`, the tracked diff contains exactly three files and
five insertions/three deletions:

- notebook: one line replaces `PENDING_AFTER_QA` with the exact 40-hex implementation commit;
- builder: the same replacement output changes to the exact implementation commit and reviewed
  comment;
- test: the prior pending assertion changes to an exact-commit assertion plus an assertion that no
  `PENDING_AFTER_QA` token remains.

No runner byte changed. The separate code-pin record accurately states the source-QA record hash,
implementation commit, builder/notebook pin and unchanged authorization boundary.

## Notebook and builder readback

- An independent in-memory builder invocation produced bytes identical to the pinned notebook.
- All six code cells remain unexecuted, have empty outputs and parse as Python.
- The notebook fixes run label `pilot_seed_20261018_r2`, seed `20261018`, epochs `100`, image size
  `1280`, batch `4`, patience `0`, device `0` and tag `pilot_100e_seed_20261018_r2`.
- Fresh mode still adds only `--stop-after-epoch 1`; resume still omits the stop target and reaches
  the real inherited resume path.
- The exact-100 outcome assertions, `epoch-0100`, one-archive assertion, distinct-runtime evidence
  and `sealed_test_accessed=false` checks remain present.
- The notebook remains train/validation-only and contains no `export-test`, `--final-eval` or
  processed-test-directory reference.
- `results/experiments/sealed_test_access_log.jsonl` remained absent.

## Mechanical verification

```text
uv run ruff check scripts/build_d1_pilot_notebook_r2.py tests/test_d1_pilot_r2.py
uv run pytest -q tests/test_d1_pilot_colab.py tests/test_d1_pilot_r2.py \
  tests/test_d1_checkpoint_runtime_evidence_r4.py \
  tests/test_d1_checkpoint_runtime_evidence_r4_r3.py \
  tests/test_d1_checkpoint_runtime_evidence_r4_r4.py \
  tests/test_d1_checkpoint_runtime_evidence_r4_r5.py \
  tests/test_d1_checkpoint_runtime_evidence_r4_r6.py
uv lock --check
graft check .
```

Observed results:

- Ruff: **PASS**;
- targeted Pilot/R4-R6 tests: **71/71 PASS**;
- root lock check: **PASS**;
- deterministic byte reproduction, AST, unexecuted-state, configuration and sealed-boundary
  attack/readback script: **PASS**;
- Git diff check: **PASS**;
- Graft wiring graph: **OK, in sync**.

No notebook cell, Colab runtime, Drive operation, training, upload, download, commit, push or
sealed-test operation was performed by this QA.

## Authorization boundary

| Action | QA disposition |
| --- | --- |
| Commit/push the exact code-pin package and both code-pin records | **YES** |
| Start Pilot R2 before successful push/readback | **NO-GO** |
| Start live Pilot R2 after remote readback resolves implementation and code-pin commits | **GO** |
| Use train/validation bundle under the already approved Colab authorization | **GO for Pilot R2 only** |
| Upload/access sealed test | **NO-GO** |
| Final evaluation/model acceptance/deployment | **NO-GO** |
