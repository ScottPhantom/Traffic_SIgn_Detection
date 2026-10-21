# D1 Pilot R5 notebook-pin package — independent QA record

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
QA role: independent, read-only source/package review  
Verdict: **PASS**

## Scope and authorization boundary

This review covers only:

- `scripts/build_d1_pilot_notebook_r5.py`;
- `detector/colab/d1_train_pilot_r5.ipynb`;
- `tests/test_d1_pilot_r5_notebook.py`.

QA did not edit PM source, run Colab, execute R5 against Drive, train or resume a model, package an
artifact, upload data, access the sealed test, commit, or push. The only new project file produced
by this review is this QA record.

## Reviewed package identities

| File | SHA-256 |
| --- | --- |
| `scripts/build_d1_pilot_notebook_r5.py` | `fff3ea340255aedbb8f4a233ce4b442bf163aa9ca725118049af28972c9761b4` |
| `detector/colab/d1_train_pilot_r5.ipynb` | `106ac040fc07a6d7aaf207bff321fa367ccac713f8b2d5c59ced8998913392fe` |
| `tests/test_d1_pilot_r5_notebook.py` | `4a5a78803acf906baeff4963d477510d9f8f03beec794f1ad8a5ef06f8e4e170` |

The notebook pins the following immutable predecessors:

| Role | Commit | Expected file SHA-256 |
| --- | --- | --- |
| training checkout | `939f6bbce9f5c955b13ebcc84addd5083d242355` | Git commit identity |
| Pilot R3 | `e20a69541e3a6327739238fc71691109ce8f51d0` | `8c9b23472091f6c677d635a54e4f4e8b896e1fcf204d627ba56eb208db00c49c` |
| Pilot R4 | `2cc45b467456e9300df613839d94c5cb0bbdcbba` | `ffcc88e2339b349775ca34e5e30531a102d0bcab1d45fa0dff9b1ea8bead25ad` |
| Pilot R5 | `6acc47f08dba385b730ac86d591cb55248d104d2` | `d4c7ab9b96fe92dd3eb6034fd1fb1144df7de35fbda88138f9b1d938f167d13b` |

Independent `git show <commit>:<path>` hashing reproduced all three sidecar hashes exactly. The
local `origin/DEV/Rroject_Pineline` remote-tracking ref contains all three sidecar commits.

## Findings

### 1. Deterministic and unexecuted notebook

PASS. Rebuilding through the reviewed builder reproduced the notebook byte-for-byte. SHA-256 for
the builder, generated notebook, and tests was unchanged before and after the deterministic test.
The notebook is valid nbformat 4.5, has five cells and four code cells, and every code cell has
`execution_count=null` with an empty output list.

The metadata explicitly requests a GPU accelerator and `gpuType=L4`. The metadata status remains
`PENDING_INDEPENDENT_QA`; the durable QA decision is this append-only record, so changing the
generated notebook after review is neither required nor permitted without a new hash and review.

### 2. Exact immutable pins

PASS. The generated notebook embeds the exact training commit plus independent commit and SHA-256
pins for R3, R4, and R5. It checks out the training commit detached, reads back `HEAD`, and requires
an exact match. Each sidecar is downloaded from the raw GitHub URL for its specific commit. The
downloaded bytes must match the pinned SHA-256 before they can be retained or executed.

Existing sidecars are opened with `O_NOFOLLOW`, must be regular files, must match the exact hash,
and must equal the newly downloaded bytes. New sidecars use `O_CREAT | O_EXCL | O_NOFOLLOW` and are
read back through the same verifier. Independent adversarial execution confirmed that an existing
sidecar symlink raises an error and a tampered regular sidecar fails its hash assertion.

### 3. Verification-only execution surface

PASS. The notebook contains no model-training call, resume-mode argument, bundle command, archive
builder, evaluation command, `export-test`, `--final-eval`, or sealed-test data path. It downloads
the exact R5 bytes and executes those bytes through `python -`, passing only:

- `--repo-root /content/Traffic_Sign_Detector`;
- `--state-dir /content/drive/MyDrive/CPV301/Traffic_Sign_Detector/M1_D1_Colab/runs/pilot_seed_20261018_r2`.

The pinned R5 source has already passed separate independent QA as a post-train packaged-state
verifier. It has no train, resume-from-checkpoint, package, bundle, evaluation, or sealed-test
route. Failure of checkout, download, hash verification, R5 execution, or result parsing prevents
the notebook from printing its terminal PASS marker.

### 4. Exact terminal evidence

PASS. Before invoking R5, the notebook requires the Drive pointer to name `epoch-0100`, the current
execution record to say `SUCCEEDED`, and `sealed_test_accessed` to be exactly `false`. These are
preflight assertions only; R5 subsequently authenticates the exact observed Drive bytes and applies
strict semantic validation.

After R5 returns successfully, the notebook parses its stdout and requires:

- status `D1_PILOT_R5_PACKAGED_STATE_VERIFIED`;
- latest generation `epoch-0100`;
- exactly 6 attempts;
- exactly 4 failed resume attempts;
- distinct runtime digests exactly `true`;
- `sealed_test_accessed` exactly `false`.

Only after all conditions pass does it print `D1_PILOT_R5_COLAB_FINALIZER_PASS`.

## Adversarial and validation evidence

- Targeted Ruff for builder and notebook tests: PASS.
- R5 notebook tests: **5/5 PASS**.
- Combined R3/R4/R5 source and notebook suites: **56 PASS, 1 SKIP**. The skip is the existing
  deliberately absent local-Drive fixture, not a package failure.
- Hash stability across the deterministic test: PASS for all three reviewed package files.
- Independent sidecar helper attack: fresh exact file accepted; symlink rejected; tampered regular
  file rejected.
- Commit-to-blob hash reproduction for R3/R4/R5: PASS.
- Notebook structure readback: five cells, four unexecuted code cells, L4 metadata: PASS.
- Root lock check: PASS, 168 packages resolved.
- Graft reported `STALE` for the new uncommitted notebook package. A freshness-aware
  `graft ask ... --source .` refreshed and inspected the builder/tests. QA did not run
  `graft build` because that would modify governed graph state; the release owner must rebuild and
  check Graft before committing this package.

## Verdict

**PASS.** The reviewed notebook-pin package is deterministic, unexecuted, L4-targeted, immutable at
all required commit/hash boundaries, fail-closed for linked or tampered sidecars, and restricted to
verification of the exact completed Pilot R2 Drive state. It requires the stated epoch-100 and
retry-aware terminal evidence and preserves `sealed_test_accessed=false`.

No blocker remains within this notebook-pin QA scope. This PASS permits the PM/owner to proceed with
the separate source-release decision. It does not authorize running Colab, changing Drive state,
starting another training batch, opening the sealed test, committing, pushing, uploading,
deploying, or publishing.
