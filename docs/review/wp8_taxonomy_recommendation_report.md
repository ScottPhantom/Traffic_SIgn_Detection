# M0-WP8 - Provisional 52-class taxonomy recommendation

Status: `M0_WP8_AWAITING_QA_PROPOSAL_ONLY`  
Boundary: `NATIVE_52_CLASS_TAXONOMY_RECOMMENDATION_ONLY_NO_D03_APPROVAL_NO_RELABEL_NO_SPLIT_NO_TRAINING`

This is a PM recommendation package for independent QA and domain review. It does not decide D-03, relabel data, create a split, authorize training, or convert a GTSRB relation into Vietnamese taxonomy truth. Every row remains `UNAPPROVED`.

## Package-level recommendation

1. Version the native DATASET01 52-class taxonomy first.
2. Keep every GTSRB relation analysis-only; never use it as an automatic merge or training target.
3. Apply code/name corrections only after per-row approval.
4. Route unresolved variant, composite, supplementary, or out-of-scope cases to explicit review and, if needed, a future UNKNOWN policy.
5. Treat support and rarity as data-risk metadata only. `rare_flag=true` means fewer than 100 images and never authorizes semantic merging.

## Recommendation counts

- `CORRECT_CODE_OR_NAME_PROPOSAL`: 19
- `KEEP_CURRENT`: 23
- `OUT_OF_SCOPE_PROPOSAL`: 1
- `SEMANTIC_REVIEW_REQUIRED`: 9

## GTSRB dispositions

- `DIRECT_ANALYSIS_ONLY`: 11
- `NONE`: 27
- `PARTIAL_ANALYSIS_ONLY`: 13
- `REVIEW_REQUIRED`: 1

## Required conflict register

| ID | Current | WP4 | Candidate | Native recommendation | GTSRB | Required reviewer action |
|---:|---|---|---|---|---|---|
| 3 | `R.302a` | PARTIAL | `R.302a` | `CORRECT_CODE_OR_NAME_PROPOSAL` | `PARTIAL_ANALYSIS_ONLY` | Approve or reject the English-label correction after checking QCVN page 117 and all three representatives. |
| 22 | `W.221b` | PARTIAL | `W.221b` | `CORRECT_CODE_OR_NAME_PROPOSAL` | `PARTIAL_ANALYSIS_ONLY` | Approve or reject the English-label correction after checking QCVN page 106 and representatives. |
| 23 | `P.111` | MISMATCH | `UNRESOLVED` | `SEMANTIC_REVIEW_REQUIRED` | `NONE` | Review each source against P.111a-d and approve a variant policy or UNKNOWN route; do not assign generic P.111 automatically. |
| 25 | `S.505a*Xe máy` | MISMATCH | `UNRESOLVED` | `SEMANTIC_REVIEW_REQUIRED` | `NONE` | Define a main-sign-plus-S.505a representation or route to UNKNOWN; do not approve Motorcycles Only as an independent QCVN meaning. |
| 28 | `S.505a*Xe tải và công` | MISMATCH | `UNRESOLVED` | `SEMANTIC_REVIEW_REQUIRED` | `NONE` | Review the depicted vehicle types and main-sign context; define an S.505a compound policy or UNKNOWN route. |
| 30 | `S.505a*Xe tải` | MISMATCH | `UNRESOLVED` | `SEMANTIC_REVIEW_REQUIRED` | `NONE` | Define a main-sign-plus-S.505a representation or route to UNKNOWN; do not approve Trucks Only as an independent QCVN meaning. |
| 31 | `Camera` | NOT_FOUND | `UNRESOLVED` | `OUT_OF_SCOPE_PROPOSAL` | `NONE` | Obtain an authoritative non-QCVN source or approve out-of-scope/UNKNOWN handling; do not assert a QCVN code. |
| 34 | `B.8a` | MISMATCH | `P.108a` | `CORRECT_CODE_OR_NAME_PROPOSAL` | `NONE` | Approve or reject both the code correction and English vehicle-type correction before relabeling. |
| 47 | `P.124b1` | MISMATCH | `P.124b` | `CORRECT_CODE_OR_NAME_PROPOSAL` | `NONE` | Approve or reject the candidate P.124b correction before relabeling; note very-low support separately. |
| 51 | `W.246c` | EXACT | `W.246c` | `KEEP_CURRENT` | `PARTIAL_ANALYSIS_ONLY` | Approve or reject the native row; keep GTSRB 38 analysis-only because warning and mandatory families differ. |

The register deliberately preserves these boundaries: S.505a means supplementary `Loại xe`; B.8a is a section/figure while P.108a is the sign code; P.124b1 is unsupported and P.124b is only a candidate; class 31 has no asserted QCVN code; class 51 is an exact native W.246c row but only a partial GTSRB analysis relation; class 23 requires P.111a-d variant review rather than a generic P.111 assignment.

## WP8-R1 QA repair clarifications

| ID | Current dataset label | Proposed QCVN-aligned code/name | Native recommendation | Sign policy | Required reviewer action |
|---:|---|---|---|---|---|
| 6 | Chỗ ngoặt nguy hiểm vòng bên trái / Danger zone on the left | `W.201a` / Dangerous Curve to the Left | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | Approve or reject the English-label correction from Danger zone on the left to Dangerous Curve to the Left; keep code W.201a and GTSRB analysis-only. |
| 14 | Cấm xe tải / No Trucks Allowed | `P.106a` / No Trucks | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | Approve or reject normalization to the fixed P.106a No Trucks class; keep GTSRB vehicles-over-3.5t analysis-only because the weight scope belongs to P.106b. |
| 42 | Các xe chỉ được rẽ trái / Left Turn | `R.301e` / Mandatory Left Turn | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | Approve or reject the English-label correction from Left Turn to Mandatory Left Turn; keep code R.301e and GTSRB analysis-only. |
| 50 | Chỗ ngoặt nguy hiểm vòng bên phải / Danger zone on the right | `W.201b` / Dangerous Curve to the Right | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | Approve or reject the English-label correction from Danger zone on the right to Dangerous Curve to the Right; keep code W.201b and GTSRB analysis-only. |

For class 14, all three pinned representatives depict ordinary P.106a without a numeric weight value. QCVN section B.6 assigns the fixed truck prohibition to P.106a and the numeric weight parameter to P.106b. The other three rows retain their QCVN codes but require explicit English-name correction proposals. These remain reviewer proposals, not approved relabels.

## Complete reviewer matrix

| ID | Current | WP4 | Native recommendation | Sign policy | GTSRB disposition | UNKNOWN route | Rare |
|---:|---|---|---|---|---|---|---|
| 0 | `W.224` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `DIRECT_ANALYSIS_ONLY` | `KEEP_NATIVE_NO_UNKNOWN` | false |
| 1 | `W.205c` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `PARTIAL_ANALYSIS_ONLY` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 2 | `P.102` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `DIRECT_ANALYSIS_ONLY` | `KEEP_NATIVE_NO_UNKNOWN` | false |
| 3 | `R.302a` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | `PARTIAL_ANALYSIS_ONLY` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | false |
| 4 | `W.205a` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `PARTIAL_ANALYSIS_ONLY` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 5 | `W.207` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `PARTIAL_ANALYSIS_ONLY` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | false |
| 6 | `W.201a` | EXACT | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | `DIRECT_ANALYSIS_ONLY` | `KEEP_NATIVE_NO_UNKNOWN` | false |
| 7 | `P.123a` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | false |
| 8 | `I.434a` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | false |
| 9 | `R.303` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `DIRECT_ANALYSIS_ONLY` | `KEEP_NATIVE_NO_UNKNOWN` | true |
| 10 | `P.130` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | false |
| 11 | `I.409` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 12 | `R.415a` | EXACT | `SEMANTIC_REVIEW_REQUIRED` | `COMPOSITE_SIGN_REVIEW` | `NONE` | `REVIEW_NATIVE_OR_UNKNOWN` | false |
| 13 | `W.245a` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `PARTIAL_ANALYSIS_ONLY` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | false |
| 14 | `P.106a*Xe tải` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | `PARTIAL_ANALYSIS_ONLY` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 15 | `W.203c` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `DIRECT_ANALYSIS_ONLY` | `KEEP_NATIVE_NO_UNKNOWN` | true |
| 16 | `P.117*` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `PARAMETERIZED_SIGN_REVIEW` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 17 | `P.124a*` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `PARAMETERIZED_SIGN_REVIEW` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | false |
| 18 | `P.107` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | `PARTIAL_ANALYSIS_ONLY` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | false |
| 19 | `P.124d` | EXACT | `SEMANTIC_REVIEW_REQUIRED` | `COMPOSITE_SIGN_REVIEW` | `NONE` | `REVIEW_NATIVE_OR_UNKNOWN` | true |
| 20 | `P.103a` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `PARTIAL_ANALYSIS_ONLY` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 21 | `W.203b` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 22 | `W.221b` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | `PARTIAL_ANALYSIS_ONLY` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 23 | `P.111` | MISMATCH | `SEMANTIC_REVIEW_REQUIRED` | `VARIANT_SELECTION_REVIEW` | `NONE` | `REVIEW_NATIVE_OR_UNKNOWN` | false |
| 24 | `P.129` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 25 | `S.505a*Xe máy` | MISMATCH | `SEMANTIC_REVIEW_REQUIRED` | `SUPPLEMENTARY_SIGN_REVIEW` | `NONE` | `REVIEW_NATIVE_OR_UNKNOWN` | true |
| 26 | `W.246a` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | `PARTIAL_ANALYSIS_ONLY` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 27 | `W.225` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `DIRECT_ANALYSIS_ONLY` | `KEEP_NATIVE_NO_UNKNOWN` | true |
| 28 | `S.505a*Xe tải và công` | MISMATCH | `SEMANTIC_REVIEW_REQUIRED` | `SUPPLEMENTARY_SIGN_REVIEW` | `NONE` | `REVIEW_NATIVE_OR_UNKNOWN` | true |
| 29 | `P.104` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 30 | `S.505a*Xe tải` | MISMATCH | `SEMANTIC_REVIEW_REQUIRED` | `SUPPLEMENTARY_SIGN_REVIEW` | `NONE` | `REVIEW_NATIVE_OR_UNKNOWN` | false |
| 31 | `Camera` | NOT_FOUND | `OUT_OF_SCOPE_PROPOSAL` | `ATOMIC_SIGN` | `NONE` | `REVIEW_NATIVE_OR_UNKNOWN` | true |
| 32 | `P.123b` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | false |
| 33 | `W.202b` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `PARTIAL_ANALYSIS_ONLY` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 34 | `B.8a` | MISMATCH | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 35 | `P.137` | EXACT | `SEMANTIC_REVIEW_REQUIRED` | `COMPOSITE_SIGN_REVIEW` | `NONE` | `REVIEW_NATIVE_OR_UNKNOWN` | true |
| 36 | `P.139` | EXACT | `SEMANTIC_REVIEW_REQUIRED` | `COMPOSITE_SIGN_REVIEW` | `NONE` | `REVIEW_NATIVE_OR_UNKNOWN` | true |
| 37 | `W.205b` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `PARTIAL_ANALYSIS_ONLY` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 38 | `P.127*50` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `PARAMETERIZED_SIGN_REVIEW` | `DIRECT_ANALYSIS_ONLY` | `KEEP_NATIVE_NO_UNKNOWN` | false |
| 39 | `P.127*60` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `PARAMETERIZED_SIGN_REVIEW` | `DIRECT_ANALYSIS_ONLY` | `KEEP_NATIVE_NO_UNKNOWN` | false |
| 40 | `P.127*80` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `PARAMETERIZED_SIGN_REVIEW` | `DIRECT_ANALYSIS_ONLY` | `KEEP_NATIVE_NO_UNKNOWN` | false |
| 41 | `P.127*40` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `PARAMETERIZED_SIGN_REVIEW` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | false |
| 42 | `R.301e` | EXACT | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | `DIRECT_ANALYSIS_ONLY` | `KEEP_NATIVE_NO_UNKNOWN` | true |
| 43 | `W.239b*` | PARTIAL | `CORRECT_CODE_OR_NAME_PROPOSAL` | `PARAMETERIZED_SIGN_REVIEW` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 44 | `W.233` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `REVIEW_REQUIRED` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 45 | `I.407a` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | false |
| 46 | `P.131a` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | false |
| 47 | `P.124b1` | MISMATCH | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 48 | `W.210` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `NONE` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |
| 49 | `P.124c` | EXACT | `SEMANTIC_REVIEW_REQUIRED` | `COMPOSITE_SIGN_REVIEW` | `NONE` | `REVIEW_NATIVE_OR_UNKNOWN` | false |
| 50 | `W.201b` | EXACT | `CORRECT_CODE_OR_NAME_PROPOSAL` | `ATOMIC_SIGN` | `DIRECT_ANALYSIS_ONLY` | `KEEP_NATIVE_NO_UNKNOWN` | false |
| 51 | `W.246c` | EXACT | `KEEP_CURRENT` | `ATOMIC_SIGN` | `PARTIAL_ANALYSIS_ONLY` | `REJECT_CROSSWALK_KEEP_NATIVE_PROVISIONALLY` | true |

## Evidence and audit trail

- Machine-readable matrix: `docs/review/generated/wp8_taxonomy_recommendation.csv` and `docs/review/generated/wp8_taxonomy_recommendation.json`.
- Each row carries exact WP4 evidence, QCVN page/section/figure or scoped NOT_FOUND evidence, support/risk, three representative stems, image and label SHA-256 values, and source bbox line/coordinates.
- Decision atlas: `docs/review/assets/wp8/taxonomy_decision_atlas/index.html` plus 13 PNG pages, derived from the pinned WP4 atlas without rebuilding WP4.
- Layout audit: `docs/review/generated/wp8_taxonomy_layout_audit.json`.
- Manifest and verifier: `docs/review/generated/wp8_taxonomy_manifest.json` and `scripts/build_wp8_taxonomy_recommendation.py verify`.

## Governance

- All 52 rows: `UNAPPROVED`.
- D-03: `PENDING`.
- Gate 0: `BLOCKED`.
- Relabel, split, and training: not authorized.
