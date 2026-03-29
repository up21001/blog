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


def inject_svgs_into_markdown(markdown: str, svgs: list[dict], slug: str) -> str:
    """SVG 참조를 마크다운 H2 섹션별로 분산 삽입.

    프론트매터 바로 뒤에 첫 SVG, 이후 H2 섹션 앞에 1개씩 배치.
    """
    if not svgs or not markdown:
        return markdown

    # SVG 참조 생성
    svg_refs = []
    for i, svg in enumerate(svgs):
        desc = svg.get("description", f"svg-{i + 1}")
        # alt를 짧게 (50자)
        alt = desc[:50] if len(desc) > 50 else desc
        path = f"/images/posts/{slug}/svg-{i + 1}.svg"
        svg_refs.append(f"![{alt}]({path})")

    # H2 섹션 위치 찾기
    h2_positions = [m.start() for m in re.finditer(r"(?m)^## ", markdown)]

    # 프론트매터 끝 위치 찾기
    fm_end = 0
    if markdown.startswith("---"):
        second_fence = markdown.index("---", 3)
        fm_end = markdown.index("\n", second_fence) + 1

    # 삽입 위치 결정: 프론트매터 뒤 + H2 섹션 사이
    insert_points = []
    if fm_end > 0:
        insert_points.append(fm_end)  # 첫 SVG: 프론트매터 바로 뒤
    insert_points.extend(h2_positions)

    # SVG 수가 삽입 포인트보다 많으면 마지막 포인트에 여러 개
    result = markdown
    offset = 0
    for i, svg_ref in enumerate(svg_refs):
        if i < len(insert_points):
            pos = insert_points[i] + offset
        else:
            # 남은 SVG는 마지막 섹션 앞에
            pos = insert_points[-1] + offset if insert_points else len(result)

        insert_text = f"\n{svg_ref}\n\n"
        result = result[:pos] + insert_text + result[pos:]
        offset += len(insert_text)

    return result


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
