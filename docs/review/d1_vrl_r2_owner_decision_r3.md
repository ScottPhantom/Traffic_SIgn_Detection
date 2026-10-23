# D1-VRL-R2 — owner decision after independent QA: build D1-VRL-R3

Date: 2026-10-23 (`Asia/Ho_Chi_Minh`)
Status: `OWNER_AUTHORIZED_R3_BUILD__ADOPTION_PENDING_QA_AND_OWNER_ACCEPTANCE`
Author: the D1-VRL-R2 author session (Claude Code)

The independent QA `docs/review/d1_vrl_r2_independent_qa_record.md` (SHA-256 `07584056…`) passed
D1-VRL-R2 with 0 Critical, 0 High, 1 Medium and 4 Low findings. It made owner acceptance
conditional on resolving M1. D1-VRL-R2 (module `2d707625…`, manifest `e23b725f…`) stays as built
and is superseded by D1-VRL-R3.

## Owner instruction (2026-10-23, Claude Code session)

> "Làm D1-VRL-R3: sửa R039 (cạnh trái về ~6–7) và R046 (cạnh dưới về ~28), thêm kiểm tra L3 (box
> vẽ tay phải có cột mắt, lệch ≤ 1 px), rồi mở QA độc lập cho R3."

("Build D1-VRL-R3: fix R039 (left edge to about 6–7) and R046 (bottom edge to about 28), add the
L3 check (hand-drawn boxes must have eye columns, deviation ≤ 1 px), then open independent QA for
R3.")

## Applied

- **M1, R039 (1223).** Left edge 0 → **6**. The author's own row profiles at y = 54/57/60 change
  from the sky (about 240) to the rim at x = 6. The dark pixels at x = 0 belong to an adjacent
  object at the frame edge. The QA re-draw gave 6.5.
- **L1, R046 (1229).** Bottom edge 23 → **28**. Column profiles at x = 128/135/142 stay dark to
  y = 25/26/27 and turn bright at y = 27/28/28. The lower rim and the bracket overlap there, so the
  box is drawn through it, consistent with R045 on 1228 (bottom 30). The QA re-draw gave 28.0.
- For both boxes the eye columns record the R3 re-draw itself, and the note says so.
- **L3.** The R3 builder refuses a `HAND_DRAWN` row without integer eye columns. It also refuses one
  whose final box differs from the eye estimate by more than 1 px on any side, or by any amount on
  the unsnapped dark frames 1823–1837.
- **Not changed:**
  - L2 (R090/R091 bottoms about 3 px short, at the tolerance edge; QA: optional). Recorded as a
    known limit.
  - L4 (coordinated-rewrite anchor). The QA pins remain the external anchor.

## Not decided here

Adoption of the derived labels as the evaluation authority, any gate, NMS or confidence change,
training, and the sealed test.

## Author-found defect in the D1-VRL-R2 notes

The R2 notes row R097 has an unquoted comma in its note. The CSV therefore reads as 15 fields, and
the note is truncated after "a faint tail to 332". The box values (296, 421, 331, 460) are
unaffected, so no R2 number changes. R3 rewrites the notes with correct quoting. The R3 builder
refuses any notes row whose field count differs from the header.
