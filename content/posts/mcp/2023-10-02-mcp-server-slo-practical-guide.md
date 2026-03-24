---
title: "MCP 서버 SLO 실무 가이드: latency, availability, error budget을 어떻게 잡을까"
date: 2023-10-02T10:17:00+09:00
lastmod: 2023-10-03T10:17:00+09:00
description: "MCP 서버를 서비스처럼 운영하려면 latency, availability, error budget을 함께 정의해야 합니다. SLO를 지표와 알람, 배포 기준으로 연결하는 방법을 정리합니다."
slug: "mcp-server-slo-practical-guide"
categories: ["mcp"]
tags: ["MCP", "SLO", "Latency", "Availability", "Error Budget", "Observability", "AI 에이전트"]
series: ["AI Agent Tooling 2026"]
featureimage: "/images/mcp-server-slo-workflow-2026.svg"
draft: false
---

MCP 서버는 "도구만 붙이면 끝"처럼 보이기 쉽지만, 실제 서비스에서는 응답 시간과 실패율이 곧 사용자 경험입니다. SLO가 없으면 문제가 생겨도 어디까지가 정상인지, 언제 배포를 멈춰야 하는지 판단하기 어렵습니다.

이 글은 MCP 서버를 운영할 때 latency, availability, error budget을 어떻게 묶어야 하는지 정리합니다. [`MCP 서버 운영 실무 가이드`](/posts/mcp-server-operations-practical-guide/), [`MCP 서버 관측성 실무 가이드`](/posts/mcp-server-observability-practical-guide/), [`MCP 서버 인증 실무 가이드`](/posts/mcp-authentication-practical-guide/), [`Remote MCP 아키텍처 가이드`](/posts/remote-mcp-architecture-practical-guide/), [`AI Cost Dashboard 실무 가이드`](/posts/ai-cost-dashboard-practical-guide/)와 같이 읽으면 운영 기준이 더 선명해집니다.

## 개요

MCP 서버 SLO는 "정확히 동작한다"보다 "얼마나 빠르고 안정적으로 동작한다"를 먼저 정의하는 작업입니다. 에이전트는 tool call을 여러 번 반복하기 때문에 한 번의 느린 응답이 전체 체감 품질을 크게 떨어뜨립니다.

이 문서에서는 다음 세 가지를 기준으로 봅니다.

- 사용 가능한 응답 시간 목표
- 허용 가능한 실패율
- 장애 시 배포와 롤백 판단 기준

## 왜 중요한가

MCP 서버를 실무에 넣으면 다음 문제가 바로 드러납니다.

- 평균은 빠른데 p95, p99가 나쁘다
- 특정 도구만 자주 타임아웃된다
- 재시도 때문에 토큰과 비용이 급격히 늘어난다
- 실패가 증가해도 배포를 멈출 기준이 없다

SLO는 이 문제를 감정이 아니라 기준으로 바꾸는 장치입니다. 특히 에이전트 기반 시스템은 "실패를 감춘다"가 아니라 "실패를 측정한다"가 중요합니다.

## 운영 지표 설계

MCP 서버 SLO는 보통 아래처럼 잡는 것이 현실적입니다.

1. availability: 월간 99.5% 이상
2. tool success rate: 주요 tool 기준 99% 이상
3. latency: p95 1.5s 이하, p99 3s 이하
4. timeout rate: 전체 요청의 1% 이하
5. retry rate: 일정 임계치 이상이면 경보

지표는 하나만 보면 안 됩니다. 빠르지만 자주 실패하는 서버는 결국 느린 서버보다 더 나쁜 경험을 만듭니다.

`workflow` 도식은 SLO를 정의하고, 측정하고, 배포 기준으로 연결하는 흐름을 보여줍니다.

![MCP server SLO workflow](/images/mcp-server-slo-workflow-2026.svg)

`choice-flow` 도식은 latency, availability, error budget 중 무엇을 우선할지 판단하는 기준을 정리합니다.

![MCP server SLO choice flow](/images/mcp-server-slo-choice-flow-2026.svg)

`architecture` 도식은 agent, gateway, MCP server, downstream API를 어떻게 관측 가능한 구조로 나누는지 보여줍니다.

![MCP server SLO architecture](/images/mcp-server-slo-architecture-2026.svg)

## 아키텍처 도식

SLO 설계는 보통 아래 순서로 이어집니다.

1. agent 요청을 request id와 session id로 묶는다
2. gateway에서 tool call별 latency를 분리한다
3. MCP server에서 success, timeout, retry를 기록한다
4. downstream API까지 포함한 end-to-end latency를 계산한다
5. error budget이 소진되면 배포를 멈춘다

이 구조가 있으면 "느리다"가 아니라 "어디서 느린지"를 말할 수 있습니다.

## 체크리스트

- 주요 tool마다 p95, p99가 정의되어 있는가
- 실패율과 timeout rate를 별도로 보고 있는가
- retry가 비용 폭증으로 이어지지 않는가
- error budget 소진 기준이 정해져 있는가
- 장애 시 배포 중지 규칙이 문서화되어 있는가
- tracing과 audit log에서 같은 request를 추적할 수 있는가

## 결론

MCP 서버 SLO는 문서가 아니라 운영 기준입니다. latency, availability, error budget을 함께 정의해야 배포와 복구, 비용 통제가 연결됩니다. 지표가 있어야 문제를 고칠 수 있고, 기준이 있어야 운영을 멈출 수 있습니다.

## 함께 읽으면 좋은 글

- [`MCP 서버 운영 실무 가이드`](/posts/mcp-server-operations-practical-guide/)
- [`MCP 서버 관측성 실무 가이드`](/posts/mcp-server-observability-practical-guide/)
- [`MCP 서버 인증 실무 가이드`](/posts/mcp-authentication-practical-guide/)
- [`Remote MCP 아키텍처 가이드`](/posts/remote-mcp-architecture-practical-guide/)
- [`AI Cost Dashboard 실무 가이드`](/posts/ai-cost-dashboard-practical-guide/)

