# Legacy successor-test compatibility R1 — independent QA record

Status: `INDEPENDENT_QA_FAIL`

Date: `2026-10-19` (Asia/Ho_Chi_Minh)  
Verdict: **FAIL**  
Findings: `0 P0 / 1 P1 / 0 P2 / 0 P3`  
Boundary: independent QA of pytest collection compatibility only; no implementation/test edit,
training, sealed-test access, upload, download, commit or push.

## Blocking finding

### P1 — A symlinked successor proof is accepted instead of failing closed

`legacy_successor_xfail_reason()` checks `Path.is_file()` and then hashes through `Path.open()`.
Both operations follow symlinks. An independently created temporary repository root with the exact
R1 `conftest.py` and a successor-manifest path symlinked to the real, hash-matching manifest
returned a non-`None` xfail reason. Therefore the collection hook would apply the strict xfail mark
when the exact proof path is a symlink, contrary to the required missing/tampered/nonregular/symlink
fail-closed contract.

Observed attack-harness results:

| Proof state | `legacy_successor_xfail_reason()` |
| --- | --- |
| missing | `None` |
| directory | `None` |
| FIFO | `None` |
| tampered regular file | `None` |
| symlink to the valid pinned manifest | **non-`None` reason — FAIL** |
| exact regular file | non-`None` reason |
| unknown/new nodeid | `None` |

The blocker is at `tests/conftest.py:84-85`. Remediation should reject symlinks explicitly before
hashing; for a race-resistant proof, open with no-follow semantics and verify the opened file
descriptor is a regular file before hashing. Add a regression that builds the exact manifest path
as a symlink and proves both helper and collection behavior remain unmarked.

## Exact mapping and collection evidence

- `LEGACY_SUCCESSOR_XFAILS` contains exactly seven full nodeids. The mapping uses exact dictionary
  lookup; no wildcard, basename or substring matching is present.
- `uv run pytest --collect-only` exited `0`, collected `1,546` tests, and each of the seven mapped
  nodeids occurred exactly once.
- Targeted execution of the four R1 regression tests plus the seven mapped historical tests exited
  `0`: `4 passed, 7 xfailed`. Every xfail reason included its exact successor manifest path and
  pinned SHA-256.
- Source readback confirms every applied marker is `pytest.mark.xfail(..., strict=True)` and an
  unknown nodeid receives no marker.
- Missing, directory, FIFO and tampered proof probes failed closed. Only the symlink probe violated
  the acceptance contract.

## Hash readback

R1 source/test files:

| Path | SHA-256 |
| --- | --- |
| `tests/conftest.py` | `6b1bf9aa7dca4c4b46e5911f3b5dae51f218c49e315473081383be89f35c170f` |
| `tests/test_legacy_successor_compatibility.py` | `9ac9acb7e3949d86e7eced8bc34ab75deca47b153e4725165f16e72922bc5f99` |

Pinned predecessor tests were independently re-hashed and match the R1 roster and their historical
anchors/manifests:

| Path | SHA-256 |
| --- | --- |
| `tests/test_wp26_remaining_edge_review_batch.py` | `99d60ffa317f2f3a566a8f3768fb907b8728240051c3c77f8754c492d12c5d1d` |
| `tests/test_wp27_r1_layout_correction.py` | `f406d316b6068d28f724a4e9f5e19ee2b61364b362cf647902760952f310f36e` |
| `tests/test_wp27_remaining_edge_review_batch.py` | `fe73fc42df74a99ea0b20f24f9622d54f01c1338f3c48150042ab20471e7b9ce` |
| `tests/test_wp28_r1_remaining_edge_review_batch.py` | `094dff55efe3ba86c1b3014339baf3140dd0b49ae7f7ee7242e4c8e42c1052f5` |
| `tests/test_wp28_r2_remaining_edge_review_batch.py` | `cbb2b02424dbe7ee830e5dbef4b2f2029e8b1fc626066db64fd0003926586122` |
| `tests/test_wp28_remaining_edge_review_batch.py` | `cc6cdcbf92da82e8f250368a17cbd0dbae1f8eee3fbdc9b1bebdea501445c5da` |
| `tests/test_wp29_remaining_edge_review_batch.py` | `34a3b9d95014fd27d970069999c3b96430db127051fd076bc22cb47d9a5ceb15` |

The four current successor proof paths are regular, non-symlink files and match their pinned hashes:

| Path | SHA-256 |
| --- | --- |
| `docs/review/generated/wp27_r2_verifier_hardening_manifest.json` | `01e2993888761793943bdfe0ea3c0d96d58c00b1965fc8cabcc402b7fa77b426` |
| `docs/review/generated/wp28_r2_remaining_edge_batch_g_manifest.json` | `63af3feb4caae868837afcca024e53ada31b6f436ffe3d769016d1b6b465fd7b` |
| `docs/review/generated/wp29_remaining_edge_batch_h_manifest.json` | `e7b56820d4dca24e54dc7f58f3e94d929f3d626b9ddb753d0e176c9de5b59a63` |
| `docs/review/generated/wp30_r1_remaining_edge_batch_i_manifest.json` | `6de144e898dcc6b48f6a4629237afe2964595deff7d514a2e85c28b55c45e2fd` |

## Other validation

- `uv run python scripts/run_parallel_checks.py verifiers`: `52/52` PASS, exit `0`.
- `uv run ruff check src tests`: PASS, exit `0`.
- `uv lock --check`: PASS, 168 packages, exit `0`.
- `uv run --project detector ruff check detector`: PASS, exit `0`.
- `uv lock --project detector --check`: PASS, 66 packages, exit `0`.
- `git diff --check`: PASS, exit `0`.
- `graft check .`: graph in sync, exit `0`; deep meaning layer remains unbuilt and was not treated
  as semantic evidence.
- Exact sealed-test access-log path scan found no file. No sealed test was accessed.
- `uv run pytest --lf -q -rxX` was started and showed no failure through approximately 18%, then
  was deliberately stopped after the definitive P1 blocker; exit `130`. It is not claimed as a
  completed full-suite pass. The PM full-run claim was not used as independent evidence.

## Verdict and routing

The current checked-in proof files are regular and the seven intended historical assertions route
as documented, while all package verifiers and static gates above pass. Nevertheless, R1 does not
satisfy its explicit fail-closed symlink requirement. The independent verdict is **FAIL** and the
package remains blocked from QA closure until a successor revision fixes the proof-file check and
passes a new independent review. `PROJECT_MEMORY.md` and `docs/product_roadmap.md` were not advanced
to PASS.
