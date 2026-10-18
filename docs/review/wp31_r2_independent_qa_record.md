# M0-WP31-R2 independent QA record

Status: `QA_PASS_WP31_R2_ONE_P2_REPORT_DISCLOSURE_PROVISIONAL_EVIDENCE_ONLY`
Reviewer: `Claude Code QA session (did not author WP31-R2; authored the WP31 and WP31-R1/WP32 QA records)`
Reviewed at: `2026-10-17T23:00:00+07:00`
Boundary: `QA_OF_D02_GROUP_ID_PROPOSAL_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_SPLIT_NO_TRAINING`

This append-only record reports independent QA of M0-WP31-R2. It modifies no package, builder,
test, manifest, `dataset_graph.py`, `PROJECT_MEMORY.md` or roadmap file. WP31-R2 keeps its
`WP31_R2_GROUP_ID_PROPOSAL_AWAITING_QA_AND_OWNER_D02_DECISION` status string.

## Verdict

- **WP31-R2: PASS.** 0 P0, 0 P1, 1 P2, 1 P3.
- **WP31-R1 P2-1 is fixed.** Every negative run now joins both of its bounding scenes. All 12 runs
  sit in a single scene group, so no run boundary can separate a sign at scene level.
- **Capture level (D02-P1): fit to offer the owner.** It is identical to WP31-R1, which passed QA
  at capture level.
- **Scene level (D02-P2): fit to offer in content, after one report correction.** The R2 scene
  partition has no same-sign split that I could find, but the report does not disclose that R2
  also **splits** WP31-R1's largest scene (P2-1).
- Neither level is proven leak-free; the report's "Limits" section says this correctly.

## Package bytes reviewed

- Builder `bde68d64b07a13b8…`.
- Test `0dca3e2b3774c1d7…`.
- Report `2c3db0e17144f198…`.
- Manifest `c17f794c33dbaf0a…`.
- The pinned WP31-R1/WP32 QA record `94994f3f54627321…` matches its pin.

## Checks performed

1. **R2 against R1, compared by diff.**
   - Builder logic: the only change in `derive` is that every negative run now unions both bounding
     scenes (`joined = True`).
   - Frames: all 3,216 rows have identical stem, split, classes, box count, flags and **capture
     ids**, so the capture level is unchanged at 54 groups.
   - Scene merges from the negative-run joins (63 → 61):
     - R1 `S0041` + `S0042` become R2 `S0041`;
     - R1 `S0052` + `S0053` + `S0054` become R2 `S0051`.
   - **One change is not a merge.** R1 `S0059` (2617–3084, 468 frames) is split into R2 `S0056`
     (2617–2936, 320 frames) and `S0057` (2937–3084, 148 frames). See P2-1.
2. **The P2 frames are now grouped correctly.**
   - 1513–1516 are all in `S0041`.
   - 2014–2018, 2030–2032 and 2050–2052 are all in `S0051`.
   - All 12 negative runs have `scene_joined=True`, and each run's left frame, negatives and right
     frame share one scene id: 0059–0062, 0186–0188, 0543–0545, 1513–1516, 1702–1709, 2014–2018,
     2030–2032, 2050–2052, 2722–2724, 2765–2767, 2792–2798 and 2998–3000. No same-sign split can
     remain across a run boundary.
3. **Independent re-derivation (QA-only script; does not import any builder or `dataset_graph`).**
   - Capture partition: 54 groups, largest `[513, 411, 226, 190, 120, 115, 87, 83]`.
   - Scene partition: 61 groups, largest `[411, 320, 226, 190, 148, 120, 115, 87]`.
   - Both partitions equal the package. Every scene group nests in one capture group, and stem 0248
     has no group.
   - My derivation reproduces the `S0059` split, so the split comes from the rules themselves, not
     from an implementation error.
4. **Same-sign check at the new boundary and across all scene pairs.**

   I re-ran two scans over the R2 scene groups:
   - same-class box geometry between different scene groups of one capture group;
   - thumbnail near-duplicates within a capture group.

   I then inspected the hits in raw frames:

   | Pair | Scene groups | Finding |
   | --- | --- | --- |
   | 2731 / 3004 (cls6, geometry 0.017) | `S0056` / `S0057` | Different signs: a dark-sky tree-lined road against the grey-sky bridge approach with the Vietnam Post rider group. |
   | 2659 / 3041 (cls46) | `S0056` / `S0057` | Different places. |
   | 2767 / 2977 (cls13) | `S0056` / `S0057` | A ĐI CHẬM sign on the tree road against one on the bridge approach. Different. |
   | 2881 / 3128 (cls12) | `S0056` / `S0058` | Different. |
   | 2958 / 3129 (cls13) | `S0057` / `S0058` | Different. |
   | 0698 / 0719 (cls34, in R1 as well) | `S0020` / `S0022` | cls10+cls34 with a 6:00–22:00 plate on a striped pole by the pagoda, against the same sign type on a blue lamp post by the coffee kiosk. Different poles. |
   | 1635 / 1671 (cls13) | `S0044` / `S0045` | The two ĐI CHẬM poles already confirmed different. |
   | 1273 / 1274 | `S0034` / `S0035` | Agreed in WP32 x039. |

   - The new `S0056`/`S0057` boundary is the reviewed cut `edge_002901` (2936/2937), which I agreed
     with in the WP31 QA.
   - The WP31 P1-2 example, the cls6 curve sign at 2971–2977 and 3000–3004, lies entirely inside
     `S0057`.
5. **Verifiers and tests.**
   - `build_wp31_r2_group_id_proposal.py verify` returns `valid=true`.
   - WP31-R1, the initial WP31 and WP32 still verify (`valid=true`).
   - `pytest tests/test_wp31_r2_group_id_proposal.py` reports 6 passed.
6. **Tampering attacks.** These ran on a staged copy. The baseline and restored runs were both
   `valid=true`. All seven failed closed:
   - E1: append a comment to the pinned R1 builder.
   - E2: append to my pinned R1/WP32 QA record.
   - E3: flip `edge_003047` in the WP30-R1 overlay.
   - E4: add whitespace to the pinned R1 manifest.
   - E5: move 2051 to another scene in the R2 frames CSV.
   - E6: set `scene_joined` to False in the gaps CSV.
   - E7: change BLOCKED to OPEN in the report.
7. **Report wording.**
   - P3-1 (WP32 no-links do not override the upstream SAME_PHYSICAL records for x055–x063, so a
     later finer split must correct them first) is stated accurately.
   - P3-2 (scene groups are close to capture groups, so D02-P2 gains little) is stated accurately
     in the owner options.
   - The boundary is stated correctly: proposal only, D-02 PENDING, Gate 0 BLOCKED, no split or
     training, and WP31-R1/WP31 byte-identical.

## Findings

### P2-1: undisclosed scene split, because the re-merge rule is not monotone

- **What the report says.** "What changed in R2" describes the change as negative runs joining
  both bounding scenes, and the change request said nothing else changed.
- **What R2 also does.** It splits WP31-R1's largest scene, `S0059`, into `S0056` (320 frames) and
  `S0057` (148 frames) at `edge_002901`. The result tables show the two groups, but the text never
  explains the split.
- **Why it happens.** The sibling re-merge rule ("resumes" = the last labelled frame of one scene
  overlaps the first labelled frame of another) depends on where each raw scene starts and ends.
  - Joining runs 2765–2767 and 2998–3000 extends the raw scenes, so their first and last labelled
    frames move.
  - The R1 re-merge of 2724–2766 (cls6) with 3000/3015 (cls6/38) therefore no longer fires.
  - Adding unions thus *removed* a merge. The derivation is not monotone, so "add a join" is not
    automatically leak-conservative.
- **Outcome.** I checked the new boundary visually (check 4) and found no shared physical sign
  across it. The R1 merge was an over-merge: the cls6 sign on the dark tree-lined road at
  2725–2765 and the cls6 sign on the bridge approach at 3000–3004 are different signs. The R2
  partition is therefore acceptable.
- **Required before D02-P2 is offered.** The report must:
  - state the split and its cause;
  - warn that any future change to the joins can split other scenes, so every rebuild needs a
    same-sign check at new boundaries.

  A verifier or test assertion that flags any scene split relative to the pinned predecessor would
  make such changes visible.

### P3-1: R1 history section shows a recomputed number

"What changed in R1" now reads "44 re-merges", but the WP31-R1 report states 51. The value is
recomputed by the R2 derivation and presented as R1 history. Either quote the R1 figure or label
the number as the R2 count.

## Governance

- Canonical WP5 remains at 3,172 PENDING edges, and all 589 sequences remain PENDING.
- D-02 remains PENDING and Gate 0 remains BLOCKED. `split_authorized=false` and
  `training_authorized=false` stay in force.
- D-01, D-03 and D-04 remain pending.
- No split, group truth, training, upload, push or publication was performed.
- This record modifies no WP31, WP31-R1, WP31-R2 or WP32 file, builder, test or manifest, nor
  `dataset_graph.py`, `PROJECT_MEMORY.md` or the roadmap.
