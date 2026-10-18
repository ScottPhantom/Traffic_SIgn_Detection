# D1 cascade Colab R2 QA remediation report

Status: `PM_READY_AWAITING_INDEPENDENT_QA`
Prepared: `2026-10-19` (`Asia/Ho_Chi_Minh`)
Boundary: `R2_REMEDIATION_ONLY_NO_COLAB_NO_TRAINING_NO_TEST_ACCESS`
Base checkpoint: `150777a49d010096fbe246a61a9589f2a27b9e00` plus the shared uncommitted worktree

## Immutable R1 verdict

R1 remains FAIL with 0 Critical, 3 High and 1 Low in
`docs/review/d1_cascade_colab_r1_independent_qa_record.md` (SHA-256
`c6ec7b19c2d2cbb2b6ff13a9676d8f0560c58f8dee01c3332a4cd276cf658782`). This R2 package does
not edit the R1 implementation record or QA record. It closes the reported findings in successor
code and tests, subject to a new independent verdict.

## Reviewed R2 candidates

| Item | SHA-256 |
| --- | --- |
| R2 runner | `12b419f6957464cf5cb665805af42e181fc4ab3bd011c9d0bacce512fc4f8924` |
| R2 notebook | `f804c847ab672c936d3022e7813005a3453bb7ca957c6237703bc31dcbe87ea6` |
| R2 tests | `29c098af352092bee0787449441bc1119459ed3ccda1de24109869e7ce82c211` |
| QA-approved cascade dataset manifest | `d6ca36a4c21cbadb922df897625ce80dc9d6fa3d5770b3c6cb84ddff78e10fd2` |
| Pinned M1 logging runner | `0d04c869d0181c68a4d60a93b05967c4db5b5e31cfc44cf653bfcbd43f225786` |
| Detector lock | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |
| Owner-approved `yolo11s.pt` | `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5` |

## H-1 — standalone result verification

R2 no longer treats a self-consistent sidecar as semantic authority. The verifier now:

1. requires both archive and sidecar to be regular non-symlink files with no symlink component;
2. validates the exact eight-member regular-file roster, sizes and SHA-256 values;
3. extracts each member manually with exclusive file creation into a fresh private directory;
4. parses the archived `run_contract.json` and `colab_execution.json` with duplicate-key and
   non-finite-value rejection;
5. replays the complete run/data/model/environment/execution validation against the live governed
   cascade contract;
6. re-hashes `best.pt` and `last.pt` against the archived run contract;
7. validates `results.csv`, text-log lifecycle and the exact SQLite schema/content/event order with
   the pinned M1-Colab-R3 logging validator;
8. derives the attestation from validated archive evidence and then requires the sidecar to equal
   it.

The QA forged package containing `not-json` lifecycle records and fake SQLite is rejected even
after every sidecar file hash is recomputed. Separate regressions reject a self-consistent fake
SQLite database and an execution record with a shortened lifecycle.

## H-2 — exact run and execution contracts

R2 validates exact schemas and cross-field equality for:

- the live cascade manifest, train/validation stem hashes, one-class map, canonical `data.yaml`,
  approved bundle and historical bundle commit;
- the exact approved model path, origin and SHA-256, including a live local model-byte check;
- `train_args.data`, project, run name and `exist_ok`, plus seed, deterministic, pretrained,
  `fliplr=0.0` and `plots=false`;
- positive `epochs`, `imgsz` and `batch`; non-negative `workers` and `patience`; finite
  `fraction` in `(0,1]`; and a non-empty device;
- the complete M1 environment schema with clean Git state, 40-hex commit, detector lock, Python,
  platform, machine, Torch, Ultralytics, CUDA version, GPU and NVIDIA driver consistency;
- exact checkpoint paths and digests;
- the token-exact `uv run python <pinned runner> _train ...` command, full lifecycle order,
  timestamps, bundle hash, run path, tag and sealed-test exclusion.

Adversarial tests mutate every QA-reported data/class/path/model field, all invalid numeric
arguments, the CUDA schema and the command prefix; each mutation is rejected.

## H-3 — no-follow atomic result creation

Before writing, R2 walks every existing output-parent component with `lstat` and rejects symlinks.
It checks archive, sidecar and both partial paths with `lstat`, including broken symlinks. Archive
and manifest partials are created exclusively (`x:gz` / `xb`), verified as regular files, then
atomically renamed. Final files are rechecked as regular non-symlinks before standalone replay.

Real regressions place symlinks at the archive, sidecar, archive-partial and sidecar-partial paths,
and place the output below a symlinked parent. Every case fails before output I/O and preserves the
external victim byte-for-byte. Standalone verification also rejects archive and sidecar symlinks.

## L-1 — notebook Ruff

Notebook imports are now one per line and sorted; the long clone command is wrapped. Code-cell
behavior, L4 metadata, empty outputs, null execution counts and one-epoch smoke default are
unchanged. Complete detector Ruff including the notebook passes.

## PM verification

- R2 cascade-Colab tests: **31/31 PASS**.
- Combined cascade Colab + cascade dataset tests: **43/43 PASS**.
- Root Ruff (`src`, `tests`, two relevant builders): PASS.
- Root lock: PASS, 168 packages resolved, unchanged.
- Complete detector Ruff (`m1`, `tests`, `colab`, `d1_cascade_classifier`): PASS, including the
  notebook.
- Complete detector suite: **79/79 PASS**.
- Detector lock: PASS, 66 packages resolved, unchanged.
- Full package verifier matrix: **52/52 PASS** in 91.8 seconds wall time.
- `git diff --check`: PASS.
- Sealed-test access log remains absent.

No Colab cell ran; no dependency/model/data was downloaded or uploaded; no model was trained,
evaluated or benchmarked; no sealed-test item was exported or read; and no commit or push occurred.

## Independent QA request

QA should reproduce the three original High exploits against R2, rerun the exact forged-lifecycle,
contradictory-contract and partial-symlink cases, review archive extraction and command/path
normalization, verify external targets remain unchanged, run complete detector Ruff including the
notebook, and issue an independent PASS/FAIL record. R2 must not be used for the Colab smoke until
that review passes.
