# M0-WP31 — D-02 group_id proposal for DATASET01

Status: `WP31_GROUP_ID_PROPOSAL_AWAITING_OWNER_D02_DECISION`
Boundary: `PROPOSAL_ONLY_FROM_PROVISIONAL_QA_PASSED_OVERLAYS_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_SPLIT_NO_TRAINING`

This package turns the independently QA-passed provisional edge overlays (WP5, WP7, WP12-R1,
WP13, WP14, WP15, WP22, WP23-R1, WP24, WP25-R1, WP26, WP27-R2, WP28-R2, WP29 and WP30-R1) into
two candidate `group_id` levels for the owner's D-02 decision. It writes no split, does not
change canonical WP5, and does not authorize training. Gate 0 remains BLOCKED.

## Grouping rules

1. **Capture group (`D02-C####`)**: connected components over edges reviewed as
   `SAME_CAPTURE_CANDIDATE` or `UNRESOLVED`. An unresolved edge is kept joined, because cutting
   it is the leak-risk direction.
2. **Scene group (`D02-S####`)**: inside each capture group, cut only edges whose physical-sign
   relation is `NOT_RELATED` (the visible signs change), then re-merge two sibling scenes in the
   same capture group when they are not adjacent and the last labelled frame of one and the first
   labelled frame of the other overlap in classes (overlap coefficient ≥ 0.5). The
   re-merge protects against frames that are out of filename order (WP29 `edge_002967`, WP30
   `edge_002977`), where the same physical sign could otherwise end up in two groups.
   52 sibling pairs were re-merged.
3. **Unreviewed negative gaps.** WP5 created no proxy edge next to the 25 empty-label frames
   (vendor split `unassigned`), so 12 negative runs covering 37 consecutive
   stem pairs were never reviewed. Capture groups join across every run (leak-safe). Scene groups
   attach the negatives to the preceding scene and join the following scene only when the two
   bounding labelled frames overlap in classes (2
   of 12 runs). The runs are listed in `docs/review/generated/wp31_unreviewed_negative_gaps.csv` and should be
   reviewed visually before the owner finalizes D-02.
4. Both levels join stems `0247` and `0249`, whose connecting edges through quarantined stem
   `0248` were never reviewed. Stem `0248` gets no group and stays excluded.
5. Sequence overlays (WP16–WP21) remain context only and are not used.

## Result

| Level | Groups | Multi-frame | Singletons | Mixed train/test | > 100 frames | Largest sizes | Largest share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Capture | 85 | 84 | 1 | 80 | 4 | [513, 411, 190, 115, 83, 78, 75, 72] | 16.0% |
| Scene | 99 | 98 | 1 | 93 | 7 | [239, 190, 172, 156, 121, 118, 115, 78] | 7.4% |

"Mixed train/test" counts groups that the vendor split currently places on both sides; every
such group is a leak in the vendor split and confirms that the vendor split cannot be used as a
holdout.

The scene level applies 40 effective cuts (listed in
`docs/review/generated/wp31_scene_cut_edges.csv`). The remaining large scene groups cannot be split further from the
reviewed evidence, because every adjacent pair inside them shares at least one physical sign:

| Scene group | Capture group | Frames | Stems | Train/test/unassigned | Classes |
| --- | --- | --- | --- | --- | --- |
| `D02-S0047` | `D02-C0044` | 190 | 0920–1109 | 149/41/0 | 0 2 3 5 10 13 17 23 26 27 |
| `D02-S0088` | `D02-C0079` | 172 | 2068–2252 | 146/26/0 | 2 3 5 10 13 16 18 23 34 39 40 |
| `D02-S0089` | `D02-C0079` | 239 | 2112–2478 | 192/47/0 | 2 3 10 12 16 18 23 26 39 40 41 45 |
| `D02-S0090` | `D02-C0080` | 115 | 2479–2593 | 94/21/0 | 2 3 8 10 12 32 33 39 45 |
| `D02-S0092` | `D02-C0082` | 156 | 2617–2882 | 127/28/1 | 2 3 8 12 17 30 35 39 46 |
| `D02-S0093` | `D02-C0082` | 118 | 2724–3084 | 99/18/1 | 6 10 12 23 38 41 45 46 |
| `D02-S0094` | `D02-C0082` | 121 | 2767–2936 | 84/32/5 | 0 8 10 13 23 28 38 39 40 46 50 |

## Independent support per class

`docs/review/generated/wp31_class_group_support.csv` counts, for each of the 52 observed classes,
how many distinct groups contain it. A class needs at least three independent groups to appear
in train, validation and test.

- Not feasible at capture level (18 classes): 9 (2 grp/43 img), 11 (2 grp/26 img), 15 (1 grp/29 img), 21 (1 grp/11 img), 24 (1 grp/56 img), 25 (2 grp/25 img), 27 (1 grp/36 img), 28 (2 grp/27 img), 33 (1 grp/19 img), 35 (1 grp/87 img), 36 (1 grp/75 img), 37 (1 grp/47 img), 42 (1 grp/21 img), 43 (2 grp/27 img), 44 (1 grp/3 img), 47 (1 grp/16 img), 48 (1 grp/41 img), 51 (1 grp/5 img).
- Not feasible at scene level (18 classes): 9, 11, 15, 21, 24, 25, 27, 28, 33, 35, 36, 37, 42, 43, 44, 47, 48, 51.

This is direct input for D-04: image counts overstate independent support.

## Owner decision options for D-02

- **D02-P1 — adopt capture groups.** Most conservative; the largest group holds
  16.0% of frames, which still allows a group-aware split.
- **D02-P2 — adopt scene groups.** Finer groups and more classes become split-feasible; relies on
  the physical-sign `NOT_RELATED` cuts and the class-overlap re-merge being sufficient.
- **D02-A — wait for creator/session metadata.** Remains preferred if it can be obtained.

Whichever option is chosen, the owner should spot-check the effective cut list before a split is
generated. Choosing an option does not by itself open Gate 0: D-01, D-03 and D-04 also remain
pending.

## Artifacts

- Frames: `docs/review/generated/wp31_group_id_frames.csv` (one row per stem, both group ids and flags).
- Groups: `docs/review/generated/wp31_group_id_groups.csv`.
- Scene cuts: `docs/review/generated/wp31_scene_cut_edges.csv`.
- Unreviewed negative gaps: `docs/review/generated/wp31_unreviewed_negative_gaps.csv`.
- Class support: `docs/review/generated/wp31_class_group_support.csv`.
- Manifest: `docs/review/generated/wp31_group_id_manifest.json`.
