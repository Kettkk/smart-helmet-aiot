package io.github.kettkk.smarthelmet.vision;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "vision_runs")
public class VisionRun {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "benchmark_id", nullable = false)
    private VisionBenchmark benchmark;

    @Column(name = "frame_stride", nullable = false)
    private Integer frameStride;

    @Column(name = "sampling_fps", nullable = false)
    private Double samplingFps;

    @Column(name = "processed_frames", nullable = false)
    private Integer processedFrames;

    @Column(name = "mean_latency_ms", nullable = false)
    private Double meanLatencyMs;

    @Column(name = "p95_latency_ms", nullable = false)
    private Double p95LatencyMs;

    @Column(name = "pipeline_fps", nullable = false)
    private Double pipelineFps;

    @Column(name = "detection_rate", nullable = false)
    private Double detectionRate;

    protected VisionRun() {
    }

    VisionRun(VisionBenchmark benchmark, VisionBenchmarkPayload.Run run) {
        this.benchmark = benchmark;
        this.frameStride = run.frameStride();
        this.samplingFps = run.samplingFps();
        this.processedFrames = run.processedFrames();
        this.meanLatencyMs = run.meanLatencyMs();
        this.p95LatencyMs = run.p95LatencyMs();
        this.pipelineFps = run.pipelineFps();
        this.detectionRate = run.continuityRate();
    }

    VisionBenchmarkPayload.Run toPayload() {
        return new VisionBenchmarkPayload.Run(
                frameStride,
                samplingFps,
                processedFrames,
                meanLatencyMs,
                p95LatencyMs,
                pipelineFps,
                detectionRate
        );
    }
}
