# D1 final evaluation R1 — run attempt 1: preflight refusal before test access

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`).
Recorded by: Claude Code (Opus 5.5), coordinating session. Append-only once committed.
`sealed_test_accessed=false`.

## What was run

After the Owner opening approval was committed
(`docs/review/d1_final_evaluation_r1_owner_open_approval.md`, commit `8300bc9`, SHA-256
`3d10cacd0aebaad735b3260711a31d8b8d2c677ddf684459c7a83ec7976ad9da`), the coordinating session ran the
pinned command exactly once, from `detector/`:

```bash
PYTHONPATH=. uv run --no-sync python -m m1.d1_final_evaluation_r1 \
  --plan docs/review/generated/d1_final_evaluation_r1_plan.json
```

## Outcome

Exit code 1. The scorer's preflight raised an error in gate 1:
- `d1_threshold_lock_r3_successor.read_for_final` → `verify`;
- line 523: `RuntimeError: lock or proof binding differs`.

The log has 19 lines and ends with `EXIT=1`. It was kept in the session scratchpad, SHA-256
`91697d790b9eea40ed72c8cf9f22a827e71239c82ef79343f7d61c59b22dc4af`.

**The sealed test was not accessed:**
- `results/experiments/sealed_test_access_log.jsonl` does not exist, so no access event was logged;
- the output directory `results/experiments/d1_final_evaluation_r1` was not created;
- the error occurred before the latency step, the access-log append and the sealed roster loader.

The one-time rule is therefore **not** consumed.

## Root cause

- The R3 lock record stores the proof path as the string
  `../docs/review/generated/d1_threshold_lock_r1_r3_proof.json`. That path is relative to `detector/`,
  the working directory used when the lock was written.
- `verify` compares that string with `str(proof_path)`.
- The scorer passes `_relative(root, plan["lock_proof"]["path"])` with `root = contract.REPO_ROOT`.
  `REPO_ROOT` is `Path(__file__).resolve().parents[1].parent`, an **absolute** path. The two strings
  therefore never match.

The contract and its QA stated that "repo root = `..`" at execution. That statement is wrong:
`REPO_ROOT` is absolute. The scorer's synthetic tests used an injected reader, so they did not
exercise this path.

The coordinating session had reproduced the same mismatch earlier, when it checked the Owner lock
approval. Calling `read_for_final` with absolute paths failed with the same error. Calling it from
`detector/` with `../`-relative paths returned the selection for both seeds.

## Consequence

- The opening approval binds contract SHA-256
  `de92d8c61599e60989438765f372d8b4bbbb4d801b9f565a46dc69557f1f05d8`. It said that a refusal is
  recorded and nothing is retried with changed parameters without a new Owner decision.
- A fix changes the scorer source hash. That changes the plan, the contract and their QA, so a **new**
  Owner opening approval is required.
- The approved threshold lock, the Q4 decision and the label decision are unaffected.
