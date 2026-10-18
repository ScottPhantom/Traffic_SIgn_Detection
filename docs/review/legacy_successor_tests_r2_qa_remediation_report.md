# Legacy successor-test compatibility R2 — QA remediation report

Status: `R2_PM_COMPLETE_AWAITING_INDEPENDENT_QA`

Date: `2026-10-19` (Asia/Ho_Chi_Minh)  
R1 independent QA verdict: `INDEPENDENT_QA_FAIL`  
R1 QA record SHA-256: `83c725afe1bd50d6d53fb7572193b16a766076847f8ac4310a03e93509f735d6`  
Boundary: pytest collection compatibility only; no runtime, dataset, model, sealed-test, upload,
download, commit or push action.

## R1 finding preserved

Independent QA found one P1 in R1: `Path.is_file()` and `Path.open()` followed a final-component
symlink. A proof path symlinked to a valid pinned successor manifest therefore produced a reason
and received strict xfail instead of failing closed.

The R1 implementation record and independent-QA record remain byte-identical:

| Preserved R1 record | SHA-256 |
| --- | --- |
| `docs/review/legacy_successor_tests_r1_implementation_record.md` | `db8add2ccd06109edb2a9a2fc47100e0c9b7807cfc0278c0a74b769e45725ec9` |
| `docs/review/legacy_successor_tests_r1_independent_qa_record.md` | `83c725afe1bd50d6d53fb7572193b16a766076847f8ac4310a03e93509f735d6` |

The original R1 regression file also remains byte-identical at
`9ac9acb7e3949d86e7eced8bc34ab75deca47b153e4725165f16e72922bc5f99`. All seven historical
predecessor tests retain the hashes recorded in both R1 records.

## R2 remediation

`tests/conftest.py` now obtains the proof through a descriptor-bound, fail-closed traversal:

1. Require a relative POSIX path without empty, dot or parent components.
2. Require platform `O_NOFOLLOW` and `O_DIRECTORY`; otherwise return no reason.
3. `lstat` and open the repository root as a real directory with no-follow semantics.
4. Walk every parent component with `openat`-style `os.open(..., dir_fd=...)`,
   `O_DIRECTORY | O_NOFOLLOW`, and bind each opened directory with `fstat` plus no-follow `stat`.
5. Open the final component with `O_NOFOLLOW | O_NONBLOCK`, require `S_ISREG(fstat.mode)`, and hash
   only through that descriptor. `O_NONBLOCK` ensures a FIFO probe cannot hang collection.
6. After hashing, compare descriptor state and the no-follow named file state, including device,
   inode, file type, size, mtime and ctime.
7. Re-check every parent binding and the repository root after hashing. A final-file or parent
   replacement during the read returns no reason.
8. Close every descriptor on every return path.

The collection hook delegates to `apply_legacy_successor_xfail(item, repo_root)`. This keeps the
production hook exact while allowing independent tests to verify both helper and marker behavior
against isolated filesystem layouts.

## R2 attack coverage

New file `tests/test_legacy_successor_compatibility_r2.py` covers:

- exact regular pinned proof → reason plus one `strict=True` xfail marker;
- missing path, directory, FIFO and tampered regular file → no reason;
- final symlink to the valid manifest → no reason and no marker;
- parent-directory symlink to a valid proof tree → no reason and no marker;
- symlinked repository root → no reason;
- replacement by a different inode containing the same valid bytes during descriptor hashing →
  no reason;
- parent directory replaced by a symlink during hashing → no reason;
- unknown nodeid with a valid proof → no marker.

R1's four mapping/pin tests remain unchanged and continue to prove the exact seven-nodeid roster,
successor hashes and all seven predecessor hashes.

## PM verification

- Targeted R1 + R2 + seven historical nodes: `12 passed, 7 xfailed`, exit `0`.
- Collection: `1554 tests collected`; the exact seven mapped historical nodeids occur once each.
- Full root runner: serial repo writers `126 passed`; parallel remainder
  `1421 passed, 7 xfailed`; both stages exit `0` (`1547 passed, 7 xfailed` total).
- Package verifiers: `52/52` PASS.
- Root Ruff (`src tests`), root lock (168 packages), detector Ruff, detector lock (66 packages) and
  `git diff --check`: PASS.
- Exact sealed-test access-log path remains absent; no sealed test was opened.

## QA request

Independent QA should reproduce the R1 symlink exploit and confirm R2 rejects it, independently
exercise final/parent/root symlinks and at least one replacement-during-read probe, inspect the
descriptor cleanup and post-hash binding checks, re-hash both immutable R1 records plus the seven
predecessor tests, then run targeted and full gates. R2 remains
`R2_PM_COMPLETE_AWAITING_INDEPENDENT_QA` until that verdict is recorded.
