---
title: "AI 감사 로그란 무엇인가: 에이전트 행동을 추적하고 재현하는 실무 가이드"
date: 2022-08-27T08:00:00+09:00
lastmod: 2022-09-02T08:00:00+09:00
description: "AI 에이전트의 입력, 툴 호출, 정책 판단, 출력 결과를 감사 가능한 형태로 남기는 방법을 정리한 실무 가이드."
slug: "ai-audit-log-practical-guide"
categories: ["ai-automation"]
tags: ["Audit Log", "Tracing", "Observability", "Compliance", "Agent Debugging", "AI Governance"]
featureimage: "/images/ai-audit-log-workflow-2026.svg"
draft: false
---

![AI Audit Log](/images/ai-audit-log-workflow-2026.svg)

AI 감사 로그는 나중에 문제를 설명하기 위한 장치입니다. 단순한 access log와 다르게, 누가 어떤 세션에서 어떤 정책으로 어떤 툴을 썼는지까지 남겨야 합니다.

이 글은 [AI 트레이싱 실무 가이드](/posts/ai-tracing-practical-guide/), [LLM 관측성 실무 가이드](/posts/llm-observability-practical-guide/), [Agent Debugging 실무 가이드](/posts/agent-debugging-practical-guide/)를 감사 관점으로 다시 묶어 설명합니다.

## 개요

감사 로그는 보안용이면서 운영용입니다. 장애가 나도 원인을 좁히고, 정책 위반이 나도 누가 왜 실행했는지 설명할 수 있어야 합니다.

실무에서는 요청 단위, 세션 단위, 툴 호출 단위로 나눠 기록하는 편이 좋습니다. 그래야 추적과 집계가 둘 다 됩니다.

## 왜 중요한가

AI 시스템은 사람이 매번 직접 누른 것보다 더 많은 결정을 자동으로 만듭니다. 기록이 없으면 재현도 어렵고 책임도 अस्प명해집니다.

감사 로그가 있으면 정책 위반, 프롬프트 인젝션, 잘못된 툴 실행, 모델 이상 응답을 빠르게 분리할 수 있습니다. 운영팀과 보안팀이 같은 데이터를 보고 이야기할 수 있다는 점도 큽니다.

## 운영 구조

감사 로그는 다음 순서가 좋습니다.

1. 요청 식별자와 세션 식별자를 부여합니다.
2. 정책 검사 결과와 승인 결과를 기록합니다.
3. 모델 입력과 출력의 요약을 남깁니다.
4. 툴 호출과 외부 전송 이력을 연결합니다.
5. 민감 데이터는 마스킹하거나 해시 처리합니다.

이 구조는 [OpenAI Evals](/posts/openai-evals-practical-guide/), [OpenAI Agent Evals](/posts/openai-agent-evals-practical-guide/), [Agent Session Management](/posts/agent-session-management-practical-guide/)와도 잘 맞습니다.

## 아키텍처 도식

![Audit Log Workflow](/images/ai-audit-log-workflow-2026.svg)

![Audit Log Choice Flow](/images/ai-audit-log-choice-flow-2026.svg)

![Audit Log Architecture](/images/ai-audit-log-architecture-2026.svg)

감사 로그는 저장만 하면 끝이 아닙니다. 검색, 필터링, 보관 정책, 마스킹 규칙까지 같이 설계해야 실제 운영에서 쓸 수 있습니다.

## 체크리스트

- 요청, 세션, 사용자 식별자가 모두 남는가
- 정책 판단과 승인 이력이 보존되는가
- 툴 호출 전후 상태를 구분할 수 있는가
- 민감 정보가 마스킹되는가
- 장애 분석에 쓸 만큼 충분히 구조화되어 있는가

## 결론

AI 감사 로그는 규정 준수를 위한 장식이 아니라, 에이전트 운영의 안전망입니다. 기록이 있어야 통제할 수 있고, 통제할 수 있어야 확장할 수 있습니다.

## 함께 읽으면 좋은 글

- [AI 트레이싱 실무 가이드](/posts/ai-tracing-practical-guide/)
- [LLM 관측성 실무 가이드](/posts/llm-observability-practical-guide/)
- [Agent Debugging 실무 가이드](/posts/agent-debugging-practical-guide/)
- [OpenAI Agent Evals 실무 가이드](/posts/openai-agent-evals-practical-guide/)
