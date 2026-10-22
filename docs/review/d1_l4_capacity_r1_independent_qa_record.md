# D1 L4 capacity successor R1 — independent QA record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: **INDEPENDENT_QA_FAIL — REPAIR REQUIRED BEFORE COMMIT, COLAB OR SELECTION**  
Reviewer: `Codex independent source-QA session`  
Boundary: `READ_ONLY_SOURCE_QA_NO_COLAB_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**FAIL: 1 Critical, 5 High, 0 Medium, 0 Low.**

The fixed 24-attempt grid, deterministic headroom/CV selection, append-only attempt roster and
train/val-only intent are present. Targeted tests and lint pass. Those controls do not close six
executable blockers: Ultralytics can silently reduce a requested batch after OOM, the measured
interval excludes data-loader wait even though `workers` is a selection dimension, the standalone
verifier accepts self-consistent forged trust roots and extra training controls, OOM evidence is
not semantically replayed, SQLite can write through a substituted symlink, and the execution
journal uses a permissive JSON decoder that accepts contradictory sealed-test keys.

Do not commit/push or run this capacity package on Colab. It may not produce an Owner decision,
configuration lock, recovery smoke or final-seed authorization. The currently running Pilot R3 is
not affected by this verdict and must not be interrupted.

## Frozen bytes reviewed

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/l4_capacity.py` | `bf42b3a55de68cfe94ebe6902f0bda9871950088e02a1632089e4d74512af564` |
| `detector/colab/run_d1_l4_capacity_r1.py` | `ee28c1f088732b205bf092d93023e81987d183fea3eb34e965595a92f28372a0` |
| `detector/colab/verify_d1_l4_capacity_r1.py` | `59d280670a598c56fe617e70651b5d156858ec4b13d57deacfd7af27c5182989` |
| `detector/tests/test_l4_capacity.py` | `6053d843b824c2ad0a1a2bf277271d5f4d7eb95aba4296bd380a2dd6cadaac43` |
| `tests/test_d1_l4_capacity_r1.py` | `ba7415529a4113e777c74c06d6c2c6a76accb62f9d92a0353dea8ccedcf556d4` |
| `docs/review/d1_l4_capacity_r1_implementation_record.md` | `0b571d40196ede01012681214b6d41bad16e4c5c3d908c1df76336c003aabf18` |

The pre-existing untracked Claude handoff and PM edits to `PROJECT_MEMORY.md` and
`docs/product_roadmap.md` were outside this QA scope and were not changed.

## Findings

### C-1 — A requested large batch can silently run at a smaller batch and still be selected

`run_d1_l4_capacity_r1.py:525-556` passes the requested batch to Ultralytics and treats a normal
return from `model.train()` as success. `StepTimer` records actual images but never requires a
full non-final batch to equal the requested batch. The result then retains the requested batch
identity at `:588-621`, and the standalone verifier only sums raw images/time at
`verify_d1_l4_capacity_r1.py:178-200`.

The pinned Ultralytics `8.4.172` implementation catches first-epoch CUDA/backend memory errors,
halves `self.args.batch` and `self.batch_size`, rebuilds the loader and retries up to three times
without propagating the exception (`ultralytics/engine/trainer.py:563-597`). Consequently a planned
batch 16 attempt can actually finish at batch 8, 4 or 2, remain `SUCCEEDED`, and contribute evidence
under the batch 16 label. A synthetic package whose planned batch-16 steps all contained four
images was accepted by the real standalone verifier.

This defeats the fixed plan, OOM classification, headroom comparison and selected final batch.

**Required repair:** fail immediately if the effective trainer batch differs from the planned
batch, record it explicitly in raw/result schemas, and make the independent verifier reject every
non-final measured step whose image count differs from the effective/planned batch. Disable or
fail-closed around Ultralytics auto batch reduction. Add a regression that simulates the pinned
first-epoch OOM-retry path and proves it cannot produce a successful planned-large-batch result.

### H-1 — The throughput timer excludes the data-loader wait while selecting `workers`

`StepTimer.on_start()` starts at `run_d1_l4_capacity_r1.py:354-355`. In the pinned Ultralytics
trainer, `for i, batch in self.train_loader` obtains the batch first and only then calls
`on_train_batch_start` (`ultralytics/engine/trainer.py:503-516`). The callback therefore begins
after the loader has yielded the batch. Time waiting for workers to decode/augment/load the next
batch is outside the recorded interval.

Because workers 4 versus 8 is an explicit selection dimension, the current metric cannot measure
the main effect it claims to compare. It can select workers using noise in compute-only timing
rather than end-to-end training throughput.

**Required repair:** measure a steady-state interval that includes iterator/data-loader wait,
preprocessing, forward, backward and optimizer work, while preserving exact actual image counts.
The test must inject different loader waits for workers 4 and 8 and demonstrate that the replayed
throughput changes accordingly.

### H-2 — The standalone verifier accepts a fully self-consistent forged package

`verify_plan()` validates the plan's self-hash, roster and profile but does not bind Git, model or
data to independent approved anchors. `verify_package()` rebuilds the report using the same
untrusted `plan["environment"]`, `plan["model"]`, `plan["data_contract"]` and `plan["git_commit"]`
at `verify_d1_l4_capacity_r1.py:309-315`. `_verify_train_args()` checks only a required subset and
allows extra behavior-changing fields.

Independent attack evidence built an exact 24-attempt package with:

- fake Git commit `ffff...ffff`;
- fake model path/hash;
- fake data YAML/export/class/split hashes;
- an extra `forged_extra_optimizer=SGD` train argument;
- batch-16 raw steps containing only four images.

After regenerating its self-hashes, SQLite, report, proposal, manifest and archive, the real
`verify_package()` returned:

```text
ATTACK_SELF_CONSISTENT_FORGED_PACKAGE=ACCEPTED
status=D1_L4_CAPACITY_R1_VERIFIED
attempts=24
sealed_test_accessed=false
```

**Required repair:** give the verifier independent expected anchors: reviewed release commit/source
hashes, approved pretrained model hash, detector lock, D-05 record, governed export/class/split
hashes and exact train-argument schema. Recompute those anchors from a supplied clean repository
checkout rather than copying them from the package being verified. Reject extra train arguments.
Add the self-consistent forged-package attack as an end-to-end negative test.

### H-3 — Generic failures can be relabelled as OOM in verified evidence

`l4_capacity.validate_repetition()` requires only `status=OOM`, `oom=true` and a non-empty error at
`detector/m1/l4_capacity.py:117-121`. It does not replay `_oom_error()` or require a typed failure
reason. The independent attack used `error="data loader failed"`; the production validator
accepted it:

```text
ATTACK_GENERIC_AS_OOM=ACCEPTED
```

This permits a generic failure to avoid the matrix's fail-fast rule and enter the aggregate as an
OOM candidate.

**Required repair:** store a controlled failure-kind plus exception type/message, validate it at
the attempt boundary, and independently replay the exact OOM predicate. Backend allocation errors
and true CUDA OOM must be explicitly enumerated; data/hash/loader/runtime errors must remain
`FAILED`. Add direct and full-package attacks.

### H-4 — SQLite attempt writes follow a substituted symlink

`record_attempt()` opens the database with `sqlite3.connect(path)` without rechecking the lexical
path, ancestors, file type, symlink state or hard-link count. Independent attack initialized the
governed database, replaced it with a symlink to an external SQLite file, then called the real
writer. It returned successfully and inserted one row into the external target:

```text
ATTACK_SQLITE_SYMLINK_EXTERNAL_WRITE=ACCEPTED
outside_attempt_rows=1
governed_is_symlink=true
```

The later package scan may reject the symlink, but that occurs after the external write and cannot
undo it.

**Required repair:** enforce lexical containment and component-wise `lstat()` immediately before
every SQLite open/write; require a regular single-link database and fail before connecting when it
has been replaced. Add root, ancestor, database-file symlink and hard-link substitution attacks
through the real CLI/writer.

### H-5 — Execution evidence accepts duplicate contradictory sealed-test keys

`verify_execution()` uses plain `json.loads` per JSONL row at
`verify_d1_l4_capacity_r1.py:251-260`, unlike the strict duplicate/non-finite parser used elsewhere.
The independent attack supplied both `"sealed_test_accessed": true` and
`"sealed_test_accessed": false` in each journal row. The last value won and the verifier accepted
the journal:

```text
ATTACK_DUPLICATE_SEALED_MARKER=ACCEPTED
```

The function also lacks exact row schemas and timestamp/chronology validation; arbitrary `x`/`y`
timestamps passed in the forged full package.

**Required repair:** use the strict duplicate/non-finite JSON decoder for every JSONL row, require
exact STARTED/SUCCEEDED schemas, UTC-aware timestamps and `started_at < finished_at`, exact boolean
`False`, and plan/report bindings. Add duplicate-key, non-finite, wrong-type, missing/extra-key and
chronology attacks.

## Controls that did pass

- Candidate grid is exactly `(4, 8, 12, 16) × (4, 8)` with three ordered repetitions: 24 entries.
- Missing, duplicate and reordered aggregate candidates are rejected.
- Three repetitions, CV ≤ 5%, sampled peak VRAM ≤ 80%, 95%-of-best tie window and deterministic
  batch/workers ordering are implemented.
- The live runner rechecks clean Git, environment, model and data before each candidate; H-2 is the
  independent package-verification gap, not absence of live preflight.
- Generic `FAILED` returned through the intended inner path stops the matrix; all completed OOM
  attempts can be retained.
- Static search found no `export-test`, `--final-eval`, test-export path or Pilot R3 import in the
  production source. The package is structurally separate from the current pilot.
- Plan, result, raw telemetry, report, selection, SQLite rows and archive members are hash-linked,
  subject to the trust/replay gaps above.
- The selection proposal remains `PROPOSAL_NOT_OWNER_APPROVED`.

## Mechanical and adversarial evidence

| Check | Result |
| --- | --- |
| Root targeted capacity tests | PASS, `11 passed, 1 skipped`; skip is root env without Torch |
| Detector capacity tests | PASS, `12 passed` |
| Complete detector tests | PASS, `105 passed` |
| Scoped Ruff for all reviewed source/tests | PASS |
| Root lock | PASS, `168 packages` |
| Detector lock | PASS, `66 packages` |
| `git diff --check` before this record | PASS |
| Graft freshness/source trace | PASS, graph in sync |
| Pinned Ultralytics readback | `8.4.172`; auto OOM reduction source confirmed |
| Generic error relabelled OOM attack | **ACCEPTED — blocker** |
| Duplicate sealed-marker journal attack | **ACCEPTED — blocker** |
| Self-consistent fake 24-attempt package | **ACCEPTED — blocker** |
| SQLite output-symlink external-write attack | **ACCEPTED — blocker** |

The repository-wide root test suite and verifier matrix were not run after the confirmed Critical
and High blockers. Green broad mechanical gates could not reverse this source verdict.

## Gate disposition

| Gate | Disposition |
| --- | --- |
| L4 capacity R1 source candidate | **FAIL** |
| Commit/push or notebook pin | **NO-GO** |
| Colab capacity execution | **NO-GO** |
| Capacity result/configuration selection | **NO-GO** |
| Owner final-config approval | **NO-GO pending repaired successor + QA** |
| Current Pilot R3 | Unchanged; continue independently |
| Sealed-test access/final evaluation | **NO-GO / not accessed** |

Repair must be append-only (for example R2), preserve this FAIL record and all R1 bytes/evidence,
add regression coverage for every accepted attack, and return to a separate independent QA session.
