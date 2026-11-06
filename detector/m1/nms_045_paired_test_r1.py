"""Paired validation test of per-class NMS IoU 0.45 against 0.70 for the D1 pilot (offline).

Contract: ``docs/review/d1_nms_045_paired_test_r1_contract.md``. Run from ``detector/`` with
``PYTHONPATH=. uv run --no-sync python -m m1.nms_045_paired_test_r1``. Reads the two QA-pinned
prediction CSVs of the NMS sweep R1; never runs inference, trains, opens sealed-test data, locks a
threshold or changes application policy.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from m1 import a3_pilot_paired_ci_r1 as ci
from m1 import nms_sweep_r1 as sweep
from m1.metrics import Frame, iou_matrix, match

PACKAGE = "D1-NMS-045-PAIRED-TEST-R1"
REPO = sweep.REPO
BUNDLE = sweep.BUNDLE
CSV_DIR = sweep.OUT
CANDIDATE, BASELINE = "classaware_0.45", "classaware_0.70"
CONF = 0.20
ROUNDS, SEED = 1000, 20261018
GT_PAIR_IOU = 0.45
OUT = REPO / "docs/review/generated/d1_nms_045_paired_test_r1.json"

PINS: dict[str, tuple[Path, str]] = {
    CANDIDATE: (
        CSV_DIR / f"predictions_{CANDIDATE}.csv",
        "eb95a5021e685c7ba60b173a184fd29535f114bcb8269916ba594e6c404261a5",
    ),
    BASELINE: (
        CSV_DIR / f"predictions_{BASELINE}.csv",
        "d4ae12e3116ad9ee80fb39f00174cdb44daf29ded7ada14ea2086b926e477a11",
    ),
    "nms_sweep_json": (
        REPO / "docs/review/generated/d1_nms_sweep_r1.json",
        "6be704d21edacd92aeb142f9fc4a5ffb6988686f24ebda9321224634f5460057",
    ),
    "nms_sweep_report": (
        REPO / "docs/review/d1_nms_sweep_r1_report.md",
        "cad83325fccddf31b8c05c7610c33bf008020389e5651b7a56dfa21ba17244e7",
    ),
    "nms_sweep_module": (
        REPO / "detector/m1/nms_sweep_r1.py",
        "0a114a495337bef898bddcbfa3711556f2d740f028d7150ca91a9029a7e4311e",
    ),
    "paired_ci_module": (
        REPO / "detector/m1/a3_pilot_paired_ci_r1.py",
        "7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4",
    ),
}
GATE = {
    BASELINE: {"tp": 547, "fp": 150, "correct": 457, "map50": 0.8521, "map50_95": 0.6089},
    CANDIDATE: {"tp": 547, "fp": 135, "correct": 457, "map50": 0.8543, "map50_95": 0.6095},
}


def check_pins() -> dict[str, str]:
    for name, (path, expected) in PINS.items():
        if path.is_symlink() or not path.is_file() or sweep.sha256(path) != expected:
            raise RuntimeError(f"pinned input differs: {name}")
    hashes = sweep.check_pins()  # bundle package, evaluation scope, scorer and metric modules
    sweep_json = json.loads(PINS["nms_sweep_json"][0].read_text(encoding="utf-8"))
    if (
        sweep_json.get("sealed_test_accessed") is not False
        or sweep_json["prediction_csv_sha256"].get(CANDIDATE) != PINS[CANDIDATE][1]
        or sweep_json["prediction_csv_sha256"].get(BASELINE) != PINS[BASELINE][1]
    ):
        raise RuntimeError("sweep JSON binding differs")
    return {**hashes, **{name: expected for name, (_, expected) in PINS.items()}}


def load_frames() -> dict[str, list[Frame]]:
    base = ci.gt_frames(BUNDLE)
    return {
        name: ci.with_predictions(base, PINS[name][0], "class_id", "confidence")
        for name in (CANDIDATE, BASELINE)
    }


def ap_pair(frames: Sequence[Frame], correct: Sequence[np.ndarray], index: np.ndarray) -> tuple:
    """Exact-class (mAP50, mAP50-95) from one ``ap_per_class`` call, as ``ci._map50_95``."""
    from ultralytics.utils.metrics import ap_per_class

    result = ap_per_class(
        np.concatenate([correct[i] for i in index]),
        np.concatenate([frames[i].pred_scores for i in index]),
        np.concatenate([frames[i].pred_classes for i in index]),
        np.concatenate([frames[i].gt_classes for i in index]),
        plot=False,
        names={i: str(i) for i in range(ci.CLASSES)},
    )
    ap = result[5]
    return float(ap[:, 0].mean()), float(ap.mean())


def gate(frames: dict[str, list[Frame]], common: Any) -> dict:
    evidence = {}
    for name, expected in GATE.items():
        p = sweep.point(frames[name], CONF)
        ap = common.average_precision(frames[name])
        ok = (
            p["tp"] == expected["tp"]
            and p["fp"] == expected["fp"]
            and p["correct_class_hits"] == expected["correct"]
            and abs(ap["map50"] - expected["map50"]) <= 1e-4
            and abs(ap["map50_95"] - expected["map50_95"]) <= 1e-4
        )
        evidence[name] = {"passed": bool(ok), "point": p, "ap": ap}
        if not ok:
            raise RuntimeError("gate 0 failed: " + json.dumps(evidence, ensure_ascii=False))
    return evidence


def _interval(values: Sequence[float], point: float) -> dict:
    return {
        "difference": float(point),
        "ci95": ci.ci95(values),
        "share_rounds_below_zero": float(np.mean(np.asarray(values) < 0)),
    }


def paired(cand: list[Frame], base: list[Frame]) -> dict:
    samples = ci.resample_indices(base, ROUNDS, SEED)
    sc, sb = ci.frame_stats(cand, CONF), ci.frame_stats(base, CONF)
    full = np.arange(len(base))
    out: dict[str, Any] = {"rounds": ROUNDS, "seed": SEED, "unit": "D-02 group", "paired": True}
    for metric in ("fp_per_image", "correct_class_recall", "agnostic_recall"):
        pc, pb = ci.summarize(sc, full)[metric], ci.summarize(sb, full)[metric]
        diffs = [ci.summarize(sc, s)[metric] - ci.summarize(sb, s)[metric] for s in samples]
        out[metric] = {"candidate": float(pc), "baseline": float(pb), **_interval(diffs, pc - pb)}
    cc, cb = ci._correct_matrices(cand), ci._correct_matrices(base)
    pc50, pc5095 = ap_pair(cand, cc, full)
    pb50, pb5095 = ap_pair(base, cb, full)
    d50, d5095 = [], []
    for s in samples:
        c50, c5095 = ap_pair(cand, cc, s)
        b50, b5095 = ap_pair(base, cb, s)
        d50.append(c50 - b50)
        d5095.append(c5095 - b5095)
    out["map50"] = {"candidate": pc50, "baseline": pb50, **_interval(d50, pc50 - pb50)}
    out["map50_95"] = {"candidate": pc5095, "baseline": pb5095, **_interval(d5095, pc5095 - pb5095)}
    return out


def per_group(cand: list[Frame], base: list[Frame]) -> list[dict]:
    sc, sb = ci.frame_stats(cand, CONF), ci.frame_stats(base, CONF)
    rows = []
    for group in sorted(set(sb["group"].tolist())):
        idx = np.flatnonzero(sb["group"] == group)
        row: dict[str, Any] = {
            "group": group,
            "frames": int(len(idx)),
            "gt": int(sb["gt"][idx].sum()),
        }
        for label, field in (
            ("fp", "fp"),
            ("correct", "aware_hits"),
            ("agnostic", "agnostic_hits"),
        ):
            c, b = int(sc[field][idx].sum()), int(sb[field][idx].sum())
            row[label] = {"candidate": c, "baseline": b, "difference": c - b}
        rows.append(row)
    return rows


def _choose(fit: dict[str, list[Frame]], common: Any) -> str | None:
    scored = []
    for name, frames in fit.items():
        p = sweep.point(frames, CONF)
        if p["agnostic_recall"] >= 0.85:
            ap = common.average_precision(frames)["map50_95"]
            scored.append((p["fp_per_image"], -ap, 0 if name == BASELINE else 1, name))
    return min(scored)[3] if scored else None


def leave_one_group_out(cand: list[Frame], base: list[Frame], common: Any) -> list[dict]:
    folds = []
    for held in sorted({f.group_id for f in base}):
        fit = {
            CANDIDATE: [f for f in cand if f.group_id != held],
            BASELINE: [f for f in base if f.group_id != held],
        }
        held_points = {
            name: sweep.point([f for f in frames if f.group_id == held], CONF)
            for name, frames in ((CANDIDATE, cand), (BASELINE, base))
        }
        folds.append(
            {
                "held_out_group": held,
                "selection": _choose(fit, common),
                "held_out": {
                    name: {k: p[k] for k in ("tp", "fp", "correct_class_hits", "fp_per_image")}
                    for name, p in held_points.items()
                },
            }
        )
    return folds


def _key(box: np.ndarray, cls: int, score: float) -> tuple:
    return (int(cls), round(float(score), 7), *(round(float(v), 3) for v in box))


def box_audit(cand: list[Frame], base: list[Frame]) -> dict:
    removed = added = 0
    changed_frames = []
    for fc, fb in zip(cand, base, strict=True):
        kc = {
            _key(b, c, s)
            for b, c, s in zip(fc.pred_boxes, fc.pred_classes, fc.pred_scores, strict=True)
            if s >= CONF
        }
        kb = {
            _key(b, c, s)
            for b, c, s in zip(fb.pred_boxes, fb.pred_classes, fb.pred_scores, strict=True)
            if s >= CONF
        }
        removed += len(kb - kc)
        added += len(kc - kb)
        mc_a, _ = match(fc, CONF, class_aware=False)
        mb_a, _ = match(fb, CONF, class_aware=False)
        mc_c, _ = match(fc, CONF, class_aware=True)
        mb_c, _ = match(fb, CONF, class_aware=True)
        if (mc_a != mb_a).any() or (mc_c != mb_c).any():
            changed_frames.append(fc.stem)
    return {
        "boxes_at_conf_020_removed_by_0_45": removed,
        "boxes_at_conf_020_added_by_0_45": added,
        "frames_with_changed_gt_matches": changed_frames,
    }


def gt_pair_exposure(cand: list[Frame], base: list[Frame]) -> dict:
    pairs = lost_candidate = lost_baseline = 0
    gt_in_pairs = 0
    detail = []
    for fc, fb in zip(cand, base, strict=True):
        if len(fb.gt_boxes) < 2:
            continue
        overlap = iou_matrix(fb.gt_boxes, fb.gt_boxes)
        involved = set()
        for i in range(len(fb.gt_boxes)):
            for j in range(i + 1, len(fb.gt_boxes)):
                if overlap[i, j] >= GT_PAIR_IOU:
                    pairs += 1
                    involved.update((i, j))
        if not involved:
            continue
        mc, _ = match(fc, CONF, class_aware=False)
        mb, _ = match(fb, CONF, class_aware=False)
        for i in sorted(involved):
            gt_in_pairs += 1
            if mb[i] and not mc[i]:
                lost_candidate += 1
            if mc[i] and not mb[i]:
                lost_baseline += 1
            detail.append(
                {
                    "stem": fb.stem,
                    "gt_index": i,
                    "matched_0_70": bool(mb[i]),
                    "matched_0_45": bool(mc[i]),
                }
            )
    return {
        "gt_pair_iou_threshold": GT_PAIR_IOU,
        "pairs": pairs,
        "gt_in_pairs": gt_in_pairs,
        "matched_at_0_70_but_not_0_45": lost_candidate,
        "matched_at_0_45_but_not_0_70": lost_baseline,
        "detail": detail,
    }


def decide(test: dict, groups: list[dict], folds: list[dict], exposure: dict) -> dict:
    conditions = {
        "c1_fp_ci_upper_below_zero": test["fp_per_image"]["ci95"][1] < 0,
        "c2_no_group_loses_correct_hits": all(g["correct"]["difference"] >= 0 for g in groups),
        "c3_agnostic_recall_ok": test["agnostic_recall"]["candidate"] >= 0.85
        and test["agnostic_recall"]["difference"] >= 0,
        "c4_map50_95_ci_not_wholly_below_zero": test["map50_95"]["ci95"][1] >= 0,
        "c5_logo_selects_0_45_in_7_of_9": sum(f["selection"] == CANDIDATE for f in folds) >= 7,
        "c6_no_group_gains_fp": all(g["fp"]["difference"] <= 0 for g in groups),
        "c7_no_paired_gt_lost": exposure["matched_at_0_70_but_not_0_45"] == 0,
    }
    decision = "SUPPORTED_ON_VALIDATION" if all(conditions.values()) else "NOT_SUPPORTED"
    return {
        "conditions": conditions,
        "failed": [k for k, v in conditions.items() if not v],
        "decision": decision,
    }


def run() -> dict:
    pins = check_pins()
    import evaluate_cascade_b0_r1 as common  # on sys.path after sweep.check_pins()

    frames = load_frames()
    cand, base = frames[CANDIDATE], frames[BASELINE]
    evidence = gate(frames, common)
    test = paired(cand, base)
    groups = per_group(cand, base)
    folds = leave_one_group_out(cand, base, common)
    exposure = gt_pair_exposure(cand, base)
    verdict = decide(test, groups, folds, exposure)
    result = {
        "package": PACKAGE,
        "scope": "validation R3 only; in-sample, post hoc; one pilot checkpoint",
        "candidate": CANDIDATE,
        "baseline": BASELINE,
        "confidence": CONF,
        "frames": 376,
        "gt_boxes": 624,
        "groups": 9,
        "input_sha256": pins,
        "gate0": evidence,
        "paired_test": test,
        "per_group": groups,
        "leave_one_group_out": folds,
        "logo_selects_candidate": sum(f["selection"] == CANDIDATE for f in folds),
        "box_audit": box_audit(cand, base),
        "gt_pair_exposure": exposure,
        "focus": {name: sweep.point(frames[name], CONF)["focus"] for name in (CANDIDATE, BASELINE)},
        **verdict,
        "replication_required": "seed 20261019 model, same contract, before any lock proposal",
        "inference_run": False,
        "thresholds_locked": False,
        "sealed_test_accessed": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("x", encoding="utf-8") as sink:
        json.dump(result, sink, indent=2, ensure_ascii=False, allow_nan=False)
        sink.write("\n")
    return result


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    result = run()
    print(json.dumps({k: result[k] for k in ("decision", "failed", "logo_selects_candidate")}))


if __name__ == "__main__":
    main()
