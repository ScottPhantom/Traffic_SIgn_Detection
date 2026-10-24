from __future__ import annotations

import hashlib
import json
from pathlib import Path

from colab import run_vgg16_54_r1_r1
from vgg16_54.contract import verify_smoke_qa

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/review/generated/vgg16_54_r1_long_r5_launch_contract.json"
SMOKE_PROOF = ROOT / "docs/review/generated/vgg16_54_r1_r4_two_runtime_smoke_qa_proof.json"
SMOKE_SHA256 = "898a440709dd477b9ec70569b52464047adb55de8ed48325eeef091f3e759132"
BUNDLE_SHA256 = "bae147b6f7c6f80ac973923df4b60fd31b6587221fe75eaa2d9ed4b93ee6a51b"
RESUME_DIGEST = "648af06dd95af878657f2f041dd78a18cdf3137c27858176454204065a3e1ff5"


def load_contract() -> dict[str, object]:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_long_r5_contract_is_closed_and_proof_bound() -> None:
    contract = load_contract()
    assert set(contract) == {
        "schema_version",
        "package",
        "authorization",
        "source_commit",
        "runner_module",
        "working_directory",
        "input_root",
        "state_path",
        "mode",
        "stop_after",
        "resume_runtime_digest",
        "config_sha256",
        "bundle_manifest_sha256",
        "owner_approval",
        "source_qa",
        "runtime_source_qa",
        "smoke_qa",
        "sealed_test_accessed",
        "command",
    }
    assert contract["schema_version"] == 1
    assert contract["package"] == "VGG16-54-R1-LONG-R5"
    assert contract["mode"] == "resume"
    assert contract["stop_after"] is None
    assert contract["resume_runtime_digest"] == RESUME_DIGEST
    assert contract["bundle_manifest_sha256"] == BUNDLE_SHA256
    assert contract["sealed_test_accessed"] is False
    assert contract["smoke_qa"] == {
        "path": (
            "/content/drive/MyDrive/CPV301/Traffic_Sign_Detector/M1_D1_Colab/"
            "vgg16_54_r1_r4_two_runtime_smoke_qa_proof.json"
        ),
        "sha256": SMOKE_SHA256,
    }
    assert hashlib.sha256(SMOKE_PROOF.read_bytes()).hexdigest() == SMOKE_SHA256
    verify_smoke_qa(SMOKE_PROOF, SMOKE_SHA256, BUNDLE_SHA256)


def test_long_r5_command_parses_as_resume_without_smoke_stop() -> None:
    contract = load_contract()
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
    assert str(arguments.state) == contract["state_path"]
    assert str(arguments.root) == contract["input_root"]
    assert arguments.bundle_manifest_sha256 == BUNDLE_SHA256
    assert arguments.smoke_qa_sha256 == SMOKE_SHA256
    assert arguments.runtime_source_qa_sha256 == (
        "cbd531302429908354858640ac501e8c0d1805c5dec5462bf5e6a1e611b044f5"
    )
