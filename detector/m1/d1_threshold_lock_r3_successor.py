"""Two-seed R3 validation lock successor. Never opens the sealed test.

This module deliberately does not call the legacy three-seed lock CLI. A future
run must first supply two independently QA'd, hash-pinned NMS CSV sets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tarfile
from pathlib import Path

from m1 import a3_pilot_paired_ci_r1 as ci
from m1 import nms_sweep_r1 as sweep
from m1 import two_seed_provisional_threshold_r1 as provisional

SEEDS = (20261018, 20261019)
GRID = tuple(
    sorted({round(i / 100, 2) for i in range(5, 100, 5)} | {i / 100 for i in range(15, 31)})
)
CONFIGS = {sweep.key(c): c for c in sweep.CONFIGS}
BASE = sweep.key(sweep.BASE)
BUNDLE_SHA256 = "8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da"
SCORER_PATHS = (
    "detector/colab/evaluate_cascade_b0_r1.py",
    "detector/m1/metrics.py",
    "detector/m1/nms_sweep_r1.py",
    "detector/m1/a3_pilot_paired_ci_r1.py",
    "detector/m1/two_seed_provisional_threshold_r1.py",
    "detector/colab/run_d1_colab.py",
)
SCORER_SHA256 = (
    "8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42",
    "d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f",
    "0a114a495337bef898bddcbfa3711556f2d740f028d7150ca91a9029a7e4311e",
    "7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4",
    "a8f93f0da02ba1decafcbcbb3b21bd12daae1b47f1845cf1cf5d3f951e6fadf3",
    "6a508eebcb83915201569bc74913a3dd546b288caf2331a9b3e4bd7a567500bc",
)
RUN_PINS = {
    20261018: {
        "weight": "5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633",
        "run_contract": "9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88",
        "attestation": "7fa5df339676adaae220e1963916b2e48e2525455713d500db5d76343e2fc9fc",
        "run_qa": "90a13c3333fac3b536146a0ed150f7dd446bec2cda57175f003f8cc0ea7cbc8d",
    },
    20261019: {
        "weight": "046cfea22e6daf45342063b58cd9082aa4b0b0528a3a6d9af7ac23bbac015bce",
        "run_contract": "1f1c3f7f2fdeb15467aa69ddbe012b880b10324b5b505d772058ebd7e96c2050",
        "attestation": "807ba02a87da944e804fc61b314618bb77692c727fb577eec5f7a6395442c80c",
        "run_qa": "68ce90a9b34bb65b7bd85f3120ac96c064cbae1b36f7ddfd510a35a1187f0ec3",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _file(row: dict, label: str) -> Path:
    if set(row) != {"path", "sha256"}:
        raise RuntimeError(f"{label} binding keys differ")
    raw = Path(row["path"]).expanduser()
    if raw.is_symlink():
        raise RuntimeError(f"{label} is a symlink")
    path = raw.resolve(strict=True)
    if not path.is_file() or sha256(path) != row["sha256"]:
        raise RuntimeError(f"{label} hash differs")
    return path


def _qa(row: dict) -> None:
    path = _file(row, "run result QA")
    verdicts = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("Verdict:")
    ]
    if (
        len(verdicts) != 1
        or re.match(r"^Verdict: (?:PASS|\*\*PASS\*\*)(?:\s|$)", verdicts[0]) is None
    ):
        raise RuntimeError("run result QA is not PASS")


def _json_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _committed_clean(path: Path, root: Path) -> None:
    """Require current bytes to equal a file in the checkout's HEAD commit."""
    try:
        relative = path.resolve(strict=True).relative_to(root.resolve(strict=True))
        committed = subprocess.run(
            ["git", "show", f"HEAD:{relative.as_posix()}"],
            cwd=root,
            capture_output=True,
            check=True,
        ).stdout
    except (ValueError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("final gate file is not committed in this checkout") from exc
    if path.read_bytes() != committed:
        raise RuntimeError("final gate file differs from HEAD")


def _run_binding(seed: int, identity: dict, predictions: dict, root: Path) -> None:
    """Independently validate the eight-file result and inference QA binding."""
    pins = RUN_PINS[seed]
    if (
        identity["weight"]["sha256"] != pins["weight"]
        or identity["run_contract"]["sha256"] != pins["run_contract"]
        or identity["run_attestation_sha256"] != pins["attestation"]
        or identity["run_result_qa"]["sha256"] != pins["run_qa"]
    ):
        raise RuntimeError("candidate differs from the QA-pinned pilot family")
    archive = _file(identity["result_archive"], "result archive")
    manifest_path = _file(identity["result_manifest"], "result manifest")
    sys.path.insert(0, str(root / "detector/colab"))
    import run_d1_colab as packager

    manifest = packager.verify_result_archive(archive, manifest_path)
    run = manifest["run"]
    members = {item["path"]: item for item in manifest["files"]}
    weight = _file(identity["weight"], "candidate weight")
    contract_path = _file(identity["run_contract"], "run contract")
    if (
        members[f"{run}/weights/best.pt"]["sha256"] != sha256(weight)
        or members[f"{run}/run_contract.json"]["sha256"] != sha256(contract_path)
        or manifest["run_attestation_sha256"] != identity["run_attestation_sha256"]
    ):
        raise RuntimeError("result archive/weight/contract/attestation binding differs")
    with tarfile.open(archive, "r:gz") as source:
        handle = source.extractfile(f"{run}/run_contract.json")
        if handle is None:
            raise RuntimeError("archived run contract is missing")
        contract = json.load(handle)
    if (
        contract.get("seed") != seed
        or contract.get("run") != run
        or contract.get("status") != "TRAINED"
        or (seed == 20261019 and contract.get("sealed_test_accessed") is not False)
        or contract.get("artifacts", {}).get("weights", {}).get("best.pt", {}).get("sha256")
        != identity["weight"]["sha256"]
    ):
        raise RuntimeError("candidate run contract identity differs")
    qa_text = _file(identity["inference_result_qa"], "inference result QA").read_text(
        encoding="utf-8"
    )
    authorization = _file(identity["inference_authorization"], "inference authorization")
    auth_text = authorization.read_text(encoding="utf-8")
    run_qa_text = _file(identity["run_result_qa"], "run result QA").read_text(encoding="utf-8")
    if (
        "0.001" not in auth_text
        or identity["weight"]["sha256"] not in auth_text
        or sha256(authorization) not in qa_text
        or identity["weight"]["sha256"] not in qa_text
        or any(row["sha256"] not in qa_text for row in predictions.values())
    ):
        raise RuntimeError("inference authorization/QA does not bind all CSVs and weight")
    if seed == 20261018:
        # The historical pilot registry QA binds these three identities but
        # predates the S2-style archive/manifest hash table. The packager above
        # independently checks all eight archived members for both seeds.
        required = (
            identity["weight"]["sha256"],
            identity["run_contract"]["sha256"],
            identity["run_attestation_sha256"],
        )
    else:
        required = (
            identity["result_archive"]["sha256"],
            identity["result_manifest"]["sha256"],
            identity["weight"]["sha256"],
        )
    if any(digest not in run_qa_text for digest in required):
        raise RuntimeError("run result QA does not bind the candidate run")


def _bundle(bundle: Path) -> tuple[list, dict]:
    manifest_path = bundle / "manifest.json"
    if sha256(manifest_path) != BUNDLE_SHA256:
        raise RuntimeError("R3 bundle manifest hash differs")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("sealed_test_accessed") is not False
        or manifest.get("test_included") is not False
        or manifest.get("counts", {}).get("val") != {"images": 376, "boxes": 624}
    ):
        raise RuntimeError("R3 bundle scope differs")
    members = manifest["members"]
    selected = [
        name
        for name in members
        if name.startswith(("data/images/val/", "data/labels54/val/"))
        or name in ("data/val_groups.json", "data/classes.csv")
    ]
    for name in selected:
        if sha256(bundle / name) != members[name]["sha256"]:
            raise RuntimeError(f"R3 bundle member differs: {name}")
    frames = ci.gt_frames(bundle)
    return frames, {
        "bundle_manifest_sha256": BUNDLE_SHA256,
        "stems_sha256": _json_hash([f.stem for f in frames]),
        "ground_truth_sha256": _json_hash(
            [[f.stem, f.group_id, f.gt_classes.tolist(), f.gt_boxes.tolist()] for f in frames]
        ),
        "groups_sha256": members["data/val_groups.json"]["sha256"],
        "class_map_sha256": members["data/classes.csv"]["sha256"],
        "scorer_sha256": dict(zip(SCORER_PATHS, SCORER_SHA256, strict=True)),
        "images": 376,
        "gt_boxes": 624,
        "groups": 9,
    }


def _scorer(root: Path) -> None:
    for name, expected in zip(SCORER_PATHS, SCORER_SHA256, strict=True):
        if sha256(root / name) != expected:
            raise RuntimeError(f"common scorer hash differs: {name}")


def _frames_by_config(base: list, predictions: dict) -> dict:
    if set(predictions) != set(CONFIGS):
        raise RuntimeError("NMS grid differs")
    out = {}
    for name, row in predictions.items():
        path = _file(row, f"prediction {name}")
        out[name] = ci.with_predictions(base, path, "class_id", "confidence")
    return out


def _per_frame(frames: list, conf: float) -> list[dict]:
    stats = ci.frame_stats(frames, conf)
    return [
        {
            "stem": frame.stem,
            "group": frame.group_id,
            "gt": int(stats["gt"][i]),
            "tp": int(stats["agnostic_hits"][i]),
            "fp": int(stats["fp"][i]),
            "correct_class_hits": int(stats["aware_hits"][i]),
        }
        for i, frame in enumerate(frames)
    ]


def build_seed_report(
    seed: int, identity: dict, predictions: dict, bundle: Path, root: Path
) -> dict:
    """Recompute a seed report from pinned CSVs; no model is loaded."""
    if seed not in SEEDS or identity.get("inference_conf") != 0.001:
        raise RuntimeError("seed or candidate inference floor differs")
    if set(identity) != {
        "weight",
        "run_contract",
        "run_attestation_sha256",
        "result_archive",
        "result_manifest",
        "run_result_qa",
        "inference_authorization",
        "inference_result_qa",
        "inference_conf",
    }:
        raise RuntimeError("candidate identity is incomplete")
    for name, row in identity.items():
        if name in ("inference_conf", "run_attestation_sha256"):
            continue
        _qa(row) if name.endswith("qa") else _file(row, name)
    if (
        not isinstance(identity["run_attestation_sha256"], str)
        or len(identity["run_attestation_sha256"]) != 64
        or any(c not in "0123456789abcdef" for c in identity["run_attestation_sha256"])
    ):
        raise RuntimeError("run attestation SHA is invalid")
    _scorer(root)
    _run_binding(seed, identity, predictions, root)
    base, binding = _bundle(bundle)
    frames = _frames_by_config(base, predictions)
    sys.path.insert(0, str(root / "detector/colab"))
    import evaluate_cascade_b0_r1 as common

    configurations = {}
    for name in CONFIGS:
        items = frames[name]
        ap = common.average_precision(items)
        cells = []
        for conf in GRID:
            per_frame = _per_frame(items, conf)
            gt = sum(f["gt"] for f in per_frame)
            tp = sum(f["tp"] for f in per_frame)
            fp = sum(f["fp"] for f in per_frame)
            cells.append(
                {
                    "confidence": conf,
                    "per_frame": per_frame,
                    "tp": tp,
                    "fp": fp,
                    "correct_class_hits": sum(f["correct_class_hits"] for f in per_frame),
                    "agnostic_recall": tp / gt,
                    "fp_per_image": fp / len(per_frame),
                }
            )
        configurations[name] = {
            "iou": CONFIGS[name][0],
            "agnostic_nms": CONFIGS[name][1],
            "map50": ap["map50"],
            "map50_95": ap["map50_95"],
            "cells": cells,
        }
    return {
        "schema_version": 1,
        "seed": seed,
        "split": "val",
        "identity": identity,
        "binding": binding,
        "confidence_grid": list(GRID),
        "predictions": predictions,
        "configurations": configurations,
        "sealed_test_accessed": False,
    }


def _load_reports(paths: list[Path], bundle: Path, root: Path) -> tuple[list[dict], dict]:
    if len(paths) != 2:
        raise RuntimeError("exactly two R3 seed reports required")
    rows = []
    for path in paths:
        row = json.loads(path.read_text(encoding="utf-8"))
        if (
            row.get("schema_version") != 1
            or row.get("split") != "val"
            or row.get("sealed_test_accessed") is not False
            or row.get("confidence_grid") != list(GRID)
            or set(row.get("configurations", {})) != set(CONFIGS)
        ):
            raise RuntimeError("R3 report schema, grid or seal differs")
        rebuilt = build_seed_report(row["seed"], row["identity"], row["predictions"], bundle, root)
        if row != rebuilt:
            raise RuntimeError("R3 report values differ from pinned CSVs")
        rows.append(row)
    if {r["seed"] for r in rows} != set(SEEDS):
        raise RuntimeError("two-seed set differs")
    rows.sort(key=lambda r: r["seed"])
    if rows[0]["binding"] != rows[1]["binding"]:
        raise RuntimeError("R3 roster, GT, groups, class map, bundle or scorer differs")
    if rows[0]["identity"]["weight"]["sha256"] == rows[1]["identity"]["weight"]["sha256"]:
        raise RuntimeError("two distinct weights required")
    return rows, {str(p): sha256(p) for p in paths}


def _aggregate(rows: list[dict]) -> list[dict]:
    cells = []
    for name, (iou, agnostic) in CONFIGS.items():
        ap = [r["configurations"][name]["map50_95"] for r in rows]
        for index, confidence in enumerate(GRID):
            points = []
            for report in rows:
                frames = report["configurations"][name]["cells"][index]["per_frame"]
                gt = sum(f["gt"] for f in frames)
                points.append(
                    {
                        "agnostic_recall": sum(f["tp"] for f in frames) / gt,
                        "fp_per_image": sum(f["fp"] for f in frames) / len(frames),
                    }
                )
            cells.append(
                {
                    "configuration": name,
                    "iou": iou,
                    "agnostic_nms": agnostic,
                    "confidence": confidence,
                    "mean_agnostic_recall": sum(p["agnostic_recall"] for p in points) / 2,
                    "mean_fp_per_image": sum(p["fp_per_image"] for p in points) / 2,
                    "mean_map50_95": sum(ap) / 2,
                    "map50_95_by_seed": dict(zip((str(s) for s in SEEDS), ap, strict=True)),
                    "map50_95_difference_19_minus_18": ap[1] - ap[0],
                    "by_seed": dict(zip((str(s) for s in SEEDS), points, strict=True)),
                    "difference_19_minus_18": {
                        key: points[1][key] - points[0][key]
                        for key in ("agnostic_recall", "fp_per_image")
                    },
                }
            )
    return cells


def _ci_and_folds(
    rows: list[dict], chosen: dict, baseline: dict, bundle: Path
) -> tuple[dict | None, list[dict]]:
    base = ci.gt_frames(bundle)
    frames = {f"seed_{r['seed']}": _frames_by_config(base, r["predictions"]) for r in rows}
    sys.path.insert(0, str(sweep.COLAB))
    import evaluate_cascade_b0_r1 as common

    change = (
        provisional.bootstrap_change(frames, chosen, baseline)
        if chosen["configuration"] != BASE
        else None
    )
    folds = provisional.leave_one_group_out(frames, common)
    return change, folds


def select_lock(rows: list[dict], bundle: Path) -> dict:
    cells = _aggregate(rows)
    selected = provisional.choose(cells)
    baseline = provisional.choose([c for c in cells if c["configuration"] == BASE])
    if selected is None or baseline is None:
        raise RuntimeError("no eligible cell or baseline; no lock")
    change, folds = _ci_and_folds(rows, selected, baseline, bundle)
    votes = 0
    allowed = False
    if selected["configuration"] != BASE:
        votes = provisional.adjacent_votes(folds, selected["configuration"])
        assert change is not None
        allowed = (
            change["fp_per_image_ci95"][1] < 0 and change["map50_95_ci95"][1] >= 0 and votes >= 7
        )
    final = selected if (selected["configuration"] == BASE or allowed) else baseline
    return {
        "unrestricted_selected": selected,
        "baseline_selected": baseline,
        "change_test": change,
        "leave_one_group_out": folds,
        "adjacent_votes": votes,
        "change_allowed": allowed,
        "selected": final,
        "each_seed_recall_ge_0_85": {
            seed: p["agnostic_recall"] >= 0.85 for seed, p in final["by_seed"].items()
        },
    }


def _proof(paths: list[Path], bundle: Path, root: Path) -> dict:
    rows, hashes = _load_reports(paths, bundle, root)
    return {
        "schema_version": 2,
        "status": "R3_VALIDATION_PROOF",
        "seeds": list(SEEDS),
        "report_sha256": hashes,
        "binding": rows[0]["binding"],
        "decision": select_lock(rows, bundle),
        "sealed_test_accessed": False,
    }


def write(paths: list[Path], bundle: Path, root: Path, out: Path, proof_path: Path) -> dict:
    """Write the versioned lock only after input report and independent QA checks."""
    if out.exists() or proof_path.exists() or out == proof_path:
        raise FileExistsError("lock output exists")
    proof = _proof(paths, bundle, root)
    selected = proof["decision"]["selected"]
    record = {
        "schema_version": 2,
        "status": "LOCKED_ON_VAL",
        "seeds": list(SEEDS),
        "selection": {
            "conf": selected["confidence"],
            "nms_iou": selected["iou"],
            "agnostic_nms": selected["agnostic_nms"],
        },
        "candidates": [],
        "proof": {"path": str(proof_path), "sha256": ""},
        "sealed_test_seen": False,
    }
    for path in paths:
        report = json.loads(path.read_text(encoding="utf-8"))
        record["candidates"].append(
            {
                "seed": report["seed"],
                "weight": report["identity"]["weight"],
                "run_contract": report["identity"]["run_contract"],
                "run_attestation_sha256": report["identity"]["run_attestation_sha256"],
                "val_report": {"path": str(path), "sha256": sha256(path)},
                **record["selection"],
            }
        )
    record["candidates"].sort(key=lambda c: c["seed"])
    proof_path.write_text(json.dumps(proof, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    record["proof"]["sha256"] = sha256(proof_path)
    out.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return record


def verify(out: Path, proof_path: Path, bundle: Path, root: Path) -> dict:
    """Recompute from all bound CSVs and reject byte or semantic drift."""
    record = json.loads(out.read_text(encoding="utf-8"))
    saved = json.loads(proof_path.read_text(encoding="utf-8"))
    if out.read_bytes() != _canonical(record) or proof_path.read_bytes() != _canonical(saved):
        raise RuntimeError("lock or proof bytes differ from canonical serialization")
    if set(record) != {
        "schema_version",
        "status",
        "seeds",
        "selection",
        "candidates",
        "proof",
        "sealed_test_seen",
    }:
        raise RuntimeError("lock schema keys differ")
    if (
        record.get("schema_version") != 2
        or record.get("status") != "LOCKED_ON_VAL"
        or record.get("sealed_test_seen") is not False
        or saved.get("sealed_test_accessed") is not False
        or record.get("proof") != {"path": str(proof_path), "sha256": sha256(proof_path)}
    ):
        raise RuntimeError("lock or proof binding differs")
    paths = [Path(p) for p in saved["report_sha256"]]
    expected = _proof(paths, bundle, root)
    if saved != expected:
        raise RuntimeError("R3 proof differs from recomputation")
    selection = expected["decision"]["selected"]
    setting = {
        "conf": selection["confidence"],
        "nms_iou": selection["iou"],
        "agnostic_nms": selection["agnostic_nms"],
    }
    if record.get("selection") != setting or record.get("seeds") != list(SEEDS):
        raise RuntimeError("lock selection differs")
    candidates = record.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 2:
        raise RuntimeError("lock candidate count differs")
    if {c["val_report"]["path"] for c in candidates} != set(saved["report_sha256"]):
        raise RuntimeError("candidate reports differ from R3 proof")
    for candidate in candidates:
        if set(candidate) != {
            "seed",
            "weight",
            "run_contract",
            "run_attestation_sha256",
            "val_report",
            "conf",
            "nms_iou",
            "agnostic_nms",
        }:
            raise RuntimeError("candidate schema keys differ")
        if any(candidate.get(key) != value for key, value in setting.items()):
            raise RuntimeError("candidate setting differs")
        report_path = _file(candidate["val_report"], "candidate report")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if (
            candidate["seed"] != report["seed"]
            or candidate["weight"] != report["identity"]["weight"]
            or candidate["run_contract"] != report["identity"]["run_contract"]
            or candidate["run_attestation_sha256"] != report["identity"]["run_attestation_sha256"]
            or saved["report_sha256"].get(candidate["val_report"]["path"])
            != candidate["val_report"]["sha256"]
        ):
            raise RuntimeError("candidate identity differs")
    if {c["seed"] for c in candidates} != set(SEEDS):
        raise RuntimeError("candidate seed set differs")
    return record


def read_for_final(
    out: Path,
    proof_path: Path,
    bundle: Path,
    root: Path,
    weight_sha256: str,
    lock_result_qa: dict,
    owner_approval: dict,
) -> dict:
    """Read only a committed, independently QA'd and Owner-approved lock."""
    record = verify(out, proof_path, bundle, root)
    _qa(lock_result_qa)
    approval = _file(owner_approval, "Owner lock approval")
    for path in (out, proof_path, Path(lock_result_qa["path"]), approval):
        _committed_clean(path, root)
    record_hash, proof_hash = sha256(out), sha256(proof_path)
    for path in (Path(lock_result_qa["path"]), approval):
        content = path.read_text(encoding="utf-8")
        if record_hash not in content or proof_hash not in content:
            raise RuntimeError("QA or Owner approval does not bind record and proof hashes")
    if weight_sha256 not in {c["weight"]["sha256"] for c in record["candidates"]}:
        raise RuntimeError("weight is not a locked candidate")
    return record["selection"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build-report", "write", "verify"))
    parser.add_argument("--reports", nargs="*", type=Path, default=[])
    parser.add_argument("--seed", type=int)
    parser.add_argument("--identity", type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--proof", type=Path)
    args = parser.parse_args()
    if args.action == "build-report":
        if args.seed is None or args.identity is None or args.predictions is None:
            parser.error("build-report requires --seed, --identity and --predictions")
        if args.out.exists():
            raise FileExistsError("seed report already exists")
        report = build_seed_report(
            args.seed,
            json.loads(args.identity.read_text(encoding="utf-8")),
            json.loads(args.predictions.read_text(encoding="utf-8")),
            args.bundle,
            args.repo_root,
        )
        args.out.write_bytes(_canonical(report))
    elif args.action == "write":
        if args.proof is None:
            parser.error("write requires --proof")
        write(args.reports, args.bundle, args.repo_root, args.out, args.proof)
    else:
        if args.proof is None:
            parser.error("verify requires --proof")
        verify(args.out, args.proof, args.bundle, args.repo_root)


if __name__ == "__main__":
    main()
