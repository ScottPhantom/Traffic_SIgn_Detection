#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "${script_dir}/.." && pwd)"
cd "${project_dir}"

# Install the exact locked runtime. Development tools are optional.
uv sync --locked --no-dev
exec uv run --no-sync cpv301 web "$@"
