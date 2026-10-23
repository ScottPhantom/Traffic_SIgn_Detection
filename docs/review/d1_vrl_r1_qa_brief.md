# D1-VRL-R1 — brief for the independent QA session

Give this brief to a fresh session that did not author D1-VRL-R1. Write the result to a new file
`docs/review/d1_vrl_r1_independent_qa_record.md`. Do not modify any other file. Do not commit,
push, train, run inference or open the sealed test. Do not run `build`.

## Package

- Builder: `detector/m1/val_relabel_r1.py` (run `verify` from `detector/`).
- Tests: `detector/tests/test_val_relabel_r1.py`.
- Owner scope and geometry decision: `docs/review/d1_vrl_r1_owner_scope_record.md`.
- Trusted box notes: `docs/review/d1_vrl_r1_box_review_notes.csv`.
- Implementation record: `docs/review/d1_vrl_r1_implementation_record.md`.
- Outputs: `docs/review/generated/d1_vrl_r1_{added_boxes,ignore_regions}.csv`,
  `docs/review/generated/d1_vrl_r1_manifest.json`, `docs/review/d1_vrl_r1_report.md`, the derived
  labels `data/processed/m1_yolo_val_vrl_r1/` and the atlas `docs/review/assets/d1_vrl_r1/`.

## Checks to perform

1. **Pins and scope.** Check every pin. Check that the notes follow the owner decision (72 small +
   6 partial → ignore; 26 accepted) and that no LOW, UNCLEAR or out-of-taxonomy item is added.
2. **Box geometry.** Read both atlas pages and the raw frames where needed. For each of the 26 added
   boxes judge whether it is tight on the sign (report boxes off by > 2 px or covering only part of
   it). For the 6 rejected re-fits (R040, R042, R044, R049, R090, R091) judge whether rejection was
   right. Spot-check at least 10 of the 72 non-refitting proposals.
3. **Independence.** Confirm the 26 boxes come from pixels, not from the model box (re-run
   `refine_box` yourself or write your own fitting), and that the report states the 78-FP ignore
   drop is circular by construction.
4. **Class ids.** Check the derived-key → YOLO-id mapping (keys 23/39/41 → 25/40/42).
5. **Derived labels.** Check that the 376 derived files equal the R4 labels plus exactly the 26
   lines, and that R4, raw, train and test labels are unchanged.
6. **Diagnostic.** Recompute 214 → 188 → 110 FP with your own script; check the ignore rule
   (≥ 50 % of prediction area, 25 % margin) and that the report labels it diagnostic only.
7. **Verifier and tests.** `uv run python -m m1.val_relabel_r1 verify` is `valid=true`; tests pass;
   on a staged copy run at least four tampering attacks (edit a note, edit a derived label file, add
   a stray file to the derived label dir, flip a byte of an atlas page) and confirm each fails
   closed.
8. **Boundary.** `evaluation_authority=false`, `gates_changed=false`, `sealed_test_accessed=false`.

Classify findings Critical / High / Medium / Low and give a PASS or FAIL verdict.
