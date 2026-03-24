"""
마크다운 내 가짜·로컬 이미지 경로 처리.

- http(s)/data: 만 “외부 실제 URL”로 보고 유지.
- 그 외(파일명만, 상대경로, placeholder 등)는 삽화 슬롯으로 간주.
- 이미지 생성 ON: 순서대로 data: URL로 치환, 남는 슬롯은 인용 블록으로.
- 이미지 생성 OFF: 인용 블록으로 바꿔 미리보기 깨짐 방지.
"""

from __future__ import annotations

import re


def _is_real_remote_url(url: str) -> bool:
    """브라우저가 그대로 로드할 수 있는 URL."""
    u = url.strip()
    if not u:
        return False
    ul = u.lower()
    return ul.startswith("http://") or ul.startswith("https://") or ul.startswith("data:")


def _is_synthetic_image_url(url: str) -> bool:
    """삽화로 채우거나 제거해야 하는 마크다운 이미지 URL."""
    return not _is_real_remote_url(url)


def inject_images_into_markdown(markdown: str, images: list[dict]) -> str:
    """로컬·플레이스홀더 형태의 ![](...) 를 순서대로 data:image... 로 치환."""
    if not images:
        return markdown
    idx = [0]

    def repl(m: re.Match) -> str:
        alt = m.group("alt") or "image"
        url = m.group("url").strip()
        if not _is_synthetic_image_url(url):
            return m.group(0)
        if idx[0] >= len(images):
            a = alt.strip()
            return f"> **그림 (삽화 슬롯 초과):** {a}\n\n" if a else ""
        img = images[idx[0]]
        idx[0] += 1
        mime = (img.get("mime") or "image/png").split(";")[0].strip()
        b64 = img["data_base64"]
        return f"![{alt}](data:{mime};base64,{b64})"

    pattern = re.compile(r"!\[(?P<alt>[^\]]*)\]\(\s*(?P<url>[^)]+?)\s*\)")
    return pattern.sub(repl, markdown)


def strip_placeholder_images(markdown: str) -> str:
    """삽화 없을 때 합성 URL 이미지를 제거하고 alt는 인용으로 유지."""

    def repl(m: re.Match) -> str:
        alt = (m.group("alt") or "").strip()
        url = m.group("url").strip()
        if not _is_synthetic_image_url(url):
            return m.group(0)
        if alt:
            return f"> **그림:** {alt}\n\n"
        return ""

    pattern = re.compile(r"!\[(?P<alt>[^\]]*)\]\(\s*(?P<url>[^)]+?)\s*\)\s*\n?")
    return pattern.sub(repl, markdown)
