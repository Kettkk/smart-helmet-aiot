#!/usr/bin/env sh
set -eu

input="data/samples/outdoor-hiking-20s.mp4"
output="experiments/results/frame-sampling"

./scripts/download-video-sample.sh

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

if [ "${VISION_PUBLISH_RESULTS:-true}" = "true" ]; then
  ./scripts/publish-vision-results.sh
else
  python3 experiments/export_dashboard_results.py
  printf 'Prepared backend payload without publishing it.\n'
fi
