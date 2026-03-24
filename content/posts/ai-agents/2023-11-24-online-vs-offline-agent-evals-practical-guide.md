---
title: "Online vs Offline Agent Evals 실무 가이드: 에이전트 평가를 언제, 어디서 돌릴까"
date: 2023-11-24T08:00:00+09:00
lastmod: 2023-12-01T08:00:00+09:00
description: "Online eval과 offline eval의 차이를 기준으로, 에이전트 평가를 운영 환경과 개발 환경에 맞게 분리하는 방법을 정리합니다."
slug: "online-vs-offline-agent-evals-practical-guide"
categories: ["ai-agents"]
tags: ["Online Evaluation", "Offline Evaluation", "Agent Evals", "OpenAI Evals", "OpenAI Agent Evals", "LLM Observability", "Evaluation Strategy"]
featureimage: "/images/online-vs-offline-agent-evals-workflow-2026.svg"
draft: false
---

Agent eval은 한 번에 다 돌리는 문제가 아닙니다. 빠르게 실패를 찾는 offline eval과, 실제 운영 환경에서 신호를 잡는 online eval은 목적이 다릅니다. 둘을 섞으면 비용이 커지고, 분리만 하면 품질 하락을 놓칩니다.

이 글에서는 두 방식의 역할을 분명히 나누고, 어떤 기준으로 섞어 운영해야 하는지 정리합니다.

![Online vs offline agent evals workflow](/images/online-vs-offline-agent-evals-workflow-2026.svg)

## 개요

offline eval은 주로 개발과 배포 전 검증에 쓰고, online eval은 운영 중 품질 감시에 씁니다. 질문은 단순합니다.

- 지금 바꾼 prompt가 안전한가
- 실제 사용자 트래픽에서 성능이 유지되는가
- 특정 도구나 분기에서만 실패하는가

이 세 질문에 답하려면 평가 대상과 시점이 다르게 설계되어야 합니다.

## 왜 중요한가

offline만 있으면 실제 사용자 분포를 놓칩니다. online만 있으면 문제를 늦게 발견하고, 비용도 큽니다.

- offline은 재현성과 속도가 강점입니다.
- online은 현실성이 강점입니다.
- 둘을 분리하면 개발 속도와 운영 안정성을 같이 얻습니다.

관련해서 [OpenAI Evals](./2026-03-24-openai-evals-practical-guide.md), [OpenAI Agent Evals](./2026-03-24-openai-agent-evals-practical-guide.md), [AI Tracing](./2026-03-24-ai-tracing-practical-guide.md)를 같이 보면 전체 그림이 잡힙니다.

## 평가 체계

권장 구조는 이렇습니다.

- offline eval
- replay eval
- canary online eval
- human review
- regression gate

![Online vs offline agent evals decision flow](/images/online-vs-offline-agent-evals-choice-flow-2026.svg)

offline은 고정 샘플과 grading 규칙에 적합하고, online은 운영 지표와 이상 탐지에 적합합니다. 둘 사이를 연결하는 것은 trace와 sample store입니다.

## 아키텍처 도식

실무에서는 다음 순서가 단순하고 강합니다.

1. 운영 트래픽을 trace로 저장합니다.
2. 대표 샘플을 offline eval 세트로 추출합니다.
3. 배포 전에는 offline regression을 돌립니다.
4. 배포 후에는 online metric과 alert를 감시합니다.
5. 실패 샘플은 다시 offline set으로 환류합니다.

![Online vs offline agent evals architecture](/images/online-vs-offline-agent-evals-architecture-2026.svg)

이 구조는 [LLM Observability](./2026-03-24-llm-observability-practical-guide.md)와 [Agent Debugging](./2026-03-24-agent-debugging-practical-guide.md)와도 잘 맞습니다.

## 체크리스트

- offline과 online의 목적이 문서화돼 있는가
- 배포 전 regression gate가 있는가
- 운영 중 online alert가 과도하지 않은가
- trace 샘플이 재평가 가능한가
- human review가 필요한 구간을 분리했는가
- 비용 때문에 online eval을 과도하게 줄이지 않았는가

## 결론

Online eval과 offline eval은 경쟁 관계가 아니라 보완 관계입니다. 개발 속도는 offline이 만들고, 운영 신뢰성은 online이 보완합니다. 둘을 분리하고 trace로 연결하면 에이전트 품질 운영이 훨씬 단단해집니다.

### 함께 읽으면 좋은 글

- [OpenAI Evals 실무 가이드](./2026-03-24-openai-evals-practical-guide.md)
- [OpenAI Agent Evals 실무 가이드](./2026-03-24-openai-agent-evals-practical-guide.md)
- [AI Tracing 실무 가이드](./2026-03-24-ai-tracing-practical-guide.md)
- [LLM Observability 실무 가이드](./2026-03-24-llm-observability-practical-guide.md)
- [Agent Debugging 실무 가이드](./2026-03-24-agent-debugging-practical-guide.md)
