# D1 Colab operator guide independent QA record

Status: `QA_FAIL_D1_COLAB_OPERATOR_GUIDE`
Reviewer: `Codex independent QA session (did not author the operator guide)`
Reviewed at: `2026-10-19T05:39:24+07:00`
Boundary: `DOCUMENT_AND_LOCAL_CONTROL_QA_ONLY_NO_COLAB_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH`
Reviewed checkpoint: `3a72bf64893221cca25987bf49a84df0fef4484f` plus the current uncommitted guide/routing worktree

## Verdict

- **FAIL — 0 Critical, 1 High, 1 Medium, 1 Low.**
- The guide correctly transcribes the Drive path, bundle names, local-source sizes/hashes, bound
  commit, notebook defaults, required workflow steps, SQLite schema, five-file state-directory
  readback, canonical eight-file result roster, standalone verifier command, seed order and
  train/validation-only boundary.
- Mechanical gates are green, but those gates do not close the operator-facing trust-chain and
  authorization findings below.
- Per the delegated boundary, this review does not edit the guide, notebook, runner, verifier,
  tests, project memory or roadmap, and it does not mark the guide PASS.

## Findings

### QA-D1-OP-GUIDE-001 — High — the guide does not authenticate the Drive bundle before the notebook uses it to select executable code

The guide lists the expected archive and sidecar digests, then tells the Owner to open the bound
notebook and run all cells. It never instructs the Owner to compute and assert the size and SHA-256
of the two files actually mounted from Drive. This matters because notebook cell 3 opens the
archive, reads `repo_git_commit` from its embedded manifest, clones that revision and checks it out
**before** `run_d1_colab.py` performs the governed bundle verification. The sidecar is not read by
the notebook at all. A substituted, self-consistent archive can therefore influence which code is
checked out and executed before the runner reaches its archive checks.

The wording `Thông tin gói đã được QA` also overstates the external evidence. The upload record and
its independent QA explicitly distinguish local cryptographic verification from Google Drive UI
readback: the Drive copy was not downloaded and re-hashed. The preserved local source files do
match the listed values, but that does not establish the current mounted Drive bytes.

Required remediation: before any archive manifest is read or any repository revision is checked
out, the guide must provide a fail-closed preflight that hashes the mounted archive and sidecar and
asserts the exact expected byte sizes and digests. It must say to stop on either mismatch and must
describe the prior QA accurately as local-source cryptographic evidence plus external filename,
displayed-size and privacy UI readback—not cryptographic verification of the Drive copy.

### QA-D1-OP-GUIDE-002 — Medium — OOM recovery contradicts the documented pilot configuration

The failure table tells the operator to retry an OOM smoke with `BATCH=4`, but the pilot section
then unconditionally says to keep `BATCH=8`. If batch 8 exhausted memory in the one-epoch smoke,
restoring it for the 100-epoch pilot is not a credible recovery path. It also makes the reviewed
smoke configuration differ from the instructed pilot configuration without an explicit protocol
decision.

Required remediation: treat the batch change as a configuration change requiring smoke-package
review before promotion. The review must decide and record the batch used for the pilot and the
three final seeds; the guide must not silently reset it to 8. All final-seed runs used for a
comparison must use the same locked training configuration.

### QA-D1-OP-GUIDE-003 — Low — gate recalibration omits the required new Owner approval

The post-pilot checklist says review may decide to recalibrate the gate once, but D-05 permits that
only when PM proposes the new level and the Owner gives a new approval before the sealed test is
opened. Omitting the approval condition can be read as delegating an authority the operator/QA does
not have.

Required remediation: state explicitly that any one-time gate recalibration requires a new Owner
decision recorded before sealed-test access; review alone cannot lower or replace the approved
gate.

## Reviewed byte pins and evidence

| Item | Readback |
| --- | --- |
| Operator guide | `bcafdca46feb272d8b21db945816f0d9bfe0ec8a9a28a7f96c823e9034256fae` |
| Notebook | `4f7e5df089efaa01be8045c232dd02cb1a4a44e97a399530778c6e639b4babca` |
| Runner | `0d04c869d0181c68a4d60a93b05967c4db5b5e31cfc44cf653bfcbd43f225786` |
| Standalone verifier | `678de7f84e54c568dd3d7001873541a6226eeb2da0e5b2f725fdcde49fb994ab` |
| D-05 Owner decision | `c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702` |
| Preserved local bundle | 766,226,824 bytes; `eb5226e36cf619e271132794c97fd633f7528d72e25463356eb165f36f43e191` |
| Preserved local sidecar | 1,499,866 bytes; `2c43d5fdff3de32af3fa3b9621f7f73cf1646c2f51801c5844ae89e8f4ae8d3b` |

The notebook at bound commit `1842a1b77e6448a54fec486937f4c0f0e6ff19f5` matches the current
notebook byte-for-byte. Its seven cells are unexecuted and have no outputs. The current runner and
verifier match the M1-Colab-R3 QA pins.

## Proportional validation

| Gate | Result |
| --- | --- |
| `tests/test_m1_colab.py` | PASS, **22/22** |
| Complete detector pytest | PASS, **79/79** |
| Targeted root Ruff | PASS |
| Detector Ruff (`m1 tests colab`) | PASS |
| Root lock | PASS, 168 packages resolved |
| Detector lock | PASS, 66 packages resolved |
| Notebook JSON parse | PASS; 7 unexecuted cells, no outputs |
| Preserved local archive/sidecar SHA-256 readback | PASS; both match the upload record |
| `git diff --check` | PASS |
| Graft freshness | PASS; wiring graph synchronized |

No Colab cell ran, no Google Drive object was changed or downloaded, no model was trained, no
sealed-test artifact was opened, and no commit, push, upload, deployment or publication occurred.
