# D1 cascade Colab R1 independent QA record

Status: `QA_FAIL_D1_CASCADE_COLAB_R1_RESULT_AND_RUN_CONTRACT_BLOCKERS`
Reviewer: `Codex independent QA session (did not author R1 and did not act as PM)`
Reviewed at: `2026-10-19T01:23:44+07:00`
Boundary: `QA_OF_D1_CASCADE_COLAB_R1_ONLY_SYNTHETIC_NO_TRAINING_NO_TEST_ACCESS_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH`
Reviewed checkpoint: `150777a49d010096fbe246a61a9589f2a27b9e00` plus the current uncommitted R1 worktree

This append-only record independently reviews only the uncommitted D1 cascade Colab R1 package
described by `docs/review/d1_cascade_colab_r1_implementation_record.md`. It changes no runner,
test, notebook, model, dataset, manifest, Owner decision, project memory or roadmap file.

## Verdict

- **D1 cascade Colab R1: FAIL.** 0 Critical, 3 High, 1 Low.
- The exact historical private bundle is genuine, train/validation-only and reconciles with the
  current governed roster. The one-class dataset contract and absence of a public evaluation/test
  route also verify.
- R1 cannot yet be trusted as an auditable Colab result package. Its standalone archive verifier
  accepts forged lifecycle artifacts, its run-contract validator accepts materially contradictory
  data/training/CUDA claims, and its packager follows a pre-existing partial-output symlink.
- Do not run the one-epoch smoke, accept a cascade checkpoint/result archive, or use this package
  for validation evidence. Issue a successor remediation and request a new independent review.
- This FAIL does not revoke the Owner's dual-baseline decision, D1 cascade dataset R2 QA PASS,
  M1-Colab-R3 QA PASS or the already verified private M1 train/validation upload.

## Reviewed byte pins

| Item | SHA-256 |
| --- | --- |
| R1 implementation record | `a467b737c0d2e24c49ceb1d2561d105dada7fc19b8adba0f0f1cd87a2ae3b516` |
| R1 runner | `fe77a05c3a4aa2ed685d3fd75bc8e9026400a0e137a10bd056cb9c492e3b8f7c` |
| R1 notebook | `a4b9871ccc7f7eaa48d2eceec4adc0192f5ae1d25f03f625608744408ce41d93` |
| R1 tests | `0f81beda9e6ffc553075cee9b4ad82bd7bf8b052c2a76a8bb687d78ea4f087da` |
| Shared M1 Colab builder | `ac0c4a9a7d15522bb4254221f252fefb640395683b4ee7b7698b61f606d47536` |
| D1 cascade dataset builder | `d2b80eb4906570e6636d3e0651a612368181e66a007c8e424d7a8df3d560cb39` |
| D1 cascade dataset manifest | `d6ca36a4c21cbadb922df897625ce80dc9d6fa3d5770b3c6cb84ddff78e10fd2` |
| Detector lock | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |
| Owner-approved `yolo11s.pt` | `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5` |
| Dual-baseline Owner decision | `39f26b0e29a2a60a5972ea07e6e0dcf04ce5e53f722a3c92b3a69b267934a0b2` |
| M1-Colab-R3 independent QA | `4b3ddcfebcb7b055dc42c229cd890234bf6decd32e8fe2a965d372732a5503c0` |
| Private-upload record | `3fda6ac5f9d775668e21decf22619faa6d5fdb94f6eabbf9bca436f17de568f7` |
| Pinned M1 logging runner | `0d04c869d0181c68a4d60a93b05967c4db5b5e31cfc44cf653bfcbd43f225786` |

## Verified controls that are not blockers

- The preserved local archive hashes to
  `eb5226e36cf619e271132794c97fd633f7528d72e25463356eb165f36f43e191`.
  The real R1 verifier re-hashed all 5,888 payload members and accepted the exact historical source
  commit `1842a1b77e6448a54fec486937f4c0f0e6ff19f5`, allowed splits `train` and `val`,
  `test_included=false`, train stem hash `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372`
  and validation stem hash `ae3f3509319fbb301012e9fbeb7431caacfcd4035c9d2f9167f24e3ed2b8f593`.
- Bundle verification compares the historical archive against a freshly derived current governed
  roster, checks exact path/split/kind/hash bindings, accepts only regular safe tar members, and
  rejects destination-parent symlinks during extraction.
- The cascade dataset verifier reports one class (`0: traffic_sign`), exact train/validation
  boundaries and no `test:` entry. The parser exposes only `run` and the internal `_train` command;
  there is no evaluation, threshold-selection, final-evaluation or test-export option.
- The internal path restricts seeds to `20261018`, `20261019` and `20261020`, pins the approved
  weight and detector lock, calls telemetry shutdown, requires observed CUDA, and sends
  `deterministic=true`, `pretrained=true`, `fliplr=0.0` and `plots=false` to Ultralytics.
- Notebook JSON parses, requests L4, has four code cells, empty outputs and null execution counts.
  It defaults to the one-epoch smoke and contains no test/evaluation route.
- `results/experiments/sealed_test_access_log.jsonl` was absent before and after QA.

## Findings

### H-1 — High: standalone result verifier accepts an entirely forged lifecycle package

`verify_result_archive()` verifies only the sidecar-defined eight-file roster, file hashes and a
self-issued attestation. It does not parse or semantically validate the archived
`run_contract.json` or `colab_execution.json`, does not validate the SQLite database, does not
reconcile checkpoint hashes against the archived run contract, and does not validate required
lifecycle steps or the exact training command from archived evidence.

Independent QA created a synthetic archive with the canonical eight names but used `not-json` for
both JSON lifecycle files, `forged` for `DB_logger.db`, arbitrary bytes for both weights and a
self-consistent sidecar. The real verifier returned success:

```text
{"FORGED_ACCEPTED": true, "run": "D1C_forged",
 "invalid_json_members": ["run_contract.json", "colab_execution.json"],
 "sqlite_magic": "forged"}
```

The local packager performs stronger pre-packaging checks, but a downloaded or copied result is
precisely where the standalone verifier is the trust boundary. Re-hashing forged bytes into a new
sidecar must not turn them into accepted training evidence.

Required repair: extract to a temporary directory with safe regular-file handling, then run the
same complete source validation used before packaging against the extracted artifacts. Derive the
canonical roster and attestation from the validated archived run contract, independently re-hash
both checkpoints, validate SQLite/text/results reconciliation and require the exact execution
lifecycle and train command. The sidecar must not be its own semantic authority.

### H-2 — High: run-contract validation accepts contradictory data, training and CUDA claims

`validate_run_contract()` pins several top-level hashes but does not validate the actual train and
validation stem hashes, one-class map, canonical `data.yaml`, or equality between `train_args.data`
and the governed contract. It also does not bind `project`, `name` or `exist_ok` to the actual run;
does not validate positive finite numeric training arguments; accepts arbitrary model path/origin;
and reduces the environment to four fields instead of calling the existing exact
`m1.contract.validate_environment_record()` CUDA identity validation.

Independent QA coherently changed the split hashes to `forged`, classes to
`{"999":"not_traffic_sign"}`, data to `/tmp/test.yaml`, model path/origin, project/name, and set
epochs/image-size/batch/workers/fraction/patience to invalid zero or negative values. It supplied
only `runtime_backend=cuda`, `cuda_available=true`, a clean-count claim and the detector-lock hash,
with no GPU name, CUDA version, NVIDIA driver, package versions or Git identity. The real
`validate_run_contract()` accepted the record.

Required repair: validate an exact run-contract schema with strict primitive/numeric constraints;
reconstruct or pass in the live governed cascade contract and require exact equality for every
data field; require `train_args.data/project/name/exist_ok` to match the run; require the approved
model path, origin and live hash; and apply the existing exact environment validator, including
non-placeholder CUDA/GPU/driver identity and clean Git/lock bindings.

### H-3 — High: a partial-output symlink is followed, overwrites an external target and is accepted

`package_result()` checks only the final archive and sidecar paths before opening
`.result.tar.gz.partial` with write mode. It neither refuses an existing partial sentinel nor
checks it with `lstat`. Independent QA placed `.result.tar.gz.partial` as a symlink to an external
victim file. The real packager followed the link, overwrote the external file, moved the symlink to
the final result path, emitted a sidecar, and `verify_result_archive()` accepted the symlinked final
archive:

```text
{'PARTIAL_SYMLINK_ACCEPTED': True,
 'output_target': '<temporary external victim>',
 'external_size': 2076,
 'verified_status': 'D1_CASCADE_COLAB_RESULT_PACKAGE'}
```

Required repair: fail closed if archive, sidecar or either temporary path exists by using `lstat`;
create temporary files with exclusive no-follow semantics in a validated non-symlink state tree;
require the final archive and manifest to be regular non-symlink files; and add real regression
tests for archive/sidecar/partial symlinks and preservation of external targets.

### L-1 — Low: the complete detector Ruff scope fails on the new notebook

The source-only detector Ruff scope passes, but `uv run --no-sync ruff check m1 tests colab
d1_cascade_classifier` reports six notebook findings: unsorted import blocks, two multiple-import
statements and one 110-character line. This is not an evidence bypass, but it contradicts a broad
reading of the implementation record's detector Ruff PASS. Format the new notebook and include it
explicitly in the successor gate.

## Additional contract gap observed with H-2

The execution-command check compares only a suffix beginning at `_train`; it does not require the
exact `uv run python <pinned runner>` prefix. A forged executable/script prefix can therefore be
recorded as if it were the governed command. The successor should bind the complete token list,
as M1-Colab-R3 does.

## Executable gate matrix

| Gate | Result | Readback |
| --- | --- | --- |
| R1 targeted tests | PASS | **9/9** |
| Entire detector suite | PASS | **70/70** |
| Root targeted Ruff | PASS | `src`, `tests` and the two pinned builders clean |
| Detector Python Ruff | PASS | `m1`, `tests`, runner and classifier package clean |
| Complete detector Ruff including notebook | FAIL | 6 findings in `d1_cascade_train.ipynb` |
| Root lock | PASS | 168 packages resolved; lock unchanged |
| Detector lock | PASS | 66 packages resolved; lock unchanged |
| Notebook JSON/execution state | PASS | 4 code cells; outputs empty; execution counts null; L4 requested |
| Real preserved private bundle | PASS | exact SHA-256; 5,888/5,888 governed payload members; train/val only |
| Forged result archive adversarial | **FAIL** | invalid lifecycle JSON and fake SQLite accepted |
| Contradictory run-contract adversarial | **FAIL** | forged data/class/CUDA/numeric contract accepted |
| Partial-symlink adversarial | **FAIL** | external target overwritten; final symlink accepted |
| Git whitespace check | PASS | `git diff --check` produced no error before this record |
| Graft freshness before QA | PASS | wiring graph synchronized at 2,453 nodes; deep layer not built |
| Sealed-test access log | PASS | absent before and after QA |

The passing authored tests demonstrate the intended happy path and several local checks, but they
do not cover the three acceptance/overwrite bypasses above. All adversarial fixtures were created
under temporary directories and removed automatically.

## Final boundary

- Independent QA edited no implementation, test or notebook file.
- No Colab cell ran; no GPU/CUDA runtime was connected or observed.
- No model was trained, evaluated, benchmarked or downloaded.
- No sealed-test image, label, export, metric or access log was opened or created.
- No upload, download, commit, push, deployment or publication occurred.
- Because the verdict is FAIL, `PROJECT_MEMORY.md` and `docs/product_roadmap.md` were deliberately
  not updated.
