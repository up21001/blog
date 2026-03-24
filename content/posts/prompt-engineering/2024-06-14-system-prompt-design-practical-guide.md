---
title: "System Prompt Design란 무엇인가: 시스템 프롬프트를 제품 수준으로 설계하는 법"
date: 2024-06-14T08:00:00+09:00
lastmod: 2024-06-19T08:00:00+09:00
description: "System Prompt Design의 구조, 우선순위, 안전장치, 운영 아키텍처를 한국어로 정리한 실무 가이드."
slug: "system-prompt-design-practical-guide"
categories: ["prompt-engineering"]
tags: ["System Prompt", "Prompt Design", "LLM Safety", "Prompt Governance", "AI Agent", "Structured Outputs"]
featureimage: "/images/system-prompt-design-workflow-2026.svg"
series: ["Prompt Operations 2026"]
draft: false
---

![System Prompt Design workflow](/images/system-prompt-design-workflow-2026.svg)

System Prompt Design은 모델에게 "무엇을 해야 하는지"만 알려주는 작업이 아닙니다. 실제로는 역할, 제약, 도구 사용 규칙, 실패 시 행동, 출력 형식을 함께 설계하는 일입니다.

이 글은 `Prompt Injection Defense`, `OpenAI Structured Outputs`, `GitHub Copilot Custom Instructions`, `Model Routing`과 연결해서 보면 좋습니다. 시스템 프롬프트는 고정 규칙이 아니라 제품 정책의 가장 앞단이기 때문입니다.

## 왜 중요한가

시스템 프롬프트가 느슨하면 모델은 매번 다른 방식으로 행동합니다. 반대로 너무 길면 우선순위가 흐려져 중요한 규칙이 묻힙니다.

- 역할과 금지 사항이 분리되어야 합니다.
- 도구 호출 조건이 명확해야 합니다.
- 출력 형식은 가능한 한 구조화되어야 합니다.
- 실패 시 fallback 행동이 정해져 있어야 합니다.

## 운영 방식

![System Prompt Design choice flow](/images/system-prompt-design-choice-flow-2026.svg)

실무에서는 시스템 프롬프트를 다음 순서로 설계합니다.

1. 역할과 목표를 한 문단으로 정의합니다.
2. 절대 규칙과 권장 규칙을 분리합니다.
3. 도구 호출 조건을 명시합니다.
4. 출력 스키마와 실패 응답을 정합니다.
5. 운영 중 수집한 실패 사례를 다시 반영합니다.

`OpenAI Structured Outputs`를 쓰면 시스템 프롬프트에서 출력 형식을 더 안정적으로 강제할 수 있습니다. `Model Routing`과 함께 쓰면 모델별로 다른 시스템 프롬프트도 운용할 수 있습니다.

## 아키텍처 도식

![System Prompt Design architecture](/images/system-prompt-design-architecture-2026.svg)

아키텍처는 `policy layer`, `task layer`, `tool layer`, `output layer`, `safety layer`로 나누는 것이 실용적입니다. 이 구조를 쓰면 시스템 프롬프트를 한 덩어리의 긴 텍스트가 아니라 운영 가능한 구성 요소로 다룰 수 있습니다.

## 체크리스트

- 역할과 금지 사항이 충돌 없이 정리되었는가
- 도구 호출 조건이 애매하지 않은가
- 출력 형식이 스키마로 고정되어 있는가
- 실패 시 대체 행동이 정의되어 있는가
- 보안 규칙이 사용자 입력보다 우선하는가

## 결론

System Prompt Design은 프롬프트를 잘 쓰는 문제가 아니라 모델 행동을 예측 가능하게 만드는 문제입니다. 구조, 우선순위, 출력 규칙, 안전장치가 함께 있어야 운영 가능한 시스템 프롬프트가 됩니다.

## 함께 읽으면 좋은 글

- [Prompt Injection Defense 실무 가이드](/posts/prompt-injection-defense-practical-guide/)
- [OpenAI Structured Outputs 실무 가이드](/posts/openai-structured-outputs-practical-guide/)
- [GitHub Copilot Custom Instructions란 무엇인가](/posts/github-copilot-custom-instructions-practical-guide/)
- [Model Routing 실무 가이드](/posts/model-routing-practical-guide/)
- [Prompt Ops란 무엇인가](/posts/prompt-ops-practical-guide/)
