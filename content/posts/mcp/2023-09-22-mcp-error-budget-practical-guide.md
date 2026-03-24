---
title: "MCP error budget 실무 가이드: 실패 허용치를 운영 기준으로 바꾸는 법"
date: 2023-09-22T10:17:00+09:00
lastmod: 2023-09-28T10:17:00+09:00
description: "MCP 서버의 실패 허용치를 어떻게 계산하고, 배포 중지와 복구 우선순위에 연결할지 error budget 관점에서 정리합니다."
slug: "mcp-error-budget-practical-guide"
categories: ["mcp"]
tags: ["MCP", "Error Budget", "Reliability", "SLO", "AI 에이전트", "Incident Response"]
series: ["AI Agent Tooling 2026"]
featureimage: "/images/mcp-error-budget-workflow-2026.svg"
draft: false
---

MCP error budget은 "실패가 없어야 한다"는 막연한 기대를 운영 가능한 규칙으로 바꾸는 장치입니다. 실제 서비스에서는 100% 가용성을 목표로 하기보다, 얼마만큼 실패를 허용하고 그 초과분을 어떻게 다룰지 정해야 합니다.

이 글은 [`MCP 서버 운영 실무 가이드`](/posts/mcp-server-operations-practical-guide/), [`MCP 서버 관측성 실무 가이드`](/posts/mcp-server-observability-practical-guide/), [`MCP 서버 인증 실무 가이드`](/posts/mcp-authentication-practical-guide/), [`AI Cost Dashboard 실무 가이드`](/posts/ai-cost-dashboard-practical-guide/)와 함께 보면 좋습니다.

## 개요

Error budget은 허용 가능한 실패량입니다. 가령 월간 99.5% availability 목표라면, 남은 0.5%가 error budget이 됩니다. 중요한 것은 이 수치를 알람이 아니라 운영 정책으로 쓰는 것입니다.

이 예산은 다음 질문에 답하게 해줍니다.

- 언제 배포를 멈출 것인가
- 언제 롤백할 것인가
- 언제 기능 개발보다 안정화가 우선인가

## 왜 중요한가

에이전트 시스템은 실패를 숨기기 쉽습니다. 재시도, fallback, 다른 tool 호출이 실패를 감춰버리면 겉보기에는 동작하는 것처럼 보일 수 있습니다.

하지만 실제로는 다음 문제가 생깁니다.

- 실패가 누적되어 비용이 올라간다
- 실패가 사용성 저하로 이어진다
- 장애가 배포와 무관하게 반복된다
- 운영팀이 어디까지 허용해야 하는지 모른다

## 운영 지표 설계

Error budget은 단순히 실패율이 아니라 운영 기준입니다. 실무에서는 아래처럼 나누는 편이 좋습니다.

1. request failure budget
2. tool execution failure budget
3. timeout failure budget
4. retry failure budget
5. downstream dependency budget

`workflow` 도식은 예산을 계산하고, 초과 여부를 판단하고, 운영 액션으로 연결하는 흐름을 보여줍니다.

![MCP error budget workflow](/images/mcp-error-budget-workflow-2026.svg)

`choice-flow` 도식은 장애가 생겼을 때 배포 중지, 롤백, 축소 운영 중 무엇을 선택할지 정리합니다.

![MCP error budget choice flow](/images/mcp-error-budget-choice-flow-2026.svg)

`architecture` 도식은 error budget을 tracing, dashboard, alert, incident response로 연결하는 구조를 보여줍니다.

![MCP error budget architecture](/images/mcp-error-budget-architecture-2026.svg)

## 아키텍처 도식

Error budget은 보통 아래처럼 운영합니다.

1. request, tool, retry 단위로 실패를 분리한다
2. 월간 또는 주간 예산을 정한다
3. 예산 소진률을 dashboard에 띄운다
4. 소진 임계치에서 배포를 멈춘다
5. incident 이후에는 원인별로 budget을 재분배한다

이렇게 해야 실패가 "알람"이 아니라 "운영 규칙"이 됩니다.

## 체크리스트

- failure를 request, tool, retry로 분리했는가
- budget 소진 시 배포 중지 규칙이 있는가
- incident 후 budget 재분배 절차가 있는가
- alert가 noisy하지 않은가
- retry가 budget을 은근히 소모하지 않는가
- tracing과 audit log로 실패 원인을 추적할 수 있는가

## 결론

Error budget은 실패를 허용하는 대신, 허용 범위를 넘었을 때 무엇을 할지 정하는 규칙입니다. MCP 서버처럼 외부 의존성이 많은 시스템에서는 이 규칙이 없으면 배포와 복구가 감으로 흐릅니다.

## 함께 읽으면 좋은 글

- [`MCP 서버 운영 실무 가이드`](/posts/mcp-server-operations-practical-guide/)
- [`MCP 서버 관측성 실무 가이드`](/posts/mcp-server-observability-practical-guide/)
- [`MCP 서버 인증 실무 가이드`](/posts/mcp-authentication-practical-guide/)
- [`Remote MCP 아키텍처 가이드`](/posts/remote-mcp-architecture-practical-guide/)
- [`AI Cost Dashboard 실무 가이드`](/posts/ai-cost-dashboard-practical-guide/)

