# M0-WP32 — cross-block link review

Status: `WP32_AWAITING_QA_REVIEW`
Boundary: `CROSS_BLOCK_LINK_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_SPLIT_NO_TRAINING`

WP31 independent QA failed because DATASET01 filename blocks from different rides interleave:
linking only numerically adjacent stems put one ride and one physical sign into several capture
groups. WP32 generates candidate links between frames in different WP31 capture groups, records a
PM visual decision for each, and re-reviews the C0079 interleaved cls23 sub-sequence.

## Candidate generation

- Near-duplicate thumbnail: 32×18 grayscale, per-image z-normalized, mean absolute difference
  < 0.35 to a frame in another capture group (same-group adjacent median ≈ 0.21).
- Label geometry: same class, box centre within 0.02, width/height ratio within
  1.25, and thumbnail difference < 0.6.
- Each candidate capture-group pair is represented by its most similar frame pair:
  54 group pairs.
- Limitation: both signals favour near-identical viewpoints. The same sign seen from a clearly
  different distance or angle in another block can still be missed, so WP32 lowers the leak risk
  but does not prove its absence.

## Decisions

- Cross-group pairs reviewed: 54. Capture links: 47. Physical-sign links:
  45.
- Links are leak-conservative: `SAME` and `UNRESOLVED` both link; only `NOT_RELATED` keeps groups
  apart.

## C0079 sub-sequence re-review

| Row | Kind | Stems | Capture | Physical sign |
| --- | --- | --- | --- | --- |
| `x055` | C0079_EDGE_edge_002045 | 2070/2071 | SAME_CAPTURE_CANDIDATE | NOT_RELATED |
| `x056` | C0079_EDGE_edge_002055 | 2080/2081 | SAME_CAPTURE_CANDIDATE | NOT_RELATED |
| `x057` | C0079_EDGE_edge_002056 | 2081/2082 | SAME_CAPTURE_CANDIDATE | NOT_RELATED |
| `x058` | C0079_EDGE_edge_002066 | 2091/2092 | SAME_CAPTURE_CANDIDATE | NOT_RELATED |
| `x059` | C0079_EDGE_edge_002067 | 2092/2093 | SAME_CAPTURE_CANDIDATE | NOT_RELATED |
| `x060` | C0079_EDGE_edge_002077 | 2102/2103 | SAME_CAPTURE_CANDIDATE | NOT_RELATED |
| `x061` | C0079_EDGE_edge_002078 | 2103/2104 | SAME_CAPTURE_CANDIDATE | NOT_RELATED |
| `x062` | C0079_EDGE_edge_002086 | 2111/2112 | SAME_CAPTURE_CANDIDATE | NOT_RELATED |
| `x063` | C0079_EDGE_edge_002087 | 2112/2113 | SAME_CAPTURE_CANDIDATE | NOT_RELATED |
| `x064` | C0079_SUBSEQUENCE | 2070/2081 | SAME_CAPTURE_CANDIDATE | SAME_PHYSICAL_SIGN_CANDIDATE |
| `x065` | C0079_SUBSEQUENCE | 2081/2092 | SAME_CAPTURE_CANDIDATE | SAME_PHYSICAL_SIGN_CANDIDATE |
| `x066` | C0079_SUBSEQUENCE | 2092/2103 | SAME_CAPTURE_CANDIDATE | SAME_PHYSICAL_SIGN_CANDIDATE |
| `x067` | C0079_SUBSEQUENCE | 2103/2112 | SAME_CAPTURE_CANDIDATE | SAME_PHYSICAL_SIGN_CANDIDATE |
| `x068` | C0079_SUBSEQUENCE | 2112/2122 | SAME_CAPTURE_CANDIDATE | SAME_PHYSICAL_SIGN_CANDIDATE |
| `x069` | C0079_SUBSEQUENCE | 2122/2133 | SAME_CAPTURE_CANDIDATE | SAME_PHYSICAL_SIGN_CANDIDATE |
| `x070` | C0079_SUBSEQUENCE | 2133/2144 | SAME_CAPTURE_CANDIDATE | SAME_PHYSICAL_SIGN_CANDIDATE |
| `x071` | C0079_SUBSEQUENCE | 2144/2155 | SAME_CAPTURE_CANDIDATE | SAME_PHYSICAL_SIGN_CANDIDATE |

## Governance

Reviewer `PM/Codex provisional visual reviewer` at `2026-10-17T20:00:00+07:00`. Decisions are provisional. They change no earlier package
and no canonical WP5 row. D-02 remains PENDING, Gate 0 remains BLOCKED,
`split_authorized=false` and `training_authorized=false`.

## Artifacts

- Candidates: `docs/review/generated/wp32_cross_block_candidates.csv`; decisions: `docs/review/generated/wp32_cross_block_decisions.csv`;
  links: `docs/review/generated/wp32_cross_block_links.csv`.
- Review notes (trusted input): `docs/review/wp32_cross_block_review_notes.csv`.
- Atlas: `docs/review/assets/wp32/cross_block/` (18 pages).
- Manifest: `docs/review/generated/wp32_cross_block_manifest.json`.
