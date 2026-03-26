---
title: "NVIDIA GPU 컨트롤러 만들기 (1) — NVAPI 초기화와 프로젝트 아키텍처"
date: 2026-03-27T09:00:00+09:00
lastmod: 2026-03-27T09:00:00+09:00
description: "C#과 NVAPI를 활용한 NVIDIA GPU 컨트롤러 개발 시리즈. 첫 번째 편에서는 프로젝트 아키텍처와 NVAPI 초기화 과정을 다룹니다."
slug: "nvapi-gpu-controller-architecture-setup"
categories: ["hardware-lab"]
tags: ["NVAPI", "NVIDIA", "GPU", "C#", "WinForms", "P/Invoke", ".NET"]
featureimage: "/images/posts/nvapi-gpu-controller/part1-architecture.svg"
series: ["NVIDIA GPU 컨트롤러 개발기 2026"]
series_order: 1
draft: false
---

NVIDIA GPU를 프로그래밍 방식으로 제어하고 싶다는 생각은 꽤 오래 됐다. 모니터 EDID를 직접 읽고 쓰고, 커스텀 해상도를 주입하고, 색공간 설정을 코드 한 줄로 바꾸는 것. GeForce Experience나 NVIDIA 제어판에 의존하지 않고 내가 원하는 타이밍에 원하는 설정을 GPU에 직접 넣는 도구가 필요했다.

결과물이 **NvGpuController** — C# WinForms(.NET 4.7.2)로 만든 NVIDIA GPU 컨트롤 애플리케이션이다. 이 시리즈에서는 이 앱을 처음부터 만들어가는 과정을 기록한다. 1편에서는 왜 NVAPI를 골랐는지, 어떻게 프로젝트를 구성했는지, 그리고 NVAPI의 독특한 초기화 메커니즘을 C# P/Invoke로 어떻게 뚫었는지 다룬다.

## 왜 NVAPI인가

NVIDIA GPU를 제어하는 공개된 방법은 몇 가지가 있다.

- **DXGI / D3D API** — 디스플레이 어댑터 열거, 모드 설정 가능. 하지만 EDID 읽기/쓰기나 커스텀 타이밍 주입은 불가.
- **Windows CCD API** (`SetDisplayConfig`) — 해상도·주사율 변경 가능. 그러나 커스텀 타이밍을 정밀하게 제어하기 어렵다.
- **NVAPI** — NVIDIA 전용 SDK. GPU 물리 정보, EDID 읽기/쓰기, 커스텀 해상도 주입, 색공간 제어까지 모두 지원한다. 단, Windows 전용이고 NVIDIA GPU에만 동작한다.

요구사항 자체가 "NVIDIA GPU + EDID + 커스텀 타이밍"이었으므로 NVAPI 외에 선택지가 없었다.

### NVAPI의 특이한 점

NVAPI는 일반적인 Win32 API나 COM 인터페이스와 구조가 다르다. **헤더 파일(.h)이 공개되어 있지만 실제 함수 심볼은 DLL에 export되어 있지 않다.** 대신 단 하나의 export 함수 `nvapi_QueryInterface`만 존재하고, 나머지 모든 함수는 **32비트 정수 ID**를 이 QueryInterface에 넘겨서 함수 포인터를 얻는 방식으로 동작한다.

```
nvapi64.dll exports:
  nvapi_QueryInterface(uint functionId) -> void*
  (그 외에는 아무것도 없음)
```

이 설계 덕분에 NVIDIA는 드라이버를 업데이트할 때 ABI를 깨지 않고 함수 구현을 교체할 수 있다. 하지만 C#에서 P/Invoke로 연결할 때는 기존 `[DllImport]` 패턴과는 다른 접근이 필요하다.

## 프로젝트 아키텍처

![전체 레이어드 아키텍처](/images/posts/nvapi-gpu-controller/part1-architecture.svg)

NvGpuController는 4개 레이어로 구성된다.

| 레이어 | 네임스페이스 | 역할 |
|---|---|---|
| UI | `NvGpuController.UI` | WinForms 화면, 사용자 입력 처리 |
| 비즈니스 로직 | `NvGpuController` | GPU/EDID/커스텀 해상도 제어 흐름 |
| 코어 / 인프라 | `NvGpuController.Core` | Logger, 공통 유틸 |
| NVAPI 래퍼 | `NvGpuController.NVAPI` | P/Invoke, 타입 정의, 마샬링 |

UI는 비즈니스 로직만 알고, 비즈니스 로직은 NVAPI 래퍼만 호출한다. UI가 직접 `NvApiWrapper`를 건드리는 일은 없다.

### 디렉토리 구조

```
NvGpuController/
├── Core/
│   └── Logger.cs          # 전역 로거
├── EDID/                  # EDID 파싱 (2편에서 다룸)
├── NVAPI/
│   ├── NvApiTypes.cs      # 구조체, 열거형 정의
│   └── NvApiWrapper.cs    # P/Invoke 래퍼 (핵심)
├── UI/
│   └── MainForm.cs        # 메인 화면
├── Program.cs             # 진입점, 예외 처리
└── NvGpuController.csproj
```

## Logger — 간결하지만 충분한 진단 도구

NVAPI 작업을 할 때 가장 중요한 것은 어떤 함수가 어떤 상태 코드를 반환했는지 추적하는 일이다. `Logger`는 이를 위해 설계된 스레드 안전한 정적 로거다.

```csharp
// Core/Logger.cs
public static class Logger
{
    public static event Action<string> OnLog;

    private static readonly ConcurrentQueue<string> _logBuffer
        = new ConcurrentQueue<string>();

    public static void Log(string message)
    {
        string entry = $"[{DateTime.Now:HH:mm:ss.fff}] {message}";
        _logBuffer.Enqueue(entry);
        OnLog?.Invoke(entry);
    }

    public static void Info(string message)  => Log($"[INFO] {message}");
    public static void Error(string message) => Log($"[ERROR] {message}");
    public static void Warn(string message)  => Log($"[WARN] {message}");

    public static void NvApiCall(string funcName, int status)
    {
        string level = status == 0 ? "OK" : $"FAIL(0x{status:X})";
        Log($"[NVAPI] {funcName} -> {level}");
    }

    public static string[] GetAllLogs() => _logBuffer.ToArray();
}
```

핵심은 `NvApiCall` 메서드다. NVAPI 함수 이름과 반환된 `NvStatus` 정수값을 받아서 성공/실패를 한 줄로 기록한다. 실패 시 16진수로 에러 코드를 출력해서 NVAPI 문서와 대조하기 쉽게 했다.

`ConcurrentQueue`를 쓴 이유는 WinForms 백그라운드 스레드(예: `Task.Run` 안에서 GPU 폴링)에서도 안전하게 로그를 남기기 위해서다. `OnLog` 이벤트를 통해 UI의 로그 뷰어가 실시간으로 메시지를 받아서 표시한다.

## Program.cs — 예외 안전망

WinForms 앱에서 P/Invoke 코드가 잘못된 포인터나 잘못된 구조체 크기를 넘기면 `AccessViolationException`이나 `SEHException`이 발생한다. 이런 예외가 UI 스레드에서 발생하면 앱이 그냥 죽어버린다.

```csharp
[STAThread]
static void Main()
{
    Application.EnableVisualStyles();
    Application.SetCompatibleTextRenderingDefault(false);

    Application.ThreadException += Application_ThreadException;
    AppDomain.CurrentDomain.UnhandledException += CurrentDomain_UnhandledException;
    Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);

    Application.Run(new UI.MainForm());
}

private static void Application_ThreadException(object sender, ThreadExceptionEventArgs e)
{
    Logger.Error($"Unhandled UI exception: {e.Exception.Message}");
    MessageBox.Show(
        $"An error occurred:\n\n{e.Exception.Message}\n\nThe application will try to continue.",
        "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
}
```

`Application.ThreadException`은 UI 스레드의 예외를 잡고, `AppDomain.CurrentDomain.UnhandledException`은 백그라운드 스레드의 예외를 잡는다. Logger에 기록하고 사용자에게 메시지를 보여준 후 앱이 계속 실행되도록 한다(치명적이지 않은 경우).

## NvApiTypes.cs — C 구조체를 C#으로

NVAPI는 C 기반이다. C#에서 사용하려면 C 구조체를 `[StructLayout]` 어트리뷰트로 정확히 매핑해야 한다. 메모리 레이아웃이 조금만 틀려도 드라이버가 잘못된 데이터를 읽어 시스템이 불안정해진다.

### NvStatus 열거형

```csharp
public enum NvStatus : int
{
    OK                      = 0,
    Error                   = -1,
    LibraryNotFound         = -2,
    NoImplementation        = -3,
    ApiNotInitialized       = -4,
    InvalidArgument         = -5,
    NvidiaDeviceNotFound    = -6,
    EndEnumeration          = -7,
    InvalidHandle           = -8,
    IncompatibleStructVersion = -9,
    // ...
    ExpectedPhysicalGpuHandle = -101,
    ExpectedDisplayHandle     = -102,
}
```

`NvStatus`는 `int`로 선언한다. NVAPI 함수는 성공 시 0, 실패 시 음수를 반환한다. `EndEnumeration(-7)`은 열거가 끝났다는 신호로, 에러가 아니라 루프 종료 조건이다.

### 구조체 버전 관리 패턴

NVAPI 구조체는 대부분 첫 4바이트가 `Version` 필드다. 이 필드에 구조체 크기와 API 버전 번호를 인코딩해서 넘겨야 드라이버가 올바른 버전으로 처리한다.

```csharp
[StructLayout(LayoutKind.Sequential)]
public struct NvGpuThermalSettings
{
    public uint Version;
    public uint Count;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 3)]
    public NvThermalSensor[] Sensors;

    public static NvGpuThermalSettings Create()
    {
        var s = new NvGpuThermalSettings();
        // 하위 16비트: 구조체 크기, 상위 16비트: API 버전 (v2)
        s.Version = (uint)(Marshal.SizeOf(typeof(NvGpuThermalSettings)) | (2 << 16));
        s.Sensors = new NvThermalSensor[3];
        return s;
    }
}
```

패턴: `Version = (size) | (apiVersion << 16)`. 이 인코딩 방식은 모든 NVAPI 구조체에 공통으로 쓰인다. `Create()` 정적 팩토리 메서드를 만들어두면 호출 측에서 버전 계산 실수를 방지할 수 있다.

### NvEdidV3 — EDID 읽기/쓰기용 구조체

```csharp
[StructLayout(LayoutKind.Sequential)]
public struct NvEdidV3
{
    public uint Version;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 256)]
    public byte[] EdidData;   // EDID 바이트 배열 (최대 256바이트)
    public uint EdidSize;     // 실제 EDID 데이터 크기
    public uint EdidId;       // 출력 ID (읽기 시 자동 설정)
    public uint Offset;       // 멀티 블록 EDID용 오프셋

    public static NvEdidV3 Create()
    {
        var e = new NvEdidV3();
        e.Version = (uint)(Marshal.SizeOf(typeof(NvEdidV3)) | (3 << 16));
        e.EdidData = new byte[256];
        return e;
    }
}
```

### NvColorControlV5 — 명시적 레이아웃

컬러 제어 구조체는 `[StructLayout(LayoutKind.Explicit)]`으로 각 필드의 오프셋을 바이트 단위로 지정한다. 컴파일러 패딩을 신뢰할 수 없기 때문이다.

```csharp
[StructLayout(LayoutKind.Explicit, Size = 16)]
public struct NvColorControlV5
{
    [FieldOffset(0)]  public uint Version;         // 4바이트
    [FieldOffset(4)]  public ushort Size;           // 2바이트
    [FieldOffset(6)]  public NvColorCmd Cmd;        // 1바이트
    [FieldOffset(7)]  public NvColorFormat ColorFormat; // 1바이트
    [FieldOffset(8)]  public byte Colorimetry;
    [FieldOffset(9)]  public NvDynamicRange DynamicRange;
    [FieldOffset(10)] public NvColorDepth ColorDepth;
    [FieldOffset(11)] public NvColorSelectionPolicy SelectionPolicy;
    [FieldOffset(12)] public byte ColorSpaceId;
    // 13~15: 패딩 (Size = 16으로 고정)
}
```

드라이버 버전에 따라 V1(12바이트), V3(12바이트), V5(16바이트)를 지원해야 한다. 각각 별도 구조체로 정의하고 버전에 따라 적절한 것을 선택해서 사용한다.

## NvApiWrapper.cs — P/Invoke의 핵심

이제 핵심이다. NVAPI를 C#에서 어떻게 초기화하는지 단계별로 살펴본다.

![NVAPI 초기화 시퀀스](/images/posts/nvapi-gpu-controller/part1-nvapi-init-flow.svg)

### 1단계: nvapi_QueryInterface DLL Import

```csharp
[DllImport("nvapi64.dll",
    EntryPoint = "nvapi_QueryInterface",
    CallingConvention = CallingConvention.Cdecl)]
private static extern IntPtr NvAPI64_QueryInterface(uint id);

[DllImport("nvapi.dll",
    EntryPoint = "nvapi_QueryInterface",
    CallingConvention = CallingConvention.Cdecl)]
private static extern IntPtr NvAPI32_QueryInterface(uint id);

private static bool _is64Bit = IntPtr.Size == 8;

private static IntPtr QueryInterface(uint id)
{
    return _is64Bit
        ? NvAPI64_QueryInterface(id)
        : NvAPI32_QueryInterface(id);
}
```

64비트/32비트 프로세스에 따라 다른 DLL을 호출한다. `IntPtr.Size == 8`이면 64비트다. `CallingConvention.Cdecl`은 NVAPI DLL이 C 호출 규약을 사용하기 때문에 필수다.

### 2단계: 함수 ID 상수 정의

각 NVAPI 함수에는 고유한 32비트 ID가 있다. 이 값은 공개 NVAPI SDK의 헤더 파일에서 가져온다.

```csharp
// 주요 함수 ID
private const uint ID_Initialize           = 0x0150E828;
private const uint ID_Unload               = 0xD22BDD7E;
private const uint ID_GetErrorMessage      = 0x6C2D048C;
private const uint ID_EnumPhysicalGPUs     = 0xE5AC921F;
private const uint ID_GPU_GetFullName      = 0xCEEE8E9F;
private const uint ID_GPU_GetEDID          = 0x37D32E69;
private const uint ID_GPU_SetEDID          = 0xE83D6456;
private const uint ID_GPU_GetThermalSettings = 0xE3640A56;
private const uint ID_DISP_ColorControl    = 0x92F9D80D;
// ... 총 21개
```

이 ID는 드라이버 버전이 바뀌어도 변하지 않는다. NVIDIA의 안정성 보장이다.

### 3단계: 델리게이트 타입 선언

![P/Invoke 래퍼 패턴](/images/posts/nvapi-gpu-controller/part1-pinvoke-pattern.svg)

각 NVAPI 함수의 서명을 C# `delegate`로 선언한다. `[UnmanagedFunctionPointer(CallingConvention.Cdecl)]` 어트리뷰트가 필수다.

```csharp
[UnmanagedFunctionPointer(CallingConvention.Cdecl)]
private delegate NvStatus NvAPI_Initialize_t();

[UnmanagedFunctionPointer(CallingConvention.Cdecl)]
private delegate NvStatus NvAPI_EnumPhysicalGPUs_t(
    [Out] NvPhysicalGpuHandle[] handles, out uint count);

[UnmanagedFunctionPointer(CallingConvention.Cdecl)]
private delegate NvStatus NvAPI_GPU_GetEDID_t(
    NvPhysicalGpuHandle handle, uint outputId, ref NvEdidV3 edid);

[UnmanagedFunctionPointer(CallingConvention.Cdecl)]
private delegate NvStatus NvAPI_GPU_GetThermalSettings_t(
    NvPhysicalGpuHandle handle, int sensorIndex,
    ref NvGpuThermalSettings settings);
```

`ref` 파라미터는 C의 포인터에 대응한다. 구조체를 값으로 넘기는 게 아니라 주소를 넘기는 것이다.

### 4단계: GetDelegate 제네릭 헬퍼

QueryInterface 호출과 델리게이트 변환을 하나의 메서드로 묶었다.

```csharp
private static T GetDelegate<T>(uint id) where T : class
{
    IntPtr ptr = QueryInterface(id);
    if (ptr == IntPtr.Zero)
        return null;
    return Marshal.GetDelegateForFunctionPointer(ptr, typeof(T)) as T;
}
```

`QueryInterface(id)`가 `IntPtr.Zero`를 반환하면 해당 함수를 드라이버가 지원하지 않는다는 뜻이다. 이 경우 `null`을 반환하고, 래퍼 메서드들은 `null` 체크 후 `NvStatus.NoImplementation`을 반환한다.

### 5단계: Initialize() 호출

```csharp
public static NvStatus Initialize()
{
    try
    {
        _Initialize = GetDelegate<NvAPI_Initialize_t>(ID_Initialize);
        if (_Initialize == null)
        {
            Logger.Error("NVAPI: nvapi_QueryInterface failed for Initialize");
            return NvStatus.LibraryNotFound;
        }

        NvStatus status = _Initialize();
        Logger.NvApiCall("NvAPI_Initialize", (int)status);

        if (status == NvStatus.OK)
        {
            _initialized = true;
            LoadDelegates();  // 나머지 21개 델리게이트 로드
        }

        return status;
    }
    catch (DllNotFoundException)
    {
        Logger.Error("NVAPI: nvapi64.dll / nvapi.dll not found.");
        return NvStatus.LibraryNotFound;
    }
    catch (Exception ex)
    {
        Logger.Error($"NVAPI: Initialize exception: {ex.Message}");
        return NvStatus.Error;
    }
}
```

에러 경로가 세 가지다:
1. DLL 자체가 없는 경우 (`DllNotFoundException`) — NVIDIA 드라이버 미설치
2. QueryInterface가 `null` 반환 — DLL은 있지만 함수 ID를 인식 못 함
3. `_Initialize()` 호출 결과가 `OK`가 아님 — 드라이버 내부 초기화 실패

### 6단계: LoadDelegates() — 나머지 함수 포인터 일괄 로드

```csharp
private static void LoadDelegates()
{
    _Unload = GetDelegate<NvAPI_Unload_t>(ID_Unload);
    _GetErrorMessage = GetDelegate<NvAPI_GetErrorMessage_t>(ID_GetErrorMessage);
    _EnumPhysicalGPUs = GetDelegate<NvAPI_EnumPhysicalGPUs_t>(ID_EnumPhysicalGPUs);
    _GPU_GetFullName = GetDelegate<NvAPI_GPU_GetFullName_t>(ID_GPU_GetFullName);
    _GPU_GetPhysicalFrameBufferSize = GetDelegate<NvAPI_GPU_GetPhysicalFrameBufferSize_t>(
        ID_GPU_GetPhysicalFrameBufferSize);
    _GPU_GetThermalSettings = GetDelegate<NvAPI_GPU_GetThermalSettings_t>(
        ID_GPU_GetThermalSettings);
    _GPU_GetAllClockFrequencies = GetDelegate<NvAPI_GPU_GetAllClockFrequencies_t>(
        ID_GPU_GetAllClockFrequencies);
    _GPU_GetEDID = GetDelegate<NvAPI_GPU_GetEDID_t>(ID_GPU_GetEDID);
    _GPU_SetEDID = GetDelegate<NvAPI_GPU_SetEDID_t>(ID_GPU_SetEDID);
    // ... 총 21개 델리게이트 로드

    Logger.Info("NVAPI: All delegates loaded");
}
```

초기화 성공 후 한 번만 호출된다. 이후 모든 NVAPI 함수 호출은 캐시된 델리게이트를 통해 이루어진다. QueryInterface를 매번 호출하는 오버헤드가 없다.

## 래퍼 메서드 패턴

래퍼 메서드들은 모두 같은 패턴을 따른다.

```csharp
public static NvStatus GPU_GetFullName(
    NvPhysicalGpuHandle handle, out string name)
{
    name = "";
    if (_GPU_GetFullName == null) return NvStatus.NoImplementation;

    var str = new NvShortString();
    var status = _GPU_GetFullName(handle, ref str);
    Logger.NvApiCall("NvAPI_GPU_GetFullName", (int)status);
    name = str.ToString();
    return status;
}
```

1. `out` 파라미터를 기본값으로 초기화
2. 델리게이트 `null` 체크
3. NVAPI 호출
4. 결과 로깅
5. 변환 후 반환

`NvShortString`은 64바이트 고정 길이 ANSI 문자열을 담는 구조체다.

```csharp
[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]
public struct NvShortString
{
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 64)]
    public string Value;

    public override string ToString() => Value ?? string.Empty;
}
```

`UnmanagedType.ByValTStr`와 `SizeConst = 64`는 마샬러에게 64바이트 고정 버퍼에서 null 종단 문자열을 읽으라는 지시다.

## 컬러 컨트롤의 특별한 케이스

대부분의 NVAPI 함수는 타입이 고정된 구조체를 받지만, `NvAPI_DISP_ColorControl`은 드라이버 버전에 따라 다른 구조체(V1/V3/V5)를 받는다. 이 경우 타입이 고정된 델리게이트를 쓸 수 없어 `IntPtr` 기반 래 raw 델리게이트를 사용했다.

```csharp
[UnmanagedFunctionPointer(CallingConvention.Cdecl)]
private delegate NvStatus NvAPI_DISP_ColorControl_Raw_t(
    uint displayId, IntPtr colorData);

public static NvStatus DISP_ColorControlV5(
    uint displayId, ref NvColorControlV5 cc)
{
    // 델리게이트 초기화 (최초 1회)
    if (_DISP_ColorControl_Raw == null)
    {
        var ptr = QueryInterface(ID_DISP_ColorControl);
        if (ptr == IntPtr.Zero) return NvStatus.NoImplementation;
        _DISP_ColorControl_Raw = Marshal.GetDelegateForFunctionPointer(
            ptr, typeof(NvAPI_DISP_ColorControl_Raw_t))
            as NvAPI_DISP_ColorControl_Raw_t;
    }

    // 비관리 힙에 구조체 복사 → NVAPI 호출 → 결과 읽기
    IntPtr mem = Marshal.AllocHGlobal(16);
    try
    {
        Marshal.StructureToPtr(cc, mem, false);
        var status = _DISP_ColorControl_Raw(displayId, mem);
        cc = (NvColorControlV5)Marshal.PtrToStructure(
            mem, typeof(NvColorControlV5));
        Logger.NvApiCall(
            $"ColorControl_v5({cc.Cmd}, depth={cc.ColorDepth})",
            (int)status);
        return status;
    }
    finally
    {
        Marshal.FreeHGlobal(mem);  // 반드시 해제
    }
}
```

`Marshal.AllocHGlobal`로 비관리 힙에 16바이트를 할당하고, 구조체를 복사한 후 포인터를 NVAPI에 전달한다. NVAPI가 버퍼를 채우면 `Marshal.PtrToStructure`로 다시 구조체로 읽어온다. `finally`에서 반드시 해제해야 메모리 누수가 없다.

V3(12바이트)와 V1(12바이트)도 같은 패턴, 크기만 다르다.

## GPU 열거 예시 — 전체 흐름 확인

초기화 후 GPU 목록을 가져오는 코드로 전체 흐름을 확인한다.

```csharp
// 초기화
var status = NvApiWrapper.Initialize();
if (status != NvStatus.OK)
{
    Logger.Error($"NVAPI 초기화 실패: {status}");
    return;
}

// GPU 열거
status = NvApiWrapper.EnumPhysicalGPUs(out var handles, out uint count);
if (status != NvStatus.OK) return;

for (uint i = 0; i < count; i++)
{
    NvApiWrapper.GPU_GetFullName(handles[i], out string name);
    NvApiWrapper.GPU_GetPhysicalFrameBufferSize(handles[i], out uint sizeKB);
    NvApiWrapper.GPU_GetBusId(handles[i], out uint busId);

    Console.WriteLine($"[{i}] {name}");
    Console.WriteLine($"    VRAM: {sizeKB / 1024} MB, Bus ID: {busId}");
}
```

로그 출력 예:
```
[09:00:00.123] [NVAPI] NvAPI_Initialize -> OK
[09:00:00.124] [INFO] NVAPI: All delegates loaded
[09:00:00.125] [NVAPI] NvAPI_EnumPhysicalGPUs -> OK
[09:00:00.126] [NVAPI] NvAPI_GPU_GetFullName -> OK
[09:00:00.127] [NVAPI] NvAPI_GPU_GetPhysicalFrameBufferSize -> OK
[09:00:00.128] [NVAPI] NvAPI_GPU_GetBusId -> OK
```

각 NVAPI 호출마다 함수 이름과 결과가 로그에 찍힌다. 문제가 생겼을 때 어느 단계에서 실패했는지 즉시 알 수 있다.

## 다음 편 예고

1편에서는 왜 NVAPI를 선택했는지, 프로젝트 구조는 어떻게 잡았는지, 그리고 NVAPI의 독특한 QueryInterface 기반 초기화를 C# P/Invoke로 구현하는 방법을 상세히 살펴봤다.

다음 편에서는 이 인프라 위에서 **EDID 읽기와 파싱**을 구현한다. `NvAPI_GPU_GetEDID`로 원시 바이트를 가져온 다음 EDID 표준 구조(Base Block, Extension Block)를 파싱해서 모니터 이름, 지원 해상도, 타이밍 정보를 추출하는 과정을 다룬다.

---

**시리즈 전체 구성**

1. **NVAPI 초기화와 프로젝트 아키텍처** (현재)
2. EDID 읽기와 파싱 — 모니터 정보 추출
3. EDID 쓰기 — 커스텀 EDID 주입
4. 커스텀 해상도 — TryCustomDisplay와 타이밍 계산
5. 컬러 컨트롤 — RGB/YUV, 비트 깊이, HDR 설정
