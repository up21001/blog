---
title: "Chroma vs Pinecone vs Weaviate — 벡터 데이터베이스 완전 비교 2026"
date: 2024-10-19T10:17:00+09:00
lastmod: 2024-10-19T10:17:00+09:00
description: "2026년 기준 주요 벡터 데이터베이스 Chroma, Pinecone, Weaviate의 특징, 가격, 성능, 코드 예시를 실무 관점에서 비교하고 선택 기준을 제시합니다."
slug: "vector-database-comparison-chroma-pinecone-weaviate"
categories: ["ai-automation"]
tags: ["벡터 DB", "Chroma", "Pinecone", "Weaviate", "RAG"]
series: []
draft: false
---

RAG 시스템을 구축할 때 가장 많이 받는 질문이 "벡터 DB는 뭘 써야 하나요?"입니다. 정답은 없지만 틀린 선택은 분명히 있습니다. 프로덕션에 Chroma를 쓰거나, 로컬 테스트에 Pinecone을 쓰는 식으로 말입니다. 이 글에서는 2026년 현재 가장 많이 쓰이는 세 가지 벡터 DB를 실무 기준으로 비교합니다.

필자는 세 가지 모두 실제 프로젝트에서 사용해봤습니다. 각각의 강점과 한계를 코드와 함께 솔직하게 정리합니다.

![벡터 데이터베이스 비교표](/images/vector-database-comparison-2026.svg)

## 벡터 DB가 필요한 이유

일반적인 관계형 DB(PostgreSQL, MySQL)는 정확한 일치 검색에 최적화되어 있습니다. `WHERE name = '김철수'`처럼 정확한 값을 찾는 쿼리에서는 탁월합니다. 하지만 "이 문장과 의미가 비슷한 문서를 찾아줘"라는 요청은 처리할 수 없습니다.

벡터 DB는 텍스트, 이미지, 오디오를 수백~수천 차원의 숫자 배열(벡터)로 변환해 저장하고, 벡터 간 거리(코사인 유사도, L2 거리 등)로 의미적 유사성을 검색합니다.

```python
# 전통 DB: 정확 매칭
SELECT * FROM documents WHERE content LIKE '%머신러닝%'

# 벡터 DB: 의미 기반 검색
query_vector = embed("딥러닝과 신경망의 차이는?")
results = vectordb.search(query_vector, k=5)
# → "머신러닝" 언급 없어도 의미적으로 유사한 문서 반환
```

## Chroma — 로컬 개발의 사실상 표준

### 특징

Chroma는 Python에서 `pip install chromadb` 한 줄로 설치하고 코드 몇 줄만으로 시작할 수 있는 임베디드 벡터 DB입니다. SQLite처럼 별도 서버 없이 로컬 파일로 동작하며, 인메모리 모드도 지원합니다.

2023년 오픈소스로 공개된 이후 RAG 프로토타이핑의 사실상 표준이 됐습니다. LangChain, LlamaIndex 튜토리얼의 90% 이상이 Chroma를 기본 예시로 사용합니다.

### 설치 및 기본 사용법

```bash
pip install chromadb
```

```python
import chromadb
from chromadb.utils import embedding_functions

# 클라이언트 생성 (로컬 파일 저장)
client = chromadb.PersistentClient(path="./chroma_data")

# OpenAI 임베딩 함수 설정
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="your-api-key",
    model_name="text-embedding-3-small"
)

# 컬렉션 생성
collection = client.get_or_create_collection(
    name="company_docs",
    embedding_function=openai_ef,
    metadata={"hnsw:space": "cosine"}  # 코사인 유사도 사용
)

# 문서 추가
collection.add(
    documents=[
        "연차 휴가는 15일입니다.",
        "재택근무는 주 3일까지 가능합니다.",
        "병가는 의사 진단서 제출 시 무제한입니다."
    ],
    metadatas=[
        {"source": "hr_policy.pdf", "page": 1},
        {"source": "work_policy.pdf", "page": 3},
        {"source": "hr_policy.pdf", "page": 5}
    ],
    ids=["doc1", "doc2", "doc3"]
)

# 검색
results = collection.query(
    query_texts=["휴가는 몇 일인가요?"],
    n_results=3,
    where={"source": "hr_policy.pdf"}  # 메타데이터 필터
)

for doc, distance in zip(results["documents"][0], results["distances"][0]):
    print(f"[유사도: {1-distance:.3f}] {doc}")
```

### LangChain 연동

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 문서에서 직접 생성
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db",
    collection_name="my_collection"
)

# 기존 DB 로드
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="my_collection"
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
```

### 장단점

**장점:**
- 설치 및 시작이 가장 쉬움
- 완전 무료 (오픈소스)
- 로컬 파일 기반, 인프라 불필요
- 메타데이터 필터 지원
- Python 네이티브 API

**단점:**
- 수백만 벡터 이상에서 성능 저하
- 분산/클러스터링 지원 미흡
- 프로덕션 SLA 보장 없음
- 동시성 처리 제한

**권장 사용 시나리오:** 로컬 개발, PoC, 개인 프로젝트, 소규모 문서(10만 건 이하)

## Pinecone — 관리형 프로덕션의 선택지

### 특징

Pinecone은 완전 관리형(Fully Managed) 벡터 DB 서비스입니다. 인프라 설정, 스케일링, 모니터링을 모두 Pinecone이 처리합니다. 개발자는 데이터 삽입과 쿼리에만 집중하면 됩니다.

2026년 기준 무료 플랜은 2개 인덱스, 100만 벡터(1536 차원 기준)를 제공합니다. 소규모 프로젝트는 무료로 충분합니다.

### 설치 및 기본 사용법

```bash
pip install pinecone-client
```

```python
from pinecone import Pinecone, ServerlessSpec
import time

# 클라이언트 초기화
pc = Pinecone(api_key="your-pinecone-api-key")

# 인덱스 생성 (처음 한 번만)
index_name = "company-rag"

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # text-embedding-3-small 차원수
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
    # 인덱스 준비 대기
    while not pc.describe_index(index_name).status["ready"]:
        time.sleep(1)

index = pc.Index(index_name)

# 벡터 삽입 (배치 처리 권장)
vectors_to_upsert = [
    {
        "id": "doc1",
        "values": [0.1, 0.2, ...],  # 1536개 float
        "metadata": {
            "text": "연차 휴가는 15일입니다.",
            "source": "hr_policy.pdf",
            "page": 1
        }
    },
    # ...
]

# 배치 삽입 (한 번에 최대 100개)
batch_size = 100
for i in range(0, len(vectors_to_upsert), batch_size):
    batch = vectors_to_upsert[i:i+batch_size]
    index.upsert(vectors=batch)

# 검색
query_vector = embed("휴가 정책")  # 실제 임베딩 함수 호출

results = index.query(
    vector=query_vector,
    top_k=5,
    filter={"source": {"$eq": "hr_policy.pdf"}},  # 메타데이터 필터
    include_metadata=True
)

for match in results["matches"]:
    print(f"[점수: {match['score']:.3f}] {match['metadata']['text']}")
```

### LangChain 연동

```python
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 문서에서 직접 생성
vectorstore = PineconeVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings,
    index_name="company-rag"
)

# 기존 인덱스 연결
vectorstore = PineconeVectorStore(
    index=pc.Index("company-rag"),
    embedding=embeddings,
    text_key="text"
)
```

### 가격 구조 (2026년 기준)

| 플랜 | 인덱스 수 | 스토리지 | 월 비용 |
|------|-----------|---------|--------|
| 무료 | 2개 | 1M 벡터 | $0 |
| Starter | 5개 | 5M 벡터 | ~$70 |
| Standard | 무제한 | 사용량 기반 | ~$0.096/시간 |
| Enterprise | 맞춤 | 무제한 | 별도 문의 |

### 장단점

**장점:**
- 설정 없이 즉시 사용
- 수억 개 벡터도 안정적 처리
- 낮은 지연시간(~10ms)
- 자동 스케일링, 고가용성
- 강력한 메타데이터 필터

**단점:**
- 대규모에서 비용 증가
- 데이터가 외부 클라우드에 저장
- 벤더 락인 위험
- 온프레미스 불가

**권장 사용 시나리오:** 스타트업 프로덕션, 인프라 팀이 없는 소규모 팀, 빠른 출시가 우선인 경우

## Weaviate — 오픈소스 + 풍부한 기능

### 특징

Weaviate는 Go로 작성된 오픈소스 벡터 DB입니다. GraphQL API, 하이브리드 검색(BM25 + 벡터), 멀티모달 지원, 모듈 시스템이 특징입니다. Docker로 셀프 호스팅하거나 Weaviate Cloud를 사용할 수 있습니다.

```bash
# Docker로 로컬 실행
docker run -d \
  -p 8080:8080 \
  -p 50051:50051 \
  -e QUERY_DEFAULTS_LIMIT=20 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  -v weaviate_data:/var/lib/weaviate \
  cr.weaviate.io/semitechnologies/weaviate:latest
```

### 기본 사용법

```bash
pip install weaviate-client
```

```python
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery

# 클라이언트 연결
client = weaviate.connect_to_local()

# 스키마(컬렉션) 정의
client.collections.create(
    name="CompanyDoc",
    vectorizer_config=Configure.Vectorizer.text2vec_openai(
        model="text-embedding-3-small"
    ),
    properties=[
        Property(name="content", data_type=DataType.TEXT),
        Property(name="source", data_type=DataType.TEXT),
        Property(name="page", data_type=DataType.INT),
        Property(name="department", data_type=DataType.TEXT),
    ]
)

collection = client.collections.get("CompanyDoc")

# 데이터 삽입 (배치)
with collection.batch.dynamic() as batch:
    for chunk in chunks:
        batch.add_object({
            "content": chunk.page_content,
            "source": chunk.metadata.get("source", ""),
            "page": chunk.metadata.get("page", 0),
            "department": chunk.metadata.get("department", "general")
        })

# 벡터 유사도 검색
results = collection.query.near_text(
    query="휴가 정책",
    limit=5,
    return_metadata=MetadataQuery(distance=True)
)

for obj in results.objects:
    print(f"[거리: {obj.metadata.distance:.3f}] {obj.properties['content'][:100]}")

# 하이브리드 검색 (벡터 + BM25)
results = collection.query.hybrid(
    query="연차 휴가 일수",
    alpha=0.7,   # 0=순수 BM25, 1=순수 벡터
    limit=5
)

# 메타데이터 필터
from weaviate.classes.query import Filter

results = collection.query.near_text(
    query="휴가",
    limit=5,
    filters=Filter.by_property("department").equal("HR")
)

client.close()
```

### LangChain 연동

```python
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain_openai import OpenAIEmbeddings
import weaviate

client = weaviate.connect_to_local()
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vectorstore = WeaviateVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings,
    client=client,
    index_name="CompanyDoc",
    text_key="content"
)

# 하이브리드 검색 retriever
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5}
)
```

### 장단점

**장점:**
- 오픈소스 (완전 무료 셀프 호스팅)
- 내장 하이브리드 검색 (BM25 + 벡터)
- GraphQL API로 복잡한 쿼리 가능
- 멀티모달 지원 (텍스트 + 이미지)
- 모듈 시스템 (자동 임베딩, 리랭킹)
- 강력한 필터링

**단점:**
- 학습 곡선이 높음
- Docker/K8s 운영 부담
- 커뮤니티가 Chroma보다 작음
- 설정이 복잡

**권장 사용 시나리오:** 온프레미스 필수 환경, 복잡한 메타데이터 필터, 하이브리드 검색이 중요한 경우, 멀티모달 RAG

## 상세 비교표

| 항목 | Chroma | Pinecone | Weaviate |
|------|--------|----------|---------|
| 배포 방식 | 로컬/임베디드 | 완전 관리형 SaaS | 셀프/클라우드 |
| 오픈소스 | O | X | O |
| 무료 한도 | 무제한 (로컬) | 100만 벡터 | 무제한 (셀프) |
| 설치 난이도 | 매우 쉬움 | 쉬움 | 중간 (Docker) |
| 확장성 | 소규모 | 대규모 | 대규모 |
| 하이브리드 검색 | 외부 구현 | 외부 구현 | 내장 |
| 멀티모달 | X | X | O |
| GraphQL API | X | X | O |
| 한국어 지원 | 임베딩 모델 의존 | 임베딩 모델 의존 | 임베딩 모델 의존 |
| 지연시간 | 로컬 속도 | ~10ms | ~20ms |
| 프로덕션 SLA | X | 99.99% | 셀프 의존 |

## 추가로 알아두면 좋은 벡터 DB

### FAISS (Facebook AI Similarity Search)

```python
import faiss
import numpy as np

dimension = 1536
index = faiss.IndexFlatL2(dimension)  # L2 거리 기반

# GPU 버전
res = faiss.StandardGpuResources()
gpu_index = faiss.index_cpu_to_gpu(res, 0, index)

vectors = np.random.random((10000, dimension)).astype('float32')
index.add(vectors)

query = np.random.random((1, dimension)).astype('float32')
distances, indices = index.search(query, k=5)
```

순수 ANN(Approximate Nearest Neighbor) 라이브러리입니다. DB 기능(CRUD, 필터)은 없고 검색 성능만 최고입니다. 별도 메타데이터 저장이 필요합니다.

### Qdrant

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(url="http://localhost:6333")

client.create_collection(
    collection_name="company_docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

client.upsert(
    collection_name="company_docs",
    points=[
        PointStruct(id=1, vector=[...], payload={"text": "내용", "source": "doc.pdf"})
    ]
)
```

Rust로 작성된 고성능 오픈소스 벡터 DB입니다. 메모리 효율이 좋고 필터 성능이 탁월합니다. 최근 RAG 커뮤니티에서 Chroma 대체재로 주목받고 있습니다.

## 선택 가이드 — 실무 결정 기준

프로젝트 단계와 요구사항에 따른 권장 선택입니다.

**Phase 1 (프로토타입, 1~4주):**
Chroma를 사용합니다. 설치가 빠르고 코드가 단순합니다. 나중에 마이그레이션도 어렵지 않습니다.

**Phase 2 (소규모 프로덕션, 팀 2~5인):**
인프라 팀이 없으면 Pinecone, 데이터 보안이 중요하면 Qdrant 셀프호스팅을 선택합니다.

**Phase 3 (대규모 프로덕션):**
- 검색 복잡도 낮음: Pinecone
- 하이브리드 검색 필수: Weaviate
- 비용 최소화: Qdrant + K8s
- GPU 서버 보유: FAISS + 자체 메타데이터 DB

**온프레미스 필수 환경:**
Weaviate 또는 Qdrant를 Docker/K8s로 셀프 호스팅합니다. Chroma는 단일 노드 한계로 권장하지 않습니다.

## 마이그레이션 팁

처음 선택한 벡터 DB에서 이전해야 할 때는 임베딩 벡터를 재사용할 수 있습니다. 동일한 임베딩 모델을 사용한다면 벡터를 추출해서 새 DB에 삽입하면 됩니다.

```python
# Chroma에서 모든 벡터 추출
collection = chroma_client.get_collection("my_docs")
all_data = collection.get(include=["embeddings", "documents", "metadatas"])

# Pinecone으로 이전
for i, (emb, doc, meta) in enumerate(zip(
    all_data["embeddings"],
    all_data["documents"],
    all_data["metadatas"]
)):
    pinecone_index.upsert(vectors=[{
        "id": all_data["ids"][i],
        "values": emb,
        "metadata": {**meta, "text": doc}
    }])
```

## 마치며

2026년 기준 RAG 프로젝트의 일반적인 선택은 이렇습니다. 개인 프로젝트와 프로토타입은 Chroma, 빠른 프로덕션 배포는 Pinecone, 온프레미스나 복잡한 쿼리는 Weaviate 혹은 Qdrant입니다. 벡터 DB는 교체 비용이 생각보다 낮기 때문에 처음부터 완벽한 선택을 고집하기보다 일단 시작하고 필요에 따라 이전하는 전략이 현실적입니다.
