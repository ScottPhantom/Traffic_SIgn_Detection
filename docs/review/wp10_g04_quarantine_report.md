# M0-WP10 G0.4 owner quarantine resolution

Status: `M0_WP10_AWAITING_QA_OWNER_APPROVED_QUARANTINE_ENFORCEMENT`  
Decision: `G0.4-bbox-0248` → `APPROVED_QUARANTINE` (`OWNER_APPROVED`)  
Decision date: `2026-10-11` (`Asia/Saigon`)  
Boundary: `OWNER_APPROVAL_OVERLAY_AND_FAIL_CLOSED_QUARANTINE_ONLY_NO_RAW_MUTATION_NO_FINAL_SPLIT_NO_TRAINING`

## Owner-approved operational rule

The owner approved quarantine for the entire image/stem `0248`. This decision applies to both raw
label rows, not only the out-of-bounds first box. Stem `0248` must be excluded from every candidate
split and from training input. The raw image and label remain immutable.

The WP9 clipped annotation remains `REVIEW_EVIDENCE_ONLY_NOT_TRAINING_LABEL`. It is not a replacement label and may
not be admitted to split generation or training.

Class `49` and its taxonomy remain in scope. The quarantine applies only to sample/stem `0248`.

## Fail-closed enforcement

`scripts/build_wp10_g04_quarantine.py check-candidate` validates the hash-bound WP10 package before
reading a candidate. If the overlay or registry is missing, invalid, re-hashed after semantic
tampering, or disconnected from the pinned raw/WP9 lineage, the candidate is rejected. If a valid
candidate list or split manifest contains stem `0248`, it is rejected. Candidates without `0248`
can pass this quarantine-specific check, but that result does **not** authorize a final split or
training.

Examples:

```bash
uv run python scripts/build_wp10_g04_quarantine.py verify --repo-root .
uv run python scripts/build_wp10_g04_quarantine.py check-candidate --repo-root . --candidate candidate.json
```

Accepted candidate formats are a JSON list of stems, a JSON object with `stems`, a JSON object with
`splits` containing stem lists, or a UTF-8 text file with one stem per nonblank line.

## Immutable lineage

- Raw image SHA-256: `07eab2035dc10b7b08be71d76c3c32ffdb960722839414f1e474da20c3ad0cbd`.
- Raw label SHA-256: `f4ec410f7bff3ee03f6110308e8e95f57c92bcc7ebf45ff3affcfd885b419c77`.
- Historical decision-status SHA-256: `87d81262e907bb1c479cfac6535e7b3f67a368c371e96b810aa02f2e92d0d72c`.
- WP8 manifest SHA-256: `9d8fc460b8162874b4082940b0e7f3ceb174c068a92378974ebd93b55da20348`.
- WP9 manifest SHA-256: `cea9423616de0bf4649d71e40f395b4cdc18ff3ea2f80e9829ea4063f009656f`.
- WP9 derived-candidate SHA-256: `8fcdd25dce463d7c57ef5f9f95ce1810db056d7d02e260e2126e3656c4a691b6`.
- WP10 owner-decision contract SHA-256: `2ebc5ffccc89a395cc7910811762421d7be6a0bb5c88448c550b9ad5146664a1`.

## Governance boundary

WP10 is awaiting QA. G0.4 becomes formally closed only after WP10 QA PASS. D-01 through D-05 remain
`PENDING`; Gate 0 remains `BLOCKED`; `split_authorized=false`; `training_authorized=false`. This
package does not create a final split, relabel raw data, train a model, or change taxonomy class 49.
