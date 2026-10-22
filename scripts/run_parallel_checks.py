#!/usr/bin/env python3
"""Run the M0 package verifiers and the pytest suite in parallel without touching pinned files.

The package builders, their tests, ``pyproject.toml`` and ``uv.lock`` are hash-pinned by
QA-passed manifests, so this runner only orchestrates existing entrypoints:

- ``verifiers`` runs every package verifier CLI as its own process, ``--jobs`` at a time. Each
  verifier is read-only, so they cannot interfere with one another.
- ``tests`` first runs the WP9/WP10/WP11 suites serially (they rewrite repository artifacts),
  then runs every other suite through pytest-xdist with ``--dist loadfile``. pytest-xdist is
  supplied with ``uv run --with`` so the pinned lock file stays unchanged.

GPU backends are deliberately not used: atlas bytes are pinned to Pillow's CPU output.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ICLOUD_RAW_ROOT = Path(
    "/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/"
    "FALL 2026 KỲ 4/CPV301/Data/DATASET01/staging/052bc980a7206f8d/raw"
)
# Byte-identical local copy (hash-verified 2026-10-17); the iCloud original stays authoritative
# for the pinned tests, which hard-code its path.
LOCAL_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"
DEFAULT_RAW_ROOT = LOCAL_RAW_ROOT if LOCAL_RAW_ROOT.is_dir() else ICLOUD_RAW_ROOT
PYTEST_XDIST_REQUIREMENT = "pytest-xdist==3.8.0"
SERIAL_TEST_FILES = (
    "tests/test_wp9_bbox_0248_adjudication.py",
    "tests/test_wp10_g04_quarantine.py",
    "tests/test_wp11_d04_rare_class_review.py",
)
RAW_ROOT_VERIFIERS = (
    "build_wp7_cross_split_review_batch.py",
    "build_wp9_bbox_0248_adjudication.py",
    "build_wp10_g04_quarantine.py",
    "build_wp11_d04_rare_class_review.py",
    "build_wp12_cross_split_review_batch.py",
    "build_wp13_cross_split_review_batch.py",
    "build_wp14_cross_split_review_batch.py",
    "build_wp15_cross_split_review_batch.py",
    "build_wp16_sequence_review_batch.py",
    "build_wp17_sequence_review_batch.py",
    "build_wp18_sequence_review_batch.py",
    "build_wp19_sequence_review_batch.py",
    "build_wp20_sequence_review_batch.py",
    "build_wp21_sequence_review_batch.py",
    "build_wp22_remaining_edge_review_batch.py",
    "build_wp23_remaining_edge_review_batch.py",
    "build_wp23_r1_remaining_edge_review_batch.py",
    "build_wp24_remaining_edge_review_batch.py",
    "build_wp25_remaining_edge_review_batch.py",
    "build_wp25_r1_remaining_edge_review_batch.py",
    "build_wp26_remaining_edge_review_batch.py",
    "build_wp27_remaining_edge_review_batch.py",
    "build_wp27_r1_layout_correction.py",
    "build_wp27_r2_verifier_hardening.py",
    "build_wp28_remaining_edge_review_batch.py",
    "build_wp28_r1_remaining_edge_review_batch.py",
    "build_wp28_r2_remaining_edge_review_batch.py",
    "build_wp29_remaining_edge_review_batch.py",
    "build_wp30_remaining_edge_review_batch.py",
    "build_wp30_r1_remaining_edge_review_batch.py",
)


@dataclass(frozen=True)
class Verifier:
    name: str
    argv: tuple[str, ...]
    # WP4 exits 0 unconditionally and reports `status`; every other verifier reports `valid`.
    passed_field: str = "valid"
    passed_value: object = True


@dataclass(frozen=True)
class Outcome:
    verifier: Verifier
    passed: bool
    seconds: float
    detail: str


def default_jobs() -> int:
    return max(1, (os.cpu_count() or 2) - 2)


def verifier_specs(raw_root: Path) -> list[Verifier]:
    raw = str(raw_root)
    specs = [
        Verifier(
            "wp3",
            (
                "scripts/build_wp3_reviewer_assets.py",
                "verify-manifest",
                "--manifest",
                "docs/review/generated/wp3_evidence_manifest.json",
            ),
        ),
        Verifier(
            "wp4",
            (
                "scripts/build_wp4_qcvn_taxonomy_audit.py",
                "verify",
                "--repo-root",
                ".",
                "--raw-root",
                raw,
            ),
            passed_field="status",
            passed_value="PASS",
        ),
        Verifier(
            "wp5",
            (
                "scripts/build_wp5_provisional_grouping_review.py",
                "verify",
                "--manifest",
                "docs/review/generated/wp5_evidence_manifest.json",
                "--repo-root",
                ".",
                "--raw-root",
                raw,
            ),
        ),
        Verifier("wp6", ("scripts/audit_e0_compute_readiness.py", "verify", "--repo-root", ".")),
        Verifier(
            "wp8", ("scripts/build_wp8_taxonomy_recommendation.py", "verify", "--repo-root", ".")
        ),
        Verifier("wp31", ("scripts/build_wp31_group_id_proposal.py", "verify", "--repo-root", ".")),
        Verifier(
            "wp31-r1", ("scripts/build_wp31_r1_group_id_proposal.py", "verify", "--repo-root", ".")
        ),
        Verifier(
            "wp31-r2", ("scripts/build_wp31_r2_group_id_proposal.py", "verify", "--repo-root", ".")
        ),
        Verifier("d01", ("scripts/build_d01_owner_decision.py", "verify", "--repo-root", ".")),
        Verifier(
            "wp35",
            (
                "scripts/build_wp35_rare_class_enrichment.py",
                "verify",
                "--repo-root",
                ".",
                "--raw-root",
                raw,
            ),
        ),
        Verifier("wp36", ("scripts/build_wp36_group_split.py", "verify", "--repo-root", ".")),
        Verifier("m1-yolo", ("scripts/build_m1_yolo_dataset.py", "verify", "--repo-root", ".")),
        Verifier(
            "d1-cascade",
            ("scripts/build_d1_cascade_detector_dataset.py", "verify", "--repo-root", "."),
        ),
        Verifier(
            "dataset01-crops",
            ("scripts/build_dataset01_crops.py", "verify", "--repo-root", ".", "--raw-root", raw),
        ),
        Verifier(
            "wp37-r1",
            (
                "scripts/build_wp37_r1_dataset_card.py",
                "verify",
                "--repo-root",
                ".",
                "--raw-root",
                raw,
            ),
        ),
        Verifier(
            "wp37",
            (
                "scripts/build_wp37_dataset_card.py",
                "verify",
                "--repo-root",
                ".",
                "--raw-root",
                raw,
            ),
        ),
        Verifier(
            "wp38",
            (
                "scripts/build_wp38_orientation_correction.py",
                "verify",
                "--repo-root",
                ".",
                "--raw-root",
                raw,
            ),
        ),
        Verifier(
            "wp38-r1",
            (
                "scripts/build_wp38_r1_orientation_correction.py",
                "verify",
                "--repo-root",
                ".",
                "--raw-root",
                raw,
            ),
        ),
        Verifier(
            "m1-wp38-r1",
            (
                "scripts/build_m1_yolo_dataset_wp38_r1.py",
                "verify",
                "--repo-root",
                ".",
            ),
        ),
        Verifier(
            "m1-wp38-r1-r1",
            (
                "scripts/build_m1_yolo_dataset_wp38_r1_integration_r1.py",
                "verify",
                "--repo-root",
                ".",
            ),
        ),
        Verifier(
            "m1-wp38-r1-r2",
            (
                "scripts/build_m1_yolo_dataset_wp38_r1_integration_r2.py",
                "verify",
                "--repo-root",
                ".",
            ),
        ),
        Verifier(
            "m1-wp38-r1-r3",
            (
                "scripts/build_m1_yolo_dataset_wp38_r1_integration_r3.py",
                "verify",
                "--repo-root",
                ".",
            ),
        ),
        Verifier(
            "m1-wp38-r1-r4",
            (
                "scripts/build_m1_yolo_dataset_wp38_r1_integration_r4.py",
                "verify",
                "--repo-root",
                ".",
            ),
        ),
        Verifier(
            "m1-colab-wp38-r1-r1",
            (
                "scripts/build_m1_colab_bundle_wp38_r1_r1.py",
                "contract",
                "--repo-root",
                ".",
            ),
        ),
        Verifier(
            "m1-colab-wp38-r1-r2",
            (
                "scripts/build_m1_colab_bundle_wp38_r1_r2.py",
                "contract",
                "--repo-root",
                ".",
            ),
        ),
        Verifier(
            "wp36-r1", ("scripts/build_wp36_r1_group_split.py", "verify", "--repo-root", ".")
        ),
        Verifier(
            "wp34-r1",
            (
                "scripts/build_wp34_r1_d04_support_and_negatives.py",
                "verify",
                "--repo-root",
                ".",
                "--raw-root",
                raw,
            ),
        ),
        Verifier(
            "wp34",
            (
                "scripts/build_wp34_d04_support_and_negatives.py",
                "verify",
                "--repo-root",
                ".",
                "--raw-root",
                raw,
            ),
        ),
        Verifier(
            "wp33",
            (
                "scripts/build_wp33_derived_labels.py",
                "verify",
                "--repo-root",
                ".",
                "--raw-root",
                raw,
            ),
        ),
        Verifier("d02", ("scripts/build_d02_owner_decision.py", "verify", "--repo-root", ".")),
        Verifier(
            "wp32",
            (
                "scripts/build_wp32_cross_block_link_review.py",
                "verify",
                "--repo-root",
                ".",
                "--raw-root",
                raw,
            ),
        ),
    ]
    for script in RAW_ROOT_VERIFIERS:
        name = script.removeprefix("build_").split("_")[0]
        if "_r1_" in script or "_r2_" in script:
            name += "-r" + script.split("_r")[1][0]
        specs.append(
            Verifier(name, (f"scripts/{script}", "verify", "--repo-root", ".", "--raw-root", raw))
        )
    return specs


def run_verifier(verifier: Verifier) -> Outcome:
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, *verifier.argv],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    seconds = time.perf_counter() - started
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        tail = (completed.stderr or completed.stdout).strip().splitlines()[-3:]
        return Outcome(verifier, False, seconds, f"exit={completed.returncode} " + " | ".join(tail))
    value = payload.get(verifier.passed_field) if isinstance(payload, dict) else None
    passed = completed.returncode == 0 and value == verifier.passed_value
    detail = f"exit={completed.returncode} {verifier.passed_field}={value!r}"
    if not passed and isinstance(payload, dict) and payload.get("errors"):
        detail += f" errors={payload['errors'][:3]!r}"
    return Outcome(verifier, passed, seconds, detail)


def run_verifiers(raw_root: Path, jobs: int, only: str | None) -> int:
    if not raw_root.is_dir():
        print(f"raw root not found: {raw_root}", file=sys.stderr)
        return 2
    specs = [spec for spec in verifier_specs(raw_root) if only is None or only in spec.name]
    if not specs:
        print(f"no verifier matches --only {only!r}", file=sys.stderr)
        return 2
    missing = [spec.argv[0] for spec in specs if not (REPO_ROOT / spec.argv[0]).is_file()]
    if missing:
        print(f"missing verifier scripts: {missing}", file=sys.stderr)
        return 2
    started = time.perf_counter()
    outcomes: list[Outcome] = []
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(run_verifier, spec) for spec in specs]
        for future in as_completed(futures):
            outcome = future.result()
            outcomes.append(outcome)
            mark = "PASS" if outcome.passed else "FAIL"
            print(
                f"{mark} {outcome.verifier.name:<8} {outcome.seconds:7.1f}s  {outcome.detail}",
                flush=True,
            )
    failed = [outcome.verifier.name for outcome in outcomes if not outcome.passed]
    elapsed = time.perf_counter() - started
    serial = sum(outcome.seconds for outcome in outcomes)
    print(
        f"\n{len(outcomes) - len(failed)}/{len(outcomes)} verifiers passed in {elapsed:.1f}s "
        f"wall ({serial:.1f}s summed, jobs={jobs})"
    )
    if failed:
        print("failed: " + ", ".join(sorted(failed)))
        return 1
    return 0


def run_tests(jobs: int, skip_serial: bool, pytest_args: list[str]) -> int:
    phases: list[tuple[str, list[str]]] = []
    if not skip_serial:
        phases.append(
            (
                "serial repo-writing suites",
                # pyproject addopts already passes -q; a second -q would hide the summary line.
                [sys.executable, "-m", "pytest", *SERIAL_TEST_FILES, *pytest_args],
            )
        )
    ignores = [f"--ignore={path}" for path in SERIAL_TEST_FILES]
    phases.append(
        (
            f"parallel suites (xdist, {jobs} workers, loadfile)",
            [
                "uv",
                "run",
                "--with",
                PYTEST_XDIST_REQUIREMENT,
                "pytest",
                "-n",
                str(jobs),
                "--dist",
                "loadfile",
                *ignores,
                *pytest_args,
            ],
        )
    )
    for label, command in phases:
        print(f"==> {label}: {' '.join(command)}", flush=True)
        started = time.perf_counter()
        returncode = subprocess.run(command, cwd=REPO_ROOT, check=False).returncode
        print(f"<== {label}: exit={returncode} in {time.perf_counter() - started:.1f}s", flush=True)
        if returncode != 0:
            return returncode
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = root.add_subparsers(dest="command", required=True)
    verifiers = commands.add_parser("verifiers", help="run every package verifier in parallel")
    verifiers.add_argument(
        "--raw-root",
        type=Path,
        default=Path(os.environ.get("DATASET01_RAW_ROOT", DEFAULT_RAW_ROOT)),
    )
    verifiers.add_argument("--jobs", type=int, default=default_jobs())
    verifiers.add_argument("--only", help="run only verifiers whose name contains this text")
    tests = commands.add_parser("tests", help="run serial writer suites, then the rest via xdist")
    tests.add_argument("--jobs", type=int, default=default_jobs())
    tests.add_argument("--skip-serial", action="store_true", help="skip the WP9/WP10/WP11 phase")
    tests.add_argument(
        "pytest_args", nargs=argparse.REMAINDER, help="extra pytest arguments after --"
    )
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.jobs < 1:
        print("--jobs must be at least 1", file=sys.stderr)
        return 2
    if args.command == "verifiers":
        return run_verifiers(args.raw_root.resolve(), args.jobs, args.only)
    extra = [arg for arg in args.pytest_args if arg != "--"]
    return run_tests(args.jobs, args.skip_serial, extra)


if __name__ == "__main__":
    raise SystemExit(main())
