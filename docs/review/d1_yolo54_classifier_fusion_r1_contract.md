# D1 YOLO54 + CompactCNN classifier fusion R1 — pre-registered experiment contract

Status: `FROZEN_AWAITING_INDEPENDENT_QA_NOT_EXECUTED`
Boundary: `DOCUMENTATION_ONLY_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST_NO_APP`
Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Author: Claude Code (Opus 5.5), side session started from the coordinating session.
Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, branch `yolo11n-dual-track-r1`,
HEAD `5e3fa2a`. Many uncommitted Owner changes exist; this contract edits none of them.

This contract fixes the rules of an offline ablation before anyone sees a fusion number. The
author computed no fusion result. No classifier ran on any detector crop, no inference ran, and
nothing was trained. Every rule below was written using only evidence already published.
The rules are the relabel pairs, thresholds, crop rule, metrics and decision rule.

Claim labels used throughout:

- **[VA]** verified artifact: the author re-read or rehashed it in this checkout on 2026-11-05;
- **[P]** proposal: a rule this contract fixes for a future run;
- **[U]** unknown or blocked.

This file has no "verified current behaviour" claims, because no code ran.

## 0. Question and predecessors

**Question [P].** The pilot already proposes a box for 612 of 624 validation signs. Does letting the
CompactCNN R2 crop classifier relabel those boxes, only in pre-registered confusable class pairs,
raise correct-class recall without raising FP/image?

| Predecessor | What this contract takes from it |
| --- | --- |
| `docs/review/next_direction_proposal_2026-11-04.md` line 16, row "Ghép YOLO54 với classifier Cascade ở nhóm lớp dễ nhầm" | The direction and its required safeguards: pre-registered pairs and switch conditions, both checkpoints and class maps, the crop/fusion rule, the same validation set and FP budget, the scorer QA'd before results are viewed, offline only, no app |
| `docs/review/cascade_classifier_improvement_r2_report.md` lines 54–61, 80–86 | The classifier candidate. In the cascade, R2 combined raised exact-class mAP50 from 0.4120 to 0.4783 (S1) and from 0.4000 to 0.4500 (N1); FP/frame rose by 0.0133 (S1) and 0.0027 (N1). This is evidence about the cascade only, not about correcting YOLO54 |
| `docs/review/vgg16_54_r4_validation_comparison_report.md` lines 74–86, 103–105 | Same-scorer comparison: CompactCNN beats VGG16-54 as the cascade classifier; YOLO54 exact-class mAP50/50-95 on the common scorer is 0.8521/0.6089 |
| `docs/review/d1_vre_r2_result_report.md` lines 41–49, 68–92 | The pilot reference and its reported confusions |
| `docs/review/sahi_r1_validation_report.md` lines 121–128, 168–173, 197–201 | 612/624 GT already have a candidate, so the bottleneck is class and score selection; same-FP-budget method; latency protocol |
| `docs/review/d1_yolo54_improvement_r3_contract.md` and its addendum | Style template; the single-change rule (the addendum §2 notes that A3 changed two arguments, a mistake this contract avoids) |

## 1. Absolute boundaries [P]

Writing this contract did none of the following, and executing it later may do none of them
without a separate written Owner authorization:

- train or fine-tune any model, YOLO or classifier;
- run YOLO inference for the accuracy arm (the pilot candidates come from the pinned CSV);
- open, list or score the sealed test (`afa03d4b…`). The pilot run directory name contains the
  token `afa03d4b` as a provenance label; reading that run's `best.pt` or validation CSV is not
  sealed-test access;
- change D-05, the conf 0.20 operating point, NMS or any threshold lock;
- enable anything in the app, or connect any output to a vehicle. Behaviour output stays
  simulation only;
- upload, commit or push.

Flags fixed for every output: `sealed_test_accessed=false`, `training_authorized=false`,
`app_enable_authorized=false`, `threshold_lock_written=false`, `d05_changed=false`.

## 2. The single change versus the pure YOLO54 pilot [P]

**Baseline arm A (pure pilot) [VA].** The YOLO11s-54 pilot is
`results/experiments/D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2/weights/best.pt`,
SHA-256 `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633`. Its post-NMS candidates
are in `d1_vre_r2/predictions_conf0001.csv`, SHA-256
`87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893`. They were produced at
conf ≥ 0.001, class-wise NMS IoU 0.70, `imgsz=1280` and `max_det=300`. The CSV has 1,999 rows and
the header `stem,rank,yolo_id,conf,x1,y1,x2,y2`, in original 960×540 pixels.

**Fusion arm B.** B is arm A with exactly one change: the class label of a pilot candidate may be
replaced by the classifier's top-1 class under rule F1 (§4). Everything else stays the same:

- every box, every score and the number of candidates per image;
- NMS (not re-run), the conf 0.20 operating point and every threshold.

B adds no box, removes no box and never changes a score.

**Consequence for FP [VA, by reading `detector/m1/metrics.py:50-115`].** `operating_point` counts
false positives and agnostic TP with `match(..., class_aware=False)`, which ignores classes. So arm B
must reproduce TP 547, FP 150, FP/image 0.398936 and agnostic recall 0.876603 at conf 0.20
exactly. The FP budget ≤ 0.3989 is therefore met by construction. Any deviation is an
implementation defect (§6, `INVALID`), not a result. Only class-aware quantities can move:
correct-class recall, per-class hits and exact-class AP.

## 3. Classifier checkpoint and class-map alignment

**Checkpoint [VA].** The classifier is CompactCNN R2 "combined" (group balance plus train-only crop
jitter), 54 outputs, at
`results/experiments/cascade_classifier_improvement_r1/compact_combined_local_r2/best.pt`, SHA-256
`d1e69eefce644cdce044017aeb265e2179cbb94eb07a8ecdb114de16930350cc` (rehashed). Its bindings:

| Item | Value |
| --- | --- |
| Epoch | 18 |
| Run contract | `contract.json` `b659a4fd…ced5a` |
| Independent artifact QA PASS | `cascade_classifier_improvement_r2_combined_result_independent_qa_record.md` `256ded50…75ca` |
| End-to-end result QA | `…_combined_e2e_result_independent_qa_record.md` `3e7aef82…46fa` |
| Architecture | `detector/d1_cascade_classifier/model.py` `fdcbc415…6b42`, `CompactCNN` lines 11–31 |
| Crop manifest | `6526844b…b576`; it pins `signnames_sha256` `cd885b46…affca` |

At execution the checkpoint is loaded with `torch.load(weights_only=True)`, which the artifact QA
showed works, and its SHA-256 is re-verified before and after loading.

**Why R2 combined and not the frozen B0 CompactCNN [P].** It is the only classifier that met the
cascade comparison gate (R2 report lines 88–93). Choosing it is itself a val-informed choice; see §7.

**Class-map alignment [VA]: exact, so not blocked.**

- `docs/review/generated/m1_yolo_classes.csv` (`7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242`;
  pinned by `val_reeval_r2.py`) and `data/processed/dataset01_crops/signnames.csv`
  (`cd885b463109d1bec3169ccb9306c7eb46c9f1c26647b527129e1257281affca`) agree on all 54 rows. For
  every row, `yolo_id == ClassId`, `derived_key == DerivedKey`, `derived_code == QCVN` and
  `name_vi == SignName`.
- The pilot's `data/processed/m1_yolo/data.yaml` (`4cd83035…8bd0`) name `i` equals
  `"<DerivedKey> <QCVN>"` of row `i` for all 54 rows.
- Classifier output index `k` therefore means pilot `yolo_id` `k`, with no remapping.

**Naming hazard [VA]; the scorer must handle it.** D1-VRE-R2's report and its eval JSON
(`559c6c6a…7c87`, `primary_r3.confusion_matrix.labels`, `per_class`) label classes by
**derived key**. The CSV and the classifier use **yolo_id**. They differ from yolo_id 16 upward.
For example, "class 32" in the report is derived key 32, which is yolo_id 33 (P.123b, support 29).
yolo_id 32 is S.505a, which has no validation support. The table below is the binding translation
for this contract. Every output must carry both keys.

| Derived key (report) | yolo_id (CSV/classifier) | Code | Val GT support (R3) |
| ---: | ---: | --- | ---: |
| 7 | 7 | P.123a (cấm rẽ trái) | 111 |
| 8 | 8 | I.434a | 51 |
| 10 | 10 | P.130 | 48 |
| 12 | 12 | R.415a | 65 |
| 17 | 19 | P.124a | 0 |
| 18 | 20 | P.107 | 0 |
| 32 | 33 | P.123b (cấm rẽ phải) | 29 |
| 39 | 40 | P.127 (60 km/h) | 15 |
| 40 | 41 | P.127 (80 km/h) | 0 |
| 41 | 42 | P.127 (40 km/h) | 26 |
| 46 | 48 | P.131a | 104 |

The support counts were recounted from `data/processed/m1_yolo_val_vrl_r3/labels/val/`
(376 files, 624 boxes) and match the report's per-class gate table (lines 72–76).

## 4. Confusable pairs and relabel rule F1 [P]

### 4.1 How the pairs were chosen (fixed, not tuned)

**Source evidence [VA].** The pilot's already-reported confusion matrix at conf 0.20
(`eval_val_vrl_r3_vre_r2.json` → `primary_r3.confusion_matrix`, rows GT, columns predicted,
class-agnostic greedy pairing) is the source. The pairs the report discusses are in
`d1_vre_r2_result_report.md` lines 85–92.

**Inclusion rule [P].** Every off-diagonal (GT class → predicted class) cell with a count of **≥ 5**
is included. Nothing else is: background cells, cells below 5 and any classifier evidence are
excluded. This gives exactly six directed pairs. The source is the class YOLO predicted, and the
target is the GT class it was confused with.

| Pair | Source yolo_id (DK) → target yolo_id (DK) | Codes | Pilot count | Citation |
| --- | --- | --- | ---: | --- |
| P1 | 10 (10) → 48 (46) | P.130 → P.131a | 58 | report line 92; JSON `pair_46_to_10` = 58 |
| P2 | 19 (17) → 7 (7) | P.124a → P.123a | 10 | report lines 85–86 |
| P3 | 40 (39) → 42 (41) | P.127 60 → P.127 40 | 7 | report lines 89–91 |
| P4 | 7 (7) → 33 (32) | P.123a → P.123b | 6 | report lines 87–88 |
| P5 | 41 (40) → 42 (41) | P.127 80 → P.127 40 | 6 | report lines 89–91 |
| P6 | 12 (12) → 8 (8) | R.415a → I.434a | 6 | JSON confusion matrix only; not in the report prose |

Excluded cells, listed for transparency: DK 7→18 (2), 4→5 (4), 14→23 (4), 26→0 (3), 34→23 (2), and
singletons.

Each source class has exactly one allowed target. yolo_id 7 is both a target (P2) and a source
(P4). F1 applies at most once per candidate and only by its **original** pilot class, so there is
no chaining: a P2 relabel to 7 is never re-examined under P4.

### 4.2 Rule F1

For every pilot candidate `b` in the CSV, at every score (all 1,999 rows, so that AP is defined),
whose original `yolo_id` `s` is a source in §4.1, with target `t`:

1. Crop `b` by §5 and compute the classifier softmax `p` (54-vector).
2. Relabel `b` from `s` to `t` **iff all** of the following hold:
   - `argmax(p) == t`;
   - `p[t] ≥ τ = 0.80`.

   Because `p[s] ≤ 1 − p[t]`, this implies `p[t] − p[s] ≥ 0.60`.
3. Otherwise keep `s`. Candidates whose class is not a source are never cropped or changed.
4. **Relabel only.** F1 never suppresses or rescores a box. The classifier has no background or
   reject class, so it has no principled basis for suppression.
5. After relabelling, NMS is not re-run. This can create same-class overlaps that the original
   class-wise NMS never saw. They stay, they count against AP, and their number at IoU ≥ 0.70 is
   reported as a diagnostic.

For scale [VA, a count of pilot CSV rows only, without GT matching]: 798 of the 1,999 candidates
have a source class. At conf ≥ 0.20 there are 350, in 235 images, with at most 5 per image.

### 4.3 Threshold τ: fixed a priori, not tuned [P]

- No train-only or held-out split exists for this classifier [VA]. All 12,621 train crops were
  used for training. The corrected validation pickle was the sole checkpoint-selection set
  (combined result QA record, "Bound authority and data"). Train-crop softmax would be optimistic,
  so it cannot calibrate τ.
- τ is therefore fixed **a priori** at 0.80. Overriding a detector label requires the classifier to
  give the target at least 4:1 odds against all other classes combined. Small softmax CNNs tend to
  be overconfident, so a lower bar such as plain argmax would make the classifier the de facto
  labeller of six source classes. A much higher bar such as 0.99 would make F1 nearly inert, given
  the classifier's measured GT-crop top-1 of 0.625. That figure is quoted for scale only; it was
  not used to pick τ.
- **Sensitivity grid (descriptive only).** τ ∈ {0.50, 0.95} is also scored and reported. It can
  never change the verdict, and no grid value may be adopted from this run.
- **Per-pair leave-one-out (descriptive only).** F1 is re-scored with each pair dropped. No pair
  may be removed or added on the basis of these numbers.
- **Multiplicity.** There is one primary configuration (six pairs, τ = 0.80) and one primary
  endpoint (Δ correct-class recall). All other GO conditions are conjunctive guards, an
  intersection–union rule, so no α inflation follows from them. The grid and leave-one-out results
  are exploratory and labelled `SENSITIVITY_NOT_DECISION`.

## 5. Crop extraction and classifier input [P]

The crop rule is identical to the QA'd cascade evaluator, so the classifier sees the input
distribution behind its published cascade results.
`detector/colab/evaluate_cascade_b0_r1.py` (SHA-256
`8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42`), `crop_bounds` lines 46–59 and
`crop_prediction` lines 62–66 [VA, read]:

- source image opened with PIL and converted to RGB;
- border `dx = max(5, 0.10·w)` and `dy = max(5, 0.10·h)` on every side;
- bounds are `floor(round(x1−dx, 6))`, `floor(round(y1−dy, 6))`, `ceil(round(x2+dx, 6))` and
  `ceil(round(y2+dy, 6))`, clipped to the image;
- `Image.crop`, then `resize((32, 32), BILINEAR)`, `uint8`;
- tensor `/255`, then `(x − 0.5)/0.5`, then `softmax(dim=1)`. This matches training normalisation
  in `detector/d1_cascade_classifier/data.py:21-23` and in `infer` (lines 148–226; normalisation at 166–168 and 201–203).

**Small or degenerate boxes.** The primary rule has no size cut-off: the QA'd cascade rule had
none, and adding one would be a free parameter. A candidate whose box is non-finite, or has zero
width or height after clipping to the image, is left unchanged and counted (`crop_invalid`).
Relabels and help/harm counts are reported by GT size bin, √(w·h) in original pixels:
`<16`, `16–32`, `32–64`, `≥64`, matching the SAHI R1 bins.

**Determinism.** The accuracy arm runs the classifier on **CPU, float32**, with
`torch.use_deterministic_algorithms(True)` and one thread, batched per image. The relabel decisions
are also recomputed on MPS. Any decision that differs between CPU and MPS is listed. The verdict
uses CPU only.

## 6. Metrics, scorer and pre-registered decision rule [P]

**Evaluation set [VA].**

- R3 validation: 376 images with roster `24e2a67d1e176a7e09caf4b1f6daa2bf5240981d00c8e1a535640e6b8066118e`;
- labels in `data/processed/m1_yolo_val_vrl_r3/labels/val/`, roster
  `dc72ebd944a38535d4f766ba4f8babc60cb6732dfcd253ed0e8d79dc86eb8343`, 624 GT;
- D-02 groups from `docs/review/generated/wp36_r1_split_frames.csv` (`8e197d9c…823a`): 9 validation
  groups, exactly as D1-VRE-R2 and SAHI R1 used them.

The 40 ignore regions are not used. A path with a `test` component is refused.

**Scorers [VA, pinned].**

- Operating points: `detector/m1/metrics.py` (`d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f`).
- Exact-class AP: the common-method `average_precision` in `evaluate_cascade_b0_r1.py` lines 88–125,
  which uses the pinned Ultralytics matcher.

**Step 0: reproduce the reference, or stop.** Before any arm-B number is computed or written, the
scorer must reproduce arm A from the CSV. If any value differs, the run stops with `INVALID`,
writes no result file, and reports:

- at conf 0.20, all from `operating_point`: TP 547, FP 150, correct-class hits 457 (sum of
  `per_class_hits`), agnostic recall 0.876603 and FP/image 0.398936;
- per-class hits for derived keys 7/32/41/46 equal to 66/18/12/55;
- common-path exact-class mAP50 0.8520835680 and mAP50-95 0.6088678435, to within 1e-9
  (`cascade_b0_r1_validation_comparison_report.md` lines 11–12).

### 6.1 Primary endpoint

**Correct-class recall at conf 0.20** = Σ class-aware hits / 624. The reference is 457/624 =
0.7324. Δ = B − A.

### 6.2 GO rule: all must hold (`GO_CANDIDATE_FOR_CONFIRMATION`)

| # | Condition | Threshold |
| --- | --- | --- |
| G1 | Correct-class hits at 0.20 | B ≥ **467** (≥ +10, about +1.6 pp). Gains below 10 boxes are within one correlated frame sequence, for example frames 1208–1228 |
| G2 | Paired group-bootstrap 95 % percentile CI of Δ correct-class recall at 0.20 | **lower bound > 0**. 1000 rounds, seed 20261018, resampling the 9 D-02 groups with replacement, the same draws for A and B |
| G3 | FP budget at 0.20 | FP_B ≤ 150 (FP/image ≤ 0.3989) **and** TP_B = 547. Expected to hold exactly (§2); a violation is `INVALID` |
| G4 | Critical classes, DK 7/32/41 (yolo_id 7/33/42) | class-aware hits_B ≥ 66 / 18 / 12 respectively. No loss is allowed |
| G5 | Other gated classes (support ≥ 20: DK 6, 8, 10, 12, 23, 34, 46) | each loses ≤ 2 hits, and none that meets its D-05 per-class reference under A falls below it under B |
| G6 | Exact-class AP, common path | Δ mAP50 ≥ 0 **and** Δ mAP50-95 ≥ 0 (point estimates) |
| G7 | Latency (§6.4) | fusion p95 ≤ **100 ms** |

**Outcomes.**

- G3 or Step 0 fails: `INVALID`.
- G1, G2, G4, G5 and G6 all hold but G7 fails: `NO_GO_LATENCY` (research note only).
- The Δ point estimate is > 0 but G1 or G2 fails: `NO_GO_UNCERTAIN`.
- Δ ≤ 0, or G4, G5 or G6 fails: `NO_GO`.
- Everything holds: `GO_CANDIDATE_FOR_CONFIRMATION`.

**Feasibility note on G2 [VA, from GT labels and group map only].** The GT of the five target
classes (yolo_id 7, 8, 33, 42, 48) lies in 6 of the 9 groups. Each class alone lies in only 1–2
groups: 33 and 8 in one each, the others in two. If help is confined to 2 groups, roughly 10 % of
resamples contain neither, which pushes the lower bound to ≤ 0. G2 therefore implicitly requires
gains spread over several groups. This is intended. R3 contract lines 166–169 record the same
coarseness.

### 6.3 Reported but not decisive

- Δ and paired CI of exact-class mAP50 and mAP50-95.
- Per-class AP50 for the 19 supported classes.
- Per-class hits for all 19 supported classes.
- Per pair: the number of relabels at conf ≥ 0.20 and at all scores, plus **help** (wrong → correct
  class-aware match) and **harm** (correct → wrong) counts.
- `crop_invalid` count, same-class overlap count after relabelling, and CPU/MPS decision
  differences.
- The size-bin breakdown.
- The §4.3 sensitivity grid and leave-one-out results.

Classes without validation support (35 classes, and source yolo_id 19, 20 and 41 have **zero** GT)
get no benefit claim. Relabels *from* them are counted. Their effect on AP enters only through
target-class matches and FP removal from source-class AP.

### 6.4 Latency protocol (identical to SAHI R1 §1.5, `sahi_r1_validation_report.md` lines 68–71)

- **Setup.** Apple M1 Pro, MPS, batch 1 image, 50 warm-up and 300 measured iterations,
  `torch.mps.synchronize()` every iteration, images cycled in validation order, `conf=0.20`,
  `iou=0.70`, `imgsz=1280`.
- **Timed span, arm A.** Read image, then `model.predict`.
- **Timed span, arm B.** The same, then select source-class boxes, crop them (§5), run one
  classifier forward on MPS for all of them, and apply F1.
- **Order control.** The SAHI QA noted (record C5) that its two arms were timed one after the
  other. Here A and B alternate within each iteration, one process, models loaded once.
- **Outputs.** p50/p95 for each arm and the Δ.
- **Artifact.** The latency JSON stores the raw per-iteration samples and the SHA-256 of the timed
  image roster. The R2 latency QA (report lines 103–108) flagged the absence of both.
- **Reference.** SAHI R1 measured full-frame p95 at 54.4 ms (`sahi_r1_latency_mps.json` `a8b06702…11b8`).
  Torch and ultralytics versions are recorded. If they differ from SAHI R1, both arms are
  remeasured in this run and only this run's numbers are used.

## 7. Validation-reuse risk and what a GO means [P]

The same 376 frames have been used many times:

- the pilot's R10 and VRE checks;
- labels R1 to R3, where R3 added 64 boxes found by reviewing **this pilot's** FPs
  (report lines 108–112);
- dynamic thresholds R1 and R2;
- A0b, SAHI R1 and temporal DT;
- checkpoint selection for the classifier (epoch 18 by validation crop macro-F1);
- now the derivation of F1's pairs from the pilot's validation confusions.

Any gain in arm B is therefore an **in-sample, optimistically biased** estimate. Consequently:

- `GO_CANDIDATE_FOR_CONFIRMATION` is only a candidate. It is **never** a D-05 pass, never a
  threshold lock and never an app-enable decision. D-05 exists only on the sealed test with three
  seeds.
- Confirmation needs scenes not used for any selection here, frozen with F1 unchanged. Those scenes
  must not be the sealed test unless the project-wide final-evaluation gate is authorized. The next
  direction proposal (line 16) asks for "nhóm scene độc lập để xác nhận" (an independent scene group
  for confirmation). Whether such a set exists is **[U]** (§9).

## 8. Outputs, determinism, manifest and QA order [P]

**Implementation (not written).** A new module `detector/m1/classifier_fusion_r1.py` plus
`detector/tests/test_classifier_fusion_r1.py`. It may import `m1.metrics` and the pinned
`evaluate_cascade_b0_r1` crop/AP functions, and must not modify them. It uses the input guards of
`val_reeval_r2`/`sahi_eval_r1`: no symlinks, regular files only, no `test` path component, and pins
re-verified before the write.

**Outputs.** Written once with `O_CREAT | O_EXCL | O_NOFOLLOW` under
`results/experiments/<pilot run>/classifier_fusion_r1/`:

| File | Content |
| --- | --- |
| `fusion_r1_predictions_conf0001.csv` | 1,999 rows in pilot CSV order: `stem,rank,yolo_id,fused_id,derived_key,fused_derived_key,conf,x1,y1,x2,y2,pair,p_target,p_source,top1_id,relabelled,crop_invalid` |
| `fusion_r1_crop_probs.csv` | full 54-way softmax (`repr` floats) for every cropped source candidate, so QA can recompute F1 without a model |
| `fusion_r1_eval.json` | canonical JSON (sorted keys, no NaN/Inf): Step 0, §6 metrics, verdict, flags |
| `fusion_r1_latency_mps.json` | §6.4 output, including raw samples |
| `fusion_r1_manifest.json` | SHA-256 of module, tests, this contract, every input pin and every output; never pins a QA record |

A model-free `verify` subcommand rebuilds every metric from the two CSVs and must be byte-identical
on re-run.

**QA order, with no fusion number viewed before step 3.**

1. Independent QA of **this contract**.
2. Written Owner authorization to implement and execute.
3. Implementation, then **independent source QA of the scorer** before any real run. QA covers:
   - Step 0 reproduction;
   - the §2 FP invariant tested on synthetic frames;
   - F1 unit cases: no chaining, P2/P4 overlap, τ boundary, invalid crop;
   - the derived-key/yolo_id translation;
   - that the paired bootstrap at Δ = 0 equals `metrics.group_bootstrap`.
4. One execution that writes the outputs.
5. Independent result QA from the CSVs before any interpretation is published.

## 9. Unknown or blocked [U]

- **U1, confirmation set.** No independent, unused scene set is known to exist. Without one, a GO
  cannot progress beyond candidate. S.505a collection (`s505a_independent_data_collection_r2.md`)
  is a different scope.
- **U2, cascade bundle copy.** The common-path reference AP was computed from a bundle copy of the
  pilot CSV (`data/yolo54_predictions_val.csv`, same SHA `87884c53…`). That bundle was not found
  under `results/` or `data/` in this checkout. The executor builds frames from the R3 labels and
  the run-directory CSV, and Step 0 must reproduce 0.8520835680/0.6088678435. If it cannot, the run
  is **blocked**.
- **U3, classifier behaviour on the source classes.** Unknown by design. Per-class GT-crop accuracy
  of the classifier on validation was deliberately not consulted, to keep the pairs and τ
  independent of it. The classifier may be weak exactly where needed: speed-limit digits on small
  32×32 crops (P3/P5), and P.130 vs P.131a (P1).
- **U4, harm to perfect classes.** Source yolo_id 10 (48/48 hits) and 12 (60/65) are strong under A.
  G5 bounds their loss, but the size of the harm is unknown until execution.
- **U5, environment.** The torch/ultralytics versions at execution, and whether MPS and CPU softmax
  agree on every decision near τ.
- **U6, 2-frame roster difference.** The WP36 split file lists 378 validation stems and the image
  roster has 376. The executor uses the D1-VRE-R2 roster and mapping, as SAHI R1 did, so this is
  inherited, not new.
- **Blocked until QA and Owner authorization:** all of §8 steps 2–5. Separate decisions would be
  needed for any app integration, threshold change, D-05 change, retraining or sealed-test access.

## 10. Evidence pins (SHA-256, rehashed 2026-11-05) [VA]

| Evidence | SHA-256 |
| --- | --- |
| `docs/review/next_direction_proposal_2026-11-04.md` | `dc2a08ad0ce171254ab5ff292cad5052ebfeb57c6ced867583c79f1c1b477d68` |
| `docs/review/cascade_classifier_improvement_r2_report.md` | `4affca752041ac8cadd45274f2a940b7795816940eed95807fbe94f048066593` |
| `…_r2_combined_result_independent_qa_record.md` | `256ded5002c63af74a2b5864c0a65b8dc2e1d2bc12fcf65000eac64c86b275ca` |
| `…_r2_combined_e2e_result_independent_qa_record.md` | `3e7aef8227addd1fb183d3c8df174aa1b519751ba5ef9783bfcbde6f67cc46fa` |
| `…_r2_combined_latency_independent_qa_record.md` | `e6f2752ae6d2f85e442c6690b9b5f7b5eef5832626d9c1c50812039aa1079d91` |
| `combined_e2e_eval_r2/comparison.json` | `2dbc63f3ba17b4defe8b5d948e5517e92c526ec81a2f28ca1ed8fa6455c41ae7` |
| Classifier `compact_combined_local_r2/best.pt` | `d1e69eefce644cdce044017aeb265e2179cbb94eb07a8ecdb114de16930350cc` |
| Classifier `compact_combined_local_r2/contract.json` | `b659a4fd78901b9f094f5d909b317f7b9b69c7bbfe88083075bdd2ee803ced5a` |
| `docs/review/generated/dataset01_crops_manifest.json` | `6526844b44670e6b933ade6b48271f0f122621f783672dbfa04a1d4119beb576` |
| `data/processed/dataset01_crops/signnames.csv` | `cd885b463109d1bec3169ccb9306c7eb46c9f1c26647b527129e1257281affca` |
| `docs/review/generated/m1_yolo_classes.csv` | `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242` |
| `data/processed/m1_yolo/data.yaml` | `4cd8303540ecf7bf8ce461b440a07ae35b5ffb047348613c3cdbc8d9c1d78bd0` |
| `docs/review/vgg16_54_r4_validation_comparison_report.md` | `1eacd8211bb6a9bc8817a2b84c42d74e39b56d6683296b11b8e96a1c66f4b689` |
| `docs/review/cascade_b0_r1_validation_comparison_report.md` | `728042dacff7e01d5c5d2ad0a9f81bd84e8a1a03e93e451c27e5efe5085dfaad` |
| `docs/review/d1_vre_r2_result_report.md` | `96255be888e5a06c40e18441a86dc3140702ba4558bcc32e9dec00bacffdf68b` |
| `docs/review/d1_vre_r2_result_independent_qa_record.md` | `95db91cbe640e27ee6de2c185a09b61902da4412717310932aa3b36e48be031b` |
| Pilot `weights/best.pt` | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` |
| Pilot `run_contract.json` / `args.yaml` | `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88` / `a457c6d51547477348c19a06ec4cf3c8794508169b2e0e1a43edc6260b7d16f0` |
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

The executor re-verifies every pin. A mismatch blocks execution and requires a successor contract.
This file is never edited in place.
