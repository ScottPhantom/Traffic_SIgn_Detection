# Codex handoff: final evaluation recovery package (R3) — 2026-11-06

- Writer: Claude, coordinating session.
- Branch `yolo11n-dual-track-r1`.
- Authority: `docs/review/d1_final_evaluation_recovery_owner_authorization_2026-11-06.md`.
- Background: `docs/review/d1_final_evaluation_r2_run_attempt_2_open_logged_no_payload.md`.

## 0. Boundaries (most important)

- **DO NOT OPEN THE TEST.**
  - Do not run `export-test`.
  - Do not call `execute` or `_real_test_roster`.
  - Do not list, read or hash anything under `data/processed/m1_yolo/*/test` or the raw test images.
  - Only `preflight` and synthetic tests may run.
- **Do not edit, delete or rename** `results/experiments/sealed_test_access_log.jsonl` or its `.lock`.
  Before and after the work, its SHA-256 must be
  `ffef1b183ec8b4a20661c4bca71efa3cab64692c445432bc38eb3b3f2773b369`, with exactly 1 line.
- **Do not change:** the lock, the proof, the lock successor, `contract.py`, the Owner records, the R1
  and R2 contracts, or the R1 and R2 opening approvals.
- Do not create an opening approval.
- No training, no inference on real weights, no push.
- Git: `git add` explicit paths only; keep the Owner's dirty files.
- Independent QA must come from a different agent, with exactly one `Verdict:` line.

## 1. Scorer successor (`detector/m1/d1_final_evaluation_r1.py`, new hash)

1. **Check the export before opening.** In preflight, or immediately before `_open_once`, check that
   `contract.EXPORT_DIR / "data_test.yaml"` exists (file presence only, no read). If it is missing,
   refuse **before** appending the access event.
2. **Accept attempt 2 exactly once.** In both preflight and `_open_once`, the opening entries in the
   log must be either:
   - empty; or
   - exactly the single attempt-2 entry. Pin it by the SHA-256 of its exact JSON line (or by its
     `time` `20261106T231301` plus the R2 plan and contract SHA-256 that it contains).

   Refuse any other entry, any second opening entry, and any entry of the R3 package itself.

   The new access event should use **a new action**, for example `d1-final-evaluation-r3-open`, so
   that a later R3 run counts as the real one-time opening. `export-test` entries (written by
   `build_m1_yolo_dataset.py`) are allowed.
3. Move `CONTRACT_PATH` to `docs/review/d1_final_evaluation_r3_contract.md`. The plan's opening
   approval becomes `docs/review/d1_final_evaluation_r3_owner_open_approval.md`. Keep `PACKAGE`
   (`D1-FINAL-EVALUATION-R1`) and `OPEN_MARKER` so the Q4 and label records stay valid.
4. **Synthetic tests:**
   - missing export → refused, and the access log is unchanged;
   - a log with exactly the attempt-2 entry → accepted;
   - a log with a different opening entry, or two entries → refused;
   - a log that already contains the R3 action → refused;
   - all existing tests still pass.

## 2. Check that `export-test` cannot break validation (static, without running it)

Read `scripts/build_m1_yolo_dataset.py`, in particular `materialise(..., ("test",))`. Confirm in
writing:
- it does not delete or overwrite `data.yaml` or the train/val images and labels;
- it writes `data_test.yaml`;
- it appends an `export-test` line to the same access log **before** materialising.

If it would overwrite train/val data or `data.yaml`, STOP and report.

## 3. Real preflight dry run (no test access)

Create `docs/review/generated/d1_final_evaluation_r3_plan.json`. From `detector/`, call **only**
`preflight` on the real files:
- Because the export does not exist yet, it must stop at the new export check, or at "Owner has not
  approved opening".
- Record the exact error message.
- Confirm that the access-log hash has not changed.

## 4. QA and the R3 contract

1. Independent source delta QA: `docs/review/d1_final_evaluation_r3_source_delta_independent_qa_record.md`.
   QA reruns the dry run itself.
2. `docs/review/d1_final_evaluation_r3_contract.md` (marker `FINAL_EVALUATION_CONTRACT: APPROVED`, R3
   plan hash). Pin the run sequence, from the checkout root:
   ```bash
   uv run --no-sync python scripts/build_m1_yolo_dataset.py export-test --final-eval \
     --reason "<plan reason>"
   cd detector/
   PYTHONPATH=. uv run --no-sync python -m m1.d1_final_evaluation_r1 \
     --plan docs/review/generated/d1_final_evaluation_r3_plan.json
   ```
   Check whether the export command needs `--raw-root` or `--wp35-root`. The defaults are
   `data/raw/DATASET01/staging/052bc980a7206f8d/raw` and `data/processed/wp35_enrichment`; checking
   that the folders exist is enough. Also state in the contract:
   - attempts 1 and 2;
   - CWD = `detector/` for the scorer;
   - the post-run reporting obligations: both FP verdicts, the label asymmetry, and the disclosure of
     attempts 1 and 2;
   - independent result QA.
3. Independent contract QA: `docs/review/d1_final_evaluation_r3_contract_independent_qa_record.md`.
4. Commit after both QAs PASS. Report the commit SHA, the R3 contract SHA-256 and the plan reason.

## 5. STOP conditions

- Any step that needs to read the test.
- The access-log hash changes.
- `export-test` would overwrite train/val data.
- The fix would require changing a pinned file outside the scorer.
- QA does not PASS after two rounds.
