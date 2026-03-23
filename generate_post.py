#!/usr/bin/env python3
"""
블로그 자동화 스크립트
Hugo + Cloudflare Pages 용 마크다운 포스트 자동 생성 (Gemini API)
"""

import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from google import genai
from google.genai import types

# .env 파일 로드
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# ────────────────────────────────────────────────
# 마스터 프롬프트 (시스템 메시지)
# ────────────────────────────────────────────────
SYSTEM_PROMPT = """너는 13년 차 베테랑 하드웨어/소프트웨어 엔지니어이자, 구글 SEO(검색 엔진 최적화) 전문가인 기술 블로거다.
전문적인 기술 지식(PCB 설계, 고속 신호 무결성, AI 에이전트 워크플로우 등)을 일반 독자부터 전문가까지 쉽게 이해할 수 있도록 체계적인 마크다운(Markdown) 형식으로 작성해야 한다.

[1단계: Hugo Front Matter 생성]
글의 최상단에 아래 형식의 YAML Front Matter를 반드시 포함하라.

---
title: "검색량이 많은 롱테일 키워드를 포함한 매력적인 제목 (50-60자)"
date: YYYY-MM-DDTHH:MM:SS+09:00
lastmod: YYYY-MM-DDTHH:MM:SS+09:00
description: "글 전체 내용을 150자 내외로 요약한 메타 설명 (검색 결과 노출용, 핵심 키워드 포함)"
slug: "url-friendly-english-slug"
categories: ["Hardware"]
tags: ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]
draft: true
---

categories는 ["Hardware", "Software", "AI", "Project"] 중 적합한 것을 선택하라.
tags는 독자가 실제로 검색할 만한 핵심 롱테일 키워드 5개 이상을 넣어라.
slug는 제목을 영어 소문자 하이픈 형식으로 변환하라 (예: "raspberry-pi-pico-wifi-sensor").

[2단계: 본문 구조화]
본문은 다음 구조를 엄수하라.

1. 도입부: 이 기술/프로젝트가 왜 중요한지, 어떤 문제를 해결하려는지 명확히 기술하라.
2. 핵심 내용 (H2, H3 활용):
   - 기술적 스펙을 정확히 명시하라.
   - 설계 과정에서의 고민과 해결책을 '엔지니어의 시각'에서 서술하라.
3. 시각화 요소:
   - 코드 블록 사용 시 적절한 언어(C, C++, Python, YAML, Shell 등)를 지정하라.
   - 중요한 수치나 비교 데이터는 Markdown Table을 사용하여 정리하라.
4. 결론 및 요약: 독자가 얻어갈 핵심 인사이트를 3줄로 요약하라.

[3단계: SEO 최적화]
- 제목에 사용된 핵심 키워드를 본문 첫 번째 문장에 자연스럽게 포함하라.
- 문장은 짧고 명료하게 작성하며, 전문 용어 뒤에는 괄호를 이용해 쉬운 설명을 덧붙여라.
- 이미지가 필요한 부분에 ![이미지 설명](image-placeholder.png) 형태로 자리 표시자를 넣어라.

[4단계: 말투 및 톤앤매너]
- "~입니다", "~합니다" 체를 사용하라.
- 가끔 "필자의 경험상~" 같은 문구를 넣어 전문성을 강조하라.
- 문단 사이 공백을 충분히 활용하여 가독성을 높여라.

반드시 완성된 마크다운 파일 형태로만 출력하고, 추가 설명이나 코드 블록 감싸기 없이 Front Matter의 --- 부터 바로 시작하라."""


def slugify(title: str) -> str:
    """제목을 파일명용 slug로 변환"""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[\s_-]+', '-', slug).strip('-')
    if not slug or len(slug) < 3:
        slug = datetime.now().strftime("%Y%m%d-%H%M%S")
    return slug


def generate_post(topic: str, api_key: str = None, max_retries: int = 3) -> str:
    """Gemini API로 블로그 포스트 생성 (재시도 로직 포함)"""
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    client = genai.Client(api_key=key)

    print(f"[*] 주제: {topic}")
    print("[*] Gemini API 호출 중...")

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=8192,
                    temperature=0.7,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
                contents=f"오늘의 주제: {topic}"
            )
            finish_reason = response.candidates[0].finish_reason if response.candidates else None
            if str(finish_reason) == "FinishReason.MAX_TOKENS":
                print(f"[!] 경고: 토큰 한도 초과로 응답이 잘렸습니다.")
            text = response.text.strip()
            # 모델이 ```markdown ... ``` 로 감싸는 경우 제거
            if text.startswith("```"):
                text = re.sub(r'^```[^\n]*\n', '', text)
                text = re.sub(r'\n```\s*$', '', text)
            text = text.strip()
            # 날짜를 실제 현재 시간으로 교체
            now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
            text = re.sub(r'date:\s*\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\n]*', f'date: {now_str}', text)
            text = re.sub(r'lastmod:\s*\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\n]*', f'lastmod: {now_str}', text)
            return text
        except Exception as e:
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"[!] API 호출 실패 (시도 {attempt}/{max_retries}): {e}")
                print(f"[*] {wait}초 후 재시도...")
                time.sleep(wait)
            else:
                raise RuntimeError(f"API 호출 {max_retries}회 모두 실패: {e}") from e


def save_post(content: str, output_dir: str = "content/posts") -> str:
    """생성된 포스트를 파일로 저장"""
    os.makedirs(output_dir, exist_ok=True)

    # Front Matter에서 slug 우선 추출, 없으면 title로 생성
    slug_match = re.search(r'^slug:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    if slug_match:
        slug = slug_match.group(1).strip()
    else:
        title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else "untitled"
        slug = slugify(title)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{slug}.md"

    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def main():
    # 주제 입력
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("블로그 주제를 입력하세요: ").strip()
        if not topic:
            print("주제를 입력해야 합니다.")
            sys.exit(1)

    # API 키 확인
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = input("GEMINI_API_KEY를 입력하세요: ").strip()

    # 포스트 생성
    content = generate_post(topic, api_key)

    # 초안 미리보기
    print("\n" + "=" * 60)
    print(content[:800] + "\n..." if len(content) > 800 else content)
    print("=" * 60)

    # 저장 확인
    confirm = input("\n이대로 저장하시겠습니까? (Y/n): ").strip().lower()
    if confirm == 'n':
        print("저장 취소.")
        sys.exit(0)

    # Hugo 사이트 루트 기준으로 저장
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "content", "posts")
    filepath = save_post(content, output_dir)

    print(f"\n[완료] 초안 저장: {filepath}")
    print("[안내] draft: true 상태입니다. 검토 후 false로 변경하여 발행하세요.")

    # Git 자동 push
    auto_push = input("\nGit push 하시겠습니까? (y/N): ").strip().lower()
    if auto_push == 'y':
        import subprocess
        subprocess.run(["git", "add", filepath], cwd=script_dir)
        subprocess.run(["git", "commit", "-m", f"draft: {topic}"], cwd=script_dir)
        subprocess.run(["git", "push"], cwd=script_dir)
        print("[완료] Git push 완료")


if __name__ == "__main__":
    main()
