# Limitations and next steps

The original prototype depended on physical devices and managed cloud services.
Those dependencies made external reproduction difficult and must not be used as
evidence until the public pipeline is recreated.

The first public milestone is a local, credential-free simulation pipeline.
The second is a benchmark with scripts, raw anonymised results, and plots.

The local MQTT benchmark now covers seeded application-layer delay and loss as
well as actual broker stop/start recovery. It does not yet model packet-level
wireless effects such as TCP retransmission, burst loss, congestion, or
reordering. A future hardware study should repeat the conditions with Linux
`tc netem`, an ESP-class edge client, longer runs, and energy measurements.
