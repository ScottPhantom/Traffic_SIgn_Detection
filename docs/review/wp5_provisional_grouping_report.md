# M0-WP5 provisional grouping leakage review

Status: `WP5_READY_FOR_RE_REVIEW_PARTIAL_VISUAL_REVIEW`  
Boundary: `PROVISIONAL_REVIEW_ONLY_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT`

This package is a deterministic reviewer queue and partial visual adjudication. It is **not** creator metadata, group truth, a final split, taxonomy approval, or training authorization.

## Coverage and observed review

- Exact edge coverage: 3178 adjacency edges.
- Cross-split priority queue: 1031 edges, all placed before same-split edges.
- Exact proxy-sequence coverage: 589 sequences linked to the 24 QA-approved WP3 contact sheets.
- Actually visually reviewed: 6 edges (5 cross-split).
- Still `PENDING`: 3172 edges, including 1026 cross-split edges, plus 589 sequences.
- Reviewed outcomes: `{"NOT_RELATED": 2, "SAME_CAPTURE_CANDIDATE": 4}`.

## Provisional leakage hypotheses

- High-confidence capture components: 4 components across 8 images; 4 cross split.
- High-confidence physical-sign components: 2 components across 4 images; 2 cross split.
- Conflicts detected inside these provisional components: 0.
- Every component is labeled `PROVISIONAL_COMPONENT_NOT_GROUP_TRUTH` and cannot be consumed as a final `group_id`.

## Decision D-02 recommendation

Prefer **D02-A**: obtain creator/session metadata, because visual similarity cannot establish true capture sessions. If that is unavailable, **D02-B** remains a funded manual fallback only after all 3172 pending edges and 589 pending sequences are reviewed, all cross-split pairs are resolved, and a second reviewer checks positive/conflict cases. D-02 remains `PENDING`.

## Fail-closed manifest contract

- Manifest schema: v2.
- Canonical source/control roster: 11 exact ID/path records.
- Canonical non-manifest artifact roster: 137 exact ID/path records, including 128 JPEG pages plus the atlas index and required tables/reports/schema/layout.
- Count semantics: `EXCLUDES_MANIFEST_FILE`; the manifest cannot hash or count itself recursively.
- Verification rejects missing, duplicate or extra records; wrong paths/types; forged counts/bytes; missing first/middle/last atlas pages; path escape; and valid-but-unexpected files.

## Safety state

Gate 0 remains `BLOCKED`; training remains unauthorized. No split, taxonomy, source image, source label, model, or runtime artifact is changed by this package.
