# D1 corrected validation R8 — QA remediation report

Date: 2026-10-22  
Status: `IMPLEMENTED_AWAITING_INDEPENDENT_QA`

R8 is an append-only successor to QA-failed R7. It does not claim that a mutable filesystem path
is durable evidence.

## Changed authority contract

- `_safe_write_report()` returns a `ReportBinding`, never a `Path`.
- The authoritative identifier is `sha256:<digest>` with exact byte count, device/inode, mode and
  link-count binding.
- The filename is explicitly marked `REOPEN_AND_VERIFY_BEFORE_USE`; it is only a locator.
- `consume_report()` reopens the locator under retained directory authority, validates the strict
  binding, reads and hashes through that same descriptor, checks sealed-test policy, and returns
  the parsed payload.
- `evaluate()` ignores inherited metric fields, consumes the newly published report through the
  verified descriptor and reconstructs its public result from that consumed payload.
- A locator replacement after publication therefore causes the next consumption to fail closed;
  it cannot silently change the metrics returned by R8.

R8 remains validation-only. It neither trains nor accesses, materializes or evaluates the sealed
test. A source QA PASS would authorize only corrected-validation evaluation of the registered pilot
checkpoint, not a new training run or final test evaluation.
