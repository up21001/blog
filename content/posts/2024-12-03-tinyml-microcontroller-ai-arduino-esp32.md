---
title: "TinyML 입문 — 마이크로컨트롤러에서 AI 모델 돌리기 (Arduino/ESP32)"
date: 2024-12-03T08:00:00+09:00
lastmod: 2024-12-07T08:00:00+09:00
description: "TinyML 개념부터 TensorFlow Lite Micro, Edge Impulse, ESP32 실전 예시까지. 마이크로컨트롤러에서 AI 추론을 실행하는 전 과정을 엔지니어 관점에서 정리합니다."
slug: "tinyml-microcontroller-ai-arduino-esp32"
categories: ["hardware-lab"]
tags: ["TinyML", "임베디드 AI", "Arduino", "ESP32", "TensorFlow Lite"]
series: []
draft: false
---

![TinyML 파이프라인](/images/tinyml-microcontroller-ai-arduino-esp32.svg)

클라우드로 데이터를 올려 추론하는 시대에서, 이제는 손톱만 한 칩 위에서 직접 AI를 돌리는 시대로 넘어오고 있습니다. TinyML(Tiny Machine Learning)은 수십 킬로바이트 수준의 메모리와 수백 밀리와트의 전력 예산 안에서 머신러닝 추론을 실행하는 기술입니다. 저는 13년간 임베디드 시스템을 다루면서 "MCU에서 AI를"이라는 아이디어가 처음 나왔을 때 반신반의했습니다. 하지만 지금은 실제 제품에 TinyML을 적용하고 있습니다. 이 글에서 그 경험을 공유합니다.

## TinyML이란 무엇인가

TinyML은 단순히 "작은 AI"가 아닙니다. 다음 세 가지 제약 조건 아래에서 ML 추론을 실행하는 전체 방법론입니다.

- **메모리**: SRAM 수십~수백 KB, Flash 수백 KB~수 MB
- **전력**: 배터리로 수개월~수년 동작
- **지연**: 수 밀리초~수십 밀리초 이내 응답

이 조건을 만족하면서 키워드 감지, 이상 진동 탐지, 이미지 분류, 제스처 인식 같은 작업을 MCU 위에서 수행할 수 있습니다. 서버로 데이터를 보낼 필요가 없으니 통신 비용, 지연, 개인정보 문제를 한꺼번에 해결합니다.

대표적인 타깃 하드웨어는 다음과 같습니다.

| 보드 | MCU | SRAM | Flash | 특징 |
|------|-----|------|-------|------|
| Arduino Nano 33 BLE Sense | nRF52840 | 256 KB | 1 MB | IMU·마이크 내장 |
| ESP32-S3 DevKit | Xtensa LX7 듀얼코어 | 512 KB + PSRAM 8MB | 8 MB | Wi-Fi·BLE, SIMD |
| Raspberry Pi Pico 2 | RP2350 | 520 KB | 4 MB | 저가, 이중코어 |
| STM32H7 | Cortex-M7 480MHz | 1 MB | 2 MB | 고성능 MCU |

## TinyML 핵심 프레임워크

### TensorFlow Lite for Microcontrollers

Google이 TensorFlow Lite(모바일용)를 더 줄여 MCU용으로 만든 것이 TensorFlow Lite for Microcontrollers(TFLM)입니다. 동적 메모리 할당 없이 정적 Tensor Arena를 사용하고, 운영체제 없이도 동작합니다.

핵심 구성 요소는 세 가지입니다.

1. **모델 파일(.tflite)**: FlatBuffer 형식으로 직렬화된 모델. C 배열로 변환해 Flash에 저장합니다.
2. **Interpreter**: 모델을 읽고 Op(연산)를 순서대로 실행합니다.
3. **Tensor Arena**: 입력·중간·출력 텐서를 담는 SRAM 버퍼입니다.

기본 추론 코드 구조는 이렇습니다.

```cpp
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "model_data.h"  // xxd로 변환한 .tflite C 배열

// Tensor Arena: 모델 크기에 맞춰 조정 필요
constexpr int kTensorArenaSize = 60 * 1024;
alignas(16) uint8_t tensor_arena[kTensorArenaSize];

tflite::AllOpsResolver resolver;
const tflite::Model* model = tflite::GetModel(g_model_data);
tflite::MicroInterpreter interpreter(model, resolver, tensor_arena,
                                     kTensorArenaSize);
interpreter.AllocateTensors();

// 입력 텐서에 데이터 복사
TfLiteTensor* input = interpreter.input(0);
memcpy(input->data.f, sensor_data, sizeof(float) * INPUT_SIZE);

// 추론
interpreter.Invoke();

// 출력 읽기
TfLiteTensor* output = interpreter.output(0);
float score = output->data.f[0];
```

### Edge Impulse

Edge Impulse는 TinyML 개발 전 과정을 웹 인터페이스로 제공하는 플랫폼입니다. 데이터 수집, 라벨링, 특징 추출, 모델 학습, MCU 코드 생성까지 한 번에 처리합니다. 프로그래밍 경험이 있는 하드웨어 엔지니어라면 처음 프로젝트를 2~3시간 안에 완성할 수 있습니다.

Edge Impulse CLI로 ESP32를 바로 연결해 데이터를 수집할 수 있습니다.

```bash
npm install -g edge-impulse-cli
edge-impulse-daemon --clean
```

포트를 지정하면 MCU에서 직접 센서 데이터를 캡처해 클라우드로 업로드합니다. 학습이 끝나면 Arduino 라이브러리 형태로 내려받아 바로 사용할 수 있습니다.

## ESP32로 키워드 감지 프로젝트

실제로 구현해 본 "예/아니오" 키워드 감지 프로젝트를 단계별로 설명합니다.

### 환경 설정

ESP32-S3 개발 보드와 I2S 마이크 모듈(INMP441)을 사용했습니다. Arduino IDE에 ESP32 보드 패키지와 TensorFlow Lite Micro 라이브러리를 설치합니다.

```
보드 매니저 URL: https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
라이브러리: Arduino_TensorFlowLite (v2.4.0+)
```

### 데이터 수집

I2S로 16kHz, 16bit 모노 오디오를 수집합니다.

```cpp
#include <driver/i2s.h>

const i2s_config_t i2s_config = {
  .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
  .sample_rate = 16000,
  .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
  .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
  .communication_format = I2S_COMM_FORMAT_STAND_I2S,
  .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
  .dma_buf_count = 4,
  .dma_buf_len = 256,
};

void setup() {
  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  // SCK=14, WS=15, SD=32 핀 설정
}
```

### 특징 추출: MFCC

원시 오디오를 바로 모델에 넣지 않고 MFCC(Mel Frequency Cepstral Coefficients)로 변환합니다. 1초짜리 오디오(16000 샘플)를 25ms 윈도우로 슬라이딩하면 약 49×13 크기의 특징 맵이 나옵니다. 이 2D 배열이 모델의 입력이 됩니다.

Edge Impulse는 이 과정을 자동으로 처리해 주므로, 수동으로 구현할 필요 없이 DSP 블록에서 "MFCC"를 선택하면 됩니다.

### 모델 구조

키워드 감지에는 가벼운 CNN 구조를 사용합니다.

```
Input (49, 13, 1)
→ Conv2D (8 filters, 3×3) + ReLU
→ MaxPool2D (2×2)
→ Conv2D (16 filters, 3×3) + ReLU
→ MaxPool2D (2×2)
→ Flatten
→ Dense (64) + ReLU
→ Dense (3) + Softmax   # yes / no / noise
```

이 구조의 파라미터 수는 약 12,000개, INT8 양자화 후 모델 크기는 약 14KB입니다. ESP32의 4MB Flash에서는 여유롭게 수용합니다.

### 양자화

실수 모델(float32)을 INT8로 양자화하면 모델 크기가 4분의 1로 줄고 추론 속도가 2~4배 빨라집니다.

```python
import tensorflow as tf

converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
converter.optimizations = [tf.lite.Optimize.DEFAULT]

# 대표 데이터셋으로 양자화 범위 보정
def representative_dataset():
    for data in validation_dataset.take(100):
        yield [tf.cast(data[0], tf.float32)]

converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8

tflite_model = converter.convert()
```

양자화 후 정확도 손실은 보통 1~2% 이내입니다.

### C 배열 변환

```bash
xxd -i model.tflite > model_data.h
```

이 명령으로 .tflite 파일을 C 헤더로 변환합니다. `unsigned char g_model_data[]`와 `unsigned int g_model_data_len`이 생성됩니다.

### 추론 루프

```cpp
void loop() {
  // 1초 분량 오디오 버퍼 수집
  size_t bytes_read;
  i2s_read(I2S_NUM_0, audio_buffer, AUDIO_BUFFER_SIZE, &bytes_read, portMAX_DELAY);

  // MFCC 특징 추출
  compute_mfcc(audio_buffer, mfcc_features);

  // 입력 텐서 설정
  TfLiteTensor* input = interpreter->input(0);
  for (int i = 0; i < FEATURE_SIZE; i++) {
    input->data.int8[i] = (int8_t)(mfcc_features[i] / input->params.scale
                           + input->params.zero_point);
  }

  // 추론
  TfLiteStatus invoke_status = interpreter->Invoke();

  // 결과 해석
  TfLiteTensor* output = interpreter->output(0);
  int8_t yes_score = output->data.int8[0];
  int8_t no_score  = output->data.int8[1];

  if (yes_score > 100) {
    Serial.println("감지: YES");
    digitalWrite(LED_PIN, HIGH);
  }
}
```

## 성능 최적화 팁

13년간 임베디드를 다루면서 익힌 TinyML 최적화 포인트를 정리합니다.

**Tensor Arena 크기 최소화**: `MicroInterpreter::arena_used_bytes()`로 실제 사용량을 측정한 뒤, 여유분 10~20%만 남기고 줄입니다. SRAM이 부족한 MCU에서는 이 작업이 필수입니다.

**Op Resolver 선택**: `AllOpsResolver` 대신 `MicroMutableOpResolver`를 사용해 모델에 필요한 Op만 등록합니다. 코드 크기가 수십 KB 줄어듭니다.

```cpp
tflite::MicroMutableOpResolver<5> resolver;
resolver.AddConv2D();
resolver.AddMaxPool2D();
resolver.AddReshape();
resolver.AddFullyConnected();
resolver.AddSoftmax();
```

**ESP32-S3 SIMD 활용**: ESP32-S3의 Xtensa LX7 코어는 벡터 명령을 지원합니다. TFLM의 Optimized Kernels 옵션을 활성화하면 Conv2D 연산이 2~3배 빨라집니다.

**슬라이딩 윈도우**: 오디오나 IMU 데이터를 새로 수집할 때마다 전체 버퍼를 갱신하지 말고, 절반만 밀어 넣는 방식으로 추론 빈도를 높이면서 CPU 부하를 줄입니다.

## 실제 제품 적용 사례

저는 산업용 모터 이상 감지 장치에 TinyML을 적용했습니다. 3축 가속도계 데이터를 ESP32로 읽어 FFT 특징을 추출하고, 1D CNN으로 정상/불균형/베어링 손상을 분류합니다. 클라우드 전송 없이 MCU 안에서 추론이 완결되므로 인터넷 연결이 없는 공장 환경에서도 동작합니다. 배터리로 약 8개월 운용 중입니다.

## 다음 단계

TinyML에 입문했다면 다음 방향을 권장합니다.

1. **Edge Impulse 공식 튜토리얼**: 키워드 감지, 모션 감지 예제가 잘 정리되어 있습니다.
2. **TensorFlow Lite Micro 예제**: GitHub의 `tensorflow/tflite-micro` 저장소에서 `hello_world`, `micro_speech` 예제를 직접 빌드해 보세요.
3. **하드웨어 업그레이드**: 이미지 분류를 해보고 싶다면 OV2640 카메라 모듈과 ESP32-S3를 조합하는 것이 가장 저렴한 출발점입니다.

마이크로컨트롤러에서 AI를 돌린다는 것이 처음에는 비현실적으로 들릴 수 있습니다. 하지만 지금 여러분의 책상 위에 있는 ESP32 보드에서 이미 가능합니다. 시작 비용은 보드 한 개와 몇 시간의 시간입니다.
