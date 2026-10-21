# D1 checkpoint/resume R4-R6 live L4 artifact independent QA record

Status: `INDEPENDENT_QA_PASS`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Reviewer: `Codex independent artifact-QA session`

Boundary: `READ_ONLY_DRIVE_ARTIFACT_QA_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**PASS.** The live R4-R6 smoke proves a recoverable epoch-1 checkpoint on Google Drive and a real
resume to epoch 2 on a second runtime identity. The artifacts satisfy the required chronology,
binding, checkpoint, archive, SQLite, text-log and sealed-test gates. No Critical, High, Medium or
Low finding remains in this review scope.

This PASS changes the D1 **single-seed 100-epoch pilot** from NO-GO to **GO**. It does not authorize
opening the sealed test, final evaluation, model acceptance, or any safety/deployment claim.

## Reviewed inputs

- Drive run directory:
  `/Users/nguyentantai/Library/CloudStorage/GoogleDrive-tainguyentan0908@gmail.com/Drive của tôi/CPV301/Traffic_Sign_Detector/M1_D1_Colab/runs/checkpoint_smoke_seed_20261018_r4_r6`.
- Source commit: `47c86d17430808ceeee6e1a1a553cf6fef88e5ed`.
- PM report: `docs/review/d1_checkpoint_resume_r4_r6_l4_smoke_report.md`.
- Source QA record: `docs/review/d1_checkpoint_resume_r4_r6_source_independent_qa_record.md`.

The PM report was treated only as a list of claims to test. The verdict below is based on direct
artifact readback, independent hashing, SQLite queries, checkpoint deserialization and the actual
R6 verifier.

## Findings

### Two attempts, two runtime identities and chronology: PASS

`execution_attempts.jsonl` contains exactly two strict JSON records and equals the embedded attempt
list in `colab_execution.json`:

| Attempt | Mode | Started UTC | Finished UTC | Status | Runtime digest |
| --- | --- | --- | --- | --- | --- |
| 1 | `fresh` | `2026-10-21T01:48:22+00:00` | `2026-10-21T01:52:04+00:00` | `PAUSED_FOR_RESUME` | `f9479825d3652e42e08acf64189ff664fd032841413baeaf0550e26bd6007520` |
| 2 | `resume` | `2026-10-21T01:55:44+00:00` | `2026-10-21T01:59:41+00:00` | `SUCCEEDED` | `6da5cabaf95dcc10e408d006badaecd3a14e128c5f9bf30a1e7d7fe85e8bdb5c` |

The fresh attempt finished before the resume attempt started. The digests differ, while both
attempts carry the same run binding
`e7f8938dd2db4a22d86cadb5cc8c01b0a2f322bf87e709940eb75fd1addc5b2f` and checkpoint binding
`41e4940f238105692f1a6ab274ec541285a2a1a131c0b212f478acdbfc3c9bbd`.
The terminal execution object is schema-version integer `2`, identifies the second digest, embeds
the two attempts exactly, reports `SUCCEEDED`, and has `error=null`.

### Checkpoint continuity and real resume: PASS

- `recovery/latest.json` points to `epoch-0002`, its manifest SHA-256 is
  `1165a7290991444071c2a588ab3a8628850757a8192a2f69d1229f33a18e79df`, and its binding matches
  both attempts.
- `epoch-0001/checkpoint_manifest.json` is
  `b6934b9b46f7bef6cdf2942d1d0209d4be19e369aaa77d61015f0ad73b8dbaf4` and declares completed
  epoch 1. Its five declared files all exist and match declared size and SHA-256, including
  `weights/last.pt` and `weights/best.pt` at 76,222,627 bytes with SHA-256
  `b7fff0d944183358909379d24dbe73dcfa32af4a31c961afc17af6f0fff2ca19`.
- `epoch-0002/checkpoint_manifest.json` declares completed epoch 2. Its five files likewise match;
  both checkpoint weights are 76,223,011 bytes with SHA-256
  `f1d7a32b9b3226dca8b2c46b432a1ad5234b1114040c464479509337ec728645`.
- Independent PyTorch deserialization found epoch metadata `0` in the epoch-1 checkpoint and `1`
  in the epoch-2 checkpoint. Both retain optimizer and EMA state. The first has `resume=false`;
  the second binds `resume` to the recovered `weights/last.pt` path.
- The epoch-1 CSV has exactly the epoch-1 result row. The epoch-2 CSV preserves that same row and
  appends exactly one epoch-2 row.
- The resume command includes `--resume` and does not include `--stop-after-epoch`. After that
  command, the text log has zero `1/2` training progress records and 929 `2/2` records. Ultralytics
  states that it resumed the saved run from epoch 2 to 2 total epochs. This rules out a second
  epoch-1 training pass.

### Archive and durable logs: PASS

The result archive SHA-256 is
`3c640d756bcdce9984ae20d96b57eca4ff936482b7f6eb6817abb92cc47291a4`; the separately stored
manifest SHA-256 is `d1e33d2c8c44660437a447b81654ab95acd79dbd9dcdc184ff45be837db464db`.
The archive contains exactly the eight manifest members: final `best.pt`, `last.pt`, `results.csv`,
`args.yaml`, `run_contract.json`, `colab_execution.json`, `colab_train.log`, and `DB_logger.db`.
Independent streaming rehashing matched every member's declared size and SHA-256. The archived
execution, text log and SQLite hashes equal the live Drive copies.

The SQLite database is valid and contains exactly 2,475 ordered `logs` rows, IDs 1 through 2475,
spanning `2026-10-21 01:48:24` to `2026-10-21 01:59:41`. Direct queries found exactly one fresh
training command with `--stop-after-epoch 1`, exactly one resume command with `--resume`, one
`PAUSED_FOR_RESUME` terminal event, one `SUCCEEDED` terminal event, `resumed=false` then
`resumed=true`, and two `sealed_test_accessed=false` records. The text log carries the same
chronology and commands.

### Source, data and environment bindings: PASS

- Git object `47c86d17430808ceeee6e1a1a553cf6fef88e5ed` exists and is a commit. The R6 runner, notebook,
  test and implementation-record bytes at that commit match the four hashes frozen by source QA.
- `colab_execution.json`, both checkpoint manifests and the final run contract bind the executed
  checkout to that commit. The run contract records a clean checkout, NVIDIA L4, CUDA 13.0,
  driver 580.82.07, Python 3.12.3, Torch 2.14.1+cu130 and Ultralytics 8.4.172.
- Local bundle SHA-256 independently matches
  `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641`. Its embedded manifest
  identifies source commit `ffc2b448f06c45dae597de5b565cab64c0377573`, 5,888 regular files, only
  `train` and `val`, and `test_included=false`. The successor execution records its code overlay as
  commit `47c86d17430808ceeee6e1a1a553cf6fef88e5ed`.
- The export manifest, class-map CSV and detector lock independently hash to
  `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71`,
  `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242`, and
  `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` respectively.
- Train/validation stem hashes are
  `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372` and
  `ae3f3509319fbb301012e9fbeb7431caacfcd4035c9d2f9167f24e3ed2b8f593` throughout execution,
  checkpoint and archive contracts. The approved pretrained file independently hashes to
  `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`.

### Sealed-test boundary: PASS

`sealed_test_accessed` is the JSON boolean `false` in the terminal execution, training outcome,
archive manifest and SQLite/text-log outcomes. The bundle manifest declares `test_included=false`.
No `results/experiments/sealed_test_access_log.jsonl` exists in the reviewed source commit, current
worktree or Drive run, and Git reports no mutation of that path. No sealed-test export or final
evaluation was run during this QA.

## Mechanical and adversarial checks

The following read-only checks were executed independently:

```text
graft check .
graft ask "Trace the R4-R6 live state verifier ..." --source .
uv run python: load R6 runner and call verify_live_state(Drive run)
shasum -a 256: live artifacts, checkpoints, bundle, model, export manifest, class map, lock
Python tarfile/hashlib: enumerate exactly eight archive members and stream-rehash every member
sqlite3 -readonly: schema, row bounds, command/outcome/resume/sealed chronology
detector uv Python + torch.load: epoch, optimizer/EMA and resume metadata for both checkpoints
git cat-file/show/ls-tree/status: source-commit and sealed-log checks
```

The real R6 verifier returned `D1_R4_LIVE_STATE_VERIFIED` and nested
`D1_RUNTIME_EVIDENCE_VERIFIED` with attempt count 2, distinct runtime digests, common bindings and
`sealed_test_accessed=false`. Independent checks above reproduced the security-relevant facts
rather than relying only on that green result.

Graft reported `STALE` only for concurrent, unrelated Streamlit presentation files outside this
artifact-QA scope. The freshness-aware query located the active R6 → R5 → R2 live/archive/runtime
verification chain. This review did not rebuild Graft because doing so would absorb unrelated
worktree changes.

## Gate disposition

| Gate | Independent QA disposition |
| --- | --- |
| Two distinct L4 runtime identities | **PASS** |
| Fresh epoch 1 persisted and recoverable | **PASS** |
| Resume continues to epoch 2 without retraining epoch 1 | **PASS** |
| Checkpoint manifests/files/hashes | **PASS** |
| Final archive/manifest and all member hashes | **PASS** |
| SQLite and text-log chronology | **PASS** |
| Code/data/model/environment binding | **PASS** |
| Sealed-test isolation | **PASS** |
| D1 single-seed 100-epoch pilot | **GO** |
| Sealed-test access/final evaluation | **NO-GO / not authorized** |

