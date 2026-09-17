CREATE TABLE telemetry_records (
    id BIGINT NOT NULL AUTO_INCREMENT,
    device_id VARCHAR(64) NOT NULL,
    recorded_at TIMESTAMP(6) NOT NULL,
    wearing BOOLEAN NOT NULL,
    body_temperature_c DOUBLE NULL,
    ambient_temperature_c DOUBLE NULL,
    ambient_humidity_pct DOUBLE NULL,
    heart_rate_bpm INTEGER NULL,
    latitude DOUBLE NULL,
    longitude DOUBLE NULL,
    impact_pressure_pa DOUBLE NULL,
    speed_mps DOUBLE NULL,
    PRIMARY KEY (id),
    INDEX idx_telemetry_device_time (device_id, recorded_at)
);
