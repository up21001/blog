---
title: "AI 에이전트 설계 패턴 — ReAct, CoT, Tool Use를 Python으로 구현하기"
date: 2022-08-10T08:00:00+09:00
lastmod: 2022-08-17T08:00:00+09:00
description: "AI 에이전트의 핵심 설계 패턴인 ReAct, Chain of Thought, Tool Use를 Python으로 직접 구현합니다. 에이전트 루프 구조부터 멀티 에이전트 패턴까지 실무 코드로 상세히 설명합니다."
slug: "ai-agent-design-patterns-react-cot-tooluse"
categories: ["ai-agents"]
tags: ["AI 에이전트", "ReAct", "Chain of Thought", "Tool Use", "LLM 에이전트"]
series: []
draft: false
---

"LLM 앱"과 "AI 에이전트"는 다릅니다. LLM 앱은 입력을 받아 출력을 반환하는 단방향 파이프라인입니다. AI 에이전트는 목표를 달성하기 위해 스스로 계획을 세우고, 도구를 사용하고, 결과를 평가하며, 필요하면 방향을 바꾸는 자율적인 시스템입니다.

2026년 현재 에이전트는 개발 자동화, 데이터 분석, 리서치 어시스턴트 등 다양한 분야에서 실무 투입이 활발합니다. 이 글에서는 에이전트를 구성하는 세 가지 핵심 패턴 — **ReAct, Chain of Thought, Tool Use** — 을 Python으로 직접 구현하며 내부 동작 원리를 이해합니다.

## AI 에이전트란 무엇인가

에이전트를 한 문장으로 정의하면 "목표 달성을 위해 반복적으로 추론하고 행동하는 LLM 기반 시스템"입니다.

일반 LLM 호출과 에이전트의 차이는 **루프**에 있습니다.

```
# 일반 LLM 호출
입력 → LLM → 출력 (끝)

# 에이전트 루프
목표 설정
    ↓
계획 수립 (CoT)
    ↓
도구 선택 및 실행 (Tool Use)
    ↓
결과 관찰 (Observation)
    ↓
목표 달성 여부 판단
    ↓ (미달성 시 반복)
최종 응답
```

{{< figure src="/images/ai-agent-design-patterns.svg" alt="AI 에이전트 설계 패턴 — ReAct CoT Tool Use" caption="ReAct, CoT, Tool Use 패턴과 통합 에이전트 루프 구조" >}}

## 패턴 1: Chain of Thought (CoT)

Chain of Thought는 LLM이 복잡한 문제를 단계별로 사고하도록 유도하는 프롬프팅 기법입니다. 2022년 Google Brain의 논문에서 제안되었으며, 수학 문제와 논리 추론에서 극적인 성능 향상을 보여주었습니다.

### Zero-shot CoT

```python
from openai import OpenAI

client = OpenAI()

def chain_of_thought(problem: str, model: str = "gpt-4o") -> str:
    """Zero-shot Chain of Thought 프롬프팅"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"{problem}\n\n단계별로 생각해 보겠습니다:"
            }
        ],
        temperature=0,
        max_tokens=1000,
    )
    return response.choices[0].message.content

# 예시: 복잡한 계산
problem = """
어느 창고에 물건이 있습니다.
월요일에 전체의 1/3을 출고했습니다.
화요일에 남은 것의 1/4을 입고받았습니다.
수요일에 현재 물건의 40%를 출고했습니다.
처음에 900개가 있었다면, 수요일 출고 후 몇 개가 남았나요?
"""

result = chain_of_thought(problem)
print(result)
```

### Few-shot CoT

예시를 제공해 더 구체적인 사고 패턴을 유도합니다.

```python
FEW_SHOT_COT_PROMPT = """다음 예시를 참고해 문제를 풀어주세요.

예시 1:
문제: 사탕이 15개 있습니다. 3명에게 똑같이 나누면 1명당 몇 개인가요?
풀이:
1. 전체 사탕: 15개
2. 나눌 사람 수: 3명
3. 1명당 사탕 = 15 ÷ 3 = 5개
답: 5개

예시 2:
문제: 시속 60km로 달리는 차가 2시간 30분 동안 이동한 거리는?
풀이:
1. 속도: 60 km/h
2. 시간: 2시간 30분 = 2.5시간
3. 거리 = 60 × 2.5 = 150 km
답: 150 km

이제 풀어주세요:
문제: {problem}
풀이:"""

def few_shot_cot(problem: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": FEW_SHOT_COT_PROMPT.format(problem=problem)
            }
        ],
        temperature=0,
    )
    return response.choices[0].message.content
```

### CoT 적용 팁

CoT는 **모델 크기에 비례해 효과**가 납니다. GPT-4o, Claude 3.7 같은 대형 모델에서 가장 효과적이며, gpt-4o-mini 같은 경량 모델에서는 효과가 제한적입니다.

또한 CoT는 추론 비용이 높습니다. 단순 분류·추출 작업에는 직접 답을 요구하는 것이 빠르고 저렴합니다. 복잡한 다단계 추론, 수학 계산, 논리 검증에 선택적으로 적용하는 것이 좋습니다.

## 패턴 2: Tool Use (Function Calling)

Tool Use는 LLM이 외부 함수, API, 데이터베이스를 호출할 수 있게 하는 패턴입니다. OpenAI의 Function Calling, Anthropic의 Tool Use가 대표적인 구현입니다.

### 도구 정의와 실행 엔진

```python
import json
import requests
from typing import Callable, Any
from openai import OpenAI

client = OpenAI()

# 도구 레지스트리 — 이름으로 함수를 찾아 실행
TOOL_REGISTRY: dict[str, Callable] = {}

def register_tool(func: Callable) -> Callable:
    """데코레이터로 도구 등록"""
    TOOL_REGISTRY[func.__name__] = func
    return func

@register_tool
def search_web(query: str) -> str:
    """웹에서 정보를 검색합니다."""
    # 실제로는 Tavily, SerpAPI 등 사용
    return f"'{query}'에 대한 검색 결과: [예시 결과]"

@register_tool
def calculate(expression: str) -> str:
    """수학 표현식을 계산합니다."""
    try:
        # eval은 보안 위험 — 실제로는 sympy 등 사용
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"계산 오류: {e}"

@register_tool
def get_current_time() -> str:
    """현재 날짜와 시간을 반환합니다."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@register_tool
def read_file(filepath: str) -> str:
    """파일 내용을 읽습니다."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()[:2000]  # 처음 2000자만
    except FileNotFoundError:
        return f"파일 없음: {filepath}"

# OpenAI tools 스키마 정의
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "최신 정보나 모르는 사실을 웹에서 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색 쿼리"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "수학 계산을 수행합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "계산할 수식 (예: 2 + 3 * 4)"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "현재 날짜와 시간을 조회합니다.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
]

def execute_tool(tool_name: str, tool_args: dict) -> str:
    """도구 이름과 인수로 실제 함수 실행"""
    if tool_name not in TOOL_REGISTRY:
        return f"알 수 없는 도구: {tool_name}"
    func = TOOL_REGISTRY[tool_name]
    return func(**tool_args)
```

## 패턴 3: ReAct (Reasoning + Acting)

ReAct는 "추론(Reasoning)과 행동(Acting)을 번갈아 반복"하는 패턴입니다. 2023년 Princeton/Google의 논문에서 제안되었으며, 에이전트 루프의 핵심 설계 패턴이 되었습니다.

### ReAct 에이전트 완전 구현

```python
class ReActAgent:
    """ReAct 패턴으로 구현한 AI 에이전트"""

    def __init__(
        self,
        tools: list,
        model: str = "gpt-4o",
        max_iterations: int = 10,
        verbose: bool = True,
    ):
        self.tools = tools
        self.model = model
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.client = OpenAI()

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)

    def run(self, goal: str) -> str:
        """에이전트 루프 실행"""
        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 목표를 달성하기 위해 도구를 사용하는 AI 에이전트입니다. "
                    "필요하면 도구를 여러 번 사용하고, 목표가 달성되면 최종 답변을 제공하세요. "
                    "항상 한국어로 답변합니다."
                )
            },
            {"role": "user", "content": goal}
        ]

        self._log(f"\n[에이전트 시작] 목표: {goal}\n{'='*60}")

        for iteration in range(self.max_iterations):
            self._log(f"\n[반복 {iteration + 1}/{self.max_iterations}]")

            # LLM 호출
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
            )

            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            # 도구 호출 없이 최종 답변
            if finish_reason == "stop" or not message.tool_calls:
                self._log(f"\n[최종 답변]\n{message.content}")
                return message.content

            # 도구 호출 처리
            messages.append(message)

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                self._log(f"  → 도구 호출: {func_name}({func_args})")

                # 실제 도구 실행
                tool_result = execute_tool(func_name, func_args)

                self._log(f"  ← 도구 결과: {tool_result[:200]}")

                # 도구 결과를 메시지에 추가
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

        # 최대 반복 초과
        self._log("\n[경고] 최대 반복 횟수 초과")
        return "최대 반복 횟수를 초과했습니다. 더 구체적인 목표를 제시해 주세요."


# 사용 예시
agent = ReActAgent(tools=TOOLS, model="gpt-4o", max_iterations=8)

result = agent.run(
    "오늘 날짜를 확인하고, (123 * 456 + 789)를 계산한 뒤, "
    "두 결과를 합쳐 요약해 주세요."
)
```

출력 예시:
```
[에이전트 시작] 목표: 오늘 날짜를 확인하고...
============================================================

[반복 1/8]
  → 도구 호출: get_current_time({})
  ← 도구 결과: 2026-03-24 22:15:33

[반복 2/8]
  → 도구 호출: calculate({"expression": "123 * 456 + 789"})
  ← 도구 결과: 56877

[최종 답변]
오늘 날짜는 2026년 3월 24일이며, 계산 결과는 56,877입니다.
```

## 에이전트 루프 안정성 강화

실무 에이전트에서 자주 발생하는 문제와 해결 방법입니다.

### 무한 루프 방지

```python
class SafeReActAgent(ReActAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_call_history: list[str] = []

    def _detect_loop(self, tool_name: str, tool_args: dict) -> bool:
        """동일한 도구를 같은 인수로 3번 이상 호출하면 루프로 판단"""
        call_signature = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"
        self.tool_call_history.append(call_signature)
        return self.tool_call_history.count(call_signature) >= 3
```

### 비용 추적

```python
class CostTrackingAgent(ReActAgent):
    def __init__(self, *args, budget_usd: float = 0.10, **kwargs):
        super().__init__(*args, **kwargs)
        self.budget_usd = budget_usd
        self.total_cost = 0.0

    def _calculate_cost(self, usage) -> float:
        # gpt-4o 기준
        input_cost = (usage.prompt_tokens / 1_000_000) * 2.50
        output_cost = (usage.completion_tokens / 1_000_000) * 10.00
        return input_cost + output_cost

    def _check_budget(self, cost: float) -> bool:
        self.total_cost += cost
        if self.total_cost > self.budget_usd:
            self._log(f"[예산 초과] ${self.total_cost:.4f} > ${self.budget_usd}")
            return False
        return True
```

## 멀티 에이전트 패턴

복잡한 태스크는 단일 에이전트보다 여러 에이전트가 협력하는 방식이 효과적입니다.

```python
class OrchestratorAgent:
    """여러 전문 에이전트를 조율하는 오케스트레이터"""

    def __init__(self):
        self.research_agent = ReActAgent(
            tools=TOOLS,
            model="gpt-4o",
        )
        self.writer_agent = ReActAgent(
            tools=[],  # 도구 없이 글쓰기만
            model="gpt-4o",
        )
        self.reviewer_agent = ReActAgent(
            tools=[],
            model="gpt-4o-mini",  # 검토는 저렴한 모델로
        )

    def run(self, topic: str) -> str:
        """리서치 → 작성 → 검토 파이프라인"""

        # 1단계: 리서치 에이전트가 정보 수집
        research_result = self.research_agent.run(
            f"'{topic}'에 대해 웹에서 최신 정보를 검색하고 핵심 내용을 정리해 주세요."
        )

        # 2단계: 작성 에이전트가 블로그 포스트 작성
        draft = self.writer_agent.run(
            f"다음 리서치 내용을 바탕으로 기술 블로그 포스트를 작성해 주세요:\n\n{research_result}"
        )

        # 3단계: 검토 에이전트가 품질 확인
        final = self.reviewer_agent.run(
            f"다음 블로그 포스트를 검토하고 개선해 주세요:\n\n{draft}"
        )

        return final
```

## Anthropic Claude Tool Use

Claude 3.7은 OpenAI와 약간 다른 Tool Use 구문을 사용합니다.

```python
import anthropic

client = anthropic.Anthropic()

claude_tools = [
    {
        "name": "calculate",
        "description": "수학 표현식을 계산합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "계산할 수식"
                }
            },
            "required": ["expression"]
        }
    }
]

response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    tools=claude_tools,
    messages=[{"role": "user", "content": "1234 * 5678은 얼마인가요?"}]
)

# 도구 호출 처리
if response.stop_reason == "tool_use":
    for block in response.content:
        if block.type == "tool_use":
            tool_name = block.name
            tool_input = block.input
            result = execute_tool(tool_name, tool_input)
            print(f"도구 결과: {result}")
```

## Extended Thinking + Tool Use (Claude 3.7)

Claude 3.7의 Extended Thinking을 에이전트와 결합하면 복잡한 문제 해결 능력이 크게 향상됩니다.

```python
response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000,  # 추론에 사용할 최대 토큰
    },
    tools=claude_tools,
    messages=[{
        "role": "user",
        "content": "복잡한 알고리즘 문제를 단계별로 분석하고 Python 코드로 구현해 주세요."
    }]
)

# thinking 블록과 응답 분리
for block in response.content:
    if block.type == "thinking":
        print(f"[내부 추론 과정]\n{block.thinking[:500]}...")
    elif block.type == "text":
        print(f"[최종 답변]\n{block.text}")
```

## 에이전트 설계 시 주의사항

**결정론적 도구 사용**: 에이전트가 외부 API를 호출할 때는 멱등성(idempotent)이 있는 도구를 우선 사용합니다. 같은 작업을 두 번 실행해도 부작용이 없어야 합니다. 이메일 발송, 주문 처리 같은 부작용이 있는 도구는 반드시 사람의 확인을 거치는 Human-in-the-Loop 패턴을 적용합니다.

**컨텍스트 길이 관리**: 에이전트 루프를 반복할수록 메시지 히스토리가 쌓여 토큰을 소모합니다. 오래된 도구 결과를 요약해 압축하는 전략이 필요합니다.

**에러 복구**: 도구 실행 실패 시 에이전트가 대안을 찾도록 프롬프트를 설계합니다. "도구 호출에 실패하면 다른 방법을 시도하세요"라는 시스템 프롬프트가 도움이 됩니다.

## 마치며

ReAct, CoT, Tool Use는 서로 독립된 패턴이 아닙니다. 실제 에이전트는 세 패턴을 동시에 활용합니다. CoT로 계획을 세우고, Tool Use로 실행하고, ReAct 루프로 결과를 평가하며 반복합니다.

에이전트 개발의 핵심은 **시스템 프롬프트 설계**입니다. LLM이 언제 도구를 사용하고, 언제 멈추고, 어떻게 에러에 대응할지를 명확히 지시하는 것이 코드보다 중요합니다. 탄탄한 시스템 프롬프트 위에 단순한 루프 코드를 얹는 것이 과도하게 복잡한 프레임워크를 쓰는 것보다 대부분의 경우 더 잘 동작합니다.
