# M1-WP38-R1 downstream integration implementation record

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Status: `PM_COMPLETE_AWAITING_INDEPENDENT_QA`  
Owner request: update the whole project after the live audit found that Drive and Dataset Graph
still represented the pre-WP38-R1 dataset.

## Scope implemented

This is an append-only downstream successor. It does not edit the pinned M1 exporter, the pinned
Dataset Graph core, WP36-R1, WP38/WP38-R1 evidence, raw DATASET01, the completed pilot or the sealed
test.

1. `scripts/build_m1_yolo_dataset_wp38_r1.py`
   - pins the QA-passed WP38-R1 manifest, lineage, builder and independent QA record;
   - preserves all WP36-R1 stem-list hashes;
   - substitutes exactly validation stems `1319..1357` with the 960x540 PNG derivatives and
     rotated labels;
   - keeps 1,912 train stems unchanged and keeps the 903-stem test seal unchanged;
   - exposes no `export-test` or `--final-eval` command;
   - materialises only train/val and records `sealed_test_accessed=false` and
     `training_authorized=false`.
2. `scripts/build_m1_colab_bundle_wp38_r1.py`
   - defines a train/val-only roster of 5,927 regular files;
   - uses 1,912 raw train images, 337 raw val images, 39 WP38-R1 PNGs, 39 WP38-R1 labels and 1,800
     WP35 image/label pairs;
   - contains no test image/label and pins the sealed-test stem hash as metadata only;
   - requires a clean committed checkout before producing an upload archive.
3. Dataset Graph successor view
   - `dataset01_view.py` wraps the pinned `dataset_graph.py` without modifying it;
   - node colours now reflect WP36-R1: 1,912 train, 376 val, 903 sealed test and 25 quarantined;
   - 39 WP38-R1 derivatives in `D02-C0034` receive an explicit orientation-corrected marker;
   - 0/54 D-02 groups are split across active train/val/test membership;
   - the historical pipeline animation continues to use vendor split for its before/after story.
4. Project status, roadmap and durable memory now report the completed pilot, the unchanged-config
   `NO-GO`, WP38-R1 and the successor's QA boundary.

## Preserved boundaries

- Raw DATASET01 bytes: unchanged.
- WP36-R1 stem membership: unchanged.
- Train images: unchanged.
- Sealed test: not exported, not opened and not evaluated.
- Completed pilot artifacts: unchanged.
- Training authorization: not granted by this package.
- Drive: no upload or remote write performed.
- Git: no commit or push performed.

## Required next gates

1. Independent QA of source, tests, generated integration manifest and a clean-checkout archive.
2. Commit only after Owner confirmation; build the official archive from that clean commit.
3. Verify archive/sidecar/parts locally, upload only after Owner confirmation, then read back and
   reconstruct from Drive with exact hashes.
4. Evaluate the existing pilot `best.pt` on corrected validation; select confidence/NMS on val.
5. Decide a new 100-epoch contract only from corrected-val evidence. The current configuration
   remains `NO-GO` for seeds `20261019` and `20261020`.

## Current verification summary

The targeted tests and full repository gates are recorded in the handoff message after execution.
This record remains `AWAITING_INDEPENDENT_QA`; PM-authored green tests are not independent QA.
