package io.github.kettkk.smarthelmet.vision;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OrderBy;
import jakarta.persistence.Table;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

@Entity
@Table(name = "vision_benchmarks")
public class VisionBenchmark {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "schema_version", nullable = false)
    private Integer schemaVersion;

    @Column(name = "measurement_timestamp", nullable = false)
    private Instant measurementTimestamp;

    @Column(name = "ingested_at", nullable = false)
    private Instant ingestedAt;

    @Column(name = "input_file", nullable = false, length = 255)
    private String inputFile;

    @Column(name = "duration_seconds", nullable = false)
    private Double durationSeconds;

    @Column(name = "source_fps", nullable = false)
    private Double sourceFps;

    @Column(nullable = false, length = 32)
    private String resolution;

    @Column(name = "model_name", nullable = false, length = 128)
    private String modelName;

    @Column(name = "execution_device", nullable = false, length = 64)
    private String executionDevice;

    @Column(name = "image_size", nullable = false)
    private Integer imageSize;

    @Column(name = "confidence_threshold", nullable = false)
    private Double confidenceThreshold;

    @Column(name = "target_classes", nullable = false, length = 512)
    private String targetClasses;

    @Column(name = "operating_point_stride", nullable = false)
    private Integer operatingPointStride;

    @OneToMany(mappedBy = "benchmark", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.EAGER)
    @OrderBy("frameStride ASC")
    private List<VisionRun> runs = new ArrayList<>();

    protected VisionBenchmark() {
    }

    public VisionBenchmark(VisionBenchmarkPayload payload) {
        this.schemaVersion = payload.schemaVersion();
        this.measurementTimestamp = payload.measurementTimestamp();
        this.ingestedAt = Instant.now();
        this.inputFile = payload.input().file();
        this.durationSeconds = payload.input().durationSeconds();
        this.sourceFps = payload.input().sourceFps();
        this.resolution = payload.input().resolution();
        this.modelName = payload.configuration().model();
        this.executionDevice = payload.configuration().device();
        this.imageSize = payload.configuration().imageSize();
        this.confidenceThreshold = payload.configuration().confidence();
        this.targetClasses = String.join(",", payload.configuration().targetClasses());
        this.operatingPointStride = payload.operatingPointStride();
        payload.runs().forEach(run -> this.runs.add(new VisionRun(this, run)));
    }

    public VisionBenchmarkPayload toPayload() {
        return new VisionBenchmarkPayload(
                schemaVersion,
                measurementTimestamp,
                new VisionBenchmarkPayload.Input(inputFile, durationSeconds, sourceFps, resolution),
                new VisionBenchmarkPayload.Configuration(
                        modelName,
                        executionDevice,
                        imageSize,
                        confidenceThreshold,
                        Arrays.stream(targetClasses.split(",")).filter(value -> !value.isBlank()).toList()
                ),
                operatingPointStride,
                runs.stream().map(VisionRun::toPayload).toList()
        );
    }
}
