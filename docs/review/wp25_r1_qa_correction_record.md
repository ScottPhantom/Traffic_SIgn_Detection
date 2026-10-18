# M0-WP25-R1 QA correction record

This append-only record preserves the independent-QA finding that caused the initial M0-WP25
package to fail. It authorizes only a one-edge review-decision correction and a corrected R1
reissue. It does not authorize WP26, D-02 approval, group truth, a final `group_id`, a split or
training.

## Initial package and verdict

- Initial package status: `WP25_AWAITING_QA_REVIEW`.
- Initial manifest SHA-256: `1d7b04d6432424297f2e14178dd59936526dec7d6293872fbda0010bb460e5e9`.
- Initial review-notes SHA-256: `b3b97a12577351ef7019f2793a0b7b988f8e7ffddb5929ae7c255a0d7e69a6b8`.
- Initial annotations SHA-256: `990d314a462a2279d9600f2b6b5e2b12c1da73dd7425e7ec07a388d883487cc5`.
- Initial selection SHA-256: `8cb67fb593d610978dcec472f0dbd0dc53b5ae1d416468b908f92ba94320e10f`.
- Initial builder SHA-256: `a1807e834a7f212907efe17f14670e31a3d8d35d90e50ec9b170f58a374b930f`.
- Independent QA verdict: **FAIL**, exactly one P1 finding; P0/P2/P3 findings: zero.
- Technical/integrity evidence remained PASS: 971/971 full tests, 18 historical/current CLI
  verifiers, 46/46 targeted WP25 tests, 18 attack classes, semantic ID-swap protection and
  clean-room 56/56.

## Finding and corrected decision

- Edge: `edge_001358`; batch position 144; canonical WP5 order 1928; initial atlas page 029 slot 4.
- Raw pair: stems `1365` to `1366`, train to train, same dimensions `960x540`, not cross-split.
- Both labels contain exactly one class-5 box:
  - `1365`: center `(0.388021, 0.303704)`, size `(0.036458, 0.055556)`.
  - `1366`: center `(0.406250, 0.313889)`, size `(0.037500, 0.046296)`.
- Proxy evidence: `uncertain`, MAE `12.005787`, dHash `18`, RGB-histogram cosine `0.99375935`.
- QA raw-frame and label review found the same road scene and the same class-5 physical sign,
  viewed after a small forward/right camera motion. The initial `NOT_RELATED` decision and
  discontinuity/non-matching-sign rationale were therefore incorrect.
- R1 correction: `SAME_CAPTURE_CANDIDATE` and `SAME_PHYSICAL_SIGN_CANDIDATE`, confidence `HIGH`.
- Corrected aggregate tally: 241 same, 9 `NOT_RELATED`, 250 `HIGH`.

The initial WP25 package and its sources remain immutable QA-failure evidence. R1 must use the
exact same 250-edge selection and 500-row lineage, preserve stem `0248` and the whole
`proxy_sequence_0050` quarantine, and change only the decision/rationale for `edge_001358`
through `docs/review/wp25_r1_edge_decision_correction.csv`.
