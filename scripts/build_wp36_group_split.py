#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and verify M0-WP36: the G0.7 group-aware train/val/test split of DATASET01.

Rules come from the owner's G0.7 decision (`docs/review/g07_owner_decision_record.md`, option A),
D-02 groups, the WP33 derived labels and D-04 parts 1 and 2. Every D-02 group goes to exactly one
split. Groups holding a class that must be trained from a single group are forced into train; the
other ("free") groups are assigned by a deterministic multi-start local search with a lexicographic
objective (per-class requirements, ratio band, test-group depth, ratio, box balance).

The test split is sealed by the SHA-256 of its sorted stem list in the manifest. `verify` re-derives
every artifact byte-for-byte and re-checks every hard rule. No training and no image I/O.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_STATUS = "WP36_AWAITING_QA_REVIEW"
BOUNDARY = "G07_SPLIT_PROPOSAL_NOT_OWNER_ACCEPTED_NO_TRAINING"
SEED = 20261018
RESTARTS = 120
SPLITS = ("train", "val", "test")
TARGET = {"train": 0.70, "val": 0.15, "test": 0.15}
TOLERANCE = 0.03
ONE_FREE_TEST = {"17", "18", "19", "30", "40", "45", "50"}
REVISED_TRAIN_ONLY = {"38"}
QUARANTINED_STEM = "0248"

GENERATED = Path("docs/review/generated")
REGISTRY = GENERATED / "d02_group_id_registry.csv"
BOXES = GENERATED / "wp33_derived_boxes.csv"
D04_PART1 = GENERATED / "d04_owner_decisions_part1.csv"
D04_PART2 = GENERATED / "d04_owner_decisions_part2.csv"
NEGATIVES = GENERATED / "d04_owner_negative_frames.csv"
WP35_LINEAGE = GENERATED / "wp35_enrichment_lineage.csv"
PINNED_SOURCES = {
    str(REGISTRY): "c3b11f4c143627fd777270b34e40486bf92fd6e82e4c306187165fef4f7155d3",
    str(BOXES): "4b9307003ce8fd3c1d50763a5950d3d57cf6b2ee6df3aeef74621707067501c0",
    str(D04_PART1): "62de39245a22292a9404702427d8b6bf3a9f746e081163d12198263815bc5409",
    str(D04_PART2): "8030f4fd7098b971009dd86831b877701dedbc24c8901fe938a352615f959c6d",
    str(NEGATIVES): "af1bd4eb314a33ef94a40f1efb01a4c5ac3ef550fbde183fb3d08861d4aa17cb",
    str(WP35_LINEAGE): "e802fc264feff5168c28b531801af04051a36accc3c893ad5ab2e72975d38fed",
    "docs/review/d04_owner_decision_part1_record.md": "0b8ff5b9b73e1aaf8d4efc78ab2eeab83d7d5a87d891988f687656771c854230",
    "docs/review/d04_owner_decision_part2_record.md": "984ce4d758483e5996443b0c25b0c391ca0cd11b1607ae501393b68e6c72562e",
    "docs/review/g07_owner_decision_record.md": "5cab1825f11cdd63ed2cd81576fe01a00bd21d2240ab0def11178771bc0afc0b",
    "docs/review/wp36_g07_split_plan.md": "05e93ec7ee474a955bbf2e000cbc17d43d963e0104617db3404721fdb8955a53",
    "scripts/build_d02_owner_decision.py": "b91af3a6abe70341bdc49d2b87787a43535628d701e8cd7430caadd189939e76",
}

FRAMES_PATH = GENERATED / "wp36_split_frames.csv"
GROUPS_PATH = GENERATED / "wp36_split_groups.csv"
COVERAGE_PATH = GENERATED / "wp36_class_coverage.csv"
CANDIDATE_PATH = GENERATED / "wp36_split_candidate.json"
MANIFEST_PATH = GENERATED / "wp36_split_manifest.json"
REPORT_PATH = Path("docs/review/wp36_group_split_report.md")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def csv_bytes(fields: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        actual = sha256_bytes((repo_root / relative).read_bytes())
        if actual != expected:
            raise ValueError(f"pinned source changed: {relative}")


def load_inputs(repo_root: Path) -> dict[str, Any]:
    registry = read_csv(repo_root / REGISTRY)
    group_of = {row["stem"]: row["group_id"] for row in registry}
    sizes = Counter(group_of.values())
    class_groups: dict[str, Counter[str]] = defaultdict(Counter)
    for box in read_csv(repo_root / BOXES):
        if box["train_eligible"] == "True":
            class_groups[box["derived_key"]][group_of[box["stem"]]] += 1
    decision = {row["derived_key"]: "TRAIN_WITH_ENRICHMENT" for row in read_csv(repo_root / D04_PART1)}
    decision.update({row["derived_key"]: row["owner_decision"] for row in read_csv(repo_root / D04_PART2)})
    for key in REVISED_TRAIN_ONLY:
        decision[key] = "TRAIN_ONLY_UNVERIFIED"
    if set(decision) != set(class_groups):
        raise ValueError("D-04 decisions do not cover exactly the WP33 trainable classes")
    negatives = {row["stem"]: row["owner_use"] for row in read_csv(repo_root / NEGATIVES)}
    lineage_groups = {row["source_group_id"] for row in read_csv(repo_root / WP35_LINEAGE)}
    return {
        "registry": registry, "group_of": group_of, "sizes": sizes, "class_groups": class_groups,
        "decision": decision, "negatives": negatives, "lineage_groups": lineage_groups,
    }


def requirements(decision: dict[str, str]) -> dict[str, frozenset[str]]:
    """Splits each class must reach. Train-only classes need only train."""
    needs = {}
    for key, value in decision.items():
        if value in ("TRAIN_WITH_ENRICHMENT", "TRAIN_ONLY_UNVERIFIED"):
            needs[key] = frozenset({"train"})
        elif value == "TRAIN_AND_TEST_NO_VAL" or key in ONE_FREE_TEST:
            needs[key] = frozenset({"train", "test"})
        elif value == "TRAIN_VAL_TEST":
            needs[key] = frozenset(SPLITS)
        else:
            raise ValueError(f"unknown D-04 decision {value} for class {key}")
    return needs


def forced_train(data: dict[str, Any]) -> set[str]:
    forced = set(data["lineage_groups"])
    for key, value in data["decision"].items():
        if value in ("TRAIN_WITH_ENRICHMENT", "TRAIN_ONLY_UNVERIFIED"):
            forced |= set(data["class_groups"][key])
    return forced


class Scorer:
    def __init__(self, data: dict[str, Any], forced: set[str]) -> None:
        self.sizes = data["sizes"]
        self.total = sum(self.sizes.values())
        self.class_groups = data["class_groups"]
        self.needs = requirements(data["decision"])
        self.forced = forced
        self.full = sorted(k for k, v in data["decision"].items() if v == "TRAIN_VAL_TEST" and k not in ONE_FREE_TEST)
        self.box_total = Counter()
        for counts in self.class_groups.values():
            for group, n in counts.items():
                self.box_total[group] += n
        self.all_boxes = sum(self.box_total.values())

    def split_of(self, assignment: dict[str, str], group: str) -> str:
        return "train" if group in self.forced else assignment[group]

    def score(self, assignment: dict[str, str]) -> tuple[float, ...]:
        frames = Counter()
        boxes = Counter()
        for group, size in self.sizes.items():
            split = self.split_of(assignment, group)
            frames[split] += size
            boxes[split] += self.box_total[group]
        share = {s: frames[s] / self.total for s in SPLITS}
        band = sum(max(0.0, abs(share[s] - TARGET[s]) - TOLERANCE) for s in SPLITS)
        unmet = 0
        for key, need in self.needs.items():
            reached = {self.split_of(assignment, g) for g in self.class_groups[key]}
            unmet += len(need - reached)
        deep = sum(
            1 for key in self.full
            if sum(1 for g in self.class_groups[key] if self.split_of(assignment, g) == "test") >= 2
        )
        ratio = sum(abs(share[s] - TARGET[s]) for s in SPLITS)
        balance = sum(abs(boxes[s] / self.all_boxes - TARGET[s]) for s in SPLITS)
        # Owner ranking (G0.7 record): per-class requirements before the ratio band.
        return (-unmet, -round(band, 6), deep, -round(ratio, 6), -round(balance, 6))


def search(scorer: Scorer, free: list[str]) -> dict[str, str]:
    rng = random.Random(SEED)
    best: tuple[tuple[float, ...], str, dict[str, str]] | None = None
    for _restart in range(RESTARTS):
        assignment = {g: rng.choices(SPLITS, weights=(0.4, 0.3, 0.3))[0] for g in free}
        current = scorer.score(assignment)
        improved = True
        while improved:
            improved = False
            for group in free:
                for split in SPLITS:
                    if split == assignment[group]:
                        continue
                    old = assignment[group]
                    assignment[group] = split
                    candidate = scorer.score(assignment)
                    if candidate > current:
                        current, improved = candidate, True
                    else:
                        assignment[group] = old
            for i, first in enumerate(free):
                for second in free[i + 1:]:
                    if assignment[first] == assignment[second]:
                        continue
                    assignment[first], assignment[second] = assignment[second], assignment[first]
                    candidate = scorer.score(assignment)
                    if candidate > current:
                        current, improved = candidate, True
                    else:
                        assignment[first], assignment[second] = assignment[second], assignment[first]
        key = "".join(assignment[g][1] for g in free)
        if best is None or current > best[0] or (current == best[0] and key < best[1]):
            best = (current, key, dict(assignment))
    assert best is not None
    return best[2]


def check_rules(data: dict[str, Any], forced: set[str], group_split: dict[str, str], frames: list[dict[str, Any]]) -> list[str]:
    errors = []
    for group in forced:
        if group_split[group] != "train":
            errors.append(f"forced group {group} is not in train")
    seen: dict[str, str] = {}
    for row in frames:
        if row["stem"] == QUARANTINED_STEM:
            errors.append("stem 0248 present")
        if seen.setdefault(row["group_id"], row["split"]) != row["split"]:
            errors.append(f"group {row['group_id']} in two splits")
        if row["stem"] in data["negatives"]:
            expected = "BACKGROUND" if data["negatives"][row["stem"]] == "DETECTOR_BACKGROUND" else "QUARANTINED"
            if row["use"] != expected:
                errors.append(f"negative {row['stem']} has use {row['use']}")
    if sum(1 for row in frames if row["use"] == "BACKGROUND") != 1:
        errors.append("exactly one background frame expected")
    return sorted(set(errors))


def render(repo_root: Path) -> dict[Path, bytes]:
    verify_pins(repo_root)
    data = load_inputs(repo_root)
    forced = forced_train(data)
    free = sorted(set(data["sizes"]) - forced)
    scorer = Scorer(data, forced)
    assignment = search(scorer, free)
    group_split = {g: scorer.split_of(assignment, g) for g in sorted(data["sizes"])}

    frames = []
    for row in sorted(data["registry"], key=lambda r: r["stem"]):
        split = group_split[row["group_id"]]
        use = {"DETECTOR_BACKGROUND": "BACKGROUND", "QUARANTINE_UNTIL_RELABELLED": "QUARANTINED"}.get(
            data["negatives"].get(row["stem"], ""), split.upper()
        )
        frames.append({"stem": row["stem"], "group_id": row["group_id"], "split": split, "use": use})
    errors = check_rules(data, forced, group_split, frames)
    if errors:
        raise ValueError(f"WP36 hard rule violations: {errors}")

    needs = requirements(data["decision"])
    groups_rows = []
    for group in sorted(data["sizes"]):
        classes = sorted((k for k, c in data["class_groups"].items() if group in c), key=lambda k: (len(k), k))
        reason = "FORCED_TRAIN" if group in forced else "SEARCH"
        groups_rows.append({
            "group_id": group, "frames": data["sizes"][group], "boxes": scorer.box_total[group],
            "split": group_split[group], "assignment": reason, "classes": " ".join(classes),
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
            "no_val_for_tuning": "val" not in needs[key],
        })

    split_stems = {s: [r["stem"] for r in frames if r["split"] == s and r["use"] != "QUARANTINED"] for s in SPLITS}
    candidate = {"splits": split_stems}
    candidate_bytes = (json.dumps(candidate, indent=1, sort_keys=True) + "\n").encode("utf-8")
    d02 = _load_d02(repo_root)
    tmp = repo_root / GENERATED / ".wp36_candidate_check.json"
    tmp.write_bytes(candidate_bytes)
    try:
        check = d02.check_candidate(repo_root, tmp)
    finally:
        tmp.unlink()
    if not check["accepted"]:
        raise ValueError(f"D-02 check-candidate rejected the split: {check['errors']}")

    usable = {s: len(split_stems[s]) for s in SPLITS}
    total_usable = sum(usable.values())
    unmet = [row["derived_key"] for row in coverage if not row["requirement_met"]]
    score = scorer.score(assignment)
    artifacts: dict[Path, bytes] = {
        FRAMES_PATH: csv_bytes(["stem", "group_id", "split", "use"], frames),
        GROUPS_PATH: csv_bytes(["group_id", "frames", "boxes", "split", "assignment", "classes"], groups_rows),
        COVERAGE_PATH: csv_bytes(list(coverage[0]), coverage),
        CANDIDATE_PATH: candidate_bytes,
    }
    manifest = {
        "package": "M0-WP36", "status": PACKAGE_STATUS, "boundary": BOUNDARY,
        "seed": SEED, "restarts": RESTARTS, "target": TARGET, "tolerance": TOLERANCE,
        "objective": {"unmet_requirements": -score[0], "band_violation": -score[1], "classes_with_2plus_test_groups": score[2],
                      "ratio_deviation": -score[3], "box_balance_deviation": -score[4]},
        "groups": {s: sum(1 for g in group_split.values() if g == s) for s in SPLITS},
        "forced_train_groups": len(forced),
        "usable_frames": usable,
        "usable_share": {s: round(usable[s] / total_usable, 4) for s in SPLITS},
        "excluded": {"quarantined_negatives": sum(1 for r in frames if r["use"] == "QUARANTINED"), "stem_0248": "absent"},
        "unmet_class_requirements": unmet,
        "test_seal_sha256": sha256_bytes("\n".join(sorted(split_stems["test"])).encode("utf-8")),
        "split_list_sha256": {s: sha256_bytes("\n".join(sorted(split_stems[s])).encode("utf-8")) for s in SPLITS},
        "pinned_sources": PINNED_SOURCES,
        "artifacts": {str(path): sha256_bytes(payload) for path, payload in sorted(artifacts.items())},
        "split_authorized": False, "training_authorized": False,
    }
    artifacts[MANIFEST_PATH] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    artifacts[REPORT_PATH] = render_report(manifest, coverage, groups_rows).encode("utf-8")
    return artifacts


def _load_d02(repo_root: Path) -> Any:
    spec = importlib.util.spec_from_file_location("wp36_d02", repo_root / "scripts/build_d02_owner_decision.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def render_report(manifest: dict[str, Any], coverage: list[dict[str, Any]], groups: list[dict[str, Any]]) -> str:
    usable, share = manifest["usable_frames"], manifest["usable_share"]
    split_table = "\n".join(
        f"| {s} | {manifest['groups'][s]} | {usable[s]} | {share[s]:.1%} |" for s in SPLITS
    )
    weak = [r for r in coverage if "val" in r["required_splits"] and r["test_groups"] < 2]
    no_val = [r["derived_key"] for r in coverage if r["no_val_for_tuning"] and r["required_splits"] != "train"]
    train_only = [r["derived_key"] for r in coverage if r["required_splits"] == "train"]
    unmet = manifest["unmet_class_requirements"]
    rows = "\n".join(
        f"| {r['derived_key']} | {r['d04_decision']} | {r['required_splits']} | {r['train_groups']}/{r['val_groups']}/{r['test_groups']} | "
        f"{r['train_boxes']}/{r['val_boxes']}/{r['test_boxes']} | {'yes' if r['requirement_met'] else '**NO**'} |"
        for r in coverage
    )
    group_lines = "\n".join(
        f"| {g['group_id']} | {g['frames']} | {g['split']} | {g['assignment']} | {g['classes']} |" for g in groups
    )
    return f"""# M0-WP36 — G0.7 group-aware split

Status: `{PACKAGE_STATUS}`
Boundary: `{BOUNDARY}`

Built from the owner's G0.7 decision (`docs/review/g07_owner_decision_record.md`, option A). Every
D-02 group is in exactly one split. Nothing here authorizes training; the split becomes the
G0.7 split only after independent QA and owner acceptance.

## Splits (usable frames: quarantined negatives excluded, 0544 counted as train background)

| Split | Groups | Frames | Share |
| --- | --- | --- | --- |
{split_table}

- {manifest['forced_train_groups']} groups are forced into train (single-group classes, class 38, WP35 sources).
- {manifest['excluded']['quarantined_negatives']} quarantined negatives are listed in
  `wp36_split_frames.csv` with `use=QUARANTINED` and left out of every split list; stem 0248 is absent.
- **Test seal:** SHA-256 of the sorted test stem list = `{manifest['test_seal_sha256']}`. Any change
  to the test list needs a new append-only split version. The M1 loader must refuse TEST frames
  outside an explicit, logged final-evaluation run.
- Search: seed {manifest['seed']}, {manifest['restarts']} restarts; objective {json.dumps(manifest['objective'])}.

## Owner review points (structural, not search artifacts)

- **Ratio band.** Usable shares are train {share['train']:.1%} / val {share['val']:.1%} / test
  {share['test']:.1%}; band violation {manifest['objective']['band_violation']:.3f}. Option A sends
  D02-C0048 (411 frames, the only free group of classes 18, 40 and 45) to test. Together with the
  single free groups of 17/19, 20, 28/30 and 50 and one test group each for 9, 11 and 25, the test
  split needs at least about 20 % of the frames, so the ±3-point band cannot be met under option A.
- **Classes 22 and 25 compete for D02-C0032.** 22 needs val, and its only other free group (C0030)
  must be test for 28 and 30. 25 has only C0032 and C0036, and needs one in train and one in test.
  At least one requirement fails whatever the search does; this build leaves
  {', '.join(unmet) or 'none'} unmet.
- Owner choices: accept as built; or accept a smaller test for 18/40/45 (C0048 to val, giving
  them no sealed test); or move class 25 to train-only.

## Class coverage

- Requirements not met: {', '.join(unmet) or 'none'}.
- No validation, so not for tuning: {', '.join(no_val)}.
- Train only (no sealed test, accuracy unknown): {', '.join(train_only)}.
- `TRAIN_VAL_TEST` classes with a single test group (weaker test evidence):
  {', '.join(r['derived_key'] for r in weak) or 'none'}.

| Class | D-04 | Required | Groups train/val/test | Boxes train/val/test | Met |
| --- | --- | --- | --- | --- | --- |
{rows}

## Groups

| Group | Frames | Split | Assignment | Classes |
| --- | --- | --- | --- | --- |
{group_lines}

## Known limits

- D-02 groups come from AI visual review. The same physical sign can still appear in two groups,
  so test scores may be optimistic.
- Train-only classes have no sealed test; their accuracy is unknown until real independent images exist.
- Box counts per split are uneven per class; small test counts (for example class 28 or 50) give
  wide confidence intervals.
"""


def build(repo_root: Path) -> dict[str, Any]:
    artifacts = render(repo_root)
    for path, payload in artifacts.items():
        (repo_root / path).parent.mkdir(parents=True, exist_ok=True)
        (repo_root / path).write_bytes(payload)
    return {"status": PACKAGE_STATUS, "artifacts": len(artifacts)}


def verify(repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        artifacts = render(repo_root)
        for path, payload in artifacts.items():
            if not (repo_root / path).is_file() or (repo_root / path).read_bytes() != payload:
                errors.append(f"artifact differs: {path}")
    except (ValueError, OSError, KeyError) as error:
        errors.append(str(error))
        artifacts = {}
    return {"status": PACKAGE_STATUS, "valid": not errors, "artifact_count": len(artifacts), "errors": errors}


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = root.parse_args(argv)
    repo_root = args.repo_root.resolve()
    result = build(repo_root) if args.command == "build" else verify(repo_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command == "build" or result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
