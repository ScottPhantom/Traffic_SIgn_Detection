# D-05 Q1 amendment — final candidate judged on two seeds (Owner decision record)

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`), evening.
Recorded by: Claude Code (Opus 5.5), coordinating session, on the Owner's written instruction in chat.
Revision 2: rewritten before commit to address the independent QA record
`docs/review/d05_q1_two_seed_amendment_independent_qa_record.md`, which reviewed revision 1
(SHA-256 `6d18b31678bf1b435c8d354d7bcfd9a6424db381f60384a31a995031a3bb439c`) and returned PARTIAL.
The delta QA (`docs/review/d05_q1_two_seed_amendment_delta_independent_qa_record.md`) returned PASS giới
hạn. Its hash and citation findings N1–N3 are fixed in place in this pre-commit copy.
Append-only once committed. This record does not edit:
- `docs/review/d05_owner_decision_record.md`
  (SHA-256 `c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702`);
- the binding D-05 proposal text `docs/review/d05_proposal.md`
  (SHA-256 `3b0e9bcac0f0af55bf10885cf8b1fa4793c835275bb89817f72ca1b5717e277f`).

Where either conflicts with this record **on the number of seeds and the gate statistic**, this record
wins. The specific text it supersedes is: the Q1 bullets of the decision record, and the Q1 line of the
proposal, `Seed cố định: 20261018, 20261019, 20261020. Gate tính trên trung bình 3 seed, báo kèm độ lệch
chuẩn` (and the D05-B row "ứng viên cuối 3 seed"). Everything else in D-05 is unchanged.
`sealed_test_accessed=false`.

## 1. Owner instruction (verbatim) and its confirmed meaning

> "Hãy thay đổi bây giờ chỉ lấy 2 seed cho pilot"

**Interpretation, confirmed by the Owner.** The recorder asked in chat: does this mean that the final
sealed-test evaluation (D-05) uses the mean of seeds 20261018 and 20261019, and that seed 20261020 is
dropped? The Owner answered **"Đúng"**. Here "pilot" means the pilot configuration, which is the final
candidate.

## 2. Decision history on this day

| Order | Owner input in chat | Effect | Evidence class |
| --- | --- | --- | --- |
| 1 | "Tôi chỉ muốn chạy chấm 2 seed thôi", then chose "Giữ 3 seed" | D-05 Q1 kept at three seeds | Chat only; not verifiable from the repository |
| 2 | "lấy trung bình trên 19 trước vì không đủ thời gian chạy 3 seed", then chose "B. Tạm thời 2 seed" | Provisional two-seed threshold only; three seeds kept for the test | The quote appears in `docs/review/d1_two_seed_provisional_threshold_r1_owner_authorization_2026-11-06.md` (SHA-256 `f71a7eea772e191b8db6bf6074b450aa71fa3c8bbeb443b69983eb610e627be4`). The option choice "B. Tạm thời 2 seed" is chat only. |
| 3 | **This record:** "Hãy thay đổi bây giờ chỉ lấy 2 seed cho pilot", then "Đúng" to the interpretation in §1 | Final candidate judged on two seeds | Chat only; not verifiable from the repository |

## 3. Timing disclosure

Two sets of results existed before this amendment was written.

**(a) Seed 20261019 validation comparison.**
- Report: `docs/review/d1_s2_r1_common_validation_report_r1.md`, SHA-256
  `b78105ba5ae763233c6a6fee657235a594455e7264073c8d7895ff68d530d2f4`.
- Independent QA records for both seeds (all `Verdict: PASS`):
  - pilot seed 20261018, run registry QA: `docs/review/d1_pilot_run_registry_independent_qa_record.md`
    (SHA-256 `90a13c3333fac3b536146a0ed150f7dd446bec2cda57175f003f8cc0ea7cbc8d`);
  - pilot seed 20261018, R3 validation result QA (a validation QA, not a run QA):
    `docs/review/d1_vre_r2_result_independent_qa_record.md`
    (SHA-256 `95db91cbe640e27ee6de2c185a09b61902da4412717310932aa3b36e48be031b`);
  - seed 20261019, completed-run QA: `docs/review/d1_s2_r1_result_independent_qa_record.md`
    (SHA-256 `68ce90a9b34bb65b7bd85f3120ac96c064cbae1b36f7ddfd510a35a1187f0ec3`).
- At confidence 0.20, class-aware NMS 0.70:
  - mAP50 is 0.731 for seed 20261019 against 0.852 for the pilot;
  - the two-seed mean of class-agnostic recall is 1054/1248 = 0.845;
  - the two-seed mean FP/image is 277/752 = 0.368.

**(b) The provisional two-seed threshold selection**, committed in `f914d31`:
- report `docs/review/d1_two_seed_provisional_threshold_r1_report.md`
  (SHA-256 `705ee356cf231f77873c62bf86631d3c5510776cdc2672777ce4caf719c7e636`), written 17:40:50;
- JSON `docs/review/generated/d1_two_seed_provisional_threshold_r1.json`
  (SHA-256 `d6ce45568709be8bb3f3ea6d9535870f5027fd40f645addeac3a4a990b627e33`), written 17:39:56.

Its results:
- the provisional setting is **confidence 0.19, class-aware NMS 0.70**;
- mean recall at that setting is 0.85497 and mean FP/image is 0.38032;
- across-class NMS 0.80 at confidence 0.19 reaches both markers (FP/image 0.24734) but was rejected,
  because its paired mAP50-95 CI lies wholly below zero.

Revision 1 of this record was written at 17:43:53 and omitted (b).

**Who had seen (b).** In chat, the Owner was asked whether they had seen (b) before deciding. They
answered **"Chưa thấy"**. The recorder (Claude) had also not read (b) when revision 1 was written. These
are self-reports and cannot be checked from the repository.

**Expectation for the binding run.** The R3 lock successor applies the same frozen rule to the same two
seeds and the same validation roster. It is therefore expected to reproduce (b)'s selection. Any
difference must be explained before a lock is approved.

**Test access.** The amendment was made before any sealed-test access.

**Direction of the change.** The stated reason is time. Seed 20261019 scored lower than the pilot, so
dropping the third seed does not discard an unfavourable known seed. A third seed could have moved the
mean either way, and that is now unknown.

## 4. What changes (D-05 Q1 only)

| D-05 Q1 | Before | After |
| --- | --- | --- |
| Final candidate seeds | 20261018, 20261019, 20261020 | **20261018, 20261019** |
| Gate statistic | Mean of 3 seeds, with standard deviation | **Mean of 2 seeds.** Each seed's value and the difference between them are reported. A two-point standard deviation is not reported as an uncertainty estimate. |
| Seed 20261020 | Required | **Not trained for the D-05 final evaluation** |

**Scope of the uncertainty that remains.** The D-02 group bootstrap CI holds the two trained weights
fixed. It describes variation over validation or test image groups only, not over training seeds.
Seed-to-seed variation is described only by the single difference between the two seeds.

## 5. What does not change

This is a summary only; the D-05 decision record and proposal govern.
- **Q2 sealed-test gates and qualifiers:**
  - mAP50 ≥ 0.60, class-aware, averaged over the classes that have test boxes (the record cites 32);
  - mAP50-95 ≥ 0.40;
  - class-agnostic recall ≥ 0.85 at IoU 0.5 and the validation-locked confidence;
  - FP/image ≤ 0.30;
  - recall ≥ 0.70 for each critical class with ≥ 20 test boxes;
  - recall ≥ 0.50 for each other class with ≥ 20 test boxes; a miss marks that class "not passed" and
    removes it from simulated behaviour, but does not fail the gate;
  - AP-small, the per-resolution breakdown and classes with < 20 test boxes are report only;
  - 95 % CIs by bootstrap over D-02 groups.
- **Q3** critical classes.
- **Q4:**
  - selection and thresholds are chosen on validation and locked before the test opens;
  - the single allowed gate recalibration is **still unused**, and still needs its own Owner decision
    before test access;
  - gates are never lowered after the test is seen.
- **Q5** latency gate.
- **Q6.**
- The one-time sealed-test rule.
- The selection rule, grid, tie-breaks and three NMS change conditions in
  `docs/review/d1_threshold_lock_r1_contract.md`
  (SHA-256 `726932dbcd32842658477c9d36f4dc7c240d412d92119e76e5b3536a4d278f0f`). Only the number of
  seeds averaged changes; see addendum 1 to that contract.

## 6. Known consequences

- With two seeds, the seed-to-seed spread is described by one difference and cannot be estimated
  reliably.
- On validation, the two known seeds differ strongly (mAP50 0.852 vs 0.731).
- On validation, confidence 0.20 is not eligible under the frozen selection rule, because the two-seed
  mean recall there is 0.845 < 0.85. The provisional selection moved to confidence 0.19, where the mean
  FP/image is 0.380. The Q2 gates themselves apply only to the sealed test.
- The two-seed selection by the R3 lock successor is now the **binding** lock input. It still needs:
  - the successor writer/verifier and its QA;
  - an inference authorization that covers the predictions it uses;
  - independent QA of the lock;
  - Owner approval of the lock record before any test access.
- The seed 20261019 predictions produced under the provisional authorization are reusable for the lock
  only if the successor's implementation record names an authorization covering that reuse. Otherwise a
  new authorization is required.

## 7. Classification

- **Verified artifact:** the hashes, times and numbers above, read from committed files.
- **Owner statement, not verifiable in the repository:** history rows 1 and 3; the §1 confirmation; the
  "Chưa thấy" answer.
- **Unknown:** what a third seed would have shown.
