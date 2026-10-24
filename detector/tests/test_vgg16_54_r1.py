from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import torch

from colab.run_vgg16_54_r1 import should_stop_early, validate_smoke_start
from vgg16_54 import contract
from vgg16_54.model import ARCHITECTURE, VGG16Crop54, build_model


def write_json(path: Path, value: object) -> str:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def approval() -> dict[str, object]:
    return {
        "decision": "APPROVED_VGG16_54_R1",
        "experiment": contract.EXPERIMENT,
        "config": contract.PROPOSED_CONFIG,
        "sealed_test_accessed": False,
    }


def test_vgg16_crop_head_has_54_outputs_and_bounded_parameter_count() -> None:
    model = build_model()
    output = model(torch.zeros(2, 3, 32, 32))
    parameters = sum(value.numel() for value in model.parameters())
    assert output.shape == (2, 54)
    assert 14_000_000 < parameters < 16_000_000
    assert isinstance(model, VGG16Crop54)


def test_vgg16_never_requests_pretrained_weights(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    class Fake(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.features = torch.nn.Sequential(
                torch.nn.Conv2d(3, 512, 1),
                torch.nn.AdaptiveAvgPool2d((1, 1)),
            )

    def fake_vgg16(*, weights: object) -> Fake:
        observed["weights"] = weights
        return Fake()

    monkeypatch.setattr("torchvision.models.vgg16", fake_vgg16)
    model = VGG16Crop54()
    assert model(torch.zeros(1, 3, 32, 32)).shape == (1, 54)
    assert observed == {"weights": None}


def test_proposal_is_scratch_only_54_class_and_has_no_flip_or_test() -> None:
    config = contract.validate_config(dict(contract.PROPOSED_CONFIG))
    assert config["architecture"] == ARCHITECTURE
    assert config["classes"] == 54
    assert config["pretrained"] is False
    assert config["horizontal_flip"] is False
    assert config["sealed_test_accessed"] is False
    assert config["epochs"] == 100
    assert config["early_stopping_min_epochs"] == 30
    assert config["early_stopping_patience"] == 15
    assert not ({"test", "test_split", "final_eval"} & set(config))


def test_early_stopping_preserves_30_epoch_window_and_uses_patience() -> None:
    config = contract.validate_config(dict(contract.PROPOSED_CONFIG))
    assert should_stop_early(29, 1, config) is False
    assert should_stop_early(30, 16, config) is False
    assert should_stop_early(31, 16, config) is True
    assert should_stop_early(100, 99, config) is False


def test_smoke_resume_requires_exact_epoch_one_checkpoint() -> None:
    validate_smoke_start("fresh", 1, 0)
    validate_smoke_start("resume", 2, 1)
    validate_smoke_start("resume", None, 37)
    with pytest.raises(RuntimeError, match="requires completed_epoch=1, observed=2"):
        validate_smoke_start("resume", 2, 2)
    with pytest.raises(RuntimeError, match="requires completed_epoch=0, observed=1"):
        validate_smoke_start("fresh", 1, 1)


def test_owner_approval_is_exact_and_hash_pinned(tmp_path: Path) -> None:
    path = tmp_path / "owner.json"
    digest = write_json(path, approval())
    assert contract.verify_owner_approval(path, digest)["decision"] == "APPROVED_VGG16_54_R1"
    changed = approval()
    changed["config"] = {**contract.PROPOSED_CONFIG, "batch": 128}
    digest = write_json(path, changed)
    with pytest.raises(RuntimeError, match="does not authorize"):
        contract.verify_owner_approval(path, digest)


def test_owner_approval_rejects_links(tmp_path: Path) -> None:
    outside = tmp_path / "outside.json"
    digest = write_json(outside, approval())
    link = tmp_path / "approval.json"
    link.symlink_to(outside)
    with pytest.raises(RuntimeError, match="symlink"):
        contract.verify_owner_approval(link, digest)


def test_source_qa_must_bind_exact_config_and_false_seal(tmp_path: Path) -> None:
    repo_root = Path(__file__).parents[2]
    path = tmp_path / "source_qa.json"
    proof = {
        "verdict": "PASS",
        "package": contract.EXPERIMENT,
        "config_sha256": contract.canonical_sha256(contract.PROPOSED_CONFIG),
        "reviewed_files": {
            relative: contract.sha256_file(repo_root / relative)
            for relative in contract.SOURCE_FILES
        },
        "sealed_test_accessed": False,
    }
    digest = write_json(path, proof)
    assert contract.verify_source_qa(path, digest, repo_root)["verdict"] == "PASS"
    proof["sealed_test_accessed"] = True
    digest = write_json(path, proof)
    with pytest.raises(RuntimeError, match="does not approve"):
        contract.verify_source_qa(path, digest, repo_root)


def test_source_qa_rejects_current_byte_drift(tmp_path: Path) -> None:
    repo_root = Path(__file__).parents[2]
    path = tmp_path / "source_qa.json"
    reviewed = {
        relative: contract.sha256_file(repo_root / relative) for relative in contract.SOURCE_FILES
    }
    reviewed["detector/vgg16_54/model.py"] = "0" * 64
    proof = {
        "verdict": "PASS",
        "package": contract.EXPERIMENT,
        "config_sha256": contract.canonical_sha256(contract.PROPOSED_CONFIG),
        "reviewed_files": reviewed,
        "sealed_test_accessed": False,
    }
    digest = write_json(path, proof)
    with pytest.raises(RuntimeError, match="does not bind current bytes"):
        contract.verify_source_qa(path, digest, repo_root)


def test_source_qa_allowlist_covers_runtime_repository_imports() -> None:
    required = {
        "detector/pyproject.toml",
        "detector/uv.lock",
        "detector/colab/extract_cascade_b0_r1.py",
        "detector/colab/run_cascade_b0_r1.py",
        "detector/d1_cascade_classifier/__init__.py",
        "detector/d1_cascade_classifier/contract.py",
        "detector/d1_cascade_classifier/data.py",
        "detector/d1_cascade_classifier/metrics.py",
        "detector/d1_cascade_classifier/model.py",
        "detector/m1/__init__.py",
        "detector/m1/checkpoint_store.py",
        "detector/m1/checkpoint_store_r2.py",
    }
    assert required <= set(contract.SOURCE_FILES)


def test_source_candidate_manifest_binds_runtime_and_review_scope() -> None:
    repo_root = Path(__file__).parents[2]
    manifest = json.loads(
        (repo_root / "docs/review/generated/vgg16_54_r1_source_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["package"] == contract.EXPERIMENT
    assert manifest["config_sha256"] == contract.canonical_sha256(contract.PROPOSED_CONFIG)
    assert manifest["sealed_test_accessed"] is False
    assert set(contract.SOURCE_FILES) <= set(manifest["files"])
    for relative, expected in manifest["files"].items():
        assert contract.sha256_file(repo_root / relative) == expected


def test_smoke_qa_requires_two_distinct_runtime_digests(tmp_path: Path) -> None:
    path = tmp_path / "smoke.json"
    proof = {
        "verdict": "PASS",
        "package": contract.EXPERIMENT,
        "config_sha256": contract.canonical_sha256(contract.PROPOSED_CONFIG),
        "bundle_manifest_sha256": "b" * 64,
        "fresh_completed_epoch": 1,
        "resume_started_epoch": 2,
        "resume_completed_epoch": 2,
        "runtime_digests": ["c" * 64, "d" * 64],
        "sealed_test_accessed": False,
    }
    digest = write_json(path, proof)
    assert contract.verify_smoke_qa(path, digest, "b" * 64)["verdict"] == "PASS"
    proof["runtime_digests"] = ["c" * 64, "c" * 64]
    digest = write_json(path, proof)
    with pytest.raises(RuntimeError, match="does not authorize"):
        contract.verify_smoke_qa(path, digest, "b" * 64)


def test_state_path_is_separate_from_active_d1_and_cascade() -> None:
    path = Path("/content/drive/MyDrive/CPV301/Traffic_Sign_Detector") / contract.STATE_SUFFIX
    assert contract.normalize_state_path(path) == path
    with pytest.raises(RuntimeError, match="state path"):
        contract.normalize_state_path(Path("/content/drive/M1_D1_Colab/runs/d1_a3_seed_20261018_r2"))


def test_colab_runner_has_no_sealed_test_surface() -> None:
    source = (
        Path(__file__).parents[1] / "colab" / "run_vgg16_54_r1.py"
    ).read_text(encoding="utf-8")
    assert "EfficientCheckpointStore" in source
    assert 'choices=("fresh", "resume")' in source
    assert "--final-eval" not in source
    assert '"test"' not in source
