# Legacy successor-test compatibility R2 — independent QA record

Status: `INDEPENDENT_QA_PASS`

Date: `2026-10-19` (Asia/Ho_Chi_Minh)  
Reviewer: `Codex independent QA session (did not author R2 and did not act as PM)`  
Baseline commit: `fd9823df6253d2e07d11f6fa2dd29b613710777e`  
Verdict: **PASS**  
Findings: `0 P0 / 0 P1 / 0 P2 / 0 P3`  
Boundary: independent QA of pytest collection compatibility only; no implementation/test/R1-record
edit, training, sealed-test access, upload, download, commit or push.

## Verdict

R2 closes the R1 P1. The proof validator now refuses a final proof symlink that the R1
`Path.is_file()`/`Path.open()` behavior accepted. Independent isolated-filesystem probes also
refused symlinked repository roots and parent components, missing paths, directories, FIFOs,
tampered bytes, same-byte final-file replacement and parent replacement. A regular file with the
exact pinned bytes still produced one `xfail(strict=True)` marker, while an unknown nodeid remained
unmarked.

The compatibility scope remains exact: seven full pytest nodeids, four exact successor-manifest
paths and four exact SHA-256 values. No wildcard, substring, basename or generic test-name masking
was found. This PASS approves only the compatibility routing repair; it does not change package
evidence, model/dataset state, D-05, split/training authorization or sealed-test state.

## Inputs and immutable evidence

| Path | Independent SHA-256 |
| --- | --- |
| `docs/review/legacy_successor_tests_r1_implementation_record.md` | `db8add2ccd06109edb2a9a2fc47100e0c9b7807cfc0278c0a74b769e45725ec9` |
| `docs/review/legacy_successor_tests_r1_independent_qa_record.md` | `83c725afe1bd50d6d53fb7572193b16a766076847f8ac4310a03e93509f735d6` |
| `docs/review/legacy_successor_tests_r2_qa_remediation_report.md` | `c8360ec2d7c307e802a182ea47de6f1ca0ff3fba258192a4eb0bd854fbc8c265` |
| `tests/conftest.py` | `b1263068efb345373a3a202c99718ff18ae29e5879e3bea05f7f772fcc639716` |
| `tests/test_legacy_successor_compatibility.py` | `9ac9acb7e3949d86e7eced8bc34ab75deca47b153e4725165f16e72922bc5f99` |
| `tests/test_legacy_successor_compatibility_r2.py` | `48dc9d431c05bbbea44b8c4fe73ac1587e1a3166b193f1736ffaccf1ff3be430` |

Both immutable R1 records and the R1 regression file match the R2 report. The seven pinned
predecessor tests were re-hashed before and after the full runner and remained unchanged:

| Path | SHA-256 |
| --- | --- |
| `tests/test_wp26_remaining_edge_review_batch.py` | `99d60ffa317f2f3a566a8f3768fb907b8728240051c3c77f8754c492d12c5d1d` |
| `tests/test_wp27_r1_layout_correction.py` | `f406d316b6068d28f724a4e9f5e19ee2b61364b362cf647902760952f310f36e` |
| `tests/test_wp27_remaining_edge_review_batch.py` | `fe73fc42df74a99ea0b20f24f9622d54f01c1338f3c48150042ab20471e7b9ce` |
| `tests/test_wp28_r1_remaining_edge_review_batch.py` | `094dff55efe3ba86c1b3014339baf3140dd0b49ae7f7ee7242e4c8e42c1052f5` |
| `tests/test_wp28_r2_remaining_edge_review_batch.py` | `cbb2b02424dbe7ee830e5dbef4b2f2029e8b1fc626066db64fd0003926586122` |
| `tests/test_wp28_remaining_edge_review_batch.py` | `cc6cdcbf92da82e8f250368a17cbd0dbae1f8eee3fbdc9b1bebdea501445c5da` |
| `tests/test_wp29_remaining_edge_review_batch.py` | `34a3b9d95014fd27d970069999c3b96430db127051fd076bc22cb47d9a5ceb15` |

The current proof paths were independently confirmed as regular files and matched their pins:

| Exact proof | SHA-256 |
| --- | --- |
| `docs/review/generated/wp27_r2_verifier_hardening_manifest.json` | `01e2993888761793943bdfe0ea3c0d96d58c00b1965fc8cabcc402b7fa77b426` |
| `docs/review/generated/wp28_r2_remaining_edge_batch_g_manifest.json` | `63af3feb4caae868837afcca024e53ada31b6f436ffe3d769016d1b6b465fd7b` |
| `docs/review/generated/wp29_remaining_edge_batch_h_manifest.json` | `e7b56820d4dca24e54dc7f58f3e94d929f3d626b9ddb753d0e176c9de5b59a63` |
| `docs/review/generated/wp30_r1_remaining_edge_batch_i_manifest.json` | `6de144e898dcc6b48f6a4629237afe2964595deff7d514a2e85c28b55c45e2fd` |

## Independent adversarial review

The implementation was read back directly. It opens the repository root, each parent and the
final proof with no-follow descriptor semantics; requires real directories and an opened regular
file; hashes only through the final descriptor; compares device/inode/type plus size, mtime and
ctime after hashing; re-checks the named file, each parent binding and the root; catches filesystem
errors by returning no proof; and closes all descriptors in `finally`.

An independent Python harness used only temporary directories and observed:

| Probe | Result |
| --- | --- |
| exact regular pinned proof | reason returned; exactly one strict xfail marker |
| missing proof | refused |
| proof path is a directory | refused |
| proof path is a FIFO | refused without blocking |
| tampered regular proof | refused |
| R1-style final symlink to valid proof | old R1 behavior reproduced acceptance; R2 refused and did not mark |
| parent component symlink to valid tree | refused and did not mark |
| repository-root symlink to valid tree | refused |
| final file replaced by a different inode with identical bytes during hashing | refused |
| parent replaced by a symlink during hashing | refused |
| unknown nodeid with valid proof present | unmarked |
| 100 valid/refused cycles | no `/dev/fd` count growth |

Graft exhaustive search found one `pytest.mark.xfail` application site in `tests/conftest.py`,
where the marker is `strict=True`. `LEGACY_SUCCESSOR_XFAILS` is consumed through exact dictionary
lookup; all other occurrences are the mapping and its two dedicated regression files.

## Execution evidence

- Exact targeted R1 + R2 + seven historical nodeids:
  `12 passed, 7 xfailed`, exit `0`. Every xfail reason named its exact proof path and SHA-256.
- `uv run pytest --collect-only`: `1554 tests collected`, exit `0`; every one of the seven mapped
  full nodeids occurred exactly once.
- `uv run python scripts/run_parallel_checks.py tests`: serial repo-writing stage
  `126 passed`; parallel stage `1421 passed, 7 xfailed`; both exit `0`. The eight warnings are the
  known Starlette `TestClient` deprecation.
- `uv run python scripts/run_parallel_checks.py verifiers`: `52/52 verifiers passed`, exit `0`.
- `uv run ruff check src tests`: PASS.
- `uv lock --check`: PASS, 168 packages resolved.
- `uv run --project detector ruff check detector`: PASS.
- `uv lock --project detector --check`: PASS, 66 packages resolved.
- `git diff --check`: PASS.
- Final `graft check .`: graph in sync. The optional deep meaning layer remains unbuilt and was not
  used as semantic evidence.
- Exact sealed-test log `results/experiments/sealed_test_access_log.jsonl`: absent after QA. No
  sealed test was accessed.

## Closure

Legacy successor-test compatibility R2 is **INDEPENDENT QA PASS with zero findings**. The R1 FAIL
record remains immutable historical evidence. This QA record is the canonical R2 verdict; routing
documents may advance R2 from awaiting QA to PASS without changing any hash-pinned package or test
artifact.
