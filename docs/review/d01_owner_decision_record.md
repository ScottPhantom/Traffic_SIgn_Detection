# D-01 owner decision — provenance and license

Status: `OWNER_APPROVED_RISK_ACCEPTED`
Decision date: `2026-10-17` (`Asia/Ho_Chi_Minh`)
Selected option: `D01-RISK_ACCEPTED_CC_BY_SA_STRICTEST_TERMS`

The owner chose to accept the license risk for DATASET01 instead of waiting for the dataset
author. Source candidate: `huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign@d869116`, archive SHA-256 `052bc980a7206f8ddd1ec2e59098dbd60a42036d3c7f7384ace4fe6416cbaa76`. The repository
metadata declares CC-BY-SA 3.0 and the card prose declares CC-BY-SA 4.0; image ownership is unknown
(`docs/review/wp3_provenance_and_fallback_report.md`). The decision applies the stricter,
compatible obligations of both versions.

## Conditions

1. Use DATASET01 for this project's research, coursework and simulation only.
2. Attribute the source in every report, dataset card, model card and release: huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign@d869116, CC-BY-SA, with the archive SHA-256.
3. Share-alike: any redistributed derivative of the images or labels (crops, relabels, splits) is released only under CC-BY-SA 4.0, which satisfies both declared versions.
4. Do not redistribute the raw images or labels outside the project until ownership is clarified.
5. Treat trained model weights as possibly subject to share-alike; attribute the dataset in any model release and re-check before any public or commercial release.
6. Re-open D-01 immediately if the author answers, the source changes, or a takedown or ownership claim is received.

## Residual risks accepted by the owner

- License version conflict (3.0 metadata vs 4.0 card prose) is unresolved by the author.
- Ownership of the original images and the author's authority to license them are unknown.
- Share-alike scope for trained model weights is legally uncertain.

## Governance

G0.1 is satisfied by owner risk acceptance, not by author confirmation. Gate 0 remains BLOCKED
because D-03, D-04 and D-05 are pending and no group-aware split (G0.7) exists yet. Public
redistribution, split generation and training are not authorized by this record.
