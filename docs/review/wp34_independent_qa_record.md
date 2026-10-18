# M0-WP34 independent QA record

Status: `QA_FAIL_WP34_NEGATIVE_AUDIT_FIVE_FALSE_TRUE_NEGATIVES_PROVISIONAL_EVIDENCE_ONLY`
Reviewer: `Claude Code QA session (did not author WP34)`
Reviewed at: `2026-10-18T02:00:00+07:00`
Boundary: `QA_OF_D04_DECISION_SUPPORT_AND_NEGATIVE_AUDIT_ONLY_NOT_OWNER_DECISION_NO_SPLIT_NO_TRAINING`

This append-only record reports independent QA of M0-WP34. It modifies no package, builder, test,
notes, manifest, `PROJECT_MEMORY.md` or roadmap file. WP34 keeps its `WP34_AWAITING_QA_REVIEW`
status string.

## Verdict

- **WP34: FAIL.** 0 P0, **1 P1**, **1 P2**, 4 P3.
- **Part A (D-04 support counts):** the counts re-derive exactly and the rule is implemented as
  stated. One wording/semantic issue must be fixed before the owner decides (P2-1).
- **Part B (negative audit):** five of the seven `TRUE_NEGATIVE` frames show a visible traffic
  sign (P1-1). If they were used as detector background, the detector would be trained to call
  a visible sign "no sign".
- **Decision disagreements:**
  - 2015, 2016, 2017, 2031 and 2051: recorded TRUE_NEGATIVE, should be UNLABELLED_SIGN_PRESENT.
  - 2793–2797: recorded UNCLEAR, should be UNLABELLED_SIGN_PRESENT.

  The other 13 decisions are agreed: 0060, 0061, 0187, 0544, 1514, 1515, 1703–1708, 2723, 2766
  and 2999. Some of them have wrong class fields (P3-1).
- **Process note:** I read the package report, which prints the decision table, before I opened
  the raw frames. I then judged every frame from raw full-resolution crops; the disagreements
  above show that the judgment was independent.

## Package bytes reviewed

- Builder `3d631195adb20bad…`, test `9704f88fac42d765…`, report `d7d65d9d78a9c060…`.
- Notes `5a6dbdb96ad6639c…`, manifest `0bc6d1707273f84b…`.

## Checks performed

1. **Part A re-derivation (QA-only script).**
   - The registry has 3,215 stems (0248 excluded). It equals the WP31-R2 capture partition with
     54 groups.
   - For all 54 WP33 trainable keys, I computed train-eligible boxes, images and distinct D-02
     groups. Boxes, images, groups and proposed option match the package exactly.
   - The rule applied is: ≥3 groups → KEEP_FULL; 2 groups → KEEP_TRAIN_AND_TEST_NO_VAL; 1 group
     with ≥30 images → KEEP_TRAIN_ONLY_UNVERIFIED; otherwise DROP. This gives 27/6/9/12, and every
     row has `owner_status=PENDING`.
   - `largest_group_share` matches only when computed over **boxes**. Over images it differs for
     nine classes (see P3-3).
2. **Part B: all 25 negatives judged from raw 960×540 frames**, together with their previous and
   next labelled frames, using zoomed crops of small or distant signs.
3. **Verifier and tests.**
   - `uv run python scripts/build_wp34_d04_support_and_negatives.py verify` returns `valid=true`
     with 13 artifacts.
   - `uv run pytest -q -p no:cacheprovider tests/test_wp34_d04_support_and_negatives.py` reports
     8 passed.
4. **Tampering attacks.** These ran on a staged copy. The baseline and restored runs were both
   `valid=true`. All seven failed closed:
   - G1: change a notes decision. Rejected with `notes anchor mismatch`.
   - G2: the same change, then run `build`. Still rejected.
   - G3: edit a support row. Rejected because the artifact differs.
   - G4: move a stem to another group in the D-02 registry. Rejected because the pinned source
     changed.
   - G5: edit one WP33 derived box. Rejected because the pinned source changed.
   - G6: flip one byte of an atlas page. Rejected because the artifact differs.
   - G7: change `owner_status` in the manifest. Rejected.

## Findings

### P1-1: five TRUE_NEGATIVE frames contain a visible sign

| Stem | Recorded | Evidence in the raw frame |
| --- | --- | --- |
| 2015 | TRUE_NEGATIVE | A small red-ringed disc on a pole right of the blue "HÃY NÓI KHÔNG VỚI RƯỢU BIA…" board. It is the same sign that 2018 labels as cls32 (P.123b) beside the same board. |
| 2016 | TRUE_NEGATIVE | The same cls32 disc beside the same board, slightly larger. |
| 2017 | TRUE_NEGATIVE | The same cls32 disc, clearly visible beside the board. |
| 2031 | TRUE_NEGATIVE | The cls32 disc is cut at the right edge, about half visible. 2030 labels the same cut sign (x=0.991, w=0.018), so the dataset convention labels partly visible signs. |
| 2051 | TRUE_NEGATIVE | Half of the cls32 disc is visible at the right edge. It is a near duplicate of 2052, which labels it. |

- **Wrong class in the rationales.** For 2015/2031/2051 the rationales name "the cls3 sign".
  The labelled sign in 2018, 2030 and 2052 is cls32, and the rationales claim it is not visible.
- **Agreed TRUE_NEGATIVE frames:**
  - 0544: the cls2/3 pole of 0543 has left the frame.
  - 2723: only the backs of signs and shop boards are visible.
- **Impact.** Under the proposed handling, TRUE_NEGATIVE frames become detector background, so
  these five frames would teach the detector to suppress a visible P.123b.
- **Fix.** Reclassify all five as UNLABELLED_SIGN_PRESENT (cls32) and re-issue the notes. Only 2
  of the 25 negatives remain usable as background.

### P2-1: the D-04 rule splits parameterised height classes in an unsafe way

The rule is applied per derived key, so the family P.117 is broken up:

- `16:2.0` becomes KEEP_TRAIN_ONLY_UNVERIFIED;
- `16:2.2` and `16:2.5` become DROP (evaluated as UNKNOWN);
- both W.239b values are dropped.

A detector or classifier trained on the class "P.117 2,0 m" alone will see every P.117 sign,
including 2,2 m and 2,5 m, as 2,0 m. That is a wrong value, which is worse than UNKNOWN for a
height restriction, and because the class is train-only, no evaluation will reveal it.

The report should flag this and offer the owner a family-level option, for example:

- treat P.117 as one train-only shape class whose value is read separately or not at all; or
- drop all P.117 values together.

A related but less acute caution applies to the speed family (38 has only 2 groups).

### P3 findings

- **P3-1: wrong class fields on agreed decisions.**
  - 1703–1708: `visible_classes` = 10. The cls10 sign below the 80/60 plates is hidden behind the
    white box truck in these frames. What is visible is the 80/60 speed plates (cls40/39), which
    are also unlabelled in 1709. The decision stays UNLABELLED_SIGN_PRESENT, but the classes
    should be `39 40`.
  - 2766: `visible_classes` = 18, and the rationale says 2767 labels cls18. 2767 actually labels
    cls13, and 2766 shows the same ĐI CHẬM triangle with its "CHÚ Ý QUAN SÁT" plate. The value
    should be 13.
  - 2723: the rationale says "cls41 pole of 2722". 2722 labels cls3.
- **P3-2: 2793–2797 should be UNLABELLED_SIGN_PRESENT (cls50), and UNCLEAR has no handling
  rule.**
  - A yellow curve-warning triangle is visible in 2793, 2795, 2796 and 2797, and partly in 2794,
    at the place 2798 labels cls50.
  - The report gives no handling for UNCLEAR. It should state that UNCLEAR frames are never
    background.
- **P3-3: the support-table column is ambiguous.** `largest_group_share` is computed over boxes,
  but the table lists images beside it, and the report does not say which. Also, a count of ≥3
  groups does not guarantee usable validation or test sets when one group dominates, for example:
  - class 28: groups of 26 and 1 images;
  - class 14: 35, 8, 3 and 1;
  - class 26: 47, 18, 14 and 1.

  Consider adding a minimum group size or share to the rule's wording.
- **P3-4: the negative-audit atlas does not support small-sign judgment.** The WP34 atlas shows
  the frames downscaled, and the missed signs in P1-1 are only a few pixels wide there. Future
  audits should zoom into the regions where the neighbouring frames have labels.

## Governance

- D-04 remains PENDING (owner). D-02 is owner-approved as D02-P1 per the pinned overlay. Gate 0
  remains BLOCKED.
- No split, relabel, training, upload, push or publication was performed.
- This record modifies no WP34 file, builder, test, notes, `PROJECT_MEMORY.md` or roadmap file.
