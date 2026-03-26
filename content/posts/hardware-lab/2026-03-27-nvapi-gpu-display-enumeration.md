---
title: "NVIDIA GPU 컨트롤러 만들기 (2) — GPU 정보 조회와 디스플레이 열거"
date: 2026-03-27T10:00:00+09:00
lastmod: 2026-03-27T10:00:00+09:00
description: "NVAPI를 통한 GPU 정보 조회, 디스플레이 열거, 모니터 식별까지. GPU 컨트롤러의 핵심 데이터 수집 과정을 상세히 다룹니다."
slug: "nvapi-gpu-display-enumeration"
categories: ["hardware-lab"]
tags: ["NVAPI", "NVIDIA", "GPU", "디스플레이", "모니터", "C#"]
featureimage: "/images/posts/nvapi-gpu-controller/part2-gpu-enum-flow.svg"
series: ["NVIDIA GPU 컨트롤러 개발기 2026"]
series_order: 2
draft: false
---

1편에서 NVAPI 래퍼 레이어를 구성하고 `NvApiWrapper`를 통해 네이티브 함수들을 C#으로 끌어들이는 방법을 살펴봤다. 이번 편에서는 그 래퍼를 실제로 활용하는 두 개의 핵심 모듈을 집중적으로 다룬다. 하나는 GPU 하드웨어 정보를 수집하는 `NvGpuInfo`, 다른 하나는 연결된 디스플레이 전체를 열거하고 모니터 이름까지 찾아내는 `NvDisplay`다.

이 두 클래스가 만들어내는 데이터 구조체 — `GpuInfoData`, `DisplayInfo`, `DriverInfo` — 가 컨트롤러 전체에서 공유되는 핵심 모델이다.

## GPU 열거: NvPhysicalGpuHandle 배열부터 시작

![GPU 열거 및 정보 수집 흐름](/images/posts/nvapi-gpu-controller/part2-gpu-enum-flow.svg)

NVAPI에서 GPU를 다루는 출발점은 언제나 물리 GPU 핸들(`NvPhysicalGpuHandle`) 배열을 얻는 것이다. `NvGpuInfo.EnumerateGPUs()`는 이 단계부터 시작해 필요한 모든 속성을 순차적으로 채운다.

```csharp
public static List<GpuInfoData> EnumerateGPUs()
{
    var result = new List<GpuInfoData>();

    NvPhysicalGpuHandle[] handles;
    uint count;
    if (NvApiWrapper.EnumPhysicalGPUs(out handles, out count) != NvStatus.OK)
        return result;

    for (int i = 0; i < count; i++)
    {
        var info = new GpuInfoData
        {
            Index = i,
            Handle = handles[i]
        };
        // ... 속성 채우기
        result.Add(info);
    }
    return result;
}
```

`EnumPhysicalGPUs`는 내부적으로 `NvAPI_EnumPhysicalGPUs`를 호출하며, 시스템에 설치된 NVIDIA GPU 핸들을 최대 64개까지 배열로 반환한다. SLI 구성이나 멀티-GPU 워크스테이션에서는 여러 핸들이 올 수 있지만, 일반 데스크탑 환경에서는 대부분 1개다.

중요한 점은 `NvStatus.OK`가 아닌 경우 즉시 빈 리스트를 반환한다는 것이다. NVAPI가 초기화되지 않았거나 드라이버가 없는 환경에서는 이 시점에 실패한다.

## GPU 속성 수집: 8가지 API 호출

핸들을 얻은 뒤 각 GPU에 대해 8가지 속성을 차례로 조회한다. 각 호출은 독립적으로 실패를 처리하므로, 일부 속성이 지원되지 않아도 나머지는 정상적으로 채워진다.

### 이름과 VRAM

```csharp
string name;
if (NvApiWrapper.GPU_GetFullName(handles[i], out name) == NvStatus.OK)
    info.Name = name;

uint vram;
if (NvApiWrapper.GPU_GetPhysicalFrameBufferSize(handles[i], out vram) == NvStatus.OK)
    info.VramSizeKB = vram;
```

`GPU_GetFullName`은 "NVIDIA GeForce RTX 4090"처럼 마케팅 이름을 반환한다. `GPU_GetPhysicalFrameBufferSize`는 실제 물리 VRAM 크기를 **킬로바이트 단위**로 반환하는데, 이 때문에 `GpuInfoData`에는 편의용 계산 프로퍼티를 두 가지 만들었다.

```csharp
public string VramSizeMB => $"{VramSizeKB / 1024} MB";
public string VramSizeGB => $"{VramSizeKB / 1024 / 1024.0:F1} GB";
```

24GB VRAM이라면 내부적으로는 `25165824`(KB)가 저장되고, `VramSizeGB`는 `"24.0 GB"`를 반환한다.

### VBIOS 버전

```csharp
string vbios;
if (NvApiWrapper.GPU_GetVbiosVersionString(handles[i], out vbios) == NvStatus.OK)
    info.VbiosVersion = vbios;
```

VBIOS 버전은 "96.00.89.00.67"처럼 점으로 구분된 문자열 형태다. 오버클럭 카드나 특수 제조사 바이오스에서는 일반 레퍼런스 카드와 다른 버전이 나온다. 이 값은 GPU-Z 같은 도구에서 보여주는 것과 동일하다.

### 온도 센서

```csharp
NvGpuThermalSettings thermal;
if (NvApiWrapper.GPU_GetThermalSettings(handles[i], out thermal) == NvStatus.OK
    && thermal.Count > 0)
    info.Temperature = thermal.Sensors[0].CurrentTemp;
```

`NvGpuThermalSettings`는 최대 3개의 `NvThermalSensor`를 담을 수 있다. 각 센서에는 `Target`(GPU, Memory, PowerSupply, Board), `CurrentTemp`, `DefaultMinTemp`, `DefaultMaxTemp`가 있다.

```csharp
public struct NvGpuThermalSettings
{
    public uint Version;
    public uint Count;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 3)]
    public NvThermalSensor[] Sensors;
}
```

`Version` 필드 구성 방식이 NVAPI 구조체 전반에서 쓰이는 관례인데, 크기와 버전 번호를 하나의 uint에 비트 연산으로 담는다.

```csharp
s.Version = (uint)(Marshal.SizeOf(typeof(NvGpuThermalSettings)) | (2 << 16));
```

상위 16비트가 버전(여기서는 2), 하위 16비트가 구조체 크기다. NVAPI가 이 필드를 검증해서 버전 불일치 시 `NvStatus.IncompatibleStructVersion`을 반환한다.

### 버스 정보

```csharp
uint busId;
if (NvApiWrapper.GPU_GetBusId(handles[i], out busId) == NvStatus.OK)
    info.BusId = busId;

NvGpuBusType busType;
if (NvApiWrapper.GPU_GetBusType(handles[i], out busType) == NvStatus.OK)
    info.BusType = busType;
```

`NvGpuBusType` 열거형에는 `PCIExpress = 3`이 현대 GPU의 표준이다. `BusId`는 Windows 장치 관리자에서 보이는 PCI 슬롯 번호와 대응한다.

### 클럭 주파수

클럭 조회는 두 번 수행한다. 현재 동작 주파수와 부스트 클럭을 각각 얻기 위해서다.

```csharp
NvGpuClockFrequencies clocks;
if (NvApiWrapper.GPU_GetAllClockFrequencies(handles[i],
        NvClockType.CurrentFreq, out clocks) == NvStatus.OK)
{
    if (clocks.Domain[(int)NvClockDomain.Graphics].bIsPresent != 0)
        info.GraphicsClockMHz =
            clocks.Domain[(int)NvClockDomain.Graphics].freq_kHz / 1000;
    if (clocks.Domain[(int)NvClockDomain.Memory].bIsPresent != 0)
        info.MemoryClockMHz =
            clocks.Domain[(int)NvClockDomain.Memory].freq_kHz / 1000;
}
if (NvApiWrapper.GPU_GetAllClockFrequencies(handles[i],
        NvClockType.BoostClock, out clocks) == NvStatus.OK)
{
    if (clocks.Domain[(int)NvClockDomain.Graphics].bIsPresent != 0)
        info.BoostClockMHz =
            clocks.Domain[(int)NvClockDomain.Graphics].freq_kHz / 1000;
}
```

`NvGpuClockFrequencies`는 32개의 `NvClockEntry` 배열을 담는다. 각 도메인(Graphics=0, Memory=4, Video=8)에 대한 항목이 존재하는지 `bIsPresent`로 확인한 뒤, `freq_kHz`를 1000으로 나눠 MHz로 변환한다. GPU 상태에 따라 현재 클럭은 게이밍 중에는 부스트 클럭에 가까운 값이, 유휴 상태에서는 기저 클럭보다 낮은 값이 나온다.

## GpuInfoData: 결과 데이터 클래스

![데이터 클래스 관계도](/images/posts/nvapi-gpu-controller/part2-data-classes.svg)

모든 속성을 담는 `GpuInfoData`의 전체 구조다.

```csharp
public class GpuInfoData
{
    public int Index { get; set; }
    public NvPhysicalGpuHandle Handle { get; set; }
    public string Name { get; set; } = "";
    public uint VramSizeKB { get; set; }
    public string VbiosVersion { get; set; } = "";
    public int Temperature { get; set; }
    public uint BusId { get; set; }
    public NvGpuBusType BusType { get; set; }
    public NvGpuType GpuType { get; set; }
    public uint GraphicsClockMHz { get; set; }
    public uint MemoryClockMHz { get; set; }
    public uint BoostClockMHz { get; set; }

    public string VramSizeMB => $"{VramSizeKB / 1024} MB";
    public string VramSizeGB => $"{VramSizeKB / 1024 / 1024.0:F1} GB";
}
```

`Handle`을 데이터 클래스에 보관하는 이유가 있다. 이후의 EDID 읽기, 커스텀 해상도 API, 색상 제어 API는 전부 `NvPhysicalGpuHandle`을 필요로 한다. DisplayPanel에서 디스플레이를 선택했을 때 연결된 GPU 핸들을 즉시 꺼내 쓸 수 있도록 여기 포함시켜 뒀다.

## 디스플레이 열거: 두 가지 ID 체계

![디스플레이 계층 구조](/images/posts/nvapi-gpu-controller/part2-display-hierarchy.svg)

디스플레이 열거는 GPU 열거보다 복잡하다. NVAPI에는 디스플레이를 식별하는 방법이 두 가지 있는데, 용도가 다르다.

- **OutputId**: EDID 읽기 / 쓰기에 사용하는 비트마스크 방식 식별자
- **DisplayId**: 커스텀 해상도 API(`NvAPI_DISP_TryCustomDisplay` 등)에 사용하는 정수 식별자

`NvDisplay.EnumerateDisplays()`는 둘 다 수집한다.

```csharp
public static List<DisplayInfo> EnumerateDisplays()
{
    var result = new List<DisplayInfo>();

    NvPhysicalGpuHandle[] gpuHandles;
    uint gpuCount;
    NvApiWrapper.EnumPhysicalGPUs(out gpuHandles, out gpuCount);

    for (uint i = 0; i < 32; i++)
    {
        NvDisplayHandle handle;
        var status = NvApiWrapper.EnumNvidiaDisplayHandle(i, out handle);
        if (status != NvStatus.OK)
            break;

        var info = new DisplayInfo { Index = (int)i, Handle = handle };
        // ...
    }
    return result;
}
```

디스플레이는 인덱스 0부터 시작해 `NvStatus.OK`가 아닌 결과가 나올 때까지 순회한다. 최대 32를 상한으로 잡아 무한 루프를 방지한다. `NvStatus.EndEnumeration`이나 그 외 오류 코드를 받으면 루프를 종료한다.

### OutputId와 DeviceName 획득

```csharp
string devName;
if (NvApiWrapper.GetAssociatedNvidiaDisplayName(handle, out devName) == NvStatus.OK)
    info.DeviceName = devName;

uint outputId;
if (NvApiWrapper.GetAssociatedDisplayOutputId(handle, out outputId) == NvStatus.OK)
    info.OutputId = outputId;
```

`DeviceName`은 Windows가 붙이는 논리 디스플레이 이름으로, `\\.\DISPLAY1`, `\\.\DISPLAY2` 같은 형태다. 이 문자열은 뒤에서 `EnumDisplaySettings`를 호출할 때 그대로 전달한다.

`OutputId`는 GPU의 물리 출력 포트와 1:1 매핑된다. 비트 단위로 인코딩되어 있어 다중 디스플레이 환경에서 각 포트를 구별하는 데 쓰인다.

### DisplayId 획득

```csharp
uint displayId;
if (NvApiWrapper.DISP_GetDisplayIdByDisplayName(info.DeviceName, out displayId) == NvStatus.OK)
    info.DisplayId = displayId;
```

`DeviceName` 문자열을 넘기면 NVAPI 내부에서 해당 디스플레이의 `DisplayId`를 반환한다. 이 값은 3편에서 다룰 커스텀 해상도 기능(`NvAPI_DISP_TryCustomDisplay`, `NvAPI_DISP_SaveCustomDisplay`)에서 핵심 인자로 쓰인다.

## 모니터 이름 찾기: 3단계 전략

디스플레이 목록에서 사용자에게 의미 있는 이름을 보여주려면 단순한 `\\.\DISPLAY1`이 아닌 "SAMSUNG", "LG ULTRAGEAR" 같은 실제 모니터 이름이 필요하다. 이를 위해 세 가지 방법을 순서대로 시도한다.

### 1단계: EDID에서 직접 읽기

```csharp
if (info.GpuHandle.IsValid && info.OutputId != 0)
{
    try
    {
        byte[] edidData;
        if (NvEdid.ReadEDID(info.GpuHandle, info.OutputId, out edidData) == NvStatus.OK
            && edidData != null)
        {
            var parsed = EDID.EdidParser.Parse(edidData);
            if (!string.IsNullOrEmpty(parsed.MonitorName))
                info.MonitorName = parsed.MonitorName;
            else
                info.MonitorName = parsed.ManufacturerId;
        }
    }
    catch { }
}
```

EDID 블록에는 모니터 제조사가 설정한 이름이 Monitor Name Descriptor(태그 0xFC)로 저장되어 있다. `EdidParser.Parse()`가 이 필드를 추출한다. 이름이 없으면 3바이트 제조사 코드(`ManufacturerId`, 예: "SAM", "LGD")를 대신 사용한다.

`GpuHandle.IsValid`와 `OutputId != 0`을 모두 확인하는 것은 방어적 체크다. 핸들이 유효하지 않거나 OutputId가 0이면 NVAPI 호출이 실패하거나 잘못된 데이터를 반환할 수 있다.

### 2단계: Windows EnumDisplayDevices 폴백

```csharp
if (string.IsNullOrEmpty(info.MonitorName))
{
    try
    {
        info.MonitorName = GetMonitorFriendlyName(info.DeviceName);
    }
    catch { }
}
```

EDID 읽기가 실패한 경우(모니터가 연결되지 않은 가상 디스플레이, 일부 도킹 스테이션 등) Windows API로 폴백한다.

```csharp
[DllImport("user32.dll", CharSet = CharSet.Ansi)]
private static extern bool EnumDisplayDevicesA(
    string lpDevice, uint iDevNum,
    ref DISPLAY_DEVICE lpDisplayDevice, uint dwFlags);

private static string GetMonitorFriendlyName(string deviceName)
{
    if (string.IsNullOrEmpty(deviceName)) return "";
    var dd = new DISPLAY_DEVICE();
    dd.cb = Marshal.SizeOf(typeof(DISPLAY_DEVICE));
    if (EnumDisplayDevicesA(deviceName, 0, ref dd, 1))
        return dd.DeviceString;
    return "";
}
```

`EnumDisplayDevicesA`에 디스플레이 어댑터 이름을 넘기면 연결된 모니터의 `DeviceString`을 반환한다. 이 값은 Windows 디스플레이 설정에서 보이는 모니터 이름과 동일하다.

### 3단계: DisplayInfo.Name 계산 프로퍼티

```csharp
public string Name =>
    !string.IsNullOrEmpty(MonitorName)
        ? $"{MonitorName} ({DeviceName})"
        : DeviceName;
```

최종적으로 UI에서 쓰이는 `Name` 프로퍼티는 모니터 이름이 있으면 `"SAMSUNG (\\.\DISPLAY1)"`, 없으면 `"\\.\DISPLAY1"`을 반환한다. 이 값이 `DisplayPanel`의 트리뷰에 표시된다.

## 현재 해상도: Windows EnumDisplaySettings

NVAPI에도 디스플레이 해상도를 조회하는 함수가 있지만, 현재 설정을 단순히 읽는 용도라면 Windows API `EnumDisplaySettingsA`가 더 직접적이다.

```csharp
[DllImport("user32.dll", CharSet = CharSet.Ansi)]
private static extern bool EnumDisplaySettingsA(
    string lpszDeviceName, int iModeNum, ref DEVMODE lpDevMode);

// iModeNum = -1 은 ENUM_CURRENT_SETTINGS

try
{
    var devMode = new DEVMODE();
    devMode.dmSize = (short)Marshal.SizeOf(typeof(DEVMODE));
    if (EnumDisplaySettingsA(info.DeviceName, -1, ref devMode))
    {
        info.CurrentWidth = devMode.dmPelsWidth;
        info.CurrentHeight = devMode.dmPelsHeight;
        info.CurrentRefreshRate = devMode.dmDisplayFrequency;
        info.CurrentBitsPerPixel = devMode.dmBitsPerPel;
    }
}
catch { }
```

`iModeNum`에 `-1`(ENUM_CURRENT_SETTINGS)을 전달하면 현재 활성 모드를 반환한다. `DEVMODE` 구조체의 `dmSize` 필드를 반드시 초기화해야 하며, 그렇지 않으면 API 호출이 실패한다.

`CurrentResolution` 계산 프로퍼티가 이 값들을 사람이 읽기 좋은 형태로 조합한다.

```csharp
public string CurrentResolution =>
    CurrentWidth > 0
        ? $"{CurrentWidth}x{CurrentHeight} @ {CurrentRefreshRate}Hz"
        : "Unknown";
```

## DriverInfo: 드라이버 버전 조회

드라이버 정보는 GPU 핸들과 무관하게 시스템 전체에서 하나다.

```csharp
public static DriverInfo GetDriverInfo()
{
    var info = new DriverInfo();
    uint version;
    string branch;
    if (NvApiWrapper.SYS_GetDriverAndBranchVersion(out version, out branch) == NvStatus.OK)
    {
        info.DriverVersion = version;
        info.Branch = branch;
    }
    return info;
}
```

`DriverVersion`은 정수로 인코딩된 버전 번호다. `VersionString` 계산 프로퍼티가 이를 익숙한 형태로 변환한다.

```csharp
public string VersionString => $"{DriverVersion / 100}.{DriverVersion % 100:D2}";
```

드라이버 버전 57283이면 `572.83`이 된다. `Branch`는 "r572_10"처럼 NVIDIA 내부 브랜치 이름이다. 두 자리 수 보장을 위해 `:D2` 포맷 지정자를 쓴다.

## DisplayInfo: 디스플레이 데이터 클래스 전체

```csharp
public class DisplayInfo
{
    public int Index { get; set; }
    public NvDisplayHandle Handle { get; set; }
    public string DeviceName { get; set; } = "";   // \\.\DISPLAY1
    public string MonitorName { get; set; } = "";  // "SAMSUNG" 등
    public uint OutputId { get; set; }             // EDID API 키
    public NvPhysicalGpuHandle GpuHandle { get; set; }
    public string GpuName { get; set; } = "";
    public uint DisplayId { get; set; }            // 커스텀 해상도 API 키
    public int CurrentWidth { get; set; }
    public int CurrentHeight { get; set; }
    public int CurrentRefreshRate { get; set; }
    public int CurrentBitsPerPixel { get; set; }

    public string Name =>
        !string.IsNullOrEmpty(MonitorName)
            ? $"{MonitorName} ({DeviceName})"
            : DeviceName;

    public string CurrentResolution =>
        CurrentWidth > 0
            ? $"{CurrentWidth}x{CurrentHeight} @ {CurrentRefreshRate}Hz"
            : "Unknown";
}
```

`GpuHandle`과 `GpuName`을 DisplayInfo에 저장하는 이유는 `DisplayPanel`에서 EDID 읽기를 할 때 해당 디스플레이가 어느 GPU에 연결되어 있는지를 알아야 하기 때문이다. `NvEdid.ReadEDID(gpuHandle, outputId, out data)` 시그니처가 GPU 핸들을 요구한다.

현재 구현에서는 `gpuHandles[0]`을 항상 사용하는 단순화가 있다. 멀티-GPU 환경에서는 각 디스플레이를 어느 GPU에서 구동하는지 정확히 매핑해야 하지만, 단일 GPU가 대부분인 현실적 사용 환경에서는 충분한 구현이다.

## UI 바인딩: GpuInfoPanel

`GpuInfoPanel`은 `NvGpuInfo.EnumerateGPUs()`의 결과를 `ListView`로 표시하는 `UserControl`이다.

```csharp
public void LoadData(List<GpuInfoData> gpus)
{
    listView.Items.Clear();

    for (int i = 0; i < gpus.Count; i++)
    {
        var gpu = gpus[i];
        if (i > 0) AddItem("", "");
        AddItem($"=== GPU #{i} ===", "");
        AddItem("Name", gpu.Name);
        AddItem("Type", gpu.GpuType.ToString());
        AddItem("VRAM", gpu.VramSizeGB);
        AddItem("VBIOS Version", gpu.VbiosVersion);
        AddItem("Temperature", $"{gpu.Temperature} C");
        AddItem("Graphics Clock", $"{gpu.GraphicsClockMHz} MHz");
        AddItem("Memory Clock", $"{gpu.MemoryClockMHz} MHz");
        AddItem("Boost Clock", $"{gpu.BoostClockMHz} MHz");
        AddItem("Bus ID", $"{gpu.BusId}");
        AddItem("Bus Type", gpu.BusType.ToString());
    }
}
```

`===` 로 시작하는 항목은 시각적 구분을 위해 어두운 배경색으로 표시한다.

```csharp
private void AddItem(string prop, string value)
{
    var item = new ListViewItem(prop);
    item.SubItems.Add(value);
    if (prop.StartsWith("==="))
    {
        item.BackColor = Color.FromArgb(60, 60, 65);
        item.ForeColor = Color.White;
    }
    listView.Items.Add(item);
}
```

`Refresh` 버튼 핸들러는 단순히 `EnumerateGPUs()`를 재호출하고 `LoadData()`에 넘기는 것으로 끝난다. 온도와 클럭은 실시간 값이므로 새로고침할 때마다 현재 값을 반영한다.

## UI 바인딩: DisplayPanel

`DisplayPanel`은 트리뷰(좌측) + 상세 정보 리스트(우측 상단) + EDID 헥스 덤프(우측 하단)의 3분할 레이아웃이다.

```csharp
public void LoadData(List<DisplayInfo> displays, List<GpuInfoData> gpus)
{
    _displays = displays;
    _gpus = gpus;
    treeView.Nodes.Clear();

    foreach (var display in displays)
    {
        var node = treeView.Nodes.Add($"Display {display.Index}: {display.Name}");
        node.Tag = display;
        node.Nodes.Add($"Resolution: {display.CurrentResolution}");
        node.Nodes.Add($"Output ID: 0x{display.OutputId:X}");
        node.Nodes.Add($"GPU: {display.GpuName}");
    }

    if (displays.Count > 0)
    {
        treeView.ExpandAll();
        treeView.SelectedNode = treeView.Nodes[0];
    }
}
```

각 노드의 `Tag`에 `DisplayInfo` 객체를 저장해 두는 것이 핵심이다. 트리뷰에서 노드를 선택했을 때 이 태그를 꺼내 상세 정보를 표시한다.

```csharp
private void TreeView_AfterSelect(object sender, TreeViewEventArgs e)
{
    var node = e.Node;
    while (node.Parent != null) node = node.Parent;
    var display = node.Tag as DisplayInfo;
    if (display == null) return;

    ShowDisplayDetail(display);
}
```

자식 노드(Resolution, Output ID 등)를 클릭해도 `while (node.Parent != null)` 루프로 최상위 노드까지 거슬러 올라가 `DisplayInfo`를 꺼낸다. 이렇게 하면 트리의 어느 노드를 클릭해도 해당 디스플레이의 상세 정보가 표시된다.

`ShowDisplayDetail`에서는 EDID 읽기까지 수행해 파싱 결과를 상세 리스트에 추가하고, 원시 바이트는 헥스 덤프로 표시한다. EDID 파싱 결과 분석은 다음 편에서 별도로 다룬다.

## OutputId: 비트마스크의 의미

`OutputId`가 단순한 인덱스가 아닌 비트마스크라는 점은 처음 보면 의아할 수 있다. 예를 들어 4포트 GPU에서 첫 번째 포트가 `0x00000001`, 두 번째가 `0x00000002`, 세 번째가 `0x00000004` 식으로 인코딩된다. 이런 방식은 NVAPI 내부에서 다수의 출력을 동시에 지정할 때(멀티-스트림, SLI 등) 비트 OR 연산으로 합칠 수 있게 설계된 것이다.

실제로 `NvAPI_GPU_GetEDID`를 호출할 때는 이 `OutputId`를 그대로 전달하면 되고, NVAPI가 내부적으로 어느 물리 포트인지 해석한다. `DisplayId`와 `OutputId`를 혼용하면 API가 `NvStatus.InvalidArgument`를 반환하므로 어떤 API에 어떤 식별자를 써야 하는지 구분해야 한다.

## 다음 편 예고

데이터 수집 파이프라인이 완성됐다. `List<GpuInfoData>`와 `List<DisplayInfo>`를 얻을 수 있게 됐으니, 이제 EDID 블록의 구체적인 파싱 로직을 살펴볼 차례다.

3편에서는 `EdidParser`가 128바이트 EDID 베이스 블록을 어떻게 해독하는지, Detailed Timing Descriptor(DTD)와 Monitor Descriptor의 구조, 그리고 CTA-861 확장 블록에 담긴 HDR 메타데이터와 VIC 코드 파싱까지 다룬다.
