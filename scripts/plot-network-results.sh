#!/usr/bin/env sh
set -eu

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
venv_dir="${NETWORK_VENV:-$repo_root/.venv-network}"

if [ ! -x "$venv_dir/bin/python" ]; then
  printf 'Missing %s. Run ./scripts/run-network-experiments.sh first.\n' "$venv_dir" >&2
  exit 1
fi

cd "$repo_root"
PYTHONPATH="$repo_root" "$venv_dir/bin/python" experiments/plot_network_results.py "$@"
