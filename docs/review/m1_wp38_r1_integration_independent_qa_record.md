# M1-WP38-R1 downstream integration independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `INDEPENDENT_QA_FAIL`

Reviewer: `Codex independent QA session (read-only source/artifact review)`

Reviewed checkout: committed base `85a8025e1ae1e78d4c84adb2cd6009003e8c93a1` plus the exact
uncommitted M1-WP38-R1 integration bytes pinned below and unrelated user/PM worktree changes.

Boundary: `READ_ONLY_NO_SOURCE_FIX_NO_TRAINING_NO_EVALUATION_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL / NO-GO — 0 Critical, 1 High, 1 Medium and 0 Low findings.**

The current bytes correctly preserve the WP36-R1 stem membership, substitute exactly validation
stems `1319..1357`, define the expected 5,927-file train/val-only Colab roster and keep the sealed
test closed. However, the exporter does not fail closed on linked writable descendants, and the
Dataset Graph wrapper does not authenticate the split/correction authorities that it presents as
accepted evidence. Both gaps are independently reproducible and are absent from the current PM
tests.

This verdict does not authorize an official archive, Drive upload, corrected-val evaluation,
another training run, a commit/push or sealed-test access. The current package must be preserved
and superseded append-only after remediation.

## Findings

### H-1 — Export output descendants can escape through symlinks and overwrite external files

Severity: **High**

Affected source: `scripts/build_m1_yolo_dataset_wp38_r1.py`, principally `materialise()` and
`_link()`.

`main()` resolves only the requested output root. `materialise()` then calls `mkdir(...,
exist_ok=True)` on `out/images/<split>` and `out/labels/<split>` without lexically walking and
`lstat()`-checking every writable descendant. `_link()` follows a linked parent and unlinks an
existing destination before creating a symlink; label `write_text()` likewise follows a linked
parent. Therefore a pre-existing `out/images` or split-directory symlink can redirect writes and
deletions outside the requested output tree.

The independent non-destructive attack created a temporary `out/images -> victim` symlink,
replaced `_link()` with a stop-before-write guard, and invoked the real `materialise()` flow. The
first train destination was lexically
`.../out/images/train/0072.jpg`, while its resolved parent was
`.../victim/train`; `escaped=True`. The production `_link()` would unlink any existing file at
that redirected destination. No repository or external victim byte was changed during QA.

Required remediation:

1. Introduce an append-only successor exporter.
2. Validate the output root and every existing/non-existing ancestor component lexically with
   `lstat()` before any `mkdir`, `unlink`, symlink creation or label write.
3. Reject symlinks, non-directories and linked writable files; require regular single-link output
   files where applicable.
4. Add attacks for linked root, `images`, `labels`, split directory and final destination, and
   prove rejection occurs before any output or victim mutation.
5. Prefer a clean temporary tree plus atomic promotion so a failed materialisation cannot leave a
   partially trusted export.

### M-1 — Dataset Graph accepts forged authorities while still claiming WP36-R1/WP38-R1 authority

Severity: **Medium**

Affected source: `src/cpv301_autodrive/dataset01_view.py` and its graph/status presentation.

`graph_payload()` reads `wp36_r1_split_frames.csv` and the WP38-R1 manifest directly, but does not
pin their hashes, verify their governing packages, validate exact schemas/rosters or assert that
the correction is exactly 39 validation-only stems in `D02-C0034`. Nevertheless it hard-codes
`splitAuthority="WP36-R1"`, `correctionAuthority="WP38-R1 QA PASS"` and
`orientationGroup="D02-C0034"`.

Two independent temporary-path attacks reproduced the issue without changing repository files:

- replacing the correction roster with only stem `0001` was accepted; the graph reported
  `orientationCorrected=1`, marked `0001` as corrected even though its actual group is
  `D02-C0001`, and still claimed `WP38-R1 QA PASS` plus `D02-C0034`;
- moving train stem `0072` to validation in a temporary split CSV was accepted and rendered as
  `WP36-R1`, changing the visible counts to `1911/377/903/25` and mixed groups to `1`.

The current real inputs happen to produce the correct values, but the view is not fail-closed
evidence. A modified uncommitted/generated authority can therefore be silently promoted into a
false governance claim.

Required remediation:

1. Introduce a small authenticated graph input contract or call the QA-passed package verifiers.
2. Pin and verify the exact WP36-R1 and WP38-R1 authority hashes before constructing the payload.
3. Validate exact schemas, unique/exhaustive stem rosters, split counts `1912/376/903/25`, the
   sealed-test stem hash, exact corrected stems `1319..1357`, group `D02-C0034`, validation-only
   membership and `sealed_test_accessed=false`.
4. Add forged-manifest, forged-split, duplicate/missing/extra row and wrong-group/split attacks.
5. On any mismatch, refuse to render an authority badge rather than falling back to unverified
   content.

## Independently confirmed invariants

- Successor and base stem lists are byte-semantically equal for train, val and test.
- Train labels are unchanged; test labels are unchanged.
- Validation label text changes only for the 29 labeled stems `1329..1357`; stems `1319..1328`
  remain governed empty labels while their images change to corrected PNG derivatives.
- Corrected roster is exactly 39 stems `1319..1357`, all in validation, with zero train/test
  overlap.
- Generated integration manifest reports train/val/test frame counts `1912/376/903` and test stem
  SHA-256 `afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc`.
- Colab bundle manifest construction re-hashed every current source and produced exactly 5,927
  files: 1,912 raw train images, 337 raw val images, 39 WP38-R1 images, 39 WP38-R1 labels,
  1,800 WP35 train images and 1,800 WP35 train labels. Its roster contains only `train` and `val`,
  `test_included=false` and `sealed_test_accessed=false`.
- The bundle builder rejects the current dirty checkout before archive creation.
- Dataset Graph current-input readback is `1912/376/903/25`, 54 groups, 0 mixed active groups and
  39 corrected markers in `D02-C0034`.
- Pinned `dataset_graph.py`, base M1 exporter/bundle builder, WP36-R1 split, README, root lock and
  root project file have no Git diff. The Dataset Graph core SHA-256 remains
  `339972e5bbd6789b7702c0726ac7644f01efb86b514261eb48927289f149f00d`.
- Repository verifier matrix passed 55/55, including `m1-wp38-r1`, `wp38-r1`, `wp36-r1` and the
  historical package verifiers.
- The exact sealed-test access log was absent before and after QA. No test image, label or model
  metric was opened.

## Mechanical evidence

| Check | Result |
| --- | --- |
| Official M1-WP38-R1 integration verifier | PASS, `valid=true` |
| Integration targeted tests | PASS, **6/6** |
| Dataset Graph targeted tests | PASS, **9/9** |
| Independent stem/label delta replay | PASS |
| Independent 5,927-file source-hash replay | PASS |
| Dirty-checkout archive rejection | PASS |
| Writable-descendant symlink attack | **ACCEPTED / FAIL** |
| Forged WP38 graph-authority attack | **ACCEPTED / FAIL** |
| Forged WP36 graph-authority attack | **ACCEPTED / FAIL** |
| Repository verifier matrix | PASS, **55/55** |
| Ruff, full `src tests` scope | PASS |
| Root `uv lock --check` | PASS, 168 packages |
| `git diff --check` | PASS |
| Graft | PASS, wiring graph synchronized |
| Sealed-test access log | ABSENT before and after QA |

## Reviewed hashes

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_yolo_dataset_wp38_r1.py` | `62bf884669f2e6670935267d4687472a5ca60e85741299a2b0d35626798933fb` |
| `scripts/build_m1_colab_bundle_wp38_r1.py` | `8502aaa11397ec4d5f82c09d59716b59cd39451086e3c30eaee238f752d7e0d9` |
| `docs/review/generated/m1_yolo_wp38_r1_integration_manifest.json` | `87a47ae3ae3118b7109acf03bafb12429c447dd104811fea2642beb5555533e0` |
| `src/cpv301_autodrive/dataset01_view.py` | `5224adfba0a5eab5e2137dd58dc489f7e4a323d70d9188686b8f59137a6a62ef` |
| `src/cpv301_autodrive/assets/dataset01_graph.html` | `636feefad0d85a8f09b6aa2adabab4ad0ee27846119b3ab8eefb57ffcebeafb3` |
| `src/cpv301_autodrive/project_status.py` | `3cebdcf590a44c6c2967a0b4b0c17c3827368997e731db9b39df402735663397` |
| `src/cpv301_autodrive/views.py` | `16a0fdd60eee47f4a888b1d3da592ed8e7294c5b24db7fcf585d6b9ec743f361` |
| `tests/test_m1_wp38_r1_integration.py` | `f5bc7f852ce20741cb8ab1ddb4a0d588111a40b55377cb3eedb7169c99cd5450` |
| `tests/test_dataset01_view.py` | `706ba565aba0b6326c934d351c7eb190d66e04fdf7339d507192cbe06702f347` |
| `docs/product_roadmap.md` | `68c2c202dafe20119ef2b82d338ca6cc223f4551f1805a56af703f09ecca8476` |
| `PROJECT_MEMORY.md` | `4eb7f058bf77d453a4de10e2c797c9088be205ffe78ae0224a592c3fd4d37e6d` |

## Governance disposition

| Gate | QA disposition |
| --- | --- |
| Exact 39-stem validation substitution in current bytes | **PASS** |
| Train/WP36 membership preservation | **PASS** |
| Sealed-test hash and closed boundary | **PASS** |
| 5,927-file train/val-only roster | **PASS** |
| Writable output safety | **FAIL — H-1** |
| Graph evidence authority | **FAIL — M-1** |
| M1-WP38-R1 integration acceptance | **FAIL / NO-GO** |
| Official archive and Drive upload | **NO-GO** |
| Corrected-val evaluation | **NO-GO pending append-only repair + QA** |
| New 100-epoch training | **NO-GO** |
| Sealed-test access | **NO-GO / not accessed** |

Final disposition: preserve this initial integration and its PM implementation record unchanged.
Create an append-only remediation successor that closes H-1 and M-1, then route that successor to
fresh independent QA. Only after QA PASS may the project build a clean-commit archive, request
upload authorization and evaluate the existing pilot on corrected validation.
