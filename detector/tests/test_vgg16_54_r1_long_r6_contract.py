from __future__ import annotations

import hashlib
import json
from pathlib import Path

from colab import run_vgg16_54_r1_r1
from vgg16_54.contract import verify_smoke_qa

ROOT = Path(__file__).resolve().parents[2]
R5 = ROOT / "docs/review/generated/vgg16_54_r1_long_r5_launch_contract.json"
R6 = ROOT / "docs/review/generated/vgg16_54_r1_long_r6_launch_contract.json"
SMOKE_PROOF = ROOT / "docs/review/generated/vgg16_54_r1_r4_two_runtime_smoke_qa_proof.json"
SMOKE_SHA256 = "898a440709dd477b9ec70569b52464047adb55de8ed48325eeef091f3e759132"
BUNDLE_SHA256 = "bae147b6f7c6f80ac973923df4b60fd31b6587221fe75eaa2d9ed4b93ee6a51b"
WORK_ROOT = "/content/vgg16_54_long_r6_work"


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_r6_changes_only_package_work_root_and_command_work_root() -> None:
    r5, r6 = load(R5), load(R6)
    assert set(r6) == set(r5) | {"work_root"}
    assert r6["package"] == "VGG16-54-R1-LONG-R6"
    assert r6["work_root"] == WORK_ROOT

    command5, command6 = r5["command"], r6["command"]
    assert isinstance(command5, list) and isinstance(command6, list)
    expected = list(command5)
    state_index = expected.index("--state")
    expected[state_index + 2 : state_index + 2] = ["--work-root", WORK_ROOT]
    assert command6 == expected

    ignored = {"package", "work_root", "command"}
    assert {key: value for key, value in r6.items() if key not in ignored} == {
        key: value for key, value in r5.items() if key not in ignored
    }


def test_r6_command_is_safe_long_resume_with_new_ephemeral_destination() -> None:
    contract = load(R6)
    command = contract["command"]
    assert isinstance(command, list)
    assert command[:5] == ["uv", "run", "python", "-m", contract["runner_module"]]
    assert "--stop-after" not in command
    assert "--final-eval" not in command
    assert "export-test" not in command
    assert "--split" not in command

    arguments = run_vgg16_54_r1_r1.parser().parse_args(command[5:])
    assert arguments.mode == "resume"
    assert arguments.stop_after is None
    assert str(arguments.work_root) == WORK_ROOT
    assert str(arguments.state) == contract["state_path"]
    assert contract["sealed_test_accessed"] is False
    assert hashlib.sha256(SMOKE_PROOF.read_bytes()).hexdigest() == SMOKE_SHA256
    verify_smoke_qa(SMOKE_PROOF, SMOKE_SHA256, BUNDLE_SHA256)
