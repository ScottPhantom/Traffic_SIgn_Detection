# D1 corrected validation R9 — QA remediation report

Date: 2026-10-22  
Status: `IMPLEMENTED_AWAITING_INDEPENDENT_QA`

R9 is the append-only successor to QA-failed R8. It retains R8's strict content binding and fixes
the remaining authority gap between the payload the evaluator intended to publish and the bytes
that were actually bound after publication.

## Remediation

- R9 independently serializes the requested payload using the pinned canonical JSON contract.
- Before accepting a binding, it requires the returned SHA-256, byte count, content URI and R9
  locator to match those intended bytes exactly.
- It then reopens the artifact through R8's descriptor-bound consumer and requires both the raw
  bytes and parsed document to equal the intended payload.
- A replacement made after predecessor publication but before binding can therefore be internally
  self-consistent yet still fails because it cannot match the independent intended-payload hash.
- `evaluate()` reconstructs all public metrics and gate fields only from the subsequently consumed,
  intended-payload-authenticated report.

R9 remains validation-only. It does not train, upload, export or access the sealed test. Source QA
PASS may authorize only corrected-validation evaluation of the already registered pilot checkpoint;
it does not authorize retraining, final test evaluation, model acceptance, deployment or publication.
