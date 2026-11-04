"""Offline evaluation of Temporal Dynamic Threshold R1 for D1 YOLO11s-54.

Subcommands:
- ``val``: evaluation A on pinned DATASET01 val predictions (no inference).
- ``mini-infer``: D1 conf-0.001 inference on the hash-pinned PHENIKAA Mini front clip only.
- ``mini-score``: evaluation B, two-class R2 diagnostic (DEMO_ONLY).

Parameters are the pre-registered ones in docs/review/temporal_threshold_r1_report.md §1.
No training, no app activation, sealed test untouched.
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for extra in (ROOT / "src", ROOT / "detector"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from cpv301_autodrive import temporal_threshold as tt  # noqa: E402
from cpv301_autodrive.review2_temporal_r1 import track_prediction_rows  # noqa: E402

GENERATED = ROOT / "docs/review/generated"
VAL_OUT = GENERATED / "temporal_threshold_r1_val.json"
MINI_OUT = GENERATED / "temporal_threshold_r1_mini.json"
MINI_DIR = ROOT / "data/processed/temporal_threshold_r1_mini"
MINI_PRED = MINI_DIR / "ROUNDABOUT_CAM_P_F_D1_conf0001_step2.csv"
MINI_MANIFEST = MINI_DIR / "ROUNDABOUT_CAM_P_F_D1_conf0001_step2.manifest.json"
MINI_SOURCE = ROOT / "data/processed/phenikaa_front_demo_r1/ROUNDABOUT_CAM_P_F.mp4"
MINI_SOURCE_SHA256 = "1fab75937ceba286abbc308138a814a7d9548b722184d4735b802f29d4b1f5ac"
MINI_LABELS = ROOT / "tmp/review2_annotation_packet_r1/frame_diagnostic_candidate_r2_v2.json"
MINI_LABELS_SHA256 = "b90710ee30d5d33bf42f751e8774a567b666dae17c3d4570183d1f4f1a2848c1"
MINI_PINNED_020 = ROOT / "tmp/review2_full_upload_smoke_r1/predictions.csv"
MINI_PINNED_020_SHA256 = "343e00c3ca91ad8e1d956196086964c2d41349fb99411ad0738a6b05f3dd46e9"
MINI_STEP = 2
CLASS_MAP = ROOT / "docs/review/generated/m1_yolo_classes.csv"
BASELINE_CONF = 0.20
FOCUS_CLASSES = (7, 32, 41, 46, 10, 12)
BOOT_ROUNDS = 1000
BOOT_SEED = 20261018
SOURCE_PINS = (
    "src/cpv301_autodrive/temporal_threshold.py",
    "src/cpv301_autodrive/review2_temporal_r1.py",
    "detector/m1/metrics.py",
    "detector/m1/dynamic_threshold_r2_r1.py",
    "detector/m1/val_reeval_r2.py",
    "scripts/evaluate_temporal_threshold_r1.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path: Path, payload: dict) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def source_pins() -> dict[str, str]:
    return {name: sha256(ROOT / name) for name in SOURCE_PINS}


# --------------------------------------------------------------------------- evaluation A


def wp_sequences() -> dict[str, str]:
    """stem -> WP16-WP21 reviewed proxy sequence id (all reviewed rows are CONTINUOUS_CANDIDATE)."""
    paths = sorted(
        glob.glob(str(ROOT / "docs/review/wp1[6-9]_sequence_review_annotations_*.json"))
        + glob.glob(str(ROOT / "docs/review/wp2[01]*sequence*annotations*.json"))
    )
    member: dict[str, str] = {}
    for path in paths:
        for decision in json.loads(Path(path).read_text(encoding="utf-8"))["decisions"]:
            if decision["capture_sequence"] != "CONTINUOUS_CANDIDATE":
                continue
            for stem in decision["members"]:
                member[stem] = decision["proxy_sequence_id"]
    return member


def segments(frames, *, reviewed_only: bool) -> list[list[int]]:
    """Consecutive stems inside one D-02 group; optionally also cut outside reviewed runs."""
    member = wp_sequences() if reviewed_only else {}
    out: list[list[int]] = []
    for index, frame in enumerate(frames):
        if out:
            prev = frames[out[-1][-1]]
            same = prev.group_id == frame.group_id and int(frame.stem) - int(prev.stem) == 1
            if same and reviewed_only:
                same = member.get(prev.stem) is not None and member.get(prev.stem) == member.get(
                    frame.stem
                )
            if same:
                out[-1].append(index)
                continue
        out.append([index])
    return out


def sequence_audit(frames) -> dict:
    from m1.metrics import iou_matrix

    member = wp_sequences()
    edges = {}
    with (GENERATED / "grouping_proxy_edges.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            edges[row["left_stem"], row["right_stem"]] = row
    gaps, kinds, maes, ious = [], Counter(), [], []
    for a, b in zip(frames, frames[1:], strict=False):
        if a.group_id != b.group_id:
            continue
        step = int(b.stem) - int(a.stem)
        if step != 1:
            gaps.append({"group": a.group_id, "left": a.stem, "right": b.stem, "stem_gap": step})
            continue
        same = member.get(a.stem) is not None and member.get(a.stem) == member.get(b.stem)
        edge = edges.get((a.stem, b.stem))
        kinds[
            "inside_reviewed_continuous_sequence"
            if same
            else f"not_inside_reviewed_sequence:{edge['proxy_status'] if edge else 'no_edge'}"
        ] += 1
        if edge:
            maes.append(float(edge["thumbnail_mae"]))
        m = iou_matrix(a.gt_boxes, b.gt_boxes)
        for i, cls in enumerate(a.gt_classes.tolist()):
            same_cls = [m[i, j] for j, c in enumerate(b.gt_classes.tolist()) if c == cls]
            ious.append(max(same_cls) if same_cls else -1.0)
    ious_arr = np.asarray(ious)
    present = ious_arr[ious_arr >= 0]
    stems_sorted = all(int(b.stem) > int(a.stem) for a, b in zip(frames, frames[1:], strict=False))
    return {
        "frames": len(frames),
        "groups": len({f.group_id for f in frames}),
        "stems_strictly_increasing_in_loader_order": stems_sorted,
        "adjacent_same_group_pairs_with_stem_step_1": sum(kinds.values()),
        "stem_gaps_inside_groups": gaps,
        "adjacent_pair_kinds": dict(sorted(kinds.items())),
        "proxy_thumbnail_mae_median": float(np.median(maes)) if maes else None,
        "gt_transitions": int(len(ious_arr)),
        "gt_transitions_without_same_class_next": int((ious_arr < 0).sum()),
        "gt_same_class_next_iou_ge_050": int((ious_arr >= 0.5).sum()),
        "gt_same_class_next_iou_ge_030": int((ious_arr >= 0.3).sum()),
        "gt_same_class_next_iou_gt_0": int((ious_arr > 0).sum()),
        "gt_same_class_next_iou_quartiles": [
            float(x) for x in np.percentile(present, [25, 50, 75])
        ],
    }


def temporal_frames(frames, segs, params: tt.TemporalParams):
    """Return converted m1 Frames (emitted boxes, track label, S_t) and run statistics."""
    out = list(frames)
    reasons, tracks = Counter(), []
    elapsed = 0
    for seg in segs:
        seq = [
            tt.SequenceFrame(
                frames[i].stem,
                tuple(
                    tt.Candidate(int(c), float(s), tuple(map(float, b)))
                    for b, c, s in zip(
                        frames[i].pred_boxes,
                        frames[i].pred_classes,
                        frames[i].pred_scores,
                        strict=True,
                    )
                ),
            )
            for i in seg
        ]
        start = time.perf_counter_ns()
        result = tt.run_sequence(seq, params)
        elapsed += time.perf_counter_ns() - start
        tracks.extend(result.tracks)
        for t, i in enumerate(seg):
            reasons.update(d.reason for d in result.decisions[t])
            kept = result.emitted(t)
            out[i] = replace(
                frames[i],
                pred_boxes=np.asarray([d.candidate.box for d in kept], dtype=float).reshape(-1, 4),
                pred_classes=np.asarray([d.label for d in kept], dtype=int),
                pred_scores=np.asarray([d.track_score for d in kept], dtype=float),
            )
    stats = {
        "decision_reasons": dict(sorted(reasons.items())),
        "tracks": len(tracks),
        "tracks_confirmed": sum(t.confirmed_frame is not None for t in tracks),
        "track_label_switches_total": sum(t.label_switches for t in tracks),
        "postprocess_ms_total_local": round(elapsed / 1e6, 3),
    }
    return out, stats


def per_frame_counts(frames, conf: float) -> np.ndarray:
    """Columns: gt, localized hit, correct-class hit, false positives (via metrics)."""
    from m1.metrics import match, operating_point

    rows = []
    for frame in frames:
        point = operating_point([frame], conf)
        correct = int(match(frame, conf, class_aware=True)[0].sum())
        rows.append((point.ground_truth, point.true_positives, correct, point.false_positives))
    return np.asarray(rows, dtype=float)


def summarize(frames, conf: float) -> dict:
    from m1.metrics import match, operating_point

    point = operating_point(frames, conf)
    correct = sum(int(match(f, conf, class_aware=True)[0].sum()) for f in frames)
    return {
        "images": point.images,
        "ground_truth": point.ground_truth,
        "localized_gt": point.true_positives,
        "correct_class_gt": correct,
        "false_positives": point.false_positives,
        "detection_recall": point.agnostic_recall,
        "correct_class_recall": correct / point.ground_truth,
        "fp_per_image": point.fp_per_image,
        "precision": point.precision,
        "per_class": {
            str(c): {
                "support": point.per_class_support.get(c, 0),
                "correct_class_hits": point.per_class_hits.get(c, 0),
            }
            for c in FOCUS_CLASSES
        },
    }


def fp_budget(frames, temporal: dict) -> dict:
    grid = [round(x, 2) for x in np.arange(0.05, 0.951, 0.01)]
    points = {c: summarize(frames, c) for c in grid}
    within = [c for c in grid if points[c]["fp_per_image"] <= temporal["fp_per_image"] + 1e-12]
    reach = [
        c for c in grid if points[c]["detection_recall"] >= temporal["detection_recall"] - 1e-12
    ]
    pick = min(within) if within else None
    match_recall = max(reach) if reach else None
    strip = ("per_class",)
    return {
        "rule": "lowest fixed conf on 0.05..0.95 step 0.01 with FP/image <= temporal (§1a)",
        "fixed_at_same_fp_budget": (
            {"conf": pick, **{k: v for k, v in points[pick].items() if k not in strip}}
            if pick is not None
            else None
        ),
        "fixed_reaching_temporal_detection_recall": (
            {
                "conf": match_recall,
                **{k: v for k, v in points[match_recall].items() if k not in strip},
            }
            if match_recall is not None
            else None
        ),
    }


def gt_track_switches(frames, segs, predicted, conf: float, params: tt.TemporalParams) -> dict:
    """Label switches of matched predictions along GT tracks inferred with the same R1 linker."""
    from m1.metrics import _greedy_pairs

    switches, tracks_ge2, tracks_with_switch, matched_frames = 0, 0, 0, 0
    for seg in segs:
        rows = []
        for t, i in enumerate(seg):
            for g, (box, cls) in enumerate(
                zip(frames[i].gt_boxes, frames[i].gt_classes, strict=True)
            ):
                rows.append(
                    {
                        "source_frame": t,
                        "time_ms_nominal": t,
                        "code": str(int(cls)),
                        "name_vi": "",
                        "x1": box[0],
                        "y1": box[1],
                        "x2": box[2],
                        "y2": box[3],
                        "_frame": i,
                        "_gt": g,
                    }
                )
        linked, _ = track_prediction_rows(
            rows,
            sample_step=1,
            iou_min=params.link_iou,
            max_missing_samples=params.max_miss - 1,
            predict_motion=params.predict_motion,
        )
        pairs = {}
        for i in seg:
            frame = predicted[i]
            pairs[i] = {g: int(frame.pred_classes[p]) for g, p in _greedy_pairs(frame, conf)[0]}
        sequence: dict[int, list[int]] = defaultdict(list)
        for row in sorted(linked, key=lambda r: r["source_frame"]):
            label = pairs[row["_frame"]].get(row["_gt"])
            if label is not None:
                sequence[int(row["track_id"])].append(label)
        for labels in sequence.values():
            matched_frames += len(labels)
            if len(labels) < 2:
                continue
            tracks_ge2 += 1
            n = sum(a != b for a, b in zip(labels, labels[1:], strict=False))
            switches += n
            tracks_with_switch += bool(n)
    return {
        "gt_tracks_with_ge2_matched_frames": tracks_ge2,
        "label_switches_total": switches,
        "gt_tracks_with_any_switch": tracks_with_switch,
        "switches_per_gt_track_ge2": switches / tracks_ge2 if tracks_ge2 else None,
        "matched_gt_frames": matched_frames,
    }


def paired_bootstrap(frames, base_counts, temp_counts) -> dict:
    groups: dict[str, list[int]] = defaultdict(list)
    for i, frame in enumerate(frames):
        groups[frame.group_id].append(i)
    names = sorted(groups)
    rng = np.random.default_rng(BOOT_SEED)
    deltas = defaultdict(list)
    for _ in range(BOOT_ROUNDS):
        idx = [i for g in rng.choice(names, size=len(names), replace=True) for i in groups[g]]
        b, t = base_counts[idx].sum(0), temp_counts[idx].sum(0)
        deltas["detection_recall"].append(t[1] / t[0] - b[1] / b[0])
        deltas["correct_class_recall"].append(t[2] / t[0] - b[2] / b[0])
        deltas["fp_per_image"].append((t[3] - b[3]) / len(idx))
    return {
        "unit": "D-02 group (9 groups), paired resampling",
        "rounds": BOOT_ROUNDS,
        "seed": BOOT_SEED,
        "delta_temporal_minus_baseline_ci95": {
            k: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
            for k, v in deltas.items()
        },
    }


def lost_recovered(frames, predicted) -> dict:
    from m1.metrics import match

    lost, recovered, lost_loc, recovered_loc = Counter(), Counter(), 0, 0
    for frame, new in zip(frames, predicted, strict=True):
        old_c = match(frame, BASELINE_CONF, True)[0]
        new_c = match(new, 0, True)[0]
        old_l = match(frame, BASELINE_CONF, False)[0]
        new_l = match(new, 0, False)[0]
        for cls, a, b in zip(
            frame.gt_classes.tolist(), old_c.tolist(), new_c.tolist(), strict=True
        ):
            if a and not b:
                lost[int(cls)] += 1
            if b and not a:
                recovered[int(cls)] += 1
        lost_loc += int(np.count_nonzero(old_l & ~new_l))
        recovered_loc += int(np.count_nonzero(~old_l & new_l))
    return {
        "correct_class_gt_lost_vs_baseline": sum(lost.values()),
        "correct_class_gt_recovered_vs_baseline": sum(recovered.values()),
        "localized_gt_lost_vs_baseline": lost_loc,
        "localized_gt_recovered_vs_baseline": recovered_loc,
        "lost_by_class": {str(k): v for k, v in sorted(lost.items())},
        "recovered_by_class": {str(k): v for k, v in sorted(recovered.items())},
    }


def short(summary: dict) -> dict:
    return {
        k: summary[k]
        for k in (
            "localized_gt",
            "correct_class_gt",
            "false_positives",
            "detection_recall",
            "correct_class_recall",
            "fp_per_image",
            "precision",
        )
    }


def evaluate_val() -> dict:
    from m1 import dynamic_threshold_r2_r1 as inputs

    frames, pins = inputs.load_frames(ROOT)
    baseline = summarize(frames, BASELINE_CONF)
    expected = (547, 150, 457, 624)
    got = (
        baseline["localized_gt"],
        baseline["false_positives"],
        baseline["correct_class_gt"],
        baseline["ground_truth"],
    )
    if (
        got != expected
        or round(baseline["detection_recall"], 4) != 0.8766
        or round(baseline["fp_per_image"], 4) != 0.3989
    ):
        raise RuntimeError(f"baseline 0.20 not reproduced: {got}")
    audit = sequence_audit(frames)
    segs = segments(frames, reviewed_only=False)
    params = tt.PRIMARY
    predicted, stats = temporal_frames(frames, segs, params)
    temporal = summarize(predicted, 0)
    base_counts = per_frame_counts(frames, BASELINE_CONF)
    temp_counts = per_frame_counts(predicted, 0)
    if tuple(base_counts.sum(0).astype(int)) != (624, 547, 457, 150):
        raise RuntimeError("per-frame baseline counts disagree with operating_point")

    sensitivity = []
    variants = (
        [("enter", v) for v in (0.25, 0.30, 0.40, 0.50)]
        + [("keep", v) for v in (0.10, 0.20)]
        + [("window", v) for v in (3, 7)]
        + [("max_miss", v) for v in (1, 3)]
        + [("link_iou", 0.50)]
    )
    for axis, value in variants:
        variant = replace(params, **{axis: value})
        if variant.keep > variant.enter:
            continue
        frames_v, stats_v = temporal_frames(frames, segs, variant)
        sensitivity.append(
            {
                "axis": axis,
                "value": value,
                **short(summarize(frames_v, 0)),
                "tracks_confirmed": stats_v["tracks_confirmed"],
            }
        )
    reviewed = segments(frames, reviewed_only=True)
    frames_r, _ = temporal_frames(frames, reviewed, params)

    return {
        "package": "TEMPORAL_DT_R1_EVAL_A_VAL",
        "status": "PROVISIONAL_RESULT_INDEPENDENT_QA_PENDING",
        "scope": (
            "DATASET01 val, 1 seed (D1 pilot), sequences inferred from consecutive stems; "
            "not a D-05 acceptance and not an independent holdout"
        ),
        "params_primary": params.__dict__,
        "preregistration": "docs/review/temporal_threshold_r1_report.md §1/§1a",
        "inputs_sha256": {
            **pins,
            "r3_label_roster": "dc72ebd944a38535d4f766ba4f8babc60cb6732dfcd253ed0e8d79dc86eb8343",
        },
        "source_sha256": source_pins(),
        "sequence_audit": audit,
        "segments_primary": len(segs),
        "segments_reviewed_only_variant": len(reviewed),
        "baseline_fixed_020": baseline,
        "temporal_primary": temporal,
        "temporal_run_stats": stats,
        "fp_budget_comparison": fp_budget(frames, temporal),
        "lost_recovered": lost_recovered(frames, predicted),
        "gt_track_label_switches": {
            "baseline_fixed_020": gt_track_switches(frames, segs, frames, BASELINE_CONF, params),
            "temporal_primary": gt_track_switches(frames, segs, predicted, 0, params),
        },
        "paired_bootstrap": paired_bootstrap(frames, base_counts, temp_counts),
        "sensitivity_report_only": sensitivity,
        "reviewed_sequence_segmentation_variant": short(summarize(frames_r, 0)),
        "sealed_test_accessed": False,
        "app_activation": False,
    }


# --------------------------------------------------------------------------- evaluation B


def mini_infer() -> dict:
    """D1 at conf 0.001 on every second frame of the pinned Mini clip (inference only)."""
    import cv2
    from PIL import Image

    from cpv301_autodrive.detector_d1_r3 import (
        CLASS_MAP_SHA256,
        IMGSZ,
        NMS_IOU,
        WEIGHTS_SHA256,
        D1Detector,
    )

    if sha256(MINI_SOURCE) != MINI_SOURCE_SHA256:
        raise RuntimeError("Mini source clip hash differs")
    MINI_DIR.mkdir(parents=True, exist_ok=True)
    for path in (MINI_PRED, MINI_MANIFEST):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite: {path}")
    detector = D1Detector()
    capture = cv2.VideoCapture(str(MINI_SOURCE))
    rows, decoded, sampled = [], 0, 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if decoded % MINI_STEP == 0:
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            for rank, det in enumerate(detector.detect(image, conf=0.001)):
                rows.append(
                    {
                        "source_frame": decoded,
                        "rank": rank,
                        "yolo_id": det.sign.yolo_id,
                        "code": det.sign.code,
                        "score": f"{det.confidence:.6f}",
                        **{
                            k: f"{v:.2f}"
                            for k, v in zip(("x1", "y1", "x2", "y2"), det.box, strict=True)
                        },
                    }
                )
            sampled += 1
        decoded += 1
    capture.release()
    with MINI_PRED.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "package": "TEMPORAL_DT_R1_MINI_D1_CONF0001",
        "status": "DEMO_ONLY",
        "command": "uv run python scripts/evaluate_temporal_threshold_r1.py mini-infer",
        "source_sha256": MINI_SOURCE_SHA256,
        "source_frames_decoded": decoded,
        "sample_every_n_frames": MINI_STEP,
        "sampled_frames": sampled,
        "model_sha256": WEIGHTS_SHA256,
        "class_map_sha256": CLASS_MAP_SHA256,
        "detector": "cpv301_autodrive.detector_d1_r3.D1Detector",
        "imgsz": IMGSZ,
        "nms_iou": NMS_IOU,
        "confidence": 0.001,
        "device": detector.device,
        "prediction_rows": len(rows),
        "prediction_csv_sha256": sha256(MINI_PRED),
        "training": False,
        "ground_truth_sign_labels": False,
        "sealed_test_accessed": False,
    }
    with MINI_MANIFEST.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    return manifest


def _iou(a, b) -> float:
    left, top = max(a[0], b[0]), max(a[1], b[1])
    right, bottom = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, right - left) * max(0.0, bottom - top)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


TARGET = {"1": "W.205c", "10": "P.130"}


def score_two_class(frames_out: dict[int, list[dict]], labels: dict) -> dict:
    """R2 scorer rules: class-specific score-ordered matching; target before ignore."""
    totals = {code: Counter() for code in TARGET.values()}
    ignored, other_on_target = Counter(), Counter()
    unscored = 0
    for record in labels["frame_records"]:
        fid = record["source_video_frame"]
        rows = frames_out.get(fid, [])
        gt = defaultdict(list)
        for target in record["in_scope_boxes"]:
            gt[TARGET[target["derived_key"]]].append(tuple(target["box"]))
        all_targets = [b for boxes in gt.values() for b in boxes]
        for code in TARGET.values():
            matched: set[int] = set()
            for row in sorted((r for r in rows if r["code"] == code), key=lambda r: -r["score"]):
                best = max(
                    ((_iou(row["box"], b), i) for i, b in enumerate(gt[code]) if i not in matched),
                    default=(0.0, -1),
                )
                if best[0] >= 0.5:
                    matched.add(best[1])
                    totals[code]["tp"] += 1
                elif any(_iou(row["box"], b) >= 0.5 for b in all_targets):
                    totals[code]["fp_wrong_target_class_or_duplicate"] += 1
                elif any(
                    _iou(row["box"], tuple(r["box"])) >= 0.5 for r in record["ignore_regions"]
                ):
                    ignored["target_code"] += 1
                else:
                    totals[code]["fp"] += 1
            totals[code]["fn"] += len(gt[code]) - len(matched)
            totals[code]["gt"] += len(gt[code])
        for row in rows:
            if row["code"] in TARGET.values():
                continue
            if any(_iou(row["box"], b) >= 0.5 for b in all_targets):
                other_on_target[row["code"]] += 1
            elif any(_iou(row["box"], tuple(r["box"])) >= 0.5 for r in record["ignore_regions"]):
                ignored["other_class"] += 1
            else:
                unscored += 1
    by_class = {}
    for code, c in totals.items():
        fp = c["fp"] + c["fp_wrong_target_class_or_duplicate"]
        by_class[code] = {
            "gt": c["gt"],
            "tp": c["tp"],
            "fp": fp,
            "fn": c["fn"],
            "fp_wrong_target_class_or_duplicate": c["fp_wrong_target_class_or_duplicate"],
        }
    return {
        "by_class": by_class,
        "other_class_on_target": dict(sorted(other_on_target.items())),
        "ignored": dict(ignored),
        "unscored_other_class": unscored,
    }


def gt_events(labels: dict) -> list[dict]:
    """Contiguous runs of a target code over evaluable sampled frames, linked by the R1 linker."""
    rows = []
    for record in labels["frame_records"]:
        fid = record["source_video_frame"]
        for k, target in enumerate(record["in_scope_boxes"]):
            x1, y1, x2, y2 = target["box"]
            rows.append(
                {
                    "source_frame": fid,
                    "time_ms_nominal": fid * 100,
                    "code": TARGET[target["derived_key"]],
                    "name_vi": "",
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "_k": k,
                }
            )
    linked, _ = track_prediction_rows(
        rows, sample_step=MINI_STEP, iou_min=0.30, max_missing_samples=1, predict_motion=True
    )
    events: dict[int, dict] = {}
    for row in linked:
        ev = events.setdefault(int(row["track_id"]), {"code": row["code"], "boxes": []})
        ev["boxes"].append(
            (int(row["source_frame"]), tuple(float(row[k]) for k in ("x1", "y1", "x2", "y2")))
        )
    return list(events.values())


def event_and_flip_stats(frames_out: dict[int, list[dict]], labels: dict) -> dict:
    events = gt_events(labels)
    detected = Counter()
    per_event = []
    for ev in events:
        hits, codes = 0, []
        for fid, box in ev["boxes"]:
            best = max(
                frames_out.get(fid, []),
                key=lambda r: (_iou(r["box"], box) >= 0.5, r["score"]),
                default=None,
            )
            if best is not None and _iou(best["box"], box) >= 0.5:
                codes.append(best["code"])
                hits += best["code"] == ev["code"]
        flips = sum(a != b for a, b in zip(codes, codes[1:], strict=False))
        detected[ev["code"]] += hits > 0
        per_event.append(
            {
                "code": ev["code"],
                "frames": len(ev["boxes"]),
                "correct_code_frames": hits,
                "matched_code_sequence": codes,
                "label_flips": flips,
                "p130_p131a_flips": sum(
                    {a, b} == {"P.130", "P.131a"} for a, b in zip(codes, codes[1:], strict=False)
                ),
            }
        )
    return {
        "gt_events": len(events),
        "gt_events_by_code": dict(Counter(ev["code"] for ev in events)),
        "events_with_ge1_correct_frame": dict(detected),
        "per_event": per_event,
    }


def evaluate_mini() -> dict:
    if sha256(MINI_LABELS) != MINI_LABELS_SHA256:
        raise RuntimeError("Mini R2 diagnostic labels hash differs")
    manifest = json.loads(MINI_MANIFEST.read_text(encoding="utf-8"))
    if (
        manifest["source_sha256"] != MINI_SOURCE_SHA256
        or manifest["sealed_test_accessed"]
        or sha256(MINI_PRED) != manifest["prediction_csv_sha256"]
    ):
        raise RuntimeError("Mini prediction manifest/CSV mismatch")
    labels = json.loads(MINI_LABELS.read_text(encoding="utf-8"))
    codes = {}
    with CLASS_MAP.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            codes[int(row["yolo_id"])] = row["derived_code"]
    raw: dict[int, list[dict]] = defaultdict(list)
    with MINI_PRED.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw[int(row["source_frame"])].append(
                {
                    "class_id": int(row["yolo_id"]),
                    "code": row["code"],
                    "score": float(row["score"]),
                    "box": tuple(float(row[k]) for k in ("x1", "y1", "x2", "y2")),
                }
            )
    sampled = list(range(0, manifest["source_frames_decoded"], MINI_STEP))
    baseline = {f: [r for r in raw[f] if r["score"] >= BASELINE_CONF] for f in sampled}

    # reproducibility: rerun at >=0.20 vs pinned conf-0.20 upload predictions
    pinned = Counter()
    if sha256(MINI_PINNED_020) == MINI_PINNED_020_SHA256:
        with MINI_PINNED_020.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                pinned[int(row["source_frame"]), row["code"]] += 1
    rerun = Counter((f, r["code"]) for f, rows in baseline.items() for r in rows)

    seq = [
        tt.SequenceFrame(
            str(f), tuple(tt.Candidate(r["class_id"], r["score"], r["box"]) for r in raw[f])
        )
        for f in sampled
    ]
    result = tt.run_sequence(seq, tt.PRIMARY)
    temporal = {
        f: [
            {
                "code": codes[d.label],
                "score": d.track_score,
                "box": d.candidate.box,
                "track_id": d.track_id,
            }
            for d in result.emitted(t)
        ]
        for t, f in enumerate(sampled)
    }
    track_flips = {
        "tracks": len(result.tracks),
        "tracks_confirmed": sum(t.confirmed_frame is not None for t in result.tracks),
        "temporal_label_switches_total": sum(t.label_switches for t in result.tracks),
    }
    return {
        "package": "TEMPORAL_DT_R1_EVAL_B_MINI",
        "status": "DEMO_ONLY_DIAGNOSTIC_INDEPENDENT_QA_PENDING",
        "scope": "74 evaluable sampled frames; only W.205c and P.130 (R2 diagnostic labels)",
        "not_used_for_parameter_selection": True,
        "params_primary": tt.PRIMARY.__dict__,
        "inputs_sha256": {
            "source_clip": MINI_SOURCE_SHA256,
            "labels_r2": MINI_LABELS_SHA256,
            "prediction_manifest": sha256(MINI_MANIFEST),
            "prediction_csv_conf0001": manifest["prediction_csv_sha256"],
            "class_map": sha256(CLASS_MAP),
        },
        "source_sha256": source_pins(),
        "inference": {
            k: manifest[k]
            for k in (
                "command",
                "device",
                "confidence",
                "imgsz",
                "nms_iou",
                "prediction_rows",
                "model_sha256",
            )
        },
        "rerun_vs_pinned_conf020_upload": {
            "pinned_rows": sum(pinned.values()),
            "rerun_rows_ge_020": sum(rerun.values()),
            "frame_code_count_mismatches": sum(
                1 for key in set(pinned) | set(rerun) if pinned[key] != rerun[key]
            ),
        },
        "baseline_fixed_020": {
            "frame_level": score_two_class(baseline, labels),
            "event_level": event_and_flip_stats(baseline, labels),
        },
        "temporal_primary": {
            "frame_level": score_two_class(temporal, labels),
            "event_level": event_and_flip_stats(temporal, labels),
            "tracks": track_flips,
        },
        "sealed_test_accessed": False,
        "app_activation": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("val", "mini-infer", "mini-score"))
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.command == "val":
        write_new(VAL_OUT, evaluate_val())
        print(VAL_OUT)
    elif args.command == "mini-infer":
        print(json.dumps(mini_infer(), indent=2))
    else:
        write_new(MINI_OUT, evaluate_mini())
        print(MINI_OUT)


if __name__ == "__main__":
    main()
