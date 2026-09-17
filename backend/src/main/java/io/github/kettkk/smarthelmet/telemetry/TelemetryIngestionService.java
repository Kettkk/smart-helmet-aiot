package io.github.kettkk.smarthelmet.telemetry;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class TelemetryIngestionService {
    private final TelemetryRepository repository;

    public TelemetryIngestionService(TelemetryRepository repository) {
        this.repository = repository;
    }

    @Transactional
    public TelemetryRecord ingest(TelemetryMessage message) {
        return repository.save(new TelemetryRecord(message));
    }
}
