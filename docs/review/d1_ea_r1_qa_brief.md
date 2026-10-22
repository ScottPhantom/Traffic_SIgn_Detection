# D1-EA-R1 — brief for the independent QA session

Give this brief to a fresh session (Claude or Codex) that did **not** author D1-EA-R1. Write the
result to a new append-only file `docs/review/d1_ea_r1_independent_qa_record.md`. Do not modify
the package, the builder, the tests, `PROJECT_MEMORY.md` or the roadmap. Do not commit, push,
train or open the sealed test.

## Package

- Builder: `detector/m1/error_analysis_r1.py` (`build` / `verify`, run from `detector/`).
- Tests: `detector/tests/test_error_analysis_r1.py`.
- Implementation record: `docs/review/d1_ea_r1_implementation_record.md`.
- Outputs:
  - `docs/review/generated/d1_ea_r1_{predictions,missed_gt,atlas_index}.csv`;
  - `docs/review/generated/d1_ea_r1_manifest.json` (SHA-256 `d87f090e…`);
  - `docs/review/d1_ea_r1_evidence_report.md`;
  - the atlas `docs/review/assets/d1_ea_r1/` (15 pages, git-ignored).
- Requirement: "Required next evidence package — D1-EA-R1" in
  `docs/review/d1_corrected_val_r10_error_analysis_and_improvement_packet_r1.md`.

## Checks to perform

1. **Pins.** Every entry in `PINNED` matches the file on disk. In particular the R10 report is
   `b33e2470…` and the weights are `5d5815a9…`. The pins also cover the R10, R1 and metrics
   modules, the class map, the packet R1 and both QA records.
2. **Reproduction of R10, independently.** With your own script, not the builder, rebuild the
   frames from `d1_ea_r1_predictions.csv` and the validation label files in
   `data/processed/m1_yolo_wp38_r1_integration_r4/labels/val/`. Then confirm all of these equal
   `eval_val_wp38_r1_r4_r10.json`:
   - the operating point at conf 0.20 (376 / 560 / 483 / 214);
   - the full confusion matrix;
   - class-aware hits for every gated class.

   Also confirm that every exported confidence is ≥ 0.20.
3. **Completeness of the export.**
   - 697 prediction rows, each disposed exactly once as PAIRED or BACKGROUND.
   - 77 missed-GT rows.
   - No stem outside the 376 validation frames, and no test or `train` stem.
4. **Atlas coverage.** The index has exactly:
   - 214 `background_fp` entries, one per BACKGROUND row;
   - every GT box of classes 7, 32 and 41 that is wrong-class or missed;
   - every 46→10 and 8→12 pair.

   Read several pages of each category, and redraw a sample of boxes from the CSVs on the raw
   images, to confirm that the tiles show the right box and caption.
5. **Determinism and fail-closed behaviour.**
   - `uv run python -m m1.error_analysis_r1 verify` returns `valid=true`.
   - `uv run pytest -q -p no:cacheprovider tests/test_error_analysis_r1.py` passes.
   - On a staged copy, run at least four tampering attacks and confirm each fails closed:
     - change one prediction row;
     - flip a byte of an atlas page;
     - add an extra atlas file;
     - append to a pinned QA record;
     - edit the R10 report;
     - re-run `build` over existing outputs (it must refuse).
6. **Boundary.**
   - `test_included=false`, `sealed_test_accessed=false` and `training_authorized=false`.
   - No code path writes validation pixels or predictions anywhere that training reads.
7. **Hypotheses in the implementation record.** Judge whether each of the four hypotheses is
   supported by the atlas and stated with the right hedging, especially:
   - the duplicate-detection share (66/214);
   - the agnostic-NMS diagnostic numbers;
   - the claim that many "no GT nearby" false positives are unlabelled real signs.

   Report any disagreement with stem ids.

Classify findings Critical / High / Medium / Low and give a PASS or FAIL verdict.
