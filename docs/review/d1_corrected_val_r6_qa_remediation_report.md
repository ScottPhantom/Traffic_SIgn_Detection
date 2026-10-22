# D1 corrected validation R6 — QA remediation report

Date: 2026-10-22  
Status: `IMPLEMENTED_AWAITING_INDEPENDENT_QA`

## Scope

R6 is an append-only successor to QA-failed R5. It does not open or export the sealed test and it
does not authorize a new training run.

## R5 finding addressed

R5 verified a named OS-temp candidate and then passed that pathname to `renameatx_np`. Independent
QA demonstrated that the pathname could be truncated or hardlinked after the final descriptor/hash
check but before rename, allowing different or alias-mutable bytes to be published.

## R6 design

- removes named staging and rename publication entirely;
- reserves the final report name directly through retained run-directory authority with
  `O_CREAT | O_EXCL | O_NOFOLLOW` and mode `000`;
- writes, hashes and verifies the same retained file descriptor;
- checks the final pathname and descriptor are the same regular inode with exactly one link;
- validates the retained directory relations before reservation and before publication;
- uses `fchmod(..., 0400)` as the publication event only after all checks pass;
- on any failure, never unlinks any pathname and forces the owned descriptor back to mode `000`;
- treats post-publication close errors as non-reversing cleanup failures.

## Required independent attacks

- pre-existing regular file, symlink and hardlink final-name collisions;
- content mutation and external hardlink creation during the write/verify window;
- final path replacement and retained-directory relation changes;
- post-publication descriptor-close failure;
- full predecessor snapshot/path-swap suite and sealed-test guards.

R5 source, tests, remediation report and completed QA record are SHA-256 pinned before R6 may run.
