#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "${script_dir}/.." && pwd)"
cd "${project_dir}"

command -v uv >/dev/null 2>&1 || {
  echo "Missing uv. Install it from https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
}

uv sync --all-extras --all-groups

uv run --no-sync python -m ipykernel install --user \
  --name cpv301-autodrive \
  --display-name "Python (CPV301 AutoDrive)"

uv run --no-sync python -c \
  "import cpv301_autodrive, tensorflow, streamlit; print('CPV301 environment ready')"

echo "Run the webapp with: ./scripts/run-web.sh"
