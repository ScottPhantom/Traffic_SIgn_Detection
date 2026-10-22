# D1-VLA-R1 validation label-completeness audit — independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_PASS_PROPOSAL_PACKAGE__WHAT_IF_IS_AN_UPPER_BOUND`  
Reviewer: `Claude Code fresh independent QA session (did not author D1-VLA-R1)`  
Boundary: `READ_ONLY_NO_INFERENCE_NO_TRAINING_NO_BUILD_NO_SEALED_TEST`

## Verdict

**PASS — 0 Critical, 0 High, 1 Medium and 6 Low findings.**

The PASS covers the proposal package: the builder, its pins, the strata, decision and proposal CSVs,
the 12 atlas pages, the report and the manifest. My own script imports no repository code. From
`d1_ea_r1_predictions.csv`, the validation label files and the raw image sizes, it reproduced:

- the R10 baseline;
- the four strata, row by row;
- the 4 duplicate merges;
- the 112 unique and 104 HIGH/MEDIUM proposals, coordinate by coordinate;
- both what-if rows, exactly.

I judged all 138 decisions from the atlas and from zoomed or brightened raw crops. I disagree with no
proposed box or class. Two decisions outside the proposals get a soft disagreement (L4), and neither
changes any number. All 14 single-file tampering attacks fail closed. A coordinated forgery that also
patches the module's embedded notes hash verifies, so the external pins below are the anchor (L1).

The PASS does **not** accept the what-if as evidence that FP/image would pass D-05 (M1). Each
proposal is the model's own box, so each added ground-truth box matches its source prediction at
IoU 1.0 by construction. The 0.293 result is therefore an upper bound on the relabel benefit, with a
margin of 2 FP below the gate.

This PASS authorizes no validation relabel, gate change, R10 replacement, smoke, training,
sealed-test access, commit or push. The manifest records `validation_relabelled=false`,
`gates_changed=false`, `training_authorized=false`, `test_included=false` and
`sealed_test_accessed=false`. I opened no test material.

## Exact reviewed inputs and pins

| Input | SHA-256 | Result |
| --- | --- | --- |
| `detector/m1/val_label_audit_r1.py` | `3826fa57a7cb8d7611c941ce590d7b9f785f4fc23e562842f9aa39c7a99838cf` | matches implementation record; **this QA record pins it** |
| `detector/tests/test_val_label_audit_r1.py` | `c6683f44c481de9b69f8f9afbf55402761f95a0c91e12288eb656123409116d7` | matches implementation record |
| `docs/review/d1_vla_r1_review_notes.csv` | `7fd81195e50992dcf45c0b4fc22499f3a0104a26a8d46e305a1153a4e8d26cec` | matches module `NOTES_SHA256` and record |
| `docs/review/generated/d1_vla_r1_manifest.json` | `3fbbe7fd2b2bc44f632f676cfa60861f963a1cf31b193119c49049e9ed9c2e46` | matches record; **this QA record pins it** |
| D1-EA-R1 predictions CSV | `cb3cb05f0cadc7d2c3e077120d5b1311648247f74a9648e287da1c4be915f1dd` | pin matched |
| D1-EA-R1 manifest (QA L1 anchor) | `d87f090e11d7acc547fb49eeb76935e2e0bcc743f3bc3fba56ab23a1cd8e07ab` | pin matched |
| `detector/m1/error_analysis_r1.py` | `6268c3fec6695fa568ed2f7ac59e824b1aad9fc537cf7df729a7040dd38d8192` | pin matched |
| `docs/review/d1_ea_r1_independent_qa_record.md` | `273c63563634d0ba002b9e5e0c9728e66e638477703715d33f2e80967262d65e` | pin matched |
| `docs/review/d1_ea_r1_hypothesis_correction_r1.md` | `f0c63f99c92f2ac6f0de6bded72af8b41113a63327aa6f89bad8533e75e0d95c` | pin matched |

The 17 artifact digests inside the manifest were confirmed by `verify`, which byte-compares every
regenerated artifact. These are 3 CSVs, 12 atlas pages, the report and the manifest itself.

## Independent re-derivation

The script `qa_vla.py` is in the reviewer scratchpad. It uses plain-Python IoU and containment and
its own greedy class-agnostic matcher at conf ≥ 0.20 and IoU ≥ 0.5. YOLO xywh is converted with the
raw image sizes (376 frames, 39 PNG).

| Quantity | Reproduced | Package |
| --- | ---: | ---: |
| GT / TP / FP (R10 baseline) | 560 / 483 / 214 | 560 / 483 / 214 |
| `OVERLAPS_LABELLED_IOU_GE_0_5` | 66 | 66 |
| `INSIDE_LABELLED_BOX` (containment ≥ 0.6) | 10 | 10 |
| `PARTIAL_OVERLAP_0_1_TO_0_5` | 0 | 0 |
| `NO_LABEL_NEARBY_IOU_LT_0_1` | 138 | 138 |
| Strata rows mismatched (stem, rank, stratum, IoU, containment to 4 dp) | 0 / 214 | — |
| Decisions `UNLABELLED_IN_TAXONOMY` / OOT unlabelled / OOT UNKNOWN / not a sign / unclear | 116 / 9 / 4 / 7 / 2 | same |
| Duplicate merges | V106→V105, V110→V109, V114→V112, V118→V117 | same |
| Unique in-taxonomy / HIGH+MEDIUM proposals | 112 / 104 | 112 / 104 |
| Proposal rows mismatched (stem, key, xywh to 1e-6, source ids) | 0 / 104 | — |
| What-if HIGH/MEDIUM: GT, FP, FP/image, recall, precision | 664, 110, 0.292553, 0.884036, 0.842181 | same |
| What-if incl. LOW: GT, FP, FP/image, recall, precision | 672, 102, 0.271277, 0.885417, 0.853659 | same |

Further checks:

- Only 6 of the 138 have a best IoU above 0, all ≤ 0.015 (1215/3, 1218/3, 1219/1, 1219/3, 1220/1,
  1236/2). No candidate has containment > 0.3, so the IoU < 0.1 cut is not borderline.
- The only near-pair not merged is V050/V051 (IoU 0.948). These are two out-of-taxonomy boxes on the
  same 1219 camera board, correctly not merged, because merging applies only to in-taxonomy rows.
- **Camera boards and the WP38 rotation.** I took the WP33 UNKNOWN rows from
  `wp33_derived_boxes.csv` and rotated them CCW (`x,y,w,h → y,1−x,h,w`) for stems 1319–1357.
  - V070/V071/V072/V073 (1324/1326/1327/1328) reach IoU 0.645 / 0.916 / 0.869 / 0.728 with the
    rotation, and 0.0 without it.
  - 1215–1220 have **no** WP33 UNKNOWN row at all, so V039/V044/V048/V050/V051/V052 are correctly
    `OUT_OF_TAXONOMY_UNLABELLED`.
  - 1321 has an UNKNOWN box, but its IoU with V069 is 0.0. V069 is a different board.
- **Corroboration from labelled neighbour frames**, not cited by the author:
  - GT of 1214–1216 and 1224–1227 labels the left disc 41 (40 km/h) and the right disc 39
    (60 km/h), for example 1214: 41 at x 92–113, 39 at x 117–137.
  - GT 1226–1229 labels the same pole's blue disc 10 and slashed disc 23.
  - GT 1823–1826 labels the P.102/R.302a pair that 1820/1821 miss.
  - GT 1329 and 1331 label the "3.5t" truck disc as class 14.
- **Sensitivity**, diagnostic only:
  - HIGH proposals only (19): FP 195, FP/image 0.519.
  - HIGH/MEDIUM without the 1823–1837 shadow run (89): FP 125, FP/image 0.332.

## Visual review of the 138 decisions

I read all 12 atlas pages. I also rendered my own zoomed and contrast-enhanced crops of the raw
frames (`qa_zoom.py`):

- the shadow run 1823/1825/1826/1830/1834/1837 at 4× brightness;
- the portrait pole 1342/1346/1350/1352/1354/1357 at 8× zoom;
- the 1208/1212/1223/1228 pole;
- the truck discs 1328/1329/1331/1332;
- the residual cases 1330, 0839, 0048, 1321, 1352/1356, and 1827/1834/1220.

| Group (review ids) | Package decision | My judgement |
| --- | --- | --- |
| V001–V005 (0024/0046/0070/0071 "DB cafe" logo), V003 (0048 shop sign), V006 (0313 bus), V008 (0328 back of a disc) | `NOT_A_SIGN` | agree |
| V007/V009 (0327/0329 blue guide boards) | OOT unlabelled | agree |
| V010 (0839, 11 px blur) | `UNCLEAR` | agree |
| V011–V060 pole 1208–1225: 10 / 23 MEDIUM, left disc → 41, right disc → 39 MEDIUM | in-taxonomy | agree. The 1228 zoom reads **40** left and **60** right, and the neighbour GT uses the same 41/39 assignment. The 1208 zoom shows a blue disc above a red-ring slashed disc above a red plate. |
| V055 (1223 "60" HIGH), V061 (1228 left disc → 41 HIGH), V062 (1229 right disc → 39 HIGH) | in-taxonomy | agree. Both discs are legible. V061's p39 is the wrong value. |
| V013/V021/V025/V031/V034 (R.415a HIGH), V053 (1221 edge-cut R.415a MEDIUM) | in-taxonomy 12 | agree |
| V039/V044/V048/V050–V052 (1215–1220 camera boards) | OOT unlabelled | agree. "TUYẾN ĐƯỜNG CÓ GIÁM SÁT, XỬ PHẠT BẰNG CAMERA", with no WP33 row |
| V063/V065 (P.130 HIGH), V064/V066–V068 (P.111a+b HIGH, plate "CẤM XE 02 VÀ 03 BÁNH") | in-taxonomy | agree |
| V069 (1321) | OOT unlabelled | soft disagreement (L4): a hotline/information board, which I would class `NOT_A_SIGN`. No numeric effect. |
| V070–V073 (1324–1328 camera boards) | OOT UNKNOWN-labelled | agree. IoU 0.645–0.916 under the WP38 rotation. |
| V074/V078 (1328/1332 "3.5t" truck disc → 14 MEDIUM) | in-taxonomy | agree with 14 MEDIUM. The zoom reads "> 3.5t" truck with a slash; see L3. |
| V075/V077 (1329/1331 R.415a HIGH) | in-taxonomy 12 | agree. GT starts labelling this board only at 1332. |
| V076 (1330 blue panel with car) | `UNCLEAR` | soft disagreement (L4). It is the R.415a board of 1329/1331, partly occluded by the pole, so it is a real in-taxonomy sign. The box is a sub-panel, so excluding it from the proposals is right. No numeric effect. |
| V079–V116 portrait pole 1342–1357: 10 / 23 MEDIUM | in-taxonomy | agree. The layout is identical to the 1208 pole: two speed discs, two plates, a blue disc, a red-ring disc and a red plate. At 11–14 px the blue disc's X and the red-ring pictogram stay unresolved even at 8× zoom, so the class rests only on the layout analogy. MEDIUM is the ceiling. This does not affect the agnostic what-if. |
| V099/V102/V105/V106/V109/V110/V112/V114/V117/V118 (1352–1357 orange triangle → 0 LOW) | in-taxonomy, excluded | agree. There is a figure in a warning triangle, but W.224 cannot be told from W.225/W.227 at 15 px. LOW and the exclusion are correct. |
| V119/V121 (P.102 HIGH), V120 (R.302a HIGH) | in-taxonomy | agree |
| V122–V126, V128–V134, V136–V138 (1823–1837 shadow run → 10 MEDIUM) | in-taxonomy | agree. At 4× brightness each frame shows a red ring, a blue field and a red X with four blue quadrants, clearest in 1830/1834/1837. This is P.130, not P.131a. It resolves the D1-EA-R1 "unresolved shadow run". |
| V127/V135 (1827/1834 edge P.102 → 2 LOW) | in-taxonomy, excluded | agree. The disc is 7 px wide and cut by the frame edge. |

There are 0 disagreements with a proposed box or class, and 2 soft decision disagreements, V069 and
V076, with no effect on proposals or what-if.

## Fail-closed attacks

The attacks ran on APFS clones under the reviewer scratchpad (`qa_tamper.py`), never in the repo.
Each one used the unchanged module with `repo_root=<stage>`. `build` was never run, on the repo or on
a stage.

| # | Attack | Result |
| ---: | --- | --- |
| 0 | Clean staged copy | `valid=true` |
| 1 | Edit one note text (V001) | **FAIL closed**: pinned notes differ |
| 2 | Proposals CSV first row key 23→10 | **FAIL closed**: artifact differs |
| 3 | Flip one byte of `review_page_07.jpg` | **FAIL closed** |
| 4 | Append to the pinned D1-EA-R1 predictions CSV | **FAIL closed**: pinned source differs |
| 5 | Append to the pinned D1-EA-R1 manifest `d87f090e…` | **FAIL closed** |
| 6 | Append to the pinned D1-EA-R1 QA record | **FAIL closed** |
| 7 | Add `review_page_13.jpg` | **FAIL closed**: unexpected atlas file |
| 8 | Replace `review_page_02.jpg` with a symlink to identical bytes | **FAIL closed** |
| 9 | Delete `review_page_12.jpg` | **FAIL closed** |
| 10 | Manifest `sealed_test_accessed` → `true` | **FAIL closed** |
| 11 | Report FP/image 0.293 → 0.250 | **FAIL closed** |
| 12 | Add a GT box to `labels/val/1208.txt` over V013 | **FAIL closed**: notes no longer cover the candidates exactly |
| 13 | Decisions CSV V074 class 14→18 | **FAIL closed** |
| 14 | Delete the decisions CSV | **FAIL closed** |
| 15 | Coordinated forgery: V076 → 12 HIGH, `NOTES_SHA256` patched in a module copy, everything re-rendered | **`valid=true`** under the forged module (manifest `d96c0512…`, FP/image 0.2899). Under the unmodified repo module the same stage **fails closed**. Only the module pin `3826fa57…` and the manifest pin `3fbbe7fd…` detect it (L1). |

## Verifier, tests and boundary

- `uv run python -m m1.val_label_audit_r1 verify` returns `valid=true`, `errors=[]` (about 1.5 s).
- `pytest -q -p no:cacheprovider tests/test_val_label_audit_r1.py tests/test_error_analysis_r1.py`:
  16 passed. `ruff check` and `ruff format --check` are clean on both D1-VLA-R1 files.
- `graft check .` reports the graph in sync, with the optional deep layer unbuilt (non-blocking).
- `graft grep "d1_vla_r1"` finds no reader outside the builder, so no training or data builder
  consumes the proposals. The atlas is git-ignored (`.gitignore:41`, `/docs/review/assets/`).
- The builder reads only `images/val` and `labels/val`. It writes only the five D1-VLA-R1 outputs and
  the atlas directory, and `build` refuses to overwrite them. No validation label file changed:
  `git status` lists only the 10 untracked package files and, after this review, this record.

## Findings

| ID | Severity | Finding | Evidence | Required action |
| --- | --- | --- | --- | --- |
| M1 | Medium | The what-if is an upper bound presented as a conditional pass. The record says FP/image "would then fall below the 0.30 D-05 gate". The report says recall rises because the added labels are ground truth "that the model must also match". But every added box is the model's own box, so it matches at IoU 1.0 by construction, and the recall gain is an artifact. | Margin 110 vs ≤ 112 FP (2 FP). 28/104 proposals are ≤ 15 px and 52 are ≤ 20 px. A uniform 2 px diagonal redraw offset gives 111 FP / 0.295; 3 px gives 149 FP / 0.396. HIGH-only gives 0.519. | Append a correction that calls 0.293 an upper bound. A relabel decision must re-evaluate with independently redrawn boxes under a QA-passed evaluator. |
| L1 | Low | The notes hash is embedded in the module, so a coordinated rewrite of notes, module and artifacts verifies | Attack 15: forged manifest `d96c0512…` returns `valid=true` | Treat module `3826fa57…` and manifest `3fbbe7fd…` (pinned here) as the anchor |
| L2 | Low | `proposed_val_labels.csv` stores **derived keys**, not YOLO ids. 45/104 rows (keys 23/39/41 → YOLO 25/40/42) would be mislabelled if copied into YOLO label files unmapped. | `m1_yolo_classes.csv`; column `derived_key` | Any relabel must map through `m1_yolo_classes.csv`, in WP33/WP34 style |
| L3 | Low | The "3.5t" disc reads "> 3.5t" truck with a slash, the P.106b form, while class 14 is P.106a. The record omits that the existing GT already labels the same disc 14 on 1329 (388,92,461,163) and 1331 (365,13,460,102), so 14 follows the dataset convention. | zoom crops 1328/1329/1331/1332 | Cite the neighbour GT; route the P.106a/b question to the Track A taxonomy audit |
| L4 | Low | Two soft decision disagreements with no numeric effect | V069 1321: a hotline/information board → `NOT_A_SIGN`. V076 1330: the occluded R.415a board of 1329/1331, so a real sign, with a sub-panel box | Note them in any relabel worklist |
| L5 | Low | 30 portrait-pole proposals (1342–1357) and the 40 MEDIUM pole proposals of 1208–1229 depend on layout and neighbour-frame consistency, not on legible pixels | 11–14 px discs; X and pictogram unresolved at 8× | Keep them MEDIUM and redraw and re-verify them at relabel. No effect on the agnostic what-if. |
| L6 | Low | Unit tests (6) cover `verify` end to end only on the clean package, not byte flips, extra files or symlinks. Atlas bytes depend on Pillow 13.0.0. | `tests/test_val_label_audit_r1.py`; manifest `pillow_version` | Attacks 3 and 7–9 show the behaviour is correct; add tests in a successor; keep `uv.lock` |

## Commands run

```text
graft check . ; graft grep "def unknown_boxes" / "def class_names" / "def frames_from_rows" / "rotat" / "d1_vla_r1"
shasum -a 256 <builder, tests, notes, manifest, 5 D1-EA-R1 pins>
cd detector && uv run python -m m1.val_label_audit_r1 verify                       # valid=true
cd detector && uv run pytest -q -p no:cacheprovider tests/test_val_label_audit_r1.py tests/test_error_analysis_r1.py   # 16 passed
cd detector && uv run ruff check / ruff format --check <2 files>                  # clean
uv run python -I <scratchpad>/qa_vla.py <repo>        # independent strata/dups/proposals/what-if/UNKNOWN
uv run python -I <scratchpad>/qa_jitter.py <repo>     # redraw-offset sensitivity
uv run python -I <scratchpad>/qa_zoom.py <repo> <out> # zoomed/brightened raw crops
uv run python <scratchpad>/qa_tamper.py <scratchpad>  # 16 staged attacks
```

No model was loaded. No inference, `build`, training, relabel, upload, commit, push or sealed-test
access occurred. The only repository change is this new file.

## Bounded next state

| Action | QA disposition |
| --- | --- |
| Treat D1-VLA-R1 (manifest `3fbbe7fd…`) as the validation label-completeness evidence | **YES** |
| Cite 0.293 as "FP/image passes once relabelled" | **NO — upper bound; correct M1 first (append-only)** |
| Owner decision on a derived validation relabel (WP33/WP34 style, redrawn boxes, YOLO-id mapping per L2) | **YES — owner decision; separate QA of the relabel** |
| Replace R10, change any gate, or gate on the what-if | **NO-GO** |
| Use validation pixels, crops, proposals or predictions for training or mining | **NO-GO** |
| Smoke, pilot, new seeds or any training from this PASS | **NO-GO** |
| Open or export sealed test | **NO-GO** |
