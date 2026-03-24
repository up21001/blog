---
title: "Retrieval Quality Metrics란 무엇인가: Precision, Recall, MRR로 RAG를 측정하는 방법"
date: 2024-04-09T08:00:00+09:00
lastmod: 2024-04-16T08:00:00+09:00
description: "RAG와 검색 시스템에서 retrieval quality를 어떻게 수치로 보는지, Precision, Recall, MRR, nDCG를 실무적으로 해석하는 방법을 정리합니다."
slug: "retrieval-quality-metrics-practical-guide"
categories: ["software-dev"]
tags: ["Retrieval Quality", "RAG", "Hybrid Search", "Reranking", "Precision", "Recall", "MRR", "nDCG"]
series: ["RAG Evaluation 2026"]
featureimage: "/images/retrieval-quality-metrics-workflow-2026.svg"
draft: true
---

검색 품질은 "그럴듯해 보이는 결과"가 아니라, 실제로 필요한 문서를 얼마나 빨리, 얼마나 정확하게 찾는지로 판단해야 합니다.

이 글은 RAG와 검색 시스템에서 가장 자주 쓰는 retrieval metrics를 정리하고, 어떤 지표를 어디에 써야 하는지 설명합니다.

![Retrieval quality metrics workflow](/images/retrieval-quality-metrics-workflow-2026.svg)

## 개요

Retrieval quality metrics는 검색 시스템이 관련 문서를 얼마나 잘 찾아오는지 측정하는 지표입니다.

실무에서는 보통 아래 네 가지를 많이 봅니다.

- Precision@K
- Recall@K
- MRR
- nDCG

## 왜 중요한가

RAG 품질은 생성 모델보다 검색 단계에서 먼저 무너지는 경우가 많습니다.

- 관련 문서가 검색되지 않으면 답변이 틀립니다.
- 관련 문서는 찾았지만 순서가 나쁘면 상위 결과만 읽는 시스템에서 손해를 봅니다.
- 검색 품질이 낮으면 reranking과 generation도 같이 흔들립니다.

## 평가 지표와 방법

| 지표 | 의미 | 실무에서 볼 때 |
|---|---|---|
| Precision@K | 상위 K개 중 관련 문서 비율 | 너무 많은 오탐을 잡는지 확인 |
| Recall@K | 관련 문서를 상위 K개 안에서 얼마나 찾는지 | RAG에서 가장 중요하게 보는 축 |
| MRR | 첫 관련 문서가 얼마나 앞에 오는지 | 순위 품질 확인 |
| nDCG | 순위와 관련도를 함께 반영 | 랭킹 품질 비교 |

검색 구조를 설계할 때는 [Hybrid Search 실무 가이드](/posts/hybrid-search-practical-guide/)와 [Reranking 실무 가이드](/posts/reranking-practical-guide/)를 같이 보는 게 좋습니다.

## 운영 팁

- Recall과 Precision을 동시에 보십시오.
- K를 하나로 고정하지 말고 5, 10, 20으로 나눠서 보십시오.
- 질문 유형별로 지표를 분리하십시오.
- reranking 전후를 반드시 비교하십시오.
- 지표가 좋아져도 실제 답변 품질이 개선되는지 확인하십시오.

## 체크리스트

- 평가용 질문셋이 실제 검색 패턴을 반영하는가
- 관련 문서 라벨이 있는가
- Recall@K와 MRR을 함께 보는가
- reranking 전후 차이를 확인하는가
- 하이브리드 검색과 단일 벡터 검색을 비교하는가

## 결론

Retrieval metrics는 RAG 품질의 바닥을 보는 도구입니다. 검색이 무너지면 생성도 의미가 없습니다.

먼저 Recall@K와 MRR부터 잡고, 이후에 nDCG와 reranking 비교를 붙이는 순서가 가장 실용적입니다.

## 함께 읽으면 좋은 글

- [Hybrid Search란 무엇인가: 2026년 키워드 검색과 벡터 검색을 함께 쓰는 실무 가이드](/posts/hybrid-search-practical-guide/)
- [Reranking이란 무엇인가: 검색 결과 품질을 끌어올리는 실무 가이드](/posts/reranking-practical-guide/)
- [RAG 평가란 무엇인가: 검색 품질과 답변 품질을 함께 보는 실무 가이드](/posts/rag-evaluation-practical-guide/)
- [RAG Ops 실무 가이드: 검색 품질과 운영 지표를 함께 관리하는 방법](/posts/rag-ops-practical-guide/)

