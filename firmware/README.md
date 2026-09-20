# Hardware firmware archive

This directory preserves the two microcontroller integrations used by the
physical smart-helmet prototype. They are included as implementation evidence;
reviewers do not need the original helmet to run the reproducible Docker path.
CI verifies the archive structure and configuration separation, but does not
claim a hardware flash test or compile against a pinned Arduino board package.

## Ownership boundary

| Module | Role | Attribution |
| --- | --- | --- |
| `esp8266-telemetry` | Receives a 31-byte UART frame from an STM32 board, parses selected measurements, and reports a Huawei Cloud IoTDA property payload over MQTT/TLS | ESP8266 bridge and cloud integration are part of this portfolio work |
| `esp32-camera` | Configures an AI-Thinker ESP32-CAM and exposes capture, control, and MJPEG stream endpoints | Prototype configuration and system integration are part of this portfolio work; the HTTP camera-server base derives from Espressif's Arduino CameraWebServer example |
| STM32 sensor firmware | Acquires and packs the upstream sensor frame | Team/external component; not authored here and intentionally not included |

The current prototype did not use the NB-IoT board shown in older development
material. No NB-IoT code, device identifier, or procurement record is included.

## ESP8266 telemetry bridge

Wiring used by the archived sketch:

```text
STM32 TX  -> ESP8266 D5 / GPIO14 (software-serial RX)
STM32 RX  -> ESP8266 D6 / GPIO12 (software-serial TX)
GND       -> GND
UART      -> 115200 baud
```

The bridge waits for 31-byte frames and maps the following offsets:

| Frame bytes | Field |
| --- | --- |
| `6` | Helmet-wear flag (parsed in the archived revision but not uploaded) |
| `7..8` | Environmental temperature source value |
| `9..10` | Heart rate |
| `11..14` | Longitude, signed integer scaled by `1e6` |
| `15..18` | Latitude, signed integer scaled by `1e6` |
| `23..24` | Impact/body-pressure value |
| `27` | Systolic pressure |
| `28` | Diastolic pressure |

Body temperature and humidity are fixed placeholders in this archived sketch;
they must not be interpreted as validated sensor measurements. See
[`docs/hardware-prototype.md`](../docs/hardware-prototype.md) for the complete
prototype scope and limitations.

To configure locally:

```bash
cd firmware/esp8266-telemetry
cp config.example.h config.h
```

Install the ESP8266 Arduino core plus `PubSubClient`, `ArduinoJson`, and
`SoftwareSerial`, then select the appropriate ESP8266 board and flash
`esp8266_telemetry.ino`. The archived sketch calls `setInsecure()` for its TLS
connection, matching the prototype. A production version must validate the
server certificate.

## ESP32-CAM node

To configure locally:

```bash
cd firmware/esp32-camera
cp config.example.h config.h
```

Install the Espressif Arduino-ESP32 core, select **AI Thinker ESP32-CAM**, and
flash `CameraWebServer.ino`. Once connected, the control page is served on port
80 and the MJPEG stream on port 81.

The checked-in `app_httpd.cpp`, `camera_index.h`, and `camera_pins.h` originate
from the Espressif Arduino CameraWebServer example and are retained so the
historical prototype configuration can be inspected. Upstream reference:
<https://github.com/espressif/arduino-esp32/tree/master/libraries/ESP32/examples/Camera/CameraWebServer>.

## Relationship to the reproducible system

The local simulator and fixed video deliberately implement the same two input
boundaries without requiring hardware:

```text
Physical prototype                  Reproducible evaluation path
STM32 -> ESP8266 -> MQTT       <=>  telemetry simulator -> MQTT
ESP32-CAM -> JPEG/MJPEG stream <=>  fixed 20-second video
```

This separation allows the repository to show the wearable prototype while
keeping the latency and reliability experiments repeatable for reviewers.
