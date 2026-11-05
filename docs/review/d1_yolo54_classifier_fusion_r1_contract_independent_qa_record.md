# D1 YOLO54 + CompactCNN classifier fusion R1 — contract independent QA record

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Reviewer: Claude Code (Opus 5.5), independent side session; not the contract author.
Scope: **contract review only**. No fusion was implemented or executed. The classifier was not run on any
detector crop, no YOLO or classifier inference ran, nothing was trained, and no fusion metric was computed or viewed.
Reviewed contract: `docs/review/d1_yolo54_classifier_fusion_r1_contract.md`, SHA-256
`40cbe72ff095b8aea9d2253c02a52c013797b2148febc4bbbd647e68a77c700c` (it matches the handoff value).
Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, branch `yolo11n-dual-track-r1`, HEAD `5e3fa2a`.

Verdict: PASS giới hạn — the evidence pins, class-map alignment, pair derivation, FP invariant, crop rule and Step 0 references are all correct. Before Owner authorization of execution, a QA'd addendum or successor must fix one guard gap (C1) and the outcome-precedence ambiguity (C2). C3–C8 are recommended corrections.

`sealed_test_accessed=false`

## Start-of-task state

- `AGENTS.md` and `PROJECT_MEMORY.md` (head) were read. `graft check .` returned `graph check: OK — the wiring graph is in sync with the code`; the deep layer is not built.
- `git log --oneline -3`: `5e3fa2a docs(review): R3 addendum — A3 executed via D1-A3-R2, criteria not met`; `724bf0c …`; `02ed548 …`.
- `git status --short | head -60` showed 12 ` M` Owner files: `PROJECT_MEMORY.md`, `docs/product_roadmap.md`, `docs/review_index.md`, `scripts/run_parallel_checks.py`, five `src/cpv301_autodrive/*` files and three `tests/*` files. It also showed many `??` files (detector/colab, detector/m1, detector/tests …). At the end the same 12 ` M` files remain. This record is the only file this review created in the repository.
- Files whose name contains `a3_pilot_paired_ci` were not opened.

## F1–F10 summary

| # | Check | Result | Key evidence |
| --- | --- | --- | --- |
| F1 | Evidence pins and cited line ranges | **PASS** | All 33 files in §10 rehash OK (`shasum -a 256 -c`). The cited ranges say what the contract claims (details below). Minor gaps: `data.py` is cited in §5 but not pinned (C4), and the RGB conversion is at evaluator lines 174–175, outside the cited 46–66 (C4). |
| F2 | Class-map alignment (§3) | **PASS** | `m1_yolo_classes.csv`, `signnames.csv` and `data.yaml` agree on 54/54 rows on every field. The translation table is correct. A recount from 376 label files and 624 boxes confirms every support count in the table. |
| F3 | Pair derivation (§4.1) | **PASS** | There are exactly six non-background off-diagonal cells ≥ 5, matching P1–P6. Direction is correct (source = predicted, target = GT). The excluded list is complete. Excluding background is justified. §7 discloses the validation reuse. |
| F4 | Rule F1 and FP invariant (§2, §4.2) | **PASS** (notes C5) | Agnostic `match` ignores classes and sorts by score (stable), so relabel-only keeps TP 547 / FP 150. There is no chaining, and P2/P4 is safe. The τ boundary dtype is unspecified (C5). Same-class overlaps are disclosed. No source-class row in the pilot CSV is degenerate. |
| F5 | τ = 0.80 (§4.3) | **PASS** | The "no held-out split" claim is true per the combined result QA record. τ is fixed by convention without any fusion result. The grid and leave-one-out are descriptive and cannot change the verdict. |
| F6 | Crop rule (§5) | **PASS giới hạn** (C4) | Border, rounding, clipping, bilinear 32×32 and `(x/255−0.5)/0.5` match the evaluator and `data.py:21-23`. The validity predicate must be stated as the evaluator's clip-then-filter (lines 192–195) followed by `crop_bounds`, which raises on an out-of-range box. |
| F7 | Decision rule (§6) | **PASS giới hạn** (C1, C2, C6) | Step 0 references are exact. The G2 feasibility note is correct. G4/G5 can be evaluated. **Gap:** DK 39 (yolo_id 40, critical, 14/15 hits) is the P3 source class but has no guard. **Ambiguity:** the outcome mapping overlaps when Δ > 0, G1/G2 fails and G4/G5/G6 also fails. |
| F8 | Latency protocol (§6.4) | **PASS giới hạn** (C3) | Setup matches SAHI §1.5 (lines 68–71). Alternating arms within each iteration addresses SAHI QA C5. The fixed A→B order leaves a position and page-cache bias. "Identical to SAHI R1 §1.5" overstates, because the order control is new. |
| F9 | Boundaries, validation reuse, outputs/QA order, unknowns | **PASS** (C7, C8) | No D-05, promotion or app overreach. GO is only a candidate. **U2 should be downgraded:** the bundle exists at `tmp/yolo11n_n1_extract_r1/`, all 8,579 manifest members verify, labels are byte-identical to R3, and a pinned N1 comparison JSON already reproduces the Step 0 AP. |
| F10 | Gates | **PASS** | `uv run ruff check src tests` → `All checks passed!` (exit 0); `uv lock --check` → `Resolved 201 packages`, exit 0. |

## Detailed findings

### F1 — evidence pins and citations

`shasum -a 256 -c` on all §10 entries (33 files; the run_contract/args.yaml row holds two files) returned `OK` for every file. Citation readback:

- `next_direction_proposal_2026-11-04.md:16`: the row "Ghép YOLO54 với classifier Cascade ở nhóm lớp dễ nhầm" lists the safeguards the contract restates: pre-registered pairs, both checkpoints and class maps, the crop/fusion rule, the same validation set and FP budget, an independent scene group, scorer QA before results, offline only.
- `cascade_classifier_improvement_r2_report.md:54-61`: the table gives R2 combined S1 0.4783/0.3310 vs frozen 0.4120/0.3050, and N1 0.4500 vs 0.4000. Lines 80–86 give FP/frame +0.0133 (S1) and +0.0027 (N1), plus the "neither … establishes a production model" boundary. Lines 88–93 hold the comparison gate the combined variant meets.
- `vgg16_54_r4_validation_comparison_report.md:74-86`: CompactCNN beats VGG16-54. YOLO54 on the same scorer is 0.8521/0.6089. Lines 103–105 label the VRE-R2 0.8839/0.6261 as a different path.
- `d1_vre_r2_result_report.md:41-49`: TP/FP 547/150, FP/image 0.3989, recall 0.8766. Lines 68–92 give per-class hits 66/111, 18/29, 12/26, 55/104 and 8/12/34/6/10/23, and the confusion prose (10 as 17, 2 as 18; 6 of class 32 as 7; 7 as 39 and 6 as 40; 46→10 = 58).
- `sahi_r1_validation_report.md:121-128`: 547/457/150 baseline and 612 GT with any candidate. Lines 168–173: full-frame p95 54.4 ms. Lines 197–201: the bottleneck is score/class selection, not missing candidates. Lines 68–71: the latency protocol.
- `cascade_b0_r1_validation_comparison_report.md:11-12`: 0.8520835680 / 0.6088678435.
- R3 contract lines 165–168 record the 9-group coarseness. R3 addendum line 55 records the two-argument A3 mistake.
- Combined result QA record: 12,621 train crops; the corrected validation pickle is "the sole selection set"; best epoch 18, macro-F1 0.5579711826, top-1 `0.625`.

### F2 — class maps and support

A script read the three maps without loading any model. Result: `rows 54 54 54`, `mismatches 0`, checking yolo_id == ClassId == row index, derived_key == DerivedKey, derived_code == QCVN, name_vi == SignName, `data.yaml` name == `"<DerivedKey> <QCVN>"`, and `m1_yolo_classes.name` == that name. Derived keys first differ from yolo_id at 16 (`16:2.0`). DK 31 does not exist, so the offset is 2 for yolo 19–32, 1 for yolo 33–43, and 2 again from yolo 46. The contract's 11-row table is correct, including the speed values (`signnames.csv` rows 40/41/42 = 60/80/40 km/h).

Recount from `data/processed/m1_yolo_val_vrl_r3/labels/val/`: 376 files, 624 boxes, 19 supported classes. yolo 7:111, 8:51, 10:48, 12:65, 19:0, 20:0, 33:29, 40:15, 41:0, 42:26, 48:104, and 32 (S.505a):0. All match the table.
Note: the pilot's `args.yaml` names the Colab path `/content/…/data/processed/m1_yolo/data.yaml`, and `run_contract.json` pins no hash for it. The local `data.yaml` (`4cd83035…`) is a regeneration. Alignment does not depend on it, because `m1_yolo_classes.csv` is pinned by `val_reeval_r2.py:94` and D1-VRE-R2.

### F3 — pairs

These are the non-background off-diagonal cells of `primary_r3.confusion_matrix.rows_gt_cols_pred` with count ≥ 5 (labels are derived keys and the index is yolo_id):

| GT (DK) | Pred (DK) | Count | Source yolo → target yolo | Contract |
| --- | --- | ---: | --- | --- |
| 46 | 10 | 58 | 10 → 48 | P1 |
| 7 | 17 | 10 | 19 → 7 | P2 |
| 41 | 39 | 7 | 40 → 42 | P3 |
| 8 | 12 | 6 | 12 → 8 | P6 |
| 41 | 40 | 6 | 41 → 42 | P5 |
| 32 | 7 | 6 | 7 → 33 | P4 |

There are exactly six, and the direction is right. Excluded non-background cells of 2–4: 7→18 (2), 4→5 (4), 14→23 (4), 26→0 (3), 34→23 (2). The singletons are 7→49, 4→1, 4→0, 34→36, 12→8, 12→30, 12→10. This matches the contract's excluded list.

Background justification: a GT→BACKGROUND cell has no agnostically paired candidate at 0.20 to relabel. A BACKGROUND→pred cell is an FP that relabel-only cannot remove (§2). Excluding background cells is therefore principled for a relabel-only rule. §7 explicitly lists "the derivation of F1's pairs from the pilot's validation confusions" as validation reuse.

Observation (non-blocking; uses only the published reference): the matrix diagonal sums to 432, while class-aware hits are 457 and agnostic TP is 547. So 115 GT are agnostically paired with a wrong-class box, and about 25 of those are nonetheless class-aware hits through another box. Cell counts therefore overstate achievable help. They are a pair-selection signal, not an upper bound on gain.

### F4 — rule F1 and FP invariant

`metrics.match` (lines 50–72) keeps boxes with score ≥ conf and orders them by `argsort(-scores, kind="stable")`. With `class_aware=False` the class filter at line 66 is skipped. `operating_point` (lines 90–115) takes TP and FP only from the agnostic call, and per-class hits from the class-aware call. Relabel-only with unchanged boxes, scores and row order therefore must give TP 547, FP 150, FP/image 0.398936 and recall 0.876603. G3 is a correctness check, not a result. Row order matters only through stable tie-breaking, and §8 keeps the pilot CSV order.

Loophole review:

- **Chaining.** F1 keys on the original class, at most once per candidate. Safe.
- **P2/P4 overlap (yolo 7).** A 19→7 relabel is not re-examined. A class-7 box may go to 33. G4 guards class-7 hits. Safe.
- **P3/P5 share a target.** Decisions are per candidate. Safe.
- **Ties at τ.** `p[t] ≥ 0.80` already implies a unique argmax, so the argmax clause is redundant but harmless. The comparison dtype is unspecified: float32 0.8f = 0.800000011920929 ≥ double 0.8. See C5.
- **Invalid crops.** In the pilot CSV, 18 rows fail `0≤x1<x2≤960, 0≤y1<y2≤540`, all yolo_id 47, which is not a source. Zero source rows are invalid, so `crop_invalid` should be 0. The predicate wording still needs C4.
- **Same-class overlaps after relabel.** They are kept, count against AP, and are reported at IoU ≥ 0.70. Disclosed.
- **Scale claim (CSV-only, no GT matching).** 798 source rows. 350 at conf ≥ 0.20, in 235 images, at most 5 per image. Confirmed.

### F5 — τ

The combined result QA record ("Bound authority and data") states that all 12,621 train crops trained the model and that the 624-crop validation pickle is the sole selection set. No held-out split exists, so the claim is true. τ = 0.80 is a convention (4:1 odds), not derived from any fusion output. The quoted top-1 0.625 is consistent with the record, and the contract says it is for scale only. That the author did not consult per-class GT-crop accuracy (U3) is an assertion this QA cannot verify, but no artifact in §10 contains fusion output. §4.3 bars the grid {0.50, 0.95} and leave-one-out from changing the verdict or from adoption. The intersection–union argument for the conjunctive guards is correct. The primary test is effectively one-sided at α = 0.025, through the 95 % percentile lower bound.

### F6 — crop rule

`evaluate_cascade_b0_r1.py:46-59` (`crop_bounds`): border `max(5, 0.1·w|h)`, `floor/ceil(round(·,6))`, clipped. Lines 62–66: `Image.crop`, then `resize((32,32), BILINEAR)`, `uint8`. Lines 164–168 and 200–203: `/255`, then `(x−0.5)/0.5`, then `softmax(·,1)`. This matches `d1_cascade_classifier/data.py:21-23` (SHA-256 `e55fbaddea154131a0ef20f8d2653150b0f2c8eecdc8ff31dbcb16d6a463ed5d`, not pinned in §10). The RGB conversion is at lines 174–175. `evaluate_compact_improvement_r2.py:93` calls `common.infer`, so the published R2 cascade results used this exact crop path.

Difference to resolve (C4): `infer` clips YOLO boxes to the image and drops non-finite or non-positive-extent boxes before cropping (lines 192–195). `crop_bounds` then **raises** `ValueError` unless `0≤x1<x2≤W, 0≤y1<y2≤H`. The contract's "non-finite or zero width/height after clipping → unchanged, `crop_invalid`" has the same meaning only if the implementation clips the raw box first and treats a `crop_bounds` ValueError as `crop_invalid`. This has no practical effect on this CSV (zero invalid source rows), but the predicate should be bound exactly.

Also, the B0 evaluator loads its CompactCNN with `weights_only=False` from `run_cascade_b0_r1`. The contract uses `d1_cascade_classifier/model.py` with `weights_only=True`, which artifact QA showed works. Step 3 source QA should confirm the state-dict keys load with no remapping.

### F7 — decision rule

- **Step 0.** These values are exact against artifacts: TP 547, FP 150, recall 0.8766025641, FP/image 0.3989361702 (VRE-R2 JSON `fixed_conf_0_20.operating_point`); Σ per-class hits = 457 over 19 classes; DK 7/32/41/46 = 66/18/12/55. Common-path 0.8520835680058519 / 0.6088678434901063 appear in `cascade_b0_r1` report lines 11–12 and also in `yolo11n_n1_seed_20261018_r1_r1/evaluation_r1/comparison_n1_r1.json` (`0447a1bd…`; see F9).
- **G1–G7.** These are internally consistent. G1 (≥ 467) implies Δ > 0. G3 is implied by §2. G5's second clause is implied by its first for every G5 class (worst case DK 8 at 30/51 = 0.588 ≥ 0.50; DK 46 at 53/104 ≥ 0.50), so it is redundant but harmless.
- **G4/G5 evaluability.** Both can be evaluated from `operating_point.per_class_hits` (yolo_id keys) through the §3 translation. The D-05 per-class references (0.70 critical, 0.50 others) and A's `passed` flags are in the VRE-R2 JSON `gates`.
- **G2 feasibility.** Recomputed from the R3 labels and `wp36_r1_split_frames.csv`: the target classes lie in 6 of 9 groups. yolo 8 is only in C0009, yolo 33 only in C0020, yolo 7 in C0009/C0044, yolo 42 in C0031/C0045, and yolo 48 in C0001/C0020. P(resample misses 2 given groups) = (7/9)^9 = 0.104. The note is correct.
- **C1 (required).** DK 39 / yolo 40 (P.127 60 km/h) is the source class of P3: 71 CSV rows, 25 at ≥ 0.20. Its A hits are 14/15, and the VRE-R2 JSON marks it `critical: true`. Because its support of 15 is below 20, it falls outside both G4 and G5. Only G1 (net) and G6 (AP) would register harm. A pre-registered guard is needed, for example "hits_B(DK 39) ≥ 14" or "loses ≤ 1".
- **C2 (required).** The outcomes overlap. If Δ > 0, G1 or G2 fails, and G4/G5/G6 also fails, the case is both `NO_GO_UNCERTAIN` and `NO_GO`. A precedence must be fixed, for example `INVALID` > `NO_GO` > `NO_GO_UNCERTAIN` > `NO_GO_LATENCY` > `GO_CANDIDATE_FOR_CONFIRMATION`. It should also state that G7 is measured regardless of the accuracy outcome. Otherwise the mapping covers every case.
- **C6 (recommended).** §8 step 3 says the "paired bootstrap at Δ = 0 equals `metrics.group_bootstrap`". `group_bootstrap` (lines 298–317) returns CIs only for agnostic recall and FP/image. Proposed wording: with the same seed and `rng.choice(sorted(groups))` draw sequence, the paired implementation's arm-A agnostic-recall and FP/image CIs equal `group_bootstrap(frames_A, 0.20)` exactly, and an arm B identical to A gives Δ CI [0, 0].

### F8 — latency

SAHI R1 §1.5 (lines 68–71) specifies M1 Pro MPS, batch 1, 50 warm-up and 300 measured, `mps.synchronize` each iteration, validation-order cycling, conf 0.20, iou 0.70, imgsz 1280, p50/p95. §6.4 matches this. SAHI QA C5 (`sahi_r1_independent_qa_record.md:17`) says the two arms were measured serially with a fresh model, so order and thermal effects were not excluded. §6.4's within-iteration alternation in one process addresses the drift part.

**C3 (recommended).**

- Arm A always runs first within an iteration, so arm B reads an image the OS has just cached. Counterbalance the order (ABAB/BABA by iteration parity, or a seeded random order) and report the order per sample.
- Change the heading "identical to SAHI R1 §1.5" to "SAHI R1 §1.5 plus order control".
- §1 forbids YOLO inference only "for the accuracy arm". State explicitly that the latency arm runs live YOLO and classifier inference on MPS, and that this falls within the execution authorization being requested.

### F9 — boundaries, reuse, outputs, unknowns

- **Boundaries.** §1 and §7 forbid D-05, threshold, app and vehicle use. `GO_CANDIDATE_FOR_CONFIRMATION` is explicitly "never a D-05 pass". There is no overreach.
- **Validation reuse.** §7 lists the R3 audit bias, dynamic thresholds, SAHI, temporal DT, classifier epoch selection and pair derivation. **C8 (minor):** §7 should also list the choice of the R2 *combined* variant over the other R2 variants by the validation cascade gate; §3 points to §7, but §7 does not name it.
- **Outputs and QA order.** `O_EXCL`, a model-free `verify`, both keys in every output, and no fusion number before step 3. Sound.
- **U2 (C7, downgrade recommended in an addendum).** This review verified the coordinator's finding:
  - `tmp/yolo11n_n1_extract_r1/manifest.json` SHA-256 = `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`. This is the N1 bundle named in the combined result QA record.
  - All **8,579/8,579** manifest members rehash OK, none missing.
  - `data/yolo54_predictions_val.csv` = `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893`, the same as the run-directory CSV.
  - `diff -rq tmp/…/data/labels54/val data/processed/m1_yolo_val_vrl_r3/labels/val` shows no difference (376 files each).
  - `data/val_groups.json` gives the same group as the WP36 split file for all 376 stems (9 groups).
  - `comparison_n1_r1.json` (`0447a1bd…`, `bundle_manifest_sha256` = `8e6ffe77…`, and the `N1_REFERENCE_SHA256` pinned in `evaluate_compact_improvement_r2.py:34`) already records `yolo54_common_method` exact-class mAP50 0.8520835680058519, mAP50-95 0.6088678434901063, TP 547, FP 150.

  U2 should be downgraded from "bundle not found / possibly blocked" to "bundle located and verified; Step 0 still mandatory". The addendum should pin the manifest, the N1 comparison JSON and the label equality, and should say whether the executor may use the bundle as `root` for the common-path AP. The bundle lives under the untracked `tmp/`, so its hash must be re-verified at execution.
- **U1 and U3–U6.** These are accurate. U6 is confirmed: 378 validation stems in the WP36 file versus 376 labelled frames, with every one of the 376 present in the split file.

## Required and proposed corrections (for an addendum or successor; the contract was not edited)

| ID | Severity | Proposal |
| --- | --- | --- |
| C1 | **Required before execution** | Add a guard for DK 39 / yolo 40 (critical, P3 source, 14/15 under A), for example hits_B ≥ 14, or a ≤ 1 loss with a stated reason. |
| C2 | **Required before execution** | Fix outcome precedence: `INVALID` > `NO_GO` > `NO_GO_UNCERTAIN` > `NO_GO_LATENCY` > `GO_CANDIDATE_FOR_CONFIRMATION`. Measure G7 in every case. |
| C3 | Recommended | Counterbalance the A/B order within the latency loop. Retitle §6.4. Authorize latency-arm live inference explicitly. |
| C4 | Recommended | Define `crop_invalid` as: clip the raw box to the image, then non-finite or non-positive extent, or `crop_bounds` raises. Cite lines 174–175 and 192–195. Pin `detector/d1_cascade_classifier/data.py` `e55fbadd…63ed5d`. |
| C5 | Recommended | Fix the τ comparison: float32 softmax cast to float64 and compared `>= 0.80`, inclusive. Note that the argmax clause is implied. |
| C6 | Recommended | Restate the §8 step 3 bootstrap equivalence test as in F7. |
| C7 | Recommended | Downgrade U2 with the pins listed in F9. |
| C8 | Minor | Add the R2-combined variant selection to the §7 reuse list. |

## Commands run (read-only; no model loaded)

| Command | Result |
| --- | --- |
| `git status --short \| head -60`; `git log --oneline -3` | 12 ` M` Owner files plus untracked; HEAD `5e3fa2a` |
| `shasum -a 256 docs/review/d1_yolo54_classifier_fusion_r1_contract.md` | `40cbe72f…a77c700c`, match |
| `graft check .` | `graph check: OK` |
| `shasum -a 256 -c <33 §10 pins>` | 33 × `OK` |
| `sed -n`/`nl` readback of the cited ranges in F1, F6, F7 | as recorded above |
| `python3 -I` class-map/support script (CSV, YAML and label files only) | `rows 54 54 54`, `mismatches 0`, `files 376 boxes 624` |
| `python3 -I` confusion-matrix script on `eval_val_vrl_r3_vre_r2.json` | six cells ≥ 5 listed in F3; diagonal 432; Σ hits 457 |
| `python3 -I` pilot CSV counts (no GT matching) | 798 / 350 / 235 / max 5; 18 invalid rows, all yolo 47, 0 among sources |
| `python3 -I` group feasibility (labels and split map only) | target classes in 6/9 groups; (7/9)^9 = 0.104 |
| `python3 -I` bundle manifest verification | 8,579 OK, 0 bad, 0 missing |
| `diff -rq tmp/yolo11n_n1_extract_r1/data/labels54/val data/processed/m1_yolo_val_vrl_r3/labels/val` | identical |
| `uv run ruff check src tests` | `All checks passed!`, exit 0 |
| `uv lock --check` | `Resolved 201 packages`, exit 0 |

## Rehashed pins (SHA-256)

| File | SHA-256 |
| --- | --- |
| Contract under review | `40cbe72ff095b8aea9d2253c02a52c013797b2148febc4bbbd647e68a77c700c` |
| `docs/review/next_direction_proposal_2026-11-04.md` | `dc2a08ad0ce171254ab5ff292cad5052ebfeb57c6ced867583c79f1c1b477d68` |
| `docs/review/cascade_classifier_improvement_r2_report.md` | `4affca752041ac8cadd45274f2a940b7795816940eed95807fbe94f048066593` |
| `docs/review/cascade_classifier_improvement_r2_combined_result_independent_qa_record.md` | `256ded5002c63af74a2b5864c0a65b8dc2e1d2bc12fcf65000eac64c86b275ca` |
| `docs/review/cascade_classifier_improvement_r2_combined_e2e_result_independent_qa_record.md` | `3e7aef8227addd1fb183d3c8df174aa1b519751ba5ef9783bfcbde6f67cc46fa` |
| `docs/review/cascade_classifier_improvement_r2_combined_latency_independent_qa_record.md` | `e6f2752ae6d2f85e442c6690b9b5f7b5eef5832626d9c1c50812039aa1079d91` |
| `results/experiments/cascade_classifier_improvement_r1/combined_e2e_eval_r2/comparison.json` | `2dbc63f3ba17b4defe8b5d948e5517e92c526ec81a2f28ca1ed8fa6455c41ae7` |
| `…/compact_combined_local_r2/best.pt` (hash only, not loaded) | `d1e69eefce644cdce044017aeb265e2179cbb94eb07a8ecdb114de16930350cc` |
| `…/compact_combined_local_r2/contract.json` | `b659a4fd78901b9f094f5d909b317f7b9b69c7bbfe88083075bdd2ee803ced5a` |
| `docs/review/generated/dataset01_crops_manifest.json` | `6526844b44670e6b933ade6b48271f0f122621f783672dbfa04a1d4119beb576` |
| `data/processed/dataset01_crops/signnames.csv` | `cd885b463109d1bec3169ccb9306c7eb46c9f1c26647b527129e1257281affca` |
| `docs/review/generated/m1_yolo_classes.csv` | `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242` |
| `data/processed/m1_yolo/data.yaml` | `4cd8303540ecf7bf8ce461b440a07ae35b5ffb047348613c3cdbc8d9c1d78bd0` |
| `docs/review/vgg16_54_r4_validation_comparison_report.md` | `1eacd8211bb6a9bc8817a2b84c42d74e39b56d6683296b11b8e96a1c66f4b689` |
| `docs/review/cascade_b0_r1_validation_comparison_report.md` | `728042dacff7e01d5c5d2ad0a9f81bd84e8a1a03e93e451c27e5efe5085dfaad` |
| `docs/review/d1_vre_r2_result_report.md` | `96255be888e5a06c40e18441a86dc3140702ba4558bcc32e9dec00bacffdf68b` |
| `docs/review/d1_vre_r2_result_independent_qa_record.md` | `95db91cbe640e27ee6de2c185a09b61902da4412717310932aa3b36e48be031b` |
| Pilot `weights/best.pt` (hash only, not loaded) | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` |
| Pilot `run_contract.json` | `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88` |
| Pilot `args.yaml` | `a457c6d51547477348c19a06ec4cf3c8794508169b2e0e1a43edc6260b7d16f0` |
| Pilot `d1_vre_r2/predictions_conf0001.csv` | `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893` |
| Pilot `d1_vre_r2/eval_val_vrl_r3_vre_r2.json` | `559c6c6a78a0d653da09a43bf6dc0663a2dbcb07f6aef4748cade369ef857c87` |
| `docs/review/sahi_r1_validation_report.md` | `38adbfaf1df8744ccac97da72667ca6ae8be71224268c16b53216cda72258cab` |
| `docs/review/sahi_r1_independent_qa_record.md` | `335a81b8fc718b6e1fc0e4b438d42cf9f3da89de1c66c00b18d67f629645af2c` |
| Pilot `sahi_r1/sahi_r1_latency_mps.json` | `a8b06702cfe50f4956c9b1f118b5b58b5494aa52e218013ba76cc07a43d811b8` |
| `docs/review/d1_yolo54_improvement_r3_contract.md` | `3382de28faa960f3c0be3acc28a1ca2d7d17192bfe371f8affca347c6886162f` |
| `docs/review/d1_yolo54_improvement_r3_addendum_a3_executed_2026-11-05.md` | `a1ab05c185f5befa4ab28607662a71a3e6fb80fe28e81368c64a5c1366c74642` |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` |
| `detector/m1/val_reeval_r2.py` | `2a0823faa15f7cb9cecb64a1f21e48e8b5b84f7e7f949683683a6992ee13ccc9` |
| `detector/m1/sahi_eval_r1.py` | `2ca327ed2901b03b1c302457c881eac0bdf0018c601ac413f70bee489163ebeb` |
| `detector/colab/evaluate_cascade_b0_r1.py` | `8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42` |
| `detector/colab/evaluate_compact_improvement_r2.py` | `1c2c7161b7d81eb109b46c23c90fcc26521070cc9b8fdb21cc2eb9d0664e4b04` |
| `detector/d1_cascade_classifier/model.py` | `fdcbc4156a4bef9b5eed56a8ebc58746408a14f6558cd4b3c38a4e49df47b77a` |
| `docs/review/generated/wp36_r1_split_frames.csv` | `8e197d9c7103ac5dc6b7ffc8a3d1aeb30bb6034048d470e4887dd868df95823a` |
| Additional: `detector/d1_cascade_classifier/data.py` (not in §10) | `e55fbaddea154131a0ef20f8d2653150b0f2c8eecdc8ff31dbcb16d6a463ed5d` |
| Additional: `tmp/yolo11n_n1_extract_r1/manifest.json` | `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da` |
| Additional: `tmp/yolo11n_n1_extract_r1/data/yolo54_predictions_val.csv` | `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893` |
| Additional: `tmp/yolo11n_n1_extract_r1/data/val_groups.json` (manifest value, verified) | `fdb2ef8ff2cc684970b6330747d7746ccfe6dfd77d60903d10233de66697d682` |
| Additional: `results/experiments/yolo11n_n1_seed_20261018_r1_r1/evaluation_r1/comparison_n1_r1.json` | `0447a1bdc2aec56980b63f3fea5340be9a1d455ed9b7872ac503c4d65779a0db` |

## Flags

`sealed_test_accessed=false`, `training_authorized=false`, `inference_run=false`, `fusion_metric_computed=false`,
`app_enable_authorized=false`, `threshold_lock_written=false`, `d05_changed=false`, `contract_edited=false`,
`commit_or_push=false`.
