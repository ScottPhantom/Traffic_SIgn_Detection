# D1 cascade detector dataset R2 QA remediation report

Status: `AWAITING_INDEPENDENT_QA`
Date: `2026-10-19` (`Asia/Ho_Chi_Minh`)
Supersedes: `D1 cascade detector dataset R1` (QA FAIL: 0 Critical, 1 High)

## R1 finding reproduced

R1 called `.resolve()` on CLI `--out` before passing the path to the exporter and verifier. This
removed the evidence that the lexical path was a symlink. Independent QA confirmed that the real
CLI wrote all `8177` artifacts through an output-root symlink into an external directory and then
reported success.

## R2 remediation

- `absolute_lexical()` makes a path absolute and normalizes `..` without resolving symlinks.
- `reject_symlink_components()` walks every existing component with `os.lstat()` and rejects any
  symlink before output I/O.
- The CLI preserves the lexical `--out` path for both `export` and `verify-export`.
- Guards run on the output root, every existing ancestor, `images`, `labels`, split directories
  and file parents.
- CLI errors are structured and return code 1 instead of writing through the path.
- A real subprocess regression covers output-root, parent and nested-directory symlinks and checks
  that every external target remains empty. It also covers `verify-export` through a root symlink.

The source-data paths remain resolved because they are read-only inputs; the finding concerned the
writable output path.

## PM validation

- Targeted Ruff: PASS.
- Cascade suite: 12/12 PASS.
- Real CLI root/parent/nested symlink regressions: PASS; external targets remained empty.
- Materialized export verifier: PASS.
- `d1-cascade` package verifier: PASS.
- `git diff --check`: PASS.

R2 is not PASS until a separate QA session repeats the original exploit and the broader
adversarial matrix.
