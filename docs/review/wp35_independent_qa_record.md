# M0-WP35 independent QA record

Status: `QA_PASS_WP35_REAL_FRAME_AUGMENTATION_TRAIN_ONLY_PROVISIONAL_EVIDENCE_ONLY`
Reviewer: `Claude Code QA session (did not author WP35)`
Reviewed at: `2026-10-18T03:30:00+07:00`
Boundary: `QA_OF_TRAIN_ONLY_AUGMENTATION_ONLY_NOT_EVALUATION_EVIDENCE_NO_SPLIT_NO_TRAINING_RUN`

This append-only record reports independent QA of M0-WP35, the real-frame augmentation for the
12 rare classes of D-04 part 1. It modifies no package, builder, test, owner record,
`PROJECT_MEMORY.md` or roadmap file. It also does not modify the git-ignored output in
`data/processed/wp35_enrichment/`.

## Verdict

- **WP35: PASS.** 0 P0, 0 P1, 0 P2, 4 P3.
- The method matches the owner's revised D-04 part 1 decision:
  - no pasting or synthesis;
  - no flip;
  - small rotation and zoom-in crops of the original frames;
  - photometric changes only.
- In the whole set I found no cut labelled sign, no black border and no wrong or missing label.

## Package bytes reviewed

- Builder `be194e3d397d8294…`, test `28c6e609ab64e82e…`, report `7c7b1882bcb8e81e…`.
- Lineage `e802fc264feff516…`, manifest `e9d42ec569a55cc1…`, preview `2d1b73c257aef4ff…`.
- Output: 1,800 images and 1,800 labels (175 MB).

## Checks performed

1. **Independent geometric check of all 1,800 images (QA-only script; does not import the
   builder).**

   For every augmented image, the script rebuilds the affine transform from the lineage
   (angle, crop scale and crop centre), maps **every** WP33 box of the source frame into the
   output, and compares the result with the label file. This includes excluded, UNKNOWN and
   other-class boxes.
   - Labels match exactly:
     - same keys in the same order for all 1,800 files;
     - largest coordinate difference 0.00045, normalised, which is the rounding of the lineage
       parameters;
     - no missing or extra boxes.
   - No cut box: with a 1.5 px tolerance for that rounding, no source box of any class is
     partly inside the output. Every box is fully inside or fully outside.
   - No black border: the output window lies inside the rotated source frame in all 1,800
     images.
   - Target size: no non-fallback target box is smaller than 12 px.
   - Counts: 150 images for each of the 12 owner classes, and every source stem's D-02 group
     equals the lineage. There are 10 source groups:

     | Classes | Source group |
     | --- | --- |
     | 1 and 51 | C0014 |
     | 16:2.2 and 43:2.7 | C0022 |
     | each other class | its own group |
   - Fallbacks: 99 images have no rotation. Of these, 39 are zoom-only and 60 are photometry-only
     (crop scale 1.000), mostly 43:2.7 (30), 1 (9) and 16:2.2 (8). The largest |angle| is 5.0°.
   - Hashes: every image and label hash equals the lineage.
2. **Visual box check: 36 images, 3 per class.**

   For each class I chose the strongest-rotation image, a fallback image where one exists, and a
   random one, and drew their label boxes myself. I zoomed in where boxes were small:
   `wp35_42_0129`, the bottom of `wp35_43_2p7_0107`, and the source frame `0360`.
   - Every target and non-target box covers its sign. Examples: the gantry signs 18/10/41/16:2.0
     beside the W.239b sign; 19/17/44 on the bridge rail; 2/3/41/50/13/51 at the junction.
   - No labelled sign appears half-visible at an image edge except in photometry-only fallbacks,
     where the cut already exists in the labelled source (for example the cls1 sign at the top of
     0464-family frames, and the 18 and 16:2.2 boxes in 0814).
3. **Realism.**
   - There is no mirroring or padding.
   - The hue shift is at most ±4 OpenCV units (about ±8°). Red and blue signs keep their meaning,
     and the sampled images show no colour inversion.
   - Haze, blur, noise and JPEG artefacts look plausible.
   - The preview shows each original next to three variants, with the target box outlined.
4. **Report wording.**

   The report states clearly that:
   - the images are training only and never used for validation, test, thresholds or accuracy;
   - every image shows the same physical sign, so no new sign instance is added;
   - the 10 source groups must be in the training split;
   - the 12 classes stay `EVAL_PENDING_REAL_INDEPENDENT_DATA` and must not trigger automatic
     simulated behaviour;
   - Gate 0 is still BLOCKED, and no split or training run was made.
5. **Verifier and tests.**
   - `uv run python scripts/build_wp35_rare_class_enrichment.py verify` returns `valid=true`
     with 1,800 images. It regenerates every image and label byte for byte and took about 20 s.
   - `uv run pytest -q -p no:cacheprovider tests/test_wp35_rare_class_enrichment.py` reports
     6 passed.
6. **Tampering attacks.**

   These ran on a staged copy that included a copy of the output directory. The baseline was
   `valid=true`. H1–H6 failed closed:
   - H1: append to the pinned D-04 record. Rejected because the pinned source changed.
   - H2: flip one byte of the decision CSV. Rejected because the pinned source changed.
   - H3: drop one box line from a label file. Rejected because the augmented file differs.
   - H4: flip one byte of an image. Rejected because the augmented file differs.
   - H5: add an extra label file. Rejected as an unexpected file.
   - H6: change a group in a lineage row. Rejected because the doc differs.

   H7 did not fail closed: deleting the whole output directory still gives `valid=true`
   (P3-1).

## Findings (all P3, non-blocking)

### P3-1: `verify` passes when the output directory is missing

`verify` checks the augmented files only `if out.is_dir()`. A fresh checkout, or a deleted
`data/processed/wp35_enrichment/`, therefore reports `valid=true` without checking any image.
Return a distinct `outputs_absent` status, or fail, so that "valid" never means the images were
checked when they were not. Deleting only one of the subfolders currently raises an uncaught
traceback, which is a non-zero exit but not a structured error.

### P3-2: "never cut a sign" covers only signs labelled in the source

The cut check covers every WP33 box. It cannot cover signs that are visible but were never
labelled in the source frame; WP34 QA showed that such signs exist in DATASET01. Excluded and
UNKNOWN boxes also stay unlabelled when they are inside the window, which matches the source.
Both behaviours are inherited, but the "Limits" section should state them.

### P3-3: the rotated boxes are slightly loose

Boxes are re-fitted as axis-aligned rectangles around the rotated corners. At 5°, a square box
grows by about 8–9% in each dimension. This is acceptable for small signs, but detector
box-precision metrics should never be computed on these images; they are training only anyway.

### P3-4: concentration and side effects to state

- Class 43:2.7 comes from 5 frames and 44 from 3 frames, with 30 photometry-only copies in
  43:2.7. Expect over-fitting to those exact views. The report already calls these classes weak.
- Augmented images keep every other train-eligible box in the window (up to 11 per image). WP35
  therefore also adds extra copies of common classes from the same 10 groups, for example 10, 23,
  18, 2 and 3. The class-balance effect should be considered when sampling.

## Governance

- D-04 part 1 is implemented as provisional train-only data. The other D-04 classes, G0.7, G0.9
  and D-05 remain pending, and Gate 0 remains BLOCKED.
- No split, training run, upload, push or publication was performed.
- This record modifies no WP35 file, output image, builder, test, owner record,
  `PROJECT_MEMORY.md` or roadmap file.
