# M0-WP31-R1 — corrected D-02 group_id proposal for DATASET01

Status: `WP31_R1_GROUP_ID_PROPOSAL_AWAITING_QA_AND_OWNER_D02_DECISION`
Boundary: `PROPOSAL_ONLY_FROM_PROVISIONAL_QA_PASSED_OVERLAYS_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_SPLIT_NO_TRAINING`

This R1 reissue corrects the QA-failed WP31 proposal (record
`docs/review/wp31_independent_qa_record.md`: 2 P1, 1 P2, 2 P3). Initial WP31 stays byte-identical
as an immutable QA-fail record. Nothing here approves D-02, writes a split or authorizes training;
Gate 0 remains BLOCKED.

## What changed

- **P1-1 (interleaved ride blocks):** the WP32 cross-block review added
  31 capture-group merges from reviewed near-duplicate and
  label-geometry candidates (`docs/review/wp32_cross_block_review_report.md`).
- **P1-2 (interleaved sibling scenes):** sibling scenes in one capture group are re-merged when
  their stem ranges interleave and they share any labelled class, in addition to the WP31 resume
  rule; WP32 physical-sign links are applied first. 51 re-merges.
  The C0079 cls23 single-pole sub-sequence was re-reviewed in WP32: same ride, but a different
  pole from the cls10/cls23 pole in the main sequence.
- **P2 (unpinned sources):** every input (inventory, WP5 CSV, `dataset_graph.py`, all overlay
  JSONs, QA records, the initial WP31 package and the WP32 package) is pinned by SHA-256.
- **P3 (wording):** see "Limits" below.

## Grouping rules

1. Capture group (`D02-C`): adjacency edges reviewed `SAME_CAPTURE_CANDIDATE`/`UNRESOLVED`, the
   twelve unreviewed negative runs, `0247`–`0249`, and WP32 capture links.
2. Scene group (`D02-S`): capture groups cut only at physical-sign `NOT_RELATED` edges, joined by
   WP32 physical-sign links, then re-merged for resumed or interleaved siblings.

## Result

| Level | Groups | Multi-frame | Singletons | Mixed train/test | > 100 frames | Largest sizes | Largest share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Capture | 54 | 54 | 0 | 54 | 6 | [513, 411, 226, 190, 120, 115, 87, 83] | 16.0% |
| Scene | 63 | 63 | 0 | 63 | 6 | [468, 411, 190, 190, 120, 115, 87, 75] | 14.6% |

4 scene cuts remain effective. Large scene groups:

| Scene group | Capture group | Frames | Stems | Train/test/unassigned | Classes |
| --- | --- | --- | --- | --- | --- |
| `D02-S0002` | `D02-C0002` | 120 | 0072–0413 | 94/25/1 | 49 |
| `D02-S0029` | `D02-C0027` | 190 | 0920–1109 | 149/41/0 | 0 2 3 5 10 13 17 23 26 27 |
| `D02-S0042` | `D02-C0038` | 190 | 1516–1985 | 146/38/6 | 10 14 20 23 29 34 38 39 40 |
| `D02-S0056` | `D02-C0048` | 411 | 2068–2478 | 338/73/0 | 2 3 5 10 12 13 16 18 23 26 34 39 40 41 45 |
| `D02-S0057` | `D02-C0049` | 115 | 2479–2593 | 94/21/0 | 2 3 8 10 12 32 33 39 45 |
| `D02-S0059` | `D02-C0051` | 468 | 2617–3084 | 364/96/8 | 0 2 3 6 8 10 12 13 17 23 28 30 35 38 39 40 41 45 46 50 |

## Independent support per class

- Fewer than 3 capture groups (23 classes): 1 (1 grp/22 img), 9 (2 grp/43 img), 11 (2 grp/26 img), 15 (1 grp/29 img), 20 (2 grp/52 img), 21 (1 grp/11 img), 24 (1 grp/56 img), 25 (2 grp/25 img), 27 (1 grp/36 img), 28 (2 grp/27 img), 29 (1 grp/45 img), 33 (1 grp/19 img), 35 (1 grp/87 img), 36 (1 grp/75 img), 37 (1 grp/47 img), 38 (2 grp/114 img), 42 (1 grp/21 img), 43 (2 grp/27 img), 44 (1 grp/3 img), 47 (1 grp/16 img), 48 (1 grp/41 img), 49 (1 grp/119 img), 51 (1 grp/5 img).
- Fewer than 3 scene groups (23 classes): 1, 9, 11, 15, 20, 21, 24, 25, 27, 28, 29, 33, 35, 36, 37, 38, 42, 43, 44, 47, 48, 49, 51.

## Limits

- Cross-block linking only covers candidates found by near-identical thumbnails or matching label
  geometry. The same sign seen from a clearly different distance or angle in another block may
  still be in a separate group, so neither level is proven leak-free.
- The twelve negative runs are bridged at capture level but were never reviewed visually.
- Over-merge is accepted as the safe direction; very large groups make a balanced split harder.

## Owner decision options for D-02

- **D02-P1 — capture groups:** coarsest; lowest residual leak risk among the two levels.
- **D02-P2 — scene groups:** finer; relies additionally on the physical-sign cuts.
- **D02-A — creator/session metadata:** still preferred if it can be obtained.

## Artifacts

- Frames `docs/review/generated/wp31_r1_group_id_frames.csv`, groups `docs/review/generated/wp31_r1_group_id_groups.csv`, cuts
  `docs/review/generated/wp31_r1_scene_cut_edges.csv`, negative gaps `docs/review/generated/wp31_r1_unreviewed_negative_gaps.csv`, class support
  `docs/review/generated/wp31_r1_class_group_support.csv`, manifest `docs/review/generated/wp31_r1_group_id_manifest.json`.
