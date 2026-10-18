#!/usr/bin/env python3
"""Verify the roster, hashes, and declared outcome of a D1 Colab result package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from run_d1_colab import verify_result_archive


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_result_archive(args.archive.resolve(), args.manifest.resolve())
    except (OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
