# Vision service

This module runs repeatable YOLO inference on a fixed video input. It is a
batch experiment boundary rather than a claim that inference runs on the
ESP32-CAM. The default configuration samples one of every five source frames
and detects the COCO `person` class on CPU.

## Run the portfolio sample

Place the local sample at `data/samples/outdoor-hiking-20s.mp4`, then run from
the repository root:

```bash
./scripts/run-vision-demo.sh
```

The first run downloads the versioned `yolo11n.pt` weights into a persistent
Docker volume. Outputs are written to `experiments/results/vision-demo/`:

- `annotated.mp4`: H.264 video with bounding boxes
- `detections.jsonl`: structured detections for each sampled frame
- `frame-metrics.csv`: per-inference latency and detection counts
- `summary.json`: configuration, mean/p50/p95 latency, FPS, and detection rate

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

Results describe this machine and configuration only. They are not accuracy
metrics: the stock clip has no ground-truth annotations, so detection rate is
reported instead of precision, recall, or mAP.
