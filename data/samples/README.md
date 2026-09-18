# Local video sample

`outdoor-hiking-20s.mp4` is a 20-second outdoor walking clip prepared as a
local input for the vision-service pipeline and reproducible inference
benchmarks.

## Provenance

- Source: [Trip, Walk, Adventure, Mountain, Forest](https://pixabay.com/videos/trip-walk-adventure-mountain-forest-99388/)
- Creator: Engin Akyurt
- Source platform: Pixabay (video ID `99388`)
- License: [Pixabay Content License](https://pixabay.com/service/license-summary/)
- Selected interval: `00:00`–`00:20`
- Prepared on: 2026-09-18

## Prepared asset

| Property | Value |
| --- | --- |
| File | `outdoor-hiking-20s.mp4` |
| Video | H.264, 1280×720, 30 fps |
| Audio | Removed |
| Duration | 20.000 seconds |
| Size | 7,031,060 bytes |
| SHA-256 | `1fc1c55a6f541088fa155818c1a33f759f36570bce9eecbb080f2650bd9b3f39` |

The video file is intentionally ignored by Git. Keep it as a local research
input rather than redistributing the stock footage as a standalone repository
asset. This metadata file may be committed.

## Recreate the local sample

Download the source video from its Pixabay page, then run:

```bash
ffmpeg -i SOURCE.mp4 -t 20 \
  -vf 'scale=1280:-2,fps=30' -an \
  -c:v libx264 -preset medium -crf 23 \
  -pix_fmt yuv420p -movflags +faststart \
  data/samples/outdoor-hiking-20s.mp4
```

Verify the prepared asset with:

```bash
ffprobe -v error \
  -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate \
  -of json data/samples/outdoor-hiking-20s.mp4

shasum -a 256 data/samples/outdoor-hiking-20s.mp4
```
