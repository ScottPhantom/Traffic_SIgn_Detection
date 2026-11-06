# D1 two-seed R3 validation threshold — Owner lock approval

Date: 2026-11-06 22:14 (`Asia/Ho_Chi_Minh`).
Recorded by: Claude Code (Opus 5.5), coordinating session, on the Owner's instruction in chat.
Append-only once committed. `sealed_test_accessed=false`.

## Owner decision (verbatim)

The coordinating session asked, in chat: "Anh có duyệt record khóa ngưỡng conf 0,19 / NMS IoU 0,70
theo lớp không?"

The Owner answered: "Duyệt khóa".

Before asking, the coordinating session independently:
- re-ran the R3 `verify` command on the record and proof (PASS);
- checked both independent QA verdicts (PASS);
- checked that the result QA and the result report contain the full record and proof hashes below.

The Owner had seen the provisional two-seed validation result before this decision. The selection rule
was frozen in the threshold-lock contract and its two-seed addendum before the provisional run, and
the R3 writer reproduced that provisional selection exactly.

## What is approved

The versioned two-seed validation threshold record and its R3 proof:

| File | SHA-256 |
| --- | --- |
| `docs/review/generated/d1_threshold_lock_r1.json` | `d39b0466a5285979c3da63546ebbd56d26d0030081f4df9fa6c75fc8ee96167d` |
| `docs/review/generated/d1_threshold_lock_r1_r3_proof.json` | `2d2fbd7cf99ee9e8b1349a55cf40b0182764efe9f7d4cd5078c06c5f8aa72e77` |

Selection: **confidence 0.19, class-aware NMS IoU 0.70** (`agnostic_nms=false`), shared by both
candidates:

| Seed | Weight SHA-256 |
| --- | --- |
| 20261018 | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` |
| 20261019 | `046cfea22e6daf45342063b58cd9082aa4b0b0528a3a6d9af7ac23bbac015bce` |

Validation values at the selection (two-seed mean):
- class-agnostic recall 0.85497;
- FP/image 0.38032;
- exact-class mAP50–95 0.56486.

Seed 20261019 alone has recall 0.82051. The mean FP/image is above the D-05 marker of 0.30.

## Evidence bound by this approval

| File | SHA-256 |
| --- | --- |
| `docs/review/d1_threshold_lock_r1_result_independent_qa_record.md` (`Verdict: PASS`) | `c113a80ef295c3ec43ef86ad07e28ad95d3a6ce2ab61fe30b5cae1392b308261` |
| `docs/review/d1_threshold_lock_r1_report.md` (`AWAITING_OWNER_APPROVAL` before this record) | `7bd92b26637fce1c0d677e94e4e4e69411c637c016a0f31b339e7c73a33807f3` |
| `docs/review/d1_two_seed_lock_r1_inference_binding_independent_qa_record.md` (`Verdict: PASS`) | `318bc488eab770d6ddd3991c25a006d1266dca62651d18cbb5fc6ff5410bb401` |
| `docs/review/d1_threshold_lock_r1_contract.md` | `726932dbcd32842658477c9d36f4dc7c240d412d92119e76e5b3536a4d278f0f` |
| `docs/review/d1_threshold_lock_r1_contract_addendum_1_two_seeds.md` | `cefbdc627266588735e0369c42b1fe426e85e78c38b3eaddef2f61ac9484a82b` |
| `docs/review/d05_q1_two_seed_owner_amendment_2026-11-06.md` | `4d451a3a4174d1b2ff34c5acc9d6683e10062e1672f01104ce76edd12585e807` |
| `tmp/d1_two_seed_lock_r1_inputs/seed_20261018_r3_report.json` (Git-ignored) | `926a850f491756fdc72c8f937e2f3433fca058bbe9969501b24a37929fc3ad31` |
| `tmp/d1_two_seed_lock_r1_inputs/seed_20261019_r3_report.json` (Git-ignored) | `c468357d6ed67aac7e90460f9d40b553db32c2df765078f89ceef7c326bfded1` |

## Effect and limits

- With this record committed, the R3 reader `read_for_final` may return the selection to the final
  evaluation scorer, provided every other gate of that scorer passes.
- This approval does **not**:
  - authorize opening, listing, counting or scoring the sealed test `afa03d4b…`; that needs a separate
    Owner opening approval bound to a finalized, QA-passed final-evaluation contract;
  - decide the single D-05 Q4 gate recalibration;
  - decide the test-label handling (current labels or a prediction-blind review);
  - change any D-05 gate;
  - change the app's demo threshold;
  - claim safety or performance on driving scenes.
- **Retention.** The seed-20261019 weight, its run contract and both seed reports live under the
  Git-ignored `tmp/d1_two_seed_lock_r1_inputs/`, as recorded in the lock. They must be kept unchanged
  until the final evaluation is complete. The verifier and reader refuse missing or changed files.
- The intervals in the proof resample D-02 image groups with both weights fixed. They do not measure
  variation across training seeds.
