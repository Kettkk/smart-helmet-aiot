#!/usr/bin/env sh
set -eu

input="data/samples/outdoor-hiking-20s.mp4"
output="experiments/results/vision-demo"
stride="${VISION_FRAME_STRIDE:-5}"

./scripts/download-video-sample.sh

mkdir -p "$output"

docker compose run --rm vision-service \
  --input /workspace/data/samples/"$(basename "$input")" \
  --output-dir /workspace/experiments/results/vision-demo \
  --model /models/yolo11n.pt \
  --device cpu \
  --target-class person \
  --frame-stride "$stride" \
  --confidence 0.25 \
  --image-size 640 \
  --warmup-runs 1

printf 'Vision demo complete: %s\n' "$output"
