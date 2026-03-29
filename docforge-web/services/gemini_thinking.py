"""Gemini 텍스트 모델(2.5 Flash 등)은 thinking_budget=0 이 거부된다.

thinking_config 를 빼면 기본이 0으로 잡혀 400 INVALID_ARGUMENT 가 날 수 있어,
텍스트 생성 호출에는 항상 양수 예산을 넘긴다."""

from __future__ import annotations

from google.genai import types

# 확장·장문 생성에도 쓰이므로 너무 작지 않게
DEFAULT_THINKING_BUDGET = 8192


def text_thinking_config(budget: int | None = None) -> types.ThinkingConfig:
    b = DEFAULT_THINKING_BUDGET if budget is None else max(1024, int(budget))
    return types.ThinkingConfig(thinking_budget=b)
