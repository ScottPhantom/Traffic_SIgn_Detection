#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and verify M0-WP36-R1: the G0.7 split rebuilt with the owner's ranking applied literally.

WP36 passed independent QA with one P2 and three P3 (`docs/review/wp36_independent_qa_record.md`).
WP36 stays byte-identical and pinned. R1, per `docs/review/g07_owner_decision_r1_record.md`:

- P2-1: the objective is (class requirements, ≥2 test groups, ratio band, ratio, box balance), so
  test-group depth now outranks the ±3-point band.
- P3-1: ratio terms use usable frames (quarantined negatives excluded), as the report shows.
- P3-2: `check-candidate` rejects quarantined stems, a misplaced background frame, and any list
  whose SHA-256 differs from the R1 manifest; the M1 loader must use it.
- P3-3: the D-02 candidate check runs in a temporary directory, never inside the repository.

Inputs, hard rules, seed and search are reused from WP36 unchanged.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("wp36_r1_base", Path(__file__).with_name("build_wp36_group_split.py"))
assert _SPEC is not None and _SPEC.loader is not None
wp36 = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = wp36
_SPEC.loader.exec_module(wp36)

PACKAGE_STATUS = "WP36_R1_AWAITING_QA_REVIEW"
BOUNDARY = "G07_SPLIT_PROPOSAL_NOT_OWNER_ACCEPTED_NO_TRAINING"
SPLITS = wp36.SPLITS
PINNED_SOURCES = {
    "scripts/build_wp36_group_split.py": "5fd5b4c189d0815f794e46bd41f1cef2f34289a3e7acad9388cfb45a50eb2c4a",
    "tests/test_wp36_group_split.py": "270b9d399c03d9fa38db9595704c2fc4d4cc688b7306fdd5e8cc6bd8ca3e6e53",
    "docs/review/wp36_group_split_report.md": "8e04ab229c64edd46b31328969b644234df2a2bf42ab94c01509de71f246ea87",
    "docs/review/generated/wp36_split_candidate.json": "964b447715aa4c95facf05dc50999539417b65dc1e4dc7129cd2caad6b64be04",
    "docs/review/generated/wp36_split_frames.csv": "1bbc0218af9085e4749965138175c61ff7cbafdae8bd3878d72fb685fbbef97d",
    "docs/review/generated/wp36_split_groups.csv": "27f81e6c317dc3396c89cb3d0d5edfe3c24c8272d71f2215cbf7e2fb3ae34530",
    "docs/review/generated/wp36_split_manifest.json": "1012b223f7f1d9ffdd153b6c980ba7f2252c8e41a301ec9b87a877457fd0cc1e",
    "docs/review/generated/wp36_class_coverage.csv": "00216563b1c78d94070ea166287a016ea99f5803d02fd4fcf423a868286015e1",
    "docs/review/wp36_independent_qa_record.md": "116f85c0794bf7ea6de62a54cf48294c19e5302b19a4d3e5fbb241f9d34f551d",
    "docs/review/g07_owner_decision_record.md": "5cab1825f11cdd63ed2cd81576fe01a00bd21d2240ab0def11178771bc0afc0b",
    "docs/review/g07_owner_decision_r1_record.md": "ddeae6a55cc819d3f97d68f425e93c20d0051f5e6f3d218f78f5f32fa2a20a29",
}
GENERATED = wp36.GENERATED
FRAMES_PATH = GENERATED / "wp36_r1_split_frames.csv"
GROUPS_PATH = GENERATED / "wp36_r1_split_groups.csv"
COVERAGE_PATH = GENERATED / "wp36_r1_class_coverage.csv"
CANDIDATE_PATH = GENERATED / "wp36_r1_split_candidate.json"
MANIFEST_PATH = GENERATED / "wp36_r1_split_manifest.json"
REPORT_PATH = Path("docs/review/wp36_r1_group_split_report.md")


def list_sha256(stems: list[str]) -> str:
    return wp36.sha256_bytes("\n".join(sorted(stems)).encode("utf-8"))


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        if wp36.sha256_bytes((repo_root / relative).read_bytes()) != expected:
            raise ValueError(f"pinned source changed: {relative}")
    wp36.verify_pins(repo_root)


class R1Scorer(wp36.Scorer):
    """WP36 scorer with usable-frame sizes (P3-1) and the owner's literal ranking (P2-1)."""

    def __init__(self, data: dict[str, Any], forced: set[str]) -> None:
        super().__init__(data, forced)
        quarantined = {stem for stem, use in data["negatives"].items() if use == "QUARANTINE_UNTIL_RELABELLED"}
        self.sizes = Counter(row["group_id"] for row in data["registry"] if row["stem"] not in quarantined)
        for group in data["sizes"]:
            self.sizes.setdefault(group, 0)
        self.total = sum(self.sizes.values())

    def score(self, assignment: dict[str, str]) -> tuple[float, ...]:
        unmet, band, deep, ratio, balance = super().score(assignment)
        return (unmet, deep, band, ratio, balance)


def render(repo_root: Path) -> dict[Path, bytes]:
    verify_pins(repo_root)
    data = wp36.load_inputs(repo_root)
    forced = wp36.forced_train(data)
    free = sorted(set(data["sizes"]) - forced)
    scorer = R1Scorer(data, forced)
    assignment = wp36.search(scorer, free)
    group_split = {g: scorer.split_of(assignment, g) for g in sorted(data["sizes"])}

    frames = []
    for row in sorted(data["registry"], key=lambda r: r["stem"]):
        split = group_split[row["group_id"]]
        use = {"DETECTOR_BACKGROUND": "BACKGROUND", "QUARANTINE_UNTIL_RELABELLED": "QUARANTINED"}.get(
            data["negatives"].get(row["stem"], ""), split.upper()
        )
        frames.append({"stem": row["stem"], "group_id": row["group_id"], "split": split, "use": use})
    errors = wp36.check_rules(data, forced, group_split, frames)
    if errors:
        raise ValueError(f"WP36-R1 hard rule violations: {errors}")

    needs = wp36.requirements(data["decision"])
    groups_rows = []
    for group in sorted(data["sizes"]):
        classes = sorted((k for k, c in data["class_groups"].items() if group in c), key=lambda k: (len(k), k))
        groups_rows.append({
            "group_id": group, "frames": data["sizes"][group], "usable_frames": scorer.sizes[group],
            "boxes": scorer.box_total[group], "split": group_split[group],
            "assignment": "FORCED_TRAIN" if group in forced else "SEARCH", "classes": " ".join(classes),
        })
    coverage = []
    for key in sorted(data["class_groups"], key=lambda k: (int(k.split(":")[0]), k)):
        counts = data["class_groups"][key]
        per = {s: [g for g in sorted(counts) if group_split[g] == s] for s in SPLITS}
        reached = {s for s in SPLITS if per[s]}
        coverage.append({
            "derived_key": key, "d04_decision": data["decision"][key],
            "required_splits": " ".join(s for s in SPLITS if s in needs[key]),
            **{f"{s}_groups": len(per[s]) for s in SPLITS},
            **{f"{s}_boxes": sum(counts[g] for g in per[s]) for s in SPLITS},
            "requirement_met": needs[key] <= reached,
            "usable_for_tuning": "val" in reached and needs[key] == frozenset(SPLITS),
        })

    split_stems = {s: [r["stem"] for r in frames if r["split"] == s and r["use"] != "QUARANTINED"] for s in SPLITS}
    candidate_bytes = (json.dumps({"splits": split_stems}, indent=1, sort_keys=True) + "\n").encode("utf-8")
    d02 = wp36._load_d02(repo_root)
    with tempfile.TemporaryDirectory() as scratch:
        probe = Path(scratch) / "candidate.json"
        probe.write_bytes(candidate_bytes)
        check = d02.check_candidate(repo_root, probe)
    if not check["accepted"]:
        raise ValueError(f"D-02 check-candidate rejected the split: {check['errors']}")

    usable = {s: len(split_stems[s]) for s in SPLITS}
    total = sum(usable.values())
    unmet = [row["derived_key"] for row in coverage if not row["requirement_met"]]
    score = scorer.score(assignment)
    artifacts: dict[Path, bytes] = {
        FRAMES_PATH: wp36.csv_bytes(["stem", "group_id", "split", "use"], frames),
        GROUPS_PATH: wp36.csv_bytes(list(groups_rows[0]), groups_rows),
        COVERAGE_PATH: wp36.csv_bytes(list(coverage[0]), coverage),
        CANDIDATE_PATH: candidate_bytes,
    }
    manifest = {
        "package": "M0-WP36-R1", "status": PACKAGE_STATUS, "boundary": BOUNDARY,
        "supersedes": "M0-WP36 (QA PASS with P2-1; kept byte-identical)",
        "seed": wp36.SEED, "restarts": wp36.RESTARTS, "target": wp36.TARGET, "tolerance": wp36.TOLERANCE,
        "objective_order": ["unmet_requirements", "classes_with_2plus_test_groups", "band_violation", "ratio_deviation", "box_balance_deviation"],
        "objective": {"unmet_requirements": -score[0], "classes_with_2plus_test_groups": score[1], "band_violation": -score[2],
                      "ratio_deviation": -score[3], "box_balance_deviation": -score[4]},
        "groups": {s: sum(1 for g in group_split.values() if g == s) for s in SPLITS},
        "forced_train_groups": len(forced),
        "usable_frames": usable,
        "usable_share": {s: round(usable[s] / total, 4) for s in SPLITS},
        "excluded": {"quarantined_negatives": sum(1 for r in frames if r["use"] == "QUARANTINED"), "stem_0248": "absent"},
        "background_stems": sorted(r["stem"] for r in frames if r["use"] == "BACKGROUND"),
        "unmet_class_requirements": unmet,
        "test_seal_sha256": list_sha256(split_stems["test"]),
        "split_list_sha256": {s: list_sha256(split_stems[s]) for s in SPLITS},
        "split_list_hash_rule": "sha256 of the sorted stems joined by '\\n', no trailing newline",
        "pinned_sources": PINNED_SOURCES,
        "artifacts": {str(path): wp36.sha256_bytes(payload) for path, payload in sorted(artifacts.items())},
        "split_authorized": False, "training_authorized": False,
    }
    artifacts[MANIFEST_PATH] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    artifacts[REPORT_PATH] = render_report(manifest, coverage, groups_rows).encode("utf-8")
    return artifacts


def render_report(manifest: dict[str, Any], coverage: list[dict[str, Any]], groups: list[dict[str, Any]]) -> str:
    usable, share = manifest["usable_frames"], manifest["usable_share"]
    split_table = "\n".join(f"| {s} | {manifest['groups'][s]} | {usable[s]} | {share[s]:.1%} |" for s in SPLITS)
    unmet = manifest["unmet_class_requirements"]
    no_tuning = [r["derived_key"] for r in coverage if r["required_splits"] != "train" and not r["usable_for_tuning"]]
    train_only = [r["derived_key"] for r in coverage if r["required_splits"] == "train"]
    single_test = [r["derived_key"] for r in coverage if r["d04_decision"] == "TRAIN_VAL_TEST" and r["test_groups"] == 1]
    rows = "\n".join(
        f"| {r['derived_key']} | {r['d04_decision']} | {r['required_splits']} | {r['train_groups']}/{r['val_groups']}/{r['test_groups']} | "
        f"{r['train_boxes']}/{r['val_boxes']}/{r['test_boxes']} | {'yes' if r['requirement_met'] else '**NO**'} |"
        for r in coverage
    )
    group_lines = "\n".join(
        f"| {g['group_id']} | {g['usable_frames']} | {g['split']} | {g['assignment']} | {g['classes']} |" for g in groups
    )
    objective = manifest["objective"]
    return f"""# M0-WP36-R1 — G0.7 group-aware split (owner ranking applied literally)

Status: `{PACKAGE_STATUS}`
Boundary: `{BOUNDARY}`

Corrects WP36 (`docs/review/wp36_independent_qa_record.md`: PASS with 1 P2, 3 P3) under the owner's
clarification `docs/review/g07_owner_decision_r1_record.md`. WP36 stays byte-identical. Nothing
here authorizes training; the split becomes the G0.7 split only after independent QA and owner
acceptance.

## What changed from WP36

- **P2-1:** objective order is now {' > '.join(manifest['objective_order'])}. Two or more test groups
  per `TRAIN_VAL_TEST` class now outranks the ±3-point band, as the G0.7 record lists.
- **P3-1:** ratio terms count usable frames (the 24 quarantined negatives excluded).
- **P3-2:** `check-candidate` in this builder rejects quarantined stems, a background frame outside
  train, and any list whose SHA-256 differs from `split_list_sha256`. The M1 loader must call it.
- **P3-3:** the D-02 candidate check runs in a temporary directory.

## Splits (usable frames)

| Split | Groups | Frames | Share |
| --- | --- | --- | --- |
{split_table}

- Objective reached: {objective['classes_with_2plus_test_groups']} `TRAIN_VAL_TEST` classes with ≥2 test groups;
  ratio band violation {objective['band_violation']:.3f} (the test split is above the 15 ± 3 % target,
  accepted by the owner in the R1 record).
- {manifest['forced_train_groups']} groups are forced into train; {manifest['excluded']['quarantined_negatives']} quarantined
  negatives are excluded; background frame(s): {', '.join(manifest['background_stems'])} (train).
- **Test seal:** `{manifest['test_seal_sha256']}` ({manifest['split_list_hash_rule']}). Any change to
  the test list needs a new append-only split version.

## Class coverage

- Requirements not met: {', '.join(unmet) or 'none'}. Class 22 and class 25 both depend on group
  D02-C0032; the owner accepted that 22 loses validation so that 25 keeps a test group.
- Not usable for model selection or threshold tuning (no validation group): {', '.join(no_tuning)}.
- Train only (no sealed test, accuracy unknown): {', '.join(train_only)}.
- `TRAIN_VAL_TEST` classes with a single test group: {', '.join(single_test) or 'none'}.

| Class | D-04 | Required | Groups train/val/test | Boxes train/val/test | Met |
| --- | --- | --- | --- | --- | --- |
{rows}

## Groups

| Group | Usable frames | Split | Assignment | Classes |
| --- | --- | --- | --- | --- |
{group_lines}

## Known limits

- D-02 groups come from AI visual review; the same physical sign can still appear in two groups,
  so test scores may be optimistic.
- Train-only classes have no sealed test; their accuracy is unknown until real independent images exist.
- Validation is small; per-class validation counts are thin, so tuning must use pooled metrics.
"""


def check_candidate(repo_root: Path, candidate: Path) -> dict[str, Any]:
    """Loader guard (QA P3-2): D-02 rules plus WP36-R1 uses and list hashes."""
    result = verify(repo_root)
    if not result["valid"]:
        return {"accepted": False, "errors": ["WP36-R1 package invalid", *result["errors"]]}
    splits = json.loads(candidate.read_text(encoding="utf-8")).get("splits")
    if not isinstance(splits, dict) or set(splits) != set(SPLITS):
        return {"accepted": False, "errors": ["candidate must have exactly train, val and test lists"]}
    errors = wp36._load_d02(repo_root).check_candidate(repo_root, candidate)["errors"]
    use = {row["stem"]: row for row in wp36.read_csv(repo_root / FRAMES_PATH)}
    manifest = json.loads((repo_root / MANIFEST_PATH).read_text(encoding="utf-8"))
    for split, stems in splits.items():
        for stem in stems:
            row = use.get(stem)
            if row and row["use"] == "QUARANTINED":
                errors.append(f"quarantined stem {stem} in split {split}")
            elif row and row["use"] == "BACKGROUND" and split != "train":
                errors.append(f"background stem {stem} outside train")
        if list_sha256(stems) != manifest["split_list_sha256"][split]:
            errors.append(f"{split} list differs from the WP36-R1 manifest")
    return {"accepted": not errors, "errors": sorted(set(errors))[:50]}


def build(repo_root: Path) -> dict[str, Any]:
    artifacts = render(repo_root)
    for path, payload in artifacts.items():
        (repo_root / path).parent.mkdir(parents=True, exist_ok=True)
        (repo_root / path).write_bytes(payload)
    return {"status": PACKAGE_STATUS, "artifacts": len(artifacts)}


def verify(repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    artifacts: dict[Path, bytes] = {}
    try:
        artifacts = render(repo_root)
        for path, payload in artifacts.items():
            if not (repo_root / path).is_file() or (repo_root / path).read_bytes() != payload:
                errors.append(f"artifact differs: {path}")
    except (ValueError, OSError, KeyError) as error:
        errors.append(str(error))
    return {"status": PACKAGE_STATUS, "valid": not errors, "artifact_count": len(artifacts), "errors": errors}


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify", "check-candidate"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    commands.choices["check-candidate"].add_argument("--candidate", type=Path, required=True)
    args = root.parse_args(argv)
    repo_root = args.repo_root.resolve()
    if args.command == "build":
        result, ok = build(repo_root), True
    elif args.command == "verify":
        result = verify(repo_root)
        ok = result["valid"]
    else:
        result = check_candidate(repo_root, args.candidate)
        ok = result["accepted"]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
