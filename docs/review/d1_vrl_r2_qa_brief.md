# D1-VRL-R2 — brief for the independent QA session

Give this brief to a fresh session that did not author D1-VRL-R2. Write the result to a new file
`docs/review/d1_vrl_r2_independent_qa_record.md`. Do not modify any other file. Do not commit,
push, train, run inference or open the sealed test. Do not run `build`. Do tampering attacks on a
staged copy outside the repository.

## Package

- Builder: `detector/m1/val_relabel_r2.py` (run `verify` from `detector/`).
- Tests: `detector/tests/test_val_relabel_r2.py`.
- Predecessor QA (FAIL): `docs/review/d1_vrl_r1_independent_qa_record.md`.
- H1 correction and owner re-decision: `docs/review/d1_vrl_r1_correction_r1.md`.
- Trusted notes, with eye estimates for hand boxes: `docs/review/d1_vrl_r2_box_review_notes.csv`.
- Implementation record: `docs/review/d1_vrl_r2_implementation_record.md`.
- Outputs:
  - `docs/review/generated/d1_vrl_r2_{added_boxes,ignore_regions}.csv`;
  - `docs/review/generated/d1_vrl_r2_manifest.json`;
  - `docs/review/d1_vrl_r2_report.md`;
  - `data/processed/m1_yolo_val_vrl_r2/`;
  - the atlas `docs/review/assets/d1_vrl_r2/` (4 pages).

## Checks to perform

1. **Pins and the owner rule.**
   - Check every pin, including the R4 val `labels_sha256` `e64345bb…`.
   - Check that the 40 ignore regions are exactly the proposals with locator ≤ 17.5 px, and that
     every other proposal is added.
   - Check that the correction record states the H1 premise truthfully.
2. **Hand-drawn geometry (38).**
   - Read the atlas and the raw frames.
   - Independently re-draw at least 12 boxes, including R047, R048, R050–R052, R039, R045, R046
     and R090/R091.
   - Report boxes off by more than 2 px on a side; for 1823/1824, more than 3 px.
   - Check the class of each hand-drawn box against the sign. The class came from D1-VLA-R1 and is
     unchanged.
3. **Independence.** Judge whether the eye → snap procedure kept the hand boxes independent of the
   model box:
   - compare the eye estimates with the final boxes and with the locators;
   - check that no hand box equals its locator.
4. **L1.**
   - Check the three tightened boxes.
   - Check the author's evidence for keeping R092.
5. **L2–L4.**
   - The report's geometry statement.
   - `stray_paths` across the whole derived root.
   - The non-vacuous mapping test.
6. **Derived labels and diagnostic.**
   - The labels are R4 plus exactly the 64 lines.
   - Recompute 214 → 150 → 110 FP yourself.
   - Confirm that the report separates the independent part (150) from the circular ignore part
     (40), and labels it diagnostic only.
7. **Verifier, tests and tampering.**
   - `verify` is valid and the tests pass.
   - Run at least six attacks, including: a note decision flipped across the 17.5 px rule, an
     adjusted box loosened, a stray file in `labels/train/`, an edited R4 label, a byte flip in an
     atlas page, and a manifest boundary flag set to true.
8. **Boundary.** `evaluation_authority=false`, `gates_changed=false`, `sealed_test_accessed=false`.

Classify findings Critical / High / Medium / Low and give a PASS or FAIL verdict.
