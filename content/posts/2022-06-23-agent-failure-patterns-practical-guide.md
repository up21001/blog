---
title: "Agent Failure Patterns 실무 가이드: 에이전트가 자주 망가지는 지점과 복구 전략"
date: 2022-06-23T10:17:00+09:00
lastmod: 2022-06-27T10:17:00+09:00
description: "AI 에이전트가 실패하는 전형적인 패턴을 정리하고, 복구 규칙과 관측 지점을 함께 설계하는 실무 가이드입니다."
slug: "agent-failure-patterns-practical-guide"
categories: ["ai-agents"]
tags: ["Agent Failure Patterns", "AI Agent", "Tool Calling", "Retry Strategy", "OpenAI Agent Evals", "Agent Debugging", "Human in the Loop"]
featureimage: "/images/agent-failure-patterns-workflow-2026.svg"
series: ["AI Agent Reliability 2026"]
draft: true
---

AI 에이전트는 한 번만 잘 동작하는 시스템이 아니라, 계속 실패를 분류하고 복구하는 시스템으로 봐야 합니다. 겉으로는 같은 요청처럼 보여도, 실제로는 도구 호출 실패, 상태 꼬임, 출력 형식 붕괴, 과도한 재시도 같은 문제가 자주 섞여 있습니다.

이 글은 그런 실패를 유형별로 나누고, 어디에서 끊고 어디에서 복구할지 결정하는 기준을 정리합니다.

![Agent failure patterns workflow](/images/agent-failure-patterns-workflow-2026.svg)

## 개요

에이전트 실패는 대개 네 가지로 압축됩니다. 입력은 맞았는데 도구가 실패하거나, 도구는 성공했는데 상태가 꼬이거나, 출력은 나왔는데 검증을 통과하지 못하거나, 모든 단계가 반복되면서 비용만 커지는 경우입니다.

문제는 실패가 하나만 오지 않는다는 점입니다. `Tool Calling`이 불안정하면 `Agent Debugging`도 어려워지고, 평가가 없으면 같은 실패를 계속 재현하게 됩니다. 그래서 실패 패턴을 먼저 분류해야 복구 설계를 제대로 할 수 있습니다.

## 왜 중요한가

실패를 분류하지 않으면 복구는 금방 임기응변이 됩니다. 임시 `retry`만 늘리면 비용이 커지고, `Human in the Loop`를 너무 늦게 넣으면 사용자는 이미 결과를 믿지 못합니다.

반대로 실패 패턴이 정리돼 있으면 운영이 쉬워집니다.

- 도구 실패는 재시도와 대체 경로로 처리합니다.
- 출력 실패는 스키마 검증과 강제 재질의로 처리합니다.
- 상태 실패는 세션 재구성이나 체크포인트로 처리합니다.
- 불확실한 결과는 사람 검토 지점으로 넘깁니다.

관련해서는 [Tool Calling 실무 가이드](/posts/2026-03-24-tool-calling-practical-guide/), [Agent Debugging 실무 가이드](/posts/2026-03-24-agent-debugging-practical-guide/), [OpenAI Agent Evals 실무 가이드](/posts/2026-03-24-openai-agent-evals-practical-guide/), [Human in the Loop란 무엇인가](/posts/2026-03-24-human-in-the-loop-practical-guide/)를 함께 보면 좋습니다.

## 실패 유형

가장 먼저 봐야 할 것은 실패가 어디에서 나는지입니다.

- 도구 호출 실패: timeout, rate limit, 잘못된 파라미터, 빈 응답
- 출력 실패: JSON 파싱 실패, 스키마 불일치, 누락된 필드
- 상태 실패: 이전 맥락이 사라지거나 잘못된 메모리가 재사용됨
- 반복 실패: 같은 동작을 계속 되풀이하면서 토큰과 비용만 증가함
- 승인 실패: 사람이 확인해야 할 작업이 자동으로 진행됨

이 분류가 있어야 다음 단계에서 retry, fallback, human review 중 무엇을 쓸지 결정할 수 있습니다.

## 복구 설계

복구는 한 가지 규칙으로 끝나지 않습니다. 실패 유형에 따라 다르게 설계해야 합니다.

1. 먼저 실패를 분류합니다.
2. 재시도 가능 여부를 확인합니다.
3. 대체 도구나 대체 모델로 전환합니다.
4. 결과가 위험하면 사람 검토 지점으로 넘깁니다.
5. 같은 실패가 반복되면 회로 차단기를 걸고 알립니다.

![Agent failure patterns choice flow](/images/agent-failure-patterns-choice-flow-2026.svg)

복구 설계에서 중요한 것은 `언제 다시 시도할지`보다 `언제 멈출지`입니다. 멈추는 기준이 없으면 에이전트는 실패를 숨기고 더 많은 실패를 만듭니다. `OpenAI Structured Outputs`나 스키마 검증을 쓰면 출력 실패를 빠르게 재현할 수 있고, `OpenAI Agent Evals`로는 같은 실패가 다시 발생하는지 확인할 수 있습니다.

## 아키텍처 도식

실무에서는 에이전트를 아래처럼 나누면 관리가 쉬워집니다.

- 요청 수신 계층: 입력 정규화와 권한 확인
- 실행 계층: tool call, model call, branch 결정
- 검증 계층: schema check, policy check, human review
- 관측 계층: trace, eval, metric, 로그 저장

![Agent failure patterns architecture](/images/agent-failure-patterns-architecture-2026.svg)

이 구조를 두면 실패가 났을 때 어디서 끊겼는지 바로 보입니다. 특히 trace와 eval이 같이 있어야 재현과 원인 분석이 분리됩니다.

## 체크리스트

1. 실패를 도구, 출력, 상태, 승인으로 나눌 수 있는가
2. 각 실패에 대응하는 retry budget이 있는가
3. fallback 경로가 자동과 수동으로 나뉘어 있는가
4. 위험한 작업은 `Human in the Loop`로 빠지게 되어 있는가
5. 실패 로그가 eval 데이터로 다시 들어가는가
6. 같은 실패가 반복되면 경보가 울리는가

## 결론

에이전트 운영의 핵심은 실패를 없애는 것이 아니라, 실패를 예측 가능한 형태로 바꾸는 것입니다. 실패 유형이 정리되면 복구 규칙을 정할 수 있고, 복구 규칙이 정리되면 평가와 모니터링까지 자연스럽게 이어집니다.

### 함께 읽으면 좋은 글

- [Tool Calling 실무 가이드](/posts/2026-03-24-tool-calling-practical-guide/)
- [Agent Debugging 실무 가이드](/posts/2026-03-24-agent-debugging-practical-guide/)
- [OpenAI Agent Evals 실무 가이드](/posts/2026-03-24-openai-agent-evals-practical-guide/)
- [Human in the Loop란 무엇인가](/posts/2026-03-24-human-in-the-loop-practical-guide/)
- [Tool Selection Strategy 실무 가이드](/posts/2026-03-24-tool-selection-strategy-practical-guide/)

