---
title: "Gemini API로 Hugo 블로그 포스트 자동 생성 스크립트 만들기 — 3편"
date: 2026-03-23T10:30:00+09:00
lastmod: 2026-03-23T10:30:00+09:00
description: "Google Gemini 2.5 Flash API를 활용해 SEO 최적화된 Hugo 블로그 포스트를 자동 생성하는 파이썬 스크립트를 설계하고 구현하는 방법을 상세히 설명합니다."
slug: "blog-automation-series-3-gemini-post-generator"
categories: ["ai-automation"]
tags: ["Gemini API", "블로그 자동화", "파이썬 스크립트", "AI 글쓰기", "SEO 자동화", "google-genai"]
series: ["블로그-자동화"]
draft: false
---

AI가 블로그 포스트를 대신 써준다는 개념이 처음에는 어색하게 느껴질 수 있습니다. 하지만 이 스크립트의 목적은 AI가 모든 것을 대체하는 것이 아닙니다. 잘 설계된 시스템 프롬프트를 통해 구조화된 초안을 빠르게 만들고, 사람이 검토하고 보완하는 과정을 돕는 것입니다.

이 편에서는 실제로 이 블로그에서 사용하는 `generate_post.py` 스크립트의 전체 구조와 구현 방법을 설명합니다.

![Gemini 포스트 생성 흐름](/images/gemini-post-generation-flow.svg)

## 준비 작업

### google-genai 패키지 설치

```bash
pip install google-genai
```

### Gemini API 키 발급

1. [Google AI Studio](https://aistudio.google.com)에 접속합니다.
2. 오른쪽 상단의 **Get API key**를 클릭합니다.
3. **Create API key**를 선택하고 프로젝트를 지정합니다.
4. 발급된 API 키를 복사합니다.

API 키는 환경 변수로 설정하는 것이 안전합니다.

```bash
# Linux/macOS
export GEMINI_API_KEY="your-api-key-here"

# Windows (PowerShell)
$env:GEMINI_API_KEY = "your-api-key-here"

# .env 파일 사용 (python-dotenv 설치 필요)
# GEMINI_API_KEY=your-api-key-here
```

## SYSTEM_PROMPT 설계 전략

시스템 프롬프트는 AI의 행동을 결정하는 가장 중요한 요소입니다. 좋은 시스템 프롬프트를 작성하면 매번 비슷한 품질의 포스트를 생성할 수 있습니다.

### 페르소나 설정

AI에게 명확한 역할을 부여합니다.

```
당신은 기술 블로그 전문 작가입니다. 개발자와 기술 독자를 위해
실용적이고 상세한 포스트를 작성합니다. 한국어로 작성하되
기술 용어는 영어를 병기합니다.
```

### 구조 지침

Hugo front matter 형식을 정확히 지정합니다. AI가 생성한 front matter가 파싱 오류를 일으키면 Hugo 빌드가 실패하므로 매우 중요합니다.

```
반드시 다음 형식으로 포스트를 작성하세요:

---
title: "포스트 제목"
date: CURRENT_DATE_PLACEHOLDER
lastmod: CURRENT_DATE_PLACEHOLDER
description: "150자 이내의 SEO 설명"
slug: "영어-소문자-하이픈"
categories: ["적절한-카테고리"]
tags: ["태그1", "태그2", "태그3", "태그4", "태그5"]
draft: false
---
```

### SEO 지침

검색 엔진 최적화를 위한 구체적인 지침을 포함합니다.

```
SEO 최적화 규칙:
- 제목에 핵심 키워드를 포함할 것
- description은 검색 결과 스니펫으로 사용되므로 핵심 내용을 요약할 것
- slug는 영어 소문자와 하이픈만 사용할 것
- 태그는 5~8개로 구체적으로 지정할 것
- 본문에 h2, h3 소제목을 사용하여 구조화할 것
- 코드 예시를 반드시 포함할 것 (기술 포스트의 경우)
```

### 톤앤매너

```
글쓰기 스타일:
- 친근하지만 전문적인 톤
- 독자가 직접 따라할 수 있는 실용적인 내용
- 추상적인 설명보다 구체적인 코드와 예시 우선
- 최소 1500단어 이상 작성
```

## generate_post.py 전체 코드

```python
import os
import sys
import time
import re
from datetime import datetime
from google import genai
from google.genai import types

# API 클라이언트 초기화
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """당신은 기술 블로그 전문 작가입니다. Hugo 정적 사이트 생성기용 마크다운 포스트를 작성합니다.

반드시 다음 front matter 형식으로 시작하세요:
---
title: "포스트 제목"
date: CURRENT_DATE_PLACEHOLDER
lastmod: CURRENT_DATE_PLACEHOLDER
description: "SEO를 위한 150자 이내 설명"
slug: "english-lowercase-slug"
categories: ["적절한-카테고리"]
tags: ["태그1", "태그2", "태그3", "태그4", "태그5"]
draft: false
---

작성 규칙:
1. 최소 1500단어 이상 작성
2. h2(##), h3(###) 소제목으로 구조화
3. 코드 블록은 언어 명시 (```python, ```bash 등)
4. 실용적인 예시와 코드를 포함
5. 한국어로 작성, 기술 용어는 영어 병기
6. SEO를 고려한 자연스러운 키워드 배치
7. 마지막에 요약 또는 다음 단계 안내 포함"""


def slugify(text: str) -> str:
    """한글 제목에서 영어 slug를 생성하는 함수"""
    # 영어와 숫자만 남기고 나머지는 하이픈으로 대체
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def get_current_date_string() -> str:
    """현재 날짜를 Hugo front matter 형식으로 반환"""
    now = datetime.now()
    return now.strftime("%Y-%m-%dT%H:%M:%S+09:00")


def replace_date_placeholder(content: str) -> str:
    """CURRENT_DATE_PLACEHOLDER를 실제 날짜로 교체"""
    current_date = get_current_date_string()
    return content.replace("CURRENT_DATE_PLACEHOLDER", current_date)


def generate_post(topic: str, max_retries: int = 4) -> str:
    """Gemini API를 호출하여 포스트를 생성, 실패 시 exponential backoff로 재시도"""

    for attempt in range(max_retries):
        try:
            print(f"포스트 생성 중... (시도 {attempt + 1}/{max_retries})")

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,
                    max_output_tokens=8192,
                ),
                contents=topic,
            )

            content = response.text
            print(f"생성 완료: {len(content)}자")
            return content

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1, 2, 4, 8초
                print(f"오류 발생: {e}")
                print(f"{wait_time}초 후 재시도...")
                time.sleep(wait_time)
            else:
                raise RuntimeError(f"최대 재시도 횟수 초과: {e}")


def save_post(content: str, topic: str) -> str:
    """생성된 포스트를 파일로 저장"""

    # 날짜 플레이스홀더 교체
    content = replace_date_placeholder(content)

    # 파일명 생성
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(topic)
    if not slug:
        slug = "post"

    filename = f"{date_prefix}-{slug}.md"
    filepath = os.path.join("content", "posts", filename)

    # 디렉토리 생성 (없는 경우)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # 파일 저장
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"저장 완료: {filepath}")
    return filepath


def main():
    if len(sys.argv) < 2:
        print("사용법: python generate_post.py '포스트 주제'")
        print("예시: python generate_post.py 'Docker Compose로 개발 환경 구축하기'")
        sys.exit(1)

    topic = " ".join(sys.argv[1:])
    print(f"주제: {topic}")

    # API 키 확인
    if not os.environ.get("GEMINI_API_KEY"):
        print("오류: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)

    # 포스트 생성
    content = generate_post(topic)

    # 파일 저장
    filepath = save_post(content, topic)

    print(f"\n완료! 생성된 파일: {filepath}")
    print("hugo server -D 로 미리보기를 확인하세요.")


if __name__ == "__main__":
    main()
```

## 코드 설명: 핵심 함수별 상세 분석

### slugify 함수

한글 주제를 영어 slug로 변환하는 함수입니다. Hugo에서 slug는 URL의 일부가 되므로 영어 소문자와 하이픈만 사용해야 합니다.

```python
def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)  # 영어/숫자/공백/하이픈 외 제거
    text = re.sub(r'[\s]+', '-', text.strip())  # 공백을 하이픈으로
    text = re.sub(r'-+', '-', text)              # 연속 하이픈 제거
    return text.strip('-')
```

주제가 한글인 경우 slug가 비어있을 수 있습니다. 그래서 `if not slug: slug = "post"` 처리가 필요합니다. 더 좋은 방법은 AI가 생성한 front matter에서 slug를 추출하는 것인데, 이는 정규식으로 구현할 수 있습니다.

### replace_date_placeholder 함수

AI가 날짜를 직접 생성하면 정확하지 않을 수 있습니다. 그래서 시스템 프롬프트에서 `CURRENT_DATE_PLACEHOLDER`라는 자리 표시자를 사용하고, 후처리 단계에서 실제 현재 시간으로 교체합니다.

```python
def replace_date_placeholder(content: str) -> str:
    current_date = get_current_date_string()
    return content.replace("CURRENT_DATE_PLACEHOLDER", current_date)
```

이 방식의 장점은 AI가 날짜 형식을 잘못 생성하는 문제를 원천 차단한다는 점입니다.

### generate_post의 재시도 로직

Gemini API는 요청이 몰리면 429(Too Many Requests) 오류를 반환할 수 있습니다. Exponential Backoff 전략으로 이를 처리합니다.

```python
for attempt in range(max_retries):
    try:
        # API 호출
        ...
    except Exception as e:
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 1초, 2초, 4초, 8초
            time.sleep(wait_time)
        else:
            raise RuntimeError(f"최대 재시도 횟수 초과: {e}")
```

4번 시도하면 최대 15초를 대기하게 됩니다(1+2+4+8). 대부분의 일시적 오류는 이 범위 내에서 해결됩니다.

## 사용 방법

스크립트 실행 전에 API 키를 환경 변수로 설정합니다.

```bash
export GEMINI_API_KEY="your-api-key"
python generate_post.py "Docker와 Docker Compose 완전 가이드"
```

실행하면 다음과 같이 출력됩니다.

```
주제: Docker와 Docker Compose 완전 가이드
포스트 생성 중... (시도 1/4)
생성 완료: 4823자
저장 완료: content/posts/2026-03-23-docker-docker-compose.md

완료! 생성된 파일: content/posts/2026-03-23-docker-docker-compose.md
hugo server -D 로 미리보기를 확인하세요.
```

## 프롬프트 개선 팁

### 카테고리 고정

블로그의 카테고리 구조가 정해져 있다면 시스템 프롬프트에 명시합니다.

```
categories는 반드시 다음 중 하나를 사용하세요:
- "dev-log" (개발 일지)
- "ai-automation" (AI와 자동화)
- "architecture" (시스템 설계)
- "life" (일상)
```

### 이미지 플레이스홀더 추가

포스트에 이미지 태그를 포함시키고 싶다면 시스템 프롬프트에 추가합니다.

```
포스트 시작 부분에 다음 형식의 이미지를 포함하세요:
![주제 관련 다이어그램](/images/post-slug-diagram.svg)
```

### 코드 품질 기준 설정

```
코드 예시 작성 규칙:
- 실행 가능한 완전한 코드를 제공할 것
- 주석으로 핵심 부분 설명
- 오류 처리 포함
- 보안에 민감한 정보는 환경 변수로 처리
```

## 실제 운영 경험

이 스크립트를 몇 달째 사용하면서 느낀 점을 공유합니다.

**잘 되는 것**: 구조적인 기술 포스트(설치 가이드, 개념 설명, 비교 분석)는 품질이 매우 높습니다. 특히 잘 알려진 기술(Docker, Python, AWS 등)에 대한 내용은 정확하고 상세합니다.

**개선이 필요한 것**: 최신 정보가 중요한 주제나 개인적인 경험을 담은 포스트는 AI 초안 이후 상당한 수정이 필요합니다. AI의 학습 데이터 컷오프 이후 변경된 내용은 직접 확인하고 업데이트해야 합니다.

**권장 워크플로우**: 스크립트로 초안을 생성하고, `hugo server -D`로 미리보기를 확인한 뒤, 잘못된 내용이나 추가하고 싶은 부분을 수정한 후 발행합니다. 전체 과정이 30분 이내로 줄어들었습니다.

다음 편에서는 Sveltia CMS를 설정하여 브라우저에서 직접 포스트를 편집하는 방법을 알아봅니다.
