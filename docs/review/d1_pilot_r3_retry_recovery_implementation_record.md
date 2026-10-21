# D1 Pilot R3 retry-recovery successor implementation record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: `IMPLEMENTED_LOCALLY_QA_PENDING_NO_RESUME_EXECUTION`  
Predecessor: immutable Pilot R2 at commit
`939f6bbce9f5c955b13ebcc84addd5083d242355`

## Incident reproduced

The live Pilot R2 checkpoint reached verified generation `epoch-0014`, but its append-only attempt
history contained the planned fresh pause followed by three recorded resume failures. The inherited
R4 validator requires exactly two attempts, so every later retry failed before training with:

`RuntimeError: resume R4 state requires exactly one fresh attempt`

The checkpoint itself remained recoverable. Re-hash verification covered `weights/last.pt`,
`weights/best.pt`, `results.csv`, `args.yaml` and `run_contract.json`; `latest.json` binds
generation `epoch-0014` to manifest SHA-256
`799ae7e21c99b65941a7c1124890dc5a1667f0645d55ed3de49fb667e459d670`.
`sealed_test_accessed=false` throughout.

## Append-only successor design

`detector/colab/run_d1_colab_pilot_r3.py` is a resume-only orchestration sidecar. It does not
modify any pinned R2 file. It deliberately executes outside the training checkout so that the
training repository remains clean and pinned to commit `939f6bb...`, which is part of the existing
checkpoint recovery binding.

The successor accepts only this ordered terminal history:

1. exactly one `fresh / PAUSED_FOR_RESUME` record;
2. zero or more `resume / FAILED` records with non-empty errors;
3. for final evidence, exactly one last `resume / SUCCEEDED` record.

Every record must retain the exact schema, UTC-aware non-overlapping chronology, common run binding,
common checkpoint binding and a valid hashed runtime identity. Every resume runtime must differ from
the fresh runtime; repeated retries on the same later runtime are permitted. The current recovery
pointer and all five checkpoint files are verified before delegation. A prior success, binding drift,
checkpoint drift, chronology overlap, malformed failure, training-checkout drift or dirty training
checkout fails closed.

The inherited Pilot R2 terminal guard remains active: only exact epoch 100 with status `COMPLETED` or
`COMPLETED_FROM_FINAL_CHECKPOINT` can be packaged as success. SQLite/text logging, archive creation,
checkpoint verification and the sealed-test marker remain inherited from the pinned runner chain.

Independent QA initially found that the candidate imported the predecessor module before checking
the training checkout. R3 Repair R1 now performs trusted lexical/no-symlink checks plus exact HEAD
and clean-worktree verification before any checkout import in `load_dependencies`, `main` and
`verify_live_state`. Regression attacks use wrong-commit, dirty and symlinked checkouts whose
predecessor module has a top-level marker side effect; every attack is rejected before the marker can
be created.

## Local verification so far

- Ruff: PASS for the R3 runner and test.
- R3 targeted tests: `12 passed, 1 skipped`; the skipped test is an optional non-committed Drive
  evidence fixture.
- Direct read-only validation of the live `execution_attempts.jsonl`: 4 records accepted as a retry
  prefix (one fresh pause plus three failed resumes), common run/checkpoint bindings, latest
  `epoch-0014`, `sealed_test_accessed=false`.

No Colab resume, upload, commit, push, sealed-test access, final evaluation or model acceptance is
claimed by this implementation record. Independent source QA is required before building and pinning
the R3 recovery notebook.
