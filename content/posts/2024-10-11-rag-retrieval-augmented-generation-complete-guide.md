---
title: "RAG(Retrieval-Augmented Generation) 완전 가이드 — 나만의 AI 지식베이스 만들기"
date: 2024-10-11T08:00:00+09:00
lastmod: 2024-10-12T08:00:00+09:00
description: "RAG 개념과 아키텍처부터 Python LangChain 구현, 벡터 DB 선택, 청킹 전략, 실전 사내 문서 Q&A 챗봇 예시까지 한 번에 정리한 완전 가이드입니다."
slug: "rag-retrieval-augmented-generation-complete-guide"
categories: ["ai-automation"]
tags: ["RAG", "벡터 데이터베이스", "임베딩", "AI 검색", "LangChain"]
series: []
draft: false
---

LLM(대형 언어 모델)은 강력하지만 결정적인 한계가 있습니다. 학습 시점 이후의 정보를 모르고, 사내 문서나 개인 데이터에는 접근할 수 없습니다. RAG(Retrieval-Augmented Generation)는 이 문제를 해결하는 현재 가장 실용적인 방법론입니다. 외부 지식베이스에서 관련 문서를 검색해 LLM의 답변 생성에 컨텍스트로 제공하는 방식으로, 할루시네이션을 줄이고 최신 정보 기반 답변을 만들어냅니다.

필자는 지난 2년간 사내 기술 문서 Q&A, 법률 계약서 검토 도구, 고객 지원 자동화 등 여러 RAG 시스템을 구축하면서 수많은 시행착오를 겪었습니다. 이 글은 그 경험을 바탕으로 RAG의 개념부터 실제 코드까지 한 번에 정리한 가이드입니다.

![RAG 아키텍처 다이어그램](/images/rag-complete-guide.svg)

## RAG란 무엇인가

RAG는 2020년 Meta AI가 발표한 논문 "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"에서 시작된 개념입니다. 핵심 아이디어는 단순합니다.

> LLM이 답변을 생성하기 전에, 외부 지식 저장소에서 관련 문서를 먼저 검색해 프롬프트에 포함시킨다.

기존 LLM 방식과 비교하면 차이가 명확합니다.

**기존 방식 (순수 LLM):**
```
사용자: "우리 회사 휴가 정책이 어떻게 되나요?"
LLM: "저는 귀사의 내부 정책을 알지 못합니다." (또는 틀린 정보 생성)
```

**RAG 방식:**
```
1. "우리 회사 휴가 정책" → 벡터 DB에서 관련 HR 문서 검색
2. 검색된 문서 + 질문 → LLM에 전달
3. LLM: "인사 규정 3조에 따르면 연차는 15일이며..." (정확한 출처 기반 답변)
```

## RAG 아키텍처 두 가지 흐름

RAG 시스템은 크게 두 가지 파이프라인으로 나뉩니다.

### 1. 인덱싱 파이프라인 (오프라인)

문서를 벡터로 변환해 저장하는 사전 작업입니다.

```
문서 로드 → 청킹(분할) → 임베딩 생성 → 벡터 DB 저장
```

### 2. 쿼리 파이프라인 (온라인)

사용자 질문에 실시간으로 응답하는 흐름입니다.

```
사용자 질문 → 임베딩 변환 → 벡터 DB 검색(TOP-K) → LLM 생성 → 답변
```

## Python + LangChain으로 RAG 구현하기

### 환경 설정

```bash
pip install langchain langchain-openai langchain-community chromadb pypdf
```

### 1단계: 문서 로드 및 청킹

```python
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# PDF 파일 로드
loader = DirectoryLoader("./docs", glob="**/*.pdf", loader_cls=PyPDFLoader)
documents = loader.load()

print(f"로드된 문서 수: {len(documents)}")

# 청킹 설정
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,       # 청크 크기 (토큰 기준)
    chunk_overlap=200,     # 청크 간 겹침 (문맥 유지)
    separators=["\n\n", "\n", ".", "!", "?", ",", " "]
)

chunks = text_splitter.split_documents(documents)
print(f"생성된 청크 수: {len(chunks)}")
```

### 2단계: 임베딩 생성 및 벡터 DB 저장

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import os

os.environ["OPENAI_API_KEY"] = "your-api-key"

# 임베딩 모델 설정
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Chroma 벡터 DB에 저장
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

print("벡터 DB 저장 완료")
```

### 3단계: RAG 체인 구성

```python
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# LLM 설정
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 커스텀 프롬프트
prompt_template = """다음 컨텍스트를 바탕으로 질문에 답변해주세요.
컨텍스트에 없는 내용은 "해당 정보를 찾을 수 없습니다"라고 답변하세요.

컨텍스트:
{context}

질문: {question}

답변:"""

PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]
)

# RAG 체인 생성
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}  # TOP-5 문서 검색
    ),
    chain_type_kwargs={"prompt": PROMPT},
    return_source_documents=True  # 출처 반환
)

# 실행
result = qa_chain.invoke({"query": "휴가 정책이 어떻게 되나요?"})
print("답변:", result["result"])
print("출처:", [doc.metadata for doc in result["source_documents"]])
```

## 청킹 전략 — 가장 중요한 부분

RAG 품질의 60% 이상은 청킹 전략에 달려 있습니다. 잘못된 청킹은 관련 정보를 쪼개거나 무관한 내용을 묶어버립니다.

### Fixed-size Chunking

가장 단순한 방식으로, 고정된 토큰 수로 분할합니다.

```python
from langchain.text_splitter import CharacterTextSplitter

splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=500,
    chunk_overlap=50
)
```

**장점:** 구현 단순, 예측 가능
**단점:** 문장/단락 중간에서 분리될 수 있음

### Recursive Character Splitting

구분자 우선순위를 지정해 의미 단위로 분할합니다. 실전에서 가장 많이 사용합니다.

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

### Semantic Chunking

임베딩 유사도를 활용해 의미적으로 연관된 문장을 묶습니다. 품질은 높지만 느립니다.

```python
from langchain_experimental.text_splitter import SemanticChunker

splitter = SemanticChunker(
    embeddings=OpenAIEmbeddings(),
    breakpoint_threshold_type="percentile"
)
```

### 청킹 크기 선택 가이드

| 문서 유형 | 권장 청크 크기 | 오버랩 |
|-----------|---------------|--------|
| 짧은 FAQ | 200~300 토큰 | 50 |
| 일반 기술 문서 | 500~1000 토큰 | 100~200 |
| 법률/계약서 | 1000~1500 토큰 | 200~300 |
| 코드 파일 | 함수 단위 | 0 |

## 벡터 DB 선택 기준

RAG 시스템의 규모와 요구사항에 따라 벡터 DB를 선택해야 합니다.

### Chroma — 로컬 프로토타이핑

```python
from langchain_community.vectorstores import Chroma

# 인메모리 (임시)
vectorstore = Chroma(embedding_function=embeddings)

# 디스크 저장
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)
```

개인 프로젝트, PoC, 로컬 개발에 최적입니다. 설치가 `pip install chromadb` 한 줄이고 별도 서버가 필요 없습니다.

### Pinecone — 프로덕션

```python
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

pc = Pinecone(api_key="your-pinecone-api-key")
index = pc.Index("my-rag-index")

vectorstore = PineconeVectorStore(index=index, embedding=embeddings)
```

대용량 프로덕션 환경에서 인프라 관리 없이 쓰고 싶을 때 선택합니다.

### FAISS — 대용량 로컬

```python
from langchain_community.vectorstores import FAISS

vectorstore = FAISS.from_documents(chunks, embeddings)
vectorstore.save_local("./faiss_index")

# 로드
vectorstore = FAISS.load_local("./faiss_index", embeddings)
```

GPU 서버가 있고 수백만 벡터를 로컬에서 처리해야 할 때 적합합니다.

## 검색 품질 향상 기법

기본 유사도 검색만으로는 한계가 있습니다. 다음 기법들을 조합해 품질을 높입니다.

### Hybrid Search (하이브리드 검색)

벡터 검색(의미 기반)과 키워드 검색(BM25)을 결합합니다.

```python
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

# BM25 (키워드 기반)
bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 5

# 벡터 기반
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# 앙상블 (0.5:0.5 가중치)
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.5, 0.5]
)
```

### MMR (Maximal Marginal Relevance)

검색 결과의 다양성을 확보합니다. 유사한 청크가 중복으로 검색되는 것을 방지합니다.

```python
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "fetch_k": 20, "lambda_mult": 0.7}
)
```

### Re-ranking

검색된 문서를 Cross-encoder로 재정렬해 최종 품질을 높입니다.

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import CohereRerank

compressor = CohereRerank(model="rerank-multilingual-v3.0", top_n=3)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vector_retriever
)
```

## 실전 예시 — 사내 기술 문서 Q&A 챗봇

실제 서비스 수준의 RAG 챗봇을 구성하는 전체 흐름입니다.

```python
import os
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory

class CompanyKnowledgeBot:
    def __init__(self, docs_path: str, db_path: str = "./chroma_db"):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.db_path = db_path

        if Path(db_path).exists():
            self.vectorstore = Chroma(
                persist_directory=db_path,
                embedding_function=self.embeddings
            )
            print("기존 벡터 DB 로드 완료")
        else:
            self.vectorstore = self._build_index(docs_path)

        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=5  # 최근 5턴 대화 기억
        )

        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 5, "fetch_k": 20}
            ),
            memory=self.memory,
            return_source_documents=True,
            verbose=False
        )

    def _build_index(self, docs_path: str):
        loader = DirectoryLoader(
            docs_path,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader
        )
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = splitter.split_documents(docs)

        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.db_path
        )
        print(f"인덱싱 완료: {len(chunks)}개 청크")
        return vectorstore

    def chat(self, question: str) -> dict:
        result = self.chain.invoke({"question": question})
        sources = list(set([
            doc.metadata.get("source", "unknown")
            for doc in result.get("source_documents", [])
        ]))
        return {
            "answer": result["answer"],
            "sources": sources
        }

# 사용 예시
bot = CompanyKnowledgeBot(docs_path="./company_docs")

while True:
    question = input("질문: ")
    if question == "exit":
        break
    response = bot.chat(question)
    print(f"답변: {response['answer']}")
    print(f"출처: {', '.join(response['sources'])}\n")
```

## RAG 평가 지표

구축한 RAG 시스템의 품질을 측정하는 방법입니다.

### RAGAS 프레임워크

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,        # 답변이 컨텍스트에 충실한가
    answer_relevancy,    # 답변이 질문과 관련 있는가
    context_precision,   # 검색된 컨텍스트가 정확한가
    context_recall       # 관련 컨텍스트를 빠짐없이 검색했는가
)
from datasets import Dataset

# 평가 데이터셋
eval_data = {
    "question": ["휴가는 며칠인가요?", "재택근무 규정은?"],
    "answer": ["연차는 15일입니다.", "주 3일 재택 가능합니다."],
    "contexts": [["HR 규정 문서..."], ["근무 규정 문서..."]],
    "ground_truth": ["연차 15일", "주 3일 재택"]
}

dataset = Dataset.from_dict(eval_data)
result = evaluate(dataset, metrics=[faithfulness, answer_relevancy])
print(result)
```

## 흔한 실수와 해결책

13년간의 경험에서 가장 자주 보는 RAG 실수들입니다.

**청크 크기를 너무 작게 설정:** 200 토큰 이하로 설정하면 문맥이 부족해 답변 품질이 떨어집니다. 최소 500 토큰부터 시작하세요.

**오버랩을 0으로 설정:** 청크 경계에서 잘린 정보가 누락됩니다. 청크 크기의 10~20%로 설정하세요.

**TOP-K를 너무 낮게:** k=1이나 k=2로 설정하면 관련 문서를 놓칩니다. k=5~10이 일반적입니다.

**임베딩 모델과 검색 모델 불일치:** 인덱싱과 쿼리 시 동일한 임베딩 모델을 사용해야 합니다. 모델을 바꾸면 재인덱싱이 필요합니다.

**한국어 문서에 영어 청크 분리자 사용:** `SemanticChunker`나 한국어에 적합한 분리자 설정을 사용하세요.

## 마치며

RAG는 현재 기업 AI 도입의 가장 현실적인 출발점입니다. 파인튜닝보다 비용이 적고, 데이터 업데이트가 쉽고, 출처를 추적할 수 있기 때문입니다. 시작은 Chroma + LangChain + GPT-4o-mini 조합으로 간단하게 프로토타입을 만들고, 규모에 따라 Pinecone이나 Weaviate로 이전하는 전략을 권장합니다.

다음 포스트에서는 Chroma, Pinecone, Weaviate를 코드 레벨에서 상세히 비교합니다.
