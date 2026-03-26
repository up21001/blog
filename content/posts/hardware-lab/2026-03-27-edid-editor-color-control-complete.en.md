---
title: "Building an NVIDIA GPU Controller (5) — EDID Editor and Color Control Complete"
date: 2026-03-27T13:00:00+09:00
lastmod: 2026-03-27T13:00:00+09:00
description: "Completing the GPU controller with EDID editor implementation and color control. The final installment reviews the full architecture of the series."
slug: "edid-editor-color-control-complete"
categories: ["hardware-lab"]
tags: ["EDID", "색상제어", "GPU", "NVAPI", "C#", "WinForms"]
featureimage: "/images/posts/nvapi-gpu-controller/part5-complete-app-en.svg"
series: ["NVIDIA GPU Controller Dev Log 2026"]
series_order: 5
draft: false
---

This is the final installment of the series. We've covered NVAPI initialization, GPU and display information queries, and custom resolutions up to this point. Now we implement the project's highlights — the **EDID editor** and **color control** — and bring the entire application to completion.

---

## What Is EDID Editing

EDID (Extended Display Identification Data) is a 128-byte (or 256-byte+ for extensions) structure that a monitor uses to advertise its capabilities to the graphics card. It is exchanged automatically over the DDC/CI channel upon connection, and the GPU driver uses this data to determine supported resolutions, color depth, HDR support, and more.

There are many reasons you might need to edit EDID:

- The monitor lies — some budget monitors declare features in EDID that they don't actually support
- KVM switches or HDMI splitters corrupt or strip the EDID
- You need to force-register a specific resolution/refresh rate combination
- You want to manually adjust HDR-related flags

NVAPI provides `NvAPI_GPU_GetEDID` / `NvAPI_GPU_SetEDID` functions that let you read and override EDID at the GPU driver level.

---

## EdidEditor Class Design

`EdidEditor` wraps a 128-byte raw array and provides type-safe methods for modifying individual EDID fields.

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

Making a copy to protect the original is the first design decision. If you accidentally corrupt the original while editing, there's no way to recover it.

### Creating a Blank EDID

Use `CreateBlank()` when you need to build a new EDID without an existing monitor.

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

The EDID header always starts with fixed magic bytes (`00 FF FF FF FF FF FF 00`). Verifying these bytes is the first step of any validation.

---

## Manufacturer ID Encoding — Into the World of Bit Packing

One of the most interesting aspects of EDID is manufacturer ID encoding. A 3-character ASCII string (e.g., "SAM", "DEL", "LEN") is packed into 16 bits across 2 bytes.

The rules are:
- Only the lower 5 bits of each alphabetic character are used (A=1, B=2, ..., Z=26)
- Three 5-bit values are packed into 15 bits
- The most significant bit (MSB) is always 0

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

Take "SAM" as an example:
- S = 19 (10011₂)
- A = 1  (00001₂)
- M = 13 (01101₂)

Packed: `[0][10011][00001][01101]` → `0100 1100` `0010 1101` → `0x4C 0x2D`

```csharp
public void SetManufacturerId(string id)
{
    var encoded = EdidParser.EncodeManufacturerId(id);
    _data[8] = encoded[0];
    _data[9] = encoded[1];
    UpdateChecksum();
}
```

This bit manipulation is a scheme designed in the IBM PC era of the 1980s — a clever way to fit a 3-character compressed alphabet into just 2 bytes.

---

## Product Code and Serial Number

The product code is a little-endian 16-bit integer:

```csharp
public void SetProductCode(ushort code)
{
    _data[10] = (byte)(code & 0xFF);       // low byte first
    _data[11] = (byte)(code >> 8);          // high byte
    UpdateChecksum();
}
```

The serial number is a 32-bit little-endian value:

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

The manufacture date stores week and year as individual bytes. The year is offset from 1990:

```csharp
public void SetManufactureDate(byte week, int year)
{
    _data[16] = week;
    _data[17] = (byte)(year - 1990);  // offset from year 1990
    UpdateChecksum();
}
```

For 2026, `data[17]` would be `36`.

---

## Digital Input and Color Depth

EDID byte 20 is the video input parameters byte. It encodes both whether the input is digital and the color depth.

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
        // bit 7: digital(1), bits 6-4: color depth code
        _data[20] = (byte)(0x80 | (depthCode << 4));
    }
    else
    {
        _data[20] = 0x00;  // analog
    }
    UpdateChecksum();
}
```

For 8bpc digital: `0x80 | (2 << 4)` = `0xA0`.

---

## Detailed Timing Descriptor (DTD) Editing

The DTD is the core of EDID. An 18-byte block encodes all timing parameters. Up to four DTD slots are located at offsets 54–125.

```csharp
public void SetDetailedTiming(int descriptorIndex, DetailedTimingDescriptor dtd)
{
    if (descriptorIndex < 0 || descriptorIndex >= 4) return;
    int offset = 54 + descriptorIndex * 18;

    // Pixel clock (in units of 10kHz, little-endian)
    _data[offset]     = (byte)(dtd.PixelClockKHz10 & 0xFF);
    _data[offset + 1] = (byte)(dtd.PixelClockKHz10 >> 8);

    // H Active + H Blanking (each 12-bit, upper 4 bits combined into byte 4)
    _data[offset + 2] = (byte)(dtd.HActive & 0xFF);
    _data[offset + 3] = (byte)(dtd.HBlanking & 0xFF);
    _data[offset + 4] = (byte)(((dtd.HActive >> 4) & 0xF0) | ((dtd.HBlanking >> 8) & 0x0F));

    // V Active + V Blanking
    _data[offset + 5] = (byte)(dtd.VActive & 0xFF);
    _data[offset + 6] = (byte)(dtd.VBlanking & 0xFF);
    _data[offset + 7] = (byte)(((dtd.VActive >> 4) & 0xF0) | ((dtd.VBlanking >> 8) & 0x0F));

    // Porch/Sync widths (H is 10-bit, V is 6-bit)
    _data[offset + 8]  = (byte)(dtd.HFrontPorch & 0xFF);
    _data[offset + 9]  = (byte)(dtd.HSyncWidth & 0xFF);
    _data[offset + 10] = (byte)(((dtd.VFrontPorch & 0x0F) << 4) | (dtd.VSyncWidth & 0x0F));
    _data[offset + 11] = (byte)(
        ((dtd.HFrontPorch >> 2) & 0xC0) | ((dtd.HSyncWidth >> 4) & 0x30) |
        ((dtd.VFrontPorch >> 2) & 0x0C) | ((dtd.VSyncWidth >> 4) & 0x03));

    // Image size (mm, each 12-bit)
    _data[offset + 12] = (byte)(dtd.HImageSizeMm & 0xFF);
    _data[offset + 13] = (byte)(dtd.VImageSizeMm & 0xFF);
    _data[offset + 14] = (byte)(((dtd.HImageSizeMm >> 4) & 0xF0) | ((dtd.VImageSizeMm >> 8) & 0x0F));

    _data[offset + 15] = dtd.HBorderPixels;
    _data[offset + 16] = dtd.VBorderPixels;
    _data[offset + 17] = dtd.Features;  // 0x18 = digital separate sync

    UpdateChecksum();
}
```

Horizontal/vertical resolution, blanking, front porch, sync width, and physical dimensions are all crammed into 18 bytes. Each parameter is distributed across multiple bytes at the bit level — misunderstand the order and you'll get completely wrong timings.

---

## Monitor Name and Range Limit Descriptor

The 18-byte slots that aren't DTDs are used as text descriptors or range limits. They're distinguished by a tag byte (`data[offset+3]`).

```csharp
private void SetDescriptorString(DescriptorTag tag, string text)
{
    // Find existing slot → allocate an empty slot if none found
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
    // ...after securing a slot:

    // Max 13 chars, terminated with 0x0A (LF), rest padded with 0x20 (space)
    byte[] strBytes = Encoding.ASCII.GetBytes(text);
    int j = 0;
    for (; j < strBytes.Length && j < 13; j++)
        _data[targetOffset + 5 + j] = strBytes[j];
    if (j < 13)
    {
        _data[targetOffset + 5 + j] = 0x0A;  // line feed as terminator
        j++;
    }
    for (; j < 13; j++)
        _data[targetOffset + 5 + j] = 0x20;  // space padding

    UpdateChecksum();
}
```

Monitor names are limited to 13 characters. `0x0A` (LF) is the string terminator, and the remainder is padded with spaces. Skipping this padding rule causes some drivers or operating systems to misread the name.

Range limits declare the monitor's vertical and horizontal refresh rate ranges and maximum pixel clock:

```csharp
public void SetRangeLimits(byte minV, byte maxV, byte minH, byte maxH,
                            byte maxPixelClockMHz10)
{
    // offset 5: minimum vertical refresh rate (Hz)
    // offset 6: maximum vertical refresh rate (Hz)
    // offset 7: minimum horizontal refresh rate (kHz)
    // offset 8: maximum horizontal refresh rate (kHz)
    // offset 9: maximum pixel clock (in units of 10MHz)
    _data[targetOffset + 5] = minV;
    _data[targetOffset + 6] = maxV;
    _data[targetOffset + 7] = minH;
    _data[targetOffset + 8] = maxH;
    _data[targetOffset + 9] = maxPixelClockMHz10;
    _data[targetOffset + 10] = 0x00;  // default GTF
    for (int i = 11; i < 18; i++)
        _data[targetOffset + i] = 0x0A;
    UpdateChecksum();
}
```

---

## Checksum Calculation

The last byte of EDID (offset 127) is the checksum. The sum of bytes 0–126 plus byte 127 must be a multiple of 256.

```csharp
public void UpdateChecksum()
{
    if (_data.Length >= 128)
        _data[127] = EdidParser.CalculateChecksum(_data, 0, 128);

    // Update checksum for each extension block as well
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

The checksum calculation logic:

```csharp
public static byte CalculateChecksum(byte[] data, int offset, int length)
{
    byte sum = 0;
    for (int i = offset; i < offset + length - 1; i++)
        sum += data[i];
    return (byte)(256 - (sum % 256));
}
```

Since every `Set*` method calls `UpdateChecksum()` automatically at the end, the caller never needs to think about it. The only exception is raw editing via `SetByte()` — in that case, you need to call it manually at the end.

![EDID Edit Workflow](/images/posts/nvapi-gpu-controller/part5-edid-edit-workflow-en.svg)

---

## Color Control — NvColorControl Multi-Version Fallback

NVAPI's color control structs vary by driver version. Three versions exist — V1, V3, and V5 — and the code tries them in order from newest to oldest, falling back to the previous version on an `IncompatibleStructVersion` error.

### Struct Definitions

**V5 (16 bytes) — for the latest drivers:**

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
    [FieldOffset(12)] public byte ColorSpaceId;      // added in V5
}
```

**V3 (12 bytes) — for mid-range drivers:**

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

**V1 (12 bytes) — for older drivers:**

V3 and V1 share the same memory layout. The only practical difference is the version number in the `Version` field. Even with an identical struct, the driver handles it differently based on that version code.

### Version Field Packing Rule

Across all of NVAPI, the `Version` field follows this rule:

```
Version = (struct size in bytes) | (version number << 16)
```

For V5: `16 | (5 << 16)` = `0x00050010`
For V3: `12 | (3 << 16)` = `0x0003000C`

This packing lets the driver validate both the struct size and version in a single integer.

### Fallback Chain Implementation

```csharp
public static NvStatus SetColorControl(
    uint displayId,
    NvColorDepth depth,
    NvColorFormat format,
    NvDynamicRange range)
{
    NvStatus status;

    // Try V5 (latest drivers)
    var v5 = NvColorControlV5.CreateSet(depth, format, range);
    status = NvApiWrapper.DISP_ColorControlV5(displayId, ref v5);
    if (status == NvStatus.OK) return status;
    if (status != NvStatus.IncompatibleStructVersion)
    {
        Logger.Error($"ColorControl v5 error: {NvApiWrapper.GetErrorMessage(status)}");
        return status;
    }

    // Try V3
    var v3 = NvColorControlV3.CreateSet(depth, format, range);
    status = NvApiWrapper.DISP_ColorControlV3(displayId, ref v3);
    if (status == NvStatus.OK) return status;
    if (status != NvStatus.IncompatibleStructVersion)
    {
        Logger.Error($"ColorControl v3 error: {NvApiWrapper.GetErrorMessage(status)}");
        return status;
    }

    // Try V1 (last resort for old drivers)
    var v1 = NvColorControlV1.CreateSet(depth, format, range);
    status = NvApiWrapper.DISP_ColorControlV1(displayId, ref v1);
    if (status == NvStatus.OK) return status;

    Logger.Error($"All ColorControl versions failed: {NvApiWrapper.GetErrorMessage(status)}");
    return status;
}
```

The code only advances to the next version on `IncompatibleStructVersion` (-9). Any other error — such as `InvalidArgument` or `NotSupported` — returns immediately. Silently swallowing all errors hides the real problem.

### Color Setting Options

```csharp
public enum NvColorDepth : byte
{
    Default = 0,  // driver decides automatically
    Bpc6    = 1,
    Bpc8    = 2,  // most SDR monitors
    Bpc10   = 3,  // recommended for HDR10, WCG
    Bpc12   = 4,
    Bpc16   = 5,
}

public enum NvColorFormat : byte
{
    RGB     = 0,  // standard for PC monitors
    YUV422  = 1,  // HDMI bandwidth saving (for 4K@60Hz bandwidth limits)
    YUV444  = 2,  // TV full chroma
    Default = 3,
}

public enum NvDynamicRange : byte
{
    Auto    = 0,
    Limited = 1,  // 16-235, TV standard
    Full    = 2,  // 0-255, PC standard
}
```

For proper HDR content viewing, `Bpc10 + RGB + Limited` is the typical combination. For SDR work on a PC monitor, `Bpc8 + RGB + Full` is correct.

![Color Control Pipeline](/images/posts/nvapi-gpu-controller/part5-color-control-en.svg)

---

## EdidEditorPanel — UI Design

`EdidEditorPanel` inherits from `UserControl` and is organized into three main areas.

```csharp
public class EdidEditorPanel : UserControl
{
    private SplitContainer splitMain;    // left: tree view / right: hex + edit form
    private SplitContainer splitRight;   // upper right: hex editor / lower right: edit fields

    private TreeView treeEdid;           // parsed EDID tree
    private TextBox hexEditor;           // raw hex dump
    // edit fields (TextBox, NumericUpDown, ComboBox...)
}
```

The hex editor uses a dark theme:

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

### Reading and Loading EDID

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
    hexEditor.Text = EdidParser.ToHexDump(data);  // update hex view

    var parsed = EdidParser.Parse(data);
    PopulateEditFields(parsed);   // fill edit fields
    PopulateTree(parsed, data);   // build tree view
}
```

When data is loaded, three views update simultaneously: the hex editor, the edit form, and the tree view.

### Applying Edits

```csharp
private void BtnApplyEdits_Click(object sender, EventArgs e)
{
    if (_editor == null)
        _editor = EdidEditor.CreateBlank();  // create blank EDID if none exists

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

    // refresh views
    _currentEdidRaw = _editor.Data;
    hexEditor.Text = EdidParser.ToHexDump(_editor.Data);
    PopulateTree(EdidParser.Parse(_editor.Data), _editor.Data);
}
```

### DTD Editing

A combo box selects the DTD slot index, and each timing parameter is entered via `NumericUpDown` controls:

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
        Features    = 0x18  // digital separate sync
    };

    _editor.SetDetailedTiming(idx, dtd);
    hexEditor.Text = EdidParser.ToHexDump(_editor.Data);
    PopulateTree(EdidParser.Parse(_editor.Data), _editor.Data);
}
```

---

## Applying and Removing EDID Overrides

### Validation Before Applying

```csharp
private void BtnApplyOverride_Click(object sender, EventArgs e)
{
    // header check
    if (!EdidParser.ValidateHeader(_currentEdidRaw))
    {
        var r = MessageBox.Show("The EDID header is invalid. Apply anyway?",
            "Invalid EDID", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
        if (r != DialogResult.Yes) return;
    }

    // checksum check
    if (!EdidParser.ValidateChecksum(_currentEdidRaw))
    {
        var r = MessageBox.Show("The checksum is invalid. Auto-correct and apply?",
            "Invalid Checksum", MessageBoxButtons.YesNoCancel, MessageBoxIcon.Warning);
        if (r == DialogResult.Cancel) return;
        if (r == DialogResult.Yes)
            _currentEdidRaw[127] = EdidParser.CalculateChecksum(_currentEdidRaw, 0, 128);
    }

    var status = NvEdid.WriteEDID(display.GpuHandle, display.OutputId, _currentEdidRaw);
    if (status == NvStatus.OK)
        MessageBox.Show("EDID override applied. A reboot may be required.");
}
```

Two validation steps before applying: header validity (magic byte check) and checksum validity. Checksum errors offer an auto-correct option.

### Removing the Override

```csharp
private void BtnRemoveOverride_Click(object sender, EventArgs e)
{
    var status = NvEdid.RemoveEDIDOverride(display.GpuHandle, display.OutputId);
    if (status == NvStatus.OK)
        MessageBox.Show("EDID override removed. Reverting to the monitor's original EDID.");
}
```

Passing empty data to `NvAPI_GPU_SetEDID` or calling a dedicated removal function causes the driver to revert to the original EDID.

---

## File I/O — Four Format Support

The ability to export and import EDID to and from files is essential for testing and sharing.

```
Save formats:
- .bin   — raw binary (128/256 bytes as-is)
- .dat   — registry table format (Windows Registry Editor compatible)
- .txt   — angle bracket format (<EDID>...</EDID>)
- .hex   — hex text (16 bytes per line)
```

Loading supports the same four formats, with the format detected automatically from the file extension:

```csharp
dlg.Filter = "All EDID Files|*.bin;*.dat;*.txt|Binary (*.bin)|*.bin|" +
             "DAT Table (*.dat)|*.dat|Hex Text (*.txt)|*.txt|All Files (*.*)|*.*";
```

---

## Complete Application Structure

![Complete Application Architecture](/images/posts/nvapi-gpu-controller/part5-complete-app-en.svg)

`MainForm` consists of four tab panels, a bottom log view, and a status bar:

```csharp
public partial class MainForm : Form
{
    private TabControl tabControl;
    private GpuInfoPanel gpuInfoPanel;          // GPU information
    private DisplayPanel displayPanel;           // display management
    private CustomResolutionPanel customResPanel; // custom resolution
    private EdidEditorPanel edidPanel;           // EDID editor
    private TextBox logTextBox;                  // real-time log
    private StatusStrip statusStrip;             // GPU/driver/display count
}
```

If NVAPI initialization fails, the app runs in a limited mode where only EDID file editing is available:

```csharp
private void SetUiDisabled()
{
    gpuInfoPanel.Enabled = false;
    displayPanel.Enabled = false;
    customResPanel.Enabled = false;
    // EDID tab remains usable for file editing
    Logger.Warn("Running in limited mode - EDID file editing only");
}
```

This design means the app can still be used to open, edit, and save EDID files even in environments without an NVIDIA GPU.

---

## Problems Encountered During Implementation

### 1. NvEdidV3's 256-Byte Buffer Limit

```csharp
[StructLayout(LayoutKind.Sequential)]
public struct NvEdidV3
{
    public uint Version;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 256)]
    public byte[] EdidData;  // fixed maximum of 256 bytes
    public uint EdidSize;
    public uint EdidId;
    public uint Offset;      // page offset (for reading extension blocks)
}
```

If the EDID exceeds 256 bytes (rare, but it happens), you need to call the function multiple times while incrementing `Offset`. I initially didn't know this and always read only 128 bytes, missing the CTA-861 extension block entirely.

### 2. Color Control Version Confusion

V1 and V3 have identical memory layouts. At first I couldn't understand why two versions existed. NVAPI uses the version number in the `Version` field to determine which feature set the driver supports. Even with the same struct, the driver handles different version numbers differently.

### 3. DTD Bit Packing Error

In the initial implementation of `SetDetailedTiming`, I miscalculated the byte that combines the upper bits of H/V (offsets 4 and 7). I was doing `HActive >> 4`, which brought down all the lower bits too. The correct code is `(HActive >> 4) & 0xF0` — only the upper 4 bits should be preserved.

### 4. Reboot Required After EDID Override

The `WriteEDID` call itself succeeds, but not all changes take effect immediately. In particular, changes to the monitor name or HDR flags often require a driver restart or a full system reboot. Displaying a clear guidance message in the UI is important.

---

## Retrospective — Wrapping Up the Series

NvGpuController is now complete across five installments. Looking back, the part that consumed the most time was — somewhat surprisingly — interpreting NVAPI documentation. NVAPI has sparse official documentation, struct definitions are scattered across header files, and the differences between versions are often impossible to know without actually trying them.

**What went well:**

- **The fallback chain pattern** — the V5 → V3 → V1 color control fallback is a robust design that works regardless of driver version.
- **EdidEditor's automatic checksum** — since every `Set*` method updates the checksum automatically, users always have valid data even without knowing EDID's internal structure.
- **Limited mode** — enabling EDID file editing without NVAPI was a practical choice that paid off.

**What could be better:**

- **Real-time hex editing** — the current flow updates the hex view after field edits, but editing hex directly doesn't update the fields. Bidirectional synchronization is needed.
- **CTA-861 extension block writing** — reading is complete, but writing (particularly HDR metadata and adding VIC codes) is not yet implemented.
- **Tree view interaction** — selecting a tree node should highlight the corresponding byte in the hex editor, but `TreeEdid_AfterSelect` is currently a no-op.

**Future improvements:**

1. CTA-861 extension block editing (HDR support, audio format declarations)
2. Bidirectional sync between hex editor and edit form
3. EDID version comparison (diff view between original and edited)
4. Integration with a known monitor database (Monitorinfo.net API, etc.)
5. Command-line mode (scripting and automation support)

---

## Closing

NvGpuController covers many facets of low-level hardware control — from P/Invoke bindings for NVAPI to EDID bit packing to multi-version fallbacks. Working with a GPU directly from C# and WinForms turned out to be far more interesting than expected, and the project gave me a concrete understanding of what data actually flows between a monitor and a GPU.

The source code is the result of building incrementally throughout this series. If you're working on a similar project, I hope the EDID bit packing details and the NVAPI Version field packing rule in particular prove useful as a reference.
