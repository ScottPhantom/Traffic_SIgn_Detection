"""Build the fail-closed D1 pilot R2 notebook from the frozen R6 smoke notebook."""

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "detector/colab/d1_train_checkpoint_r6.ipynb"
OUTPUT = REPO_ROOT / "detector/colab/d1_train_pilot_r2.ipynb"
SOURCE_SHA256 = "e42716fad4eb7b8d651565b611f11936d6a7b8b624832dccad8e513c55263fa6"

REPLACEMENTS = (
    ("# CPV301 D1 checkpoint/recovery smoke R4-R6", "# CPV301 D1 100-epoch pilot R2", 1),
    (
        "This successor notebook uses only train/val. Run `MODE = 'fresh'` first: it "
        "intentionally pauses after one completed epoch and leaves a verified Drive checkpoint. "
        "Disconnect the runtime, reconnect a new L4 runtime, change only `MODE = 'resume'`, and "
        "Run all again. Do not start the 100-epoch pilot until the resulting package passes "
        "independent QA.",
        "Pilot R2 uses only train/val and disables early stopping. Run `MODE = 'fresh'` first to "
        "persist epoch 1, disconnect that runtime, connect a new L4 runtime, change only "
        "`MODE = 'resume'`, and Run all through epoch 100. An abrupt runtime loss before a "
        "terminal record may be retried with `MODE = 'resume'`; preserve any recorded failure for "
        "review. Sealed-test export and final evaluation are forbidden.",
        1,
    ),
    (
        'CODE_COMMIT = "47c86d17430808ceeee6e1a1a553cf6fef88e5ed"  '
        "# QA-passed R4-R6 implementation",
        'CODE_COMMIT = "939f6bbce9f5c955b13ebcc84addd5083d242355"  '
        "# QA-passed Pilot R2 implementation",
        1,
    ),
    (
        'RUN_LABEL = "checkpoint_smoke_seed_20261018_r4_r6"',
        'RUN_LABEL = "pilot_seed_20261018_r2"',
        1,
    ),
    (
        'str(REPO_DIR / "detector/colab/run_d1_colab_checkpoint_r6.py")',
        'str(REPO_DIR / "detector/colab/run_d1_colab_pilot_r2.py")',
        1,
    ),
    ('    "2",\n', '    "100",\n', 1),
    (
        '    "--batch",\n    "4",\n',
        '    "--batch",\n    "4",\n    "--patience",\n    "0",\n',
        1,
    ),
    ('    "checkpoint_smoke_r4_r6",\n', '    "pilot_100e_seed_20261018_r2",\n', 1),
    (
        '    print("Checkpoint smoke leg PASS. Disconnect runtime, reconnect L4, set '
        'MODE=resume, Run all.")',
        '    print("Pilot epoch 1 PASS. Disconnect runtime, connect a new L4, set MODE=resume, "'
        ' "and Run all.")',
        1,
    ),
    (
        '    print({"resume_smoke": "PASS", "archive": str(archives[0]), "latest": latest})',
        '    assert execution["training_outcome"]["status"] in {'
        '"COMPLETED", "COMPLETED_FROM_FINAL_CHECKPOINT"}\n'
        '    assert execution["training_outcome"]["completed_epoch"] == 100\n'
        '    assert latest["generation"] == "epoch-0100", latest\n'
        '    print({"pilot_100_epochs": "PASS", "archive": str(archives[0]), "latest": latest})',
        1,
    ),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    if sha256_file(SOURCE) != SOURCE_SHA256:
        raise RuntimeError("frozen R6 notebook hash differs")
    notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
    combined = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    for before, _, expected_count in REPLACEMENTS:
        if combined.count(before) != expected_count:
            raise RuntimeError(f"replacement cardinality differs: {before[:80]!r}")
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        source = "".join(cell["source"])
        for before, after, _ in REPLACEMENTS:
            source = source.replace(before, after)
        cell["source"] = source.splitlines(keepends=True)
    OUTPUT.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return notebook


if __name__ == "__main__":
    build()
