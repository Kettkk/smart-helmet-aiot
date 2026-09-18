#!/usr/bin/env sh
set -eu

input="data/samples/outdoor-hiking-20s.mp4"
output="experiments/results/frame-sampling"

if [ ! -f "$input" ]; then
  printf 'Missing local video sample: %s\n' "$input" >&2
  printf 'See data/samples/README.md for provenance and preparation.\n' >&2
  exit 1
fi

mkdir -p "$output"

docker compose run --rm --entrypoint python vision-service \
  -m app.benchmark \
  --input /workspace/data/samples/outdoor-hiking-20s.mp4 \
  --output-dir /workspace/experiments/results/frame-sampling \
  --model /models/yolo11n.pt \
  --device cpu \
  --target-class person \
  --strides 1 2 5 10 \
  --confidence 0.25 \
  --image-size 640 \
  --warmup-runs 1

printf 'Frame-sampling benchmark complete: %s\n' "$output"
