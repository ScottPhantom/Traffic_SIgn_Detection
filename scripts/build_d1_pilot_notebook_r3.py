"""Build the resume-only D1 Pilot R3 recovery notebook from frozen Pilot R2."""

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "detector/colab/d1_train_pilot_r2.ipynb"
OUTPUT = REPO_ROOT / "detector/colab/d1_train_pilot_r3.ipynb"
SOURCE_SHA256 = "721c5c0f35eb58719bcc6b5a71ce24cce136388bb8060bc2393aec7a5da4b1ae"
TRAINING_COMMIT = "939f6bbce9f5c955b13ebcc84addd5083d242355"
RECOVERY_COMMIT = "e20a69541e3a6327739238fc71691109ce8f51d0"
RECOVERY_RUNNER_SHA256 = "8c9b23472091f6c677d635a54e4f4e8b896e1fcf204d627ba56eb208db00c49c"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    if sha256_file(SOURCE) != SOURCE_SHA256:
        raise RuntimeError("frozen Pilot R2 notebook hash differs")
    notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
    if len(notebook["cells"]) != 7:
        raise RuntimeError("Pilot R2 notebook cell count differs")

    notebook["cells"][0]["source"] = (
        "# CPV301 D1 100-epoch pilot R3 retry recovery\n\n"
        "Resume-only successor for the verified Pilot R2 checkpoint at `epoch-0014`. The governed "
        "training checkout remains pinned to its original commit while the independently QA-passed "
        "R3 orchestration sidecar is fetched from a separate pinned commit and SHA-256 verified. "
        "Run all once on L4. Sealed-test export and final evaluation are forbidden.\n"
    ).splitlines(keepends=True)

    cell2 = "".join(notebook["cells"][2]["source"])
    replacements = (
        (
            'MODE = "fresh"  # first run: fresh; after reconnecting a new runtime: resume',
            'MODE = "resume"  # fixed: recover verified epoch-0014; never restart fresh',
        ),
        (
            f'CODE_COMMIT = "{TRAINING_COMMIT}"  # QA-passed Pilot R2 implementation',
            f'TRAINING_COMMIT = "{TRAINING_COMMIT}"  # checkpoint-bound clean training checkout\n'
            "CODE_COMMIT = TRAINING_COMMIT\n"
            f'RECOVERY_COMMIT = "{RECOVERY_COMMIT}"  # independently QA-passed R3 sidecar\n'
            f'RECOVERY_RUNNER_SHA256 = "{RECOVERY_RUNNER_SHA256}"\n'
            'RECOVERY_RUNNER = Path("/content/run_d1_colab_pilot_r3.py")\n'
            'RECOVERY_RUNNER_URL = (\n'
            '    "https://raw.githubusercontent.com/ScottPhantom/Traffic_SIgn_Detection/"\n'
            '    f"{RECOVERY_COMMIT}/detector/colab/run_d1_colab_pilot_r3.py"\n'
            ')',
        ),
        ('assert MODE in {"fresh", "resume"}', 'assert MODE == "resume"'),
    )
    for before, after in replacements:
        if cell2.count(before) != 1:
            raise RuntimeError(f"cell 2 replacement cardinality differs: {before!r}")
        cell2 = cell2.replace(before, after)
    import_anchor = "import hashlib\nimport re\n"
    if cell2.count(import_anchor) != 1:
        raise RuntimeError("cell 2 import anchor cardinality differs")
    cell2 = cell2.replace(
        import_anchor, "import hashlib\nimport os\nimport re\nimport stat\n", 1
    )
    cell2 += (
        "\n\ndef verified_recovery_runner_bytes():\n"
        "    fd = os.open(RECOVERY_RUNNER, os.O_RDONLY | os.O_NOFOLLOW)\n"
        "    try:\n"
        "        info = os.fstat(fd)\n"
        "        assert stat.S_ISREG(info.st_mode), \"Recovery runner is not a regular file\"\n"
        "        chunks = []\n"
        "        while True:\n"
        "            chunk = os.read(fd, 1024 * 1024)\n"
        "            if not chunk:\n"
        "                break\n"
        "            chunks.append(chunk)\n"
        "    finally:\n"
        "        os.close(fd)\n"
        "    payload = b\"\".join(chunks)\n"
        "    assert hashlib.sha256(payload).hexdigest() == RECOVERY_RUNNER_SHA256\n"
        "    return payload\n"
    )
    notebook["cells"][2]["source"] = cell2.splitlines(keepends=True)

    cell3 = "".join(notebook["cells"][3]["source"])
    before_state = (
        'if MODE == "fresh":\n'
        '    assert not STATE_DIR.exists(), f"Fresh state already exists: {STATE_DIR}"\n'
        'else:\n'
        '    assert (STATE_DIR / "recovery/latest.json").is_file(), '
        '"Verified recovery pointer missing"'
    )
    after_state = (
        'assert (STATE_DIR / "recovery/latest.json").is_file(), '
        '"Verified recovery pointer missing"'
    )
    if cell3.count(before_state) != 1:
        raise RuntimeError("cell 3 state guard cardinality differs")
    notebook["cells"][3]["source"] = cell3.replace(
        before_state, after_state
    ).splitlines(keepends=True)

    cell4 = "".join(notebook["cells"][4]["source"])
    if cell4.count("import sys\n") != 1:
        raise RuntimeError("cell 4 import cardinality differs")
    cell4 = cell4.replace("import sys\n", "import sys\nimport urllib.request\n", 1)
    anchor = 'assert observed == CODE_COMMIT\n'
    injected = (
        'assert observed == TRAINING_COMMIT\n'
        'runner_bytes = urllib.request.urlopen(RECOVERY_RUNNER_URL, timeout=60).read()\n'
        'assert hashlib.sha256(runner_bytes).hexdigest() == RECOVERY_RUNNER_SHA256\n'
        'if os.path.lexists(RECOVERY_RUNNER):\n'
        '    assert verified_recovery_runner_bytes() == runner_bytes\n'
        'else:\n'
        '    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW\n'
        '    fd = os.open(RECOVERY_RUNNER, flags, 0o600)\n'
        '    with os.fdopen(fd, "wb") as handle:\n'
        '        handle.write(runner_bytes)\n'
        '    assert verified_recovery_runner_bytes() == runner_bytes\n'
    )
    if cell4.count(anchor) != 1:
        raise RuntimeError("cell 4 commit assertion cardinality differs")
    cell4 = cell4.replace(anchor, injected, 1)
    old_print = 'print({"code_commit": observed, "checkout_clean": True})'
    new_print = (
        'print({"training_commit": observed, "recovery_commit": RECOVERY_COMMIT, '
        '"recovery_runner_sha256": RECOVERY_RUNNER_SHA256, "checkout_clean": True})'
    )
    if cell4.count(old_print) != 1:
        raise RuntimeError("cell 4 output cardinality differs")
    notebook["cells"][4]["source"] = cell4.replace(
        old_print, new_print
    ).splitlines(keepends=True)

    cell5 = "".join(notebook["cells"][5]["source"])
    runner_path = 'str(REPO_DIR / "detector/colab/run_d1_colab_pilot_r2.py")'
    if cell5.count(runner_path) != 1:
        raise RuntimeError("cell 5 runner cardinality differs")
    cell5 = cell5.replace(
        "command = [\n    sys.executable,\n    " + runner_path + ",",
        'verified_runner_bytes = verified_recovery_runner_bytes()\ncommand = [\n'
        '    sys.executable,\n    "-",',
        1,
    )
    fresh_block = 'if MODE == "fresh":\n    command += ["--stop-after-epoch", "1"]\n'
    if cell5.count(fresh_block) != 1:
        raise RuntimeError("cell 5 fresh branch cardinality differs")
    cell5 = cell5.replace(fresh_block, "")
    run_call = "subprocess.run(command, check=True)"
    if cell5.count(run_call) != 1:
        raise RuntimeError("cell 5 subprocess cardinality differs")
    cell5 = cell5.replace(
        run_call, "subprocess.run(command, input=verified_runner_bytes, check=True)", 1
    )
    notebook["cells"][5]["source"] = cell5.splitlines(keepends=True)

    notebook["cells"][6]["source"] = (
        "import json\n"
        "import sys\n\n"
        "import types\n\n"
        'execution = json.loads((STATE_DIR / "colab_execution.json").read_text())\n'
        'latest = json.loads((STATE_DIR / "recovery/latest.json").read_text())\n'
        'assert execution["sealed_test_accessed"] is False\n'
        'assert execution["status"] == "SUCCEEDED", execution\n'
        'archives = sorted(STATE_DIR.glob("*_result.tar.gz"))\n'
        "assert len(archives) == 1, archives\n"
        'assert execution["training_outcome"]["status"] in {\n'
        '    "COMPLETED", "COMPLETED_FROM_FINAL_CHECKPOINT"\n'
        "}\n"
        'assert execution["training_outcome"]["completed_epoch"] == 100\n'
        'assert latest["generation"] == "epoch-0100", latest\n'
        "verified_runner_bytes = verified_recovery_runner_bytes()\n"
        'module_name = "d1_pilot_r3_live_verifier"\n'
        "verifier = types.ModuleType(module_name)\n"
        "verifier.__file__ = str(RECOVERY_RUNNER)\n"
        "sys.modules[module_name] = verifier\n"
        "exec(\n"
        '    compile(verified_runner_bytes, str(RECOVERY_RUNNER), "exec"),\n'
        "    verifier.__dict__,\n"
        ")\n"
        "runtime_evidence = verifier.verify_live_state(STATE_DIR, REPO_DIR)\n"
        'assert runtime_evidence["runtime_evidence"]["distinct_runtime_digests"] is True\n'
        'assert runtime_evidence["runtime_evidence"]["sealed_test_accessed"] is False\n'
        "print({\n"
        '    "pilot_100_epochs": "PASS",\n'
        '    "archive": str(archives[0]),\n'
        '    "latest": latest,\n'
        '    "runtime_evidence": runtime_evidence,\n'
        "})\n"
    ).splitlines(keepends=True)

    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
    OUTPUT.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return notebook


if __name__ == "__main__":
    build()
