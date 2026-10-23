# D1-VRL-R2 derived validation labels (hand-drawn successor) — independent QA record

Date: 2026-10-23 (`Asia/Ho_Chi_Minh`)
Status: `INDEPENDENT_QA_PASS_WITH_FINDINGS__ONE_HAND_BOX_OUT_OF_TOLERANCE`
Reviewer: `Claude Code fresh independent QA session (did not author D1-VRL-R1 or D1-VRL-R2)`
Boundary: `READ_ONLY_NO_INFERENCE_NO_TRAINING_NO_BUILD_NO_SEALED_TEST`

## Verdict

**PASS — 0 Critical, 0 High, 1 Medium and 4 Low findings.**

The H1 correction is truthful and the owner rule is implemented exactly:
- every proposal with a locator ≤ 17.5 px on its longer side is an ignore region (40);
- every other proposal is added ground truth (64 = 38 hand-drawn + 23 re-fitted + 3 re-fitted and
  tightened);
- the builder refuses either decision on the wrong side of 17.5 px, and that rule fails closed when
  attacked with a re-pinned module.

All pins match. `verify` returns `valid=true`. The 10 R1 + R2 tests pass. The derived labels are R4
plus exactly the 64 lines. My own matcher reproduces 214 → 150 → 110 FP exactly. The report keeps
the independent part (150 FP, 0.399/image) apart from the circular ignore part (40 FP) and calls
the table a diagnostic.

I re-drew 21 of the 38 hand boxes from the raw frames and screened 12 more with a rim circle fit:
- 29 of the 33 agree with my re-draw within 1.5 px on every side;
- **R039** is 6.5 px loose on the left side (M1);
- **R046** is about 5 px short at the bottom, where the rim meets a bracket (L1);
- **R090/R091** are about 3 px short at the bottom, at the edge of their 3 px tolerance (L2).

None of these changes the diagnostic: my corrected R039 and R046 boxes still match their
predictions at IoU 0.815 and 0.879.

The hand boxes look independent of the model box:
- none equals its locator;
- they sit inside the locator on average;
- for my 21 re-draws they are closer to my geometry than the locator in 17 cases.

M1 is a real geometry defect in ground truth that the author says was checked by eye. It does not
affect IoU-0.5 matching, so it does not reach High. It must be resolved before the labels become the
evaluation authority (see the bounded next state).

This PASS authorizes nothing by itself. It does not make the derived labels the evaluation
authority. It does not authorize a gate change, R10 replacement, threshold change, training, smoke
run, sealed-test access, commit or push. I opened no test material and ran no model.

## Exact reviewed inputs and pins

| Input | SHA-256 | Result |
| --- | --- | --- |
| `detector/m1/val_relabel_r2.py` | `2d70762550dd6e7752e122b31c3628256a8eafebf3ca14f7be6facfc5ca12710` | matches implementation record; **this QA record pins it** |
| `detector/tests/test_val_relabel_r2.py` | `a6cc320adc24e9d15a0f408352608ad85c1ad8919c38528aa3ba9ecd790a1baa` | matches |
| `docs/review/d1_vrl_r2_box_review_notes.csv` | `a9c05fa8ad578de0eaa819e123e5a89c055576d2c28853cf529708d5407eda2e` | matches module `PINNED` and record |
| `docs/review/d1_vrl_r1_correction_r1.md` | `d3376ec32b13ea33ec94a43b124d6738d541ab2c1b35a465fa07361ce4b318d0` | matches |
| `docs/review/d1_vrl_r1_independent_qa_record.md` | `e168b6bf2cb5b3322ff3f3ffb7701bf65433952610baeafe42aeca1e435fab0c` | matches |
| `detector/m1/val_relabel_r1.py` | `9fba10089ad23fc494b2548fec60acf4d07ae34feebcc8bfb530887b0ff5eff5` | matches |
| `docs/review/generated/d1_vrl_r1_manifest.json` | `3fd91263dabc775bf8967e604a589bb20143bfc43fb45f2e16fa814e973eb34f` | matches |
| `docs/review/generated/m1_yolo_wp38_r1_integration_r4_manifest.json` | `6982a76f06f7486dd5d14015b7858ea74088f6ab3fcad6d54c576772b3c7e602` | matches |
| the other 9 inherited D1-VRL-R1 pins (`val_label_audit_r1.py` `3826fa57…`, VLA-R1 proposals `70773b4b…` and manifest `3fbbe7fd…`, VLA-R1 QA `5e856b77…` and correction `be06ee89…`, VRL-R1 notes `4458474f…` and scope `a96e55f4…`, `d1_ea_r1_predictions.csv` `cb3cb05f…`, `m1_yolo_classes.csv` `7cda296a…`) | as listed in the manifest `pinned_sources` | all match (checked by `verify_pins`, which `verify` passes) |
| R4 val labels, `labels_sha256` (own formula: sorted `stem\n<content>`) | `e64345bb3a618187d10828ccc135172736ff45956570359da4fa99d441f320cc` | recomputed: **unchanged**; equals the R4 manifest value |
| `docs/review/generated/d1_vrl_r2_added_boxes.csv` (64 rows) | `f8d364bdab9b578c297029076b851808ad9986d0ae95def3e87664b4e5922688` | matches |
| `docs/review/generated/d1_vrl_r2_ignore_regions.csv` (40 rows) | `ec102253b3b049186a966254b2ad54fe6cdefb7251e486632f30b82cf4c2bf4e` | matches |
| `docs/review/generated/d1_vrl_r2_manifest.json` | `e23b725f711ae6f9a15f8db4d00e13ec8048a392f8db10296972113573c008ff` | matches; **this QA record pins it** |
| `docs/review/d1_vrl_r2_report.md` | `73016ba46525069e1d43b15d0e148d476ce91c0d592106a0658aad180fe1b346` | equals the manifest; byte-compared by `verify` |
| `docs/review/d1_vrl_r2_implementation_record.md` | `03276743c516bd76a474b60a509fcc91f996ff1d4bb88fd29faaad5a38550bd4` | read |
| `docs/review/d1_vrl_r2_qa_brief.md` | `db1219617c8f9d7e1de5ad4c2ff695092233ef2fd71210615797bf4a2f7405ff` | followed |
| derived label roster (manifest field) | `f772bae26ac93ac0fa594177cf00afb65dd1ceb6f5fd31793808f04bf39b9373` | matches record |
| atlas `added_page_01…04.jpg` | `1a98f8bd…`, `048e1d7c…`, `37744e0f…`, `e9ed8245…` | equal the manifest |
| `ignore_regions.json` | `4aaee942…` | equals the manifest |

The manifest lists 384 artifacts: 2 CSVs, the report, `ignore_regions.json`, 376 label files and
4 atlas pages. `verify` byte-compares each against a fresh render.

## Check 1 — pins and the owner rule

- All pins above match.
- `qa_core.py` imports no repository code. It recomputes every locator from the VLA-R1 proposal
  CSV and the raw image size:

  | Rule | Result |
  | --- | --- |
  | locator ≤ 17.5 px ⇒ `IGNORE_REGION`, in the ignore CSV, not added | 40 / 40 |
  | locator > 17.5 px ⇒ added, not ignored | 64 / 64 |
  | ignore geometry = locator + 25 % per side, clipped | 40 / 40 within 0.006 px |
  | ignore reason states the measured size (`locator WxH px`) | 40 / 40 |
  | added `yolo_id` = class-map of the proposal key | 64 / 64 |
  | notes R001–R104 in order, stem and key equal the proposal | 104 / 104 |

- Nearest the boundary: R008 16.90, R022 16.92, R017 17.03, R014 17.07, R013 17.09 (ignored);
  R018 17.78, R004 17.98, R023 18.00 (hand-drawn). No item sits on the boundary.
- **The correction record states the H1 premise truthfully.** From my locators and the R1 notes,
  the 72 split 40 / 20 / 7 / 5 over ≤ 17.5 / 17.5–25 / 25–40 / > 40 px, and the 6 partial re-fits
  split 0 / 0 / 5 / 1. This matches the correction's table exactly. The correction names the frames
  outside the poles (1236, 1242–1245) and the legible large signs. It withdraws the "small
  low-saturation" description and accepts the predecessor QA's measurement. The owner instruction
  is quoted in Vietnamese with a translation. R2 hand-draws every item > 17.5 px, which is more
  than the minimum of "at least 12 items ≥ 25 px".

## Check 2 — hand-drawn geometry (38)

Method:
- I read all 4 atlas pages.
- From the raw frames, I rendered my own nearest-neighbour crops with a pixel grid and **no box
  drawn** (`qa_crop.py`). Frames 1823/1824 were brightened 3.5×.
- I placed each edge by eye. I then refined it with sub-pixel 50 % luminance crossings on the outer
  rim (`qa_edge.py`, `qa_prof.py`). For discs I also used a least-squares circle fit to the rim
  crossings of the middle rows (`qa_circle.py`), which gives the top and bottom of a disc whose pole
  or bracket hides them. For the dark 1823/1824 discs I used R−G / B−G chroma profiles
  (`qa_red.py`).
- The seeds were my own visual centres. No package box or locator was used to place an edge.

**Independent re-draws (21, including all items the brief names):**

| ID | Frame | Key | QA re-draw (x1, y1, x2, y2) | Package box | Max side diff | Worst side |
| --- | ---: | ---: | --- | --- | ---: | --- |
| R004 | 1208 | 41 | 210.5, 94.5, 227.5, 112.0 | 211, 95, 228, 112 | 0.5 | L |
| R012 | 1210 | 39 | 180.0, 106.0, 197.5, 123.0 | 179, 107, 197, 123 | 1.0 | L |
| R018 | 1212 | 10 | 163.2, 170.4, 178.1, 185.3 | 164, 171, 178, 185 | 0.8 | L |
| R023 | 1213 | 10 | 150.1, 169.1, 165.4, 184.4 | 150, 169, 165, 185 | 0.6 | B |
| R025 | 1214 | 10 | 132.8, 175.0, 148.3, 190.4 | 133, 175, 148, 190 | 0.4 | B |
| R028 | 1215 | 10 | 87.2, 182.5, 103.2, 198.5 | 87, 183, 103, 198 | 0.5 | T |
| R030 | 1216 | 10 | 56.8, 178.2, 73.5, 194.9 | 57, 179, 73, 194 | 0.9 | B |
| R033 | 1217 | 39 | 19.3, 137.7, 40.9, 158.0 | 18, 138, 41, 159 | 1.3 | L |
| R038 | 1223 | 23 | 26.7, 130.2, 49.6, 153.2 | 27, 131, 49, 152 | 1.2 | B |
| **R039** | 1223 | 39 | **6.5**, 43.5, 36.2, 71.0 | **0**, 44, 36, 70 | **6.5** | **L** |
| R041 | 1224 | 23 | 81.4, 97.4, 104.9, 120.9 | 82, 98, 105, 120 | 0.9 | B |
| R043 | 1225 | 23 | 125.0, 99.3, 149.0, 123.4 | 125, 100, 149, 123 | 0.7 | T |
| R045 | 1228 | 41 | 83.6, 0.0, 119.0, 30.3 | 84, 0, 119, 30 | 0.4 | L |
| **R046** | 1229 | 39 | 116.4, 0.0, 153.1, **28.0** | 117, 0, 153, **23** | **5.0** | **B** |
| R047 | 1236 | 10 | 25.5, 0.0, 68.0, 36.0 | 26, 0, 68, 37 | 1.0 | B |
| R048 | 1242 | 23 | 0.0, 77.0, 58.9, 138.3 | 0, 77, 58, 138 | 0.9 | R |
| R050 | 1243 | 23 | 0.0, 63.7, 65.0, 130.3 | 0, 63, 65, 131 | 0.7 | T |
| R051 | 1244 | 23 | 0.0, 32.6, 80.2, 111.0 | 0, 32, 80, 110 | 1.0 | B |
| R052 | 1245 | 23 | 0.0, 0.0, 60.9, 80.2 | 0, 0, 60, 80 | 0.9 | R |
| R090 | 1823 | 10 | 331.0, 437.5, 363.0, 472.0 | 332, 439, 362, 469 | 3.0 | B |
| R091 | 1824 | 10 | 321.5, 445.0, 357.0, 481.0 | 323, 445, 355, 478 | 3.0 | B |

**Findings from the re-draws:**

- **R039 (M1).** The "60" disc's outer rim starts at x ≈ 6.5. Rows 52, 57 and 62 cross 50 % at x ≈ 6.9,
  6.1 and 7.0. Columns 0–1 belong to a different object at the frame edge (luminance about
  147, against a background of about 240). The package box starts at x = 0, and so does the eye
  estimate. The box is therefore 6.5 px loose on the left of a 30 px disc, IoU 0.78 with my
  re-draw. The R2 atlas tile shows the gap. The locator (x1 = 5.0) was closer.
- **R046 (L1).** The "60" disc's interior ends at y ≈ 22. Its lower rim (y 23–27) coincides with a
  dark horizontal bracket, which also runs left of the disc (x 108–117). The column profile at
  x = 125 / 135 / 145 stays dark to y = 25 / 27 / 27. The circle fit to the side rims (r = 18.3,
  centre y = 10.0, residual 0.04 px) predicts a bottom at 28.3. The package box stops at 23. The
  same sign series on the previous frame (R045, "40") was drawn through the bracket to 30, which my
  profile confirms. I read R046 as about 5 px short. Because the bracket overlaps the rim, the
  correct bottom is somewhat ambiguous.
- **R090/R091 (L2).** The red-ring chroma (R−G) along the disc centre column stays ≥ +8 to y ≈ 471
  (1823) and ≈ 481 (1824). The package bottoms are 469 and 478. Left, top and right are within
  1.5–2 px. That is at the 3 px tolerance the brief allows for these two, with about ±1–2 px
  measurement uncertainty on a dark, cluttered frame. The locator (480.0) was closer on R091.

**Circle-fit screen of 12 more** (rim crossings, residual ≤ 0.14 px, seed = locator centre; this
screen uses the locator only as a seed):
- R026, R027, R029, R031, R032, R034, R035, R040, R042 and R044 agree with the package box within
  1.0 px on every side.
- R036's left side is clipped at the frame edge. Its bottom rim is at y ≈ 166.5 by column profile,
  against 165 (1.5 px).
- R049's left side reaches x = 0 (rows 20 and 30 dark at column 0). The box agrees.

Not individually re-measured: R007, R010, R016, R019 and R020. These are the "40"/"60" discs on
1209–1212, where the digits defeat the rim fit. In the atlas, at about 8× zoom, they look snug.

**Classes.** The atlas and my crops agree with the unchanged D1-VLA-R1 keys:
- key 10 = P.130 (blue disc with red rim or X): R018…R049, R090, R091;
- key 23 = P.111a+b (crossed motorbike / three-wheeler, with the "CẤM XE 02 VÀ 03 BÁNH" plate on
  1242–1245);
- key 39 = 60 km/h: R039, R046, R033 and R036 read "60";
- key 41 = 40 km/h: R045 reads "40".

The 1208–1212 "40"/"60" pairs (R004/R007/R010/R019 vs R012/R016/R020) are too blurred for me to
read the digits independently. Their keys come from D1-VLA-R1, which passed its own QA, and they are
consistent with the frame sequence. Every added row's `yolo_id` equals the class map of its
proposal key.

## Check 3 — independence of the hand boxes

| Measure | Result |
| --- | --- |
| hand box equal to its rounded locator | 0 / 38 |
| final = eye estimate on all 4 sides | 9 / 38 (including R090/R091, not snapped, as stated) |
| max \|final − eye\| on any side | 1 px for the other 29: the snap stayed within the stated 1 px |
| eye − locator, signed mean per side (x1, y1, x2, y2) | +0.78, +0.60, −1.33, −0.69 px: the eye boxes sit **inside** the model box |
| \|eye − locator\| per side | mean 1.08 px, 52 % ≤ 1 px, max 5.0 px |
| IoU(hand, locator) | min 0.644, median 0.811, max 0.964 (record: 0.64 / 0.81 / 0.96) |
| closer to the QA re-draw than the locator (max side diff), over 21 re-draws | 17 / 21. The exceptions are R039, R046, R090 and R091 (the M1/L1/L2 boxes). |

Judgement:
- **The procedure kept the boxes independent.** A copied model box would equal or track the
  locator. Instead, the hand boxes are systematically tighter and mostly closer to the rim the
  pixels show.
- The two largest eye-versus-locator departures (R039 left −5.0, R046 bottom −3.5) moved **away**
  from my geometry. This is also evidence of independence, though it was wrong both times.
- The crops were centred on the locator, so the centre was not blind. That leaks position, not edge
  placement, and is disclosed in the record.
- The builder does not check the eye columns. It does not require them to be filled for
  `HAND_DRAWN`, or `|final − eye| ≤ 1`. The procedure is protected only by the notes pin (L3).

## Check 4 — L1 (tightened boxes and R092)

R−G chroma profiles on the raw frames:

| ID | Change | QA profile | Judgement |
| --- | --- | --- | --- |
| R095 (1828) | right 348 → 345 | row 460: R−G +9 at 344–345, +5 at 348; edge ≈ 346 | within 1 px; the tightening is right |
| R097 (1830) | right 335 → 331 | row 434: +8 to 331, +6 at 332–334, +5 at 335; rows 440/446 near 0 beyond 327 | faint tail; 331 is defensible (≤ 2 px) |
| R103 (1836) | bottom 489 → 485 | column 370: peak +44 at 480, half-max ≈ 483, +4 at 485 | within 1–2 px; the tightening is right |
| R092 (1825) | kept at 360 | rows 470/475: peak +9 at 356–358, +5 at 360, +3 at 361 | half-max ≈ 360; **the author's evidence holds**, and keeping 360 is justified |

All three adjustments are tighter than the re-fit, by at most 6 px. Attack 2b shows that the builder
refuses a loosening. I accept the R092 disagreement with predecessor L1 on the stated profile.

## Check 5 — L2, L3 and L4

- **L2.** The report states: "Geometry is guaranteed by the visual check, not by the colour fit …
  A re-evaluation must keep the IoU-0.5 matching rule." The implementation record says the same.
  **Confirmed.** M1/L1 show that the visual check is not perfect, but both defects stay far inside
  IoU 0.5.
- **L3.** `stray_paths` walks the whole `data/processed/m1_yolo_val_vrl_r2/` tree and the atlas
  directory. It flags symlinks, unexpected files and directories that hold no artifact. Attacks 3,
  3b, 3c, 3d, 3e and 9 fail closed. **Fixed.**
- **L4.**
  - `R4_VAL_LABELS_SHA256 = e64345bb…` is enforced in `verify_pins` (attacks 4 and 4b).
  - `test_official_package_verifies_counts_and_maps_ids` asserts set equality `{(23, 25), (39, 40),
    (41, 42)}` over real added rows. The data has 12 rows of key 23, 7 of key 39 and 5 of key 41, so
    the test is no longer vacuous.
  - **Fixed.**

## Check 6 — derived labels and diagnostic

`qa_labels_diag.py` imports no repository code. It checks the derived labels:
- `labels/val/` holds exactly 376 regular `.txt` files, with the same stems as R4 and no symlinks.
- Every file equals its R4 text followed by exactly that stem's added lines, rendered from the added
  CSV.
- 64 lines are added across 43 files: 560 → 624 lines.
- The R4 val `labels_sha256` is unchanged (`e64345bb…`). The R4 export has no test directory.

For the diagnostic I used my own greedy class-agnostic matcher:
- predictions with conf ≥ 0.20, in descending confidence, ties broken by `pred_rank`;
- each matches the best unmatched GT at IoU ≥ 0.5;
- an unmatched prediction is ignored if ≥ 50 % of its area lies inside an ignore region of its
  frame.

| Labels | GT | TP | FP | Ignored | FP/image | Agnostic recall | Precision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R10 (R4) | 560 | 483 | 214 | — | 0.569149 | 0.862500 | 0.692970 |
| + 26 re-fits only (R1 equivalent) | 586 | 509 | 188 | — | 0.500000 | 0.868601 | 0.730273 |
| **+ 64 added (independent)** | 624 | 547 | **150** | — | **0.398936** | 0.876603 | 0.784792 |
| + 64 + 40 ignore (circular) | 624 | 547 | 110 | 40 | 0.292553 | 0.876603 | 0.832572 |

These equal the manifest `summary` exactly. Every one of the 64 added boxes is matched (TP +64).

Points on the diagnostic:
- The hand-drawn boxes move 38 FP from the circular to the independent side: 188 → 150, compared
  with D1-VRL-R1.
- Containment thresholds 0.3 and 0.9 give the same 40 ignored, so each region exempts exactly its
  source prediction. That is the circularity the report states.
- With my corrected R039 and R046 boxes, both predictions still match (IoU 0.815, 0.879). The
  150 / 110 figures do not change.

The report:
- shows "FP before ignore 150" and "FP in ignore regions 40" as separate columns;
- labels 150 FP as "Independent of the model geometry";
- labels the further 40 as "Circular by construction … no evidence that the model is right";
- states "This is a diagnostic, not an evaluation … changes no gate".

**Confirmed.** 0.399 FP/image is still above the 0.30 gate, and the record says so.

## Check 7 — verifier, tests and tampering

Verifier and tests:
- `uv run python -m m1.val_relabel_r2 verify` (from `detector/`) returns `valid=true`, `errors=[]`
  (about 1.5 s).
- `pytest -p no:cacheprovider tests/test_val_relabel_r2.py tests/test_val_relabel_r1.py` passes 10
  tests.
- `ruff check` and `ruff format --check` are clean on both R2 files.
- Full `detector` suite: 225 passed, exit 0. `uv lock --check` is OK.

Tampering attacks:
- They ran on APFS clones of `docs/`, `data/` and `detector/m1/` under the reviewer scratchpad
  (`qa_tamper.py`).
- Each attack calls `verify(repo_root=<stage>)` of the unmodified repository module. The attacks
  marked "re-pinned" instead use a staged copy of the module whose notes pin was set to the tampered
  notes, so that they test the rule itself rather than the pin.
- `build` was never run. Attack 99 rendered forged artifacts into its own stage only.

| # | Attack | Result |
| ---: | --- | --- |
| 0 | clean staged copy | valid=true |
| 1 | notes R008 (17.0 px) IGNORE_REGION -> HAND_DRAWN with a box (notes pin unchanged) | **FAIL closed** (pinned D1-VRL-R2 source differs: docs/review/d1_vrl_r2_box_review_notes.csv) |
| 1b | same flip with the staged module re-pinned to the tampered notes (size rule itself) | **FAIL closed** (R008: hand-drawn boxes are only for locators > 17.5 px) |
| 1c | R018 (17.8 px) HAND_DRAWN -> IGNORE_REGION, staged module re-pinned | **FAIL closed** (R018: ignore regions are only for locators <= 17.5 px) |
| 2 | R095 adjusted box loosened 345 -> 349 (notes pin unchanged) | **FAIL closed** (pinned D1-VRL-R2 source differs: docs/review/d1_vrl_r2_box_review_notes.csv) |
| 2b | R095 loosened, staged module re-pinned (tighten-only rule itself) | **FAIL closed** (R095: adjustment may only tighten the re-fit by <= 6 px) |
| 3 | stray labels/train/0001.txt under the derived root | **FAIL closed** (unexpected path: data/processed/m1_yolo_val_vrl_r2/labels/train; unexpected path: data/processed/m1_yolo_val_vrl_r2/labels/train/0001.txt) |
| 3b | empty directory data/processed/m1_yolo_val_vrl_r2/extra/ | **FAIL closed** (unexpected path: data/processed/m1_yolo_val_vrl_r2/extra) |
| 3c | stray data/processed/m1_yolo_val_vrl_r2/extra.json | **FAIL closed** (unexpected path: data/processed/m1_yolo_val_vrl_r2/extra.json) |
| 3d | hidden labels/val/.DS_Store | **FAIL closed** (unexpected path: data/processed/m1_yolo_val_vrl_r2/labels/val/.DS_Store) |
| 3e | stray atlas added_page_05.jpg | **FAIL closed** (unexpected path: docs/review/assets/d1_vrl_r2/added_page_05.jpg) |
| 4 | R4 val label 1208.txt replaced (one class/box line) | **FAIL closed** (WP38-R1 R4 validation labels differ from labels_sha256 e64345bb…) |
| 4b | same class change in R4 0001.txt and derived 0001.txt | **FAIL closed** (WP38-R1 R4 validation labels differ from labels_sha256 e64345bb…) |
| 5 | one byte flipped in added_page_03.jpg | **FAIL closed** (artifact differs: docs/review/assets/d1_vrl_r2/added_page_03.jpg) |
| 6 | manifest evaluation_authority -> true | **FAIL closed** (artifact differs: docs/review/generated/d1_vrl_r2_manifest.json) |
| 6b | manifest gates_changed -> true | **FAIL closed** (artifact differs: docs/review/generated/d1_vrl_r2_manifest.json) |
| 6c | manifest sealed_test_accessed -> true | **FAIL closed** (artifact differs: docs/review/generated/d1_vrl_r2_manifest.json) |
| 7 | added_boxes.csv R039 x1 0 -> 6 | **FAIL closed** (artifact differs: docs/review/generated/d1_vrl_r2_added_boxes.csv) |
| 8 | derived 1223.txt last line deleted | **FAIL closed** (artifact differs: data/processed/m1_yolo_val_vrl_r2/labels/val/1223.txt) |
| 9 | derived 1208.txt replaced by a symlink to identical bytes | **FAIL closed** (artifact differs: data/processed/m1_yolo_val_vrl_r2/labels/val/1208.txt; unexpected path: data/processed/m1_yolo_val_vrl_r2/labels/val/1208.txt) |
| 10 | report FP/image 0.399 -> 0.299 | **FAIL closed** (artifact differs: docs/review/d1_vrl_r2_report.md) |
| 11 | ignore_regions.json margin 0.25 -> 0.3 | **FAIL closed** (artifact differs: data/processed/m1_yolo_val_vrl_r2/ignore_regions.json) |
| 12 | correction record (pinned) one word changed | **FAIL closed** (pinned D1-VRL-R2 source differs: docs/review/d1_vrl_r1_correction_r1.md) |
| 99 | coordinated forgery (notes R039 x1 0->6, module re-pinned, re-rendered; manifest 257c3480) under FORGED module | `valid=true` under the forged module (L4) |
| 99b | same forged stage under the REPOSITORY module | **FAIL closed** (pinned D1-VRL-R2 source differs: docs/review/d1_vrl_r2_box_review_notes.csv) |

All six attacks the brief requires fail closed: the note flip across 17.5 px (1, and 1b/1c at
rule level), the loosened adjustment (2, 2b), the stray `labels/train/` file (3), the edited R4
label (4, 4b), the atlas byte flip (5) and the manifest boundary flags (6, 6b, 6c). Forgery 99 is
detected only by the module pin; this record pins module `2d707625…` and manifest `e23b725f…`.

## Check 8 — boundary

The manifest records:
- `evaluation_authority=false`
- `gates_changed=false`
- `sealed_test_accessed=false`
- `training_authorized=false`
- `test_included=false`
- `train_or_test_labels_changed=false`
- `supersedes=D1-VRL-R1`
- `pillow_version=13.0.0`

Status `D1_VRL_R2_AWAITING_INDEPENDENT_QA`. The report says that the labels are "not yet the
evaluation authority". `graft grep` finds no consumer of `m1_yolo_val_vrl_r2` or `val_relabel_r2`
other than the builder and its test. Both output trees are git-ignored. **Confirmed.**

## Findings

| ID | Severity | Finding | Evidence | Required action |
| --- | --- | --- | --- | --- |
| M1 | **Medium** | Hand box R039 (1223, "60" disc) is 6.5 px loose on the left side: x1 = 0 where the disc starts at x ≈ 6.5. It includes a sliver of an adjacent object at the frame edge. The eye estimate made the same error, and the record's "checked by eye" did not catch it. | Rows 52/57/62 cross 50 % at x ≈ 6.9/6.1/7.0; columns 0–1 ≈ 147 luminance against a background of about 240. The atlas tile shows the gap. IoU 0.78 with the QA re-draw (6.5, 43.5, 36.2, 71.0). The prediction still matches (0.815), so the diagnostic is unchanged. | Before the labels become the evaluation authority, either correct R039 (x1 ≈ 6–7) in an append-only successor or correction, or have the owner acceptance record explicitly accept it with this evidence. |
| L1 | Low | Hand box R046 (1229) bottom at 23, while the disc rim reaches about 28. The rim coincides with a dark bracket, so the box stops at the interior. This is inconsistent with R045 on 1228, drawn through the bracket to 30. | Column profiles at x = 125/135/145 are dark to 25/27/27. Side-rim circle fit: r 18.3, centre y 10.0, residual 0.04, bottom 28.3. IoU 0.81. | Correct alongside M1 (y2 ≈ 27–28), or record the convention chosen for rims behind brackets. |
| L2 | Low | R090/R091 bottoms are about 3 px short of the red-ring profile, at the 3 px tolerance. | R−G ≥ +8 to y ≈ 471 (1823) and ≈ 481 (1824), against 469 / 478. | Optional; the ±2 px limit in the report is slightly optimistic for the bottom edges. |
| L3 | Low | The independence procedure is not machine-checked. The builder does not require eye columns for `HAND_DRAWN`, or `\|final − eye\| ≤ 1` on snapped frames; only the notes pin protects them. | `check_box_decision` reads only `x1…y2` | In a successor, assert eye columns present and `max \|final − eye\| ≤ 1` (0 for 1823/1824) |
| L4 | Low | Carry-over of D1-VRL-R1 L5: a coordinated rewrite of notes, module pin and artifacts verifies under the forged module | Attack 99 | Treat module `2d707625…` and manifest `e23b725f…` (pinned here) as the anchor |

What this QA does **not** dispute:
- the 40 / 64 split and the 17.5 px rule;
- the truthfulness of the H1 correction;
- the 23 re-fits;
- the three L1 tightenings and the retention of R092;
- the classes;
- the diagnostic arithmetic and its independent/circular split;
- the L2/L3/L4 fixes;
- the boundary flags.

## Commands run

```text
shasum -a 256 <module, test, notes, correction, R1 QA, R1 module/manifest, R4 manifest, 3 outputs, report, records, brief, atlas, ignore json>
graft check . ; graft grep "def val_images" / "m1_yolo_val_vrl_r2" / "val_relabel_r2"
cd detector && uv run python -m m1.val_relabel_r2 verify                                     # valid=true
cd detector && uv run pytest -q -p no:cacheprovider tests/test_val_relabel_r2.py tests/test_val_relabel_r1.py   # 10 passed
cd detector && uv run ruff check / ruff format --check <2 R2 files>                          # clean
cd detector && uv run pytest -q -p no:cacheprovider    (background)                          # 225 passed (225 dots, no F/E), exit 0; uv lock --check OK
uv run python -I <scratchpad>/qa/qa_core.py <repo> <scratchpad>/qa        # owner rule, ignore geometry, eye/final/locator stats
uv run python -I <scratchpad>/qa/qa_crop.py <repo> <scratchpad>/qa plain <ids>   # box-free tick-grid crops
uv run python -I <scratchpad>/qa/qa_edge.py | qa_prof.py | qa_circle.py | qa_red.py <repo> <stem> ...   # edge evidence
uv run python -I <scratchpad>/qa/qa_cmp.py <repo> <scratchpad>/qa          # re-draw vs package vs locator
uv run python -I <scratchpad>/qa/qa_labels_diag.py <repo>                  # R4 + 64; 214 -> 150 -> 110
detector/.venv/bin/python -I <scratchpad>/qa/qa_tamper.py <scratchpad> <repo>/detector     # staged attacks
```

All scripts were run with the working directory `detector/` and wrote only to the scratchpad.
`git status --short` before and after shows the same 23 untracked entries, plus this file. No model
was loaded. No inference, `build`, training, relabel, upload, commit, push or sealed-test access
occurred. The only repository change is this new file.

## Bounded next state

| Action | QA disposition |
| --- | --- |
| Owner acceptance record for D1-VRL-R2 (manifest `e23b725f…`) as derived validation labels | **YES, eligible**, provided it resolves M1 (correct R039, and preferably R046, in an append-only successor/correction with its own QA, **or** explicitly accept the deviation with this evidence) |
| Make the derived labels the evaluation authority | **NO** — only after the owner acceptance and a QA-passed re-evaluation contract |
| Re-evaluation contract on the derived labels (IoU-0.5 matching kept, ignore regions reported separately as circular) | **YES**, after the owner acceptance |
| Cite 150 FP / 0.399 FP/image as the independent diagnostic | **YES, as a diagnostic only** — not a gate result; it is still above the 0.30 gate |
| Cite 110 FP / 0.293 FP/image as a gate result | **NO-GO** — circular ignore part |
| Change any gate, NMS or confidence; replace R10 | **NO-GO** |
| Use validation pixels, labels or predictions for training or mining | **NO-GO** |
| Smoke, pilot, new seeds or any training from this record | **NO-GO** |
| Open or export the sealed test | **NO-GO** |
