# D1 two-seed R3 lock — inference binding authorization

Date: 2026-11-06 (Asia/Ho_Chi_Minh). Status: `REUSE_ONLY_VALIDATION_R3`.

## Owner scope

The coordination handoff quotes the Owner (2026-11-06):

> "Bắt đầu bàn giao công việc"

Its Appendix A quotes the Owner:

> "Bổ sung bàn giao"

The Owner also authorized this task in the current chat:

> "Tôi cho phép sao chép archive pilot và file manifest từ thư mục Google Drive đồng bộ vào tmp/d1_two_seed_lock_r1_inputs/pilot/, chỉ sao chép, không sửa trên Drive. Không mở sealed test, không suy luận mới, không train, không push."

This record authorizes reuse of exactly the 22 existing validation R3 CSVs below for one R3 two-seed lock-writer run. It does not authorize new inference, training, opening the sealed test, changing the app threshold or D-05, or pushing. The resulting lock is pending independent QA and a separate Owner approval before use. `sealed_test_accessed=false`.

## Original run provenance and inference floor

Pilot: `docs/review/d1_nms_sweep_r1_contract.md:16` specifies `conf=0.001`, `imgsz=1280`, batch 1 and Ultralytics default `max_det=300`.

Seed 20261019: the QA-pinned `detector/m1/two_seed_provisional_threshold_r1.py:414,420` invokes `sweep.infer(detector, *config, device)` for the baseline and remaining ten configurations; `detector/m1/nms_sweep_r1.py:130-138` defines that same `sweep.infer` call to `detector.predict` with `conf=0.001`, `imgsz=1280`, batch 1 and default `max_det=300`. This is source-call evidence for the seed-19 inference floor; the S2 narrative report alone does not state the numeric floor.

Reuse binding: `inference_conf=0.001`; `imgsz=1280`; `max_det=300` (Ultralytics default, not an explicit argument). All CSV minima independently exceed 0.001.

| Seed | Original source, authorization or QA artifact | SHA-256 |
| --- | --- | --- |
| 20261018 | `docs/review/d1_nms_sweep_r1_owner_authorization_2026-11-06.md` | `83cd0b57e6320bee3858447239666a688aea78b6e24d6cf7d985d0255a71a487` |
| 20261018 | `docs/review/d1_nms_sweep_r1_contract.md` | `754979728d665918a341ff7b26308f7465b049a5e0462f75c16151e52b000d9a` |
| 20261018 | `docs/review/d1_nms_sweep_r1_result_independent_qa_record.md` | `75808758357b099adb5b43968dcaba594196875535689fa76256406625ace320` |
| 20261018 | `docs/review/generated/d1_nms_sweep_r1.json` | `6be704d21edacd92aeb142f9fc4a5ffb6988686f24ebda9321224634f5460057` |
| 20261019 | `docs/review/d1_two_seed_provisional_threshold_r1_owner_authorization_2026-11-06.md` | `f71a7eea772e191b8db6bf6074b450aa71fa3c8bbeb443b69983eb610e627be4` |
| 20261019 | `docs/review/d1_two_seed_provisional_threshold_r1_report.md` | `705ee356cf231f77873c62bf86631d3c5510776cdc2672777ce4caf719c7e636` |
| 20261019 | `docs/review/d1_two_seed_provisional_threshold_r1_result_independent_qa_record.md` | `fd8389e063097a7748ddfec72b1b20abfe15841ba67cef1dfa468b1a083a52aa` |
| 20261019 | `docs/review/generated/d1_two_seed_provisional_threshold_r1.json` | `d6ce45568709be8bb3f3ea6d9535870f5027fd40f645addeac3a4a990b627e33` |
| 20261019 | `detector/m1/two_seed_provisional_threshold_r1.py` | `a8f93f0da02ba1decafcbcbb3b21bd12daae1b47f1845cf1cf5d3f951e6fadf3` |
| 20261019 | `detector/m1/nms_sweep_r1.py` | `0a114a495337bef898bddcbfa3711556f2d740f028d7150ca91a9029a7e4311e` |

## Candidate weight binding

| Seed | Weight | SHA-256 |
| --- | --- | --- |
| 20261018 | `results/experiments/D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2/weights/best.pt` | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` |
| 20261019 | `tmp/d1_two_seed_lock_r1_inputs/s2/best.pt` | `046cfea22e6daf45342063b58cd9082aa4b0b0528a3a6d9af7ac23bbac015bce` |

## Frozen predictions

All paths below are local CSV files from previous QA-passed inference. The digest column was verified against the corresponding generated JSON above. `min_confidence` is the minimum parsed candidate score, not a newly chosen operating threshold.

| Seed | NMS configuration | Prediction CSV | SHA-256 | min_confidence |
| --- | --- | --- | --- | ---: |
| 20261018 | `agnostic_0.80` | `results/experiments/d1_nms_sweep_r1/predictions_agnostic_0.80.csv` | `5372a9e13dc264bb1c498a7e9296e736ff51f64857b65f5d5ad2debd2a9f0d4f` | 0.0010072 |
| 20261018 | `agnostic_0.85` | `results/experiments/d1_nms_sweep_r1/predictions_agnostic_0.85.csv` | `9c3a67b7b23776d972232cfb20b90bec6bec97990f874c00638db6ee2cde9365` | 0.0010072 |
| 20261018 | `agnostic_0.90` | `results/experiments/d1_nms_sweep_r1/predictions_agnostic_0.90.csv` | `afc7a3c93f24ecd63f9a4daea963c1994df91adbe3a2f358ee7802672bed5d94` | 0.0010024 |
| 20261018 | `classaware_0.45` | `results/experiments/d1_nms_sweep_r1/predictions_classaware_0.45.csv` | `eb95a5021e685c7ba60b173a184fd29535f114bcb8269916ba594e6c404261a5` | 0.0010046 |
| 20261018 | `classaware_0.50` | `results/experiments/d1_nms_sweep_r1/predictions_classaware_0.50.csv` | `98613bd93dbbad9d832f1894681a846fe732bedd7d71aa5b66025f497ef5f492` | 0.0010046 |
| 20261018 | `classaware_0.55` | `results/experiments/d1_nms_sweep_r1/predictions_classaware_0.55.csv` | `80c3f634317c1e0430feb9542dbe73bebe08ea6858d4eb9f8035b731dea50a4e` | 0.0010046 |
| 20261018 | `classaware_0.60` | `results/experiments/d1_nms_sweep_r1/predictions_classaware_0.60.csv` | `24a7192dad073e0db1668dffddd7f038a0329352ff6efc4cd7f314e2e0cb8678` | 0.0010046 |
| 20261018 | `classaware_0.65` | `results/experiments/d1_nms_sweep_r1/predictions_classaware_0.65.csv` | `81f7358e2f9d54f70c2481f11145791abe731478c0f4147e042e7ecd9c7c6c6a` | 0.0010046 |
| 20261018 | `classaware_0.70` | `results/experiments/d1_nms_sweep_r1/predictions_classaware_0.70.csv` | `d4ae12e3116ad9ee80fb39f00174cdb44daf29ded7ada14ea2086b926e477a11` | 0.0010046 |
| 20261018 | `classaware_0.75` | `results/experiments/d1_nms_sweep_r1/predictions_classaware_0.75.csv` | `16407e74507fde184e696baf37768e3b411464279297e8eb8685dd5c0e005b2d` | 0.0010046 |
| 20261018 | `classaware_0.80` | `results/experiments/d1_nms_sweep_r1/predictions_classaware_0.80.csv` | `36f088edb2abd00977e5a49779c6204a7d3fb2952756aa47f05f931bed56ca75` | 0.0010046 |
| 20261019 | `agnostic_0.80` | `results/experiments/d1_two_seed_provisional_threshold_r1/predictions_agnostic_0.80.csv` | `0b746302c749dd7fefb7d6d6a7e9a46bbed1f3ddd4d586ee8eeb53b2dc9ba295` | 0.0010021 |
| 20261019 | `agnostic_0.85` | `results/experiments/d1_two_seed_provisional_threshold_r1/predictions_agnostic_0.85.csv` | `987d2634992685bf53ecf4208727f4d4d472448162e48a7322505dcd719b51b2` | 0.0010009 |
| 20261019 | `agnostic_0.90` | `results/experiments/d1_two_seed_provisional_threshold_r1/predictions_agnostic_0.90.csv` | `027a166d9ea47f34e0498591d6cc8955e967ca1806a7d3c3a982d6aa6e32b0ef` | 0.0010004 |
| 20261019 | `classaware_0.45` | `results/experiments/d1_two_seed_provisional_threshold_r1/predictions_classaware_0.45.csv` | `811e2935845d4195507653d743c05f43419bd73ca234761cb1ef4b700114705d` | 0.0010026 |
| 20261019 | `classaware_0.50` | `results/experiments/d1_two_seed_provisional_threshold_r1/predictions_classaware_0.50.csv` | `c843f73a710674fda66763d1dffe08a85d45b43dc703d650ff924fec10721b8f` | 0.0010026 |
| 20261019 | `classaware_0.55` | `results/experiments/d1_two_seed_provisional_threshold_r1/predictions_classaware_0.55.csv` | `e9e3041c6708fb38dc495d4a30f299fe375413a89e078582d900cb735c6b0f7f` | 0.0010026 |
| 20261019 | `classaware_0.60` | `results/experiments/d1_two_seed_provisional_threshold_r1/predictions_classaware_0.60.csv` | `d4cc6b1f10a9ac6d97091f5418808a2097744edea2307b5e38b373d441e3db76` | 0.0010026 |
| 20261019 | `classaware_0.65` | `results/experiments/d1_two_seed_provisional_threshold_r1/predictions_classaware_0.65.csv` | `041950b291e6db6b635c6acf6228af337c5e41790ce1015f664e3ae9af25bc5e` | 0.0010021 |
| 20261019 | `classaware_0.70` | `results/experiments/d1_two_seed_provisional_threshold_r1/predictions_classaware_0.70.csv` | `eb0ca49efde4a4c921c38e2eb00d7136a29c50d50e46cd49557356ca9c9a33b8` | 0.0010021 |
| 20261019 | `classaware_0.75` | `results/experiments/d1_two_seed_provisional_threshold_r1/predictions_classaware_0.75.csv` | `7ab3e9a9ef995cfd913a612cc5368af8bad7a40ad66d4e55f38c332218e15048` | 0.0010021 |
| 20261019 | `classaware_0.80` | `results/experiments/d1_two_seed_provisional_threshold_r1/predictions_classaware_0.80.csv` | `35fc180ea8bd4b6ee8e1afa2521ec4ca58a30cb02063c26869c3a48bc7043213` | 0.0010021 |

## Boundary

This is an append-only evidence binding. No prediction is generated by this record, and no threshold is effective until the R3 writer output is independently QA-passed and separately approved by the Owner. `sealed_test_accessed=false`.
