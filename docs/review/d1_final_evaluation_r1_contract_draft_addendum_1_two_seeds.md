# D1 final evaluation contract draft — addendum 1: two seeds

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`) · Author: Claude Code (Opus 5.5), coordinating session.
Status: `DRAFT_NOT_AUTHORIZED` (unchanged).
Revision 2: rewritten before commit after the independent QA of revision 1 (SHA-256 `8767d1e31d52e96c974fa0250e845c9060af01e65c9d3597a1ad2140fe48b7f8`) returned PARTIAL. The delta QA
(`docs/review/d05_q1_two_seed_amendment_delta_independent_qa_record.md`) returned PASS giới hạn. Its
findings N1, N2, N4 and N5 are fixed in place in this pre-commit copy.
Append-only once committed. Does not edit `docs/review/d1_final_evaluation_r1_contract_draft.md`
(SHA-256 `17a0bf3df57de66dd6369a7da78c58ad4b9df52f195fbd3a0aa1933f1cab1d71`).
Authority: `docs/review/d05_q1_two_seed_owner_amendment_2026-11-06.md`.
`sealed_test_accessed=false`.

## Replacements

| Draft location | Original text (abridged) | Replaced by |
| --- | --- | --- |
| Line 13 | "Three-seed validation threshold-selection contract" | the threshold-selection contract **as amended by its addendum 1 (two seeds)** |
| Line 15 | "Seed `20261020` has no training permission… The three-seed final candidate is unknown until all three completed-run result QAs…" | The final candidate is the pilot configuration with seeds 20261018 and 20261019. Both have independent run QA PASS: pilot `docs/review/d1_pilot_run_registry_independent_qa_record.md` (SHA-256 `90a13c3333fac3b536146a0ed150f7dd446bec2cda57175f003f8cc0ea7cbc8d`), and seed 20261019 `docs/review/d1_s2_r1_result_independent_qa_record.md` (SHA-256 `68ce90a9b34bb65b7bd85f3120ac96c064cbae1b36f7ddfd510a35a1187f0ec3`). Seed 20261020 is not part of the final evaluation. |
| Line 19, prerequisite 1 | "Complete the three predeclared candidate seeds `20261018`, `20261019` and `20261020`…" | **Satisfied** for the two seeds 20261018 and 20261019, by the two run QA records cited in the row above |
| Line 22, prerequisite 4 | "covering the actual three weights" | covering the actual **two** weights |
| Line 29, Q1 | "mean of three seeds, with their sample standard deviation reported" | **mean of two seeds**; each seed's test value and the difference between them are reported; no two-point standard deviation as uncertainty |
| Line 44, Q5 | "three candidate identities" | **two** candidate identities |
| Line 50, successor | "three candidate bindings" | **two** candidate bindings |
| Line 54, execution | "using the fixed three weights" | using the fixed **two** weights |
| **Catch-all** | any remaining three-seed or seed 20261020 reference | means the two seeds 20261018 and 20261019 |

**Uncertainty scope.** The D-02 group bootstrap CI holds both trained weights fixed. It covers test image
groups, not training seeds.

The other prerequisites are unchanged. The list below is a summary only; the draft text governs, including
every part of prerequisite 2:
- the R3 lock writer/verifier/reader;
- the Owner's single recalibration decision;
- the finalized contract with QA;
- explicit Owner approval to open the test once.

The gates and the one-time rule are also unchanged.

## Open Owner question carried forward (not resolved here)

The validation labels were partially corrected in R3:
- R3 was accepted in `docs/review/d1_vrl_r3_owner_acceptance_record.md`
  (SHA-256 `4d9482856771960240cdf727834e9283fb9ba072f88992c6204dcbb6405d7480`);
- its candidates came from the label audit `docs/review/d1_vla_r1_report.md`
  (SHA-256 `93ee9566e7b237e7bc61ab7e858a2b17db76cebf0865ae178a7017022b8d0e9f`). That audit examined the
  pilot's 214 background false positives at confidence 0.20; it was not a full search for missed signs;
- R3 added 64 boxes and 40 ignore regions for signs too small to label (as described in the acceptance
  record).

The open question carried forward here was raised in the coordinating session's final-evaluation readiness
review of 2026-11-06. It is not taken from an earlier committed record.

The test labels have not been reviewed, because reviewing them is a form of test access. The R3
correction also used seed 20261018's predictions, which may favour that seed on validation.

Before test access, the finalized contract must record an Owner choice between:
- (a) scoring the test with its current labels and stating this asymmetry; or
- (b) a separately authorized, prediction-blind review of the test labels.

This draft does not choose.
