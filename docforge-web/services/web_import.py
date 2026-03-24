"""URL에서 콘텐츠를 가져와 Gemini로 다듬어 반환."""

from __future__ import annotations

import base64
import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

from .text_gen import TEXT_MODEL

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.5",
}

# 이미지 최대 크기 (5 MB)
_MAX_IMG_BYTES = 5 * 1024 * 1024
# 가져올 이미지 최대 개수
_MAX_IMAGES = 8


def _is_valid_image_url(url: str) -> bool:
    """콘텐츠 이미지로 쓸 만한 URL인지 간이 판별."""
    p = urlparse(url).path.lower()
    # 아이콘·로고·트래커·광고 제외 (경로 세그먼트 단위로 검사)
    segments = p.split("/")
    skip_segments = ("logo", "icon", "avatar", "badge", "pixel", "tracking", "sponsor")
    skip_prefix = ("ad-", "ad_")
    for seg in segments:
        if seg in skip_segments:
            return False
        if any(seg.startswith(px) for px in skip_prefix):
            return False
    return p.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"))


async def fetch_page(url: str) -> tuple[str, list[dict]]:
    """
    URL에서 본문 텍스트와 이미지를 추출.

    Returns:
        (text_content, images)
        images: [{"url": str, "data_base64": str, "mime": str}]
    """
    async with httpx.AsyncClient(follow_redirects=True, timeout=20, headers=_HEADERS) as c:
        resp = await c.get(url)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "lxml")

    # 불필요한 태그 제거
    for tag in soup.select("script, style, nav, footer, header, aside, .sidebar, .ad, .advertisement, .cookie-banner"):
        tag.decompose()

    # 본문 추출 (article > main > body 순으로 시도)
    article = soup.select_one("article") or soup.select_one("main") or soup.select_one("body")
    if not article:
        article = soup

    # 텍스트 추출 (구조 보존)
    text_parts = []
    for el in article.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre", "code", "table"]):
        tag_name = el.name
        txt = el.get_text(strip=True)
        if not txt:
            continue
        if tag_name.startswith("h"):
            level = int(tag_name[1])
            text_parts.append(f"{'#' * level} {txt}")
        elif tag_name == "li":
            text_parts.append(f"- {txt}")
        elif tag_name == "blockquote":
            text_parts.append(f"> {txt}")
        elif tag_name in ("pre", "code"):
            text_parts.append(f"```\n{txt}\n```")
        else:
            text_parts.append(txt)

    text_content = "\n\n".join(text_parts)

    # 이미지 URL 수집
    img_tags = article.find_all("img", src=True)
    image_urls = []
    seen = set()
    for img in img_tags:
        src = img.get("src", "")
        if not src:
            continue
        full = urljoin(url, src)
        if full in seen:
            continue
        seen.add(full)
        if _is_valid_image_url(full):
            image_urls.append(full)
        if len(image_urls) >= _MAX_IMAGES:
            break

    # 이미지 다운로드
    images = []
    async with httpx.AsyncClient(follow_redirects=True, timeout=15, headers=_HEADERS) as c:
        for img_url in image_urls:
            try:
                r = await c.get(img_url)
                r.raise_for_status()
                data = r.content
                if len(data) > _MAX_IMG_BYTES:
                    continue
                ct = r.headers.get("content-type", "image/jpeg")
                mime = ct.split(";")[0].strip()
                if "svg" in mime:
                    mime = "image/svg+xml"
                elif "png" in mime:
                    mime = "image/png"
                elif "webp" in mime:
                    mime = "image/webp"
                elif "gif" in mime:
                    mime = "image/gif"
                else:
                    mime = "image/jpeg"
                b64 = base64.standard_b64encode(data).decode("ascii")
                images.append({"url": img_url, "data_base64": b64, "mime": mime})
            except Exception as e:
                logger.debug("이미지 다운로드 실패 %s: %s", img_url, e)

    return text_content, images


REWRITE_SYSTEM = """당신은 전문 블로그 글 에디터입니다.
사용자가 제공하는 원본 텍스트를 아래 규칙에 따라 다듬어 주세요.

## 규칙
1. 원문의 핵심 정보와 구조를 유지하되, 문장을 더 자연스럽고 읽기 좋게 다듬어라.
2. 한국어로 작성하라. 원문이 영어면 자연스럽게 번역하라.
3. 마크다운 형식을 사용하라 (H2/H3 제목, 코드블록, 리스트, 표 등).
4. 중복·불필요한 문장은 제거하되 정보 손실은 최소화하라.
5. 코드 블록이 있으면 그대로 유지하라.
6. 광고·프로모션·쿠키 안내 등 비본문 내용은 제거하라.
7. 첫 줄에 적절한 H1 제목을 넣어라.
8. 너무 짧으면 보충 설명을 추가해도 좋지만, 원문에 없는 사실을 지어내지는 마라.
"""


async def rewrite_text(text: str, api_key: str, url: str = "") -> str:
    """Gemini로 텍스트를 다듬어 마크다운으로 반환."""
    client = genai.Client(api_key=api_key)

    user_msg = f"원본 URL: {url}\n\n--- 원본 텍스트 ---\n{text[:30000]}"

    response = await client.aio.models.generate_content(
        model=TEXT_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=REWRITE_SYSTEM,
            max_output_tokens=65536,
            temperature=0.5,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
        contents=user_msg,
    )
    result = response.text.strip()
    # 마크다운 펜스 제거
    if result.startswith("```"):
        result = re.sub(r"^```[^\n]*\n", "", result)
        result = re.sub(r"\n```\s*$", "", result)
    return result.strip()
