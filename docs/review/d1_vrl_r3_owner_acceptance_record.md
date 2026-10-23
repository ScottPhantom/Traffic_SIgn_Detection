# D1-VRL-R3 — owner acceptance record

Date: 2026-10-23 (`Asia/Ho_Chi_Minh`)
Status: `OWNER_ACCEPTED_AS_DERIVED_VALIDATION_LABELS__NOT_YET_EVALUATION_AUTHORITY`
Recorded by: the D1-VRL author session (Claude Code), on the owner's instruction

## Owner instruction (2026-10-23, Claude Code session)

> "Lập biên bản owner acceptance cho D1-VRL-R3 (chấp nhận L1 R039 ~2 px như hiện trạng), rồi commit
> cục bộ toàn bộ chuỗi D1-VRL R1–R3, chưa push."

("Record the owner acceptance for D1-VRL-R3, accepting L1, R039 at about 2 px, as is; then commit
the whole D1-VRL R1–R3 chain locally, without pushing.")

## What is accepted

The owner accepts **D1-VRL-R3** as the project's derived validation label set, superseding
D1-VRL-R1 (QA FAIL) and D1-VRL-R2 (QA PASS with M1). The accepted package is identified by:

| Item | SHA-256 |
| --- | --- |
| `detector/m1/val_relabel_r3.py` | `34b89e320775abb8bf6186558ce03666c221331969c978836b01342e2e0d72ec` |
| `docs/review/generated/d1_vrl_r3_manifest.json` | `87dd0fd9ecea85745f613a788ef70ae830d396fc9e747f233db0c6fc536b8e07` |
| `docs/review/d1_vrl_r3_box_review_notes.csv` | `b653abb393fa278a4737cf3e08160e1c312d5b1b11d96cba029da8f3e4f4a385` |
| derived label roster `data/processed/m1_yolo_val_vrl_r3/labels/val/` | `dc72ebd944a38535d4f766ba4f8babc60cb6732dfcd253ed0e8d79dc86eb8343` |
| independent QA record `docs/review/d1_vrl_r3_independent_qa_record.md` | `33ef3935…` (PASS, 0 Critical / 0 High / 0 Medium / 4 Low) |

**Contents.** The R4 validation labels (`labels_sha256` `e64345bb…`) plus 64 added boxes:

- 38 hand-drawn;
- 23 pixel re-fitted;
- 3 re-fitted and tightened.

There are 40 ignore regions, for the proposals whose locator is ≤ 17.5 px.

## Low findings accepted as is

- **L1 — R039 bottom.** The bottom of R039 (y2 = 70) stops at the top of the bracket, about 2 px
  short of the disc's lower ring. The owner accepts this as is; the QA records that it does not
  change any match.
- **L2 — eye-column rule.** The eye-column rule cannot detect a wrong eye estimate. This is
  disclosed.
- **L3 — forged rewrite.** A coordinated rewrite verifies under a forged module. The anchor is the
  module and manifest hashes above, as pinned in the QA record.
- **L4 — R090/R091 bottoms.** The bottoms of R090 and R091 are about 3 px short. This is a
  disclosed limit.

## What this acceptance does NOT do

- It does **not** make the derived labels the D-05 evaluation authority. That requires a
  QA-passed re-evaluation contract that keeps IoU-0.5 matching and reports the circular
  ignore-region part separately.
- It does not change any gate, NMS or confidence setting. It does not replace R10, whose result
  stays the authoritative corrected-validation baseline until a re-evaluation passes QA.
- The diagnostic 150 FP / 0.399 FP/image may be cited only as a diagnostic, and it is still above
  the 0.30 gate. The 110 FP / 0.293 figure must not be cited as a gate result.
- Validation pixels, labels and predictions remain forbidden for training, augmentation or
  mining. The sealed test stays closed. Nothing is pushed or uploaded.

## Next state

- Allowed: draft a re-evaluation contract on the D1-VRL-R3 labels, with its own independent QA
  before any run.
- Still open from D1-EA-R1 and D1-VLA-R1: the NMS contract with per-class recall gates (class 46),
  the critical classes 7, 32 and 41, and the Track A/B smoke contracts on Colab L4.
