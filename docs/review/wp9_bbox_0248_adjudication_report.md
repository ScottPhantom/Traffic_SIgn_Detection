# M0-WP9 bbox 0248 adjudication report

Status: `M0_WP9_AWAITING_QA_DECISION_SUPPORT_ONLY`  
Boundary: `DECISION_SUPPORT_ONLY_NO_RAW_OVERWRITE_NO_RELABEL_NO_SPLIT_NO_TRAINING`

## Verified raw fact

- Target: stem `0248`, split `train`, class `49` (`P.124c`), label line `1` / zero-based index `0`.
- Image: `960x540`, SHA-256 `07eab2035dc10b7b08be71d76c3c32ffdb960722839414f1e474da20c3ad0cbd`.
- Raw label SHA-256: `f4ec410f7bff3ee03f6110308e8e95f57c92bcc7ebf45ff3affcfd885b419c77`; source bytes remain unchanged.
- Raw YOLO: `0.992188 0.345370 0.053125 0.101852`.
- Raw pixel box: `(927.00048, 158.99976, 978.00048, 213.99984)`.
- Right overflow: `18.00048 px` beyond image boundary `x=960`.
- Line 2 remains inside the image and is not changed by the derived candidate.

## Visual assessment

The full raw frame and boundary zoom show that the rightmost target sign is itself cut by the
right image edge. The case is therefore classified as
`IMAGE_EDGE_TRUNCATED_OBJECT_WITH_RAW_BOX_EXTENDING_BEYOND_RIGHT_BOUNDARY`, with `HIGH`
confidence. It is not merely annotation overshoot around a fully visible object.

Frames `0247` and `0249` support continuity as adjacency context only. Their relationship is
`ADJACENCY_CONTEXT_PROXY_ONLY_NOT_GROUP_GROUND_TRUTH`; they do not establish a final group.

## Options presented to the owner

1. `keep_raw_as_warning`: preserve the immutable raw label and warning; no training approval.
2. `create_separate_clipped_derived_annotation`: create a separate image-valid candidate for
   review/tooling; never overwrite raw and do not treat it as training-approved.
3. `quarantine_image_from_approved_dataset`: exclude stem `0248` from approved training until an
   owner decision is recorded.

## PM recommendation — proposal, not owner approval

Recommend `QUARANTINE_FROM_TRAINING_PENDING_OWNER_DECISION` while keeping raw handling as `KEEP_RAW_IMMUTABLE_FOR_PROVENANCE`. A clipped candidate
is supplied only as `REVIEW_ONLY_NOT_APPROVED_TRAINING_LABEL`. Clipping fixes coordinate validity but cannot reconstruct
the missing portion of the sign, so it is not sufficient evidence to authorize training.

Derived line 1:

```text
49 0.982812750 0.345370000 0.034374500 0.101852000
```

The transform is limited to `x_max := min(978.00048, 960.0)`; `x_min`, `y_min`, and `y_max` stay
unchanged, then YOLO `x_center` and `width` are recomputed. Line 2 is copied unchanged.

## Governance state

- Owner decision `G0.4-bbox-0248`: `PENDING`; selected option: `null`.
- Gate 0: `BLOCKED`.
- `relabel_authorized=false`, `split_authorized=false`, `training_authorized=false`.
- This package does not mutate raw data, approve a relabel, create a split, or authorize training.

## Evidence binding

- WP1 manifest: `28adbf21dd2057fe5fc7999daccaa52d1201ea0459ef1bb7475a780ed85c51c6`.
- WP2 manifest: `506ec141bef032282f90b3d35741ece49a43fed617c3dea93863d4c32330a505`.
- WP4 manifest: `c60c09018900071cc66d8bc01db32300f4efc6a4316bda9f506819026400db1c`.
- WP8 manifest (must remain unchanged): `9d8fc460b8162874b4082940b0e7f3ceb174c068a92378974ebd93b55da20348`.
- WP9 adjudication contract: `0b0a87e1b1b8f4c1c2cac739eb87aa6441ec1cbfbdbad264a0f391231c002da5`.
