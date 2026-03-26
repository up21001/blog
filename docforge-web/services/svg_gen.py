"""SVG 생성 서비스 — Gemini 텍스트 모델로 편집 가능한 SVG 코드 생성."""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET

import httpx

logger = logging.getLogger(__name__)

SVG_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{SVG_MODEL}:generateContent"
)

SYSTEM_PROMPTS: dict[str, str] = {
    "architecture": """You are an expert SVG architect diagram generator.
Generate clean, readable, manually-editable SVG code for architecture/system diagrams.

Rules:
- Output ONLY the SVG code, nothing else. Start with <svg and end with </svg>.
- Use viewBox="0 0 800 600" (adjust height as needed, width always 800)
- Style: modern flat design, rounded rectangles, clear arrows, readable labels
- Colors: use a clean palette (#4A90D9 blue, #50C878 green, #FF6B6B red, #FFD93D yellow, #6C5CE7 purple, #f8f9fa background)
- Font: font-family="Arial, sans-serif"
- All text must be in Korean if the prompt is Korean
- Include proper arrow markers with <defs>
- Make it visually clear and professionally structured
- Add subtle drop shadows using <filter> for boxes
- No external resources, no JavaScript

═══ ARROW RULES — VIOLATIONS WILL PRODUCE BROKEN DIAGRAMS ═══

RENDERING ORDER (non-negotiable):
1. First: ALL rectangles, boxes, shapes, and text labels
2. Last: ALL arrows, connectors, paths — they MUST be the final elements before </svg>
→ This ensures arrows render ON TOP of everything

ARROW GEOMETRY (zero tolerance for overlap):
- Every arrow STARTS at the exact EDGE of its source box (not center, not inside)
- Every arrow ENDS 15px BEFORE the edge of its target box (so arrowhead touches edge, not overlaps)
- Use markerWidth="8" markerHeight="6", refX="8" so the arrowhead tip aligns with path end
- ABSOLUTE BAN: no arrow path may cross through ANY box it is not connected to
- If source and target are not adjacent: the arrow MUST route through EMPTY SPACE only
  → Go UP above all boxes, travel horizontally, then come DOWN to target
  → Or go DOWN below all boxes, travel horizontally, then come UP to target
  → Use L-shaped (2 segments) or Z-shaped (3 segments) polylines with explicit x,y waypoints
- For vertical connections between stacked boxes: use straight vertical lines, centered on the box

ARROW LABELS:
- Place labels in empty space NEAR the arrow midpoint
- Labels must NEVER overlap any box or other label
- Use small font (12-13px), offset 10px from the arrow path

SELF-CHECK before outputting:
For each arrow, mentally trace its full path pixel by pixel.
Ask: "Does this path cross any rectangle boundary it shouldn't?"
If YES → add waypoints to route around it.
If you skip this check, the diagram WILL have overlapping arrows.""",

    "infographic": """You are an expert SVG infographic generator.
Generate clean, readable, manually-editable SVG code for infographics and data visualizations.

Rules:
- Output ONLY the SVG code, nothing else. Start with <svg and end with </svg>.
- Use viewBox="0 0 800 1000" (adjust height as needed)
- Style: colorful, engaging, data-driven design
- Use charts (bar, pie, timeline), icons, numbers prominently
- Colors: vibrant but harmonious palette
- Font: font-family="Arial, sans-serif", use bold for numbers/titles
- All text must be in Korean if the prompt is Korean
- Include a clear title at the top
- No external resources, no JavaScript
- If using arrows/connectors: ABSOLUTE BAN on crossing through any box. Route arrows through empty space only (above/below all boxes). Place all arrow elements AFTER all box elements. Self-check each path for overlap before output.""",

    "icon": """You are an expert SVG icon generator.
Generate clean, scalable, manually-editable SVG icon code.

Rules:
- Output ONLY the SVG code, nothing else. Start with <svg and end with </svg>.
- Use viewBox="0 0 24 24" (standard icon size)
- Style: clean line icon OR filled icon, consistent stroke width (strokeWidth="2" for line icons)
- Single color using currentColor or a specified color
- Simple, recognizable, pixel-perfect design
- No text labels inside the icon
- No external resources, no JavaScript""",
}


def _build_prompt(svg_type: str, description: str, style: str) -> str:
    style_hints = {
        "modern": "modern flat design, clean lines",
        "minimal": "minimal, monochrome, simple shapes only",
        "colorful": "vibrant colors, rich visual style",
        "dark": "dark background (#1a1a2e), light elements, neon accents",
    }
    style_desc = style_hints.get(style, style_hints["modern"])

    return f"Generate an SVG {svg_type} for: {description}\nStyle: {style_desc}"


def _extract_svg(text: str) -> str:
    """응답에서 SVG 코드만 추출하고 유효성 검사."""
    # 코드블록 마커 제거
    text = re.sub(r"^```(?:svg|xml)?\s*", "", text.strip())
    text = re.sub(r"\s*```\s*$", "", text.strip())

    # <svg>...</svg> 추출
    m = re.search(r"(<svg[\s\S]*?</svg>)", text, re.IGNORECASE)
    if m:
        svg = m.group(1).strip()
    else:
        # </svg> 없이 잘린 경우 → 자동 닫기 시도
        m = re.search(r"(<svg[\s\S]*)", text, re.IGNORECASE)
        if m:
            svg = m.group(1).strip() + "\n</svg>"
            logger.warning("SVG가 잘려 있어 </svg>를 자동 추가했습니다.")
        else:
            return text.strip()

    return _validate_and_fix_svg(svg)


def _validate_and_fix_svg(svg: str) -> str:
    """SVG XML 유효성 검사. 깨진 경우 복구 시도."""
    # xmlns 누락 시 추가
    if 'xmlns=' not in svg:
        svg = svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    # currentColor → 실제 색상 (img 태그에서 렌더링 안 됨)
    svg = svg.replace('stroke="currentColor"', 'stroke="#4A90D9"')
    svg = svg.replace('fill="currentColor"', 'fill="#4A90D9"')
    try:
        ET.fromstring(svg)
        return svg
    except ET.ParseError as e:
        logger.warning("SVG XML 파싱 실패: %s — 복구 시도", e)

    # 열린 태그 자동 닫기 시도 (최대 5단계)
    fixed = svg
    for _ in range(5):
        try:
            ET.fromstring(fixed)
            return fixed
        except ET.ParseError:
            # 마지막 완전한 태그 이후를 잘라내고 </svg>로 닫기
            pass

        # 마지막 불완전한 태그/속성 제거
        # 잘린 속성값 (예: fill="#4) 제거
        fixed = re.sub(r'<[^>]*$', '', fixed.rstrip())
        # 닫히지 않은 텍스트 노드 정리
        fixed = fixed.rstrip()
        if not fixed.endswith("</svg>"):
            fixed += "\n</svg>"

    # 최종 검증
    try:
        ET.fromstring(fixed)
        logger.info("SVG 복구 성공")
        return fixed
    except ET.ParseError as e:
        raise ValueError(f"SVG가 유효하지 않아 복구할 수 없습니다: {e}") from e


async def generate_svg_async(
    api_key: str,
    description: str,
    svg_type: str = "architecture",
    style: str = "modern",
    max_retries: int = 3,
) -> str:
    """SVG 코드 생성 후 유효성 검사까지 수행. 실패 시 재시도."""
    system_prompt = SYSTEM_PROMPTS.get(svg_type, SYSTEM_PROMPTS["architecture"])
    user_prompt = _build_prompt(svg_type, description, style)

    last_err = None
    for attempt in range(1, max_retries + 1):
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 65536,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                GEMINI_API_URL,
                params={"key": api_key},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        try:
            return _extract_svg(raw)
        except ValueError as e:
            last_err = e
            logger.warning("SVG 생성 시도 %d/%d 실패: %s — 재시도", attempt, max_retries, e)

    raise ValueError(f"SVG 생성 {max_retries}회 시도 후 실패: {last_err}")
