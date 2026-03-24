---
title: "Reranking이란 무엇인가: 검색 결과 품질을 끌어올리는 실무 가이드"
date: 2024-04-04T08:00:00+09:00
lastmod: 2024-04-04T08:00:00+09:00
description: "Reranking이 왜 검색 품질의 마지막 한 끗인지, cross encoder와 LLM rerank를 언제 써야 하는지, Qdrant·pgvector·RAG 파이프라인에서 어떻게 붙이는지 정리한 2026년 실무 가이드."
slug: "reranking-practical-guide"
categories: ["software-dev"]
tags: ["Reranking", "Search Quality", "RAG", "Hybrid Search", "Cross Encoder", "Vector Search", "Retrieval"]
series: ["Vector Search 2026"]
featureimage: "/images/reranking-workflow-2026.svg"
draft: true
---

Reranking은 처음에 가져온 후보 문서를 다시 정렬하는 단계입니다. 검색 파이프라인에서 가장 많이 놓치는 부분이지만, 실제 품질 차이는 여기서 크게 납니다.

벡터 검색이나 Hybrid Search는 후보를 잘 뽑는 단계이고, reranking은 그 후보 중에서 진짜로 쓸만한 결과를 골라내는 단계입니다. `Qdrant`, `pgvector`, `Supabase AI & Vectors`, `OpenAI File Search`를 쓰더라도 최종 품질을 높이려면 reranking이 거의 필수입니다.

![Reranking workflow](/images/reranking-workflow-2026.svg)

## 왜 중요한가

검색 품질 문제는 보통 top 20까지는 괜찮아 보이다가 top 5에서 무너집니다. 사용자는 상위 몇 개만 보기 때문에, reranking이 없으면 "찾긴 찾았는데 답답한 검색"이 됩니다.

- 비슷한 후보가 많을수록 reranking 효과가 큽니다.
- 짧은 쿼리보다 문장형 쿼리에서 이득이 큽니다.
- 검색 결과를 LLM 컨텍스트로 넣는 RAG에서는 더 중요합니다.

## 빠른 시작

가장 기본적인 흐름은 다음과 같습니다.

1. vector search나 hybrid search로 20개에서 100개 후보를 가져옵니다.
2. reranker에 `query + passage` 쌍을 넣습니다.
3. relevance score로 다시 정렬합니다.
4. 상위 몇 개만 LLM에 전달합니다.

```text
retrieve 50 -> rerank -> keep top 5 -> generate
```

reranker는 대체로 아래 셋 중 하나로 나뉩니다.

- Cross encoder 기반 모델
- LLM 기반 reranker
- 도메인 특화 score rule과 결합한 하이브리드 방식

## 성능/비용 트레이드오프

| 방식 | 장점 | 단점 |
|---|---|---|
| No rerank | 가장 싸고 빠릅니다 | 품질이 들쭉날쭉합니다 |
| Cross encoder | 품질과 비용의 균형이 좋습니다 | 추가 추론 비용이 듭니다 |
| LLM rerank | 유연하고 설명력이 좋습니다 | 느리고 비쌉니다 |
| Rule + rerank | 운영 제어가 쉽습니다 | 설계가 복잡해집니다 |

실무에서는 "모든 쿼리에 reranking"보다 "의도가 불분명한 쿼리와 중요 검색에만 reranking"이 더 낫습니다.

## 체크리스트

- 후보 수를 너무 적게 잡지 않습니다.
- reranker 입력 길이를 초과하지 않도록 chunk를 조정합니다.
- latency budget을 검색 단계와 분리해 계산합니다.
- top-k 평가셋을 만들고 reranking 전후를 비교합니다.
- exact match가 중요한 필드는 reranker에 함께 넣습니다.
- RAG에서는 answer quality만 보지 말고 citation 정확도도 봅니다.

## 결론

Reranking은 검색 품질의 마지막 관문입니다. 특히 Hybrid Search를 쓰는 환경에서는 reranking이 있어야 "후보를 잘 찾는 검색"이 아니라 "실제로 쓸 수 있는 검색"이 됩니다.

검색 품질을 한 단계 올리고 싶다면, first-stage retrieval보다 reranking부터 먼저 튜닝하는 것이 효율적입니다.

## 함께 읽으면 좋은 글

- [Hybrid Search란 무엇인가: 2026년 키워드 검색과 벡터 검색을 함께 쓰는 실무 가이드](/posts/hybrid-search-practical-guide/)
- [Qdrant란 무엇인가: 2026년 벡터 데이터베이스 실무 가이드](/posts/qdrant-practical-guide/)
- [pgvector란 무엇인가: 2026년 PostgreSQL 벡터 확장 실무 가이드](/posts/pgvector-practical-guide/)
- [OpenAI File Search란 무엇인가: 2026년 문서 검색 기반 AI 실무 가이드](/posts/openai-file-search-practical-guide/)
