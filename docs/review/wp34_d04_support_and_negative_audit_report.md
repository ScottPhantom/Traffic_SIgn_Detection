# M0-WP34 — D-04 decision support on WP33 labels and negative audit

Status: `WP34_AWAITING_QA_REVIEW`
Boundary: `D04_DECISION_SUPPORT_AND_NEGATIVE_AUDIT_PROVISIONAL_NOT_OWNER_DECISION_NO_SPLIT_NO_TRAINING`

Inputs are pinned: WP33 derived boxes and taxonomy (independent QA PASS), the D-02 group registry
(owner approved D02-P1) and the inventory. Stem 0248 stays quarantined. Nothing here is an owner
decision, a split or a training authorization.

## Part A — D-04 proposal per class

Counts use train-eligible WP33 boxes and independent D-02 groups. A class needs at least three
groups so that train, validation and test can each receive one.

| Proposed option | Classes |
| --- | --- |
| `KEEP_FULL` | 27 |
| `DROP_FROM_V1_COLLECT_MORE` | 12 |
| `KEEP_TRAIN_AND_TEST_NO_VAL` | 6 |
| `KEEP_TRAIN_ONLY_UNVERIFIED` | 9 |

- **KEEP_FULL** (27): 0 W.224 (312 img/11 grp), 2 P.102 (467 img/11 grp), 3 R.302a (454 img/11 grp), 4 W.205a (33 img/3 grp), 5 W.207 (256 img/12 grp), 6 W.201a (163 img/5 grp), 7 P.123a (247 img/6 grp), 8 I.434a (213 img/5 grp), 10 P.130 (1030 img/19 grp), 12 R.415a (279 img/7 grp), 13 W.245a (371 img/12 grp), 14 P.106a (47 img/4 grp), 17 P.124a (105 img/4 grp), 18 P.107 (154 img/3 grp), 19 P.124d (29 img/3 grp), 22 W.221b (92 img/3 grp), 23 P.111a+P.111b (465 img/8 grp), 26 W.246a (80 img/4 grp), 30 S.505a (138 img/3 grp), 32 P.123b (186 img/7 grp), 34 P.108a (82 img/5 grp), 39 P.127 (342 img/7 grp), 40 P.127 (210 img/3 grp), 41 P.127 (274 img/13 grp), 45 I.407a (190 img/5 grp), 46 P.131a (423 img/8 grp), 50 W.201b (105 img/3 grp)
- **DROP_FROM_V1_COLLECT_MORE** (12): 1 W.205c (22 img/1 grp), 15 W.203c (29 img/1 grp), 16:2.2 P.117*2.2 (18 img/1 grp), 16:2.5 P.117*2.5 (9 img/1 grp), 21 W.203b (11 img/1 grp), 33 W.202b (19 img/1 grp), 42 R.301e (21 img/1 grp), 43:2.5 W.239b*2.5 (22 img/1 grp), 43:2.7 W.239b*2.7 (5 img/1 grp), 44 W.233 (3 img/1 grp), 47 P.124b (16 img/1 grp), 51 W.246c (5 img/1 grp)
- **KEEP_TRAIN_AND_TEST_NO_VAL** (6): 9 R.303 (43 img/2 grp), 11 I.409 (26 img/2 grp), 20 P.103a (52 img/2 grp), 25 S.505a (25 img/2 grp), 28 S.505a (27 img/2 grp), 38 P.127 (114 img/2 grp)
- **KEEP_TRAIN_ONLY_UNVERIFIED** (9): 16:2.0 P.117*2.0 (43 img/1 grp), 24 P.129 (56 img/1 grp), 27 W.225 (36 img/1 grp), 29 P.104 (45 img/1 grp), 35 P.137 (87 img/1 grp), 36 P.139 (75 img/1 grp), 37 W.205b (47 img/1 grp), 48 W.210 (41 img/1 grp), 49 P.124c (119 img/1 grp)

Option meanings:

- `KEEP_FULL`: normal train/validation/test treatment.
- `KEEP_TRAIN_AND_TEST_NO_VAL`: one group to train, one to test; thresholds for this class cannot
  be tuned on validation.
- `KEEP_TRAIN_ONLY_UNVERIFIED`: the whole group goes to train; the class is never evaluated and
  every report must label it unverified.
- `DROP_FROM_V1_COLLECT_MORE`: not trained in v1; its boxes are evaluated as UNKNOWN under the
  D-03 UNKNOWN policy until more independent data is collected.

The owner may override any row, for example by keeping a small class train-only.

## Part B — negative audit (25 empty-label frames)

Each negative was reviewed between its previous and next labelled frames
(`docs/review/assets/wp34/negatives/`). Decisions: {'UNLABELLED_SIGN_PRESENT': 13, 'TRUE_NEGATIVE': 7, 'UNCLEAR': 5}.

| Stem | Decision | Visible classes | Rationale |
| --- | --- | --- | --- |
| 0060 | UNLABELLED_SIGN_PRESENT | 46 | Blurred frame of the same HALO street as 0059/0062; the small cls46 no-parking disc beside the traffic light is still visible but unlabelled. |
| 0061 | UNLABELLED_SIGN_PRESENT | 46 | Blurred frame between 0059 and 0062; the same cls46 disc near the traffic light is visible but unlabelled. |
| 0187 | UNLABELLED_SIGN_PRESENT | 49 | Same gantry junction as 0186/0188; both cls49 signs on the gantry and pole are clearly visible but unlabelled. |
| 1514 | UNLABELLED_SIGN_PRESENT | 29 39 40 | Same highway as 1516: the cls29 sign under the 80/60 speed plates beside the alcohol billboard is clearly visible but unlabelled. |
| 1515 | UNLABELLED_SIGN_PRESENT | 29 39 40 | Same highway as 1516: the cls29 sign and the 80/60 speed plates are clearly visible but unlabelled. |
| 1703 | UNLABELLED_SIGN_PRESENT | 10 | Same red car 51G 502.98 and riders as 1709; the small distant cls10 sign labelled in 1709 is visible at the same spot but unlabelled. |
| 1704 | UNLABELLED_SIGN_PRESENT | 10 | Same red car 51G 502.98 and riders as 1709; the small distant cls10 sign labelled in 1709 is visible at the same spot but unlabelled. |
| 1705 | UNLABELLED_SIGN_PRESENT | 10 | Same red car 51G 502.98 and riders as 1709; the small distant cls10 sign labelled in 1709 is visible at the same spot but unlabelled. |
| 1706 | UNLABELLED_SIGN_PRESENT | 10 | Same red car 51G 502.98 and riders as 1709; the small distant cls10 sign labelled in 1709 is visible at the same spot but unlabelled. |
| 1707 | UNLABELLED_SIGN_PRESENT | 10 | Same red car 51G 502.98 and riders as 1709; the small distant cls10 sign labelled in 1709 is visible at the same spot but unlabelled. |
| 1708 | UNLABELLED_SIGN_PRESENT | 10 | Same red car 51G 502.98 and riders as 1709; the small distant cls10 sign labelled in 1709 is visible at the same spot but unlabelled. |
| 2766 | UNLABELLED_SIGN_PRESENT | 18 | Same tree-lined road as 2767; the small red/yellow sign cluster labelled cls18 in 2767 is visible at the same place but unlabelled. |
| 2793 | UNCLEAR | 50? | Same road and riders as 2798; a tiny distant red sign may be visible where 2798 labels cls50, too small to confirm. |
| 2794 | UNCLEAR | 50? | Same road and riders as 2798; a tiny distant red sign may be visible where 2798 labels cls50, too small to confirm. |
| 2795 | UNCLEAR | 50? | Same road and riders as 2798; a tiny distant red sign may be visible where 2798 labels cls50, too small to confirm. |
| 2796 | UNCLEAR | 50? | Same road and riders as 2798; a tiny distant red sign may be visible where 2798 labels cls50, too small to confirm. |
| 2797 | UNCLEAR | 50? | Same road and riders as 2798; a tiny distant red sign may be visible where 2798 labels cls50, too small to confirm. |
| 2999 | UNLABELLED_SIGN_PRESENT | 13 | Bridge approach between 2998 and 3000; the DI CHAM cls13 triangle and its plate are visible but cut at the right edge, unlabelled. |

Proposed handling (owner decision): use `TRUE_NEGATIVE` frames as detector background images;
quarantine `UNLABELLED_SIGN_PRESENT` frames from detector training until they are relabelled in a
derived label set, and never use them as background.

## Artifacts

- Class support: `docs/review/generated/wp34_d04_class_support.csv`.
- Negative audit: `docs/review/generated/wp34_negative_audit.csv`; notes `docs/review/wp34_negative_review_notes.csv` (pinned).
- Manifest: `docs/review/generated/wp34_manifest.json`.
