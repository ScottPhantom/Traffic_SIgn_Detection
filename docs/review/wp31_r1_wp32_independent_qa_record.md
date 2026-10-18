# M0-WP32 and M0-WP31-R1 independent QA record

Status: `QA_PASS_WP32_AND_WP31_R1_CAPTURE_LEVEL_WITH_ONE_SCENE_LEVEL_P2_PROVISIONAL_EVIDENCE_ONLY`
Reviewer: `Claude Code QA session (did not author WP32 or WP31-R1; authored the WP31 QA record)`
Reviewed at: `2026-10-17T21:30:00+07:00`
Boundary: `QA_OF_D02_GROUP_ID_PROPOSAL_AND_CROSS_BLOCK_LINKS_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_SPLIT_NO_TRAINING`

This append-only record reports independent QA of M0-WP32 (the cross-block link review) and of
M0-WP31-R1 (the corrected D-02 `group_id` proposal). It modifies no package, builder, test,
`dataset_graph.py`, `PROJECT_MEMORY.md` or roadmap file. Both packages keep their historical
`*_AWAITING_QA*` status strings.

## Verdict

- **WP32: PASS.** 0 P0, 0 P1, 0 P2, 1 P3. I agree with all 71 of 71 decisions.
- **WP31-R1: PASS at capture level.** 0 P0, 0 P1, **1 P2**, 2 P3. The P2 affects only the scene
  level (option D02-P2). It must be fixed before scene groups are offered to the owner as an
  option. The capture level (D02-P1) is not affected.
- All four leak examples from the WP31 QA record now sit in one capture group and one scene
  group (check 4). WP31 P2-1 (unpinned sources) and P3-2 (wording) are resolved.

## Package bytes reviewed

- WP32:
  - builder `9272001062423049…`;
  - notes `2dd0d8a9931eede6…` (equal to the builder's `EXPECTED_NOTES_SHA256`);
  - manifest `c73206e2388849a2…`;
  - report `6c638f98a04086e9…`.
- WP31-R1:
  - builder `c4e28b32f76e1af8…`;
  - manifest `b698192e2575d71b…`;
  - report `0db358481e12b233…`;
  - test `caaff1c362d3f403…`.
- The pinned WP31 QA record `5639265731217e77…` matches its pin.

## Checks performed

1. **WP32 visual review: all 18 of 18 pages and all 71 rows read directly.**

   The atlas prints each decision beside its pair (see P3-W1), so my judgment came from the image
   panels. I made the call before reading each printed decision.
   - **Cross-group rows x001–x054.**
     - **x001–x017, cls49 junction:** the same gantry, NGVU.VN building, pink-backpack rider and
       food-delivery rider. Agreed SAME/SAME.
     - **x018–x023:** the bus-route cls0/1 pole and the cls2/3 junction. Agreed SAME/SAME.
     - **x028–x030 and x032–x036, x038, x040–x041:** the cls32 and cls7 boulevards. These have the
       same white-shirt rider and pink-backpack rider, or the same pink-raincoat queue. Agreed
       SAME/SAME.
     - **x042–x053, cls29 chain and red car 51G 502.98:** agreed SAME/SAME.
     - **The seven NOT/NOT rows:**
       - x021 (0521/1056), x025 (0586/1167) and x031 (0751/3043): different roads, riders and
         vehicles.
       - x024 (0585/0691): an underpass gantry against a roadside shop.
       - x027 (0681/1100): the metro viaduct against a coffee-shop crosswalk.
       - x037 (1168/2542): an empty bike lane against a busy alcohol-billboard road.
       - x054 (2268/3016): a red-cargo motorbike against the Vietnam Post rider group.

       All seven agreed.
     - **x026 (0685/0718), SAME/NOT/MEDIUM:** the same blue lamp-post road beside the viaduct.
       0685 shows a cls10+cls7 pole and 0718 a cls10+cls34 pole with a 6:00–22:00 plate, so
       these are different signs. Agreed.
     - **x039 (1273/1274), SAME/NOT/MEDIUM:** the same palms and gantry. The near cls23 CẤM sign
       and the distant cls41 are different signs. Agreed.
     - **x050 (1706/1903), SAME/UNRESOLVED:** the same red car and riders. 1706 has no box.
       Agreed; linking it conservatively is correct.
   - **C0079 re-review, x055–x071.**
     - The blue-helmet visor sub-sequence shows one single-pole cls23 with its plate, growing
       steadily: 2070, 2081, 2092, 2103, 2112, 2122, 2133, 2144, 2155.
     - The main sequence's cls10 over cls23 pole by the AH1 sign, with cls18 on the right, is a
       different pole.
     - Agreed: x055–x063 SAME/NOT and x064–x071 SAME/SAME.
2. **WP32 data integrity.**
   - The notes have 71 rows and equal the decisions CSV field by field.
   - Totals: 52 SAME/SAME, 11 SAME/NOT, 7 NOT/NOT and 1 SAME/UNRESOLVED.
   - I re-derived the link CSV from the decisions, treating SAME and UNRESOLVED as a link and
     NOT_RELATED as no link. It matches exactly: 64 capture links, 7 capture no-links, 53 scene
     links and 18 scene no-links.
3. **Independent WP31-R1 re-derivation (QA-only script; does not import the builders or
   `dataset_graph`).**
   - Links come from the WP32 decisions CSV, and the scene re-merge is iterated until stable.
   - Capture partition: 54 groups, largest `[513, 411, 226, 190, 120, 115, 87, 83]`.
   - Scene partition: 63 groups, largest `[468, 411, 190, 190, 120, 115, 87, 75]`.
   - Both partitions equal the package. Every scene group nests in one capture group, and stem
     0248 has no group.
4. **The WP31 QA examples are resolved.**

   | Example | Capture group | Scene group |
   | --- | --- | --- |
   | cls49 junction (0076–0413, ten former groups) | `D02-C0002` | `D02-S0002` |
   | cls29 chain (1516–1879) | `D02-C0038` | `D02-S0042` |
   | C0079 cls23 visor sub-sequence and 2253 | `D02-C0048` | `D02-S0056` |
   | C0082 cls6 curve sign (2971–3015) | `D02-C0051` | `D02-S0059` |

   The C0067 ĐI CHẬM poles (1635/1671) stay in two scene groups, which is correct: they are
   different poles.
5. **Search for missed links.**
   - Thumbnail scan: I repeated my 32×18 near-duplicate scan against the WP31-R1 groups. No pair
     of different capture groups falls below 0.35; the closest is 0.371 (0521/1147, different
     scenes).
   - Context-crop scan: I added a second scan matching same-class sign crops at three times box
     size across capture groups, and inspected the top hits visually: 1226/1922, 1922/2385,
     1271/1422, 0802/1422, 1235/2898 and 1057/2101.
     - Several of these show the common "cls10 over cls23 with CẤM XE 02 VÀ 03 BÁNH" pole type or
       80/60 plates.
     - In every case the frames show different roads, riders and vehicles. I found no missed
       capture link.
   - Limit: neither scan proves that no link was missed (the report says so correctly).
   - Scene level: the scan found the negative-frame problem described in P2-1.
6. **Verifiers and tests.**
   - `build_wp32_cross_block_link_review.py verify` returns `valid=true` with 23 artifacts.
   - `build_wp31_r1_group_id_proposal.py verify` returns `valid=true` with 7 artifacts.
   - Initial WP31 `verify` still returns `valid=true`.
   - `pytest tests/test_wp31_r1_wp32_cross_block.py` reports 9 passed.
7. **Tampering attacks.** These ran on a staged copy. The baseline and restored runs were both
   valid on both verifiers.
   - D1: flip a capture decision in the pinned WP29 overlay. WP31-R1 rejects it with `pinned
     source changed`. WP32 stays valid, because WP32 depends on the initial WP31 frames, not the
     overlays directly.
   - D2: change x021 to SAME in the WP32 notes. WP32 rejects it with `review-notes anchor
     mismatch`.
   - D3: the same change, then run WP32 `build`. Still rejected by the same anchor, so the pinned
     notes cannot be re-signed by a rebuild.
   - D4: change x001 LINK to NO_LINK in the links CSV. Both verifiers reject it.
   - D5: move stem 1622 to another capture group in the WP31-R1 frames CSV. WP31-R1 rejects it.
   - D6: append to the pinned WP31 QA record. Both verifiers reject it.
   - D7: flip one byte of an atlas page. WP32 rejects it.
8. **Boundary and limits wording.** Both reports state:
   - proposal only;
   - D-02 PENDING and Gate 0 BLOCKED;
   - `split_authorized=false` and `training_authorized=false`;
   - no change to canonical WP5 or earlier packages.

   WP31-R1 "Limits" correctly says that neither level is proven leak-free, and that over-merging
   is accepted. See P2-1 for one missing limit.

## Findings

### WP31-R1 P2-1: box-less frames attached to the wrong scene group

Scene rule 3 attaches every negative (empty-label) frame to the **preceding** labelled scene.
Where the run separates two different scene groups, the negatives are often visually part of the
**following** scene. They are near duplicates of frames in another scene group and show the same,
unlabelled, physical sign.

| Negative stems | Placed in | Visually belongs to | Evidence |
| --- | --- | --- | --- |
| 1514, 1515 | `D02-S0041` (after 1513 cls10) | `D02-S0042` | Same "ĐÃ UỐNG RƯỢU BIA" billboard, 80/60 plates, unlabelled cls29 sign, white-sack motorbike and striped-shirt rider as 1516–1540. Thumbnail MAE to 1516 is 0.37; to 1513 it is 1.08. |
| 2015, 2016, 2017 | `D02-S0052` (after 2014 cls0) | `D02-S0053` | Same striped-barrier road and backpack rider as 2018. MAE to 2018 is 0.52–0.71; to 2014 it is 1.14–1.18. |
| 2051 | `D02-S0054` (after 2050 cls41) | `D02-S0053` | Near duplicate of 2052 and 2030/2031 (S0053): same riders, and the cls32 sign is at the right edge. MAE to 2052 is 0.36, to 2031 is 0.22, and to 2050 is 0.85. |

- **Impact.** A split over WP31-R1 scene groups could put near-identical frames (2051 and 2052;
  1514 and 1516) on opposite sides. The frames are unlabelled, so this mostly affects detector
  negatives and evaluation, but it is a scene-level leak.
- **Capture level is unaffected:** every run is joined there.
- **Fix:** before scene groups are offered, choose one of:
  - attach each negative to its visually matching neighbour after review;
  - join both bounding scenes (the leak-conservative choice);
  - exclude the 25 negatives from scene-level splitting.

  Also add the issue to the "Limits" section.
- **Correction of my WP31 record.** There I listed run 1513–1516 as agreed because its labelled
  signs differ. The negatives 1514/1515 belong to the 1516 scene, so that agreement was wrong
  for the scene level.

### WP31-R1 P3-1: WP32 physical-sign no-links do not override upstream edges

The x055–x063 decisions (`SAME_CAPTURE` / `NOT_RELATED`) re-review WP27-R2/WP14 edges that are
still recorded upstream as SAME_PHYSICAL. WP31-R1 applies only WP32 `LINK` rows. The incorrect
upstream SAME_PHYSICAL records therefore still drive scene unions, and the cut list omits these
edges.

This does not change the result: C0048 becomes one 411-frame scene through the interleave rule,
which is the safe direction. It should still be documented, so that a later finer scene split does
not silently rely on the wrong upstream records.

### WP31-R1 P3-2: the scene level adds little over the capture level for the large groups

Because of the "interleaved and share any class" re-merge, the large scene groups are nearly
identical to their capture groups:

- S0056 equals C0048 (411 frames);
- S0059 holds 468 of the 513 frames in C0051.

There are 63 scene groups against 54 capture groups. This is the safe direction, but the owner
should know that option D02-P2 gains little.

### WP32 P3-W1: the atlas shows decisions next to each pair

Each page prints the PM decision and rationale beside the pair, so a reviewer cannot judge the
pair blind. This follows the earlier atlas convention. For future link reviews, consider a
decision-free atlas variant for QA.

## Governance

- Canonical WP5 remains at 3,172 PENDING edges, and all 589 sequences remain PENDING.
- D-02 remains PENDING and Gate 0 remains BLOCKED. `split_authorized=false` and
  `training_authorized=false` stay in force.
- D-01, D-03 and D-04 remain pending.
- No split, group truth, training, upload, push or publication was performed.
- This record modifies no WP32, WP31 or WP31-R1 file, builder, test or manifest, nor
  `dataset_graph.py`, `PROJECT_MEMORY.md` or the roadmap.
