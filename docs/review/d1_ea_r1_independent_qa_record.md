# D1-EA-R1 validation error evidence package — independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_PASS_EVIDENCE_PACKAGE__HYPOTHESES_H1_H4_NOT_ACCEPTED_AS_STATED`  
Reviewer: `Claude Code fresh independent QA session (did not author D1-EA-R1)`  
Boundary: `READ_ONLY_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST`

## Verdict

**PASS — 0 Critical, 0 High, 3 Medium and 6 Low findings.**

The PASS covers the evidence package: the builder, its pins, the prediction/missed-GT/atlas-index
CSVs, the 15 atlas pages, the evidence report and the manifest. An independent script that does
not import repository code rebuilt all 376 frames from `d1_ea_r1_predictions.csv` and the
validation label files. It reproduced the R10 operating point, the full 55×55 confusion matrix and
the class-aware hits/support of all 19 gated classes exactly. Atlas coverage is exact. Every
tampering attack failed closed except one coordinated forgery, which only the externally pinned
manifest digest detects (L1).

The PASS does **not** accept the author's hypotheses as written. H1's agnostic-NMS diagnostic
omits that gated class 46 would fall below its gate (M1). H4's class-7 small-object claim is
numerically wrong (M2). The record also does not reconcile the pre-QA inference run with the
packet-R1 QA NO-GO (M3). Correct these in an append-only addendum before any Track A/B contract
cites H1 or H4.

This PASS authorizes no smoke, training, new seeds, NMS change, sealed-test access, model
acceptance, commit or push. `test_included=false`, `sealed_test_accessed=false`,
`training_authorized=false` and `validation_pixels_in_training=false` in the manifest. No test
material was opened during this review.

## Exact reviewed inputs and pins

| Input | SHA-256 | Result |
| --- | --- | --- |
| `detector/m1/error_analysis_r1.py` | `6268c3fec6695fa568ed2f7ac59e824b1aad9fc537cf7df729a7040dd38d8192` | matches implementation record |
| `detector/tests/test_error_analysis_r1.py` | `5373f248bc30090093c5f8a6efd437b6f07f458a28734b63ae85e83ff607704b` | matches implementation record |
| `docs/review/generated/d1_ea_r1_manifest.json` | `d87f090e11d7acc547fb49eeb76935e2e0bcc743f3bc3fba56ab23a1cd8e07ab` | matches brief; **this QA record pins it** |
| R10 report `…_r2/eval_val_wp38_r1_r4_r10.json` | `b33e247038c237d059207f75ad8ff33e0b5d6d00e4380826cd35ae85aefa02d5` | pin matched (file mode `0400`) |
| Weights `…_r2/weights/best.pt` | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` | pin matched |
| `detector/m1/corrected_val_r10.py` | `5897e951244a5e8761bda7202779fe30acb0d5da085686d49c96a04f69e5dfd3` | pin matched |
| `detector/m1/corrected_val_r1.py` | `0e56949d4a8e01b01a3de509f982ecbb4d0fd4ec1b44ef51975b47621289b8e5` | pin matched |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` | pin matched |
| `docs/review/generated/m1_yolo_classes.csv` | `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242` | pin matched |
| R10 result QA record | `9940b31c344e9e683d0bd3d6ddc25b8a31053bbeb83398801637be08df2d06a2` | pin matched |
| Error-analysis packet R1 | `9ec8dd0d9e2866ef098ca3afada624ea5562837531f9b077981c45940ed0f78f` | pin matched |
| Packet R1 QA record | `c4b8fa62bd158ba4f300b28cf14bb9c4d8f1147dbf410e4a57582f70fb565942` | pin matched |

The 19 artifact digests inside the manifest were confirmed by `verify`, which byte-compares every
regenerated artifact. `corrected_val_r10.verify_corrected_data()` also passed: 376 validation
frames, 39 corrected frames and `test_included=false`. It took 155 s and changed nothing in
`git status`.

## Independent reproduction of R10

The reproduction script is in the reviewer scratchpad, outside the repository. It uses plain Python
IoU and its own greedy matcher, with no `m1` import. Image sizes come from the raw files, and labels
are converted from YOLO xywh to pixel xyxy.

| Quantity | Reproduced | R10 |
| --- | ---: | ---: |
| Images | 376 | 376 |
| Ground-truth boxes | 560 | 560 |
| Class-agnostic TP (PAIRED) | 483 | 483 |
| FP (BACKGROUND) | 214 | 214 |
| Unmatched GT | 77 | 77 (matrix background column) |

- Confusion matrix: equal to `confusion_matrix.rows_gt_cols_pred` cell for cell, labels equal
  `[*derived_keys, "BACKGROUND"]`. SHA-256 of `json.dumps(matrix)` is
  `6f932feb6741eb8014c8ee5213d5cf38a4a122f4ec839e61ef0f0df0a76cf665`, as the manifest records.
- Class-aware hits/support: all 19 entries of `gates.classes` match, with no exceptions, including
  7 = 66/111, 32 = 18/29, 41 = 12/21, 46 = 55/104 and 8 = 32/51.
- Per-row disposition, `gt_index`, `gt_class` and IoU (to 4 dp): 0 mismatches over 697 rows.
- Minimum exported confidence 0.2023 (≥ 0.20); ranks are dense `0..n-1` per stem and
  non-increasing in confidence; no duplicate `(stem, pred_rank)`; 0 image-size mismatches.
- Missed-GT set: 77 rows, equal as a `(stem, gt_index)` set to my unmatched GT.

## Completeness and boundary

- 697 prediction rows = 483 `PAIRED` + 214 `BACKGROUND`, each exactly once.
- Every prediction stem is among the 376 `images/val` stems; validation ∩ `images/train` stems = ∅.
  No test path was read.
- The builder writes only to `docs/review/generated/d1_ea_r1_*`, `docs/review/d1_ea_r1_evidence_report.md`
  and `docs/review/assets/d1_ea_r1/` (`error_analysis_r1.py:713-716`). `graft grep "d1_ea_r1"` finds
  no other reader, and no training builder reads `docs/review/assets/`. The atlas directory is
  git-ignored (`.gitignore:41`).
- `ruff check` and `ruff format --check` pass on both files. `verify` returns `valid=true` (about
  1.4 s), and `pytest -q -p no:cacheprovider tests/test_error_analysis_r1.py` passes 10/10.
- `graft check .` reports the graph is in sync; the optional deep layer is unbuilt (non-blocking).

## Atlas coverage and visual check

| Category | Index entries | Expected from CSVs | Exact set match |
| --- | ---: | ---: | --- |
| `background_fp` | 214 (8 pages) | 214 BACKGROUND rows | yes |
| `critical_7` | 49 (2 pages) | 13 wrong-class + 36 missed | yes |
| `critical_32` | 11 | 6 + 5 | yes |
| `critical_41` | 10 | 8 + 2 | yes |
| `pair_46_to_10` | 58 (2 pages) | 58 | yes |
| `pair_8_to_12` | 6 | 6 | yes |

All 348 index captions agree with the stem, class and `gt_index` of their prediction rows. I read
12 of the 15 pages myself: background-FP pages 01–08, both `critical_7` pages, `critical_41`, and
`pair_46_to_10` page 01. In every tile I checked, the box and caption matched the CSV.

I also redrew boxes directly from the CSVs onto the raw images with my own code, for 1827 (ranks
0/1/3), 1828 (rank 0), 1212 (ranks 0/1/2/3/5), 0279 (missed gt 0/2), 0345 (missed gt 0) and
0313 (rank 2). They agree with the atlas tiles, including the edge-truncated P.102 box of 1827
rank 1 at x = 0–7 px.

Note: `critical_<c>` follows the diagnostic agnostic pairing, as the report states. It therefore
includes 5 GT boxes that are class-aware gate hits: class 7 stems 0314, 0338, 0339, 0341 and class
41 stem 1947. Gate misses are 45/11/9, while the atlas holds 49/11/10.

## Fail-closed attacks (staged copies in the reviewer scratchpad, never in the repo)

Each attack ran on a fresh APFS clone of exactly the files that `verify` reads, using the unchanged
module with `repo_root=<stage>`.

| # | Attack | Result |
| ---: | --- | --- |
| 0 | Clean staged copy | `valid=true` |
| 1 | Change conf of prediction row 1 (+0.01) | **FAIL closed**: manifest differs |
| 2 | Flip one row PAIRED→BACKGROUND (0001 rank 0) | **FAIL closed**: predictions CSV differs |
| 3 | Delete one BACKGROUND row | **FAIL closed**: `false_positives: 213 != 214; confusion matrix differs from R10` |
| 4 | Flip one byte of `critical_7_page_01.jpg` | **FAIL closed**: artifact differs |
| 5 | Add `critical_7_page_03.jpg` | **FAIL closed**: unexpected atlas file |
| 6 | Replace `critical_41_page_01.jpg` by a symlink to identical bytes | **FAIL closed** |
| 7 | Delete `pair_8_to_12_page_01.jpg` | **FAIL closed** |
| 8 | Append to the pinned R10 result QA record | **FAIL closed**: pinned source differs |
| 9 | Edit R10 report (`false_positives` 214→213) | **FAIL closed**: pinned source differs |
| 10 | Manifest `test_included` → `true` | **FAIL closed**: manifest differs |
| 11 | Move one GT box in `labels/val/0001.txt` | **FAIL closed**: predictions CSV and manifest differ |
| 12 | `build` over existing outputs | **refused**: `outputs already exist; the package is append-only` |
| 13 | `build` with only the atlas directory present | **refused** (same message) |
| 14 | Coordinated forgery: 0001 rank-0 `x1` +0.5 px, then regenerate every artifact with the package's own `render` | **`valid=true`**: forged manifest `e81ce086…`. Only the external pin `d87f090e…` detects it (L1) |

`build` was never run against the repository. Both refusals happened before any model load.

## Hypotheses in the implementation record

My own numbers come from the exported CSVs, the labels, the atlas and raw-image crops.

**H1: duplicates (66/214) — numbers reproduce; framing incomplete (M1).** 66/214 = 30.8 % of
background FPs have IoU ≥ 0.5 with an already-paired GT. Comparing each with the paired box it
overlaps most (65 of the 66 overlap one at IoU ≥ 0.5):

- 11 are same-class duplicates, for example 1240–1245 and 1350–1357 (p12 next to paired p12);
- 29 carry another wrong class, for example 1231–1235 (p30 on an R.415a board) and 0003/0065/0068
  (p10 next to paired p46);
- 25 carry the **correct** GT class while the higher-scoring paired box is wrong. Among them:
  - 0004, 0019, 0030, 0041, 0044, 0047, 0053, 0055: p46 behind a paired p10;
  - 0314: p7 behind p18;
  - 0338, 0339, 0341: p7 behind p17;
  - 0334, 0335: p8 behind p12;
  - 1721: p4 behind p5.

The agnostic-NMS diagnostic reproduces as stated: at IoU 0.7, FP/image 0.4335; at IoU 0.5,
0.3777; agnostic recall stays 0.8625; class 7 falls 0.595→0.559 and class 41 0.571→0.524. The
record omits two more drops:

- gated class 46 falls from 55/104 = 0.5288 to 42/104 = 0.4038, below the non-critical 0.50 gate;
- class 8 falls from 0.627 to 0.588.

So agnostic NMS alone trades one failing gate (FP/image, still above 0.30) for a newly failing
one (class 46). It mainly suppresses exactly the 25 correct-class boxes listed above. It is also an
approximation: re-NMS of already class-wise-NMS'd boxes at conf ≥ 0.20 is not Ultralytics
`agnostic_nms=True` on the raw candidates.

**H2: many no-GT-nearby FPs are unlabelled real signs — supported as hedged, needs a split (L3).**
The record does not define "138". It equals best IoU < 0.1 with any GT; 132 have IoU exactly 0.
Within those 138, the atlas shows many in-taxonomy real but unlabelled signs:

- P.130, P.111a+b and P.127 40/60 discs in 1208–1229 and 1342–1357;
- P.102 in 1820, 1821, 1827 and 1834.

1212 and 1820 are as described. But the same 138 also contain:

- out-of-taxonomy real boards: camera-surveillance boards 1215–1220 and 1324–1328 (p12/p30), and
  the phone board 1321;
- true non-sign FPs: the "DB cafe" logo 0024/0046/0070/0071 (p39), the bus in 0313 (p12) and the
  shop sign in 0048 (p5);
- an unresolved run, 1823–1837 p10, in deep shadow (conf 0.44–0.91), where I could not confirm a
  sign even at 3× brightness.

The P.131a FPs (0041–0055, 0721–0741) and the bus-stop FPs (0323, 0332–0335) are not in the 138.
They lie next to a labelled GT and belong to H1.

A label-completeness audit must separate these classes of cause before any FP/image re-estimate.

**H3: class 12 sub-panel boxes — supported.** 1240–1245 and 1350–1357 show p12 boxes on one or
two panels of an R.415a board labelled as a whole. p30 (S.505a) also fires on the same boards
(1231–1243).

**H4: class 7 — factually wrong as stated (M2).** The 36 class-7 misses are not
"in one sequence (0279–0296)". Only 17 are there (GT width 11–17 px), plus 0301 (14 px).
The other 18 are:

- 17 in 1777–1798, mid-size at 25–46 px, dark and backlit;
- 0345, large (114 px) and clearly visible;
- 1817 and 1818, large (98 and 110 px) and backlit.

Small size explains at most 18 of 36. The taxonomy caveat is well founded: my 0345 crop shows a
motorbike pictogram with a left-turn arrow under the slash. This is the same sign that 0336–0346
predict as 17 (P.124a).

## Findings

| ID | Severity | Finding | Evidence | Required action |
| --- | --- | --- | --- | --- |
| M1 | Medium | H1 reports agnostic-NMS gains and "slight" class 7/41 losses, but omits that gated class 46 falls below its 0.50 gate and class 8 also drops. It also omits that 25/66 "duplicates" are the correct-class box. | 46: 55/104 → 42/104 at both NMS IoU 0.7 and 0.5; 8: 0.627→0.588; stems listed in H1 above | Append correction; any NMS contract must gate per-class recall, not only FP/image |
| M2 | Medium | H4 misstates the class-7 miss structure | 17/36 in 0279–0296; 17 in 1777–1798 at 25–46 px; 0345/1817/1818 at 98–114 px | Append correction before Track A cites small-object limits |
| M3 | Medium | `build` (MPS inference) ran before implementation QA, although the packet-R1 QA record says "Execute D1-EA-R1 validation inference: NO-GO until the exact implementation passes independent QA". The record cites only the Owner's device choice (handoff item 3). | `d1_corrected_val_r10_error_analysis_r1_independent_qa_record.md`, Bounded next state | Append Owner authorization or acknowledgement. Impact is contained: validation-only, exact R10 reproduction, no train/test. |
| L1 | Low | `verify` regenerates the manifest from the CSV it checks, so a coordinated rewrite of all artifacts verifies | Attack 14: forged manifest `e81ce0868eee9763f13ef08c408014e8784aa9cef2e4e79a76063dc0bc391d5c` returns `valid=true` | Treat `d87f090e…` (pinned here) as the anchor; a successor verifier should compare it |
| L2 | Low | `missed_gt.csv` `best_retained_class` names the first retained prediction when every IoU is 0 | All 77 misses have IoU 0.0000; 50 still carry a class, for example 0279 gt 0/2 → `6` | Blank the class when IoU = 0 in any successor. All 77 misses are total non-detections. |
| L3 | Low | H2's "138" is undefined, and the population mixes in-taxonomy unlabelled signs, out-of-taxonomy boards, true non-sign FPs and an unresolved shadow run | See H2 above | Define the IoU < 0.1 cut and stratify the label audit |
| L4 | Low | Weights directory is untracked but not git-ignored | `git status`: `?? …_r2/weights/` (`best.pt` 76 MB and `last.pt`); `git check-ignore` returns no rule | Add an ignore rule or take care with `git add` (not changed by this QA) |
| L5 | Low | Unit tests do not exercise `verify()` end to end (byte flip, extra atlas file, symlink) | `tests/test_error_analysis_r1.py`: 10 synthetic tests | Attacks 4–7 above show that the behaviour is correct; add tests in a successor |
| L6 | Low | Atlas JPEG bytes depend on Pillow 13.0.0 / libjpeg. `verify` fails closed on another environment rather than silently passing. | `manifest.pillow_version` | Keep `uv.lock`; informational |

Observation, not a finding: the 46→10 pair is P.131a (single slash) predicted as P.130 (cross).
The two are near-identical at 0002–0039 resolution. The 41→39/40 confusions are within the P.127
40/60/80 family (1214–1227, 1945, 1947). Both are consistent with the packet's Track A taxonomy
audit list.

## Commands run

```text
graft check . ; graft skeleton detector/m1/metrics.py ; graft grep "d1_ea_r1" ; graft grep "review/assets"
shasum -a 256 <all 9 pins, builder, tests, manifest>
cd detector && uv run python -m m1.error_analysis_r1 verify                      # valid=true
cd detector && uv run pytest -q -p no:cacheprovider tests/test_error_analysis_r1.py   # 10 passed
cd detector && uv run ruff check / ruff format --check <2 files>                 # clean
cd detector && uv run python -c "corrected_val_r10.verify_corrected_data()"     # 376 val, 39 corrected
uv run python -I <scratchpad>/qa_repro.py <repo> <scratchpad>    # independent reproduction
uv run python -I <scratchpad>/qa_hyp.py <repo>                   # hypotheses, agnostic NMS
uv run python -I <scratchpad>/qa_redraw.py <repo> <scratchpad>   # raw-image box redraws
uv run python <scratchpad>/qa_tamper.py <scratchpad>             # 15 staged attacks
```

No model was loaded. No inference, `build` against the repository, training, upload, commit, push
or sealed-test access occurred. The only repository change is this new file.

## Bounded next state

| Action | QA disposition |
| --- | --- |
| Treat D1-EA-R1 artifacts (manifest `d87f090e…`) as the validation error evidence | **YES** |
| Cite H1 agnostic-NMS numbers or H4 small-object claim as written | **NO — correct M1/M2 first (append-only)** |
| Freeze a post-processing (NMS) contract | **Only with per-class gates incl. 46; separate QA** |
| Validation label-completeness audit (derived relabel, WP33/WP34 style) | **YES — stratified per L3; separate QA** |
| Use validation pixels/crops/predictions for training or mining | **NO-GO** |
| Smoke, pilot, new seeds or any training from this PASS | **NO-GO** |
| Open or export sealed test | **NO-GO** |
