---
title: "NVIDIA GPU 컨트롤러 만들기 (4) — 커스텀 해상도와 디스플레이 타이밍 계산"
date: 2026-03-27T12:00:00+09:00
lastmod: 2026-03-27T12:00:00+09:00
description: "CVT, GTF 타이밍 공식으로 커스텀 해상도를 계산하고 NVAPI로 적용하는 과정. 디스플레이 타이밍의 모든 것을 다룹니다."
slug: "custom-display-resolution-timing"
categories: ["hardware-lab"]
tags: ["디스플레이", "해상도", "타이밍", "CVT", "GTF", "NVAPI", "C#"]
featureimage: "/images/posts/nvapi-gpu-controller/part4-timing-diagram.svg"
series: ["NVIDIA GPU 컨트롤러 개발기 2026"]
series_order: 4
draft: false
---

시리즈 앞 편에서 NVAPI 초기화와 GPU 정보 조회, EDID 읽기·쓰기를 다뤘다. 이번에는 프로젝트의 핵심 기능인 **커스텀 해상도**를 다룬다. 단순히 NVAPI 함수를 호출하는 것이 아니라, 모니터가 실제로 이해하는 언어인 **디스플레이 타이밍**을 직접 계산하고 적용하는 과정이다.

## 디스플레이 타이밍이란

모니터와 GPU는 픽셀 데이터를 주고받을 때 단순히 해상도 숫자만 교환하지 않는다. CRT 시대부터 이어진 아날로그 신호 규약이 디지털로 계승되면서, 화면을 구성하는 픽셀 외에도 일정한 **여백 구간(blanking)**이 존재한다.

![디스플레이 타이밍 구조](/images/posts/nvapi-gpu-controller/part4-timing-diagram.svg)

### 수평(Horizontal) 타이밍

한 라인을 전송하는 동안의 시간 구조다:

| 구간 | 역할 |
|------|------|
| **H Active** | 실제 화면에 표시되는 픽셀 (예: 1920) |
| **H Front Porch (HFP)** | 액티브 구간 종료 후 동기 펄스 전까지의 여백 |
| **H Sync Width (HSW)** | 동기 펄스 구간. 모니터가 라인 시작을 인식 |
| **H Back Porch (HBP)** | 동기 펄스 이후 다음 액티브 구간까지의 여백 |
| **H Total** | 위 4구간의 합 (예: 2200) |

### 수직(Vertical) 타이밍

프레임 단위의 구조는 수평과 동일한 패턴을 따른다:

| 구간 | 역할 |
|------|------|
| **V Active** | 실제 라인 수 (예: 1080) |
| **V Front Porch (VFP)** | 수직 방향 전면 포치 |
| **V Sync Width (VSW)** | 수직 동기 펄스 |
| **V Back Porch (VBP)** | 수직 방향 후면 포치 |
| **V Total** | 합계 (예: 1125) |

### 픽셀 클럭 공식

모든 타이밍의 기준이 되는 픽셀 클럭(Pixel Clock)은 다음으로 결정된다:

```
Pixel Clock (MHz) = H_Total × V_Total × Refresh Rate ÷ 1,000,000
```

1920×1080@60Hz의 실제 픽셀 클럭:
```
2200 × 1125 × 60 ÷ 1,000,000 = 148.5 MHz
```

NVAPI에서는 이 값을 **10kHz 단위**로 표현한다. 148.5 MHz = `14850`. `NvTiming.Pclk` 필드가 이 단위를 사용한다.

```csharp
[StructLayout(LayoutKind.Sequential)]
public struct NvTiming
{
    public ushort HVisible;      // H Active 픽셀 수
    public ushort HBorder;
    public ushort HFrontPorch;
    public ushort HSyncWidth;
    public ushort HTotal;
    public byte HSyncPol;        // 1 = Positive, 0 = Negative

    public ushort VVisible;      // V Active 라인 수
    public ushort VBorder;
    public ushort VFrontPorch;
    public ushort VSyncWidth;
    public ushort VTotal;
    public byte VSyncPol;

    public ushort Interlaced;
    public uint Pclk;            // 픽셀 클럭 (10kHz 단위)
    public NvTimingExt Etc;

    public double RefreshRate
    {
        get
        {
            if (HTotal == 0 || VTotal == 0) return 0;
            return (Pclk * 10000.0) / (HTotal * VTotal);
        }
    }
}
```

`RefreshRate` 속성은 역산으로 실제 주사율을 구한다. `Pclk × 10000`이 Hz 단위 픽셀 클럭이고 이를 `HTotal × VTotal`로 나누면 프레임레이트가 나온다.

---

## CVT v1.2 알고리즘

**CVT(Coordinated Video Timings)**는 VESA가 제정한 타이밍 계산 표준이다. LCD 시대에 맞게 설계됐으며, Standard와 Reduced Blanking 두 가지 변형이 있다.

![CVT vs GTF 알고리즘 비교](/images/posts/nvapi-gpu-controller/part4-cvt-gtf-flow.svg)

### CVT Standard Blanking

`TimingCalculator.CalculateCVT()` 메서드에서 `reducedBlanking = false`인 경우다:

```csharp
public static NvTiming CalculateCVT(int hActive, int vActive, double refreshRate,
    bool reducedBlanking = false)
{
    // CVT Standard Blanking
    double hPeriodEstimate = ((1000000.0 / refreshRate) - 550.0) / (vActive + 3);
    int vSyncWidth = GetVSyncWidth(hActive, vActive);
    int vFrontPorch = 3;
    int vBackPorch = (int)Math.Floor(550.0 / hPeriodEstimate) + 1;
    if (vBackPorch < 6) vBackPorch = 6;
    int vBlanking = vFrontPorch + vSyncWidth + vBackPorch;
    int vTotal = vActive + vBlanking;

    int idealDutyCycle = (int)(30.0 - (300000.0 * hPeriodEstimate / 1000000.0));
    if (idealDutyCycle < 20) idealDutyCycle = 20;

    int hBlanking = (int)(hActive * idealDutyCycle / (100.0 - idealDutyCycle));
    hBlanking = ((hBlanking / 16) + 1) * 16; // 16의 배수 (character cell)
    int hTotal = hActive + hBlanking;

    double pclk = (double)hTotal * vTotal * refreshRate / 1000000.0;
    pclk = Math.Ceiling(pclk * 4) / 4; // 0.25 MHz 단위로 올림

    int hSyncWidth = (int)(hTotal * 0.08);
    hSyncWidth = ((hSyncWidth / 8) + 1) * 8; // 8의 배수
    int hBackPorch = hBlanking / 2;
    int hFrontPorch = hBlanking - hSyncWidth - hBackPorch;

    timing.HSyncPol = 0; // Negative
    timing.VSyncPol = 1; // Positive
    timing.Pclk = (uint)(pclk * 100); // 10kHz 단위
```

핵심 공식들:

**수평 주기 추정:**
```
hPeriodEstimate = (1,000,000 / rr - 550) / (vActive + 3)   [단위: µs]
```
550µs는 수직 블랭킹 시간 추정값이다.

**이상적 수평 블랭킹 비율(duty cycle):**
```
idealDutyCycle = 30 - (300,000 × hPeriod / 1,000,000)   [단위: %]
```
최솟값은 20%. 이 공식이 해상도가 높을수록(주기가 짧을수록) 블랭킹 비율이 낮아지는 특성을 반영한다.

**hBlanking 계산:**
```
hBlanking = hActive × duty / (100 - duty)
→ 16의 배수로 올림 (character cell alignment)
```

**동기 폭과 포치:**
```
hSyncWidth = hTotal × 8%  → 8의 배수
hBackPorch = hBlanking ÷ 2
hFrontPorch = hBlanking - hSyncWidth - hBackPorch
```

### CVT Reduced Blanking

LCD 모니터에서 블랭킹을 최소화해 대역폭을 아끼는 방식이다. 특히 고주사율 커스텀 해상도에 적합하다:

```csharp
if (reducedBlanking)
{
    // 수평 블랭킹은 고정값
    int hBlank = 80;
    int hFrontPorch = 48;
    int hSyncWidth = 32;

    int vMinPorch = 3;
    int vSyncWidth = GetVSyncWidth(hActive, vActive);
    int vFrontPorch = vMinPorch;

    double hPeriod = (1000000.0 / refreshRate - 460.0) / (vActive + vFrontPorch + vSyncWidth);
    int vBackPorch = (int)Math.Round(460.0 / hPeriod);
    if (vBackPorch < 6) vBackPorch = 6;

    timing.HSyncPol = 1; // Positive (Standard와 반대!)
    timing.VSyncPol = 0; // Negative
```

RB의 특징:
- **hBlank = 80픽셀** 고정 (Standard는 수백 픽셀)
- **hFP=48, hSW=32** 고정
- 동기 극성이 Standard와 **반대** (HSyn+, VSyn-)
- 픽셀 클럭이 낮아져 HDMI/DP 대역폭 절약

### 화면 비율별 V Sync Width

`GetVSyncWidth`는 화면 비율에 따라 수직 동기 폭을 결정한다. VESA 규격을 따른다:

```csharp
private static int GetVSyncWidth(int hActive, int vActive)
{
    double ratio = (double)hActive / vActive;
    if (Math.Abs(ratio - 4.0 / 3.0) < 0.1) return 4;   // 4:3
    if (Math.Abs(ratio - 16.0 / 9.0) < 0.1) return 5;  // 16:9
    if (Math.Abs(ratio - 16.0 / 10.0) < 0.1) return 6; // 16:10
    if (Math.Abs(ratio - 5.0 / 4.0) < 0.1) return 7;   // 5:4
    if (Math.Abs(ratio - 15.0 / 9.0) < 0.1) return 7;  // 15:9
    if (Math.Abs(ratio - 21.0 / 9.0) < 0.1) return 5;  // 21:9
    return 5; // 기본값
}
```

---

## GTF 알고리즘

**GTF(Generalized Timing Formula)**는 CVT 이전에 VESA가 제정한 구형 표준이다. CRT 모니터의 물리적 특성을 수식으로 모델링한다. 레거시 모니터 호환성이 필요할 때 사용한다.

```csharp
public static NvTiming CalculateGTF(int hActive, int vActive, double refreshRate)
{
    // GTF 상수 (VESA 규격 고정값)
    const double MIN_PORCH = 1;
    const double V_SYNC_RQD = 3;
    const double H_SYNC_PCT = 8.0;
    const double MIN_V_BACK_PORCH = 550.0; // µs
    const double M = 600.0;
    const double C = 40.0;
    const double K = 128.0;
    const double J = 20.0;

    double CPrime = ((C - J) * K / 256.0) + J;   // = 30.0
    double MPrime = K / 256.0 * M;                // = 300.0
```

GTF의 핵심은 C'와 M' 상수다. 이 값들은 CRT 빔의 되돌아오기(retrace) 속도를 모델링한 경험적 상수다.

**수직 블랭킹 계산:**
```
hPeriodEstimate = (1/rr - 550µs) / (vActive + vFP + vSW)
vBackPorch = 550µs ÷ hPeriod
```

**수평 duty cycle:**
```
idealDutyCycle = C' - M' × hPeriod(µs) / 1000
               = 30 - 300 × hPeriod / 1000
```

GTF와 CVT Standard의 수식은 비슷해 보이지만 계산 경로가 다르다. GTF는 `hPeriod`를 먼저 정확히 계산한 뒤 픽셀 클럭을 역산하는 반면, CVT는 이상적인 pclk를 먼저 추정한다.

```csharp
    // GTF: hPeriod로 pclk 역산
    double pclk = (double)hTotal / (hPeriodEstimate * 1000000.0) / 1000000.0;

    // 10kHz 단위 변환
    timing.Pclk = (uint)(pclk * 100000000.0 / 10000.0);
```

GTF는 항상 HSyn-, VSyn+ 극성을 사용한다.

---

## 수동 타이밍

CVT/GTF 계산 결과를 사용자가 직접 수정하거나, 모니터 데이터시트의 타이밍을 그대로 입력할 때는 수동 모드를 사용한다:

```csharp
public static NvTiming CreateManualTiming(
    int hActive, int hFrontPorch, int hSyncWidth, int hTotal,
    int vActive, int vFrontPorch, int vSyncWidth, int vTotal,
    double pixelClockMHz, bool hSyncPositive, bool vSyncPositive)
{
    var timing = NvTiming.Create();
    timing.HVisible = (ushort)hActive;
    timing.HFrontPorch = (ushort)hFrontPorch;
    timing.HSyncWidth = (ushort)hSyncWidth;
    timing.HTotal = (ushort)hTotal;
    timing.HSyncPol = (byte)(hSyncPositive ? 1 : 0);
    // ... 수직도 동일
    timing.Pclk = (uint)(pixelClockMHz * 100); // 10kHz 단위
    return timing;
}
```

UI의 `Custom ResolutionPanel`에서 `cboTimingMode`가 "Manual"이면 사용자가 각 값을 직접 `numHFP`, `numHSW`, `numHTotal`, `numVFP`, `numVSW`, `numVTotal`, `numPixelClock` 에 입력한다.

---

## NvCustomDisplay 구조체

계산된 타이밍을 NVAPI에 전달하려면 `NvCustomDisplay` 구조체에 담아야 한다:

```csharp
[StructLayout(LayoutKind.Sequential)]
public struct NvCustomDisplay
{
    public uint Version;
    public uint Width;           // 해상도 너비
    public uint Height;          // 해상도 높이
    public uint Depth;           // 색 심도 (보통 32)
    public uint ColorFormat;     // 색상 포맷
    public NvViewportF SourcePartition; // 소스 파티션 (보통 전체: 0,0,1,1)
    public float XRatio;         // 스케일 비율 (보통 1.0)
    public float YRatio;
    public NvTiming Timing;      // 타이밍 파라미터
    public uint HwModeSetOnly;   // 0: 영구 적용, 1: 하드웨어 모드만

    public static NvCustomDisplay Create()
    {
        var cd = new NvCustomDisplay();
        cd.Version = (uint)(Marshal.SizeOf(typeof(NvCustomDisplay)) | (1 << 16));
        cd.Timing = NvTiming.Create();
        cd.SourcePartition = new NvViewportF { X = 0, Y = 0, W = 1.0f, H = 1.0f };
        cd.XRatio = 1.0f;
        cd.YRatio = 1.0f;
        return cd;
    }
}
```

`Version` 필드는 NVAPI의 공통 패턴으로, 구조체 크기와 버전 번호를 비트 합산한 값이다. `HwModeSetOnly = 0`이면 Windows 디스플레이 드라이버 모델(WDDM)에도 등록되고, `1`이면 하드웨어 레지스터만 변경해 빠르지만 재부팅 후 초기화된다.

---

## TryCustomDisplay vs SaveCustomDisplay

커스텀 해상도 적용은 두 단계로 나뉜다.

### 1단계: TryCustomDisplay — 임시 적용

```csharp
public static NvStatus TryCustomResolution(uint displayId,
    uint width, uint height, uint depth, uint colorFormat, NvTiming timing)
{
    // 주사율 계산 후 NvTimingExt에 저장
    if (timing.HTotal > 0 && timing.VTotal > 0 && timing.Pclk > 0)
    {
        double hz = (timing.Pclk * 10000.0) / (timing.HTotal * timing.VTotal);
        timing.Etc.Rr = (ushort)Math.Round(hz);
        timing.Etc.Rrx1k = (uint)Math.Round(hz * 1000.0);
    }

    var cd = NvCustomDisplay.Create();
    cd.Width = width;
    cd.Height = height;
    cd.Depth = depth;
    cd.ColorFormat = colorFormat;
    cd.Timing = timing;
    cd.HwModeSetOnly = 0;

    var ids = new uint[] { displayId };
    var displays = new NvCustomDisplay[] { cd };

    var status = NvApiWrapper.DISP_TryCustomDisplay(ids, 1, displays);
```

`TryCustomDisplay`는 해상도를 즉시 적용하되 **NVAPI 내부 임시 상태**로만 보존한다. 드라이버가 재시작되거나 `RevertCustomDisplay`를 호출하면 원래대로 돌아온다. UI에서 "Test (15s)" 버튼이 이 경로를 사용한다.

`NvTimingExt.Rr`은 Hz 정수, `Rrx1k`는 0.001Hz 단위다. 두 필드를 모두 채워야 드라이버가 올바른 주사율을 인식한다.

### 2단계: SaveCustomDisplay — 영구 저장

```csharp
public static NvStatus SaveCustomResolution(uint displayId, NvDisplayHandle displayHandle)
{
    var ids = new uint[] { displayId };
    NvStatus status;

    // 시도 1: displayId + (0,0)
    status = NvApiWrapper.DISP_SaveCustomDisplay(ids, 1, 0, 0);
    if (status == NvStatus.OK) { Logger.Info("Saved via displayId (0,0)"); return status; }

    // 시도 2: displayId + (1,0)
    status = NvApiWrapper.DISP_SaveCustomDisplay(ids, 1, 1, 0);
    if (status == NvStatus.OK) { Logger.Info("Saved via displayId (1,0)"); return status; }

    // 시도 3~4: NvDisplayHandle로 재시도
    if (displayHandle.IsValid)
    {
        var handles = new NvDisplayHandle[] { displayHandle };
        status = NvApiWrapper.DISP_SaveCustomDisplayByHandle(handles, 1, 0, 0);
        if (status == NvStatus.OK) return status;

        status = NvApiWrapper.DISP_SaveCustomDisplayByHandle(handles, 1, 1, 0);
        if (status == NvStatus.OK) return status;
    }
```

`SaveCustomDisplay`의 세 번째·네 번째 인자는 NVAPI 문서에도 정확한 의미가 명시되지 않은 플래그다. 실험적으로 `(0,0)`, `(1,0)` 조합을 순서대로 시도하며, DisplayId와 DisplayHandle 두 가지 API 오버로드를 모두 거친다. 드라이버 버전마다 동작이 다를 수 있어 이런 폴백 체인이 필요하다.

저장된 커스텀 해상도는 드라이버 재시작 후에도 유지되며, Windows 디스플레이 설정 앱에서도 선택 가능해진다.

---

## 해상도 되돌리기 (Revert Safety)

커스텀 해상도가 모니터와 맞지 않으면 화면이 완전히 꺼질 수 있다. 이 때문에 "Test" 기능에는 자동 복귀 타이머가 붙어 있다:

```csharp
// BtnTest_Click 에서:
revertCountdown = 15;
revertTimer.Start();
btnSave.Enabled = false;

private void RevertTimer_Tick(object sender, EventArgs e)
{
    revertCountdown--;
    lblStatus.Text = $"테스트 중... {revertCountdown}초 후 자동 복귀";
    if (revertCountdown <= 0)
    {
        revertTimer.Stop();
        NvCustomDisplayManager.RevertCustomResolution(displayId);
    }
}
```

`RevertCustomResolution`은 두 단계 폴백 전략을 사용한다:

```csharp
public static NvStatus RevertCustomResolution(uint displayId)
{
    // 1차: NVAPI RevertCustomDisplay
    var ids = new uint[] { displayId };
    var status = NvApiWrapper.DISP_RevertCustomDisplay(ids, 1);
    if (status == NvStatus.OK)
    {
        Logger.Info("Custom display reverted via NVAPI");
        return status;
    }

    // 2차 폴백: Windows ChangeDisplaySettingsEx
    Logger.Warn("NVAPI RevertCustomDisplay not available, using Windows API fallback");
    int result = ChangeDisplaySettingsExA(null, IntPtr.Zero, IntPtr.Zero, 0, IntPtr.Zero);
    if (result == 0) // DISP_CHANGE_SUCCESSFUL
    {
        Logger.Info("Display reverted via Windows API");
        return NvStatus.OK;
    }
```

NVAPI `DISP_RevertCustomDisplay`가 실패하면 Win32 `ChangeDisplaySettingsEx`를 `null` 디바이스명, 빈 `DEVMODE`로 호출해 OS 기본 해상도로 강제 복귀한다. 화면이 안 보이는 상황에서도 15초 후 자동으로 원상복구되므로 사용자가 맹목적으로 기다릴 필요가 없다.

---

## 대역폭 계산

커스텀 해상도가 인터페이스 한계를 초과하면 화면이 출력되지 않는다. 사전 검증을 위해:

![대역폭 계산 공식과 인터페이스 한계](/images/posts/nvapi-gpu-controller/part4-bandwidth-calc.svg)

```csharp
public static double CalculateBandwidthGbps(int hTotal, int vTotal,
    double refreshRate, int bitsPerPixel)
{
    return (double)hTotal * vTotal * refreshRate * bitsPerPixel / 1000000000.0;
}
```

**주의**: `hActive`, `vActive`가 아니라 **`hTotal`, `vTotal`** (blanking 포함)을 사용한다. 인터페이스는 blanking 구간에도 클럭을 유지하기 때문이다.

실용 한계:

| 인터페이스 | 대역폭 | 실용 한계 |
|-----------|--------|----------|
| HDMI 1.4 | 10.2 Gbps | 1080p 144Hz 또는 4K 30Hz (8bpc) |
| HDMI 2.0 | 18 Gbps | 4K 60Hz (8bpc) |
| HDMI 2.1 | 48 Gbps | 4K 144Hz, 8K 60Hz |
| DP 1.4 | 32.4 Gbps | 4K 120Hz (DSC 적용 시 더 높음) |
| DP 2.0 | 80 Gbps | 16K급 |

10bpc(HDR)는 8bpc보다 25% 더 많은 대역폭이 필요하다. 4K 60Hz를 HDMI 2.0으로 10bpc로 출력하려면 `14.256 × (30/24) = 17.82 Gbps`로 한계에 근접한다.

---

## 타이밍 오버라이드 모드

NVAPI는 타이밍 생성 방식을 `NvTimingOverride` 열거형으로 지정할 수 있다:

```csharp
public enum NvTimingOverride : int
{
    Current  = 0,   // 현재 설정 유지
    Auto     = 1,   // 드라이버 자동 선택
    EDID     = 2,   // 모니터 EDID의 타이밍
    DMT      = 3,   // VESA DMT 표준 타이밍
    DMTRb    = 4,   // DMT Reduced Blanking
    CVT      = 5,   // CVT Standard
    CVTRb    = 6,   // CVT Reduced Blanking
    GTF      = 7,   // GTF
    EIA861   = 8,   // CEA/EIA-861 (HDMI 표준 타이밍)
    AnalogTV = 9,   // 아날로그 TV
    CEA861CVT = 10,
    AsiaTV   = 11,  // 아시아 TV 규격
    Custom   = 255, // 완전 수동 타이밍
}
```

커스텀 해상도를 적용할 때는 `NvTimingOverride.Custom`을 사용한다. 이 모드에서는 드라이버가 타이밍을 자체 계산하지 않고 우리가 채운 `NvTiming` 구조체 값을 그대로 하드웨어에 전달한다.

---

## 프리셋 관리

자주 사용하는 해상도 설정은 CSV 파일로 저장·불러온다:

```csharp
private string _presetsPath = Path.Combine(
    AppDomain.CurrentDomain.BaseDirectory, "presets.csv");

private List<ResolutionPreset> _presets = new List<ResolutionPreset>();
```

`ResolutionPreset`은 해상도, 주사율, 타이밍 파라미터, 픽셀 클럭을 하나의 레코드로 묶는다. UI 우측 패널의 `DataGridView`에 표시되며, 더블클릭하면 해당 설정이 좌측 입력 폼에 자동으로 채워진다.

```csharp
private void DgvPresets_CellDoubleClick(object sender, DataGridViewCellEventArgs e)
{
    // 선택한 프리셋을 폼에 로드
    var preset = GetSelectedPreset();
    if (preset == null) return;

    numWidth.Value = preset.Width;
    numHeight.Value = preset.Height;
    numRefresh.Value = (decimal)preset.RefreshRate;
    numPixelClock.Value = (decimal)preset.PixelClockMHz;
    numHFP.Value = preset.HFrontPorch;
    // ...
}
```

---

## EDID DetailedTimingDescriptor 변환

계산된 `NvTiming`은 EDID 형식으로도 변환할 수 있다. 3편에서 다룬 EDID 쓰기 기능과 연동할 때 사용한다:

```csharp
public static DetailedTimingDescriptor ToDetailedTiming(NvTiming timing)
{
    int hBlanking = timing.HTotal - timing.HVisible;
    int vBlanking = timing.VTotal - timing.VVisible;

    return new DetailedTimingDescriptor
    {
        PixelClockKHz10 = (ushort)timing.Pclk,
        HActive = timing.HVisible,
        HBlanking = hBlanking,
        VActive = timing.VVisible,
        VBlanking = vBlanking,
        HFrontPorch = timing.HFrontPorch,
        HSyncWidth = timing.HSyncWidth,
        VFrontPorch = timing.VFrontPorch,
        VSyncWidth = timing.VSyncWidth,
        Features = (byte)((timing.HSyncPol != 0 ? 0x02 : 0)
                        | (timing.VSyncPol != 0 ? 0x04 : 0) | 0x18)
    };
}
```

`Features` 바이트는 EDID 규격에서 동기 극성 비트를 담는다. `0x18`은 디지털 신호(separate sync)를 나타내는 기본 플래그다.

---

## 실제 사용 흐름 정리

1. **UI에서 해상도·주사율·타이밍 모드 선택**
2. **Calculate 버튼** → `TimingCalculator.CalculateCVT()` 또는 `CalculateGTF()` 호출, 결과를 폼에 표시
3. **Test (15s) 버튼** → `TryCustomResolution()`, 15초 후 자동 복귀
4. 화면이 정상이면 **Save 버튼** → `SaveCustomResolution()` (4가지 방법 폴백)
5. 문제가 생기면 **Restore Original** → `RevertCustomResolution()` 즉시 호출

핵심은 "적용 → 검증 → 저장" 3단계 분리다. 모니터가 지원하지 않는 타이밍을 실수로 저장하는 상황을 원천 차단한다.

---

## 마치며

디스플레이 타이밍은 겉으로 보이는 해상도 숫자 뒤에 숨겨진 복잡한 세계다. CVT와 GTF는 수십 년간 쌓인 디스플레이 엔지니어링 경험의 결정체이며, NVAPI는 이를 드라이버 수준에서 직접 제어할 수 있는 창구를 제공한다.

다음 5편에서는 이 커스텀 해상도 기능에 색 공간 제어(Color Space, HDR)를 결합해, 동일한 NVAPI로 SDR과 HDR을 전환하는 방법을 다룬다.

---

**시리즈 목차**
- (1) [프로젝트 개요와 NVAPI 아키텍처](/posts/hardware-lab/nvapi-gpu-controller-architecture/)
- (2) [GPU 열거와 모니터 연결 감지](/posts/hardware-lab/nvapi-gpu-enumeration-monitor-detection/)
- (3) [EDID 읽기·쓰기와 커스텀 EDID 주입](/posts/hardware-lab/nvapi-edid-read-write-custom-injection/)
- **(4) 커스텀 해상도와 디스플레이 타이밍 계산** ← 현재
- (5) 색 공간 제어와 HDR 전환 (예정)
