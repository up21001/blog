---
title: "Agent Debugging 실무 가이드: 복잡한 AI 워크플로우를 재현하고 고치는 방법"
date: 2022-06-10T08:00:00+09:00
lastmod: 2022-06-14T08:00:00+09:00
description: "Agent Debugging을 위해 trace, eval, prompt version, tool call 실패를 어떻게 재현하고 고쳐야 하는지 정리한 실무 가이드입니다."
slug: "agent-debugging-practical-guide"
categories: ["ai-agents"]
tags: ["Agent Debugging", "LLM Observability", "Tracing", "Evaluation", "Prompt Versioning", "LangSmith", "Phoenix", "OpenAI Agent Evals"]
featureimage: "/images/agent-debugging-workflow-2026.svg"
draft: false
---

Agent Debugging은 "응답이 이상하다"는 감상에서 끝나지 않고, 어느 단계의 입력과 출력이 문제였는지 재현하는 과정입니다. 에이전트는 분기, 메모리, 툴 호출, 재시도, 모델 교체가 섞이기 때문에 일반 디버깅 방식만으로는 부족합니다.

![Agent debugging workflow](/images/agent-debugging-workflow-2026.svg)

## 개요

에이전트 디버깅의 목적은 실패를 빨리 찾는 것이 아니라, 실패를 다시 만들 수 있게 하는 것입니다. 재현 가능한 trace, prompt version, tool input/output, memory snapshot이 있어야 원인을 분리할 수 있습니다.

`LangSmith`와 `Phoenix`는 trace 재생과 실험 관리에 좋고, `OpenAI Agent Evals`는 워크플로우 품질을 검증하는 데 유용합니다. `Helicone`과 `Portkey`는 운영 중 패턴 분석과 라우팅 측면에서 함께 보기에 좋습니다.

## 왜 필요한가

에이전트 실패는 대개 한 군데가 아니라 여러 군데가 겹쳐서 발생합니다.

- 툴 입력은 맞지만 툴 출력 해석이 틀릴 수 있습니다.
- 프롬프트는 맞지만 메모리가 오염될 수 있습니다.
- 모델은 맞지만 라우팅이 잘못될 수 있습니다.
- 중간 단계는 정상인데 최종 조합이 틀릴 수 있습니다.

이 때문에 최종 답변만 보는 방식으로는 원인을 못 찾는 경우가 많습니다.

## 측정 항목

디버깅을 위해 남겨야 하는 핵심 항목은 다음과 같습니다.

- 사용자 입력과 시스템 프롬프트 버전
- 각 tool call의 입력, 출력, 에러
- retry, fallback, branch 선택 결과
- memory 저장/조회 결과
- 모델명, temperature, token usage
- 최종 응답과 중간 결과의 차이

## 운영 방식

가장 좋은 방식은 실패를 "한 번에" 고치려 하지 않는 것입니다. 먼저 재현 가능한 케이스를 만들고, 그 다음 하나씩 분리합니다.

1. 실패 trace를 캡처합니다.
2. prompt와 tool input을 고정합니다.
3. 모델 변경 여부를 분리합니다.
4. eval로 회귀를 확인합니다.
5. 같은 실패가 다시 나오는지 검증합니다.

`OpenAI Evals`는 회귀 테스트용, `OpenAI Agent Evals`는 agent workflow 검증용으로 보기 좋습니다. `Anthropic` 계열 도구를 쓰는 경우에도 trace와 tool use 로그를 남기는 습관이 중요합니다.

## 체크리스트

- 실패 케이스를 trace 단위로 재생할 수 있는가
- prompt 버전과 model 버전을 따로 볼 수 있는가
- tool call 실패와 응답 실패를 분리할 수 있는가
- memory 상태를 디버깅 시점에 확인할 수 있는가
- 회귀 테스트가 자동화되어 있는가
- 운영 환경과 테스트 환경이 같은 기준으로 보이는가

## 결론

Agent Debugging은 복잡한 AI 시스템을 운영 가능한 수준으로 끌어올리는 핵심 작업입니다. trace와 eval 없이 디버깅하면 결국 감으로 고치게 됩니다.

### 함께 읽으면 좋은 글

- [OpenAI Agent Evals 실무 가이드: 에이전트 워크플로우를 실패 없이 검증하는 방법](./2026-03-24-openai-agent-evals-practical-guide.md)
- [OpenAI Evals 실무 가이드: 프롬프트와 모델 품질을 정량적으로 검증하는 방법](./2026-03-24-openai-evals-practical-guide.md)
- [Phoenix가 왜 주목받는가: 2026년 오픈소스 LLM 트레이싱과 평가 실무 가이드](./2026-03-24-phoenix-practical-guide.md)

![Agent debugging decision flow](/images/agent-debugging-choice-flow-2026.svg)
