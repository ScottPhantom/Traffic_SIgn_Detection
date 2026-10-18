# D1 cascade detector dataset R2 independent QA record

Status: `QA_PASS_D1_CASCADE_DATASET_R2_R1_FINDING_CLOSED`
Reviewer: `Codex independent QA session (did not author the R2 remediation and did not act as PM)`
Reviewed at: `2026-10-19T01:14:47+07:00`
Boundary: `QA_OF_D1_CASCADE_DATASET_R2_ONLY_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH`
Reviewed checkpoint: `a3efc3ad334f576ed750c6ca26df02fb5aa34878` plus the current uncommitted D1-R2 worktree

This append-only record independently reviews the successor package described by
`docs/review/d1_cascade_dataset_r2_qa_remediation_report.md`. It preserves the R1 FAIL verdict and
its evidence. The review changed no implementation, test, model, dataset, manifest or Owner
decision. Apart from this record, it updates only the durable D1 status in `PROJECT_MEMORY.md` and
`docs/product_roadmap.md`.

## Verdict

- **D1 cascade detector dataset R2: PASS.** 0 Critical, 0 High, 0 Medium, 0 Low.
- The R1 High output-symlink finding is closed. The real `export` and `verify-export` CLI paths
  preserve the lexical output path, reject an existing symlink component and leave the external
  target empty. Regression coverage also exercises output-root, parent and nested-directory
  symlinks.
- The materialized package contains only `train` and `val`, with one class (`0: traffic_sign`). It
  has 3,712 train frames / 12,621 train boxes and 376 validation frames / 560 validation boxes.
  No nonzero class token and no `test` path was found.
- WP35 is train-only: 1,800 WP35 image symlinks and 1,800 labels occur under `train`; zero occur
  under `val`.
- The QA-pinned M1 builder, export manifest and class map are unchanged from `HEAD`. The D1
  successor does not modify the M1 builder or M1 materialized output.
- The cascade gate addendum remains `PROPOSAL_NOT_OWNER_APPROVED`. R2 exposes no D1 test-export
  command and does not make the cascade eligible for sealed-test use.
- This PASS approves the reviewed one-class train/validation dataset package only. It does not
  approve a cascade classifier, metric gates, threshold policy, Colab runner, pilot, model
  training, sealed-test access, upload, download, commit, push, deployment or publication.

## Reviewed byte pins

| Item | SHA-256 |
| --- | --- |
| R2 remediation report | `1c67b15e79fa6603e0f1e6a58aa2d6cf4e7aacd8bfba0d7131e8295c3aac7c88` |
| D1-R2 builder | `d2b80eb4906570e6636d3e0651a612368181e66a007c8e424d7a8df3d560cb39` |
| D1-R2 tests | `8770afc81a30a61c7bf240e32cf21fdb74b1b480dd8564f9a5d35d582aa7feef` |
| D1 cascade manifest | `d6ca36a4c21cbadb922df897625ce80dc9d6fa3d5770b3c6cb84ddff78e10fd2` |
| Cascade gate addendum proposal | `56d100532278fc5a13d552c3a067821508d5b40f9a04704092ff88c8b371f403` |
| Dual-baseline Owner decision | `39f26b0e29a2a60a5972ea07e6e0dcf04ce5e53f722a3c92b3a69b267934a0b2` |
| QA-pinned M1 builder | `3b52c63f2aeeea9e93f779ebe4102715def96a1f176e809cfd0dc12fbe9cef93` |
| M1 export manifest | `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71` |
| M1 class map | `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242` |

## Independent code and boundary review

### R1 symlink remediation

- `absolute_lexical()` makes the output path absolute without resolving symlink components.
- `reject_symlink_components()` walks every existing component with `os.lstat()` and rejects a
  symlink before output I/O.
- `main()` preserves the lexical `--out` path for both `export` and `verify-export`; only the
  read-only source paths are resolved.
- Output-root, `images`, `labels`, split directories and file parents are checked. Expected image
  symlinks remain separately constrained to their exact source target and SHA-256.
- A real CLI rerun of the original output-root exploit returned code 1 for both `export` and
  `verify-export`, named the lexical linked root in the error and left the external target with
  zero entries.
- `test_real_cli_rejects_root_parent_and_nested_symlinks_before_writing` repeats root, parent and
  nested-directory attacks through a subprocess and asserts that all external targets stay empty.

### Split, class and source boundaries

- `ALLOWED_SPLITS` is the fixed tuple `("train", "val")`; the CLI choices are exactly
  `manifest`, `verify`, `export` and `verify-export`.
- `expected_records()` iterates only the allowed train/validation split labels. WP35 records are
  inserted only into `result["train"]`.
- `collapse_label_text()` validates the five-token YOLO row, source class range, finite normalized
  coordinates and preserves the four coordinate tokens byte-for-byte while replacing only the
  class token with `0`.
- The verifier requires the exact output-root roster, exact train/validation split rosters, exact
  image/label rosters, exact image source target/hash, exact collapsed label bytes and exact
  one-class YAML. Extra or tampered files fail closed.
- The committed manifest binds the M1 manifest, M1 class map, Owner dual-baseline decision and the
  governed train/validation/test-seal hashes. The test-seal hash is governance metadata; no D1
  route materializes a test image or label.
- The materialized output independently read back as 4,088 image symlinks, 4,088 regular label
  files and one `data.yaml`; the only split directories are `train` and `val`.
- `results/experiments/sealed_test_access_log.jsonl` remained absent before and after QA.

## Executable gate matrix

| Gate | Result | Readback |
| --- | --- | --- |
| D1-R2 targeted tests | PASS | **12/12** |
| R1 exploit regression | PASS | Real CLI `export=1`, `verify-export=1`, external entries `0` |
| D1 manifest verifier | PASS | `valid=true`, `errors=[]` |
| D1 materialized-export verifier | PASS | `valid=true`, `errors=[]` |
| Materialized output readback | PASS | train/val only; one class; 3,712/376 frames; 12,621/560 boxes |
| Full package verifier matrix | PASS | **52/52** in 134.4 seconds wall time |
| Root Ruff | PASS | `All checks passed!` for `src`, `tests` and changed scripts |
| Root lock | PASS | 168 packages resolved; lock unchanged |
| Detector Ruff | PASS | `All checks passed!` |
| Entire detector suite | PASS | **54/54** |
| Detector lock | PASS | 66 packages resolved; lock unchanged |
| Git whitespace check | PASS | `git diff --check` produced no error |
| Graft freshness | PASS | Wiring graph in sync at 2,334 nodes; deep meaning layer not built |

All `uv` validation ran offline with `--no-sync`; no dependency download occurred. The delegated
gate requested the 12 targeted root tests rather than the full historical root pytest suite, so
the latter was not run. Graft check/ask/skeleton queries were used before source inspection and
reported approximately 76,284 source tokens saved (about USD 0.04 at the session rate). Graft was
used as navigation and blast-radius evidence, not as semantic proof.

## Final boundary

- No implementation or test was edited by independent QA.
- No model was trained, evaluated or benchmarked. No classifier or D1 runner was created.
- No sealed-test image, export, metric or access log was produced.
- No upload, download, commit, push, deployment or publication occurred.
- R1 remains an immutable QA FAIL record; this R2 record is its independent successor PASS.
