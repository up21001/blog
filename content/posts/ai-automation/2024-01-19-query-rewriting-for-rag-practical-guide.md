---
title: "Query Rewriting for RAG란 무엇인가: 검색 전에 질문을 다듬는 실무 가이드"
date: 2024-01-19T08:00:00+09:00
lastmod: 2024-01-23T08:00:00+09:00
description: "Query Rewriting for RAG를 통해 짧은 질문, 모호한 질문, 대화형 질문을 검색 친화적으로 바꾸는 방법을 정리합니다."
slug: "query-rewriting-for-rag-practical-guide"
categories: ["ai-automation"]
tags: ["Query Rewriting", "RAG", "Retrieval", "Hybrid Search", "Prompting", "Reranking", "Search"]
series: ["RAG Routing 2026"]
featureimage: "/images/query-rewriting-for-rag-workflow-2026.svg"
draft: true
---

Query Rewriting for RAG는 사용자의 원문 질문을 그대로 검색하지 않고, 검색에 더 잘 맞는 형태로 바꾸는 단계입니다. 대화형 질문은 문맥이 짧고 생략이 많아서, 그대로 벡터 검색이나 키워드 검색에 넣으면 결과가 흔들립니다.

이 글은 질문 재작성의 목적, 적용 위치, 실패 패턴을 중심으로 정리합니다.

![Query rewriting for RAG workflow](/images/query-rewriting-for-rag-workflow-2026.svg)

## 왜 중요한가

검색 품질은 질문 품질의 영향을 크게 받습니다. 좋은 인덱스가 있어도 질문이 애매하면 retrieval이 흔들립니다.

- "그거", "이건", "아까 말한 것" 같은 대화형 표현은 그대로 검색하기 어렵습니다.
- 짧은 질문은 핵심 키워드가 부족해서 recall이 떨어집니다.
- 질문 재작성은 reranking보다 앞단에서 검색 후보 자체를 개선합니다.

## 라우팅/재작성 설계

재작성은 보통 두 가지 방식으로 나눕니다.

1. 문맥 보강형: 대화 히스토리를 붙여서 완전한 질문으로 바꿉니다.
2. 검색 최적화형: 키워드와 동의어를 보강해서 검색 친화적으로 만듭니다.

```text
user question -> context expansion -> search-friendly rewrite -> retrieve -> rerank
```

실무에서는 아래 기준이 중요합니다.

- 최신성 질문은 재작성보다 소스 선택이 더 중요할 수 있습니다.
- 내부 문서 검색은 정밀한 키워드 보강이 효과적입니다.
- 대화형 RAG는 재작성 결과를 로그로 남겨야 디버깅이 가능합니다.

## 아키텍처 도식

![Query rewriting for RAG architecture](/images/query-rewriting-for-rag-architecture-2026.svg)

재작성 계층은 검색 앞단에서 실행되며, 너무 공격적으로 바꾸면 원래 의도가 사라질 수 있습니다. 그래서 원문과 재작성문을 둘 다 저장하는 편이 좋습니다.

- 원문 질문을 유지합니다.
- 재작성 규칙을 버전 관리합니다.
- 재작성 품질을 검색 결과와 함께 봅니다.

![Query rewriting for RAG choice flow](/images/query-rewriting-for-rag-choice-flow-2026.svg)

## 체크리스트

- 재작성 전과 후의 질문을 함께 저장하는가
- 대화 문맥을 너무 길게 붙이지 않는가
- 재작성 결과가 원문의 의도를 바꾸지 않는가
- reranking과 역할이 겹치지 않는가
- 실패 시 원문 질문으로 되돌아가는가

## 결론

Query Rewriting for RAG는 작은 보정처럼 보이지만, 실제로는 검색 품질을 크게 좌우하는 전처리 계층입니다. 라우팅과 재작성을 함께 설계하면 `Hybrid Search`, `Tavily`, `Exa` 같은 검색 소스의 성능을 더 안정적으로 끌어올릴 수 있습니다.

## 함께 읽으면 좋은 글

- [Hybrid Search란 무엇인가: 2026년 키워드 검색과 벡터 검색을 함께 쓰는 실무 가이드](/posts/hybrid-search-practical-guide/)
- [Reranking이란 무엇인가: 검색 결과 품질을 끌어올리는 실무 가이드](/posts/reranking-practical-guide/)
- [Retrieval Quality Metrics란 무엇인가: Precision, Recall, MRR로 RAG를 측정하는 방법](/posts/retrieval-quality-metrics-practical-guide/)
- [RAG 평가란 무엇인가: 검색 품질과 답변 품질을 함께 보는 실무 가이드](/posts/rag-evaluation-practical-guide/)
- [Tavily란 무엇인가: 검색 기반 AI를 위한 실무 가이드](/posts/tavily-practical-guide/)
- [Exa란 무엇인가: AI 검색과 리서치 자동화를 위한 실무 가이드](/posts/exa-practical-guide/)
