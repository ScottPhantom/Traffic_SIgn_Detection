"""D1-S2-R1 source gates and the exact pilot argument delta."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pytest

from m1 import contract
from m1 import resumable_train as base
from m1 import resumable_train_s2_r1 as s2


def args(**changes: object) -> argparse.Namespace:
    values = {
        **s2.FROZEN,
        "device": "0",
        "resume": False,
        "stop_after_epoch": 1,
        "owner_authorization": Path("docs/review/auth.md"),
        "owner_authorization_sha256": "a" * 64,
    }
    return argparse.Namespace(**{**values, **changes})


def test_pilot_contract_is_pinned_and_only_seed_changes() -> None:
    path = contract.REPO_ROOT / "results/experiments" / s2.PILOT_RUN / "run_contract.json"
    if not path.is_file():
        pytest.skip("local pilot artifact unavailable")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == s2.PILOT_CONTRACT_SHA256
    pilot = json.loads(path.read_text())
    candidate = base.train_arguments(
        bound={"data_yaml": pilot["train_args"]["data"]},
        args=args(),
        results_dir=Path(pilot["train_args"]["project"]),
        name=pilot["train_args"]["name"],
    )
    assert set(candidate) == set(pilot["train_args"])
    assert {key for key in candidate if candidate[key] != pilot["train_args"][key]} == {"seed"}
    assert candidate["seed"] == 20261019
    assert candidate["data"] == pilot["train_args"]["data"]
    assert "optimizer" not in candidate


@pytest.mark.parametrize(
    "field,value",
    [
        ("seed", 20261020),
        ("epochs", 40),
        ("batch", 8),
        ("patience", 30),
        ("imgsz", 640),
        ("workers", 2),
        ("fraction", 0.5),
        ("tag", "other"),
    ],
)
def test_frozen_values_refuse_changes(field: str, value: object) -> None:
    with pytest.raises(RuntimeError, match="frozen arguments differ"):
        s2.validate_frozen(args(**{field: value}))


def test_fresh_and_resume_boundaries() -> None:
    with pytest.raises(RuntimeError, match="fresh run requires"):
        s2.validate_frozen(args(stop_after_epoch=None))
    with pytest.raises(RuntimeError, match="resume forbids"):
        s2.validate_frozen(args(resume=True, stop_after_epoch=1))
    s2.validate_frozen(args(resume=True, stop_after_epoch=None))


def test_authorization_gate_before_predecessor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(contract, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(base, "execute", lambda *_a, **_k: pytest.fail("predecessor called"))
    with pytest.raises(FileNotFoundError):
        s2.execute(args(), yolo_factory=lambda _p: None)


def test_authorization_record_and_patched_predecessor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = tmp_path / "docs/review/auth.md"
    record.parent.mkdir(parents=True)
    record.write_text(
        f"{s2.AUTHORIZATION_LINE}\n{s2.EXPERIMENT}\n{s2.PILOT_CONTRACT_SHA256}\n20261019\n",
        encoding="utf-8",
    )
    sha = hashlib.sha256(record.read_bytes()).hexdigest()
    monkeypatch.setattr(contract, "REPO_ROOT", tmp_path)
    before = (base.recovery_binding, base.train_arguments, base.write_json)

    def fake_execute(_args: argparse.Namespace, **_kw: object) -> dict[str, object]:
        bound = {"data_yaml": "/content/Traffic_Sign_Detector/data/processed/m1_yolo/data.yaml"}
        train = base.train_arguments(
            bound=bound,
            args=_args,
            results_dir=Path("/content/Traffic_Sign_Detector/results/experiments"),
            name="s2-run",
        )
        assert train["seed"] == 20261019 and train["data"] == bound["data_yaml"]
        binding = base.recovery_binding(
            bound={
                "export_manifest_sha256": "x",
                "class_map_sha256": "y",
                "split_stem_sha256": {"test": "z"},
            },
            model={"sha256": "w"},
            environment={"git_commit": "c", "detector_lock_sha256": "l"},
            args=_args,
        )
        assert binding["owner_authorization_sha256"] == sha
        assert binding["pilot_contract_sha256"] == s2.PILOT_CONTRACT_SHA256
        return {"status": "PAUSED_FOR_RESUME", "completed_epoch": 1}

    monkeypatch.setattr(base, "execute", fake_execute)
    outcome = s2.execute(args(owner_authorization_sha256=sha))
    assert outcome["experiment"] == s2.EXPERIMENT
    assert (base.recovery_binding, base.train_arguments, base.write_json) == before


def test_authorization_refuses_other_seed_and_forbidden_filename(tmp_path: Path) -> None:
    record = tmp_path / "docs/review/auth.md"
    record.parent.mkdir(parents=True)
    record.write_text(f"{s2.AUTHORIZATION_LINE}\n{s2.PILOT_CONTRACT_SHA256}\n20261020\n")
    sha = hashlib.sha256(record.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError, match="does not name 20261019"):
        s2.verify_owner_authorization(tmp_path, Path("docs/review/auth.md"), sha)
    with pytest.raises(RuntimeError, match="repo-relative"):
        s2.verify_owner_authorization(tmp_path, Path("docs/review/test_auth.md"), sha)
