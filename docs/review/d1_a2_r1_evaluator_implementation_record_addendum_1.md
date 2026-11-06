# D1-A2-R1 evaluator implementation record — addendum 1 (after independent source QA)

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`) · Author: Claude Code (Opus 5.5), coordinating session.
Append-only. Does not edit `d1_a2_r1_evaluator_implementation_record.md`
(SHA-256 `dab36b1fb1b25492456baddd752e220f2d583b4d7954a357254a5ba26465664a`) or any reviewed source.
Responds to `d1_a2_r1_evaluator_source_independent_qa_record.md`
(SHA-256 `1ec37fc3fc3c0507dcef3b922cf69c7f51a5ddb9bf3d0e117004b12075184be5`, PASS giới hạn).
`sealed_test_accessed=false`. No source file is changed by this addendum.

## M1 — corrected morning evaluator command (replaces the first command of record §5)

`detector/pyproject.toml` sets `package = false`. Running the script directly puts `colab/` on the
path, not `detector/`, so `m1` does not import. Always pass `PYTHONPATH=.`:

```bash
cd detector
PYTHONPATH=. uv run --no-sync python colab/evaluate_d1_a2_r1_common_r1.py \
  --bundle ../tmp/yolo11n_n1_extract_r1 \
  --state "<STATE>" \
  --archive "<ARCHIVE>" --archive-sha256 <ARCHIVE_SHA> \
  --manifest "<MANIFEST>" --manifest-sha256 <MANIFEST_SHA> \
  --owner-authorization-sha256 <AUTH_SHA> \
  --expected-checkout <CHECKOUT> \
  --output-dir ../results/experiments/d1_a2_seed_20261018_r1/evaluation_common_r1 \
  --device mps
```

Leave the two paired-CI commands as they are. They use `python -m` and already resolve `m1`, but
`PYTHONPATH=.` is harmless to add.

## M2 — scope of accepted archives

The evaluator accepts only the standard A2 package: one fresh pause and one successful resume,
schema v2, produced by the A2 launcher's own packaging shim. A process kill on Colab records no
attempt, so a second resume still yields two attempts and stays accepted.

If packaging fails on Colab and the result has to be salvaged with a repair packager (as A3 did with
`package_d1_a3_r2_result_r1.py`, schema 3, three attempts), **this evaluator will refuse it, by
design.** That case needs a new append-only evaluator successor with its own independent source QA.
Do not loosen this one.

## Low findings

L1–L7 are accepted as recorded in the QA record and deferred to any successor. For L1 (the
unpinned predecessor chain), the A2 result QA must record the SHA-256 of `contract.py`,
`metrics.py`, `evaluate_cascade_b0_r1.py`, `run_yolo11n_n1_r1.py` and the launcher chain as found
at scoring time.

## Classification

- Verified current behavior: the M1 failure and fix, as reproduced by the QA probe.
- Proposal: the M2 successor path, needed only if a repair packager is used.
