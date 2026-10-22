# D1-VLA-R1 — brief for the independent QA session

Give this brief to a fresh session that did not author D1-VLA-R1. Write the result to a new file
`docs/review/d1_vla_r1_independent_qa_record.md`. Do not modify any other file. Do not commit,
push, train, run inference or open the sealed test. Do not run `build`.

## Package

- Builder: `detector/m1/val_label_audit_r1.py` (run `verify` from `detector/`).
- Tests: `detector/tests/test_val_label_audit_r1.py`.
- Trusted notes: `docs/review/d1_vla_r1_review_notes.csv`.
- Implementation record: `docs/review/d1_vla_r1_implementation_record.md`.
- Outputs:
  - `docs/review/generated/d1_vla_r1_{background_fp_strata,decisions,proposed_val_labels}.csv`;
  - `docs/review/generated/d1_vla_r1_manifest.json`;
  - `docs/review/d1_vla_r1_report.md`;
  - the atlas `docs/review/assets/d1_vla_r1/` (12 pages).

## Checks to perform

1. **Pins.** Check the pins, including the D1-EA-R1 manifest anchor `d87f090e…`.
2. **Strata.** With your own script, recompute the four strata of the 214 background false
   positives (66 / 10 / 138, and 0 partial overlaps) from the D1-EA-R1 prediction CSV and the
   labels.
3. **Decisions.** Read all 12 review pages, then the raw frames where needed, and judge every one
   of the 138 decisions and every proposed class independently. Report disagreements with the
   review id. Pay particular attention to:
   - the 1208–1229 and 1342–1357 pole classes 10, 23, 39 and 41, including the claim that the
     left disc reads 40 and the right disc reads 60;
   - the 1823–1837 shadow run, decided as P.130;
   - the camera boards: UNKNOWN-labelled versus unlabelled, recomputed with the WP38 rotation for
     stems 1319–1357;
   - the class-14 "3.5t" truck disc;
   - the LOW triangles in 1352–1357.
4. **Duplicates and what-if.** Re-derive the duplicate merges (4), the 104 proposals and the
   what-if table (FP 110, FP/image 0.293, recall 0.884). Check that the report presents them as
   diagnostic only.
5. **Verifier and tests.**
   - `uv run python -m m1.val_label_audit_r1 verify` returns `valid=true`.
   - The tests pass.
   - On a staged copy, run at least four tampering attacks and confirm each fails closed: edit a
     note, edit the proposals CSV, flip a byte of an atlas page, and append to a pinned D1-EA-R1
     file.
6. **Boundary.** Confirm that no validation relabel, gate change or training use occurs, and that
   `sealed_test_accessed=false`.

Classify findings Critical / High / Medium / Low and give a PASS or FAIL verdict.
