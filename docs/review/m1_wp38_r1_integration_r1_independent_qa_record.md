# M1-WP38-R1 downstream integration R1 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `INDEPENDENT_QA_FAIL`

Reviewer: `Codex independent QA session (read-only source/artifact review)`

Reviewed checkout: committed base `85a8025e1ae1e78d4c84adb2cd6009003e8c93a1` plus the exact
uncommitted R1 bytes pinned below and unrelated user/PM worktree changes.

Boundary: `READ_ONLY_NO_SOURCE_FIX_NO_TRAINING_NO_EVALUATION_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL / NO-GO — 0 Critical, 1 High, 0 Medium and 1 Low findings.**

R1 closes the predecessor's ordinary linked-output attacks and fully closes M-1 for authenticated
Dataset Graph authorities. Current materialisation is semantically correct and train/val-only.
However, the writable implementation still has a reproducible check/use race after creating its
private staging directory. A concurrent replacement can redirect the first directory creation and
all subsequent output writes outside the staging tree; cleanup then fails and leaves the replaced
staging symlink behind. This is the same writable-path safety boundary H-1 intended to close, so
R1 cannot pass independent QA.

No training, validation evaluation, model inference, official bundle creation, Drive write,
commit/push or sealed-test access is authorized by this record.

## Findings

### H-1-R1 — Private staging path is not descriptor-bound and remains replaceable after check

Severity: **High**

Affected source: `scripts/build_m1_yolo_dataset_wp38_r1_integration_r1.py`, principally
`materialise()`, `_safe_tree()`, `_mkdir()` and exception cleanup.

The normal path is safer than the predecessor: the requested output must be absent, its existing
parents are walked with `lstat()`, and a random sibling staging directory is created. But after
`os.mkdir(staging)`, all descendants are still addressed by pathname. The code neither opens the
new staging directory with a no-follow directory descriptor nor rechecks its identity before
`_safe_tree(staging)`. Therefore a concurrent actor can remove the empty staging directory and
replace that exact pathname with a symlink before `_mkdir(staging, "images")`.

Independent stop-before-write reproduction:

1. Invoke the real `materialise()` flow in a temporary parent with a separate victim directory and
   sentinel.
2. At the `_safe_tree()` boundary, remove the newly created empty staging directory and replace it
   with `staging -> victim`, modelling a concurrent rename/replacement in the exact check/use
   window.
3. Let the real `_safe_tree()` call `_mkdir()`, but stop immediately before the first mutation.

Observed evidence:

- lexical first target: `.../.export.tmp-<uuid>/images`;
- resolved parent: the independent `victim` directory;
- `escaped_to_victim=true`;
- sentinel remained byte-identical because QA stopped before mutation;
- exception cleanup called `shutil.rmtree()` on the replaced symlink, raised `OSError`, masked the
  original failure and left `.export.tmp-<uuid>` present as a symlink.

Without the QA stop guard, `_mkdir()` would create `victim/images`; later label and image writes
would continue under the redirected location. The random UUID reduces accidental collision but
does not make the path identity stable against a watcher/replacement race.

Required remediation:

1. Preserve R1 and this verdict append-only; implement a new successor.
2. Open the trusted output parent and staging directory using directory file descriptors with
   no-follow semantics; retain and compare `fstat()` identity.
3. Perform directory creation, exclusive file writes and symlink creation relative to trusted
   `dir_fd` handles, or revalidate parent/staging identity immediately before every pathname write
   with race-safe failure behavior.
4. Make cleanup descriptor/identity-bound. If the staging pathname was replaced, remove only the
   originally created object when its identity still matches; never follow or recursively delete a
   replacement.
5. Add deterministic replacement-race attacks at output parent, staging root, `images`, `labels`,
   split directory and verification paths. Assert original error preservation, no victim mutation
   and no leftover staging entry.

### L-1 — Graft wiring graph is stale for the R1 source handoff

Severity: **Low**

`graft check .` reports the graph `STALE`: R1 exporter/view/tests are newly added and changes to
`run_parallel_checks.py`, `views.py` and `test_web_app.py` are not incorporated. This does not
change runtime semantics or the H-1-R1 verdict, but it violates the repository handoff contract
for new source. Independent QA did not rebuild Graft because this review is read-only.

Required remediation: after the R1 code successor is complete, run
`graft build . && graft check .` and include the synchronized graph in the handoff before fresh QA.

## Closure of predecessor findings

### Predecessor H-1 ordinary linked-output attacks

**PASS for non-racing cases.** Independent read-only attacks confirmed rejection before victim
mutation for:

- symlinked output parent;
- symlinked output root;
- existing output containing linked `images`, `labels`, split directory or final leaf;
- existing regular-file output;
- existing hardlinked-file output.

The sentinel, regular file and both hardlink names remained byte-identical. These cases are mostly
rejected by R1's new-output-only policy before any descendant is touched. Final-leaf writes inside
the private tree additionally use `O_EXCL`/`O_NOFOLLOW` or exclusive symlink creation. The
remaining concurrent replacement window is H-1-R1 above.

### Predecessor M-1 Dataset Graph authority

**PASS / closed.** Current authority pins and semantic validation reject both direct byte tampering
and coherent-repin attacks. Independent QA refreshed the temporary authority hash after each
mutation so that semantic validation, not only the first hash comparison, was exercised. All of
the following were rejected:

- forged WP38 corrected stem;
- WP38 wrong split;
- forged WP36 train-to-val movement;
- duplicate, missing and extra WP36 rows;
- wrong WP36 CSV schema;
- wrong D02 group for corrected stem `1319`.

The exact current authorities reproduce 3,215 governed rows, counts `1912/376/903/24` plus raw
stem `0248` displayed separately as quarantined, test stem hash `afa03d4b...`, and exactly 39
validation-only corrected stems `1319..1357` in `D02-C0034`. The application imports
`dataset01_view_r1`, so the authenticated wrapper is on the live view path.

## Materialised candidate and sealed boundary

- `verify-export` returned `valid=true` for
  `data/processed/m1_yolo_wp38_r1_integration_r1/`.
- Train: 3,712 image symlinks and 3,712 regular labels = 1,912 unchanged real images plus 1,800
  WP35 pairs.
- Validation: 376 image symlinks and 376 regular labels.
- Validation PNG roster is exactly the 39 corrected stems `1319..1357`; every corrected link
  resolves to its governed WP38-R1 derivative.
- All 1,912 real train-image links resolve to the original governed raw image path; no corrected
  stem overlaps train or test.
- `images/test` and `labels/test` are absent.
- R1 exposes no `export-test` or `--final-eval` command.
- Exact sealed-test access log remained absent before and after QA.

## Mechanical evidence

| Check | Result |
| --- | --- |
| Exact requested R1 source hashes | PASS, 5/5 |
| R1 integration verifier | PASS, `valid=true` |
| R1 + graph targeted tests | PASS, **15/15** |
| Materialised export verifier | PASS, `valid=true` |
| Exact corrected/train/test roster replay | PASS |
| Non-racing linked parent/root/images/labels/split/leaf attacks | PASS, all rejected before victim mutation |
| Existing regular/hardlinked output attacks | PASS, rejected and unchanged |
| Coherent forged graph-authority attacks | PASS, **8/8 rejected** |
| Staging replacement race | **FAIL — write path escaped; cleanup left replacement symlink** |
| Repository verifier matrix | PASS, **56/56** |
| Ruff, full `src tests` scope | PASS |
| Root `uv lock --check` | PASS, 168 packages |
| `git diff --check` | PASS |
| Graft | **STALE — L-1** |
| Sealed-test access log | ABSENT before and after QA |

## Reviewed hashes

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_yolo_dataset_wp38_r1_integration_r1.py` | `29839def04afa2ba8915195a8362f3e65fcde1fc22700bac242dc804e7461fa1` |
| `docs/review/generated/m1_yolo_wp38_r1_integration_r1_manifest.json` | `6fbc33e8cd168a203d798e8abfee077f8f34450e8e9b66c03f9812d675e75675` |
| `src/cpv301_autodrive/dataset01_view_r1.py` | `6763c8d7fd22004773bbac84067f39d0b85c88df5c049759de9250bf433431dc` |
| `tests/test_m1_wp38_r1_integration_r1.py` | `187ed5d34f83e75c86d74502dbda0e6a46f480f64735eaff64c98667672dea71` |
| `tests/test_dataset01_view_r1.py` | `b8f32ae5bf6dce31c37af64ce4552bc32d0022106022a793757da1020964bff4` |
| `docs/review/m1_wp38_r1_integration_r1_qa_remediation_report.md` | `c567bcdcc6a0e2a556b58a19cefbd922aff32253debc8f70abe927c9349f290e` |
| Initial integration independent QA FAIL record | `3f676588350e089c72457b3159ddb434122642671258c7d0f46dbc605feae338` |

## Governance disposition

| Gate | QA disposition |
| --- | --- |
| Exact 39-stem validation substitution | **PASS** |
| Train/WP36 membership preservation | **PASS** |
| Sealed-test hash and closed boundary | **PASS** |
| Materialised train/val-only export | **PASS** |
| Dataset Graph authority M-1 | **PASS / closed** |
| Ordinary linked-output H-1 cases | **PASS** |
| Concurrent writable-path replacement | **FAIL — H-1-R1** |
| Graft handoff freshness | **FAIL — L-1** |
| R1 integration acceptance | **FAIL / NO-GO** |
| Official archive/Drive upload | **NO-GO** |
| Corrected-validation evaluation | **NO-GO pending successor + fresh QA** |
| New 100-epoch training | **NO-GO** |
| Sealed-test access | **NO-GO / not accessed** |

Final disposition: preserve the predecessor and R1 bytes plus both independent FAIL records. Build
an append-only successor that binds writable directory identity across check/use and cleanup, then
route it to fresh independent QA. Only a QA PASS permits clean-commit archive work and a separate
Owner-authorized corrected-validation evaluation; it still would not authorize a new 100-epoch
run or sealed-test access.
