# D1-S2-R1 independent source QA

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Reviewer: separate Codex QA agent
`/root/s2_source_qa`; this agent did not author or operate the trainer, launcher,
or Colab run. Boundary: local source, contract, authorization record, and focused
tests. No training, Drive write, Git push, R3 scoring, or sealed-test access occurred.
`sealed_test_accessed=false`.

Verdict: PASS — source is ready for commit A and a separately reviewed notebook; this verdict does not cover a live L4 smoke or result.

## Reviewed identity

| File | SHA-256 |
| --- | --- |
| `docs/review/d1_s2_r1_owner_authorization_2026-11-06.md` | `4f394487f7c8d51c31c268414bc16aabc1baa57a41822563459489d0940d2f0c` |
| `docs/review/d1_s2_r1_run_contract.md` | `c226bf281811aaf0245d697b07993b2b358f1ceb8140ac6edf274d95322a5088` |
| `detector/m1/resumable_train_s2_r1.py` | `a7025fd0ebaad0e0cdee5113d7f72c5f17606485e5a05da7b5cb2f99b6b98936` |
| `detector/colab/run_d1_colab_s2_r1.py` | `f69b071a42e2193948cd2406528cd646d3046e18ffdd1c0e9930103b13ebada1` |
| `detector/tests/test_s2_r1_train.py` | `5cd8fd5c9f6cf3d46f03c78a609757c8fe2d82eccfc4f68e7cc737c1971f0361` |
| `detector/tests/test_s2_r1_colab.py` | `c7f8614e277c72dd712177351c786a5ef344dc3c2e7a6d26032c9902c3b1fb4d` |

The local pilot `run_contract.json` independently hashes to
`9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88`.
Its 16 passed train-argument keys match the S2 source template exactly after changing
only `seed` from 20261018 to 20261019 (with the new run's `name` and `project`
treated as identity fields). In the direct local comparison using the pilot's own
name/project, the changed-key set is exactly `{seed}`. The `data` value stays the
pilot export YAML. No `optimizer` override is passed; pretrained, deterministic,
`fliplr`, epochs, patience, image size, batch, workers, fraction and device match.
The pilot weight SHA is `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`;
the governed export manifest hashes to
`8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71`.
The authorized bundle and sidecar SHA values in the S2 contract match the A2
notebook's pins; live Drive bytes remain to be checked by the notebook and launcher.

## Source checks

1. The trainer and launcher both require a repo-relative SHA-matching Owner record
   before invoking predecessor training or creating Drive state. The record contains
   the Owner sentence conveyed by Claude, names the pilot SHA and seed 20261019,
   and has the exact authorization line. The record filename contains no case-insensitive
   `test` substring, avoiding the inherited path guard. Neither source file alone
   grants training authorization.
2. The trainer freezes seed 20261019, 100 epochs, patience 0, imgsz 1280, batch 4,
   workers 4, fraction 1.0, tag `s2_r1`, CUDA device 0, and a mandatory epoch-1
   fresh pause. Resume forbids a stop boundary and the complete run must reach epoch
   100. Its callback path is the unchanged `m1.resumable_train` predecessor. The
   checkpoint binding adds experiment, single-change declaration, pilot SHA and
   authorization SHA; the run contract adds those fields and a false seal flag.
3. The launcher captures the predecessor parser before patching it, then restores
   each patched function in `finally`. It pins the checkout commit, authorization,
   state path and bundle SHA into the run binding. The state suffix is unique to S2.
   The command invokes only `m1.resumable_train_s2_r1`. The inherited R6/R5/R2/R1
   chain handles checkpointing, two-runtime evidence and result packaging.
4. The S2 packaging shim handles the extra run-contract fields that the base exact
   schema would reject. It requires the exact S2 schema, training arguments, governed
   data binding, approved pretrained weight, D-05 gates, clean L4/CUDA checkout,
   authorized record, false seal flag, and both weight hashes before attestation.
   The inherited packager uses its returned attestation hash. This was checked by
   the synthetic positive/negative package tests; real Colab packaging is unverified.
5. Source does not export/open the sealed payload, does not use the A2 repeat list,
   and does not evaluate on the R3 roster. The inherited export is train/val only;
   the test digest remains a binding value, not payload access.

## Local gates and remaining live gates

- `uv run pytest -q tests/test_s2_r1_train.py tests/test_s2_r1_colab.py`:
  23 passed. The synthetic negative cases include changed seed, data, seal,
  export, GPU and authorization in the package validator.
- `uv run ruff check` on the four new Python files: PASS.
- `uv lock --check` in `detector/`: PASS, 66 packages.
- `graft check .` after the coordinating agent rebuilt the graph: OK.
- Notebook QA must still prove a clean clone of commit A at exactly
  `/content/Traffic_Sign_Detector`, exact bundle/sidecar hashes and L4 requirement.
  Independent live smoke QA must inspect the real Drive checkpoint/log/contract,
  3,712 train and 376 val images, exact train-argument delta, a distinct later
  runtime digest, and `sealed_test_accessed=false` before resume. This record
  establishes none of those live outcomes.
