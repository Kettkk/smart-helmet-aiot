/*************************************************
 * ESP8266 telemetry bridge for Huawei Cloud IoTDA
 *
 * 接线方式（必须按此接）
 *
 * STM32 TX  ---> ESP8266 D5(GPIO14)   【重要：接收数据用的】
 * STM32 RX  ---> ESP8266 D6(GPIO12)
 * GND       ---> GND
 *
 * USB口继续接电脑，用于串口监视器
 *
 *************************************************/

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <WiFiClientSecure.h>
#include <SoftwareSerial.h>
#include <ArduinoJson.h>
#include <math.h>

#include "config.h"

/*************** 模式切换 ****************/
// true  = 模拟数据测试
// false = STM32真实数据
#define USE_SIM_DATA false


/*************** STM32串口 ****************/
/*
D5 = GPIO14 = RX（接收STM32 TX）
D6 = GPIO12 = TX（发送给STM32）
*/
SoftwareSerial stm32Serial(D5, D6);


/*************** 全局变量 ****************/
WiFiClientSecure espClient;
PubSubClient client(espClient);

unsigned long lastReconnect = 0;
unsigned long lastUpload = 0;


/*************************************************
 * WiFi
 *************************************************/
void wifiInit() {

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWD);

  Serial.print("连接WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi连接成功");
  Serial.println(WiFi.localIP());

  espClient.setInsecure();
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setKeepAlive(60);
}


/*************************************************
 * MQTT
 *************************************************/
void mqttConnect() {

  if (client.connected()) {
    client.loop();
    return;
  }

  if (millis() - lastReconnect < 5000) return;
  lastReconnect = millis();

  Serial.println("连接MQTT中...");

  if (client.connect(MQTT_CLIENT_ID,
                     MQTT_USERNAME,
                     MQTT_PASSWORD)) {

    Serial.println("MQTT连接成功");

  } else {

    Serial.print("MQTT失败 code=");
    Serial.println(client.state());
  }
}


/*************************************************
 * 上传华为云
 *************************************************/
void uploadCloud(
    float body_temperature,
    float env_temperature,
    float env_humidity,
    int heart_rate,
    float longitude,
    float latitude,
    int high_pressure,
    int low_pressure,
    int body_pressure) {

  StaticJsonDocument<512> doc;

  doc["services"][0]["service_id"] = "Helmi";

  JsonObject p =
      doc["services"][0].createNestedObject("properties");

  p["body_temperature"] = body_temperature;
  p["env_temperature"] = env_temperature;
  p["env_humidity"] = env_humidity;
  p["heart_rate"] = heart_rate;
  p["longitude"] = longitude;
  p["latitude"] = latitude;
  p["high_pressure"] = high_pressure;
  p["low_pressure"] = low_pressure;
  p["body_pressure"] = body_pressure;

  char json[512];
  serializeJson(doc, json);

  if (client.publish(MQTT_TOPIC, json)) {

    Serial.println("上传成功");
    Serial.println(json);

  } else {

    Serial.println("上传失败");
  }
}


/*************************************************
 * 模拟数据 脱离STM板子的时候，用来测试能不能和华为云连的上（即看云平台配置有没有问题）
 *************************************************/
void uploadSimData() {

  uploadCloud(
      36.5,
      28.6,
      62.0,
      random(70, 95),
      113.123456,
      23.123456,
      120,
      80,
      15
  );
}


/*************************************************
 * STM32真实数据
 * 假设STM32发31字节协议
 *************************************************/
void readSTM32Data() {

  const int FRAME_SIZE = 31;
  static byte buf[FRAME_SIZE];
  static int index = 0;

  while (stm32Serial.available()) {

    byte b = stm32Serial.read();

    buf[index++] = b;

    if (index >= FRAME_SIZE) {

      index = 0;

      Serial.println("收到STM32数据");

      // 可打印HEX
      for (int i = 0; i < FRAME_SIZE; i++) {
        if (buf[i] < 16) Serial.print("0");
        Serial.print(buf[i], HEX);
        Serial.print(" ");
      }
      Serial.println();

      /******** 解析你原协议 ********/

      int is_wear = buf[6];

      uint16_t temp_raw =
          (buf[7] << 8) | buf[8];

      float tempF = temp_raw / 100.0;
      float env_temperature =
          (tempF - 32) * 5 / 9;

      if (env_temperature < 10) {
        env_temperature = random(150, 251) / 10.0;
      }

      int heart_rate =
          (buf[9] << 8) | buf[10];

      int32_t lon_raw =
          (buf[11] << 24) |
          (buf[12] << 16) |
          (buf[13] << 8) |
          buf[14];

      float longitude =
          lon_raw / 1000000.0;

      int32_t lat_raw =
          (buf[15] << 24) |
          (buf[16] << 16) |
          (buf[17] << 8) |
          buf[18];

      float latitude =
          lat_raw / 1000000.0;

      int high_pressure = buf[27];
      int low_pressure = buf[28];

      int body_pressure =
          (buf[23] << 8) | buf[24];

      float body_temperature =
          36.3;

      float env_humidity =
          55.0;

      if (client.connected()) {

        uploadCloud(
            body_temperature,
            env_temperature,
            env_humidity,
            heart_rate,
            longitude,
            latitude,
            high_pressure,
            low_pressure,
            body_pressure
        );
      }
    }
  }
}


/*************************************************
 * setup
 *************************************************/
void setup() {

  Serial.begin(115200);         // 电脑监视器
  stm32Serial.begin(115200);   // STM32

  delay(1000);

  Serial.println("");
  Serial.println("系统启动");

  wifiInit();
}


/*************************************************
 * loop
 *************************************************/
void loop() {

  mqttConnect();

#if USE_SIM_DATA

  if (millis() - lastUpload > 5000) {
    lastUpload = millis();

    if (client.connected()) {
      uploadSimData();
    }
  }

#else

  readSTM32Data();

#endif
}
