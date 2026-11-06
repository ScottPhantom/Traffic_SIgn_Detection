"""D1-S2-R1: pilot training with seed 20261019 as the sole configuration change."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from m1 import contract
from m1 import resumable_train as base
from m1 import yolo54_improvement_r3 as r3

EXPERIMENT = "D1-S2-R1"
PILOT_RUN = r3.RUN
PILOT_CONTRACT_SHA256 = "9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88"
AUTHORIZATION_LINE = "OWNER_AUTHORIZES_TRAINING: D1-S2-R1"
AUTHORIZATION_DIR = Path("docs/review")
TRAINING_AUTHORIZED = False  # Presence of this module is not authorization.
SEALED_TEST_ACCESSED = False
FROZEN = {
    "seed": 20261019,
    "epochs": 100,
    "imgsz": 1280,
    "batch": 4,
    "workers": 4,
    "fraction": 1.0,
    "patience": 0,
    "tag": "s2_r1",
}


def validate_frozen(args: argparse.Namespace) -> None:
    observed = {key: getattr(args, key) for key in FROZEN}
    if observed != FROZEN:
        raise RuntimeError(f"{EXPERIMENT} frozen arguments differ: {observed!r}")
    if str(args.device) != "0":
        raise RuntimeError(f"{EXPERIMENT} requires CUDA device 0")
    if args.resume and args.stop_after_epoch is not None:
        raise RuntimeError(f"{EXPERIMENT} resume forbids --stop-after-epoch")
    if not args.resume and args.stop_after_epoch != 1:
        raise RuntimeError(f"{EXPERIMENT} fresh run requires --stop-after-epoch 1")


def verify_owner_authorization(root: Path, path: Path | None, sha256: str | None) -> dict[str, str]:
    if path is None or sha256 is None:
        raise RuntimeError(f"{EXPERIMENT} requires an Owner authorization path and SHA-256")
    relative = Path(path)
    if (
        relative.is_absolute()
        or relative.parent != AUTHORIZATION_DIR
        or relative.suffix != ".md"
        or "test" in relative.name.lower()
        or relative.name == "d1_s2_r1_run_contract.md"
    ):
        raise RuntimeError("Owner authorization must be a repo-relative docs/review record")
    if re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise RuntimeError("Owner authorization SHA-256 must be 64 lowercase hex digits")
    data = r3.guard(root.absolute(), relative).read_bytes()
    if hashlib.sha256(data).hexdigest() != sha256:
        raise RuntimeError("Owner authorization record SHA-256 differs")
    lines = {line.strip() for line in data.decode("utf-8").splitlines()}
    if AUTHORIZATION_LINE not in lines:
        raise RuntimeError("Owner authorization record lacks the exact authorization line")
    text = data.decode("utf-8")
    for required in (EXPERIMENT, PILOT_CONTRACT_SHA256, str(FROZEN["seed"])):
        if required not in text:
            raise RuntimeError(f"Owner authorization record does not name {required}")
    return {"path": relative.as_posix(), "sha256": sha256}


def execute(
    args: argparse.Namespace, *, yolo_factory: Callable[[str], Any] | None = None
) -> dict[str, Any]:
    validate_frozen(args)
    authorization = verify_owner_authorization(
        contract.REPO_ROOT, args.owner_authorization, args.owner_authorization_sha256
    )
    original_binding = base.recovery_binding
    original_arguments = base.train_arguments
    original_write_json = base.write_json

    def bound_binding(**kwargs: Any) -> dict[str, Any]:
        # Use the captured predecessor, avoiding recursion while base is patched.
        return {
            **original_binding(**kwargs),
            "experiment": EXPERIMENT,
            "single_change": "seed",
            "pilot_contract_sha256": PILOT_CONTRACT_SHA256,
            "owner_authorization_sha256": authorization["sha256"],
        }

    def bound_arguments(**kwargs: Any) -> dict[str, Any]:
        actual = original_arguments(**kwargs)
        expected = {
            "batch": 4,
            "data": kwargs["bound"]["data_yaml"],
            "deterministic": True,
            "device": "0",
            "epochs": 100,
            "exist_ok": True,
            "fliplr": 0.0,
            "fraction": 1.0,
            "imgsz": 1280,
            "name": kwargs["name"],
            "patience": 0,
            "plots": False,
            "pretrained": True,
            "project": str(kwargs["results_dir"]),
            "seed": 20261019,
            "workers": 4,
        }
        if actual != expected:
            raise RuntimeError(
                f"{EXPERIMENT} train_args differ from pilot except seed/run identity"
            )
        return actual

    def write_s2_json(path: Path, payload: dict[str, Any]) -> None:
        if path.name == "run_contract.json":
            payload = {
                **payload,
                "experiment": EXPERIMENT,
                "pilot_run": PILOT_RUN,
                "single_change": "seed",
                "pilot_contract_sha256": PILOT_CONTRACT_SHA256,
                "owner_authorization": authorization,
                "sealed_test_accessed": False,
            }
        original_write_json(path, payload)

    base.recovery_binding = bound_binding
    base.train_arguments = bound_arguments
    base.write_json = write_s2_json
    try:
        outcome = base.execute(args, yolo_factory=yolo_factory)
    finally:
        base.recovery_binding = original_binding
        base.train_arguments = original_arguments
        base.write_json = original_write_json
    if args.stop_after_epoch is None and (
        outcome.get("status") not in {"COMPLETED", "COMPLETED_FROM_FINAL_CHECKPOINT"}
        or outcome.get("completed_epoch") != 100
    ):
        raise RuntimeError(f"{EXPERIMENT} did not complete epoch 100: {outcome!r}")
    return {**outcome, "experiment": EXPERIMENT}


def parser() -> argparse.ArgumentParser:
    root = base.parser()
    root.description = __doc__
    root.set_defaults(**FROZEN)
    root.add_argument("--owner-authorization", type=Path)
    root.add_argument("--owner-authorization-sha256")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        outcome = execute(args)
    except (OSError, RuntimeError, ValueError, KeyError, UnicodeDecodeError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}))
        return 1
    print(json.dumps(outcome, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
