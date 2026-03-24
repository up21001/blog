---
title: "Agent Sandboxing란 무엇인가: AI 에이전트 실행 환경을 격리하는 실무 가이드"
date: 2022-07-07T08:00:00+09:00
lastmod: 2022-07-09T08:00:00+09:00
description: "AI 에이전트를 안전하게 실행하기 위해 파일, 네트워크, 프로세스 범위를 격리하는 Agent Sandboxing 설계 방법을 정리합니다."
slug: "agent-sandboxing-practical-guide"
categories: ["ai-agents"]
tags: ["Agent Sandboxing", "Isolation", "AI Agent", "Container", "Security", "MCP Security"]
featureimage: "/images/agent-sandboxing-workflow-2026.svg"
draft: true
---

![Agent Sandboxing](/images/agent-sandboxing-workflow-2026.svg)

Agent Sandboxing은 에이전트가 실행되는 환경을 제한해서, 오류와 악성 입력의 피해 범위를 줄이는 방법입니다. 파일 시스템, 네트워크, 자격 증명 접근을 작은 경계 안에 가둬 두는 것이 핵심입니다.

이 글은 [Prompt Injection Defense](/posts/prompt-injection-defense-practical-guide/), [AI Access Control](/posts/ai-access-control-practical-guide/), [Cloudflare Remote MCP Security](/posts/cloudflare-remote-mcp-security-practical-guide/)와 함께 읽으면 좋습니다.

## 개요

에이전트는 도구를 쓰고 외부 시스템에 접속합니다. 이때 하나의 잘못된 명령이 로컬 파일, 비밀 키, 네트워크 자원까지 건드릴 수 있습니다.

샌드박스는 이런 영향을 제한합니다. 실행 컨테이너, 읽기 전용 파일 시스템, 제한된 네트워크, 짧은 수명의 토큰이 보통의 출발점입니다.

## 왜 중요한가

에이전트가 똑똑해질수록 사고 반경도 커집니다. 샌드박스가 없으면 디버깅 실수나 프롬프트 인젝션이 곧 시스템 사고가 됩니다.

- 임시 실행과 영구 저장을 분리할 수 있습니다.
- 외부 네트워크 접속 범위를 줄일 수 있습니다.
- 비밀 키와 사용자 데이터를 분리할 수 있습니다.

## 권한 설계

샌드박스는 권한 모델과 같이 가야 합니다.

1. 파일 접근 범위를 디렉터리 단위로 제한합니다.
2. 네트워크는 허용 도메인만 통과시킵니다.
3. 실행 시간과 메모리도 상한을 둡니다.
4. 실패 시 컨테이너를 폐기하고 새로 만듭니다.

## 아키텍처 도식

![Agent Sandboxing Choice Flow](/images/agent-sandboxing-choice-flow-2026.svg)

![Agent Sandboxing Architecture](/images/agent-sandboxing-architecture-2026.svg)

격리 환경은 도구 호출 앞단에 있어야 합니다. 그래야 잘못된 요청이 실제 호스트에 영향을 주기 전에 차단됩니다.

## 체크리스트

- 파일 시스템이 쓰기 가능한 범위를 제한했는가
- 네트워크 화이트리스트가 있는가
- 토큰과 비밀 키가 컨테이너 외부에 남지 않는가
- 실행 시간, CPU, 메모리 상한이 있는가
- 실패 시 환경을 폐기하는가

## 결론

Agent Sandboxing은 개발 편의보다 운영 안전을 우선하는 설계입니다. 격리 경계를 먼저 만들면 에이전트를 더 과감하게 확장할 수 있습니다.

## 함께 읽으면 좋은 글

- [Prompt Injection Defense](/posts/prompt-injection-defense-practical-guide/)
- [AI Access Control](/posts/ai-access-control-practical-guide/)
- [Enterprise AI Governance](/posts/enterprise-ai-governance-practical-guide/)
- [Cloudflare Remote MCP Security](/posts/cloudflare-remote-mcp-security-practical-guide/)

