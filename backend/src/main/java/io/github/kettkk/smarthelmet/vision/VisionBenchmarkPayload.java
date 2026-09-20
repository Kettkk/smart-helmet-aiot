package io.github.kettkk.smarthelmet.vision;

import jakarta.validation.Valid;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.PositiveOrZero;

import java.time.Instant;
import java.util.List;

public record VisionBenchmarkPayload(
        @NotNull @Min(1) Integer schemaVersion,
        @NotNull Instant measurementTimestamp,
        @NotNull @Valid Input input,
        @NotNull @Valid Configuration configuration,
        @NotNull @Min(1) Integer operatingPointStride,
        @NotEmpty List<@Valid Run> runs
) {
    public record Input(
            @NotBlank String file,
            @Positive double durationSeconds,
            @Positive double sourceFps,
            @NotBlank String resolution
    ) {
    }

    public record Configuration(
            @NotBlank String model,
            @NotBlank String device,
            @Positive int imageSize,
            @DecimalMin("0.0") @DecimalMax("1.0") double confidence,
            @NotEmpty List<@NotBlank String> targetClasses
    ) {
    }

    public record Run(
            @Min(1) int frameStride,
            @Positive double samplingFps,
            @Positive int processedFrames,
            @Positive double meanLatencyMs,
            @Positive double p95LatencyMs,
            @Positive double pipelineFps,
            @PositiveOrZero @DecimalMax("1.0") double continuityRate
    ) {
    }
}
