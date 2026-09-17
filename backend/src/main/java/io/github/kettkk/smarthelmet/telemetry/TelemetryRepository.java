package io.github.kettkk.smarthelmet.telemetry;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.Optional;

public interface TelemetryRepository extends JpaRepository<TelemetryRecord, Long> {
    Optional<TelemetryRecord> findFirstByDeviceIdOrderByRecordedAtDesc(String deviceId);

    List<TelemetryRecord> findByDeviceIdOrderByRecordedAtDesc(String deviceId, Pageable pageable);

    @Query("select distinct t.deviceId from TelemetryRecord t order by t.deviceId")
    List<String> findDistinctDeviceIds();
}
