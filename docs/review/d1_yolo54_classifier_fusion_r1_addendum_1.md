# D1 YOLO54 + CompactCNN classifier fusion R1 — Addendum 1 (QA corrections C1–C8)

Status: `FROZEN_AWAITING_INDEPENDENT_QA_NOT_EXECUTED`
Boundary: `DOCUMENTATION_ONLY_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST_NO_APP`
Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Author: Claude Code (Opus 5.5), side session started from the coordinating session. Not the author
of the contract's independent QA.
Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, branch `yolo11n-dual-track-r1`,
HEAD `17db663`. Many uncommitted Owner changes exist; this addendum edits none of them.

This addendum is **append-only**. The contract is not edited. Where this addendum and the contract
disagree, this addendum governs, but only on the points listed in §1–§8. Everything else in the
contract stays binding as written (§9).

While writing it, the author ran no inference, ran the classifier on no crop, trained nothing,
computed no fusion metric and viewed none. The checks below read hashes, CSV coordinates, label
files, the published VRE-R2 evaluation JSON and source lines only.

Claim labels:

- **[VA]** verified artifact: re-read or rehashed by this author in this checkout on 2026-11-05;
- **[P]** proposal: a binding rule for the future implementation and execution;
- **[U]** unknown.

No claim here is "verified current behaviour", because no code ran.

## 0. Pinned documents [VA]

| Document | SHA-256 |
| --- | --- |
| Contract `docs/review/d1_yolo54_classifier_fusion_r1_contract.md` (committed in `17db663`) | `40cbe72ff095b8aea9d2253c02a52c013797b2148febc4bbbd647e68a77c700c` |
| Contract QA record `docs/review/d1_yolo54_classifier_fusion_r1_contract_independent_qa_record.md` | `aa3c4e384118a02fa28fb790d056951221334c7ecdefa410e02f381b83d5e902` |
| Owner authorization `docs/review/d1_yolo54_classifier_fusion_r1_owner_authorization_2026-11-05.md` | `9f8c5f20c4dab52258d64270d490fc720c941bc1478a22550a549560e3556fcd` |

The authorization record says that execution is authorized only after an independent QA PASS of
this addendum, exactly once, offline, on validation images only.

## 1. C1 (required): guard for critical class DK 39 / yolo_id 40

**QA proposal (quoted):** "Add a guard for DK 39 / yolo 40 (critical, P3 source, 14/15 under A),
for example hits_B ≥ 14, or a ≤ 1 loss with a stated reason."

**Evidence [VA].** In the pilot evaluation JSON `eval_val_vrl_r3_vre_r2.json` (`559c6c6a…7c87`),
`primary_r3.fixed_conf_0_20.gates.classes["39"]` is
`{"critical": true, "gated": false, "hits": 14, "passed": null, "recall": 0.9333…, "support": 15}`.
The gate keys are derived keys. By contract §3, DK 39 is yolo_id 40, P.127 (60 km/h), and it is the
source class of pair P3 (40 → 42).

**Resolution [P].** Add guard **G4b** to the contract §6.2 GO rule:

| # | Condition | Threshold |
| --- | --- | --- |
| G4b | Critical class DK 39 (yolo_id 40, P.127 60 km/h), class-aware hits at conf 0.20 | hits_B ≥ **14**, the arm-A value. No loss is allowed |

- G4b is computed as `operating_point(frames_B, 0.20).per_class_hits[40]`. In `detector/m1/metrics.py:90-115`
  that dict is keyed by GT class, which is the yolo_id in these frames. Every output reports it
  under both keys (yolo_id 40, DK 39).
- G4b is part of the GO rule. Failing it gives `NO_GO` (§2).
- **Step 0 is extended by one reference:** arm A must reproduce per-class hits **14** for yolo_id 40
  (DK 39), alongside the contract's 66/18/12/55 for DK 7/32/41/46. Any difference gives `INVALID`.

**Justification.**

- G4 already forbids any loss on the critical classes DK 7/32/41. DK 39 is also marked critical,
  but it fell outside G4, which lists only three classes, and outside G5, which requires support
  ≥ 20. "No loss on a critical class" is the same rule G4 applies, now extended to the one
  critical class that F1 directly touches as a source.
- A D-05-style reference would be much looser: 11/15 = 0.733 still meets the 0.70 critical
  reference, so it would accept three lost hits. That is why the guard is "no loss", not the D-05
  reference.
- F1 can move boxes only out of class 40 (P3), never into it, so the realistic direction of change
  for this class is a loss.
- With G4b, every relabel source class that has validation support is guarded:
  - yolo_id 7 (DK 7) by G4;
  - yolo_id 10 (DK 10) and 12 (DK 12) by G5;
  - yolo_id 40 (DK 39) by G4b.

  The other source classes, yolo_id 19, 20 and 41, have zero validation GT (contract §3), so they
  have no hits that could be lost. Every target class is also guarded: 7, 33 and 42 by G4, and 8
  and 48 by G5.

## 2. C2 (required): outcome precedence and a total mapping

**QA proposal (quoted):** "Fix outcome precedence: `INVALID` > `NO_GO` > `NO_GO_UNCERTAIN` >
`NO_GO_LATENCY` > `GO_CANDIDATE_FOR_CONFIRMATION`. Measure G7 in every case."

**Resolution [P].** The precedence is

`INVALID` > `NO_GO` > `NO_GO_UNCERTAIN` > `NO_GO_LATENCY` > `GO_CANDIDATE_FOR_CONFIRMATION`.

This replaces the contract's §6.2 "Outcomes" list.

**Execution order.**

1. Step 0. If it fails, the run stops before arm B, as contract §6 already requires. The outcome is
   `INVALID`, no result file is written, and the stop report gives the failing reference values.
2. The accuracy arm (arm B on CPU), plus the MPS decision recompute.
3. The §6.4 latency arm. It is **always** run once Step 0 has passed, whatever the accuracy guards
   show. It runs in the same execution, before the outcome is computed.
4. Every guard is evaluated and recorded. Only then is the outcome assigned, by code, with the
   mapping below.

**Inputs to the mapping.**

- **S0**: Step 0 passed, including the C1 extension.
- **G1–G7** as in the contract, plus **G4b**.
- **Δ**: the point estimate of the primary endpoint.
- **L**: the latency arm completed with 300 valid measured samples for each arm, so G7 can be
  evaluated.

**Mapping.** Evaluate the rows in order; the first row that matches assigns the outcome.

| Order | Condition | Outcome |
| ---: | --- | --- |
| 1 | not S0, **or** not G3, **or** not L | `INVALID` |
| 2 | Δ ≤ 0, **or** not G4, **or** not G4b, **or** not G5, **or** not G6 | `NO_GO` |
| 3 | not G1, **or** not G2 (Δ > 0 is guaranteed here by row 2) | `NO_GO_UNCERTAIN` |
| 4 | not G7 | `NO_GO_LATENCY` (research note only) |
| 5 | otherwise: S0, L and all of G1, G2, G3, G4, G4b, G5, G6, G7 hold | `GO_CANDIDATE_FOR_CONFIRMATION` |

**Totality and uniqueness.** Rows 1–4 are tried in a fixed order and row 5 is the complement of
rows 1–4, so every combination of guard values maps to exactly one outcome. The contract's overlap
case is now resolved: Δ > 0, G1 or G2 fails, and G4/G4b/G5/G6 also fails gives `NO_GO` by row 2.

**Making it total required one new condition.** A latency arm that cannot be measured (L false)
gives `INVALID`, not `NO_GO_LATENCY`. Otherwise "G7 measured in every case" would have no outcome
when the measurement itself fails. Under the authorization record, an `INVALID` run may not be
re-run without new written Owner authorization.

**Reporting [P].** `fusion_r1_eval.json` records:

- the boolean of S0, L, Δ > 0, G1–G7 and G4b;
- `failed_guards`, the list of every failing condition, not only the one that set the outcome;
- `outcome` and `outcome_row`, the row of the table above that matched.

G7's measured values are reported whatever the outcome.

## 3. C3 (recommended): latency order control, §6.4 heading, live-inference coverage

**QA proposal (quoted):** "Counterbalance the A/B order within the latency loop. Retitle §6.4.
Authorize latency-arm live inference explicitly."

**Resolution [P].**

- **Heading.** Contract §6.4 is to be read as **"Latency protocol (SAHI R1 §1.5 setup plus order
  control)"**. It does not claim to be identical to SAHI R1. Its setup (M1 Pro MPS, batch 1, 50
  warm-up and 300 measured iterations, `torch.mps.synchronize()` every iteration, validation-order
  cycling, `conf=0.20`, `iou=0.70`, `imgsz=1280`) matches `sahi_r1_validation_report.md` lines
  68–71 [VA]. The within-iteration order control is new.
- **Counterbalancing (alternating start).** Iterations are indexed from 0, separately for warm-up
  (0–49) and measurement (0–299).
  - In an even iteration, arm A is timed first and then arm B.
  - In an odd iteration, arm B is timed first and then arm A.
  - Both arms of an iteration use the same validation image, and each arm's timed span includes
    its own image read.
  - This gives 150 AB and 150 BA measured iterations.
  - Each raw sample records its `order` (`AB` or `BA`) and its position within the iteration
    (`first` or `second`).
- **Statistics.** G7 uses arm B's p95 over all 300 measured samples. As non-decision diagnostics,
  p50/p95 are also reported per arm, split by position (first or second).
- **Reading note, no rule changed.** Contract §6.4 says arm B runs "one classifier forward on MPS
  for all of them". When an image has no source-class box at conf 0.20, no classifier forward runs.
  The sample is still timed and recorded.
- **Live inference.** The latency arm runs live YOLO11s-54 pilot inference and live CompactCNN
  inference on local MPS, on validation images only. This is covered by the authorization record,
  §3.B. It applies only after this addendum passes independent QA. Contract §1's ban on YOLO
  inference still applies, unchanged, to the **accuracy** arm, which uses the pinned CSV.

## 4. C4 (recommended): exact `crop_invalid` predicate

**QA proposal (quoted):** "Define `crop_invalid` as: clip the raw box to the image, then non-finite
or non-positive extent, or `crop_bounds` raises. Cite lines 174–175 and 192–195. Pin
`detector/d1_cascade_classifier/data.py` `e55fbadd…63ed5d`."

**Source readback [VA]**, `detector/colab/evaluate_cascade_b0_r1.py` (`8bedb4c1…6b42`, unchanged):

- lines 174–175 open the image and call `source.convert("RGB")`;
- lines 192–193 clip x to `[0, image.width]` and y to `[0, image.height]` with NumPy `clip`;
- line 194 keeps only rows with `np.isfinite(boxes).all(1) & (x2 > x1) & (y2 > y1)`;
- line 195 applies that keep-mask;
- lines 49–52 (`crop_bounds`) raise `ValueError("invalid predicted box")` unless the box is
  finite and `0 ≤ x1 < x2 ≤ W` and `0 ≤ y1 < y2 ≤ H`.

`detector/d1_cascade_classifier/data.py` lines 21–23 apply `/255`, then `(x − 0.5)/0.5`, matching the
evaluator's normalisation (lines 164–168 and 200–203).

**Resolution [P].** For each candidate whose original `yolo_id` is a source class:

1. Open the image with PIL and call `convert("RGB")`. Let `W` and `H` be its size.
2. Parse `x1, y1, x2, y2` from the CSV as float64 into `b`. Clip `b[[0, 2]]` to `[0, W]` and
   `b[[1, 3]]` to `[0, H]` with `np.clip`, as at evaluator lines 192–193. This follows NumPy
   semantics: ±inf becomes the bound and NaN stays NaN.
3. `crop_invalid = not np.isfinite(b).all() or b[2] <= b[0] or b[3] <= b[1]`, as at line 194.
4. Otherwise call the pinned `crop_prediction(image, b)` (lines 62–66). If `crop_bounds` raises
   `ValueError`, the candidate is `crop_invalid`. After steps 2–3 this branch should never fire;
   it is a defensive backstop.
5. A `crop_invalid` candidate keeps its original class `s` and is written with `crop_invalid=1`
   and empty probability fields. The run counts and reports it.
6. The clipped box `b` is used **only** as the crop input. The box scored in arm B is the original
   CSV box, unchanged (contract §2).

**Expected count [VA, CSV coordinates only, no GT matching].** 0 of the 798 source-class rows lie
outside `[0, 960] × [0, 540]` or have non-positive extent. So clipping is a no-op for every source
row, and the expected `crop_invalid` count is 0. The executor still reports the actual count.

**Pin [VA]:** `detector/d1_cascade_classifier/data.py` SHA-256
`e55fbaddea154131a0ef20f8d2653150b0f2c8eecdc8ff31dbcb16d6a463ed5d`. The author rehashed it; it
matches the QA record.

## 5. C5 (recommended): τ comparison dtype

**QA proposal (quoted):** "Fix the τ comparison: float32 softmax cast to float64 and compared
`>= 0.80`, inclusive. Note that the argmax clause is implied."

**Resolution [P].**

1. `p` is the CPU float32 output of `torch.softmax(logits, dim=1)`, converted with `.numpy()`, so it
   stays float32.
2. `top1 = int(np.argmax(p))`; on an exact tie NumPy returns the first index.
3. `pt = float(p[t])` is an exact float32 → float64 conversion.
4. Relabel **iff** `top1 == t and pt >= 0.80`, where `0.80` is the float64 literal. The comparison
   is inclusive.
5. Boundary. The float32 value nearest 0.8 is 0.800000011920928955078125, which relabels. The next
   float32 below it, 0.7999999523162841796875, does not. Both are required unit cases in the
   step-3 source QA.
6. For τ = 0.80 the argmax clause is implied: `pt ≥ 0.8 > 0.5` means `t` is the unique maximum. It
   stays in the rule because it is harmless. For the descriptive τ = 0.50 grid point, it still
   binds in an exact two-way tie at 0.5.
7. `p_target`, `p_source` and every value in `fusion_r1_crop_probs.csv` are written as
   `repr(float(v))` of the float32 value. A model-free QA recompute of F1 therefore reproduces
   every decision bit for bit.
8. The MPS decision recompute and the τ ∈ {0.50, 0.95} sensitivity grid use the same comparison.

## 6. C6 (recommended): bootstrap-equivalence test in §8 step 3

**QA proposal (quoted):** "Restate the §8 step 3 bootstrap equivalence test as in F7." F7 says
`group_bootstrap` returns CIs only for agnostic recall and FP/image. It proposes the wording: "with
the same seed and `rng.choice(sorted(groups))` draw sequence, the paired implementation's arm-A
agnostic-recall and FP/image CIs equal `group_bootstrap(frames_A, 0.20)` exactly, and an arm B
identical to A gives Δ CI [0, 0]."

**Resolution [P].** The contract §8 step-3 bullet "that the paired bootstrap at Δ = 0 equals
`metrics.group_bootstrap`" is replaced by the following test.

- The paired implementation uses `np.random.default_rng(20261018)`, 1000 rounds, and per round
  `rng.choice(sorted(groups), size=len(groups), replace=True)` over the 9 D-02 groups. This is the
  draw sequence of `metrics.group_bootstrap` at `detector/m1/metrics.py:298-317` [VA, read]. Each
  round's draw is applied to both arms.
- **(a)** The arm-A agnostic-recall CI and FP/image CI from the paired implementation equal
  `group_bootstrap(frames_A, 0.20)` exactly (float equality).
- **(b)** When arm B is set identical to arm A, the Δ correct-class-recall CI is exactly
  `[0.0, 0.0]`.

`group_bootstrap` computes no class-aware recall. G2's Δ CI therefore comes from the paired
implementation itself. (a) checks that its draws are the reference draws, and (b) checks that the
pairing is correct.

## 7. C7 (recommended): downgrade U2, the common-path bundle

**QA proposal (quoted):** "Downgrade U2 with the pins listed in F9." F9 also asks the addendum to
say "whether the executor may use the bundle as `root` for the common-path AP".

**Verification by this author [VA].**

| Check | Result |
| --- | --- |
| `tmp/yolo11n_n1_extract_r1/manifest.json` SHA-256 | `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da` |
| Manifest members rehashed | 8,579 OK, 0 mismatched, 0 missing. Manifest `sealed_test_accessed=false`, `test_included=false`, val counts 376 images and 624 boxes |
| `tmp/yolo11n_n1_extract_r1/data/yolo54_predictions_val.csv` | `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893`, byte-identical in hash to the run-directory `d1_vre_r2/predictions_conf0001.csv` |
| `diff -rq tmp/yolo11n_n1_extract_r1/data/labels54/val data/processed/m1_yolo_val_vrl_r3/labels/val` | no difference; 376 files |
| Bundle `data/images/val` vs the R3 export `data/processed/m1_yolo_wp38_r1_integration_r4/images/val` (the `IMAGE_DIR` of `val_reeval_r2.py`) | same 376 names, 376/376 byte-identical. The bundle's `{name: sha256}` roster hashes to `24e2a67d1e176a7e09caf4b1f6daa2bf5240981d00c8e1a535640e6b8066118e`, the contract's image roster. **This finding is new; the QA record did not check images** |
| `tmp/yolo11n_n1_extract_r1/data/val_groups.json` | `fdb2ef8ff2cc684970b6330747d7746ccfe6dfd77d60903d10233de66697d682`, rehashed. Its equality to the WP36 group map for all 376 stems was verified by the QA record (F9), not re-verified here |
| `results/experiments/yolo11n_n1_seed_20261018_r1_r1/evaluation_r1/comparison_n1_r1.json` | `0447a1bdc2aec56980b63f3fea5340be9a1d455ed9b7872ac503c4d65779a0db`, rehashed. That it records common-path mAP50 0.8520835680058519 and mAP50-95 0.6088678434901063 is per the QA record (F9) |

**Hazard [VA].** `data/processed/m1_yolo/images/val` is **not** the same file set: at least stems
1319 and 1320 differ in suffix (`.jpg` there, `.png` in the bundle). Do not use it as an image source
for this run.

**Resolution [P].** U2 is downgraded. It no longer reads "bundle not found / possibly blocked". It
now reads: **"bundle located and verified; Step 0 remains mandatory and binding."**

- The executor **may** use `tmp/yolo11n_n1_extract_r1/data` as the common-path bundle. That covers
  the `root` for the common-path AP, the image source for crops, the labels and the group map.
  Equivalently, it may use the R3 export images with the R3 labels.
- Whichever source it uses, three hashes are required at execution: image roster `24e2a67d…118e`,
  label roster `dc72ebd9…8343` (contract §6) and CSV `87884c53…c893`.
- The bundle lives under the untracked `tmp/`. Its full manifest (8,579 members) is re-verified
  at execution, before Step 0. Any mismatch blocks the run.
- Arm A's authoritative input stays the run-directory CSV (contract §2). The bundle CSV may be used
  only because its hash is byte-identical.
- **Step 0 stays the binding check.** If the scorer cannot reproduce TP 547, FP 150, Σ hits 457,
  per-class hits 66/18/12/55 and 14 (yolo_id 40, from C1), agnostic recall 0.876603, FP/image
  0.398936 and common-path mAP50/50-95 0.8520835680/0.6088678435 within 1e-9, the outcome is
  `INVALID`.

## 8. C8 (minor): R2-combined variant selection in the §7 reuse list

**QA proposal (quoted):** "Add the R2-combined variant selection to the §7 reuse list."

**Resolution [P].** Contract §7's list of validation reuse gains one item: **the choice of the R2
"combined" variant over the group-balance-only and jitter-only variants.** It was chosen because
it alone met the validation cascade comparison gate. `cascade_classifier_improvement_r2_report.md`
lines 90–92 [VA, read] say "The combined candidate meets this validation gate; group balance and
jitter alone do not". That gate used the same validation frames. This adds to the in-sample
optimism already disclosed in §7. Like the rest of §7, it changes no rule.

## 9. What does not change [P]

Apart from §1–§8, nothing in the contract changes. In particular:

- **Pairs**: P1–P6 (yolo_id 10→48, 19→7, 40→42, 7→33, 41→42, 12→8), and the no-chaining rule.
- **τ = 0.80**, the relabel-only rule F1, and the descriptive-only sensitivity grid and
  leave-one-out results.
- **The primary endpoint**: correct-class recall at conf 0.20, reference 457/624.
- **G1–G7 thresholds**: G1 ≥ 467; G2 lower bound > 0 (1000 rounds, seed 20261018, 9 groups);
  G3 FP ≤ 150 and TP = 547; G4 hits ≥ 66/18/12; G5 ≤ 2 lost hits plus the D-05 reference clause;
  G6 Δ mAP50 ≥ 0 and Δ mAP50-95 ≥ 0; G7 p95 ≤ 100 ms. G4b is **added**; no existing threshold
  moves.
- **The evaluation set**: 376 R3 validation frames, 624 GT, 9 D-02 groups, ignore regions unused,
  `test` paths refused.
- **The classifier checkpoint** (`d1e69eef…50cc`), the pilot CSV, the crop geometry, CPU float32
  for the verdict, and the scorers.
- **Outputs and their schemas, the `O_EXCL` write rule and the model-free `verify` subcommand.**
  Two additions: `fusion_r1_eval.json` gains the §2 reporting fields, and the latency JSON gains
  the §3 per-sample `order` and `position`.
- **The flags**: `sealed_test_accessed=false`, `training_authorized=false`,
  `app_enable_authorized=false`, `threshold_lock_written=false`, `d05_changed=false`.
- **Contract §7**: a GO is only an in-sample candidate; it is never a D-05 pass, a threshold lock or
  an app decision.

**Manifest binding [P].** `fusion_r1_manifest.json` pins this addendum and the authorization
record by SHA-256, next to the contract. As the contract requires, it still pins no QA record.

## 10. Unknowns carried forward [U]

- U1 (no independent confirmation scene set), U3 (classifier behaviour on the source classes), U4
  (size of harm to strong classes), U5 (environment and CPU/MPS agreement) and U6 (the 378/376
  roster difference) stay as stated in the contract.
- U2 is downgraded by §7.
- Whether this addendum's rules are themselves correct is for its independent QA.

## 11. Commands run (read-only; no model loaded, no inference)

| Command | Result |
| --- | --- |
| `git status --short \| head -60` | 12 ` M` Owner files (`PROJECT_MEMORY.md`, `docs/product_roadmap.md`, `docs/review_index.md`, `scripts/run_parallel_checks.py`, 5 × `src/cpv301_autodrive/*`, 3 × `tests/*`), plus many `??` |
| `git log --oneline -3` | `17db663 docs(review): pre-registered YOLO54+CompactCNN fusion R1 contract, QA PASS giới hạn`; `399bf70 …`; `5e3fa2a …` |
| `graft check .` | `graph check: OK — the wiring graph is in sync with the code`; deep layer not built |
| `shasum -a 256` on the contract, QA record, `data.py`, bundle manifest and CSV, `val_groups.json`, `comparison_n1_r1.json`, evaluator, `metrics.py`, VRE-R2 eval JSON | all match the values in this file and in the contract |
| `nl -ba` readback of evaluator lines 46–66, 160–205; `data.py` 15–25; `metrics.py` 74–116, 295–320; SAHI report 66–72; R2 report 86–94 | as cited |
| `python3 -I` read of `eval_val_vrl_r3_vre_r2.json` `primary_r3.fixed_conf_0_20` | DK 39: critical, not gated, hits 14, support 15; Σ hits 457 over 19 classes; TP 547, FP 150 |
| `python3 -I` pilot CSV coordinate check (no GT matching) | 1,999 rows, 798 source rows, 0 out of bounds or degenerate |
| `python3 -I` bundle manifest verification | 8,579 OK, 0 bad, 0 missing |
| `diff -rq` bundle `labels54/val` vs R3 labels | identical |
| `python3 -I` image hash comparison, bundle vs R3 export | 376/376 identical; both rosters `24e2a67d…118e` |

## 12. Flags

`sealed_test_accessed=false`, `training_authorized=false`, `inference_run=false`,
`fusion_metric_computed=false`, `app_enable_authorized=false`, `threshold_lock_written=false`,
`d05_changed=false`, `contract_edited=false`, `commit_or_push=false`.
