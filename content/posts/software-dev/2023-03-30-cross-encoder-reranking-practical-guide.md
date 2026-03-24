---
title: "Cross-Encoder Reranking 실무 가이드: 정확도를 높이는 모델 선택과 운영"
date: 2023-03-30T08:00:00+09:00
lastmod: 2023-04-04T08:00:00+09:00
description: "Cross-encoder reranking을 언제 써야 하는지, bi-encoder와 무엇이 다른지, 어떤 운영 포인트를 봐야 하는지 정리한 실무 가이드."
slug: "cross-encoder-reranking-practical-guide"
categories: ["software-dev"]
tags: ["Cross-Encoder", "Reranking", "Bi-Encoder", "RAG", "Search Quality", "Embedding"]
series: ["RAG Routing 2026"]
featureimage: "/images/cross-encoder-reranking-workflow-2026.svg"
draft: false
---

Cross-encoder reranking은 질문과 문서를 함께 넣어 직접 관련도를 계산하는 방식이다. bi-encoder보다 느리지만, 상위 후보의 순서를 더 정교하게 잡는다.

![Cross-encoder reranking workflow](/images/cross-encoder-reranking-workflow-2026.svg)

## 개요

Reranking 모델은 크게 두 부류로 나뉜다. 빠른 검색용 bi-encoder와 정확도 중심의 cross-encoder다.

- bi-encoder는 미리 임베딩을 만들어 빠르게 찾는다.
- cross-encoder는 query-document pair를 직접 평가해 더 정확하다.
- 두 방식을 섞으면 검색 속도와 정확도의 균형을 잡기 쉽다.

## 왜 중요한가

RAG 시스템에서 cross-encoder reranking은 비용이 들더라도 상위 문서 품질을 안정화하는 수단이다. 특히 긴 문서, 유사 문서가 많은 코퍼스, 도메인 특화 검색에서 효과가 크다.

- 상위 몇 개 결과의 품질이 전체 답변 품질을 좌우한다.
- 검색 결과가 비슷비슷할수록 reranker의 분별력이 중요해진다.
- 평가가 어려운 도메인일수록 품질 보정 장치가 필요하다.

## 운영/튜닝 포인트

![Cross-encoder choice flow](/images/cross-encoder-reranking-choice-flow-2026.svg)

- 후보군을 너무 크게 넣으면 지연시간이 크게 늘어난다.
- `top 10`, `top 20`, `top 50`처럼 후보 크기를 실험으로 정해야 한다.
- 정확도 개선이 실제 사용자 체감으로 이어지는지 봐야 한다.

운영 시에는 다음 순서가 현실적이다.

1. 검색 후보군을 먼저 안정화한다.
2. cross-encoder를 상위 후보에만 적용한다.
3. latency budget 안에서 처리 가능한 `k`를 찾는다.
4. 도메인별로 reranker 모델을 분리할지 결정한다.

## 아키텍처 도식

![Cross-encoder architecture](/images/cross-encoder-reranking-architecture-2026.svg)

Cross-encoder는 검색 품질을 올리는 대신 비용과 지연시간을 가져간다. 그래서 시스템 안에서 어디까지 정확도를 사고, 어디서 비용을 아낄지 명확히 정해야 한다.

## 체크리스트

- reranking 대상 후보 수가 latency budget 안에 들어오는가.
- `MRR`, `nDCG`, `answer accuracy`가 실제로 개선되는가.
- fallback 경로가 있어 reranker 장애 시에도 서비스가 동작하는가.
- 모델 교체가 가능한 구조인가.

## 결론

Cross-encoder reranking은 비싸지만 강력하다. 검색 품질이 제품 경쟁력의 핵심이라면, 상위 후보에만 선택적으로 적용하는 방식이 가장 실용적이다.

## 함께 읽으면 좋은 글

- [Reranking 운영 실무 가이드](/posts/reranking-operations-practical-guide/)
- [Retrieval Quality Metrics란 무엇인가](/posts/retrieval-quality-metrics-practical-guide/)
- [Hybrid Search란 무엇인가](/posts/hybrid-search-practical-guide/)
- [RAG Query Routing란 무엇인가](/posts/rag-query-routing-practical-guide/)

