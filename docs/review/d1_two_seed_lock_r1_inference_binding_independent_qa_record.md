# D1 two-seed R3 lock — independent inference binding QA

Reviewed: 2026-11-06 (Asia/Ho_Chi_Minh), by a Codex agent separate from the A3 record author. Scope: only existing validation R3 prediction CSVs, copied pilot archive and existing S2 archive; no inference or training.

Verdict: PASS — bounded input reuse binding for the two-seed R3 writer; no final threshold approval.

## Bound record and candidate weights

| Artifact | SHA-256 |
| --- | --- |
| `docs/review/d1_two_seed_lock_r1_inference_binding_authorization_2026-11-06.md` (final A3 bytes) | `40e9f8806feab30a803fec633b7907e03a4d8b0ee785c5edc860ebd902f2615a` |
| `seed 20261018 best.pt` | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` |
| `seed 20261019 best.pt` | `046cfea22e6daf45342063b58cd9082aa4b0b0528a3a6d9af7ac23bbac015bce` |

## Recomputed prediction CSVs

Each listed SHA-256 is independently computed from local bytes and equals the same configuration key in the QA-passed generated JSON. Every CSV has the exact seven-column prediction schema; all have at least one candidate and minimum confidence >=0.001.

| Seed | Configuration | SHA-256 | Minimum confidence | Rows |
| --- | --- | --- | ---: | ---: |
| 20261018 | `agnostic_0.80` | `5372a9e13dc264bb1c498a7e9296e736ff51f64857b65f5d5ad2debd2a9f0d4f` | 0.0010072 | 1534 |
| 20261018 | `agnostic_0.85` | `9c3a67b7b23776d972232cfb20b90bec6bec97990f874c00638db6ee2cde9365` | 0.0010072 | 1724 |
| 20261018 | `agnostic_0.90` | `afc7a3c93f24ecd63f9a4daea963c1994df91adbe3a2f358ee7802672bed5d94` | 0.0010024 | 2137 |
| 20261018 | `classaware_0.45` | `eb95a5021e685c7ba60b173a184fd29535f114bcb8269916ba594e6c404261a5` | 0.0010046 | 1832 |
| 20261018 | `classaware_0.50` | `98613bd93dbbad9d832f1894681a846fe732bedd7d71aa5b66025f497ef5f492` | 0.0010046 | 1861 |
| 20261018 | `classaware_0.55` | `80c3f634317c1e0430feb9542dbe73bebe08ea6858d4eb9f8035b731dea50a4e` | 0.0010046 | 1891 |
| 20261018 | `classaware_0.60` | `24a7192dad073e0db1668dffddd7f038a0329352ff6efc4cd7f314e2e0cb8678` | 0.0010046 | 1917 |
| 20261018 | `classaware_0.65` | `81f7358e2f9d54f70c2481f11145791abe731478c0f4147e042e7ecd9c7c6c6a` | 0.0010046 | 1958 |
| 20261018 | `classaware_0.70` | `d4ae12e3116ad9ee80fb39f00174cdb44daf29ded7ada14ea2086b926e477a11` | 0.0010046 | 1999 |
| 20261018 | `classaware_0.75` | `16407e74507fde184e696baf37768e3b411464279297e8eb8685dd5c0e005b2d` | 0.0010046 | 2073 |
| 20261018 | `classaware_0.80` | `36f088edb2abd00977e5a49779c6204a7d3fb2952756aa47f05f931bed56ca75` | 0.0010046 | 2188 |
| 20261019 | `agnostic_0.80` | `0b746302c749dd7fefb7d6d6a7e9a46bbed1f3ddd4d586ee8eeb53b2dc9ba295` | 0.0010021 | 1820 |
| 20261019 | `agnostic_0.85` | `987d2634992685bf53ecf4208727f4d4d472448162e48a7322505dcd719b51b2` | 0.0010009 | 2093 |
| 20261019 | `agnostic_0.90` | `027a166d9ea47f34e0498591d6cc8955e967ca1806a7d3c3a982d6aa6e32b0ef` | 0.0010004 | 2718 |
| 20261019 | `classaware_0.45` | `811e2935845d4195507653d743c05f43419bd73ca234761cb1ef4b700114705d` | 0.0010026 | 2446 |
| 20261019 | `classaware_0.50` | `c843f73a710674fda66763d1dffe08a85d45b43dc703d650ff924fec10721b8f` | 0.0010026 | 2459 |
| 20261019 | `classaware_0.55` | `e9e3041c6708fb38dc495d4a30f299fe375413a89e078582d900cb735c6b0f7f` | 0.0010026 | 2472 |
| 20261019 | `classaware_0.60` | `d4cc6b1f10a9ac6d97091f5418808a2097744edea2307b5e38b373d441e3db76` | 0.0010026 | 2500 |
| 20261019 | `classaware_0.65` | `041950b291e6db6b635c6acf6228af337c5e41790ce1015f664e3ae9af25bc5e` | 0.0010021 | 2548 |
| 20261019 | `classaware_0.70` | `eb0ca49efde4a4c921c38e2eb00d7136a29c50d50e46cd49557356ca9c9a33b8` | 0.0010021 | 2611 |
| 20261019 | `classaware_0.75` | `7ab3e9a9ef995cfd913a612cc5368af8bad7a40ad66d4e55f38c332218e15048` | 0.0010021 | 2714 |
| 20261019 | `classaware_0.80` | `35fc180ea8bd4b6ee8e1afa2521ec4ca58a30cb02063c26869c3a48bc7043213` | 0.0010021 | 2826 |

## Independent checks

- The A3 record hash and its 22 path/hash rows were read back. The ten provenance/source/QA entries and two candidate-weight entries in its table all matched current file bytes. Original pilot and S2 result QA records each have a PASS verdict; original inference-result QA records for both CSV sets also have a PASS verdict.
- The pilot NMS contract `docs/review/d1_nms_sweep_r1_contract.md:16` explicitly specifies `conf=0.001`, `imgsz=1280`, batch 1, and default `max_det=300`.
- For seed 20261019, the QA-pinned `detector/m1/two_seed_provisional_threshold_r1.py:414,420` calls `sweep.infer` for the baseline and other ten configurations. The QA-pinned `detector/m1/nms_sweep_r1.py:130-138` passes `conf=0.001` and `imgsz=1280` to `detector.predict`; `max_det=300` is the stated default, not an explicit call argument. This source call chain supplies the numeric floor required by Appendix A. The S2 narrative report does not separately state the numeric floor; CSV minima corroborate the floor but alone cannot prove the exact inference argument.
- `run_d1_colab.verify_result_archive` passed on the copied pilot archive/manifest and existing S2 archive/manifest. Each manifest binds eight members, terminal `SUCCEEDED`, and `sealed_test_accessed=false`. Pilot archive/manifest SHA-256: `6ae2e6a29e1712ff5372764d5cc1eb6bb7ae9c9d06d7a08de8aab3e3c2f6778f` / `0ecac47986d946ed83dfbac1e203f60b4e6055e5054ed9c52476db128b7f7796`; S2: `c9367603c67650968514d00699d73bc0202fb7e1b69c4a6af413b34f60b2164e` / `b771a58996f75257f2a58adcb684273dff637be28b5d66606a66a721694e172e`. Manifest attestation SHA-256 values match the R3 successor pins: pilot `7fa5df339676adaae220e1963916b2e48e2525455713d500db5d76343e2fc9fc`; S2 `807ba02a87da944e804fc61b314618bb77692c727fb577eec5f7a6395442c80c`.
- Full best-weight hashes above match `RUN_PINS` in `detector/m1/d1_threshold_lock_r3_successor.py:45-57`. Pilot and S2 extracted run contracts also match the pinned SHA-256 values `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88` and `1f1c3f7f2fdeb15467aa69ddbe012b880b10324b5b505d772058ebd7e96c2050`.

## Limit

This PASS establishes byte identity, input provenance, archive integrity and the source-level inference floor for reuse of existing validation R3 predictions. It does not validate the lock writer output, select or approve a deployable threshold, establish external generalization, or authorize sealed-test access. No new predictions were made; `sealed_test_accessed=false`.
