# D1 corrected validation R10 — live-compatibility remediation report

Date: 2026-10-22  
Status: `IMPLEMENTED_AWAITING_INDEPENDENT_QA`

R10 is an append-only successor to R9 after the first real corrected-validation attempt failed
closed following inference. It preserves R9's exact intended canonical-byte authority.

## Remediation

- The intended payload is still independently serialized to canonical JSON before publication.
- Binding SHA-256, byte count, content URI and locator must still match those exact bytes.
- Descriptor-consumed raw bytes must still equal the independently computed intended bytes.
- The redundant parsed-document check now compares the consumed document with
  `json.loads(canonical_intended_bytes)`, so JSON-normalized tuple/list and object-key forms cannot
  cause a false failure.
- R10 retains R8's strict descriptor, inode, mode, link-count, locator, schema and sealed-safe
  checks and R9's substitution defence.

The failed R9 report remains preserved and is not promoted. R10 remains validation-only; it does
not train, upload, export or access the sealed test. Independent QA PASS is required before a new
R10 evaluation attempt on the registered pilot checkpoint.
