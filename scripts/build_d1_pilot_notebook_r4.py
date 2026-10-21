"""Build the post-train D1 Pilot R4 packaging-repair notebook from frozen R3."""

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "detector/colab/d1_train_pilot_r3.ipynb"
OUTPUT = REPO_ROOT / "detector/colab/d1_train_pilot_r4.ipynb"
SOURCE_SHA256 = "67d8d24a3f432b17085069d7d7545a3673bdd3fa6771be094f698c6e99e8ee81"
TRAINING_COMMIT = "939f6bbce9f5c955b13ebcc84addd5083d242355"
R3_COMMIT = "e20a69541e3a6327739238fc71691109ce8f51d0"
R3_SHA256 = "8c9b23472091f6c677d635a54e4f4e8b896e1fcf204d627ba56eb208db00c49c"
R4_COMMIT = "2cc45b467456e9300df613839d94c5cb0bbdcbba"
R4_SHA256 = "ffcc88e2339b349775ca34e5e30531a102d0bcab1d45fa0dff9b1ea8bead25ad"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, before: str, after: str, label: str) -> str:
    if text.count(before) != 1:
        raise RuntimeError(f"{label} replacement cardinality differs")
    return text.replace(before, after, 1)


def build() -> dict:
    if sha256_file(SOURCE) != SOURCE_SHA256:
        raise RuntimeError("frozen Pilot R3 notebook hash differs")
    notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
    if len(notebook["cells"]) != 7:
        raise RuntimeError("Pilot R3 notebook cell count differs")
    notebook["metadata"].pop("r4_status", None)
    notebook["metadata"]["pilot_r4_status"] = "PENDING_INDEPENDENT_QA"

    notebook["cells"][0]["source"] = (
        "# CPV301 D1 Pilot R4 epoch-0100 packaging repair\n\n"
        "Resume-only post-train repair for the verified `epoch-0100` checkpoint. It never trains "
        "another epoch. The governed training checkout, R3 predecessor, and independently "
        "QA-passed R4 sidecar are fetched with separate immutable commit and SHA-256 pins. "
        "Run all once on L4. "
        "Sealed-test export and final evaluation are forbidden.\n"
    ).splitlines(keepends=True)

    cell2 = "".join(notebook["cells"][2]["source"])
    cell2 = replace_once(
        cell2,
        'MODE = "resume"  # fixed: recover verified epoch-0014; never restart fresh',
        'MODE = "resume"  # fixed: package verified epoch-0100; never train again',
        "cell 2 mode",
    )
    cell2 = replace_once(
        cell2,
        f'RECOVERY_COMMIT = "{R3_COMMIT}"  # independently QA-passed R3 sidecar',
        f'RECOVERY_COMMIT = "{R3_COMMIT}"  # hash-pinned R3 predecessor sidecar',
        "cell 2 R3 comment",
    )
    anchor = (
        'RECOVERY_RUNNER_URL = (\n'
        '    "https://raw.githubusercontent.com/ScottPhantom/Traffic_SIgn_Detection/"\n'
        '    f"{RECOVERY_COMMIT}/detector/colab/run_d1_colab_pilot_r3.py"\n'
        ')\n'
    )
    injected = anchor + (
        f'R4_COMMIT = "{R4_COMMIT}"  # independently QA-passed R4 packaging repair\n'
        f'R4_RUNNER_SHA256 = "{R4_SHA256}"\n'
        'R4_RUNNER = Path("/content/run_d1_colab_pilot_r4.py")\n'
        'R4_RUNNER_URL = (\n'
        '    "https://raw.githubusercontent.com/ScottPhantom/Traffic_SIgn_Detection/"\n'
        '    f"{R4_COMMIT}/detector/colab/run_d1_colab_pilot_r4.py"\n'
        ')\n'
    )
    cell2 = replace_once(cell2, anchor, injected, "cell 2 R4 pins")
    old_helper = cell2[cell2.index("def verified_recovery_runner_bytes():") :]
    new_helper = (
        "def verified_runner_bytes(path, expected_sha256):\n"
        "    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)\n"
        "    try:\n"
        "        info = os.fstat(fd)\n"
        "        assert stat.S_ISREG(info.st_mode), \"Runner is not a regular file\"\n"
        "        chunks = []\n"
        "        while True:\n"
        "            chunk = os.read(fd, 1024 * 1024)\n"
        "            if not chunk:\n"
        "                break\n"
        "            chunks.append(chunk)\n"
        "    finally:\n"
        "        os.close(fd)\n"
        "    payload = b\"\".join(chunks)\n"
        "    assert hashlib.sha256(payload).hexdigest() == expected_sha256\n"
        "    return payload\n"
    )
    cell2 = cell2.replace(old_helper, new_helper)
    notebook["cells"][2]["source"] = cell2.splitlines(keepends=True)

    cell3 = "".join(notebook["cells"][3]["source"])
    cell3 = replace_once(
        cell3,
        'assert (STATE_DIR / "recovery/latest.json").is_file(), '
        '"Verified recovery pointer missing"\n',
        'assert (STATE_DIR / "recovery/latest.json").is_file(), '
        '"Verified recovery pointer missing"\n'
        'preflight_latest = json.loads((STATE_DIR / "recovery/latest.json").read_text())\n'
        'assert preflight_latest["generation"] == "epoch-0100", preflight_latest\n',
        "cell 3 final checkpoint",
    )
    cell3 = "import json\n" + cell3
    notebook["cells"][3]["source"] = cell3.splitlines(keepends=True)

    cell4 = "".join(notebook["cells"][4]["source"])
    start = cell4.index("runner_bytes = urllib.request.urlopen")
    end = cell4.index("assert not subprocess.run", start)
    download_block = (
        "def download_verified_runner(path, url, expected_sha256):\n"
        "    payload = urllib.request.urlopen(url, timeout=60).read()\n"
        "    assert hashlib.sha256(payload).hexdigest() == expected_sha256\n"
        "    if os.path.lexists(path):\n"
        "        assert verified_runner_bytes(path, expected_sha256) == payload\n"
        "    else:\n"
        "        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW\n"
        "        fd = os.open(path, flags, 0o600)\n"
        "        with os.fdopen(fd, \"wb\") as handle:\n"
        "            handle.write(payload)\n"
        "        assert verified_runner_bytes(path, expected_sha256) == payload\n"
        "    return payload\n\n"
        "r3_bytes = download_verified_runner(\n"
        "    RECOVERY_RUNNER, RECOVERY_RUNNER_URL, RECOVERY_RUNNER_SHA256\n"
        ")\n"
        "r4_bytes = download_verified_runner(R4_RUNNER, R4_RUNNER_URL, R4_RUNNER_SHA256)\n"
    )
    cell4 = cell4[:start] + download_block + cell4[end:]
    old_print = (
        'print({"training_commit": observed, "recovery_commit": RECOVERY_COMMIT, '
        '"recovery_runner_sha256": RECOVERY_RUNNER_SHA256, "checkout_clean": True})'
    )
    new_print = (
        'print({"training_commit": observed, "r3_commit": RECOVERY_COMMIT, '
        '"r3_sha256": RECOVERY_RUNNER_SHA256, "r4_commit": R4_COMMIT, '
        '"r4_sha256": R4_RUNNER_SHA256, "checkout_clean": True})'
    )
    cell4 = replace_once(cell4, old_print, new_print, "cell 4 summary")
    notebook["cells"][4]["source"] = cell4.splitlines(keepends=True)

    cell5 = "".join(notebook["cells"][5]["source"])
    cell5 = replace_once(
        cell5,
        "verified_runner_bytes = verified_recovery_runner_bytes()",
        "verified_r4_bytes = verified_runner_bytes(R4_RUNNER, R4_RUNNER_SHA256)",
        "cell 5 runner read",
    )
    cell5 = replace_once(
        cell5,
        "subprocess.run(command, input=verified_runner_bytes, check=True)",
        "subprocess.run(command, input=verified_r4_bytes, check=True)",
        "cell 5 runner execution",
    )
    notebook["cells"][5]["source"] = cell5.splitlines(keepends=True)

    notebook["cells"][6]["source"] = (
        "import importlib.util\n"
        "import json\n"
        "import sys\n\n"
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
        'spec = importlib.util.spec_from_file_location("d1_pilot_r4_live_verifier", R4_RUNNER)\n'
        "assert spec is not None and spec.loader is not None\n"
        "verifier = importlib.util.module_from_spec(spec)\n"
        "sys.modules[spec.name] = verifier\n"
        "spec.loader.exec_module(verifier)\n"
        "pilot_r3 = verifier.load_pilot_r3(REPO_DIR)\n"
        "runtime_evidence = pilot_r3.verify_live_state(STATE_DIR, REPO_DIR)\n"
        'assert runtime_evidence["runtime_evidence"]["distinct_runtime_digests"] is True\n'
        'assert runtime_evidence["runtime_evidence"]["sealed_test_accessed"] is False\n'
        "print({\n"
        '    "pilot_100_epochs_and_packaging": "PASS",\n'
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
