"""One-command launcher for the CPV301 AutoDrive Streamlit webapp."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
RUN_WEB_SCRIPT = PROJECT_ROOT / "scripts" / "run-web.sh"


def main(argv: list[str] | None = None) -> int:
    """Sync the project environment and run the existing Streamlit entry point."""

    forwarded_args = sys.argv[1:] if argv is None else argv
    command = [str(RUN_WEB_SCRIPT), *forwarded_args]

    if not RUN_WEB_SCRIPT.is_file():
        print(f"Không tìm thấy web launcher: {RUN_WEB_SCRIPT}", file=sys.stderr)
        return 1

    print("Đang chuẩn bị môi trường và khởi động CPV301 AutoDrive...", flush=True)
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
        )
    except KeyboardInterrupt:
        return 130
    except OSError as exc:
        print(f"Không thể khởi động webapp: {exc}", file=sys.stderr)
        return 1
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
