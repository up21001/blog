---
title: "STM32 vs ESP32 vs Raspberry Pi Pico — 2026년 MCU 선택 가이드"
date: 2022-04-01T08:00:00+09:00
lastmod: 2022-04-06T08:00:00+09:00
description: "STM32, ESP32, Raspberry Pi Pico 2를 프로젝트 목적별로 비교 분석. 산업용 제어, IoT 연결, 교육용 프로토타이핑 각 상황에서 어떤 MCU를 선택해야 하는지 13년 경력 엔지니어가 정리합니다."
slug: "stm32-esp32-rpi-pico-mcu-guide-2026"
categories: ["hardware-lab"]
tags: ["STM32", "ESP32", "Raspberry Pi Pico", "MCU", "임베디드"]
series: []
draft: false
---

"ESP32 쓰면 되지 않나요?"

신입 엔지니어들에게 자주 듣는 말입니다. 맞는 말이기도 하고, 상황에 따라서는 완전히 틀린 말이기도 합니다. 임베디드 개발 13년 동안 STM32, ESP32, 그리고 Raspberry Pi Pico를 다 써본 입장에서 솔직하게 정리해보겠습니다.

2026년 현재 MCU 시장은 흥미로운 시점입니다. TinyML이 실용화 단계에 접어들었고, ESP32-P4 같은 고성능 신제품이 등장했으며, Raspberry Pi Pico 2는 RP2350 칩으로 성능을 크게 끌어올렸습니다.

## MCU 선택의 기준

MCU를 고를 때 고려해야 할 핵심 요소는 다음과 같습니다.

1. **무선 통신 필요 여부** — WiFi/BLE가 필요한가
2. **실시간성 요구 수준** — 마이크로초 단위 타이밍이 필요한가
3. **소비 전력** — 배터리로 몇 개월을 버텨야 하는가
4. **개발 생태계** — 쓸 수 있는 라이브러리가 풍부한가
5. **단가와 수급** — 양산 시 안정적으로 구매 가능한가

![2026 MCU 선택 가이드 비교표](/images/mcu-comparison-2026.svg)

## STM32 — 산업 현장의 믿음직한 일꾼

ST마이크로일렉트로닉스의 STM32 시리즈는 Cortex-M 기반으로 F0부터 H7까지 다양한 라인업을 갖추고 있습니다. 임베디드 개발 입문 시절부터 써온 플랫폼이라 애착이 있습니다.

### 강점

**실시간 제어에서 독보적입니다.** STM32H7 시리즈는 Cortex-M7 코어에 400MHz 동작을 지원합니다. FreeRTOS, ThreadX 같은 RTOS와 조합하면 마이크로초 단위의 정밀한 타이밍 제어가 가능합니다. 모터 제어, 전력 변환, 산업용 통신(CANbus, Modbus) 등에서 여전히 최선의 선택입니다.

**하드웨어 주변장치가 풍부합니다.** 다중 SPI/I2C/UART, 고분해능 ADC, 하드웨어 암호화 엔진 등 전용 하드웨어가 많습니다. 소프트웨어로 처리하면 CPU를 잡아먹는 작업을 하드웨어가 대신합니다.

**2026년에는 ST Edge AI 플랫폼**도 주목할 만합니다. STM32N6 시리즈에는 NPU(Neural Processing Unit)가 내장되어 TinyML 추론을 CPU 부담 없이 처리합니다.

### 약점

무선 통신이 내장되어 있지 않습니다. WiFi가 필요하면 ESP8266/ESP32 모듈을 UART로 붙여야 합니다. 설계가 복잡해지고 단가도 올라갑니다.

초기 설정 진입 장벽이 있습니다. STM32CubeIDE, HAL 라이브러리, 클록 설정 등 배워야 할 것이 많습니다. Arduino처럼 plug-and-play는 아닙니다.

### 추천 사용처

- 모터 드라이버, 서보 컨트롤러
- 산업용 센서 인터페이스 (4-20mA, RS-485)
- 전력 변환 장치 (SMPS, 인버터)
- 배터리 BMS 컨트롤러
- 의료기기, 항공우주 (인증 가능한 HAL 라이브러리)

```c
// STM32 HAL로 ADC + DMA 고속 샘플링 예시
HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_buffer, ADC_BUFFER_SIZE);
// DMA 완료 콜백에서 처리
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc) {
    process_samples(adc_buffer, ADC_BUFFER_SIZE);
}
```

## ESP32 — IoT 프로젝트의 절대 강자

Espressif Systems의 ESP32는 2016년 등장 이후 IoT 시장을 장악했습니다. 저렴한 가격에 WiFi+BLE 내장, 풍부한 커뮤니티, Arduino 호환성까지 갖췄습니다.

### 강점

**무선 연결이 모든 것을 바꿉니다.** $3~5짜리 칩 하나로 스마트홈 기기, 환경 센서, 원격 제어 장치를 만들 수 있습니다. WiFi 6까지 지원하는 ESP32-C6, 고성능 HMI를 위한 ESP32-P4 등 목적별 파생 모델도 다양합니다.

**생태계가 압도적입니다.** Arduino IDE, PlatformIO, MicroPython, ESP-IDF 모두 지원됩니다. GitHub에서 원하는 센서 라이브러리를 못 찾는 경우가 거의 없습니다.

**ESP32-S3의 AI 확장 명령어**도 흥미롭습니다. TensorFlow Lite Micro로 간단한 음성 인식, 이미지 분류를 MCU에서 직접 실행할 수 있습니다.

### 약점

실시간성이 STM32에 미치지 못합니다. WiFi 스택이 CPU를 점유하는 시간이 있어서 타이밍 지터(jitter)가 발생합니다. 엄격한 실시간 제어에는 적합하지 않습니다.

전력 소비가 상대적으로 높습니다. 딥슬립 모드를 잘 활용해야 배터리 수명을 늘릴 수 있습니다. 슬립 없이 WiFi를 켜두면 수백 mA를 소비합니다.

### 추천 사용처

- 스마트홈 기기 (온도계, 플러그, 스위치)
- IoT 센서 노드 (MQTT, HTTP 연결)
- OTA 업데이트가 필요한 기기
- 빠른 프로토타이핑
- 웨어러블 (딥슬립 활용 시)

```python
# MicroPython으로 ESP32 MQTT 센서 전송
import network
import machine
from umqtt.simple import MQTTClient

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('SSID', 'PASSWORD')

client = MQTTClient('esp32', 'broker.local')
client.connect()

sensor = machine.ADC(machine.Pin(34))
while True:
    value = sensor.read()
    client.publish('home/sensor', str(value))
    machine.lightsleep(60000)  # 1분 슬립
```

## Raspberry Pi Pico 2 — 교육과 취미의 새 기준

2024년 출시된 Pico 2는 RP2350 칩을 탑재했습니다. Cortex-M33 듀얼코어에 RISC-V 코어도 선택 가능한 독특한 구성입니다.

### 강점

**MicroPython 경험이 최고 수준입니다.** Raspberry Pi 재단이 MicroPython 개발에 직접 기여하는 만큼 안정성과 문서화가 뛰어납니다.

**PIO(Programmable I/O)**가 혁신적입니다. 소프트웨어로 임의의 통신 프로토콜을 구현할 수 있습니다. WS2812 LED 제어, SPI 커스텀 프로토콜 등을 CPU 부담 없이 처리합니다.

**가격이 저렴하고 구하기 쉽습니다.** 교육용, 취미용으로 부담 없이 시작할 수 있습니다.

### 약점

무선 통신은 Pico W(WiFi+BLE 내장) 모델을 선택해야 합니다. 기본 Pico에는 없습니다.

산업용 인증, 전문 지원이 상대적으로 부족합니다. 취미나 교육 레벨을 넘어 상용 제품에 쓰기에는 고려해야 할 점이 있습니다.

```python
# Pico PIO로 WS2812 LED 제어
import array, time
from machine import Pin
import rp2

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT,
             autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2; T2 = 5; T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")           .side(1)    [T2 - 1]
    label("do_zero")
    nop()                    .side(0)    [T2 - 1]
    wrap()
```

## 2026년 TinyML 트렌드

세 플랫폼 모두 AI/ML 추론을 지원하는 방향으로 발전하고 있습니다. 울트라로우파워 MCU에서 TinyML을 실행하는 것이 이제 현실이 됐습니다.

- **STM32**: ST Edge AI, X-CUBE-AI 툴체인으로 Keras 모델을 C 코드로 변환
- **ESP32-S3**: TensorFlow Lite Micro, 음성 웨이크워드 감지
- **Pico 2**: TensorFlow Lite Micro (Cortex-M33 DSP 확장 활용)

## 최종 선택 가이드

상황별로 요약하면 다음과 같습니다.

**산업용 제어, 정밀 타이밍, 모터 드라이버** → STM32

**WiFi 연결 IoT, 빠른 프로토타이핑, 스마트홈** → ESP32

**교육, 취미, MicroPython 입문, PIO 활용** → Raspberry Pi Pico 2

**TinyML, AI 추론이 핵심인 경우** → ESP32-S3 또는 STM32N6

시작할 때 하나를 깊게 파는 것이 좋습니다. ESP32로 시작해서 IoT 기초를 익히고, 이후 산업 현장에서 필요하면 STM32로 넘어가는 경로를 추천합니다. 세 플랫폼 모두 적절한 자리가 있습니다. 용도에 맞게 선택하시면 됩니다.
