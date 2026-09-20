#!/usr/bin/env sh
set -eu

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
venv_dir="${NETWORK_VENV:-$repo_root/.venv-network}"

if [ ! -x "$venv_dir/bin/python" ]; then
  python3 -m venv "$venv_dir"
fi

"$venv_dir/bin/python" -m pip install --quiet --requirement "$repo_root/experiments/requirements.txt"
cd "$repo_root"
case "${1:-}" in
  -h|--help)
    exec "$venv_dir/bin/python" experiments/network_reliability.py "$@"
    ;;
esac
PYTHONPATH="$repo_root" "$venv_dir/bin/python" experiments/network_reliability.py "$@"
"$venv_dir/bin/python" experiments/plot_network_results.py

printf 'Network results: experiments/results/network\n'
printf 'Network plots: experiments/plots/network\n'
