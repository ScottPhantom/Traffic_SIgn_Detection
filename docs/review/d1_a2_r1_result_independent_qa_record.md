# D1-A2-R1 result independent QA record

Checked: 2026-11-06, about 07:10–07:15 (`Asia/Ho_Chi_Minh`).
Reviewer: Claude Code (Opus 5.5), an independent result-QA subagent. This reviewer did not write
the A2 source, the notebook or the evaluator, and did not operate the Colab run (Codex operated it).
Statements by the author or operator were treated as claims and checked again here.
Boundary: read-only result QA of the A2 result archive, its manifest, the epoch-100 checkpoint,
the execution records and the logs. There was no training, no inference or loading of the weights
for prediction, no validation scoring, no download or upload, no threshold or D-05 change, and no
git command in the main checkout. Scratch files went only to
`/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/c0d7550b-5da5-44ff-bc50-750b12caaceb/scratchpad/qa_a2_result/`.
`sealed_test_accessed=false`.

Verdict: PASS — the A2 result archive and manifest, the epoch-100 checkpoint, the two-runtime execution evidence, the run contract and binding, `results.csv`, and the SQLite/text logs all verify, and the real archive passes the evaluator's offline rebuild of `inspect_a2_run_weights` (recomputed attestation `3047b09d…28c0`). The archive may proceed to the contract §4 common evaluator.

This verdict covers result integrity only. It is not a metric claim, an A2-vs-pilot comparison,
a D-05 acceptance or a vehicle-behavior validation.

## 1. Inputs and provenance

- Read: `AGENTS.md`; the handoff `docs/review/d1_a2_r1_claude_handoff_2026-11-06.md`
  (SHA-256 `89a6d3f0…77e8`); the run contract (`1ce15365…96e1`, equal to the authorization pin);
  the Owner authorization record (`1a11b283…21c9`); both source-QA records; the notebook QA record;
  the live-smoke QA record (`aaeb45cf…559d`); and the execution record (`8535f2e4…8a45`).
- `graft check .` (main checkout): graph in sync. `graft skeleton detector/m1/checkpoint_store.py`
  was used to locate the retention/prune logic. Pinned source in the main checkout:
  `run_d1_colab_a2_r1.py` `a6bb6e68…d6de` and `resumable_train_a2_r1.py` `c3823eef…2ace`. Both
  equal the contract §5 pins.
- Artifacts: the byte copies in `tmp/a2_state/` and the original synced Drive folder
  `…/M1_D1_Colab/runs/d1_a2_seed_20261018_r1`.

## 2. Copy equals original (verified artifact)

All 14 files in `tmp/a2_state` were hashed and compared with the synced Drive originals. All 14 are
EQUAL in size and SHA-256:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `…_a2_r1_result.tar.gz` | 42,528,074 | `ea7dba03b0a53cfea41fd876544715d783e56abf4837568df4e74f256a66a609` |
| `…_a2_r1_result.tar.gz.manifest.json` | 1,986 | `7a4e18563ee0c16a8dd01506e48a5c9fe379e205b3af96db25b4cf933a07d343` |
| `DB_logger.db` | 31,219,712 | `94496541236bbee341d0272dbccea567b4b12c2a73b8840ed539a8998557bbe5` |
| `colab_execution.json` | 4,583 | `52ef6245be892f83faecf93717a0817db0af5d13c0cd1b5a4e5692fd0c88f149` |
| `colab_train.log` | 23,657,307 | `04582787d4181a2dae6bab700a0342bde2f2610fa6309223ae53d22b256191ab` |
| `execution_attempts.jsonl` | 973 | `2329ec1f42f8859499da8f6062878f75f8afbcebf194fd40b68f1d9e3b8951ab` |
| `recovery/latest.json` | 233 | `cbe617e776837fe43fd9d7808b3d32770a5f0bd71cf71a80a6a4e5bd709b00db` |
| `recovery/training_outcome.json` | 297 | `4540ebf699b03cbb1250c31c0172f4b1f6d206ad12f88f5320416fbcc484276f` |
| `epoch-0100/checkpoint_manifest.json` | 2,530 | `84b69261933faf1b8a6e9fd804fc82a3a1bb36cdfcf3664e2f2d3b565b8c0ab2` |
| `epoch-0100/weights/last.pt` | 76,235,491 | `8332b1af8f46d7e19121508af39a588096bb05a4953c2430fe496d519ad4f498` |
| `epoch-0100/weights/best.pt` | 76,227,299 | `86c708aa9d358838e548c4c13f2bbd7a29bb9df1eacf4de47af19ba25faa0acb` |
| `epoch-0100/results.csv` | 12,699 | `bdd84912be32fa500264e820abcb2c010fe7cb36c49653d49bb7282d554cd7b0` |
| `epoch-0100/args.yaml` | 2,111 | `539969935283e1d6e34c0e6ce80e31607f5f1823fee5ce773dc93644aca301dd` |
| `epoch-0100/run_contract.json` | 3,658 | `084dc0898576daf303e31f38a7c49a4c529cb0c3a296394784e5929cf2e8f677` |

After all checks the copies were hashed again (aggregate of the file-hash list
`39e36c50…4435`) and were unchanged. The Drive folder holds only these files plus
`recovery/snapshots/epoch-0099`. It has no `quarantine/` folder and no `.partial` staging
directory.

## 3. Archive and manifest (verified artifact)

- The archive hashes to `ea7dba03…a609` (42,528,074 B), and the manifest to `7a4e1856…d343`
  (1,986 B). The manifest binds `archive_name` (equal to the file basename) and
  `archive_sha256 = ea7dba03…a609`. It also declares `status=D1_COLAB_RESULT_PACKAGE`,
  `terminal_outcome=SUCCEEDED`, `sealed_test_accessed=false` and
  `run_attestation_sha256=3047b09d…28c0`.
- The archive has 8 members, all regular files, with no links and no duplicate names. The member
  set equals the manifest set. It was extracted with `tarfile` `filter='data'` into the scratch
  `extract/` folder. Every member matches its declared size and SHA-256:

| Member | Bytes | SHA-256 |
| --- | ---: | --- |
| `<run>/weights/best.pt` | 19,289,370 | `9781f7d840e48a140d6031dc2b388359093a06a2b6f8912ba31b6a300c0ebb0b` |
| `<run>/weights/last.pt` | 19,289,370 | `e602547ee5a875854e0a751ca5c66ae8da36550bec694e1f72d0ae0ead530df7` |
| `<run>/results.csv` | 12,699 | `bdd84912be32fa500264e820abcb2c010fe7cb36c49653d49bb7282d554cd7b0` |
| `<run>/args.yaml` | 2,111 | `539969935283e1d6e34c0e6ce80e31607f5f1823fee5ce773dc93644aca301dd` |
| `<run>/run_contract.json` | 4,212 | `9cc5318a25f9789b5da6afd3fd318743eb728372759be50f40ac8f8f3d2aac8b` |
| `colab_logs/colab_execution.json` | 4,583 | `52ef6245…f149` (equal to the Drive top-level file) |
| `colab_logs/colab_train.log` | 23,657,307 | `04582787…91ab` (equal to the Drive top-level file) |
| `colab_logs/DB_logger.db` | 31,219,712 | `94496541…bbe5` (equal to the Drive top-level file) |

- The `best.pt`, `last.pt` and `results.csv` pins in the handoff match exactly. The archived
  `results.csv` and `args.yaml` are byte-identical to the epoch-100 checkpoint copies.
- `run` = `D1_yolo11s_wp33_afa03d4b_20261018_20261105T224723_a2_r1`. It matches the evaluator's
  `RUN_PATTERN`.

## 4. Execution and checkpoint (verified artifact)

- `colab_execution.json` reads `schema_version=2` (int), `experiment=package=D1-A2-R1`,
  `mode=resume`, `status=SUCCEEDED` and `error=null`. Its `training_outcome` is
  `status=COMPLETED` (not `COMPLETED_EARLY_STOPPED`), `completed_epoch=100`, `resumed=true` and
  `sealed_test_accessed=false`. It also records `checkout_commit=f3f75717…eb255`, seed 20261018,
  epochs 100, imgsz 1280, batch 4, device `0` and tag `a2_r1`. The state path ends in
  `M1_D1_Colab/runs/d1_a2_seed_20261018_r1`. `bundle_binding.test_included=false`, and the bundle
  SHA is `7ea344cb…d641`. `recovery/training_outcome.json` agrees.
- `execution_attempts.jsonl` has exactly 2 records, which equal `execution_attempts` inside
  `colab_execution.json`:
  - fresh: `PAUSED_FOR_RESUME`, 2026-11-05 15:46:09–15:50:35 UTC, digest `df394f37…c80b`;
  - resume: `SUCCEEDED`, 16:03:48–23:38:33 UTC, digest `0e86ec57…1a98`.

  The two digests differ. Both attempts use schema `sha256:d1-runtime-v1:tag+linux-boot-id`, run
  binding `7f34c722…a3f` and checkpoint binding `873163a4…b06d`. The chronology does not overlap.
- Both legs ran on NVIDIA L4. The fresh leg shows this at log L108/L134, and the resume leg at
  log L1597/L1623 (`gpu_name: NVIDIA L4`, `CUDA:0 (NVIDIA L4, 22563MiB)`). The resume-leg
  `m1.cli check` also prints `git_commit=f3f75717…`, `git_dirty_files=0` and Ultralytics 8.4.172.
- `recovery/latest.json` points to `generation=epoch-0100`, with manifest `84b69261…0ab2` (the
  actual file hash matches) and binding `873163a4…b06d`. The checkpoint manifest declares
  `completed_epoch=100`, `status=RECOVERABLE` and `binding_sha256=873163a4…b06d`. This equals the
  smoke's binding in the live-smoke QA record. All 5 declared files match in size and SHA-256
  (the table in §2). The checkpoint `run_contract.json` (`084dc089…f677`) is byte-identical to the
  smoke's epoch-1 contract, so the run contract did not change between the legs.
- Checkpoint metadata was read by a pickle-opcode scan only (`pickletools.genops`, no unpickling).
  Checkpoint `best.pt` holds `epoch=35` (0-based, so epoch 36), `best_fitness=0.57779` and the
  date `2026-11-05T17:40:19Z`. Checkpoint `last.pt` holds `epoch=99` (epoch 100). The archived
  weights are optimizer-stripped (`epoch=-1`, `best_fitness=None`) and carry the same save dates.
  This explains the 19.3 MB vs 76 MB size difference: they are the same saves, packaged
  differently.

## 5. Run contract and binding (verified artifact)

- The archived `run_contract.json` differs from the checkpoint copy only in `status`
  (`STARTED`→`TRAINED`) and the added `artifacts.weights`. These bind `best.pt` `9781f7d8…0b0b`
  and `last.pt` `e602547e…0df7`, equal to the archived members.
- `environment`: `git_dirty_files=0`, `git_commit=f3f7571794a5db04ad302fecf8014546ec1eb255`,
  `gpu_name=NVIDIA L4`, `runtime_backend=cuda`, `ultralytics=8.4.172`, `torch=2.14.1+cu130` and
  detector lock `5d56642a…aec5`.
- `train_args` were compared key for key with the pinned pilot `run_contract.json`
  (`9f8fc94c…0b88`, re-hashed here). The key sets are identical. The only differences are `data`
  (`…/d1_a2_r1/runtime/a2_data.yaml`) and `name` (run identity, allowed by contract §2). The
  effective `args.yaml` was compared with the pilot `args.yaml` (`a457c6d5…16f0`, re-hashed). It
  differs only in `data`, `name`, `model`/`resume`/`save_dir` (run-directory paths).
  `optimizer=AdamW` and `lr0=0.000172` equal the pilot.
- Frozen values confirmed: patience 0, epochs 100, imgsz 1280, batch 4, seed 20261018,
  `fliplr=0.0`, workers 4, fraction 1.0, deterministic, pretrained, plots false and device `0`.
  The pretrained SHA is `85a76fe8…02d5`.
- `a2_data`: rule `A2_ALL_975_RAW_AND_WP35`; 4,687 entries; 975/339/636 repeated;
  `data_yaml_changed_keys=["train"]`; list manifest `12f09435…0cbd`.
- The list SHA `90d735d6…fdec2`, the roster SHA `0ce6afdc…69aa3` and the authorization SHA
  `1a11b283…21c9` are consistent everywhere they appear: the execution JSON, `train_command`, the
  checkpoint binding, both run contracts and the trainer stdout in the log. The repo authorization
  record hashes to `1a11b283…21c9`.
- `sealed_test_accessed=false` appears in the manifest, the execution JSON (top level and
  `training_outcome`), `training_outcome.json`, both run contracts and the final trainer stdout.
  `test_included=false` is set in `bundle_binding`. The split-stem `test` hash `afa03d4b…24bc` in
  the binding and contract is a seal identity, not an access.

## 6. `results.csv` (verified artifact; descriptive only)

- There are 100 rows with epochs exactly 1..100, in order, with no duplicates and no
  NaN/inf/empty cells.
- Ultralytics 8.4.172 fitness (`detector/.venv/.../ultralytics/utils/metrics.py`
  L1017–1020) is weights `[0, 0, 0, 1.0]`, which is `metrics/mAP50-95(B)`. By that column the
  best epoch is **36**: P 0.73719, R 0.73302, mAP50 0.79278, mAP50-95 0.57779. This agrees with
  the checkpoint `best.pt` metadata (§4) and with the end-of-run `best.pt` validation line
  (log L121982: `all 376 560 0.737 0.733 0.792 0.577`).
- Epoch 100: P 0.75075, R 0.63938, mAP50 0.71708, mAP50-95 0.50892.
- These are per-epoch numbers on the export `val` split (376 images, 560 instances). They are not
  the R3 roster (624 boxes) and not the contract §3 criteria. **No win/loss conclusion is drawn.**

## 7. Logs (verified artifact)

These checks ran on a scratch copy of the archived DB, opened `mode=ro`.

- SQLite: `PRAGMA integrity_check=ok`. The tables are `logs` and `sqlite_sequence`. `logs` has
  **122,015** rows, with ids contiguous from 1 to 122,015. All rows are INFO from logger
  `CPV_log_record`, from 2026-11-05 15:46:11 to 23:38:33.
- Parity: `colab_train.log` has 122,015 lines and ends in a newline. `logs.message` ordered by id
  equals the text lines exactly, one for one (`msgs == lines` → True).
- `Using 4687 train, 376 val images for fraction=1.0 at imgsz=1280` appears twice: L216 (fresh)
  and L1704 (resume). `Resuming training … from epoch 2 to 100 total epochs` is at L1703. The log
  shows `1 epochs completed` (fresh) and `99 epochs completed in 7.498 hours` (resume). There is
  no EarlyStopping line. The terminal lines are `PAUSED_FOR_RESUME` (L1489) and
  `SUCCEEDED; validated result packaging begins` (L122015).
- Scans found 0 tracebacks, 0 `error`/`exception`/`WARNING` lines and 0 `nan`. They found 0
  `images/test`, `labels/test` or `/test/` paths. Label scans touched only
  `data/processed/m1_yolo/labels/train` (62 progress lines) and `labels/val` (6). The 17
  `afa03d4b` hits are the run name (which embeds the seal prefix) and the seal hash in printed
  bindings. The only `"test":` line is that binding hash.

## 8. Offline attestation (verified current behavior on this real archive)

Function: the staged evaluator `tmp/a2_eval/detector/colab/evaluate_d1_a2_r1_common_r1.py`
(SHA-256 `c08f5de6…8317`). Its source QA was `PASS giới hạn` (M1 PYTHONPATH; M2 two-attempt
package only). It was imported with
`PYTHONPATH=<a2_eval>/detector/colab:<main>/detector/colab:<main>/detector`,
`PYTHONDONTWRITEBYTECODE=1`, `TMPDIR=<scratch>` and the main checkout's locked venv Python
(`-s -B`). Only the verification functions were called. `run()`, `extract_best` and all inference
paths were not called. Results:

| Check | Result |
| --- | --- |
| `verify_predecessors` (A3 evaluator `5d8e49bf…`, A2 launcher `a6bb6e68…`, A2 trainer `c3823eef…`) | PASS |
| `verify_candidate_pins` (archive/manifest/authorization SHA, 40-hex checkout) | PASS |
| `verify_archive` (launcher `r6.verify_r4_result_archive`: R1 eight-file roster, R6 int `schema_version=2`, exactly two attempts, distinct runtime digests; `RUN_PATTERN`) | PASS: `D1_RUNTIME_EVIDENCE_VERIFIED`, `attempt_count=2`, `distinct_runtime_digests=true` |
| `read_small_members` | PASS |
| `verify_attestation` (offline `inspect_a2_run_weights` rebuild: exact A2 schema, list/roster/auth, `train_args` = pilot + data, CUDA L4 clean checkout `f3f75717…`, governed export binding, D-05 gates, weight bindings) | PASS: recomputed `3047b09db7a993b2260a9e8a88746b1cc474f3218a1eff55d3bbf368536a28c0`, equal to the manifest |
| `verify_execution` | PASS |
| `verify_training_log` | PASS |
| `a2t.verify_owner_authorization` (repo record) | PASS |
| evaluator `verify_live_state` (on the byte-identical copy) | PASS |
| `verify_candidate` (full composed gate) | PASS: `training_outcome=COMPLETED`, `best_sha256=9781f7d8…0b0b`, `run_contract_sha256=9cc5318a…ac8b` |
| launcher `r6.verify_live_state` (on the byte-identical copy) | PASS: `D1_R4_LIVE_STATE_VERIFIED` |

The live-state verifiers were run on the copy and not on the Drive folder, so as not to
materialize the Drive `epoch-0099` placeholder. The copy is byte-equal to Drive for every file
those verifiers read (§2).

## 9. Findings

No Critical, High or Medium finding.

- **I1 — Info: Drive `recovery/snapshots/epoch-0099` metadata.** `ls -ldO` shows
  `compressed,dataless`, link count 65,535, size 2,097,120, mtime 06:27:09 and ctime 06:48:56.
  This is a Google Drive File Provider placeholder: an unmaterialized directory, with placeholder
  link count and size values. It is not a filesystem defect. `CheckpointStore` keeps
  `retention=2` generations (`checkpoint_store.py` L129–136, L301–316), so `epoch-0099` is the
  expected previous generation. The pointer and every verifier use only `epoch-0100`. **It does
  not matter for this verdict.** It was not listed or opened. Fix: none. If an epoch-99 rollback is
  ever needed, materialize it on purpose and verify its manifest first.
- **I2 — Info: the run contract's `environment` is the fresh-leg snapshot.** The trainer keeps the
  `run_contract.json` written at fresh start and adds only `status`/`artifacts` at the end. The
  resume runtime's environment is therefore evidenced by the log (`m1.cli check`, L1590–1625:
  clean `f3f75717…`, NVIDIA L4, Ultralytics 8.4.172, the same values) and by the distinct runtime
  digest. It is not attested inside the contract. Fix (future launchers, proposal): record a
  per-attempt environment block.
- **I3 — Info: per-epoch validation is not the §4 evaluation set.** `results.csv` and the
  end-of-run validation use the export `val` labels (376 images, 560 instances). The §4 evaluator
  uses the R3 roster (376 frames, 624 boxes). The `best.pt` selection (epoch 36) uses the former,
  as the contract §10 expects. Fix: none. Do not compare these numbers with §3 criteria.
- **I4 — Info: wall time exceeded the estimate.** The resume leg ran 16:03:48–23:38:33 UTC
  (about 7.58 h), plus the fresh leg's 4.4 min. Ultralytics reports 7.498 h for 99 epochs. The
  contract §9 estimate was about 5 L4-hours (4.6–5.3) and was classified as unknown. This
  resolves that unknown. It has no integrity impact.
- **I5 — Info: the execution record has a sync-timing caveat (acknowledged).** Every factual
  statement in `docs/review/d1_a2_r1_execution_record.md` matches the artifacts: commit A/B, the
  attempt windows, both digests, the 5 table rows (sizes and hashes), the eight-member manifest
  binding, attestation `3047b09d…28c0`, 122,015 log lines, `integrity_check=ok` and
  `sealed_test_accessed=false`. Its "Handoff boundary" paragraph says that the Drive listing and
  the Mac sync had not yet exposed the archive. That was true when it was written and is now
  superseded: the archive and manifest are present and equal to the copies. The handoff
  acknowledges this, and the record was correctly left unedited. Fix: none.

## 10. Commands run (all read-only on inputs)

- `shasum -a 256` / `stat` over every file in `tmp/a2_state` and its Drive original (14/14 EQUAL);
  `ls -la`, `stat`, `ls -ldO` and `xattr` (names only) on the Drive folder and the `epoch-0099`
  directory entry.
- `python3 -I scripts/extract_verify.py <archive> <manifest> <scratch>/extract` → `ALL True`.
- `python3 -I scripts/contract_checks.py <pilot run_contract> <archived run_contract> <ckpt run_contract> <archived args.yaml> <pilot args.yaml> <archived results.csv>`.
- `python3 -I scripts/log_checks.py <archived DB> <archived log> <scratch>/work` (DB copied first, then opened `mode=ro`).
- `python3 -I scripts/ckpt_meta.py <ckpt best/last> <archived best/last>` (pickle opcode scan, no unpickling).
- `grep` on the archived log, and `grep` of the locked Ultralytics `metrics.py`/`trainer.py` for fitness.
- `graft check .`; `graft skeleton detector/m1/checkpoint_store.py`; `graft skeleton detector/colab/run_d1_colab_checkpoint_r6.py`.
- `<main>/detector/.venv/bin/python -s -B scripts/attest_driver.py` with the PYTHONPATH in §8.

## 11. Claim classification

- **Verified artifact:**
  - every hash and size in §2–§3;
  - the execution, attempt, checkpoint and binding facts in §4–§5;
  - the `results.csv` structure and best epoch 36 in §6;
  - SQLite integrity, the row count and parity in §7;
  - the execution-record statements in I5.
- **Verified current behavior:** the staged evaluator's verification functions and the launcher
  `r6.verify_live_state` accept this real archive and state (§8). The earlier "unknown" in contract
  §12 (packaging-shim behavior on a real Colab result) is now resolved: the packaged attestation
  recomputes exactly.
- **Proposal:** I2's per-attempt environment block. The §4 evaluator run and its result QA are
  still to come.
- **Unknown:**
  - the git object contents of commit A/B and of `a0fd8d46…`, which were not inspected because git
    in the main checkout was out of scope;
  - the contents of the Drive `epoch-0099` generation (not opened);
  - any A2 metric on the R3 roster, and any A2-vs-pilot outcome.

## 12. Gate decision

**The A2 archive may proceed to the contract §4 common evaluator.** Use these pins:

- archive `ea7dba03…a609`;
- manifest `7a4e1856…d343`;
- `best.pt` `9781f7d8…0b0b`;
- authorization `1a11b283…21c9`;
- `--expected-checkout f3f7571794a5db04ad302fecf8014546ec1eb255`.

Then run the evaluator under its own source-QA conditions: M1 (`PYTHONPATH`); M2 is satisfied by
this standard two-attempt package. An independent result QA of the evaluation must follow. The
sealed test `afa03d4b…` stays closed.

`sealed_test_accessed=false`.
