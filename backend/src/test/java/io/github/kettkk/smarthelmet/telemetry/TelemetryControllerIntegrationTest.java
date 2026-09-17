package io.github.kettkk.smarthelmet.telemetry;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.kettkk.smarthelmet.mqtt.MqttTelemetrySubscriber;
import jakarta.validation.Validator;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import java.time.Instant;
import java.nio.charset.StandardCharsets;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class TelemetryControllerIntegrationTest {
    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private TelemetryRepository repository;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private Validator validator;

    @Autowired
    private TelemetryIngestionService ingestionService;

    @BeforeEach
    void setUp() {
        repository.deleteAll();
        repository.save(new TelemetryRecord(new TelemetryMessage(
                "helmet-sim-001",
                Instant.parse("2026-01-01T00:00:00Z"),
                true,
                36.6,
                22.4,
                55.0,
                78,
                30.2741,
                120.1551,
                1013.0,
                1.2
        )));
    }

    @Test
    void listsDevicesAndReturnsLatestTelemetry() throws Exception {
        mockMvc.perform(get("/api/v1/devices"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].deviceId").value("helmet-sim-001"));

        mockMvc.perform(get("/api/v1/devices/helmet-sim-001/latest"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.timestamp").value("2026-01-01T00:00:00Z"))
                .andExpect(jsonPath("$.id").doesNotExist())
                .andExpect(jsonPath("$.heartRateBpm").value(78));
    }

    @Test
    void returnsNotFoundForUnknownDevice() throws Exception {
        mockMvc.perform(get("/api/v1/devices/unknown/latest"))
                .andExpect(status().isNotFound());
    }

    @Test
    void mqttPayloadIsValidatedAndPersisted() throws Exception {
        String payload = """
                {
                  "deviceId": "helmet-mqtt-002",
                  "timestamp": "2026-01-01T00:00:01Z",
                  "wearing": true,
                  "bodyTemperatureC": 36.7,
                  "ambientTemperatureC": 21.5,
                  "ambientHumidityPct": 57.0,
                  "heartRateBpm": 81,
                  "latitude": 30.2742,
                  "longitude": 120.1552,
                  "impactPressurePa": 1012.5,
                  "speedMps": 1.3
                }
                """;
        MqttTelemetrySubscriber subscriber = new MqttTelemetrySubscriber(
                objectMapper,
                validator,
                ingestionService,
                "tcp://unused:1883",
                "smart-helmet/telemetry",
                "test-client"
        );

        subscriber.messageArrived(
                "smart-helmet/telemetry",
                new MqttMessage(payload.getBytes(StandardCharsets.UTF_8))
        );

        TelemetryRecord stored = repository
                .findFirstByDeviceIdOrderByRecordedAtDesc("helmet-mqtt-002")
                .orElseThrow();
        assertThat(stored.getHeartRateBpm()).isEqualTo(81);
    }
}
