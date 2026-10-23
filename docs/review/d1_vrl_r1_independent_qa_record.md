# D1-VRL-R1 derived validation labels with ignore regions — independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_FAIL__IGNORE_REGION_PREMISE_MISSTATED`  
Reviewer: `Claude Code fresh independent QA session (did not author D1-VRL-R1)`  
Boundary: `READ_ONLY_NO_INFERENCE_NO_TRAINING_NO_BUILD_NO_SEALED_TEST`

## Verdict

**FAIL — 0 Critical, 1 High, 0 Medium and 5 Low findings.**

The mechanics of the package are sound. Every pin matches. `verify` returns `valid=true` and the
5 tests pass. I reproduced the re-fit of all 104 proposals with my own HSV and component code, and
it gives the same 26 / 6 / 72 split. I also reproduced the derived labels (R4 plus exactly 26
lines) and the diagnostic 214 → 188 → 110 FP exactly. The report states that the 78-FP ignore drop
is circular, and I confirm it: the drop does not change for any containment threshold from 0.3 to
0.9 or for a margin of 0. The 26 added boxes are on the right signs and come from pixels. The 6
partial re-fits were correctly rejected.

The FAIL rests on **H1**. The owner geometry decision describes "the other 72" as "11–17 px
low-saturation discs on the 1208–1229 and 1342–1357 poles". The trusted notes give the same reason
for every one of them: "no reliable colour region: small low-saturation sign". This is false for a
large part of the set:

- Only 40 of the 72 locators are ≤ 17.5 px on their longer side. 20 are 17.5–25 px, 7 are
  25–40 px and **5 are 44–80 px**.
- Five lie outside the named poles, on frames 1236 and 1242–1245.
- At least 12 are large, saturated and legible:
  - the P.111a+b discs on 1242–1245 (61–80 px, strong red ring);
  - the P.130 disc on 1236 (44 × 34 px);
  - the "40"/"60" speed discs on 1223/1228/1229 (33–39 px);
  - the 1217/1223–1225 discs (25–27 px).
- 9 of the 72 + 6 ignored items are HIGH class-confidence proposals.

The owner scope required boxes that cannot be re-fitted to be "entered by hand, or dropped with a
reason". The owner approved the ignore route on a factual premise that does not hold for these
items. For them, the circular ignore mechanism replaced an independent hand-drawn ground-truth box
that was feasible. The owner's acceptance needs a correct premise, so the package cannot pass as
built.

This FAIL authorizes nothing. It does not make the derived labels the evaluation authority. It
does not authorize a gate change, R10 replacement, threshold change, training, smoke run, sealed-test
access, commit or push. I opened no test material and ran no model.

## Exact reviewed inputs and pins

| Input | SHA-256 | Result |
| --- | --- | --- |
| `detector/m1/val_relabel_r1.py` | `9fba10089ad23fc494b2548fec60acf4d07ae34feebcc8bfb530887b0ff5eff5` | matches implementation record; **this QA record pins it** |
| `detector/tests/test_val_relabel_r1.py` | `1f6393685aa636a7cb56c79761075a4a5984c5130e66e4f036b232770e30dcf6` | matches |
| `docs/review/d1_vrl_r1_box_review_notes.csv` | `4458474f2c75830567bc094f43d46cad885fab4245d3347ad4f9790f78736101` | matches module `PINNED` and record |
| `docs/review/d1_vrl_r1_owner_scope_record.md` | `a96e55f464dfd98c0a08ace0db11d589429a420b3f752d02f74584a04c4a103b` | matches |
| `docs/review/generated/d1_vla_r1_proposed_val_labels.csv` | `70773b4be23e223ae149e616098d7d91d1042cdcfd689f220030fa83fbd32356` | matches |
| `docs/review/generated/d1_vla_r1_manifest.json` | `3fbbe7fd2b2bc44f632f676cfa60861f963a1cf31b193119c49049e9ed9c2e46` | matches |
| `detector/m1/val_label_audit_r1.py` | `3826fa57a7cb8d7611c941ce590d7b9f785f4fc23e562842f9aa39c7a99838cf` | matches |
| `docs/review/d1_vla_r1_independent_qa_record.md` | `5e856b77dace347774246e4f11a38379f3b068182e65bf35e92dac56c030948c` | matches |
| `docs/review/d1_vla_r1_correction_r1.md` | `be06ee8949db75bc964e5d41d4c646fe95de7a90b9a1790194b23727fd282765` | matches |
| `docs/review/generated/d1_ea_r1_predictions.csv` | `cb3cb05f0cadc7d2c3e077120d5b1311648247f74a9648e287da1c4be915f1dd` | matches |
| `docs/review/generated/m1_yolo_classes.csv` | `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242` | matches |
| `docs/review/generated/d1_vrl_r1_added_boxes.csv` (26 rows) | `8a88e31b022b223cd4f13d1c7e6e9e8b1d3e8666b884ef6743a90806806c047d` | matches |
| `docs/review/generated/d1_vrl_r1_ignore_regions.csv` (78 rows) | `b2cc664a2c54cf742131e45d40c0f6a6a8928e9fc69fb9d4f9e35b8d663f522c` | matches |
| `docs/review/generated/d1_vrl_r1_manifest.json` | `3fd91263dabc775bf8967e604a589bb20143bfc43fb45f2e16fa814e973eb34f` | matches; **this QA record pins it** |
| `docs/review/d1_vrl_r1_report.md` | `9c6fe2f7a3b08d91b614437d6f0a3c1bdc47ed3dea98abf59d071b585f4c24a1` | byte-compared by `verify` |
| derived label roster (manifest field) | `152993d027dc3ecf29a54a1ace6a05a6bbc9632b83083f00e7f442e8d3064e5a` | matches record |
| R4 val labels, `labels_sha256` per `m1_yolo_wp38_r1_integration_r4_manifest.json` | `e64345bb3a618187d10828ccc135172736ff45956570359da4fa99d441f320cc` | recomputed: **unchanged** |
| R4 train labels (1,912 non-WP35 stems), `labels_sha256` | `d907fb9f82bbcee4bfb0d6f34d9a673c6f7dbe4173967c92b7552c607abb3b49` | recomputed: **unchanged** |

The manifest lists 382 artifacts: 2 CSVs, the report, `ignore_regions.json`, 376 label files and
2 atlas pages. `verify` byte-compares each of them against a fresh render.

## Check 1 — pins and scope

- All pins above match.
- The notes cover the 104 proposals in order, R001–R104, with matching stem and derived key.
- Decisions: 26 `ACCEPT_REFINED` and 78 `IGNORE_REGION`. The 78 are 72 with "no reliable colour
  region…" and 6 partial re-fits (R040, R042, R044, R049, R090, R091). This matches the owner
  decision by count and by id.
- The proposal CSV has only HIGH (19) and MEDIUM (85) rows. No LOW row, no `UNCLEAR` and no
  out-of-taxonomy board is present, so none is added. Added keys: 2 ×2, 3 ×1, 10 ×13, 12 ×8 and
  14 ×2.
- **Premise defect (H1).** The decision text and the notes misdescribe the 72. My measurement of
  the locator size on the longer side gives:

  | Locator size | Count |
  | --- | ---: |
  | ≤ 17.5 px | 40 |
  | 17.5–25 px | 20 |
  | 25–40 px | 7 |
  | > 40 px | 5 |

  Frames: the 72 span 1208–1218, 1223–1225, 1228–1229, **1236, 1242–1245** and 1342–1357.

  The items > 25 px are: R033 1217 (26 × 24), R038 1223 (27 × 23), R039 1223 (33 × 30), R041 1224
  (26 × 23), R043 1225 (27 × 24), R045 1228 (36 × 30), R046 1229 (39 × 26), R047 1236 (44 × 34),
  R048 1242 (61 × 64), R050 1243 (67 × 70), R051 1244 (80 × 78) and R052 1245 (63 × 80).

  The zoom crops show:
  - R048/R050/R051/R052: clear red-ring P.111a+b discs with motorbike and three-wheeler
    pictograms and the "CẤM XE 02 VÀ 03 BÁNH" plate;
  - R047: a clear P.130;
  - R039/R045/R046: legible "60"/"40"/"60" discs.

  None of these is "small" or practically "low-saturation". The colour fit misses them for other
  reasons, such as the component merging or splitting with the adjacent plate or disc (best IoU
  0.12–0.28). That is not the reason recorded.

## Check 2 — box geometry

I read both atlas pages and rendered my own nearest-neighbour zooms of the raw frames, at 3.5×
brightness for the 1823–1837 shadow run. In these zooms the yellow box is the locator, the green box
is the added box and the magenta box is the rejected re-fit.

| Added boxes | Judgement |
| --- | --- |
| R003/R011/R015/R021/R024 (1208–1213 R.415a board), R054/R055 (1329/1331), R037 (1221, cut at the edge) | Tight on the blue board, within about 1–2 px |
| R053 (1328) and R056 (1332, cut at the top edge) "3.5t" discs | Tight on the outer red ring |
| R087/R089 (1820/1821 P.102), R088 (1820 R.302a) | On the disc. R089 is blurred, and its top/left edge may sit up to about 2 px inside the pink rim, which is within tolerance. R088 extends about 2 px below the disc. |
| R093/R094/R096/R098/R099/R101/R102/R104 (shadow run) | Tight |
| **R092 (1825), R095 (1828), R097 (1830)** | About 4–5 px loose on the **right** side, picking up reddish background next to the disc |
| **R103 (1836)** | About 4 px loose at the **bottom**, onto the plate edge. The box is 44 × 49 px for a disc that is wider than it is tall. |

The loose sides are corroborated by a strict-mask profile (s > 0.3): 4–5 columns or rows inside
those box edges carry no sign pixels. All four boxes still contain the whole sign and their IoU with
a tight box is about 0.85–0.9. This is reported as L1.

**The 6 rejected re-fits are correctly rejected.**
- R040/R042/R044: the re-fit covers only the blue centre of a 25 px P.130 and misses the red rim.
- R049: the re-fit covers only the upper-left part of a 72 × 55 P.130 that is cut by the top edge.
- R090: the re-fit is a narrow central strip.
- R091: the re-fit covers the left half of the shadowed disc.

R040/R042/R044/R049 are legible and could have been hand-drawn. The owner chose to ignore them, and
that choice was made on an accurate description ("covers only part"), so it is not a finding.

**Spot check of the 72 (27 items).**
- Small items: R001, R002, R005, R009, R022, R057, R058, R059, R064, R066, R070, R075, R080, R085
  and R086. These are 10–16 px pole discs with grey/brown rims at about 8× zoom. I agree that no
  reliable colour region exists and that an ignore region is reasonable.
- Larger items: R032, R033, R035, R036, R038, R039, R041, R043, R045, R046, R047, R048, R050, R051
  and R052.
  - R032/R035/R036 (19–24 px) are borderline.
  - The 12 items ≥ 25 px listed in Check 1 contradict the recorded reason (H1).

## Check 3 — independence

My `qa_fit.py` imports no repository code. It has its own float HSV formula, not PIL's 8-bit HSV,
its own 8-connected labelling and its own IoU. It uses the same thresholds:
- red: h < 20 or > 330, s > 0.15, v > 0.15;
- blue: 190 < h < 260, s > 0.15, v > 0.12;
- a crop of one box size per side;
- best-IoU component ≥ 0.3.

| Result | Count |
| --- | ---: |
| `ACCEPT_REFINED` that re-fit | 26 / 26 |
| partial `IGNORE_REGION` that re-fit (the 6 above) | 6 |
| "no reliable" `IGNORE_REGION` that do not re-fit | 72 / 72 |
| added boxes identical to the package | 20 / 26 |
| added boxes differing by 1 px on one side (rounding of the 8-bit HSV) | 5 |
| added boxes differing by 3 px on one side (R053 x2 426 vs 429) | 1 |

The IoU of an added box with the model box is min 0.66, median 0.87, max 0.96, as reported.

**The boxes come from pixels, not from the model box.** The written coordinates are integer pixel
extents of a colour component. The model box only selects the component and sizes the crop.

Applying the same fit to the 83 existing human ground-truth boxes ≥ 18 px of classes 2/3/10/12/14
gives median IoU 0.869 and p10 0.38. 88 % differ from the human box by > 2 px on at least one side.
The fit is therefore a locator-free geometry source, not a reproducer of the dataset's box
convention. The visual check is the real guard (L2).

Robustness: shifting every added box diagonally by 2 px leaves all 26 matched to a prediction at
IoU ≥ 0.5. A 3 px shift loses R089; a 4 px shift loses R087, R088, R089 and R092.

The report's Limits section states: "The ignore-region FP drop is circular by construction … it
is not evidence that the model is right on those discs. Only the 26 re-fitted boxes are independent
of the model geometry." The implementation record says the same. **Confirmed.**

## Check 4 — class ids

`m1_yolo_classes.csv` (pinned `7cda296a…`) maps derived key → YOLO id as follows:

| Derived key | YOLO id |
| --- | ---: |
| 2 | 2 |
| 3 | 3 |
| 10 | 10 |
| 12 | 12 |
| 14 | 14 |
| **23** | **25** (P.111a+P.111b) |
| **39** | **40** (P.127) |
| **41** | **42** (P.127) |

All 26 added rows carry `yolo_id` equal to the mapping of their key. Their keys are 2/3/10/12/14,
which map to themselves. The 23/39/41 keys occur only in ignore rows, which carry no class id.
`derive` maps through the CSV, so it would map keys 23/39/41 correctly. The unit test asserting this
is vacuous on the current data (L4).

## Check 5 — derived labels

`qa_labels.py` imports no repository code. Its results:
- `labels/val/` holds exactly 376 regular `.txt` files, with no symlinks and no other entries, and
  the same stem set as R4.
- In every file the R4 lines come first, byte for byte, followed by exactly that stem's added lines.
- 26 lines are added across 25 files. 1820 receives 2 lines and 351 files are identical to R4.
- No R4 file lacks a trailing newline. The 10 empty R4 files stay empty, apart from any that
  receive an added line.

Unchanged inputs:
- The R4 val `labels_sha256` recomputes to `e64345bb…` and the R4 train `labels_sha256` to
  `d907fb9f…`, both equal to the R4 integration manifest.
- No file under the R4 export or `data/raw` is newer than the owner scope record.
- `git status` shows no change to tracked files.
- The R4 export has no test directory. The test split exists only as hash metadata in the R4
  manifest and was not opened.
- `graft grep "m1_yolo_val_vrl_r1"` and `graft grep "val_relabel_r1"` find no consumer other than
  the builder and its test. No training or data builder reads the derived labels.

## Check 6 — diagnostic

`qa_diag.py` uses its own greedy class-agnostic matcher: descending confidence, ties broken by
`pred_rank`, best unmatched IoU ≥ 0.5. Its other inputs:
- ground truth from the R4 label files and the raw image sizes;
- ignore regions recomputed from the proposals and notes (locator expanded by 25 % per side, clipped
  to the image). They agree with the package CSV within 0.005 px.

| Labels | GT | TP | FP | Ignored | FP/image | Agnostic recall | Precision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R10 (R4) | 560 | 483 | 214 | — | 0.569149 | 0.8625 | 0.69297 |
| + 26 added | 586 | 509 | 188 | — | 0.500000 | 0.868601 | 0.730273 |
| + 26 + 78 ignore | 586 | 509 | 110 | 78 | 0.292553 | 0.868601 | 0.822294 |

These numbers equal the manifest exactly.

- **The ignore rule is implemented as specified**: an unmatched prediction with ≥ 50 % of its area
  inside a region is not counted, and the margin is 25 % per side.
- Containment thresholds 0.3, 0.7 and 0.9, and a margin of 0, all give the same 78 ignored and
  110 FP. Each region exempts exactly its source prediction, so the margin and threshold play no
  role. This confirms the circularity the report states.
- The report and the record label the table as a diagnostic, "not an evaluation … changes no gate".
  **Confirmed.**

## Check 7 — verifier, tests and tampering

Verifier and tests:
- `uv run python -m m1.val_relabel_r1 verify` returns `valid=true`, `errors=[]` (about 1.5 s).
- `pytest tests/test_val_relabel_r1.py` passes 5 tests.
- `ruff check` and `ruff format --check` are clean on both files.
- Full `detector` suite: see the commands section.

Tampering attacks:
- They ran on APFS clones under the reviewer scratchpad (`qa_tamper.py`), using the unmodified
  repository module with `verify(repo_root=<stage>)`.
- `build` was never run, on the repository or on a stage.
- The one exception is attack 99, which wrote forged artifacts into its own stage through
  `render()`.

| # | Attack | Result |
| ---: | --- | --- |
| 0 | Clean staged copy | `valid=true` |
| 1 | Edit one note text (R001) | **FAIL closed** (pinned notes differ) |
| 2 | Note R047 `IGNORE_REGION` → `ACCEPT_REFINED` | **FAIL closed** (pinned notes differ) |
| 3 | Derived `1208.txt`, one coordinate digit changed | **FAIL closed** |
| 4 | Derived `0024.txt`, one GT line appended | **FAIL closed** |
| 5 | Stray `labels/val/9999.txt` | **FAIL closed** (unexpected file) |
| 6 | Hidden `labels/val/.DS_Store` | **FAIL closed** |
| 7 | Delete derived `1837.txt` | **FAIL closed** |
| 8 | Derived `1208.txt` replaced by a symlink to identical bytes | **FAIL closed** |
| 9 | Flip one byte of `added_page_01.jpg` | **FAIL closed** |
| 10 | Add `added_page_03.jpg` | **FAIL closed** (unexpected file) |
| 11 | `ignore_regions.json` margin 0.25 → 0.5 | **FAIL closed** |
| 12 | Manifest `evaluation_authority` → `true` | **FAIL closed** |
| 13 | Report FP/image 0.293 → 0.250 | **FAIL closed** |
| 14 | `added_boxes.csv` R003 x1 336 → 335 | **FAIL closed** |
| 15 | The same GT line appended to R4 `1208.txt` and derived `1208.txt` | **FAIL closed** (derived order and report) |
| 15b | The same class flip 28 → 29 in R4 `1208.txt` and derived `1208.txt`, which leaves the agnostic diagnostic unchanged | **FAIL closed** (manifest digests) |
| 16 | Stray `data/processed/m1_yolo_val_vrl_r1/extra.json` at the derived root | **`valid=true`, not detected** (L3) |
| 17 | Stray `labels/train/x.txt` beside `labels/val` | **`valid=true`, not detected** (L3) |
| 99 | Coordinated forgery: note text changed, module `PINNED` patched, everything re-rendered | `valid=true` under the forged module (manifest `1db9a728…`); **fails closed** under the repository module. Only the module pin `9fba1008…` and the manifest pin `3fd91263…` detect it (L5). |

All four attacks the brief requires (1, 3/4, 5 and 9) fail closed.

## Check 8 — boundary

The manifest records:
- `evaluation_authority=false`
- `gates_changed=false`
- `sealed_test_accessed=false`
- `training_authorized=false`
- `test_included=false`
- `train_or_test_labels_changed=false`
- `pillow_version=13.0.0`

The report and the record status say that the labels are not the evaluation authority until QA,
an owner acceptance and a QA-passed re-evaluation contract. **Confirmed.**

## Findings

| ID | Severity | Finding | Evidence | Required action |
| --- | --- | --- | --- | --- |
| H1 | **High** | The owner geometry decision and the trusted notes describe all 72 non-refitting proposals as "11–17 px low-saturation discs on the 1208–1229 and 1342–1357 poles" / "small low-saturation sign". This is false for a large part of the set. The owner approved the circular ignore route, rather than the scope's "entered by hand, or dropped with a reason", on that premise. The report repeats it ("small low-saturation sign: 72"; "Ignore regions remove the small pole discs"). | Locator size: 40 ≤ 17.5 px, 20 at 17.5–25, 7 at 25–40, 5 at 44–80. Frames 1236 and 1242–1245 lie outside the named poles. Legible, saturated large signs: R047 (P.130 44 × 34), R048/R050/R051/R052 (P.111a+b 61–80 px), R039/R045/R046 ("60"/"40"/"60" 33–39 px), R033/R038/R041/R043 (25–27 px). 9 HIGH class-confidence proposals are among the ignored items. | Append a correction to the scope and implementation records with the true size and frame distribution. Get an owner re-decision for at least the 12 items ≥ 25 px, and preferably for every item > 17.5 px: hand-draw independent boxes, or keep them as ignore regions with a truthful reason. Build a successor package (D1-VRL-R2), since this one is append-only, and give it independent QA. |
| L1 | Low | 4 of 26 added boxes are about 4–5 px loose on one side | R092/R095/R097 on the right side, R103 at the bottom (zoom at 3.5× brightness; strict-mask profile). The other 22 are within about 2 px. | Tighten them by hand in the successor, or record the tolerance |
| L2 | Low | The colour fit does not reproduce the dataset's human box convention | On 83 existing human GT boxes ≥ 18 px: median IoU 0.869, p10 0.38, 88 % > 2 px off on some side | State that the visual check, not the fit, guarantees geometry. A re-evaluation should keep IoU 0.5. |
| L3 | Low | `verify` polices only `labels/val/` and the atlas directory. Stray files elsewhere under the derived root, including a sibling `labels/train/`, verify as valid. | Attacks 16 and 17 | Check the whole `data/processed/m1_yolo_val_vrl_r1/` tree in a successor |
| L4 | Low | The unit test for the 23/39/41 → 25/40/42 mapping is vacuous: no added row has those keys, and the subset assertion passes on an empty set. The R4 source labels are not in `PINNED`; they are protected only through the manifest digests. | `test_official_package_verifies_and_counts`; attacks 15 and 15b | Add a non-vacuous mapping test, and pin the R4 val `labels_sha256` `e64345bb…` |
| L5 | Low | A coordinated rewrite of notes, module and artifacts verifies | Attack 99, forged manifest `1db9a728…` | Treat module `9fba1008…` and manifest `3fd91263…` (pinned here) as the anchor |

What this QA does **not** dispute:
- the 26 added boxes and their classes;
- the rejection of the 6 partial re-fits;
- the ignore treatment of the about 40 genuinely small (≤ 17.5 px) pole discs;
- the arithmetic of the diagnostic;
- the circularity statement.

H1 may change the independent part of the diagnostic. If the large signs are hand-drawn as ground
truth, their predictions become TP on independent geometry instead of being exempted circularly.
The circular share of the 110-FP figure would shrink, while recall and FP could move either way. The
188 FP figure from the 26 added boxes is unaffected.

## Commands run

```text
shasum -a 256 <module, test, notes, scope, 7 upstream pins, 3 outputs, report, records>
graft check . ; graft grep "PREDICTIONS_PATH" / "def frames_from_rows" / "def val_images" / "def class_names" / "labels_sha256" / "m1_yolo_val_vrl_r1" / "val_relabel_r1"
cd detector && uv run python -m m1.val_relabel_r1 verify                                # valid=true
cd detector && uv run pytest -q -p no:cacheprovider tests/test_val_relabel_r1.py        # 5 passed
cd detector && uv run ruff check / ruff format --check <2 files>                        # clean
cd detector && uv run pytest -q -p no:cacheprovider ; uv lock --check                   # see note below
uv run python -I <scratchpad>/qa/qa_fit.py <repo>      # independent re-fit of all 104
uv run python -I <scratchpad>/qa/qa_zoom.py <repo> ...  # zoom/brightened crops (added, rejected, 27 of the 72)
uv run python -I <scratchpad>/qa/qa_bias.py <repo>     # colour fit vs existing human GT
uv run python -I <scratchpad>/qa/qa_profile.py <repo>  # strict-mask edge slack of the 26
python3 -I <scratchpad>/qa/qa_labels.py <repo>          # derived = R4 + 26; R4 val/train hashes
uv run python -I <scratchpad>/qa/qa_diag.py <repo>     # 214 -> 188 -> 110, IoA/margin sensitivity
.venv/bin/python -I <scratchpad>/qa/qa_tamper.py <scratchpad> <repo>/detector   # 19 staged attacks + forgery
```

Process note: the first `qa_fit.py` run wrote its own `fit.json` output into `detector/` (the
working directory). I moved it to the scratchpad straight away, and `git status` confirmed no
residue. No repository file was modified.

No model was loaded. No inference, `build`, training, relabel, upload, commit, push or sealed-test
access occurred. The only repository change is this new file.

## Bounded next state

| Action | QA disposition |
| --- | --- |
| Treat D1-VRL-R1 (manifest `3fd91263…`) as accepted derived validation labels | **NO — FAIL on H1** |
| Owner acceptance record for D1-VRL-R1 as built | **NO — correct the premise first (append-only)** |
| Correction record and owner re-decision on the > 17.5 px non-refitting items, then a successor D1-VRL-R2 with hand-drawn independent boxes or truthful ignore reasons, then independent QA | **YES** |
| Reuse the 26 added boxes and the 6 rejections in the successor | **YES** (L1 tightening optional) |
| Cite 110 FP / 0.293 FP/image as a gate result | **NO-GO** — diagnostic only, with a circular ignore part |
| Change any gate, NMS or confidence; replace R10 | **NO-GO** |
| Use validation pixels, labels or predictions for training or mining | **NO-GO** |
| Smoke, pilot, new seeds or any training from this record | **NO-GO** |
| Open or export the sealed test | **NO-GO** |
