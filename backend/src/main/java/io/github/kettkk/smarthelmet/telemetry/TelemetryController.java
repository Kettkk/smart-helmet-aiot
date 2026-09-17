package io.github.kettkk.smarthelmet.telemetry;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@Validated
@RestController
@RequestMapping("/api/v1/devices")
public class TelemetryController {
    private final TelemetryRepository repository;

    public TelemetryController(TelemetryRepository repository) {
        this.repository = repository;
    }

    @GetMapping
    public List<DeviceSummary> devices() {
        return repository.findDistinctDeviceIds().stream()
                .map(deviceId -> repository.findFirstByDeviceIdOrderByRecordedAtDesc(deviceId)
                        .map(record -> new DeviceSummary(deviceId, record.getRecordedAt()))
                        .orElseThrow())
                .toList();
    }

    @GetMapping("/{deviceId}/latest")
    public TelemetryRecord latest(@PathVariable String deviceId) {
        return repository.findFirstByDeviceIdOrderByRecordedAtDesc(deviceId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND, "No telemetry found for device " + deviceId));
    }

    @GetMapping("/{deviceId}/telemetry")
    public List<TelemetryRecord> history(
            @PathVariable String deviceId,
            @RequestParam(defaultValue = "100") @Min(1) @Max(500) int limit) {
        return repository.findByDeviceIdOrderByRecordedAtDesc(deviceId, PageRequest.of(0, limit));
    }
}
