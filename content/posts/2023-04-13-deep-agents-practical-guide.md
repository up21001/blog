---
title: "Deep Agents란 무엇인가: 2026년 계획형 에이전트와 서브에이전트 실무 가이드"
date: 2023-04-13T10:17:00+09:00
lastmod: 2023-04-14T10:17:00+09:00
description: "Deep Agents가 왜 주목받는지, 계획, 서브에이전트, 파일 시스템 기반 컨텍스트 관리, 장기 메모리, SDK와 CLI를 어떻게 쓰는지 2026년 기준으로 정리한 실무 가이드입니다."
slug: "deep-agents-practical-guide"
categories: ["ai-automation"]
tags: ["Deep Agents", "LangGraph", "Subagents", "Planning", "Long-term Memory", "CLI", "Agent Harness"]
series: ["AI Agent Tooling 2026"]
featureimage: "/images/deep-agents-workflow-2026.svg"
draft: false
---

`Deep Agents`는 2026년 기준으로 `planning agents`, `subagents`, `deepagents`, `LangGraph`, `agent harness` 같은 검색어에서 빠르게 검색량이 늘기 쉬운 주제입니다. 이유는 명확합니다. 복잡한 작업은 단순 채팅 한 번으로 끝나지 않고, 계획 수립, 단계 분해, 작업 분리, 파일 시스템 컨텍스트, 장기 메모리가 함께 필요하기 때문입니다.

LangChain 공식 문서의 Deep Agents 개요는 이를 `complex, multi-step tasks`를 위한 에이전트 하니스로 설명합니다. 계획, 파일 시스템 기반 컨텍스트 관리, subagent spawning, long-term memory가 핵심입니다. 즉 `Deep Agents란 무엇인가`, `서브에이전트`, `계획형 에이전트`, `LangGraph 기반 agent harness`를 찾는 독자에게 잘 맞습니다.

![Deep Agents 워크플로우](/images/deep-agents-workflow-2026.svg)

## 이런 분께 추천합니다

- 복잡한 작업을 계획-실행-검증으로 나누고 싶은 개발자
- 서브에이전트와 장기 메모리를 실무에 쓰려는 팀
- `Deep Agents`, `LangGraph`, `agent harness`를 비교 중인 분

## Deep Agents의 핵심은 무엇인가

핵심은 "계획과 분해를 에이전트 내부 기본 기능으로 넣는다"는 점입니다.

| 기능 | 의미 |
|---|---|
| Planning | 할 일을 먼저 쪼갬 |
| File system tools | 파일 기반 컨텍스트 관리 |
| Subagents | 전문 역할 분리 |
| Long-term memory | 세션 간 기억 |
| SDK | 애플리케이션에 붙이는 기본 패키지 |
| CLI | 터미널 코딩 에이전트 |

Deep Agents는 LangGraph runtime 위에서 동작합니다. 그래서 durable execution, streaming, human-in-the-loop 같은 운영 특성을 함께 가져갑니다.

## 왜 지금 Deep Agents가 중요해졌는가

AI 에이전트는 점점 더 "한 번 답하는 모델"이 아니라 "프로젝트를 끝내는 작업자"에 가까워지고 있습니다. 그럴수록 아래 기능이 필요합니다.

- 계획을 먼저 세운다
- 파일과 디렉터리를 컨텍스트로 쓴다
- 역할별 서브에이전트로 분리한다
- 긴 작업을 기억하고 이어서 한다

Deep Agents는 이런 패턴을 가장 직접적으로 담습니다.

## 어떤 팀에 잘 맞는가

- 코드 수정, 조사, 문서 정리, 리서치를 하나의 작업 흐름으로 다뤄야 한다
- 장기 실행 작업에 컨텍스트 손실이 치명적이다
- CLI 기반 에이전트 워크플로우를 선호한다
- 프로젝트 관습을 학습하는 에이전트를 만들고 싶다

## 실무 도입 시 체크할 점

1. 계획과 실행 단계를 분리합니다.
2. 파일 시스템 접근 범위를 먼저 제한합니다.
3. subagent 역할을 작게 나눕니다.
4. 장기 메모리 저장 전략을 정합니다.
5. CLI와 SDK의 역할을 나눠 설계합니다.

## 장점과 주의점

장점:

- 복잡한 작업을 계획적으로 수행하기 좋습니다.
- 서브에이전트 분리가 명확합니다.
- 장기 메모리와 프로젝트 컨텍스트를 잘 다룹니다.
- LangGraph 기반이라 운영 특성이 강합니다.

주의점:

- 파일 시스템 컨텍스트를 잘못 열면 위험합니다.
- 계획을 과하게 쪼개면 오히려 느려집니다.
- 단순 작업에는 과할 수 있습니다.

![Deep Agents 선택 흐름](/images/deep-agents-choice-flow-2026.svg)

## 검색형 키워드

- `Deep Agents란 무엇인가`
- `subagents`
- `planning agents`
- `LangGraph agent harness`
- `terminal coding agent`

## 한 줄 결론

Deep Agents는 2026년 기준으로 복잡한 작업을 계획, 분해, 위임, 기억하는 구조로 운영하려는 팀에게 특히 잘 맞는 에이전트 프레임워크입니다.

## 참고 자료

- Deep Agents overview: https://docs.langchain.com/oss/python/deepagents/overview
- Deep Agents overview (JS): https://docs.langchain.com/oss/javascript/deepagents/overview
- Deep Agents CLI: https://docs.langchain.com/oss/javascript/deepagents/cli/overview
- Deep Agents streaming: https://docs.langchain.com/oss/python/deepagents/streaming/overview

## 함께 읽으면 좋은 글

- [LangGraph란 무엇인가: 2026년 상태 저장 AI 에이전트 오케스트레이션 실무 가이드](/posts/langgraph-practical-guide/)
- [Agno란 무엇인가: 2026년 멀티 에이전트 런타임과 AgentOS 실무 가이드](/posts/agno-practical-guide/)
- [Claude Code란 무엇인가: 2026년 AI 코딩 에이전트 실무 가이드](/posts/claude-code-practical-guide-2026/)
