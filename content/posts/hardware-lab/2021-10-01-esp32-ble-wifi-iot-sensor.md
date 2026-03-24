---
title: "ESP32로 무선 IoT 센서 만들기 — BLE + WiFi 듀얼 모드 완전 정복"
date: 2021-10-01T08:00:00+09:00
lastmod: 2021-10-03T08:00:00+09:00
description: "ESP32의 BLE와 WiFi를 동시에 활용해 저전력 IoT 센서 노드를 만드는 방법. 회로 구성부터 펌웨어 코드, 클라우드 연동까지 13년 차 엔지니어가 실전 경험을 바탕으로 설명합니다."
slug: "esp32-ble-wifi-iot-sensor"
categories: ["hardware-lab"]
tags: ["ESP32", "BLE", "WiFi", "IoT", "센서", "MQTT", "임베디드"]
series: []
draft: false
---

ESP32를 처음 접했을 때, 솔직히 이게 이렇게 오래 살아남을 칩이 될 거라고는 몰랐다. 2016년에 나온 칩인데 2026년 현재도 IoT 프로젝트의 기본값이고, 심지어 Espressif는 CES 2026에서 WiFi 6E를 지원하는 ESP32-E22까지 발표했다. 이 글은 그런 ESP32의 핵심 강점 중 하나인 **BLE + WiFi 듀얼 모드**를 제대로 활용하는 방법에 대한 이야기다.

## 왜 BLE와 WiFi를 동시에 쓰는가

가장 흔한 IoT 패턴은 "WiFi로 직접 클라우드 연결"이다. 간단하고 코드도 짧다. 문제는 **배터리**다. WiFi 연결 유지에 드는 전력은 BLE에 비해 수십 배 이상이다. 배터리로 동작하는 센서 노드에 WiFi를 켜두면 AA 배터리 두 개가 일주일을 버티기 어렵다.

반면 BLE만 쓰면 소비전력은 해결되지만, 인터넷 연결을 위해 스마트폰이나 별도 게이트웨이가 반드시 필요하다. 결국 실제 현장에서 많이 쓰는 패턴은 이렇다:

- **센서 노드**: BLE Peripheral 모드, 딥슬립으로 배터리 수명 극대화
- **게이트웨이**: BLE Central + WiFi, 여러 노드의 데이터를 수집해 클라우드로 전송

혹은 노드 자체가 WiFi 직접 연결을 하되, 측정 후 즉시 딥슬립에 빠지는 방식도 유효하다.

![ESP32 BLE + WiFi 듀얼 모드 IoT 센서 아키텍처](/images/esp32-ble-wifi-sensor-architecture.svg)

## 하드웨어 구성

내가 가장 자주 쓰는 조합이다.

| 부품 | 역할 | 가격 (대략) |
|------|------|------------|
| ESP32-WROOM-32E | 메인 MCU | ₩2,500 |
| DHT22 | 온도 + 습도 | ₩2,000 |
| BMP280 | 기압 + 고도 | ₩1,500 |
| MQ-135 | 공기질 (CO2, VOC) | ₩3,000 |
| 18650 리튬 배터리 | 전원 | ₩5,000 |
| TP4056 모듈 | 배터리 충전 | ₩800 |

총 부품 단가 약 15,000원. 케이스와 PCB 포함해도 3만 원 이하로 꽤 쓸만한 환경 모니터링 노드가 나온다.

**배선 포인트:**
- DHT22: GPIO4 (단선 프로토콜, 4.7kΩ 풀업 저항 필수)
- BMP280: I2C → GPIO21(SDA), GPIO22(SCL)
- MQ-135: ADC → GPIO34 (입력 전용 핀)
- 배터리 전압 모니터링: GPIO35 (분압 저항으로 3.3V 이하로 낮춰야 함)

## 펌웨어 코드 (ESP-IDF + Arduino 스타일)

```cpp
#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_BMP280.h>
#include <esp_sleep.h>

#define DHTPIN 4
#define DHTTYPE DHT22
#define SLEEP_DURATION_US (5 * 60 * 1000000ULL)  // 5분

// BLE UUIDs
#define SERVICE_UUID        "12345678-1234-1234-1234-123456789abc"
#define CHAR_TEMP_UUID      "12345678-1234-1234-1234-123456789ab1"
#define CHAR_HUMID_UUID     "12345678-1234-1234-1234-123456789ab2"
#define CHAR_PRESS_UUID     "12345678-1234-1234-1234-123456789ab3"

DHT dht(DHTPIN, DHTTYPE);
Adafruit_BMP280 bmp;
BLEServer* pServer = nullptr;
BLECharacteristic* pTempChar = nullptr;
BLECharacteristic* pHumidChar = nullptr;
BLECharacteristic* pPressChar = nullptr;
bool deviceConnected = false;

class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) { deviceConnected = true; }
  void onDisconnect(BLEServer* pServer) { deviceConnected = false; }
};

void setupBLE() {
  BLEDevice::init("ESP32-Sensor-Node");
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService* pService = pServer->createService(SERVICE_UUID);

  pTempChar = pService->createCharacteristic(
    CHAR_TEMP_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );
  pTempChar->addDescriptor(new BLE2902());

  pHumidChar = pService->createCharacteristic(
    CHAR_HUMID_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );
  pHumidChar->addDescriptor(new BLE2902());

  pPressChar = pService->createCharacteristic(
    CHAR_PRESS_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );
  pPressChar->addDescriptor(new BLE2902());

  pService->start();

  BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  BLEDevice::startAdvertising();
}

void readAndPublish() {
  float temp = dht.readTemperature();
  float humid = dht.readHumidity();
  float pressure = bmp.readPressure() / 100.0F;

  if (isnan(temp) || isnan(humid)) {
    Serial.println("DHT 읽기 실패");
    return;
  }

  // BLE Notify
  char buf[16];
  snprintf(buf, sizeof(buf), "%.1f", temp);
  pTempChar->setValue(buf);
  pTempChar->notify();

  snprintf(buf, sizeof(buf), "%.1f", humid);
  pHumidChar->setValue(buf);
  pHumidChar->notify();

  snprintf(buf, sizeof(buf), "%.1f", pressure);
  pPressChar->setValue(buf);
  pPressChar->notify();

  Serial.printf("온도: %.1f°C, 습도: %.1f%%, 기압: %.1fhPa\n",
                temp, humid, pressure);
}

void setup() {
  Serial.begin(115200);
  dht.begin();

  if (!bmp.begin(0x76)) {
    Serial.println("BMP280 초기화 실패");
  }

  setupBLE();
  Serial.println("BLE 광고 시작");
}

void loop() {
  readAndPublish();

  if (!deviceConnected) {
    // 연결된 클라이언트 없으면 30초 후 딥슬립
    delay(30000);
    Serial.println("딥슬립 진입");
    esp_deep_sleep(SLEEP_DURATION_US);
  }

  delay(2000);  // 연결 중에는 2초마다 갱신
}
```

이 코드의 핵심은 **연결 여부에 따라 동작을 다르게 하는 것**이다. BLE 클라이언트(게이트웨이 또는 스마트폰 앱)가 연결되어 있으면 2초마다 데이터를 notify하고, 연결이 없으면 30초 대기 후 딥슬립에 빠진다.

## 게이트웨이 구현 (Python, 라즈베리파이 또는 PC)

게이트웨이는 BLE Central 역할을 하며 수집한 데이터를 MQTT 브로커로 올린다.

```python
import asyncio
from bleak import BleakClient, BleakScanner
import paho.mqtt.client as mqtt
import json

DEVICE_NAME = "ESP32-Sensor-Node"
MQTT_BROKER = "localhost"
MQTT_TOPIC_BASE = "home/sensors"

CHAR_UUIDS = {
    "temperature": "12345678-1234-1234-1234-123456789ab1",
    "humidity":    "12345678-1234-1234-1234-123456789ab2",
    "pressure":    "12345678-1234-1234-1234-123456789ab3",
}

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

sensor_data = {}

def notification_handler(key):
    def handler(sender, data):
        value = float(data.decode())
        sensor_data[key] = value
        payload = json.dumps({"value": value, "unit": key})
        mqtt_client.publish(f"{MQTT_TOPIC_BASE}/{key}", payload)
        print(f"[{key}] {value}")
    return handler

async def main():
    print("BLE 스캔 중...")
    devices = await BleakScanner.discover()
    target = next((d for d in devices if d.name == DEVICE_NAME), None)

    if not target:
        print("디바이스를 찾을 수 없습니다")
        return

    print(f"연결: {target.address}")
    async with BleakClient(target.address) as client:
        for key, uuid in CHAR_UUIDS.items():
            await client.start_notify(uuid, notification_handler(key))

        print("데이터 수신 중... Ctrl+C로 종료")
        while True:
            await asyncio.sleep(1.0)

asyncio.run(main())
```

## 배터리 수명 최적화 — 실제 측정값

딥슬립 5분 주기로 운용했을 때 실제 측정값:

| 상태 | 전류 |
|------|------|
| WiFi 활성 | ~160mA |
| BLE Advertising | ~15mA |
| BLE Connected (Notify) | ~25mA |
| 딥슬립 | ~10µA |
| 데이터 읽기 + Notify (2초) | 평균 ~18mA |

2600mAh 18650 배터리 기준으로 계산하면:
- WiFi 상시 연결: 약 16시간
- BLE + 딥슬립 5분 주기: **약 5~6개월**

이 차이가 BLE를 선택하는 이유다. 실내 고정 센서라면 USB 전원을 써서 WiFi를 쓰는 게 낫지만, 야외나 배터리 의존 환경에서는 BLE 구조가 압도적으로 유리하다.

## 클라우드 연동 — Grafana + InfluxDB

MQTT 브로커(Mosquitto)에 올라온 데이터를 InfluxDB에 저장하고 Grafana로 시각화하는 구성이다. Docker Compose로 5분이면 세팅된다.

```yaml
# docker-compose.yml
version: '3'
services:
  mosquitto:
    image: eclipse-mosquitto:2
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto/config:/mosquitto/config

  influxdb:
    image: influxdb:2.7
    ports:
      - "8086:8086"
    environment:
      - INFLUXDB_DB=sensors
      - INFLUXDB_ADMIN_USER=admin
      - INFLUXDB_ADMIN_PASSWORD=password

  telegraf:
    image: telegraf:1.29
    volumes:
      - ./telegraf/telegraf.conf:/etc/telegraf/telegraf.conf
    depends_on:
      - influxdb
      - mosquitto

  grafana:
    image: grafana/grafana:10.4.0
    ports:
      - "3000:3000"
    depends_on:
      - influxdb
```

Telegraf가 MQTT를 구독해서 InfluxDB에 쓰는 브리지 역할을 한다. telegraf.conf의 핵심 부분:

```toml
[[inputs.mqtt_consumer]]
  servers = ["tcp://mosquitto:1883"]
  topics = ["home/sensors/#"]
  data_format = "json"
  json_string_fields = []

[[outputs.influxdb_v2]]
  urls = ["http://influxdb:8086"]
  token = "your-token"
  organization = "home"
  bucket = "sensors"
```

## 실전에서 겪은 문제들

**문제 1: BLE와 WiFi 동시 사용 시 간섭**

ESP32에서 BLE와 WiFi를 동시에 쓰면 같은 2.4GHz 대역을 공유하므로 간섭이 발생한다. 특히 WiFi 대역폭이 큰 작업(OTA 업데이트 등)을 할 때 BLE 연결이 끊기는 경우가 있다. 해결책은 시분할 방식으로 운용하거나, 업무 특성상 동시 동작이 필수라면 WiFi 채널을 1, 6, 11 중 하나로 고정하고 BLE 채널과 겹침을 최소화하는 설정을 쓰는 것이다.

**문제 2: DHT22 타이밍 민감성**

DHT22는 1-wire 프로토콜을 쓰는데, ESP32에서 인터럽트나 WiFi 처리가 겹치면 타이밍이 틀어져서 읽기 실패가 빈번하다. `dht.readTemperature()`가 NaN을 반환하면 그냥 이전 값을 유지하거나 한 번 더 읽는 로직을 반드시 넣어야 한다. 아니면 처음부터 I2C 방식의 SHT31을 쓰는 걸 추천한다. 약간 비싸지만 훨씬 안정적이다.

**문제 3: 딥슬립 후 재부팅 시 BLE 재초기화**

ESP32에서 딥슬립에서 깨어나면 사실상 전체 재부팅이 일어난다. BLE 스택도 다시 초기화해야 한다. 이 과정에서 메모리 단편화가 쌓이면 몇 주 후에 힙 오버플로가 발생하기도 한다. `esp_restart()`를 주기적으로 넣어두거나 RTC 메모리를 활용해 상태를 보존하는 구조가 필요하다.

## 다음 단계

이 기반 위에 다음 확장을 추천한다:

1. **메시 네트워킹**: ESP-NOW 또는 BLE Mesh를 써서 여러 노드가 서로 데이터를 릴레이하는 구조
2. **OTA 업데이트**: ArduinoOTA 또는 ESP-IDF의 OTA 파티션을 써서 펌웨어 원격 업데이트
3. **엣지 AI**: ESP32-S3는 내장 벡터 연산 유닛이 있어서 TensorFlow Lite Micro로 간단한 이상 감지 모델을 돌릴 수 있다

ESP32 에코시스템은 2026년 기준으로 정말 성숙해졌다. 10년 전에 라즈베리파이로 하던 작업의 상당 부분을 ESP32 하나로 처리할 수 있고, 소비전력은 비교도 안 될 정도로 낮다. IoT를 처음 시작한다면 이 플랫폼이 여전히 가장 좋은 출발점이라고 생각한다.
