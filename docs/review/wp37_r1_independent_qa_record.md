# M0-WP37-R1 independent QA record

Status: `QA_PASS_WP37_R1_G09_CARD_READY`
Reviewer: `Claude Code QA session (did not author WP37 or WP37-R1; authored the WP37 QA record)`
Reviewed at: `2026-10-18T12:00:00+07:00`
Boundary: `QA_OF_DATASET_CARD_ONLY_NOT_GATE0_APPROVAL_NO_TRAINING`

This append-only record reports independent QA of M0-WP37-R1, the revised DATASET01 card. It
modifies no builder, input, card, generated file, owner record, `PROJECT_MEMORY.md` or roadmap
file.

## Verdict

- **WP37-R1: PASS.** 0 P0, 0 P1, 0 P2, 0 P3.
- Every WP37 finding (P2-1 and P3-1 to P3-4) is fixed faithfully, and the card has no other
  content changes.
- The decode sizes and edge-per-resolution numbers re-derive exactly, and the package fails
  closed.
- **G0.9:** from the QA side, `docs/dataset01_card_r1.md` is sufficient for G0.9 PASS. Marking
  the gate PASS remains the owner's or PM's decision.

## Package bytes reviewed

- Builder `557b3e4aa3241613…`, test `cf8eac7576e1f7e5…`.
- R1 card `8e616bcb808f1e36…`, manifest `150c85afb74e6fc9…`, decode sizes `5bcba8a4c58e9e5e…`.
- The WP37 files are pinned and byte-identical to the bytes I reviewed in WP37: builder
  `e9dbeb40…`, test `ac129231…`, card `564d3cd6…` and manifest `f455b327…`. My WP37 QA record
  (`0bedaf5f…`) is also pinned. WP37 `verify` still returns `valid=true`.

## Checks performed

1. **Each fix, checked against the WP37 record.**
   - **P2-1.** The buckets are now "Bucket độ sáng trung bình (nội dung cảnh + phơi sáng), không
     phải điều kiện chiếu sáng".
     - The 7 DARK frames are described as daylight scenes shot against a tree canopy. This matches
       my inspection of 1848, 1850 and 1851.
     - The card states that no frame is verified as low-light or night, and night and heavy-rain
       performance stay UNKNOWN.
     - The split caution is now a shift in luminance and resolution distribution.
     - §8 and the §10 checklist row are updated to match.
     - No "ảnh tối", "camera hành trình", "cầm tay" or "đa số" text remains.
   - **P3-1.** The actual decode sizes are listed: 1920×1080 → 480×270 (813), 540×960 → 540×960
     (39) and 960×540 → 480×270 (2,364). A new edge table, split by resolution, states that
     comparisons are only valid within one resolution.
   - **P3-2.** The card now reads "≈37 % box (3.088/8.334) có diện tích < 0,1 % ảnh"; 3,088 of
     8,334 is 37.05 %.
   - **P3-3.**
     - The mandated attribution now equals the D-01 text: source@d869116, CC-BY-SA and the
       archive SHA-256.
     - "Data Palpating Team" is marked as unverified, from WP3.
     - The augmentation parent is UNKNOWN, and the WP32 near-duplicates are explicitly not
       augmentation evidence.
   - **P3-4.** The observation now reads "phần lớn… xe máy đông, một số là đường vắng/thoáng (ví
     dụ 0150, 0181, 0543)". It is labelled a reviewer observation, and the device type is
     UNKNOWN.
2. **Diff scope.** `diff docs/dataset01_card.md docs/dataset01_card_r1.md` shows only these
   changes:
   - the title, the status and the R1 introductory sentence;
   - the replacements listed in check 1;
   - the new edge-per-resolution table and decode-size reference;
   - the §9 verify command;
   - the §10 capture-conditions row.

   No number, class row, group row, split value or owner-decision text changed. The builder also
   asserts that each replaced passage occurs exactly once (`text.count(old) != 1` fails).
3. **Re-derivation (QA-only).**
   - I decoded all 3,216 frames with `draft("L", (480, 270))`. The decode size and edge strength
     match every row of `wp37_r1_decode_sizes.csv`, and its luma and bucket columns equal the WP37
     capture CSV.
   - The edge quartiles per resolution and split for usable frames match the card exactly:

     | Resolution | train | val | test |
     | --- | --- | --- | --- |
     | 1920×1080 | 671: 18.2 / 19.8 / 21.9 | — | 134: 16.5 / 18.6 / 25.5 |
     | 540×960 | — | 39: 18.2 / 19.9 / 21.4 | — |
     | 960×540 | 1241: 22.1 / 25.9 / 28.7 | 337: 22.4 / 30.2 / 33.8 | 769: 22.6 / 24.4 / 30.3 |
4. **Fail-closed behaviour.**
   - `uv run python scripts/build_wp37_r1_dataset_card.py verify --repo-root . --raw-root
     data/raw/DATASET01/staging/052bc980a7206f8d/raw` returns `valid=true` with 3 artifacts.
   - `uv run pytest -q -p no:cacheprovider tests/test_wp37_r1_dataset_card.py` reports 6 passed.
   - Tampering on a staged copy. The baseline and restored runs were both `valid=true`. All eight
     failed closed:
     - M1: append to my pinned WP37 QA record. Rejected because the pinned source changed.
     - M2: edit the WP37 card. Rejected because the pinned source changed.
     - M3: put "ảnh tối" back into the R1 card. Rejected because the artifact differs.
     - M4: edit a decode-size row. Rejected because the artifact differs.
     - M5: edit the WP37 capture CSV. Rejected because the pinned source changed.
     - M6: edit the R1 manifest. Rejected because the artifact differs.
     - M7: re-encode raw image 1320 at a smaller size. Rejected with "WP37 no longer reproduces".
     - M8: add a comment to the WP37 builder. Rejected because the pinned source changed.
5. **G0.9 sufficiency.**
   - The card now classifies every capture-condition claim correctly and states the license and
     attribution exactly as D-01 does.
   - It gives verified group lineage, taxonomy, D-04 status and the sealed split.
   - It lists every unknown explicitly: location, date, weather, device, night and rain
     performance, and the augmentation parent.
   - The §10 checklist covers all items that G0.9 was missing.

## Governance

- WP37-R1 changes no labels, groups or split.
- With G0.9 ready, D-05 (thresholds, latency and seed count, set on the val split) is the
  remaining open item before Gate 0. Training is not authorized by this record.
- No upload, push or publication was performed. This record modifies no WP37 or WP37-R1 file,
  input, owner record, `PROJECT_MEMORY.md` or roadmap file.
