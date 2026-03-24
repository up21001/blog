---
title: "Reranking 비용과 지연시간 트레이드오프 실무 가이드"
date: 2024-03-31T08:00:00+09:00
lastmod: 2024-03-31T08:00:00+09:00
description: "Reranking을 넣을 때 비용과 latency가 어떻게 늘어나는지, 어디서 절충해야 하는지, 운영 중 어떤 수치를 봐야 하는지 정리한 가이드."
slug: "reranking-cost-latency-tradeoff-practical-guide"
categories: ["software-dev"]
tags: ["Reranking", "Latency", "Cost Optimization", "RAG", "Search Quality", "Performance"]
series: ["RAG Routing 2026"]
featureimage: "/images/reranking-cost-latency-tradeoff-workflow-2026.svg"
draft: true
---

Reranking은 품질을 높이지만 비용과 지연시간을 함께 올린다. 그래서 운영에서는 "얼마나 좋아졌는가"와 "얼마나 느려졌는가"를 동시에 봐야 한다.

![Reranking cost latency workflow](/images/reranking-cost-latency-tradeoff-workflow-2026.svg)

## 개요

Reranking 트레이드오프는 단순하다. 후보가 많아질수록 품질은 좋아질 가능성이 높지만, 처리 시간과 비용도 같이 증가한다.

- 작은 시스템은 reranking이 거의 공짜처럼 보일 수 있다.
- 문서 수와 트래픽이 늘면 reranking 비용이 눈에 띄게 커진다.
- 결국 "어디까지 reranking할 것인가"가 설계의 핵심이 된다.

## 왜 중요한가

RAG 운영에서 가장 흔한 실수는 품질 개선만 보고 reranking을 무작정 키우는 것이다. 실제로는 latency budget, GPU/CPU 비용, 호출당 토큰 비용이 함께 움직인다.

- 사용자 대기시간이 길어지면 품질 개선 효과가 상쇄될 수 있다.
- 초당 요청 수가 늘면 작은 비용 차이도 크게 증폭된다.
- reranking은 검색 품질의 최적화가 아니라 시스템 전체의 최적화로 봐야 한다.

## 운영/튜닝 포인트

![Reranking cost latency choice flow](/images/reranking-cost-latency-tradeoff-choice-flow-2026.svg)

- 후보군 크기를 작게 유지하면 비용은 줄지만 recall이 떨어질 수 있다.
- reranking을 모든 요청에 적용하지 말고 질문 유형별로 분기하는 편이 낫다.
- 캐싱과 routing을 섞으면 reranker 호출 수를 줄일 수 있다.

운영 지표는 다음처럼 나누는 것이 실용적이다.

1. 검색 품질 지표: `MRR`, `nDCG`, `top-k hit rate`
2. 시스템 지표: `p95 latency`, `CPU/GPU utilization`
3. 비용 지표: `cost per query`, `rerank calls per request`

## 아키텍처 도식

![Reranking cost latency architecture](/images/reranking-cost-latency-tradeoff-architecture-2026.svg)

구조적으로 보면 reranking은 "품질 향상 엔진"이면서 동시에 "비용 증폭기"다. 라우팅, 캐시, 후보군 축소가 같이 있어야 안정적으로 운영된다.

## 체크리스트

- reranking이 필요한 요청만 선별하고 있는가.
- top-k와 latency budget을 함께 관리하는가.
- reranker 비용을 요청 유형별로 분리해서 보고 있는가.
- 품질 개선이 비용 증가를 정당화하는가.

## 결론

Reranking은 정답이 아니라 절충이다. 품질, 비용, 지연시간 사이에서 어느 지점을 고를지 명확히 정하고, 그 기준을 지표로 계속 검증해야 한다.

## 함께 읽으면 좋은 글

- [Reranking 운영 실무 가이드](/posts/reranking-operations-practical-guide/)
- [Cross-Encoder Reranking 실무 가이드](/posts/cross-encoder-reranking-practical-guide/)
- [Retrieval Quality Metrics란 무엇인가](/posts/retrieval-quality-metrics-practical-guide/)
- [RAG Query Routing란 무엇인가](/posts/rag-query-routing-practical-guide/)

