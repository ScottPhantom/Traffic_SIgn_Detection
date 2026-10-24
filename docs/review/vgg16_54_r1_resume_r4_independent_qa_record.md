# VGG16-54 R1 R4 epoch-2 resume launcher independent QA record

Status: `QA_PASS_RESUME_EPOCH_2_ONLY`

Reviewed: `2026-10-24T20:08:10+07:00`

Reviewer boundary: independent delta and artifact-readiness QA. The reviewer did not resume,
train, upload, download, commit, push or access the sealed test. This append-only record reviews
only the R4 launcher and its read-only preflight against the synced epoch-1 state.

## Reviewed files and anchors

- Builder SHA-256:
  `66cc022df83b1b7fc5228ff5b5bdc5565b425d32bd8575f73139f370edd9bd35`.
- Notebook SHA-256:
  `76c58b32cf0f9ab83bad8be074805dcf4e397b58a8bd6a36f31f6a91c345cd75`.
- Notebook-test SHA-256:
  `eea369dff4b9d4b38d550deca938abbe841cdb959a3bb545e8f031b1e4567849`.
- Implementation-record SHA-256:
  `b8c5bb23be79a8e135d9a754b9f68ba549631c66c04269211af4c2157cfa5af3`.
- Fresh-smoke proof SHA-256:
  `97b9dbbba6ebb99e30df733949684e9aef2e486f7e8357cee4b90968e42da580`.
- Fresh-smoke artifact-QA record SHA-256:
  `f6ed749b53d82ecd88b9b6299f4b7862eff9d4490966c9f36c7a093ff954ad8f`.
- Immutable source commit:
  `2e1d981e70e02b19d1998fa17be8c8a0de033df0`.
- Fresh runtime digest:
  `15f95cca74680341a2e90aeee1e6679050ddf3974ab525e6ad7366eb1000453f`.

## Deterministic delta and execution boundary

Independent parsed-cell comparison found the R4 notebook identical to the QA-PASS R3 notebook
except for the five declared cells: title, configuration, preflight, postflight and final gate.
Metadata, checkout/proof/bundle anchors, state suffix, extraction and governed runner invocation
remain unchanged. Independent temporary generation was byte-identical to the reviewed notebook.
All nine cells are clean, with `execution_count=null`, empty outputs and compilable code.

The execution boundary is exactly:

- state: `M1_D1_Colab/runs/vgg16_54_seed_20261018_r2`;
- mode: `resume`;
- stop: epoch `2`;
- runtime: exact `NVIDIA L4`, with a runtime digest distinct from the pinned fresh digest;
- runner: `python -m colab.run_vgg16_54_r1_r1`;
- data boundary: reviewed train/validation bundle only.

The governed runner independently verifies the source-QA proof, exact L4 evidence, prior smoke
state, binding and new runtime identity before model work. It rejects same-runtime resume and
restricts this smoke to epoch 2.

## Real synced-state preflight

The R4 proof/state checks were reproduced read-only against the actual locally synced Drive state.
The exact 11-file roster passed: five state/log/pointer files, five snapshot payloads and one
checkpoint manifest. Every expected file was a single-link regular file with exact proof-bound
size and SHA-256. The exact checkpoint generation is `epoch-0001`; execution is `SMOKE_STOP` at
epoch 1 with one fresh NVIDIA L4 attempt, matching runtime/GPU evidence and
`sealed_test_accessed=false`.

The proof uses a closed top-level schema, rejects duplicate JSON keys and non-finite constants,
and pins the expected state-artifact keys, snapshot paths, record keys, manifest hash, binding,
configuration, source commit and authorization. Any proof mutation, including a duplicated
snapshot row, changes the outer pinned proof hash before semantic use.

## Adversarial checks

- Wrong proof schema, duplicate JSON keys and non-finite JSON constants were rejected.
- Mutated proof rows, file size/hash, state path, mode, stop value, source/binding/runtime anchors
  and hidden long/sealed routes differ from the deterministic reviewed notebook or pinned proof.
- Direct file symlinks fail the notebook's `lstat` regular/single-link check.
- A state-root or ancestor symlink is independently rejected by the governed runner's
  ancestor-aware strict JSON and checkpoint-directory guards before resume, even though the
  notebook also rehashes every final file and exact roster.
- The exact notebook contains no `export-test`, `--final-eval`, test-split route or long-run path.
- Postflight requires `SMOKE_STOP` at epoch 2, exactly two attempts, fresh then resume ordering,
  a new L4 runtime digest, equal run/checkpoint binding and `sealed_test_accessed=false`.

## Reproduced gates

- Targeted builder/test Ruff: PASS.
- Exact R4 notebook Ruff: PASS.
- Root and detector lock checks: PASS.
- R2+R3+R4 notebook suite: `13 passed`.
- Governed VGG/runtime/checkpoint regression suite: `35 passed`.
- Real synced-state read-only preflight: PASS, 11/11 exact files.
- Final `graft check .`: OK, 4,951 nodes; the optional unbuilt meaning layer is non-blocking.

## Operational prerequisite and verdict

At review time, the exact fresh-smoke proof existed in the repository but was not yet present at
the notebook's private Drive path
`M1_D1_Colab/vgg16_54_r1_r3_fresh_smoke_qa_proof.json`. Before execution, that exact file must be
uploaded and read back from Drive with SHA-256
`97b9dbbba6ebb99e30df733949684e9aef2e486f7e8357cee4b90968e42da580`.
The notebook will fail before resume while this prerequisite is absent.

`PASS`, zero source/notebook blockers, for uploading and executing **only the exact reviewed R4
notebook** after the proof readback, on a genuinely new NVIDIA L4, through epoch 2 only. Epoch-2
artifacts require independent two-runtime artifact QA. This PASS does not authorize long training,
model publication, sealed-test access, commit or push.
