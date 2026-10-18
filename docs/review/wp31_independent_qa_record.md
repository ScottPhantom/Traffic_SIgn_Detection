# M0-WP31 independent QA record

Status: `QA_FAIL_WP31_GROUP_ID_PROPOSAL_NOT_LEAK_SAFE_PROVISIONAL_EVIDENCE_ONLY`
Reviewer: `Claude Code QA session (did not author WP31)`
Reviewed at: `2026-10-17T18:00:00+07:00`
Boundary: `QA_OF_D02_GROUP_ID_PROPOSAL_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_SPLIT_NO_TRAINING`

This append-only record reports independent QA of M0-WP31, the D-02 `group_id` proposal. It does
not modify the package, its builder, its tests, `dataset_graph.py`, `PROJECT_MEMORY.md` or the
roadmap. WP31 keeps its `WP31_GROUP_ID_PROPOSAL_AWAITING_OWNER_D02_DECISION` status string.

## Verdict

- WP31: **FAIL**: 0 P0, **2 P1**, **1 P2**, 2 P3.
- The package faithfully implements its stated rules. My independent re-derivation matches it
  exactly. The rules themselves, however, are not leak-safe for DATASET01:
  - Frames from one ride are interleaved across non-adjacent filename blocks.
  - Rule 1 only links numerically adjacent stems.

  As a result, the same physical sign and the same riders land in different **capture** groups
  (P1-1). The scene re-merge also misses interleaved segments (P1-2).
- **Neither D02-P1 (capture groups) nor D02-P2 (scene groups) should be offered to the owner as
  leak-safe until P1-1 is fixed.**

## Package bytes reviewed

- Builder `b08a394192a9f0c6…`, test `fb383fac5dd9a4f9…`, report `093ec24c77e227d0…`.
- Frames `5ec635d891b95848…`, groups `20584add142886e8…`, scene cuts `3d0bf6d48f17cab5…`.
- Negative gaps `0b96dbcff419c953…`, class support `31b3115dfdbee3b7…`, manifest
  `15a61fcc118414b5…`.
- `dataset_graph.py` `339972e5bbd6789b…`.

## Checks performed

1. **Independent re-derivation.** I wrote a QA-only script that does not import
   `dataset_graph`. It reads the inventory, the canonical WP5 CSV and the 14 effective overlay
   JSONs directly.
   - Canonical WP5 has 3,178 edges. Of these, 3,176 are decided and 2 are undecided
     (`edge_000242`/`edge_000243`, stem 0248). No overlay re-reviews another overlay's edge.
   - Capture outcomes: 3,090 SAME_CAPTURE, 84 NOT_RELATED and 2 UNRESOLVED.
   - There are 39 edge-less adjacencies:
     - 2 are around the quarantined stem 0248;
     - the other 37 form 12 negative runs that hold all 25 box-less frames.
   - My capture partition equals the package: 85 groups, largest
     `[513, 411, 190, 115, 83, 78, 75, 72]`.
   - My scene partition, including the sibling re-merge, equals the package: 99 groups, largest
     `[239, 190, 172, 156, 121, 118, 115, 78]`.
   - There are 56 cut edges, of which 40 are effective.
   - Stem 0248 has no group.
2. **Invariants.**
   - No SAME_CAPTURE or UNRESOLVED edge crosses two capture groups.
   - No capture NOT_RELATED edge connects frames that ended up in the same capture group.
   - Every scene group nests inside one capture group.
   - No non-cut SAME_CAPTURE or UNRESOLVED edge crosses two scene groups.
3. **Visual inspection of raw frames.** I read contact sheets with the label boxes drawn and
   zoomed crops, covering:
   - effective cuts in C0023, C0067, C0079 and C0082;
   - 6 of the 12 negative runs (0543–0545, 1513–1516, 1702–1709, 2014–2018, 2722–2724,
     2792–2798);
   - the end points of the large groups S0047, S0089 and S0090.

   I also ran two automated scans to find candidates and then inspected the hits visually:
   - matching label class and box geometry between different scene groups of one capture group;
   - a whole-dataset near-duplicate scan comparing 32×18 normalized grayscale thumbnails against
     the nearest frame in a different capture group.
   - Agreed cuts:
     - `edge_001644` (1654/1655): two different ĐI CHẬM poles. The MÀN CỬA sign is visible far
       down the road in 1645.
     - `edge_002901` (2936/2937): a tree-lined road against the bridge approach.
     - The C0023 0501–0528 alternation: the cls0/1 pole at the bus against the cls2/3 sign.
   - Agreed negative runs: 0543–0545, 1513–1516, 2014–2018, 2722–2724 and 2792–2798 show
     different scenes or signs across the run. Run 1702–1709 shows the same ride on both sides;
     the capture level joins it, and the scene split matches the different labelled signs (cls29
     against cls10).
4. **Package verifier and tests.**
   - `uv run python scripts/build_wp31_group_id_proposal.py verify` returns `valid=true` with
     7 artifacts.
   - `uv run pytest -q -p no:cacheprovider tests/test_wp31_group_id_proposal.py` reports
     11 passed.
5. **Tampering attacks.** These ran on a staged copy. The baseline and restored runs were both
   `valid=true`.
   - Six attacks failed closed:
     - C1: move stem 1622 to C0062 in the frames CSV.
     - C2: set `training_authorized=true` in the manifest.
     - C3: flip class 49 feasibility in the support CSV.
     - C4: revert `edge_003047` in the WP30-R1 overlay without rebuilding.
     - C5: change the report text to "Gate 0 is OPEN".
     - C6: set WP30-R1 `qa_passed=False` in `dataset_graph`. Rejected with "every edge overlay
       must be independently QA-passed".
   - One coherent attack verified as valid (see P2-1): revert `edge_003047` in the overlay, run
     `build`, then `verify`. The result is `valid=true` with 86 capture groups.
6. **Boundary statement.** The report and manifest correctly say:
   - proposal only;
   - D-02 PENDING and Gate 0 BLOCKED;
   - `split_authorized=false`, `training_authorized=false` and
     `final_group_truth_created=false`;
   - no split was written and canonical WP5 is unchanged.

   The leak-safety wording is overstated (P3-2).

## Findings

### P1-1: capture groups split one ride and one physical sign across non-adjacent filename blocks

The stems interleave blocks from different rides. For example, ten frames of ride A are
followed by a block of ride B, and then ride A resumes. Rule 1 only unions numerically adjacent
stems, so every resumed block of ride A becomes a new capture group. Raw frames confirm the same
physical signs, buildings, vehicles and riders in different capture groups:

- **cls49 junction:** the NGVU.VN building, the two cls49 signs on the gantry, the pink-backpack
  rider and the orange food-delivery rider appear in **C0004, C0006, C0008, C0010, C0012, C0014,
  C0016, C0018 and C0020**, which are the 10-frame blocks 0113–0122, 0135–0144 and so on up to
  0405–0413. The thumbnail scan also links C0002. Stems 0220 (C0010) and 0242 (C0012) are near
  duplicates (thumbnail MAE 0.063). The support CSV counts class 49 in 10 independent capture
  groups, but in effect this is one or two scenes.
- **cls29 sign** under 80/60 plates beside the "ĐÃ UỐNG RƯỢU BIA KHÔNG LÁI XE" billboard and a
  pylon, with the same white-sack motorbike and the same striped-shirt rider (plate 59-P1 206.75).
  It appears in **C0062 (1516–1518), C0064 (1537–1546), C0066 (1622–1631) and C0068
  (1681–1702)**, with near-duplicate thumbnails 1518/1537, 1546/1622 and 1631/1681. The support
  CSV counts class 29 in 4 capture groups, which are all one sign. The same chain continues into
  C0070 and C0072 (1715/1729 is a near duplicate: same red car, plate 51G 502.98).
- **Scale (lower bound).** Same-group adjacent pairs have a median thumbnail MAE of 0.230.
  - Below 0.25, there are 23 nearest-neighbour pairs between different capture groups, touching
    27 capture groups. These collapse into 6 chains, the largest spanning 10 groups.
  - Below 0.15, there are 11 pairs.

  The scan only finds near-identical viewpoints. Same-sign pairs seen from different distances
  are not counted.
- **Effect.** A group-aware split over WP31 capture groups can place the same physical sign in
  both train and test, which is the leak D-02 exists to prevent. Scene groups nest inside capture
  groups, so they inherit the defect. The class-support table overstates independent groups (at
  least classes 49 and 29), so its feasibility list for D-04 is not reliable.
- **Required before D-02.** Add a cross-block linking step: near-duplicate or label-geometry
  candidates between non-adjacent capture groups, reviewed visually with the same two-axis
  protocol. Then rebuild both levels and the support table.

### P1-2: scene re-merge misses interleaved sibling scenes; the same sign is in two scene groups

Rule 3 re-merges sibling scenes only when one starts after the other has fully ended
(`first_b - last_a > 1`). Siblings whose stem ranges interleave are never compared. Two confirmed
cases:

- **C0079, cls23 single-pole sign:** behind the parked red container truck, seen through the
  blue-helmet visor sub-sequence.
  - It is labelled in **S0088** at stems 2068, 2069, 2070, 2081, 2092 and 2103. The box widths
    grow steadily: 0.034, 0.036, 0.045, 0.047, 0.050, 0.052.
  - It is also labelled in **S0089** at 2112, 2122, 2133 and onwards, at 0.053, 0.055 and so on.
  - The upstream edges joining 2070, 2081, 2092 and 2103 to their neighbours are recorded as
    SAME_PHYSICAL_SIGN. These are `edge_002045`, `edge_002055`, `edge_002056`, `edge_002066` and
    `edge_002077` in WP27-R2, and `edge_002067` and `edge_002078` in WP14. The neighbours
    (2071, 2080, 2082, 2104) actually show a different cls10+cls23 pole by the AH1 sign.
  - The matching WP27-R2 edges 2111/2112 onward record NOT_RELATED, so the overlays are
    internally inconsistent here.
- **C0082, cls6 curve sign** below the blue twin panel, by the same blue billboard and with the
  same cream-helmet rider. It is labelled in **S0095** at 2971–2977 and in **S0093** at
  3000–3004. Raw crops confirm it is the same physical sign. S0093 reached 3000–3004 through the
  re-merge with 3015+, but S0095 interleaves with S0093 and so was not compared.
- **Fix:** when sibling ranges interleave, compare every labelled frame pair, or adopt the
  capture level. Re-review the C0079 WP27-R2/WP14 edges listed above.

### P2-1: the verifier does not pin its sources

`verify` re-derives everything, including the source hashes in the manifest, from the files on
disk. No source hash is pinned in the builder. Changing a QA-passed overlay and then running
`build` therefore re-verifies as valid. I demonstrated this with `edge_003047` reverted, which
gives 86 capture groups and `valid=true`. Earlier packages pin their trusted inputs, for example
the WP30-R1 builder pins the WP30 notes and the WP30 QA record. WP31 should pin the overlay JSONs,
the WP5 CSV, the inventory, `dataset_graph.py` and the QA records.

### P3-1: possible over-merge in S0090 (not verified in depth)

S0090 (2479–2593, 115 frames) spans a dark rainy city frame (2479) and bright, dry boulevard
frames (2540, 2593). Every adjacent edge is reviewed as SAME, so this follows the evidence, but it
may be two rides. Over-merging is the safe direction. This is noted for the owner and is not
blocking. The endpoints of S0047 and S0089 look like single rides.

### P3-2: leak-safety wording in the report is overstated

The report calls capture groups "leak-safe" across negative runs and D02-P1 "most conservative".
Given P1-1, the capture level is not conservative across non-adjacent blocks. The report should
say that cross-block links were not reviewed.

## Governance

- Canonical WP5 remains at 3,172 PENDING edges, and all 589 sequences remain PENDING.
- D-02 remains PENDING and Gate 0 remains BLOCKED. `split_authorized=false` and
  `training_authorized=false` stay in force.
- No split, group truth, training, upload, push or publication was performed.
- This record did not modify the WP31 package, its builder or tests, `dataset_graph.py`,
  `PROJECT_MEMORY.md` or the roadmap.
