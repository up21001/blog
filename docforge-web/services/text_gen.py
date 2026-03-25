"""Gemini 텍스트 생성 (블로그 generate_post.py 패턴)."""

from __future__ import annotations

import asyncio
import os
import re
import time
from datetime import datetime

from google import genai
from google.genai import types

from .prompt_config import get_effective_prompts

# 문서 본문·이미지용 영문 프롬프트 생성에 공통 사용
TEXT_MODEL = "gemini-2.5-flash"

TEXT_MODELS = {
    "gemini-2.5-flash": "Gemini 2.5 Flash (빠름/저비용)",
    "gemini-3-pro-preview": "Gemini 3 Pro (고품질 추론)",
}

# (max_output_tokens, 사용자 메시지에 붙는 분량 지시)
LENGTH_TIER: dict[str, tuple[int, str]] = {
    "short": (65536, "분량: 짧게. 핵심만 약 800~1500자 한글 분량."),
    "medium": (65536, "분량: 보통. 약 2000~4000자 한글, 예제 1~2개."),
    "long": (65536, "분량: 길게. 약 5000~9000자 한글. 단계·표·코드를 충분히."),
    "very_long": (
        65536,
        "분량: 매우 길게. 10000자 한글 이상에 가깝게. H2로 장을 나누고 개념도 설명·주의사항·예제를 상세히.",
    ),
}

EXCERPT_BY_TIER = {
    "short": 2500,
    "medium": 5000,
    "long": 9000,
    "very_long": 14000,
}


def excerpt_limit_for_tier(length_tier: str) -> int:
    return EXCERPT_BY_TIER.get(length_tier if length_tier in EXCERPT_BY_TIER else "medium", 5000)


def _strip_markdown_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[^\n]*\n", "", text)
        text = re.sub(r"\n```\s*$", "", text)
    return text.strip()


def generate_document(
    topic: str,
    template_key: str,
    api_key: str,
    max_retries: int = 3,
    length_tier: str = "medium",
    text_model: str | None = None,
) -> str:
    eff = get_effective_prompts()
    if template_key not in eff:
        template_key = "plain"
    system_instruction = eff.get(template_key) or eff["plain"]
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    tier = length_tier if length_tier in LENGTH_TIER else "medium"
    max_out, length_msg = LENGTH_TIER[tier]

    use_model = text_model if text_model and text_model in TEXT_MODELS else TEXT_MODEL
    client = genai.Client(api_key=key)
    user_msg = eff["document_user"].format(topic=topic) + f"\n\n【작성 지시】{length_msg}"

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=use_model,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    max_output_tokens=max_out,
                    temperature=0.7,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
                contents=user_msg,
            )
            text = response.text.strip()
            text = _strip_markdown_fence(text)
            # 모든 템플릿에서 날짜를 현재 시간으로 교정
            now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
            text = re.sub(
                r"date:\s*\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[^\n]*",
                f"date: {now_str}",
                text,
            )
            text = re.sub(
                r"lastmod:\s*\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[^\n]*",
                f"lastmod: {now_str}",
                text,
            )
            # date: YYYY-MM-DD (시간 없는 형태)도 교정
            text = re.sub(
                r"date:\s*\d{4}-\d{2}-\d{2}\s*$",
                f"date: {now_str}",
                text,
                flags=re.MULTILINE,
            )
            return text
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(2**attempt)
            else:
                raise RuntimeError(f"텍스트 생성 실패 ({max_retries}회): {last_err}") from last_err


def generate_image_prompts(
    topic: str,
    markdown_excerpt: str,
    count: int,
    api_key: str,
    excerpt_max_chars: int = 5000,
    extra_hints: str | None = None,
) -> list[str]:
    """삽화용 짧은 영문 프롬프트 여러 개."""
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
    client = genai.Client(api_key=key)
    cap = max(500, min(excerpt_max_chars, 20000))
    raw = markdown_excerpt or ""
    hints = (extra_hints or "").strip()
    if hints:
        sep = "\n\n---\n\n"
        max_hints = min(2500, max(200, cap // 3))
        if len(hints) > max_hints:
            hints = hints[:max_hints]
        prefix = hints + sep
        room = cap - len(prefix)
        if room < 400:
            hints = hints[: max(50, cap - 400 - len(sep))]
            prefix = hints + sep
            room = cap - len(prefix)
        excerpt = (prefix + raw)[:cap]
    else:
        excerpt = raw[:cap]
    eff = get_effective_prompts()
    prompt = eff["image_prompt_generator"].format(
        topic=topic, excerpt=excerpt, count=count
    )

    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=65536, temperature=0.85),
    )
    lines = []
    for line in response.text.strip().splitlines():
        line = line.strip().lstrip("-*0123456789.) ")
        if line:
            lines.append(line)
    return lines[:count] if lines else [f"Abstract editorial illustration about: {topic[:80]}"]


def generate_svg_specs(
    topic: str,
    markdown_excerpt: str,
    count: int,
    api_key: str,
    excerpt_max_chars: int = 6000,
) -> list[dict]:
    """문서를 분석해 필요한 SVG 에셋 스펙 목록 반환.
    각 항목: {type, style, description}
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
    client = genai.Client(api_key=key)
    excerpt = (markdown_excerpt or "")[:excerpt_max_chars]

    prompt = f"""Topic (Korean): {topic}

Article excerpt:
{excerpt}

Based on this article, decide what SVG assets would best enhance the content.
Generate exactly {count} SVG asset specifications.

For each asset output one JSON object per line (no array brackets, no markdown):
{{"type": "architecture"|"infographic"|"icon", "style": "modern"|"minimal"|"colorful"|"dark", "description": "Korean description of what to draw"}}

Rules:
- type "architecture": system diagrams, flow charts, process flows
- type "infographic": data comparisons, step lists, statistics
- type "icon": single concept icons (small, symbolic)
- Match each asset to a specific section or concept in the article
- Write descriptions in Korean, be specific and detailed
- Output only JSON lines, nothing else"""

    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=65536, temperature=0.5),
    )

    import json
    specs: list[dict] = []
    for line in response.text.strip().splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
            if "type" in obj and "description" in obj:
                obj.setdefault("style", "modern")
                specs.append(obj)
        except Exception:
            continue
    # 부족하면 기본값 채우기
    while len(specs) < count:
        specs.append({"type": "architecture", "style": "modern", "description": f"{topic} 관련 다이어그램"})
    return specs[:count]


async def generate_svg_specs_async(
    topic: str,
    markdown_excerpt: str,
    count: int,
    api_key: str,
    excerpt_max_chars: int = 6000,
) -> list[dict]:
    return await asyncio.to_thread(
        generate_svg_specs, topic, markdown_excerpt, count, api_key, excerpt_max_chars
    )


async def generate_document_async(
    topic: str, template_key: str, api_key: str, length_tier: str = "medium",
    text_model: str | None = None,
) -> str:
    return await asyncio.to_thread(
        generate_document, topic, template_key, api_key, 3, length_tier, text_model
    )


def translate_to_english(
    korean_markdown: str,
    api_key: str,
    max_retries: int = 3,
) -> str:
    """한글 마크다운을 영문으로 번역. 프론트매터 구조 유지."""
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    client = genai.Client(api_key=key)
    prompt = f"""Translate the following Korean blog post markdown to English.

Rules:
- Keep ALL frontmatter YAML fields (---, title, date, slug, categories, tags, draft, etc.)
- Translate the title to English
- Keep the slug as-is (do not translate)
- Keep categories and tags as-is (do not translate)
- Keep all markdown formatting, headings, code blocks, links, image paths exactly as-is
- Translate only the Korean text content to natural, professional English
- Do not add or remove any sections
- Do not wrap output in code fences
- Output the complete translated markdown directly

Korean markdown:
{korean_markdown}"""

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=TEXT_MODEL,
                config=types.GenerateContentConfig(
                    max_output_tokens=65536,
                    temperature=0.3,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
                contents=prompt,
            )
            text = response.text.strip()
            text = _strip_markdown_fence(text)
            return text
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(2**attempt)
            else:
                raise RuntimeError(f"영문 번역 실패 ({max_retries}회): {last_err}") from last_err


async def translate_to_english_async(
    korean_markdown: str, api_key: str
) -> str:
    return await asyncio.to_thread(translate_to_english, korean_markdown, api_key)


async def generate_image_prompts_async(
    topic: str,
    markdown_excerpt: str,
    count: int,
    api_key: str,
    excerpt_max_chars: int = 5000,
    extra_hints: str | None = None,
) -> list[str]:
    return await asyncio.to_thread(
        generate_image_prompts,
        topic,
        markdown_excerpt,
        count,
        api_key,
        excerpt_max_chars,
        extra_hints,
    )
