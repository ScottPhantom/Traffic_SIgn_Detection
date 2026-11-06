"""Two-seed, validation-only provisional NMS/confidence diagnostic.

Run from ``detector`` with ``PYTHONPATH=. uv run --no-sync python -m
m1.two_seed_provisional_threshold_r1 write``. This never trains, opens the
sealed test, changes the app, or writes a threshold-lock record.
"""

from __future__ import annotations

import argparse
import json
import tarfile
import tempfile
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from m1 import a3_pilot_paired_ci_r1 as ci
from m1 import nms_sweep_r1 as sweep
from m1.metrics import Frame

ROOT = sweep.REPO
BUNDLE = sweep.BUNDLE
OUT = ROOT / "results/experiments/d1_two_seed_provisional_threshold_r1"
RESULT = ROOT / "docs/review/generated/d1_two_seed_provisional_threshold_r1.json"
STATE = ROOT / "tmp/d1_s2_seed_20261019_r1_state"
ARCHIVE = STATE / ("D1_yolo11s_wp33_afa03d4b_20261019_20261106T113001_s2_r1_result.tar.gz")
MANIFEST = Path(f"{ARCHIVE}.manifest.json")
WEIGHT_SHA = "046cfea22e6daf45342063b58cd9082aa4b0b0528a3a6d9af7ac23bbac015bce"
GRID = tuple(
    sorted(
        {round(i / 100, 2) for i in range(5, 100, 5)} | {round(i / 100, 2) for i in range(15, 31)}
    )
)
ROUNDS, SEED = 1000, 20261018
BASE = sweep.key(sweep.BASE)
STATUS = "PROVISIONAL_TWO_SEED_NOT_A_LOCK"

PINS = {
    "owner_authorization": (
        ROOT / "docs/review/d1_two_seed_provisional_threshold_r1_owner_authorization_2026-11-06.md",
        "f71a7eea772e191b8db6bf6074b450aa71fa3c8bbeb443b69983eb610e627be4",
    ),
    "run_qa": (
        ROOT / "docs/review/d1_s2_r1_result_independent_qa_record.md",
        "68ce90a9b34bb65b7bd85f3120ac96c064cbae1b36f7ddfd510a35a1187f0ec3",
    ),
    "evaluation_qa": (
        ROOT / "docs/review/d1_s2_r1_common_validation_result_independent_qa_record.md",
        "4fc33d5375e1cc9df14ab64c472242530b619081b8f48b0c3cf9e1898773ca3f",
    ),
    "s2_comparison": (
        ROOT
        / "results/experiments/d1_s2_seed_20261019_r1/evaluation_common_r1/comparison_s2_r1.json",
        "0d76dc34eaa8dfe4c155dfb16a0d150862ae2e568c623319f3a65db45c5a46b4",
    ),
    "s2_common_csv": (
        ROOT / "results/experiments/d1_s2_seed_20261019_r1/evaluation_common_r1/s2_predictions.csv",
        "eb0ca49efde4a4c921c38e2eb00d7136a29c50d50e46cd49557356ca9c9a33b8",
    ),
    "s2_archive": (ARCHIVE, "c9367603c67650968514d00699d73bc0202fb7e1b69c4a6af413b34f60b2164e"),
    "s2_manifest": (MANIFEST, "b771a58996f75257f2a58adcb684273dff637be28b5d66606a66a721694e172e"),
    "pilot_nms_json": (
        ROOT / "docs/review/generated/d1_nms_sweep_r1.json",
        "6be704d21edacd92aeb142f9fc4a5ffb6988686f24ebda9321224634f5460057",
    ),
    "pilot_nms_qa": (
        ROOT / "docs/review/d1_nms_sweep_r1_result_independent_qa_record.md",
        "75808758357b099adb5b43968dcaba594196875535689fa76256406625ace320",
    ),
    "nms_source": (
        ROOT / "detector/m1/nms_sweep_r1.py",
        "0a114a495337bef898bddcbfa3711556f2d740f028d7150ca91a9029a7e4311e",
    ),
    "paired_source": (
        ROOT / "detector/m1/a3_pilot_paired_ci_r1.py",
        "7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4",
    ),
    "selection_contract": (
        ROOT / "docs/review/d1_threshold_lock_r1_contract.md",
        "726932dbcd32842658477c9d36f4dc7c240d412d92119e76e5b3536a4d278f0f",
    ),
    "selection_contract_qa": (
        ROOT / "docs/review/d1_threshold_lock_r1_contract_independent_qa_record.md",
        "e85c1ac36973f82b85bc28842afd01aa0c286b83db388f065f72115cac11d4a6",
    ),
    "bundle": (
        BUNDLE / "manifest.json",
        "8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da",
    ),
}


def _require(path: Path, digest: str) -> None:
    if path.is_symlink() or not path.is_file() or sweep.sha256(path) != digest:
        raise RuntimeError(f"pinned input differs: {path}")


def _qa_pass(path: Path) -> None:
    verdicts = [
        x for x in path.read_text(encoding="utf-8").splitlines() if x.startswith("Verdict:")
    ]
    if len(verdicts) != 1 or not verdicts[0].startswith("Verdict: PASS"):
        raise RuntimeError(f"independent QA is not PASS: {path}")


def preflight() -> tuple[dict, dict, dict[str, str]]:
    """Check every prior result and pilot CSV before loading a model."""
    hashes = {}
    for label, (path, digest) in PINS.items():
        _require(path, digest)
        hashes[label] = digest
    for label in ("run_qa", "evaluation_qa", "pilot_nms_qa", "selection_contract_qa"):
        _qa_pass(PINS[label][0])
    sweep_pins = sweep.check_pins()  # validates all governed R3 train/val bundle members
    hashes.update({f"sweep_{name}": digest for name, digest in sweep_pins.items()})
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    comparison = json.loads(PINS["s2_comparison"][0].read_text(encoding="utf-8"))
    pilot = json.loads(PINS["pilot_nms_json"][0].read_text(encoding="utf-8"))
    if (
        manifest.get("sealed_test_accessed") is not False
        or comparison.get("sealed_test_accessed") is not False
        or comparison.get("split") != "val"
        or comparison.get("s2_best_weight_sha256") != WEIGHT_SHA
        or comparison.get("s2_result_archive_sha256") != hashes["s2_archive"]
        or comparison.get("prediction_csv_sha256") != hashes["s2_common_csv"]
        or pilot.get("sealed_test_accessed") is not False
        or pilot.get("thresholds_locked") is not False
        or set(pilot["configurations"]) != {sweep.key(c) for c in sweep.CONFIGS}
        or set(pilot["prediction_csv_sha256"]) != set(pilot["configurations"])
    ):
        raise RuntimeError("result, validation, or seal binding differs")
    for name, digest in pilot["prediction_csv_sha256"].items():
        _require(sweep.OUT / f"predictions_{name}.csv", digest)
        hashes[f"pilot_{name}"] = digest
    return manifest, comparison, hashes


def extract_weight(destination: Path) -> None:
    """Extract only the QA-pinned S2 best weight into a disposable directory."""
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        members = [m for m in archive.getmembers() if m.name.endswith("/weights/best.pt")]
        if len(members) != 1 or not members[0].isfile() or members[0].issym():
            raise RuntimeError("S2 archive has no unique regular best.pt")
        source = archive.extractfile(members[0])
        if source is None:
            raise RuntimeError("S2 best.pt cannot be read")
        with source, destination.open("xb") as sink:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                sink.write(chunk)
    _require(destination, WEIGHT_SHA)


def load_pilot(pilot: dict) -> dict[str, list[Frame]]:
    base = ci.gt_frames(BUNDLE)
    frames = {
        name: ci.with_predictions(
            base, sweep.OUT / f"predictions_{name}.csv", "class_id", "confidence"
        )
        for name in pilot["configurations"]
    }
    p = sweep.point(frames[BASE], 0.20)
    if (p["tp"], p["fp"], p["correct_class_hits"]) != (547, 150, 457):
        raise RuntimeError("pilot 0.20 anchor differs")
    return frames


def equivalence(s2: list[Frame], comparison: dict, common: object) -> dict:
    """Stop before the other ten NMS inferences if 0.70 differs from QA S2."""
    p = sweep.point(s2, 0.20)
    ap = common.average_precision(s2)
    stored = comparison["s2_common_method"]
    fixed, expected_ap = stored["fixed_conf_020"], stored["exact_class_ap"]
    good = (
        (p["tp"], p["fp"], p["correct_class_hits"]) == (507, 127, 379)
        and (p["tp"], p["fp"], p["correct_class_hits"])
        == (
            fixed["true_positives"],
            fixed["false_positives"],
            sum(fixed["per_class_hits"].values()),
        )
        and abs(ap["map50"] - expected_ap["map50"]) <= 1e-4
        and abs(ap["map50_95"] - expected_ap["map50_95"]) <= 1e-4
    )
    proof = {
        "passed": good,
        "conf_020": p,
        "ap": ap,
        "qa_comparison_sha256": PINS["s2_comparison"][1],
    }
    if not good:
        raise RuntimeError("S2 NMS 0.70 equivalence failed: " + json.dumps(proof))
    return proof


def selection_grid() -> tuple[float, ...]:
    return GRID


def score_cell(pilot: dict, s2: dict, ap_mean: float, name: str, confidence: float) -> dict:
    return {
        "configuration": name,
        "confidence": confidence,
        "seed_20261018": pilot,
        "seed_20261019": s2,
        "mean_agnostic_recall": (pilot["agnostic_recall"] + s2["agnostic_recall"]) / 2,
        "mean_fp_per_image": (pilot["fp_per_image"] + s2["fp_per_image"]) / 2,
        "seed_difference_19_minus_18": {
            "agnostic_recall": s2["agnostic_recall"] - pilot["agnostic_recall"],
            "fp_per_image": s2["fp_per_image"] - pilot["fp_per_image"],
        },
        "mean_map50_95": ap_mean,
    }


def choose(cells: Sequence[dict]) -> dict | None:
    eligible = [c for c in cells if c["mean_agnostic_recall"] >= 0.85]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda c: (
            c["mean_fp_per_image"],
            -c["confidence"],
            -c["mean_map50_95"],
            abs(c["iou"] - 0.70),
            c["agnostic_nms"],
            c["iou"],
        ),
    )


def _point(stats: dict, indices: np.ndarray) -> dict:
    gt = float(stats["gt"][indices].sum())
    return {
        "agnostic_recall": float(stats["agnostic_hits"][indices].sum() / gt),
        "fp_per_image": float(stats["fp"][indices].sum() / len(indices)),
        "tp": int(stats["agnostic_hits"][indices].sum()),
        "fp": int(stats["fp"][indices].sum()),
        "gt": int(gt),
        "images": int(len(indices)),
    }


def _two_seed_point(stats18: dict, stats19: dict, indices: np.ndarray) -> dict:
    a, b = _point(stats18, indices), _point(stats19, indices)
    return {
        "seed_20261018": a,
        "seed_20261019": b,
        "mean_agnostic_recall": (a["agnostic_recall"] + b["agnostic_recall"]) / 2,
        "mean_fp_per_image": (a["fp_per_image"] + b["fp_per_image"]) / 2,
    }


def bootstrap_change(
    frames: dict[str, dict[str, list[Frame]]], selected: dict, baseline: dict
) -> dict:
    """Reuse one nine-group draw across both seeds and both NMS settings."""
    samples = ci.resample_indices(frames["seed_20261018"][BASE], ROUNDS, SEED)
    chosen, reference = selected["configuration"], baseline["configuration"]
    pairs = {
        (seed, name): frames[seed][name]
        for seed in ("seed_20261018", "seed_20261019")
        for name in (chosen, reference)
    }
    stats = {
        key: ci.frame_stats(
            value, selected["confidence"] if key[1] == chosen else baseline["confidence"]
        )
        for key, value in pairs.items()
    }
    correct = {key: ci._correct_matrices(value) for key, value in pairs.items()}
    fp_diffs, map_diffs = [], []
    for sample in samples:
        fp_means, map_means = [], []
        for name in (chosen, reference):
            fp_means.append(
                sum(
                    _point(stats[(seed, name)], sample)["fp_per_image"]
                    for seed in ("seed_20261018", "seed_20261019")
                )
                / 2
            )
            map_means.append(
                sum(
                    ci._map50_95(pairs[(seed, name)], correct[(seed, name)], sample)
                    for seed in ("seed_20261018", "seed_20261019")
                )
                / 2
            )
        fp_diffs.append(fp_means[0] - fp_means[1])
        map_diffs.append(map_means[0] - map_means[1])
    return {
        "rounds": ROUNDS,
        "seed": SEED,
        "unit": "intact D-02 group",
        "same_draws_all_seeds_and_settings": True,
        "candidate": {"configuration": chosen, "confidence": selected["confidence"]},
        "reference": {"configuration": reference, "confidence": baseline["confidence"]},
        "fp_per_image_difference": selected["mean_fp_per_image"] - baseline["mean_fp_per_image"],
        "fp_per_image_ci95": ci.ci95(fp_diffs),
        "map50_95_difference": selected["mean_map50_95"] - baseline["mean_map50_95"],
        "map50_95_ci95": ci.ci95(map_diffs),
    }


def adjacent_votes(folds: Sequence[dict], chosen: str) -> int:
    config = next(c for c in sweep.CONFIGS if sweep.key(c) == chosen)
    same = [c[0] for c in sweep.CONFIGS if c[1] == config[1]]
    i = same.index(config[0])
    allowed = {sweep.key((v, config[1])) for v in same[max(0, i - 1) : i + 2]}
    return sum(fold["selected_configuration"] in allowed for fold in folds)


def decide_change(
    selected: dict, baseline: dict, change: dict | None, folds: Sequence[dict]
) -> dict:
    """Keep class-aware 0.70 unless every frozen change condition holds."""
    votes = adjacent_votes(folds, selected["configuration"])
    allowed = bool(
        selected["configuration"] == BASE
        or (
            change is not None
            and change["fp_per_image_ci95"][1] < 0
            and change["map50_95_ci95"][1] >= 0
            and votes >= 7
        )
    )
    return {
        "provisional": selected if allowed else baseline,
        "change_allowed": allowed and selected["configuration"] != BASE,
        "adjacent_votes": votes,
    }


def leave_one_group_out(frames: dict[str, dict[str, list[Frame]]], common: object) -> list[dict]:
    """Select using eight groups; report the held-out group's two-seed mean."""
    first = frames["seed_20261018"][BASE]
    groups = np.asarray([f.group_id for f in first])
    # Cache per-frame matching once; each fold only changes the group indices.
    stats = {
        (seed, name, confidence): ci.frame_stats(items, confidence)
        for seed, settings in frames.items()
        for name, items in settings.items()
        for confidence in GRID
    }
    folds = []
    for held in sorted(set(groups)):
        fit, hold = np.flatnonzero(groups != held), np.flatnonzero(groups == held)
        candidates = []
        for config in sweep.CONFIGS:
            name = sweep.key(config)
            fit_ap = (
                sum(
                    common.average_precision([frames[seed][name][i] for i in fit])["map50_95"]
                    for seed in ("seed_20261018", "seed_20261019")
                )
                / 2
            )
            for confidence in GRID:
                p = _two_seed_point(
                    stats[("seed_20261018", name, confidence)],
                    stats[("seed_20261019", name, confidence)],
                    fit,
                )
                candidates.append(
                    {
                        "configuration": name,
                        "confidence": confidence,
                        "iou": config[0],
                        "agnostic_nms": config[1],
                        "mean_map50_95": fit_ap,
                        **p,
                    }
                )
        chosen = choose(candidates)
        if chosen is None:
            folds.append({"held_out_group": held, "selected_configuration": None})
            continue
        name, confidence = chosen["configuration"], chosen["confidence"]
        held_stats = [
            stats[(seed, name, confidence)] for seed in ("seed_20261018", "seed_20261019")
        ]
        folds.append(
            {
                "held_out_group": held,
                "selected_configuration": name,
                "confidence": confidence,
                "held_out": _two_seed_point(*held_stats, hold),
            }
        )
    return folds


def run(device: str) -> dict:
    _, comparison, hashes = preflight()
    if RESULT.exists() or OUT.exists():
        raise FileExistsError("provisional output already exists; refusing overwrite")
    import evaluate_cascade_b0_r1 as common  # on sys.path after sweep.check_pins()
    from ultralytics import YOLO, settings
    from ultralytics.utils import checks

    checks.AUTOINSTALL = checks.ONLINE = False
    settings.update({"sync": False, "wandb": False, "mlflow": False, "clearml": False})
    pilot_json = json.loads(PINS["pilot_nms_json"][0].read_text(encoding="utf-8"))
    pilot = load_pilot(pilot_json)
    with tempfile.TemporaryDirectory(prefix="d1_s2_provisional_") as temporary:
        weight = Path(temporary) / "best.pt"
        extract_weight(weight)
        detector = YOLO(str(weight))
        if len(detector.names) != 54:
            raise RuntimeError("S2 best.pt is not 54-class")
        s2 = {BASE: sweep.infer(detector, *sweep.BASE, device)}
        gate = equivalence(s2[BASE], comparison, common)
        print("S2 classaware_0.70 equivalence PASS", flush=True)
        for config in sweep.CONFIGS:
            name = sweep.key(config)
            if name != BASE:
                s2[name] = sweep.infer(detector, *config, device)
                print(f"S2 {name} inferred", flush=True)
    frames = {"seed_20261018": pilot, "seed_20261019": s2}
    configurations, cells = {}, []
    for config in sweep.CONFIGS:
        name = sweep.key(config)
        ap18 = pilot_json["configurations"][name]["ap"]
        ap19 = common.average_precision(s2[name])
        mean_ap = (ap18["map50_95"] + ap19["map50_95"]) / 2
        configurations[name] = {
            "iou": config[0],
            "agnostic_nms": config[1],
            "map50_95": {
                "seed_20261018": ap18["map50_95"],
                "seed_20261019": ap19["map50_95"],
                "mean": mean_ap,
            },
        }
        for confidence in GRID:
            a, b = sweep.point(pilot[name], confidence), sweep.point(s2[name], confidence)
            cells.append(
                {
                    **score_cell(a, b, mean_ap, name, confidence),
                    "iou": config[0],
                    "agnostic_nms": config[1],
                }
            )
    selected = choose(cells)
    base_selected = choose([c for c in cells if c["configuration"] == BASE])
    if selected is None or base_selected is None:
        raise RuntimeError("no eligible two-seed cell; no provisional threshold")
    change = (
        bootstrap_change(frames, selected, base_selected)
        if selected["configuration"] != BASE
        else None
    )
    folds = leave_one_group_out(frames, common)
    decision = decide_change(selected, base_selected, change, folds)
    provisional = decision["provisional"]
    OUT.mkdir(mode=0o700, parents=True, exist_ok=False)
    csv_hashes = {
        name: sweep.write_predictions(OUT / f"predictions_{name}.csv", s2[name]) for name in s2
    }
    output = {
        "package": "D1-TWO-SEED-PROVISIONAL-THRESHOLD-R1",
        "status": STATUS,
        "split": "val",
        "images": 376,
        "gt_boxes": 624,
        "groups": 9,
        "seeds": [20261018, 20261019],
        "confidence_grid": GRID,
        "input_sha256": hashes,
        "s2_best_weight_sha256": WEIGHT_SHA,
        "s2_prediction_csv_sha256": csv_hashes,
        "device": device,
        "baseline_equivalence": gate,
        "configurations": configurations,
        "cells": cells,
        "unrestricted_selected": selected,
        "classaware_0_70_selected": base_selected,
        "change_test": change,
        "leave_one_group_out": folds,
        "adjacent_votes": decision["adjacent_votes"],
        "change_allowed": decision["change_allowed"],
        "provisional_selected": provisional,
        "each_seed_recall_ge_0_85": {
            seed: provisional[seed]["agnostic_recall"] >= 0.85
            for seed in ("seed_20261018", "seed_20261019")
        },
        "any_cell_both_d05_markers": any(
            c["mean_agnostic_recall"] >= 0.85 and c["mean_fp_per_image"] <= 0.30 for c in cells
        ),
        "thresholds_locked": False,
        "sealed_test_accessed": False,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    with RESULT.open("x", encoding="utf-8") as sink:
        json.dump(output, sink, indent=2, ensure_ascii=False, allow_nan=False)
        sink.write("\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight", "write"))
    parser.add_argument("--device", choices=("mps", "cpu"), default="mps")
    args = parser.parse_args()
    if args.mode == "preflight":
        _, _, hashes = preflight()
        print(f"PREFLIGHT PASS: {len(hashes)} pinned files; sealed_test_accessed=false")
    else:
        result = run(args.device)
        print(
            json.dumps(
                {k: result[k] for k in ("status", "provisional_selected", "change_allowed")},
                default=str,
            )
        )


if __name__ == "__main__":
    main()
