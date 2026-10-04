from __future__ import annotations

import subprocess
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

LAUNCHER_SPEC = spec_from_file_location(
    "project_main",
    Path(__file__).resolve().parents[1] / "main.py",
)
assert LAUNCHER_SPEC is not None and LAUNCHER_SPEC.loader is not None
launcher = module_from_spec(LAUNCHER_SPEC)
LAUNCHER_SPEC.loader.exec_module(launcher)


def test_main_runs_project_web_launcher(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_run(command, *, cwd, check):
        observed.update(command=command, cwd=cwd, check=check)
        return subprocess.CompletedProcess(command, returncode=0)

    monkeypatch.setattr(launcher.subprocess, "run", fake_run)

    assert launcher.main(["--port", "8511"]) == 0
    assert observed == {
        "command": [str(launcher.RUN_WEB_SCRIPT), "--port", "8511"],
        "cwd": launcher.PROJECT_ROOT,
        "check": False,
    }


def test_main_returns_shell_interrupt_code(monkeypatch) -> None:
    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(launcher.subprocess, "run", interrupt)

    assert launcher.main([]) == 130
