# D1 final evaluation — Owner authorization of the R4 fix package

Date: 2026-11-07 (`Asia/Ho_Chi_Minh`).
Recorded by: Claude Code (Opus 5.5), coordinating session, on the Owner's instruction in chat.
Append-only once committed.

## Context

`docs/review/d1_final_evaluation_r3_run_attempt_3_scoring_crash.md` (commit `4f27bc0`) records attempt 3:
- the test was exported and opened;
- both weights made predictions on it;
- `score_two_seeds` crashed on the non-integer class keys (`16:2.0`, …);
- no metric, verdict or prediction file exists, and no result was seen.

## Owner decision (verbatim)

The coordinating session asked: "Do you approve fixing the scorer (save predictions before scoring)
and predicting the test one more time?" The Owner answered: "Duyệt sửa R4".

## What is authorized now (preparation; no test access)

1. **A scorer successor that:**
   - handles the real class map, including the five sub-class keys;
   - writes each seed's raw test predictions and their SHA-256 to the output directory **before**
     scoring;
   - accepts the access-log history exactly as it stands: the attempt-2 opening, the `export-test`
     line, and the single R3 opening at `20261107T000513` (line SHA-256
     `85d4a64c574cd906402a68c2e606d1bd1325c5f835fd212853faf5624d2155d1`), and refuses anything else;
   - logs a new action for R4.
2. **An end-to-end rehearsal on validation R3 only**, with the two pinned weights and the locked
   setting. It runs the same predict → save → score → report code path on a validation roster, into a
   separate rehearsal directory, so no remaining crash can occur after the next real opening.

   This is new validation inference. The coordinating session included it in the R4 scope because
   attempt 3 shows that synthetic tests alone are not enough. It never touches the test.
3. **An R4 contract and plan** with independent source and contract QA.

## What still needs a separate Owner approval

The real R4 run, one more prediction pass on the already exported test. It needs a new opening record
bound to the QA-passed R4 contract hash and a new chat approval. The test export is **not** run again.

## Unchanged

- The lock (`82e6b6f`), Q4 (`8726d8c`) and current-label (`00578c2`) decisions stay in force.
- No threshold, gate, weight or label may change.
- The access log stays append-only.
- The final report must:
  - disclose attempts 1, 2 and 3, including that attempt 3 ran a full prediction pass on the test
    whose output was lost unseen;
  - give both FP verdicts (0.30 and 0.40) and the label asymmetry;
  - pass an independent result QA.
