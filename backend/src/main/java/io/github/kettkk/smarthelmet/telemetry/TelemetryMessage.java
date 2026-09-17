package io.github.kettkk.smarthelmet.telemetry;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.Instant;

public record TelemetryMessage(
        @NotBlank String deviceId,
        @NotNull Instant timestamp,
        @NotNull Boolean wearing,
        @DecimalMin("25.0") @DecimalMax("45.0") Double bodyTemperatureC,
        @DecimalMin("-50.0") @DecimalMax("80.0") Double ambientTemperatureC,
        @DecimalMin("0.0") @DecimalMax("100.0") Double ambientHumidityPct,
        @Min(20) @Max(240) Integer heartRateBpm,
        @DecimalMin("-90.0") @DecimalMax("90.0") Double latitude,
        @DecimalMin("-180.0") @DecimalMax("180.0") Double longitude,
        @DecimalMin("0.0") Double impactPressurePa,
        @DecimalMin("0.0") Double speedMps
) {
}
