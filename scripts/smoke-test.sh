#!/usr/bin/env sh
set -eu

base_url="${BASE_URL:-http://localhost:8080}"
dashboard_url="${DASHBOARD_URL:-http://localhost:3000}"
device_id="${SIMULATOR_DEVICE_ID:-helmet-sim-001}"

health="$(curl --fail --silent "$base_url/actuator/health")"
latest="$(curl --fail --silent "$base_url/api/v1/devices/$device_id/latest")"
history="$(curl --fail --silent "$base_url/api/v1/devices/$device_id/telemetry?limit=3")"
dashboard="$(curl --fail --silent "$dashboard_url")"

VISION_RESULTS_API_URL="$base_url/api/v1/vision/benchmarks" \
  ./scripts/publish-vision-results.sh
vision="$(curl --fail --silent "$base_url/api/v1/vision/benchmarks/latest")"

printf '%s' "$health" | grep -q '"status":"UP"'
printf '%s' "$latest" | grep -q "\"deviceId\":\"$device_id\""
printf '%s' "$history" | grep -q "\"deviceId\":\"$device_id\""
printf '%s' "$dashboard" | grep -q '<title>HELM Field Telemetry</title>'
printf '%s' "$vision" | grep -q '"operatingPointStride"'

printf 'Smoke test passed for %s\n' "$device_id"
printf 'Dashboard available at %s\n' "$dashboard_url"
printf 'Latest telemetry: %s\n' "$latest"
printf 'Latest vision benchmark is available through the backend API.\n'
