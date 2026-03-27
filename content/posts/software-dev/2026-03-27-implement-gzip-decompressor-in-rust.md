---
title: "Rust로 250줄 만에 Gzip 압축 해제기 구현하기 — 단계별 실습 가이드"
date: 2026-03-27T23:59:36+09:00
lastmod: 2026-03-27T23:59:36+09:00
description: "Rust의 강력한 성능을 활용하여 Gzip(DEFLATE) 압축 해제 알고리즘의 원리를 이해하고, 250줄 이내의 코드로 직접 구현해 봅니다."
slug: "implement-gzip-decompressor-in-rust"
categories: ["software-dev"]
tags: ["rust", "gzip", "deflate", "algorithm", "tutorial"]
draft: false
---

이 튜토리얼에서는 압축 알고리즘의 표준이라 할 수 있는 Gzip(GNU zip)의 압축 해제기를 Rust 언어를 사용하여 밑바닥부터 직접 구현해 봅니다. Gzip의 핵심인 DEFLATE 알고리즘(LZ77 + 허프만 코딩)의 동작 원리를 깊이 있게 이해하고, 외부 라이브러리 없이 순수 Rust 코드 250줄 내외로 동작하는 압축 해제기를 완성하는 것이 목표입니다.

![Gzip 파일의 전체적인 구조를 보여주는 다이어그램. 파일은 Gzip 헤더, DEFLATE 압축 데이터 블록, 그리고 Gzip 푸터(CRC32 및 원본 데이터 크기)로 구성됨을 바이트 단위로 시각화합니다.](/images/posts/implement-gzip-decompressor-in-rust/svg-1.svg)

**배울 내용**
* Gzip 파일 포맷의 헤더 및 푸터 구조 분석
* 비트 단위 데이터를 읽기 위한 Bit Reader 구현 기법
* 정규 허프만 트리(Canonical Huffman Tree)의 생성 및 디코딩 원리
* LZ77 알고리즘의 슬라이딩 윈도우(Sliding Window)를 이용한 데이터 복원
* DEFLATE 알고리즘의 동적 허프만(Dynamic Huffman) 블록 파싱

**사전 요구사항**
* **OS**: Windows, macOS, Linux 등 Rust 지원 운영체제
* **언어**: Rust (Edition 2021, 버전 1.60 이상 권장)
* **기타**: 기본적인 비트 연산(Bitwise operation)에 대한 이해

![image-1.png](/images/posts/implement-gzip-decompressor-in-rust/image-1.png)

---

## 환경 설정

먼저 새로운 Rust 프로젝트를 생성합니다. 외부 압축 해제 크레이트(crate)는 사용하지 않으며, 오직 Rust의 표준 라이브러리만을 사용하여 알고리즘의 본질에 집중합니다.

```bash
# 새로운 바이너리 프로젝트 생성
cargo new mini_gzip
cd mini_gzip
```

프로젝트가 생성되면 `src/main.rs` 파일을 열어 코드를 작성할 준비를 합니다. 테스트를 위해 간단한 텍스트 파일을 Gzip으로 압축하여 프로젝트 루트에 준비해 두는 것이 좋습니다.

```bash
# 테스트용 압축 파일 생성 (Linux/macOS 기준)
echo "Hello, Rust! This is a simple gzip decompression test. Rust is fast and safe." > test.txt
gzip test.txt
# test.txt.gz 파일이 생성됩니다.
```

---

## 단계 1: Gzip 파일 구조 이해 및 헤더 파싱

Gzip 파일은 단순히 압축된 데이터만 있는 것이 아니라, 파일의 메타데이터를 담고 있는 헤더(Header)와 무결성 검증을 위한 푸터(Footer)로 감싸져 있습니다. 

Gzip 헤더는 최소 10바이트로 구성되며 다음과 같은 구조를 가집니다:
1. **ID1 (1 byte)**: 매직 넘버 `0x1F`
2. **ID2 (1 byte)**: 매직 넘버 `0x8B`
3. **CM (1 byte)**: 압축 방식 (8 = DEFLATE)
4. **FLG (1 byte)**: 플래그 (파일 이름, 코멘트 등의 존재 여부)
5. **MTIME (4 bytes)**: 수정 시간
6. **XFL (1 byte)**: 추가 플래그
7. **OS (1 byte)**: 운영체제 정보

![image-2.png](/images/posts/implement-gzip-decompressor-in-rust/image-2.png)

우선 파일을 읽고 이 10바이트 헤더를 검증하는 코드를 작성해 봅니다. 플래그에 따라 가변적인 추가 데이터(예: 원본 파일명)가 존재할 수 있으므로 이를 건너뛰는 로직도 필요합니다.

```rust
use std::fs::File;
use std::io::{self, Read};

pub struct GzipDecoder<R: Read> {
    reader: R,
}

impl<R: Read> GzipDecoder<R> {
    pub fn new(mut reader: R) -> io::Result<Self> {
        let mut header = [0u8; 10];
        reader.read_exact(&mut header)?;

        // 매직 넘버 및 압축 방식 검증
        if header[0] != 0x1F || header[1] != 0x8B {
            return Err(io::Error::new(io::ErrorKind::InvalidData, "Invalid Gzip magic number"));
        }
        if header[2] != 8 {
            return Err(io::Error::new(io::ErrorKind::InvalidData, "Unsupported compression method"));
        }

        let flags = header[3];
        
        // FEXTRA 플래그 처리
        if flags & 0x04 != 0 {
            let mut len_bytes = [0u8; 2];
            reader.read_exact(&mut len_bytes)?;
            let extra_len = u16::from_le_bytes(len_bytes) as usize;
            let mut extra = vec![0u8; extra_len];
            reader.read_exact(&mut extra)?;
        }
        
        // FNAME 플래그 처리 (Null-terminated string)
        if flags & 0x08 != 0 {
            let mut byte = [0u8; 1];
            loop {
                reader.read_exact(&mut byte)?;
                if byte[0] == 0 { break; }
            }
        }
        
        // FCOMMENT 플래그 처리
        if flags & 0x10 != 0 {
            let mut byte = [0u8; 1];
            loop {
                reader.read_exact(&mut byte)?;
                if byte[0] == 0 { break; }
            }
        }
        
        // FHCRC 플래그 처리
        if flags & 0x02 != 0 {
            let mut crc = [0u8; 2];
            reader.read_exact(&mut crc)?;
        }

        Ok(Self { reader })
    }
}
```

**실행 결과 예시:**
이 코드는 헤더를 성공적으로 파싱하면 `GzipDecoder` 인스턴스를 반환하고, 파일 형식이 맞지 않으면 에러를 발생시킵니다.

---

## 단계 2: 비트 스트림 리더(Bit Reader) 구현

DEFLATE 알고리즘은 바이트 단위가 아니라 **비트(Bit)** 단위로 데이터를 압축합니다. 따라서 바이트 스트림을 받아 원하는 개수만큼의 비트를 읽어내는 비트 리더(Bit Reader)가 필수적입니다. 

주의할 점은 DEFLATE가 데이터를 읽을 때 **LSB(Least Significant Bit, 최하위 비트)** 부터 읽는다는 사실입니다. 예를 들어 바이트 `11010010`에서 3비트를 읽는다면 오른쪽 끝의 `010`을 먼저 읽게 됩니다.

![바이트 스트림에서 비트 단위로 데이터를 읽어내는 Bit Reader의 동작 방식을 시각적으로 설명하는 파이프라인. 입력 바이트 버퍼, 현재 읽는 비트 위치, 그리고 출력되는 비트 값의 흐름을 보여줍니다.](/images/posts/implement-gzip-decompressor-in-rust/svg-2.svg)

효율적인 비트 처리를 위해 버퍼 역할을 할 `bit_buffer`와 현재 버퍼에 남은 비트 수를 나타내는 `bit_count`를 관리하는 구조체를 만듭니다.

```rust
pub struct BitReader<R: Read> {
    reader: R,
    bit_buffer: u32,
    bit_count: u8,
}

impl<R: Read> BitReader<R> {
    pub fn new(reader: R) -> Self {
        Self {
            reader,
            bit_buffer: 0,
            bit_count: 0,
        }
    }

    // 지정된 개수(n)만큼의 비트를 읽어 반환합니다.
    pub fn read_bits(&mut self, n: u8) -> io::Result<u32> {
        while self.bit_count < n {
            let mut byte = [0u8; 1];
            if self.reader.read(&mut byte)? == 0 {
                return Err(io::Error::new(io::ErrorKind::UnexpectedEof, "EOF while reading bits"));
            }
            // 새로 읽은 바이트를 버퍼의 위쪽에 채웁니다.
            self.bit_buffer |= (byte[0] as u32) << self.bit_count;
            self.bit_count += 8;
        }

        // 결과값 추출 (LSB부터 n비트)
        let result = self.bit_buffer & ((1 << n) - 1);
        self.bit_buffer >>= n;
        self.bit_count -= n;
        
        Ok(result)
    }
}
```

이 `BitReader`는 앞으로 허프만 코드나 LZ77 길이/거리 코드를 읽을 때 핵심 엔진으로 작동합니다.

---

## 단계 3: 정규 허프만 트리(Canonical Huffman Tree) 구현

DEFLATE는 데이터의 출현 빈도에 따라 짧은 비트를 할당하는 허프만 코딩을 사용합니다. 일반적인 허프만 트리와 달리, DEFLATE는 트리의 형태를 전송하지 않고 **각 심볼의 코드 길이(Code Length)** 만 전송합니다. 이 길이 정보만으로 송수신자가 동일한 형태의 '정규 허프만 트리(Canonical Huffman Tree)'를 재구성할 수 있습니다.

코드 길이 배열을 받아 실제 비트 코드를 할당하고, 비트 스트림으로부터 심볼을 디코딩하는 구조체를 작성합니다.

![정규 허프만 트리(Canonical Huffman Tree)의 구조와 디코딩 원리를 시각화한 다이어그램. 비트 코드와 해당 심볼(리터럴/길이/거리) 간의 매핑을 트리 형태로 보여주며, 코드 길이별 정렬 방식을 포함합니다.](/images/posts/implement-gzip-decompressor-in-rust/svg-4.svg)

```rust
#[derive(Debug)]
pub struct HuffmanTree {
    counts: [u16; 16],
    symbols: Vec<u16>,
}

impl HuffmanTree {
    // 코드 길이 배열로부터 허프만 트리를 구축합니다.
    pub fn build(code_lengths: &[u8]) -> Self {
        let mut counts = [0u16; 16];
        for &len in code_lengths {
            if len > 0 { counts[len as usize] += 1; }
        }

        let mut next_code = [0u16; 16];
        let mut code = 0;
        for bits in 1..16 {
            code = (code + counts[bits - 1]) << 1;
            next_code[bits] = code;
        }

        let mut symbols = vec![0; code_lengths.len()];
        let mut sorted_symbols = vec![0; code_lengths.len()];
        let mut offsets = [0usize; 16];
        
        let mut offset = 0;
        for bits in 1..16 {
            offsets[bits] = offset;
            offset += counts[bits] as usize;
        }

        for (symbol, &len) in code_lengths.iter().enumerate() {
            if len > 0 {
                let idx = offsets[len as usize];
                sorted_symbols[idx] = symbol as u16;
                offsets[len as usize] += 1;
            }
        }

        Self { counts, symbols: sorted_symbols }
    }

    // 비트 스트림에서 1비트씩 읽으며 심볼을 디코딩합니다.
    pub fn decode<R: Read>(&self, reader: &mut BitReader<R>) -> io::Result<u16> {
        let mut code = 0;
        let mut first = 0;
        let mut index = 0;

        for bits in 1..16 {
            code = (code << 1) | reader.read_bits(1)? as u32;
            let count = self.counts[bits] as u32;
            
            if code - first < count {
                return Ok(self.symbols[index + (code - first) as usize]);
            }
            index += count as usize;
            first = (first + count) << 1;
        }
        Err(io::Error::new(io::ErrorKind::InvalidData, "Invalid Huffman code"))
    }
}
```

이 구현은 트리를 명시적인 노드 포인터 구조로 만들지 않고, 배열의 인덱스 계산만으로 디코딩을 수행하므로 메모리 사용량이 적고 속도가 매우 빠릅니다.

---

## 단계 4: DEFLATE 블록 파싱 - 동적 허프만 트리

DEFLATE 데이터는 여러 개의 블록(Block)으로 나뉩니다. 각 블록은 3비트의 헤더를 가지며, 1비트는 마지막 블록 여부(`BFINAL`), 2비트는 압축 유형(`BTYPE`)을 나타냅니다. 가장 복잡하고 자주 쓰이는 유형은 `BTYPE = 10`인 **동적 허프만 압축(Dynamic Huffman Compression)** 입니다.

동적 블록은 다음 순서로 데이터를 읽어야 합니다.
1. `HLIT` (5 bits), `HDIST` (5 bits), `HCLEN` (4 bits) 읽기
2. 코드 길이 알파벳(Code Length Alphabet)의 허프만 트리 구축
3. 2번의 트리를 이용해 리터럴/길이(Literal/Length) 트리와 거리(Distance) 트리의 코드 길이 배열 디코딩
4. 최종 리터럴 트리와 거리 트리 구축

![DEFLATE 스트림 내의 다양한 블록 타입(비압축 블록, 고정 허프만 블록, 동적 허프만 블록)의 구조를 개략적으로 보여주는 다이어그램. 각 블록의 헤더(BFINAL, BTYPE)와 데이터 구성 방식의 차이점을 명확히 나타냅니다.](/images/posts/implement-gzip-decompressor-in-rust/svg-6.svg)

```rust
fn decode_dynamic_block<R: Read>(reader: &mut BitReader<R>, out: &mut Vec<u8>) -> io::Result<()> {
    let hlit = reader.read_bits(5)? as usize + 257;
    let hdist = reader.read_bits(5)? as usize + 1;
    let hclen = reader.read_bits(4)? as usize + 4;

    // 코드 길이 알파벳의 순서 (DEFLATE 스펙에 정의됨)
    let cl_indices = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15];
    let mut cl_lengths = [0u8; 19];
    for i in 0..hclen {
        cl_lengths[cl_indices[i]] = reader.read_bits(3)? as u8;
    }

    let cl_tree = HuffmanTree::build(&cl_lengths);
    let mut lengths = vec![0u8; hlit + hdist];
    let mut i = 0;

    // 리터럴/거리 코드 길이 디코딩
    while i < hlit + hdist {
        let sym = cl_tree.decode(reader)?;
        match sym {
            0..=15 => { lengths[i] = sym as u8; i += 1; },
            16 => {
                let repeat = reader.read_bits(2)? as usize + 3;
                let prev = lengths[i - 1];
                for _ in 0..repeat { lengths[i] = prev; i += 1; }
            },
            17 => {
                let repeat = reader.read_bits(3)? as usize + 3;
                i += repeat;
            },
            18 => {
                let repeat = reader.read_bits(7)? as usize + 11;
                i += repeat;
            },
            _ => unreachable!(),
        }
    }

    let lit_tree = HuffmanTree::build(&lengths[0..hlit]);
    let dist_tree = HuffmanTree::build(&lengths[hlit..]);

    // 단계 5의 LZ77 디코딩 로직 호출
    decode_lz77(reader, out, &lit_tree, &dist_tree)
}
```

---

## 단계 5: LZ77 압축 해제 로직

트리가 모두 구축되었다면 이제 실제 압축된 데이터를 풀 차례입니다. DEFLATE는 LZ77 알고리즘을 사용하여 반복되는 문자열을 "이전 데이터에서 N바이트 뒤로 가서 L바이트만큼 복사해라"라는 **길이(Length)** 와 **거리(Distance)** 정보로 대체합니다. 

심볼 `0~255`는 리터럴 바이트 그대로 출력하고, `256`은 블록의 끝(End of Block)을 의미합니다. `257~285`는 복사할 길이(Length)를 나타냅니다.

![LZ77 알고리즘의 슬라이딩 윈도우(Sliding Window) 동작 방식을 설명하는 인포그래픽. '사전(Dictionary)' 역할을 하는 이전 데이터와 '룩어헤드 버퍼(Look-ahead Buffer)'에서 현재 처리 중인 데이터를 보여주며, 매칭되는 패턴을 찾아 복사하는 과정을 시각적으로 표현합니다.](/images/posts/implement-gzip-decompressor-in-rust/svg-5.svg)

```rust
// DEFLATE 스펙에 정의된 길이 및 거리 기본값/추가 비트 테이블
const LENGTH_BASE: [u16; 29] = [3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258];
const LENGTH_EXTRA: [u8; 29] = [0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0];
const DIST_BASE: [u16; 30] = [1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577];
const DIST_EXTRA: [u8; 30] = [0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13];

fn decode_lz77<R: Read>(reader: &mut BitReader<R>, out: &mut Vec<u8>, lit_tree: &HuffmanTree, dist_tree: &HuffmanTree) -> io::Result<()> {
    loop {
        let sym = lit_tree.decode(reader)?;
        match sym {
            0..=255 => out.push(sym as u8), // 리터럴 바이트
            256 => break,                   // 블록 종료
            257..=285 => {
                // 길이(Length) 계산
                let len_idx = (sym - 257) as usize;
                let extra_bits = LENGTH_EXTRA[len_idx];
                let length = LENGTH_BASE[len_idx] + reader.read_bits(extra_bits)? as u16;

                // 거리(Distance) 계산
                let dist_sym = dist_tree.decode(reader)?;
                let dist_idx = dist_sym as usize;
                let extra_bits = DIST_EXTRA[dist_idx];
                let distance = DIST_BASE[dist_idx] + reader.read_bits(extra_bits)? as u16;

                // 슬라이딩 윈도우에서 데이터 복사
                for _ in 0..length {
                    let val = out[out.len() - distance as usize];
                    out.push(val);
                }
            },
            _ => return Err(io::Error::new(io::ErrorKind::InvalidData, "Invalid literal/length symbol")),
        }
    }
    Ok(())
}
```

`out` 벡터가 전체 출력 버퍼이자 LZ77의 슬라이딩 윈도우 역할을 동시에 수행합니다. 최근 압축 해제된 데이터가 벡터의 끝에 추가되므로, `out.len() - distance` 인덱스를 참조하여 과거 데이터를 쉽게 복사할 수 있습니다.

---

## 단계 6: 블록 루프 및 푸터 처리

마지막으로, 압축된 블록들을 순회하며 해제하고, Gzip 파일의 맨 끝에 위치한 8바이트 푸터(CRC32 및 원본 파일 크기)를 확인하는 메인 함수를 작성합니다. 분량 상 CRC32 검증 알고리즘 자체 구현은 생략하고 원본 크기 일치 여부만 확인합니다.

```rust
pub fn decompress_gzip<R: Read>(mut reader: R) -> io::Result<Vec<u8>> {
    // 1. 헤더 파싱
    let _decoder = GzipDecoder::new(&mut reader)?;
    let mut bit_reader = BitReader::new(reader);
    let mut out_buffer = Vec::new();

    // 2. DEFLATE 블록 순회
    loop {
        let bfinal = bit_reader.read_bits(1)?;
        let btype = bit_reader.read_bits(2)?;

        match btype {
            0 => {
                // 압축되지 않은 블록 (구현 생략 - 스펙 참조)
                return Err(io::Error::new(io::ErrorKind::Unsupported, "Uncompressed blocks not implemented"));
            },
            1 => {
                // 고정 허프만 블록 (구현 생략 - 스펙 참조)
                return Err(io::Error::new(io::ErrorKind::Unsupported, "Fixed Huffman blocks not implemented"));
            },
            2 => decode_dynamic_block(&mut bit_reader, &mut out_buffer)?,
            _ => return Err(io::Error::new(io::ErrorKind::InvalidData, "Invalid block type")),
        }

        if bfinal == 1 { break; }
    }

    // 3. 푸터 처리 (비트 버퍼에 남은 자투리 비트를 버리고 바이트 단위로 정렬해야 함)
    // 간단한 구현을 위해 여기서는 생략하나, 실제 상용 코드에서는 CRC32와 ISIZE를 검증합니다.

    Ok(out_buffer)
}
```

![DEFLATE 알고리즘의 전체적인 압축 해제 과정을 보여주는 순서도. LZ77 디코딩과 허프만 디코딩이 어떻게 상호작용하여 원본 데이터를 복원하는지 단계별로 설명합니다.](/images/posts/implement-gzip-decompressor-in-rust/svg-3.svg)

---

## 전체 코드

위에서 설명한 모든 요소를 결합한 전체 코드입니다. `main.rs`에 붙여넣고 실행해 볼 수 있습니다. (설명을 위해 BTYPE 0, 1 등 일부 엣지 케이스는 생략하고 가장 핵심인 동적 허프만 블록 위주로 구성했습니다.)

```rust
use std::fs::File;
use std::io::{self, Read, Write};

// --- BitReader, HuffmanTree, Constant Tables 생략 (위의 단계 2~5 코드 복사) ---
// (지면 관계상 핵심 구조체 선언만 요약)

pub struct BitReader<R: Read> { /* ... */ }
impl<R: Read> BitReader<R> { /* ... */ }

pub struct HuffmanTree { /* ... */ }
impl HuffmanTree { /* ... */ }

const LENGTH_BASE: [u16; 29] = [3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258];
const LENGTH_EXTRA: [u8; 29] = [0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0];
const DIST_BASE: [u16; 30] = [1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577];
const DIST_EXTRA: [u8; 30] = [0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13];

// decode_lz77, decode_dynamic_block, GzipDecoder, decompress_gzip 구현 포함

fn main() -> io::Result<()> {
    // 앞서 생성한 test.txt.gz 파일을 엽니다.
    let file = File::open("test.txt.gz")?;
    
    // 압축 해제 실행
    match decompress_gzip(file) {
        Ok(decompressed_data) => {
            println!("압축 해제 성공! 데이터 크기: {} bytes", decompressed_data.len());
            // 복원된 문자열 출력
            let text = String::from_utf8_lossy(&decompressed_data);
            println!("내용:\n{}", text);
        }
        Err(e) => {
            eprintln!("압축 해제 실패: {}", e);
        }
    }

    Ok(())
}
```

---

## 마치며

이 튜토리얼을 통해 복잡해 보이는 Gzip과 DEFLATE 알고리즘을 250줄 남짓한 Rust 코드로 분해하여 직접 구현해 보았습니다. 비트 스트림 처리, 정규 허프만 트리의 배열 기반 구축 방법, 그리고 LZ77의 슬라이딩 윈도우 기법 등은 압축 알고리즘뿐만 아니라 시스템 프로그래밍 전반에 걸쳐 매우 유용한 개념입니다.

*   Rust의 소유권과 안전성을 바탕으로 메모리 오류 없이 바이너리 데이터를 파싱할 수 있었습니다.
*   배열 인덱스 계산을 통한 허프만 트리 최적화 기법을 배웠습니다.
*   데이터 압축 알고리즘의 표준인 DEFLATE의 내부 구조를 이해했습니다.

**다음 단계 제안:**
이번에 생략된 '고정 허프만 블록(Fixed Huffman Block)' 처리 로직과 푸터의 'CRC32 무결성 검증' 로직을 직접 구현하여 추가해 보세요. 또한 `std::io::Write` 트레이트를 활용하여 메모리 버퍼가 아닌 파일 스트림으로 직접 압축을 해제하도록 최적화해 보는 것도 훌륭한 학습이 될 것입니다.