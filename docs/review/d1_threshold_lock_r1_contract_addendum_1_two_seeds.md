# D1 threshold lock R1 contract — addendum 1: two seeds (follows the D-05 Q1 amendment)

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`) · Author: Claude Code (Opus 5.5), coordinating session.
Status: `FROZEN_AWAITING_INDEPENDENT_QA`.
Revision 2: rewritten before commit after the independent QA of revision 1 (SHA-256 `2348c583b6b2625560e02fe233e0a08834a8a9548142676b557ec61ee88c80c2`)
returned PARTIAL (`docs/review/d05_q1_two_seed_amendment_independent_qa_record.md`).
Append-only once committed. Does not edit `docs/review/d1_threshold_lock_r1_contract.md`
(SHA-256 `726932dbcd32842658477c9d36f4dc7c240d412d92119e76e5b3536a4d278f0f`).
Authority: `docs/review/d05_q1_two_seed_owner_amendment_2026-11-06.md`.
`sealed_test_accessed=false`, `thresholds_locked=false`.

## 1. Replacements

| Contract location | Original text (abridged) | Replaced by |
| --- | --- | --- |
| Title (line 1) | "three-seed threshold lock" | **two-seed** threshold lock |
| Fixed inputs, candidate family | "seeds `20261018`, `20261019`, `20261020`" | seeds **`20261018`, `20261019`** |
| Line 19, R3 successor duties | "verify all three seeds have the same 376 frame stems…"; "require one shared `(confidence, nms_iou, agnostic_nms)` for all three weights" | verify **both** seeds …; one shared setting for **both** weights |
| Line 25, scoring | "take the arithmetic mean across three seeds"; "Report each seed and sample standard deviation"; "three-seed mean" of mAP50-95 | arithmetic mean across **two** seeds. Report each seed, the mean and the **difference between the two seeds**; no two-point standard deviation as uncertainty. **Two-seed** mean of mAP50-95. |
| Line 26, per-seed check | "reaches recall ≥ 0.85 in each seed" | unchanged wording; "each seed" means the two seeds |
| Line 27, NMS change rule | "same group draws across all three seeds and both NMS settings. Compute each draw's three-seed mean…"; "three-seed mean held-out recall and FP/image"; "its prespecified three-seed confidence point" | same group draws across **both seeds** and both NMS settings; each draw's **two-seed** mean before the difference; **two-seed** mean held-out recall and FP/image; its prespecified **two-seed** confidence point |
| Line 28, pilot evidence | "Neither is preapproved for this three-seed lock" | "… for this **two-seed** lock" |
| Line 32, future lock record | "after all three runs pass independent result QA"; "exactly three candidates, one identical confidence and NMS setting for all three" | after **both** runs pass independent result QA (both have; see the amendment §3); exactly **two** candidates, one identical setting for **both** |
| Line 34, planned invocation | `--reports <seed18-R3> <seed19-R3> <seed20-R3>` | `--reports <seed18-R3> <seed19-R3>`. The executable command is still to be pinned in the successor's implementation record. |
| **Catch-all** | any remaining reference to three seeds, three weights, three reports or seed 20261020 | means the two seeds 20261018 and 20261019, their two weights and their two reports |

**Uncertainty scope.** The paired D-02 group bootstrap holds both trained weights fixed. It describes
variation over validation image groups, not over training seeds.

## 2. Unchanged

All of the following stay exactly as frozen:
- the R3 binding decision, and the requirement for an independently QA'd R3 lock writer/verifier and
  final reader;
- the confidence grid (0.05–0.95, plus the fine grid 0.15–0.30 in steps of 0.01);
- the NMS grid and modes;
- the eligibility rule;
- every tie-break;
- the three NMS change conditions, with 1,000 rounds and seed 20261018;
- the stop-without-lock condition;
- per-seed inference authorization;
- Owner approval before test access;
- the Q4 single-recalibration rule;
- the sealed-test boundary.

## 3. Existing schema

`detector/m1/contract.py` fixes three seeds (`SEEDS`, line 37) and requires exactly three seeds, weights
and reports (lines 364–397). It therefore cannot read a two-candidate lock. The lock must go through the
R3 successor writer/verifier/reader, which must require exactly the two seeds above. Existing pinned files
are not edited.

## 4. Relation to the provisional two-seed run

`docs/review/d1_two_seed_provisional_threshold_r1_report.md` (commit `f914d31`) applied this rule as a
non-binding diagnostic. It selected confidence 0.19 with class-aware NMS 0.70.
- The binding selection must be computed by the R3 successor writer, and is expected to reproduce that
  result.
- The provisional output must not be re-labelled as the lock.
- Reusing its seed 20261019 predictions needs a named authorization that covers the reuse (see the
  amendment §6).
