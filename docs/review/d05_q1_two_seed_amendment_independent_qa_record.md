# D-05 Q1 two-seed amendment and addenda — independent QA record

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`) · Reviewer: independent QA agent (Claude Code, Opus 5.5). I did
not write any of the reviewed documents. This was a read-only review: no file was edited other than this
record, git was not run, and no inference, training, scoring or upload was performed.
`sealed_test_accessed=false`. The sealed test `afa03d4b…` was not opened, listed, counted or scored.

Verdict: PARTIAL — the Q1 change is correctly scoped, every pin matches, the quoted numbers recompute
exactly and no gate, selection rule, grid, tie-break, NMS change condition, one-time test rule or Q4
allowance was silently changed; but the timing disclosure omits the already-computed two-seed provisional
selection, the Owner's word "pilot" is reinterpreted without saying so, the binding D-05 proposal text is
not superseded, both addenda leave three-seed clauses unreplaced under a "nothing else" heading, and no
document states that the group bootstrap CI does not cover training-seed variation.

## Files under review (SHA-256, start = end)

| File | Start | End |
| --- | --- | --- |
| `docs/review/d05_q1_two_seed_owner_amendment_2026-11-06.md` | `6d18b31678bf1b435c8d354d7bcfd9a6424db381f60384a31a995031a3bb439c` | identical |
| `docs/review/d1_threshold_lock_r1_contract_addendum_1_two_seeds.md` | `2348c583b6b2625560e02fe233e0a08834a8a9548142676b557ec61ee88c80c2` | identical |
| `docs/review/d1_final_evaluation_r1_contract_draft_addendum_1_two_seeds.md` | `8767d1e31d52e96c974fa0250e845c9060af01e65c9d3597a1ad2140fe48b7f8` | identical |

## Reference pins (recomputed)

| Reference | Recomputed SHA-256 | Matches pins in reviewed files |
| --- | --- | --- |
| `docs/review/d05_owner_decision_record.md` | `c81f37ed…5555702` | yes (amendment) |
| `docs/review/d1_threshold_lock_r1_contract.md` | `726932db…4d278f0f` | yes (amendment, lock addendum) |
| `docs/review/d1_final_evaluation_r1_contract_draft.md` | `17a0bf3d…b1d71` | yes (final-eval addendum) |
| `docs/review/d1_s2_r1_common_validation_report_r1.md` | `b78105ba…68d530d2f4` | yes (amendment) |
| `docs/review/d1_s2_r1_result_independent_qa_record.md` | `68ce90a9…f0ec3` (Verdict PASS, line 9) | cited by path in lock addendum |
| `detector/m1/contract.py` | `901e7e37…a6bbbf` | equals the lock contract pin |
| `docs/review/d05_proposal.md` (D-05 binding text) | `3b0e9bca…5717e277f` | not cited by the amendment (see M2) |

## Checks

1. **Pins.** All pins in the three files match. PASS.
2. **Scope of change.** Amendment §3/§4 and both addenda change only seed count, the gate statistic
   (two-seed mean, difference instead of SD) and the dependent counts. Q2 values, Q3, Q4 (selection on val,
   lock before test, single recalibration still unused, never lowered after test), Q5, the one-time test
   rule, the confidence grid, NMS grid, eligibility rule, tie-breaks, the three NMS change conditions
   (1,000 resamples, seed 20261018, ≥ 7/9 folds) and stop-without-lock are restated unchanged. No silent
   change found. No later recalibration record exists in `docs/review/` (grep). PASS, with L4/L5 wording.
3. **Numbers.** S2 report table: agnostic recall 547/624 and 507/624; FP 150/376 and 127/376; mAP50
   0.8521 and 0.7309. Two-seed means: (547+507)/1248 = 0.84455 → **0.845**; (150+127)/752 = 0.36835 →
   **0.368**. mAP50 0.731 vs 0.852 correct. Decision-history row 2 quote equals the authorization record
   (`f71a7eea…`) and the provisional handoff; row 1 ("keep 3 seeds" first) is consistent with handoff line 7.
   Numbers PASS; disclosure incomplete (H1, M1, L6).
4. **Lock addendum completeness.** Covered: line 12 seeds, line 25 mean/SD/mAP mean, line 26 "each seed",
   line 27 bootstrap and LOGO means, line 32 "all three runs"/"exactly three candidates"/"for all three".
   Not covered: see M3. Bootstrap/LOGO two-seed mean is unambiguous (same group draw for both seeds and
   both NMS settings; per-draw arithmetic mean of the two per-seed metrics, then difference; for recall and
   FP/image on identical images/GT this equals the pooled rate). Schema note verified: `contract.py:37`
   `SEEDS = (20261018, 20261019, 20261020)`; `:364-365` "exactly the three D-05 seeds"; `:391` seed set
   must equal `SEEDS`; `:393-394` three distinct weights; `:397` three val reports. Accurate.
5. **Final-eval addendum.** Partially complete (L1). Test-label choice is stated without choosing, but its
   premise wording is not neutral (L2).
6. **Statistical caution.** "Two-point SD is not reported as an uncertainty estimate" is stated in all three.
   That the D-02 group bootstrap CI is over validation/test groups for fixed weights, not over training
   seeds, is stated in none of them (M4). It is stated in the S2 report (lines 30-33) and the provisional
   report (lines 65-68).
7. **Premature lock/test risk.** No reviewed clause authorizes a lock or test access: the lock addendum is
   `FROZEN_AWAITING_INDEPENDENT_QA`, `thresholds_locked=false`; the final-eval addendum stays
   `DRAFT_NOT_AUTHORIZED`; remaining gates (R3 successor writer/verifier/reader with QA, per-NMS×seed
   inference authorization, lock QA, Owner lock approval, finalized contract with QA, Owner test approval)
   are listed as unchanged. Residual risks: H1, M3, L7. No sealed-test access log exists at
   `results/experiments/sealed_test_access_log.jsonl` (the path `scripts/build_m1_yolo_dataset.py:58`
   writes), consistent with no logged access.

## Findings

### H1 — High — timing disclosure omits the two-seed provisional selection that already existed

Evidence: file birth times — `docs/review/generated/d1_two_seed_provisional_threshold_r1.json`
(`d6ce4556…`) 17:39:56 and `docs/review/d1_two_seed_provisional_threshold_r1_report.md` (`705ee356…`)
17:40:50, both before the amendment (17:43:53) and addenda (17:44:07, 17:44:15). That report gives the
full two-seed outcome under the unchanged rule: conf 0.19, class-aware NMS 0.70, mean recall 0.85497,
mean FP/image 0.38032 (seed 19 alone recall 0.82051); across-class 0.80 meets both markers (FP 0.24734)
but is rejected by the mAP CI [-0.13119, -0.03448]. The amendment says only that the S2 conf-0.20 report
was known, then makes "the two-seed threshold selection" binding. Birth time does not prove the Owner or
recorder had read the report; the record does not say either way. Because the rule and grid are unchanged
and both known seeds are kept, this is a disclosure gap, not evidence of outcome-driven rule change.
Fix: append a note stating that the provisional two-seed selection output existed before the amendment,
its result (above), whether the Owner/recorder had seen it, and that the binding R3 successor run on the
same inputs is expected to reproduce it.

### M1 — Medium — Owner wording "cho pilot" reinterpreted as the final candidate without saying so

Evidence: amendment §1 quotes "Hãy thay đổi bây giờ chỉ lấy 2 seed cho pilot"; §2 row 3 and the title
record "final candidate judged on two seeds". In D-05 Q1, "pilot" is the 1-seed stage distinct from the
final candidate; the lock contract (line 12) calls the family "YOLO11s-54 pilot configuration". Both
readings are plausible. Fix: state the interpretation explicitly ("pilot" = the pilot configuration's
final-candidate family) and record an Owner confirmation of it.

### M2 — Medium — the binding D-05 proposal text is not superseded

Evidence: `d05_owner_decision_record.md` lines 8-9: "The proposal file is the binding text."
`d05_proposal.md` line 33 still fixes seeds 20261018/19/20 and "trung bình 3 seed, báo kèm độ lệch
chuẩn". The amendment's precedence clause (line 7) covers only the decision record. Fix: pin
`d05_proposal.md` (`3b0e9bcac0f0af55bf10885cf8b1fa4793c835275bb89817f72ca1b5717e277f`) and state that its
Q1 seed/SD text is superseded by the same two-seed rule.

### M3 — Medium — lock addendum leaves three-seed clauses unreplaced under "Replacements (and nothing else)"

Evidence: lock contract line 19 ("verify all three seeds have the same 376 frame stems…"; "one shared
`(confidence, nms_iou, agnostic_nms)` for all three weights"), line 27 ("select per-class 0.70 and its
prespecified three-seed confidence point"), line 28 ("this three-seed lock"), line 34 (planned invocation
with `<seed20-R3>`), and the title. Addendum §3 partly mitigates line 19 ("must now require exactly the two
seeds"), but the heading implies the table is exhaustive, so a literal reader (or the successor
implementer reading line 19/34) still sees three-seed requirements. Fix: add rows for each clause plus a
catch-all: "every remaining reference to three seeds, seed 20261020, 'all three' or a third report in the
contract reads as the two seeds 20261018 and 20261019."

### M4 — Medium — no statement that the group bootstrap CI excludes training-seed uncertainty

Evidence: amendment §3/§5 and both addenda drop the SD and say the spread "cannot be estimated reliably",
but D-05 Q2 keeps a D-02 group bootstrap CI on the two-seed mean and the lock uses paired group CIs. None
of the three documents says these CIs are conditional on the two trained weights and say nothing about
another training seed. Fix: add one sentence to the amendment and the final-eval addendum: "The D-02 group
bootstrap CI quantifies roster/group variation for the two fixed weights; it is not an interval over
training seeds. Seed variation is described only by the two-seed difference."

### L1 — Low — final-eval addendum incomplete and one row mis-attributed

Evidence: unreplaced draft text at line 50 ("three candidate bindings"), line 54 ("using the fixed three
weights"), line 15 ("…until all three completed-run result QAs and validation comparisons exist") and
descriptive lines 13/48. Row 2 attributes line-15 text to "Prerequisite 1"; Prerequisite 1's own text
(line 19, "Complete the three predeclared candidate seeds … A third seed requires its own approval") is
not quoted. Fix: add rows for lines 19, 50 and 54 and the same catch-all as M3.

### L2 — Low — test-label question premise is not neutral

Evidence: "The validation labels were completed in R3: 64 added boxes and ignore regions." R3 added 64
boxes mined from the pilot model's own false positives with no symmetric search for missed signs
(`d1_vre_r2_contract.md` `751d78fe…` §9), plus 40 ignore regions (`d1_vrl_r3_owner_acceptance_record.md`).
"Completed" overstates; the mining also favours seed 20261018 on R3. The source of the "carried forward"
question is not cited. The (a)/(b) choice itself is stated without choosing. Fix: replace "completed" with
"partially corrected (64 boxes from the pilot's own FPs, 40 ignore regions; no search for misses)", cite
the source, and note the seed asymmetry.

### L3 — Low — pilot result QA asserted without citation

Evidence: lock addendum §1 last row: "the pilot (QA-passed earlier)". The records exist:
`docs/review/d1_vre_r2_result_independent_qa_record.md` (`95db91cb…`) and
`docs/review/d1_pilot_run_registry_independent_qa_record.md` (`90a13c33…`, Verdict PASS). Fix: cite them
with hashes.

### L4 — Low — amendment §4 Q2 summary drops qualifiers

Evidence: omits "test boxes", "averaged over the 32 classes", that an other-class miss marks the class
not passed without failing the gate, the report-only items, and Q6. Line 7 ("Everything else in D-05 is
unchanged") covers this. Fix: add "summary only; D-05 text governs".

### L5 — Low — validation means described as gate failures

Evidence: §5 "0.845, below the 0.85 gate"; "0.368, above the 0.30 gate". Q2 gates apply to the sealed test.
On validation these are rule markers, and conf 0.20 is simply ineligible under the selection rule. Fix:
say "below the 0.85 eligibility marker on validation (conf 0.20 is ineligible under the rule)".

### L6 — Low — claim classification of Owner quotes

Evidence: §6 classifies only hashes and numbers. Rows 1 and 3 are chat quotes that the repository cannot
verify; row 2 matches `f71a7eea…`. Fix: classify rows 1 and 3 as "recorded by coordinator; not
repository-verifiable".

### L7 — Low — inference authorization coverage for reusing the provisional seed-19 sweep

Evidence: the seed-19 11-configuration inference was authorized only as a "provisional diagnostic … not
the frozen three-seed threshold lock" (`f71a7eea…` lines 11-15), and the lock contract (line 32) requires
each NMS × seed inference to have its own authorization and QA. The handoff (not under review) says those
predictions may be reused for the lock; the lock addendum §2 keeps the requirement but does not say
whether reuse needs a new authorization. Its result QA now exists
(`d1_two_seed_provisional_threshold_r1_result_independent_qa_record.md`, created 17:46:20, Verdict PASS).
Fix: the successor implementation record must name the authorization that covers the predictions it
binds, or obtain one.

## Claim classification

- **Verified artifact/result:** all hashes in this record; S2 table values and the two-seed means
  0.84455/0.36835; `contract.py` three-seed enforcement lines; provisional report values quoted in H1;
  file birth times; absence of a sealed-test access log file.
- **Verified current behavior:** `bind_threshold_lock` rejects any lock that does not bind exactly the three
  D-05 seeds (read from source, not executed).
- **Proposal:** every "Fix" above.
- **Unknown:** whether the Owner or recorder saw the provisional report before the amendment; the Owner's
  intended meaning of "cho pilot"; unlogged sealed-test access (not observable; none logged); what a third
  seed would have shown.

`sealed_test_accessed=false`
