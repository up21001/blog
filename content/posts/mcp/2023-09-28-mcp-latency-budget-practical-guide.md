---
title: "MCP latency budget 실무 가이드: 응답 속도 목표를 설계하는 방법"
date: 2023-09-28T08:00:00+09:00
lastmod: 2023-10-01T08:00:00+09:00
description: "Agent, gateway, tool server, downstream API로 나뉘는 MCP 지연 시간을 분해하고 latency budget을 운영 지표로 바꾸는 방법을 정리합니다."
slug: "mcp-latency-budget-practical-guide"
categories: ["mcp"]
tags: ["MCP", "Latency Budget", "Performance", "SLO", "AI 에이전트", "Observability"]
series: ["AI Agent Tooling 2026"]
featureimage: "/images/mcp-latency-budget-workflow-2026.svg"
draft: false
---

MCP latency budget은 "응답이 빠르다"를 정성적으로 말하지 않고, 각 구간별 예산을 수치로 나누는 방식입니다. 이 예산이 없으면 느림의 원인을 agent, network, tool server, downstream 중 어디에 둘지 결정하기 어렵습니다.

이 글은 [`MCP 서버 운영 실무 가이드`](/posts/mcp-server-operations-practical-guide/), [`MCP 서버 관측성 실무 가이드`](/posts/mcp-server-observability-practical-guide/), [`Remote MCP 아키텍처 가이드`](/posts/remote-mcp-architecture-practical-guide/), [`AI Cost Dashboard 실무 가이드`](/posts/ai-cost-dashboard-practical-guide/)와 연결해서 읽는 것을 전제로 합니다.

## 개요

Latency budget은 전체 응답 목표를 여러 구간으로 쪼개는 일입니다. 예를 들어 2초 목표가 있다면 agent planning 300ms, network 200ms, tool execution 900ms, downstream API 600ms처럼 나눌 수 있습니다.

이렇게 나누면 아래 문제가 줄어듭니다.

- 어디서 최적화해야 하는지 명확해진다
- 느려졌을 때 책임 구간이 선명해진다
- 배포 전후 성능 비교가 쉬워진다

## 왜 중요한가

MCP는 여러 번의 tool call을 포함하기 쉽습니다. 한 번의 작은 지연이 누적되어 전체 체감 속도를 망칠 수 있습니다. 평균 latency만 보면 놓치는 문제도 많습니다.

- p95는 괜찮은데 p99가 급증한다
- 특정 tool만 네트워크 왕복이 길다
- 재시도 때문에 사용자가 더 오래 기다린다
- 모델 응답은 빠른데 tool I/O가 느리다

## 운영 지표 설계

Latency budget은 다음처럼 계층화하는 것이 실무적입니다.

1. agent planning budget
2. gateway routing budget
3. MCP server execution budget
4. downstream API budget
5. retry budget

지표는 평균보다 분포를 봐야 합니다.

- p50: 평상시 속도
- p95: 대부분의 체감 속도
- p99: 장애성 지연

`workflow` 도식은 budget이 어떻게 쪼개지는지 보여줍니다.

![MCP latency budget workflow](/images/mcp-latency-budget-workflow-2026.svg)

`choice-flow` 도식은 budget을 어디에 먼저 배분할지 결정하는 흐름을 보여줍니다.

![MCP latency budget choice flow](/images/mcp-latency-budget-choice-flow-2026.svg)

`architecture` 도식은 각 구간의 latency를 어떻게 수집하고 대시보드로 모을지 보여줍니다.

![MCP latency budget architecture](/images/mcp-latency-budget-architecture-2026.svg)

## 아키텍처 도식

Latency budget은 보통 아래 순서로 설계합니다.

1. user request에 request id를 부여한다
2. gateway에서 route별 latency를 기록한다
3. MCP server에서 tool별 실행 시간을 기록한다
4. downstream API 응답 시간을 따로 분리한다
5. 최종 end-to-end latency를 계산한다

이후 지연이 길어지는 구간부터 먼저 최적화합니다.

## 체크리스트

- p50, p95, p99가 각각 기록되는가
- tool call별 latency가 분리되는가
- retry가 latency 예산을 침범하지 않는가
- timeout 설정이 budget과 일치하는가
- batch 요청과 실시간 요청이 분리되는가
- dashboard에서 구간별 병목을 바로 볼 수 있는가

## 결론

Latency budget은 속도 최적화가 아니라 우선순위 설정입니다. 예산을 나눠야 병목을 찾을 수 있고, 병목을 찾아야 최적화가 가능합니다. MCP처럼 여러 계층이 있는 시스템에서는 이 방식이 가장 실용적입니다.

## 함께 읽으면 좋은 글

- [`MCP 서버 운영 실무 가이드`](/posts/mcp-server-operations-practical-guide/)
- [`MCP 서버 관측성 실무 가이드`](/posts/mcp-server-observability-practical-guide/)
- [`MCP 서버 인증 실무 가이드`](/posts/mcp-authentication-practical-guide/)
- [`Remote MCP 아키텍처 가이드`](/posts/remote-mcp-architecture-practical-guide/)
- [`AI Cost Dashboard 실무 가이드`](/posts/ai-cost-dashboard-practical-guide/)

