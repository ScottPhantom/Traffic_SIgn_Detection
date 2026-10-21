"""Build the governed D1 100-epoch pilot notebook from the QA-passed R6 smoke notebook."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "detector/colab/d1_train_checkpoint_r6.ipynb"
OUTPUT = REPO_ROOT / "detector/colab/d1_train_pilot_r1.ipynb"

REPLACEMENTS = (
    (
        "# CPV301 D1 checkpoint/recovery smoke R4-R6",
        "# CPV301 D1 single-seed 100-epoch pilot R1",
    ),
    (
        "This successor notebook uses only train/val. Run `MODE = 'fresh'` first: it "
        "intentionally pauses after one completed epoch and leaves a verified Drive checkpoint. "
        "Disconnect the runtime, reconnect a new L4 runtime, change only `MODE = 'resume'`, and "
        "Run all again. Do not start the 100-epoch pilot until the resulting package passes "
        "independent QA.",
        "This pilot uses only train/val and the QA-passed R6 recovery runner. Run "
        "`MODE = 'fresh'` first: it intentionally pauses after epoch 1 and leaves a verified "
        "Drive checkpoint. Disconnect that runtime, connect a new L4 runtime, change only "
        "`MODE = 'resume'`, and Run all to continue through epoch 100. If Colab abruptly loses "
        "the runtime before recording a terminal attempt, connect another L4 runtime and run "
        "`MODE = 'resume'` again. For a recorded FAILED attempt, preserve the Drive state and stop "
        "for review. Sealed-test export and final evaluation are forbidden.",
    ),
    (
        'RUN_LABEL = "checkpoint_smoke_seed_20261018_r4_r6"',
        'RUN_LABEL = "pilot_seed_20261018_r1"',
    ),
    ('    "2",\n', '    "100",\n'),
    ('    "checkpoint_smoke_r4_r6",\n', '    "pilot_100e_seed_20261018_r1",\n'),
    (
        '    print("Checkpoint smoke leg PASS. Disconnect runtime, reconnect L4, set '
        'MODE=resume, Run all.")',
        '    print("Pilot epoch 1 checkpoint PASS. Disconnect runtime, reconnect a new L4, "'
        ' "set MODE=resume, and Run all.")',
    ),
    (
        '    print({"resume_smoke": "PASS", "archive": str(archives[0]), "latest": latest})',
        '    assert latest["generation"] == "epoch-0100", latest\n'
        '    print({"pilot_100_epochs": "PASS", "archive": str(archives[0]), "latest": latest})',
    ),
)


def build() -> dict:
    notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        cell["execution_count"] = None if cell["cell_type"] == "code" else cell.get(
            "execution_count"
        )
        cell["outputs"] = [] if cell["cell_type"] == "code" else cell.get("outputs", [])
        source = "".join(cell["source"])
        for before, after in REPLACEMENTS:
            source = source.replace(before, after)
        cell["source"] = source.splitlines(keepends=True)
    OUTPUT.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return notebook


if __name__ == "__main__":
    build()
