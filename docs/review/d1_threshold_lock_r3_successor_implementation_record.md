# D1 R3 two-seed threshold lock successor — source implementation

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Status: `SOURCE_ONLY_NO_LOCK_WRITTEN`.
`sealed_test_accessed=false`; `thresholds_locked=false`.

## Authority and scope

- Frozen base contract `docs/review/d1_threshold_lock_r1_contract.md` SHA-256
  `726932dbcd32842658477c9d36f4dc7c240d412d92119e76e5b3536a4d278f0f`.
- Two-seed addendum `docs/review/d1_threshold_lock_r1_contract_addendum_1_two_seeds.md`
  SHA-256 `cefbdc627266588735e0369c42b1fe426e85e78c38b3eaddef2f61ac9484a82b`.
- Owner amendment `docs/review/d05_q1_two_seed_owner_amendment_2026-11-06.md`
  SHA-256 `4d451a3a4174d1b2ff34c5acc9d6683e10062e1672f01104ce76edd12585e807`.
- The addendum's independent delta QA is PASS with the hash typo correction made before commit.
- This implementation used synthetic inputs and existing, QA-pinned pilot NMS CSVs only. It did not
  read, create or score seed-20261019 predictions, run inference, train, or open the sealed test.

## Design

`detector/m1/d1_threshold_lock_r3_successor.py` defines a versioned seed report builder,
`write`, `verify` and `read_for_final`. It does not call the old three-seed lock CLI. A future
`build-report` invocation needs exactly 11 hash-pinned CSVs for one seed, a hash-pinned identity
JSON, and validation-only bundle `tmp/yolo11n_n1_extract_r2`. It recomputes each cell from the
CSV using the common scorer; stores per-frame GT/TP/FP/correct-class counts, cell totals and
full-candidate mAP. It checks both seeds' identical R3 roster/GT/group/class/scorer binding.

Source SHA-256 at this gate:

| New file | SHA-256 |
| --- | --- |
| `detector/m1/d1_threshold_lock_r3_successor.py` | `6e15865a7fe4bcbad27cbd5c66ff74eeb0f8d8df9b8070e6777f6ca2a845c454` |
| `detector/tests/test_d1_threshold_lock_r3_successor.py` | `b5ab720cd0addb12384ac989c4d09300a07e3fe34e36e747e1f0ce284269f14c` |

The candidate family is pinned to the independently QA'd pilot and S2 best-weight, run-contract,
attestation and run-QA SHA-256 values. The general eight-member archive verifier checks the
archive and manifest, including terminal success and seal. The archived contract is checked for
seed, run, status and best-weight identity. For the older pilot registry QA, the pinned weight,
contract and attestation are required in the record. For S2, the archive, manifest and weight
digests are required. Future NMS inference authorization must name the weight and `conf=0.001`;
independent inference-result QA must PASS and contain the authorization, weight and all 11 CSV
hashes. This is stricter than merely declaring a low inference floor in a report.

The frozen grid and tie order are taken from the base contract. The two-seed mean and difference
replace the original three-seed mean/standard deviation. The paired 1,000-draw D-02 group
bootstrap reuses every draw across two seeds and both NMS settings. Nine leave-one-group-out
folds are always computed. An NMS change is made only when all three frozen conditions pass;
otherwise the eligible class-aware 0.70 cell is used. No eligible baseline means no lock.

The writer uses **schema version 2** plus an R3 proof sidecar. The lock stores the sidecar path and
SHA-256. The sidecar stores the two report hashes, R3 binding, selection, confidence intervals
and nine folds. `verify` rebuilds both reports from their pinned CSVs and recomputes the
selection. It requires each candidate's report path/hash to be among the sidecar reports, checks
identical settings in both candidates and rejects byte drift in the canonical JSON. The
`read_for_final` API verifies the record again, then requires record, sidecar, independent lock
result QA and Owner approval to match the checkout's HEAD bytes. Both QA and approval documents
must include the full record and sidecar SHA-256 values. The reader itself never opens test data.

## Future invocation (not executed)

From `detector/`, with `PYTHONPATH=.` and the same checkout/source hashes for both reports:

```bash
uv run --no-sync python -m m1.d1_threshold_lock_r3_successor build-report \
  --seed 20261018 --identity <pilot-identity.json> \
  --predictions <pilot-11-csv-bindings.json> \
  --bundle ../tmp/yolo11n_n1_extract_r2 --repo-root .. \
  --out <seed18-r3-report.json>
uv run --no-sync python -m m1.d1_threshold_lock_r3_successor build-report \
  --seed 20261019 --identity <s2-identity.json> \
  --predictions <s2-11-csv-bindings.json> \
  --bundle ../tmp/yolo11n_n1_extract_r2 --repo-root .. \
  --out <seed19-r3-report.json>
uv run --no-sync python -m m1.d1_threshold_lock_r3_successor write \
  --reports <seed18-r3-report.json> <seed19-r3-report.json> \
  --bundle ../tmp/yolo11n_n1_extract_r2 --repo-root .. \
  --out <versioned-lock.json> --proof <r3-proof.json>
uv run --no-sync python -m m1.d1_threshold_lock_r3_successor verify \
  --bundle ../tmp/yolo11n_n1_extract_r2 --repo-root .. \
  --out <versioned-lock.json> --proof <r3-proof.json>
```

These commands are **planned**;
there are no authorized S2 NMS CSV bindings in this task. The final evaluator must call
`read_for_final` only after lock-result QA, a clean tracked lock/proof and an explicit Owner
approval record exist. The old `m1.cli lock-thresholds` and schema-1 reader are incompatible.

## Source-only verification

- `uv run ruff check src tests`: PASS.
- `uv lock --check`: PASS.
- `cd detector && PYTHONPATH=. uv run --no-sync pytest -q tests/test_d1_threshold_lock_r3_successor.py`:
  10 passed. Tests include synthetic refusal/tie/bootstrap/fold cases; the pilot test invokes the
  real report builder on 11 already-pinned CSVs and compares all available coarse-grid cells and
  full-candidate AP to the QA JSON. At 0.20 the pilot anchor is TP 547, FP 150 and 457 correct
  class hits; at the diagnostic fine point 0.19 it is 555/155/461. The pilot test bypasses only
  the future per-seed authorization metadata gate, tested separately with synthetic artifacts.
- `graft build . && graft check .`: graph in sync.

## Remaining gates and limits

- No real seed reports, lock, proof, lock-result QA or Owner lock approval were created.
- The pilot result archive is not currently in this checkout. A future real build must first
  supply its QA-pinned archive, manifest, and run contract from the retained private artifacts;
  the writer will refuse missing or mismatched files.
- This source gate does not validate behavior on seed 20261019 NMS predictions. Authorization,
  independent result QA and a separately reviewed lock are still required before final evaluation.
