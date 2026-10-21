# D1 Pilot run registry — independent QA record

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
QA mode: independent, read-only, fail-closed  
Verdict: **PASS**

## Scope and authorization boundary

This review covers only:

- `docs/review/generated/d1_run_registry.json`;
- the complete extracted run
  `results/experiments/D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2`;
- the already authenticated result-archive manifest used to compare extracted run files;
- the read-only `m1` run inspection and `register-runs` CLI generation contracts.

QA did not change the registry or run artifacts, evaluate a model, train or resume a model, access
the sealed test, commit, or push. The only project file created by QA is this append-only record.

## Registry identity and schema

The reviewed registry SHA-256 is:

`ba5ab04fd6e28e849a6b1aaf345bb5e284eb2a7aa1ee9c7cee0714209ed2b0c9`

Strict JSON parsing found the exact required top-level schema:

- `schema_version=1`;
- status `RUNS_REGISTERED`;
- approved pretrained SHA-256
  `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`;
- export-manifest SHA-256
  `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71`;
- detector lock SHA-256
  `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5`;
- an `entries` list containing exactly one entry.

The one entry is the reviewed seed-20261018 Pilot run. No duplicate or additional run is present.

## Complete extracted-run comparison

The extracted run contains exactly five regular, non-symlink files and no extra file. Each file
matches the corresponding result-archive manifest entry in path, size and SHA-256:

| Extracted file | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `args.yaml` | 2,187 | `a457c6d51547477348c19a06ec4cf3c8794508169b2e0e1a43edc6260b7d16f0` |
| `results.csv` | 12,695 | `b515c4407ecfec7e1448efac438ca7e9bc8abbed7ce992e10eee02efcc81394e` |
| `run_contract.json` | 2,901 | `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88` |
| `weights/best.pt` | 76,225,315 | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` |
| `weights/last.pt` | 76,235,555 | `75ada6ba44804252c65e6ec76660511e0cc6ea69ee164c766055033dac11ea25` |

The archive manifest status remains `D1_COLAB_RESULT_PACKAGE`, its terminal outcome is `SUCCEEDED`,
and `sealed_test_accessed=false`.

## Run-contract validation

The production `m1.contract.inspect_run_weights` path accepted `weights/best.pt` and independently
validated the whole extracted run. QA additionally read back the following exact contract facts:

- experiment `D1`, run name equal to the extracted directory, status `TRAINED`;
- approved seed `20261018`;
- model `yolo11s.pt`, origin `ultralytics/assets v8.4.0`, approved pretrained SHA-256
  `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`;
- training configuration: 100 epochs, image size 1280, batch 4, deterministic mode, pretrained
  weights, `fliplr=0.0`, seed 20261018 and train/val data YAML;
- data bindings equal the governed live contract for export manifest, class map and train/val/test
  stem hashes;
- D-05 gate object exactly equals the governed detector gate object;
- environment passes the production strict validator with a clean training checkout, detector-lock
  binding, CUDA backend, NVIDIA L4, CUDA 13.0, driver 580.82.07, PyTorch 2.14.1+cu130 and
  Ultralytics 8.4.172;
- both and only `best.pt` and `last.pt` are bound by the run contract and match their live extracted
  bytes.

The test stem hash in the data contract is an immutable split-seal binding, not evidence of test
data access. The extracted directory contains no test artifact or test metric. `results.csv`
contains only epoch, train-loss, validation-loss and validation detector metric columns.

## Canonical run attestation

The production inspector generated this attestation from the extracted run:

- run-contract SHA-256
  `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88`;
- best-weight SHA-256
  `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633`;
- last-weight SHA-256
  `75ada6ba44804252c65e6ec76660511e0cc6ea69ee164c766055033dac11ea25`;
- approved pretrained, export-manifest and detector-lock hashes listed above;
- seed 20261018 and the exact Pilot run name.

Canonical JSON hashing of that attestation produced:

`7fa5df339676adaae220e1963916b2e48e2525455713d500db5d76343e2fc9fc`

This is exactly the single registry entry's canonical hash and exactly the
`run_attestation_sha256` stored by the authenticated result-archive manifest.

## CLI generation reproduction

QA redirected only `RUN_REGISTRY` to a temporary directory and invoked the production
`m1.cli.cmd_register_runs` handler with the reviewed `best.pt`. The handler re-inspected the full
run and wrote a temporary registry. That generated file was byte-for-byte identical to the reviewed
registry and had the same SHA-256
`ba5ab04fd6e28e849a6b1aaf345bb5e284eb2a7aa1ee9c7cee0714209ed2b0c9`.

The CLI returned:

- `entries=1`;
- `ready_for_evaluation=false`;
- next action: independently review and commit the registry unchanged before evaluation.

The temporary reproduction did not modify the reviewed registry.

## Fail-closed release state

The reviewed registry and extracted run are currently untracked. A read-only call to
`bind_run_weights` rejected the otherwise valid checkpoint with:

`run registry must be committed and clean`

This is expected and confirms that this QA PASS alone cannot enable evaluation. The exact reviewed
registry must later become Git-tracked, committed and clean through a separately authorized release
step before the production binding accepts it. Any byte change after this QA invalidates this
record's hash and requires review again.

## Validation summary

- registry declared SHA-256 and strict schema: PASS;
- exactly one registry entry: PASS;
- exact five-file extracted run versus archive manifest: PASS;
- production run-contract inspector: PASS;
- status, seed, model, training invariants, governed data, D-05 gates and environment: PASS;
- exact best/last weight bindings: PASS;
- canonical attestation versus registry and archive manifest: PASS;
- byte-exact CLI reproduction in a temporary output path: PASS;
- uncommitted-registry fail-closed guard: PASS;
- Graft wiring graph: `OK` and in sync with source;
- sealed test: not accessed; the archive manifest remains `sealed_test_accessed=false`.

## Verdict and authorization boundary

**PASS.** The reviewed one-entry registry is a byte-exact product of the production CLI and binds
the complete extracted seed-20261018 run to its authenticated archive, contract, model, governed
data, D-05 gates, environment and canonical attestation.

This PASS approves only the registry content at SHA-256
`ba5ab04fd6e28e849a6b1aaf345bb5e284eb2a7aa1ee9c7cee0714209ed2b0c9`. It does not authorize
commit or push, model evaluation, threshold selection, latency measurement, another training seed,
sealed-test access, artifact mutation, deployment or publication. Evaluation remains technically
blocked until a separately authorized commit records the unchanged registry and extracted run.
