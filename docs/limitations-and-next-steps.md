# Limitations and next steps

The original prototype depended on physical devices and managed cloud services.
The public reconstruction now provides a credential-free live telemetry loop,
an offline fixed-video benchmark, raw synthetic measurements, and reproducible
plots. Archived firmware and photographs document the physical research origin
but are not required to run either public path.

The two paths have different timing semantics. Telemetry is ingested live,
while vision inference is a controlled offline experiment. Spring Boot now
validates and persists the resulting benchmark summary and the dashboard reads
it through REST. Live frames and per-frame detections are intentionally not
streamed; adding them would require authentication, bounded retention, and
observable failure handling outside the current research question.

The fixed hiking clip is unlabelled. Detection continuity can be reported, but
precision, recall, mAP, and calibrated uncertainty cannot. Those accuracy
questions are explicitly outside the scope of this portfolio study.

The local MQTT benchmark now covers seeded application-layer delay and loss as
well as actual broker stop/start recovery. It does not yet model packet-level
wireless effects such as TCP retransmission, burst loss, congestion, or
reordering. A future hardware study should repeat the conditions with Linux
`tc netem`, an ESP-class edge client, and longer runs. Energy optimisation is
outside the stated research question.

The STM32 acquisition firmware was not developed as part of this portfolio and
is not included. The Android client is historical evidence rather than part of
the tested Compose stack. The system remains a research prototype, not a
certified medical or personal-safety product.
