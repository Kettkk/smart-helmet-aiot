#!/usr/bin/env sh
set -eu

target="data/samples/outdoor-hiking-20s.mp4"
source_url="https://commons.wikimedia.org/wiki/Special:Redirect/file/Be_Considerate_of_Others_Day_7_-_The_Seven_Days_of_Leave_No_Trace_(11571149015).webm"
source_sha256="2df5b656d692d7c882a8a504a35223e08fb101974c412f6f62fe71b213feca01"
target_sha256="49a5a01f2721be546fb45900ea927efcc04431c1abe181a651b53d90547d64c7"

sha256() {
  python3 - "$1" <<'PY'
import hashlib
import pathlib
import sys

digest = hashlib.sha256()
with pathlib.Path(sys.argv[1]).open("rb") as handle:
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(block)
print(digest.hexdigest())
PY
}

for command in curl ffmpeg python3; do
  if ! command -v "$command" >/dev/null 2>&1; then
    printf 'Required command not found: %s\n' "$command" >&2
    exit 1
  fi
done

if [ -f "$target" ] && [ "$(sha256 "$target")" = "$target_sha256" ]; then
  printf 'Verified video sample: %s\n' "$target"
  exit 0
fi

temporary_dir="$(mktemp -d)"
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM
source_file="$temporary_dir/source.webm"
prepared_file="$temporary_dir/outdoor-hiking-20s.mp4"

printf 'Downloading the public-domain reference video...\n'
curl --location --fail --retry 3 --retry-delay 2 \
  --output "$source_file" "$source_url"

actual_source_sha256="$(sha256 "$source_file")"
if [ "$actual_source_sha256" != "$source_sha256" ]; then
  printf 'Source SHA-256 mismatch.\nExpected: %s\nActual:   %s\n' \
    "$source_sha256" "$actual_source_sha256" >&2
  exit 1
fi

ffmpeg -hide_banner -loglevel error -y \
  -i "$source_file" -t 20 \
  -vf 'scale=1280:-2,fps=30' -an \
  -c:v libx264 -preset medium -crf 23 \
  -pix_fmt yuv420p -movflags +faststart \
  "$prepared_file"

actual_target_sha256="$(sha256 "$prepared_file")"
if [ "$actual_target_sha256" != "$target_sha256" ]; then
  printf 'Prepared sample SHA-256 mismatch.\nExpected: %s\nActual:   %s\n' \
    "$target_sha256" "$actual_target_sha256" >&2
  printf 'Use FFmpeg 7.1.1 to reproduce the pinned research input exactly.\n' >&2
  exit 1
fi

mkdir -p "$(dirname "$target")"
mv "$prepared_file" "$target"
printf 'Downloaded and verified video sample: %s\n' "$target"
