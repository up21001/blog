---
title: "OpenAI API 실전 가이드 — Python으로 GPT 앱 처음 만들기"
date: 2023-11-26T10:17:00+09:00
lastmod: 2023-11-30T10:17:00+09:00
description: "OpenAI API 키 발급부터 기본 호출, 스트리밍, Function Calling, 비용 관리까지 Python으로 GPT 앱을 처음 만드는 완전한 실전 가이드입니다. 13년 차 엔지니어가 실무 팁을 담아 정리했습니다."
slug: "openai-api-python-beginner-guide"
categories: ["ai-automation"]
tags: ["OpenAI API", "GPT", "Python", "AI 앱 개발", "Function Calling"]
series: []
draft: false
---

OpenAI API를 처음 사용하려는 개발자가 가장 많이 막히는 지점이 있습니다. API 키 발급은 했는데 실제 앱에 어떻게 연동하는지, 스트리밍은 어떻게 구현하는지, 비용을 어떻게 관리하는지 — 이 세 가지입니다. 13년 차 엔지니어로서 수십 개의 GPT 연동 프로젝트를 경험하며 얻은 실전 지식을 이 글에 모두 담겠습니다.

## 사전 준비

Python 3.9 이상과 pip가 설치되어 있다면 시작할 수 있습니다. OpenAI 공식 SDK를 설치합니다.

```bash
pip install openai python-dotenv
```

`python-dotenv`는 API 키를 코드에 직접 노출하지 않고 `.env` 파일로 관리하기 위해 필요합니다.

{{< figure src="/images/openai-api-python-guide.svg" alt="OpenAI API Python 앱 개발 플로우" caption="API 키 발급부터 Function Calling까지 단계별 개발 흐름" >}}

## 1단계: API 키 발급과 환경 설정

[platform.openai.com](https://platform.openai.com)에 가입 후 **API Keys** 메뉴에서 새 키를 생성합니다. 키는 생성 직후 한 번만 표시되므로 반드시 안전한 곳에 복사해 두어야 합니다.

프로젝트 루트에 `.env` 파일을 만들고 키를 저장합니다.

```bash
# .env
OPENAI_API_KEY=sk-proj-...여기에_실제_키_입력...
```

`.gitignore`에 `.env`를 반드시 추가합니다. API 키가 GitHub에 올라가면 OpenAI가 자동으로 키를 비활성화하고 알림을 보내지만, 그 사이 요금이 발생할 수 있습니다.

```python
# config.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
```

## 2단계: 기본 API 호출

OpenAI API의 핵심은 `chat.completions.create()` 메서드입니다. `messages` 파라미터에 대화 히스토리를 배열로 전달합니다.

```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": "당신은 친절한 Python 코딩 튜터입니다. 한국어로 답변합니다."
        },
        {
            "role": "user",
            "content": "리스트 컴프리헨션을 언제 쓰는 게 좋나요?"
        }
    ],
    max_tokens=500,
    temperature=0.7,
)

print(response.choices[0].message.content)
print(f"사용 토큰: {response.usage.total_tokens}")
```

### 주요 파라미터 설명

**model**: 어떤 모델을 사용할지 지정합니다. `gpt-4o`는 최상위, `gpt-4o-mini`는 경량 저비용 버전입니다.

**temperature**: 0.0~2.0 범위로 창의성을 조절합니다. 코드 생성·분류 작업은 0.0~0.3, 창작·브레인스토밍은 0.7~1.2를 권장합니다.

**max_tokens**: 응답의 최대 토큰 수를 제한합니다. 설정하지 않으면 모델 최대값까지 생성하여 비용이 예상보다 높아질 수 있습니다.

**top_p**: temperature와 함께 사용하는 다른 창의성 조절 파라미터입니다. 일반적으로 temperature만 조절하고 top_p는 기본값(1.0)을 유지하는 것을 권장합니다.

## 3단계: 스트리밍으로 실시간 응답 구현

ChatGPT처럼 글자가 하나씩 나타나는 UX를 구현하려면 스트리밍이 필요합니다. `stream=True`를 설정하면 됩니다.

```python
def stream_response(user_message: str) -> None:
    """스트리밍으로 GPT 응답을 실시간 출력"""
    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_message}],
        stream=True,
        max_tokens=1000,
    )

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()  # 줄바꿈

stream_response("Python 데코레이터를 쉽게 설명해 주세요.")
```

FastAPI와 연동할 때는 `StreamingResponse`를 활용합니다.

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import OpenAI

app = FastAPI()
client = OpenAI()

@app.post("/chat")
async def chat_stream(message: str):
    def generate():
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": message}],
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    return StreamingResponse(generate(), media_type="text/plain")
```

## 4단계: Function Calling으로 외부 도구 연동

Function Calling은 GPT가 외부 함수나 API를 호출할 시점을 스스로 판단하게 하는 기능입니다. 에이전트 시스템의 핵심입니다.

```python
import json
import requests

# 1. 도구 스키마 정의
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "특정 도시의 현재 날씨를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "조회할 도시 이름 (예: Seoul, Tokyo)"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "온도 단위"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# 2. 실제 함수 구현
def get_weather(city: str, unit: str = "celsius") -> dict:
    """날씨 API 호출 (예시)"""
    # 실제로는 OpenWeatherMap 같은 API 호출
    return {"city": city, "temperature": 22, "unit": unit, "condition": "맑음"}

# 3. Function Calling 흐름
def run_with_tools(user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]

    # 첫 번째 호출: GPT가 도구 사용 여부 결정
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # GPT가 자동으로 도구 선택
    )

    message = response.choices[0].message

    # 도구 호출이 필요한 경우
    if message.tool_calls:
        messages.append(message)  # GPT 응답 추가

        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            # 실제 함수 실행
            if func_name == "get_weather":
                result = get_weather(**func_args)

            # 도구 결과를 메시지에 추가
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })

        # 두 번째 호출: 도구 결과를 포함해 최종 응답 생성
        final_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        return final_response.choices[0].message.content

    return message.content

print(run_with_tools("서울 날씨 알려줘"))
```

## 5단계: 대화 히스토리 관리

멀티턴 대화를 구현하려면 이전 메시지를 `messages` 배열에 쌓아나가야 합니다.

```python
class ChatSession:
    def __init__(self, system_prompt: str = "당신은 친절한 AI 어시스턴트입니다."):
        self.messages = [{"role": "system", "content": system_prompt}]
        self.client = OpenAI()

    def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.messages,
            max_tokens=1000,
        )

        assistant_message = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": assistant_message})

        # 컨텍스트 관리: 최근 20개 메시지만 유지 (system 제외)
        if len(self.messages) > 21:
            self.messages = [self.messages[0]] + self.messages[-20:]

        return assistant_message

# 사용 예시
session = ChatSession("당신은 Python 전문가입니다.")
print(session.chat("리스트와 튜플의 차이는?"))
print(session.chat("그럼 어떤 상황에서 튜플을 써야 하나요?"))
```

컨텍스트 길이 관리는 비용과 직결됩니다. 무한정 히스토리를 쌓으면 토큰 비용이 기하급수적으로 늘어납니다. 최근 N개 메시지만 유지하거나, 오래된 대화를 요약해 압축하는 전략을 사용합니다.

## 비용 관리 — 가장 중요한 실전 팁

OpenAI API 비용은 입력 + 출력 토큰의 합산입니다. 실수로 무제한 요청이 발생하면 큰 비용이 청구될 수 있습니다.

### 1. Usage Limits 설정 (필수)

platform.openai.com → **Billing** → **Usage limits**에서 월 한도를 반드시 설정합니다. Hard limit을 넘으면 API가 자동 차단됩니다.

### 2. tiktoken으로 사전 토큰 계산

```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """텍스트의 토큰 수를 사전 계산"""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# 비용 예측
def estimate_cost(input_text: str, output_tokens: int = 500) -> float:
    input_tokens = count_tokens(input_text)
    # gpt-4o 기준: 입력 $2.50/1M, 출력 $10/1M
    input_cost = (input_tokens / 1_000_000) * 2.50
    output_cost = (output_tokens / 1_000_000) * 10.00
    return input_cost + output_cost

text = "Python 비동기 프로그래밍에 대해 자세히 설명해 주세요."
print(f"예상 비용: ${estimate_cost(text):.6f}")
```

### 3. 모델 계층화 전략

```python
MODEL_TIERS = {
    "simple": "gpt-4o-mini",    # 분류, 추출, 단순 요약
    "standard": "gpt-4o",       # 일반적인 생성, 번역
    "complex": "gpt-4o",        # 복잡한 추론, 코드 생성
}

def get_model(complexity: str) -> str:
    return MODEL_TIERS.get(complexity, "gpt-4o-mini")
```

단순 작업에 gpt-4o-mini를 쓰면 비용이 gpt-4o 대비 약 16분의 1로 줄어듭니다.

### 4. 응답 캐싱

동일한 입력에 대해 반복 호출하지 않도록 캐싱을 구현합니다.

```python
import hashlib
import json
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_completion(prompt: str, model: str = "gpt-4o-mini") -> str:
    """동일 프롬프트에 대한 API 호출 캐싱"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0,  # 캐싱 시 temperature=0으로 결정론적 출력
    )
    return response.choices[0].message.content
```

## 에러 핸들링

프로덕션 코드에서는 반드시 에러 처리를 구현해야 합니다.

```python
from openai import RateLimitError, APIError, APIConnectionError
import time

def safe_completion(messages: list, retries: int = 3) -> str | None:
    """재시도 로직을 포함한 안전한 API 호출"""
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1000,
            )
            return response.choices[0].message.content

        except RateLimitError:
            wait_time = 2 ** attempt  # 지수 백오프: 1s, 2s, 4s
            print(f"Rate limit 초과. {wait_time}초 후 재시도...")
            time.sleep(wait_time)

        except APIConnectionError:
            print("네트워크 연결 오류. 재시도 중...")
            time.sleep(1)

        except APIError as e:
            print(f"API 오류: {e.status_code} - {e.message}")
            break

    return None
```

## 마치며

OpenAI API는 처음에는 단순해 보이지만, 프로덕션 수준의 앱을 만들려면 스트리밍, Function Calling, 비용 관리, 에러 핸들링을 모두 다뤄야 합니다. 이 글에서 소개한 패턴들은 실제 서비스에서 검증한 코드이므로, 그대로 사용하셔도 좋습니다.

다음 단계로는 LangChain이나 LlamaIndex 같은 프레임워크를 활용해 더 복잡한 RAG 파이프라인을 구축하는 것을 권장합니다. API 기초를 탄탄히 익힌 후에 프레임워크를 배우면 훨씬 빠르게 이해할 수 있습니다.
