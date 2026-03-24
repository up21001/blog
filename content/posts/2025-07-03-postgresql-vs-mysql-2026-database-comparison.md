---
title: "PostgreSQL vs MySQL 2026 — 어떤 데이터베이스를 선택해야 할까?"
date: 2025-07-03T08:00:00+09:00
lastmod: 2025-07-06T08:00:00+09:00
description: "PostgreSQL과 MySQL을 2026년 기준으로 성능, JSON 지원, 확장성, 비용, 사용 사례 측면에서 비교합니다. 프로젝트 유형별 최적 선택 기준을 실무 관점에서 정리합니다."
slug: "postgresql-vs-mysql-2026-database-comparison"
categories: ["software-dev"]
tags: ["PostgreSQL", "MySQL", "데이터베이스", "SQL", "백엔드"]
series: []
draft: false
---

데이터베이스를 선택할 때 가장 많이 맞닥뜨리는 질문이 "PostgreSQL을 써야 할까요, MySQL을 써야 할까요?"입니다. 13년간 다양한 규모의 서비스를 운영하면서 두 데이터베이스를 모두 실무에서 써봤습니다. 2026년 현재도 이 질문은 여전히 유효하며, 정답은 프로젝트 맥락에 따라 달라집니다.

이 글에서는 성능, JSON 지원, 확장성, 라이선스, 실제 사용 사례를 기준으로 두 DB를 꼼꼼히 비교합니다.

![PostgreSQL vs MySQL 2026 비교](/images/postgresql-vs-mysql-2026.svg)

## 두 데이터베이스의 역사와 철학

**PostgreSQL**은 1986년 UC 버클리에서 시작된 프로젝트로, "객체 관계형 데이터베이스"라는 정체성을 유지하고 있습니다. SQL 표준 준수와 기능 완전성을 최우선으로 삼습니다. PostgreSQL License는 MIT에 가까운 자유도를 제공하며 상용 제품에도 제약 없이 사용할 수 있습니다.

**MySQL**은 1995년 MySQL AB가 개발하고 현재는 Oracle이 소유합니다. 빠른 읽기 성능과 쉬운 운영을 설계 목표로 삼았습니다. GPL과 상용 라이선스의 이중 구조를 가지며, Oracle의 소유권에 불안감을 느낀 커뮤니티가 MariaDB를 분기했습니다.

두 DB 모두 오랜 역사와 방대한 레퍼런스를 갖추고 있습니다. 어느 쪽을 골라도 "망하는" 선택은 아닙니다. 다만 특정 요구사항에서는 명확한 차이가 있습니다.

## 성능 비교

### 읽기 집약적 OLTP

단순 PK 기반 단일 행 조회처럼 극도로 단순한 읽기 작업에서는 MySQL이 PostgreSQL보다 미세하게 빠른 경우가 있습니다. 이 차이는 벤치마크에서 보이지만 실제 애플리케이션에서는 인덱스 설계와 쿼리 최적화가 훨씬 큰 영향을 미칩니다.

### 복잡한 쿼리와 조인

조인이 많고 서브쿼리가 중첩된 분석 쿼리에서는 PostgreSQL의 쿼리 플래너가 MySQL보다 일관되게 우수합니다. PostgreSQL은 병렬 쿼리 실행, CTE(Common Table Expression) 최적화, 윈도우 함수 처리에서 강점을 발휘합니다.

```sql
-- PostgreSQL의 윈도우 함수 활용 예시
SELECT
  user_id,
  order_date,
  amount,
  SUM(amount) OVER (
    PARTITION BY user_id
    ORDER BY order_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_total
FROM orders;
```

MySQL 8.0부터 윈도우 함수를 지원하지만, 복잡한 쿼리에서 실행 계획의 안정성은 PostgreSQL이 앞섭니다.

### 쓰기 성능과 MVCC

두 DB 모두 MVCC(Multi-Version Concurrency Control)를 사용하지만 구현 방식이 다릅니다. MySQL(InnoDB)은 언두 로그 기반으로 MVCC를 구현하며, PostgreSQL은 테이블에 여러 버전의 행을 직접 저장합니다.

PostgreSQL 방식은 VACUUM 작업이 필요하지만 읽기 트랜잭션에서 잠금 없이 구 버전 데이터를 읽을 수 있어 높은 동시성 환경에서 안정적입니다.

## JSON 지원: PostgreSQL의 압도적 우위

JSON 데이터를 다루는 측면에서 PostgreSQL은 MySQL을 크게 앞섭니다.

### PostgreSQL JSONB

PostgreSQL은 `json`과 `jsonb` 두 타입을 제공합니다. `jsonb`는 바이너리 형식으로 저장되어 인덱싱과 연산이 훨씬 빠릅니다.

```sql
-- JSONB 컬럼 생성 및 GIN 인덱스
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name TEXT,
  attributes JSONB
);

CREATE INDEX idx_products_attrs ON products USING GIN (attributes);

-- JSON 경로 조회
SELECT * FROM products
WHERE attributes @> '{"color": "blue", "size": "L"}';

-- JSON 내부 값 추출
SELECT
  name,
  attributes->>'color' AS color,
  (attributes->>'price')::numeric AS price
FROM products
WHERE (attributes->>'price')::numeric > 10000;
```

GIN 인덱스를 사용하면 JSONB 컬럼 내부의 키-값 쌍을 인덱싱할 수 있어 복잡한 JSON 필터링도 빠르게 수행합니다.

### MySQL JSON

MySQL 5.7.8부터 JSON 컬럼을 지원합니다. 기본 JSON 저장 및 함수 조회는 가능하지만, 인덱싱이 제한적입니다. 함수형 인덱스(Generated Column)를 사용해 특정 JSON 경로에 인덱스를 걸 수 있지만, PostgreSQL의 GIN 인덱스처럼 동적으로 임의 키를 인덱싱하는 것은 불가능합니다.

JSON을 자주 조회·필터링하는 서비스라면 PostgreSQL이 훨씬 실용적입니다.

## 확장성: PostgreSQL 생태계의 강점

PostgreSQL의 가장 강력한 차별점 중 하나는 확장(Extension) 생태계입니다.

### 주목할 만한 PostgreSQL 확장

**PostGIS**: 지리 정보 처리를 위한 표준 확장입니다. 위도·경도 기반 거리 계산, 공간 인덱스, 지오펜싱 쿼리를 SQL로 처리합니다. 배달 서비스, 지도 앱, 부동산 플랫폼에서 필수적입니다.

```sql
-- PostGIS 예시: 반경 1km 이내 매장 조회
SELECT name, ST_Distance(location, ST_Point(127.027, 37.498)::geography) AS dist
FROM stores
WHERE ST_DWithin(location, ST_Point(127.027, 37.498)::geography, 1000)
ORDER BY dist;
```

**pgvector**: AI/ML 서비스에서 임베딩 벡터를 저장하고 유사도 검색을 수행합니다. ChatGPT 스타일 시맨틱 검색, RAG(Retrieval-Augmented Generation) 시스템에서 활발히 사용됩니다.

```sql
-- pgvector 예시: 코사인 유사도 검색
SELECT id, content, 1 - (embedding <=> '[0.1, 0.2, ...]'::vector) AS similarity
FROM documents
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

**TimescaleDB**: 시계열 데이터 처리를 위한 확장입니다. 하이퍼테이블, 연속 집계, 압축 기능을 제공합니다. IoT 센서 데이터, 로그, 메트릭 수집 서비스에 적합합니다.

MySQL은 이런 수준의 확장 생태계가 없습니다. 지리 정보나 벡터 검색이 필요하면 별도 서비스(Elasticsearch, Pinecone 등)를 추가해야 합니다.

## 복제와 고가용성

### PostgreSQL 복제

PostgreSQL은 스트리밍 복제(WAL 기반)와 논리 복제를 모두 지원합니다. Patroni, Repmgr 같은 오픈소스 HA 솔루션과 잘 통합됩니다.

- **스트리밍 복제**: 바이트 단위로 WAL을 전송해 스탠바이가 프라이머리와 거의 동일한 상태 유지
- **논리 복제**: 테이블 단위로 선택적 복제 가능, 버전 업그레이드 시 활용

### MySQL 복제

MySQL은 그룹 복제(Group Replication)와 InnoDB Cluster를 통해 HA를 구현합니다. Oracle이 적극 지원하는 MySQL Router와 함께 사용하면 자동 페일오버가 가능합니다.

MySQL Replication은 수십 년간 검증된 성숙도를 가지며, 특히 AWS RDS, Google Cloud SQL 같은 관리형 서비스에서 설정이 간편합니다.

## 클라우드 관리형 서비스 비교

| 서비스 | PostgreSQL | MySQL |
|---|---|---|
| AWS | RDS PostgreSQL, Aurora PostgreSQL | RDS MySQL, Aurora MySQL |
| Google Cloud | Cloud SQL for PostgreSQL, AlloyDB | Cloud SQL for MySQL |
| Azure | Azure Database for PostgreSQL (Flexible) | Azure Database for MySQL |
| Supabase | PostgreSQL 기반 (전용) | - |
| PlanetScale | - | MySQL 기반 (Vitess) |
| Neon | PostgreSQL 서버리스 | - |

Supabase와 Neon은 PostgreSQL 전용으로, 클라우드 네이티브 워크플로우를 원한다면 PostgreSQL 선택지가 더 다양합니다. PlanetScale은 MySQL을 기반으로 한 서버리스 DB로, 글로벌 샤딩과 브랜치 워크플로우를 제공합니다.

## 라이선스와 비용

PostgreSQL License는 BSD와 유사한 자유 라이선스입니다. 상용 제품에 PostgreSQL을 내장해도 소스 공개 의무가 없습니다.

MySQL의 GPL 라이선스는 MySQL을 포함한 소프트웨어를 배포할 때 소스 공개를 요구할 수 있습니다. SaaS는 GPL의 배포 조건에서 벗어날 수 있지만, 내장 소프트웨어 제품이라면 법무 검토가 필요합니다. 상용 라이선스는 Oracle에서 구매해야 합니다.

MySQL 대신 MariaDB를 사용하면 라이선스 우려를 덜 수 있습니다. MariaDB는 MySQL 5.5에서 분기되었으며 GPL이지만 Oracle 의존성이 없습니다.

## 사용 사례별 추천

### PostgreSQL을 선택해야 할 때

- **복잡한 쿼리와 분석 워크로드**: 조인, 윈도우 함수, CTE가 많은 서비스
- **JSON/반정형 데이터**: JSONB로 유연한 스키마를 관리해야 할 때
- **AI·ML 서비스**: pgvector로 임베딩 검색을 DB에서 직접 처리할 때
- **지리 정보 서비스**: PostGIS로 공간 데이터를 다룰 때
- **시계열 데이터**: TimescaleDB 확장이 필요할 때
- **라이선스 자유도**: 상용 제품에 내장하거나 소스 공개 없이 사용할 때
- **스타트업 · 신규 프로젝트**: 기술 부채 없이 시작한다면 PostgreSQL이 기본 선택

### MySQL을 선택해야 할 때

- **WordPress · Drupal 등 레거시 스택**: 이미 MySQL 기반 CMS 생태계가 구축된 경우
- **단순 CRUD 집약적 서비스**: 복잡한 분석이 없고 읽기 트래픽이 많을 때
- **PlanetScale 사용**: MySQL 기반의 서버리스·브랜치 워크플로우가 필요할 때
- **기존 MySQL 운영 팀**: 이미 MySQL DBA와 운영 도구가 갖춰진 경우
- **Aurora MySQL**: AWS에서 고성능 MySQL 호환 클러스터가 필요할 때

## 실무에서 겪은 이야기

과거 한 이커머스 프로젝트에서 MySQL을 쓰다가 JSON 필터링 성능 문제로 고생한 적이 있습니다. 상품 속성을 JSON으로 저장했는데, 특정 속성 조합으로 필터링하는 쿼리가 풀 스캔이 되는 문제였습니다. 결국 해당 서비스를 PostgreSQL로 마이그레이션하면서 GIN 인덱스를 적용했고, 같은 쿼리가 100배 이상 빨라졌습니다.

반면 수백만 명이 사용하는 커뮤니티 서비스에서는 MySQL을 10년째 운영 중인 팀이 있었습니다. 간단한 게시글·댓글 CRUD 중심 서비스였고, DBA 팀의 MySQL 노하우가 깊었습니다. 그 경우 굳이 PostgreSQL로 마이그레이션할 이유가 없었습니다.

## 결론

2026년 기준으로 새로운 프로젝트를 시작한다면 **PostgreSQL을 기본 선택으로 권장합니다.** 라이선스 자유도, 풍부한 확장 생태계, JSON 처리 능력, AI/ML 연동 측면에서 PostgreSQL이 앞서 있습니다. 특히 pgvector 덕분에 AI 기능을 추가할 때 별도 벡터 DB 없이 시작할 수 있다는 점은 큰 장점입니다.

MySQL은 이미 MySQL 생태계를 사용 중이거나, WordPress 같은 MySQL 의존 스택을 운영하거나, PlanetScale의 워크플로우가 필요한 경우에 좋은 선택입니다.

어느 쪽이든 올바른 인덱스 설계, 쿼리 최적화, 커넥션 풀 관리가 DB 선택보다 성능에 더 큰 영향을 미친다는 사실을 잊지 마십시오. 도구를 잘 쓰는 것이 도구를 잘 고르는 것만큼 중요합니다.
