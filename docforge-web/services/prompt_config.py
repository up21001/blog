"""
사용자 편집 가능 프롬프트 — data/user_prompts.json 에 저장.
없으면 services/prompts.py 기본값 사용.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from . import prompts as prompts_defaults

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PACKAGE_ROOT / "data"
USER_PROMPTS_PATH = DATA_DIR / "user_prompts.json"

KEYS = ("blog", "philosophy", "plain", "tutorial", "review", "comparison", "troubleshoot", "weekly", "news", "prompt_eng", "document_user", "image_prompt_generator")

# document_user: {topic}
# image_prompt_generator: {topic}, {excerpt}, {count}


def _built_in_defaults() -> dict[str, str]:
    return {
        "blog": prompts_defaults.BLOG,
        "philosophy": prompts_defaults.PHILOSOPHY,
        "plain": prompts_defaults.PLAIN,
        "tutorial": prompts_defaults.TUTORIAL,
        "review": prompts_defaults.REVIEW,
        "comparison": prompts_defaults.COMPARISON,
        "troubleshoot": prompts_defaults.TROUBLESHOOT,
        "weekly": prompts_defaults.WEEKLY,
        "news": prompts_defaults.NEWS,
        "prompt_eng": prompts_defaults.PROMPT_ENG,
        "document_user": "주제: {topic}\n위 주제로 모듈형 블로그 문서를 작성하라. 각 섹션은 독립적으로 편집·재생성 가능한 블록 구조로 만들어라.",
        "image_prompt_generator": """Topic (Korean): {topic}

Article excerpt (for context — match diagrams to these sections):
{excerpt}

Generate exactly {count} separate lines. Each line is ONE English prompt for an AI image generator.

Priority styles (choose the most appropriate per section):
1. Technical concept diagram: clean flowchart, architecture diagram, layered system schematic
2. Infographic: data visualization, comparison chart, step-by-step process flow
3. 3D isometric illustration: server racks, hardware components, network topology
4. Abstract technical art: circuit patterns, data streams, neural network nodes

Rules:
- No readable text, letters, or numbers in the image
- No logos, faces, or celebrities
- Use flat design or isometric 3D — avoid photorealistic people
- Each prompt must match a specific section concept from the article excerpt
- Prefer diagram/schematic style over generic tech photos

Output only the prompts, one per line, no numbering or bullets.""",
    }


def get_effective_prompts() -> dict[str, str]:
    """생성 시 사용 — 파일 + 기본값 병합."""
    base = _built_in_defaults()
    if not USER_PROMPTS_PATH.is_file():
        return base
    try:
        raw = json.loads(USER_PROMPTS_PATH.read_text(encoding="utf-8"))
        for k in KEYS:
            if k in raw and isinstance(raw[k], str) and raw[k].strip():
                base[k] = raw[k]
    except Exception as e:
        logger.warning("user_prompts.json 로드 실패, 기본값 사용: %s", e)
    return base


def get_for_api() -> dict:
    """편집 화면용 + 메타."""
    eff = get_effective_prompts()
    return {
        "prompts": eff,
        "placeholders": {
            "document_user": ["topic"],
            "image_prompt_generator": ["topic", "excerpt", "count"],
            "blog": "시스템 지시 — 문서 템플릿 blog",
            "philosophy": "시스템 지시 — 문서 템플릿 philosophy",
            "plain": "시스템 지시 — 문서 템플릿 plain",
            "tutorial": "시스템 지시 — 문서 템플릿 tutorial",
            "review": "시스템 지시 — 문서 템플릿 review",
            "comparison": "시스템 지시 — 문서 템플릿 comparison",
            "troubleshoot": "시스템 지시 — 문서 템플릿 troubleshoot",
            "weekly": "시스템 지시 — 문서 템플릿 weekly",
            "news": "시스템 지시 — 문서 템플릿 news",
            "prompt_eng": "시스템 지시 — 문서 템플릿 prompt_eng",
        },
    }


def validate_prompts(d: dict[str, str]) -> None:
    """필수 플레이스홀더가 있으면 검증. 실패 시 ValueError."""
    d["document_user"].format(topic="테스트")
    d["image_prompt_generator"].format(topic="t", excerpt="e", count=1)


def save_prompts(updates: dict[str, str]) -> dict[str, str]:
    """부분 업데이트 저장 후 전체 유효성 검사."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    current = get_effective_prompts()
    for k, v in updates.items():
        if k in KEYS and isinstance(v, str):
            current[k] = v
    validate_prompts(current)
    USER_PROMPTS_PATH.write_text(
        json.dumps({k: current[k] for k in KEYS}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return current


def reset_to_defaults() -> None:
    if USER_PROMPTS_PATH.is_file():
        USER_PROMPTS_PATH.unlink()


def get_builtin_defaults() -> dict[str, str]:
    """편집기 ‘기본값으로 되돌리기’용 (파일 무시)."""
    return _built_in_defaults()
