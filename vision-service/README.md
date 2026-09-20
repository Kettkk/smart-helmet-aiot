# Vision service

This module runs repeatable YOLO inference on a fixed video input. It is a
batch experiment boundary rather than a claim that inference runs on the
ESP32-CAM. The default configuration samples one of every five source frames
and detects the COCO `person` class on CPU.

## Run the portfolio sample

Run from the repository root:

```bash
./scripts/run-vision-demo.sh
```

The runner automatically downloads the public-domain reference video and
verifies both the source and prepared-sample SHA-256 digests before inference.
See `data/samples/README.md` for provenance and the pinned transformation.

The first run downloads the versioned `yolo11n.pt` weights into a persistent
Docker volume. Outputs are written to `experiments/results/vision-demo/`:

- `annotated.mp4`: H.264 video with bounding boxes
- `detections.jsonl`: structured detections for each sampled frame
- `frame-metrics.csv`: per-inference latency and detection counts
- `summary.json`: configuration, mean/p50/p95 latency, FPS, and continuity rate

Change the sampling interval without changing code:

```bash
VISION_FRAME_STRIDE=10 ./scripts/run-vision-demo.sh
```

Run the controlled stride comparison and regenerate all figures:

```bash
./scripts/run-vision-benchmark.sh
./scripts/plot-vision-results.sh
```

This evaluates strides 1, 2, 5, and 10 with every other setting held constant.
Raw runs are stored under `experiments/results/frame-sampling/`, while PNG and
SVG figures are stored under `experiments/plots/vision/`.

When the backend is running, `run-vision-benchmark.sh` also converts the result
to the documented API schema and publishes it to
`POST /api/v1/vision/benchmarks`. Republish existing results with
`./scripts/publish-vision-results.sh`. The Vue dashboard then retrieves the
latest persisted record from `GET /api/v1/vision/benchmarks/latest`.

Results describe this machine and configuration only. They are not accuracy
metrics: the fixed clip has no ground-truth annotations, so continuity rate is
reported instead of precision, recall, or mAP.
