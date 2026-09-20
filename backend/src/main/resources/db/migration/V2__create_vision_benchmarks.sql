CREATE TABLE vision_benchmarks (
    id BIGINT NOT NULL AUTO_INCREMENT,
    schema_version INTEGER NOT NULL,
    measurement_timestamp TIMESTAMP(6) NOT NULL,
    ingested_at TIMESTAMP(6) NOT NULL,
    input_file VARCHAR(255) NOT NULL,
    duration_seconds DOUBLE NOT NULL,
    source_fps DOUBLE NOT NULL,
    resolution VARCHAR(32) NOT NULL,
    model_name VARCHAR(128) NOT NULL,
    execution_device VARCHAR(64) NOT NULL,
    image_size INTEGER NOT NULL,
    confidence_threshold DOUBLE NOT NULL,
    target_classes VARCHAR(512) NOT NULL,
    operating_point_stride INTEGER NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_vision_benchmark_measurement (measurement_timestamp)
);

CREATE TABLE vision_runs (
    id BIGINT NOT NULL AUTO_INCREMENT,
    benchmark_id BIGINT NOT NULL,
    frame_stride INTEGER NOT NULL,
    sampling_fps DOUBLE NOT NULL,
    processed_frames INTEGER NOT NULL,
    mean_latency_ms DOUBLE NOT NULL,
    p95_latency_ms DOUBLE NOT NULL,
    pipeline_fps DOUBLE NOT NULL,
    detection_rate DOUBLE NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_vision_run_benchmark
        FOREIGN KEY (benchmark_id) REFERENCES vision_benchmarks (id)
        ON DELETE CASCADE,
    UNIQUE KEY uk_vision_run_stride (benchmark_id, frame_stride)
);
