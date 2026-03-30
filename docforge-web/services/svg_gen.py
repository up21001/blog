"""SVG 생성 서비스 — Gemini 텍스트 모델로 편집 가능한 SVG 코드 생성."""

from __future__ import annotations

import logging
import math
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

═══ TEXT OVERFLOW RULES — KOREAN TEXT IS WIDER THAN LATIN ═══

- viewBox width is 800. ALL text MUST stay within x=40 to x=760 (720px usable).
- Korean characters are ~1.2× wider than Latin at the same font-size.
  → At font-size 18: max ~35 Korean chars per line
  → At font-size 22: max ~28 Korean chars per line
  → At font-size 28: max ~22 Korean chars per line
- NEVER place long description text beside an icon in a narrow column.
  → Put the title on one row, icon below it, description text BELOW the icon using FULL width.
- If a text line exceeds the usable width, split it into multiple <text> lines (dy or separate y).
- SELF-CHECK: for every <text> element, calculate (x + text_width). If it exceeds 760, shorten or split.

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
- Labels must NEVER overlap any box, other label, or other arrow
- Use small font (12-13px), offset 10px from the arrow path
- CRITICAL: Add a white background rectangle behind EVERY arrow label text:
  → <rect x="..." y="..." width="..." height="..." fill="white" rx="3"/>
  → Place the rect BEFORE the text element so it acts as a backdrop
  → This ensures labels are always readable even near boxes

ARROW-BOX CLEARANCE:
- All arrows must maintain at least 20px clearance from any box they are not connected to
- Arrow paths that run parallel to a box edge must be at least 25px away from that edge
- Vertical arrows between stacked boxes: center on box, keep labels to the side (not on the line)
- For feedback/return arrows (going back up or left): route them at least 40px OUTSIDE the outermost box edge
  → e.g., a left-side feedback arrow should have x < (leftmost_box_x - 40)
  → e.g., a bottom return arrow should have y > (bottom_box_y + bottom_box_height + 30)

SELF-CHECK before outputting:
For each arrow, mentally trace its full path pixel by pixel.
Ask: "Does this path cross any rectangle boundary it shouldn't?"
If YES → add waypoints to route around it.
For each arrow label, check: "Does this text overlap any box or other text?"
If YES → move it to clear space or add a white background rect.
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
- Korean text overflow prevention: viewBox width is 800, usable text area x=40 to x=760. Korean chars are ~1.2× wider than Latin. At font-size 18 max ~35 chars/line, at 22 max ~28, at 28 max ~22. Never place long text beside icons in narrow columns — use full width below icons. Split long lines into multiple <text> elements.
- If using arrows/connectors: ABSOLUTE BAN on crossing through any box. Route arrows through empty space only (above/below all boxes, with at least 20px clearance). Place all arrow elements AFTER all box elements. Add white background rects behind all arrow labels. For feedback/return arrows, route at least 40px outside the outermost box edge. Self-check each path for overlap before output.""",

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

    "data_structure": """You are an expert SVG data structure diagram generator.
Generate clean, readable, manually-editable SVG code for binary data layouts, memory maps, and byte-level diagrams.

Rules:
- Output ONLY the SVG code, nothing else. Start with <svg and end with </svg>.
- Use viewBox="0 0 800 600" (adjust height as needed, width always 800)
- Style: precise technical layout, monospace-style labels, grid-aligned boxes
- Colors: use a clean technical palette (#2D3748 dark, #4A90D9 blue, #50C878 green, #FFD93D yellow, #f8f9fa background, #e2e8f0 field borders)
- Font: font-family="Courier New, monospace" for byte values and offsets; font-family="Arial, sans-serif" for labels
- All text must be in Korean if the prompt is Korean
- Show byte offsets on the left margin, field names inside or above boxes
- Use consistent box heights for fixed-size fields; proportional widths for multi-byte fields
- Include a legend if multiple field types are shown
- No external resources, no JavaScript

═══ TEXT OVERFLOW RULES — KOREAN TEXT IS WIDER THAN LATIN ═══

- viewBox width is 800. ALL text MUST stay within x=40 to x=760 (720px usable).
- Korean characters are ~1.2× wider than Latin at the same font-size.
  → At font-size 18: max ~35 Korean chars per line
  → At font-size 14: max ~45 Korean chars per line
- If a text line exceeds the usable width, split it into multiple <text> lines.

═══ ARROW RULES — VIOLATIONS WILL PRODUCE BROKEN DIAGRAMS ═══

RENDERING ORDER (non-negotiable):
1. First: ALL rectangles, boxes, shapes, and text labels
2. Last: ALL arrows, connectors, paths — they MUST be the final elements before </svg>

ARROW GEOMETRY (zero tolerance for overlap):
- Every arrow STARTS at the exact EDGE of its source box (not center, not inside)
- Every arrow ENDS 15px BEFORE the edge of its target box
- ABSOLUTE BAN: no arrow path may cross through ANY box it is not connected to
- Route through EMPTY SPACE only — use L-shaped or Z-shaped polylines with explicit waypoints""",

    "timing": """You are an expert SVG timing diagram generator.
Generate clean, readable, manually-editable SVG code for signal timing waveforms and protocol timing diagrams.

Rules:
- Output ONLY the SVG code, nothing else. Start with <svg and end with </svg>.
- Use viewBox="0 0 800 500" (adjust height as needed, width always 800)
- Style: oscilloscope-inspired, clean waveforms, precise alignment
- Colors: dark background (#1a1a2e) with bright signal lines (#50C878 green, #4A90D9 blue, #FFD93D yellow, #FF6B6B red) for dark style; or white background with dark lines for modern style
- Font: font-family="Courier New, monospace" for timing labels; font-family="Arial, sans-serif" for signal names
- All text must be in Korean if the prompt is Korean
- Signal names on the left column (x=10 to x=140), waveforms in the right area (x=150 to x=790)
- Draw horizontal baselines for each signal; use sharp vertical transitions for digital signals
- Mark clock edges, setup/hold times, and data valid windows with annotations
- Include a time axis at the bottom with tick marks
- No external resources, no JavaScript

═══ TEXT OVERFLOW RULES ═══
- viewBox width is 800. ALL text MUST stay within x=10 to x=790.
- Signal name column: x=10 to x=140 (130px). Keep names short or use 2 lines.
- Korean characters are ~1.2× wider than Latin at the same font-size. At font-size 12: max ~10 Korean chars in signal name column.""",

    "class_diagram": """You are an expert SVG class diagram generator.
Generate clean, readable, manually-editable SVG code for UML class diagrams showing relationships, inheritance, and composition.

Rules:
- Output ONLY the SVG code, nothing else. Start with <svg and end with </svg>.
- Use viewBox="0 0 800 700" (adjust height as needed, width always 800)
- Style: UML-compliant, clean boxes with header/body/method sections, clear relationship lines
- Colors: use a clean palette (#4A90D9 blue for class headers, #f8f9fa box background, #2D3748 border, #50C878 interface headers, #6C5CE7 abstract headers)
- Font: font-family="Arial, sans-serif"; bold for class names; regular for attributes and methods
- All text must be in Korean if the prompt is Korean
- Class boxes: header section (class name, bold, centered), attributes section, methods section — separated by horizontal lines
- Relationships: solid line with filled triangle for inheritance, dashed line with open arrow for interface, solid line with diamond for composition/aggregation
- Show multiplicity labels on association ends (1, *, 0..1, 1..*)
- No external resources, no JavaScript

═══ TEXT OVERFLOW RULES — KOREAN TEXT IS WIDER THAN LATIN ═══
- viewBox width is 800. ALL text MUST stay within x=20 to x=780.
- Korean characters at font-size 14: max ~40 chars per line inside a box.
- If class name or attribute text overflows the box width, shorten with ellipsis or reduce font size.

═══ ARROW RULES — VIOLATIONS WILL PRODUCE BROKEN DIAGRAMS ═══
RENDERING ORDER (non-negotiable):
1. First: ALL class boxes and text labels
2. Last: ALL relationship lines and arrows

ARROW GEOMETRY:
- Lines connect box EDGES, not centers
- Inheritance arrows: hollow triangle arrowhead pointing TO the parent class
- ABSOLUTE BAN: no line may cross through any unrelated class box
- Route through EMPTY SPACE using explicit waypoints""",

    "pipeline": """You are an expert SVG pipeline diagram generator.
Generate clean, readable, manually-editable SVG code for data flow pipelines, ETL processes, and multi-stage processing diagrams.

Rules:
- Output ONLY the SVG code, nothing else. Start with <svg and end with </svg>.
- Use viewBox="0 0 800 500" (adjust height as needed, width always 800)
- Style: modern flat design, left-to-right or top-to-bottom flow, stage boxes with process labels
- Colors: gradient-like progression (#4A90D9 → #50C878 → #6C5CE7 for stages), data flow arrows in #2D3748, #f8f9fa background
- Font: font-family="Arial, sans-serif"; bold for stage names; small regular for data labels on arrows
- All text must be in Korean if the prompt is Korean
- Each pipeline stage: rounded rectangle with icon area (top) and label (below)
- Show data/event labels on arrows between stages
- Include throughput numbers or transformation annotations where relevant
- Add a subtle progress indicator or numbered sequence
- No external resources, no JavaScript

═══ TEXT OVERFLOW RULES — KOREAN TEXT IS WIDER THAN LATIN ═══
- viewBox width is 800. ALL text MUST stay within x=20 to x=780.
- Korean characters at font-size 14: max ~40 chars per line.

═══ ARROW RULES — VIOLATIONS WILL PRODUCE BROKEN DIAGRAMS ═══
RENDERING ORDER (non-negotiable):
1. First: ALL stage boxes and text labels
2. Last: ALL arrows — they MUST be the final elements before </svg>

ARROW GEOMETRY:
- Arrows connect box EDGES (not centers, not inside)
- ABSOLUTE BAN: no arrow may pass through any stage box it is not connected to
- For non-adjacent stages: route ABOVE or BELOW all boxes with explicit waypoints""",

    "flowchart": """You are an expert SVG flowchart generator.
Generate clean, readable, manually-editable SVG code for decision flows, algorithm steps, and process flowcharts.

Rules:
- Output ONLY the SVG code, nothing else. Start with <svg and end with </svg>.
- Use viewBox="0 0 800 800" (adjust height as needed, width always 800)
- Style: classic flowchart symbols — rectangles for process steps, diamonds for decisions, ovals for start/end, parallelograms for I/O
- Colors: use a clean palette (#4A90D9 blue for process, #FFD93D yellow for decision, #50C878 green for start/end, #FF6B6B red for error paths, #f8f9fa background)
- Font: font-family="Arial, sans-serif"; centered text inside shapes
- All text must be in Korean if the prompt is Korean
- Label all decision branches (예/아니오, Yes/No, True/False)
- Flow should read top-to-bottom or left-to-right
- Include connectors for loops/back-edges that route cleanly around boxes
- No external resources, no JavaScript

═══ TEXT OVERFLOW RULES — KOREAN TEXT IS WIDER THAN LATIN ═══
- viewBox width is 800. ALL text MUST stay within x=20 to x=780.
- Korean characters at font-size 14: max ~40 chars per line inside shapes.
- If text is too long for a shape, use 2 lines (separate <text> elements with dy offset).

═══ ARROW RULES — VIOLATIONS WILL PRODUCE BROKEN DIAGRAMS ═══
RENDERING ORDER (non-negotiable):
1. First: ALL shapes (rectangles, diamonds, ovals) and text labels
2. Last: ALL arrows — they MUST be the final elements before </svg>

ARROW GEOMETRY:
- Arrows connect shape EDGES (not centers, not inside)
- Every arrow ENDS 15px BEFORE the target shape edge (arrowhead touches edge, no overlap)
- ABSOLUTE BAN: no arrow may pass through any shape it is not connected to
- Back-edges (loops): route LEFT of all boxes or RIGHT of all boxes, never crossing through""",

    "comparison": """You are an expert SVG comparison diagram generator.
Generate clean, readable, manually-editable SVG code for side-by-side comparisons, versus diagrams, and feature matrix tables.

Rules:
- Output ONLY the SVG code, nothing else. Start with <svg and end with </svg>.
- Use viewBox="0 0 800 700" (adjust height as needed, width always 800)
- Style: clean two-column or multi-column layout, clear visual separation, checkmarks/crosses for features
- Colors: use a clean palette (#4A90D9 blue for option A, #50C878 green for option B, #FF6B6B red for option C if needed, #f8f9fa row backgrounds alternating with #ffffff, #2D3748 text)
- Font: font-family="Arial, sans-serif"; bold for column headers and item names
- All text must be in Korean if the prompt is Korean
- Include a title row, column headers, and feature rows
- Use ✓ (checkmark) and ✗ (cross) or colored circles to indicate presence/absence
- Highlight the recommended/winner column with a subtle border or background
- No external resources, no JavaScript

═══ TEXT OVERFLOW RULES — KOREAN TEXT IS WIDER THAN LATIN ═══
- viewBox width is 800. ALL text MUST stay within x=20 to x=780.
- In a 2-column layout each column is ~360px wide; Korean at font-size 14: max ~25 chars per cell.
- In a 3-column layout each column is ~240px wide; Korean at font-size 13: max ~16 chars per cell.
- If cell text overflows, wrap to 2 lines using separate <text> elements with dy offset.""",

    "hierarchy": """You are an expert SVG hierarchy diagram generator.
Generate clean, readable, manually-editable SVG code for tree structures, organizational charts, and hierarchical decompositions.

Rules:
- Output ONLY the SVG code, nothing else. Start with <svg and end with </svg>.
- Use viewBox="0 0 800 700" (adjust height as needed, width always 800)
- Style: top-down tree layout, consistent node sizes, clean connecting lines
- Colors: use level-based coloring (#4A90D9 blue for root, #50C878 green for level 2, #6C5CE7 purple for level 3, #FFD93D yellow for leaf nodes, #f8f9fa background)
- Font: font-family="Arial, sans-serif"; bold for root and important nodes; regular for leaves
- All text must be in Korean if the prompt is Korean
- Root node at the top center; children spread horizontally below each parent
- Use straight or elbow connector lines from parent bottom-center to child top-center
- Equal horizontal spacing between siblings; equal vertical spacing between levels
- If tree is wide, reduce node width and font size proportionally to fit within 800px
- No external resources, no JavaScript

═══ TEXT OVERFLOW RULES — KOREAN TEXT IS WIDER THAN LATIN ═══
- viewBox width is 800. ALL text MUST stay within x=10 to x=790.
- Node width should be calculated based on the longest label: Korean at font-size 13 ≈ 13px/char.
- If a label is too long for the node box, use 2 lines or abbreviate.

═══ CONNECTOR RULES ═══
RENDERING ORDER (non-negotiable):
1. First: ALL node boxes and text labels
2. Last: ALL connector lines — they MUST be the final elements before </svg>

CONNECTOR GEOMETRY:
- Lines connect parent BOTTOM-CENTER to child TOP-CENTER
- ABSOLUTE BAN: no connector may pass through any node box it is not connected to
- For wide trees where siblings are far apart: use elbow connectors (horizontal segment at parent level, then vertical down to child)""",
}


def _build_prompt(svg_type: str, description: str, style: str, language: str = "ko", reference_svg: str = "") -> str:
    style_hints = {
        "modern": "modern flat design, clean lines",
        "minimal": "minimal, monochrome, simple shapes only",
        "colorful": "vibrant colors, rich visual style",
        "dark": "dark background (#1a1a2e), light elements, neon accents",
    }
    style_desc = style_hints.get(style, style_hints["modern"])

    # 한글 SVG 참조가 있으면 번역 모드
    if reference_svg and language == "en":
        return (
            f"Translate the following Korean SVG to English. "
            f"ONLY translate text content (labels, titles, descriptions) to English. "
            f"Keep the EXACT same SVG structure, CSS styles, viewBox, coordinates, colors, and all attributes. "
            f"Do NOT restructure, redesign, or regenerate the SVG — only change Korean text to English equivalents.\n\n"
            f"Korean SVG:\n{reference_svg}"
        )

    lang_instruction = ""
    if language == "en":
        lang_instruction = "\nIMPORTANT: ALL text labels, titles, and descriptions in the SVG MUST be in English. Do NOT use Korean."
    else:
        lang_instruction = "\nIMPORTANT: ALL text labels, titles, and descriptions in the SVG MUST be in Korean."

    return f"Generate an SVG {svg_type} for: {description}\nStyle: {style_desc}{lang_instruction}"


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


def _fix_style_block_css(svg: str) -> str:
    """Repair common CSS syntax mistakes inside <style> blocks."""

    def _repair(match: re.Match[str]) -> str:
        css = match.group(1)
        css = re.sub(r'([a-zA-Z_-][\w-]*)\s*=\s*"([^"]+)"', r"\1: \2;", css)
        css = re.sub(r"([a-zA-Z_-][\w-]*)\s*=\s*'([^']+)'", r"\1: \2;", css)
        css = re.sub(
            r"([a-zA-Z_-][\w-]*)\s*:\s*([^;{}\n]+)(?=\s+[a-zA-Z_-][\w-]*\s*:|\s*})",
            r"\1: \2;",
            css,
        )
        css = re.sub(
            r"([a-zA-Z_-][\w-]*)\s*:\s*([^;{}\n]+)(\s*\n)",
            r"\1: \2;\3",
            css,
        )
        css = re.sub(r";\s*;", ";", css)
        css = re.sub(r"\s+}", " }", css)
        return f"<style>{css}</style>"

    return re.sub(r"<style\b[^>]*>([\s\S]*?)</style>", _repair, svg, flags=re.IGNORECASE)


def _fix_common_svg_issues(svg: str) -> str:
    """Normalize easy-to-repair SVG issues before linting/parsing."""
    if 'xmlns=' not in svg:
        svg = svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    svg = svg.replace('stroke="currentColor"', 'stroke="#4A90D9"')
    svg = svg.replace('fill="currentColor"', 'fill="#4A90D9"')
    svg = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', svg)
    svg = _fix_style_block_css(svg)
    svg = _fix_border_fill_none(svg)
    svg = _fix_path_fill_none(svg)
    return svg


def _fix_border_fill_none(svg: str) -> str:
    """CSS 클래스에 stroke만 있고 fill이 없으면 fill: none 추가 (검은 박스 방지)."""
    def _add_fill_none(match: re.Match[str]) -> str:
        css = match.group(1)
        # stroke가 있지만 fill이 없는 CSS 규칙에 fill: none 추가
        def _fix_rule(rule_match: re.Match[str]) -> str:
            selector = rule_match.group(1)
            body = rule_match.group(2)
            has_stroke = re.search(r'\bstroke\s*:', body)
            has_fill = re.search(r'\bfill\s*:', body)
            # border/outline/connector 류 클래스이거나 stroke만 있고 fill 없는 경우
            is_border_class = any(kw in selector.lower() for kw in
                                  ['border', 'outline', 'connector', 'line', 'separator', 'divider'])
            if has_stroke and not has_fill and is_border_class:
                body = body.rstrip()
                if not body.endswith(';'):
                    body += ';'
                body += ' fill: none;'
            return f"{selector} {{{body}}}"
        css = re.sub(r'([^{}]+)\{([^{}]+)\}', _fix_rule, css)
        return f"<style>{css}</style>"
    return re.sub(r"<style\b[^>]*>([\s\S]*?)</style>", _add_fill_none, svg, flags=re.IGNORECASE)


def _fix_path_fill_none(svg: str) -> str:
    """stroke가 있지만 fill이 없는 <path>/<line>/<polyline>에 fill='none' 추가."""
    def _fix_element(match: re.Match[str]) -> str:
        tag_content = match.group(0)
        has_stroke = 'stroke=' in tag_content or 'stroke:' in tag_content
        has_fill = 'fill=' in tag_content
        if has_stroke and not has_fill:
            # 자기 닫는 태그인 경우
            if tag_content.rstrip().endswith('/>'):
                return tag_content.replace('/>', ' fill="none"/>')
            # 여는 태그인 경우
            return tag_content[:-1] + ' fill="none">'
        return tag_content
    svg = re.sub(r'<path\b[^>]*/?>', _fix_element, svg)
    svg = re.sub(r'<line\b[^>]*/?>', _fix_element, svg)
    svg = re.sub(r'<polyline\b[^>]*/?>', _fix_element, svg)
    return svg


def _parse_num(value: str | None, default: float = 0.0) -> float:
    if not value:
        return default
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(match.group(0)) if match else default


def _parse_viewbox(root: ET.Element) -> tuple[float, float, float, float]:
    viewbox = root.get("viewBox")
    if viewbox:
        parts = [p for p in re.split(r"[\s,]+", viewbox.strip()) if p]
        if len(parts) == 4:
            return tuple(float(p) for p in parts)  # type: ignore[return-value]
    width = _parse_num(root.get("width"), 800.0)
    height = _parse_num(root.get("height"), 600.0)
    return 0.0, 0.0, width, height


def _text_content(el: ET.Element) -> str:
    parts = [el.text or ""]
    for child in el:
        parts.append(child.text or "")
        parts.append(child.tail or "")
    return "".join(parts).strip()


def _approx_text_width(text: str, font_size: float) -> float:
    width = 0.0
    for ch in text:
        if ord(ch) > 127:
            width += font_size * 0.95
        elif ch.isspace():
            width += font_size * 0.35
        else:
            width += font_size * 0.6
    return width


def _nearest_container_width(root: ET.Element, x: float, y: float) -> float | None:
    best_distance = math.inf
    best_width: float | None = None

    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "rect":
            rx = _parse_num(el.get("x"))
            ry = _parse_num(el.get("y"))
            rw = _parse_num(el.get("width"))
            rh = _parse_num(el.get("height"))
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                distance = abs((rx + rw / 2) - x) + abs((ry + rh / 2) - y)
                if distance < best_distance:
                    best_distance = distance
                    best_width = max(rw - 16.0, 0.0)
        elif tag == "ellipse":
            cx = _parse_num(el.get("cx"))
            cy = _parse_num(el.get("cy"))
            rx = _parse_num(el.get("rx"))
            ry = _parse_num(el.get("ry"))
            if rx and ry and ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                distance = abs(cx - x) + abs(cy - y)
                if distance < best_distance:
                    best_distance = distance
                    best_width = max(rx * 2 - 16.0, 0.0)
        elif tag == "polygon":
            points = []
            for pair in re.findall(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", el.get("points", "")):
                points.append((float(pair[0]), float(pair[1])))
            if points:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                if min(xs) <= x <= max(xs) and min(ys) <= y <= max(ys):
                    distance = abs((min(xs) + max(xs)) / 2 - x) + abs((min(ys) + max(ys)) / 2 - y)
                    if distance < best_distance:
                        best_distance = distance
                        best_width = max(max(xs) - min(xs) - 20.0, 0.0)

    return best_width


def _lint_svg_quality(svg: str) -> list[str]:
    svg = _fix_common_svg_issues(svg)
    issues: list[str] = []

    for style_match in re.finditer(r"<style\b[^>]*>([\s\S]*?)</style>", svg, flags=re.IGNORECASE):
        if re.search(r"[a-zA-Z_-][\w-]*\s*=\s*['\"][^'\"]+['\"]", style_match.group(1)):
            issues.append("style block contains XML-style assignments instead of CSS declarations")
            break

    try:
        root = ET.fromstring(svg)
    except ET.ParseError as e:
        issues.append(f"svg is not valid XML: {e}")
        return issues

    _, _, viewbox_width, viewbox_height = _parse_viewbox(root)

    # stroke가 있지만 fill이 없는 rect 검출 (검은 박스 위험)
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "rect":
            has_stroke = el.get("stroke") is not None
            has_fill = el.get("fill") is not None
            has_class = el.get("class", "")
            # stroke가 있고 fill이 없는 rect (CSS 클래스로 fill 설정된 경우 제외 가능)
            if has_stroke and not has_fill and not has_class:
                issues.append(f'rect with stroke but no fill attribute — may render as black box')

    for el in root.iter():
        if el.tag.rsplit("}", 1)[-1] != "text":
            continue

        text = _text_content(el)
        if not text:
            continue

        x = _parse_num(el.get("x"))
        y = _parse_num(el.get("y"))
        font_size = _parse_num(el.get("font-size"), 14.0)
        width = _approx_text_width(text, font_size)

        if x < 0 or y < 0 or x > viewbox_width or y > viewbox_height:
            issues.append(f'text "{text[:40]}" is positioned outside the viewBox')
            continue

        if x + width > viewbox_width - 10:
            issues.append(f'text "{text[:40]}" overflows the right edge of the viewBox')
            continue

        container_width = _nearest_container_width(root, x, y)
        if container_width and width > container_width:
            issues.append(f'text "{text[:40]}" is wider than its containing shape')

    return issues


async def _repair_svg_with_model(
    client: httpx.AsyncClient,
    api_key: str,
    svg: str,
    issues: list[str],
    svg_type: str,
    style: str,
    language: str,
) -> str:
    issue_lines = "\n".join(f"- {issue}" for issue in issues[:10])
    repair_prompt = f"""You are repairing a broken SVG {svg_type} diagram.
Return ONLY valid SVG markup.

Requirements:
- Keep the same topic and overall meaning.
- Fix invalid CSS in <style> blocks.
- Fix overlapping labels, clipped text, and text that is wider than its box.
- If text is too long, wrap it into multiple <text>/<tspan> lines or enlarge the container.
- Preserve the intended visual style: {style}.
- Keep all labels in {"English" if language == "en" else "Korean"}.
- Ensure the final SVG is valid XML and renders cleanly inside its own viewBox.
- Do not output markdown fences or explanations.

Detected issues:
{issue_lines}

SVG to repair:
{svg}
"""
    payload = {
        "contents": [{"role": "user", "parts": [{"text": repair_prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 32768,
        },
    }
    resp = await client.post(
        GEMINI_API_URL,
        params={"key": api_key},
        json=payload,
    )
    resp.raise_for_status()
    data = resp.json()
    candidate = data["candidates"][0]
    repaired_raw = candidate["content"]["parts"][0]["text"]
    return _extract_svg(repaired_raw)


def _validate_and_fix_svg(svg: str) -> str:
    """SVG XML 유효성 검사. 깨진 경우 단계별 복구 시도."""
    # xmlns 누락 시 추가
    if 'xmlns=' not in svg:
        svg = svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    # currentColor → 실제 색상 (img 태그에서 렌더링 안 됨)
    svg = svg.replace('stroke="currentColor"', 'stroke="#4A90D9"')
    svg = svg.replace('fill="currentColor"', 'fill="#4A90D9"')

    # Step 1: 이스케이프되지 않은 & 문자 처리 (가장 흔한 XML 파싱 오류)
    svg = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', svg)

    try:
        ET.fromstring(svg)
        return svg
    except ET.ParseError as e:
        logger.warning("SVG XML 파싱 실패: %s — 복구 시도", e)

    fixed = svg

    # Step 2: 잘린 속성값 제거 (예: fill="#4)
    fixed = re.sub(r'<[^>]*$', '', fixed.rstrip())
    if not fixed.rstrip().endswith("</svg>"):
        fixed = fixed.rstrip() + "\n</svg>"
    try:
        ET.fromstring(fixed)
        logger.info("SVG 복구 성공 (잘린 태그 제거)")
        return fixed
    except ET.ParseError:
        pass

    # Step 3: 닫히지 않은 태그 강제 닫기 (text, g, rect, path 등)
    unclosed_tags = re.findall(r'<(text|g|tspan|style|defs|filter|marker)\b[^/]*(?<!/)>', fixed)
    for tag in reversed(unclosed_tags):
        close_tag = f"</{tag}>"
        if fixed.count(f"<{tag}") > fixed.count(close_tag):
            # </svg> 앞에 닫는 태그 삽입
            fixed = fixed.replace("</svg>", f"{close_tag}\n</svg>", 1)
    try:
        ET.fromstring(fixed)
        logger.info("SVG 복구 성공 (닫히지 않은 태그 처리)")
        return fixed
    except ET.ParseError:
        pass

    # Step 4: 마지막 완전한 최상위 요소까지만 유지
    last_complete = fixed.rfind("</g>")
    if last_complete == -1:
        last_complete = fixed.rfind("/>")
    if last_complete > 0:
        fixed = fixed[:last_complete + (4 if "</g>" in fixed[last_complete:last_complete+4] else 2)]
        fixed = fixed.rstrip() + "\n</svg>"
    try:
        ET.fromstring(fixed)
        logger.info("SVG 복구 성공 (불완전 요소 절삭)")
        return fixed
    except ET.ParseError as e:
        raise ValueError(f"SVG가 유효하지 않아 복구할 수 없습니다: {e}") from e


async def generate_svg_async(
    api_key: str,
    description: str,
    svg_type: str = "architecture",
    style: str = "modern",
    max_retries: int = 3,
    language: str = "ko",
    reference_svg: str = "",
) -> str:
    """SVG 코드 생성 후 유효성 검사까지 수행. 실패 시 재시도."""
    system_prompt = SYSTEM_PROMPTS.get(svg_type, SYSTEM_PROMPTS["architecture"])

    # 참조 SVG가 있으면 번역 전용 시스템 프롬프트 사용
    if reference_svg and language == "en":
        system_prompt = (
            "You are an SVG translator. Given a Korean SVG, translate ONLY the text content to English. "
            "Preserve the EXACT same SVG structure, CSS styles, viewBox, coordinates, colors, classes, "
            "and all attributes. Do NOT restructure, redesign, add, or remove any SVG elements. "
            "Output valid XML SVG only."
        )
    else:
        system_prompt += """

Global SVG quality requirements:
- Output valid XML SVG only.
- Never use XML attributes inside <style> blocks. CSS must use property: value; syntax only.
- Avoid giant solid fallback shapes caused by invalid styles.
- Before finishing, verify every text label fits inside its shape and does not overlap nearby labels.
- For long labels, wrap into multiple lines using <tspan> or separate <text> elements.
- If a label cannot fit, enlarge the containing box or diamond instead of letting text overflow.
- Keep at least 12px padding between text and shape borders.
- All CSS classes for borders/outlines MUST include "fill: none;" to prevent black fill.
- Arrow/connector labels must have a white background rect behind them for readability.
- Arrows must maintain at least 20px clearance from boxes they are not connected to.
"""
        if language == "en":
            system_prompt = system_prompt.replace(
                "All text must be in Korean if the prompt is Korean",
                "All text MUST be in English. Do NOT use Korean text."
            )
    user_prompt = _build_prompt(svg_type, description, style, language, reference_svg)

    import asyncio as _aio
    import time as _time

    last_err = None
    t_start = _time.monotonic()
    total_deadline = 180.0  # 전체 최대 3분
    was_truncated = False  # MAX_TOKENS 잘림 발생 여부

    async with httpx.AsyncClient(timeout=90.0) as client:
        for attempt in range(1, max_retries + 1):
            if _time.monotonic() - t_start > total_deadline:
                break

            # 이전 시도에서 잘렸으면 단순화 지시 추가
            current_user_prompt = user_prompt
            if was_truncated:
                current_user_prompt += (
                    "\n\nCRITICAL: Previous attempt was truncated (too long). "
                    "You MUST simplify the SVG significantly:\n"
                    "- Use fewer elements (max 15-20 shapes)\n"
                    "- Shorter text labels\n"
                    "- No decorative elements (shadows, gradients)\n"
                    "- Simple flat colors only\n"
                    "- Reduce viewBox height if possible\n"
                    "- Keep the SVG under 3000 characters total"
                )

            payload = {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": current_user_prompt}]}],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 65536,
                    "thinkingConfig": {"thinkingBudget": 8192},
                },
            }

            try:
                resp = await client.post(
                    GEMINI_API_URL,
                    params={"key": api_key},
                    json=payload,
                )
            except Exception as e:
                last_err = e
                logger.warning("SVG HTTP 요청 실패: %s — 재시도 %d/%d", e, attempt, max_retries)
                await _aio.sleep(min(8 * (2 ** (attempt - 1)), 40))
                continue

            if resp.status_code == 429:
                delay = min(10 * (2 ** (attempt - 1)), 40)
                logger.warning("SVG 429 rate limit, %ds 후 재시도 (%d/%d)", delay, attempt, max_retries)
                await _aio.sleep(delay)
                last_err = ValueError("429 rate limit")
                continue

            resp.raise_for_status()
            data = resp.json()

            # finishReason 확인 — 잘린 출력 감지
            candidate = data["candidates"][0]
            finish_reason = candidate.get("finishReason", "")
            if finish_reason == "MAX_TOKENS":
                logger.warning("SVG 출력 잘림 (MAX_TOKENS) 시도 %d/%d — 단순화 후 재시도", attempt, max_retries)
                last_err = ValueError("SVG output truncated (MAX_TOKENS)")
                was_truncated = True
                await _aio.sleep(3)
                continue
            if finish_reason == "SAFETY":
                raise ValueError("SVG 콘텐츠가 안전 필터에 의해 차단됨")

            raw = candidate["content"]["parts"][0]["text"]
            try:
                svg = _extract_svg(raw)
                issues = _lint_svg_quality(svg)
                if issues:
                    logger.warning("SVG quality issues detected for %s: %s", svg_type, "; ".join(issues[:5]))
                    try:
                        repaired = await _repair_svg_with_model(
                            client=client,
                            api_key=api_key,
                            svg=svg,
                            issues=issues,
                            svg_type=svg_type,
                            style=style,
                            language=language,
                        )
                        repaired_issues = _lint_svg_quality(repaired)
                        if len(repaired_issues) < len(issues):
                            svg = repaired
                            issues = repaired_issues
                    except Exception as repair_err:
                        logger.warning("SVG repair pass failed: %s", repair_err)
                if issues:
                    logger.warning("Returning SVG with remaining issues: %s", "; ".join(issues[:5]))
                return svg
            except ValueError as e:
                last_err = e
                logger.warning("SVG 생성 시도 %d/%d 실패: %s — 재시도", attempt, max_retries, e)

    raise ValueError(f"SVG 생성 {max_retries}회 시도 후 실패: {last_err}")
