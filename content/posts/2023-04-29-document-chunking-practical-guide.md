---
title: "Document Chunking이란 무엇인가: 2026년 청킹 전략을 고르는 실무 가이드"
date: 2023-04-29T08:00:00+09:00
lastmod: 2023-04-29T08:00:00+09:00
description: "고정 길이, 의미 기반, 계층형 청킹을 비교하고 문서 구조에 맞는 chunk 전략을 선택하는 기준을 설명합니다."
slug: "document-chunking-practical-guide"
categories: ["software-dev"]
tags: ["RAG", "Chunking", "Document Processing", "Embeddings", "Hybrid Search", "Qdrant", "RAG Ops"]
series: ["RAG Pipeline 2026"]
featureimage: "/images/document-chunking-workflow-2026.svg"
draft: true
---

Document Chunking은 RAG 품질을 좌우하는 가장 현실적인 설계 포인트 중 하나입니다. 같은 문서라도 어떻게 나누느냐에 따라 검색 결과와 응답 품질이 크게 달라집니다.

이 글에서는 고정 길이, 의미 기반, 계층형 청킹을 비교하고, [RAG 인덱싱 파이프라인](/posts/rag-indexing-pipeline-practical-guide/), [Hybrid Search](/posts/hybrid-search-practical-guide/), [임베딩 모델 선택](/posts/embedding-model-selection-practical-guide/), [RAG Ops](/posts/rag-ops-practical-guide/)와 어떻게 연결되는지 설명합니다.

![Document chunking workflow](/images/document-chunking-workflow-2026.svg)

## 개요

청킹은 문서를 검색 가능한 단위로 자르는 작업입니다. 하지만 단순히 길이만 줄이는 작업으로 보면 안 됩니다. 문단, 제목, 코드 블록, 표, 리스트 같은 구조를 유지해야 검색 결과가 더 잘 맞습니다.

좋은 청킹은 검색 recall과 precision을 동시에 올리고, 불필요한 토큰 낭비를 줄여 비용도 낮춥니다.

## 왜 중요한가

- 너무 큰 chunk는 질문과 무관한 문장까지 같이 들어갑니다.
- 너무 작은 chunk는 맥락이 끊겨 답변이 빈약해집니다.
- overlap이 과하면 비용이 증가합니다.
- 구조를 무시하면 코드, 정책 문서, 매뉴얼에서 품질이 급격히 떨어집니다.

결국 청킹은 embedding 품질보다 앞단에서 품질을 결정하는 필터입니다.

## 파이프라인 설계

대표적인 설계 순서는 다음과 같습니다.

1. 문서 형식을 파악합니다.
2. 제목과 섹션 구조를 추출합니다.
3. 문서 유형에 맞는 splitter를 선택합니다.
4. chunk size와 overlap을 조정합니다.
5. 메타데이터를 붙입니다.
6. 샘플 쿼리로 결과를 검증합니다.

![Document chunking choice flow](/images/document-chunking-choice-flow-2026.svg)

### 전략 선택

- 고정 길이: 단순 문서, 대량 처리, 빠른 배치에 적합합니다.
- 의미 기반: 섹션 경계가 중요한 기술 문서에 적합합니다.
- 계층형: 긴 정책 문서, 매뉴얼, 책형 문서에 적합합니다.

실무에서는 하나만 고정하지 않고, 문서 타입별로 splitter를 분리하는 방식이 더 안정적입니다. 이때 [RAG 데이터 신선도](/posts/rag-data-freshness-practical-guide/)가 높아질수록 재청킹 빈도도 같이 증가하므로, 운영 비용까지 같이 봐야 합니다.

## 아키텍처 도식

![Document chunking architecture](/images/document-chunking-architecture-2026.svg)

권장 구조는 아래와 같습니다.

- Parser가 원문을 정규화합니다.
- Structure extractor가 제목과 단락 경계를 찾습니다.
- Chunk policy engine이 문서 타입별 규칙을 적용합니다.
- Metadata enrich step이 출처와 권한을 붙입니다.
- Embedding worker가 chunk별 벡터를 생성합니다.
- Vector DB가 검색 단위로 저장합니다.

청킹은 임베딩 모델과 분리해서 생각하기 쉽지만 실제로는 같이 움직입니다. [임베딩 모델 선택](/posts/embedding-model-selection-practical-guide/)에서 모델 크기와 언어 성능을 바꾸면 chunk 길이도 다시 봐야 합니다.

## 체크리스트

- 문서 타입별 청킹 규칙이 분리되어 있는가
- 코드 블록과 표를 잘라먹지 않는가
- overlap이 실제 품질 향상에 기여하는가
- chunk 단위 메타데이터가 충분한가
- 재청킹이 필요한 문서 유형이 정의되어 있는가
- 샘플 쿼리로 청킹 품질을 검증하는가
- 운영 로그에서 chunk 길이 분포를 확인하는가

## 결론

청킹은 단순한 전처리가 아니라 검색 품질 엔진의 일부입니다. 문서 구조를 보존하면서 검색 단위를 만들어야 RAG 전체 흐름이 안정됩니다.

## 함께 읽으면 좋은 글

- [RAG 인덱싱 파이프라인이란 무엇인가](/posts/rag-indexing-pipeline-practical-guide/)
- [RAG 데이터 신선도란 무엇인가](/posts/rag-data-freshness-practical-guide/)
- [Hybrid Search란 무엇인가](/posts/hybrid-search-practical-guide/)
- [임베딩 모델 선택 가이드](/posts/embedding-model-selection-practical-guide/)
- [RAG 운영 체크리스트란 무엇인가](/posts/rag-operations-checklist-practical-guide/)

