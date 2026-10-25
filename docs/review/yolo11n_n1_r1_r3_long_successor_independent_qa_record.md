# YOLO11n N1 R1-R3 long-successor independent QA

Date: 2026-10-25 (`Asia/Ho_Chi_Minh`)  
Scope: pre-execution source/notebook, real epoch-0002 artifact and remediated final-verifier QA  
Verdict: **PASS**

## Authorization boundary

This PASS satisfies the independent pre-execution QA gate only for the exact hashes in this
record. Together with the existing Owner authorization, the exact reviewed successor may advance
to its controlled L4 long-resume workflow after its delivery/checkout pins are preserved. It does
not authorize a different notebook or source, validation evaluation, threshold selection,
sealed-test access, publication, deployment or a safety claim. No training, upload, commit, push
or sealed-test access was performed during this review.
`sealed_test_accessed=false` was observed in the real smoke state, proof and train/validation
archive.

## Reviewed inputs and observed SHA-256

| Artifact | SHA-256 |
| --- | --- |
| `scripts/build_yolo11n_n1_r1_r3_long_notebook.py` | `0a187615b816aab2b8cd1b2f9c2f712e062eaaec33cfef4a9fcf2a6464c23fa5` |
| `tests/test_yolo11n_n1_r1_r3_long_notebook.py` | `350dfa7224a0b83f749454ba731525d18abde894a41dc71dcc21d5cfc05fdb74` |
| `detector/colab/yolo11n_n1_r1_r3_long.ipynb` | `1b3522cfe8e7fa7ee330a5fd46466f79d5d3d02134b7d7e80e40c58d1f705f31` |
| `docs/review/yolo11n_n1_r1_r3_long_run_contract.md` | `7858ae78683a97bdfaa04c40833c5d2827aad03a9887fcb4720d71923cde1159` |
| `docs/review/generated/yolo11n_n1_r1_r2_smoke_qa_proof.json` | `84f98827da16884a6c95162e73d00bc6ae3ff1fa80c5f4aff67431d765f4f421` |
| `detector/colab/run_yolo11n_n1_r1_r1.py` | `cd3edab0adee25c8642f840edb36d899687ba952bdfcbaca853568f65dcd72e6` |
| `detector/m1/checkpoint_store.py` | `e1f8f00c036d6407d327164d907f3641427864cc35cf817336209ae5da76891c` |
| source-QA record | `5fd51deea1679263b224fc45531f30a3d0a5aac86b3d044d262446e77a48b92a` |
| smoke artifact-QA record | `2c1ab19b14456e75f37c454cb619c2dbad1509e1e8eb63a30bc897e603415eb4` |
| Owner decision record | `b2b40c5937e25316c6806d5bcb6babbdcf284860a2305f2fc7b5915a058e2b8c` |
| local train/validation archive | `5798ad93f552e1f7c36b46a3470fc9f8f85c5125df753786d63e228822299d05` |
| archive `manifest.json` | `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da` |

The notebook-pinned commit
`d8471ed0cfeca71ae823fc9ecf50625500e1b4be` exists locally, is contained by
`origin/codex/yolo11n-dual-track-r1`, and contains byte-identical copies of the runner, smoke
proof, source-QA record and smoke artifact-QA record above.

## Verified real smoke state

The authoritative local Drive sync was read at
`M1_D1_Colab/runs/yolo11n_n1_seed_20261018_r1_r1`; no file in it was changed.

- `latest.json` SHA-256:
  `ed42322f480030cd05a5f1bffb30731dad9a75eba5e158883535e078c6debb6a`.
- Latest generation: `epoch-0002`; checkpoint-manifest SHA-256:
  `6d437c376e4aeaa8d438c06618c9c6bd9b32d5fcd31b59c55f4b693cd9c2ab3e`.
- Binding SHA-256:
  `098766d77d0b5146f560cb3e0125c6af0c5d5815f165e29c0224b290db6e1275`.
- All five checkpoint members matched their manifest sizes and hashes.
- Execution status was `SMOKE_STOP`; modes were exactly `fresh`, `resume`; runtime digests were
  exactly the two values pinned in the proof.
- Text-log and SQLite event sequences were byte-equivalent after JSON parsing; SQLite
  `pragma integrity_check` returned `ok`.
- The proof's config and manifest binding exactly matched the checkpoint binding. Its Colab state
  path digest matched the exact pinned `/content/drive/MyDrive/.../yolo11n_n1_seed_20261018_r1_r1`
  path.

The local 785 MiB archive matched its pin, contained exactly 8,580 entries including one
`manifest.json`, had no path component named `test`, and declared `test_included=false` and
`sealed_test_accessed=false`.

## Source and gate findings that passed

1. `require_long_run_qa` accepted the exact proof against the real epoch-0002 checkpoint bytes.
2. Recomputed anchors or semantic changes to verdict, stage, seal, smoke epochs, package, state
   path, checkpoint pointer, runtime uniqueness, manifest or config all failed closed.
3. A modified checkpoint member, modified pointer, checkpoint-member symlink, state-path symlink,
   proof symlink and proof hardlink all failed closed.
4. The long command is `mode=resume`, omits `--stop-after`, uses the R1-R1 runner and isolated
   state, and is restricted by an exact `gpu_name == 'NVIDIA L4'` notebook preflight.
5. The notebook contains no `export-test`, `final-eval`, test split or other sealed-test route.
6. The frozen target remains 100 epochs. The runner restores from the latest valid checkpoint and
   refuses a fresh unrestricted run. It reuses the existing classifiers.
7. `worker_rng_exact_replay=false` is explicitly disclosed in the contract and is required by
   checkpoint recovery validation.
8. Two independent rebuilds were byte-identical and matched the reviewed notebook hash.

## Remediation chronology and final artifact verifier

The first reviewed notebook snapshot (`0c9ae188...`) failed because its final cell could emit
`LONG_RUN_PASS` for a missing text log, a non-tar result and fabricated manifest. A first
remediation added exact archive/log parity, but adversarial QA then showed that it could still
accept an epoch-0100 pointer without any checkpoint snapshot and coherently fabricated dummy model
members. Both findings were reported before execution; neither deficient snapshot is approved.

The final reviewed notebook (`1b3522cf...`) closes both findings. Its verifier now requires:

- regular, non-symlink, single-link, nonempty live execution, text log, SQLite log, final pointer,
  result archive and result manifest;
- immutable read-only SQLite integrity, exact schema and row-for-row parity with text log, plus
  execution-attempt and terminal-event parity for the live and archived copies;
- a strict epoch-0100 latest-pointer schema/version/binding and checkpoint-manifest hash;
- a real `epoch-0100` snapshot with exact checkpoint schema, run identity, binding, five-member
  roster and every member size/hash;
- an exact eight-member safe tar roster with every byte read back and compared with the result
  manifest;
- equality between all five result model artifacts and their checkpoint-manifest records;
- live `SUCCEEDED` after epoch-100 `TRAINING_COMPLETE`, archived `FINALIZING` at epoch-100
  `TRAINING_COMPLETE`, all seal values false and all recovery events disclosing
  `worker_rng_exact_replay=false`.

A synthetic positive end state containing the exact checkpoint and result chains passed. Removing
the epoch-0100 snapshot, adding a pointer key, changing a checkpoint artifact, rebinding and
rehashing a checkpoint manifest, changing a result model artifact coherently, linking a checkpoint
member, or breaking either live or archived log/SQLite parity all failed closed. There are no
remaining blockers in the reviewed scope.

## Commands and results

```text
graft build . && graft check .
# OK; wiring graph in sync (5,206 nodes, deep meaning layer not built)

graft ask "Audit YOLO11n N1 R1-R3 long successor: proof-to-epoch2 state binding, require_long_run_qa attacks, long notebook resume command and L4 guard, epoch100 verification/package/log/seal expectations, worker RNG disclosure, contract and tests." --source .
# refreshed task-relevant graph; estimated 17,800 tokens saved

uv run ruff check scripts/build_yolo11n_n1_r1_r3_long_notebook.py tests/test_yolo11n_n1_r1_r3_long_notebook.py
# All checks passed

uv lock --check
cd detector && uv lock --check
# both resolved successfully

# isolated two-build reproduction plus notebook-focused tests
# rebuilt twice equal=true; rebuilt matches reviewed notebook=true;
# SHA-256 1b3522cf...; 5 tests passed

cd detector && uv run ruff check colab/run_yolo11n_n1_r1_r1.py \
  tests/test_yolo11n_n1_r1.py tests/test_yolo11n_n1_r1_r1.py \
  tests/test_checkpoint_store.py tests/test_checkpoint_store_r2.py
# All checks passed

cd detector && uv run pytest tests/test_yolo11n_n1_r1.py \
  tests/test_yolo11n_n1_r1_r1.py tests/test_checkpoint_store.py \
  tests/test_checkpoint_store_r2.py
# 26 passed in 3.17s

# direct require_long_run_qa harness
# exact proof/state ACCEPT; 19 altered-proof/binding/checkpoint/path/link cases REJECT

# final stable verifier synthetic harness
# exact checkpoint-bound eight-member end state ACCEPT
# missing snapshot, latest schema drift, checkpoint byte drift, checkpoint binding drift,
# result/checkpoint model mismatch, checkpoint symlink, live DB/text mismatch and archived
# DB/text mismatch all REJECT
```

