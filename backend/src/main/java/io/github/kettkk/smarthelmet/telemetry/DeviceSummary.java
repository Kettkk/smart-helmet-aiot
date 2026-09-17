package io.github.kettkk.smarthelmet.telemetry;

import java.time.Instant;

public record DeviceSummary(String deviceId, Instant lastSeen) {
}
