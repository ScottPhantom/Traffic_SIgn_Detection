# M1-Colab-R3 independent QA record

Status: `QA_PASS_M1_COLAB_R3_R1_R2_FINDINGS_CLOSED`
Reviewer: `Codex independent QA session (did not author the R3 remediation and did not act as PM)`
Reviewed at: `2026-10-19T00:42:46+07:00`
Boundary: `QA_OF_M1_COLAB_R3_PACKAGE_ONLY_SYNTHETIC_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_COMMIT_NO_PUSH`
Reviewed checkpoint: `dcf0d5dc0e793c77df271e622ae9d87307d920cf` plus the current uncommitted R3 worktree

This append-only record re-reviews only the M1-Colab-R3 package described by
`docs/review/m1_colab_r3_qa_remediation_report.md`. It preserves the R1 and R2 FAIL verdicts and
their evidence byte-for-byte. Apart from this record, the independent review changed no source,
test, notebook, model, dataset, manifest, Owner decision, project memory or roadmap file.

## Verdict

- **M1-Colab-R3: PASS.** 0 Critical, 0 High, 0 Medium, 0 Low.
- All four R1 findings remain closed: evidence-derived packaging, mandatory frozen sync, exact
  non-placeholder CUDA identity and refusal to overwrite archive/sidecar/partial sentinels.
- All three R2 findings are closed: the standalone verifier derives the canonical eight-member
  roster, both canonical checkpoints are independently re-hashed, and the training command is
  bound token-for-token to the run contract.
- The independent synthetic matrix completed **13 accepted positive controls** and **86 expected
  rejections** with zero unexpected acceptance and zero false rejection.
- Every delegated mechanical gate passes. No open finding remains within the M1-Colab-R3 scope.
- This PASS approves the reviewed package controls only. It does not authorize a bundle upload,
  Colab execution, model training, sealed-test access, commit, push, deployment or publication.

## Reviewed byte pins

| Item | SHA-256 |
| --- | --- |
| R3 remediation report | `8f5da774013a20c3d3743a8a0726411118c2ada4494e45bb6c05d33fd39d5002` |
| `scripts/build_m1_colab_bundle.py` | `ac0c4a9a7d15522bb4254221f252fefb640395683b4ee7b7698b61f606d47536` |
| `tests/test_m1_colab.py` | `7dac63809b5fb673c032bed2a94894380d011ab2337949598acace703e3dff30` |
| `detector/colab/run_d1_colab.py` | `0d04c869d0181c68a4d60a93b05967c4db5b5e31cfc44cf653bfcbd43f225786` |
| `detector/colab/verify_d1_result.py` | `678de7f84e54c568dd3d7001873541a6226eeb2da0e5b2f725fdcde49fb994ab` |
| `detector/colab/d1_train.ipynb` | `4f7e5df089efaa01be8045c232dd02cb1a4a44e97a399530778c6e639b4babca` |
| `detector/m1/contract.py` | `901e7e372d9660cd79e6bfcab43684b1693f0a4aafad9f4c331fd8f04ba6bbbf` |
| `detector/m1/cli.py` | `86c92e642cd733a7cdd9151f85acf09267cd3b35f4ccad81ff64a207d19f2672` |
| `detector/tests/test_m1.py` | `dce78d1201ad73efc577151e1820ef54c0f21ca8c86a9431828bc0093bb4e7b9` |

## Independent adversarial readback

### Canonical archive and standalone verifier

- A canonical eight-member synthetic archive and matching manifest were accepted by both the core
  verifier and the standalone `verify_d1_result.py` CLI.
- Self-consistent manifest/archive pairs containing only `best.pt`, or the canonical eight files
  plus an extra ninth member, were rejected.
- Wrong archive name; malformed or uppercase attestation; malformed, uppercase or mismatched
  member hashes; negative, boolean or string sizes; invalid run IDs; archive-hash drift; terminal
  outcome drift; duplicate manifest records; duplicate/link/traversal members; missing members and
  tampered member bytes were rejected.
- The archive and manifest rosters therefore cannot define a smaller or larger trust boundary than
  the run-derived canonical allowlist.

### Checkpoint and packaging integrity

- The real `inspect_run_weights()` accepted a synthetic complete run only after independently
  hashing canonical `best.pt` and `last.pt`.
- Mutating `last.pt` after the run contract was written caused both direct inspection and the real
  `package_run()` path to reject; no final archive or sidecar was created.
- Missing or symlinked `last.pt`, a bad recorded `best.pt` hash and a missing run-contract field
  were rejected.
- `FAILED` execution, `sealed_test_accessed=true`, invalid SQLite bytes, an empty text log and an
  empty results CSV all failed before final package creation.
- Existing archive, sidecar, archive-partial and sidecar-partial sentinels were preserved for both
  bundle and result packaging.

### Exact execution command and runtime identity

- The exact positive command bound model, seed, epochs, image size, batch, device, workers,
  fraction, patience and safe tag to the run contract and was accepted.
- Contradicting each bound value independently was rejected. Missing, duplicate, unknown and
  reordered flags, an unsafe tag and `plots=true` were also rejected.
- `FAILED`, sealed-test-touched, non-null-error, invalid-bundle-hash, missing-field and missing
  `detector_lock_synchronized` execution records were rejected. The parser has no `--skip-sync`
  bypass.
- All fifteen combinations of the five forbidden placeholders (`UNKNOWN`, `N/A`, `NONE`, `NULL`,
  `UNAVAILABLE`) across CUDA version, GPU name and NVIDIA driver were rejected. A valid Apple M1
  Pro / arm64 / MPS record remained accepted.

### Notebook and sealed-test boundary

- Every notebook code cell remains unexecuted.
- `SMOKE = True` and `EPOCHS = 1 if SMOKE else 100` preserve the one-epoch default.
- The notebook contains no `export-test`, `--final-eval` or `--skip-sync` route.
- Independent QA did not open, enumerate, export, hash or otherwise inspect any sealed-test image,
  label or result artifact.

## Executable gate matrix

| Gate | Result | Readback |
| --- | --- | --- |
| Root targeted tests | PASS | **38/38** collected and passed: YOLO export 9, crop export 7, M1-Colab 22 |
| Detector suite | PASS | **54/54** |
| Package verifiers | PASS | **51/51** in 91.0 seconds wall time |
| Root targeted Ruff | PASS | `All checks passed!` |
| Detector Ruff | PASS | `All checks passed!` for `m1 tests colab` |
| Root lock | PASS | 168 packages resolved; lock unchanged |
| Detector lock | PASS | 66 packages resolved; lock unchanged |
| Detector CLI contract check | PASS | Apple M1 Pro, `arm64`, MPS, expected detector lock and split hashes |
| Standalone verifier help and notebook JSON | PASS | Both parsed successfully |
| Git whitespace check | PASS | `git diff --check` produced no error |
| Graft freshness | PASS | Wiring graph synchronized at 2,303 nodes and 5,843 edges |

Graft map, ask, skeleton, callers and grep queries were used before source inspection. Their
reported savings total approximately 775,788 source tokens, worth about USD 0.43 at the session
rate. Graft tier 0 was used for navigation and blast-radius evidence only, not as semantic proof.

The full historical root pytest suite was not run because it is outside the delegated R3 gate;
the current targeted root suite, complete detector suite and all 51 package verifiers ran. All
attack fixtures were created under temporary directories and removed after execution. No archive
was uploaded, no Colab cell ran, no model was trained and no sealed-test artifact was opened.
