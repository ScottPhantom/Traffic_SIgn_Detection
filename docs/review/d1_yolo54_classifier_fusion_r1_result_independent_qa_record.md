# D1 YOLO54 + CompactCNN classifier fusion R1 — independent result QA record (contract §8 step 5)

Status: `RESULT_QA_COMPLETE`
Boundary: `MODEL_FREE_READBACK_NO_RUN_NO_CLASSIFIER_NO_YOLO_NO_TRAINING_NO_SEALED_TEST_NO_APP`
Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Reviewer: Claude Code (Opus 5.5), side session started from the coordinating session. I did not
write the contract, the addendum, the scorer or its tests, and I did not perform the execution.
Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, branch `yolo11n-dual-track-r1`,
HEAD `17db663`. Many uncommitted Owner changes exist; this record is the only file I created, and I
edited no existing file and no output file.

I did not re-run `run`. I did not load the classifier and did not run YOLO. Every number below was
recomputed from the two output CSVs, the pilot CSV, the R3 labels and the verified bundle, using
`detector/m1/metrics.py` and the pinned `evaluate_cascade_b0_r1.py` AP integrator and baseline
loader. My scratch scorer asserts that the fusion module is not imported. The only call into the
fusion module is the R9 `verify` gate the brief requires.

Verdict: PASS giới hạn — the `NO_GO` outcome (C2 row 2) is confirmed: every decision input (89 relabels, TP/FP 547/150 in both arms, hits 457 → 456, per-class hits, mAP50/50-95, the paired Δ CI [−0.04975, +0.05747], latency p95, the guard flags and the failed-guard list) reproduces exactly from the CSVs. The limits are scope limits that cannot change the outcome: model-free QA cannot attest that the softmax values or latency timings were produced by the models it trusts as measured inputs, the D-05 reference constants come from `detector/m1/contract.py`, which the manifest does not pin (it is committed and clean), and the reported-not-decisive paired mAP CI was not recomputed.

## 1. Pins verified (SHA-256, rehashed 2026-11-05)

**Outputs under review.** Directory
`results/experiments/D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2/classifier_fusion_r1/`.

| File | SHA-256 | Brief | Manifest |
| --- | --- | --- | --- |
| `fusion_r1_predictions_conf0001.csv` | `916ad347abab19de1c0256966e78be640bea4fabc959a2213628ed8167b5084e` | match | match |
| `fusion_r1_crop_probs.csv` | `e0456a4f551c8caad7eaad2ca05de30f6377b03f61f4f3ef0752a11ab2e31986` | match | match |
| `fusion_r1_eval.json` | `e425f38f2c895449519263873cad64cda19571045ac8023ce274f17d000d2edf` | match | match |
| `fusion_r1_latency_mps.json` | `bd7a0f0873093a23a2710c18481ca7cf6da7aff3205517a8bfebdc5a4adc03c6` | match | — |
| `fusion_r1_manifest.json` | `664ad91306c01c8dd4152d8de79cffc9aef6d890be6695dd6b1bb59d1bd1dee2` | match | (self) |

The SHAs were rehashed again after the `verify` gate and are unchanged.

**Binding spec and sources.**

| Item | SHA-256 |
| --- | --- |
| Contract `docs/review/d1_yolo54_classifier_fusion_r1_contract.md` | `40cbe72ff095b8aea9d2253c02a52c013797b2148febc4bbbd647e68a77c700c` |
| Addendum 1 `docs/review/d1_yolo54_classifier_fusion_r1_addendum_1.md` | `fa2ea121623a0072256cd56e88ba1d1e60a90cd85a51f0869fa5d70623bdd6e9` |
| Owner authorization `…_owner_authorization_2026-11-05.md` | `9f8c5f20c4dab52258d64270d490fc720c941bc1478a22550a549560e3556fcd` |
| Contract QA record | `aa3c4e384118a02fa28fb790d056951221334c7ecdefa410e02f381b83d5e902` |
| Addendum QA record | `b483788d4056722ccb2a6e6192afced592cc887afbcc844e3527a956874e632c` |
| Source QA record | `c40f1c585c66601b781bdbd049ae133d463d349b0dce9c476aabb30342abd01c` |
| Delta source QA record | `21d52706ad2f9b5663b41537ee22a1c38e1b66c9a14548d552720b8407c48d86` |
| Module `detector/m1/classifier_fusion_r1.py` | `c28033cf3494ef5c6e01af30fdb4aec49dc1470a760565c6bf28744ca836c271` (= delta-QA'd SHA) |
| Tests `detector/tests/test_classifier_fusion_r1.py` | `7ef2a45aa4fb151dbc69108792e0e64c9d2eb8ef32e276aa999c05a583fb05be` (= delta-QA'd SHA) |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` |
| `detector/colab/evaluate_cascade_b0_r1.py` | `8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42` |
| `detector/colab/run_cascade_b0_r1.py` | `0ece03891ebe0f8c318efd7a062fdb8d799d4cf9cc357b0cf8840b4103ad876a` |
| `detector/d1_cascade_classifier/data.py` / `model.py` | `e55fbaddea154131a0ef20f8d2653150b0f2c8eecdc8ff31dbcb16d6a463ed5d` / `fdcbc4156a4bef9b5eed56a8ebc58746408a14f6558cd4b3c38a4e49df47b77a` |
| `detector/m1/sahi_eval_r1.py` / `val_reeval_r2.py` | `2ca327ed2901b03b1c302457c881eac0bdf0018c601ac413f70bee489163ebeb` / `2a0823faa15f7cb9cecb64a1f21e48e8b5b84f7e7f949683683a6992ee13ccc9` |
| `detector/m1/contract.py` (D-05 constants; **not** in the manifest) | `901e7e372d9660cd79e6bfcab43684b1693f0a4aafad9f4c331fd8f04ba6bbbf`, tracked, no diff vs HEAD |
| Pilot CSV `d1_vre_r2/predictions_conf0001.csv` | `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893` |
| Bundle CSV `tmp/yolo11n_n1_extract_r1/data/yolo54_predictions_val.csv` | `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893` |
| Bundle manifest `tmp/yolo11n_n1_extract_r1/manifest.json` | `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`; 8,579 members rehashed, 0 bad |
| Bundle `data/val_groups.json` | `fdb2ef8ff2cc684970b6330747d7746ccfe6dfd77d60903d10233de66697d682` |
| Image roster (`json.dumps({name: sha256}, sort_keys=True)`) | `24e2a67d1e176a7e09caf4b1f6daa2bf5240981d00c8e1a535640e6b8066118e`, reproduced |
| Latency timed sequence | `2bb0c9f03206b938c500709df05d823db5aa1478888fe3bb61a7a96cb8f5f3fa`, reproduced from my own schedule |

All 31 manifest pins (3 documents, 22 inputs, 2 sources, 4 outputs) were rehashed by my script, with
0 mismatches. They include the pilot `best.pt` `5d5815a9…b633`, the classifier `best.pt`
`d1e69eef…50cc` and its `contract.json` `b659a4fd…d5a`, the VRE-R2 eval JSON `559c6c6a…7c87`, the
SAHI latency JSON `a8b06702…11b8`, `m1_yolo_classes.csv` `7cda296a…d58d242`, `signnames.csv`
`cd885b46…affca`, `data.yaml` `4cd83035…8bd0` and `wp36_r1_split_frames.csv` `8e197d9c…823a`.

## 2. Check table

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| R1 | Integrity and provenance | **PASS** | 5 output SHAs match the brief and the manifest. 31/31 manifest pins match. The manifest's `sources` pin is the module and tests at the delta-QA'd SHAs. The module mtime (15:11:53) and tests mtime (15:13:45) predate the delta QA record (15:36:34), which predates the outputs. The directory holds exactly 5 files, no stop report, no temp or duplicate file. The mtimes fall within 2.1 ms of one another (epoch 1793868846.4402–.4423, 15:54:06), consistent with one write-once publish. No other file under `results/` or `tmp/` is newer than the delta QA record. All manifest, eval and latency flags are false: `sealed_test_accessed`, `training_authorized`, `app_enable_authorized`, `threshold_lock_written`, `d05_changed`, `push_authorized`, `rerun_after_results_authorized`. Bundle 8,579/8,579 members OK |
| R2 | F1 recomputation, model-free | **PASS** | 1,999/1,999 predictions rows in pilot order. `stem,rank,yolo_id,conf,x1,y1,x2,y2` are text-identical to the pilot CSV (0 mismatches), so boxes, scores and order are unchanged. 798 crop-prob rows equal exactly the 798 source-class rows. Every probability is an exact float32. Max softmax sum error is 2.9e−7. I re-applied F1 (P1–P6 in yolo_id space, `argmax(float32 p) == t and float(p[t]) >= 0.80`, original class only): **0/1,999 `fused_id` mismatches**. `derived_key`, `fused_derived_key`, `pair`, `p_target`, `p_source` (`repr`), `top1_id`, `relabelled` and `crop_invalid=0` all agree (0 mismatches). **89 relabels**: P1 41, P2 0, P3 4, P4 22, P5 0, P6 22. At conf ≥ 0.20: 37 (24/0/1/8/0/4). Candidates per pair: 217/32/71/152/26/300. P2 made no relabel, so the P2→P4 no-chaining case did not arise in the data. The nearest decisions to τ were 0.7952 (kept) and 0.8118 (relabelled); none lies at the float32 boundary |
| R3 | Metrics, own scorer | **PASS** | Arm A: TP 547, FP 150, hits 457, agnostic recall 0.8766025641, FP/image 0.3989361702, mAP50 0.8520835680058519, mAP50-95 0.6088678434901063 (Step 0 reproduced). Arm B: TP 547, FP 150, hits **456**, mAP50 **0.8335054474607682**, mAP50-95 **0.5950155312404559**. Δ mAP50 −0.018578, Δ mAP50-95 −0.013852. All per-class hits and all 19 per-class AP50 values equal the eval JSON (table §3). Help/harm at conf 0.20, total: help 13, harm 14. By pair, isolated: P1 4/12, P2 0/0, P3 1/0, P4 6/2, P5 0/0, P6 2/0. All equal the eval JSON. By GT size bin and by relabelled-box size bin: equal. Same-class overlaps at IoU ≥ 0.70 involving a relabelled box: 54 at all scores and 8 at conf ≥ 0.20, equal |
| R4 | Paired bootstrap | **PASS** | My paired implementation (`default_rng(20261018)`, 1000 rounds, `rng.choice(sorted(9 groups), 9, replace=True)`, same draw for both arms, numpy-linear percentiles): Δ correct-class recall CI **[−0.04975014459876656, 0.05747198275862073]**, exactly equal. Share of rounds with Δ > 0 is 0.453. Arm CIs [0.6070, 0.8275] / [0.6082, 0.8429], equal. Addendum C6(a): my arm-A agnostic-recall and FP/image CIs equal `metrics.group_bootstrap(frames_A, 0.20)` float-exactly. The CI is not confined by any group: by group, C0020 is +10 (49 → 59), C0044 −12 (90 → 78), C0045 +1, all others 0 |
| R5 | Decision | **PASS** | Recomputed guards: S0 true; L true (300 + 300 valid); Δ = −1 hit (≤ 0); G1 false (456 < 467); G2 false (lower −0.0498 ≤ 0); G3 true (547/150 both arms); G4 false (DK 7 64 < 66; DK 32 24 ≥ 18 and DK 41 13 ≥ 12 pass); G4b true (DK 39 14 ≥ 14); G5 false (DK 10 loses 12 > 2; DK 6/8/12/23/34/46 pass, and all still meet the D-05 reference 0.50); G6 false (both Δ < 0); G7 true (58.10 ≤ 100 ms). C2 table: row 1 does not match (S0, G3 and L hold). Row 2 matches through Δ ≤ 0, ¬G4 and ¬G5 and ¬G6. **Outcome `NO_GO`, `outcome_row` 2**, equal to the eval JSON. The failed list `[delta_positive, G1, G2, G4, G5, G6]` is complete and correct: it omits exactly the holding conditions S0, L, G3, G4b, G7 |
| R6 | Latency | **PASS** | 600 raw samples: iterations 0–299, one A and one B per iteration, all valid, `error` null, finite, > 0. Even iterations are `AB` (A first), odd iterations `BA` (B first): 150 each. Every sample's `order`/`position` is consistent. Both arms of an iteration use the same image, index (50 + j) mod 376, and the name equals the sorted validation roster at that index. Image roster `24e2a67d…118e` and timed-sequence SHA `2bb0c9f0…f5f3fa` were reproduced independently. Recomputed p50/p95: A 48.629/55.466 ms, B 50.362/**58.098** ms (Δ p95 2.632). B by position (diagnostic): first p95 58.52, second 56.64. All equal the eval JSON. Environment: torch 2.14.1 and ultralytics 8.4.172, the same as the SAHI R1 latency JSON, so `versions_match_sahi_r1=true` is correct. M1 Pro MPS, conf 0.20, IoU 0.70, imgsz 1280, max_det 300, warm-up 50 with 0 invalid. G7 uses arm-B p95 over all 300 samples, as Addendum C3 specifies |
| R7 | CPU/MPS | **PASS** | My CPU relabel set, recomputed from the crop-prob CSV, has 89 rows. The eval JSON's 89 `mps_relabel_rows` equal it as a set, and `differences` is empty. Every verdict quantity (R2–R5) was reproduced from the CPU crop-prob CSV alone, so only CPU feeds the verdict. Limit: the MPS rows are a run-recorded input; model-free QA cannot re-derive them |
| R8 | Interpretation limits | **PASS (noted, §4)** | — |
| R9 | Gates | **PASS** | `verify`: exit 0, `{"verified": true, "errors": []}`. ruff: "All checks passed!". `uv lock --check`: OK. `graft check .`: OK. The output SHAs are unchanged after `verify` |

## 3. Per-class hits at conf 0.20 (recomputed; equal to `fusion_r1_eval.json`)

| yolo_id | DK | Support | Hits A | Hits B | Guard |
| ---: | ---: | ---: | ---: | ---: | --- |
| 7 | 7 | 111 | 66 | **64** | G4 fails |
| 8 | 8 | 51 | 32 | 34 | G5 passes |
| 10 | 10 | 48 | 48 | **36** | G5 fails (loss 12) |
| 12 | 12 | 65 | 60 | 60 | G5 passes |
| 33 | 32 | 29 | 18 | **24** | G4 passes |
| 40 | 39 | 15 | 14 | 14 | G4b passes |
| 42 | 41 | 26 | 12 | 13 | G4 passes |
| 48 | 46 | 104 | 55 | 59 | G5 passes |
| 6 / 25 / 35 | 6 / 23 / 34 | 22 / 28 / 37 | 20 / 28 / 31 | 20 / 28 / 31 | G5 passes |
| others (0, 2, 3, 4, 5, 13, 14, 28) | — | 88 | 73 | 73 | unchanged |
| **Σ** | | **624** | **457** | **456** | |

Per-class AP50 moved only for 7 (0.7525 → 0.7802), 8 (0.7813 → 0.7884), 10 (0.9393 → **0.6866**),
12 (0.8649 → 0.8769), 33 (0.8968 → 0.9335), 40 (0.7413 → 0.7515), 42 (0.5350 → 0.5323) and
48 (0.8199 → **0.6284**). All 19 values were checked.

## 4. R8 — what the result does and does not show

- **Under the pre-registered rule, the outcome is `NO_GO`.** It fails through Δ ≤ 0, G4, G5 and G6.
  G1 and G2 also fail. This is a negative result for the single pre-registered configuration (six
  pairs, τ = 0.80, relabel-only), not a statement about classifier fusion in general.
- **In-sample validation only.** The 376 frames were reused for many selections (contract §7,
  Addendum C8), so even the gains are optimistically biased. Nothing here is a D-05 result, a
  threshold lock or an app decision. Behaviour output stays simulation only.
- **The mechanism is visible and offsetting.** The classifier helped weak target classes: DK 32 +6
  via P4, DK 46 +4 and DK 8 +2 via P1/P6, DK 41 +1 via P3. But P1 harmed P.130 (DK 10) by 12
  correct boxes (48 → 36; AP50 0.939 → 0.687), all in the 32–64 px bin and the D02-C0044 group, and
  P4 cost DK 7 two hits. Net −1 hit, with both mAP deltas negative.
- **No pair or τ may be re-selected from these numbers.** The descriptive `SENSITIVITY_NOT_DECISION`
  rows (reproduced exactly) include τ = 0.95 at 467 hits with a slightly positive Δ mAP, and
  leave-P1-out at 464 hits. Adopting either would be tuning on the validation set that produced
  it. Neither has a G2 CI, and neither is a candidate. They describe where the harm came from;
  they do not authorize a successor configuration.
- No re-run is proposed. Under the authorization record, any further fusion experiment needs a new
  contract, its own QA, new Owner authorization and data not used here.

## 5. Commands run

| Command | Result |
| --- | --- |
| `git status --short \| head -60` | 13 ` M` Owner files (`PROJECT_MEMORY.md`, `docs/product_roadmap.md`, `docs/review/cam_hanh_trinh_display_rename_r1_2026-11-04.md`, `docs/review_index.md`, `scripts/run_parallel_checks.py`, 5 × `src/cpv301_autodrive/*`, 3 × `tests/*`), then `??` files including `detector/m1/classifier_fusion_r1.py` |
| `git log --oneline -3` | `17db663 docs(review): pre-registered YOLO54+CompactCNN fusion R1 contract, QA PASS giới hạn`; `399bf70 …`; `5e3fa2a …` |
| `graft check .` (start and end) | `graph check: OK — the wiring graph is in sync with the code`; deep layer not built |
| `graft skeleton` on `metrics.py`, `evaluate_cascade_b0_r1.py`, `classifier_fusion_r1.py` | API orientation only. I read the module for definitions only (`same_class_overlaps` docstring, `latency_schedule` phase names, G5 reference source) and did not call it |
| `shasum -a 256` on outputs, module, tests, contract, addendum, 4 QA records, authorization, scorers, `contract.py`, bundle files | as in §1 |
| `stat -f "%Fm %Fc %z %N"` on the output files; `find results tmp -newer <delta QA record> -type f` | 5 files within 2.1 ms; only those 5 are newer |
| `(cd detector && uv run python <scratchpad>/qa_fusion_r1.py)` | exit 0, about 19 s. R1 pins and bundle, R2 F1, R3 metrics/AP/help-harm, R4 bootstrap with C6(a) equivalence, sensitivity, R6 samples, R7 set equality; output in the scratchpad (`qa_out.json`) |
| `python3 -I <scratchpad>/qa_extra.py` plus an inline timed-sequence hash | relabel box bins (lt16 0, 16–32 11/6, 32–64 42/21, ≥64 36/10), same-class overlaps 54/8, timed-sequence SHA reproduced |
| `(cd detector && uv run python -m m1.classifier_fusion_r1 verify)` | exit 0; `{"verified": true, "errors": []}` |
| `uv run ruff check src tests` | `All checks passed!` |
| `uv lock --check` | `Resolved 201 packages`, exit 0 |

The scratch scripts live in the session scratchpad
(`/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/03ed18b0-aba1-4bf3-b2a0-76ee46be2a8a/scratchpad/`),
not in the repo.

## 6. Observations, none blocking

- **O1.** `detector/m1/contract.py` supplies the D-05 per-class references (critical 0.70,
  other 0.50) that G5's second clause reads, but `fusion_r1_manifest.json` does not pin it. It is
  committed, last changed in `1842a1b`, with no working-tree diff, SHA `901e7e37…bbbf`. The verdict is
  insensitive to it, because DK 10 fails G5 on the loss clause (12 > 2) whatever the reference. A
  successor manifest should pin it.
- **O2.** The paired mAP50/50-95 bootstrap CIs (`REPORTED_NOT_DECISIVE`: [−0.0687, 0.0078] and
  [−0.0510, 0.0057]) were not recomputed. They do not enter any guard.
- **O3.** Model-free QA treats `fusion_r1_crop_probs.csv`, the MPS relabel rows and the latency
  `ms` values as measured inputs. It verifies their internal consistency and every downstream
  number, not their physical origin. This is inherent to the contract's design (§8 "so QA can
  recompute F1 without a model").

## 7. Flags

`sealed_test_accessed=false`, `training_authorized=false`, `inference_run=false`,
`classifier_loaded=false`, `yolo_run=false`, `run_rerun=false`, `app_enable_authorized=false`,
`threshold_lock_written=false`, `d05_changed=false`, `existing_files_edited=false`,
`output_files_edited=false`, `commit_or_push=false`.
