# D1 YOLO54 + CompactCNN classifier fusion R1 — Addendum 1 independent QA record

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Reviewer: Claude Code (Opus 5.5), independent side session. Not the author of the addendum, the
authorization record, the contract or the contract's QA record.
Scope: **document review only**. No fusion was implemented or executed. The classifier ran on no
crop, no YOLO or classifier inference ran, nothing was trained, and no fusion metric was computed
or viewed. The only metric computed was a model-free recount of the **arm A** reference (pure pilot
CSV against the R3 labels), as the task brief allowed.
Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, branch `yolo11n-dual-track-r1`,
HEAD `17db663`.

Reviewed files:

| File | SHA-256 (rehashed, matches handoff) |
| --- | --- |
| `docs/review/d1_yolo54_classifier_fusion_r1_addendum_1.md` | `fa2ea121623a0072256cd56e88ba1d1e60a90cd85a51f0869fa5d70623bdd6e9` |
| `docs/review/d1_yolo54_classifier_fusion_r1_owner_authorization_2026-11-05.md` | `9f8c5f20c4dab52258d64270d490fc720c941bc1478a22550a549560e3556fcd` |

Verdict: PASS giới hạn — C1 and C2 are resolved correctly and C3–C8 are resolved; the outcome mapping is total and unique, no existing rule is loosened, and the authorization record is scoped correctly. No correction is required before execution; Q1–Q6 below are recommended clarifications to be bound in the step-3 implementation and checked by its independent source QA.

**Execution status.** Under the authorization record §3 reading rule, a PASS giới hạn satisfies
condition B only if it lists no correction required before execution. This record lists none.
Condition B is therefore met: contract §8 steps 3–5, as amended by Addendum 1, **may proceed**, once,
offline, on validation images only. The next step is step 3 (scorer implementation plus independent
source QA before any real run), not the execution itself.

`sealed_test_accessed=false`

## Start-of-task state

- `AGENTS.md` and the head of `PROJECT_MEMORY.md` were read. The sibling note
  `fusion_r1_addendum_1_notes.md` in the shared notes folder was read as data.
- `graft check .`: `graph check: OK — the wiring graph is in sync with the code`; deep layer not built.
- `git log --oneline -3`: `17db663 docs(review): pre-registered YOLO54+CompactCNN fusion R1 contract, QA PASS giới hạn`;
  `399bf70 feat(d1): paired A3−pilot validation CIs with independent QA PASS`;
  `5e3fa2a docs(review): R3 addendum — A3 executed via D1-A3-R2, criteria not met`.
- `git status --short | head -60`: 12 ` M` Owner files (`PROJECT_MEMORY.md`, `docs/product_roadmap.md`,
  `docs/review_index.md`, `scripts/run_parallel_checks.py`, `src/cpv301_autodrive/app_pages/07_demo.py`,
  `src/cpv301_autodrive/dataset01_view.py`, `src/cpv301_autodrive/dataset01_view_r1.py`,
  `src/cpv301_autodrive/presentation.py`, `src/cpv301_autodrive/views.py`,
  `tests/test_e0_compute_readiness.py`, `tests/test_web_app.py`,
  `tests/test_wp35_rare_class_enrichment.py`), then `??` entries under `detector/colab/`,
  `detector/m1/` and `detector/tests/`. The two reviewed files are untracked (`??`). This record is
  the only file this review created in the repository; no existing file was edited.

## A1–A7 summary

| # | Check | Result | Key evidence |
| --- | --- | --- | --- |
| A1 | Pins | **PASS** | 42/42 files `OK` under `shasum -a 256 -c`: the 33 contract §10 pins, `data.py`, bundle manifest, bundle CSV, `val_groups.json`, `comparison_n1_r1.json`, contract, contract QA record and both reviewed files. Manifest member `data/yolo54_predictions_val.csv` = `{bytes 203251, sha256 87884c53…c893}`. All 8,579 manifest members rehash OK. |
| A2 | C1 resolved | **PASS** | Model-free recount with `m1.metrics.operating_point(frames_A, 0.20)`: `per_class_hits[40] = 14`, support 15. VRE-R2 JSON `classes["39"]` = 14/15, critical, not gated. Keys are GT `yolo_id`. Every source class with validation support is guarded (7 G4, 10/12 G5, 40 G4b); 19/20/41 have 0 GT. Every target is guarded. |
| A3 | C2 resolved | **PASS** (Q1) | All 3,072 combinations of S0, L, G1–G7, G4b and sign(Δ) ∈ {<0, =0, >0} enumerated: 0 gaps; each maps to exactly one row; the first-match table agrees with the QA precedence on every combination (0 disagreements). "G7 measured in every case" is consistent with "L false → `INVALID`". |
| A4 | C3–C8 | **PASS** (Q2–Q5) | C3 counterbalancing well-defined, 150 AB / 150 BA, §6.4 retitled. C4 predicate matches evaluator 174–175, 192–195 and `crop_bounds` 46–52; 0/798 source rows invalid. C5 boundary values exact. C6 draw sequence equals `group_bootstrap` 298–317. C7 claims re-verified, including images and group map. C8 quote matches R2 report 90–92. |
| A5 | Nothing else changed | **PASS** (Q6) | Pairs, τ, primary endpoint, G1–G7 thresholds, evaluation set and flags are unchanged. Changes are additions or tightenings only (G4b, Step 0 + 14, L → `INVALID`, reporting fields). No silent loosening found. |
| A6 | Authorization record | **PASS** (Q5 note) | Owner words quoted verbatim with relay caveat and [U]. Scope = addendum now; after QA PASS, §8 steps 3–5 once, offline, CPU classifier, MPS recompute, MPS latency arm, validation images only. All seven exclusions explicit. The added [P] reading rule only narrows. No over-reach. |
| A7 | Gate | **PASS** | `uv run ruff check src tests` → `All checks passed!` (exit 0); `uv lock --check` → `Resolved 201 packages in 4ms` (exit 0). |

## Detailed findings

### A1 — pins

- `shasum -a 256 -c` over a 42-line pin list returned `42 OK`, 0 failures. The list holds every
  contract §10 pin (33 files, the pilot `run_contract.json`/`args.yaml` row counted as two), plus
  `detector/d1_cascade_classifier/data.py` (`e55fbadd…63ed5d`), `tmp/yolo11n_n1_extract_r1/manifest.json`
  (`8e6ffe77…bb6da`), `tmp/yolo11n_n1_extract_r1/data/yolo54_predictions_val.csv` (`87884c53…c893`),
  `tmp/yolo11n_n1_extract_r1/data/val_groups.json` (`fdb2ef8f…d682`),
  `results/experiments/yolo11n_n1_seed_20261018_r1_r1/evaluation_r1/comparison_n1_r1.json`
  (`0447a1bd…779a0db`), the contract (`40cbe72f…c700c`), the contract QA record (`aa3c4e38…e902`) and
  the two reviewed files.
- The manifest is a dict with key `members` (8,579 entries `{bytes, sha256}`). Its member
  `data/yolo54_predictions_val.csv` is `{"bytes": 203251, "sha256": "87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893"}`,
  equal to the run-directory `d1_vre_r2/predictions_conf0001.csv`.
- A full manifest re-verification (size and SHA-256 of every member) gave `8579 ok 0 bad 0 missing`.
  No member path has a `test` component. Manifest `sealed_test_accessed=false`, `test_included=false`,
  `counts.val = {images 376, boxes 624}`.

### A2 — C1 (DK 39 / yolo_id 40)

- **Arm-A value.** Frames were built from the pinned pilot CSV (1,999 rows) and the R3 labels
  (`data/processed/m1_yolo_val_vrl_r3/labels/val/`, 376 files). Image sizes were read from the bundle
  images' headers; all are 960×540. `operating_point(frames, 0.20)` from `detector/m1/metrics.py`
  (`d24570f8…`) returned TP 547, FP 150, GT 624, agnostic recall 0.876603, FP/image 0.398936,
  Σ per_class_hits 457 over 19 classes, and `per_class_hits[40] = 14`, `per_class_support[40] = 15`.
  The VRE-R2 JSON gives `classes["39"] = {critical: true, gated: false, hits: 14, support: 15}`, and
  `classes["40"]` is absent (DK 40 = yolo 41 has no support). **14 is the correct arm-A value**, and
  the recount also reproduces every other contract Step 0 operating-point reference (66/18/12/55 for
  yolo 7/33/42/48).
- **Index space.** `operating_point` keys `per_class_hits` by `frame.gt_classes`, which hold the label
  files' first column, i.e. `yolo_id`. The addendum's `per_class_hits[40]` is therefore correctly in
  yolo_id space, and it reports both keys.
- **Coverage.** Recounted support of the source classes: yolo 7: 111 (G4), 10: 48 (G5 as DK 10),
  12: 65 (G5 as DK 12), 40: 15 (G4b), 19/20/41: 0. Targets: 7, 33, 42 (G4), 8 and 48 (G5 as DK 8,
  DK 46). Because F1 relabels only source → target, class-aware hits can change only for GT classes
  in sources ∪ targets, so the remaining critical classes in the JSON (DK 0, 2, 13; 13/13, 7/7,
  17/17; not sources or targets) cannot be affected. With G4b, every class F1 can touch that has
  validation support is guarded.
- "No loss" (≥ 14) is stricter than the QA's alternative (≤ 1 loss) and stricter than the D-05
  reference (≥ 11/15). It tightens, it does not loosen.

### A3 — C2 (precedence and totality)

- Enumeration over S0, L, G1, G2, G3, G4, G4b, G5, G6, G7 (2^10) × sign(Δ) (3) = 3,072
  combinations, 2,048 of them logically feasible (G1 ⇒ Δ > 0). For each, the addendum's first-match
  table yields exactly one outcome, and that outcome equals the highest-precedence member of the set
  of outcomes the contract's own predicates (extended with G4b and L) would assign, under
  `INVALID > NO_GO > NO_GO_UNCERTAIN > NO_GO_LATENCY > GO`. Gaps 0, disagreements 0.
  2,773 combinations had more than one candidate outcome and are resolved by precedence (the
  original contract alone had 617 overlapping combinations and no gaps).
- Distribution: `INVALID` 2,688, `NO_GO` 376, `NO_GO_UNCERTAIN` 6, `NO_GO_LATENCY` 1,
  `GO_CANDIDATE_FOR_CONFIRMATION` 1 (only all-true with Δ > 0).
- The QA's overlap case (Δ > 0, G1/G2 fails and G4/G5/G6 fails) maps to `NO_GO` by row 2. Row 3's
  note "Δ > 0 is guaranteed here by row 2" is correct.
- **G7 vs `INVALID`.** The latency arm always runs once Step 0 passes (execution order step 3), so G7
  is attempted in every case that reaches arm B. A Step 0 failure stops the run before arm B, as the
  contract already required, so no latency is measured then; that is the only case without a G7
  attempt and it is already `INVALID`. If measurement fails, L is false and row 1 gives `INVALID`,
  which is evaluated before row 4 reads G7. This is consistent, and it is the conservative choice:
  a run whose accuracy guards show `NO_GO` but whose latency arm failed is `INVALID`, not `NO_GO`, and
  under the authorization record it cannot be re-run without new Owner authorization. `failed_guards`
  still records every failing accuracy guard, so no information is lost. The new L condition is
  disclosed in §2 of the addendum; it tightens.
- **Q1 (recommended).** "300 valid measured samples" does not define *valid*. Bind it in step 3,
  e.g. "the timed call returned without exception and the duration is finite and > 0"; anything else
  makes L false.

### A4 — C3–C8

- **C3.** Iteration parity is indexed separately for warm-up (0–49) and measurement (0–299); even = AB,
  odd = BA; both arms use the same image; each arm's span includes its own read. This gives exactly
  150 AB and 150 BA measured iterations, so the page-cache advantage of the second position is shared
  equally by both arms; per-sample `order`/`position` are recorded and per-position p50/p95 are
  non-decision diagnostics. G7 = arm B p95 over all 300. Well-defined. §6.4 is retitled
  "Latency protocol (SAHI R1 §1.5 setup plus order control)", and the setup claims match
  `sahi_r1_validation_report.md` lines 68–71 (re-read: M1 Pro MPS, batch 1, warm-up 50, 300 measured,
  `torch.mps.synchronize()` each iteration, val-order cycling, `conf=0.20`, `iou=0.70`, `imgsz=1280`).
  Live latency-arm inference is tied to authorization §3.B, and the contract §1 ban stays on the
  accuracy arm. The "no source box → no classifier forward, still timed" reading note changes no rule.
  **Q2 (recommended):** state whether measured iteration 0 uses validation image 0 or continues the
  cycle after warm-up (image 50). Non-decision, but it should be fixed before the run.
- **C4.** Re-read `detector/colab/evaluate_cascade_b0_r1.py` (`8bedb4c1…`): 174–175 open and
  `convert("RGB")`; 192–193 clip x to `[0, W]`, y to `[0, H]`; 194 keep-mask
  `isfinite(boxes).all(1) & (x2 > x1) & (y2 > y1)`; 195 applies it; 49–52 `crop_bounds` raises
  `ValueError("invalid predicted box")` unless finite and `0 ≤ x1 < x2 ≤ W`, `0 ≤ y1 < y2 ≤ H`.
  `data.py` 21–23 is `/255`, then `(x − 0.5)/0.5`, equal to evaluator 164–168 and 200–203. The
  addendum's six-step predicate reproduces this exactly, including NumPy clip semantics, and keeps
  the original CSV box for scoring (contract §2). Recount: 0 of 798 source rows fail either the raw
  bounds test or the addendum's clip-then-filter predicate; 18 rows fail the raw bounds test overall,
  all `yolo_id` 47 (not a source). Expected `crop_invalid` = 0 is correct.
- **C5.** NumPy check: `float(np.float32(0.8))` = `0.800000011920928955078125` → `>= 0.80` True;
  `np.nextafter` below = `0.7999999523162841796875` → False. Both values in the addendum are exact.
  The argmax-implied argument holds (p[t] ≥ 0.8 leaves ≤ ~0.2 for all other classes). `repr(float(v))`
  of float32 values round-trips exactly, so a model-free recompute reproduces every decision.
- **C6.** `metrics.group_bootstrap` (lines 298–317): `names = sorted(groups)`,
  `rng = np.random.default_rng(seed)`, per round `rng.choice(names, size=len(names), replace=True)`,
  CIs by `np.percentile(·, 2.5/97.5)`, only for agnostic recall and FP/image. The addendum's draw
  sequence is identical; test (a) (exact float equality of arm-A agnostic-recall and FP/image CIs)
  verifies the draws, and test (b) (B ≡ A ⇒ Δ CI exactly `[0.0, 0.0]`) would fail for unpaired
  draws. Correct. **Q3 (recommended):** add one synthetic case in step-3 source QA where B differs
  from A by a known number of hits in one group, so the sign and pairing of Δ are tested
  beyond the degenerate zero case.
- **C7.** Re-verified: manifest and members (A1); bundle CSV equals run CSV; `diff`-equivalent label
  check (376 files, byte-identical, roster `dc72ebd9…8343` in the R3 `{name: sha256}` form); bundle
  `data/images/val` vs `data/processed/m1_yolo_wp38_r1_integration_r4/images/val` — same 376 names,
  376/376 byte-identical, both rosters `24e2a67d…118e` (computed as `val_reeval_r2.image_roster`:
  SHA-256 of `json.dumps({name: sha256}, sort_keys=True)`). The group map, which the addendum did not
  re-verify, was re-verified here: `val_groups.json` equals the `wp36_r1_split_frames.csv` group for
  all 376 stems (0 mismatches, 9 groups). Hazard confirmed: `data/processed/m1_yolo/images/val` has
  `1319.jpg`/`1320.jpg`; the bundle has `1319.png`/`1320.png`. The downgrade of U2 is justified,
  and Step 0 stays binding.
  **Q4 (recommended).** The R4-export images are **symlinks** into `data/raw/DATASET01/...` (bundle
  images are regular files). Contract §8 summarises the input guards as "no symlinks, regular files
  only", while `val_reeval_r2.image_files` actually allows links into two governed roots. If the
  executor chooses the "equivalently, the R3 export images" path, the source QA must confirm it uses
  the `val_reeval_r2` governed-link rule; otherwise use the bundle. Also, the addendum calls that
  directory "the R3 export"; it is the WP38-R1 integration R4 export directory used with the R3
  labels (`val_reeval_r2.py:69-70`). Naming only.
- **C8.** `cascade_classifier_improvement_r2_report.md` lines 90–92 read "**The combined candidate meets
  this validation gate**; group balance and jitter alone do not." The addendum's quote matches,
  apart from bold markup. The added §7 reuse item changes no rule.

### A5 — nothing else changed

Compared addendum §9 and every resolution against the contract text:

- Pairs P1–P6 and the no-chaining rule: unchanged. τ = 0.80 and the F1 rule: unchanged (C5 only fixes
  dtype and inclusivity, which the contract's `≥` already implied). Sensitivity grid and leave-one-out:
  still descriptive.
- Primary endpoint (correct-class recall at 0.20, reference 457/624): unchanged.
- G1 ≥ 467, G2 lower bound > 0 (1000 rounds, seed 20261018, 9 groups), G3 FP ≤ 150 and TP = 547,
  G4 ≥ 66/18/12, G5 (≤ 2 lost hits plus D-05 clause), G6 Δ mAP50 ≥ 0 and Δ mAP50-95 ≥ 0, G7 p95 ≤ 100 ms:
  all unchanged.
- Evaluation set (376 frames, roster `24e2a67d…`, labels `dc72ebd9…`, 624 GT, 9 groups, ignore regions
  unused, `test` refused): unchanged. Checkpoint `d1e69eef…`, CPU float32 verdict: unchanged.
- Flags: unchanged.
- Additions and tightenings only: G4b; Step 0 + 14; L → `INVALID`; latency counterbalancing;
  reporting fields `failed_guards`, `outcome_row`, `order`, `position`; manifest pins the addendum and
  the authorization record (still no QA record). C6 replaces an ill-defined test with a precise one.
  None of these loosens a gate.
- **Q6 (recommended, inherited from the contract).** The Step 0 sentence in addendum §7 lists
  "agnostic recall 0.876603, FP/image 0.398936 and common-path mAP50/50-95 … within 1e-9". The 1e-9
  tolerance belongs to the mAP pair, as in contract §6; read literally for the 6-dp recall and FP/image
  displays it would fail (0.8766025641 − 0.876603 ≈ 4.4e-7). Bind them in step 3 as the exact
  fractions 547/624 and 150/376 (which follow from TP/FP), not as rounded decimals.

### A6 — authorization record

- **Verbatim and caveat.** The coordinator's message and the Owner's reply "cho phép" are quoted; §2
  states the session did not see the chat and marks anything beyond the relay [U]. Note (Q5): §3
  "Interpretation told to the Owner" is also relayed content but is not itself labelled as relayed;
  the relayed coordinator message names only C1 and C2, while §3.A covers C1–C8. This is not
  over-reach (C3–C8 were QA-recommended document corrections, and the addendum is what the Owner
  authorized writing), but a future record should label §3 as relayed [U] for consistency.
- **Scope.** §3.A: the addendum now. §3.B: after an independent QA PASS of the addendum, contract §8
  steps 3–5 (as amended) exactly once, offline: CPU float32 classifier for the accuracy arm, MPS
  decision recompute, §6.4 latency arm with live YOLO11s-54 and classifier inference on local MPS;
  every arm on the R3 validation images only (roster `24e2a67d…`). This matches the brief exactly.
- **Exclusions.** §4 lists training/fine-tuning, app integration/enablement, D-05/conf 0.20/NMS/
  thresholds/threshold lock, sealed test (with the provenance-token caveat), upload, `git push` and
  unauthorized commits, and any re-run after results (including another τ, pairs, checkpoint or a
  fixed bug; `INVALID` needs new written authorization). All explicit.
- **Over-reach.** None. The added [P] reading rule (PASS giới hạn counts only without a required
  correction) is labelled as not told to the Owner and only narrows the authorization. Reading note:
  fixing the scorer after a step-3 source-QA finding on synthetic data is not a "re-run after
  results", because no real-run result exists at that point.

### A7 — gate

`uv run ruff check src tests` → `All checks passed!`, exit 0. `uv lock --check` → `Resolved 201
packages in 4ms`, exit 0. No source file was changed, so no Graft rebuild was needed.

## Recommended clarifications (proposals; none required before execution)

| ID | Severity | Proposal |
| --- | --- | --- |
| Q1 | Recommended, bind in step 3 | Define a "valid" latency sample (returned without exception, finite, > 0 ms). |
| Q2 | Recommended, bind in step 3 | State the image index of measured iteration 0 (restart at 0 or continue after warm-up). |
| Q3 | Recommended, step-3 source QA | Add a synthetic non-zero paired-Δ case to the C6 bootstrap test. |
| Q4 | Recommended, step-3 source QA | If the R4-export images are used, apply the `val_reeval_r2` governed-link rule; otherwise use the bundle (regular files). Read "R3 export" as the WP38-R1 integration R4 export directory. |
| Q5 | Minor, documentation | Label authorization §3 as relayed [U], like §2. |
| Q6 | Recommended, bind in step 3 | Step 0 recall and FP/image compared as exact fractions 547/624 and 150/376; the 1e-9 tolerance applies to the mAP pair only. |

## Commands run (read-only; no model loaded, no inference)

| Command | Result |
| --- | --- |
| `graft check .` | `graph check: OK — the wiring graph is in sync with the code` |
| `git status --short \| head -60`; `git log --oneline -3` | 12 ` M` Owner files plus `??`; HEAD `17db663` |
| `shasum -a 256` on the two reviewed files, contract, contract QA record | all four match the handoff values |
| `shasum -a 256 -c <42-line pin list>` | `42 OK` |
| `python3 -I` manifest verification (sizes + SHA-256 of all members) | `8579 ok 0 bad 0 missing`; no `test` member; CSV member `87884c53…`, 203,251 bytes |
| `python3 -I` image/label roster script | bundle vs R4-export images 376/376 identical; both rosters `24e2a67d…118e`; labels roster `dc72ebd9…8343`; bundle labels identical; `m1_yolo/images/val` has `1319.jpg`/`1320.jpg` vs bundle `.png` |
| `ls -l` on both image directories | R4-export images are symlinks into `data/raw/DATASET01/...`; bundle images are regular files |
| `uv run python -I` arm-A recount with `m1.metrics.operating_point` (pilot CSV + R3 labels, no model) | TP 547, FP 150, recall 0.876603, FP/image 0.398936, Σ hits 457 / 19 classes; yolo 40: 14/15; 7/33/42/48: 66/18/12/55; JSON `classes["39"]` 14/15 critical, not gated |
| `python3 -I` outcome enumeration (3,072 combinations) | 0 gaps, 0 disagreements with QA precedence; each combination one outcome |
| `uv run python -I` CSV predicate, float32 boundary, group-map script | 0/798 source rows invalid (18 invalid overall, all yolo 47); boundary values exact; `val_groups.json` = WP36 groups for 376/376 stems, 9 groups |
| `nl -ba` readback: evaluator 44–68, 158–210; `data.py` 12–28; `metrics.py` 1–120, 296–318; SAHI report 66–72; R2 report 86–94; `val_reeval_r2.py` 69–70, 152–154, 221–262 | as cited above |
| `uv run ruff check src tests` | `All checks passed!`, exit 0 |
| `uv lock --check` | `Resolved 201 packages in 4ms`, exit 0 |

Scratch scripts were kept outside the repository (session scratchpad) and wrote nothing into it.

## SHA-256 values

| File | SHA-256 |
| --- | --- |
| Reviewed: `docs/review/d1_yolo54_classifier_fusion_r1_addendum_1.md` | `fa2ea121623a0072256cd56e88ba1d1e60a90cd85a51f0869fa5d70623bdd6e9` |
| Reviewed: `docs/review/d1_yolo54_classifier_fusion_r1_owner_authorization_2026-11-05.md` | `9f8c5f20c4dab52258d64270d490fc720c941bc1478a22550a549560e3556fcd` |
| `docs/review/d1_yolo54_classifier_fusion_r1_contract.md` | `40cbe72ff095b8aea9d2253c02a52c013797b2148febc4bbbd647e68a77c700c` |
| `docs/review/d1_yolo54_classifier_fusion_r1_contract_independent_qa_record.md` | `aa3c4e384118a02fa28fb790d056951221334c7ecdefa410e02f381b83d5e902` |
| `detector/d1_cascade_classifier/data.py` | `e55fbaddea154131a0ef20f8d2653150b0f2c8eecdc8ff31dbcb16d6a463ed5d` |
| `tmp/yolo11n_n1_extract_r1/manifest.json` | `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da` |
| `tmp/yolo11n_n1_extract_r1/data/yolo54_predictions_val.csv` | `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893` |
| Pilot `d1_vre_r2/predictions_conf0001.csv` | `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893` |
| Pilot `d1_vre_r2/eval_val_vrl_r3_vre_r2.json` | `559c6c6a78a0d653da09a43bf6dc0663a2dbcb07f6aef4748cade369ef857c87` |
| `tmp/yolo11n_n1_extract_r1/data/val_groups.json` | `fdb2ef8ff2cc684970b6330747d7746ccfe6dfd77d60903d10233de66697d682` |
| `results/experiments/yolo11n_n1_seed_20261018_r1_r1/evaluation_r1/comparison_n1_r1.json` | `0447a1bdc2aec56980b63f3fea5340be9a1d455ed9b7872ac503c4d65779a0db` |
| `detector/colab/evaluate_cascade_b0_r1.py` | `8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42` |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` |
| `detector/m1/val_reeval_r2.py` | `2a0823faa15f7cb9cecb64a1f21e48e8b5b84f7e7f949683683a6992ee13ccc9` |
| Classifier `compact_combined_local_r2/best.pt` (hash only, not loaded) | `d1e69eefce644cdce044017aeb265e2179cbb94eb07a8ecdb114de16930350cc` |
| `docs/review/sahi_r1_validation_report.md` | `38adbfaf1df8744ccac97da72667ca6ae8be71224268c16b53216cda72258cab` |
| `docs/review/cascade_classifier_improvement_r2_report.md` | `4affca752041ac8cadd45274f2a940b7795816940eed95807fbe94f048066593` |
| `docs/review/generated/wp36_r1_split_frames.csv` | `8e197d9c7103ac5dc6b7ffc8a3d1aeb30bb6034048d470e4887dd868df95823a` |
| Image roster (bundle and R4 export, `{name: sha256}`) | `24e2a67d1e176a7e09caf4b1f6daa2bf5240981d00c8e1a535640e6b8066118e` |
| R3 label roster (`{name: sha256}`) | `dc72ebd944a38535d4f766ba4f8babc60cb6732dfcd253ed0e8d79dc86eb8343` |

All other contract §10 pins also returned `OK` (A1).

## Flags

`sealed_test_accessed=false`, `training_authorized=false`, `inference_run=false`,
`fusion_metric_computed=false`, `app_enable_authorized=false`, `threshold_lock_written=false`,
`d05_changed=false`, `reviewed_files_edited=false`, `existing_files_edited=false`,
`commit_or_push=false`.
