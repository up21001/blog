---
title: "NVIDIA Jetson Orin으로 엣지 AI 구현하기 — 실시간 객체 인식 프로젝트"
date: 2024-11-17T08:00:00+09:00
lastmod: 2024-11-19T08:00:00+09:00
description: "Jetson Orin NX 16GB에 JetPack을 설치하고 YOLOv8을 TensorRT로 최적화해 실시간 객체 인식을 구현하는 전 과정을 엔지니어 시각으로 정리합니다."
slug: "nvidia-jetson-orin-edge-ai-object-detection"
categories: ["hardware-lab"]
tags: ["Jetson Orin", "엣지 AI", "YOLO", "객체 인식", "NVIDIA"]
series: []
draft: false
---

![Jetson Orin 엣지 AI 파이프라인](/images/nvidia-jetson-orin-edge-ai-object-detection.svg)

NVIDIA Jetson 시리즈를 처음 접한 건 2018년 Jetson TX2였습니다. 당시엔 "이 정도면 충분하다"고 생각했는데, Orin 세대를 손에 쥐었을 때 다시 같은 생각을 했습니다. 100 TOPS라는 숫자보다, 그 성능이 손바닥 크기 보드에 들어간다는 사실이 더 인상적입니다. 이 글에서는 Jetson Orin NX 16GB에 YOLOv8을 올려 실시간 객체 인식 시스템을 구축하는 과정을 설명합니다.

## Jetson Orin 제품군 선택 가이드

Jetson Orin은 세 가지 폼팩터로 나옵니다.

| 제품 | AI 성능 | GPU | 메모리 | 전력 | 권장 용도 |
|------|---------|-----|--------|------|----------|
| Orin Nano 4GB | 20 TOPS | 512-core | 4 GB | 7~10W | 프로토타입, 교육 |
| Orin Nano 8GB | 40 TOPS | 1024-core | 8 GB | 7~15W | 스마트 카메라 |
| Orin NX 8GB | 70 TOPS | 1024-core | 8 GB | 10~20W | 산업용 비전 |
| Orin NX 16GB | 100 TOPS | 1024-core | 16 GB | 10~25W | 다중 카메라 AI |
| AGX Orin 32GB | 200 TOPS | 2048-core | 32 GB | 15~60W | 자율주행, 로봇 |

저는 다중 카메라(4채널) 실시간 추론을 목표로 Orin NX 16GB를 선택했습니다. Seeed reComputer J4012 캐리어보드를 사용해 M.2 SSD와 CSI 카메라를 함께 연결했습니다.

## JetPack 6 설치

JetPack 6는 Ubuntu 22.04 기반으로, CUDA 12.2, cuDNN 8.9, TensorRT 8.6을 포함합니다.

### SDK Manager로 플래싱

호스트 PC(Ubuntu 20.04 이상)에 NVIDIA SDK Manager를 설치합니다.

```bash
# SDK Manager 설치
sudo apt-get install ./sdkmanager_*.deb

# Jetson을 Recovery Mode로 부팅 후 USB 연결
sdkmanager --cli install --logintype devzone \
  --product Jetson --version 6.0 \
  --targetos Linux --host
```

플래싱에 약 30~40분이 소요됩니다. 완료 후 HDMI 모니터를 연결하면 Ubuntu 데스크톱이 보입니다.

### 기본 설정

```bash
# 전력 모드 설정 (10W 절전 / 25W 최대)
sudo nvpmodel -m 0   # 25W MAXN 모드

# Jetson 클럭 최대화
sudo jetson_clocks

# 시스템 정보 확인
jetson_release
# JetPack 6.0 (L4T 36.3.0)
# CUDA 12.2.140
# TensorRT 8.6.2.3
```

MAXN 모드와 `jetson_clocks`를 함께 적용하면 추론 성능이 절전 모드 대비 약 40% 향상됩니다. 발열이 증가하므로 방열판과 팬을 반드시 달아야 합니다.

## YOLOv8 환경 구성

### Python 가상환경 설정

```bash
# 가상환경 생성
python3 -m venv ~/trt_env
source ~/trt_env/bin/activate

# PyTorch (Jetson 전용 빌드)
pip install torch torchvision \
  --index-url https://pypi.jetson-ai-lab.dev/jp6/cu122

# Ultralytics YOLOv8
pip install ultralytics

# 설치 확인
python3 -c "import torch; print(torch.cuda.is_available())"
# True
```

NVIDIA가 Jetson용 PyTorch 빌드를 별도 서버에서 배포합니다. 일반 pip 빌드로는 CUDA를 인식하지 못하므로 반드시 Jetson 전용 인덱스를 사용해야 합니다.

### YOLOv8 추론 테스트

```python
from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")  # nano 모델로 시작

# 웹캠 추론
results = model.predict(
    source=0,           # /dev/video0
    show=True,
    conf=0.5,
    device="cuda:0"
)
```

처음 실행 시 모델이 자동으로 다운로드됩니다. GPU 추론으로 약 45 FPS가 나오는 것을 확인했습니다.

## TensorRT 최적화

YOLOv8의 추론 성능을 극대화하려면 TensorRT 엔진으로 변환해야 합니다.

### ONNX → TensorRT 변환

```python
from ultralytics import YOLO

# PT → ONNX → TensorRT 변환 (한 번에)
model = YOLO("yolov8n.pt")
model.export(
    format="engine",
    device=0,
    half=True,          # FP16 모드
    simplify=True,
    workspace=4,        # GPU 메모리 (GB)
    batch=1
)
# yolov8n.engine 파일 생성됨 (~10분 소요)
```

INT8 양자화를 원한다면 보정 데이터셋이 필요합니다.

```python
model.export(
    format="engine",
    device=0,
    int8=True,
    data="coco.yaml",   # 보정용 데이터셋
    workspace=4,
)
```

### TensorRT 엔진으로 추론

```python
from ultralytics import YOLO

# TensorRT 엔진 로드
model = YOLO("yolov8n.engine")

# 실시간 추론 루프
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while True:
    ret, frame = cap.read()
    results = model.predict(frame, conf=0.4, verbose=False)
    annotated = results[0].plot()
    cv2.imshow("Jetson Orin YOLO", annotated)
    if cv2.waitKey(1) == ord('q'):
        break
```

변환 결과 성능을 측정했습니다.

| 설정 | FPS | 지연 (ms) | 메모리 |
|------|-----|-----------|--------|
| PT (FP32) | 45 | 22 | 2.1 GB |
| TRT FP16 | 82 | 12 | 1.2 GB |
| TRT INT8 | 156 | 6 | 0.8 GB |

INT8 변환으로 정확도는 mAP 기준 약 1.5% 하락했지만, FPS는 3.5배 향상되었습니다.

## 4채널 다중 카메라 파이프라인

실제 프로젝트에서는 공장 라인 4곳을 동시에 감시해야 했습니다. GStreamer 파이프라인으로 4개 카메라를 병렬로 처리합니다.

```python
import threading
from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.engine")

def process_camera(camera_id, source):
    cap = cv2.VideoCapture(source)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model.predict(frame, conf=0.4, verbose=False)
        # 결과를 공유 큐에 푸시
        result_queue[camera_id].put(results[0])

# 4개 스레드 병렬 실행
cameras = [0, 1, 2, 3]
threads = [threading.Thread(target=process_camera, args=(i, c))
           for i, c in enumerate(cameras)]
for t in threads:
    t.start()
```

4채널 동시 추론 시 각 채널당 약 35 FPS를 유지했습니다. Orin NX 16GB의 GPU 점유율은 약 75%, DLA는 사용하지 않은 상태였습니다.

## DLA 활용으로 추가 성능 확보

Jetson Orin에는 GPU와 별개로 DLA(Deep Learning Accelerator)가 2개 내장되어 있습니다. GPU와 DLA를 분리해 사용하면 전체 처리량을 더 높일 수 있습니다.

```python
# DLA 코어 0 사용
model.export(
    format="engine",
    device=0,
    half=True,
    dla_core=0          # DLA 코어 지정
)
```

DLA는 지원 레이어가 제한적이므로(Conv, BN, ReLU 계열만), 지원하지 않는 레이어는 자동으로 GPU로 폴백됩니다. YOLOv8의 경우 약 70%의 레이어가 DLA에서 실행되었습니다.

## 시스템 모니터링

```bash
# GPU/CPU/메모리 실시간 모니터링
sudo jtop

# 온도 확인
cat /sys/class/thermal/thermal_zone*/temp
# 정상 범위: 40~65°C (부하 시)

# 전력 측정
sudo tegrastats
# RAM 3421/16384MB, CPU [45%@2035,38%@2035,41%@2035,40%@2035]
# GPU 52% GR3D_FREQ 918MHz, Temp CPU@52C GPU@55C
```

`jtop`은 Jetson 전용 모니터링 도구로 `pip install jetson-stats`로 설치합니다. GPU 클럭, 전력, 온도를 한 화면에서 볼 수 있어 최적화 작업에 필수입니다.

## 실제 프로젝트 결과

공장 라인 4채널 이상 감지 시스템을 3개월 운용한 결과입니다.

- **처리량**: 4채널 × 720p × 35 FPS 안정 동작
- **소비 전력**: 평균 18W (MAXN 모드)
- **오탐률**: 모델 파인튜닝 후 2% 미만
- **MTBF**: 3개월 무중단 동작 (OS 업데이트 제외)

Jetson AGX Orin 대비 Orin NX의 가격은 절반 이하입니다. 단일 카메라 또는 소규모 다중 카메라 시스템이라면 Orin NX 16GB가 최선의 가성비를 제공합니다.

## 마치며

Jetson Orin은 엣지 AI 플랫폼 중 가장 성숙한 생태계를 가지고 있습니다. JetPack의 완성도, TensorRT의 최적화 수준, NVIDIA 공식 문서와 커뮤니티 지원이 모두 훌륭합니다. 라즈베리 파이처럼 저렴하지는 않지만, 실제 산업 현장에서 요구하는 성능과 안정성을 갖춘 플랫폼은 Jetson이 거의 유일합니다.

다음 글에서는 Raspberry Pi AI Kit으로 더 낮은 예산에서 컴퓨터 비전을 구현하는 방법을 다루겠습니다.
