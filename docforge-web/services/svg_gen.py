"""SVG 생성 서비스 — Gemini 텍스트 모델로 편집 가능한 SVG 코드 생성."""

from __future__ import annotations

import re
import httpx

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
- No external resources, no JavaScript""",

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
- No external resources, no JavaScript""",

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
    """응답에서 SVG 코드만 추출."""
    # ```svg ... ``` 또는 ```xml ... ``` 블록 처리
    m = re.search(r"```(?:svg|xml)?\s*(<svg[\s\S]*?</svg>)\s*```", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # 직접 <svg>...</svg> 추출
    m = re.search(r"(<svg[\s\S]*?</svg>)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text.strip()


async def generate_svg_async(
    api_key: str,
    description: str,
    svg_type: str = "architecture",
    style: str = "modern",
) -> str:
    """SVG 코드 생성 후 반환."""
    system_prompt = SYSTEM_PROMPTS.get(svg_type, SYSTEM_PROMPTS["architecture"])
    user_prompt = _build_prompt(svg_type, description, style)

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 8192,
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            GEMINI_API_URL,
            params={"key": api_key},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    raw = data["candidates"][0]["content"]["parts"][0]["text"]
    return _extract_svg(raw)
