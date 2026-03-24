---
title: "AI 안전 가드레일 실무 가이드: LLM 정책, 검증, 차단을 한 번에 설계하는 법"
date: 2022-09-21T08:00:00+09:00
lastmod: 2022-09-26T08:00:00+09:00
description: "AI 안전 가드레일을 처음 설계할 때 필요한 정책, 검증, 차단 흐름을 실무 관점에서 정리한 가이드입니다. Guardrails AI, NeMo Guardrails, OpenAI Agents SDK와 함께 어떻게 조합할지 설명합니다."
slug: "ai-safety-guardrails-practical-guide"
categories: ["ai-automation"]
tags: ["AI Safety", "Guardrails", "LLM Policy", "Validation", "Safety Checks", "Agent Safety"]
featureimage: "/images/ai-safety-guardrails-workflow-2026.svg"
draft: true
---

![AI 안전 가드레일 실무 가이드](/images/ai-safety-guardrails-workflow-2026.svg)

LLM을 실제 서비스에 넣으면 가장 먼저 부딪히는 문제는 성능이 아니라 안전입니다. 잘못된 답변, 정책 위반, 민감 정보 노출, 도구 오남용은 한 번만 터져도 제품 신뢰를 크게 깎습니다. 그래서 가드레일은 선택 기능이 아니라 기본 인프라에 가깝습니다.

이 글은 AI 안전 가드레일을 어떻게 나눠 설계해야 하는지, 어디서 검증하고 어디서 차단해야 하는지, 그리고 어떤 도구를 붙이면 좋은지 실무 기준으로 정리합니다. 이미 [Guardrails AI](/posts/guardrails-ai-practical-guide/), [NeMo Guardrails](/posts/nemo-guardrails-practical-guide/), [OpenAI Agents SDK](/posts/openai-agents-sdk-practical-guide/)를 보고 있다면, 이 글은 그 사이를 연결하는 설계도 역할을 합니다.

## 왜 중요한가

가드레일이 필요한 이유는 단순합니다. LLM은 그럴듯하게 잘못 말할 수 있고, 도구가 붙으면 잘못된 말이 바로 실행으로 이어질 수 있기 때문입니다.

- 정책 위반 응답이 사용자에게 그대로 노출된다
- 민감 정보가 로그, 프롬프트, 외부 도구로 새어 나간다
- 에이전트가 허용되지 않은 도구를 호출한다
- 모델이 환각한 내용을 사실처럼 전달한다

이 문제는 모델만 바꾼다고 해결되지 않습니다. 입력, 중간 상태, 출력, 도구 호출 각각에서 별도의 방어층이 필요합니다.

## 문제 구조

실무에서는 보통 아래 4단계로 분해합니다.

1. 입력 검증: 사용자의 요청이 정책 위반인지 먼저 본다
2. 컨텍스트 정리: 민감 정보, 불필요한 데이터, 악성 지시를 제거한다
3. 출력 검증: 응답이 형식, 정책, 금지어 기준을 통과하는지 확인한다
4. 실행 차단: 도구 호출, 결제, 삭제 같은 고위험 작업을 별도로 승인한다

여기서 핵심은 "모델이 알아서 판단하겠지"를 버리는 것입니다. 정책은 모델 프롬프트보다 코드와 규칙으로 먼저 강제해야 합니다.

## 실무 대응 방법

가장 단순한 설계는 다음처럼 구성합니다.

- 라우터: 요청 유형 분류
- 정책 엔진: 허용/차단 규칙
- 검증기: JSON, 길이, 금지 항목 확인
- 도구 게이트: 위험한 액션 전 승인
- 감사 로그: 누가, 언제, 무엇을 요청했는지 기록

이 구조는 [NeMo Guardrails](/posts/nemo-guardrails-practical-guide/)의 rails/config 개념과 잘 맞고, [Guardrails AI](/posts/guardrails-ai-practical-guide/)의 validator/check 개념과도 잘 맞습니다. 에이전트 레벨에서는 [OpenAI Agents SDK](/posts/openai-agents-sdk-practical-guide/)나 [Anthropic Tool Use](/posts/anthropic-tool-use-practical-guide/) 앞단에 붙이는 방식이 실용적입니다.

## 체크리스트

- 정책 위반을 모델 프롬프트가 아니라 코드로 막고 있는가
- 입력과 출력 모두 검증하는가
- 도구 호출 전에 별도 승인 단계가 있는가
- 민감 정보 마스킹이 로그와 컨텍스트 양쪽에 있는가
- 차단 사유가 관측 가능하게 남는가
- 실패 시 안전한 기본값으로 떨어지는가

이 체크리스트가 없으면 안전 장치는 대부분 문서에만 있고 운영에는 없습니다.

## 결론

AI 안전 가드레일은 모델 성능 문제가 아니라 시스템 설계 문제입니다. 입력, 출력, 도구 호출을 분리해서 다루면 안전성과 디버깅 가능성이 함께 올라갑니다. 처음부터 복잡하게 만들 필요는 없지만, 최소한 정책 검증과 실행 차단은 분리해 두는 편이 좋습니다.

## 함께 읽으면 좋은 글

- [Guardrails AI 실무 가이드](/posts/guardrails-ai-practical-guide/)
- [NeMo Guardrails 실무 가이드](/posts/nemo-guardrails-practical-guide/)
- [OpenAI Agents SDK 실무 가이드](/posts/openai-agents-sdk-practical-guide/)
- [Anthropic Tool Use 실무 가이드](/posts/anthropic-tool-use-practical-guide/)
