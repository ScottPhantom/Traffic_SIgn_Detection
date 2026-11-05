"""D1-A2-R1 trainer tests: single change, authorization gate, smoke/resume binding."""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from test_a2_repeat_list_r1 import make_export

from m1 import a2_repeat_list_r1 as a2list
from m1 import contract
from m1 import resumable_train_a2_r1 as a2t
from m1 import yolo54_improvement_r3 as r3

PILOT_DIR = contract.REPO_ROOT / "results/experiments" / r3.RUN
PILOT_ARGS_SHA256 = "a457c6d51547477348c19a06ec4cf3c8794508169b2e0e1a43edc6260b7d16f0"
PILOT_CONTRACT_SHA256 = "9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_authorization(root: Path, spec: a2list.Spec, name: str = "auth.md", **kw: str) -> str:
    text = kw.get(
        "text",
        "# Owner authorization (synthetic)\n\n"
        f"{a2t.AUTHORIZATION_LINE}\n\n"
        f"Experiment {a2t.EXPERIMENT}; list {spec.train_list_sha256}; "
        f"roster {spec.repeated_roster_sha256}.\n",
    )
    path = root / "docs/review" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return sha(path.read_bytes())


def arguments(tmp_path: Path, *, resume: bool, auth: str | None, name: str = "auth.md"):
    return argparse.Namespace(
        model=tmp_path / "models/pretrained/yolo11s.pt",
        checkpoint_dir=tmp_path / "drive/recovery",
        results_dir=tmp_path / "results/experiments",
        resume=resume,
        stop_after_epoch=None if resume else 1,
        seed=20261018,
        epochs=100,
        imgsz=1280,
        batch=4,
        device="0",
        workers=4,
        fraction=1.0,
        patience=0,
        tag="a2_r1",
        owner_authorization=None if auth is None else Path("docs/review") / name,
        owner_authorization_sha256=auth,
    )


def patch_contract(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> a2list.Spec:
    spec = make_export(tmp_path)
    model = tmp_path / "models/pretrained/yolo11s.pt"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"approved-model")
    monkeypatch.setattr(a2t, "SPEC", spec)
    monkeypatch.setattr(contract, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        contract,
        "bind_training_model",
        lambda path: {"path": path, "sha256": "a" * 64, "origin": "test"},
    )
    monkeypatch.setattr(
        contract,
        "check_contract",
        lambda: {
            "export_manifest_sha256": "b" * 64,
            "class_map_sha256": "c" * 64,
            "split_stem_sha256": {"train": "d" * 64, "val": "e" * 64, "test": "f" * 64},
            "data_yaml": str(tmp_path / spec.export_dir / "data.yaml"),
        },
    )
    monkeypatch.setattr(
        contract,
        "environment",
        lambda: {"git_commit": "1" * 40, "detector_lock_sha256": "2" * 64},
    )
    monkeypatch.setattr(contract, "disable_telemetry", lambda: None)
    monkeypatch.setattr(contract, "RESULTS_DIR", tmp_path / "results/experiments")
    return spec


class FakeYOLO:
    observed: list[dict[str, object]] = []
    drop_duplicates = False

    def __init__(self, source: str) -> None:
        self.source = source
        self.callbacks: dict[str, list[object]] = {}

    def add_callback(self, event: str, callback: object) -> None:
        assert event in {"on_model_save", "on_train_start"}
        self.callbacks.setdefault(event, []).append(callback)

    def train(self, *, resume: bool = False, **kwargs: object) -> None:
        self.observed.append({"resume": resume, **kwargs})
        data = yaml.safe_load(Path(str(kwargs["data"])).read_text())
        files = Path(data["train"]).read_text().splitlines()
        if self.drop_duplicates:
            files = sorted(set(files))
        loader = SimpleNamespace(dataset=SimpleNamespace(im_files=files))
        for callback in self.callbacks.get("on_train_start", []):
            callback(SimpleNamespace(train_loader=loader))
        run = Path(str(kwargs["project"])) / str(kwargs["name"])
        (run / "weights").mkdir(parents=True, exist_ok=True)
        start = 2 if resume else 1
        for epoch in range(start, int(kwargs["epochs"]) + 1):
            (run / "weights/last.pt").write_bytes(f"last-{epoch}".encode())
            (run / "weights/best.pt").write_bytes(f"best-{epoch}".encode())
            (run / "results.csv").write_text(
                "epoch,loss\n" + "\n".join(f"{i},0.5" for i in range(1, epoch + 1)) + "\n",
                encoding="utf-8",
            )
            (run / "args.yaml").write_text("epochs: 100\nfliplr: 0.0\n", encoding="utf-8")
            trainer = SimpleNamespace(save_dir=run, epoch=epoch - 1, stop=False)
            for callback in self.callbacks.get("on_model_save", []):
                callback(trainer)
            if trainer.stop:
                break


class DuplicateDroppingYOLO(FakeYOLO):
    drop_duplicates = True


class EarlyStopYOLO(FakeYOLO):
    def train(self, *, resume: bool = False, **kwargs: object) -> None:
        super().train(resume=resume, **{**kwargs, "epochs": 3})


# ------------------------------------------------------------------------- single change


def test_single_change_against_pilot_args_yaml_and_run_contract(tmp_path: Path) -> None:
    args_yaml, run_contract = PILOT_DIR / "args.yaml", PILOT_DIR / "run_contract.json"
    if not args_yaml.is_file() or not run_contract.is_file():
        pytest.skip("pilot args.yaml/run_contract.json absent")
    assert sha(args_yaml.read_bytes()) == PILOT_ARGS_SHA256
    assert sha(run_contract.read_bytes()) == PILOT_CONTRACT_SHA256
    pilot_effective = yaml.safe_load(args_yaml.read_text())
    pilot_train = contract.strict_json(run_contract)["train_args"]

    a2_data = {"runtime_data_yaml": "/content/x/data/processed/d1_a2_r1/runtime/a2_data.yaml"}
    results = Path(pilot_train["project"])
    a2_train = a2t.train_arguments(
        bound={"data_yaml": pilot_train["data"]},
        args=arguments(tmp_path, resume=False, auth=None),
        results_dir=results,
        name=pilot_train["name"],
        a2=a2_data,
    )
    assert set(a2_train) == set(pilot_train)
    assert {k for k in a2_train if a2_train[k] != pilot_train[k]} == {"data"}
    assert a2_train["data"] == a2_data["runtime_data_yaml"]
    run_identity = {"data", "project", "name", "model", "resume", "save_dir"}
    for key, value in a2_train.items():
        if key not in run_identity:
            assert pilot_effective[key] == value, key
    assert (a2_train["patience"], a2_train["fliplr"], a2_train["epochs"]) == (0, 0.0, 100)
    assert (a2_train["batch"], a2_train["imgsz"], a2_train["seed"]) == (4, 1280, 20261018)
    # Pilot optimizer was `auto`; with 4,687 entries it still resolves to AdamW (<=10,000 iters).
    assert "optimizer" not in a2_train
    assert -(-4687 // max(4, pilot_effective["nbs"])) * 100 <= 10000


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("epochs", 40),
        ("seed", 20261019),
        ("batch", 8),
        ("patience", 30),
        ("imgsz", 640),
        ("workers", 2),
        ("fraction", 0.5),
        ("tag", "other"),
    ),
)
def test_frozen_a2_rejects_changed_argument(tmp_path: Path, field: str, value: object) -> None:
    args = arguments(tmp_path, resume=False, auth=None)
    setattr(args, field, value)
    with pytest.raises(RuntimeError, match="frozen arguments differ"):
        a2t._validate_frozen(args)


def test_resume_forbids_a_second_stop_boundary(tmp_path: Path) -> None:
    args = arguments(tmp_path, resume=True, auth=None)
    args.stop_after_epoch = 2
    with pytest.raises(RuntimeError, match="resume forbids"):
        a2t._validate_frozen(args)


def test_plan_carries_no_authorization() -> None:
    plan = a2t.plan()
    assert plan["training_authorized"] is False
    assert plan["sealed_test_accessed"] is False
    assert plan["frozen"]["patience"] == 0
    assert plan["repeat_yolo_ids"] == {"7": 7, "32": 33, "41": 42}
    assert plan["train_list_sha256"] == a2list.A2_TRAIN_LIST_SHA256
    assert a2t.TRAINING_AUTHORIZED is False


# ------------------------------------------------------------------------- authorization


def test_execute_refuses_without_authorization_before_touching_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_contract(monkeypatch, tmp_path)

    def must_not_run(*_args: object) -> None:
        raise AssertionError("data prepared before the authorization gate")

    monkeypatch.setattr(a2t, "prepare_a2_data", must_not_run)
    with pytest.raises(RuntimeError, match="refuses to train without an Owner authorization"):
        a2t.execute(arguments(tmp_path, resume=False, auth=None), yolo_factory=FakeYOLO)
    assert not (tmp_path / "drive").exists()


@pytest.mark.parametrize(
    ("case", "message"),
    (
        ("wrong_sha", "SHA-256 differs"),
        ("no_line", "lacks the line"),
        ("other_list", "does not name"),
        ("outside_docs", "repo-relative docs/review"),
        ("run_contract", "repo-relative docs/review"),
        ("bad_hex", "64 lowercase hex"),
    ),
)
def test_authorization_gate_refusals(tmp_path: Path, case: str, message: str) -> None:
    spec = make_export(tmp_path)
    path: Path | str = Path("docs/review/auth.md")
    if case == "no_line":
        digest = write_authorization(
            tmp_path,
            spec,
            text=f"{a2t.EXPERIMENT} {spec.train_list_sha256} {spec.repeated_roster_sha256}\n",
        )
    elif case == "other_list":
        digest = write_authorization(
            tmp_path, spec, text=f"{a2t.AUTHORIZATION_LINE}\n{a2t.EXPERIMENT} list 339 only\n"
        )
    else:
        digest = write_authorization(tmp_path, spec)
    if case == "wrong_sha":
        digest = "0" * 64
    elif case == "outside_docs":
        path = Path("auth.md")
    elif case == "run_contract":
        path = Path("docs/review/d1_a2_r1_run_contract.md")
    elif case == "bad_hex":
        digest = digest.upper()
    with pytest.raises(RuntimeError, match=message):
        a2t.verify_owner_authorization(tmp_path, path, digest, spec)


# ------------------------------------------------------------------------- smoke / resume


def test_fresh_smoke_pause_then_resume_binds_list_and_completes_100(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = patch_contract(monkeypatch, tmp_path)
    auth = write_authorization(tmp_path, spec)
    FakeYOLO.observed.clear()
    fresh = a2t.execute(arguments(tmp_path, resume=False, auth=auth), yolo_factory=FakeYOLO)
    assert fresh["status"] == "PAUSED_FOR_RESUME"
    assert fresh["completed_epoch"] == 1
    assert fresh["a2_train_list_sha256"] == spec.train_list_sha256

    latest = contract.strict_json(
        tmp_path / "drive/recovery/snapshots/epoch-0001/checkpoint_manifest.json"
    )
    binding = latest["binding"]
    assert binding["experiment"] == "D1-A2-R1"
    assert binding["a2_train_list_sha256"] == spec.train_list_sha256
    assert binding["a2_repeated_roster_sha256"] == spec.repeated_roster_sha256
    assert binding["owner_authorization_sha256"] == auth
    assert binding["patience"] == 0 and binding["epochs"] == 100

    shutil.rmtree(fresh["run_dir"])  # distinct runtime: run dir restored from the checkpoint
    resumed = a2t.execute(arguments(tmp_path, resume=True, auth=auth), yolo_factory=FakeYOLO)
    assert resumed["status"] == "COMPLETED"
    assert resumed["completed_epoch"] == 100
    record = contract.strict_json(Path(resumed["run_dir"]) / "run_contract.json")
    assert record["experiment"] == "D1-A2-R1"
    assert record["single_change"] == "data"
    assert record["sealed_test_accessed"] is False
    assert record["owner_authorization"] == {"path": "docs/review/auth.md", "sha256": auth}
    assert record["a2_data"]["train_list_sha256"] == spec.train_list_sha256
    assert record["train_args"]["data"] == record["a2_data"]["runtime_data_yaml"]
    assert record["contract"]["data_yaml"].endswith("m1_yolo/data.yaml")
    assert record["status"] == "TRAINED"
    assert [item["resume"] for item in FakeYOLO.observed] == [False, True]


def test_resume_refuses_a_different_authorization_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = patch_contract(monkeypatch, tmp_path)
    auth = write_authorization(tmp_path, spec)
    a2t.execute(arguments(tmp_path, resume=False, auth=auth), yolo_factory=FakeYOLO)
    other = write_authorization(
        tmp_path,
        spec,
        name="auth_other.md",
        text=(
            f"{a2t.AUTHORIZATION_LINE}\n{a2t.EXPERIMENT} {spec.train_list_sha256} "
            f"{spec.repeated_roster_sha256} (second record)\n"
        ),
    )
    with pytest.raises(RuntimeError, match="checkpoint binding differs"):
        a2t.execute(
            arguments(tmp_path, resume=True, auth=other, name="auth_other.md"),
            yolo_factory=FakeYOLO,
        )


def test_resume_refuses_a_changed_a2_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spec = patch_contract(monkeypatch, tmp_path)
    auth = write_authorization(tmp_path, spec)
    a2t.execute(arguments(tmp_path, resume=False, auth=auth), yolo_factory=FakeYOLO)
    listed = tmp_path / spec.out_dir / a2list.LIST_NAME
    listed.write_bytes(listed.read_bytes().replace(b"images/train/0006.jpg\n", b""))
    with pytest.raises(RuntimeError, match="differs from the recomputed list"):
        a2t.execute(arguments(tmp_path, resume=True, auth=auth), yolo_factory=FakeYOLO)


def test_dataset_guard_rejects_a_deduplicated_train_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = patch_contract(monkeypatch, tmp_path)
    auth = write_authorization(tmp_path, spec)
    with pytest.raises(RuntimeError, match="train dataset differs from the A2 list"):
        a2t.execute(
            arguments(tmp_path, resume=False, auth=auth), yolo_factory=DuplicateDroppingYOLO
        )


def test_early_stopped_long_run_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = patch_contract(monkeypatch, tmp_path)
    auth = write_authorization(tmp_path, spec)
    args = arguments(tmp_path, resume=False, auth=auth)
    args.stop_after_epoch = None
    with pytest.raises(RuntimeError, match="did not complete the frozen 100 epochs"):
        a2t.execute(args, yolo_factory=EarlyStopYOLO)


def test_parser_defaults_are_the_frozen_pilot_values(tmp_path: Path) -> None:
    parsed = a2t.parser().parse_args(
        ["--model", str(tmp_path / "m.pt"), "--checkpoint-dir", str(tmp_path / "r")]
    )
    assert {key: getattr(parsed, key) for key in a2t.FROZEN} == a2t.FROZEN
    assert parsed.owner_authorization is None
