# D-02 owner decision — group identity

Status: `OWNER_APPROVED`
Decision date: `2026-10-17` (`Asia/Ho_Chi_Minh`)
Selected option: `D02-P1_WP31_R2_CAPTURE_GROUPS`

The owner approved option D02-P1: the 54 capture groups of M0-WP31-R2 (independent QA
PASS, `docs/review/wp31_r2_independent_qa_record.md`) are the DATASET01 `group_id`. Scene groups
(D02-P2) were not adopted.

## Registry

- `docs/review/generated/d02_group_id_registry.csv`: one row per stem, 3215 stems, 54 groups
  (largest [513, 411, 226, 190, 120]). Stem `0248` stays quarantined and has no group.
- Overlay: `docs/review/generated/d02_owner_decision_overlay.json`. Lineage pins the WP31-R2 package, its QA record, builder
  and test by SHA-256.

## Enforcement

`scripts/build_d02_owner_decision.py check-candidate --candidate <file>` rejects a candidate split
that places one `group_id` in two splits, contains stem `0248`, or references an
unknown stem. Missing or tampered inputs fail closed.

## Known limits accepted by the owner

- Groups come from provisional AI visual review, not human review or creator metadata.
- Cross-block linking covered near-identical views only; the grouping is not proven leak-free.
- The 12 negative runs are bridged at capture level but were never reviewed visually.

## Governance

D-02 is resolved and G0.6 is satisfied by this decision. Gate 0 remains BLOCKED because D-01,
D-03, D-04 and D-05 are still pending and no group-aware split (G0.7) exists yet.
`split_authorized=false` and `training_authorized=false`. No earlier package, the historical
decision template or raw data was changed.
