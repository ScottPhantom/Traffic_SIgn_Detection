# M0-WP23-R1 QA correction record

This append-only record preserves the independent-QA finding that caused the initial M0-WP23
package to fail. It authorizes only a one-edge review-decision correction and a corrected R1
reissue. It does not authorize WP24, D-02 approval, group truth, a final `group_id`, a split or
training.

## Initial package and verdict

- Initial package status: `WP23_AWAITING_QA_REMAINING_EDGE_BATCH_B_PM_PROVISIONAL_REVIEW`.
- Initial manifest SHA-256: `dec19a75bb2def4d29afabe36963f7cdfd474b5c2bdd556e8c40ec198a8f09dd`.
- Initial review-notes SHA-256: `c9159a36096f11c409e1c88ad49d15947ed052db7d5e4fddb310647f47a113c8`.
- Initial annotations SHA-256: `2720ac892a9f0ebe46dc027a722702031a8519aaa856965d560da99d85e2c7be`.
- Initial selection SHA-256: `e6913b2eeba22c990cef393490f8d8cb2caaa6745b2045e6edf64c3a6f9973a6`.
- Independent QA verdict: **FAIL**, exactly one High finding; Critical/Medium/Low findings: zero.
- Technical/integrity evidence remained PASS: 851/851 full tests, 16 historical/current CLI
  verifiers, 45/45 targeted WP23 tests, 18 attack classes and clean-room 56/56.

## Finding and corrected decision

- Edge: `edge_000664`; canonical WP5 order 1476; initial atlas page 039 slot 2.
- Raw pair: stems `0671` to `0672`, train to train, not cross-split.
- Both frames contain the same five annotated class IDs: `7`, `10`, `17`, `19`, `44`.
- Proxy evidence: `strong_candidate`, MAE `6.303241`, dHash `6`, RGB-histogram cosine
  `0.99600903`.
- QA raw-frame review found the same camera advancing slightly within the same scene, with the
  same five annotated signs/objects. The initial `NOT_RELATED` decision and discontinuity
  rationale were therefore incorrect.
- R1 correction: `SAME_CAPTURE_CANDIDATE` and `SAME_PHYSICAL_SIGN_CANDIDATE`, confidence `HIGH`.
- Corrected aggregate tally: 234 same, 16 `NOT_RELATED`, 250 `HIGH`.

The initial WP23 package and its sources remain immutable audit evidence. R1 must use the exact
same 250-edge selection and lineage, with only the decision and rationale for `edge_000664`
changed through `docs/review/wp23_r1_edge_decision_correction.csv`.
