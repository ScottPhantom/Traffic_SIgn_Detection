# D1 YOLO54 improvement R3 — independent QA record (source and evaluation readiness)

Reviewer: Claude Code, independent QA session (reviewed R1 and R2, did not author R3) · Date:
2026-10-23 · Worktree `.claude/worktrees/centercam-yolo54-r1`, branch `claude/centercam-yolo54-r1`,
HEAD `b901255`, with the R3 files uncommitted. The evidence root is the main checkout
`/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, which was only read. Boundary respected:
no training, inference or model load, no Colab or Drive, no sealed test, no commit, no write or git
operation in the main checkout. The one file QA wrote is this record.

## 1. Hashes reviewed

All seven match the handoff values.

| File | SHA-256 |
| --- | --- |
| `docs/review/generated/d1_yolo54_improvement_r3_manifest.json` | `b14d21048cf372395a8e4370d1a1f0845755acfb1348cec2592b441e8d7ab667` |
| `detector/m1/yolo54_improvement_r3.py` | `548144b107714d95427b1704700a2ff8cd879143d8f2366e931afecf6777a639` |
| `detector/tests/test_yolo54_improvement_r3.py` | `70ca887414e268b630ba9686f8a9282d15d264556712a889b381703aa2341b62` |
| `docs/review/d1_yolo54_improvement_r3_contract.md` | `3382de28faa960f3c0be3acc28a1ca2d7d17192bfe371f8affca347c6886162f` |
| `docs/review/d1_yolo54_improvement_r3_implementation_record.md` | `667d4f309184d7395bda4c21907418a1d65924b3193f577e0325d67551699316` |
| `docs/review/d1_yolo54_improvement_r3_qa_brief.md` | `7febb84e5b9ab3e9d9d832b5bd506f65dbfea7bc85f4549b67bacdd3ddcdac7f` |
| `docs/review/generated/d1_yolo54_improvement_r3_analysis.json` | `214aaf404c28cc19edcbbd4216e174e569e6bd44c7ef39d134728361aa44c97b` |

`git status` shows only these seven untracked files, and `git diff --stat b901255` is empty, so R1,
R2 and every shared file are unchanged. `detector/m1/metrics.py` in the worktree equals the main
checkout's copy (`d24570f8…`).

## 2. Commands and results

| Command | Result |
| --- | --- |
| `uv run ruff check` and `ruff format --check` on the module and its tests (from `detector/`) | `All checks passed!`; `2 files already formatted` |
| `CPV301_EVIDENCE_ROOT=<main> uv run pytest -o addopts="" -q tests/test_yolo54_improvement_r3.py` | `45 passed in 14.59s` |
| The same without `CPV301_EVIDENCE_ROOT` | `44 passed, 1 skipped` (the real-evidence test skips) |
| `uv run python -m m1.yolo54_improvement_r3 check --evidence-root <main>` | exit 0; `pins: 25`; TP 547, FP 150, GT 624, images 376, recall 0.8766025641025641, FP/image 0.39893617021276595, precision 0.7847919655667145; bootstrap CI recall [0.8138, 0.9514], FP/image [0.1449, 0.8158]; `d05_q4_conf 0.2` |
| QA rebuild `analyse(<main>)` then `canonical(...)` (scratchpad `qa_r3_rebuild.py`) | **byte-identical** to the analysis JSON (`214aaf40…`, 18 s). `evidence_pins == PINNED`. All 6 manifest file hashes match, and the manifest `evidence_pins == PINNED`. |
| QA guard and parser probes (scratchpad `qa_r3_guard.py`, temporary root) | §3.7 and §3.8 below |
| `graft check .` (worktree) | `graph check: OK` |

QA did not rerun the full detector and root suites, and it takes the author's 16 and 768
data-gap failures as reported. They do not touch the R3 module, which adds no root `src` or
`tests` file.

## 3. Results by brief check

1. **Evidence binding.**
   - All 25 `PINNED` hashes verify against the evidence root (`check`).
   - The manifest matches the package files.
   - The analysis `evidence_pins` equal `PINNED`.
   - The manifest pins no R3 QA record. It does pin three **predecessor** QA records as evidence;
     see L1.
2. **Scientific validity.**
   - **A0b exactness holds.** The raw candidates come from `cli.iter_image_predictions` (pinned
     `cli.py` `3e0c13b3…`, lines 142–150), called by `corrected_val_r1.py:158`. The call uses
     `model.predict(conf=0.001, iou=0.70, max_det=300)` and leaves `agnostic_nms` and
     `multi_label` at their Ultralytics 8.4.172 defaults of `False`.
   - In `utils/nms.py`, class-wise NMS separates classes by a `max_wh` offset (line 146). A kept
     box can be suppressed only by a higher-scoring box of the same class, which survives any
     per-class threshold that the lower box survives.
   - Other conditions that could break exactness do not apply:
     - `max_det`: the maximum is 29 candidates per image, and the code checks it;
     - `max_nms` (30,000): at 1280 px there are about 19k anchors;
     - the NMS time limit: batch 1, so no other image is cut.
   - The comparison is `>=` in `metrics.match` and `apply_thresholds`, against `>` in
     Ultralytics. No candidate equals a grid value; the minimum gap is 8.6e-6.
   - The search space is 4 classes × 3 values plus 1 combined probe = 13 configurations, as
     coded and stored.
   - No configuration lifts classes 7, 32 and 41 to ≥ 0.70 together (QA scan: empty set).
   - The minimum class-wise FP/image is exactly 0.39894. FP is monotone, because a lower-scoring
     added box cannot change the greedy outcome of the boxes above it.
   - The first global threshold with FP/image ≤ 0.30 is 0.35, at recall 0.776.
   - The implementation-record table matches the JSON.
3. **Metric compatibility.**
   - `reproduce` checks the fixed point, the per-class hits, the 1000-round CI and the Q4
     selection exactly, against the pinned report.
   - `bootstrap_samples` uses the same `default_rng(seed)`, the same sorted group names, the same
     `rng.choice` call and the same group-concatenation order as `metrics.group_bootstrap`. The
     per-frame counts are additive. `analyse` refuses unless the 0.20 CI equals the
     `group_bootstrap` CI, and the rebuild passed that check.
   - Matching, IoU 0.5, the gates and the critical keys come from `m1.metrics` and `m1.contract`.
4. **Pre-NMS versus post-NMS.**
   - A0 is `A0_REQUIRES_VALIDATION_ONLY_REINFERENCE`, with `agnostic_nms_verified=false`,
     `nms_grid_evaluated=false` and `reinference_authorized=false`. Even the
     `PRE_NMS_CANDIDATES` branch evaluates nothing.
   - The re-inference contract is a proposal (contract §3).
5. **No validation leakage.**
   - The A2 roster reads only `labels/train` and the WP35 source labels. It verifies the raw stem
     list `6ac76750…`, the raw labels `d907fb9f…`, the 1,800 lineage hashes, and the
     source→export id mapping.
   - QA checked that all 1,800 WP35 `source_stem`s are WP36-R1 **train** frames. The code does not
     check this itself; see L4.
   - The R3 validation labels are used for scoring only. A1 is blocked.
6. **No sealed-test access.**
   - The guard refuses any component containing `test`, and label directories refuse such
     entries.
   - No test directory is listed or created.
   - `sealed_test_accessed=false`, `test_included=false` and `training_authorized=false`
     throughout the analysis.
7. **Path attacks** (probes on a temporary root). Each of these is refused:
   - an absolute path, `..` and the empty path;
   - a hardlinked file (`st_nlink` 2);
   - a symlinked directory in the chain and a symlinked file;
   - a `testing/` component;
   - a `.DS_Store` entry and a directory named `sub.txt` inside a label folder.

   `package_source=True` appears exactly once, in `write_manifest`, over the fixed
   `PACKAGE_FILES`. It still refuses symlinks, hardlinks and escapes.
8. **Fail-closed behavior.**
   - Refused CSV inputs: NaN, Inf, a float rank, a non-integer class, a wrong header,
     non-contiguous ranks, ascending scores, and an image at 300 rows.
   - `_strict_bool_false` refuses `0` and `None`.
   - `_strict_int` refuses `True` and `3.0`.
   - The author's tests cover the hash, roster and group-map changes and the preflight→write
     change.
9. **Determinism.** The rebuild is byte-identical (§2).
10. **A2/A3 freeze.**
    - Each run changes one thing.
    - Both are `WAITING_FOR_L4_AND_OWNER_AUTHORIZATION` with `training_authorized=false`.
    - `DB_logger.db`, `colab_train.log`, `colab_execution.json`, `execution_attempts.jsonl` and
      `<run>_result.tar.gz(.manifest.json)` all appear in `colab/run_d1_colab_pilot_r5.py`.
    - The A2 executable-path gap is disclosed.
    - The A3 criterion supersedes R2's wording; see L5.
11. **No interaction with Cascade B0.** The module and tests have no Colab, Drive or Cascade
    reference. No Codex-held file was changed, and nothing was committed.

## 4. Findings

Critical: none. High: none. Medium: none.

### Low

- **L1 — "Never pins a QA record" is literally false.** Contract §7, the brief (check 1) and the
  `write_manifest` docstring say the manifest pins no QA record. It pins three predecessor QA
  records as evidence: `d1_vre_r2_source_independent_qa_record.md`,
  `d1_vre_r2_result_independent_qa_record.md` and `d1_ea_r1_independent_qa_record.md`. The intent,
  not pinning the package's **own** QA record, is met.
  *Reproduction:* `[p for p in manifest["evidence_pins"] if "qa_record" in p]` returns 3 paths.
  *Fix:* reword to "never pins this package's own QA record".
- **L2 — Degenerate and near-degenerate CIs are under-disclosed.** The contract gives class 32
  `[0.138, 0.138]` as the example. QA's group count on the R3 labels shows:

  | Class | Groups |
  | --- | --- |
  | 32 | 1 (D02-C0020: 29) |
  | 7 | 2 (D02-C0009: 68, D02-C0044: 43) |
  | 41 | 2 (D02-C0045: 14, D02-C0031: 12) |
  | 46 | 2 (D02-C0020: 35, D02-C0001: 69) |

  Every focus-class paired CI is therefore a mixture of at most two group ratios, not a usable
  uncertainty estimate. Examples: class 7 at 0.05 gives `[0.059, 0.186]`, and class 41 at 0.05
  gives `[0.0, 0.143]`.
  *Fix:* store the per-class group count in the JSON, and state that focus-class CIs with ≤ 2
  groups are non-informative.
- **L3 — Exactness preconditions are not checked from the report.** The D1-VRE-R2 report
  `settings` hold no `agnostic_nms`, `multi_label` or `max_det` field. `load_report` checks
  `candidate_conf`, `nms_iou` and `iou_match`, and `max_det` is a module constant. The
  preconditions hold through the pinned `cli.py` and the Ultralytics defaults (§3.2), but the
  code asserts none of them, and the `>=` against `>` boundary is not asserted.
  *Fix:* record the source line evidence in the JSON, and assert that no candidate score equals
  a threshold value.
- **L4 — The A2 lineage split is not verified in code.** `a2_repeat_roster` checks the WP35
  label hashes against the pinned lineage, but not that each `source_stem` is a WP36-R1 train
  frame. QA verified that all 1,800 are train frames, so there is no leak today, but the guarantee
  rests on the pinned lineage.
  *Fix:* join `source_stem` to `wp36_r1_split_frames.csv` and refuse non-train frames.
- **L5 — The A3 criterion is underspecified, and its supersession is document-only.** R3 says
  "FP/image compared at the highest grid confidence whose recall reaches 0.8766, against the
  pilot's 0.3989" without a pass direction or margin. The QA-passed R2 module still prints its
  non-inferiority wording in `plan`, and the supersession lives only in the R3 contract.
  *Fix:* state "≤ 0.3989", and note in the next R2 successor's `plan` output that R3 supersedes
  it.
- **L6 — The preflight→write re-check covers `PINNED` only.** `publish` re-verifies the 25
  pinned files. The R3 label roster (`dc72ebd9…`) and the train label roster and hashes are
  checked at load only, which partly contradicts contract §7, "after every pin is re-verified".
  The risk is negligible on a read-only evidence root.
  *Fix:* re-run `load_r3_labels` and the A2 roster hash in `publish`.

### Informational

- **I1.** `check` does not run the paired-bootstrap equality; only `build`/`analyse` does, and
  only when `rounds == 1000`.
- **I2.** The global-grid 0.20 baseline and A0b both score at conf 0 after per-class filtering.
  This equals `operating_point(frames, 0.20)`, as the reproduction confirms.
- **I3.** The main checkout's `git status` held pre-existing uncommitted changes (79 lines). QA
  wrote nothing there.

## 5. Verdict

Counts: 0 Critical, 0 High, 0 Medium, 6 Low, 3 Informational. The A0b exactness argument, the
compatibility gate, the paired bootstrap, the post-NMS honesty of A0, the leakage and sealed-test
boundaries, the path guards and determinism all hold on independent reproduction. Status may move
to `YOLO54_IMPROVEMENT_R3_SOURCE_READY`. This verdict authorises no training, re-inference, test
access, upload, commit or push.

Verdict: **PASS**
