# M0-WP19 — D02-C sequence review, Batch D

Status: `WP19_AWAITING_QA_SEQUENCE_BATCH_D_PM_PROVISIONAL_REVIEW`  
Boundary: `SEQUENCE_BATCH_D_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

This package records one PM/Codex provisional visual pass over the exact next 100 quarantine-
eligible canonical WP5 PENDING sequences after the independently QA-passed WP16-R1 Batch A,
WP17 Batch B and WP18 Batch C.
It does not approve D-02, create final/transitive group truth or a split, or authorize training.
D02-A creator/session metadata remains preferred.

## Selection and review protocol

- Selection: `proxy_sequence_0302` through `proxy_sequence_0401`, exact canonical order with no
  gap, after excluding the exact union of WP16, WP17 and WP18 (300-sequence eligible prefix) and
  the whole quarantined `proxy_sequence_0050`.
- Exclusion registry keeps canonical row 50 `PENDING`, `overlay_reviewed=False`, reason
  `CONTAINS_QUARANTINED_STEM_0248`; no member is removed or rewritten.
- Source coverage: 100 sequences, 422 unique member frames and 824 bbox occurrences; all
  image/label hashes, dimensions, decode state, classes and bbox context verified.
- Reviewer: `PM/Codex provisional sequence reviewer` at `2026-10-11T23:55:00+07:00`.
- All 100 sequences and all 422 member frames were directly inspected in the 100-page WP19 atlas.
  Proxy metrics were context only; creator/session/physical-sign identity metadata is unavailable.

## Hardened verifier contract

- Exact 101-file atlas roster: index plus one page for each sequence.
- Exact 31-field manifest top-level schema rejects every missing or unknown field; each nested
  source/artifact record is exact-key checked.
- Index, 100 JPEG pages and layout are regenerated in isolation and byte/deep-compared.
- Trusted review-notes SHA-256 `627e0598d077ccb568c252b7980833cd317803398385fce61e467c3e2de483b1` pins exact decisions and IDs.
  Coherent rollback and count-preserving decision-ID swaps cannot override this source anchor.

## Provisional capture-sequence outcomes

- `CONTINUOUS_CANDIDATE`: 100

## Provisional physical-sign-sequence outcomes

- `MULTIPLE_SIGNS`: 61
- `SAME_PHYSICAL_SIGN_CANDIDATE`: 39

## Confidence

- `HIGH`: 100

## Remaining workload and governance

- Canonical WP5 remains unchanged at 589 PENDING sequences.
- WP16+WP17+WP18+WP19 overlays cover 400 sequences; 189 remain outside all four overlays, including
  the quarantined sequence that stays canonical `PENDING` and unreviewed.
- Canonical WP5 remains unchanged at 3,172 PENDING edges; five QA-passed cross-split overlays do
  not resolve the remaining 2,146 other pending edges or create sequence truth.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `training_authorized=false`.

## Artifacts

- Decisions: `docs/review/wp19_sequence_review_annotations_batch_d.json`.
- Selection: `docs/review/generated/wp19_sequence_batch_d_selection.csv`.
- Exclusions: `docs/review/generated/wp19_sequence_batch_d_exclusions.csv`.
- Member lineage: `docs/review/generated/wp19_sequence_batch_d_member_lineage.csv`.
- Layout audit: `docs/review/generated/wp19_sequence_batch_d_layout_audit.json`.
- Atlas: `docs/review/assets/wp19/sequence_batch_d/index.html` and 100 JPEG pages.
- Manifest: `docs/review/generated/wp19_sequence_batch_d_manifest.json`.
