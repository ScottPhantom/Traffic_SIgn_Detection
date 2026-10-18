# Local-only evidence artifacts

The public Git repository intentionally excludes `docs/review/assets/` and the two source PDFs in
`references/qcvn41_2024/`.

`docs/review/assets/` contains review renders derived from DATASET01 images. D-01 permits project
research use but does not permit redistribution of the raw images or labels while ownership is
unresolved. Any redistributed derivative must be attributed and licensed CC-BY-SA 4.0. To avoid
accidentally publishing image content, the public checkpoint versions the builders, reports,
annotations, manifests, hashes and source-provenance records, while the rendered pixels remain in
the owner's local project checkout.

The QCVN PDFs are retained locally as exact-hash source evidence. Their provenance metadata,
evidence index and expected hashes remain versioned under `references/qcvn41_2024/`.

This boundary means a fresh public clone does not contain the complete visual-review evidence
store. Reproduction requires separately obtaining the authorized sources, verifying their pinned
hashes, and regenerating the local-only artifacts. It does not weaken or replace the repository's
fail-closed manifests.
