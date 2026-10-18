# D1 cascade Colab R2 independent QA record

Status: `QA_PASS_D1_CASCADE_COLAB_R2_R1_FINDINGS_CLOSED`
Reviewer: `Codex independent QA session (did not author the R2 remediation and did not act as PM)`
Reviewed at: `2026-10-19T01:39:39+07:00`
Boundary: `QA_OF_D1_CASCADE_COLAB_R2_ONLY_SYNTHETIC_NO_COLAB_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH`
Reviewed checkpoint: `150777a49d010096fbe246a61a9589f2a27b9e00` plus the current uncommitted R2 worktree

This append-only record independently reviews only the D1 cascade Colab R2 successor described by
`docs/review/d1_cascade_colab_r2_qa_remediation_report.md`. It preserves the R1 implementation and
FAIL record. Independent QA changed no implementation, test, notebook, model, dataset, manifest or
Owner decision. Apart from this record, it updates only the durable R2 status in
`PROJECT_MEMORY.md` and `docs/product_roadmap.md`.

## Verdict

- **D1 cascade Colab R2: PASS.** 0 Critical, 0 High, 0 Medium, 0 Low.
- R2 closes all three R1 High findings. Standalone verification safely extracts an exact result
  roster, reconstructs and semantically validates the governed run and execution contracts,
  re-hashes both checkpoints, and validates the SQLite/text/results lifecycle before trusting the
  derived attestation. Re-hashed forged contract, checkpoint, lifecycle and SQLite packages fail.
- Result creation rejects final, sidecar, partial and parent-path redirects before output I/O.
  Independent QA repeated the archive-partial symlink attack and verified that the external victim
  remained byte-for-byte unchanged and no final archive appeared.
- The governed data contract is exactly one class (`0: traffic_sign`), only `train` and `val`, with
  the pinned train and validation stem hashes, canonical `data.yaml`, approved bundle hash and
  historical source commit. The parser and notebook expose no test export, evaluation,
  threshold-selection or final-evaluation route.
- The notebook remains unexecuted, requests an L4 GPU, defaults to the one-epoch smoke and is clean
  under complete detector Ruff. No Colab cell ran and no real CUDA runtime was observed by QA.
- This PASS approves only the reviewed R2 controls for the one-class detector Colab path. It does
  not approve the cascade gate addendum or classifier, produce a trained model or result, open the
  sealed test, or authorize upload, download, commit, push, deployment or publication.

## Reviewed byte pins

| Item | SHA-256 |
| --- | --- |
| R1 implementation record | `a467b737c0d2e24c49ceb1d2561d105dada7fc19b8adba0f0f1cd87a2ae3b516` |
| R1 independent QA FAIL record | `c6ec7b19c2d2cbb2b6ff13a9676d8f0560c58f8dee01c3332a4cd276cf658782` |
| R2 remediation report | `ecbad52a5709f4fec41b0ceef5b7e48817e343b4b5affcd7686cdfaf75344c7c` |
| R2 runner | `12b419f6957464cf5cb665805af42e181fc4ab3bd011c9d0bacce512fc4f8924` |
| R2 notebook | `f804c847ab672c936d3022e7813005a3453bb7ca957c6237703bc31dcbe87ea6` |
| R2 tests | `29c098af352092bee0787449441bc1119459ed3ccda1de24109869e7ce82c211` |
| Cascade dataset R2 independent QA record | `ab44989e28357acd84d5e9c8c92431bb8b7c2f48b52a1d0904476f6d4e5cba5a` |
| D1 cascade dataset manifest | `d6ca36a4c21cbadb922df897625ce80dc9d6fa3d5770b3c6cb84ddff78e10fd2` |
| D1 cascade dataset builder | `d2b80eb4906570e6636d3e0651a612368181e66a007c8e424d7a8df3d560cb39` |
| Shared M1 bundle builder | `ac0c4a9a7d15522bb4254221f252fefb640395683b4ee7b7698b61f606d47536` |
| Pinned M1 logging runner | `0d04c869d0181c68a4d60a93b05967c4db5b5e31cfc44cf653bfcbd43f225786` |
| Detector lock | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |
| Owner-approved `yolo11s.pt` | `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5` |
| Dual-baseline Owner decision | `39f26b0e29a2a60a5972ea07e6e0dcf04ce5e53f722a3c92b3a69b267934a0b2` |
| Private-upload record | `3fda6ac5f9d775668e21decf22619faa6d5fdb94f6eabbf9bca436f17de568f7` |
| Private-upload independent QA record | `0008bcdd58ce60bf08c0c93c3ea678fbd8587385c26e0dedb103d0a2a1480cfc` |

## Independent acceptance review

### Standalone result semantics and exact roster

- A fresh synthetic successful run packaged and independently replayed with terminal outcome
  `SUCCEEDED`, `sealed_test_accessed=false` and exactly these eight regular members:
  `best.pt`, `last.pt`, `results.csv`, `args.yaml`, `run_contract.json`,
  `colab_execution.json`, `colab_train.log` and `DB_logger.db` under their canonical run/log paths.
- The verifier requires the exact sidecar schema and roster, safe relative member names, regular
  tar members, positive sizes and SHA-256 values. It manually writes each member with exclusive
  creation inside a fresh private temporary directory rather than calling a permissive tar
  extraction API.
- After extraction it parses strict JSON, validates the full run contract against current governed
  data/model/environment values, validates the token-exact command and lifecycle, re-hashes both
  weights against the archived contract, and calls the source-pinned M1 SQLite/text/results
  validator. Only then is the attestation reconstructed and compared with the sidecar.
- QA independently changed the archived one-class map to `999: forged`, changed `best.pt`, and
  recomputed every affected archive and sidecar hash. Both packages were rejected because their
  semantics contradicted governed evidence. The authored regressions also rejected invalid JSON,
  fake SQLite, shortened lifecycle, forged command prefix, unsafe member names and every original
  R1 contradictory run-contract field.

### Governed train/validation, model and environment contract

- Live contract readback returned cascade manifest
  `d6ca36a4c21cbadb922df897625ce80dc9d6fa3d5770b3c6cb84ddff78e10fd2`, M1 export manifest
  `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71`, exact classes
  `{"0": "traffic_sign"}`, `test_included=false`, train stem
  `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372` and validation stem
  `ae3f3509319fbb301012e9fbeb7431caacfcd4035c9d2f9167f24e3ed2b8f593`.
- The approved upload is bound to archive SHA-256
  `eb5226e36cf619e271132794c97fd633f7528d72e25463356eb165f36f43e191` and historical source
  commit `1842a1b77e6448a54fec486937f4c0f0e6ff19f5`. Because the archive was present locally, QA ran
  the full verifier: all 5,888 payload members re-hashed and reconciled with the current governed
  roster; splits were exactly `train`/`val`; `test_included=false`; counts were 1,912 raw train,
  376 raw validation, 1,800 WP35 train images and 1,800 WP35 train labels.
- Run validation requires the exact approved model path, origin and SHA-256, plus live model bytes;
  exact data/project/name/`exist_ok`; approved seeds `20261018`, `20261019`, `20261020`;
  positive numeric training values; `deterministic=true`, `pretrained=true`, `fliplr=0.0` and
  `plots=false`; and the complete clean CUDA/GPU/driver/package/Git/lock environment schema.
- The internal-training regression observed telemetry shutdown before the fake Ultralytics run and
  observed the governed seed, CUDA-only contract, deterministic/pretrained flags, zero horizontal
  flip and disabled plots. No actual training occurred.

### No-follow result creation and notebook state

- The packager walks existing output-parent components with `lstat`, refuses any existing archive,
  sidecar or partial path including broken symlinks, exclusively creates both partials, requires
  regular files, atomically renames them and rechecks the final files before semantic replay.
- Authored real regressions covered archive, sidecar, archive-partial, sidecar-partial and linked
  parent targets. Independent QA repeated the archive-partial case using a harmless temporary
  external file and confirmed its original bytes remained unchanged.
- Notebook readback found four code cells, all outputs empty and all execution counts null. Colab
  metadata requests `L4`; code retains the one-epoch smoke launcher and no test/evaluation route.

## Executable gate matrix

| Gate | Result | Readback |
| --- | --- | --- |
| R2 cascade-Colab targeted tests | PASS | **31/31** |
| Combined cascade Colab + cascade dataset tests | PASS | **43/43** |
| Independent valid-package replay | PASS | exact 8-member roster; semantic status `D1_CASCADE_COLAB_RESULT_PACKAGE` |
| Independent re-hashed contract forgery | PASS | rejected |
| Independent re-hashed checkpoint forgery | PASS | rejected |
| Independent partial-output redirect | PASS | rejected; external victim unchanged; final archive absent |
| Historical private bundle | PASS | exact archive hash; **5,888/5,888** payload members; train/val only |
| Root targeted Ruff | PASS | `src`, `tests` and both relevant builders clean |
| Root lock | PASS | 168 packages resolved; lock unchanged |
| Complete detector Ruff including notebook | PASS | `m1`, `tests`, `colab`, `d1_cascade_classifier` clean |
| Entire detector suite | PASS | **79/79** |
| Detector lock | PASS | 66 packages resolved; lock unchanged |
| Full package verifier matrix | PASS | **52/52** in 91.9 seconds wall time |
| Notebook state | PASS | 4 code cells; empty outputs; null execution counts; L4 requested |
| Git whitespace check | PASS | `git diff --check` produced no error before this record |
| Graft freshness | PASS | wiring graph in sync at 2,486 nodes; deep meaning layer not built |
| Sealed-test access log | PASS | absent before and after QA |

All `uv` validation ran with `--no-sync` except the read-only lock checks; no dependency download
occurred. The delegated gate requested the task-specific root suites and the entire detector suite,
not the historical full root suite. Graft was used for source orientation, API surface and flow
inspection; executable tests, artifact bytes and direct adversarial replay establish this verdict.

## Final boundary

- Independent QA edited no implementation, test or notebook file.
- No Colab cell ran; no GPU/CUDA runtime was connected or observed.
- No model was trained, evaluated, benchmarked, uploaded or downloaded.
- No sealed-test image, label, export, metric or access log was opened or created.
- No commit, push, deployment or publication occurred.
- R1 remains an immutable QA FAIL record; this R2 record is its independent successor PASS.
