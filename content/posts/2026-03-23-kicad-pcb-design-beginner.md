---
title: "KiCad로 첫 PCB 만들기 — 회로도부터 Gerber 파일까지 완전 정복"
date: 2026-03-23T10:00:00+09:00
lastmod: 2026-03-23T10:00:00+09:00
description: "KiCad 9.0으로 첫 PCB를 설계하는 전 과정을 13년 차 엔지니어가 실전 팁과 함께 안내합니다. 회로도 작성, 풋프린트 할당, PCB 레이아웃, Gerber 출력까지 단계별로 설명합니다."
slug: "kicad-pcb-design-beginner"
categories: ["hardware-lab"]
tags: ["KiCad", "PCB", "회로설계", "하드웨어", "Gerber", "JLCPCB"]
series: []
draft: false
---

PCB 설계를 처음 배울 때 가장 높은 허들은 "어떤 도구를 써야 하는가"다. Altium Designer는 업계 표준이지만 라이선스가 수백만 원이고, Eagle은 오토데스크에 인수된 이후 정책이 껄끄럽다. 결론부터 말하면 **KiCad**가 답이다. 완전 무료, 오픈소스, 상업적 사용도 가능하고, 기능은 Altium에 결코 밀리지 않는다. 2026년 현재 버전 9.0은 내가 입문할 때와 비교하면 완전히 다른 도구가 됐다.

이 글은 "LED 하나 깜박이는 ESP32 최소 회로" 수준의 첫 PCB를 설계하면서 전체 과정을 안내한다. 회로 설계보다 **KiCad 도구 사용법과 실수 포인트**에 집중했다.

![KiCad PCB 설계 워크플로우](/images/kicad-pcb-design-workflow.svg)

## KiCad 설치 및 환경 세팅

[kicad.org](https://www.kicad.org) 에서 최신 버전을 받아 설치한다. Windows/macOS/Linux 모두 지원한다. 설치 후 반드시 해야 할 것:

1. **전역 심볼 라이브러리 경로 확인**: Preferences → Manage Symbol Libraries → 기본 라이브러리들이 잘 보이는지 확인
2. **풋프린트 라이브러리 확인**: Preferences → Manage Footprint Libraries → 마찬가지로 기본 라이브러리 체크
3. **3D 뷰어용 모델 경로 설정**: 선택 사항이지만 STEP 파일 경로를 지정해두면 나중에 3D 뷰에서 실제 부품처럼 보인다

## Step 1: 회로도 작성 (Schematic Editor)

KiCad는 반드시 **회로도 먼저, PCB 나중**이다. 회로도 없이 바로 PCB 에디터를 열 수도 있지만 그렇게 하면 net 정보가 없어서 라우팅 가이드를 받을 수 없다.

### 새 프로젝트 생성

```
File → New Project
프로젝트 이름: esp32-minimal
저장 경로: 원하는 위치
```

프로젝트를 만들면 `.kicad_pro`, `.kicad_sch`, `.kicad_pcb` 세 파일이 생성된다. 모두 사람이 읽을 수 있는 텍스트 포맷이라 Git으로 버전 관리가 가능하다.

### 심볼 배치

회로도 에디터에서 `A` 키를 누르면 심볼 선택창이 뜬다. 우리가 필요한 심볼:
- `ESP32-WROOM-32E` — Device 또는 RF 라이브러리에서 찾는다
- `LED` — Device 라이브러리
- `R` (저항) — Device 라이브러리
- `Connector_PinHeader_2.54mm:PinHeader_1x02` — 전원 커넥터용
- `PWR_FLAG` — 반드시 VCC와 GND 네트에 붙여야 ERC 통과

**중요한 실수 포인트**: `PWR_FLAG`를 VCC와 GND 네트에 각각 하나씩 붙이지 않으면 ERC(전기 규칙 검사)에서 "핀이 드라이브되지 않는 네트" 경고가 뜬다. KiCad는 전원이 어디서 오는지 명시적으로 선언하길 요구한다.

### 배선

`W` 키로 와이어 모드 시작. ESP32의 EN 핀은 10kΩ 풀업 저항으로 3.3V에 연결해야 정상 동작한다. IO0 핀은 플래싱 모드 진입용 버튼(GND에 풀다운)을 달아두면 나중에 매우 편하다.

최소 회로:
```
3.3V → ESP32 VDD (3V3 핀)
GND → ESP32 GND
ESP32 EN → 10kΩ → 3.3V
ESP32 IO0 → 버튼 → GND (버튼 없이 사용 시 3.3V에 풀업)
ESP32 GPIO2 → 220Ω → LED → GND
USB-UART 모듈 TXD → ESP32 RXD0
USB-UART 모듈 RXD → ESP32 TXD0
```

### ERC 실행

회로도 완성 후 Inspect → Electrical Rules Checker → Run. 오류가 없어야 다음 단계로 간다. 경고도 원인을 이해하고 넘어갈 것.

## Step 2: 풋프린트 할당

회로도의 각 심볼에 실제 물리적 패드 패턴(풋프린트)을 연결하는 단계다.

Tools → Assign Footprints에서 각 부품에 풋프린트를 지정한다.

| 심볼 | 풋프린트 |
|------|---------|
| ESP32-WROOM-32E | RF_Module:ESP32-WROOM-32 |
| LED | LED_THT:LED_D5.0mm |
| R (저항) | Resistor_SMD:R_0805_2012Metric |
| 커넥터 | Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical |

**SMD vs THT 선택**: 첫 PCB라면 SMD(표면실장)보다 THT(관통홀) 부품이 납땜하기 쉽다. 하지만 저항 같은 단순한 부품은 0805 크기의 SMD도 손납땜으로 충분히 가능하다. 0603 이하는 루페나 현미경 없이는 힘들다.

## Step 3: PCB 레이아웃

회로도에서 Tools → Update PCB from Schematic을 실행하면 PCB 에디터에 모든 부품이 "라츠네스트(ratsnest)" — 연결되어야 할 핀들 사이의 가는 선 — 와 함께 나타난다.

### 부품 배치 원칙

**전원 경로 먼저**: USB 커넥터 → 전원 입력 커패시터 → 레귤레이터 순서로 배치. 전류가 흐를 경로를 먼저 잡아두면 나머지가 자연스럽게 따라온다.

**바이패스 커패시터는 IC에 붙여서**: ESP32의 각 전원 핀에 100nF 커패시터를 최대한 가까이 붙인다. 이게 멀어질수록 노이즈 억제 효과가 떨어진다.

**크리스털은 MCU 가까이**: 발진기가 있다면 기생 커패시턴스를 줄이기 위해 MCU 핀 바로 옆에 배치해야 한다. 긴 배선은 주파수 드리프트를 유발한다.

**LED와 커넥터는 외곽에**: 사용자가 접근해야 하는 부품은 보드 가장자리로 배치한다.

### 라우팅 (배선)

`X` 키로 라우팅 시작. 선폭 기본값:
- 신호선: 0.25mm
- 전원선: 0.5mm 이상
- GND: 폴리곤(베타 구리 채움) 사용

**GND 폴리곤 채우기**: PCB 에디터에서 `B.Cu` 레이어에서 `P` 키로 폴리곤 영역을 보드 외곽을 따라 그린다. 채울 네트를 GND로 지정하면 빈 공간을 모두 구리로 채운다. 이렇게 하면 GND 배선이 자동으로 되고, 방열과 노이즈 차폐 효과도 있다.

2레이어 PCB에서는 일반적으로:
- `F.Cu` (앞면): 신호 배선
- `B.Cu` (뒷면): GND 폴리곤

### 실크스크린

F.Silkscreen 레이어에 부품 레이블, 보드 이름, 버전, 날짜를 추가한다. 나중에 디버깅할 때 이 정보가 있으면 훨씬 편하다.

## Step 4: DRC 검사 및 Gerber 출력

### DRC (설계 규칙 검사)

Inspect → Design Rules Checker → Run. JLCPCB의 기본 제조 룰:
- 최소 배선 폭: 0.127mm (실용적으로는 0.2mm 이상 권장)
- 최소 패드 간격: 0.127mm
- 최소 드릴 직경: 0.2mm
- 보드 외곽은 Edge.Cuts 레이어에 닫힌 폴리라인으로

오류가 없으면 Gerber를 출력한다.

### Gerber 파일 출력

File → Fabrication Outputs → Gerbers → 출력 설정:

```
포함 레이어:
- F.Cu, B.Cu (앞뒤 구리)
- F.Paste, B.Paste (솔더 페이스트, SMD 있을 때)
- F.Silkscreen, B.Silkscreen (인쇄)
- F.Mask, B.Mask (솔더 마스크)
- Edge.Cuts (외곽선)

드릴 파일:
- Generate Drill Files → 동일 폴더에 저장
```

Gerber 파일들을 하나의 ZIP으로 묶어서 JLCPCB에 업로드하면 자동으로 파싱해서 미리보기를 보여준다. 이 미리보기를 꼭 확인하자.

## 주문 — JLCPCB 기준

JLCPCB에서 첫 PCB 주문 기준:
- 5장, 100×100mm 이하: $2 (배송비 별도)
- 기본 옵션: FR4, 1.6mm, 2레이어, HASL, 녹색
- 제조 기간: 약 24~48시간
- 배송 (EMS 기준): 7~10일

처음 해보면 박스 열 때의 설렘이 있다. 자기가 설계한 회로가 실물로 나왔을 때의 느낌은 코드 첫 실행과는 또 다른 쾌감이다.

## 내가 저지른 실수들

13년을 해온 나도 아직까지 가끔 저지르는 실수들:

1. **풋프린트 미러링**: 커넥터를 보드 뒷면에 배치할 때 미러링을 안 해서 방향이 반대로 나오는 경우. 뒷면 부품은 반드시 Mirror 체크.

2. **핀 1 방향**: IC의 핀 1 위치를 회로도와 풋프린트에서 맞추지 않아 반대로 납땜하는 실수. 납땜 전 데이터시트와 2~3번 확인.

3. **보드 두께와 커넥터 높이**: 스택 구조일 때 커넥터 높이 + 부품 높이를 계산하지 않아 다른 PCB와 충돌.

4. **GND 폴리곤 리프레시 안 함**: 배선을 수정한 후 폴리곤을 다시 채우지(Fill All Zones, 단축키 `B`) 않으면 Gerber에 이전 상태가 그대로 나온다.

5. **JLCPCB 드릴 레이어 좌표계**: Gerber와 드릴 파일의 좌표계가 다르면 홀 위치가 틀어진다. "Use Excellon format"과 "mm 단위" 설정을 맞출 것.

## 첫 PCB 이후

첫 PCB가 동작하는 순간, 두 번째 PCB 설계가 하고 싶어진다. 다음 단계로 추천하는 것들:

- **4레이어 PCB**: 전원/GND를 내부 레이어에 배치해 노이즈 특성이 크게 향상된다. 가격은 2레이어 대비 2~3배
- **임피던스 제어**: 고주파 신호(USB 3.0, MIPI 등)를 다룰 때 필수
- **부품 조립 서비스(PCBA)**: JLCPCB의 SMT 서비스를 쓰면 부품까지 실장해서 배송해준다. 솔더링이 귀찮은 부분을 맡길 수 있다

KiCad는 진입 장벽이 있지만 한번 넘으면 하드웨어를 보는 눈이 완전히 달라진다. 소프트웨어 엔지니어라도 PCB 한 장 만들어보길 강력히 추천한다.
