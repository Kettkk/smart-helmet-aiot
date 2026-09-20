package io.github.kettkk.smarthelmet.vision;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@AutoConfigureMockMvc
class VisionBenchmarkControllerIntegrationTest {
    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private VisionBenchmarkRepository repository;

    @BeforeEach
    void setUp() {
        repository.deleteAll();
    }

    @Test
    void persistsAndReturnsLatestBenchmark() throws Exception {
        mockMvc.perform(post("/api/v1/vision/benchmarks")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(validPayload()))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.operatingPointStride").value(5))
                .andExpect(jsonPath("$.runs[0].meanLatencyMs").value(108.4));

        mockMvc.perform(get("/api/v1/vision/benchmarks/latest"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.input.file").value("outdoor-hiking-20s.mp4"))
                .andExpect(jsonPath("$.configuration.model").value("yolo11n.pt"))
                .andExpect(jsonPath("$.runs[0].continuityRate").value(0.9917));

        mockMvc.perform(post("/api/v1/vision/benchmarks")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(validPayload()))
                .andExpect(status().isCreated());
        assertThat(repository.count()).isEqualTo(1);
    }

    @Test
    void rejectsInvalidContinuityRate() throws Exception {
        mockMvc.perform(post("/api/v1/vision/benchmarks")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(validPayload().replace("0.9917", "1.2")))
                .andExpect(status().isBadRequest());
    }

    @Test
    void rejectsUnknownOperatingPoint() throws Exception {
        mockMvc.perform(post("/api/v1/vision/benchmarks")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(validPayload().replace(
                                "\"operatingPointStride\": 5",
                                "\"operatingPointStride\": 10")))
                .andExpect(status().isBadRequest());
    }

    @Test
    void returnsNotFoundBeforeResultsArePublished() throws Exception {
        mockMvc.perform(get("/api/v1/vision/benchmarks/latest"))
                .andExpect(status().isNotFound());
    }

    private String validPayload() {
        return """
                {
                  "schemaVersion": 1,
                  "measurementTimestamp": "2026-09-20T06:32:34Z",
                  "input": {
                    "file": "outdoor-hiking-20s.mp4",
                    "durationSeconds": 20.0,
                    "sourceFps": 30.0,
                    "resolution": "1280x720"
                  },
                  "configuration": {
                    "model": "yolo11n.pt",
                    "device": "CPU",
                    "imageSize": 640,
                    "confidence": 0.25,
                    "targetClasses": ["person"]
                  },
                  "operatingPointStride": 5,
                  "runs": [{
                    "frameStride": 5,
                    "samplingFps": 6.0,
                    "processedFrames": 120,
                    "meanLatencyMs": 108.4,
                    "p95LatencyMs": 114.8,
                    "pipelineFps": 34.5,
                    "continuityRate": 0.9917
                  }]
                }
                """;
    }
}
