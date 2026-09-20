# Upstream attribution

`app_httpd.cpp`, `camera_index.h`, and `camera_pins.h` are retained from the
Espressif Arduino-ESP32 CameraWebServer example used by the prototype. The
original copyright and Apache-2.0 notice in `app_httpd.cpp` is preserved.

Upstream project:
<https://github.com/espressif/arduino-esp32/tree/master/libraries/ESP32/examples/Camera/CameraWebServer>

The local `CameraWebServer.ino` records the prototype-specific AI-Thinker board,
camera, Wi-Fi, buffering, flash, and frame-rate configuration. Repository-local
credentials are supplied through the ignored `config.h` file.
