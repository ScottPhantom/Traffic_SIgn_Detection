# M0-WP38 orientation-correction implementation record

Date: 2026-10-22  
Status: `WP38_AWAITING_INDEPENDENT_QA`

## Scope and boundary

WP38 addresses the 39 frames in capture group `D02-C0034` whose decoded size is
540x960 even though the scene was recorded in landscape orientation. The package does not edit
the raw JPEG files. It produces a decoded-pixel derivative by rotating each source frame 90
degrees counter-clockwise, resulting in a 960x540 PNG, and applies the same transform to the
validation-only YOLO labels.

This work does not change the WP36-R1 split, authorize training, open the sealed test, or replace
any pinned predecessor artifact. The derived package remains evidence-only until independent QA
passes and a separately approved successor contract authorizes its use.

## Exact input and output contract

- Exact source roster: stems `1319` through `1357`, inclusive; 39 frames.
- Capture group: `D02-C0034`.
- Split: validation only.
- Source size: 540x960; derived size: 960x540.
- Rotation: `CCW_90`.
- Normalized YOLO transform: `x' = y`, `y' = 1 - x`, `w' = h`, `h' = w`.
- Transformed labels: 29 boxes across YOLO class IDs 12 and 14.
- Raw images mutated: false.
- Sealed test accessed: false.
- Training authorized: false.

## Implemented artifacts

- Builder/verifier: `scripts/build_wp38_orientation_correction.py`.
- Tests: `tests/test_wp38_orientation_correction.py`.
- Lineage ledger: `docs/review/generated/wp38_orientation_correction_lineage.csv`.
- Manifest: `docs/review/generated/wp38_orientation_correction_manifest.json`.
- Ignored derived data: `data/processed/wp38_orientation_corrected/`.
- Ignored visual-review pages: `docs/review/assets/wp38/orientation_correction/`.
- Parallel verifier registration: `wp38` in `scripts/run_parallel_checks.py`.

The package has an exact roster, hashes every source and derived file, pins all predecessor inputs,
binds the builder source hash, writes atomically, rejects unexpected files, and rejects symlink or
hardlink outputs.

## Current measured evidence

- Builder result: `valid=true`, `frame_count=39`, `box_count=29`, `rotation=CCW_90`.
- Manifest SHA-256: `a59fd9f59236e990be722e09063a52065e1ed0a0dcb0d7f03fa4baf52d82313e`.
- Lineage SHA-256: `1d7340d5c222925751a45c30d58b4a2ebc04715457d048842036be5414c6e659`.
- Builder SHA-256: `c3b2726241b53be23a9e1b233d38b5dad3994d2f6fc073beabef82f6bd89c23e`.
- Targeted test result: 7 passed.
- Manual visual review: all eight pages, covering all 39 frames, were inspected; scene orientation is
  upright and the displayed boxes remain aligned with the signs.

These are implementation-team observations, not an independent QA verdict.

## Independent QA acceptance criteria

QA must independently reproduce the roster and rotation direction, inspect all 39 visual panels,
recompute decoded-pixel equality and transformed label geometry, confirm exact artifact hashes and
raw immutability, exercise tamper/extra-file/symlink/hardlink defenses, and confirm
`sealed_test_accessed=false` and `training_authorized=false`. Only an append-only independent QA
PASS may move WP38 beyond `WP38_AWAITING_INDEPENDENT_QA`.
