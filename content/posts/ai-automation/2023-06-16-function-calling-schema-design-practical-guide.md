---
title: "Function Calling Schema Design 실무 가이드: JSON 스키마를 잘 설계하는 법"
date: 2023-06-16T08:00:00+09:00
lastmod: 2023-06-20T08:00:00+09:00
description: "Function Calling에 들어가는 JSON 스키마를 안정적으로 설계하는 방법과, 실무에서 자주 깨지는 포인트를 정리한 가이드입니다."
slug: "function-calling-schema-design-practical-guide"
categories: ["ai-automation"]
tags: ["Function Calling", "JSON Schema", "Structured Outputs", "Tool Calling", "OpenAI API", "Anthropic Tool Use"]
featureimage: "/images/function-calling-schema-design-workflow-2026.svg"
series: ["AI Agent Tooling 2026"]
draft: true
---

Function Calling의 품질은 모델보다 스키마에서 먼저 결정됩니다. 입력 필드가 모호하면 모델은 자주 흔들리고, 느슨한 스키마는 결국 후처리 코드와 예외 처리만 늘립니다.

![Function Calling schema design workflow](/images/function-calling-schema-design-workflow-2026.svg)

## 왜 중요한가

스키마는 모델과 시스템 사이의 계약입니다. 계약이 선명해야 도구 호출이 예측 가능해지고, 호출 로그를 분석할 수 있고, 재시도 전략도 세울 수 있습니다.

실무에서는 `OpenAI Structured Outputs`와 같이 스키마를 강하게 거는 방식이 특히 유용합니다. [OpenAI Structured Outputs](/posts/2026-03-24-openai-structured-outputs-practical-guide/)와 [Anthropic Tool Use](/posts/2026-03-24-anthropic-tool-use-practical-guide/)를 같이 보면 “모델 출력 안정성”과 “도구 호출 안정성”이 어떻게 맞물리는지 보입니다.

## 설계 원칙

좋은 스키마는 사람이 읽기 쉽고, 모델이 채우기 쉽고, 서버가 검증하기 쉽습니다.

- 필드는 가능한 한 구체적으로 정의합니다.
- enum은 자유 텍스트보다 우선합니다.
- optional보다 required가 더 안전한 경우가 많습니다.
- 숫자 범위, 문자열 길이, 패턴을 제약합니다.
- 중첩 구조는 필요할 때만 씁니다.

```json
{
  "type": "object",
  "properties": {
    "query": { "type": "string", "minLength": 3 },
    "source": {
      "type": "string",
      "enum": ["docs", "db", "web"]
    },
    "top_k": { "type": "integer", "minimum": 1, "maximum": 10 }
  },
  "required": ["query", "source"]
}
```

## 실패 패턴

스키마는 넓게 만들수록 편해 보이지만 실제로는 더 위험합니다.

- `string` 하나로 모든 입력을 받으면 검증이 무너집니다.
- `anyOf`와 깊은 중첩은 모델 혼란을 키웁니다.
- nullable을 남발하면 후속 코드가 복잡해집니다.
- 이름이 비슷한 필드가 많으면 선택 정확도가 떨어집니다.

실무에서는 schema first보다 contract first로 보는 편이 맞습니다. 어떤 값을 받을지 먼저 정하고, 그 다음에 모델이 채우도록 설계해야 합니다.

## 빠른 시작

처음 설계할 때는 다음 기준이 유효합니다.

1. 사용자 입력을 한 문장으로 요약합니다.
2. 필수 필드만 먼저 정의합니다.
3. enum과 범위를 먼저 고정합니다.
4. 예외 값은 validation에서 막습니다.
5. 샘플 입력과 샘플 출력으로 테스트합니다.

`OpenAI Agents SDK`나 `MCP` 쪽 도구를 붙일 때도 같은 원칙이 적용됩니다. 구조가 보이면 재사용성이 올라갑니다.

## 결론

Function Calling 스키마는 AI 에이전트의 문법입니다. 문법이 헐거우면 시스템이 흔들리고, 문법이 명확하면 모델은 도구를 훨씬 안정적으로 사용할 수 있습니다.

![Function Calling schema design decision flow](/images/function-calling-schema-design-choice-flow-2026.svg)

## 함께 읽으면 좋은 글

- [OpenAI Structured Outputs 실무 가이드](/posts/2026-03-24-openai-structured-outputs-practical-guide/)
- [Anthropic Tool Use 실무 가이드](/posts/2026-03-24-anthropic-tool-use-practical-guide/)
- [OpenAI Responses API 실무 가이드](/posts/2026-03-23-openai-responses-api-practical-guide/)
- [OpenAI Remote MCP 실무 가이드](/posts/2026-03-24-openai-remote-mcp-practical-guide/)
