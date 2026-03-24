---
title: "Whisper AI로 회의록 자동 생성하기 — OpenAI 음성 인식 실전 가이드"
date: 2025-05-03T08:00:00+09:00
lastmod: 2025-05-09T08:00:00+09:00
description: "OpenAI Whisper를 설치부터 실전 파이프라인까지 단계별로 설명합니다. Python으로 음성을 텍스트로 변환하고 LLM으로 자동 요약하는 전체 구현 코드를 공개합니다."
slug: "whisper-ai-meeting-notes-automation"
categories: ["ai-automation"]
tags: ["Whisper", "음성 인식", "회의록 자동화", "OpenAI", "Python"]
series: []
draft: false
---

팀 회의가 끝난 후 회의록을 작성하는 일은 대부분의 팀에서 누군가 억지로 맡는 일입니다. 손으로 작성하면 30분~1시간, 그것도 회의 내용을 기억하면서 정리해야 하니 쉽지 않습니다. 저도 몇 년간 이 문제를 해결하고 싶었는데, OpenAI의 Whisper가 공개된 이후 상황이 완전히 달라졌습니다.

지금은 회의 녹음 파일을 넣으면 5~10분 안에 전체 텍스트 변환과 요약까지 자동으로 나옵니다. 이 글에서는 Whisper 설치부터 LLM 요약 연동까지 실제로 돌아가는 파이프라인을 공개합니다.

![Whisper AI 회의록 자동화 파이프라인](/images/whisper-ai-meeting-notes.svg)

---

## Whisper란 무엇인가

Whisper는 OpenAI가 2022년 공개한 오픈소스 음성 인식(STT, Speech-to-Text) 모델입니다. 99개 언어를 지원하고, 한국어 인식률이 상당히 높습니다. 무엇보다 **완전 무료로 로컬에서 실행**할 수 있다는 점이 핵심입니다.

기존에 사용하던 Google Cloud Speech-to-Text나 네이버 Clova는 API 비용이 발생하고 외부 서버로 음성 데이터를 전송해야 했습니다. 보안에 민감한 내부 회의 내용을 외부로 보내는 것은 부담스럽습니다. Whisper는 이 두 가지 문제를 모두 해결합니다.

2024년 말 기준으로 `large-v3` 모델이 가장 최신이며, 한국어 인식 정확도가 크게 개선되었습니다.

---

## 환경 설정

### 필수 요구사항

```bash
# Python 3.9 이상 필요
python --version

# CUDA GPU가 있으면 속도가 10배 이상 빠름
# CPU만 있어도 동작하지만 large 모델은 느림
nvidia-smi  # NVIDIA GPU 확인
```

GPU가 없는 경우, `tiny`나 `base` 모델을 쓰거나 OpenAI API를 통한 Whisper를 사용하는 것이 현실적입니다. 1시간 회의를 `large-v3` 모델로 CPU만으로 처리하면 30~60분이 걸리기도 합니다. RTX 3080 이상의 GPU가 있으면 5~10분 내에 처리됩니다.

### 설치

```bash
# 가상환경 생성 권장
python -m venv whisper-env
source whisper-env/bin/activate  # Windows: whisper-env\Scripts\activate

# Whisper 설치
pip install openai-whisper

# ffmpeg 설치 필요 (음성 파일 처리용)
# macOS
brew install ffmpeg

# Ubuntu
sudo apt install ffmpeg

# Windows (chocolatey)
choco install ffmpeg
```

---

## 기본 사용법

### 커맨드라인으로 빠르게 시작

설치가 완료되면 명령어 한 줄로 바로 쓸 수 있습니다.

```bash
# 기본 사용 (자동 언어 감지)
whisper meeting.mp3

# 한국어 지정 (더 정확함)
whisper meeting.mp3 --language Korean

# 모델 선택 + 출력 형식 지정
whisper meeting.mp3 --model large-v3 --language Korean --output_format txt

# 타임스탬프 포함 SRT 자막 파일 생성
whisper meeting.mp3 --model medium --language Korean --output_format srt
```

### Python으로 프로그래밍 방식 사용

```python
import whisper
import json

def transcribe_audio(audio_path: str, model_name: str = "large-v3") -> dict:
    """
    음성 파일을 텍스트로 변환합니다.

    Args:
        audio_path: 음성 파일 경로 (mp3, wav, m4a, ogg 등)
        model_name: 사용할 Whisper 모델 (tiny, base, small, medium, large-v3)

    Returns:
        변환 결과 딕셔너리 (text, segments 포함)
    """
    print(f"모델 로딩 중: {model_name}")
    model = whisper.load_model(model_name)

    print(f"음성 인식 시작: {audio_path}")
    result = model.transcribe(
        audio_path,
        language="ko",           # 한국어 지정
        verbose=True,            # 진행 상황 출력
        word_timestamps=True,    # 단어별 타임스탬프
    )

    return result

# 사용 예시
result = transcribe_audio("team_meeting_2026_03.mp3")

# 전체 텍스트
print(result["text"])

# 타임스탬프별 세그먼트
for segment in result["segments"]:
    start = segment["start"]
    end = segment["end"]
    text = segment["text"]
    print(f"[{start:.1f}s - {end:.1f}s] {text}")
```

---

## 실전 파이프라인 구현

단순 텍스트 변환을 넘어, LLM으로 요약까지 자동화하는 전체 파이프라인입니다.

### 프로젝트 구조

```
meeting-notes/
├── transcribe.py       # Whisper STT
├── summarize.py        # LLM 요약
├── pipeline.py         # 전체 파이프라인
├── output/             # 결과 저장
│   ├── raw/            # 원본 텍스트
│   └── summary/        # 요약 파일
└── recordings/         # 녹음 파일
```

### transcribe.py

```python
import whisper
import os
from pathlib import Path
from datetime import timedelta

def format_timestamp(seconds: float) -> str:
    """초를 HH:MM:SS 형식으로 변환"""
    return str(timedelta(seconds=int(seconds)))[:-3] if seconds >= 3600 \
           else f"00:{str(timedelta(seconds=int(seconds)))[3:]}"

def transcribe_meeting(
    audio_path: str,
    output_dir: str = "output/raw",
    model_name: str = "medium"
) -> str:
    """
    회의 녹음을 텍스트로 변환하고 파일로 저장합니다.
    """
    os.makedirs(output_dir, exist_ok=True)

    model = whisper.load_model(model_name)
    result = model.transcribe(
        audio_path,
        language="ko",
        verbose=False
    )

    # 타임스탬프 포함 텍스트 생성
    lines = []
    for seg in result["segments"]:
        timestamp = format_timestamp(seg["start"])
        lines.append(f"[{timestamp}] {seg['text'].strip()}")

    formatted_text = "\n".join(lines)

    # 파일 저장
    base_name = Path(audio_path).stem
    output_path = os.path.join(output_dir, f"{base_name}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(formatted_text)

    print(f"변환 완료: {output_path}")
    return formatted_text
```

### summarize.py

```python
from openai import OpenAI

client = OpenAI()  # OPENAI_API_KEY 환경변수 필요

SUMMARY_PROMPT = """
당신은 회의록 전문 작성자입니다.
아래 회의 내용을 분석하여 다음 형식으로 정리해주세요.

## 회의 요약
[3~5줄로 회의의 핵심 내용]

## 주요 논의 사항
- [논의 사항 1]
- [논의 사항 2]
...

## 결정된 사항
- [결정 1]
- [결정 2]
...

## 액션 아이템
| 담당자 | 할 일 | 기한 |
|--------|--------|------|
| [이름] | [업무] | [날짜] |

## 다음 회의 안건 (언급된 경우)
- [안건]

회의 내용:
{transcript}
"""

def summarize_meeting(
    transcript: str,
    output_dir: str = "output/summary",
    filename: str = "summary"
) -> str:
    """
    회의 텍스트를 LLM으로 요약합니다.
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": SUMMARY_PROMPT.format(transcript=transcript)
            }
        ],
        temperature=0.3,  # 낮은 temperature로 일관성 확보
    )

    summary = response.choices[0].message.content

    # 파일 저장
    output_path = os.path.join(output_dir, f"{filename}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"요약 완료: {output_path}")
    return summary
```

### pipeline.py — 전체 자동화

```python
import sys
import os
from pathlib import Path
from transcribe import transcribe_meeting
from summarize import summarize_meeting

def process_meeting(audio_path: str, model: str = "medium") -> None:
    """
    녹음 파일 하나를 받아 전체 파이프라인을 실행합니다.
    """
    if not os.path.exists(audio_path):
        print(f"파일을 찾을 수 없습니다: {audio_path}")
        sys.exit(1)

    base_name = Path(audio_path).stem
    print(f"\n{'='*50}")
    print(f"회의록 자동화 시작: {base_name}")
    print(f"{'='*50}\n")

    # 1단계: 음성 인식
    print("[1/2] 음성 인식 중...")
    transcript = transcribe_meeting(
        audio_path,
        output_dir="output/raw",
        model_name=model
    )

    # 2단계: LLM 요약
    print("\n[2/2] AI 요약 중...")
    summary = summarize_meeting(
        transcript,
        output_dir="output/summary",
        filename=base_name
    )

    print(f"\n{'='*50}")
    print("완료!")
    print(f"원본: output/raw/{base_name}.txt")
    print(f"요약: output/summary/{base_name}.md")
    print(f"{'='*50}\n")
    print(summary)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python pipeline.py <녹음파일> [모델명]")
        print("예시: python pipeline.py meeting.mp3 medium")
        sys.exit(1)

    audio_file = sys.argv[1]
    model_name = sys.argv[2] if len(sys.argv) > 2 else "medium"

    process_meeting(audio_file, model_name)
```

실행 방법은 간단합니다.

```bash
# 기본 실행 (medium 모델)
python pipeline.py recordings/team_meeting.mp3

# large-v3 모델 사용 (더 정확하지만 느림)
python pipeline.py recordings/team_meeting.mp3 large-v3
```

---

## 모델 선택 가이드

상황에 따른 모델 추천입니다.

| 상황 | 추천 모델 | 이유 |
|------|----------|------|
| 짧은 미팅 (30분 이내), CPU만 있음 | `small` | 빠르고 충분한 정확도 |
| 일반적인 팀 회의, GPU 없음 | `medium` | 정확도와 속도 균형 |
| 중요한 외부 미팅, GPU 있음 | `large-v3` | 최고 정확도 |
| 실시간 처리 필요 | `tiny` or `base` | 속도 우선 |
| 비용 절감, API 활용 | OpenAI API | 서버 자원 절약 |

---

## OpenAI API 방식 (로컬 GPU 없을 때)

GPU가 없거나 빠른 처리가 필요하다면 OpenAI API를 쓰는 것도 좋습니다. 비용은 분당 약 $0.006으로, 1시간 회의에 약 $0.36(약 500원) 수준입니다.

```python
from openai import OpenAI

client = OpenAI()

def transcribe_with_api(audio_path: str) -> str:
    """OpenAI API를 통한 Whisper 사용"""
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ko",
            response_format="verbose_json",  # 타임스탬프 포함
        )
    return transcript.text
```

단, 보안이 중요한 회의 내용은 로컬 Whisper를 쓰는 것이 바람직합니다.

---

## 자주 겪는 문제와 해결 방법

**문제 1: "CUDA out of memory" 오류**

GPU 메모리가 부족할 때 발생합니다. `large-v3`는 약 10GB VRAM이 필요합니다.

```python
# 더 작은 모델로 전환하거나 CPU 사용 강제
model = whisper.load_model("medium", device="cpu")
```

**문제 2: 한국어 인식률이 낮을 때**

`language` 파라미터를 명시하지 않으면 자동 감지가 틀리는 경우가 있습니다.

```python
# 반드시 language 명시
result = model.transcribe(audio_path, language="ko")
```

**문제 3: 여러 사람 발언 구분 (화자 분리)**

기본 Whisper는 화자를 구분하지 못합니다. `pyannote.audio` 라이브러리를 추가로 써야 합니다.

```bash
pip install pyannote.audio
```

화자 분리까지 필요한 경우는 별도 포스트로 다루겠습니다.

---

## 실제 사용 결과

저희 팀에서 3개월간 사용한 결과를 공유합니다. 주 3회 1시간짜리 팀 회의 기준입니다.

- **회의록 작성 시간**: 평균 45분 → 10분 (검토 시간 포함)
- **인식 정확도 (medium 모델)**: 약 92% (한국어, 마이크 근접 환경)
- **가장 큰 오류**: 고유명사, 영어 혼용 단어, 낮은 음질 구간
- **실제 비용**: 로컬 GPU 사용으로 API 비용 없음

완벽하지는 않습니다. 여전히 결과물 검토는 사람이 합니다. 하지만 "빈 문서에서 시작"과 "90% 완성된 초안을 다듬기"는 완전히 다른 경험입니다.

회의 녹음은 핸드폰 기본 녹음 앱으로 충분합니다. 가능하면 외장 마이크나 USB 마이크를 쓰면 인식률이 크게 올라갑니다.
