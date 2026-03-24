---
title: "Cloudflare MCPAgent란 무엇인가: Cloudflare Agents와 Remote MCP를 연결하는 실무 가이드"
date: 2022-12-20T10:17:00+09:00
lastmod: 2022-12-21T10:17:00+09:00
description: "Cloudflare Agents, Durable Objects, Remote MCP를 함께 묶어서 상태 저장형 AI 에이전트를 설계하는 방법을 실무 관점에서 정리합니다."
slug: "cloudflare-mcpagent-practical-guide"
categories: ["ai-agents"]
tags: ["Cloudflare Agents", "MCP", "Remote MCP", "Cloudflare MCPAgent", "Durable Objects", "Workers", "AI 에이전트", "Tool Calling"]
series: ["AI Agent Tooling 2026"]
featureimage: "/images/cloudflare-mcpagent-workflow-2026.svg"
draft: false
---

Cloudflare MCPAgent는 공식 제품명이라기보다, `Cloudflare Agents + Remote MCP + Durable Objects`를 묶어 생각할 때 유용한 실무 개념입니다. 핵심은 단순합니다. 에이전트의 상태는 Cloudflare에 두고, 외부 도구는 MCP 서버로 분리해서 연결하는 방식입니다.

이 접근은 채팅 UI 하나를 붙이는 수준보다 훨씬 실전적입니다. 사용자 세션, 작업 이력, 승인 상태, 도구 호출 로그가 한 덩어리로 움직여야 하기 때문입니다. 이 글에서는 Cloudflare 기반 에이전트 구조를 MCP와 연결하는 방법을 정리합니다.

## 개요

Cloudflare 쪽에서 에이전트를 설계할 때 중요한 점은 상태와 실행을 분리하는 것입니다.

- 상태는 Durable Objects에 둡니다.
- 계산과 라우팅은 Workers에서 처리합니다.
- 외부 도구는 Remote MCP로 분리합니다.
- 민감한 호출은 승인 흐름을 거칩니다.

이 구성을 쓰면, 단순한 함수 호출형 봇보다 오래 가는 작업과 복잡한 도구 체인을 다루기 쉬워집니다.

## 왜 주목받는가

Cloudflare MCPAgent가 주목받는 이유는 세 가지입니다.

1. 상태 저장형 에이전트를 엣지에서 운영할 수 있습니다.
2. MCP를 통해 외부 도구를 표준화된 방식으로 붙일 수 있습니다.
3. Durable Objects 덕분에 세션별 컨텍스트와 승인 기록을 일관되게 관리할 수 있습니다.

특히 `OpenAI Remote MCP`나 `FastMCP`처럼 MCP 서버 생태계가 커질수록, Cloudflare를 중간 실행 계층으로 두는 구성이 매력적입니다. 이미 [`Cloudflare Agents란 무엇인가: 2026년 상태 저장 AI 에이전트 실무 가이드`](/posts/cloudflare-agents-practical-guide/)와 [`OpenAI Remote MCP란 무엇인가: Responses API에서 외부 도구를 연결하는 실무 가이드`](/posts/openai-remote-mcp-practical-guide/)를 읽었다면 이어서 보기에 좋습니다.

## 빠른 시작

가장 단순한 시작은 다음 흐름입니다.

1. Cloudflare Workers에서 에이전트 요청을 받습니다.
2. Durable Objects로 세션 상태를 읽고 씁니다.
3. 필요하면 Remote MCP 서버를 호출합니다.
4. 도구 결과를 정리해서 사용자에게 반환합니다.

코드보다 먼저 해야 할 일은 도구 경계를 정하는 것입니다. 예를 들어 검색, 문서 조회, 티켓 생성, 승인 요청을 각각 다른 MCP 서버나 다른 도구 집합으로 분리하면 운영이 쉬워집니다.

## 설계 포인트

Cloudflare MCPAgent 설계에서 핵심은 “에이전트가 모든 것을 직접 하지 않게 만드는 것”입니다.

- 세션 상태는 Durable Objects에 고정합니다.
- 도구 목록은 allowlist 형태로 제한합니다.
- 장기 작업은 큐나 예약 실행으로 분리합니다.
- 출력은 사용자 메시지와 기계 판독용 로그를 분리합니다.
- 승인 필요한 도구는 별도 경로로 보냅니다.

이 구조는 [`FastMCP란 무엇인가: 2026년 Python MCP 서버 실무 가이드`](/posts/fastmcp-practical-guide/)와도 잘 맞습니다. FastMCP로 서버를 만들고, Cloudflare 쪽에서 실행 계층과 세션 상태를 담당하게 두면 역할이 깔끔하게 나뉩니다.

## 보안 체크리스트

Cloudflare 기반 MCPAgent는 편하지만, 도구가 늘어날수록 보안 설계가 중요해집니다.

- 외부 MCP 서버는 신뢰 가능한 도메인만 허용합니다.
- 인증과 승인 상태를 세션별로 기록합니다.
- 민감한 도구는 `require_approval` 같은 수동 승인 흐름을 둡니다.
- 토큰과 API 키는 클라이언트에 직접 노출하지 않습니다.
- 실행 로그에서 입력과 출력 범위를 분리해 저장합니다.
- 프롬프트 인젝션 가능성을 전제로 도구 결과를 검증합니다.

특히 Remote MCP를 붙일 때는 “무슨 도구를 쓸 수 있나”보다 “무슨 도구를 절대 못 쓰게 할 것인가”를 먼저 정해야 합니다. 이 관점은 [`Cloudflare Remote MCP 보안 가이드: 승인, 도구 제한, 네트워크 경계 설계`](/posts/cloudflare-remote-mcp-security-practical-guide/)에서 더 자세히 다룹니다.

## 결론

Cloudflare MCPAgent는 상태 저장형 AI 에이전트를 운영 가능한 구조로 끌어올리는 실무 패턴입니다. Durable Objects로 상태를 고정하고, Workers로 흐름을 제어하고, MCP로 외부 도구를 표준화하면 복잡한 에이전트도 관리 가능한 단위로 쪼갤 수 있습니다.

처음부터 거대한 에이전트를 만들기보다, 하나의 세션과 하나의 도구 체인부터 시작하는 편이 좋습니다. 그 다음 승인, 로깅, 관측성, 멀티 도구 라우팅 순서로 확장하면 됩니다.

## 함께 읽으면 좋은 글

- [`Cloudflare Agents란 무엇인가: 2026년 상태 저장 AI 에이전트 실무 가이드`](/posts/cloudflare-agents-practical-guide/)
- [`OpenAI Remote MCP란 무엇인가: Responses API에서 외부 도구를 연결하는 실무 가이드`](/posts/openai-remote-mcp-practical-guide/)
- [`FastMCP란 무엇인가: 2026년 Python MCP 서버 실무 가이드`](/posts/fastmcp-practical-guide/)
- [`MCP 서버란 무엇인가: 2026 AI 에이전트 도구 연결 실무 가이드`](/posts/mcp-server-practical-guide-2026/)
