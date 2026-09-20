#!/usr/bin/env sh
set -eu

payload="experiments/results/frame-sampling/dashboard-payload.json"
endpoint="${VISION_RESULTS_API_URL:-http://localhost:8080/api/v1/vision/benchmarks}"

if ! command -v curl >/dev/null 2>&1; then
  printf 'Required command not found: curl\n' >&2
  exit 1
fi

python3 experiments/export_dashboard_results.py --output "$payload"

response_file="$(mktemp)"
trap 'rm -f "$response_file"' EXIT HUP INT TERM

status="$(curl --silent --show-error \
  --output "$response_file" \
  --write-out '%{http_code}' \
  --header 'Content-Type: application/json' \
  --request POST \
  --data-binary "@$payload" \
  "$endpoint")"

if [ "$status" != "201" ]; then
  printf 'Vision benchmark publication failed with HTTP %s:\n' "$status" >&2
  cat "$response_file" >&2
  exit 1
fi

printf 'Published vision benchmark to %s\n' "$endpoint"
