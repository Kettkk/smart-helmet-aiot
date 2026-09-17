package io.github.kettkk.smarthelmet.telemetry;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "telemetry_records")
public class TelemetryRecord {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "device_id", nullable = false, length = 64)
    private String deviceId;

    @Column(name = "recorded_at", nullable = false)
    private Instant recordedAt;

    @Column(nullable = false)
    private Boolean wearing;

    @Column(name = "body_temperature_c")
    private Double bodyTemperatureC;

    @Column(name = "ambient_temperature_c")
    private Double ambientTemperatureC;

    @Column(name = "ambient_humidity_pct")
    private Double ambientHumidityPct;

    @Column(name = "heart_rate_bpm")
    private Integer heartRateBpm;

    private Double latitude;
    private Double longitude;

    @Column(name = "impact_pressure_pa")
    private Double impactPressurePa;

    @Column(name = "speed_mps")
    private Double speedMps;

    protected TelemetryRecord() {
    }

    public TelemetryRecord(TelemetryMessage message) {
        this.deviceId = message.deviceId();
        this.recordedAt = message.timestamp();
        this.wearing = message.wearing();
        this.bodyTemperatureC = message.bodyTemperatureC();
        this.ambientTemperatureC = message.ambientTemperatureC();
        this.ambientHumidityPct = message.ambientHumidityPct();
        this.heartRateBpm = message.heartRateBpm();
        this.latitude = message.latitude();
        this.longitude = message.longitude();
        this.impactPressurePa = message.impactPressurePa();
        this.speedMps = message.speedMps();
    }

    @JsonIgnore
    public Long getId() { return id; }
    public String getDeviceId() { return deviceId; }
    @JsonProperty("timestamp")
    public Instant getRecordedAt() { return recordedAt; }
    public Boolean getWearing() { return wearing; }
    public Double getBodyTemperatureC() { return bodyTemperatureC; }
    public Double getAmbientTemperatureC() { return ambientTemperatureC; }
    public Double getAmbientHumidityPct() { return ambientHumidityPct; }
    public Integer getHeartRateBpm() { return heartRateBpm; }
    public Double getLatitude() { return latitude; }
    public Double getLongitude() { return longitude; }
    public Double getImpactPressurePa() { return impactPressurePa; }
    public Double getSpeedMps() { return speedMps; }
}
