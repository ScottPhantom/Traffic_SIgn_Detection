# YOLO11n N1 R1-R2 composite source independent QA record

Date: 2026-10-25 (Asia/Ho_Chi_Minh)  
Verdict: **PASS**  
Reviewer: independent QA session `/root/yolo11n_dual_track_r1_source_qa`

## Scope and reason for this successor

This append-only record addresses only the execution-eligibility binding defect documented in
`docs/review/yolo11n_n1_r1_r1_live_smoke_failure_r2_record.md`. It does not change the model,
dataset, configuration, runner, state path, weights, epoch policy or sealed-test boundary.

The inherited guard accepts exactly one canonical, unqualified PASS verdict line and then requires
this same record to contain the hashes of every source member embedded in the train/validation bundle, the
Cascade B0 execution contract, and the R1-R1 repair runner. The earlier repair-only QA record did
not repeat the full bundle-source table and used a qualified PASS heading, so the live fresh smoke
failed before state creation.

The independent reviewer replaced `PENDING` only after reproducing every check below. A FAIL
verdict would retain the failing evidence and block notebook generation/execution.

## Pinned prior QA and failure evidence

| File | SHA-256 |
| --- | --- |
| `docs/review/yolo11n_dual_track_r1_source_independent_qa_record.md` | `bcf7470d931d23445785c1103e3c919aca4c696b22738079756572892ce4f632` |
| `docs/review/yolo11n_n1_r1_r1_source_independent_qa_record.md` | `57eb794e7256f1797a2961286330a98baa9a87664c9c6d84b84fe9ffda332254` |
| `docs/review/yolo11n_n1_r1_r1_live_smoke_failure_r2_record.md` | `e8556846bb77092ececde440858415ea37583ca0478eb4fdb31b84242b682caa` |

## Bundle-source binding required by the inherited guard

| Bundle member | SHA-256 |
| --- | --- |
| `detector/colab/build_cascade_b0_bundle_r1.py` | `9b5b73b1a64449655963e13f437f15814ef879d17fff3a521a209e7414851afe` |
| `detector/colab/build_yolo11n_n1_bundle_r1.py` | `a7a8d9cd8520ddd0656c2fe582f239404b4f71b566f5bae9eccd8fd6daa20529` |
| `detector/colab/evaluate_cascade_b0_r1.py` | `8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42` |
| `detector/colab/extract_cascade_b0_r1.py` | `f67663f42f8904e63f892c0ae5e861b1954c2fe9c12292cc0b607c0e3d64f068` |
| `detector/colab/run_cascade_b0_r1.py` | `0ece03891ebe0f8c318efd7a062fdb8d799d4cf9cc357b0cf8840b4103ad876a` |
| `detector/colab/run_yolo11n_n1_r1.py` | `b60e829104f644248912acddf4397fe07ff647e709feefef6dd0443c393e5753` |
| `detector/d1_cascade_classifier/__init__.py` | `fda3d39a0603c715c111ce2eac8757932d27a0b45104a47b8802331d7336435b` |
| `detector/d1_cascade_classifier/contract.py` | `e847db9ae322fe3a7ba11e8e77743ec32440027f5d29222f2c937d746a9cfc94` |
| `detector/d1_cascade_classifier/data.py` | `e55fbaddea154131a0ef20f8d2653150b0f2c8eecdc8ff31dbcb16d6a463ed5d` |
| `detector/d1_cascade_classifier/metrics.py` | `612259aa52bf8794db3c717b7b6f481532f9bccc572034709cfcefc66d316078` |
| `detector/d1_cascade_classifier/model.py` | `fdcbc4156a4bef9b5eed56a8ebc58746408a14f6558cd4b3c38a4e49df47b77a` |
| `detector/m1/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `detector/m1/checkpoint_store.py` | `e1f8f00c036d6407d327164d907f3641427864cc35cf817336209ae5da76891c` |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` |
| `detector/pyproject.toml` | `80a60ba75ecf68a33006a9dbb8d32eacb75b7a7dbe87dd952b7b9f9f9ab1fa7e` |
| `detector/uv.lock` | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |
| `docs/review/cascade_b0_execution_contract_r1.md` | `e19871af64a169fd5560c1414914a5915a70d43e981ce3d340df6d4429a660e7` |

## R1-R1 repair binding

| File | SHA-256 |
| --- | --- |
| `detector/colab/run_yolo11n_n1_r1_r1.py` | `cd3edab0adee25c8642f840edb36d899687ba952bdfcbaca853568f65dcd72e6` |
| `detector/tests/test_yolo11n_n1_r1_r1.py` | `b1258334cb47b853baf46ceff84aee5b524fcefc4e7786c7f219cc47c96e6216` |

## Additional N1 successor-governance bindings

These two bundle members are not selected by the inherited generic source-extension filter, but
the N1 wrapper explicitly requires their byte hashes in the same QA record.

| Bundle member | SHA-256 |
| --- | --- |
| `docs/review/yolo11n_dual_track_r1_owner_decision_record.md` | `b2b40c5937e25316c6806d5bcb6babbdcf284860a2305f2fc7b5915a058e2b8c` |
| `docs/review/yolo11n_dual_track_r1_run_contract.md` | `60a0e2fb16565a19ba99957d01f3160ca4872659361951ce3d0d8316e69247f3` |

## Independent checks required for a PASS

1. Recompute the train/validation archive and manifest hashes and confirm no test payload exists.
2. Derive the 16 source-member hashes from the real bundle manifest and byte-compare them with the
   table above.
3. Confirm the Cascade execution-contract hash and R1-R1 runner/test hashes above.
4. Invoke the real `require_source_qa` path against a temporary exact-PASS copy of this record and
   the extracted real bundle; it must pass.
5. Remove or alter the canonical PASS marker, one bundle-source hash, the Cascade contract hash, or
   the R1-R1 runner hash; each attack must fail closed.
6. Re-run the focused R1/R1-R1/checkpoint tests and scoped Ruff checks.
7. Confirm the runner has no sealed-test route, preserves the state suffix
   `M1_D1_Colab/runs/yolo11n_n1_seed_20261018_r1_r1`, and keeps
   `sealed_test_accessed=false`.

## Boundary

This record may authorize only a new source-hash-pinned notebook delta for fresh epoch 1 followed
by a different-runtime resume to epoch 2. It does not authorize 100-epoch training, evaluation,
publication, sealed-test access, model acceptance or deployment.

## Reproduced independent evidence

- The real local archive `tmp/yolo11n_n1_r1.tar.gz` is a regular non-symlink file of
  `823358941` bytes and recomputed to
  `5798ad93f552e1f7c36b46a3470fc9f8f85c5125df753786d63e228822299d05`.
  The extracted real `manifest.json` recomputed to
  `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`.
- The archive has 8,580 regular-file/directory members including `manifest.json`; the manifest has
  8,579 payload members. Neither roster contains a `test` path, an unsafe path, a link or a special
  entry. Manifest policy is `test_included=false`, `sealed_test_accessed=false`, one detector class,
  train 3,712 images / 12,621 boxes and validation 376 images / 624 boxes.
- All 16 source-member bytes, the Cascade execution contract and the two successor-governance
  members recomputed exactly to the hashes recorded above. Current checkout bytes match the real
  extracted bundle for all of those inherited inputs. The R1-R1 runner and test hashes also match.
- The real runner `check` path verified all bundle members and returned `valid=true` with
  `sealed_test_accessed=false`. The real `require_source_qa` path accepted a temporary exact-PASS
  copy of this completed record against the extracted real bundle.
- Missing or qualified PASS, record-anchor drift, one altered bundle-source hash, an altered
  Cascade-contract hash, an altered R1-R1 runner hash, altered owner/run-contract bindings, a
  symlinked QA record, a symlinked parent and a symlinked bundle root were each rejected. Actual
  source-byte and Cascade-contract-byte mutations in an isolated shadow bundle were also rejected.
- Scoped Ruff passed. Focused R1, R1-R1 and checkpoint-store tests passed: 26 tests, zero failures.
- The failed R1-R1 state remains absent from the locally synchronized Drive path. No training,
  upload, commit, push, evaluation or sealed-test access occurred during this review.
