#!/usr/bin/env sh
set -eu

if [ ! -f experiments/results/frame-sampling/summary.csv ]; then
  printf 'Missing benchmark results. Run ./scripts/run-vision-benchmark.sh first.\n' >&2
  exit 1
fi

docker compose run --rm --entrypoint python vision-service \
  /workspace/experiments/plot_vision_results.py \
  --results-dir /workspace/experiments/results/frame-sampling \
  --baseline-stride 5 \
  --output-dir /workspace/experiments/plots/vision

printf 'Vision plots complete: experiments/plots/vision\n'
