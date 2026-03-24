---
title: "Tool Permission Model란 무엇인가: AI 에이전트 도구 권한을 최소 권한으로 설계하는 실무 가이드"
date: 2024-07-02T08:00:00+09:00
lastmod: 2024-07-04T08:00:00+09:00
description: "AI 에이전트가 도구를 호출할 때 권한을 역할, 상황, 정책 기준으로 나누는 Tool Permission Model 설계 방법을 정리합니다."
slug: "tool-permission-model-practical-guide"
categories: ["ai-automation"]
tags: ["Tool Permission Model", "Least Privilege", "AI Agent", "Tool Policy", "Access Control", "Security"]
featureimage: "/images/tool-permission-model-workflow-2026.svg"
draft: false
---

![Tool Permission Model](/images/tool-permission-model-workflow-2026.svg)

Tool Permission Model은 AI 에이전트가 어떤 도구를 언제, 어떤 범위까지 쓸 수 있는지 정하는 규칙입니다. 핵심은 단순 허용이 아니라, 역할과 상황에 맞게 권한을 줄이는 데 있습니다.

이 글은 [AI Access Control](/posts/ai-access-control-practical-guide/), [Enterprise AI Governance](/posts/enterprise-ai-governance-practical-guide/), [Tool Calling](/posts/tool-calling-practical-guide/)과 같이 보면 구조가 더 빨리 잡힙니다.

## 개요

도구 권한을 느슨하게 두면 에이전트는 편해지지만, 실수 하나가 곧 데이터 유출이나 잘못된 변경으로 이어집니다. 반대로 너무 엄격하면 에이전트가 일을 못 합니다.

Tool Permission Model은 그 중간점을 찾는 설계입니다. 읽기 전용 도구, 변경 도구, 외부 전송 도구를 분리하고, 민감도에 따라 승인 단계를 다르게 둡니다.

## 왜 중요한가

AI 에이전트는 사용자의 의도를 잘못 해석할 수 있습니다. 그래서 도구 권한은 "가능한가"보다 "허용해야 하는가"를 먼저 봐야 합니다.

- 조회와 변경을 분리할 수 있습니다.
- 민감한 작업은 추가 확인을 거칠 수 있습니다.
- 도구별 로그를 남겨 사후 분석이 쉬워집니다.

## 권한 설계

권한 설계는 보통 세 단계로 나눕니다.

1. `role` 기준으로 기본 권한을 나눕니다.
2. `context` 기준으로 요청 상황을 평가합니다.
3. `policy` 기준으로 허용, 차단, 승인 필요를 결정합니다.

예를 들어 검색 도구는 넓게 허용하되, 결제나 삭제 도구는 별도 승인으로 분리하는 방식이 좋습니다.

## 아키텍처 도식

![Tool Permission Model Choice Flow](/images/tool-permission-model-choice-flow-2026.svg)

![Tool Permission Model Architecture](/images/tool-permission-model-architecture-2026.svg)

도구 호출 직전에 정책 엔진이 한 번 더 개입해야 합니다. 이 단계가 없으면 프롬프트 수준의 요청이 곧바로 실행됩니다.

## 체크리스트

- 읽기와 쓰기 도구를 분리했는가
- 민감 작업은 승인 단계가 있는가
- 도구별 로그와 사용자 식별자가 남는가
- 기본 허용이 아니라 기본 거부에 가깝게 설계했는가
- 외부 전송 도구는 화이트리스트로 제한했는가

## 결론

Tool Permission Model은 에이전트가 강해질수록 더 중요해집니다. 권한을 명확히 나누면, 에이전트는 필요한 일만 하고 사고 가능성은 낮아집니다.

## 함께 읽으면 좋은 글

- [AI Access Control](/posts/ai-access-control-practical-guide/)
- [Enterprise AI Governance](/posts/enterprise-ai-governance-practical-guide/)
- [Tool Calling](/posts/tool-calling-practical-guide/)
- [Prompt Injection Defense](/posts/prompt-injection-defense-practical-guide/)

