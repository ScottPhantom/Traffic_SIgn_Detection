# D1 Colab backend R1 successor bundle independent QA record

Status: `QA_PASS_D1_COLAB_BACKEND_R1_SUCCESSOR_DELIVERY`

Reviewer: `Codex independent QA session (did not author the successor notebook, bundle or guide changes)`

Reviewed at: `2026-10-20T10:46:36+07:00`

Boundary: `LOCAL_SUCCESSOR_DELIVERY_QA_ONLY_NO_UPLOAD_NO_COLAB_RUN_NO_TRAINING_NO_COMMIT_NO_PUSH_NO_SEALED_TEST_ACCESS`

Reviewed checkpoint: `ffc2b448f06c45dae597de5b565cab64c0377573` plus the current uncommitted successor-delivery worktree and ignored local bundle artifacts

## Verdict

- **PASS — 0 Critical, 0 High, 0 Medium, 0 Low.**
- The exact local successor archive and sidecar match the declared sizes and SHA-256 values and
  pass the official bundle verifier.
- The embedded repository commit is the QA-approved backend R1 commit
  `ffc2b448f06c45dae597de5b565cab64c0377573`; its primary runner bytes retain the reviewed
  `MPLBACKEND=Agg` remediation.
- The package contains exactly 5,888 governed train/validation payload files plus one manifest,
  with no test member, unsafe member path, non-regular member or duplicate member.
- The successor notebook is unexecuted, hashes both exact mounted files before reading the archive
  manifest, uses the fresh `smoke_seed_20261018_backend_r1` state label and contains no sealed-test
  export/final-evaluation command.
- This PASS approves only the local delivery bytes and operator controls. It is not evidence of an
  upload, Colab smoke, epoch, checkpoint, result package, metric or accepted model.

## Exact local artifacts

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tmp/m1_colab_train_val_backend_r1.tar.gz` | `766226800` | `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641` |
| `tmp/m1_colab_train_val_backend_r1.tar.gz.manifest.json` | `1499866` | `7e0dc5b0144faa5f0be407224eaf8070dd51199fa8a1d2f164b248fd6a06d5b2` |

The sidecar bytes are identical to the embedded `m1_colab_bundle_manifest.json`. Official verifier
readback returned:

- `status=VERIFIED`;
- `repo_git_commit=ffc2b448f06c45dae597de5b565cab64c0377573`;
- `file_count=5888` and `test_included=false`;
- 1,912 raw train images, 376 raw validation images, 1,800 WP35 train images and 1,800 WP35 train
  labels;
- train stem-list SHA-256
  `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372`;
- validation stem-list SHA-256
  `ae3f3509319fbb301012e9fbeb7431caacfcd4035c9d2f9167f24e3ed2b8f593`.

An independent tar roster audit found 5,889 total members: one embedded manifest plus 5,888 payload
files. All members are regular files; there are zero duplicate names, zero absolute/parent-traversal
paths and zero `/test/` paths.

## Notebook and operator audit

- All six code cells have `execution_count=null` and empty outputs.
- The first code cell mounts Drive. The immediately following configuration/preflight cell verifies
  both mounted file sizes and SHA-256 values. Only the next cell calls `tarfile.open(BUNDLE)` and
  reads the embedded manifest.
- The embedded manifest must declare `test_included=false` and `allowed_splits=['train', 'val']`;
  the notebook then clones and checks out the exact embedded commit and verifies `HEAD` equality.
- The operational archive/sidecar names, sizes, hashes, full commit and new run label agree across
  the notebook, guide and successor record.
- The guide explicitly marks failed run `smoke_seed_20261018` as immutable evidence that must not be
  reused. It contains only the successor configuration assignment
  `RUN_LABEL = 'smoke_seed_20261018_backend_r1'` and no old checkout instruction.
- The runner rejects a non-empty state directory. The bundle builder refuses any pre-existing
  archive, sidecar or partial output; the targeted suite re-verifies its no-overwrite behavior.
- The local bundle lives under ignored `tmp/`; no dataset payload is introduced into the tracked
  worktree.

During the first review snapshot, the guide still contained the failed run label as an operational
assignment and the retired `1842a1b…` checkout instruction. These two Medium operational findings
were corrected before final verdict. A regression test now requires the successor bundle, full
commit and new label while rejecting both stale label assignments and the retired checkout text.
The final corrected snapshot was re-read and all affected gates were rerun.

## Reviewed tracked-file pins

| Item | SHA-256 |
| --- | --- |
| Successor notebook | `2e96fc82de959cab2fba59fe70dd1ba77a4b67bb3d07a4b7aca309236dfb4ade` |
| Primary Colab tests | `8ae76c8c235a585eb6d8e3e9dc6659d72eb4984a50e4be46125bed7016c7f4f0` |
| Operator guide | `07528fcc9e5b0bfdc85d2f8e44b796c4eacd22daa808ec19432b99c32cb1a879` |
| Successor bundle record | `065fea12d679f7c2460055e5e3817b44dc3f141394cd1bcde4222e52dd6f2f2d` |

## Validation

| Gate | Result |
| --- | --- |
| Official `build_m1_colab_bundle.py verify` | PASS, `VERIFIED`, 5,888 payload files, `test_included=false` |
| Independent archive/sidecar byte readback | PASS, exact sizes and SHA-256 values |
| Independent tar roster/type/path audit | PASS, 5,889 members, all regular, zero duplicate/unsafe/test paths |
| `tests/test_m1_colab.py` | PASS, **24/24** |
| Root Ruff (`src tests scripts main.py`) | PASS |
| Root dependency lock | PASS, **168 packages** resolved |
| Notebook JSON parse/readback | PASS, six unexecuted code cells and zero outputs |
| `git diff --check` | PASS |
| Graft rebuild/check | PASS, graph synchronized at **2,522 nodes / 6,380 edges** |
| Exact `results/experiments/sealed_test_access_log.jsonl` | ABSENT |

No Drive object was created or overwritten, no Colab cell was run, no model was trained, no test
split or sealed-test artifact was opened, and no commit or push was performed by this QA session.
