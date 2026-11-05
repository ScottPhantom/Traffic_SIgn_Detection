"""D1-A2-R1 resumable training: the pilot with exactly one change, `data` = the A2 repeat list.

Contract: `docs/review/d1_a2_r1_run_contract.md` (status
`FROZEN_AWAITING_INDEPENDENT_SOURCE_QA_NOT_AUTHORIZED`). Append-only successor that follows the
D1-A3-R1 pattern (`m1.resumable_train_a3_r1`) and reuses the unchanged `m1.resumable_train`
checkpoint/resume/finalisation path.

Every pilot argument is kept: seed 20261018, 100 epochs, patience 0 (the pilot's value, read from
its `args.yaml` and `run_contract.json`; Ultralytics treats 0 as "no early stopping"), batch 4,
imgsz 1280, workers 4, fraction 1.0, `fliplr=0`, deterministic, pretrained YOLO11s `85a76fe8…`,
`optimizer` left at Ultralytics `auto` as in the pilot. The only train-argument difference is
`data`, which points to a runtime YAML whose single changed line is `train:` (the A2 list).

Before any data or model is touched the trainer refuses unless an Owner authorization record path
and its SHA-256 are passed; the record must name this experiment, the A2 list SHA-256 and the
roster SHA-256, and must contain the exact authorization line `AUTHORIZATION_LINE`. The source
itself carries `TRAINING_AUTHORIZED = False`.

The A2 list is built or verified (roster `0ce6afdc…`, list `90d735d6…`) before training, its hashes
enter the checkpoint recovery binding (so a checkpoint resumes only with the same list and the
same authorization) and `run_contract.json`. At `on_train_start` the trainer checks that the
Ultralytics train dataset holds exactly the 4,687 runtime-list entries.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import re
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from m1 import a2_repeat_list_r1 as a2list
from m1 import contract
from m1 import resumable_train as base
from m1 import yolo54_improvement_r3 as r3

BASE_RECOVERY_BINDING = base.recovery_binding
BASE_TRAIN_ARGUMENTS = base.train_arguments
EXPERIMENT = "D1-A2-R1"
PILOT_RUN = r3.RUN
SINGLE_CHANGE = "data"
TRAINING_AUTHORIZED = False
SEALED_TEST_ACCESSED = False
AUTHORIZATION_DIR = Path("docs/review")
AUTHORIZATION_LINE = "OWNER_AUTHORIZES_TRAINING: D1-A2-R1"
FROZEN = {
    "seed": 20261018,
    "epochs": 100,
    "imgsz": 1280,
    "batch": 4,
    "workers": 4,
    "fraction": 1.0,
    "patience": 0,
    "tag": "a2_r1",
}
# Module attribute so tests can substitute a synthetic export specification.
SPEC = a2list.SPEC


def _validate_frozen(args: argparse.Namespace) -> None:
    observed = {key: getattr(args, key) for key in FROZEN}
    if observed != FROZEN:
        raise RuntimeError(f"{EXPERIMENT} frozen arguments differ: {observed!r}")
    if str(args.device) != "0":
        raise RuntimeError(f"{EXPERIMENT} requires CUDA device 0")
    if args.resume and args.stop_after_epoch is not None:
        raise RuntimeError(f"{EXPERIMENT} resume forbids --stop-after-epoch")


def verify_owner_authorization(
    root: Path, path: Path | str | None, sha256: str | None, spec: a2list.Spec
) -> dict[str, str]:
    """Refuse unless a hash-matching Owner record authorizes exactly this A2 list."""
    if path is None or sha256 is None:
        raise RuntimeError(
            f"{EXPERIMENT} refuses to train without an Owner authorization record path and SHA-256"
        )
    relative = Path(path)
    if (
        relative.is_absolute()
        or relative.parent != AUTHORIZATION_DIR
        or not relative.name.endswith(".md")
        or relative.name == "d1_a2_r1_run_contract.md"
    ):
        raise RuntimeError(
            f"Owner authorization must be a repo-relative docs/review record: {path}"
        )
    if re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise RuntimeError("Owner authorization SHA-256 must be 64 lowercase hex digits")
    data = r3.guard(root.absolute(), relative).read_bytes()
    if a2list.sha256_bytes(data) != sha256:
        raise RuntimeError("Owner authorization record SHA-256 differs")
    text = data.decode("utf-8")
    if AUTHORIZATION_LINE not in {line.strip() for line in text.splitlines()}:
        raise RuntimeError(f"Owner authorization record lacks the line {AUTHORIZATION_LINE!r}")
    for required in (EXPERIMENT, spec.train_list_sha256, spec.repeated_roster_sha256):
        if required not in text:
            raise RuntimeError(f"Owner authorization record does not name {required}")
    return {"path": relative.as_posix(), "sha256": sha256}


def prepare_a2_data(root: Path, spec: a2list.Spec) -> dict[str, Any]:
    """Build-or-verify the canonical list, then materialise the runtime list and data YAML."""
    verified = a2list.ensure(root, spec)
    return a2list.materialize_runtime(root, verified, spec)


def _a2_binding_fields(a2: dict[str, Any], authorization: dict[str, str]) -> dict[str, Any]:
    return {
        "experiment": EXPERIMENT,
        "single_change": SINGLE_CHANGE,
        "owner_authorization_sha256": authorization["sha256"],
        "a2_rule_id": a2["rule_id"],
        "a2_train_list_sha256": a2["train_list_sha256"],
        "a2_repeated_roster_sha256": a2["repeated_roster_sha256"],
        "a2_train_list_entries": a2["train_list_entries"],
    }


def recovery_binding(
    *,
    bound: dict[str, Any],
    model: dict[str, str],
    environment: dict[str, Any],
    args: argparse.Namespace,
    a2: dict[str, Any],
    authorization: dict[str, str],
) -> dict[str, Any]:
    binding = BASE_RECOVERY_BINDING(bound=bound, model=model, environment=environment, args=args)
    return {**binding, **_a2_binding_fields(a2, authorization)}


def train_arguments(
    *,
    bound: dict[str, Any],
    args: argparse.Namespace,
    results_dir: Path,
    name: str,
    a2: dict[str, Any],
) -> dict[str, Any]:
    pilot = BASE_TRAIN_ARGUMENTS(bound=bound, args=args, results_dir=results_dir, name=name)
    return {**pilot, SINGLE_CHANGE: a2["runtime_data_yaml"]}


def run_contract_extras(a2: dict[str, Any], authorization: dict[str, str]) -> dict[str, Any]:
    return {
        "experiment": EXPERIMENT,
        "pilot_run": PILOT_RUN,
        "single_change": SINGLE_CHANGE,
        "a2_data": dict(a2),
        "owner_authorization": dict(authorization),
        "sealed_test_accessed": False,
    }


def dataset_guard(expected: Counter[str]) -> Callable[[Any], None]:
    """`on_train_start` callback: the Ultralytics train set must equal the runtime list."""

    def check(trainer: Any) -> None:
        observed = Counter(os.path.normpath(str(f)) for f in trainer.train_loader.dataset.im_files)
        if observed != expected:
            raise RuntimeError(
                f"{EXPERIMENT} train dataset differs from the A2 list: "
                f"{sum(observed.values())} entries vs {sum(expected.values())}"
            )

    return check


def plan(spec: a2list.Spec = SPEC) -> dict[str, Any]:
    """The frozen source specification; carries no authorization."""
    return {
        "experiment": EXPERIMENT,
        "pilot_run": PILOT_RUN,
        "single_change": SINGLE_CHANGE,
        "frozen": dict(FROZEN),
        "patience_source": "pilot args.yaml and run_contract.json: patience 0",
        "data": "<runtime A2 data YAML: pilot data.yaml with train: -> A2 list>",
        "rule_id": a2list.RULE_ID,
        "train_list_sha256": spec.train_list_sha256,
        "repeated_roster_sha256": spec.repeated_roster_sha256,
        "train_list_entries": spec.train_list_entries,
        "repeat_yolo_ids": dict(spec.yolo_ids),
        "training_authorized": TRAINING_AUTHORIZED,
        "sealed_test_accessed": SEALED_TEST_ACCESSED,
    }


def execute(
    args: argparse.Namespace,
    *,
    yolo_factory: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    _validate_frozen(args)
    root = contract.REPO_ROOT
    spec = SPEC
    authorization = verify_owner_authorization(
        root, args.owner_authorization, args.owner_authorization_sha256, spec
    )
    a2 = prepare_a2_data(root, spec)
    expected_entries = a2list.runtime_entries(a2)
    if sum(expected_entries.values()) != spec.train_list_entries:
        raise RuntimeError(f"{EXPERIMENT} runtime list size differs from the frozen spec")

    if yolo_factory is None:
        from ultralytics import YOLO

        yolo_factory = YOLO
    inner_factory: Callable[[str], Any] = yolo_factory

    def guarded_factory(source: str) -> Any:
        model = inner_factory(source)
        model.add_callback("on_train_start", dataset_guard(expected_entries))
        return model

    original_binding = base.recovery_binding
    original_arguments = base.train_arguments
    original_write_json = base.write_json
    extras = run_contract_extras(a2, authorization)

    def write_a2_json(path: Path, payload: dict[str, Any]) -> None:
        if path.name == "run_contract.json":
            if payload.get("train_args", {}).get("data") != a2["runtime_data_yaml"]:
                raise RuntimeError(f"{EXPERIMENT} run contract data is not the A2 runtime YAML")
            payload = {**payload, **extras}
        original_write_json(path, payload)

    base.recovery_binding = functools.partial(recovery_binding, a2=a2, authorization=authorization)
    base.train_arguments = functools.partial(train_arguments, a2=a2)
    base.write_json = write_a2_json
    try:
        outcome = base.execute(args, yolo_factory=guarded_factory)
    finally:
        base.recovery_binding = original_binding
        base.train_arguments = original_arguments
        base.write_json = original_write_json

    if args.stop_after_epoch is None and (
        outcome.get("status") not in {"COMPLETED", "COMPLETED_FROM_FINAL_CHECKPOINT"}
        or outcome.get("completed_epoch") != FROZEN["epochs"]
    ):
        raise RuntimeError(f"{EXPERIMENT} did not complete the frozen 100 epochs: {outcome!r}")
    return {**outcome, "experiment": EXPERIMENT, "a2_train_list_sha256": a2["train_list_sha256"]}


def parser() -> argparse.ArgumentParser:
    root = base.parser()
    root.description = __doc__
    root.set_defaults(
        seed=FROZEN["seed"],
        epochs=FROZEN["epochs"],
        imgsz=FROZEN["imgsz"],
        batch=FROZEN["batch"],
        workers=FROZEN["workers"],
        fraction=FROZEN["fraction"],
        patience=FROZEN["patience"],
        tag=FROZEN["tag"],
    )
    root.add_argument("--owner-authorization", type=Path)
    root.add_argument("--owner-authorization-sha256")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        outcome = execute(args)
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}))
        return 1
    print(json.dumps(outcome, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
