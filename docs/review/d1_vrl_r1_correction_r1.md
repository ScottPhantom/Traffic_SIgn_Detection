# D1-VRL-R1 — correction R1 after independent QA, and owner re-decision for D1-VRL-R2

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)
Status: `CORRECTION_APPENDED_AFTER_INDEPENDENT_QA_FAIL__OWNER_REDECIDED_GEOMETRY_FOR_R2`
Author: the D1-VRL-R1 author session (Claude Code)

This append-only record answers `docs/review/d1_vrl_r1_independent_qa_record.md` (FAIL, 0
Critical, 1 High, 0 Medium, 5 Low). D1-VRL-R1 (module `9fba1008…`, manifest `3fd91263…`) stays
as built and is **superseded** by D1-VRL-R2. Where the owner scope record
(`d1_vrl_r1_owner_scope_record.md`, `a96e55f4…`), the D1-VRL-R1 implementation record or report
disagree with this file, this file wins.

## H1 — corrected premise

The geometry decision said the 72 proposals without a colour re-fit are "11–17 px low-saturation
discs on the 1208–1229 and 1342–1357 poles", and the notes gave every one the reason "small
low-saturation sign". That was the author's description, and it is wrong. Measured on the longer
side of the locator:

| Locator size | Of the 72 | Of the 6 partial re-fits |
| --- | ---: | ---: |
| ≤ 17.5 px | 40 | 0 |
| 17.5–25 px | 20 | 0 |
| 25–40 px | 7 | 5 |
| > 40 px | 5 | 1 |

The 72 also include frames 1236 and 1242–1245, outside the named poles. Several are large,
saturated and legible (P.111a+b discs 61–80 px on 1242–1245, the P.130 disc on 1236, the
"40"/"60" discs on 1223–1229). The colour fit missed them because the component merged with or
split from the neighbouring disc or plate, not because they are small. The QA's measurement is
accepted in full.

## Owner re-decision (2026-10-22)

After reading the QA, the owner instructed, in the Claude Code session:

> "Ghi bản sửa H1, rồi làm D1-VRL-R2: tự vẽ tay box độc lập cho các mục > 17,5 px không fit
> được (ít nhất 12 mục ≥ 25 px), giữ ~40 đĩa ≤ 17,5 px làm vùng bỏ qua với lý do đúng, sửa luôn
> L1–L4."

("Record the H1 correction, then build D1-VRL-R2: hand-draw independent boxes for the items
> 17.5 px that could not be fitted (at least the 12 items ≥ 25 px), keep the ~40 discs ≤ 17.5 px
as ignore regions with a truthful reason, and also fix L1–L4.")

Applied as follows:

- **Hand-drawn (38):** every proposal > 17.5 px without an accepted re-fit — the 32 of the 72 and
  the 6 partial re-fits (R040, R042, R044, R049, R090, R091), which the QA agreed were partial and
  which are equally "not fitted". Drawn by eye without the model box, see the R2 notes.
- **Ignore regions (40):** exactly the proposals ≤ 17.5 px, each with its measured size as reason.
- **Kept (26):** the accepted re-fits; L1 tightens three of them (R095, R097, R103). For R092 the
  red-ring profile ends at column 359, so its right edge 360 is kept; that disagreement with L1 is
  recorded with its evidence.
- **L2–L4** are fixed in the R2 builder (see its implementation record). **L5** (coordinated
  rewrite) remains a known limit of self-hashed packages; the QA record's pins are the anchor.

## Next state

- D1-VRL-R1: not accepted, not the evaluation authority.
- D1-VRL-R2: build authorized by the instruction above; adoption needs independent QA, an owner
  acceptance record and a QA-passed re-evaluation contract.
- Unchanged NO-GO: gate/NMS/confidence changes, R10 replacement, training on validation data,
  smoke runs, the sealed test.
