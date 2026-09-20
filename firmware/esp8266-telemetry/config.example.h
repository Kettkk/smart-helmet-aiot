#pragma once

// Copy this file to config.h and replace every placeholder locally.
#define WIFI_SSID "your-wifi-ssid"
#define WIFI_PASSWD "your-wifi-password"

#define MQTT_SERVER "your-iotda-endpoint.example.com"
#define MQTT_PORT 8883
#define MQTT_USERNAME "your-device-id"
#define MQTT_PASSWORD "your-device-secret"
#define MQTT_CLIENT_ID "your-device-id_0_0_YYYYMMDDHH"
#define MQTT_TOPIC "$oc/devices/" MQTT_USERNAME "/sys/properties/report"
