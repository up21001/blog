---
title: "MCP Multi-Tenant란 무엇인가: 조직별 서버 분리와 데이터 경계를 지키는 실무 가이드"
date: 2023-09-29T08:00:00+09:00
lastmod: 2023-10-01T08:00:00+09:00
description: "MCP Multi-Tenant를 어떻게 설계해야 하는지, 조직별 경계, 데이터 분리, 권한 정책, 감사 로그를 실무 관점에서 정리합니다."
slug: "mcp-multi-tenant-practical-guide"
categories: ["mcp"]
tags: ["MCP Multi-Tenant", "Tenant Isolation", "Remote MCP", "MCP Security", "AI Access Control", "Tool Calling", "Durable Objects"]
series: ["MCP Security 2026"]
featureimage: "/images/mcp-multi-tenant-workflow-2026.svg"
draft: true
---

MCP Multi-Tenant는 여러 조직이 같은 MCP 기반 서비스를 쓰더라도 데이터와 권한 경계를 유지하는 설계입니다. 에이전트가 강력해질수록 tenant isolation은 선택이 아니라 기본값이 되어야 합니다.

![MCP Multi-Tenant 워크플로우](/images/mcp-multi-tenant-workflow-2026.svg)

## 개요

멀티테넌트 MCP 구조는 단순히 사용자 ID를 붙이는 것만으로 끝나지 않습니다. 서버 경계, 데이터 저장소 경계, tool 정책, 로그 경계를 함께 나눠야 합니다.

이 글은 [`Cloudflare MCPAgent`](/posts/cloudflare-mcpagent-practical-guide/)와 [`Remote MCP Architecture`](/posts/remote-mcp-architecture-practical-guide/)를 기준으로 설명합니다. 인증과 OAuth는 각각 [`MCP Authentication`](/posts/mcp-authentication-practical-guide/)과 [`MCP OAuth`](/posts/mcp-oauth-practical-guide/)를 함께 보면 좋습니다.

## 왜 중요한가

멀티테넌트 경계가 무너지면 다음 문제가 생깁니다.

1. 한 tenant의 tool이 다른 tenant의 데이터를 보게 됩니다.
2. 감사 로그가 섞여 원인 추적이 어려워집니다.
3. rate limit과 비용 정산이 꼬입니다.
4. 긴급 차단이나 권한 회수 시 영향 범위를 제어하기 어렵습니다.

AI 에이전트는 기존 SaaS보다 호출 빈도와 권한 이동이 더 동적이기 때문에, 경계가 더 엄격해야 합니다.

## 인증/권한 설계

멀티테넌트 MCP는 보통 아래 3개의 경계를 둡니다.

1. Identity boundary: 사용자가 누구인지 식별합니다.
2. Tenant boundary: 어떤 조직에 속하는지 구분합니다.
3. Tool boundary: 어떤 MCP tool을 사용할 수 있는지 제한합니다.

[`Tool Permission Model`](/posts/tool-permission-model-practical-guide/)과 [`AI Access Control`](/posts/ai-access-control-practical-guide/)를 붙이면 tenant별 정책을 tool 수준으로 내릴 수 있습니다.

## 아키텍처 도식

아래 도식은 멀티테넌트 운영 흐름, 선택 기준, 구조 분리를 함께 보여줍니다.

![MCP Multi-Tenant 선택 기준](/images/mcp-multi-tenant-choice-flow-2026.svg)

![MCP Multi-Tenant 아키텍처](/images/mcp-multi-tenant-architecture-2026.svg)

실무에서는 다음 중 하나를 선택합니다.

- Tenant별 MCP 서버 분리: 보안은 강하지만 운영 비용이 높습니다.
- Shared server + tenant namespace: 비용 효율이 좋고, 정책 엔진이 중요합니다.
- Hybrid: 핵심 계정은 분리하고 나머지는 공유합니다.

Cloudflare의 경우 Durable Objects처럼 상태를 tenant 단위로 묶는 방식이 특히 잘 맞습니다. [`Cloudflare Remote MCP Security`](/posts/cloudflare-remote-mcp-security-practical-guide/)와 같이 보면 경계 설정이 더 선명해집니다.

## 체크리스트

- tenant ID가 요청 전파 체인에 항상 포함되는가
- 저장소 네임스페이스가 tenant별로 나뉘는가
- tool allowlist가 tenant별로 다른가
- 감사 로그가 tenant 기준으로 검색 가능한가
- rate limit과 quota가 tenant별로 분리되는가
- 운영자 권한이 tenant 데이터에 직접 닿지 않는가
- 긴급 차단 시 특정 tenant만 빠르게 비활성화 가능한가

## 결론

MCP Multi-Tenant는 에이전트 서비스를 기업 환경으로 가져갈 때 가장 먼저 고민해야 할 구조입니다. tenant 경계를 인증, 정책, 저장소, 로그에 모두 반영해야 실무에서 사고를 줄일 수 있습니다.

작게는 shared server + namespace로 시작하고, 민감한 조직부터 전용 서버로 분리하는 방식이 현실적입니다.

## 함께 읽으면 좋은 글

- [`Cloudflare MCPAgent`](/posts/cloudflare-mcpagent-practical-guide/)
- [`Remote MCP Architecture`](/posts/remote-mcp-architecture-practical-guide/)
- [`MCP Authentication`](/posts/mcp-authentication-practical-guide/)
- [`MCP OAuth`](/posts/mcp-oauth-practical-guide/)
- [`AI Access Control`](/posts/ai-access-control-practical-guide/)

