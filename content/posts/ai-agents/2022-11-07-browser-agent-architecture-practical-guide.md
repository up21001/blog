---
title: "Browser Agent 아키텍처 실무 가이드: 브라우저 자동화와 에이전트를 분리하는 방법"
date: 2022-11-07T08:00:00+09:00
lastmod: 2022-11-12T08:00:00+09:00
description: "Browser Agent를 설계할 때 브라우저 실행, 상태 관리, 안전장치, 로그 구조를 어떻게 나눠야 하는지 정리한 실무 가이드입니다."
slug: "browser-agent-architecture-practical-guide"
categories: ["ai-agents"]
tags: ["Browser Agent", "Browser Automation", "AI Agent", "Playwright", "Stagehand", "Browserbase", "OpenAI Computer Use"]
series: ["AI Agent Tooling 2026"]
featureimage: "/images/browser-agent-architecture-workflow-2026.svg"
draft: false
---

브라우저 자동화는 단순히 클릭과 입력을 흉내 내는 작업처럼 보이지만, 실제로는 상태 관리와 실패 복구가 핵심입니다. `Browser Agent`는 이 작업을 에이전트 계층과 브라우저 실행 계층으로 분리해, 더 예측 가능하고 운영 가능한 구조로 만드는 접근입니다.

이 글에서는 브라우저 에이전트 아키텍처를 어떻게 나누는지, 어떤 도구와 함께 쓰면 좋은지, 그리고 운영에서 어떤 안전장치를 넣어야 하는지 정리합니다.

![Browser Agent 아키텍처](/images/browser-agent-architecture-workflow-2026.svg)

## 개요

Browser Agent는 보통 아래 3개 레이어로 나눠 생각하면 이해가 쉽습니다.

- 계획 레이어: LLM이 다음 행동을 결정합니다.
- 실행 레이어: Playwright, Browserbase, Browser Use 같은 도구가 실제 브라우저를 움직입니다.
- 관측 레이어: 스크린샷, DOM 스냅샷, 로그, 이벤트를 모아서 재현 가능하게 만듭니다.

이 구조를 분리하지 않으면, "어떤 단계에서 실패했는지"와 "왜 실패했는지"를 구분하기 어렵습니다.

## 왜 주목받는가

Browser Agent가 주목받는 이유는 웹이 여전히 가장 흔한 업무 인터페이스이기 때문입니다. 로그인, 폼 입력, 다운로드, 사내 시스템 처리, 고객 포털 조회 같은 작업은 API가 없는 경우가 많습니다.

Browser Use, Stagehand, Browserbase, OpenAI Computer Use 같은 도구가 함께 언급되는 이유도 같습니다. 각 도구는 표현은 다르지만 결국 같은 문제를 다룹니다. 브라우저라는 비결정적 환경에서 에이전트가 안정적으로 행동하도록 만드는 것입니다.

## 구현 흐름

실무에서는 아래 순서로 설계하는 편이 안전합니다.

1. 사용자의 의도를 구조화합니다.
2. 허용된 사이트와 동작 범위를 명시합니다.
3. 브라우저 세션을 준비하고 상태를 분리합니다.
4. 에이전트가 다음 행동을 제안합니다.
5. 실행 계층이 행동을 수행하고 결과를 반환합니다.
6. 실패 시 스크린샷과 DOM을 저장합니다.
7. 재시도 규칙과 중단 기준을 적용합니다.

이때 중요한 점은 에이전트가 브라우저를 직접 "소유"하지 않도록 하는 것입니다. 실행 권한은 별도 계층에서 통제해야 합니다.

## 리스크와 안전장치

브라우저 에이전트에서 가장 자주 터지는 문제는 다음과 같습니다.

- 로그인 세션 만료
- CAPTCHA 또는 봇 탐지
- 페이지 구조 변경
- 잘못된 버튼 클릭
- 반복 제출

대응책은 단순합니다.

- allowlist 도메인만 허용합니다.
- 결제, 삭제, 제출 같은 행위는 확인 단계를 둡니다.
- 민감 페이지는 human-in-the-loop로 분기합니다.
- 자동 재시도 횟수와 타임아웃을 제한합니다.
- 실행 직후 스크린샷과 로그를 남깁니다.

## 체크리스트

- 브라우저 세션이 작업 단위로 분리되는가
- 로그인/쿠키 상태를 안전하게 보관하는가
- 실패 시 재현 가능한 로그가 남는가
- 클릭과 입력이 정책으로 제한되는가
- 수동 승인 지점이 정의되어 있는가
- 셀렉터 변경에 대비한 fallback이 있는가

## 결론

Browser Agent는 "웹을 조작하는 LLM"이 아니라 "웹 조작을 안전하게 오케스트레이션하는 시스템"으로 봐야 합니다. 실행 계층과 계획 계층을 분리하면 운영 난이도가 크게 내려갑니다.

Browser Use, Stagehand, Browserbase, OpenAI Computer Use를 비교할 때도 결국 기준은 같습니다. 자동화 범위, 상태 관리 방식, 관측성, 안전장치가 맞는지 확인하면 됩니다.

## 함께 읽으면 좋은 글

- [Browser Use란 무엇인가: 2026년 AI 브라우저 자동화 실무 가이드](/posts/browser-use-practical-guide/)
- [Stagehand란 무엇인가: 2026년 AI 웹 자동화 실무 가이드](/posts/stagehand-practical-guide/)
- [Browserbase란 무엇인가: 2026년 AI 브라우저 인프라 실무 가이드](/posts/browserbase-practical-guide/)
- [OpenAI Computer Use 실무 가이드: 브라우저와 화면 조작을 에이전트에 맡기는 방법](/posts/openai-computer-use-practical-guide/)
