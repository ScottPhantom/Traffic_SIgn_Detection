# D1 YOLO54 + CompactCNN classifier fusion R1 — scorer independent source QA record (contract §8 step 3)

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Reviewer: Claude Code (Opus 5.5), independent side session. I did not write the scorer, its tests,
its implementation record, the contract, Addendum 1, either earlier QA record or the
authorization record.
Scope: **source review only**. I did not invoke `run` or `latency`, and I ran no latency
measurement. I did not run the classifier on any crop, real or synthetic. I computed no arm-B or
fusion metric on real data. The only real-data computations were arm A (pilot CSV against the R3
labels, Step 0) and bootstrap checks on arm A against itself. Both are allowed by the brief.
Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, branch `yolo11n-dual-track-r1`,
HEAD `17db663`.

Verdict: PARTIAL — the scoring rules, Step 0, F1, crop, metrics, guards, outcome table, bootstrap and latency protocol match the binding spec, but `run` cannot complete. `manifest()` refuses its own test-file path, so `run` raises after every fusion metric and the latency arm have been computed and before anything is written. Pins are also not re-verified before the write. Two corrections are required before execution (R1, R2), followed by a delta source QA.

**May the single real `run` proceed? No.** As written, `run` would crash at
`detector/m1/classifier_fusion_r1.py:1778` (`manifest` → `regular_file(…, TESTS)` →
`val_reeval_r2.guard_path` refuses every path component that contains `test`). The failure
would come after Step 0, the CPU accuracy arm, the MPS recompute, the latency arm and the full
`build_eval`, and before publication. The process would exit with a traceback and no output
directory. Under authorization §4, an execution that cannot complete needs a new written Owner
authorization. The defect would therefore consume the single run. The run gate also refuses this
record, because its verdict is not PASS. After R1 and R2 are fixed, the module's SHA-256 changes,
and a new source-QA record must quote the new hash.

`sealed_test_accessed=false`

## Under review (rehashed at start and at end; unchanged)

| File | SHA-256 |
| --- | --- |
| `detector/m1/classifier_fusion_r1.py` | `90359373a38752d09c2bc7a8206c53f66c726d99b18cf2d7e6da5fe45b9eaf24` |
| `detector/tests/test_classifier_fusion_r1.py` | `de949559a69ad404ee7833e3ded20646dc508daf1014d90559a83cc53bc893af` |
| `docs/review/d1_yolo54_classifier_fusion_r1_implementation_record.md` | `51e69893fec4733dbe1cd336f600ecc6538d0843835ed42db93d7ef22f924e54` |

## Binding spec (rehashed; all match the brief)

| Document | SHA-256 |
| --- | --- |
| Contract `docs/review/d1_yolo54_classifier_fusion_r1_contract.md` | `40cbe72ff095b8aea9d2253c02a52c013797b2148febc4bbbd647e68a77c700c` |
| Addendum 1 `docs/review/d1_yolo54_classifier_fusion_r1_addendum_1.md` | `fa2ea121623a0072256cd56e88ba1d1e60a90cd85a51f0869fa5d70623bdd6e9` |
| Addendum 1 QA record (Q1–Q6) | `b483788d4056722ccb2a6e6192afced592cc887afbcc844e3527a956874e632c` |
| Contract QA record | `aa3c4e384118a02fa28fb790d056951221334c7ecdefa410e02f381b83d5e902` |
| Owner authorization | `9f8c5f20c4dab52258d64270d490fc720c941bc1478a22550a549560e3556fcd` |

All five were read in full. The sibling note `fusion_r1_scorer_notes.md` in the shared notes
folder was read as data.

## Start-of-task state

- `AGENTS.md` and the head of `PROJECT_MEMORY.md` were read.
- `graft check .` returned `graph check: OK — the wiring graph is in sync with the code`; the deep
  layer is not built.
- `git log --oneline -3` returned `17db663 docs(review): pre-registered YOLO54+CompactCNN fusion R1 contract, QA PASS giới hạn`,
  `399bf70 feat(d1): paired A3−pilot validation CIs with independent QA PASS` and
  `5e3fa2a docs(review): R3 addendum — A3 executed via D1-A3-R2, criteria not met`.
- `git status --short | head -60` showed 13 ` M` Owner files:
  - `PROJECT_MEMORY.md`, `docs/product_roadmap.md`,
    `docs/review/cam_hanh_trinh_display_rename_r1_2026-11-04.md`, `docs/review_index.md`;
  - `scripts/run_parallel_checks.py`;
  - `src/cpv301_autodrive/app_pages/07_demo.py`, `dataset01_view.py`, `dataset01_view_r1.py`,
    `presentation.py`, `views.py`;
  - `tests/test_e0_compute_readiness.py`, `tests/test_web_app.py`,
    `tests/test_wp35_rare_class_enrichment.py`.

  It also showed `??` entries under `detector/colab/`, `detector/m1/` (including
  `classifier_fusion_r1.py`) and `detector/tests/`. The same 13 ` M` files remained at the end.
- No `classifier_fusion_r1/` output directory exists under the pilot run directory, either before or
  after this review.

## S1–S8 summary

| # | Check | Result | Key evidence |
| --- | --- | --- | --- |
| S1 | Step 0 | **PASS** | The module's `step0` (exit 0) and my own independent rebuild agree: TP 547, FP 150, 457 hits, recall `== 547/624` and FP/image `== 150/376` (exact), hits 66/18/12/55 and 14, mAP50 `0.8520835680058519`, mAP50-95 `0.6088678434901063`. The check fails closed on a class mutation, a score mutation or a +2e-9 shift of the reference mAP. Inside `run`, a failure returns `INVALID` with no write. |
| S2 | Rule F1 | **PASS** | P1–P6 are in yolo_id space with the right direction. The C5 compare is exact and inclusive at the float32 boundary values. Argmax uses the first index. There is no chaining (keyed on the original class), and the P2/P4 overlap is correct. F1 only relabels; NMS is not re-run; the overlap diagnostic is present. |
| S3 | Crop and normalisation | **PASS** | The scorer calls the pinned `crop_prediction`/`crop_bounds` (evaluator `8bedb4c1…`) on a PIL `convert("RGB")` image. The tensor ops equal evaluator lines 199–203 and `data.py:21-23`. The `crop_invalid` predicate is exactly C4 steps 1–6. |
| S4 | Metrics and decision | **PASS** | The G3 FP invariant leads to `INVALID`. G1–G7 and G4b use the exact thresholds. My own truth table agrees on all 2,048 flag combinations (0 disagreements). The bootstrap draws are identical to `group_bootstrap`, verified on real arm A: CIs equal, B ≡ A gives `[0.0, 0.0]`, and the Q3 non-zero test exists. The DK/yolo translation is correct. Sensitivity results are labelled and never read by `guards`. |
| S5 | Latency | **PASS** | AB/BA alternate by parity: 150/150. 50 warm-up and 300 measured iterations. Q1 validity and Q2 index `(50 + j) % 376` are bound. `torch.mps.synchronize` runs per arm. Raw samples, roster SHA, schedule SHA and environment versions are stored. A failure makes L false, which gives `INVALID`. |
| S6 | Guards and write path | **FAIL** (R1, R2) | Path, test and symlink guards are correct, and the Q4 bundle-only policy is safe and justified. The O_EXCL/O_NOFOLLOW publish, source-QA gate, `weights_only=True` with SHA before and after, CPU deterministic verdict and fixed flags are correct. **R1:** `manifest()` raises on the real checkout, so `run` cannot complete. **R2:** pins are not re-verified before the write (contract §8; SAHI R1 does this at `sahi_eval_r1.py:651`). |
| S7 | Tests and gates | **PASS giới hạn** (gap G-a) | 42 passed, and ruff, both `uv lock --check` runs and `graft check` are green. **Gap:** no test exercises `run` past its refusal gates, nor `manifest()`, nor `verify()` end to end. That is why R1 was not caught. |
| S8 | Implementation record | **PASS giới hạn** | It honestly states that `run`, latency, `load_classifier`, MPS and `verify` were not executed. Its Q1–Q6 bindings are accurate. Its §8 lists the checkpoint layout and `bind_run_weights` as [U]; both are now resolved by this QA (S6). It does not mention the manifest path conflict. |

## Detailed findings

### S1 — Step 0

- I ran `(cd detector && uv run python -m m1.classifier_fusion_r1 step0)`. Exit code 0.
  - 22 pins verified; bundle 8,579/8,579 members verified (full).
  - Image roster `24e2a67d…118e`, label roster `dc72ebd9…8343`, CSV `87884c53…c893`.
  - Image source `tmp/yolo11n_n1_extract_r1/data/images/val`.
  - All ten checks `true`. Observed values are those listed in the S1 row of the summary table.
  - No file was written.
- **Independent rebuild** (scratch script, not the module's frame builder). I built `Frame`s
  directly from the bundle label files, PIL image sizes, `val_groups.json` and the run-directory
  CSV, then scored them with `m1.metrics.operating_point` and the pinned evaluator's
  `average_precision`. Results:
  - 376 images, 624 GT, TP 547, FP 150, Σ hits 457;
  - `agnostic_recall == 547/624` True and `fp_per_image == 150/376` True;
  - hits yolo 7/33/42/48/40 = 66/18/12/55/14;
  - mAP50 0.8520835680058519 and mAP50-95 0.6088678434901063, bit-identical to the module.
- **Fail-closed.** `step0_check` returned `passed=false` in each of three cases:
  - one class-48 row with conf ≥ 0.5 relabelled to 10;
  - one row's score lowered from ≥ 0.5 to 0.1;
  - the reference mAP50 shifted by 2e-9.

  After the reference was restored it returned `true`. In `run` (lines 1734–1743), a failed Step 0
  returns `INVALID` with `outcome_row 1`, `written: []`, no output directory and exit code 2, and
  that happens before the classifier is loaded. Q6 is bound: recall and FP/image are compared as
  exact fractions, and the 1e-9 tolerance applies to the mAP pair only (lines 950–954).

### S2 — Rule F1

- **Pairs.** `PAIRS` (lines 172–179) is `(P1, 10→48)`, `(P2, 19→7)`, `(P3, 40→42)`, `(P4, 7→33)`,
  `(P5, 41→42)` and `(P6, 12→8)`, in yolo_id space. In derived keys these are 10→46, 17→7,
  39→41, 7→32, 40→41 and 12→8, matching contract §4.1 and Addendum §9. The source is the
  predicted class and the target is the GT class.
- **τ (C5).** `relabel` (lines 597–604) requires a float32 54-vector. It refuses float64 input,
  uses `top1 = int(np.argmax(p))` and relabels iff `top1 == t and float(p[t]) >= 0.80`. My checks:
  - float32(0.8) = 0.800000011920928955078125 relabels;
  - `nextafter` below it does not;
  - an exact 0.5/0.5 tie at τ = 0.50 with source index 10 < target 48 does not relabel (first-index argmax);
  - a float64 vector is refused.
- **Decisions are taken from the written text** (C5 item 7). `run` re-parses
  `fusion_r1_crop_probs.csv` (`repr(float(v))`). It decides from those values, and
  `parse_probs_csv` requires every value to round-trip exactly to float32.
- **No chaining.** `decide` (lines 632–655) keys only on `row.yolo_id`, the original class, and
  applies at most one relabel. My cases:
  - P2 then P4 gave `[19→7, 7→33, 47 kept]`;
  - a class-19 row whose probabilities favour 33 stays 19;
  - an invalid crop keeps its class;
  - a cropped non-source row is refused.
- **Relabel only.** `arm_frames` replaces only `pred_classes`. Boxes, scores and CSV order are
  unchanged. NMS is never called. G3 checks TP_B = TP_A = 547 and FP_B = FP_A ≤ 150.
- **Overlap diagnostic.** `same_class_overlaps` counts same-class pairs at IoU ≥ 0.70 that involve
  a relabelled box, at all scores and at conf ≥ 0.20. It is reported, not decisive.

### S3 — Crop and normalisation

- `crop_input` (lines 607–617) follows C4:
  1. it copies the box as float64;
  2. it `np.clip`s x to `[0, W]` and y to `[0, H]`;
  3. it returns `None` (= `crop_invalid`) if the box is non-finite or has non-positive extent;
  4. otherwise it calls the pinned `crop_prediction`, and treats a `ValueError` as `crop_invalid`.

  The clipped copy is used only as the crop input. The scored box stays the raw CSV box. My cases:
  - NaN, zero width and negative extent → invalid;
  - a box wholly to the right of the image clips to zero width → invalid;
  - −inf clipped to 0 → valid;
  - a box partly outside the image → valid, clipped to `[0, 0, 10, 10]`;
  - a raising `crop_fn` → invalid.
- **Image.** `_read_rgb` opens the image with PIL and calls `convert("RGB")`, as at evaluator lines
  174–175. Crops on a dummy 960×540 image are `(32, 32, 3)` uint8.
- **Tensor ops.** `classify` (lines 620–629) is
  `from_numpy(crops.transpose(0,3,1,2).copy()).float().to(device)/255`, then `softmax(model((x−0.5)/0.5), 1)`.
  This is token for token evaluator lines 199–203, and equivalent to `data.py:21-23`
  (`/255`, `−0.5`, `/0.5`). The output is asserted to be float32 `(n, 54)`.
- The only input difference from the evaluator is that the CSV boxes are parsed as float64, while
  the evaluator's live boxes were float32. Addendum C4 step 2 mandates float64, so this is not a
  defect.

### S4 — Metrics and decision

- **G3 / FP invariant.** `metrics.match` with `class_aware=False` ignores classes. TP and FP come
  only from the agnostic call, so relabel-only cannot move them. The repository test
  `test_a_moved_box_breaks_g3_and_is_invalid` shows that a moved box breaks G3 and gives `INVALID`.
- **Thresholds** (lines 215–220, 1104–1120):
  - G1: hits ≥ 467;
  - G2: paired CI lower bound > 0;
  - G3: as above;
  - G4: yolo 7/33/42 ≥ 66/18/12;
  - G4b: yolo 40 ≥ 14;
  - G5: DK 6, 8, 10, 12, 23, 34, 46 (yolo 6, 8, 10, 12, 25, 35, 48) each lose ≤ 2 hits, and none
    may fall below the D-05 reference (0.50; none of them is in `contract.CRITICAL_KEYS`) if it met
    it under A. Arm-A supports are 22/51/48/65/28/37/104, all ≥ 20, so the zero-support raise
    cannot fire;
  - G6: Δ mAP50 ≥ 0 and Δ mAP50-95 ≥ 0, using the pinned evaluator;
  - G7: L and arm-B p95 ≤ 100 ms.

  `delta_positive` is `delta_hits > 0`, which is equivalent to Δ recall > 0 because the
  denominator 624 is fixed. All of these match the contract and Addendum 1.
- **Outcome table.** My own `mine()` encodes the C2 table independently. Over all 2^11 = 2,048
  combinations of S0, L, delta_positive, G1–G7 and G4b:
  - it agrees with `assign_outcome` on outcome and row every time (0 disagreements);
  - the distribution is INVALID 1,792, NO_GO 248, NO_GO_UNCERTAIN 6, NO_GO_LATENCY 1 and GO 1;
  - `failed_guards` equals the list of all false flags in `GUARD_ORDER` every time;
  - numpy `bool_` flags are refused.

  The addendum QA's 3,072 combinations used a three-valued Δ. Here Δ is the binary
  `delta_positive`, so 2,048 is the full space.
- **Paired bootstrap (C6).** `resample_indices` uses `default_rng(20261018)`, 1,000 rounds and
  `rng.choice(sorted(groups), size=9, replace=True)`. Each draw is applied to both arms. On real
  arm A against itself:
  - the arm-A agnostic-recall and FP/image CIs equal `metrics.group_bootstrap(frames_A, 0.20)` exactly;
  - the Δ correct-class-recall CI is `[0.0, 0.0]`;
  - 9 groups and 1,000 rounds are used;
  - my own regeneration of the 1,000 draws is index-identical to the module's.

  **Q3.** `test_paired_bootstrap_nonzero_delta_has_known_sign_and_pairing` adds 2 hits inside one
  group, checks every round's Δ against a hand formula, checks the zero-Δ rounds, and checks that
  swapping the arms flips the sign. This is a real non-degenerate test.
- **Translation.** `class_names` checks that `m1_yolo_classes.csv` equals `signnames.csv` row by
  row. `EXPECTED_DERIVED_KEYS` matches the live map, e.g. 19→17, 20→18, 25→23, 33→32, 35→34,
  40→39, 41→40, 42→41 and 48→46. Every output row and per-class entry carries both keys.
- **Sensitivity.** The τ ∈ {0.50, 0.95} grid and the leave-one-out variants are built in
  `build_eval` (lines 1493–1521). Each entry is labelled `SENSITIVITY_NOT_DECISION`. Their values
  never reach `guards()`, whose inputs are `arm_a`, `arm_b`, `boot`, `ap_a`, `ap_b`, `latency`,
  `names` and Step 0 only. The paired mAP CIs are labelled `REPORTED_NOT_DECISIVE`.
- **Implementer-chosen definitions.** Help and harm are counted per GT at conf 0.20. Per-pair
  help/harm is an isolated single-pair counterfactual. Relabels are binned by the predicted box's
  √(w·h). All three affect reported values only, not the verdict, and I find them reasonable.

### S5 — Latency

- **Schedule.** `latency_schedule` and `latency_protocol` (lines 1155–1206) run warm-up iterations
  0–49 on images 0–49, then measured iteration `j` on image `(50 + j) % 376` (**Q2**). Even
  iterations run AB and odd iterations run BA, and both arms use the same image. Each arm's span
  is `clock → arm(path) → sync() → clock`, and the arm reads its own image.
  - With synthetic arms: 700 calls, 600 measured samples.
  - The first samples are `(0, 50, AB, first, A)`, `(0, 50, AB, second, B)`,
    `(1, 51, BA, first, B)` and `(1, 51, BA, second, A)`.
  - L is true and the split is 150/150.
- **Q1.** A sample is valid iff it raised no exception, and its duration is finite and > 0 ms.
  A raising arm yields invalid samples, so L is false. If setup fails, `completed=False` and L is
  false. Row 1 then gives `INVALID` (lines 1325–1329, 1229). G7 uses arm-B p95 over all 300 valid
  samples. Per-position statistics are diagnostics only.
- **Recorded.** Each raw sample stores iteration, image index, name, order, position, arm, ms,
  valid and error. The run-level record stores the image roster SHA, the SHA of the full timed
  sequence and `contract.environment()` (torch and ultralytics versions), with
  `versions_match_sahi_r1`. The sync function is `torch.mps.synchronize`.
- **Disclosed difference, acceptable.** Arm A reads the image with PIL plus BGR conversion,
  instead of SAHI's `imread`, so that both arms share the same read.
- **Latency preflight** (lines 1406–1422). It runs before Step 0, refuses rather than consumes the
  run, and computes no metric. I executed it as a function. It is model-free and inference-free:
  MPS available; `bind_run_weights` OK (run registry `ba5ab04f…b0c9`, git-tracked and clean);
  torch 2.14.1 and ultralytics 8.4.172, `versions_match_sahi_r1 = true`.

### S6 — Guards and write path

- **Path guards.** Every input goes through `val_reeval_r2.guard_path`. It refuses absolute paths,
  `..`, any component containing `test` (case-insensitive substring) and any symlink component.
  `regular_file` also requires `S_ISREG` under `lstat`. I confirmed that it refuses
  `detector/tests/…`, `data/raw/x/latest.png`, `/etc/passwd` and `../x`. `verify_bundle` also
  refuses a manifest with a test member or a bundle test directory.
- **Q4 symlink policy: safe and justified.** The module reads images, labels and the group map only
  from `tmp/yolo11n_n1_extract_r1/data`. All of these are regular files and every one is hashed
  against the 8,579-member manifest. At load, the image roster must equal `24e2a67d…118e`. That is
  the same roster as the R4-export images, which are symlinks into `data/raw/DATASET01`, and the
  addendum QA showed the two sets are byte-identical 376/376. Refusing the symlinked directory
  therefore loses nothing, avoids the governed-link exception, and never touches
  `data/processed/m1_yolo/images/val`, the directory with the `.jpg`/`.png` hazard.
- **Write-once.** `publish` stages each file with `O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW`
  (`vre.write_exclusive`: fsync, then read-back), then calls `renamex_np(RENAME_EXCL)`. It removes
  the staging directory on failure. `refuse_existing_outputs` runs before any input is read and
  again before publication, and it also catches dangling symlinks.
- **Source-QA gate.** `check_source_qa` runs first. It requires:
  - both arguments, and a 64-character lowercase hex hash;
  - a repo-relative, guarded, regular record whose bytes hash to the given value;
  - exactly one `Verdict:` line after NFC normalisation, of the form PASS or PASS giới hạn;
  - quotes of the current module, contract and addendum SHAs.

  This record contains all three SHAs, but its verdict is PARTIAL, so the gate correctly refuses it
  (checked; see Commands). The gate cannot tell whether a PASS giới hạn lists a required
  correction. That remains the coordinator's duty under the authorization reading rule.
- **Classifier.** `load_classifier` re-verifies `d1e69eef…` before and after
  `torch.load(weights_only=True)`. It checks `epoch == 18` and `config ==` the pinned
  `contract.json`, then calls `load_state_dict(strict=True)`. The implementation record left the
  payload layout as [U]. I resolved it by loading the payload only: no model forward and no crop.
  - Keys are `best, config, epoch, history, model, optimizer`.
  - `epoch` = 18, and `config` equals `contract.json`.
  - A strict load into `CompactCNN` gives "All keys matched successfully".
  - The SHA is unchanged before and after.
- **Deterministic CPU verdict.** `deterministic_cpu()` sets one thread and
  `use_deterministic_algorithms(True)` around the CPU pass only, then restores both settings. The
  MPS decisions are stored as `cpu_mps.mps_relabel_rows`, and the differences are recomputed. The
  verdict never reads them.
- **Flags.** `FLAGS` holds the five contract flags plus the authorization's `push_authorized` and
  `rerun_after_results_authorized`, all false. They are carried into the eval JSON, the latency
  JSON and the manifest.
- **`verify`.** It is model-free. It rebuilds the predictions CSV and the eval JSON from the two
  CSVs, the latency JSON (whose statistics, L and G7 are recomputed from the raw samples) and the
  stored MPS rows, then compares bytes and the manifest output hashes. This is consistent with the
  contract, since latency cannot be rebuilt without a model. It is tested synthetically, including
  tamper detection. It cannot be run on real outputs yet.
- **R1 (required, blocking).** `manifest()` (lines 1684–1701) calls
  `regular_file(repo_root, TESTS)` with `TESTS = detector/tests/test_classifier_fusion_r1.py`.
  `guard_path` refuses it: `RuntimeError: refused sealed-test path: detector/tests/test_classifier_fusion_r1.py`,
  reproduced by calling `manifest(REPO_ROOT, {})` directly. `run` calls `manifest` at line 1778,
  after all computation and before `publish`, so `run` can never write its outputs. No test calls
  `manifest()`.
- **R2 (required).** Contract §8 requires that pins be "re-verified before the write". `run`
  verifies `PINS` and the bundle only in `load_state`, at the start. Before `publish` it re-checks
  only that no output exists. `manifest()` records the `PINS` constants, not fresh hashes. The SAHI
  R1 precedent re-runs `vre.verify_pins` before its write (`sahi_eval_r1.py:651`).

### S7 — Tests and gates

The gate results are listed under Commands run. Assessment of the 42 tests against the spec:

- **Covered well.**
  - Pair, τ and translation values; the τ float32 boundary; argmax ties.
  - No chaining and the P2/P4 overlap; the C4 predicate and backstop.
  - One forward per image, float32 output; G3 invariant and break.
  - Every outcome row, plus totality and precedence.
  - Bootstrap equivalence and the Q3 non-zero case; bit-exact probability round trip.
  - Latency counterbalancing and Q1 invalid samples; byte-identical model-free rebuild and tamper detection.
  - Overlap and help/harm; publish write-once and symlink refusal.
  - The source-QA gate's refusal forms; test-path and symlink refusal; bundle-manifest refusal.
  - CSV out-of-scope rows; the `latency` CLI measures nothing.
- **Gap G-a, which caused R1.** No test drives `run` beyond its refusal gates on a synthetic root
  with a fake classifier, fake latency and fake evaluator. Nothing calls `manifest()` or `verify()`
  end to end, so the integration from `build_eval` through `manifest` and `publish` to `verify` is
  unexercised.
- **Gap G-b.** `load_classifier`, `measure_latency`, `latency_preflight` and `deterministic_cpu`
  have no unit test. The first three need real artifacts or MPS. This QA closed the classifier
  layout and preflight by direct inspection.
- **Gap G-c.** No test pins the R2 behaviour, i.e. that a pin changed mid-run blocks publication.

### S8 — Implementation record

The record states honestly what ran and what did not:

- ran: `step0` (exit 0) and the 42 tests;
- not run: `run`, latency, `load_classifier`, MPS and `verify` on real outputs;
- `inference_run=false` and `fusion_metric_computed=false`.

Its §4 binds Q1–Q6, and the bindings match the code:

- Q1 is `summarize_latency`;
- Q2 is `(50 + j) % 376`;
- Q3 is the test reviewed above;
- Q4 is bundle-only with every symlink refused;
- Q5 is documentation-only and needs no code;
- Q6 is the exact fractions.

Its Step 0 table matches my independent rebuild. Its open points are:

- [U] checkpoint layout — now resolved, OK;
- [U] `bind_run_weights` — now resolved, OK;
- [P] definitions — accepted above.

It does not disclose the R1 path conflict, because the conflict was not detected.

## Required corrections (proposals; the module, tests and every existing file were left unedited)

| ID | Severity | Proposal |
| --- | --- | --- |
| R1 | **Required before execution (blocking)** | Make `manifest()` hash `TESTS` without the `test`-substring refusal. Keep the symlink and regular-file checks, e.g. a `_source_file(repo_root, relative)` helper allow-listed to exactly `TESTS`, that walks the components with `is_symlink()` and requires `S_ISREG`. Do not relax `guard_path` for data inputs. Better still, compute the `sources` hashes (module and tests) at the **start** of `run`, next to `check_source_qa`, and fail there, so a path error can never surface after metrics exist. Add a test that calls `manifest(REPO_ROOT, {})` on the real checkout, and one with a synthetic root containing `detector/tests/…`. |
| R2 | **Required before execution** | Immediately before `refuse_existing_outputs` and `publish` in `run`, re-run `verify_pins(repo_root)`, re-check the module and test SHAs against the values captured at the start (the module SHA is the one the source-QA record quotes), and re-check the classifier SHA. Abort without writing on any mismatch. Prefer `verify_bundle(full=False)` over the used members as well. |
| R3 | Recommended | Add an end-to-end `run` test on a synthetic root, with injected fake classifier, latency and evaluator, that reaches `publish` and then `verify()` with no errors. This closes gap G-a. |
| R4 | Recommended | Three `raise`s can fire after Step 0 and before publication, and each would consume the run with no record. They are the CPU/MPS crop-set mismatch at line 1753, the G5 zero-support raise and the `parse_probs_csv` sum tolerance. All are unreachable on these inputs: crop sets do not depend on the device, G5 supports are ≥ 22 and float32 softmax sums lie well within 1e-5. Either pre-check them before the classifier runs, or record them as `INVALID` with a written stop report. |
| R5 | Minor | After R1 and R2, the implementation record needs an append-only addendum that gives the new module and test SHAs and discloses R1. A **delta source QA** of the diff must then quote the new module hash before `run`. |

None of these touches a rule, a threshold, D-05, the pairs, τ or the outcome table.

## Commands run

| Command | Result |
| --- | --- |
| `graft check .` (start and end) | `graph check: OK — the wiring graph is in sync with the code` |
| `git status --short \| head -60`; `git log --oneline -3` | 13 ` M` Owner files plus `??`; HEAD `17db663` |
| `shasum -a 256` on the 3 reviewed files and 5 spec documents (start and end) | all match the brief; unchanged at end |
| `(cd detector && uv run python -m m1.classifier_fusion_r1 step0)` | exit 0; `step0.passed = true`; values in S1 |
| Scratch `qa_checks.py`, run with `PYTHONPATH=detector uv run python`. It does an independent arm-A rebuild, Step 0 fail-closed mutations, F1/crop/decide unit cases, a 2,048-row truth table, the bootstrap on real arm A versus `group_bootstrap`, the translation, synthetic latency, guards and `manifest(REPO_ROOT, {})`. No classifier forward and no arm-B data | exit 0; results in S1–S6; `manifest` raises (R1) |
| `latency_preflight(REPO_ROOT)` called as a function (no inference) | MPS available, registry `ba5ab04f…`, torch 2.14.1 / ultralytics 8.4.172, `versions_match_sahi_r1 = true` |
| `torch.load(best.pt, weights_only=True)` plus a strict `load_state_dict`, with no forward pass | keys `best, config, epoch, history, model, optimizer`; epoch 18; config equals `contract.json`; all keys matched; SHA unchanged |
| `(cd detector && uv run pytest -q tests/test_classifier_fusion_r1.py)` | `42 passed in 2.46s`, exit 0 |
| `(cd detector && uv run ruff check m1 tests)` | `All checks passed!`, exit 0 |
| `uv run ruff check src tests` | `All checks passed!`, exit 0 |
| `uv lock --check` (root) | `Resolved 201 packages`, exit 0 |
| `(cd detector && uv lock --check)` | `Resolved 66 packages`, exit 0 |
| `check_source_qa(REPO_ROOT, <this record>, <its SHA>)` called as a function | refuses: `the source-QA record needs one PASS / PASS giới hạn verdict` (exactly one `Verdict:` line, PARTIAL) |
| `ls <pilot run>/classifier_fusion_r1` | no such directory (before and after) |

Scratch scripts and their outputs are in the session scratchpad, outside the repository. No source
file was changed, so no Graft rebuild was needed.

## Other SHA-256 values used

| File | SHA-256 |
| --- | --- |
| `detector/m1/val_reeval_r2.py` | `2a0823faa15f7cb9cecb64a1f21e48e8b5b84f7e7f949683683a6992ee13ccc9` |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` |
| `detector/colab/evaluate_cascade_b0_r1.py` | `8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42` |
| `detector/d1_cascade_classifier/data.py` (module pin) | `e55fbaddea154131a0ef20f8d2653150b0f2c8eecdc8ff31dbcb16d6a463ed5d` |
| Classifier `compact_combined_local_r2/best.pt` (loaded for layout only) | `d1e69eefce644cdce044017aeb265e2179cbb94eb07a8ecdb114de16930350cc` |
| Pilot `d1_vre_r2/predictions_conf0001.csv` | `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893` |
| `tmp/yolo11n_n1_extract_r1/manifest.json` | `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da` |
| `docs/review/generated/d1_run_registry.json` (via preflight) | `ba5ab04fd6e28e849a6b1aaf345bb5e284eb2a7aa1ee9c7cee0714209ed2b0c9` |
| Image roster / R3 label roster | `24e2a67d1e176a7e09caf4b1f6daa2bf5240981d00c8e1a535640e6b8066118e` / `dc72ebd944a38535d4f766ba4f8babc60cb6732dfcd253ed0e8d79dc86eb8343` |

The 22 module `PINS` were all verified by `step0` (`pins_verified: 22`).

## Flags

`sealed_test_accessed=false`, `training_authorized=false`, `run_invoked=false`,
`latency_measured=false`, `classifier_forward_run=false`, `fusion_metric_computed=false`,
`app_enable_authorized=false`, `threshold_lock_written=false`, `d05_changed=false`,
`reviewed_files_edited=false`, `existing_files_edited=false`, `commit_or_push=false`.
