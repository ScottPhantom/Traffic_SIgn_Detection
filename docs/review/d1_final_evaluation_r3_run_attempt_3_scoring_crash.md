# D1 final evaluation — run attempt 3 (R3): test opened and predicted, scoring crashed, no result

Date: 2026-11-07 (`Asia/Ho_Chi_Minh`).
Recorded by: Claude Code (Opus 5.5), coordinating session. Append-only once committed.

## What was run

The run followed the R3 Owner opening approval (`docs/review/d1_final_evaluation_r3_owner_open_approval.md`,
commit `fcfb84c`) and the pinned two-command sequence.

1. **Test export.**
   - Command: `export-test --final-eval --reason "<plan reason>"`.
   - Exit 0, status `EXPORTED`, `verified: true`, `written: {"test": 903}`.
   - It appended one `export-test` access line at `2026-11-07T00:01:44+07:00`.
   - Log in the session scratchpad, SHA-256
     `0f9d9a89dbb6967a4b696068d38e7dee6e9252ea862ba743b3ca6eaaf72ac7ab`.
2. **R3 scorer, from `detector/`.**
   - It passed preflight, the validation-only latency step and the repeated preflight.
   - It appended `d1-final-evaluation-r3-open` at `20261107T000513`, loaded the test roster and ran the
     prediction pass for both weights.
   - It then raised an error in `score_two_seeds` (line 632):
     `ValueError: invalid literal for int() with base 10: '16:2.0'`.
   - Exit 1. The run log is in the session scratchpad: 18 lines, traceback only, SHA-256
     `ba05eb71da3b0475215aff467f90dfa0d99da7d7ef9087058231eb38a8fc4e98`.

## State after the run

- Access log `results/experiments/sealed_test_access_log.jsonl`: 3 lines (attempt-2 opening,
  `export-test`, R3 opening). SHA-256 `a8f45f5092ff7c7f8dea66bde0620b9108d7f61174d885bb3c424a8cdf477e45`.
- **The sealed test was opened and both models made predictions on it.** This is the real one-time
  opening of the R3 package.
- **No test metric, verdict or prediction file exists.**
  - The predictions lived in memory only and were lost when the process exited.
  - The output directory `results/experiments/d1_final_evaluation_r1` was not created.
  - The log prints no number.
- Nobody, the coordinating session included, has seen any test result.
- The test export now exists under the Git-ignored `data/processed/m1_yolo/` (`images/test`,
  `labels/test`, `data_test.yaml`).

## Root cause

- `score_two_seeds` sorts `contract.class_ids()` with `int(key)`.
- The real class map `docs/review/generated/m1_yolo_classes.csv` has five non-integer derived keys:
  `16:2.0`, `16:2.2`, `16:2.5`, `43:2.5`, `43:2.7` (height-limit sub-classes).
- The synthetic tests used integer keys only, and the source and contract QAs did not run the scoring
  function against the real class map.
- The scorer also scored in memory without first saving predictions, so a scoring bug loses the whole
  prediction pass.

## Consequence

- The scorer now refuses any further run, because the R3 action exists.
- Producing a result needs a new Owner decision and a successor that:
  - fixes the class ordering (for example, sort by YOLO id);
  - is tested on the real class map;
  - writes the raw predictions to disk before scoring;
  - accepts exactly this one R3 event as a no-result attempt.
- The thresholds, gates, weights and labels stay fixed, and no result has been seen, so re-running the
  same prediction pass cannot be used to tune anything. It is still a second prediction pass on the
  test and must be disclosed.
- The alternative is to stop and report that the final evaluation produced no result.

Every final report must disclose attempts 1, 2 and 3.
