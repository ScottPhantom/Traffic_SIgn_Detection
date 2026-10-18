from __future__ import annotations

import json
import pickle
import socket
from pathlib import Path

import numpy as np
import pytest
import torch

from d1_cascade_classifier import cli, contract
from d1_cascade_classifier.data import CropDataset
from d1_cascade_classifier.metrics import classification_metrics, latency_stats
from d1_cascade_classifier.model import build_model


def arrays(labels: list[int]) -> dict[str, np.ndarray]:
    count = len(labels)
    return {
        "features": np.arange(count * 32 * 32 * 3, dtype=np.uint8).reshape(count, 32, 32, 3),
        "labels": np.asarray(labels, dtype=np.uint8),
        "sizes": np.full((count, 2), 40, dtype=np.uint16),
        "coords": np.tile(np.asarray([[5, 5, 35, 35]], dtype=np.uint16), (count, 1)),
    }


def make_fixture(root: Path) -> tuple[Path, Path]:
    root.mkdir(parents=True)
    split_arrays = {"train": arrays([0, 1, 1]), "val": arrays([0, 2])}
    names = "ClassId,SignName,DerivedKey,QCVN\n" + "".join(
        f"{index},Class {index},K{index},Q{index}\n" for index in range(contract.CLASSES)
    )
    (root / "signnames.csv").write_text(names, encoding="utf-8")
    splits: dict[str, object] = {}
    for split, filename in contract.DATA_FILES.items():
        with (root / filename).open("wb") as handle:
            pickle.dump(split_arrays[split], handle, protocol=pickle.HIGHEST_PROTOCOL)
        index_name = contract.INDEX_FILES[split]
        sample_count = len(split_arrays[split]["labels"])
        index_payload = b"index\n" + b"".join(
            f"{index}\n".encode() for index in range(sample_count)
        )
        (root / index_name).write_bytes(index_payload)
        labels = split_arrays[split]["labels"]
        per_class = {str(i): int(np.sum(labels == i)) for i in sorted(set(labels.tolist()))}
        splits[split] = {
            "classes": len(per_class),
            "file": filename,
            "index_sha256": contract.sha256_file(root / index_name),
            "per_class": per_class,
            "samples": len(labels),
            "sha256": {
                key: contract.sha256_bytes(value.tobytes(order="C"))
                for key, value in split_arrays[split].items()
            },
            "signs_under_16px": 0,
            "sources": {"SYNTHETIC": len(labels)},
        }
    manifest = {
        "classes": 54,
        "format": {
            "border": "synthetic",
            "coords": "synthetic",
            "features": "synthetic",
            "labels": "synthetic",
            "resize": "synthetic",
            "sizes": "synthetic",
        },
        "package": "DATASET01-GTSRB-STYLE",
        "pinned_sources": {"synthetic": "0" * 64},
        "signnames_sha256": contract.sha256_file(root / "signnames.csv"),
        "splits": splits,
        "status": "DATASET01_GTSRB_STYLE_CROPS",
        "test": "sealed",
        "use_limits": ["synthetic fixture"],
    }
    manifest_path = root.parent / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return root, manifest_path


def test_real_governed_train_val_contract() -> None:
    bound, loaded = contract.check_data_contract()
    assert bound["manifest_sha256"] == contract.MANIFEST_SHA256
    assert bound["splits"]["train"]["samples"] == 12621
    assert bound["splits"]["val"]["samples"] == 560
    assert loaded["train"]["features"].shape == (12621, 32, 32, 3)
    assert bound["sealed_test_accessed"] is False


def test_synthetic_contract_checks_exact_schema_hashes_and_roster(tmp_path: Path) -> None:
    data_root, manifest = make_fixture(tmp_path / "fixture")
    bound, loaded = contract.check_data_contract(
        data_root, manifest, expected_manifest_sha256=None
    )
    assert bound["splits"]["val"]["samples"] == 2
    loaded["val"]["features"][0, 0, 0, 0] ^= 1
    with (data_root / "valid.p").open("wb") as handle:
        pickle.dump(loaded["val"], handle, protocol=pickle.HIGHEST_PROTOCOL)
    with pytest.raises(RuntimeError, match="hash differs"):
        contract.check_data_contract(data_root, manifest, expected_manifest_sha256=None)
    (data_root / "extra.bin").write_bytes(b"unexpected")
    with pytest.raises(RuntimeError, match="roster differs"):
        contract.check_data_contract(data_root, manifest, expected_manifest_sha256=None)


def test_restricted_pickle_rejects_arbitrary_global(tmp_path: Path) -> None:
    data_root, manifest = make_fixture(tmp_path / "fixture")
    with (data_root / "train.p").open("wb") as handle:
        pickle.dump(Path("forbidden"), handle)
    with pytest.raises(RuntimeError, match="forbidden pickle global"):
        contract.check_data_contract(data_root, manifest, expected_manifest_sha256=None)


def test_test_paths_and_test_artifacts_are_refused(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="sealed-test path"):
        contract.check_data_contract(tmp_path / "test", tmp_path / "manifest.json")
    data_root, manifest = make_fixture(tmp_path / "fixture")
    (data_root / "test.p").write_bytes(b"never read")
    with pytest.raises(RuntimeError, match="roster differs"):
        contract.check_data_contract(data_root, manifest, expected_manifest_sha256=None)


def test_only_fixed_seeds_and_known_architectures_are_allowed() -> None:
    assert tuple(contract.SEEDS) == (20261018, 20261019, 20261020)
    for architecture in contract.ARCHITECTURES:
        assert contract.validate_architecture(architecture) == architecture
    with pytest.raises(RuntimeError, match="unknown architecture"):
        contract.validate_architecture("owner_not_asked")
    with pytest.raises(RuntimeError, match="seed 1 is not approved"):
        contract.validate_seed(1)


def test_compact_model_has_exactly_54_outputs() -> None:
    model = build_model("compact_cnn")
    assert model(torch.zeros(2, 3, 32, 32)).shape == (2, 54)


def test_vgg16_is_constructed_with_weights_none(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    class Fake(torch.nn.Module):
        def forward(self, inputs: torch.Tensor) -> torch.Tensor:
            return torch.zeros(len(inputs), contract.CLASSES)

    def fake_vgg16(*, weights: object, num_classes: int) -> Fake:
        calls.update(weights=weights, num_classes=num_classes)
        return Fake()

    monkeypatch.setattr("torchvision.models.vgg16", fake_vgg16)
    build_model("vgg16_scratch")
    assert calls == {"weights": None, "num_classes": 54}


def test_dataset_has_fixed_preprocessing_and_no_augmentation() -> None:
    dataset = CropDataset(arrays([3]))
    first, label = dataset[0]
    second, _ = dataset[0]
    assert torch.equal(first, second)
    assert first.shape == (3, 32, 32) and int(label) == 3
    assert contract.model_config("compact_cnn")["horizontal_flip"] is False


def test_metrics_include_requested_validation_evidence() -> None:
    targets = np.asarray([0, 0, 1, 2])
    probabilities = np.full((4, 54), 0.0)
    probabilities[0, 0] = 1.0
    probabilities[1, 1] = 1.0
    probabilities[2, 1] = 1.0
    probabilities[3, 2] = 1.0
    report = classification_metrics(targets, probabilities)
    assert report["top1_accuracy"] == 0.75
    assert report["represented_classes"] == 3
    assert report["balanced_accuracy_supported_classes"] == pytest.approx(5 / 6)
    assert report["macro_f1_supported_classes"] == pytest.approx((2 / 3 + 2 / 3 + 1) / 3)
    assert report["ece_15_bin"] == 0.25
    assert report["per_class"]["0"]["support"] == 2
    assert report["per_class"]["53"]["recall"] is None


def test_metrics_reject_invalid_probabilities() -> None:
    with pytest.raises(ValueError, match="sum to one"):
        classification_metrics(np.asarray([0]), np.zeros((1, 54)))
    bad = np.zeros((1, 54))
    bad[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        classification_metrics(np.asarray([0]), bad)


def test_latency_contract_is_batch1_warmup50_and_300_measurements() -> None:
    assert contract.LATENCY_WARMUP == 50 and contract.LATENCY_ITERATIONS == 300
    report = latency_stats([float(index) for index in range(300)])
    assert report["n"] == 300 and report["p95_ms"] == pytest.approx(284.05)
    with pytest.raises(ValueError, match="exactly 300"):
        latency_stats([1.0])


def test_cli_has_no_test_split_or_final_eval_surface() -> None:
    parser = cli.parser()
    help_text = parser.format_help()
    assert "--final-eval" not in help_text
    evaluate = parser.parse_args(["evaluate", "--weights", "run/weights/best.pt"])
    assert not hasattr(evaluate, "split") and not hasattr(evaluate, "final_eval")
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["evaluate", "--weights", "run/weights/best.pt", "--split", "test"]
        )


def test_offline_environment_is_applied_and_restored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WANDB_DISABLED", raising=False)
    with contract.offline_mode():
        assert contract.os.environ["WANDB_DISABLED"] == "true"
        assert contract.os.environ["HF_HUB_OFFLINE"] == "1"
        with pytest.raises(RuntimeError, match="network access is disabled"):
            socket.create_connection(("127.0.0.1", 9))
    assert "WANDB_DISABLED" not in contract.os.environ


def test_run_bindings_cover_data_model_config_and_environment() -> None:
    names = {"data_sha256", "model_sha256", "config_sha256", "environment_sha256"}
    source = Path(cli.__file__).read_text(encoding="utf-8")
    assert all(f'"{name}"' in source for name in names)


def make_valid_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, dict[str, object]]:
    results = tmp_path / "results"
    monkeypatch.setattr(contract, "RESULTS_DIR", results)
    data_contract = {
        "manifest_path": "/governed/manifest.json",
        "manifest_sha256": "manifest",
        "signnames_sha256": "names",
        "splits": {},
        "sealed_test_accessed": False,
    }
    monkeypatch.setattr(contract, "check_data_contract", lambda: (data_contract, {}))
    run = results / "run"
    weights_dir = run / "weights"
    weights_dir.mkdir(parents=True)
    for path, payload in (
        (weights_dir / "best.pt", b"best"),
        (weights_dir / "last.pt", b"last"),
        (run / "history.json", b"{}"),
    ):
        path.write_bytes(payload)
    model = contract.model_config("compact_cnn")
    config = {
        "architecture": "compact_cnn",
        "batch": 8,
        "device": "cpu",
        "epochs": 1,
        "horizontal_flip": False,
        "learning_rate": 0.001,
        "model_config_sha256": contract.canonical_sha256(model),
        "seed": 20261018,
        "weights": None,
        "workers": 0,
    }
    environment = {
        "cuda_available": False,
        "detector_lock_sha256": contract.sha256_file(contract.LOCK_PATH),
        "git_commit": "commit",
        "git_dirty_files": 0,
        "machine": "arm64",
        "mps_available": False,
        "offline_environment": contract.OFFLINE_ENVIRONMENT,
        "platform": "synthetic",
        "python": "3.12",
        "torch": "synthetic",
        "torchvision": "synthetic",
    }
    artifacts = {
        path.name: {"path": str(path), "sha256": contract.sha256_file(path)}
        for path in (weights_dir / "best.pt", weights_dir / "last.pt", run / "history.json")
    }
    record = {
        "artifacts": artifacts,
        "bindings": {
            "config_sha256": contract.canonical_sha256(config),
            "data_sha256": contract.canonical_sha256(data_contract),
            "environment_sha256": contract.canonical_sha256(environment),
            "model_sha256": contract.canonical_sha256(model),
        },
        "config": config,
        "data": data_contract,
        "environment": environment,
        "experiment": "D1_CASCADE_CLASSIFIER",
        "model": model,
        "run": "run",
        "seed": 20261018,
        "status": "TRAINED",
    }
    (run / "run_contract.json").write_text(json.dumps(record), encoding="utf-8")
    return run, weights_dir / "best.pt", record


def test_run_contract_bindings_and_all_artifacts_are_verified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run, best, record = make_valid_run(tmp_path, monkeypatch)
    assert contract.load_run_weights(str(best))[1]["run"] == "run"
    record["bindings"]["environment_sha256"] = "forged"
    (run / "run_contract.json").write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(RuntimeError, match="binding differs"):
        contract.load_run_weights(str(best))


@pytest.mark.parametrize(
    "relative",
    ["run_contract.json", "history.json", "weights/best.pt", "weights/last.pt"],
)
def test_run_loader_rejects_symlinked_metadata_and_every_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, relative: str
) -> None:
    run, best, _record = make_valid_run(tmp_path, monkeypatch)
    target = run / relative
    external = tmp_path / (relative.replace("/", "_") + ".external")
    target.replace(external)
    target.symlink_to(external)
    with pytest.raises(RuntimeError, match="symlink component"):
        contract.load_run_weights(str(best))
    assert external.is_file()


def test_run_loader_rejects_symlinked_run_parent_and_outside_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run, best, _record = make_valid_run(tmp_path, monkeypatch)
    external_run = tmp_path / "external-run"
    run.replace(external_run)
    run.symlink_to(external_run, target_is_directory=True)
    with pytest.raises(RuntimeError, match="symlink component"):
        contract.load_run_weights(str(best))
    outside = external_run / "weights/best.pt"
    with pytest.raises(RuntimeError, match="must stay under"):
        contract.load_run_weights(str(outside))


def stub_evaluation(
    monkeypatch: pytest.MonkeyPatch, weights: Path
) -> None:
    record = {"seed": 20261018, "model": {"architecture": "compact_cnn"}}
    monkeypatch.setattr(cli, "load_model", lambda *_args: (torch.nn.Identity(), weights, record))
    split = arrays([0])
    monkeypatch.setattr(contract, "check_data_contract", lambda: ({}, {"val": split}))
    probabilities = np.zeros((1, contract.CLASSES), dtype=np.float64)
    probabilities[0, 0] = 1.0
    monkeypatch.setattr(
        cli,
        "predict",
        lambda *_args: (np.asarray([0], dtype=np.int64), probabilities, 0.0),
    )


def test_real_evaluate_cli_refuses_report_symlink_without_external_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    results = tmp_path / "results"
    monkeypatch.setattr(contract, "RESULTS_DIR", results)
    run = results / "run"
    weights = run / "weights/best.pt"
    weights.parent.mkdir(parents=True)
    weights.write_bytes(b"synthetic")
    stub_evaluation(monkeypatch, weights)
    external = tmp_path / "external-eval.json"
    original = b"OWNER DATA MUST STAY BYTE IDENTICAL"
    external.write_bytes(original)
    (run / "eval_val.json").symlink_to(external)
    assert cli.main(["evaluate", "--weights", str(weights), "--device", "cpu"]) == 1
    assert external.read_bytes() == original
    assert (run / "eval_val.json").is_symlink()
    assert "regular non-symlink" in capsys.readouterr().err


def test_real_latency_cli_refuses_report_symlink_without_external_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    results = tmp_path / "results"
    monkeypatch.setattr(contract, "RESULTS_DIR", results)
    run = results / "run"
    weights = run / "weights/best.pt"
    weights.parent.mkdir(parents=True)
    weights.write_bytes(b"synthetic")

    class FastModel(torch.nn.Module):
        def forward(self, inputs: torch.Tensor) -> torch.Tensor:
            return torch.zeros(len(inputs), contract.CLASSES)

    record = {"seed": 20261018, "model": {"architecture": "compact_cnn"}}
    monkeypatch.setattr(cli, "load_model", lambda *_args: (FastModel(), weights, record))
    monkeypatch.setattr(
        contract, "check_data_contract", lambda: ({}, {"val": arrays([0])})
    )
    external = tmp_path / "external-latency.json"
    original = b"OWNER LATENCY TARGET MUST STAY BYTE IDENTICAL"
    external.write_bytes(original)
    (run / "latency_cpu.json").symlink_to(external)
    assert cli.main(["latency", "--weights", str(weights), "--device", "cpu"]) == 1
    assert external.read_bytes() == original
    assert (run / "latency_cpu.json").is_symlink()
    assert "regular non-symlink" in capsys.readouterr().err


def test_atomic_json_write_replaces_regular_file_without_temporary_residue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    results = tmp_path / "results"
    monkeypatch.setattr(contract, "RESULTS_DIR", results)
    output = results / "run/report.json"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"old regular file")
    contract.write_json(output, {"status": "PASS", "value": 7})
    assert json.loads(output.read_text(encoding="utf-8")) == {"status": "PASS", "value": 7}
    assert [path.name for path in output.parent.iterdir()] == ["report.json"]


def test_json_write_rejects_symlinked_parent_without_external_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    results = tmp_path / "results"
    results.mkdir()
    monkeypatch.setattr(contract, "RESULTS_DIR", results)
    external = tmp_path / "external-run"
    external.mkdir()
    (results / "run").symlink_to(external, target_is_directory=True)
    with pytest.raises(RuntimeError, match="symlink component"):
        contract.write_json(results / "run/report.json", {"must_not": "escape"})
    assert list(external.iterdir()) == []


def test_new_run_directory_rejects_symlink_component(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    external = tmp_path / "external"
    external.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(external, target_is_directory=True)
    monkeypatch.setattr(contract, "RESULTS_DIR", linked)
    with pytest.raises(RuntimeError, match="symlink component"):
        contract.prepare_run_directory(linked / "run")
    assert list(external.iterdir()) == []
