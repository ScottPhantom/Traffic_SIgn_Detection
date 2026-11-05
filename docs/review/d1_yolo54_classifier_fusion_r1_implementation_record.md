# D1 YOLO54 + CompactCNN classifier fusion R1 — scorer implementation record (contract §8 step 3)

Status: `AWAITING_INDEPENDENT_SOURCE_QA`
Boundary: `IMPLEMENTATION_ONLY_NO_RUN_NO_LATENCY_NO_CLASSIFIER_ON_REAL_CROPS_NO_FUSION_METRIC`
Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Author: Claude Code (Opus 5.5), side session started from the coordinating session. Not the author
of the contract, Addendum 1, either QA record or the authorization record.
Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, branch `yolo11n-dual-track-r1`,
HEAD `17db663`. Many uncommitted Owner changes exist; this step edited none of them.

This record is append-only. It describes a scorer that **has not been executed on real data**
beyond the pilot-only Step 0 that the task brief allowed. The classifier was not loaded, no crop of
a real image was classified, `run` and the latency arm were not executed, and no arm-B or fusion
metric exists. The next step is independent source QA (contract §8 step 3), then exactly one `run`.

Claim labels: **[VB]** verified current behaviour (code ran in this checkout today); **[VA]**
verified artifact (rehashed or re-read today); **[P]** proposal or binding rule for a later step;
**[U]** unknown.

## 1. Created files

| File | SHA-256 | Lines |
| --- | --- | ---: |
| `detector/m1/classifier_fusion_r1.py` | `90359373a38752d09c2bc7a8206c53f66c726d99b18cf2d7e6da5fe45b9eaf24` | 1876 |
| `detector/tests/test_classifier_fusion_r1.py` | `de949559a69ad404ee7833e3ded20646dc508daf1014d90559a83cc53bc893af` | 874 |
| this record | not self-hashed; reported in the session hand-off | — |

No existing file was edited. Nothing was staged, committed, stashed or pushed. Files whose name
contains `d1_train_label_completeness` were not touched.

## 2. Start-of-task state [VA]

- Read in full: `AGENTS.md`, `PROJECT_MEMORY.md` (head), the contract, Addendum 1, the addendum QA
  record, the authorization record, the contract QA record. Sibling notes
  `fusion_r1_contract_notes.md` and `fusion_r1_addendum_1_notes.md` read as data.
- `shasum -a 256` of the five bound documents, all equal to the brief:

  | Document | SHA-256 |
  | --- | --- |
  | `docs/review/d1_yolo54_classifier_fusion_r1_contract.md` | `40cbe72ff095b8aea9d2253c02a52c013797b2148febc4bbbd647e68a77c700c` |
  | `docs/review/d1_yolo54_classifier_fusion_r1_addendum_1.md` | `fa2ea121623a0072256cd56e88ba1d1e60a90cd85a51f0869fa5d70623bdd6e9` |
  | `docs/review/d1_yolo54_classifier_fusion_r1_addendum_1_independent_qa_record.md` | `b483788d4056722ccb2a6e6192afced592cc887afbcc844e3527a956874e632c` |
  | `docs/review/d1_yolo54_classifier_fusion_r1_owner_authorization_2026-11-05.md` | `9f8c5f20c4dab52258d64270d490fc720c941bc1478a22550a549560e3556fcd` |
  | `docs/review/d1_yolo54_classifier_fusion_r1_contract_independent_qa_record.md` | `aa3c4e384118a02fa28fb790d056951221334c7ecdefa410e02f381b83d5e902` |

- `git log --oneline -3`: `17db663 docs(review): pre-registered YOLO54+CompactCNN fusion R1 contract, QA PASS giới hạn`;
  `399bf70 feat(d1): paired A3−pilot validation CIs with independent QA PASS`;
  `5e3fa2a docs(review): R3 addendum — A3 executed via D1-A3-R2, criteria not met`.
- `git status --short | head -60`: 13 ` M` Owner files (`PROJECT_MEMORY.md`,
  `docs/product_roadmap.md`, `docs/review/cam_hanh_trinh_display_rename_r1_2026-11-04.md`,
  `docs/review_index.md`, `scripts/run_parallel_checks.py`, five `src/cpv301_autodrive/*`, three
  `tests/*`), then `??` entries under `detector/colab/`, `detector/m1/`, `detector/tests/`. The same
  13 ` M` files remain at the end.
- `graft check .`: `graph check: OK — the wiring graph is in sync with the code`.
- Reference code read through Graft (`graft skeleton`) and the cited spans:
  `detector/m1/metrics.py` (`match`, `operating_point`, `group_bootstrap`, `latency_stats`),
  `detector/colab/evaluate_cascade_b0_r1.py` (`crop_bounds`, `crop_prediction`,
  `average_precision`, `infer`, `load_pinned_baseline`), `detector/m1/sahi_eval_r1.py` (constants,
  `size_recall`, `latency`, `write_new`, `verify`), `detector/m1/val_reeval_r2.py` (`guard_path`,
  `image_files`, `source_qa_passed`, `write_exclusive`, `_rename_exclusive`, `publish`,
  `class_map`, `_r3_roster_hash`), `detector/m1/a3_pilot_paired_ci_r1.py` (`gt_frames`,
  `with_predictions`, `frame_stats`, `resample_indices`, `paired_block`, `map_block`),
  `detector/d1_cascade_classifier/model.py` and `data.py`, and the checkpoint save/load code in
  `detector/colab/train_compact_improvement_r2.py:460-461` and
  `evaluate_compact_improvement_r2.py:74-81`.

## 3. What the module does [VB for code paths exercised by tests or `step0`; P otherwise]

Subcommands (from `detector/`, `uv run python -m m1.classifier_fusion_r1 …`):

| Command | Behaviour | Executed today |
| --- | --- | --- |
| `step0` | Verifies every pin and the full bundle manifest, rebuilds arm A from the pilot CSV and the R3 labels, prints Step 0. No classifier, no fusion number, no write | **Yes** (§6) |
| `latency` | Prints the C3 schedule (first measured iterations and the AB/BA counts). Measures nothing: the live latency arm runs only inside `run`, after Step 0 (Addendum 1 §2 order) | Yes (synthetic CLI test) |
| `run --source-qa-record <repo-relative path> --source-qa-sha256 <hex>` | The single execution: QA gate → output-existence gate → pins → latency preflight → Step 0 → CPU accuracy arm → MPS recompute → latency arm → guards/outcome → write-once publish | **No** (only its refusal gates, on a synthetic root) |
| `verify` | Model-free: re-verifies inputs, rebuilds the predictions CSV and the eval JSON from the two CSVs plus the two measured inputs, compares bytes, checks manifest output hashes | No (rebuild logic tested synthetically) |

### 3.1 Inputs and the Q4 symlink policy

- **Decision (Q4):** the module reads validation images, labels and the group map **only from the
  N1 bundle** `tmp/yolo11n_n1_extract_r1/data` (Addendum 1 §7 allows it). Bundle images are regular
  files. Every input path goes through `val_reeval_r2.guard_path`, which refuses an absolute or
  `..` path, any component containing `test` (case-insensitive substring, so `latest` is refused
  too) and any symlink component; `regular_file` additionally requires `S_ISREG` via `lstat`.
- **Consequence:** the WP38-R1 integration R4 export (`data/processed/m1_yolo_wp38_r1_integration_r4/images/val`,
  symlinks into `data/raw/DATASET01/...`) is **not used and would be refused**. The
  `val_reeval_r2` governed-link rule is therefore not needed and not implemented. `data/processed/m1_yolo/images/val`
  (the `.jpg`/`.png` hazard) is never referenced.
- Bound at load (`load_state`): 22 file pins (`PINS`), full manifest re-verification (8,579
  members, size + SHA-256, no `test` member, no `data/*test*` directory), the bundle CSV member equal
  to the run-directory CSV `87884c53…`, image roster `24e2a67d…` (`{name: sha256}` hash), R3
  label roster `dc72ebd9…` (`_r3_roster_hash`), 624 GT, 376 frames, 9 groups, and the bundle group
  map equal to `wp36_r1_split_frames.csv` for all 376 stems. Arm A's authoritative candidates are
  read from the run-directory CSV (contract §2), validated as `load_pinned_baseline` does.
- **Implementation-time pin (new, stricter):** `detector/colab/run_cascade_b0_r1.py`
  `0ece03891ebe0f8c318efd7a062fdb8d799d4cf9cc357b0cf8840b4103ad876a`, because the pinned evaluator
  imports it. The evaluator itself (`8bedb4c1…`) is re-hashed before import.
- Class maps: `m1_yolo_classes.csv` and `signnames.csv` must agree row by row, and the contract §3
  translation (plus G5 DK 6/23/34 → yolo 6/25/35) is asserted. Every output row and per-class entry
  carries both the yolo_id and the derived key.

### 3.2 Rule F1, crop and classifier (contract §4–§5, C4, C5)

- `relabel(p, s, τ)`: `p` must be a float32 54-vector; `top1 = int(np.argmax(p))`; relabel iff
  `top1 == t and float(p[t]) >= τ` (float64 literal, inclusive). `decide` keys on the **original**
  CSV class only; a candidate whose class is not a source is never cropped (an error if it is).
  No chaining is structurally guaranteed: a second hop would need `argmax(p)` to equal two
  different targets for one vector (a mutation adding a second hop was an equivalent mutant, §7).
- `crop_input`: float64 copy of the raw box, `np.clip` x to `[0, W]` and y to `[0, H]`,
  `crop_invalid` if non-finite or non-positive extent, else the pinned `crop_prediction`; a
  `ValueError` from `crop_bounds` is also `crop_invalid`. The clipped copy is the crop input only;
  the scored box is the raw CSV box.
- `classify`: the evaluator's tensor ops in the same order (`/255`, `(x−0.5)/0.5`, `softmax(·, 1)`),
  output asserted float32 `(n, 54)`; one forward per image with source candidates.
- CPU verdict pass inside `deterministic_cpu()`: `torch.set_num_threads(1)` and
  `torch.use_deterministic_algorithms(True)`, **restored afterwards** so the MPS recompute and the
  latency arm run under SAHI R1 defaults.
- `load_classifier`: `torch.load(weights_only=True)`, SHA-256 `d1e69eef…` re-verified before and
  after, `payload["epoch"] == 18`, `payload["config"] ==` the pinned `contract.json`, strict
  `load_state_dict(payload["model"])`. The key layout is taken from the training/evaluation source
  only; it was **not** verified by loading **[U until `run`]**.
- The crop-probability CSV stores `repr(float(v))` of every float32 value; `run` re-parses that text
  and takes every decision from it, so `verify` reproduces each decision bit for bit (C5 item 7).

### 3.3 Metrics, guards and outcome (contract §6, C1, C2, C6, Q3, Q6)

- **Step 0** (`step0_check`): `operating_point(frames_A, 0.20)` — TP 547, FP 150, GT 624, images
  376, Σ hits 457, `agnostic_recall == 547/624` and `fp_per_image == 150/376` (exact float
  equality, **Q6**), per-class hits yolo 7/33/42/48/40 = 66/18/12/55/14 (**C1**), and the pinned
  evaluator's `average_precision` mAP50/50-95 within 1e-9 of 0.8520835680/0.6088678435 (tolerance
  for the mAP pair only). Inside `run`, a failure returns `INVALID` (row 1) with **no file written**
  and the stop report on stdout (exit 2).
- **Primary endpoint:** correct-class recall at 0.20 = Σ class-aware hits / 624; Δ = B − A.
- **G1** hits_B ≥ 467. **G2** paired CI lower bound > 0. **G3** TP_B = 547 = TP_A and
  FP_B = FP_A ≤ 150. **G4** hits_B yolo 7/33/42 ≥ 66/18/12. **G4b** hits_B yolo 40 ≥ 14.
  **G5** for DK 6, 8, 10, 12, 23, 34, 46: loss ≤ 2 and, if A meets its D-05 per-class reference
  (`contract.GATES`: 0.70 critical, 0.50 otherwise; none of these is critical), B also meets it;
  a G5 class with zero support raises. **G6** Δ mAP50 ≥ 0 and Δ mAP50-95 ≥ 0 (pinned evaluator).
  **G7** `L` and arm-B p95 ≤ 100 ms.
- **Outcome** (`assign_outcome`, Addendum 1 §2): first match of
  row 1 `INVALID` (¬S0 ∨ ¬G3 ∨ ¬L), row 2 `NO_GO` (Δ ≤ 0 ∨ ¬G4 ∨ ¬G4b ∨ ¬G5 ∨ ¬G6), row 3
  `NO_GO_UNCERTAIN` (¬G1 ∨ ¬G2), row 4 `NO_GO_LATENCY` (¬G7), row 5 `GO_CANDIDATE_FOR_CONFIRMATION`.
  The eval JSON records every boolean (`S0, L, delta_positive, G1…G7, G4b`), `failed_guards`
  (all failing conditions), `outcome` and `outcome_row`.
- **Paired bootstrap (C6):** `np.random.default_rng(20261018)`, 1000 rounds, per round
  `rng.choice(sorted(groups), size=9, replace=True)`, the same draw applied to both arms; per-frame
  additive counts as in `a3_pilot_paired_ci_r1`. Reported: Δ CI of correct-class recall (G2), and
  arm-A/arm-B marginal CIs of agnostic recall and FP/image. Paired mAP50/50-95 Δ CIs are reported as
  `REPORTED_NOT_DECISIVE`.
- **Reported, not decisive (§6.3):** per-class hits/support/recall for every supported class (both
  keys); per-class AP50 for both arms; per pair: candidates (all scores / ≥ 0.20), cropped,
  `crop_invalid`, relabels (all scores / ≥ 0.20); help/harm; `crop_invalid` and cropped totals;
  same-class overlaps at IoU ≥ 0.70 involving a relabelled box (all scores and ≥ 0.20); size bins;
  CPU/MPS differences; sensitivity τ ∈ {0.50, 0.95} and leave-one-out per pair, every entry labelled
  `SENSITIVITY_NOT_DECISION` and never read by `guards`.
- **Definitions fixed here [P] (the contract left them open; QA should confirm):**
  - *help / harm (total):* per GT at conf 0.20, class-aware miss under A → hit under B is help,
    hit → miss is harm; also split by GT size bin √(w·h) (`<16`, `16–32`, `32–64`, `≥64`).
  - *help / harm per pair:* the **isolated** counterfactual "A plus only that pair's relabels" vs A,
    because a GT change in a frame with several relabels cannot be attributed uniquely.
  - *relabels by size bin:* binned by the **predicted box** √(w·h), since a relabelled box may match
    no GT; help/harm use the GT size.
- **CPU/MPS:** MPS decisions at τ = 0.80 are stored in the eval JSON as `cpu_mps.mps_relabel_rows`
  (a measured input); the differences against the CPU decisions are recomputed. The verdict uses
  CPU only. `run` refuses if the CPU and MPS crop sets differ.

### 3.4 Latency arm (§6.4, C3, Q1, Q2)

- `latency_protocol`: warm-up iterations 0–49 and measured iterations 0–299, parity indexed
  separately; even = A then B, odd = B then A; both arms use the same image; each arm's timed span
  is `start → arm(path) → sync() → stop`, and the arm reads its own image.
- **Q2 (bound):** measured iteration `j` uses validation image index `(50 + j) % 376` (the cycle
  continues after warm-up, exactly as SAHI R1's single `index % len(images)` loop). Warm-up
  iteration `i` uses image `i`.
- **Q1 (bound):** a measured sample is valid iff the timed call returned without exception and its
  duration is finite and > 0 ms. `L` is true iff the arm completed, each arm has exactly 300
  measured samples, all valid, and the orders are 150 AB / 150 BA. Any exception during setup or a
  sample is recorded (not raised); `L` false → `INVALID` (row 1).
- Each raw sample stores `iteration`, `image_index`, `image`, `order`, `position`, `arm`, `ms`,
  `valid`, `error`. The latency JSON also stores the image roster hash and
  `timed_sequence_sha256` (hash of the full warm-up + measured schedule with file names).
- Arm A: PIL read + `convert("RGB")` → BGR array → `predict(conf=0.20, iou=0.70, imgsz=1280,
  device="mps", max_det=300)`. Arm B: the same, then source-class boxes → C4 crop → one MPS
  classifier forward (none when no source box; still timed) → F1. Arm A uses the PIL read (not
  SAHI's `ultralytics.utils.patches.imread`) so that both arms share the same read; this is a
  deliberate difference from SAHI R1's arm and is disclosed here.
- **Latency preflight before Step 0 (new, fail-early):** `run` checks MPS availability,
  `contract.bind_run_weights` (the SAHI R1 binding, needs the git-tracked clean run registry) and
  the torch/ultralytics versions against the pinned SAHI R1 latency JSON, **before** any metric is
  computed, so an unusable environment refuses the run instead of consuming it as `INVALID`.
  Observed today: torch 2.14.1 and ultralytics 8.4.172 in `detector/`, equal to SAHI R1's
  environment record; `torch.backends.mps.is_available()` = True **[VB]**. The preflight function
  itself was not executed.

### 3.5 Source-QA gate and write-once outputs

- `check_source_qa` runs first in `run`. It refuses unless both CLI arguments are present, the hash
  is 64 lowercase hex digits, the record path is repo-relative and passes `guard_path` (no symlink,
  no `test`), its bytes hash to `--source-qa-sha256`, the NFC-normalised text has **exactly one**
  line starting `Verdict:` and that line is `Verdict: PASS…` or `Verdict: PASS giới hạn…` (optional
  `**` bold; `PASSED`, `PASS_WITH…`, `NOT PASS`, `FAIL` are refused), and the record quotes the
  current SHA-256 of this module, the contract and Addendum 1.
- **Limit [P]:** the gate cannot tell whether a `PASS giới hạn` lists a correction required before
  execution. Under the authorization record's reading rule such a record does not authorize the
  run; the coordinator must not invoke `run` with it.
- `refuse_existing_outputs` (before any input read, and again before publishing) refuses if
  `<run>/classifier_fusion_r1/` or any of the five output names exists, including a dangling
  symlink (`os.path.lexists`).
- `publish`: a private staging directory, every file created with
  `O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW` (`val_reeval_r2.write_exclusive`, fsync, read-back), then one
  exclusive rename (`renamex_np RENAME_EXCL`); on any failure the staging directory is removed.
- Outputs (contract §8): `fusion_r1_predictions_conf0001.csv` (1,999 rows, pilot order, exact
  schema `stem,rank,yolo_id,fused_id,derived_key,fused_derived_key,conf,x1,y1,x2,y2,pair,p_target,p_source,top1_id,relabelled,crop_invalid`,
  original `conf`/box strings re-emitted verbatim), `fusion_r1_crop_probs.csv`
  (`stem,rank,yolo_id,derived_key,pair,p_00…p_53`, cropped source rows only),
  `fusion_r1_eval.json` (canonical: sorted keys, `allow_nan=False`), `fusion_r1_latency_mps.json`
  (canonical), `fusion_r1_manifest.json` (module, tests, contract, addendum, authorization, all
  input pins, the four other outputs, flags; **no QA record**, as the contract requires; the
  source-QA record hash appears only in `run`'s stdout).
- `verify` rebuilds from the two CSVs. Two measured inputs cannot be recomputed without a model and
  are carried through: the latency JSON (its statistics, `L` and G7 are recomputed from the raw
  samples) and `cpu_mps.mps_relabel_rows` (the differences are recomputed).

## 4. Recommended clarifications Q1–Q6 — where they are bound

| ID | Binding |
| --- | --- |
| Q1 | `latency_protocol` / `summarize_latency`: valid = no exception, finite, > 0 ms; `L` needs 300 valid per arm and 150/150 orders (§3.4) |
| Q2 | `latency_schedule`: measured `j` → image `(50 + j) % 376`; warm-up `i` → image `i` (§3.4) |
| Q3 | `test_paired_bootstrap_nonzero_delta_has_known_sign_and_pairing`: B gains exactly 2 hits inside group G4; per-round Δ = 2·copies(G4)/GT(draw) is checked against the paired CI, its sign, the zero rounds and the arm swap |
| Q4 | Bundle-only, regular files only, every symlink refused; R4 export not used (§3.1); `test_test_paths_and_symlinks_are_refused` builds the R4 link pattern and expects refusal |
| Q5 | Documentation of the authorization record; no code change applies. Noted, not acted on (the authorization record is not edited) |
| Q6 | `step0_check`: `agnostic_recall == 547/624`, `fp_per_image == 150/376` (exact), 1e-9 only for mAP (§3.3) |

Addendum 1 items: C1 → G4b + Step 0 yolo 40 = 14; C2 → `assign_outcome`, `failed_guards`,
`outcome_row`, latency after Step 0 regardless of accuracy guards; C3 → §3.4; C4 → `crop_input`;
C5 → `relabel` + `repr` text; C6 → `resample_indices` + tests (a)/(b); C7 → bundle verification;
C8 → disclosed in the eval JSON `claim_scope`.

## 5. Tests (synthetic only) [VB]

`detector/tests/test_classifier_fusion_r1.py`: 25 test functions, **42 cases** (15 parametrised
outcome rows, 4 accepted verdict forms). Every frame, box and probability is synthetic; the real
class-map files are not read (a synthetic map is written to `tmp_path`); the pinned evaluator is
imported for its code (crop rule, Ultralytics AP) and run on synthetic frames only.

| Required coverage | Test(s) |
| --- | --- |
| FP invariant | `test_relabel_only_preserves_tp_fp_and_agnostic_recall` (25 random relabellings + F1), `test_a_moved_box_breaks_g3_and_is_invalid` |
| No chaining, P2/P4 overlap | `test_no_chaining_and_p2_p4_overlap` (19→7 not re-examined, 7→33, 19 with top1 33 stays, LOO keeps original-class keying) |
| τ boundary at 0.80 | `test_tau_boundary_is_inclusive_on_float32_values` (0.800000011920928955078125 relabels, 0.7999999523162841796875 does not, all six pairs); `test_argmax_clause_binds_only_in_an_exact_tie_on_the_grid` |
| Invalid crop | `test_invalid_crop_predicate_and_backstop` (NaN, zero width/height, outside, inverted, `-inf` clipped, `ValueError` backstop, CSV row written with `crop_invalid=1` and empty fields) |
| Every outcome row | `test_every_outcome_row` (15 cases) and `test_outcome_mapping_is_total_unique_and_follows_precedence` (all 2,048 boolean combinations vs an independent precedence implementation) |
| Bootstrap equivalence at Δ = 0 | `test_bootstrap_draws_equal_group_bootstrap_and_zero_delta_is_exact` (heterogeneous groups, shuffled frame order; arm-A CIs == `group_bootstrap` exactly; B ≡ A → `[0.0, 0.0]`) |
| Non-zero paired Δ (Q3) | `test_paired_bootstrap_nonzero_delta_has_known_sign_and_pairing` |
| Write-once refusal | `test_publish_is_write_once_and_refuses_symlinks`, `test_run_gate_accepts_pass_forms_then_refuses_existing_output` (existing directory and dangling symlink) |
| Source-QA gate refusal | `test_run_refuses_without_a_source_qa_pass` (missing args, bad hex, wrong hash, FAIL / NOT PASS / PASSED / PASS_WITH_NOTES / two verdicts / none, missing quoted hashes, absolute path, symlinked record) |
| Test-path refusal and symlink policy (Q4) | `test_test_paths_and_symlinks_are_refused`, `test_bundle_manifest_with_test_member_or_bad_member_is_refused`, `test_pilot_csv_parser_refuses_out_of_scope_rows` |
| Other | class-map translation, one forward per image + float32, probability CSV bit-exact round trip, latency counterbalancing / Q1 invalid samples, byte-identical model-free rebuild and tamper detection, overlap and help/harm counting, `latency` CLI measures nothing |

**Mutation check [VB]** (module patched in place, suite run, module restored; restored file hash
re-checked equal to §1): `>=` → `>` at τ: caught; outcome rows 2/3 swapped: caught; removing the x
clip: caught; unsorted group names in the draws: caught (after making the bootstrap test's groups
heterogeneous and its frame order shuffled — the first version missed it); adding a second relabel
hop: survived, an equivalent mutant (§3.2).

## 6. Step 0 on the real pilot CSV (pilot-only; no fusion) [VB]

Command: `(cd detector && uv run python -m m1.classifier_fusion_r1 step0)`, exit 0, about 4 s.
Inputs: 22 pins verified, bundle 8,579/8,579 members verified (full), image roster `24e2a67d…118e`,
label roster `dc72ebd9…8343`, CSV `87884c53…c893`, images from `tmp/yolo11n_n1_extract_r1/data/images/val`.

| Check | Observed | Reference | Pass |
| --- | --- | --- | --- |
| Images / GT | 376 / 624 | 376 / 624 | yes |
| TP / FP at 0.20 | 547 / 150 | 547 / 150 | yes |
| Σ correct-class hits | 457 | 457 | yes |
| Agnostic recall | 0.8766025641025641 (== 547/624) | 547/624 | yes |
| FP/image | 0.39893617021276595 (== 150/376) | 150/376 | yes |
| Hits yolo 7/33/42/48 (DK 7/32/41/46) | 66 / 18 / 12 / 55 | 66 / 18 / 12 / 55 | yes |
| Hits yolo 40 (DK 39), G4b reference | 14 | 14 | yes |
| Common-path mAP50 | 0.8520835680058519 | 0.8520835680 ± 1e-9 | yes |
| Common-path mAP50-95 | 0.6088678434901063 | 0.6088678435 ± 1e-9 | yes |

`step0.passed = true`, `fusion_metric_computed = false`, `classifier_loaded = false`. No file was
written.

## 7. Gates [VB]

| Command | Result |
| --- | --- |
| `(cd detector && uv run pytest -q tests/test_classifier_fusion_r1.py)` | 42 passed, exit 0 |
| `(cd detector && uv run ruff check m1 tests)` | `All checks passed!`, exit 0 |
| `uv run ruff check src tests` | `All checks passed!`, exit 0 |
| `uv lock --check` (root) | `Resolved 201 packages`, exit 0 |
| `(cd detector && uv lock --check)` | `Resolved 66 packages`, exit 0 |
| `graft build . && graft check .` | `parsed: 2 of 496 files`; `graph check: OK`. `.gitignore` already listed `/graft/` (line 30) and is unchanged |
| `graft blast` | 13 changed (Owner) files, 0 impacted symbols; the two new files are untracked and have no indexed dependents |

`ruff format` was applied to the two new files only.

## 8. Not done, not verified, open points for source QA

- **Not executed:** `run`, the latency arm, the latency preflight, `load_classifier`, the MPS
  recompute, `verify` on real outputs. No output directory exists.
- **[U]** checkpoint payload layout (`model`, `epoch`, `config`) and strict state-dict load — from
  source reading only; a mismatch would make `run` raise after Step 0 and before any write.
- **[U]** whether `contract.bind_run_weights` still passes (needs the run registry git-tracked and
  clean); the preflight would refuse before Step 0 if not.
- **[P] for QA to confirm:** the help/harm and size-bin definitions in §3.3; the arm-A image read in
  §3.4; G5's zero-support raise; the implementation-time pin of `run_cascade_b0_r1.py`; that the
  manifest omits the source-QA record (contract wording) while `run`'s stdout reports it.
- Runtime of `run` is expected to be dominated by the 1,000-round paired mAP bootstrap and the
  latency arm (minutes); not measured.
- The coordinator invokes `run` exactly once, only with a source-QA record whose verdict is PASS or
  a PASS giới hạn without corrections required before execution, and only after a further
  `git status`/pin check if anything changed since this record.

## 9. Flags

`sealed_test_accessed=false`, `training_authorized=false`, `inference_run=false` (no YOLO, no
classifier), `fusion_metric_computed=false`, `classifier_loaded=false`, `app_enable_authorized=false`,
`threshold_lock_written=false`, `d05_changed=false`, `existing_files_edited=false`,
`commit_or_push=false`.
