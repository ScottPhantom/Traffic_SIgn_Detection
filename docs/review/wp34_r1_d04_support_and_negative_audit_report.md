# M0-WP34-R1 — corrected D-04 decision support and negative audit

Status: `WP34_R1_AWAITING_QA_REVIEW`
Boundary: `D04_DECISION_SUPPORT_AND_NEGATIVE_AUDIT_PROVISIONAL_NOT_OWNER_DECISION_NO_SPLIT_NO_TRAINING`

Corrects the QA-failed WP34 (`docs/review/wp34_independent_qa_record.md`: 1 P1, 1 P2, 4 P3). The
initial WP34 package stays byte-identical. Nothing here is an owner decision for the 42 pending
classes, a split or a training authorization.

## Part A — D-04 support (54 WP33 classes × 54 D-02 groups)

| Option | Classes |
| --- | --- |
| `KEEP_FULL` | 27 |
| `OWNER_TRAIN_WITH_ENRICHMENT` | 12 |
| `KEEP_TRAIN_AND_TEST_NO_VAL` | 6 |
| `KEEP_TRAIN_ONLY_UNVERIFIED` | 9 |

- **KEEP_FULL** (27): 0 W.224 (312 img/11 grp), 2 P.102 (467 img/11 grp), 3 R.302a (454 img/11 grp), 4 W.205a (33 img/3 grp), 5 W.207 (256 img/12 grp), 6 W.201a (163 img/5 grp), 7 P.123a (247 img/6 grp), 8 I.434a (213 img/5 grp), 10 P.130 (1030 img/19 grp), 12 R.415a (279 img/7 grp), 13 W.245a (371 img/12 grp), 14 P.106a (47 img/4 grp ⚠dominated), 17 P.124a (105 img/4 grp), 18 P.107 (154 img/3 grp), 19 P.124d (29 img/3 grp), 22 W.221b (92 img/3 grp), 23 P.111a+P.111b (465 img/8 grp), 26 W.246a (80 img/4 grp), 30 S.505a (138 img/3 grp), 32 P.123b (186 img/7 grp), 34 P.108a (82 img/5 grp), 39 P.127 (342 img/7 grp), 40 P.127 (210 img/3 grp), 41 P.127 (274 img/13 grp), 45 I.407a (190 img/5 grp), 46 P.131a (423 img/8 grp), 50 W.201b (105 img/3 grp)
- **OWNER_TRAIN_WITH_ENRICHMENT** (12): 1 W.205c (22 img/1 grp), 15 W.203c (29 img/1 grp), 16:2.2 P.117*2.2 (18 img/1 grp), 16:2.5 P.117*2.5 (9 img/1 grp), 21 W.203b (11 img/1 grp), 33 W.202b (19 img/1 grp), 42 R.301e (21 img/1 grp), 43:2.5 W.239b*2.5 (22 img/1 grp), 43:2.7 W.239b*2.7 (5 img/1 grp), 44 W.233 (3 img/1 grp), 47 P.124b (16 img/1 grp), 51 W.246c (5 img/1 grp)
- **KEEP_TRAIN_AND_TEST_NO_VAL** (6): 9 R.303 (43 img/2 grp), 11 I.409 (26 img/2 grp ⚠dominated), 20 P.103a (52 img/2 grp), 25 S.505a (25 img/2 grp), 28 S.505a (27 img/2 grp ⚠dominated), 38 P.127 (114 img/2 grp ⚠dominated)
- **KEEP_TRAIN_ONLY_UNVERIFIED** (9): 16:2.0 P.117*2.0 (43 img/1 grp), 24 P.129 (56 img/1 grp), 27 W.225 (36 img/1 grp), 29 P.104 (45 img/1 grp), 35 P.137 (87 img/1 grp), 36 P.139 (75 img/1 grp), 37 W.205b (47 img/1 grp), 48 W.210 (41 img/1 grp), 49 P.124c (119 img/1 grp)

- `largest_group_box_share` is the share of the class's **boxes** in its largest group (QA P3-3).
  Classes above 80% are flagged `dominated`: their extra groups add little
  independent evidence: 11 I.409 (81%), 14 P.106a (86%), 28 S.505a (96%), 38 P.127 (84%).
- **Height families (QA P2-1).** P.117 (2,0 / 2,2 / 2,5 m) and W.239b (2,5 / 2,7 m) are each
  one physical sign shape with a printed value. All their value classes are now trained
  (2,0 m as train-only, the others under D-04 part 1), so no single value class can absorb the
  others. The value reading stays **unverified** for the whole family until each value is
  evaluated on real independent images; behaviour must not use the value before that.
- The 12 classes approved in D-04 part 1 show `OWNER_TRAIN_WITH_ENRICHMENT`.

## Part B — negative audit (zoomed re-review)

Each negative was re-reviewed on its own page: both labelled neighbours, then the negative at
1,600 px width so that small distant signs are visible (`docs/review/assets/wp34_r1/negatives/`). `UNCLEAR` is no longer allowed.

- True negatives usable as detector background: 1 (0544).
- Frames with an unlabelled visible sign: 24. They must never be used as
  background; proposed handling is quarantine from detector training until relabelled in a
  derived label set (owner decision).

| Stem | Visible classes | Rationale |
| --- | --- | --- |
| 0060 | 46 | Red-rimmed blue cls46 disc left of the HALO shopfront is clearly visible at 1600 px where 0059 and 0062 label it; not a valid background frame |
| 0061 | 46 | Same cls46 disc as 0060 remains visible one frame later; quarantine until relabelled |
| 0187 | 49 | The cls49 sign labelled in the adjacent frame is still in view at small size; quarantine until relabelled |
| 1514 | 29 39 40 | cls29 sign (labelled in 1516) and the 80/60 plates cls39/40 (labelled further along the same chain e.g. 1540) are visible; quarantine until relabelled |
| 1515 | 29 39 40 | Same cls29 sign and cls39/40 plates as 1514 one frame later; quarantine until relabelled |
| 1703 | 39 40 | cls39 and cls40 sign faces visible; the cls10 sign of the neighbours is hidden behind the truck so it is not listed (QA P3-1 correction) |
| 1704 | 39 40 | Same occlusion run as 1703; cls39 and cls40 visible and cls10 hidden by the truck |
| 1705 | 39 40 | Same occlusion run as 1703; cls39 and cls40 visible and cls10 hidden by the truck |
| 1706 | 39 40 | Same occlusion run as 1703; cls39 and cls40 visible and cls10 hidden by the truck |
| 1707 | 39 40 | Same occlusion run as 1703; cls39 and cls40 visible and cls10 hidden by the truck |
| 1708 | 39 40 | End of the occlusion run; cls39 and cls40 visible and cls10 hidden by the truck |
| 2015 | 32 | Small red-rimmed cls32 disc visible to the right of the blue board in the 1600 px view (confirms QA P1 finding) |
| 2016 | 32 | Same cls32 disc as 2015 one frame later (QA P1 finding) |
| 2017 | 32 | Same cls32 disc as 2015 two frames later (QA P1 finding) |
| 2031 | 32 | Red-rimmed disc partly cut at the right edge where 2030 has a labelled box; the blue alcohol board is not a traffic-sign class (QA P1 finding) |
| 2051 | 32 | cls32 disc of the neighbouring frames still in view (QA P1 finding) |
| 2723 | 46 | The cls3 sign of 2722 has left the frame (QA P3 rationale correction) but a small distant blue disc is visible down the road where 2724 labels cls46; quarantined conservatively rather than used as background |
| 2766 | 13 | cls13 sign of the neighbouring frames visible (QA P3-1 class correction) |
| 2793 | 50 | Small yellow cls50 curve-warning triangle visible down the right roadside where 2798 labels cls50 (QA P3-2 finding) |
| 2794 | 50 | Same cls50 triangle as 2793 (QA P3-2 finding) |
| 2795 | 50 | Yellow cls50 triangle visible between the trees at the right roadside in the raw frame (QA P3-2 finding) |
| 2796 | 50 | Same cls50 triangle as 2795 (QA P3-2 finding) |
| 2797 | 50 | Same cls50 triangle as 2795 one frame before the labelled 2798 (QA P3-2 finding) |
| 2999 | 6 13 38 | The cls13 ĐI CHẬM triangle is cut at the right edge and the distant board carrying the cls38 speed discs and the cls6 triangle labelled in 3000 is already visible down the road; quarantine until relabelled |

## Artifacts

- Class support `docs/review/generated/wp34_r1_d04_class_support.csv`, negative audit `docs/review/generated/wp34_r1_negative_audit.csv`, notes
  `docs/review/wp34_r1_negative_review_notes.csv` (pinned), manifest `docs/review/generated/wp34_r1_manifest.json`.
