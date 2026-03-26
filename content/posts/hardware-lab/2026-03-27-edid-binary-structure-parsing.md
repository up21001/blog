---
title: "NVIDIA GPU 컨트롤러 만들기 (3) — EDID 바이너리 구조와 파싱 심층 분석"
date: 2026-03-27T11:00:00+09:00
lastmod: 2026-03-27T11:00:00+09:00
description: "EDID 바이너리 포맷의 128바이트 구조를 바이트 단위로 분석하고, CTA-861 확장 블록까지 파싱하는 과정을 실제 코드와 함께 설명합니다."
slug: "edid-binary-structure-parsing"
categories: ["hardware-lab"]
tags: ["EDID", "모니터", "디스플레이", "바이너리", "파싱", "CTA-861", "C#"]
featureimage: "/images/posts/nvapi-gpu-controller/part3-edid-structure.svg"
series: ["NVIDIA GPU 컨트롤러 개발기 2026"]
series_order: 3
draft: false
---

이전 편에서는 NVAPI를 초기화하고 GPU 핸들과 디스플레이 Output ID를 얻는 과정을 다뤘습니다. 이번 편은 시리즈 중 가장 기술적으로 깊이 들어가는 내용입니다. NVIDIA GPU로부터 읽어온 EDID 바이트 배열이 실제로 어떤 구조를 갖고 있는지, 그리고 우리의 C# 파서가 어떻게 그 구조를 해석하는지 바이트 단위로 파헤쳐 봅니다.

---

## EDID란 무엇인가

**EDID(Extended Display Identification Data)**는 모니터가 GPU에게 자신이 누구인지, 무엇을 지원하는지 알려주는 바이너리 데이터입니다. 1994년 VESA가 처음 제정한 이 표준은 현재 EDID 1.4까지 발전했으며, 128바이트의 베이스 블록과 추가적인 128바이트 확장 블록으로 구성됩니다.

모니터를 컴퓨터에 연결하면 GPU는 I2C 버스(DDC 채널)를 통해 모니터에서 EDID를 읽어옵니다. 운영체제와 드라이버는 이 데이터를 기반으로 지원 해상도, 재생률, 색 공간, HDR 능력 등을 파악합니다. NVAPI는 이 과정을 C# 레벨에서 접근할 수 있도록 `NvAPI_GPU_GetEDID` 함수를 제공합니다.

![EDID 128바이트 베이스 블록 구조](/images/posts/nvapi-gpu-controller/part3-edid-structure.svg)

---

## NVAPI로 EDID 읽기

파싱에 앞서 먼저 NVAPI로 원시 데이터를 가져오는 부분을 살펴봅시다. `NvEdid.cs`의 `ReadEDID` 메서드가 이 역할을 담당합니다.

```csharp
public static NvStatus ReadEDID(NvPhysicalGpuHandle gpuHandle,
                                 uint outputId, out byte[] edidData)
{
    edidData = null;

    // 첫 번째 호출: 총 크기와 첫 256바이트 수신
    var edid = NvEdidV3.Create();
    edid.Offset = 0;
    var status = NvApiWrapper.GPU_GetEDID(gpuHandle, outputId, ref edid);
    if (status != NvStatus.OK || edid.EdidSize == 0)
        return status;

    uint totalSize = edid.EdidSize;
    edidData = new byte[totalSize];
    uint firstChunk = System.Math.Min(totalSize, 256);
    System.Array.Copy(edid.EdidData, edidData, firstChunk);

    // 나머지 블록을 256바이트씩 읽기
    uint offset = 256;
    while (offset < totalSize)
    {
        var nextEdid = NvEdidV3.Create();
        nextEdid.Offset = offset;
        status = NvApiWrapper.GPU_GetEDID(gpuHandle, outputId, ref nextEdid);
        if (status != NvStatus.OK) break;
        uint chunk = System.Math.Min(totalSize - offset, 256);
        System.Array.Copy(nextEdid.EdidData, 0, edidData, offset, chunk);
        offset += 256;
    }

    Logger.Info($"EDID read complete: {totalSize} bytes ({totalSize / 128} blocks)");
    return NvStatus.OK;
}
```

`NvEdidV3` 구조체는 NVAPI의 `NV_EDID_V3`에 대응합니다. 핵심은 한 번에 최대 256바이트만 읽을 수 있다는 점입니다. 4K 모니터처럼 CTA-861 확장 블록이 여러 개인 경우 총 EDID가 256바이트(128×2)를 넘을 수 있으므로, `Offset` 필드를 증가시키며 반복 호출합니다.

`NvEdidV3`의 버전 필드는 특이한 방식으로 초기화됩니다.

```csharp
e.Version = (uint)(Marshal.SizeOf(typeof(NvEdidV3)) | (3 << 16));
```

상위 16비트에 버전 번호(3), 하위 16비트에 구조체 크기를 OR 연산으로 합칩니다. NVAPI의 공통 패턴으로, 드라이버가 호환성을 검사하는 데 사용합니다.

---

## 128바이트 베이스 블록 상세 분석

![EDID 파싱 파이프라인](/images/posts/nvapi-gpu-controller/part3-parsing-flow.svg)

### 헤더 매직 (0x00–0x07)

EDID의 첫 8바이트는 항상 고정된 매직 값입니다.

```
00 FF FF FF FF FF FF 00
```

`EdidParser.ValidateHeader()`는 이 8바이트를 검사합니다.

```csharp
private static readonly byte[] EDID_HEADER = { 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00 };

public static bool ValidateHeader(byte[] data)
{
    if (data == null || data.Length < 128) return false;
    for (int i = 0; i < 8; i++)
        if (data[i] != EDID_HEADER[i]) return false;
    return true;
}
```

헤더가 일치하지 않으면 해당 데이터는 유효한 EDID가 아닙니다. 파일 손상이나 NVAPI 호출 실패를 감지하는 첫 번째 관문입니다.

### 체크섬 알고리즘 (0x7F)

128바이트의 마지막 바이트는 체크섬입니다. EDID 명세는 베이스 블록 128바이트 전체의 합이 256으로 나누어 떨어져야 한다고 정의합니다.

```csharp
public static bool ValidateChecksum(byte[] data, int offset = 0, int length = 128)
{
    byte sum = 0;
    for (int i = offset; i < offset + length; i++)
        sum += data[i];
    return sum == 0;  // byte overflow 덕분에 자동으로 mod 256
}
```

`byte` 타입은 0–255 범위이므로 오버플로우가 자동으로 mod 256 역할을 합니다. 체크섬 바이트를 새로 계산할 때는 나머지 127바이트 합의 보수를 취합니다.

```csharp
public static byte CalculateChecksum(byte[] data, int offset = 0, int length = 128)
{
    byte sum = 0;
    for (int i = offset; i < offset + length - 1; i++)  // 마지막 바이트 제외
        sum += data[i];
    return (byte)(256 - sum);  // 2의 보수
}
```

### 제조사 ID 인코딩 (0x08–0x09)

이 부분이 EDID에서 가장 흥미로운 비트 조작입니다. 3글자 ASCII 알파벳 문자열을 2바이트 16비트 정수로 압축합니다.

![제조사 ID 인코딩 비트 다이어그램](/images/posts/nvapi-gpu-controller/part3-manufacturer-id.svg)

각 문자에서 `'A'`의 값(65)을 빼고 1을 더하면 A=1, B=2, ..., Z=26이 되어 5비트로 표현 가능합니다. 세 문자를 각각 5비트씩 15비트에 패킹하고 최상위 비트는 항상 0으로 채웁니다.

```csharp
public static string DecodeManufacturerId(byte b1, byte b2)
{
    int id = (b1 << 8) | b2;
    char c1 = (char)(((id >> 10) & 0x1F) + 'A' - 1);  // 비트 14:10
    char c2 = (char)(((id >> 5)  & 0x1F) + 'A' - 1);  // 비트  9:5
    char c3 = (char)((id         & 0x1F) + 'A' - 1);  // 비트  4:0
    return $"{c1}{c2}{c3}";
}
```

예시로 삼성(SAM)을 인코딩해 보겠습니다.

- S = 19 = `10011`
- A = 1  = `00001`
- M = 13 = `01101`

16비트로 패킹하면: `0_10011_00001_01101` = `0100 1100 0010 1101` = `0x4C 0x2D`

반대로 인코딩하는 `EncodeManufacturerId()`도 동일한 로직의 역연산입니다.

```csharp
public static byte[] EncodeManufacturerId(string id)
{
    id = id.ToUpper();
    int c1 = id[0] - 'A' + 1;
    int c2 = id[1] - 'A' + 1;
    int c3 = id[2] - 'A' + 1;
    int val = (c1 << 10) | (c2 << 5) | c3;
    return new byte[] { (byte)(val >> 8), (byte)(val & 0xFF) };
}
```

### 제품 코드 및 시리얼 번호 (0x0A–0x0F)

```csharp
// Product code (bytes 10-11, little-endian)
block.ProductCode = (ushort)(data[10] | (data[11] << 8));

// Serial number (bytes 12-15, little-endian)
block.SerialNumber = (uint)(data[12] | (data[13] << 8)
                           | (data[14] << 16) | (data[15] << 24));
```

x86 시스템의 관례대로 리틀 엔디언으로 저장됩니다. 낮은 주소에 LSB가 위치합니다. 시리얼 번호가 `0x00000000`이거나 `0x01010101`인 경우 실제 시리얼 번호가 없고, 디스크립터 영역(0xFC–0x7D)의 모니터 시리얼 문자열을 사용하라는 신호입니다.

### 제조 날짜 (0x10–0x11)

```csharp
block.ManufactureWeek = data[16];         // 1~53주
block.ManufactureYear = data[17] + 1990;  // 오프셋 1990년
```

연도는 0이 1990년을 의미하는 오프셋 인코딩입니다. 예를 들어 `data[17] = 34`이면 2024년입니다. 일부 모니터는 주차 바이트를 `0xFF`로 설정하여 제조 연도만 표시하기도 합니다.

### 비디오 입력 파라미터 (0x14)

```csharp
block.IsDigital = (data[20] & 0x80) != 0;
if (block.IsDigital)
{
    int depth = (data[20] >> 4) & 0x07;
    byte[] depths = { 0, 6, 8, 10, 12, 14, 16, 0 };
    block.BitDepth = depths[depth];
}
```

비트 7이 1이면 디지털 인터페이스(HDMI, DisplayPort), 0이면 아날로그(VGA)입니다. 디지털인 경우 비트 6:4가 색 심도를 나타냅니다.

| 값 | 색 심도 |
|----|--------|
| 000 | 정의되지 않음 |
| 001 | 6비트 |
| 010 | 8비트 |
| 011 | 10비트 |
| 100 | 12비트 |
| 101 | 14비트 |
| 110 | 16비트 |

### 화면 크기와 감마 (0x15–0x17)

```csharp
block.HScreenSizeCm = data[21];  // 가로 cm
block.VScreenSizeCm = data[22];  // 세로 cm
block.Gamma = (data[23] + 100) / 100.0;
```

화면 크기는 센티미터 단위 정수입니다. `0x3C 0x22`라면 60×34cm로, 대각선 길이를 계산하면 약 69cm ≈ 27인치입니다.

감마는 0이 1.00, 120이 2.20인 오프셋 인코딩입니다. 일반 sRGB 모니터의 경우 `data[23] = 120` (2.20)이 보편적입니다.

---

## 색도 좌표 (Chromaticity, 0x19–0x22)

10바이트 영역에 CIE 1931 색도 좌표(Rx, Ry, Gx, Gy, Bx, By, Wx, Wy)를 압축 저장합니다. 각 좌표는 10비트 정밀도를 가지며, 하위 2비트를 첫 2바이트에 모아두고 상위 8비트를 이후 바이트에 저장하는 복잡한 배치 방식을 사용합니다.

실제 sRGB 기준점 좌표를 예로 들면 다음과 같습니다.

| 색점 | x | y |
|------|---|---|
| 적색(R) | 0.640 | 0.330 |
| 녹색(G) | 0.300 | 0.600 |
| 청색(B) | 0.150 | 0.060 |
| 백색(W, D65) | 0.3127 | 0.3290 |

---

## 확립된 타이밍 (Established Timings, 0x23–0x25)

3바이트 비트맵으로 레거시 해상도 지원 여부를 표현합니다.

```csharp
public List<string> GetTimingList()
{
    var list = new List<string>();
    string[] timings1 = { "720x400@70Hz", "720x400@88Hz", "640x480@60Hz", "640x480@67Hz",
                          "640x480@72Hz", "640x480@75Hz", "800x600@56Hz", "800x600@60Hz" };
    string[] timings2 = { "800x600@72Hz", "800x600@75Hz", "832x624@75Hz", "1024x768@87Hz(I)",
                          "1024x768@60Hz", "1024x768@70Hz", "1024x768@75Hz", "1280x1024@75Hz" };
    string[] timings3 = { "1152x870@75Hz", ... };

    for (int i = 0; i < 8; i++)
    {
        if ((Byte1 & (1 << (7 - i))) != 0) list.Add(timings1[i]);
        if ((Byte2 & (1 << (7 - i))) != 0) list.Add(timings2[i]);
        ...
    }
    return list;
}
```

비트 7이 가장 높은 우선순위입니다. 예를 들어 `Byte1 = 0x21` (`0010 0001`)이면 640×480@60Hz와 800×600@60Hz를 지원합니다.

---

## 표준 타이밍 (Standard Timings, 0x26–0x35)

16바이트에 최대 8개의 표준 타이밍을 2바이트 쌍으로 저장합니다.

```csharp
public int HActive => (HPixelDiv8Minus31 + 31) * 8;
public int VActive
{
    get
    {
        int aspect = (AspectAndRefresh >> 6) & 0x03;
        switch (aspect)
        {
            case 0: return HActive * 10 / 16;  // 16:10
            case 1: return HActive * 3 / 4;    // 4:3
            case 2: return HActive * 4 / 5;    // 5:4
            case 3: return HActive * 9 / 16;   // 16:9
            default: return 0;
        }
    }
}
public int RefreshRate => (AspectAndRefresh & 0x3F) + 60;
```

예를 들어 `0xD1 0xC0`라면:

- 가로: `(0xD1 + 31) × 8 = (209 + 31) × 8 = 1920`
- 종횡비: `(0xC0 >> 6) & 0x03 = 3` → 16:9 → 세로 = 1920 × 9 / 16 = 1080
- 재생률: `(0xC0 & 0x3F) + 60 = 0 + 60 = 60Hz`

결과: 1920×1080@60Hz

---

## 상세 타이밍 디스크립터 (DTD, 0x36–0x7D)

4개의 18바이트 슬롯 중 첫 번째는 대개 모니터의 네이티브 해상도를 나타내는 상세 타이밍 디스크립터(DTD)를 담습니다. 나머지 슬롯은 DTD이거나 특수 디스크립터일 수 있습니다.

```csharp
private static void ParseDescriptor(byte[] data, int offset, EdidBaseBlock block)
{
    // pixel clock != 0 → 상세 타이밍 디스크립터
    if (data[offset] != 0 || data[offset + 1] != 0)
    {
        var dtd = new DetailedTimingDescriptor();
        // 픽셀 클럭: 10kHz 단위
        dtd.PixelClockKHz10 = (ushort)(data[offset] | (data[offset + 1] << 8));
        // 가로 해상도: 8비트 + 상위 4비트 (byte[4]의 상위 니블)
        dtd.HActive   = data[offset + 2] | ((data[offset + 4] & 0xF0) << 4);
        dtd.HBlanking = data[offset + 3] | ((data[offset + 4] & 0x0F) << 8);
        dtd.VActive   = data[offset + 5] | ((data[offset + 7] & 0xF0) << 4);
        dtd.VBlanking = data[offset + 6] | ((data[offset + 7] & 0x0F) << 8);
        ...
    }
    else
    {
        // pixel clock == 0 → 디스플레이 디스크립터
        byte tag = data[offset + 3];
        switch (tag)
        {
            case 0xFC: // 모니터 이름
            case 0xFF: // 모니터 시리얼 문자열
            case 0xFD: // 주사율 범위 제한
        }
    }
}
```

### DTD 픽셀 클럭 계산

픽셀 클럭은 10kHz 단위 16비트 리틀 엔디언으로 저장됩니다.

```csharp
public double PixelClockMHz => PixelClockKHz10 * 0.01;
```

4K@60Hz 모니터라면 픽셀 클럭이 약 594MHz이므로 저장값은 59400이 됩니다. `0x08 0xE8` → `(0x08 | (0xE8 << 8))` = `0xE808` = 59400 → 594.00MHz.

### DTD 실제 재생률 계산

```csharp
public double RefreshRate
{
    get
    {
        if (HTotal == 0 || VTotal == 0) return 0;
        return (PixelClockKHz10 * 10000.0) / (HTotal * VTotal);
    }
}
```

총 수평 픽셀(HActive + HBlanking)과 총 수직 라인(VActive + VBlanking)을 곱한 값이 프레임당 총 픽셀 수입니다. 픽셀 클럭을 이로 나누면 초당 프레임 수, 즉 재생률이 나옵니다.

### 디스크립터 태그 유형

픽셀 클럭이 0인 슬롯은 `data[offset + 3]`의 태그 바이트로 유형을 식별합니다.

```csharp
public enum DescriptorTag : byte
{
    MonitorSerialNumber = 0xFF,   // 모니터 시리얼 문자열 (최대 13자)
    DataString          = 0xFE,   // 임의 ASCII 문자열
    MonitorRangeLimits  = 0xFD,   // GTF/CVT 주사율 범위 제한
    MonitorName         = 0xFC,   // 모니터 모델명 (최대 13자)
    ColorPoint          = 0xFB,   // 추가 색도 좌표
    StandardTimingId    = 0xFA,   // 추가 표준 타이밍 8개
    CVTTimingCodes      = 0xF8,   // CVT 3바이트 타이밍 코드
    EstablishedTimingsIII = 0xF7, // 확립된 타이밍 3 (추가)
    Dummy               = 0x10,   // 패딩
}
```

`MonitorRangeLimits` (0xFD) 디스크립터는 모니터가 지원하는 수직 주사율 범위(MinVRate ~ MaxVRate Hz)와 수평 주사율 범위(MinHRate ~ MaxHRate kHz), 최대 픽셀 클럭을 기록합니다. 가변 재생률(VRR) 모니터의 경우 이 범위가 특히 중요합니다.

---

## CTA-861 확장 블록 파싱

![CTA-861 확장 블록 구조](/images/posts/nvapi-gpu-controller/part3-cta861-extension.svg)

HDMI, DisplayPort 모니터는 거의 예외 없이 128번째 바이트(0x7E)가 1 이상이며, 이는 CTA-861 확장 블록이 뒤따름을 의미합니다. `byte[128]`부터 시작하는 두 번째 128바이트 블록입니다.

### CTA-861 블록 헤더

```csharp
var block = new CtaExtensionBlock
{
    Tag      = data[blockOffset],     // 0x02 = CTA-861
    Revision = data[blockOffset + 1], // 보통 0x03
    DTDOffset = data[blockOffset + 2], // 데이터 블록 끝 오프셋
    Flags    = data[blockOffset + 3]  // 기능 플래그
};
```

`Flags` 바이트의 각 비트는 다음을 의미합니다.

| 비트 | 의미 |
|------|------|
| 7 | 언더스캔 지원 |
| 6 | 기본 오디오 지원 |
| 5 | YCbCr 4:4:4 지원 |
| 4 | YCbCr 4:2:2 지원 |
| 3:0 | 네이티브 DTD 개수 |

### 데이터 블록 파싱 루프

각 데이터 블록은 1바이트 헤더로 시작합니다. 상위 3비트가 태그 코드, 하위 5비트가 페이로드 길이입니다.

```csharp
int pos = blockOffset + 4;
int dataEnd = blockOffset + block.DTDOffset;

while (pos < dataEnd && pos < blockOffset + 127)
{
    byte header = data[pos];
    int tag    = (header >> 5) & 0x07;  // 상위 3비트
    int length = header & 0x1F;          // 하위 5비트

    switch ((CtaDataBlockTag)tag)
    {
        case CtaDataBlockTag.Video:           // 태그 2
        case CtaDataBlockTag.Audio:           // 태그 1
        case CtaDataBlockTag.SpeakerAllocation: // 태그 4
        case CtaDataBlockTag.VendorSpecific:  // 태그 3
        case CtaDataBlockTag.Extended:        // 태그 7
    }

    pos += 1 + length;  // 헤더 1바이트 + 페이로드
}
```

### Video Data Block — VIC 코드

```csharp
private static CtaVideoDataBlock ParseVideoDataBlock(byte[] data, int offset, int length)
{
    var vdb = new CtaVideoDataBlock();
    for (int i = 0; i < length; i++)
        vdb.VicCodes.Add((byte)(data[offset + i] & 0x7F));  // bit7=네이티브 플래그 제거
    return vdb;
}
```

VIC(Video Identification Code)는 해상도와 재생률을 하나의 숫자로 식별합니다. 주요 VIC 코드 일부를 소개합니다.

| VIC | 해상도/재생률 |
|-----|-------------|
| 1 | 640×480p@59.94/60Hz |
| 16 | 1920×1080p@59.94/60Hz |
| 97 | 3840×2160p@59.94/60Hz |
| 104 | 3840×2160p@119.88/120Hz |
| 214 | 7680×4320p@59.94/60Hz (8K) |

코드는 최대 255개(1바이트)이며, HDMI 2.1부터는 확장 VIC를 별도 블록으로 수용합니다.

### Audio Data Block — 오디오 포맷

각 오디오 디스크립터는 3바이트입니다.

```csharp
adb.Descriptors.Add(new CtaAudioDescriptor
{
    FormatCode  = (byte)((data[offset + i] >> 3) & 0x0F),    // 상위 4비트
    MaxChannels = (byte)((data[offset + i] & 0x07) + 1),     // 하위 3비트 + 1
    SampleRates = data[offset + i + 1],  // 비트맵: 32/44.1/48/88.2/96/176.4/192kHz
    BitDepths   = data[offset + i + 2],  // 비트맵: 16/20/24비트
});
```

포맷 코드 1은 LPCM(비압축 PCM), 2는 AC-3, 7은 DTS, 11은 DTS-HD, 12는 Dolby TrueHD(MAT/MLP)입니다.

### Speaker Allocation Data Block

```csharp
public class CtaSpeakerAllocation
{
    public byte Data { get; set; }
    public bool FrontLeftRight => (Data & 0x01) != 0;  // FL/FR
    public bool LFE            => (Data & 0x02) != 0;  // 서브우퍼
    public bool FrontCenter    => (Data & 0x04) != 0;  // FC
    public bool RearLeftRight  => (Data & 0x08) != 0;  // RL/RR
    public bool RearCenter     => (Data & 0x10) != 0;  // RC
}
```

5.1 채널 스피커 구성의 경우 `Data = 0x07` (FL/FR + LFE + FC)가 됩니다.

### HDMI Vendor Specific Data Block

IEEE OUI `03-0C-00`으로 HDMI 벤더 블록임을 식별합니다.

```csharp
private static HdmiVendorBlock ParseHdmiVendorBlock(byte[] data, int offset, int length)
{
    // OUI 검증
    if (data[offset] != 0x03 || data[offset + 1] != 0x0C || data[offset + 2] != 0x00)
        return null;

    var hvb = new HdmiVendorBlock();
    if (length >= 6)
    {
        byte dcFlags = data[offset + 5];
        hvb.SupportsAI     = (dcFlags & 0x80) != 0;   // Audio Infoframe
        hvb.DeepColor48bit = (dcFlags & 0x40) != 0;   // 16비트/채널
        hvb.DeepColor36bit = (dcFlags & 0x20) != 0;   // 12비트/채널
        hvb.DeepColor30bit = (dcFlags & 0x10) != 0;   // 10비트/채널
    }
    if (length >= 7)
        hvb.MaxTmdsClock5MHz = data[offset + 6];  // 5MHz 단위
    return hvb;
}
```

예를 들어 `MaxTmdsClock5MHz = 60`이면 최대 TMDS 클럭이 300MHz입니다. HDMI 1.4는 최대 340MHz, HDMI 2.0은 최대 600MHz입니다.

---

## Extended Data Block — HDR과 색역

태그 7(Extended) 블록은 확장 태그 바이트로 세부 종류를 구분합니다.

### HDR 정적 메타데이터 (ExtTag=0x06)

```csharp
block.HdrMetadata = new HdrStaticMetadata
{
    SupportedEotf        = data[offset + 1],
    SupportedSmType      = data[offset + 2],
    MaxLuminance         = length >= 4 ? data[offset + 3] : (byte)0,
    MaxFrameAvgLuminance = length >= 5 ? data[offset + 4] : (byte)0,
    MinLuminance         = length >= 6 ? data[offset + 5] : (byte)0,
};
```

EOTF(전자 광학 전달 함수) 지원 비트맵은 다음과 같습니다.

```csharp
public bool SupportsSDR => (SupportedEotf & 0x01) != 0;  // 전통 SDR
public bool SupportsHDR => (SupportedEotf & 0x02) != 0;  // HDR (BT.1886)
public bool SupportsPQ  => (SupportedEotf & 0x04) != 0;  // Perceptual Quantizer (HDR10)
public bool SupportsHLG => (SupportedEotf & 0x08) != 0;  // Hybrid Log-Gamma
```

휘도 값은 `100 × 2^(MaxLuminance / 32)` cd/m² 공식으로 디코딩합니다. 일반 HDR 모니터라면 최대 휘도 600–1000 nits, 최소 휘도 0.01–0.05 nits 수준입니다.

### 색역 (Colorimetry, ExtTag=0x05)

```csharp
public class ColorimetryData
{
    public byte Data { get; set; }
    public bool xvYCC601  => (Data & 0x01) != 0;
    public bool xvYCC709  => (Data & 0x02) != 0;
    public bool BT2020cYCC => (Data & 0x20) != 0;
    public bool BT2020YCC  => (Data & 0x40) != 0;
    public bool BT2020RGB  => (Data & 0x80) != 0;
}
```

HDR10을 지원하는 모니터는 일반적으로 BT.2020 색역도 함께 지원하므로 `Data & 0xE0`이 0이 아닙니다.

### HDMI Forum VSDB (ExtTag=0x0B) — HDMI 2.1 기능

```csharp
block.HdmiForumData = new HdmiForumVSDB
{
    MaxTmdsClock = data[offset + 1],
    Flags1       = data[offset + 4],
    Flags2       = data[offset + 5],
    MaxFrlRate   = data[offset + 6],
};
```

`MaxFrlRate`는 FRL(Fixed Rate Link) 최대 속도를 나타냅니다. HDMI 2.1의 FRL은 TMDS를 대체하는 새 물리 레이어입니다.

```csharp
public int MaxFrlRateGbps
{
    get {
        switch (MaxFrlRate & 0x0F)
        {
            case 1: return 9;   // 3레인 × 3Gbps
            case 2: return 18;  // 3레인 × 6Gbps
            case 3: return 24;  // 4레인 × 6Gbps
            case 4: return 32;  // 4레인 × 8Gbps
            case 5: return 40;  // 4레인 × 10Gbps
            case 6: return 48;  // 4레인 × 12Gbps (최대)
            default: return 0;  // TMDS 전용
        }
    }
}
```

4K@120Hz나 8K@60Hz를 구현하려면 최소 FRL 5 (40Gbps)가 필요합니다.

---

## 파일 I/O — EDID 저장과 로딩

`EdidFileIO.cs`는 다양한 포맷으로 EDID를 저장하고 로딩하는 기능을 제공합니다.

### 파일 포맷 자동 감지

```csharp
public static byte[] LoadFromFile(string path)
{
    string ext = Path.GetExtension(path).ToLower();

    // 바이너리 파일: 원시 바이트
    if (ext == ".bin")
        return File.ReadAllBytes(path);

    string text = File.ReadAllText(path, Encoding.ASCII);

    // 형식 1: <D00FFFFFF...> — 꺾쇠 괄호 HEX
    if (text.Contains("<D"))
        return ParseAngleBracketFormat(text);

    // 형식 2: EDID BYTES: 테이블
    if (text.Contains("EDID BYTES:"))
        return ParseTableFormat(text);

    // 형식 3: 순수 HEX 문자열
    string cleaned = Regex.Replace(text, @"[^0-9A-Fa-f]", "");
    if (cleaned.Length >= 256)
        return HexStringToBytes(cleaned);

    // 폴백: 바이너리 헤더 확인
    var raw = File.ReadAllBytes(path);
    if (raw.Length >= 128 && raw[0] == 0x00 && raw[1] == 0xFF)
        return raw;

    return null;
}
```

세 가지 텍스트 포맷을 지원하는 이유는 시중에 EDID를 다루는 다양한 도구들이 서로 다른 포맷을 사용하기 때문입니다. `<D...>` 형식은 일부 모니터 설정 유틸리티가 사용하는 포맷이고, 테이블 형식은 16진수 덤프 형태로 사람이 읽기 쉬운 포맷입니다.

### 저장 포맷 선택

```csharp
// 바이너리 저장 (가장 작고 범용적)
EdidFileIO.SaveAsBinary("monitor.bin", edidData);

// 꺾쇠 형식 TXT
EdidFileIO.SaveAsAngleBracketTxt("monitor.txt", edidData);
// 결과: <D00FFFFFF FFFFFF0043...>

// 테이블 형식 DAT
EdidFileIO.SaveAsTableDat("monitor.dat", edidData);
// 결과: EDID BYTES:
//       0x    00 01 02 ...
//       00 | 00 FF FF FF ...
//       10 | 4C 2D ...
```

---

## 실제 EDID 헥스 덤프 읽기

파서가 생성하는 헥스 덤프를 이해하는 것도 디버깅에 중요합니다. `EdidParser.ToHexDump()`는 아래와 같은 형식을 출력합니다.

```
     00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F   ASCII
     -----------------------------------------------   ----------------
0000 00 FF FF FF FF FF FF 00 4C 2D E8 08 01 01 01 01   ........L-......
0010 21 1A 01 03 80 3C 22 78 0A CF 74 A3 57 4C 9D 24   !.....<"x..t.WL.$
0020 11 50 54 BF EF 80 D1 C0 81 C0 81 80 A9 C0 B3 00   .PT.............
0030 95 00 81 40 02 3A 80 18 71 38 2D 40 58 2C 45 00   ...@.:..q8-@X,E.
0040 ...
```

첫 번째 행에서 `4C 2D`는 제조사 ID SAM(삼성)이고, `E8 08`은 리틀 엔디언으로 제품 코드 0x08E8 = 2280임을 알 수 있습니다. `0x3C 0x22`(60, 34)는 60×34cm 화면, `0x78`(120)은 감마 2.20을 나타냅니다.

---

## 마무리

이번 편에서는 EDID의 128바이트 베이스 블록부터 CTA-861 확장 블록까지 바이트 단위로 파헤쳤습니다. 핵심 내용을 정리하면 다음과 같습니다.

- **헤더 매직**: `00 FF FF FF FF FF FF 00`으로 EDID 식별
- **체크섬**: 128바이트 합의 mod 256이 0이어야 함
- **제조사 ID**: 3글자 알파벳을 5비트씩 패킹해 2바이트로 압축
- **DTD vs 디스크립터**: byte[0,1]이 0이 아니면 타이밍, 0이면 태그 기반 디스크립터
- **CTA-861**: 각 데이터 블록이 3비트 태그 + 5비트 길이 헤더로 시작
- **확장 태그**: HDR, 색역, HDMI Forum VSDB는 Extended(태그 7) 블록의 서브타입
- **NVAPI 읽기**: 256바이트 청크 단위 반복 호출로 전체 EDID 수집

다음 편에서는 이렇게 파싱한 EDID 데이터를 WinForms UI에서 표시하고 수정하는 방법, 그리고 수정된 EDID를 다시 GPU에 주입하는 과정을 다룹니다.
