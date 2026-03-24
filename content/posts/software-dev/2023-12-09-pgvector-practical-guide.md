---
title: "pgvector란 무엇인가: 2026년 PostgreSQL 벡터 확장 실무 가이드"
date: 2023-12-09T12:34:00+09:00
lastmod: 2023-12-11T12:34:00+09:00
description: "pgvector가 무엇인지, PostgreSQL 안에서 embeddings와 similarity search를 어떻게 운영하는지, AI와 vectors를 Postgres로 묶는 이유를 2026년 기준으로 정리한 실무 가이드."
slug: "pgvector-practical-guide"
categories: ["software-dev"]
tags: ["pgvector", "PostgreSQL", "Vector Extension", "Embeddings", "Similarity Search", "RAG", "AI with Postgres"]
series: ["Vector Database 2026"]
featureimage: "/images/pgvector-workflow-2026.svg"
draft: false
---

`pgvector`는 PostgreSQL에 벡터 검색 기능을 추가하는 확장입니다. 새로운 데이터베이스를 또 하나 도입하기보다, 이미 쓰고 있는 `PostgreSQL` 안에 `embeddings`와 `similarity search`를 함께 넣고 싶을 때 가장 먼저 검토하게 되는 선택지입니다.

핵심은 단순합니다. `AI & vectors with Postgres`입니다. 테이블, 조인, 트랜잭션, 인덱스, 권한 모델을 그대로 활용하면서 벡터 검색을 얹을 수 있습니다. 운영 관점에서는 데이터가 한 곳에 모인다는 점이 강력합니다.

![pgvector 워크플로우](/images/pgvector-workflow-2026.svg)

## 이런 분께 추천합니다
- 이미 PostgreSQL을 핵심 DB로 쓰고 있는 팀
- 벡터 데이터와 관계형 데이터를 같이 다뤄야 하는 경우
- 별도 vector DB를 도입하기 전에 빠르게 시작하고 싶은 경우
- RAG 기능을 기존 백엔드에 자연스럽게 붙이고 싶은 경우

## 핵심은 무엇인가

pgvector는 벡터를 PostgreSQL의 한 데이터 타입처럼 다룰 수 있게 해줍니다. 그래서 일반적인 애플리케이션 로직과 벡터 검색이 같은 DB 경계 안에서 움직입니다.

| 핵심 요소 | 의미 |
|---|---|
| PostgreSQL extension | 기존 Postgres에 기능 추가 |
| Embeddings | 텍스트/이미지 등의 벡터 저장 |
| Similarity search | 가까운 벡터를 빠르게 조회 |
| SQL | 익숙한 쿼리 언어로 제어 |
| Indexes | 성능 튜닝에 HNSW, IVFFlat 활용 |
| AI with Postgres | 관계형 데이터와 벡터를 한곳에서 관리 |

## 왜 지금 중요한가

AI 기능은 대개 기존 제품 안에 붙습니다. 이때 새로운 벡터 DB를 추가하는 것보다, 이미 안정적으로 운영 중인 PostgreSQL에 벡터 기능을 얹는 편이 훨씬 단순할 수 있습니다.

pgvector는 특히 다음 상황에서 유용합니다.

- 운영하는 시스템이 이미 Postgres 중심이다
- 벡터 검색 결과를 사용자, 문서, 권한, 상태와 함께 조인해야 한다
- 초기에는 간단하게 시작하고 나중에 확장 여부를 판단하고 싶다

## 어떤 팀에 잘 맞는가

pgvector는 `DB를 하나 줄이고 싶은 팀`에 잘 맞습니다. 별도의 vector DB를 붙이지 않아도 되므로, 데이터 이동과 동기화 비용이 줄어듭니다.

- 제품 데이터가 이미 PostgreSQL에 있다
- 문서 검색 결과를 SQL로 필터링해야 한다
- 벡터 검색과 CRUD를 한 트랜잭션 흐름 안에서 다루고 싶다
- 백엔드 팀이 SQL 기반 운영에 익숙하다

반대로, 초대규모 벡터 검색이나 전용 search engine 수준의 기능이 필요하면 별도 vector DB와 비교가 필요합니다.

## 실무 도입 시 체크할 점
1. 현재 Postgres 용량과 쿼리 부하를 먼저 확인합니다.
2. embedding 컬럼과 인덱스 전략을 데이터 크기에 맞게 설계합니다.
3. similarity search와 기존 SQL 필터의 조합을 미리 테스트합니다.
4. 쓰기 빈도가 높으면 인덱스 유지 비용도 같이 봅니다.
5. 검색 품질은 chunking, embedding model, metadata 설계가 좌우합니다.

![pgvector 선택 흐름](/images/pgvector-choice-flow-2026.svg)

## 장점과 주의점

장점:

- 이미 쓰는 PostgreSQL에 그대로 붙일 수 있습니다.
- 관계형 데이터와 벡터를 한 DB에서 관리할 수 있습니다.
- SQL과 기존 운영 도구를 계속 활용할 수 있습니다.
- 도입 장벽이 낮고 실무 적용이 빠릅니다.

주의점:

- PostgreSQL이 만능은 아닙니다.
- 데이터와 트래픽이 커질수록 전용 vector DB와 비교가 필요합니다.
- 인덱스와 쿼리 튜닝을 소홀히 하면 성능이 쉽게 떨어질 수 있습니다.

## 검색형 키워드
- `pgvector`
- `pgvector PostgreSQL`
- `Postgres vector search`
- `embeddings in PostgreSQL`
- `AI with Postgres`

## 한 줄 결론

pgvector는 `이미 PostgreSQL을 쓰는 팀이 AI 벡터 검색을 가장 현실적으로 시작하는 방법`입니다.

## 참고 자료

- pgvector GitHub: https://github.com/pgvector/pgvector
- pgvector docs: https://github.com/pgvector/pgvector/tree/master
- PostgreSQL extension docs: https://www.postgresql.org/docs/current/external-extensions.html

## 함께 읽으면 좋은 글

- [Supabase란 무엇인가: 2026년 개발자용 실무 가이드](/posts/supabase-practical-guide/)
- [PostgreSQL과 AI 벡터 검색을 함께 설계하는 방법](/posts/vector-database-comparison-2026-v2/)
- [RAG란 무엇인가: 2026년 검색 증강 생성 완전 가이드](/posts/rag-retrieval-augmented-generation-complete-guide/)
