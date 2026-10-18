# M0-WP37 independent QA record

Status: `QA_PASS_WP37_WITH_ONE_P2_CARD_WORDING_FIX_REQUIRED_BEFORE_G09_PASS`
Reviewer: `Claude Code QA session (did not author WP37)`
Reviewed at: `2026-10-18T11:00:00+07:00`
Boundary: `QA_OF_DATASET_CARD_ONLY_NOT_GATE0_APPROVAL_NO_TRAINING`

This append-only record reports independent QA of M0-WP37, the G0.9 dataset card for DATASET01.
It modifies no builder, input, card, generated file, owner record, `PROJECT_MEMORY.md` or roadmap
file.

## Verdict

- **WP37: PASS.** 0 P0, 0 P1, **1 P2**, 4 P3.
- **Numbers.** Every number I checked re-derives from the pinned inputs.
- **Determinism and pins.** The package fails closed and regenerates byte for byte.
- **Capture proxies.** Luma is measured correctly, and the reported split shift is real.
- **G0.9 should be marked PASS only after P2-1 is fixed in a card revision.** The card describes
  DARK/DIM as capture lighting conditions, for example "ảnh tối". The 7 DARK frames are daylight
  frames of a sign against dense foliage, not low-light captures.

## Package bytes reviewed

- Builder `e9dbeb40937c6467…`, test `ac129231569686dc…`.
- Card `564d3cd6e572fa81…`, manifest `f455b32750953a40…`.

## Checks performed

1. **Numbers (QA-only script; does not import the builder).**
   - **Images:** 3,216 images and 3,215 with a D-02 group. Usable frames are 3,191: train
     1,912, val 376 and test 903.
   - **Split hashes:** the WP36-R1 manifest gives train `6ac76750…`, val `ae3f3509…` and test
     `afa03d4b…`, the same values as the G0.7 acceptance record.
   - **Boxes:** 8,334 boxes, 8,290 of them train-eligible. The not-trained breakdown matches WP33:

     | Role | Boxes |
     | --- | --- |
     | UNKNOWN_EVAL_ONLY | 38 |
     | QUARANTINED | 2 |
     | EXCLUDED, very blurry | 2 |
     | EXCLUDED, cut off at the image edge | 1 |
     | EXCLUDED, the class-18 mislabel | 1 |
   - **Classes:**
     - The 22 classes without a sealed test and the 13 test-but-no-tuning classes equal the
       WP36-R1 coverage table.
     - All 56 class-card rows match the coverage table's train/val/test box counts.
   - **Groups:** all 54 group-lineage rows match the registry sizes, the WP36-R1 split of each
     group and the WP35 enriched-image counts.
   - **Metadata:** EXIF 0 and GPS 0.
   - **Small boxes:** there are 3,088 boxes with area below 0.1 % of the image, matching WP1.
     See P3-2 for the wording.
2. **D-01 wording, compared with `d01_owner_decision_record.md`.**
   - **Faithful:**
     - the source and commit, the CC-BY-SA attribution and the archive SHA-256;
     - the 3.0 / 4.0 conflict;
     - unknown image ownership;
     - risk accepted on 2026-10-17;
     - CC-BY-SA 4.0 share-alike for distributed derivatives;
     - no redistribution of the raw images or labels;
     - model weights possibly subject to share-alike;
     - re-opening D-01 if the author answers or a claim is received;
     - research, coursework and simulation use only.
   - **Deviations:** see P3-3.
3. **Capture proxies.**
   - I re-measured mean luminance on full-resolution RGB decodes (BT.601). The result differs from
     the package's draft-decode values by a median of 0.01 and at most 0.05, with 0 bucket
     disagreements. Pillow `12.3.0` is recorded in the manifest.
   - The split shift is real:

     | Split | 540×960 frames | 1920×1080 frames | DARK frames | Median luma |
     | --- | --- | --- | --- | --- |
     | train | 0 | 671 | 0 | 118.1 |
     | val | all 39 | 0 | all 7 | 106.3 |
     | test | 0 | 134 | 0 | 130.0 |

     The 7 DARK frames are 1843–1845 and 1848–1851.
   - **Draft decode size:** portrait frames are **not** decoded at 480×270. `draft()` leaves
     540×960 frames at full size (see P3-1).
   - **Visual check of the buckets.** I inspected DARK 1850, 1851 and 1848, the darkest DIM frame
     1847, DIM 3085 and 1052, BRIGHT 0181 and 0150, and the brightest frame 3186.
     - The DARK and darkest DIM frames are daylight shots looking up at a cls34 sign in front of
       a dense tree canopy. The low mean comes from the dark foliage filling the frame, not from
       low light (P2-1).
     - DIM and BRIGHT track exposure and scene content reasonably.
4. **Claim classification.**
   - Location, date, weather and device are UNKNOWN, and EXIF and GPS are both 0.
   - The traffic line is labelled "quan sát của reviewer… không phải metadata". That label is
     adequate, but the sentence overgeneralises and names a device type (P3-4).
   - Owner decisions are labelled OWNER DECISION, and measured values are labelled VERIFIED.
5. **Checklist §10.** It covers the three missing G0.9 items (capture conditions, license and
   group lineage) together with taxonomy, D-04 and the split. With the P2-1 wording fix it is
   sufficient for G0.9. Two rows would make it stronger: intended use / limits (§1, §8) and
   explicit UNKNOWNs (location, date, weather, device, night/rain performance).
6. **Fail-closed behaviour.**
   - `uv run python scripts/build_wp37_dataset_card.py verify --repo-root . --raw-root
     data/raw/DATASET01/staging/052bc980a7206f8d/raw` returns `valid=true` with 5 artifacts in
     about 2 s.
   - `uv run pytest -q -p no:cacheprovider tests/test_wp37_dataset_card.py` reports 8 passed.
   - WP36-R1 `verify` still returns `valid=true`.
   - Tampering on a staged copy, including a staged raw-image directory. The baseline and restored
     runs were both `valid=true`. All seven failed closed:
     - L1: append to the D-01 record. Rejected because the pinned source changed.
     - L2: edit the WP36-R1 coverage CSV. Rejected because the pinned source changed.
     - L3: change the license text in the card. Rejected because the artifact differs.
     - L4: change DARK to DIM in the capture CSV. Rejected because the artifact differs.
     - L5: change the Pillow version in the manifest. Rejected because the artifact differs.
     - L6: append to the G0.7 acceptance record. Rejected because the pinned source changed.
     - L7: brighten raw image 1843. Rejected because the capture, lineage and other artifacts
       differ.

## Findings

### P2-1: "DARK" is a scene-luminance bucket, not a lighting condition

§4 presents the luma buckets as capture conditions:

- "Ảnh DARK dùng được: 7…";
- "Val tối hơn train/test";
- "kết quả trên … ảnh tối chỉ có ở val".

All 7 DARK frames (1843–1851) are daytime frames framed against a dark tree canopy. The mean
luminance measures scene content and exposure, not illumination. A reader, or a later D-05
threshold study, could take them for low-light evidence.

Required card revision:

- Call the buckets "mean-luminance buckets (scene content + exposure)".
- State that the DARK frames are daylight foliage scenes and that the dataset has **no
  low-light or night frames that were verified as such**.
- Rephrase the val-vs-test caution as a luminance and resolution distribution shift.

### P3 findings

- **P3-1: draft size and edge proxy.**
  - The card says the measure uses "ảnh decode nháp 480×270 xám" for every frame. The 39 portrait
    540×960 frames are decoded at full size.
  - The edge proxy depends on resolution. Median edges are about 19–20 for 1920×1080 frames and
    24–30 for 960×540 frames, so the per-split edge quartiles partly reflect the resolution mix.
  - State the actual decode sizes, and report edge strength per resolution.
- **P3-2: "Box nhỏ chiếm đa số" is inaccurate.** 3,088 of 8,334 boxes is 37 %, not a majority.
  Write "≈37 % box có diện tích < 0,1 % ảnh".
- **P3-3: the D-01 attribution adds unverified details.**
  - "Ghi công bắt buộc" adds "(creator: Data Palpating Team)". That is an unverified creator
    claim from the upload description (WP3) and is not part of the D-01 attribution text. Keep it
    out of the mandated string, or mark it as an unverified claim.
  - The augmentation sentence should follow WP3: the augmentation parent of any image is UNKNOWN.
    The WP32 near-duplicate pairs are frames from interleaved rides, not evidence of
    augmentation.
  - The card's unconditional "không phân phối lại ảnh/nhãn gốc" is stricter than D-01's "until
    ownership is clarified", which is acceptable.
- **P3-4: the reviewer observation overgeneralises.**
  - "Ảnh là camera hành trình/cầm tay trên đường đô thị có xe máy dày đặc" names a device type
    and claims every frame. Several frames show quiet or open roads, for example 0150, 0181 and
    0543.
  - Suggested wording: "phần lớn ảnh là đường có xe máy đông (quan sát của reviewer); loại thiết
    bị UNKNOWN".

## Governance

- WP37 documents DATASET01; it changes no labels, groups or split.
- G0.9 can move to PASS after a card revision that fixes P2-1. The P3 findings are recommended
  in the same revision.
- D-05 remains open, Gate 0 remains BLOCKED, and training is not authorized.
- No upload, push or publication was performed. This record modifies no WP37 file, input, owner
  record, `PROJECT_MEMORY.md` or roadmap file.
