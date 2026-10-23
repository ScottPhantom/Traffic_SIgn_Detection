# D1-VRL-R3 — brief for the independent QA session

Give this brief to a fresh session that did not author D1-VRL-R3. Write the result to a new file
`docs/review/d1_vrl_r3_independent_qa_record.md` and modify no other file. Run scripts with their
output in your own scratchpad, and do tampering attacks on a staged copy outside the repository.
Do not run `build`, commit, push, train, run inference or open the sealed test.

## Package

- Builder: `detector/m1/val_relabel_r3.py`. Run `verify` from `detector/`.
- Tests: `detector/tests/test_val_relabel_r3.py`.
- Predecessor QA (PASS, with M1): `docs/review/d1_vrl_r2_independent_qa_record.md`.
- Owner decision: `docs/review/d1_vrl_r2_owner_decision_r3.md`.
- Trusted notes: `docs/review/d1_vrl_r3_box_review_notes.csv`.
- Implementation record: `docs/review/d1_vrl_r3_implementation_record.md`.
- Outputs:
  - `docs/review/generated/d1_vrl_r3_{added_boxes,ignore_regions}.csv`;
  - `docs/review/generated/d1_vrl_r3_manifest.json`;
  - `docs/review/d1_vrl_r3_report.md`;
  - `data/processed/m1_yolo_val_vrl_r3/`;
  - the atlas `docs/review/assets/d1_vrl_r3/`.

## Checks to perform

1. **Pins and delta.**
   - Check every pin.
   - Confirm that, against D1-VRL-R2, the only box changes are R039 x1 0 → 6 and R046 y2 23 → 28.
   - Confirm that the notes differ from R2 only in those two rows and in the re-quoted R097 note.
   - Confirm that the ignore regions are byte-identical to R2.
2. **Geometry.** From the raw frames, independently re-measure:
   - R039 (left edge) and R046 (bottom edge);
   - R045 as the consistency reference for drawing through the bracket.

   Report any side off by more than 2 px.
3. **L3 check.**
   - Confirm `check_notes` refuses: missing or non-integer eye columns; a hand box more than 1 px
     from its eye estimate; any departure on 1823–1837; and a wrong field count.
   - Judge whether recording the R3 re-draw as the eye estimate for R039 and R046 is disclosed
     honestly and is acceptable.
4. **Author-found defect.** Confirm that the R2 R097 note was malformed (15 fields) and that no R2
   number depended on it.
5. **Derived labels and diagnostic.**
   - The labels are R4 plus exactly 64 lines.
   - Recompute 214 → 150 → 110 FP.
   - The report separates the independent and circular parts, and calls the table a diagnostic.
6. **Verifier, tests and tampering.**
   - `verify` is valid and the tests pass.
   - Run at least six attacks, including:
     - R039 reverted to x1 = 0 with the module re-pinned (L3 rule);
     - an eye column removed;
     - an unquoted comma in a note;
     - a stray file under the derived root;
     - an edited R4 label;
     - a manifest boundary flag set to true.
7. **Boundary.** `evaluation_authority=false`, `gates_changed=false`, `sealed_test_accessed=false`.

Classify findings Critical / High / Medium / Low and give a PASS or FAIL verdict.
