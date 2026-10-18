# D-03 owner decision, part 1 — 42 low-risk taxonomy rows

Status: `OWNER_APPROVED_PART_1_OF_D03`
Decision date: `2026-10-17` (`Asia/Ho_Chi_Minh`)
Decision table: `docs/review/generated/d03_owner_decisions_part1.csv`

The owner reviewed the 42 WP8 rows marked `KEEP_CURRENT` (23) or `CORRECT_CODE_OR_NAME_PROPOSAL`
(19) one class at a time, with three DATASET01 crops per class
(`docs/review/assets/d03_visual/d03_19_corrections.jpg`, `d03_23_keep.jpg`).

## Outcome

- 40 classes: WP8 recommendation accepted as proposed.
- Class 3 (R.302a): owner kept the current name "Phải đi vòng sang bên phải / Right Turn Only".
- Class 24 (P.129): owner kept the current name "Kiểm tra / Customs Checkpoint".
- Class 1 (W.205c): kept, including the English name "Equal-level Intersection".
- Classes 38, 39, 40, 41 take code P.127 with the value in the name and stay separate classes per
  value; whether speed limits should be merged is part of the parameterized-sign policy (pending).
- Classes 44 and 51: code and name kept; whether to keep the classes at all is a D-04 question.

## Label follow-ups

- Class 18 (P.107): the owner identified the first WP8 sample, stem `0776` line 7, as a
  height-limit sign (P.117) mislabelled as class 18. It must be corrected in a derived label set;
  raw labels stay immutable.
- Class 34 sample stem `0689` and class 40 sample stem `1539`: the owner confirmed both labels are
  correct.

## Still pending for D-03 (G0.5 remains BLOCKED)

- 9 `SEMANTIC_REVIEW_REQUIRED` rows: 12, 19, 23, 25, 28, 30, 35, 36, 49.
- 1 `OUT_OF_SCOPE_PROPOSAL` row: 31 (camera surveillance).
- Policies: parameterized signs (speed and height values), supplementary S.505a, and UNKNOWN routing.

No raw label, earlier package or the historical decision template was changed. Split generation
and training remain unauthorized.
