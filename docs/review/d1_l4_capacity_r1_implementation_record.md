# D1 L4 capacity successor R1 — implementation record

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
Status: **IMPLEMENTED SOURCE CANDIDATE — AWAITING INDEPENDENT QA**  
Authorization boundary: no Colab execution, upload, commit, push, model selection, sealed-test
access or final-training authorization is created by this record.

## Purpose

The running 100-epoch Pilot R3 remains an evidence-producing pilot at its existing immutable
configuration. R1 is a separate, append-only successor package for measuring how an idle NVIDIA
L4 handles the governed D1 train/val workload before the three final seeds. It does not modify,
resume, accelerate or otherwise compete with the live pilot.

The package answers one operational question only: which reviewed `batch × workers` configuration
provides near-best measured training throughput while retaining at least 20% observed L4 VRAM
headroom? It does not compare detector quality and cannot approve a model.

## Implemented source surface

| File | Role |
| --- | --- |
| `detector/m1/l4_capacity.py` | Fixed experiment design, strict schemas, aggregate replay, stability/headroom gates and deterministic selection proposal. |
| `detector/colab/run_d1_l4_capacity_r1.py` | Idle-L4 preflight, frozen plan, isolated candidate subprocesses, raw timing/GPU telemetry, SQLite/text/execution evidence and archive packaging. |
| `detector/colab/verify_d1_l4_capacity_r1.py` | Standalone replay of all raw attempts, database, report, proposal, manifest and archive. |
| `detector/tests/test_l4_capacity.py` | Selection-policy and semantic-tamper tests. |
| `tests/test_d1_l4_capacity_r1.py` | Runner/path/journal/database/packaging tests. |

No predecessor runner, notebook, pinned QA record or live Drive artifact was edited.

## Frozen capacity design

- Candidate batches: `4, 8, 12, 16`.
- Data-loader workers: `4, 8`.
- Repetitions: exactly `3` per pair, in the frozen ordered roster; 24 isolated subprocesses.
- Per repetition: one epoch, `fraction=0.25`, `imgsz=1280`, seed `20261018`, deterministic mode,
  AMP enabled, validation disabled, checkpoint saving disabled and `fliplr=0.0`.
- First 10 observed train batches are warm-up; the result records actual images and measured batch
  seconds after warm-up rather than assuming a full nominal batch.
- GPU telemetry records the exact GPU UUID, utilization, used/total VRAM, power and temperature.
- Generic failures remain `FAILED`; only a PyTorch OOM type or explicit `CUDA out of memory`
  message may become `OOM`.
- A successful candidate must have three successful repetitions, at least 10 measured batches and
  three GPU samples per repetition, and throughput coefficient of variation at most 5%.
- Eligible candidates must use at most 80% peak VRAM. Selection keeps candidates within 95% of the
  best median images/second, then chooses the smaller batch, fewer workers and finally lower VRAM.

The frozen plan binds exact Git commit, clean worktree, detector lock/environment, model hash,
train/val data contract, L4 UUID and the complete 24-attempt roster before the first attempt starts.

## Evidence and fail-closed behavior

Each repetition writes immutable raw telemetry and a result file. The orchestrator appends every
attempt to SQLite, writes a text log and uses an append-only execution journal with terminal
`SUCCEEDED` or `FAILED`. A generic failure ends the matrix rather than being hidden or reclassified.
Successful completion emits:

- `capacity_report.json`, rebuilt from all 24 raw attempts;
- `capacity_selection_proposal.json` with status `PROPOSAL_NOT_OWNER_APPROVED`;
- `capacity_evidence_manifest.json` and `capacity_evidence.tar.gz`;
- SQLite, text log, execution journal and every per-attempt raw/result file.

The standalone verifier replays raw step timing, GPU summaries, repetition aggregates, the fixed
grid, deterministic selection, SQLite rows, terminal execution, manifest hashes and each archive
member. Writable paths use lexical ancestor checks and reject symlinks/overwrites. The runner has
no test-export or final-evaluation route; every layer records `sealed_test_accessed=false`.

## Current gates and next actions

1. Source-level targeted tests and lint must pass.
2. A separate QA session must attack the actual R1 source and issue PASS or a successor repair.
3. After QA PASS, Owner must explicitly authorize commit/push and the later Colab capacity run.
4. The capacity run must wait for the current 100-epoch pilot to release its L4. Running both on
   the same runtime would invalidate throughput and VRAM evidence.
5. Any measured selection remains a proposal. Owner approval and a new configuration-bound
   two-runtime checkpoint/resume smoke are required before the three final seeds.

The notebook is intentionally not created or pinned in this uncommitted source candidate: its
source commit must be a clean reviewed commit. No current pilot notebook is reused or changed.
