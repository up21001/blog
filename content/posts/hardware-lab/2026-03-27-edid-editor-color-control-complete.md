---
title: "NVIDIA GPU 컨트롤러 만들기 (5) — EDID 편집기와 색상 제어 완성"
date: 2026-03-27T13:00:00+09:00
lastmod: 2026-03-27T13:00:00+09:00
description: "EDID 편집기 구현과 색상 제어 기능으로 GPU 컨트롤러를 완성합니다. 시리즈 최종편에서 전체 아키텍처를 돌아봅니다."
slug: "edid-editor-color-control-complete"
categories: ["hardware-lab"]
tags: ["EDID", "색상제어", "GPU", "NVAPI", "C#", "WinForms"]
featureimage: "/images/posts/nvapi-gpu-controller/part5-complete-app.svg"
series: ["NVIDIA GPU 컨트롤러 개발기 2026"]
series_order: 5
draft: false
---

시리즈 마지막 편입니다. 지금까지 NVAPI 초기화, GPU/디스플레이 정보 조회, 커스텀 해상도까지 다뤘습니다. 이번에는 프로젝트의 하이라이트인 **EDID 편집기**와 **색상 제어**를 구현하고, 전체 애플리케이션을 완성합니다.

---

## EDID 편집이란 무엇인가

EDID(Extended Display Identification Data)는 모니터가 자신의 특성을 그래픽 카드에 알려주는 128바이트(확장 시 256바이트+) 구조체입니다. 연결 즉시 DDC/CI 채널을 통해 자동으로 교환되며, GPU 드라이버는 이 데이터를 기반으로 지원 해상도, 색 깊이, HDR 여부 등을 결정합니다.

EDID를 편집해야 하는 이유는 다양합니다:

- 모니터가 거짓말을 한다 — 일부 저가 모니터는 지원하지 않는 기능을 EDID에 선언
- KVM 스위치나 HDMI 분배기가 EDID를 날려버린다
- 특정 해상도/주사율 조합을 강제로 등록해야 한다
- HDR 관련 플래그를 수동으로 조정하고 싶다

NVAPI는 `NvAPI_GPU_GetEDID` / `NvAPI_GPU_SetEDID` 함수를 제공해 GPU 드라이버 수준에서 EDID를 읽고 오버라이드할 수 있게 해줍니다.

---

## EdidEditor 클래스 설계

`EdidEditor`는 128바이트 원시 배열을 래핑하고, 각 EDID 필드를 타입 안전하게 수정하는 메서드를 제공합니다.

```csharp
public class EdidEditor
{
    private byte[] _data;

    public byte[] Data => _data;
    public int Length => _data?.Length ?? 0;

    public EdidEditor(byte[] edidData)
    {
        if (edidData == null)
            _data = new byte[128];
        else
        {
            _data = new byte[edidData.Length];
            Array.Copy(edidData, _data, edidData.Length);
        }
    }
}
```

복사본을 만들어 원본을 보호하는 것이 첫 번째 설계 결정입니다. 편집 중 실수로 원본을 망가뜨리면 복구할 방법이 없기 때문입니다.

### 빈 EDID 생성

기존 모니터 없이 새 EDID를 만들 때 `CreateBlank()`를 사용합니다.

```csharp
public static EdidEditor CreateBlank()
{
    var data = new byte[128];
    // Header: 0x00 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0x00
    data[0] = 0x00;
    data[1] = 0xFF; data[2] = 0xFF; data[3] = 0xFF;
    data[4] = 0xFF; data[5] = 0xFF; data[6] = 0xFF;
    data[7] = 0x00;
    // EDID version 1.4
    data[18] = 0x01;
    data[19] = 0x04;
    // Digital input
    data[20] = 0x80;
    // Unused standard timings placeholder
    for (int i = 38; i < 54; i += 2)
    {
        data[i] = 0x01;
        data[i + 1] = 0x01;
    }
    var editor = new EdidEditor(data);
    editor.UpdateChecksum();
    return editor;
}
```

EDID 헤더는 항상 고정된 매직 바이트(`00 FF FF FF FF FF FF 00`)입니다. 이를 확인하는 것이 유효성 검사의 첫 단계입니다.

---

## 제조사 ID 인코딩 — 비트 패킹의 세계

EDID에서 가장 흥미로운 부분 중 하나가 제조사 ID 인코딩입니다. 3자리 ASCII 문자열(예: "SAM", "DEL", "LEN")을 16비트 2바이트에 욱여넣습니다.

규칙은 다음과 같습니다:
- 각 알파벳 문자에서 하위 5비트만 사용 (A=1, B=2, ..., Z=26)
- 3개의 5비트 값을 15비트에 패킹
- 최상위 비트(MSB)는 항상 0

```csharp
public static byte[] EncodeManufacturerId(string id)
{
    if (id == null || id.Length != 3)
        return new byte[] { 0, 0 };

    id = id.ToUpper();
    int c1 = id[0] - 'A' + 1; // 'A'=1, 'Z'=26
    int c2 = id[1] - 'A' + 1;
    int c3 = id[2] - 'A' + 1;

    // Pack: [0][c1:5][c2:5][c3:5]
    byte b0 = (byte)((c1 << 2) | (c2 >> 3));
    byte b1 = (byte)((c2 << 5) | c3);
    return new byte[] { b0, b1 };
}
```

"SAM"을 예로 들면:
- S = 19 (10011₂)
- A = 1  (00001₂)
- M = 13 (01101₂)

패킹: `[0][10011][00001][01101]` → `0100 1100` `0010 1101` → `0x4C 0x2D`

```csharp
public void SetManufacturerId(string id)
{
    var encoded = EdidParser.EncodeManufacturerId(id);
    _data[8] = encoded[0];
    _data[9] = encoded[1];
    UpdateChecksum();
}
```

이 비트 조작은 1980년대 IBM PC 시절에 설계된 구조로, 2바이트에 3자의 압축 알파벳을 넣는 영리한 방법입니다.

---

## 제품 코드와 시리얼 번호

제품 코드는 리틀 엔디안 16비트 정수입니다:

```csharp
public void SetProductCode(ushort code)
{
    _data[10] = (byte)(code & 0xFF);       // 하위 바이트 먼저
    _data[11] = (byte)(code >> 8);          // 상위 바이트
    UpdateChecksum();
}
```

시리얼 번호는 32비트 리틀 엔디안:

```csharp
public void SetSerialNumber(uint serial)
{
    _data[12] = (byte)(serial & 0xFF);
    _data[13] = (byte)((serial >> 8) & 0xFF);
    _data[14] = (byte)((serial >> 16) & 0xFF);
    _data[15] = (byte)((serial >> 24) & 0xFF);
    UpdateChecksum();
}
```

제조 날짜는 주(week)와 연도를 각각 1바이트로 저장합니다. 연도는 1990을 기준으로 오프셋됩니다:

```csharp
public void SetManufactureDate(byte week, int year)
{
    _data[16] = week;
    _data[17] = (byte)(year - 1990);  // 1990년 기준 오프셋
    UpdateChecksum();
}
```

2026년이면 `data[17] = 36`이 됩니다.

---

## 디지털 입력과 색 깊이 설정

EDID 바이트 20은 비디오 입력 파라미터입니다. 디지털 입력 여부와 색 깊이를 함께 인코딩합니다.

```csharp
public void SetDigitalInput(bool digital, byte bitDepth)
{
    if (digital)
    {
        byte depthCode = 0;
        switch (bitDepth)
        {
            case 6:  depthCode = 1; break;
            case 8:  depthCode = 2; break;
            case 10: depthCode = 3; break;
            case 12: depthCode = 4; break;
            case 14: depthCode = 5; break;
            case 16: depthCode = 6; break;
        }
        // 비트 7: 디지털(1), 비트 6-4: 색 깊이 코드
        _data[20] = (byte)(0x80 | (depthCode << 4));
    }
    else
    {
        _data[20] = 0x00;  // 아날로그
    }
    UpdateChecksum();
}
```

8bpc 디지털이면 `0x80 | (2 << 4)` = `0xA0`이 됩니다.

---

## Detailed Timing Descriptor (DTD) 편집

DTD는 EDID의 핵심입니다. 18바이트 블록에 타이밍 파라미터 전체를 인코딩합니다. 최대 4개의 DTD 슬롯이 오프셋 54~125에 위치합니다.

```csharp
public void SetDetailedTiming(int descriptorIndex, DetailedTimingDescriptor dtd)
{
    if (descriptorIndex < 0 || descriptorIndex >= 4) return;
    int offset = 54 + descriptorIndex * 18;

    // 픽셀 클럭 (10kHz 단위, 리틀 엔디안)
    _data[offset]     = (byte)(dtd.PixelClockKHz10 & 0xFF);
    _data[offset + 1] = (byte)(dtd.PixelClockKHz10 >> 8);

    // H Active + H Blanking (각 12비트, 상위 4비트는 합쳐서 바이트 4에)
    _data[offset + 2] = (byte)(dtd.HActive & 0xFF);
    _data[offset + 3] = (byte)(dtd.HBlanking & 0xFF);
    _data[offset + 4] = (byte)(((dtd.HActive >> 4) & 0xF0) | ((dtd.HBlanking >> 8) & 0x0F));

    // V Active + V Blanking
    _data[offset + 5] = (byte)(dtd.VActive & 0xFF);
    _data[offset + 6] = (byte)(dtd.VBlanking & 0xFF);
    _data[offset + 7] = (byte)(((dtd.VActive >> 4) & 0xF0) | ((dtd.VBlanking >> 8) & 0x0F));

    // Porch/Sync 너비 (H는 10비트, V는 6비트)
    _data[offset + 8]  = (byte)(dtd.HFrontPorch & 0xFF);
    _data[offset + 9]  = (byte)(dtd.HSyncWidth & 0xFF);
    _data[offset + 10] = (byte)(((dtd.VFrontPorch & 0x0F) << 4) | (dtd.VSyncWidth & 0x0F));
    _data[offset + 11] = (byte)(
        ((dtd.HFrontPorch >> 2) & 0xC0) | ((dtd.HSyncWidth >> 4) & 0x30) |
        ((dtd.VFrontPorch >> 2) & 0x0C) | ((dtd.VSyncWidth >> 4) & 0x03));

    // 이미지 크기 (mm, 각 12비트)
    _data[offset + 12] = (byte)(dtd.HImageSizeMm & 0xFF);
    _data[offset + 13] = (byte)(dtd.VImageSizeMm & 0xFF);
    _data[offset + 14] = (byte)(((dtd.HImageSizeMm >> 4) & 0xF0) | ((dtd.VImageSizeMm >> 8) & 0x0F));

    _data[offset + 15] = dtd.HBorderPixels;
    _data[offset + 16] = dtd.VBorderPixels;
    _data[offset + 17] = dtd.Features;  // 0x18 = 디지털 분리 동기

    UpdateChecksum();
}
```

18바이트 안에 수평/수직 해상도, 블랭킹, 프런트 포치, 싱크 폭, 물리적 크기를 모두 때려넣는 구조입니다. 각 파라미터가 여러 바이트에 걸쳐 비트 단위로 분산되어 있어서, 순서를 잘못 이해하면 완전히 엉뚱한 타이밍이 나옵니다.

---

## 모니터 이름과 레인지 리밋 디스크립터

DTD가 아닌 18바이트 슬롯은 텍스트 디스크립터 또는 레인지 리밋으로 사용됩니다. 태그 바이트(`data[offset+3]`)로 구분됩니다.

```csharp
private void SetDescriptorString(DescriptorTag tag, string text)
{
    // 기존 슬롯 찾기 → 없으면 빈 슬롯 할당
    int targetOffset = -1;
    for (int i = 0; i < 4; i++)
    {
        int offset = 54 + i * 18;
        if (_data[offset] == 0 && _data[offset + 1] == 0
            && _data[offset + 3] == (byte)tag)
        {
            targetOffset = offset;
            break;
        }
    }
    // ...슬롯 확보 후:

    // 최대 13자, 종료는 0x0A(LF), 나머지 패딩 0x20(스페이스)
    byte[] strBytes = Encoding.ASCII.GetBytes(text);
    int j = 0;
    for (; j < strBytes.Length && j < 13; j++)
        _data[targetOffset + 5 + j] = strBytes[j];
    if (j < 13)
    {
        _data[targetOffset + 5 + j] = 0x0A;  // 줄 바꿈으로 끝
        j++;
    }
    for (; j < 13; j++)
        _data[targetOffset + 5 + j] = 0x20;  // 스페이스 패딩

    UpdateChecksum();
}
```

모니터 이름은 최대 13자로 제한됩니다. 0x0A(LF)가 문자열 종료 마커이고, 나머지는 공백으로 채웁니다. 이 패딩 규칙을 지키지 않으면 일부 드라이버나 OS가 이름을 올바르게 읽지 못합니다.

레인지 리밋은 모니터의 수직/수평 주사율 범위와 최대 픽셀 클럭을 선언합니다:

```csharp
public void SetRangeLimits(byte minV, byte maxV, byte minH, byte maxH,
                            byte maxPixelClockMHz10)
{
    // 오프셋 5: 최소 수직 주사율 (Hz)
    // 오프셋 6: 최대 수직 주사율 (Hz)
    // 오프셋 7: 최소 수평 주사율 (kHz)
    // 오프셋 8: 최대 수평 주사율 (kHz)
    // 오프셋 9: 최대 픽셀 클럭 (10MHz 단위)
    _data[targetOffset + 5] = minV;
    _data[targetOffset + 6] = maxV;
    _data[targetOffset + 7] = minH;
    _data[targetOffset + 8] = maxH;
    _data[targetOffset + 9] = maxPixelClockMHz10;
    _data[targetOffset + 10] = 0x00;  // 기본 GTF
    for (int i = 11; i < 18; i++)
        _data[targetOffset + i] = 0x0A;
    UpdateChecksum();
}
```

---

## 체크섬 계산

EDID의 마지막 바이트(오프셋 127)는 체크섬입니다. 0~126 바이트의 합계와 127번 바이트를 더하면 256의 배수가 되어야 합니다.

```csharp
public void UpdateChecksum()
{
    if (_data.Length >= 128)
        _data[127] = EdidParser.CalculateChecksum(_data, 0, 128);

    // 확장 블록도 각자 체크섬 업데이트
    for (int ext = 1;
         ext <= _data[126] && (ext + 1) * 128 <= _data.Length;
         ext++)
    {
        int blockStart = ext * 128;
        _data[blockStart + 127] =
            EdidParser.CalculateChecksum(_data, blockStart, 128);
    }
}
```

체크섬 계산 로직:

```csharp
public static byte CalculateChecksum(byte[] data, int offset, int length)
{
    byte sum = 0;
    for (int i = offset; i < offset + length - 1; i++)
        sum += data[i];
    return (byte)(256 - (sum % 256));
}
```

모든 `Set*` 메서드 끝에서 `UpdateChecksum()`을 자동 호출하므로, 사용자가 직접 신경 쓸 필요가 없습니다. 단, `SetByte()`로 원시 편집을 한 경우에는 마지막에 수동으로 호출해야 합니다.

![EDID 편집 워크플로우](/images/posts/nvapi-gpu-controller/part5-edid-edit-workflow.svg)

---

## 색상 제어 — NvColorControl 다중 버전 폴백

NVAPI의 색상 제어는 드라이버 버전에 따라 구조체 버전이 달라집니다. V1, V3, V5 세 가지 버전이 존재하며, 최신 버전부터 순서대로 시도하고 `IncompatibleStructVersion` 오류가 나면 이전 버전으로 폴백합니다.

### 구조체 정의

**V5 (16바이트) — 최신 드라이버용:**

```csharp
[StructLayout(LayoutKind.Explicit, Size = 16)]
public struct NvColorControlV5
{
    [FieldOffset(0)]  public uint Version;           // size | (5 << 16)
    [FieldOffset(4)]  public ushort Size;
    [FieldOffset(6)]  public NvColorCmd Cmd;         // Get=1, Set=2
    [FieldOffset(7)]  public NvColorFormat ColorFormat;
    [FieldOffset(8)]  public byte Colorimetry;
    [FieldOffset(9)]  public NvDynamicRange DynamicRange;
    [FieldOffset(10)] public NvColorDepth ColorDepth;
    [FieldOffset(11)] public NvColorSelectionPolicy SelectionPolicy;
    [FieldOffset(12)] public byte ColorSpaceId;      // V5에서 추가
}
```

**V3 (12바이트) — 중간 드라이버용:**

```csharp
[StructLayout(LayoutKind.Explicit, Size = 12)]
public struct NvColorControlV3
{
    [FieldOffset(0)] public uint Version;    // size | (3 << 16)
    [FieldOffset(4)] public NvColorCmd Cmd;
    [FieldOffset(5)] public NvColorFormat ColorFormat;
    [FieldOffset(6)] public byte Colorimetry;
    [FieldOffset(7)] public NvDynamicRange DynamicRange;
    [FieldOffset(8)] public NvColorDepth ColorDepth;
}
```

**V1 (12바이트) — 구형 드라이버:**

V3와 레이아웃이 동일하지만 `Version` 필드의 버전 번호만 다릅니다. 실질적인 차이는 드라이버가 인식하는 버전 코드뿐입니다.

### Version 필드 패킹 규칙

NVAPI 전반에 걸쳐 Version 필드는 다음 규칙을 따릅니다:

```
Version = (구조체 크기(바이트)) | (버전 번호 << 16)
```

V5의 경우: `16 | (5 << 16)` = `0x00050010`
V3의 경우: `12 | (3 << 16)` = `0x0003000C`

이 패킹 방식 덕분에 드라이버가 구조체 크기와 버전을 하나의 정수로 검증할 수 있습니다.

### 폴백 체인 구현

```csharp
public static NvStatus SetColorControl(
    uint displayId,
    NvColorDepth depth,
    NvColorFormat format,
    NvDynamicRange range)
{
    NvStatus status;

    // V5 시도 (최신 드라이버)
    var v5 = NvColorControlV5.CreateSet(depth, format, range);
    status = NvApiWrapper.DISP_ColorControlV5(displayId, ref v5);
    if (status == NvStatus.OK) return status;
    if (status != NvStatus.IncompatibleStructVersion)
    {
        Logger.Error($"ColorControl v5 error: {NvApiWrapper.GetErrorMessage(status)}");
        return status;
    }

    // V3 시도
    var v3 = NvColorControlV3.CreateSet(depth, format, range);
    status = NvApiWrapper.DISP_ColorControlV3(displayId, ref v3);
    if (status == NvStatus.OK) return status;
    if (status != NvStatus.IncompatibleStructVersion)
    {
        Logger.Error($"ColorControl v3 error: {NvApiWrapper.GetErrorMessage(status)}");
        return status;
    }

    // V1 시도 (구형 드라이버 최후 수단)
    var v1 = NvColorControlV1.CreateSet(depth, format, range);
    status = NvApiWrapper.DISP_ColorControlV1(displayId, ref v1);
    if (status == NvStatus.OK) return status;

    Logger.Error($"All ColorControl versions failed: {NvApiWrapper.GetErrorMessage(status)}");
    return status;
}
```

`IncompatibleStructVersion`(-9)인 경우에만 다음 버전으로 넘어가고, 다른 오류(예: `InvalidArgument`, `NotSupported`)는 즉시 반환합니다. 오류를 무조건 삼키면 실제 문제를 숨기게 됩니다.

### 색상 설정 옵션

```csharp
public enum NvColorDepth : byte
{
    Default = 0,  // 드라이버 자동 결정
    Bpc6    = 1,
    Bpc8    = 2,  // 대부분의 SDR 모니터
    Bpc10   = 3,  // HDR10, WCG 권장
    Bpc12   = 4,
    Bpc16   = 5,
}

public enum NvColorFormat : byte
{
    RGB     = 0,  // PC 모니터 표준
    YUV422  = 1,  // HDMI 대역폭 절약 (4K@60Hz 한계 상황)
    YUV444  = 2,  // TV 풀 크로마
    Default = 3,
}

public enum NvDynamicRange : byte
{
    Auto    = 0,
    Limited = 1,  // 16-235, TV 표준
    Full    = 2,  // 0-255, PC 표준
}
```

HDR 콘텐츠를 제대로 보려면 `Bpc10 + RGB + Limited` 조합이 일반적입니다. PC 모니터의 SDR 작업에서는 `Bpc8 + RGB + Full`이 맞습니다.

![색상 제어 파이프라인](/images/posts/nvapi-gpu-controller/part5-color-control.svg)

---

## EdidEditorPanel — UI 설계

`EdidEditorPanel`은 `UserControl`을 상속하고 세 개의 주요 영역으로 구성됩니다.

```csharp
public class EdidEditorPanel : UserControl
{
    private SplitContainer splitMain;    // 좌: 트리뷰 / 우: 헥스+편집폼
    private SplitContainer splitRight;   // 우상: 헥스에디터 / 우하: 편집 필드

    private TreeView treeEdid;           // 파싱된 EDID 트리
    private TextBox hexEditor;           // 원시 헥스 덤프
    // 편집 필드들 (TextBox, NumericUpDown, ComboBox...)
}
```

헥스 에디터는 다크 테마로 구성됩니다:

```csharp
hexEditor = new TextBox
{
    Multiline = true,
    ScrollBars = ScrollBars.Both,
    Font = new Font("Consolas", 9F),
    BackColor = Color.FromArgb(30, 30, 30),
    ForeColor = Color.Lime,
    WordWrap = false
};
```

### EDID 읽기와 로드

```csharp
private void BtnReadEdid_Click(object sender, EventArgs e)
{
    var display = _displays[cboDisplay.SelectedIndex];

    byte[] edidData;
    var status = NvEdid.ReadEDID(display.GpuHandle, display.OutputId, out edidData);
    if (status == NvStatus.OK && edidData != null)
    {
        LoadEdidData(edidData);
    }
}

private void LoadEdidData(byte[] data)
{
    _currentEdidRaw = data;
    _editor = new EdidEditor(data);
    hexEditor.Text = EdidParser.ToHexDump(data);  // 헥스 뷰 업데이트

    var parsed = EdidParser.Parse(data);
    PopulateEditFields(parsed);   // 편집 필드 채우기
    PopulateTree(parsed, data);   // 트리뷰 구성
}
```

데이터가 로드되면 세 곳이 동시에 업데이트됩니다: 헥스 에디터, 편집 폼, 트리뷰.

### 편집 적용

```csharp
private void BtnApplyEdits_Click(object sender, EventArgs e)
{
    if (_editor == null)
        _editor = EdidEditor.CreateBlank();  // 없으면 빈 EDID 생성

    _editor.SetManufacturerId(txtManufacturer.Text);
    _editor.SetProductCode(Convert.ToUInt16(txtProductCode.Text, 16));
    _editor.SetSerialNumber(uint.Parse(txtSerial.Text));
    _editor.SetManufactureDate((byte)numWeek.Value, (int)numYear.Value);
    _editor.SetEdidVersion(1, (byte)(cboEdidVersion.SelectedIndex == 0 ? 3 : 4));
    _editor.SetDigitalInput(chkDigital.Checked, (byte)numBitDepth.Value);
    _editor.SetScreenSize((byte)numHSize.Value, (byte)numVSize.Value);
    _editor.SetGamma((double)numGamma.Value / 100.0);
    _editor.SetMonitorName(txtMonitorName.Text);
    _editor.UpdateChecksum();

    // 뷰 갱신
    _currentEdidRaw = _editor.Data;
    hexEditor.Text = EdidParser.ToHexDump(_editor.Data);
    PopulateTree(EdidParser.Parse(_editor.Data), _editor.Data);
}
```

### DTD 편집

DTD 슬롯 인덱스를 콤보박스로 선택하고 각 타이밍 파라미터를 `NumericUpDown`으로 입력합니다:

```csharp
private void BtnDtdApply_Click(object sender, EventArgs e)
{
    int idx = cboDtdIndex.SelectedIndex;

    var dtd = new DetailedTimingDescriptor
    {
        PixelClockKHz10 = (ushort)(numDtdPixelClock.Value * 100),
        HActive    = (int)numDtdHActive.Value,
        HBlanking  = (int)numDtdHBlanking.Value,
        VActive    = (int)numDtdVActive.Value,
        VBlanking  = (int)numDtdVBlanking.Value,
        HFrontPorch = (int)numDtdHFP.Value,
        HSyncWidth  = (int)numDtdHSW.Value,
        VFrontPorch = (int)numDtdVFP.Value,
        VSyncWidth  = (int)numDtdVSW.Value,
        Features    = 0x18  // 디지털 분리 동기
    };

    _editor.SetDetailedTiming(idx, dtd);
    hexEditor.Text = EdidParser.ToHexDump(_editor.Data);
    PopulateTree(EdidParser.Parse(_editor.Data), _editor.Data);
}
```

---

## EDID 오버라이드 적용과 제거

### 유효성 검사 후 적용

```csharp
private void BtnApplyOverride_Click(object sender, EventArgs e)
{
    // 헤더 검사
    if (!EdidParser.ValidateHeader(_currentEdidRaw))
    {
        var r = MessageBox.Show("EDID 헤더가 잘못되었습니다. 그래도 적용하시겠습니까?",
            "잘못된 EDID", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
        if (r != DialogResult.Yes) return;
    }

    // 체크섬 검사
    if (!EdidParser.ValidateChecksum(_currentEdidRaw))
    {
        var r = MessageBox.Show("체크섬이 잘못되었습니다. 자동 수정 후 적용하시겠습니까?",
            "잘못된 체크섬", MessageBoxButtons.YesNoCancel, MessageBoxIcon.Warning);
        if (r == DialogResult.Cancel) return;
        if (r == DialogResult.Yes)
            _currentEdidRaw[127] = EdidParser.CalculateChecksum(_currentEdidRaw, 0, 128);
    }

    var status = NvEdid.WriteEDID(display.GpuHandle, display.OutputId, _currentEdidRaw);
    if (status == NvStatus.OK)
        MessageBox.Show("EDID 오버라이드 적용 완료. 재부팅이 필요할 수 있습니다.");
}
```

적용 전 두 단계 검사: 헤더 유효성(매직 바이트 확인), 체크섬 유효성. 체크섬 오류는 자동 수정 옵션을 제공합니다.

### 오버라이드 제거

```csharp
private void BtnRemoveOverride_Click(object sender, EventArgs e)
{
    var status = NvEdid.RemoveEDIDOverride(display.GpuHandle, display.OutputId);
    if (status == NvStatus.OK)
        MessageBox.Show("EDID 오버라이드가 제거되었습니다. 원래 모니터 EDID로 복원됩니다.");
}
```

`NvAPI_GPU_SetEDID`에 빈 데이터를 넘기거나 전용 제거 함수를 호출하면 드라이버가 원본 EDID로 되돌아갑니다.

---

## 파일 I/O — 4가지 형식 지원

EDID를 파일로 내보내고 가져오는 기능은 테스트와 공유에 필수입니다.

```
저장 형식:
- .bin   — 원시 이진 (128/256바이트 그대로)
- .dat   — 레지스트리 테이블 형식 (Windows 레지스트리 편집기 호환)
- .txt   — 꺾쇠 괄호 형식 (<EDID>...</EDID>)
- .hex   — 헥스 텍스트 (한 줄에 16바이트씩)
```

불러오기도 동일한 4가지 형식을 지원하며, 확장자를 보고 형식을 자동 판단합니다:

```csharp
dlg.Filter = "All EDID Files|*.bin;*.dat;*.txt|Binary (*.bin)|*.bin|" +
             "DAT Table (*.dat)|*.dat|Hex Text (*.txt)|*.txt|All Files (*.*)|*.*";
```

---

## 전체 애플리케이션 구조

![전체 애플리케이션 아키텍처](/images/posts/nvapi-gpu-controller/part5-complete-app.svg)

`MainForm`은 네 개의 탭 패널과 하단 로그 뷰, 상태 바로 구성됩니다:

```csharp
public partial class MainForm : Form
{
    private TabControl tabControl;
    private GpuInfoPanel gpuInfoPanel;          // GPU 정보
    private DisplayPanel displayPanel;           // 디스플레이 관리
    private CustomResolutionPanel customResPanel; // 커스텀 해상도
    private EdidEditorPanel edidPanel;           // EDID 편집기
    private TextBox logTextBox;                  // 실시간 로그
    private StatusStrip statusStrip;             // GPU/드라이버/디스플레이 수
}
```

NVAPI 초기화 실패 시 EDID 파일 편집만 가능한 제한 모드로 동작합니다:

```csharp
private void SetUiDisabled()
{
    gpuInfoPanel.Enabled = false;
    displayPanel.Enabled = false;
    customResPanel.Enabled = false;
    // EDID 탭은 파일 편집 용도로 계속 사용 가능
    Logger.Warn("Running in limited mode - EDID file editing only");
}
```

이 설계 덕분에 NVIDIA GPU가 없는 환경에서도 EDID 파일을 열고 편집하고 저장하는 용도로 앱을 활용할 수 있습니다.

---

## 구현 중 마주친 문제들

### 1. NvEdidV3의 256바이트 버퍼 제한

```csharp
[StructLayout(LayoutKind.Sequential)]
public struct NvEdidV3
{
    public uint Version;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 256)]
    public byte[] EdidData;  // 최대 256바이트 고정
    public uint EdidSize;
    public uint EdidId;
    public uint Offset;      // 페이지 오프셋 (확장 블록 읽기용)
}
```

EDID가 256바이트를 넘으면(드문 경우지만 존재) `Offset`을 증가시키며 여러 번 호출해야 합니다. 처음에는 이를 모르고 항상 128바이트만 읽어 CTA-861 확장 블록을 놓쳤습니다.

### 2. 색상 제어 버전 혼란

V1과 V3는 메모리 레이아웃이 동일합니다. 처음에는 왜 두 가지가 존재하는지 이해하지 못했습니다. NVAPI는 `Version` 필드의 버전 번호로 드라이버가 지원하는 기능 집합을 결정합니다. 같은 구조체라도 버전 번호가 다르면 드라이버가 다르게 처리합니다.

### 3. DTD 비트 패킹 오류

`SetDetailedTiming`의 처음 구현에서 H/V 상위 비트 합산 바이트(오프셋 4, 7)를 잘못 계산했습니다. `HActive >> 4`를 했더니 하위 비트까지 전부 내려왔습니다. 올바른 코드는 `(HActive >> 4) & 0xF0`으로 상위 4비트만 유지해야 합니다.

### 4. EDID 오버라이드 후 재부팅

`WriteEDID` 호출 자체는 성공하지만, 모든 변경사항이 즉시 반영되지는 않습니다. 특히 모니터 이름이나 HDR 플래그 변경은 드라이버 재시작 또는 재부팅이 필요한 경우가 많습니다. UI에 명확한 안내 메시지를 표시하는 것이 중요합니다.

---

## 회고 — 시리즈를 마치며

5편에 걸쳐 NvGpuController를 완성했습니다. 뒤돌아보면 가장 많은 시간을 쓴 부분은 의외로 NVAPI 문서 해석이었습니다. NVAPI는 공식 문서가 빈약하고, 구조체 정의는 헤더 파일에 흩어져 있으며, 버전별 차이는 실제로 시도해보기 전까지 알 수 없는 경우가 많았습니다.

**잘 된 부분:**

- **폴백 체인 패턴** — V5 → V3 → V1으로 이어지는 색상 제어 폴백은 드라이버 버전에 무관하게 동작하는 강건한 설계입니다.
- **EdidEditor의 자동 체크섬** — 모든 Set* 메서드 끝에서 자동으로 체크섬을 업데이트하므로, 사용자가 EDID 내부 구조를 몰라도 항상 유효한 데이터를 유지합니다.
- **제한 모드** — NVAPI 없이도 EDID 파일 편집이 가능하게 한 점은 실용적인 선택이었습니다.

**아쉬운 부분:**

- **실시간 헥스 편집** — 현재는 필드 편집 후 헥스 뷰를 갱신하지만, 반대로 헥스를 직접 수정하면 필드가 갱신되지 않습니다. 양방향 동기화가 필요합니다.
- **CTA-861 확장 블록 쓰기** — 읽기는 완성됐지만 쓰기(특히 HDR 메타데이터, VIC 코드 추가)는 미구현 상태입니다.
- **트리뷰 인터랙션** — 트리 노드를 선택하면 해당 바이트가 헥스 에디터에서 하이라이트되어야 하지만, `TreeEdid_AfterSelect`는 현재 비어있습니다.

**향후 개선 방향:**

1. CTA-861 확장 블록 편집 (HDR 지원, 오디오 포맷 선언)
2. 헥스 에디터 ↔ 편집 폼 양방향 동기화
3. EDID 버전 비교 (원본 vs 편집본 diff 뷰)
4. 알려진 모니터 데이터베이스 연동 (Monitorinfo.net API 등)
5. 커맨드라인 모드 (스크립트 자동화 지원)

---

## 마무리

NvGpuController는 NVAPI의 P/Invoke 바인딩부터 EDID 비트 패킹, 다중 버전 폴백까지 저수준 하드웨어 제어의 여러 측면을 담고 있습니다. C#과 WinForms의 제약 안에서 GPU를 직접 다루는 경험은 생각보다 훨씬 흥미로웠고, 모니터와 GPU 사이에서 실제로 어떤 데이터가 오가는지 구체적으로 이해하게 되었습니다.

소스코드는 시리즈 전체를 통해 단계적으로 만들어진 결과물입니다. 비슷한 프로젝트를 진행 중이라면 특히 EDID 비트 패킹과 NVAPI Version 필드 규칙 부분이 참고가 되길 바랍니다.
