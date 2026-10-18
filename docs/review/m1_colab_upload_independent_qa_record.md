# M1 Colab private-upload independent QA record

Status: `QA_PASS_M1_COLAB_PRIVATE_UPLOAD_CHECKPOINT`
Reviewer: `Codex independent QA session (did not perform the upload and did not author the upload record)`
Reviewed at: `2026-10-19T00:51:32+07:00`
Boundary: `LOCAL_ARTIFACT_COMMIT_AND_RECORD_QA_ONLY_NO_COLAB_NO_UPLOAD_NO_DOWNLOAD_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_COMMIT_NO_PUSH`

## Checkpoint correction and verdict

- The delegated prompt initially named prefix `5f265e4b`. PM corrected that typo during QA.
- The exact checkpoint reviewed is
  `5f265e434236f23a792c18638a0fdd2a921eaed5` (`Record verified private M1 Colab upload`).
- Local `HEAD`, the local `origin/DEV/Rroject_Pineline` tracking ref and a read-only
  `git ls-remote` query of the remote branch all returned that exact full SHA.
- **Verdict: PASS — 0 Critical, 0 High, 0 Medium, 0 Low.** The upload record is internally
  consistent with the preserved local archive and sidecar, and the commit-bound verifier behaves
  fail-closed.
- This verdict verifies local cryptographic bytes, Git state and the accuracy/boundaries of the
  committed record. It does not independently re-observe the Google Drive UI or assert that the
  remote Drive copy was downloaded and hashed.

## Reviewed inputs

| Item | Readback |
| --- | --- |
| Upload record | `docs/review/m1_colab_private_upload_record.md`, SHA-256 `3fda6ac5f9d775668e21decf22619faa6d5fdb94f6eabbf9bca436f17de568f7` |
| Bound source commit | `1842a1b77e6448a54fec486937f4c0f0e6ff19f5` |
| Archive | `tmp/m1_colab_train_val.tar.gz`, 766,226,824 bytes, SHA-256 `eb5226e36cf619e271132794c97fd633f7528d72e25463356eb165f36f43e191` |
| Sidecar | `tmp/m1_colab_train_val.tar.gz.manifest.json`, 1,499,866 bytes, SHA-256 `2c43d5fdff3de32af3fa3b9621f7f73cf1646c2f51801c5844ae89e8f4ae8d3b` |
| Bundle builder | `scripts/build_m1_colab_bundle.py`, SHA-256 `ac0c4a9a7d15522bb4254221f252fefb640395683b4ee7b7698b61f606d47536` |
| Colab regression tests | `tests/test_m1_colab.py`, SHA-256 `7dac63809b5fb673c032bed2a94894380d011ab2337949598acace703e3dff30` |

The displayed Drive sizes in the record are arithmetically consistent with the local files:
766,226,824 bytes is 730.7 MiB and 1,499,866 bytes is 1.4 MiB after one-decimal rounding.

## Archive and manifest readback

- The embedded `m1_colab_bundle_manifest.json` is byte-for-byte identical to the local sidecar;
  both hash to `2c43d5fdff3de32af3fa3b9621f7f73cf1646c2f51801c5844ae89e8f4ae8d3b`.
- Manifest status is `TRAIN_VAL_ONLY_READY`; `allowed_splits` is exactly `["train", "val"]`;
  `test_included=false`; `regular_files_only=true`.
- The manifest contains exactly 5,888 unique payload records. The tar contains exactly 5,889
  unique members: those 5,888 payload paths plus the embedded manifest. Both rosters agree exactly
  and every tar member is a regular file.
- Payload source-split counts are 5,512 train and 376 validation records. Kind counts are 2,288
  raw images, 1,800 WP35 train images and 1,800 WP35 train labels.
- Declared component counts sum exactly to 5,888: 1,912 raw train images, 376 raw validation
  images, 1,800 WP35 train images and 1,800 WP35 train labels.
- No manifest payload path contains a `test` path component. The only sealed-test datum is the
  committed stem-list hash
  `afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc`.
- Train and validation stem-list hashes match the record exactly:
  `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372` and
  `ae3f3509319fbb301012e9fbeb7431caacfcd4035c9d2f9167f24e3ed2b8f593`.

## Commit-bound fail-closed verification

- Running the real bundle verifier against current checkpoint `5f265e434236...` returned exit 1
  with `bundle manifest binding differs: repo_git_commit`. No archive or manifest byte was changed.
- A temporary detached worktree at exact commit
  `1842a1b77e6448a54fec486937f4c0f0e6ff19f5` was clean and used the real verifier against the
  preserved archive. It returned `status=VERIFIED`, archive hash `eb5226e...e191`, file count
  5,888, the exact train/validation stem hashes and `test_included=false`.
- The detached worktree was removed after verification. The main worktree remained clean before
  this append-only QA record was added.

## Privacy, repository and execution boundaries

- Commit `5f265e434236...` changes only `PROJECT_MEMORY.md`, `docs/product_roadmap.md` and the upload
  record. The archive and sidecar are ignored by `tmp/`, are not tracked and do not appear in the
  checkpoint tree.
- The added/modified file content contains no email address, Google Drive URL, Drive folder ID,
  API/client key or secret, bearer token or password assignment. It records only the human-readable
  private path `My Drive/CPV391/M1_D1_Colab`.
- Standard Git author/committer metadata contains the same email identity already present in
  earlier repository commits. This QA treats that pre-existing VCS identity separately from the
  changed file-content leakage check; no email was newly added to the checkpoint's file content.
- The committed record distinguishes external UI readback from local cryptographic evidence. It
  does not claim the Drive copy itself was downloaded or cryptographically re-verified.
- The bound notebook is unexecuted, has `SMOKE=True`, sets one epoch for smoke, uses the expected
  Drive path and contains no `export-test` or `--final-eval` route.
- The checkpoint tree contains no D1 `best.pt`, `last.pt`, result archive or experiment output.
  The only tracked experiment entry found is the pre-existing E0 baseline manifest.
- The record correctly states that no Colab runtime was connected, no GPU/CUDA identity was
  observed, no training/checkpoint/metric/latency/result archive exists and the sealed test was not
  exported, uploaded, opened or evaluated.

## Proportional validation

| Gate | Result |
| --- | --- |
| `tests/test_m1_colab.py` | PASS, 22/22 |
| Targeted Ruff | PASS |
| Root `uv lock --check` | PASS, 168 packages resolved |
| `git diff --check` before QA record | PASS |
| Graft freshness | PASS, synchronized wiring graph at 2,303 nodes / 5,843 edges |

Graft map and task-specific ask were used before source inspection and reported approximately
717,929 saved source tokens, worth about USD 0.42 at the session rate. Graft tier 0 was used only
for navigation; artifact bytes and executable verifier results establish this verdict.

No Colab cell was run. No dataset or artifact was uploaded or downloaded by independent QA. No
sealed-test image, label or result was opened or exported. No commit or push was performed.
