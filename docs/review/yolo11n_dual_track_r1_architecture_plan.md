# YOLO11n dual-track R1 — architecture and training preparation

Date: 2026-10-25 (`Asia/Ho_Chi_Minh`)  
Status: `PRECOMMIT_SOURCE_INDEPENDENT_QA_PASS`  
Boundary: `NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_TRAINING_NO_SEALED_TEST`

## Authority and objective

The Owner reports that the lecturer accepted the existing comparison between:

1. a direct 54-class YOLO11s detector;
2. a one-class YOLO11s detector followed by a CompactCNN or VGG16-54 crop classifier.

The requested extension is to add YOLO11n in the same two roles before the next review. This
document is an implementation plan. It does not independently verify the lecturer conversation or
authorize a Colab run. The Owner later authorized the official-weight download and froze both
tracks at 100 epochs in `yolo11n_dual_track_r1_owner_decision_record.md`.

The two new tracks are intentionally separate:

| Track | New candidate | Matched control | Scientific question |
| --- | --- | --- | --- |
| `N54` | YOLO11n, 54 classes | D1-A3-R2 YOLO11s, 54 classes | How much accuracy is traded for lower compute in a direct detector? |
| `N1` | YOLO11n, one class `traffic_sign` | Cascade B0 YOLO11s, one class | Can a smaller proposal detector preserve recall and improve cascade latency? |

The current CompactCNN and VGG16-54 weights are held fixed for the first `N1` comparison. They
must not be retrained in the same experiment, because that would confound the effect of replacing
YOLO11s with YOLO11n.

## Architecture matrix

```text
Direct family
camera/frame -> YOLO11s-54 (control) -> boxes + 54-class labels
camera/frame -> YOLO11n-54 (N54)     -> boxes + 54-class labels

Cascade family
camera/frame -> YOLO11s-1 (control) -> crop -> CompactCNN or VGG16-54
camera/frame -> YOLO11n-1 (N1)      -> crop -> CompactCNN or VGG16-54
```

This produces six reportable pipelines without inventing a new dataset or classifier:

1. YOLO11s-54;
2. YOLO11n-54;
3. YOLO11s-1 + CompactCNN;
4. YOLO11n-1 + CompactCNN;
5. YOLO11s-1 + VGG16-54;
6. YOLO11n-1 + VGG16-54.

The direct and cascade families answer different questions. Detector-only AP/recall may be
compared across the one-class controls, but GT-crop classifier accuracy must never be compared to
full-scene exact-class mAP as if they were the same metric.

## Local model-size evidence

The pinned detector environment can instantiate both architectures from the locally installed
Ultralytics model definitions without downloading weights. Readback on 2026-10-25 reported:

| Architecture definition | Parameters | GFLOPs at 640 | GFLOPs at 1280 |
| --- | ---: | ---: | ---: |
| `yolo11n.yaml` | 2,624,080 | 6.673 | 27.431 |
| `yolo11s.yaml` | 9,458,752 | 21.836 | 88.820 |

YOLO11n therefore has about 27.7% of the parameters and 30.9% of the nominal 1280-pixel FLOPs of
YOLO11s in this environment. That does **not** imply training will be 3.2 times faster: image
decoding, augmentation, validation, checkpoint hashing and Google Drive I/O do not shrink with the
network.

## Proposed matched configurations

The Owner froze these values on 2026-10-25. They become executable only after independent source
QA and the later smoke/notebook/Colab gates pass.

### N54 — direct 54-class detector

Change only the model family relative to D1-A3-R2:

| Field | Proposed value |
| --- | --- |
| model | official `yolo11n.pt`, SHA-256 `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1` |
| classes | 54 |
| seed | `20261018` |
| epochs | 100 exactly |
| image size | 1280 |
| batch / workers | 4 / 4 for the first matched comparison |
| schedule | `cos_lr=True` |
| fraction / patience | 1.0 / 30 |
| deterministic | true |
| horizontal flip | `fliplr=0.0` |
| data | reuse the exact approved D1-A3 train/validation-only bundle |
| state | `M1_D1_Colab/runs/yolo11n_n54_seed_20261018_r1` |

Keeping batch/workers identical is deliberate: the first report should isolate model size. A later
throughput experiment may select a larger batch for YOLO11n, but it must be reported as a separate
run because batch size changes the optimization trajectory.

### N1 — one-class cascade detector

Change only the detector model family relative to Cascade B0:

| Field | Proposed value |
| --- | --- |
| detector model | official `yolo11n.pt`, the same pinned file used by N54 |
| detector classes | one: `traffic_sign` |
| seed | `20261018` |
| detector epochs | 100 exactly |
| image size | 1280 |
| batch / workers | 4 / 4 for the first matched comparison |
| optimizer/schedule | preserve the Cascade B0 detector settings exactly |
| horizontal/vertical flip | `0.0` / `0.0` |
| detector data | exact Cascade B0 one-class train/validation roster and boxes |
| classifiers | reuse the QA-passed CompactCNN and VGG16-54 weights unchanged |
| state | `M1_D1_Colab/runs/yolo11n_n1_seed_20261018_r1` |

The existing Cascade B0 bundle embeds `models/yolo11s.pt`, and its runner opens that exact member.
N1 therefore needs an append-only bundle/runner successor. The old bundle and runner remain
unchanged and reproducible.

## Required implementation packages

### Package N54-R1

1. Owner decision record for the exact N54 configuration and official-weight download.
2. `resumable_train_n54_r1.py`, built as a successor rather than editing A3.
3. `run_yolo11n_n54_r1.py` with a unique package, required checkout pin, state suffix and run
   binding.
4. Fresh and resume notebook builders with immutable Git and proof hashes.
5. Tests for model hash/name, 54-class YAML, frozen arguments, state isolation, resume semantics,
   retry history, logs, archive/manifest and `sealed_test_accessed=false`.

### Package N1-R1

1. Owner decision record for the exact N1 configuration.
2. A new train/validation-only Cascade bundle containing the pinned `yolo11n.pt`; no test payload.
3. A detector-only successor runner that retains the existing classifier artifacts unchanged.
4. Fresh/resume notebook builders and distinct Drive state.
5. Tests for one-class remapping, box preservation, model binding, stage isolation, recovery,
   result packaging and seal state.

No source package may modify a hash-pinned YOLO11s predecessor. No shared state path may be used.

## Execution gates for each track

```text
Owner config/download decision
  -> exact yolo11n.pt hash and local load check
  -> append-only source + contract
  -> independent source QA PASS
  -> immutable commit and notebook proof (only with explicit commit/push authority)
  -> verify private train/val bundle; test absent
  -> fresh L4 smoke to epoch 1
  -> new-runtime resume to epoch 2
  -> independent smoke artifact QA PASS
  -> long train
  -> archive/hash/SQLite/text-log/runtime/seal verification
  -> validation-only common-method evaluation
  -> independent result QA
  -> latency measurement on the same deployment device/protocol
```

`N54` and `N1` have independent gates. A PASS for one does not authorize the other. The sealed test
remains closed throughout this comparison phase.

## Comparison contract

Use the same corrected 376-frame / 624-box validation roster and common scorer already used for
YOLO54, Cascade B0 and VGG16-54. Report at minimum:

- detector-only mAP50, mAP50-95, AP-small, class-agnostic recall and FP/image;
- direct/cascade exact-class mAP50 and mAP50-95;
- per-class AP/recall with support and unsupported classes called out;
- classifier top-1, macro-F1, balanced accuracy and ECE for the fixed classifiers;
- selected validation threshold plus the fixed confidence-0.20 point;
- batch-1 p50/p95 latency with hardware, image size, warm-up and repeats;
- parameters, FLOPs, artifact size and observed training time;
- failure examples and `sealed_test_accessed=false`.

The first decision is a Pareto comparison, not a claim that nano is automatically better:

1. retain YOLO11n if it gives a material latency/size benefit with an acceptable measured quality
   loss;
2. retain YOLO11s if the nano accuracy loss is too large;
3. consider selective routing/ensemble work only after both nano results have independent QA.

## Realistic 2–3 day schedule

| Window | Work | Exit evidence |
| --- | --- | --- |
| Day 1 | freeze both configs, obtain/pin weight, implement successors, focused checks and source QA | two source-QA verdicts and immutable inputs |
| Day 1–2 | N54 fresh/resume smoke, artifact QA, 100-epoch run and validation evaluation | N54 archive, common-score result and QA record |
| Day 2–3 | N1 fresh/resume smoke, artifact QA, 100-epoch detector run, reuse both classifiers, evaluate four cascade combinations | N1 archive, comparison table and QA record |
| End of Day 3 | measured latency and review package | lecturer-ready architecture/metric table |

The last observed YOLO11s A3 resume covered epochs 2–40 in about 85 minutes before the separate
packaging repair. The observed Cascade B0 detector's final long attempt covered the remaining
epochs in about 6.8 hours. Based on model compute alone, proposed planning ranges on an available
L4 are roughly 1–2 hours for N54 training and 3–5 hours for N1 training, plus smoke, evaluation,
QA and any runtime reconnect. These are estimates, not measured YOLO11n times.

Two to three calendar days is therefore realistic if the official weight, QA reviewer, immutable
commit/notebook and L4 runtime are available without a blocking failure. It is not safe to promise
completion in that window if a source/smoke QA finding requires an append-only repair or Colab
quota/runtime availability changes.

## Open gates after source implementation

1. Separate Owner authorization for the scoped immutable commit, push and any private Drive upload
   required by Colab.
2. Commit-pinned notebook/source proof and bundle readback.
3. Independent fresh/resume smoke QA before either 100-epoch long run.

