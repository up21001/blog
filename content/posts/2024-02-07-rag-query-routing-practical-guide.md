---
title: "RAG Query Routing이란 무엇인가: 질문 유형에 따라 검색 경로를 나누는 실무 가이드"
date: 2024-02-07T10:17:00+09:00
lastmod: 2024-02-12T10:17:00+09:00
description: "RAG Query Routing을 언제 쓰는지, 어떤 라우터를 두는지, Hybrid Search와 Tavily, Exa를 어떻게 조합하는지 정리한 실무 가이드."
slug: "rag-query-routing-practical-guide"
categories: ["software-dev"]
tags: ["RAG", "Query Routing", "Hybrid Search", "Tavily", "Exa", "Retrieval", "Search"]
series: ["RAG Routing 2026"]
featureimage: "/images/rag-query-routing-workflow-2026.svg"
draft: true
---

RAG Query Routing은 질문을 받자마자 하나의 검색 경로만 고집하지 않고, 의도에 따라 다른 검색 경로를 고르는 방식입니다. 예를 들어 내부 문서 검색이 맞는 질문과 외부 웹 검색이 필요한 질문은 같은 파이프라인으로 처리하면 비용과 정확도 모두 손해를 봅니다.

이 글은 질문 분류, 검색 경로 선택, 결과 병합까지를 하나의 운영 단위로 보는 방법을 정리합니다.

![RAG query routing workflow](/images/rag-query-routing-workflow-2026.svg)

## 왜 중요한가

RAG가 커질수록 검색 대상은 하나가 아닙니다. 제품 문서, 정책 문서, FAQ, 코드, 외부 웹, 그리고 실시간성이 필요한 소스가 함께 섞입니다.

- 모든 질문에 벡터 검색만 쓰면 외부 최신 정보에 약합니다.
- 모든 질문에 웹 검색만 쓰면 내부 지식과 권한 제어가 약해집니다.
- 라우팅이 없으면 latency와 비용이 함께 커집니다.

## 라우팅 설계

기본 구조는 간단합니다.

1. 질문을 분류합니다.
2. 내부 문서, 하이브리드 검색, 웹 검색 중 하나 이상을 선택합니다.
3. 필요하면 reranking을 한 번 더 적용합니다.
4. 최종 답변에 출처를 붙입니다.

```text
question -> intent classifier -> route -> retrieve -> rerank -> answer
```

실무에서는 보통 다음 기준을 씁니다.

- 내부 정책, 매뉴얼, 사내 문서는 `Hybrid Search`를 우선합니다.
- 최신 뉴스, 가격, 공개 API 변경은 `Tavily`나 `Exa`를 우선합니다.
- 애매한 질문은 두 경로를 모두 태운 뒤 reranking으로 좁힙니다.

## 아키텍처 도식

![RAG query routing architecture](/images/rag-query-routing-architecture-2026.svg)

보통 라우터는 별도 서비스로 빼는 편이 좋습니다. 이유는 검색 백엔드가 늘어날수록 라우팅 규칙과 관측 포인트가 복잡해지기 때문입니다.

- classifier는 질문 길이와 키워드보다 의도 신호를 봅니다.
- router는 policy와 latency budget을 같이 봅니다.
- retriever는 내부 검색과 외부 검색을 느슨하게 연결합니다.

![RAG query routing choice flow](/images/rag-query-routing-choice-flow-2026.svg)

## 체크리스트

- 질문 유형을 내부 문서형, 최신 정보형, 혼합형으로 나눴는가
- 외부 검색을 허용할지 정책으로 분리했는가
- reranking을 라우팅 뒤에 둘지, 검색 뒤에 둘지 정했는가
- 라우팅 결과를 로그로 남기고 있는가
- 실패 시 fallback 경로가 있는가

## 결론

RAG Query Routing은 검색 품질을 높이기 위한 선택이 아니라, 큰 RAG 시스템을 운영 가능하게 만드는 기본 장치입니다. 질문마다 같은 검색 경로를 쓰는 순간 비용, 정확도, latency가 동시에 흔들립니다.

라우팅 규칙을 먼저 분리하고, 그 다음에 `Hybrid Search`, `Tavily`, `Exa`, `Reranking`을 연결하는 순서가 가장 안정적입니다.

## 함께 읽으면 좋은 글

- [Hybrid Search란 무엇인가: 2026년 키워드 검색과 벡터 검색을 함께 쓰는 실무 가이드](/posts/hybrid-search-practical-guide/)
- [Reranking이란 무엇인가: 검색 결과 품질을 끌어올리는 실무 가이드](/posts/reranking-practical-guide/)
- [Retrieval Quality Metrics란 무엇인가: Precision, Recall, MRR로 RAG를 측정하는 방법](/posts/retrieval-quality-metrics-practical-guide/)
- [RAG 평가란 무엇인가: 검색 품질과 답변 품질을 함께 보는 실무 가이드](/posts/rag-evaluation-practical-guide/)
- [Tavily란 무엇인가: 검색 기반 AI를 위한 실무 가이드](/posts/tavily-practical-guide/)
- [Exa란 무엇인가: AI 검색과 리서치 자동화를 위한 실무 가이드](/posts/exa-practical-guide/)
