package io.github.kettkk.smarthelmet.vision;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.HashSet;

@RestController
@RequestMapping("/api/v1/vision/benchmarks")
public class VisionBenchmarkController {
    private final VisionBenchmarkRepository repository;

    public VisionBenchmarkController(VisionBenchmarkRepository repository) {
        this.repository = repository;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Transactional
    public VisionBenchmarkPayload ingest(@Valid @RequestBody VisionBenchmarkPayload payload) {
        var strides = payload.runs().stream().map(VisionBenchmarkPayload.Run::frameStride).toList();
        if (new HashSet<>(strides).size() != strides.size()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Frame strides must be unique");
        }
        if (!strides.contains(payload.operatingPointStride())) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST, "Operating-point stride must identify a published run");
        }
        var existing = repository.findByMeasurementTimestamp(payload.measurementTimestamp());
        if (existing.isPresent()) {
            return existing.orElseThrow().toPayload();
        }
        return repository.save(new VisionBenchmark(payload)).toPayload();
    }

    @GetMapping("/latest")
    @Transactional(readOnly = true)
    public VisionBenchmarkPayload latest() {
        return repository.findFirstByOrderByMeasurementTimestampDesc()
                .map(VisionBenchmark::toPayload)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND, "No vision benchmark has been published"));
    }
}
