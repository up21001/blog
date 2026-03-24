---
title: "MCP OAuth란 무엇인가: Remote MCP에서 사용자 동의와 토큰 위임을 설계하는 실무 가이드"
date: 2023-09-30T08:00:00+09:00
lastmod: 2023-10-04T08:00:00+09:00
description: "MCP OAuth를 어떻게 붙여야 하는지, 사용자 동의, 범위 제한, 토큰 위임, revocation을 실무 관점에서 정리합니다."
slug: "mcp-oauth-practical-guide"
categories: ["mcp"]
tags: ["MCP OAuth", "OAuth 2.1", "Remote MCP", "Model Context Protocol", "User Consent", "Token Delegation", "AI Agent Security"]
series: ["MCP Security 2026"]
featureimage: "/images/mcp-oauth-workflow-2026.svg"
draft: false
---

MCP OAuth는 Remote MCP를 사용자 계정과 연결하는 핵심 수단입니다. 로컬 환경에서는 간단해 보이지만, 여러 사용자가 같은 MCP 서버를 쓰는 순간 동의 화면, 범위 제한, 토큰 교체, 취소 흐름이 모두 중요해집니다.

![MCP OAuth 워크플로우](/images/mcp-oauth-workflow-2026.svg)

## 개요

MCP OAuth는 "로그인 버튼"이 아니라 "도구 위임 계약"에 가깝습니다. 사용자는 특정 범위의 데이터만 허용해야 하고, 에이전트는 그 범위를 벗어나는 도구를 호출할 수 없어야 합니다.

이 글은 [`OpenAI Remote MCP`](/posts/openai-remote-mcp-practical-guide/)와 [`Cloudflare Remote MCP Security`](/posts/cloudflare-remote-mcp-security-practical-guide/)를 함께 쓰는 시나리오를 기준으로 설명합니다.

## 왜 중요한가

OAuth가 빠지면 Remote MCP는 쉽게 "모두가 같은 서버를 쓰는 구조"가 됩니다. 그러면 다음 문제가 생깁니다.

1. 사용자별 데이터 분리가 어렵습니다.
2. 범위가 넓은 토큰이 재사용될 수 있습니다.
3. 감사 로그에서 누가 승인했는지 추적하기 어렵습니다.
4. revocation과 재동의 흐름이 꼬입니다.

MCP OAuth는 이런 문제를 막기 위한 최소 장치입니다.

## 인증/권한 설계

실무에서는 아래 순서로 설계하는 편이 좋습니다.

1. 사용자 인증: OAuth authorization code flow로 사용자 신원을 확인합니다.
2. 동의 범위: scopes를 좁게 정의합니다.
3. 토큰 위임: 에이전트에는 필요한 범위만 전달합니다.
4. 세션 교체: access token과 refresh token의 수명을 다르게 둡니다.
5. 취소 처리: revoke 시 tool access도 즉시 차단합니다.

[`AI Access Control`](/posts/ai-access-control-practical-guide/)과 [`Tool Permission Model`](/posts/tool-permission-model-practical-guide/)을 같이 보면 OAuth scope를 tool policy로 변환하는 방식이 더 명확해집니다.

## 아키텍처 도식

아래 도식은 OAuth의 승인 흐름, 선택 기준, 시스템 구조를 분리해서 보여줍니다.

![MCP OAuth 선택 기준](/images/mcp-oauth-choice-flow-2026.svg)

![MCP OAuth 아키텍처](/images/mcp-oauth-architecture-2026.svg)

보통은 다음 구조가 안정적입니다.

- 브라우저 또는 앱에서 동의 화면을 먼저 처리합니다.
- MCP 서버는 authorization server와 resource server 역할을 분리합니다.
- 에이전트는 access token을 직접 저장하지 않고 세션 토큰만 보관합니다.
- 위험한 tool은 추가 승인 단계로 넘깁니다.

## 체크리스트

- scopes가 최소 권한 원칙을 따르는가
- access token 수명이 짧은가
- refresh token이 안전하게 보관되는가
- revoke 시 세션과 tool 권한이 같이 취소되는가
- 사용자별 감사 로그가 남는가
- 승인 화면이 읽기 쉬운가
- 에이전트가 토큰 전체를 노출하지 않는가

## 결론

MCP OAuth는 Remote MCP를 실제 서비스로 올릴 때 빠질 수 없는 계층입니다. 범위를 좁게 자르고, 동의와 취소를 명확히 정의하면 사용자 신뢰와 운영 안정성이 같이 올라갑니다.

처음에는 단순한 authorization code + PKCE로 시작하고, 이후 세션 관리와 정책 엔진을 추가하는 방식이 가장 현실적입니다.

## 함께 읽으면 좋은 글

- [`OpenAI Remote MCP`](/posts/openai-remote-mcp-practical-guide/)
- [`Cloudflare Remote MCP Security`](/posts/cloudflare-remote-mcp-security-practical-guide/)
- [`MCP Authentication`](/posts/mcp-authentication-practical-guide/)
- [`Tool Permission Model`](/posts/tool-permission-model-practical-guide/)
- [`AI Access Control`](/posts/ai-access-control-practical-guide/)

