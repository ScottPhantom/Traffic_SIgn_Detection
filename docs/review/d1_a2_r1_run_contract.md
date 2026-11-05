# D1-A2-R1 frozen run contract — YOLO11s-54 repeat factor for classes 7/32/41

Status: `FROZEN_AWAITING_INDEPENDENT_SOURCE_QA_NOT_AUTHORIZED`
Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Author: Claude Code (Opus 5.5), side session started by the coordinating session.
Boundary: source and documentation only. No training, Colab, upload, inference, threshold change,
D-05 change or sealed-test access happened. `training_authorized=false`,
`sealed_test_accessed=false`.

## 1. Authority and scope

| Authority | SHA-256 | Role |
| --- | --- | --- |
| `docs/review/d1_yolo54_improvement_r3_contract.md` | `3382de28faa960f3c0be3acc28a1ca2d7d17192bfe371f8affca347c6886162f` | Binding spec: §5 A2 row |
| `docs/review/d1_yolo54_improvement_r3_addendum_a3_executed_2026-11-05.md` | `a1ab05c185f5befa4ab28607662a71a3e6fb80fe28e81368c64a5c1366c74642` | A2 unchanged, unauthorized; 975-vs-339 open |
| `docs/review/generated/d1_yolo54_improvement_r3_analysis.json` | (R3 output; roster below) | Computed A2 roster |
| Pilot `run_contract.json` | `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88` | Pilot train args |
| Pilot `args.yaml` | `a457c6d51547477348c19a06ec4cf3c8794508169b2e0e1a43edc6260b7d16f0` | Pilot effective args |
| `docs/review/d1_a3_r1_run_contract.md` / `d1_a3_r2_run_contract.md` | `ed6754f3…8cd71c33` / `2cf71027…4115a47e` | Launcher/trainer precedent |

The pilot run is
`D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2`.

This contract authorizes nothing. It freezes the A2 experiment and its source package so that an
independent source QA can review them. Training needs a separate written Owner authorization
record (§6) and an NVIDIA L4 runtime.

## 2. Frozen experiment

A2 changes exactly one thing from the pilot: the train list. Every train image whose exported label
holds derived-key class 7, 32 or 41 is listed twice. There are no new pixels, and validation and
test data are not touched.

| Field | Value | Source of the value |
| --- | --- | --- |
| experiment | `D1-A2-R1` | this contract |
| architecture | YOLO11s, 54 classes | pilot |
| pretrained | `models/pretrained/yolo11s.pt`, SHA-256 `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5` | pilot |
| seed | `20261018` | pilot |
| epochs | `100` exactly; an early-stopped result is rejected | pilot |
| patience | `0`, as in the pilot `args.yaml` and `run_contract.json`. Ultralytics reads 0 as "no early stopping". | pilot |
| image size / batch | `1280` / `4` | pilot |
| workers / fraction / device | `4` / `1.0` / CUDA `0` | pilot |
| `fliplr` | `0.0` | pilot, D-05 forbidden override |
| deterministic / pretrained / plots | `True` / `True` / `False` | pilot |
| optimizer | not passed (`auto`), as in the pilot | pilot |
| **data** | runtime YAML `data/processed/d1_a2_r1/runtime/a2_data.yaml`. It is the pilot export `data.yaml` with the `train:` line alone changed to the A2 runtime list. | **the single change** |
| tag | `a2_r1` | run identity only |
| Drive state suffix | `M1_D1_Colab/runs/d1_a2_seed_20261018_r1` | run identity only |
| checkout | passed as `--expected-checkout` (40-hex). It must equal `git rev-parse HEAD`. | run identity only |

`project`, `name`, `exist_ok` and the run directory are run identity. They differ from the pilot
only because the run name contains the new tag.

### 2.1 Data delta (train only; verified artifact)

| Quantity | Value |
| --- | --- |
| Train images (M1 export `8a8df5f2…`) | 3,712 = 1,912 raw WP36-R1 frames + 1,800 WP35 train-only images |
| Repeated images | **975**: 339 raw frames and 636 WP35 images |
| Train list entries | **4,687** = 3,712 + 975 |
| Train boxes, derived key 7 (yolo_id 7, `P.123a`) | 83 raw + 145 WP35 |
| Train boxes, derived key 32 (yolo_id **33**, `P.123b`) | 86 raw + 52 WP35 |
| Train boxes, derived key 41 (yolo_id **42**, `P.127`) | 171 raw + 439 WP35 |
| Repeated roster SHA-256 | `0ce6afdc84ffab0db361920c4c7817517353fd8b1b901e51770d2f3f4eb69aa3` |
| Canonical A2 list SHA-256 | `90d735d67bde2bf736b5fc8570110561f0184747f3fb25c8f42a3a599d0fdec2` |
| List manifest SHA-256 | `12f09435a923cfe9e11c6c62f63d1c9906e9840d75ed2908df755bc30b110cbd` |

The roster hash is SHA-256 of the sorted repeated stems joined by `\n`, as in R3
`a2_repeat_roster`. The canonical list is one line per entry, in the form
`images/train/<stem>.jpg`, relative to the M1 export root. Stems are sorted, and each repeated stem
appears twice in a row. Ultralytics sorts image files itself, so the line order does not affect
training.

**Derived-key/yolo_id hazard.** Derived keys are not YOLO ids. The pinned class map
(`m1_yolo_classes.csv`, `7cda296a…`) maps 7→7, 32→**33** and 41→**42**. The repeat keys come from
the R3 module (`A2_REPEAT_KEYS`, a subset of `FOCUS_KEYS`). They are translated through the class
map and checked against `EXPECTED_YOLO_IDS`. Tests cover the real class map and a synthetic export
in which yolo_id 32/41 (other derived keys) must **not** be repeated. They also cover an identity
class map, which must be refused.

### 2.2 Training-budget consequence (verified arithmetic, not a measurement)

With the same epochs and batch, A2 runs `ceil(4687/4)=1,172` iterations per epoch, against the
pilot's 928. That is about 26 % more optimizer steps in total, and the warmup (3 epochs) lasts more
iterations. A2 is therefore **not compute-matched**. An A2 gain or loss mixes the higher exposure of
classes 7/32/41 with the larger step count. The Ultralytics `auto` optimizer rule still resolves to
AdamW with lr0 0.000172, as in the pilot `args.yaml`: `ceil(4687/64)×100 = 7,400`, which is at most
10,000 iterations (Ultralytics 8.4.172 source, `engine/trainer.py`). Mosaic draws partner images
from the same list, so repeated images are also more likely as mosaic partners. This is inherent to
list repetition.

## 3. Success criteria (copied verbatim from R3 §5; not changed here)

R3 §5 table, A2 "Success on R3" cell:

> Recall of classes 7, 32 and 41 each up by ≥ 0.05; FP/image up by ≤ 0.03; overall recall ≥ 0.85;
> paired CIs reported

R3 module `run_specs` (machine text, same rule):

> on R3 at conf 0.20: recall of classes 7, 32 and 41 each up by >= 0.05; FP/image up by no more
> than 0.03; overall recall >= 0.85; paired group-bootstrap CIs reported

The classes are **derived keys**. In YOLO prediction CSVs and per-class tables, look up derived key
7 under yolo_id 7, derived key 32 under yolo_id 33, and derived key 41 under yolo_id 42. Validation
support on the R3 roster is 111 / 29 / 26 boxes (R3 §4). Meeting these criteria does not change
D-05 and does not accept the model.

## 4. Evaluator plan (proposal; nothing here is built)

- **Common path.** A2 is scored on the same common evaluator path as D1-A3-R2:
  `detector/colab/evaluate_d1_a3_r2_common_r1.py` (`5d8e49bf…`, uncommitted in the Desktop
  checkout). It uses the corrected train/val-only bundle `8e6ffe77…` and the 376-frame / 624-box
  R3 roster (Ultralytics IoU matching/AP plus the `m1` D-05 operating points). That evaluator pins
  the A3 archive. A2 needs an append-only successor (proposed name
  `evaluate_d1_a2_r1_common_r1.py`) that changes only the candidate archive, manifest and `best.pt`
  pins, and accepts the A2 result archive only after its run attestation verifies. The pilot side
  stays the same QA-passed common-path anchor.
- **Paired CI.** A successor of `detector/m1/a3_pilot_paired_ci_r1.py` (`7edb3824…`) computes the
  A2 − pilot differences. It uses 1,000 rounds, seed 20261018 and intact D-02 capture-group
  resampling, with identical draws for both models. It reports the differences for recall of
  classes 7/32/41, FP/image and overall recall at conf 0.20, and checks point estimates against the
  result JSON before any CI.
- **Uncertainty caveat.** There are only 9 validation groups. A class whose boxes sit in few groups
  can give a degenerate paired CI (R3 §4 cites class 32 at [0.138, 0.138]). Such an interval shows
  too little group variation. It is not precision.
- **Selection.** The criteria are read at the fixed point conf 0.20. No threshold is selected or
  locked, and the sealed test (`afa03d4b…`) stays closed.

## 5. Source package (new files only; pending independent source QA)

| File | SHA-256 |
| --- | --- |
| `detector/m1/a2_repeat_list_r1.py` | `28fc4cedb438859f2edd6215a97eb00cb36f385344e19731155e1da971712619` |
| `detector/m1/resumable_train_a2_r1.py` | `c3823eefb9777912fc76302a642427a64869c9097274fc4d5841966c07d42ace` |
| `detector/colab/run_d1_colab_a2_r1.py` | `a6bb6e684701b5a95bd03b71bac777693ec08f1ccb853c98edb2cefdcec2d6de` |
| `detector/tests/test_a2_repeat_list_r1.py` | `1213bfd854dc979bbde6401df51a666194ae224e2b22fbf16c91c88f64a1e248` |
| `detector/tests/test_resumable_train_a2_r1.py` | `baee841bb99d4581cecf9601622fd86dd52f7947f6b4ddba65da3e434a4970dd` |
| `detector/tests/test_run_d1_colab_a2_r1.py` | `6a5745e1eed306d8968dbfe584710916fde871f9fb2bfedaabeb458c22eb0997` |

These predecessors are reused unchanged:

| File | SHA-256 |
| --- | --- |
| `detector/m1/yolo54_improvement_r3.py` (pinned inside the list module) | `548144b107714d95427b1704700a2ff8cd879143d8f2366e931afecf6777a639` |
| `detector/m1/resumable_train.py` | `0a963d4bc246613402283531b6280836606ac1f5b35b5d215b3959a1354aa6e7` |
| `detector/m1/checkpoint_store.py` | `e1f8f00c036d6407d327164d907f3641427864cc35cf817336209ae5da76891c` |
| `detector/m1/contract.py` | `901e7e372d9660cd79e6bfcab43684b1693f0a4aafad9f4c331fd8f04ba6bbbf` |
| `detector/colab/run_d1_colab_checkpoint_r6.py` | `71a9f4a9f8efaa81f657dd414ab8a7d3354ae13a7fcd024e04b42ef2ccce8a35` |
| `detector/colab/run_d1_colab_checkpoint_r1.py` | `e3193ad71e4376149d925958cc8c3d415e7ca912f7adfeae86973548db701336` |
| `detector/uv.lock` (Ultralytics 8.4.172) | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |

### 5.1 What the source does (verified current behavior by the tests in §7)

**`m1.a2_repeat_list_r1`** has two commands, `build` and `verify`.

- It reads only:
  - the pinned M1 export, whose manifest must hash to `8a8df5f2…` and whose train binding must be
    the pilot's `6ac76750…` / `d907fb9f…`;
  - the authorities that manifest pins: class map, WP35 lineage, WP36-R1 split frames and the raw
    image inventory.
- It refuses:
  - a raw stem that is not a WP36-R1 `train` frame, and a WP35 image whose source frame is not
    train;
  - any list entry outside `images/train/`, with a `val` component, or with a component containing
    `test`;
  - any symlink in the input chain, except the export's own image links;
  - an image link whose target escapes, or differs from, the exact governed raw/WP35 source;
  - train image bytes that differ from the inventory or lineage hashes;
  - any count, box total, roster hash or list hash that differs from §2.1.
- It recomputes the roster independently with the QA-passed R3 `a2_repeat_roster` and requires
  agreement.
- Output is write-once (`O_CREAT|O_EXCL|O_NOFOLLOW`), contains no timestamps, and is
  byte-deterministic. It goes to the Git-ignored `data/processed/d1_a2_r1/`.
- A runtime copy with absolute paths and the runtime data YAML is written there too, only by the
  trainer. The runtime files are written once or must be byte-identical.

**`m1.resumable_train_a2_r1`** follows the D1-A3-R1 pattern.

- It freezes the §2 values and requires CUDA device 0. Resume forbids a stop boundary.
- It refuses to train, before touching data, unless an Owner authorization record path and SHA-256
  are passed (§6).
- It builds or verifies the A2 list and materialises the runtime list and YAML.
- Through the unchanged `m1.resumable_train` path, it trains with `train_args` equal to the pilot's
  except `data`. Tested against the pilot `run_contract.json` (key set identical, only `data`
  differs) and against the pilot `args.yaml` (every passed key equal except run identity).
- The checkpoint recovery binding adds the experiment, the authorization SHA, the rule id, the list
  SHA, the roster SHA and the entry count. A checkpoint therefore resumes only under the same list
  and the same authorization.
- `run_contract.json` gains `experiment`, `pilot_run`, `single_change`, `a2_data` (list, roster
  and runtime hashes), `owner_authorization` and `sealed_test_accessed=false`.
- At `on_train_start` it checks that the Ultralytics train dataset equals the runtime list as a
  multiset (4,687 entries).
- A run without `--stop-after-epoch` must end `COMPLETED` or `COMPLETED_FROM_FINAL_CHECKPOINT` at
  epoch 100.

**`colab/run_d1_colab_a2_r1.py`** follows the D1-A3-R2 launcher pattern.

- It keeps the captured predecessor parser (no recursion), the R6 two-runtime evidence controls,
  and the pilot-runner R5 result names: `<run>_result.tar.gz` + `.manifest.json`,
  `colab_execution.json`, `execution_attempts.jsonl`, `DB_logger.db` and `colab_train.log`.
- The authorization gate and the `--expected-checkout` check run before any state is written.
- The run binding includes the authorization SHA, the checkout, the state path, the bundle and the
  list/roster hashes.
- **A3 lesson applied.** D1-A3-R2 failed at packaging only because `contract.inspect_run_weights`
  requires exactly the base run-contract keys
  (`docs/review/d1_a3_r2_packaging_repair_r1_record.md`). The A2 launcher hands the inherited
  packager a contract shim whose `inspect_run_weights` validates the A2 schema exactly. It checks:
  - the extra keys;
  - the list and roster hashes;
  - the runtime file hashes;
  - `train_args` = pilot + data;
  - the CUDA checkout;
  - the authorization;
  - the weight bindings;
  - the governed export binding.

  The rest of the packager is unchanged. This shim has unit tests only. It has not run against a
  real Colab result (unknown until the run).

## 6. Owner authorization record (required before any training)

The trainer and the launcher both refuse unless `--owner-authorization` names a repo-relative
`docs/review/*.md` record (not this contract) and `--owner-authorization-sha256` matches its bytes.
The record must:

- contain, on a line by itself, the exact text `OWNER_AUTHORIZES_TRAINING: D1-A2-R1`;
- name `D1-A2-R1`;
- name the list SHA `90d735d6…fdec2` and the roster SHA `0ce6afdc…69aa3` in full.

A record for a different list, such as the 339-frame variant, cannot authorize this run.
Nothing in this contract is an authorization. This document deliberately does not contain the
authorization line as a standalone line.

## 7. Gates (in order; none is passed yet)

1. **Independent source QA** of the §5 package. It must cover the roster/list reproduction, the
   refusal paths, the single-change diff, the authorization gate, the resume binding, the
   predecessor-chain entry without recursion, and the A2 packaging shim.
2. **Commit** of the QA-passed package. This needs the Owner's explicit authorization. The
   launcher's `--expected-checkout` is that commit.
3. **Owner authorization record** (§6), including the D-A2-1 choice (§8). Without it the source
   refuses.
4. **L4 smoke.** `mode=fresh` on NVIDIA L4 with `--stop-after-epoch 1`. Verify `epoch-0001`, its
   manifest and binding (list SHA, authorization SHA), the SQLite and text logs, `colab_train.log`
   showing 4,687 train images, and `sealed_test_accessed=false`.
5. **Smoke QA**, independent, of the live Drive artifacts.
6. **Resume** on a distinct L4 runtime digest, with no stop boundary, to epoch 100. The run and
   checkpoint bindings must be identical to the smoke's.
7. **Result QA** of the archive and run attestation, then the §4 evaluator successor and its own
   source and result QA. Only then is A2 compared with the pilot. The sealed test remains closed.

## 8. Open Owner decision D-A2-1: all 975 images or 339 raw frames only

**Implemented (the frozen R3 spec):** all 975 images, rule id `A2_ALL_975_RAW_AND_WP35`.

**If the Owner chooses 339 raw frames only**, the following changes. These values were computed
read-only from the same export in this session; they are not pinned in source.

| Item | 975 (implemented) | 339 raw only (alternative) |
| --- | --- | --- |
| Repeated images | 975 (339 raw + 636 WP35) | 339 raw |
| List entries | 4,687 | 4,051 |
| Roster SHA-256 | `0ce6afdc…69aa3` | `2485b4bd2f1f47fc677dff582a065681e4d51d4b8dc8f68f02ef4e6330ccc422` |
| List SHA-256 (same line format) | `90d735d6…fdec2` | `c953d458b087f80939422d6d2d8a7243b4505ce7e1f270289b36bb95b88c6b95` |
| Iterations/epoch at batch 4 | 1,172 | 1,013 |
| `auto` optimizer | AdamW (7,400 ≤ 10,000) | AdamW (6,400 ≤ 10,000) |

The 339 variant also changes the source and the process:

- **Source.** Append-only successors are needed: an `a2_repeat_list_r2` with a new rule id and
  expected values, plus a trainer/launcher successor pinning the new hashes. The R1 files must not
  be edited.
- **Contract and QA.** A new run contract and a new source QA are needed.
- **Authorization.** The authorization record must name the 339 hashes.
- **Data.** WP35 images would still be trained once; only raw frames gain extra exposure.

## 9. Cost and time (estimate; not measured for A2)

- **Measured pilot (verified artifact).** The pilot `results.csv` `time` column reads 14,786 s
  (about 4.1 h) cumulative at epoch 100 on L4, including its fresh/resume legs. It was read in this
  session and not separately QA'd.
- **A2 estimate.** Training iterations scale by about 1.26× and per-epoch validation is unchanged.
  The estimate is **about 5 L4-hours (range 4.6–5.3 h)** plus Colab setup, smoke and resume
  overhead. The real figure is **unknown** until the run.
- **R2 comparison (estimate).** R2's own estimate for a 100-epoch YOLO11s ablation was 3.8 L4-h.

## 10. Known risks and limitations

- **Not compute-matched** (§2.2).
- **Train-label cache.** Ultralytics rewrites `data/processed/m1_yolo/labels/train.cache` in the
  training checkout, because the image list differs from the pilot's. It is a derived cache, and
  the export verifier does not read it. The pilot's own artifacts are unaffected.
- **Checkout path on resume.** The runtime YAML and list contain absolute paths. Resume must run
  from the same checkout path, which on Colab is `/content/Traffic_Sign_Detector`. A different
  path makes the write-once runtime check refuse rather than silently retarget.
- **Pilot validation split during training.** Per-epoch validation and `best.pt` selection use the
  export `val` split in `data.yaml`, unchanged from the pilot. The R3 roster is used only by the
  §4 evaluator.
- **Single seed.** As with the pilot and A3, one seed is not a population estimate.
- **Untracked evaluator.** The common evaluator named in §4 is uncommitted in the Desktop checkout.
  Its QA-passed state must be re-pinned before the A2 successor is built.

## 11. Local execution record (2026-11-05)

On the Desktop checkout (HEAD `7a95591e111cd0f8efa440145cf010a4de0763d6`, branch
`yolo11n-dual-track-r1`):

- `uv run python -m m1.a2_repeat_list_r1 build` and then `verify` both returned
  `A2_TRAIN_LIST_VERIFIED`.
- The roster SHA was `0ce6afdc…69aa3`, an **exact match**. The counts were 3,712 / 1,912 / 1,800 /
  975 / 339 / 636 / 4,687. The box totals matched §2.1. The R3 cross-check returned `MATCH`, and
  image bytes were verified.
- Written (Git-ignored):
  - `data/processed/d1_a2_r1/a2_train_list.txt` (`90d735d6…`, 4,687 lines);
  - `a2_train_list_manifest.json` (`12f09435…`).
- No runtime YAML was written locally.
- A read-only probe of Ultralytics 8.4.172 `BaseDataset.get_img_files` on a scratch absolute copy
  of the list returned 4,687 files (3,712 unique, 975 twice). Label paths resolved to the export's
  `labels/train`. No label cache was written.

## 12. Classification of claims

- **Verified artifact:**
  - the authority hashes in §1;
  - the pilot argument values;
  - every count and hash in §2.1;
  - the 339-variant values in §8 (computed, not pinned);
  - the pilot 14,786 s time;
  - the local outputs in §11.
- **Verified current behavior:** the §5.1 behaviors, by the 80 new tests and the local
  build/verify; the Ultralytics list-duplicate behavior in §11 (8.4.172 only).
- **Proposal:**
  - the §4 evaluator and paired-CI successors;
  - the §7 gate sequence;
  - the 339-variant source change;
  - the cost estimate in §9.
- **Unknown:**
  - the A2 outcome;
  - A2 wall time;
  - the behavior of the packaging shim on a real Colab result;
  - whether Colab installs exactly the locked Ultralytics (the lock pins 8.4.172; `uv sync --frozen`
    is the existing launcher step);
  - the D-A2-1 choice.
