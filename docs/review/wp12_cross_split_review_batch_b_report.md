# M0-WP12-R1 — D02-B cross-split manual review, Batch B

Status: `WP12_R1_AWAITING_QA_BATCH_B_PM_PROVISIONAL_REVIEW`  
Boundary: `BATCH_B_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

This package records one PM/Codex provisional visual pass over exactly 250 canonical WP5 pending
cross-split pairs. It does not approve D-02, does not create final/transitive group truth or a split,
and does not authorize training. D02-A creator/session metadata remains preferred.

## Selection and review protocol

- Selection: exact next 250 unique canonical WP5 rows with `cross_split=True` and
  `review_status=PENDING`, preserving WP5 review order and excluding the exact 100-edge WP7 Batch-A
  roster. Canonical WP5 reviewed rows are ineligible by construction.
- Selected edge range: `edge_000315` through `edge_001033` in Batch-B order.
- Source coverage: 500 endpoint rows with 1553 total boxes;
  quarantined stem `0248` is absent.
- Reviewer: `PM/Codex provisional visual reviewer` at `2026-10-11T18:00:00+07:00`.
- All 250 pairs/500 raw frames were directly inspected in the dedicated 50-page WP12 atlas before
  annotation. Proxy fields were context only.
- Creator/session/physical-sign identity metadata: unavailable for every record.

## R1 repair lineage

- Independent QA rejected the pre-repair manifest `0b5c90de79326bc7cccb18830078c5aef5ec46bd8559ca1f909e3a5878456347` because the
  verifier did not semantically bind atlas bytes/layout to deterministic regeneration and did not
  pin the approved PM review-notes source.
- R1 requires the exact 51-file atlas roster, regenerates the index/50 JPEG pages and layout audit
  in an isolated temporary directory for byte/deep comparison, and pins review-notes SHA-256
  `27adbf366cfbfd2c03c1025e82bd6cef26e1b353e1e50340ddc6d7a5f9ed75b4` plus the approved decision counts and unresolved edge IDs.
- Status remains awaiting independent QA. This repair does not change any PM visual decision.
- Independent QA found 0 blind capture-decision disagreements and visually accepted 50/50 pages;
  its package verdict remained FAIL solely because of the three verifier blockers repaired here.

## Provisional capture outcomes

- `NOT_RELATED`: 8
- `SAME_CAPTURE_CANDIDATE`: 240
- `UNRESOLVED`: 2

Capture-hypothesis count cross-check:

- `NOT_RELATED`: 8
- `SAME_CAPTURE_CANDIDATE`: 240
- `UNRESOLVED`: 2

## Provisional physical-sign outcomes

- `NOT_RELATED`: 14
- `SAME_PHYSICAL_SIGN_CANDIDATE`: 235
- `UNRESOLVED`: 1

## Confidence

- `HIGH`: 243
- `MEDIUM`: 7

## Remaining workload and governance

- Canonical WP5 remains unchanged at 3172 PENDING edges until this separate package receives QA review.
- Outside the WP7 and WP12 overlays, 2822 canonical
  PENDING edges remain without either overlay; 676
  of those are cross-split.
- All 589 WP5 sequences remain PENDING.
- Any future PM/QA disagreement remains unresolved/uncertain and cannot form a positive component.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `training_authorized=false`.

## Artifacts

- Decisions: `docs/review/wp12_visual_review_annotations_batch_b.json`.
- Selection: `docs/review/generated/wp12_batch_b_selection.csv`.
- Source lineage: `docs/review/generated/wp12_batch_b_source_lineage.csv`.
- Layout audit: `docs/review/generated/wp12_batch_b_layout_audit.json`.
- Atlas: `docs/review/assets/wp12/batch_b/index.html` and 50 JPEG pages.
- Manifest: `docs/review/generated/wp12_batch_b_manifest.json`.
