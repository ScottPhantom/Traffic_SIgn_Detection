# VGG16-54 R1 — independent QA brief

Review read-only in a session that did not author this package. Do not train and do not open the
sealed test.

## Scope

- `detector/vgg16_54/__init__.py`
- `detector/vgg16_54/model.py`
- `detector/vgg16_54/contract.py`
- `detector/colab/run_vgg16_54_r1.py`
- `detector/colab/extract_cascade_b0_r1.py`
- `detector/colab/run_cascade_b0_r1.py` (imported bundle verifier and event logger)
- `detector/d1_cascade_classifier/{__init__,contract,data,metrics,model}.py`
- `detector/m1/{__init__,checkpoint_store,checkpoint_store_r2}.py`
- `detector/tests/test_vgg16_54_r1.py`
- `docs/review/vgg16_54_r1_preparation_contract.md`
- `detector/pyproject.toml` and `detector/uv.lock`

The machine-readable source proof must bind every entry in `SOURCE_FILES`; review must fail if a
runtime import is absent from that allowlist.

## Required checks

1. Prove the VGG16 convolutional stack requests `weights=None`, outputs exactly 54 logits and has
   the declared compact crop head.
2. Verify exact Cascade B0 bundle bytes/counts and prove no sealed-test member or route exists.
3. Attack Owner/source-QA/smoke proof paths with wrong hashes, links, schema changes and seal=true.
4. Prove fresh epoch 1 and resume epoch 2 cannot silently restart or cross into D1/Cascade state;
   specifically, resume smoke must reject a latest checkpoint at epoch 2 or later instead of
   training epoch 3.
5. Tamper with model/optimizer/scaler/RNG/binding/checkpoint ledger/latest pointer; prove a bad
   ledger is rejected before restore copies bytes or any GPU epoch begins.
6. Verify exactly two large recovery generations remain and checkpoint I/O is separately timed.
7. Reproduce selection by supported-class macro-F1 with validation loss as tie-breaker.
8. Prove the 100-epoch value is a ceiling: early stopping cannot occur before epoch 30, uses
   patience 15, packages a valid early-stopped terminal checkpoint, and never replaces `best.pt`
   with the last epoch merely because training continued.
9. Run Ruff, targeted detector tests, full detector tests and lock check.
10. Confirm no upload, download, training, commit, push or sealed-test access occurred.

PASS authorizes only a future L4 smoke after the Owner config approval is pinned. It does not
authorize the long run, publication, test access or a claim that VGG16 is better than CompactCNN.
