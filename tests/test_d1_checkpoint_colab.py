from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_runner():
    path = REPO_ROOT / "detector/colab/run_d1_colab_checkpoint_r1.py"
    spec = importlib.util.spec_from_file_location("test_d1_checkpoint_colab_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner()


def arguments(*, mode: str) -> argparse.Namespace:
    return argparse.Namespace(
        mode=mode,
        seed=20261018,
        epochs=2,
        imgsz=1280,
        batch=4,
        device="0",
        workers=4,
        fraction=1.0,
        patience=30,
        tag="checkpoint_smoke_r1",
        stop_after_epoch=1 if mode == "fresh" else None,
    )


def test_successor_commands_separate_pause_and_resume(tmp_path: Path) -> None:
    model = tmp_path / "models/yolo11s.pt"
    state = tmp_path / "drive/state"
    fresh = runner.build_train_command(arguments(mode="fresh"), model, state)
    resumed = runner.build_train_command(arguments(mode="resume"), model, state)
    assert "--stop-after-epoch" in fresh
    assert "--resume" not in fresh
    assert "--resume" in resumed
    assert "--stop-after-epoch" not in resumed
    for command in (fresh, resumed):
        assert command[:5] == ["uv", "run", "python", "-m", "m1.resumable_train"]
        assert "export-test" not in command
        assert "--final-eval" not in command


def test_successor_notebook_is_unexecuted_fail_closed_and_train_val_only() -> None:
    path = REPO_ROOT / "detector/colab/d1_train_checkpoint_r1.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert all(cell.get("execution_count") is None for cell in code_cells)
    assert all(not cell.get("outputs") for cell in code_cells)
    source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert "PENDING_AFTER_QA" not in source
    assert "b9ce31f7278e41f51f6bd7430c2f97f653321618" in source
    assert "Wait for QA, commit and push before Colab" in source
    assert "run_d1_colab_checkpoint_r1.py" in source
    assert "--stop-after-epoch" in source
    assert 'MODE == "fresh"' in source
    assert 'MODE in {"fresh", "resume"}' in source
    assert "recovery/latest.json" in source
    assert "epoch-0001" in source
    assert "export-test" not in source
    assert "--final-eval" not in source
    assert "data/processed/m1_yolo/test" not in source


def test_successor_runner_does_not_mutate_pinned_primary_runner() -> None:
    source = (
        REPO_ROOT / "detector/colab/run_d1_colab_checkpoint_r1.py"
    ).read_text(encoding="utf-8")
    assert "run_d1_colab.py" in source
    assert "extract_historical_bundle" in source
    assert "source_repo_git_commit" in source
    assert "code_repo_git_commit" in source
    assert "test_included\": False" in source


def test_historical_bundle_reads_each_gzip_member_once_in_archive_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    archive_path = tmp_path / "bundle.tar.gz"
    payloads = {
        "data/train/a.txt": b"alpha",
        "data/val/b.txt": b"bravo",
    }
    records = [
        {
            "path": name,
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "source_split": "train" if "/train/" in name else "val",
            "kind": "fixture",
        }
        for name, payload in payloads.items()
    ]
    with tarfile.open(archive_path, "w:gz") as archive:
        for name, payload in payloads.items():
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
        manifest_payload = b"{}"
        manifest_member = tarfile.TarInfo("manifest.json")
        manifest_member.size = len(manifest_payload)
        archive.addfile(manifest_member, io.BytesIO(manifest_payload))
    with tarfile.open(archive_path, "r:gz") as archive:
        members = {member.name: member for member in archive.getmembers()}

    class FakeBuilder:
        MANIFEST_MEMBER = "manifest.json"

        @staticmethod
        def read_archive_manifest(_archive_path: Path):
            return (
                {
                    "repo_git_commit": "historical",
                    "contract": "train-val-only",
                    "file_count": len(records),
                    "files": records,
                },
                members,
            )

        @staticmethod
        def expected_records(_repo_root: Path):
            return records, {
                "repo_git_commit": "successor",
                "contract": "train-val-only",
            }

        @staticmethod
        def _safe_destination(root: Path, name: str) -> Path:
            return root / name

        @staticmethod
        def sha256_file(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest()

    real_open = tarfile.open
    reads: list[str] = []

    class CountingArchive:
        def __init__(self, archive):
            self.archive = archive

        def __enter__(self):
            self.archive.__enter__()
            return self

        def __exit__(self, *args):
            return self.archive.__exit__(*args)

        def extractfile(self, member):
            reads.append(member.name)
            return self.archive.extractfile(member)

    monkeypatch.setattr(runner, "load_bundle_builder", lambda _repo_root: FakeBuilder)
    monkeypatch.setattr(
        runner.tarfile,
        "open",
        lambda path, mode: CountingArchive(real_open(path, mode)),
    )

    result = runner.extract_historical_bundle(repo_root, archive_path)

    assert result["status"] == "EXTRACTED_FOR_SUCCESSOR"
    assert reads == list(payloads)
    for name, payload in payloads.items():
        assert (repo_root / name).read_bytes() == payload
        assert not (repo_root / name).with_name(f".{Path(name).name}.partial").exists()


@pytest.mark.parametrize(
    "child",
    (
        "colab_train.log",
        "DB_logger.db",
        "colab_execution.json",
        "colab_execution.json.tmp",
        "execution_attempts.jsonl",
    ),
)
def test_resume_rejects_writable_child_symlinks_without_touching_target(
    tmp_path: Path, child: str
) -> None:
    state = tmp_path / "state"
    (state / "recovery").mkdir(parents=True)
    (state / "recovery/latest.json").write_text("{}", encoding="utf-8")
    sentinel = tmp_path / f"outside-{child.replace('/', '_')}"
    sentinel.write_text("sentinel", encoding="utf-8")
    (state / child).symlink_to(sentinel)
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"invalid-but-regular")
    with pytest.raises(RuntimeError, match="writable state child is a symlink"):
        runner.main(
            [
                "--repo-root",
                str(REPO_ROOT),
                "--bundle",
                str(bundle),
                "--state-dir",
                str(state),
                "--mode",
                "resume",
            ]
        )
    assert sentinel.read_text(encoding="utf-8") == "sentinel"
