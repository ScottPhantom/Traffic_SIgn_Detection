"""Synthetic-only refusal and scoring tests for the prepared final evaluator."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from m1 import contract
from m1 import d1_final_evaluation_r1 as final
from m1.metrics import Frame


def _write(root: Path, name: str, content: bytes) -> dict[str, str]:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {"path": name, "sha256": hashlib.sha256(content).hexdigest()}


def _json(root: Path, name: str, value: dict) -> dict[str, str]:
    return _write(root, name, final.canonical(value))


def _fixture(root: Path) -> tuple[Path, dict]:
    source = {
        name: _write(root, name, f"synthetic source {name}\n".encode())["sha256"]
        for name in final.SOURCE_PATHS
    }
    proof = _json(root, "docs/review/proof.json", {"synthetic": True})
    qa = _write(root, "docs/review/lock_qa.md", b"Verdict: PASS\n")
    lock_owner = _write(root, "docs/review/lock_owner.md", b"Owner approved synthetic lock\n")
    bundle = _json(
        root,
        "tmp/synthetic_val/manifest.json",
        {"test_included": False, "sealed_test_accessed": False},
    )
    q4 = _json(
        root,
        "docs/review/q4.json",
        {
            "package": final.PACKAGE,
            "decision": "KEEP_ORIGINAL",
            "gates": contract.GATES,
            "owner_quote": "synthetic decision",
            "sealed_test_accessed": False,
        },
    )
    label = _json(
        root,
        "docs/review/label.json",
        {
            "package": final.PACKAGE,
            "mode": "CURRENT_LABELS",
            "owner_quote": "synthetic decision",
            "sealed_test_accessed": False,
        },
    )
    weights = [
        {"seed": seed, **_write(root, f"tmp/synthetic_weights/{seed}.pt", f"fake-{seed}".encode())}
        for seed in final.SEEDS
    ]
    lock = _json(
        root,
        "docs/review/lock.json",
        {
            "candidates": [
                {"seed": weight["seed"], "weight": {"sha256": weight["sha256"]}}
                for weight in weights
            ]
        },
    )
    plan = {
        "package": final.PACKAGE,
        "schema_version": 1,
        "lock_record": lock,
        "lock_proof": proof,
        "lock_result_qa": qa,
        "owner_lock_approval": lock_owner,
        "bundle": bundle,
        "final_contract": final.CONTRACT_PATH,
        "owner_open_approval": "docs/review/open_owner.md",
        "q4_decision": q4,
        "label_decision": label,
        "weights": weights,
        "source_sha256": source,
        "output_dir": "results/experiments/synthetic_final",
        "reason": "synthetic fixture",
        "imgsz": 1280,
        "device": "mps",
        "sealed_test_accessed": False,
    }
    path = Path("docs/review/synthetic_plan.json")
    _json(root, path.as_posix(), plan)
    plan_hash = final.sha256(root / path)
    contract_bytes = f"{final.CONTRACT_MARKER}\nplan={plan_hash}\n".encode()
    _write(root, final.CONTRACT_PATH, contract_bytes)
    contract_hash = hashlib.sha256(contract_bytes).hexdigest()
    _write(
        root,
        plan["owner_open_approval"],
        f"{final.OPEN_MARKER}\n{contract_hash}\n{plan['reason']}\n".encode(),
    )
    return path, plan


def _rebind(root: Path, path: Path, plan: dict) -> None:
    _json(root, path.as_posix(), plan)
    plan_hash = final.sha256(root / path)
    contract_bytes = f"{final.CONTRACT_MARKER}\nplan={plan_hash}\n".encode()
    _write(root, final.CONTRACT_PATH, contract_bytes)
    contract_hash = hashlib.sha256(contract_bytes).hexdigest()
    _write(
        root,
        plan["owner_open_approval"],
        f"{final.OPEN_MARKER}\n{contract_hash}\n{plan['reason']}\n".encode(),
    )


def _reader(*args: object) -> dict[str, object]:
    return {"conf": 0.2, "nms_iou": 0.7, "agnostic_nms": False}


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_lock",
        "bad_lock_hash",
        "three_weights",
        "same_weight",
        "swapped_seed_labels",
        "missing_lock_owner",
        "missing_contract",
        "missing_open_owner",
        "missing_q4",
        "missing_label",
        "bad_weight_hash",
        "already_opened",
        "non_val_bundle",
        "bad_source_hash",
    ],
)
def test_preflight_refuses_missing_or_changed_gate_before_fake_test_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    plan_path, plan = _fixture(tmp_path)
    forbidden = tmp_path / "sealed_fake"

    def reject_access(*_args: object, **_kwargs: object) -> None:
        raise AssertionError(f"fake sealed data was accessed: {forbidden}")

    monkeypatch.setattr(final, "_real_test_roster", reject_access)
    if mutation == "missing_lock":
        (tmp_path / plan["lock_record"]["path"]).unlink()
    elif mutation == "bad_lock_hash":
        (tmp_path / plan["lock_record"]["path"]).write_text("changed")
    elif mutation == "three_weights":
        plan["weights"].append({"seed": 20261020, **_write(tmp_path, "tmp/extra.pt", b"fake")})
    elif mutation == "same_weight":
        plan["weights"][1]["sha256"] = plan["weights"][0]["sha256"]
    elif mutation == "swapped_seed_labels":
        plan["weights"][0]["seed"], plan["weights"][1]["seed"] = (
            plan["weights"][1]["seed"],
            plan["weights"][0]["seed"],
        )
    elif mutation == "missing_lock_owner":
        (tmp_path / plan["owner_lock_approval"]["path"]).unlink()
    elif mutation == "missing_contract":
        (tmp_path / final.CONTRACT_PATH).unlink()
    elif mutation == "missing_open_owner":
        (tmp_path / plan["owner_open_approval"]).unlink()
    elif mutation == "missing_q4":
        (tmp_path / plan["q4_decision"]["path"]).unlink()
    elif mutation == "missing_label":
        (tmp_path / plan["label_decision"]["path"]).unlink()
    elif mutation == "bad_weight_hash":
        (tmp_path / plan["weights"][0]["path"]).write_bytes(b"changed")
    elif mutation == "already_opened":
        _write(tmp_path, final.ACCESS_LOG, final.canonical({"action": final.ACCESS_ACTION}))
    elif mutation == "non_val_bundle":
        (tmp_path / plan["bundle"]["path"]).write_text('{"test_included":true}')
    elif mutation == "bad_source_hash":
        (tmp_path / next(iter(final.SOURCE_PATHS))).write_bytes(b"changed")
    if mutation in {"three_weights", "same_weight", "swapped_seed_labels"}:
        _rebind(tmp_path, plan_path, plan)
    with pytest.raises(RuntimeError):
        final.preflight(plan_path, root=tmp_path, reader=_reader, committed=False)
    assert not forbidden.exists()


def test_preflight_accepts_only_one_shared_two_seed_setting(tmp_path: Path) -> None:
    plan_path, _ = _fixture(tmp_path)
    approved = final.preflight(plan_path, root=tmp_path, reader=_reader, committed=False)
    assert approved.selection == {"conf": 0.2, "nms_iou": 0.7, "agnostic_nms": False}
    assert approved.label_mode == "CURRENT_LABELS"
    assert approved.label_overlay is None

    calls = iter(
        (
            {"conf": 0.2, "nms_iou": 0.7, "agnostic_nms": False},
            {"conf": 0.3, "nms_iou": 0.7, "agnostic_nms": False},
        )
    )
    with pytest.raises(RuntimeError, match="one verified R3 setting"):
        final.preflight(
            plan_path, root=tmp_path, reader=lambda *_args: next(calls), committed=False
        )


def test_q4_and_label_decisions_refuse_unapproved_or_unsupported_state(tmp_path: Path) -> None:
    plan_path, plan = _fixture(tmp_path)
    q4 = tmp_path / plan["q4_decision"]["path"]
    decision = json.loads(q4.read_text())
    decision["decision"] = "RECALIBRATE_ONCE"
    decision["gates"]["min_support_for_class_gate"] = 1
    q4.write_bytes(final.canonical(decision))
    plan["q4_decision"]["sha256"] = final.sha256(q4)
    _rebind(tmp_path, plan_path, plan)
    with pytest.raises(RuntimeError, match="class support"):
        final.preflight(plan_path, root=tmp_path, reader=_reader, committed=False)

    label = tmp_path / plan["label_decision"]["path"]
    decision["gates"]["min_support_for_class_gate"] = 20
    q4.write_bytes(final.canonical(decision))
    plan["q4_decision"]["sha256"] = final.sha256(q4)
    label.write_bytes(
        final.canonical(
            {
                "package": final.PACKAGE,
                "mode": "PREDICTION_BLIND_REVIEW",
                "owner_quote": "synthetic",
                "sealed_test_accessed": False,
            }
        )
    )
    plan["label_decision"]["sha256"] = final.sha256(label)
    _rebind(tmp_path, plan_path, plan)
    with pytest.raises(RuntimeError, match="separate QA"):
        final.preflight(plan_path, root=tmp_path, reader=_reader, committed=False)


def test_blind_review_preflight_checks_metadata_without_reading_label_payload(
    tmp_path: Path,
) -> None:
    plan_path, plan = _fixture(tmp_path)
    reviewed_hash = "a" * 64
    reviewed_path = "tmp/synthetic_sealed/reviewed_labels.json"
    review_qa = _write(
        tmp_path,
        "docs/review/blind_review_qa.md",
        f"Verdict: PASS\napproved_labels_sha256={reviewed_hash}\n".encode(),
    )
    label = tmp_path / plan["label_decision"]["path"]
    label.write_bytes(
        final.canonical(
            {
                "package": final.PACKAGE,
                "mode": "PREDICTION_BLIND_REVIEW",
                "owner_quote": "synthetic decision",
                "sealed_test_accessed": False,
                "approved_labels": {"path": reviewed_path, "sha256": reviewed_hash},
                "blind_review_qa": review_qa,
            }
        )
    )
    plan["label_decision"]["sha256"] = final.sha256(label)
    _rebind(tmp_path, plan_path, plan)
    approved = final.preflight(plan_path, root=tmp_path, reader=_reader, committed=False)
    assert approved.label_overlay == {"path": reviewed_path, "sha256": reviewed_hash}
    assert not (tmp_path / reviewed_path).exists()


def _frame(stem: str, group: str, cls: int, predicted: bool, pred_cls: int) -> Frame:
    box = np.array([[0.0, 0.0, 20.0, 20.0]])
    return Frame(
        stem=stem,
        group_id=group,
        gt_boxes=box,
        gt_classes=np.array([cls]),
        pred_boxes=box.copy() if predicted else np.zeros((0, 4)),
        pred_classes=np.array([pred_cls]) if predicted else np.zeros(0, dtype=int),
        pred_scores=np.array([0.9]) if predicted else np.zeros(0),
        image_width=100,
        image_height=100,
    )


def test_synthetic_two_seed_mean_class_gate_and_ap_support() -> None:
    base = [_frame(f"c{i}", f"g{i % 2}", 0, True, 0) for i in range(20)]
    base += [_frame(f"o{i}", f"g{i % 2}", 1, True, 0) for i in range(20)]
    second = [replace(frame) for frame in base]
    gates = {**contract.GATES, "map50": 0.0, "map50_95": 0.0}
    result = final.score_two_seeds(
        {20261018: base, 20261019: second},
        _reader(),
        gates,
        {str(i): i for i in range(54)},
        rounds=5,
    )
    assert result["two_seed"]["agnostic_recall"]["mean"] == 1.0
    assert result["two_seed"]["fp_per_image"]["mean"] == 0.0
    assert result["per_class"]["0"]["support"] == 20
    assert result["per_class"]["1"]["support"] == 20
    assert result["per_class"]["1"]["passed"] is False
    assert result["excluded_from_simulated_behavior"] == ["1"]
    assert all(result["gate_checks_excluding_latency"].values())
    assert result["per_seed"]["20261018"]["exact_class_ap"]["supported_classes"] == [0, 1]
    assert result["sealed_test_accessed"] is False


def test_synthetic_critical_miss_fails_gate_and_roster_drift_refuses() -> None:
    base = [_frame(f"c{i}", "g1", 0, True, 1) for i in range(20)]
    by_seed = {20261018: base, 20261019: [replace(frame) for frame in base]}
    gates = {**contract.GATES, "map50": 0.0, "map50_95": 0.0}
    result = final.score_two_seeds(
        by_seed, _reader(), gates, {str(i): i for i in range(54)}, rounds=2
    )
    assert result["gate_checks_excluding_latency"]["critical_classes"] is False
    assert result["per_class"]["0"]["mean_recall"] == 0.0
    by_seed[20261019][0] = replace(by_seed[20261019][0], group_id="different")
    with pytest.raises(RuntimeError, match="roster"):
        final.score_two_seeds(by_seed, _reader(), gates, {str(i): i for i in range(54)}, rounds=2)


def test_open_once_logs_before_any_synthetic_roster_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[str] = []
    log = tmp_path / final.ACCESS_LOG
    approved = final.Approved(
        "0" * 64,
        "1" * 64,
        _reader(),
        contract.GATES,
        "CURRENT_LABELS",
        None,
        ({"seed": 20261018}, {"seed": 20261019}),
        "synthetic",
        log,
        tmp_path / "results/experiments/synthetic",
    )

    def fake_append(action: str, reason: str) -> None:
        seen.append("log")
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as sink:
            sink.write(final.canonical({"action": action, "reason": reason}).decode())

    monkeypatch.setattr(contract, "log_test_access", fake_append)
    assert final._open_once(approved)["action"] == final.ACCESS_ACTION
    assert seen == ["log"]
    with pytest.raises(RuntimeError, match="already recorded"):
        final._open_once(approved)


def test_missing_gate_never_reaches_fake_sealed_loader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan_path, plan = _fixture(tmp_path)
    (tmp_path / plan["q4_decision"]["path"]).unlink()
    touched = []

    def forbidden() -> None:
        touched.append("fake sealed loader")
        raise AssertionError("synthetic sealed loader was called")

    monkeypatch.setattr(final, "_real_test_roster", forbidden)
    original = final.preflight
    monkeypatch.setattr(
        final,
        "preflight",
        lambda path: original(path, root=tmp_path, reader=_reader, committed=False),
    )
    with pytest.raises(RuntimeError):
        final.execute(plan_path)
    assert touched == []
