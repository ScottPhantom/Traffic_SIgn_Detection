from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from colab import run_vgg16_54_r1_r1 as runner
from vgg16_54 import contract_r1


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def attempt(mode: str, epoch: int, value: str, binding: str) -> dict[str, object]:
    return {
        "time": 1.0,
        "stage": "vgg16_classifier",
        "event": "ATTEMPT",
        "sealed_test_accessed": False,
        "mode": mode,
        "completed_epoch": epoch,
        "runtime_identity": {"schema": contract_r1.RUNTIME_SCHEMA, "digest": value},
        "gpu": {
            "device_name": "NVIDIA L4",
            "cuda_version": "12.8",
            "device_count": 1,
            "capability": [8, 9],
            "total_memory_bytes": 24_000_000_000,
        },
        "run_binding_sha256": binding,
        "checkpoint_binding_sha256": binding,
    }


def write_execution(path: Path, epoch: int, attempts: list[dict[str, object]]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "colab_execution.json").write_text(
        json.dumps(
            {
                "status": "SMOKE_STOP",
                "event": "SMOKE_STOP",
                "epoch": epoch,
                "sealed_test_accessed": False,
                "execution_attempts": attempts,
            }
        )
    )


def test_runtime_evidence_requires_exact_l4(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner.torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(runner.torch.cuda, "get_device_name", lambda _index: "NVIDIA T4")
    with pytest.raises(RuntimeError, match="requires NVIDIA L4"):
        runner.runtime_evidence()


def test_runtime_evidence_uses_boot_scoped_digest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    boot = tmp_path / "boot_id"
    boot.write_text("12345678-1234-1234-1234-123456789abc\n")
    monkeypatch.setattr(runner, "BOOT_ID_PATH", boot)
    monkeypatch.setattr(runner.torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(runner.torch.cuda, "get_device_name", lambda _index: "NVIDIA L4")
    monkeypatch.setattr(runner.torch.cuda, "device_count", lambda: 1)
    monkeypatch.setattr(runner.torch.cuda, "get_device_capability", lambda _index: (8, 9))
    monkeypatch.setattr(
        runner.torch.cuda,
        "get_device_properties",
        lambda _index: SimpleNamespace(total_memory=24_000_000_000),
    )
    monkeypatch.setattr(runner.torch.version, "cuda", "12.8")
    identity, gpu = runner.runtime_evidence()
    assert identity["schema"] == contract_r1.RUNTIME_SCHEMA
    assert len(identity["digest"]) == 64
    assert gpu["device_name"] == "NVIDIA L4"
    assert gpu["capability"] == [8, 9]


def test_governed_event_binds_runtime_gpu_and_checkpoint() -> None:
    captured: list[tuple[Path, str, str, dict[str, object]]] = []

    def original(state: Path, stage: str, name: str, **values: object) -> None:
        captured.append((state, stage, name, values))

    identity = {"schema": contract_r1.RUNTIME_SCHEMA, "digest": "b" * 64}
    gpu = {
        "device_name": "NVIDIA L4",
        "cuda_version": "12.8",
        "device_count": 1,
        "capability": [8, 9],
        "total_memory_bytes": 24_000_000_000,
    }
    emit = runner.make_governed_event(original, identity, gpu, "a" * 64)
    emit(Path("/state"), "vgg16_classifier", "ATTEMPT", mode="fresh", completed_epoch=0)
    values = captured[0][3]
    assert values["runtime_identity"] == identity
    assert values["gpu"] == gpu
    assert values["run_binding_sha256"] == "a" * 64
    assert values["checkpoint_binding_sha256"] == "a" * 64

    with pytest.raises(RuntimeError, match="may not be overridden"):
        emit(
            Path("/state"),
            "vgg16_classifier",
            "ATTEMPT",
            mode="fresh",
            completed_epoch=0,
            runtime_identity=identity,
        )


def test_resume_rejects_same_runtime(tmp_path: Path) -> None:
    binding = "a" * 64
    fresh = "b" * 64
    write_execution(tmp_path, 1, [attempt("fresh", 0, fresh, binding)])
    with pytest.raises(RuntimeError, match="genuinely new runtime"):
        contract_r1.verify_prior_smoke_state(
            tmp_path,
            mode="resume",
            stop_after=2,
            binding_sha256=binding,
            current_digest=fresh,
        )


def test_fresh_is_restricted_to_epoch_one_smoke(tmp_path: Path) -> None:
    binding = "a" * 64
    assert (
        contract_r1.verify_prior_smoke_state(
            tmp_path,
            mode="fresh",
            stop_after=1,
            binding_sha256=binding,
            current_digest="b" * 64,
        )
        == []
    )
    with pytest.raises(RuntimeError, match="epoch-1 smoke"):
        contract_r1.verify_prior_smoke_state(
            tmp_path,
            mode="fresh",
            stop_after=None,
            binding_sha256=binding,
            current_digest="b" * 64,
        )


def test_resume_accepts_new_runtime_and_bound_attempt(tmp_path: Path) -> None:
    binding = "a" * 64
    write_execution(tmp_path, 1, [attempt("fresh", 0, "b" * 64, binding)])
    result = contract_r1.verify_prior_smoke_state(
        tmp_path,
        mode="resume",
        stop_after=2,
        binding_sha256=binding,
        current_digest="c" * 64,
    )
    assert result == ["b" * 64]


def test_long_run_requires_reviewed_resume_runtime(tmp_path: Path) -> None:
    binding = "a" * 64
    attempts = [
        attempt("fresh", 0, "b" * 64, binding),
        attempt("resume", 1, "c" * 64, binding),
    ]
    write_execution(tmp_path, 2, attempts)
    with pytest.raises(RuntimeError, match="QA-reviewed resume runtime"):
        contract_r1.verify_prior_smoke_state(
            tmp_path,
            mode="resume",
            stop_after=None,
            binding_sha256=binding,
            current_digest="d" * 64,
        )


def test_source_qa_is_exact_and_hash_bound(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    reviewed: dict[str, str] = {}
    for relative in contract_r1.SUCCESSOR_SOURCE_FILES:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative)
        reviewed[relative] = digest(relative.encode())
    proof = tmp_path / "proof.json"
    payload = {
        "verdict": "PASS",
        "package": contract_r1.SUCCESSOR_PACKAGE,
        "reviewed_files": reviewed,
        "sealed_test_accessed": False,
    }
    proof.write_text(json.dumps(payload))
    assert contract_r1.verify_successor_source_qa(proof, digest(proof.read_bytes()), repo)
    payload["sealed_test_accessed"] = True
    proof.write_text(json.dumps(payload))
    with pytest.raises(RuntimeError, match="does not authorize"):
        contract_r1.verify_successor_source_qa(proof, digest(proof.read_bytes()), repo)


def test_state_successor_does_not_reuse_failed_r1_suffix(tmp_path: Path) -> None:
    good = tmp_path / contract_r1.STATE_SUFFIX
    assert contract_r1.normalize_state_path(good) == good.absolute()
    with pytest.raises(RuntimeError, match="must end"):
        contract_r1.normalize_state_path(tmp_path / "runs/vgg16_54_seed_20261018_r1")
