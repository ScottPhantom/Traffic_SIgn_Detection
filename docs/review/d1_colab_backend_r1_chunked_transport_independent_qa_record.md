# D1 Colab backend R1 chunked transport independent QA record

Status: `QA_PASS_D1_COLAB_BACKEND_R1_CHUNKED_TRANSPORT`

Reviewer: `Codex independent QA session (did not author the chunking or notebook changes)`

Reviewed at: `2026-10-20T11:37:47+07:00`

Boundary: `LOCAL_TRANSPORT_QA_ONLY_NO_UPLOAD_NO_COLAB_RUN_NO_TRAINING_NO_COMMIT_NO_PUSH_NO_SEALED_TEST_ACCESS`

Reviewed checkpoint: `1a32722fd33f37da4a17b6c80588a792451199f9` plus the current uncommitted chunked-transport worktree and ignored local transport artifacts

## Verdict

- **PASS — 0 Critical, 0 High, 0 Medium, 0 Low.**
- All eight local part files match their exact pinned sizes and SHA-256 values. Concatenating them
  in lexical `part-00` through `part-07` order produces the exact already-reviewed original archive
  SHA-256 `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641`
  and size `766226800` bytes.
- The notebook validates the mounted sidecar and every selected part before creating an output,
  writes a reconstructed archive only to the runtime-local fixed `/content` path with exclusive
  creation, and verifies the final archive size/hash before `tarfile.open` reads its manifest.
- The exact single-archive path remains supported and fail-closed: it is never rewritten, and the
  same final size/hash gate runs before manifest access.
- This PASS approves only the local transport controls. It does not authorize or prove upload,
  Colab execution, training, a checkpoint, result package, metric or accepted model.

## Exact transport artifacts

| Part | Bytes | SHA-256 |
| --- | ---: | --- |
| `part-00` | `99614720` | `53f30f08406fbef5b8451610b2fd44a1f2be42ca6d50f612b68e5ace285e66ff` |
| `part-01` | `99614720` | `8451fe932760179d4b2e1a9cbdd21fd58744bc6b8f3d2a90e431cece7f546544` |
| `part-02` | `99614720` | `867c935bf152ddfc3e7919547dccf3682291326b60b956a8100fc1a59b60e98d` |
| `part-03` | `99614720` | `046fc8ae5d4e0a91196ccd6a6afa422fb1254baea7ae30bc3cab39602b534907` |
| `part-04` | `99614720` | `6d3751d858232fada5d57e8e892f3e272cd5b9e34efb184971b3f4786842665d` |
| `part-05` | `99614720` | `938106e4d34743e9b79109feb98d573f317afad44289f792f070f22e3924159b` |
| `part-06` | `99614720` | `3497c1a10314c74d4b81ba9a5a49653b16ba2e2d52b424fd7655623547cb6408` |
| `part-07` | `68923760` | `5f5ca85bc392310b2b5693ad9d0723f046eca9fd7980b45c944f22a3b3bc0eea` |

The seven full parts total 697,303,040 bytes; adding the final 68,923,760-byte part yields exactly
766,226,800 bytes. The machine-readable part manifest is 1,514 bytes with SHA-256
`6595b82c142167e9a84bd6122612bc9abb06c33eedf0d4d7b041ef5e638037f0`.
Its eight ordered `(name, size, sha256)` records exactly equal notebook `PART_SPECS`.

Streaming the eight files in lexical order directly into SHA-256, without creating another
archive, returned the original archive hash. The preserved original archive and sidecar still have
their independently approved hashes:

- archive: `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641`;
- sidecar: `7e0dc5b0144faa5f0be407224eaf8070dd51199fa8a1d2f164b248fd6a06d5b2`.

## Source-commit verifier reconciliation

Running the official verifier against the current documentation HEAD `1a32722…` correctly failed
closed with `bundle manifest binding differs: repo_git_commit`; the archive intentionally binds the
earlier backend-fix source commit and was not rewritten to follow documentation commits.

QA therefore created a temporary detached clean worktree at the exact embedded commit
`ffc2b448f06c45dae597de5b565cab64c0377573`, exposed the unchanged governed local data read-only via
that worktree, and ran that commit's official verifier against the absolute preserved archive path.
It returned `status=VERIFIED`, `file_count=5888`, `test_included=false`, the expected counts and the
exact train/validation stem-list hashes. The temporary worktree was removed immediately afterward;
the main worktree remained on `1a32722…`.

This matches the notebook flow: it hashes the transport, reads the embedded commit, clones and
checks out that exact commit, verifies `HEAD`, and only then invokes the bound runner against the
reconstructed or original archive.

## Notebook and safety audit

- Six code cells remain unexecuted with empty outputs; the notebook contains neither `export-test`
  nor `--final-eval`.
- On the part route, all eight files are required, size-checked and hash-checked in the pinned tuple
  before `BUNDLE.open('xb')` can execute. Concatenation follows the tuple's lexical order.
- The only reconstruction target is
  `/content/m1_colab_train_val_backend_r1.tar.gz`. Exclusive `xb` creation prevents overwrite. If
  an output already exists, it is not rewritten and must independently pass the final exact hash.
- Both transport routes converge on the same `EXPECTED_BUNDLE_BYTES` and
  `EXPECTED_BUNDLE_SHA256` assertions before `tarfile.open(BUNDLE)`.
- Sidecar bytes are verified before transport selection. The archive manifest must still declare
  only `train` and `val` and `test_included=false`.
- The guide uses the same eight-part range, sizes, runtime path and fail-closed verification order.
- The new part manifest and payloads remain under ignored `tmp/`; `git status` contains no tracked
  archive, sidecar, part manifest or part payload.

## Reviewed tracked-file pins

| Item | SHA-256 |
| --- | --- |
| Chunk-aware notebook | `12b29493ec69c38adc4de9443756d8dbe5a548a38edaf7cab4641b757b74d52f` |
| Primary Colab tests | `a87f248583745fdcf54c5874ad53438b2b0966bbbd4642ab54b1e5e97522c48c` |
| Operator guide | `43ffc6e3034b225bc8ff2a2f81eba106087bcfbb70a65c7c77189d944460cee6` |
| Chunked transport record | `62fed9046960849be4aeed24e8fbfcc973ca6097aa895021f40af5d963fc35a3` |

## Validation

| Gate | Result |
| --- | --- |
| All eight individual part size/hash checks | PASS |
| Part manifest vs notebook `PART_SPECS` | PASS, exact eight-record equality |
| Lexical streaming concatenation | PASS, exact original size/hash |
| Official verifier at embedded commit | PASS, `VERIFIED`, 5,888 files, train/val only |
| Current-HEAD official verifier | Expected fail-closed on `repo_git_commit`; no bytes rewritten |
| `tests/test_m1_colab.py` | PASS, **24/24** |
| Root Ruff (`src tests scripts main.py`) | PASS |
| Root dependency lock | PASS, **168 packages** resolved |
| Notebook JSON/execution-state readback | PASS, six unexecuted code cells and zero outputs |
| `git diff --check` | PASS |
| Graft check | PASS, graph synchronized at **2,522 nodes / 6,380 edges** |
| Exact `results/experiments/sealed_test_access_log.jsonl` | ABSENT |

No upload was attempted, no Drive file was created/overwritten/deleted, no Colab cell ran, no model
was trained, no test split or sealed-test artifact was opened, and no commit or push was performed
by this QA session.
