---
title: "Retrieval Router란 무엇인가: 검색 소스를 자동으로 고르는 실무 가이드"
date: 2024-04-09T10:17:00+09:00
lastmod: 2024-04-13T10:17:00+09:00
description: "Retrieval Router를 이용해 내부 문서, 하이브리드 검색, 웹 검색, 벡터 검색을 자동으로 분기하는 설계 방법을 정리합니다."
slug: "retrieval-router-practical-guide"
categories: ["software-dev"]
tags: ["Retrieval Router", "RAG", "Routing", "Hybrid Search", "Tavily", "Exa", "Vector Search"]
series: ["RAG Routing 2026"]
featureimage: "/images/retrieval-router-workflow-2026.svg"
draft: false
---

Retrieval Router는 질문에 맞는 검색 소스를 자동으로 고르는 계층입니다. 단순히 검색을 한번 더 하는 장치가 아니라, 어떤 데이터셋을 우선할지와 어떤 검색 전략이 더 적합한지를 결정하는 게 핵심입니다.

이 방식은 내부 문서 중심 시스템과 웹 리서치 중심 시스템을 하나의 제품 안에서 같이 운영할 때 특히 유용합니다.

![Retrieval router workflow](/images/retrieval-router-workflow-2026.svg)

## 왜 중요한가

검색 소스가 늘어나면 오히려 정확도가 떨어질 수 있습니다. 검색 대상이 많아질수록 잘못된 소스를 먼저 고르는 비용이 커지기 때문입니다.

- 사내 문서와 외부 웹을 같은 우선순위로 두면 정책 위반이 생깁니다.
- 벡터 검색만 고집하면 최신 정보가 늦습니다.
- 검색 소스가 많을수록 라우터가 없으면 운영 규칙이 코드 곳곳에 퍼집니다.

## 라우팅/재작성 설계

라우터는 보통 아래 순서로 움직입니다.

1. 질문의 의도와 최신성 요구를 분류합니다.
2. 내부 문서, 외부 웹, 통합 검색 중 하나를 선택합니다.
3. 필요한 경우 질문을 재작성해서 검색 효율을 높입니다.
4. 검색 결과를 합치고 reranking을 적용합니다.

```text
question -> router -> select source -> retrieve -> optional rewrite -> rerank
```

실무에서는 다음 규칙이 잘 먹힙니다.

- 정책, 가격, API 문서처럼 변화가 빠른 항목은 웹 검색을 우선합니다.
- 제품, 운영, 내부 지식은 `Hybrid Search`를 우선합니다.
- 소스가 애매하면 `Retrieval Quality Metrics`로 라우터 성능을 따로 봅니다.

## 아키텍처 도식

![Retrieval router architecture](/images/retrieval-router-architecture-2026.svg)

라우터는 검색 백엔드 앞단에서만 동작시키지 말고, 결과 품질 로그도 같이 남겨야 합니다. 그래야 어떤 소스가 자주 오판하는지 보입니다.

- router decision을 샘플링해서 검토합니다.
- source별 latency와 hit rate를 분리해서 봅니다.
- failover를 명시적으로 둡니다.

![Retrieval router choice flow](/images/retrieval-router-choice-flow-2026.svg)

## 체크리스트

- 질문마다 우선 검색 소스를 한 번만 정하고 있는가
- 내부/외부/혼합 검색 기준이 문서화되어 있는가
- 라우터의 오판을 추적할 수 있는가
- 소스별 비용과 latency를 따로 볼 수 있는가
- reranking과 query rewriting의 적용 순서를 정했는가

## 결론

Retrieval Router는 검색 품질을 자동화하는 계층입니다. 검색 소스가 늘어나는 순간부터는 "어디서 검색할지"가 "무엇을 검색할지"만큼 중요해집니다.

처음에는 단순 규칙 기반으로 시작하고, 이후에 query classifier와 재작성 단계를 붙이는 방식이 가장 안전합니다.

## 함께 읽으면 좋은 글

- [Hybrid Search란 무엇인가: 2026년 키워드 검색과 벡터 검색을 함께 쓰는 실무 가이드](/posts/hybrid-search-practical-guide/)
- [Reranking이란 무엇인가: 검색 결과 품질을 끌어올리는 실무 가이드](/posts/reranking-practical-guide/)
- [Retrieval Quality Metrics란 무엇인가: Precision, Recall, MRR로 RAG를 측정하는 방법](/posts/retrieval-quality-metrics-practical-guide/)
- [RAG 평가란 무엇인가: 검색 품질과 답변 품질을 함께 보는 실무 가이드](/posts/rag-evaluation-practical-guide/)
- [Tavily란 무엇인가: 검색 기반 AI를 위한 실무 가이드](/posts/tavily-practical-guide/)
- [Exa란 무엇인가: AI 검색과 리서치 자동화를 위한 실무 가이드](/posts/exa-practical-guide/)
