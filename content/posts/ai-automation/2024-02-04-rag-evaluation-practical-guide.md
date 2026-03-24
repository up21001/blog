---
title: "RAG 평가란 무엇인가: 검색 품질과 답변 품질을 함께 보는 실무 가이드"
date: 2024-02-04T08:00:00+09:00
lastmod: 2024-02-07T08:00:00+09:00
description: "RAG 시스템을 실제로 운영할 때 어떤 지표를 봐야 하는지, Ragas와 OpenAI Evals를 어떻게 함께 써야 하는지 정리한 실무 가이드입니다."
slug: "rag-evaluation-practical-guide"
categories: ["ai-automation"]
tags: ["RAG Evaluation", "Ragas", "OpenAI Evals", "OpenAI Agent Evals", "RAG Ops", "Evaluation"]
series: ["RAG Evaluation 2026"]
featureimage: "/images/rag-evaluation-workflow-2026.svg"
draft: false
---

RAG 평가는 단순히 정답 문자열이 맞는지 보는 일이 아닙니다. 검색이 제대로 됐는지, 근거가 충분한지, 최종 답변이 그 근거를 잘 반영했는지를 함께 봐야 합니다.

이 글은 RAG 운영 관점에서 평가를 어떻게 나누고, 어떤 도구를 어디에 붙이며, 실험 결과를 어떻게 해석할지 정리합니다.

![RAG evaluation workflow](/images/rag-evaluation-workflow-2026.svg)

## 개요

RAG 평가는 보통 세 단계로 나눠서 봅니다.

1. 검색 단계가 관련 문서를 잘 찾는가
2. 재정렬 단계가 상위 결과를 잘 다듬는가
3. 생성 단계가 근거를 바탕으로 답변하는가

이 셋이 분리되지 않으면 문제가 생겼을 때 원인을 찾기 어렵습니다.

## 왜 중요한가

RAG는 모델만 바꾼다고 품질이 일정하게 오르지 않습니다. 실제 품질은 문서 품질, chunking, embedding, retrieval, reranking, prompt, generation이 함께 결정합니다.

평가가 없으면 다음 문제가 반복됩니다.

- 검색은 좋아졌는데 답변이 더 나빠지는 상황
- 문서가 바뀌었는데 회귀를 못 잡는 상황
- 운영 중 트래픽이 늘어도 품질 저하를 모르는 상황

## 평가 지표와 방법

RAG 평가는 최소한 아래 항목을 분리해서 봐야 합니다.

| 항목 | 예시 지표 |
|---|---|
| Retrieval | Recall@K, Precision@K, MRR |
| Reranking | nDCG, top-k hit rate |
| Generation | groundedness, correctness, citation coverage |
| System | latency, cost, failure rate |

Ragas는 retrieval과 generation을 함께 보는 데 유용하고, OpenAI Evals나 Agent Evals는 프롬프트와 에이전트 워크플로우 회귀 테스트에 좋습니다.

## 운영 팁

- 검색 품질과 답변 품질을 같은 점수로 합치지 마십시오.
- 작은 골든셋부터 시작하고 점진적으로 늘리십시오.
- 실패 케이스는 반드시 태그로 남기십시오.
- 문서 배포와 평가 실행을 분리하십시오.
- 검색이 흔들리면 chunking과 embedding부터 다시 보십시오.

RAG 운영 자체를 다루는 글은 [RAG Ops 실무 가이드](/posts/rag-ops-practical-guide/)를 같이 보면 좋습니다.

## 체크리스트

- 검색 지표와 생성 지표가 분리되어 있는가
- 골든셋이 실제 사용자 질문을 반영하는가
- 회귀 테스트가 자동으로 돌고 있는가
- 실패 케이스가 재현 가능한가
- 배포 전 평가 결과를 확인하는가

## 결론

RAG 평가는 모델 점수 하나로 끝나지 않습니다. 검색, 재정렬, 생성, 운영 지표를 분리해서 봐야 원인을 찾을 수 있고, 개선 속도도 빨라집니다.

먼저 작은 평가셋을 만들고, 그 위에 회귀 테스트를 얹는 방식이 가장 현실적입니다.

## 함께 읽으면 좋은 글

- [Ragas란 무엇인가: 2026년 RAG 평가와 실험 실무 가이드](/posts/ragas-practical-guide/)
- [OpenAI Evals 실무 가이드: 프롬프트와 모델 품질을 정량적으로 검증하는 방법](/posts/openai-evals-practical-guide/)
- [OpenAI Agent Evals 실무 가이드: 에이전트 워크플로우를 실패 없이 검증하는 방법](/posts/openai-agent-evals-practical-guide/)
- [RAG Ops 실무 가이드: 검색 품질과 운영 지표를 함께 관리하는 방법](/posts/rag-ops-practical-guide/)

