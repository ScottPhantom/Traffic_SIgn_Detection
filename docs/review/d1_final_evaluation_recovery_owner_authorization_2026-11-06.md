# D1 final evaluation — Owner authorization of the recovery package

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`).
Recorded by: Claude Code (Opus 5.5), coordinating session, on the Owner's instruction in chat.
Append-only once committed.

## Context

`docs/review/d1_final_evaluation_r2_run_attempt_2_open_logged_no_payload.md` (commit `477720d`) records
attempt 2:
- the one-time access event was appended at `20261106T231301`;
- the run then stopped because the test export `data/processed/m1_yolo/data_test.yaml` does not exist;
- no test image, label, prediction or result was read or produced.

## Owner decision (verbatim)

The coordinating session asked: "Do you approve a recovery package to finish test scoring, or stop and
present validation only?" The Owner answered: "Duyệt gói khôi phục".

## What is authorized now

Preparation only, with **no test access**:
1. **A scorer successor.** It must check that the test export exists (file presence of
   `data_test.yaml` only) **before** appending the access event. It must accept the single recorded
   attempt-2 event as a no-payload attempt, identified by:
   - action `d1-final-evaluation-r1-open`;
   - time `20261106T231301`;
   - contract `0f8bbf10…`;
   - access-log SHA-256 `ffef1b183ec8b4a20661c4bca71efa3cab64692c445432bc38eb3b3f2773b369` at the time
     of this record.

   It must refuse any other prior opening entry.
2. **An R3 final-evaluation contract and plan** with independent source and contract QA. The contract
   must pin the run sequence: the test export (`scripts/build_m1_yolo_dataset.py export-test
   --final-eval --reason …`, logged as `export-test`), then the scorer command.

## What still needs a separate Owner approval

The test export and the scorer run themselves. They will be authorized only by a new opening record
bound to the QA-passed R3 contract hash, given in a new chat approval.

## Unchanged

- The approved lock (`82e6b6f`), the Q4 gates (`8726d8c`) and the current-label decision (`00578c2`)
  stay in force. No threshold, gate, weight or label may change.
- The access log stays append-only and is never edited or deleted.
- The final report must disclose attempts 1 and 2. It must also give both FP verdicts (0.30 and 0.40)
  and the label asymmetry, and pass an independent result QA.
