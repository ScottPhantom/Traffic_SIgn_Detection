#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "${script_dir}/.." && pwd)"
cd "${project_dir}"

# uv resolves the lockfile and installs every declared project/dev/extra
# dependency before the app starts.
uv sync --all-extras --all-groups
exec uv run --no-sync cpv301 web "$@"
