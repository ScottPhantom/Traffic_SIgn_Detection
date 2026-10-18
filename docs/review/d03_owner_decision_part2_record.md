# D-03 owner decision, part 2 — semantic rows and taxonomy policies

Status: `OWNER_APPROVED_D03_DECISIONS_COMPLETE_DERIVED_RELABEL_PENDING`
Decision date: `2026-10-17` (`Asia/Ho_Chi_Minh`)
Tables: `docs/review/generated/d03_owner_decisions_part2.csv`,
`docs/review/generated/d03_owner_policies.csv`
Visual evidence: `docs/review/assets/d03_visual/d03_10_semantic.jpg`

With part 1 (`docs/review/d03_owner_decision_part1_record.md`), every one of the 52 DATASET01
taxonomy rows now has an owner decision.

## Rows

| Class | Current | Decision |
| --- | --- | --- |
| 12 | R.415a | Keep one class for all lane-layout variants |
| 19, 35, 36, 49 | P.124d, P.137, P.139, P.124c | Keep each composite sign as its own class |
| 23 | P.111 | **Split into QCVN variants P.111a–d** (relabel needed) |
| 25, 28, 30 | S.505a plates | Keep, renamed "Biển phụ loại xe: …"; never interpreted alone |
| 31 | Camera | Route to UNKNOWN: not trained; kept as out-of-taxonomy evaluation samples |

## Policies

- Speed limits (38, 39, 40, 41): one class per value.
- Height values (16 P.117, 43 W.239b): **split by value** (relabel needed). This overrides the
  part-1 note that all height values share one class.
- Supplementary S.505a: kept as renamed classes; behaviour uses the associated main sign.
- UNKNOWN: no trained UNKNOWN class; reject below a validation-calibrated threshold (M3);
  out-of-taxonomy signs are used only for evaluation.

## Work required before G0.5 can pass

All decisions are made, but three changes need a derived label set (raw labels stay immutable):

1. Relabel every class-23 box as P.111a, b, c or d.
2. Read the value on every class-16 and class-43 box and assign a per-value class.
3. Correct stem `0776` line 7 from class 18 to the height-limit class (part 1 follow-up).

Until that derived label set exists and is verified, G0.5 remains BLOCKED. Split generation and
training remain unauthorized.

## Revision 2026-10-17 (append-only, after WP33 review)

- Class 23: the WP33 atlas (`docs/review/assets/wp33/`) shows that essentially all 465 boxes are
  one combined design — a moped (P.111a) and a motorised three-wheeler (P.111b) in one circle — which
  is not a single QCVN variant. The owner revised the decision from "split into P.111a–d" to **keep
  one class, renamed "P.111a+P.111b — Cấm xe gắn máy và xe ba bánh có động cơ (biển ghép)"**.
- Height values: owner approved the WP33 readings (P.117: 2,0 m ×43, 2,5 m ×9, 2,2 m ×18;
  W.239b: 2,5 m ×22, 2,7 m ×5). Boxes whose value cannot be read (16: 2088:2, 2278:2, 2279:2; the
  class-18 mislabel 0776:7) are excluded from training; 0776:7 loses its class-18 label.
