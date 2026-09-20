#include "esp_camera.h"
#include <WiFi.h>

#include "config.h"

// ===================
// 选择摄像头型号
// ===================
#define CAMERA_MODEL_AI_THINKER  // 适用于 ESP32-CAM

#include "camera_pins.h"

void startCameraServer();
void flashBlink(int pin, int times, int delayTime);

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println("\nESP32-CAM 初始化...");

  // **配置闪光灯引脚**
  pinMode(4, OUTPUT);
  digitalWrite(4, LOW);  // 关闭闪光灯

  // 配置摄像头参数
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 8000000;
  config.pixel_format = PIXFORMAT_JPEG;  // 适用于流媒体
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 15;
  config.fb_count = 1;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;

  // 如果 PSRAM 可用，优化摄像头性能
  if (psramFound()) {
    config.jpeg_quality = 10;  // 提高 JPEG 质量
    config.fb_count = 2;       // 增加缓冲区数量
    config.grab_mode = CAMERA_GRAB_LATEST;
  } else {
    config.frame_size = FRAMESIZE_SVGA;  // 降低分辨率，防止内存不足
    config.fb_location = CAMERA_FB_IN_DRAM;
  }

  // 初始化摄像头
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("摄像头初始化失败，错误代码 0x%x\n", err);
    return;
  }

  // 获取摄像头传感器配置
  sensor_t *s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);        // 垂直翻转
    s->set_brightness(s, 1);   // 增加亮度
    s->set_saturation(s, -2);  // 降低饱和度
  }

  // 降低初始分辨率，提高帧率
  s->set_framesize(s, FRAMESIZE_QVGA);

  // 连接 WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  WiFi.setSleep(false);  // 关闭 WiFi 省电模式，提高稳定性

  Serial.print("正在连接 WiFi");
  int retry = 0;
  while (WiFi.status() != WL_CONNECTED && retry < 20) {  // 限制重试次数
    delay(500);
    Serial.print(".");
    retry++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi 连接成功！");
    Serial.print("IP 地址: ");
    Serial.println(WiFi.localIP());

    // **WiFi 连接成功，闪光灯闪烁 2 次**
    flashBlink(4, 2, 200);

    startCameraServer();
  } else {
    Serial.println("\nWiFi 连接失败，请检查网络设置！");
  }

  Serial.println("ESP32-CAM 服务器已启动...");
}

void loop() {
  camera_fb_t *fb = esp_camera_fb_get();  // 获取摄像头帧数据
  if (!fb) {
    Serial.println("⚠️ 摄像头拍照失败！");
    return;
  }

  // 在这里可以进行额外的图像处理（如推流、存储等）

  esp_camera_fb_return(fb);  // 释放帧缓冲，防止内存溢出
  delay(5000);  // 限制帧率，降低 CPU 负担
}

// **新增函数：控制闪光灯**
void flashBlink(int pin, int times, int delayTime) {
  for (int i = 0; i < times; i++) {
    digitalWrite(pin, HIGH);  // 打开闪光灯
    delay(delayTime);
    digitalWrite(pin, LOW);   // 关闭闪光灯
    delay(delayTime);
  }
}
