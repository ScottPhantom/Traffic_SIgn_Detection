# Codex handoff: fix the lock-proof path binding in the final scorer, then re-prepare the R2 contract — 2026-11-06

- Writer: Claude, coordinating session.
- Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, branch `yolo11n-dual-track-r1`.
- Background: `docs/review/d1_final_evaluation_r1_run_attempt_1_preflight_refusal.md`.
  - The first real run stopped at preflight gate 1 with "lock or proof binding differs".
  - The sealed test was **not** accessed: there is no access log and no output directory.

## 0. Boundaries (unchanged, most important)

- **Do not open the test.**
  - Do not run `m1.d1_final_evaluation_r1` without `preflight` only.
  - Do not call `execute`, the roster loader, `export-test`, or anything that touches `afa03d4b…`.
  - `results/experiments/sealed_test_access_log.jsonl` must still not exist when you finish.
- **Do not change** the lock record, the proof, the lock successor, `contract.py`, or the Owner
  decision records (lock approval, Q4, labels).
- **Do not change** `docs/review/d1_final_evaluation_r1_contract.md` or the R1 opening approval. They
  are committed and append-only.
- Do not create an Owner opening approval.
- No training, no inference, no push.
- Git: `git add` explicit paths only. Keep the Owner's dirty files.
- Independent QA must come from a different agent or session, with exactly one `Verdict:` line.

## 1. Scorer fix (append-only successor of the source)

In `detector/m1/d1_final_evaluation_r1.py`, preflight passes the lock and proof as absolute paths. The
lock stores `../docs/...`, so the strings differ. The fix:
- Before calling the reader, read `record["proof"]["path"]` from the lock record.
- Check that this path, resolved against the **current working directory**, is the same file as
  `root / plan["lock_proof"]["path"]` (use `samefile` and the hash).
- If it is, pass the lock and proof to the reader as paths relative to the CWD, so the strings match
  what the lock stores. If it is not, refuse.
- Require CWD `== REPO_ROOT / "detector"`; refuse otherwise.
- Check the bundle the same way: in my manual check the reader passed with the relative bundle
  `../tmp/yolo11n_n1_extract_r2`. Find out whether the absolute bundle path also passes; if not, pass
  it relative to the CWD too.

**Move the hard-coded paths to R2**, because the R1 files may not be edited:
- `CONTRACT_PATH` → `docs/review/d1_final_evaluation_r2_contract.md`;
- the plan's `owner_open_approval` → `docs/review/d1_final_evaluation_r2_owner_open_approval.md`.

Keep the `PACKAGE` value unless the access log or Q4/label records require a new one. The Q4 and label
JSON files say `D1-FINAL-EVALUATION-R1`. If the package changes, those records no longer match, so
**keep `PACKAGE` unchanged**.

Tests:
- add a test that uses the **real** reader (not an injected reader) on a synthetic lock written with
  `../` paths and CWD = `detector/`; it must pass;
- the same test with a different CWD must refuse;
- the existing 21 tests must still pass.

## 2. Real dry-run check of preflight (required, no test access)

Write a new plan `docs/review/generated/d1_final_evaluation_r2_plan.json` (new source hash, same weights,
lock, Q4 and labels). From `detector/`, call **only** `preflight(plan_path)` on the real files.

It is expected to pass gate 1 (the R3 lock reader returns conf 0.19 / NMS IoU 0.70 for both seeds) and
then stop at the "final contract is absent" or "Owner has not approved opening" gate. Record the exact
error message. That proves every gate before opening works on real data.

Before and after the call, confirm that `results/experiments/sealed_test_access_log.jsonl` does not
exist.

## 3. QA and the R2 contract

1. Independent source delta QA of the fix:
   `docs/review/d1_final_evaluation_r2_source_delta_independent_qa_record.md`. QA reruns the dry-run
   check from step 2 itself.
2. Write `docs/review/d1_final_evaluation_r2_contract.md` as the successor of R1:
   - keep the content, with the `FINAL_EVALUATION_CONTRACT: APPROVED` marker and the R2 plan hash;
   - fix the wrong sentence "repo root = `..`": `REPO_ROOT` is absolute, and CWD must be `detector/`;
   - cite the attempt-1 refusal record;
   - keep the post-run reporting obligations (both FP verdicts 0.30 and 0.40, label asymmetry,
     result QA).
3. Independent contract QA: `docs/review/d1_final_evaluation_r2_contract_independent_qa_record.md`.
4. Commit after both QAs PASS. Report the commit SHA, the contract SHA-256 and the plan reason so the
   Owner can approve opening again.

## 4. STOP conditions

- Any step that needs to read the test.
- The fix would require changing the lock, the proof, the lock successor or an Owner record.
- The real dry run does not get past gate 1.
- QA does not PASS after two rounds.
