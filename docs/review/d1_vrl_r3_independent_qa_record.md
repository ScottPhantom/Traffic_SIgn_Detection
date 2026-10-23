# D1-VRL-R3 derived validation labels (successor of D1-VRL-R2) — independent QA record

Date: 2026-10-23 (`Asia/Ho_Chi_Minh`)
Status: `INDEPENDENT_QA_PASS_WITH_LOW_FINDINGS`
Reviewer: `Claude Code fresh independent QA session (did not author D1-VRL-R1, R2 or R3)`
Boundary: `READ_ONLY_NO_INFERENCE_NO_TRAINING_NO_BUILD_NO_SEALED_TEST`

## Verdict

**PASS — 0 Critical, 0 High, 0 Medium and 4 Low findings.**

D1-VRL-R3 does exactly what the owner decision ordered:
- **R039 x1 0 → 6.** My row profiles put the left rim at x ≈ 6.0–6.4.
- **R046 y2 23 → 28.** My column profiles and side-rim geometry put the bottom at ≈ 28.0. This is
  the same "through the bracket" convention as R045, whose bottom I measure at ≈ 30.3 against the
  package's 30.
- **The L3 rule.** It refuses missing or non-integer eye columns, a hand box more than 1 px from
  its eye estimate, any departure on 1823–1837, and a wrong field count. Each was attacked with a
  re-pinned module, and each failed closed.

Against D1-VRL-R2, the only box changes are those two edges. The notes differ only in the R039,
R046 and R097 rows. The ignore regions are byte-identical. The derived labels are R4 plus exactly
64 lines. My own matcher reproduces 214 → 150 → 110 FP exactly. The author-found R097 defect is
real (15 fields in R2), and no R2 number depended on it.

The 4 Low findings:
- **L1.** The R039 bottom (70), unchanged from R2, is about 2 px short. It is drawn to the top of
  the bracket, not through it as R045 and R046 are.
- **L2.** The L3 rule checks only the agreement between the final box and the author-written eye
  columns. For R039 and R046 those columns are the R3 re-draw, as disclosed.
- **L3 and L4** are carry-overs: the coordinated-rewrite anchor, and the R090/R091 bottoms.

None of these changes the diagnostic or any IoU-0.5 match.

This PASS resolves D1-VRL-R2 QA M1 and L1 for the purpose of owner acceptance. It authorizes
nothing by itself:
- it does not make the derived labels the evaluation authority;
- it does not authorize a gate change, R10 replacement, threshold change, training, smoke run,
  sealed-test access, commit or push.

I opened no test material and ran no model.

## Exact reviewed inputs and pins

| Input | SHA-256 | Result |
| --- | --- | --- |
| `detector/m1/val_relabel_r3.py` | `34b89e320775abb8bf6186558ce03666c221331969c978836b01342e2e0d72ec` | matches implementation record; **this QA record pins it** |
| `detector/tests/test_val_relabel_r3.py` | `8467d181b3317fc9ff71b0ef19d7ac21fdd2d73f05ea377a1105849ded5766d7` | matches |
| `docs/review/d1_vrl_r3_box_review_notes.csv` | `b653abb393fa278a4737cf3e08160e1c312d5b1b11d96cba029da8f3e4f4a385` | matches module `PINNED` and record |
| `docs/review/d1_vrl_r2_owner_decision_r3.md` | `34ad3fd303e0bd935352405506ce9d6af505be445d9520d70f458b2fd4e267f8` | matches |
| `docs/review/d1_vrl_r2_independent_qa_record.md` | `0758405680147ba9b153758076b0803245373947ece90953f22ca3025369514d` | matches |
| `detector/m1/val_relabel_r2.py` | `2d70762550dd6e7752e122b31c3628256a8eafebf3ca14f7be6facfc5ca12710` | matches (pinned by the R2 QA) |
| `docs/review/generated/d1_vrl_r2_manifest.json` | `e23b725f711ae6f9a15f8db4d00e13ec8048a392f8db10296972113573c008ff` | matches (pinned by the R2 QA) |
| the other 15 inherited pins (`val_label_audit_r1.py`, `val_relabel_r1.py`, R2 notes `a9c05fa8…`, VLA-R1 proposals/manifest/QA/correction, VRL-R1 notes/scope/correction/QA, VRL-R1 manifest, `d1_ea_r1_predictions.csv`, `m1_yolo_classes.csv`, R4 manifest) | as listed in the manifest `pinned_sources` (20 entries) | all match (`verify_pins`, run by `verify`, passes; 11 of them re-checked by hand in the R2 QA and unchanged) |
| R4 val labels, `labels_sha256` (own formula: sorted `stem\n<content>`) | `e64345bb3a618187d10828ccc135172736ff45956570359da4fa99d441f320cc` | recomputed: **unchanged** |
| `docs/review/generated/d1_vrl_r3_added_boxes.csv` (64 rows) | `e6d19d490e308cc301c03b68c14a12216951e2ec3a788a8118ee17ff3be4a59e` | matches |
| `docs/review/generated/d1_vrl_r3_ignore_regions.csv` (40 rows) | `ec102253b3b049186a966254b2ad54fe6cdefb7251e486632f30b82cf4c2bf4e` | matches; **byte-identical to R2** |
| `docs/review/generated/d1_vrl_r3_manifest.json` | `87dd0fd9ecea85745f613a788ef70ae830d396fc9e747f233db0c6fc536b8e07` | matches; **this QA record pins it** |
| `docs/review/d1_vrl_r3_report.md` | `a66e1baeb8e889cc9cd770ef2c1e3b9e90d9683b85ad8b0dde7b6942bf141123` | equals the manifest; byte-compared by `verify` |
| `docs/review/d1_vrl_r3_implementation_record.md` | `0e2e72f3d23119c4df9fddc30b4e8ffd89585b3edcb485d7b912fc918c0e786d` | read |
| `docs/review/d1_vrl_r3_qa_brief.md` | `9251a58a731b463141afd5aa2af5bbfa2946418af119fd51250a76e6c04d59cd` | followed |
| derived label roster (manifest field; own recomputation) | `dc72ebd944a38535d4f766ba4f8babc60cb6732dfcd253ed0e8d79dc86eb8343` | matches record |
| atlas `added_page_01…04.jpg` | `1a98f8bd…`, `9057edf1…`, `4e8fa212…`, `e9ed8245…` | equal the manifest; pages 01 and 04 are byte-identical to R2, while 02 (R039) and 03 (R046) differ |
| `data/processed/m1_yolo_val_vrl_r3/ignore_regions.json` | `4aaee942…` | equals the manifest; byte-identical to R2 |

The manifest lists 384 artifacts: 2 CSVs, the report, `ignore_regions.json`, 376 label files and
4 atlas pages. `verify` byte-compares each against a fresh render.

## Check 1 — pins and delta against D1-VRL-R2

All pins above match.

`diff` of the R2 and R3 added-box CSVs gives exactly two changed rows:

| ID | R2 | R3 | Changed fields |
| --- | --- | --- | --- |
| R039 (1223) | 0, 44, 36, 70; IoU 0.7103 | **6**, 44, 36, 70; IoU 0.7780 | x1 and the derived x_center/width/IoU |
| R046 (1229) | 117, 0, 153, 23; IoU 0.7854 | 117, 0, 153, **28**; IoU 0.8633 | y2 and the derived y_center/height/IoU |

`diff` of the R2 and R3 notes gives exactly three changed rows:
- **R039.** `x1` and `eye_x1` change 0 → 6. The note is rewritten to describe the R3 re-draw. The
  eye y1/x2 values (43/37) stay the R2 eye estimate, consistent with "other edges as in R2".
- **R046.** `y2` and `eye_y2` change 23 → 28, and the note is rewritten.
- **R097.** The note is re-quoted. Its text is unchanged except that it is no longer truncated.

The derived label trees differ from R2 only in `1223.txt` (line 3) and `1229.txt` (line 4), the
YOLO lines of R039 and R046. All other 374 files are byte-identical. `d1_vrl_r3_ignore_regions.csv`
and `ignore_regions.json` are byte-identical to R2. Decision counts are unchanged: 40
`IGNORE_REGION`, 38 `HAND_DRAWN`, 23 `ACCEPT_REFINED` and 3 `ACCEPT_REFINED_ADJUSTED`.
**Confirmed.**

## Check 2 — geometry (own re-measurement from the raw frames)

Method:
- I rendered box-free 14× nearest-neighbour crops with a pixel tick grid (`crop.py`).
- I placed each edge by eye. I then refined it with 50 % luminance crossings between the background
  and the rim minimum (`prof.py`), in box coordinates (pixel *i* spans [*i*, *i*+1)).
- I seeded only from my own view of the crops. No package box or locator was used to place an
  edge.

| ID | Frame | Side | Profile evidence | QA estimate | Package | Diff |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| **R039** | 1223 | **left** | rows 54/57/60: 239→166, 221→137, 234→169 between x = 5 and 6; crossings 6.35 / 6.02 / 6.38 | **6.0–6.4** | **6** | ≤ 0.4 |
| R039 | 1223 | top | columns 16/21: crossing 44.1 / 43.6 | 43.6 | 44 | 0.4 |
| R039 | 1223 | right | rows 54/57/60: 35.6 / 36.2 / 36.1 | 36.0 | 36 | 0.2 |
| R039 | 1223 | bottom | column 21: interior ~155, ring minimum 94 at y = 71, bright 214 at 73 (outer edge ≈ 72.3); at x = 31 the rim is clear of the bar, and its edge (≈ 68.5) with an ellipse through the top and sides gives ≈ 72.2 | **≈ 72** | 70 | **≈ 2 (L1)** |
| **R046** | 1229 | **bottom** | columns 125/130/135/140/145 cross dark→bright at 26.5 / 27.3 / 28.1 / 28.0 / 28.5; the side rims are widest at y ≈ 10 (width 37.1), so r ≈ 18.5 and the bottom is ≈ 28.5 | **≈ 28.0** | **28** | ≤ 0.5 |
| R046 | 1229 | left / right | rows 5/10/15: left 116.5 / 116.1 / 117.1, right 152.6 / 153.2 / 152.5 | 116.6 / 152.8 | 117 / 153 | ≤ 0.4 |
| R045 (reference) | 1228 | bottom | columns 97/101/106/111 cross at 29.6 / 30.3 / 30.3 / 30.8 | ≈ 30.3 | 30 | 0.3 |
| R045 (reference) | 1228 | left / right | row 10: 83.9 / 119.05 | 83.9 / 119.0 | 84 / 119 | ≤ 0.1 |

Findings:
- **R039 left (M1 of the R2 QA) is fixed.** Columns 0–1 are dark (131/146 at rows 54/57) where an
  adjacent object touches the frame edge. They then return to sky (≈ 240) before the rim at x ≈ 6.
  The atlas tile shows the box snug on the left.
- **R046 bottom (L1 of the R2 QA) is fixed** and follows the R045 convention. Both boxes run
  through the bracket to the dark→bright step below it. This step lies where the side-rim circle
  closes (≈ 28.5 for R046). R045 is drawn the same way and measures 30.3 against 30.
- **R039 bottom (new L1, inherited unchanged from R2).**
  - A diagonal bar crosses under the disc. At x = 2 it is dark at y = 67–69; at x = 31 it is dark
    at 71–72.
  - The R039 box stops at 70, at the top of the bar. The disc's lower ring continues to ≈ 72.
  - That is about 2 px short by my measurement. The R2 QA estimated 71.0.
  - Unlike R045/R046, this box is **not** drawn through the bracket. The atlas tile shows the rim
    just below the box line.
  - It is at the 2 px reporting threshold. My corrected box (6.2, 43.6, 36.1, 72.0) has IoU 0.907
    with the package box and 0.847 with its prediction, so the match is unchanged.
- No side of R039, R046 or R045 is off by more than 2 px except the borderline R039 bottom
  (≈ 2.0–2.3 px).

## Check 3 — the L3 check

`check_notes` runs before any decision is applied:
- **Field count.** A row with an extra field (key `None` in `DictReader`) or a missing field (a
  `None` value) is refused.
- **Eye columns.** For every `HAND_DRAWN` row it needs integer `x1…y2` and `eye_x1…eye_y2`.
- **Departure.** It refuses `max |final − eye| > 1`, or `> 0` for stems 1823–1837.

Re-pinned attacks (table in Check 6) show that each refusal works on the real package:
- 2: eye column removed;
- 2b: non-integer `211.5`;
- 2c: all four eye columns removed;
- 2e: 2 px departure;
- 1b, 1d: R039 or R046 reverted with the eye column kept;
- 2d: 1 px departure on 1823;
- 3, 3b, 3c: wrong field count.

The unit tests cover the same refusals on synthetic rows.

State of the real notes:
- all 38 hand rows have integer eye columns;
- the maximum departure is 1 px;
- 9 rows have final = eye: R012, R026, R028, R033, R035, R036, R046, R090 and R091;
- the only hand rows on 1823–1837 are R090 and R091, both with 0 px departure.

**The R3 re-draw recorded as the eye estimate.**
- For R039 (`eye_x1` 6) and R046 (`eye_y2` 28), the eye columns are not a blind eye estimate in the
  R2 sense. They are the profile re-draw that the R2 QA evidence prompted. For those two edges the
  1 px rule therefore holds by construction.
- This is disclosed in four places: in each note ("eye columns record this re-draw"), in the owner
  decision, in the implementation record and in the report.
- It is acceptable:
  - the owner ordered both values ("~6–7", "~28") from QA evidence;
  - my own independent profiles confirm both values within 0.5 px;
  - the alternative, keeping the wrong R2 eye values, would make the rule refuse the correction.
- Independence from the model box is not harmed. The new edges come from pixel profiles that two
  QA reviewers reproduced.

The limit is inherent and is recorded as L2. The rule can only check the final box against the
author's eye columns. Attack 1c sets both R039 `x1` and `eye_x1` back to 0, the R2 state, with the
module re-pinned. It passes the rule layer and is caught only by the artifact comparison. A full
re-render would then pass under a forged module (attack 99, L3).

## Check 4 — author-found defect (R2 R097)

- `csv.reader` on `d1_vrl_r2_box_review_notes.csv` gives field counts {14, 15}. The only 15-field
  row is R097.
- `DictReader` truncates its note after "…with a faint tail to 332". The remainder (" and the
  brightened atlas shows the disc rim reaching 330") goes under the key `None`.
- The box columns are intact: 296, 421, 331, 460. The eye columns are empty, as they should be for
  an adjusted re-fit.
- In `val_relabel_r2.py`, `note["note"]` is used only twice:
  - in the non-empty check, which the truncated text still passes;
  - as the `reason` of an `IGNORE_REGION` row, which R097 (`ACCEPT_REFINED_ADJUSTED`) is not.
- No R2 artifact contains the note text.

**No R2 number depended on it.** This is confirmed by Check 1: R097 is byte-identical in the R2 and
R3 added CSVs. The R3 notes all have 14 fields.

## Check 5 — derived labels and diagnostic

`diag.py` imports no repository code. It checks:
- `labels/val/` holds exactly 376 regular `.txt` files, with the same stems as R4 and no symlinks;
- every file equals its R4 text followed by exactly that stem's added lines, rendered from the
  added CSV;
- 64 lines are added across 43 files: 560 → 624 lines;
- the roster hash recomputes to `dc72ebd9…`;
- R4 `labels_sha256` is unchanged.

For the diagnostic I used my own greedy class-agnostic matcher:
- predictions with conf ≥ 0.20, in descending confidence, ties broken by `pred_rank`;
- each matches the best unmatched GT at IoU ≥ 0.5;
- an unmatched prediction is ignored if ≥ 50 % of its area lies inside an ignore region of its
  frame.

| Labels | GT | TP | FP | Ignored | FP/image | Agnostic recall | Precision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R10 (R4) | 560 | 483 | 214 | — | 0.569149 | 0.862500 | 0.692970 |
| **R3, added boxes (independent)** | 624 | 547 | **150** | — | **0.398936** | 0.876603 | 0.784792 |
| R3, + 40 ignore regions (circular) | 624 | 547 | 110 | 40 | 0.292553 | 0.876603 | 0.832572 |

These equal the manifest `summary` exactly. All 64 added boxes are matched.

The report:
- shows "FP before ignore 150" and "FP in ignore regions 40" as separate columns;
- labels 150 FP as "Independent of the model geometry";
- labels the further 40 as "Circular by construction … no evidence that the model is right on the
  small discs";
- states "This is a diagnostic, not an evaluation … changes no gate";
- states that the critical classes 7, 32 and 41 are untouched.

The implementation record repeats this and notes that 0.399 is above the 0.30 gate. **Confirmed.**

## Check 6 — verifier, tests and tampering

Verifier and tests:
- `uv run python -m m1.val_relabel_r3 verify` (from `detector/`) returns `valid=true`, `errors=[]`
  (1.4 s).
- The R2 and R1 verifiers are still `valid=true`.
- `pytest -p no:cacheprovider tests/test_val_relabel_r3.py tests/test_val_relabel_r2.py
  tests/test_val_relabel_r1.py` passes 15 tests.
- `ruff check` and `ruff format --check` are clean on both R3 files.
- Full `detector` suite: 230 passed (230 dots, no F/E), exit 0. `uv lock --check` is OK
  (66 packages resolved).

Tampering attacks:
- They ran on APFS clones of `docs/review`, `data/processed/m1_yolo_wp38_r1_integration_r4`,
  `data/processed/m1_yolo_val_vrl_r3` and `detector/m1`, staged under the reviewer scratchpad
  (`tamper.py`).
- Each attack calls `verify(repo_root=<stage>)` of the unmodified repository module. Attacks marked
  "re-pinned" instead use the staged module, with its notes pin set to the tampered notes, so that
  they test the rule itself rather than the pin.
- `build` was never run on the repository. Attack 99 rendered forged artifacts into its own stage
  only.

| # | Attack | Result |
| ---: | --- | --- |
| 0 | clean staged copy | valid=true |
| 1 | notes R039 x1 6 → 0 (eye_x1 stays 6), pin unchanged | **FAIL closed** (pinned D1-VRL-R3 source differs: notes) |
| 1b | **R039 x1 6 → 0 (eye stays 6), module re-pinned (L3 rule)** | **FAIL closed** (R039: hand-drawn box departs from its eye estimate by more than 1 px) |
| 1c | R039 x1 and eye_x1 both → 0 (the R2 state), re-pinned | **FAIL closed** at the artifact layer only (added CSV, 1223.txt, atlas page 02 differ); the rule layer accepts it (L2) |
| 1d | R046 y2 28 → 23 (eye stays 28), re-pinned | **FAIL closed** (R046: … more than 1 px) |
| 2 | **R004 eye_x1 removed**, re-pinned | **FAIL closed** (R004: hand-drawn row needs integer box and eye columns) |
| 2b | R004 eye_x1 = `211.5`, re-pinned | **FAIL closed** (same) |
| 2c | all four R018 eye columns removed, re-pinned | **FAIL closed** (same) |
| 2d | R090 (dark 1823) eye_y2 +1 px, re-pinned | **FAIL closed** (R090: … more than 0 px) |
| 2e | R004 eye_x1 2 px from the final box, re-pinned | **FAIL closed** (R004: … more than 1 px) |
| 3 | **unquoted comma in R097 note** (R2 defect re-introduced), re-pinned | **FAIL closed** (box-review note R097 has a malformed field count) |
| 3b | unquoted comma in the R039 hand-drawn note, re-pinned | **FAIL closed** (R039 … malformed field count) |
| 3c | R039 row truncated to 13 fields, re-pinned | **FAIL closed** (R039 … malformed field count) |
| 3d | unquoted comma in R097 note, pin unchanged | **FAIL closed** (pinned source differs: notes) |
| 4 | **stray `labels/train/0001.txt` under the derived root** | **FAIL closed** (unexpected path: …/labels/train; …/labels/train/0001.txt) |
| 4b | hidden `labels/val/.DS_Store` | **FAIL closed** (unexpected path) |
| 4c | stray atlas `added_page_05.jpg` | **FAIL closed** (unexpected path) |
| 4d | derived `1223.txt` replaced by a symlink to identical bytes | **FAIL closed** (artifact differs; unexpected path) |
| 5 | **R4 val label `1208.txt`: class id changed** | **FAIL closed** (WP38-R1 R4 validation labels differ from labels_sha256 e64345bb…) |
| 5b | same edit mirrored into derived `1208.txt` | **FAIL closed** (same) |
| 6 | **manifest `evaluation_authority` → true** | **FAIL closed** (artifact differs: d1_vrl_r3_manifest.json) |
| 6b | manifest `gates_changed` → true | **FAIL closed** (same) |
| 6c | manifest `sealed_test_accessed` → true | **FAIL closed** (same) |
| 7 | added_boxes.csv R039 x1 6 → 0 | **FAIL closed** (artifact differs: d1_vrl_r3_added_boxes.csv) |
| 7b | control: ignore CSV replaced by the R2 file | valid=true (expected: byte-identical) |
| 8 | derived `1229.txt` reverted to the R2 file (y2 23) | **FAIL closed** (artifact differs: …/1229.txt) |
| 9 | one byte flipped in `added_page_03.jpg` | **FAIL closed** (artifact differs) |
| 10 | report "0.399 per image" → "0.299" | **FAIL closed** (artifact differs: report) |
| 11 | pinned R2 module, one comment byte | **FAIL closed** (pinned source differs: val_relabel_r2.py) |
| 12 | pinned owner decision, one word | **FAIL closed** (pinned source differs: owner decision) |
| 99 | coordinated forgery: R039 x1 + eye_x1 → 0, module re-pinned, artifacts re-built in the stage (forged manifest `99caa52f…`, diagnostic still 150 FP) | `valid=true` under the FORGED module (L3) |
| 99b | same forged stage under the REPOSITORY module | **FAIL closed** (pinned D1-VRL-R3 source differs: notes) |

All six attacks the brief requires fail closed:
- R039 reverted to x1 = 0 with the module re-pinned (1b);
- an eye column removed (2);
- an unquoted comma in a note (3, 3b);
- a stray file under the derived root (4);
- an edited R4 label (5);
- the manifest boundary flags (6, 6b, 6c).

My first run of 3b was a no-op, because its search text did not occur in the R039 note, and it
returned `valid=true`. I corrected the mutation, and the re-run fails closed as shown.

## Check 7 — boundary

The manifest records:
- `evaluation_authority=false`
- `gates_changed=false`
- `sealed_test_accessed=false`
- `training_authorized=false`
- `test_included=false`
- `train_or_test_labels_changed=false`
- `supersedes=D1-VRL-R2`
- `pillow_version=13.0.0`

Status `D1_VRL_R3_AWAITING_INDEPENDENT_QA`. The report says that the labels are "not yet the
evaluation authority". `graft grep` finds no consumer of `m1_yolo_val_vrl_r3` or `val_relabel_r3`
other than the builder and its test. Both output trees are git-ignored (`.gitignore:16` and `:41`).
**Confirmed.**

## Findings

| ID | Severity | Finding | Evidence | Required action |
| --- | --- | --- | --- | --- |
| L1 | Low | The R039 bottom (y2 = 70, unchanged from R2) stops at the top of the diagonal bracket. The disc's lower ring reaches about 72. This is inconsistent with the "through the bracket" convention that R3 adopts for R046, after R045. | Column 21: ring minimum at 71, bright at 73 (edge ≈ 72.3); the x = 31 rim plus an ellipse through the top and sides gives ≈ 72.2; the atlas tile shows the rim below the line. The R2 QA estimated 71.0. My box keeps the prediction matched (IoU 0.847). | Optional. Fix in any future successor (y2 ≈ 72), or note it in the owner acceptance record. Not a blocker. |
| L2 | Low | The L3 rule checks only that the final box agrees with author-written eye columns. It cannot detect a wrong eye estimate. For R039 and R046 the eye columns are the R3 re-draw, so the rule holds by construction there (disclosed). | Attack 1c: x1 and eye_x1 both back to 0 pass the rule layer; only the artifact comparison catches them. | None beyond the pins. The R3 values are independently confirmed in Check 2. |
| L3 | Low | Carry-over of R2 L4: a coordinated rewrite of the notes, the module pin and the artifacts verifies under the forged module. | Attack 99 (forged manifest `99caa52f…`) | Treat module `34b89e32…` and manifest `87dd0fd9…`, pinned here, as the anchor. |
| L4 | Low | Carry-over of R2 L2: the R090/R091 bottoms are about 3 px short. They are unchanged, by the owner decision. | R2 QA red-ring profiles; the report states the limit | None (disclosed limit). |

What this QA does **not** dispute:
- the R039 and R046 corrections;
- the L3 implementation;
- the R097 diagnosis;
- the unchanged 62 boxes and 40 ignore regions;
- the classes;
- the diagnostic arithmetic and its independent/circular split;
- the boundary flags.

## Commands run

```text
shasum -a 256 <module, test, notes, owner decision, R2 QA/module/manifest, R2+R3 CSVs, R3 manifest, report, records, brief, atlas, ignore json>
diff <R2 vs R3 notes>; diff <R2 vs R3 added CSV>; cmp <376 derived labels, ignore json, atlas pages R2 vs R3>
graft grep "m1_yolo_val_vrl_r3" ; graft grep "val_relabel_r3"
cd detector && uv run python -m m1.val_relabel_r3 verify          # valid=true (also r2, r1 verify: valid=true)
cd detector && uv run pytest -q -p no:cacheprovider tests/test_val_relabel_r3.py tests/test_val_relabel_r2.py tests/test_val_relabel_r1.py   # 15 passed
cd detector && uv run ruff check / ruff format --check <2 R3 files>                   # clean
cd detector && uv run pytest -q -p no:cacheprovider   (background) ; uv lock --check
uv run python -I <scratchpad>/qa/crop.py <frame> <out> x0 y0 x1 y1        # box-free tick-grid crops (1223, 1228, 1229)
uv run python -I <scratchpad>/qa/prof.py <frame> row|col <i> <a> <b>      # luminance profiles
uv run python -I <scratchpad>/qa/diag.py <repo>                           # R4 + 64; roster; 214 -> 150 -> 110
detector/.venv/bin/python -I <scratchpad>/qa/tamper.py <scratchpad>/qa <repo> [ids]   # staged attacks
```

Every script wrote only to the reviewer scratchpad. `git status --short` before and after shows
the same 34 untracked entries, plus this file. No model was loaded. No inference, `build` on the
repository, training, relabel, upload, commit, push or sealed-test access occurred. The only
repository change is this new file.

## Bounded next state

| Action | QA disposition |
| --- | --- |
| Owner acceptance record for D1-VRL-R3 (module `34b89e32…`, manifest `87dd0fd9…`) as derived validation labels | **YES, eligible.** R2 QA M1 and L1 are resolved. L1 here (R039 bottom ≈ 2 px) may be accepted as is or noted. |
| Make the derived labels the evaluation authority | **NO** — only after the owner acceptance and a QA-passed re-evaluation contract |
| Re-evaluation contract on the derived labels (IoU-0.5 matching kept, ignore regions reported separately as circular) | **YES**, after the owner acceptance |
| Cite 150 FP / 0.399 FP/image as the independent diagnostic | **YES, as a diagnostic only** — not a gate result; it is still above the 0.30 gate |
| Cite 110 FP / 0.293 FP/image as a gate result | **NO-GO** — circular ignore part |
| Change any gate, NMS or confidence; replace R10 | **NO-GO** |
| Use validation pixels, labels or predictions for training or mining | **NO-GO** |
| Smoke, pilot, new seeds or any training from this record | **NO-GO** |
| Open or export the sealed test | **NO-GO** |
