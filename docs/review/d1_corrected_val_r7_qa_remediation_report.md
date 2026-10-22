# D1 corrected validation R7 — QA remediation report

Date: 2026-10-22  
Status: `IMPLEMENTED_AWAITING_INDEPENDENT_QA`

R7 is an append-only successor to QA-failed R6. R6 published and verified the correct descriptor,
but returned a lexical path without reopening it after publication; an ancestor-directory change
could therefore make the returned path identify different bytes.

R7 retains all R6 behavior and then performs a fresh public-path round trip:

- reopen the run directory through the integration authority and validate all relations;
- open the report once relative to that retained directory and once through the public lexical path;
- require both descriptors to be the same regular, single-link, mode-`0400` inode;
- hash both descriptors against the exact canonical payload;
- validate relations again and recheck the final directory entry before returning success.

R7 remains validation-only, uses train/val authority only, and declares
`sealed_test_accessed=false`. It does not authorize training or sealed-test access.
