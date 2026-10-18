# M0-WP3 provenance escalation and fallback dataset report

Status: **READY FOR RE-REVIEW — EVIDENCE ONLY**  
Decision boundary: D-01, D-02, and D-03 remain `PENDING`; Gate 0 remains `BLOCKED`;
`training_authorized=false`. No external party was contacted and no dataset was downloaded.

## Claim vocabulary

- **VERIFIED**: directly observed in a retained local artifact or named public primary record.
- **CANDIDATE**: useful lead, but not sufficient to approve a decision or training use.
- **PROPOSAL**: reviewer-facing option or suggested next action.
- **UNKNOWN**: the inspected evidence does not establish the claim.

## D-01 provenance history

| Evidence | Revision or timestamp | Classification | What it establishes | Strength and limitation |
|---|---|---|---|---|
| Local DATASET01 archive | SHA-256 `052bc980a7206f8ddd1ec2e59098dbd60a42036d3c7f7384ace4fe6416cbaa76` | VERIFIED artifact | The retained archive and extracted source are the current control artifact. Local bytes match the pinned Hugging Face `classes_en.txt`, `labels/0001.txt`, and `images/0001.jpg` probes already recorded by WP1. | Strong byte-level identity probes, but not proof of ownership or license authority. |
| [Hugging Face dataset](https://huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign) | Public record retrieved `2026-10-10T14:39:52Z`; current SHA `d869116a5f89e9ba2aa36b1c0582a39c310e3d0c` | VERIFIED public record | Public dataset metadata identifies `thanhhiepvos/vietnam_traffic_sign`, 3,216 rows, and `cc-by-sa-3.0`. | Strong for the public record; does not establish that the uploader can license every image. |
| [Pinned Hugging Face commit](https://huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign/commit/d869116a5f89e9ba2aa36b1c0582a39c310e3d0c) | `d869116a5f89e9ba2aa36b1c0582a39c310e3d0c`, 2025-04-04 | VERIFIED public record | Upload description states roughly 3,200 images, YOLO XYWH annotations, a linked augmentation repository, a Data Palpating Team creator claim, and CC BY-SA 4.0 usage terms. | Strong for what the commit description claims; the 4.0 statement conflicts with repository metadata and is not independent authority evidence. |
| Hugging Face metadata history | Initial `a81681ca3e1617a758aa47cff2052c46f6d233b1`; metadata commits `8336ab8f6081c32f123a4aa23c8ba7cc240a7ba0`, `b93a4e1ef04af03fab0c25746ae2e4b9795cd0b0`, `b8eed8c00f597e00f504c5a260fe747d6939bdd7` | VERIFIED public record | The initial and later metadata history retain `cc-by-sa-3.0`; later commits add descriptive metadata. | Strong evidence of a persistent metadata value, not proof that 3.0 is legally governing. |
| [Kaggle dataset record](https://www.kaggle.com/datasets/maitam/vietnamese-traffic-signs) and official read-only API | API snapshot retrieved `2026-10-10T14:39:52Z`; versions 1–8 | CANDIDATE upstream lineage | Version 1 is recorded as an initial release by Mai Tam on 2023-11-04; versions 2–8 name Thanh Hiep Vo, ending 2025-04-09. Current record says CC BY-SA 4.0. | Strong public chronology, but no large file download or cross-platform full-file hash comparison was performed; exact derivation from Kaggle to Hugging Face remains UNKNOWN. |
| [Image-Augmentation repository](https://github.com/nguyenmai333/Image-Augmentation) | Latest inspected commit `b45abba`; README SHA-256 `7b8a4c5c22212c063581ff629af2db42f181948e150ff9ca1632e8e640a28d12` | VERIFIED linked tooling; UNKNOWN application lineage | The Hugging Face upload links augmentation tooling that documents blur, noise, brightness, and contrast operations. | The repository has no detected license, and there is no per-image transformation manifest tying it to DATASET01. |

Retained snapshot hashes:

- Hugging Face API payload: `40d312e8750a403b6779a1320ec5400f7c3db47916e09414439dbaf0e04ff0e4`
- Pinned Hugging Face README: `7c9ae7f21d63e913e2b1e1688a7a702d3e548638e463e145af857620bfe66ec8`
- Kaggle API payload: `fa540f5b443c4b9cd1380f2e30e60110280741d35bb2ee15c806404fefa5370b`
- Image-Augmentation README: `7b8a4c5c22212c063581ff629af2db42f181948e150ff9ca1632e8e640a28d12`

Observed API size fields are not treated as content identifiers. The Kaggle endpoints exposed
different byte totals (`793982321` and `793394914`) during inspection, so neither value is used
as a fixed checksum or acceptance fact.

### D-01 result

- **VERIFIED**: the local control identity, pinned Hugging Face revision, and the existence of
  a 3.0-versus-4.0 license metadata conflict.
- **CANDIDATE**: Kaggle is a plausible upstream record.
- **UNKNOWN**: licensor authority, image-level ownership, third-party sources, and which exact
  license version governs each component.
- **PROPOSAL**: a future authorized reviewer may send
  `dataset_owner_outreach_draft.md`; it was not sent in WP3.

## D-02 grouping and split evidence

WP2 produced 589 proxy sequences over 2,280 source images. Those sequences are deterministic
image-similarity aids only, not creator/session/video group truth. WP3 therefore labels every
grouping reviewer record `PROXY_ONLY_NOT_GROUP_TRUTH`, shows source stems, original split,
adjacent-edge proxy metrics, and contact-sheet lineage, but does not create or approve final
group IDs.

- **VERIFIED**: local WP2 proxy outputs and their hashes; the current source has no embedded
  creator/session/group metadata sufficient for a group-safe split.
- **UNKNOWN**: capture session, route, video, photographer, augmentation parent, and creator
  group identifiers.
- **PROPOSAL**: obtain authoritative grouping metadata, fund manual adjudication, or exclude
  this dataset from independent-holdout claims. Selecting among those options remains D-02.

## D-03 taxonomy evidence

The generated atlas covers class IDs 0–51 exactly once. It shows dataset code/name, image and
box support, conflict flags, deterministic source stems, and YOLO bounding-box overlays. Every
row remains `UNAPPROVED`; no label, mapping, or source annotation is changed.

- **VERIFIED**: 52-class source coverage and reviewer lineage.
- **UNKNOWN**: authoritative semantic approval and cross-jurisdiction GTSRB equivalence.
- **PROPOSAL**: a qualified Vietnamese traffic-sign reviewer must decide every mapping row.

## Fallback dataset candidates

All rows below are **CANDIDATE only**. A public license label is not by itself proof that the
publisher controls every image. No candidate was downloaded, selected, merged, or approved.

| Candidate | Primary record | Observed scope | Public license signal | Access/grouping/provenance risks |
|---|---|---|---|---|
| Current DATASET01 control | [Hugging Face](https://huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign) | 3,216 images, 52 classes, YOLO boxes | Conflict: CC BY-SA 3.0 metadata versus 4.0 upload description | Control remains blocked by authority, upstream, and grouping UNKNOWNs. |
| Vietnamese Traffic Sign — hoangfvx | [Roboflow project](https://universe.roboflow.com/hoangfvx/vietnamese-traffic-sign-bihit) | 2,532 images, 75 classes, object detection | CC BY 4.0 project label | Account/download conditions, original creator authority, capture groups, and taxonomy reconciliation remain UNKNOWN. |
| Vietnam traffic sign detection, version 5 | [Roboflow version](https://universe.roboflow.com/vietnam-traffic-sign-detection/vietnam-traffic-sign-detection-2i2j8/dataset/5) | 10,940 generated images; 59 classes; declared 9,540/786/614 split | Public Domain project label | Version includes resize, contrast, shear, exposure, and five outputs per training example; parent grouping and licensor authority remain UNKNOWN. |
| VIA Datasets 1.0 | [Official VIA page](https://via.makerviet.org/vi/docs/4_resources/via-datasets-1-0/) and [release](https://github.com/makerviet/via-datasets/releases/tag/v1.0) | 11,095 images, 6 classes; Goodgame and ICT/FPT Digital Race teams named | No explicit standard dataset license found; repository API reports no license | Narrow taxonomy, exact permissions, image ownership, and grouping metadata require written confirmation. |
| Vietnamese Traffic Signs catalog mirror | [Dataset Ninja repository](https://github.com/dataset-ninja/vietnamese-traffic-signs) | Catalog reports about 1,000 images, 29 classes | Repository explicitly records license as unknown | Source points back to Kaggle; unsuitable as a license-strengthening fallback without upstream proof. |

### Fallback result

The current DATASET01 remains the control artifact because it already has local byte-level
evidence and WP1/WP2 audit history. None of the alternatives is promoted above **CANDIDATE**.
A replacement requires separate provenance, license, download, taxonomy, grouping, and quality
review; public counts cannot substitute for those gates.

## Generated reviewer evidence

- `generated/wp3_provenance_escalation.json`: machine-readable source history and claim status.
- `generated/wp3_fallback_dataset_candidates.csv`: comparison matrix with unresolved risks.
- `generated/wp3_grouping_review_index.csv` and `assets/wp3/grouping/`: proxy-only batches.
- `generated/wp3_taxonomy_reviewer_atlas.csv` and `assets/wp3/taxonomy/`: 52-class atlas.
- `generated/wp3_source_lineage.csv`: retained source path/hash lineage for rendered images.
- `generated/wp3_render_layout_audit.json`: complete rendered text and pixel-bound evidence for
  every grouping/taxonomy row and page.
- `generated/wp3_evidence_manifest.json`: artifact/input sizes and SHA-256 values.

The generator validates source hashes before rendering, wraps text without dropping characters,
and refuses non-proxy grouping rows, non-`UNAPPROVED` taxonomy rows, incomplete class coverage,
or out-of-bounds text. The portable manifest uses logical roots and repository-relative paths;
its verifier checks every artifact, every recorded source input, and explicit WP1/WP2/provenance/
decision/source-preservation controls. It does not write raw data or `decision_status.json`.
