---
title: "AI Tracing 실무 가이드: LLM과 에이전트 흐름을 한 번에 추적하는 방법"
date: 2022-09-24T08:00:00+09:00
lastmod: 2022-09-30T08:00:00+09:00
description: "AI Tracing을 어디에 써야 하는지, 어떤 이벤트를 남겨야 하는지, LangSmith와 Phoenix처럼 추적 기반 관측성을 어떻게 설계하는지 정리한 실무 가이드입니다."
slug: "ai-tracing-practical-guide"
categories: ["ai-automation"]
tags: ["AI Tracing", "LLM Observability", "Tracing", "Agent Debugging", "LangSmith", "Phoenix", "OpenTelemetry"]
featureimage: "/images/ai-tracing-workflow-2026.svg"
draft: true
---

AI Tracing은 LLM 호출을 단순 로그로 남기는 수준을 넘어, 프롬프트, 모델 응답, 툴 호출, 리트라이, 분기 흐름을 하나의 실행 경로로 묶어 보는 방식입니다. 에이전트가 복잡해질수록 "왜 이런 답이 나왔는가"를 바로 설명할 수 있어야 하고, 그 출발점이 추적입니다.

![AI tracing workflow](/images/ai-tracing-workflow-2026.svg)

## 개요

Tracing의 핵심은 각 요청을 단일 이벤트가 아니라 실행 그래프로 보는 것입니다. 사용자 입력에서 시작해 모델 호출, 툴 실행, 후처리, 재시도, 종료까지 이어지는 전체 경로를 붙잡아야 문제를 재현할 수 있습니다.

`LangSmith`와 `Phoenix`가 자주 언급되는 이유도 여기에 있습니다. 둘 다 단순 메트릭보다 더 깊게 들어가며, trace 단위로 입력과 출력을 연결해 분석할 수 있습니다.

## 왜 필요한가

LLM 시스템은 일반 웹 API보다 실패 원인이 훨씬 넓습니다.

- 같은 입력인데도 모델 버전 변경으로 출력이 달라질 수 있습니다.
- 툴 호출 하나의 실패가 전체 응답 품질을 망칠 수 있습니다.
- 프롬프트 수정이 정확도뿐 아니라 비용과 지연시간에 영향을 줍니다.
- 에이전트는 분기와 재시도가 많아 로그만으로는 흐름을 복원하기 어렵습니다.

이 때문에 tracing은 "장애가 났을 때 보는 도구"가 아니라, 출시 전 품질 검증과 출시 후 운영까지 묶는 기본 레이어가 됩니다.

## 측정 항목

실무에서는 아래 항목을 trace에 같이 남겨야 쓸모가 있습니다.

- 요청 ID와 사용자 세션 ID
- 모델명, 버전, temperature, max tokens
- 프롬프트 버전과 시스템 메시지 버전
- 툴 이름, 입력값, 응답값, 실패 사유
- 토큰 수, latency, retry 횟수
- 최종 응답과 중간 단계 결과

특히 agent workflow에서는 "최종 답변"보다 "어느 단계에서 꼬였는지"가 중요합니다. 그래서 span을 얕게 여러 개 두는 편이 좋습니다.

## 운영 방식

실무에서 가장 안정적인 패턴은 `app logs`와 `traces`를 분리하는 것입니다. 로그는 인프라와 에러 중심, trace는 실행 흐름과 품질 중심으로 가져가면 분석이 빨라집니다.

`LangSmith`는 prompt 버전 관리와 평가, `Phoenix`는 오픈소스 tracing과 dataset 실험에 강점이 있습니다. `Helicone`은 API 사용량과 세션 분석에 강하고, `Portkey`는 게이트웨이와 라우팅 관점에서 함께 보기 좋습니다.

## 체크리스트

- trace ID를 사용자 요청과 끝까지 연결했는가
- 모델 호출과 툴 호출을 같은 세션에서 볼 수 있는가
- 프롬프트 버전이 trace에 남는가
- 실패 케이스를 다시 재생할 수 있는가
- 비용과 latency를 요청별로 분리해서 보는가
- 운영 중인 모델 변경이 trace에서 드러나는가

## 결론

AI Tracing은 에이전트를 운영 가능한 시스템으로 바꾸는 가장 기본적인 레이어입니다. 로그만으로 버티는 구조보다, trace를 먼저 붙이는 구조가 훨씬 빠르게 안정화됩니다.

### 함께 읽으면 좋은 글

- [LangSmith가 왜 중요한가: 2026년 LLM 관측성, 평가, Agent Builder 실무 가이드](./2026-03-24-langsmith-practical-guide.md)
- [Phoenix가 왜 주목받는가: 2026년 오픈소스 LLM 트레이싱과 평가 실무 가이드](./2026-03-24-phoenix-practical-guide.md)
- [OpenAI Agent Evals 실무 가이드: 에이전트 워크플로우를 실패 없이 검증하는 방법](./2026-03-24-openai-agent-evals-practical-guide.md)

![AI tracing decision flow](/images/ai-tracing-choice-flow-2026.svg)
