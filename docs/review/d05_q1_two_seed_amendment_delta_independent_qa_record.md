# D-05 Q1 two-seed amendment, revision 2 — delta independent QA record

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`) · Reviewer: independent delta QA agent (Claude Code, Opus 5.5).
I did not write the reviewed documents or the first QA record. Read-only review: no file was edited
other than creating this record. Git was not run. No inference, training, scoring or upload was done.
`sealed_test_accessed=false`: the sealed test `afa03d4b…` was not opened, listed, counted or scored.

Verdict: PASS giới hạn — all eleven first-QA findings (H1, M1–M4, L1–L7) are closed or reduced to Low residue; revision 2 introduces no silent scope change, no number error in the metrics, and no path to a lock or test access that skips a remaining gate; but three abbreviated hashes are wrong (N1, Medium) and must be corrected before the append-only commit.

## Files under review (SHA-256; start = end)

| File | Start | End |
| --- | --- | --- |
| `docs/review/d05_q1_two_seed_owner_amendment_2026-11-06.md` (rev 2) | `a6dd66d594413bf825fe3bb5df8cee8a1adfb21c70e65b3397cede7c7a68479f` | identical |
| `docs/review/d1_threshold_lock_r1_contract_addendum_1_two_seeds.md` (rev 2) | `c40fa497d4b5d5067bde812a0a3833fd5107dd318b281acb295ca53b1cd776ac` | identical |
| `docs/review/d1_final_evaluation_r1_contract_draft_addendum_1_two_seeds.md` (rev 2) | `849b91476ff821e2fb827bd007c83fbe356a1a32f9e9533bd8fcb2022da96a02` | identical |
| First QA `docs/review/d05_q1_two_seed_amendment_independent_qa_record.md` | `67e07cf25a9b3589cd71d7cb4fcab8b0987ba36d20ca11abb1a0c18cd22b576b` | identical |

## Reference pins (recomputed)

| Reference | SHA-256 | As cited in rev 2 |
| --- | --- | --- |
| `docs/review/d05_proposal.md` | `3b0e9bcac0f0af55bf10885cf8b1fa4793c835275bb89817f72ca1b5717e277f` | full, correct (amendment L12) |
| `docs/review/d05_owner_decision_record.md` | `c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702` | full, correct (amendment L10) |
| `docs/review/d1_threshold_lock_r1_contract.md` | `726932dbcd32842658477c9d36f4dc7c240d412d92119e76e5b3536a4d278f0f` | full, correct (amendment L117; lock addendum L8) |
| `docs/review/d1_final_evaluation_r1_contract_draft.md` | `17a0bf3df57de66dd6369a7da78c58ad4b9df52f195fbd3a0aa1933f1cab1d71` | full, correct (final-eval addendum L8) |
| `docs/review/d1_s2_r1_common_validation_report_r1.md` | `b78105ba5ae763233c6a6fee657235a594455e7264073c8d7895ff68d530d2f4` | full, correct (amendment L43) |
| `docs/review/d1_two_seed_provisional_threshold_r1_report.md` | `705ee356cf231f77873c62bf86631d3c5510776cdc2672777ce4caf719c7e636` | `705ee356…e636`, correct (amendment L54) |
| `docs/review/generated/d1_two_seed_provisional_threshold_r1.json` | `d6ce45568709be8bb3f3ea6d9535870f5027fd40f645addeac3a4a990b627e33` | `d6ce4556…e627be4`, **wrong suffix** (amendment L56; N1) |
| `docs/review/d1_two_seed_provisional_threshold_r1_owner_authorization_2026-11-06.md` | `f71a7eea772e191b8db6bf6074b450aa71fa3c8bbeb443b69983eb610e627be4` | `f71a7eea…e4c`, **wrong suffix** (amendment L34; N1) |
| Rev 1 final-eval addendum (from first QA L21) | `8767d1e31d52e96c974fa0250e845c9060af01e65c9d3597a1ad2140fe48b7f8` | `8767d1e3…a7f48b7f8`, **wrong suffix** (final-eval addendum L5; N1) |
| Rev 1 amendment / rev 1 lock addendum (first QA L19–20) | `6d18b316…a3bb439c` / `2348c583…88c80c2` | correct |
| `docs/review/d1_pilot_run_registry_independent_qa_record.md` | `90a13c3333fac3b536146a0ed150f7dd446bec2cda57175f003f8cc0ea7cbc8d` | path only; Verdict **PASS** (line 5, 144) |
| `docs/review/d1_vre_r2_result_independent_qa_record.md` | `95db91cbe640e27ee6de2c185a09b61902da4412717310932aa3b36e48be031b` | path only; Verdict **PASS** (line 213); line 200: added boxes "came from this model's own FPs" |
| `docs/review/d1_s2_r1_result_independent_qa_record.md` | `68ce90a9b34bb65b7bd85f3120ac96c064cbae1b36f7ddfd510a35a1187f0ec3` | path only; Verdict PASS (line 9) |
| `docs/review/d1_vrl_r3_owner_acceptance_record.md` | `4d9482856771960240cdf727834e9283fb9ba072f88992c6204dcbb6405d7480` | path only; line 28 "64 added boxes", line 34 "40 ignore regions, for the proposals whose locator is ≤ 17.5 px". It does not itself state the FP origin (N5). |

## Status of first-QA findings

| ID | Status | Evidence (rev 2 line refs) |
| --- | --- | --- |
| H1 | **Closed** (hash typo split out as N1) | Amendment L53–79. Values match provisional report L11–21, L38–39: conf 0.19, class-aware NMS 0.70, mean recall 0.85497, mean FP/image 0.38032; across-class 0.80 at conf 0.19 meets both markers with FP 0.24734 and is rejected because the paired mAP50-95 CI ([-0.13119, -0.03448]) is wholly below zero. Times 17:40:50 (report) and 17:39:56 (JSON) equal the file birth times. Report hash correct; JSON hash suffix wrong (N1). Who saw it: L67–69 (Owner "Chưa thấy"; recorder self-report), classified as unverifiable at L140–141 and L68–69. Reproduction expectation and "explain any difference before lock approval": L71–73; repeated in lock addendum L53–61 with "must not be re-labelled as the lock". Commit `f914d31` is consistent with the session's git-log snapshot; not re-verified (git not run). |
| M1 | **Closed** | Amendment L20–27: explicit question (final D-05 test uses mean of 20261018+20261019, 20261020 dropped) and Owner answer "Đúng"; "pilot" = pilot configuration = final candidate. Classified as unverifiable Owner statement at L140–141; history row 3 L35. Matches the coordinator-reported exchange. |
| M2 | **Closed** | Amendment L11–17: `d05_proposal.md` pinned with the correct full hash; superseded text quoted verbatim and matches proposal line 33; D05-B "ứng viên cuối 3 seed" (proposal line 30) also superseded; precedence limited to "number of seeds and the gate statistic". |
| M3 | **Closed** | Lock addendum L16–25. My re-scan of contract title and lines 12, 19, 25, 26, 27, 28, 32, 34 found every three-seed clause either rowed or under the catch-all (L25: three seeds/weights/reports/seed 20261020). Line 24 "three change conditions" is correctly not swept by the catch-all. Line 12 "Seed `20261020` is not approved to train" is consistent with the catch-all. |
| M4 | **Closed** | Amendment L89–91; lock addendum L27–28; final-eval addendum L26–27: the D-02 bootstrap holds the two weights fixed and is not an interval over training seeds. |
| L1 | **Closed** | Final-eval addendum L16–24 rows for draft lines 13, 15, 19, 22, 29, 44, 50, 54 plus catch-all. Re-scan of draft lines 13–54: lines 20 ("all three candidate weight/run/report hashes") and 48 ("common three-seed selection") are caught by the catch-all. Prerequisite 1 is now correctly attributed to line 19. |
| L2 | **Partially closed** | Final-eval addendum L39–51: "partially corrected", 64 boxes from the pilot's FPs with no full search for misses, 40 ignore regions, seed-20261018 asymmetry stated, (a)/(b) neutral, "This draft does not choose". Residue in N5 (citation of FP origin; source of the "carried forward" question still not cited). |
| L3 | **Partially closed** | Amendment L44–47 cite the pilot and S2 QA records by path, without hashes; VRE-R2 QA is a validation-evaluation QA but is listed under "independent run QA". Final-eval addendum L17–18 assert "completed-run result QA PASS" and prerequisite 1 "Satisfied" without citation. Records exist and say PASS. Residue in N2. |
| L4 | **Closed** | Amendment L95–113: "summary only; the D-05 decision record and proposal govern"; test boxes, class averaging (32 cited), other-class miss rule, report-only items, Q6 restored. |
| L5 | **Closed** | Amendment L125–127: validation markers vs sealed-test gates distinguished; conf 0.20 "not eligible under the frozen selection rule". |
| L6 | **Closed** | Amendment L33–35 evidence-class column; L137–142 classification. Minor residue: row 2's option choice (N3). |
| L7 | **Closed** | Amendment L130–135 and lock addendum L60–61: reuse of seed-20261019 predictions needs a named authorization covering the reuse, otherwise a new authorization. |

## Checks for new problems

1. **Scope.** Only seed count, gate statistic and dependent counts change. Grid, NMS modes, eligibility,
   tie-breaks, three NMS change conditions (1,000 rounds, seed 20261018), stop-without-lock, Q2–Q6, the
   single unused Q4 recalibration and the one-time rule are restated as unchanged (amendment L93–118;
   lock addendum L30–44; final-eval addendum L29–35). "Seed 20261020 not trained for the D-05 final
   evaluation" (amendment L87) is the Owner-confirmed scope change, not a silent one. No run directory for
   seed 20261020 exists under `results/experiments/` (directory names only listed).
2. **Numbers.** S2 report lines 43–46: recall 547/624 and 507/624, FP 150/376 and 127/376, mAP50 0.8521
   and 0.7309; means 1054/1248 = 0.845 and 277/752 = 0.368 correct. Provisional values correct (H1 row).
3. **Lock/test gates.** Lock addendum stays `FROZEN_AWAITING_INDEPENDENT_QA`, `thresholds_locked=false`;
   final-eval addendum stays `DRAFT_NOT_AUTHORIZED`. Remaining gates (successor writer/verifier/reader
   with QA, inference authorization, lock QA, Owner lock approval, finalized contract with QA, explicit
   Owner test approval) are kept (amendment L128–132; lock addendum L32–44). Marking prerequisite 1
   "Satisfied" does not open anything, because prerequisites 2–5 remain. Lock addendum L23 "both have"
   result QA is true for run QA; lock contract line 32 per-NMS×seed authorization is untouched. No
   sealed-test access log exists at `results/experiments/sealed_test_access_log.jsonl`.
4. **Owner statements.** "Chưa thấy" (L67–69) and "Đúng" (L24–27) are recorded and classified as
   unverifiable Owner statements (L140–141).

## New findings

### N1 — Medium — three abbreviated hashes have wrong suffixes

Evidence: amendment L56 `d6ce4556…e627be4` (true `…a990b627e33`; `e627be4` is the authorization
record's suffix); amendment L34 `f71a7eea…e4c` (true `…610e627be4`); final-eval addendum L5
`8767d1e3…a7f48b7f8` (true `…40fe48b7f8`). Prefixes and paths are right, so identity is recoverable,
but these are integrity pins in documents that become append-only on commit, and N1 sits inside the H1
disclosure. Fix before commit: replace each with the full 64-hex value from the pins table above, and
re-hash-check (no substantive re-review needed).

### N2 — Low — run-QA claims without hashes (L3 residue)

Evidence: amendment L44–47; final-eval addendum L17–18. Fix: cite
`d1_pilot_run_registry_independent_qa_record.md` (`90a13c33…7cbc8d`, PASS) and
`d1_s2_r1_result_independent_qa_record.md` (`68ce90a9…87f0ec3`, PASS) with full hashes in both places,
and label `d1_vre_r2_result_independent_qa_record.md` as the pilot's R3 validation-evaluation QA, not run QA.

### N3 — Low — history row 2 evidence class overstated

Evidence: amendment L34 says row 2 is "Quoted in" `f71a7eea…`. That record (line 5) contains only
"lấy trung bình trên 19 trước vì không đủ thời gian chạy 3 seed."; the choice "B. Tạm thời 2 seed" does not
appear in it or elsewhere in `docs/`. Fix: "first quote verified in f71a7eea…; option choice chat only".

### N4 — Low — abridged prerequisite list in the final-eval addendum

Evidence: final-eval addendum L29–33 summarize prerequisite 2 as "the R3 lock writer/verifier/reader",
omitting its inference permissions, source/result QAs, lock-record QA and Owner lock approval (draft
line 20). The draft text still governs because it is not replaced, so no gate is lost. Fix: add
"(summary; draft prerequisites 2–5 govern)".

### N5 — Low — test-label question citation (L2 residue)

Evidence: final-eval addendum L39–42 cite only `d1_vrl_r3_owner_acceptance_record.md`, which gives the
counts but not the FP origin, and describes the 40 ignore regions as "for proposals whose locator is
≤ 17.5 px", not "signs that are too small". The source of the carried-forward question is still not
named. Fix: add `d1_vre_r2_contract.md` line 112 and `d1_vre_r2_result_independent_qa_record.md`
line 200 as the FP-origin evidence; use the record's wording for ignore regions; name the source of
the question.

## Claim classification

- **Verified artifact/result:** all SHA-256 values in this record; provisional report and S2 report values;
  file birth times; QA verdict lines; R3 counts; absence of a seed-20261020 run directory and of a
  sealed-test access log file.
- **Owner statement, not verifiable in the repository:** "Chưa thấy"; "Đúng"; history rows 1 and 3 and the
  row-2 option choice.
- **Recorder self-report, not verifiable:** the recorder had not read the provisional report when writing revision 1.
- **Unknown:** commit `f914d31` contents (git not run; consistent with the session snapshot); what a third seed would have shown.
- **Proposal:** every "Fix" above.

`sealed_test_accessed=false`
