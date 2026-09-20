package io.github.kettkk.smarthelmet.vision;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.time.Instant;

public interface VisionBenchmarkRepository extends JpaRepository<VisionBenchmark, Long> {
    Optional<VisionBenchmark> findFirstByOrderByMeasurementTimestampDesc();
    Optional<VisionBenchmark> findByMeasurementTimestamp(Instant measurementTimestamp);
}
