# Codex handoff: R4 fix for the final scorer, validation rehearsal, R4 contract — 2026-11-07

- Writer: Claude, coordinating session.
- Branch `yolo11n-dual-track-r1`.
- Authority: `docs/review/d1_final_evaluation_r4_owner_authorization_2026-11-07.md`.
- Background: `docs/review/d1_final_evaluation_r3_run_attempt_3_scoring_crash.md`.
- The presentation is today, so prioritise correctness and go straight to the point.

## 0. Boundaries (most important)

- **DO NOT TOUCH THE TEST.** Do not run `export-test` or `execute` on the real plan. Do not read, list
  or hash anything under `data/processed/m1_yolo/images/test` or `labels/test`, or
  `data_test.yaml`.
- **Do not edit or delete** the access log. Before and after the work it must have SHA-256
  `a8f45f5092ff7c7f8dea66bde0620b9108d7f61174d885bb3c424a8cdf477e45` and exactly 3 lines.
- Do not change the lock, the proof, the lock successor, `contract.py`, the Owner records, or the
  R1–R3 contracts and approvals.
- Do not create an opening approval.
- No training, no push.
- Git: `git add` explicit paths only; keep the Owner's dirty files.
- Independent QA must come from a different agent, with exactly one `Verdict:` line.

## 1. Scorer successor (`detector/m1/d1_final_evaluation_r1.py`)

1. **Class map.** Do not call `int()` on `derived_key`. Sort by `yolo_id`, or by a stable key that
   handles `16:2.0`, `16:2.2`, `16:2.5`, `43:2.5`, `43:2.7`. Check every other place that assumes
   integer keys:
   - `CRITICAL_KEYS`;
   - `per_class_*`;
   - lines 500–502 and 754;
   - the Markdown report writer.
2. **Save predictions before scoring.** After each weight's prediction pass, write the raw predictions
   (stem, class, confidence, box) to `output_dir`, together with their SHA-256 and the weight hash,
   before calling `score_two_seeds`. If scoring fails, the files stay for diagnosis.
   - **Do not** add a path that scores from those files without a new Owner decision.
   - Write every output atomically, so no half-written result is left behind.
3. **Access history.** Accept exactly these 3 lines, pinned by the SHA-256 of each line:
   - the attempt-2 opening;
   - `export-test` at 2026-11-07T00:01:44+07:00;
   - the R3 opening at `20261107T000513`, line SHA-256
     `85d4a64c574cd906402a68c2e606d1bd1325c5f835fd212853faf5624d2155d1`.

   The new action is `d1-final-evaluation-r4-open`. Refuse any other history.
4. Move `CONTRACT_PATH` and the opening approval to R4 (`d1_final_evaluation_r4_contract.md`,
   `d1_final_evaluation_r4_owner_open_approval.md`). Keep `PACKAGE` and `OPEN_MARKER`.
5. **Tests:**
   - scoring on the **real** class map `docs/review/generated/m1_yolo_classes.csv` with synthetic
     predictions covering the 5 sub-class keys;
   - the prediction file exists after a scoring crash (inject a fault);
   - access history with exactly 3 lines → accepted;
   - access history with a missing line, an extra line, or an existing R4 action → refused;
   - all existing tests still pass.

## 2. End-to-end rehearsal on validation R3 (required, real weights, no test)

- Add a rehearsal entry point (a separate function or flag) that does all of the following:
  - runs the **same** code path as after the opening (load roster → predict both weights → save
    predictions → `score_two_seeds` → write JSON and Markdown);
  - uses the validation R3 roster (`tmp/yolo11n_n1_extract_r2`, 376 images, labels from the bundle)
    as the stand-in roster, with the locked setting conf 0.19 / class-aware NMS 0.70 and
    `imgsz=1280`;
  - writes to `results/experiments/d1_final_evaluation_r4_rehearsal_val/`;
  - **never** calls `_open_once` and never reads the test.
- Run it on MPS. It must finish with exit 0 and produce all output files.
- **Sanity check:** recall/FP at the operating point must match the lock (TP 555/512, FP 155/131;
  mean recall 0.85497, FP 0.38032), within a small MPS tolerance. If they differ significantly, STOP
  and report.
- Record the run in `docs/review/d1_final_evaluation_r4_val_rehearsal_record.md`, with output hashes.

## 3. QA and the R4 contract

1. Independent source delta QA: `docs/review/d1_final_evaluation_r4_source_delta_independent_qa_record.md`.
   QA reads the rehearsal outputs and checks the sanity numbers.
2. `docs/review/d1_final_evaluation_r4_contract.md` (marker `FINAL_EVALUATION_CONTRACT: APPROVED`, R4
   plan hash). Pin **only** the scorer command; export is not run again:
   ```bash
   cd detector/
   PYTHONPATH=. uv run --no-sync python -m m1.d1_final_evaluation_r1 \
     --plan docs/review/generated/d1_final_evaluation_r4_plan.json
   ```
   Also state in the contract:
   - attempts 1–3, including that attempt 3 made predictions on the test and lost them unseen;
   - the reporting obligations: both FP verdicts, the label asymmetry, disclosure of attempts 1–3;
   - independent result QA.
3. Independent contract QA: `docs/review/d1_final_evaluation_r4_contract_independent_qa_record.md`.
4. A real preflight-only check from `detector/` must stop at "Owner has not approved opening". The
   access-log hash must not change.
5. Commit after both QAs PASS. Report the commit SHA, the R4 contract SHA-256 and the plan reason.

## 4. STOP conditions

- Any step that needs to read the test.
- The access log changes.
- The rehearsal fails, or its numbers differ significantly from the lock.
- The fix would require changing a pinned file outside the scorer.
- QA does not PASS after two rounds.
