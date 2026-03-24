---
title: "LangChain vs LlamaIndex — RAG 애플리케이션 프레임워크 비교"
date: 2023-08-09T08:00:00+09:00
lastmod: 2023-08-11T08:00:00+09:00
description: "RAG 애플리케이션 개발을 위한 LangChain과 LlamaIndex의 구조, 코드 패턴, 벡터 DB 연동 방식을 실제 코드 예시로 비교합니다. 어떤 프레임워크를 선택해야 할지 명확한 기준을 제시합니다."
slug: "langchain-vs-llamaindex-rag-comparison"
categories: ["ai-automation"]
tags: ["LangChain", "LlamaIndex", "RAG", "벡터 DB", "AI 애플리케이션"]
series: []
draft: false
---

LLM 앱 개발을 시작할 때 가장 먼저 부딪히는 질문이 있습니다. "LangChain을 써야 하나, LlamaIndex를 써야 하나?" 두 프레임워크 모두 RAG(Retrieval-Augmented Generation) 애플리케이션 개발을 위한 강력한 도구이지만, 설계 철학과 강점이 다릅니다.

13년 차 엔지니어로서 두 프레임워크를 모두 실무 프로젝트에 사용한 경험을 바탕으로, 같은 RAG 기능을 두 프레임워크로 각각 구현해 비교합니다.

## RAG란 무엇인가

RAG(Retrieval-Augmented Generation)는 LLM이 학습 데이터에 없는 정보를 외부 지식베이스에서 검색해 답변을 생성하는 아키텍처입니다.

```
사용자 질문
    ↓
질문을 벡터로 변환 (임베딩)
    ↓
벡터 DB에서 유사 문서 검색
    ↓
검색된 문서 + 질문을 LLM에 전달
    ↓
LLM이 문서 기반으로 답변 생성
```

이 파이프라인을 구현하는 데 필요한 컴포넌트들(문서 로더, 청킹, 임베딩, 벡터 DB, LLM 연동)을 추상화한 것이 LangChain과 LlamaIndex입니다.

{{< figure src="/images/langchain-vs-llamaindex-rag.svg" alt="LangChain vs LlamaIndex RAG 파이프라인 비교" caption="두 프레임워크의 RAG 파이프라인 구조와 특징 비교" >}}

## LangChain 개요

LangChain은 2022년 말 등장해 LLM 앱 개발의 사실상 표준으로 자리 잡았습니다. 핵심 철학은 **체인(Chain)**: 여러 컴포넌트를 연결해 복잡한 파이프라인을 구성한다는 개념입니다.

### 주요 구성요소

- **LCEL (LangChain Expression Language)**: 파이프라인을 `|` 연산자로 선언적으로 구성
- **Runnable**: 모든 컴포넌트가 구현하는 공통 인터페이스
- **Memory**: 대화 히스토리 관리
- **Agents**: 도구를 자율적으로 선택하는 에이전트
- **LangSmith**: 추적, 디버깅, 평가 플랫폼

```bash
pip install langchain langchain-openai langchain-community faiss-cpu
```

## LlamaIndex 개요

LlamaIndex(구 GPT Index)는 데이터 인덱싱과 RAG 파이프라인에 특화된 프레임워크입니다. "데이터와 LLM을 연결하는 가장 쉬운 방법"을 목표로 합니다.

### 주요 구성요소

- **Index**: 문서를 구조화하는 다양한 인덱스 유형
- **QueryEngine**: 인덱스에 질의하는 인터페이스
- **Node**: 문서의 기본 단위
- **LlamaParse**: PDF·문서 고품질 파싱 서비스
- **Workflows**: 비동기 이벤트 기반 파이프라인

```bash
pip install llama-index llama-index-llms-openai llama-index-embeddings-openai
```

## 같은 RAG를 두 프레임워크로 구현

회사 내규 문서를 기반으로 질문에 답하는 Q&A 시스템을 두 프레임워크로 각각 구현해 비교합니다.

### LangChain 구현

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 1. 문서 로드 및 청킹
loader = PyPDFLoader("company_policy.pdf")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", "。", " "],
)
chunks = splitter.split_documents(docs)

# 2. 벡터 DB 구축
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever(
    search_type="mmr",  # Maximum Marginal Relevance
    search_kwargs={"k": 4, "fetch_k": 20},
)

# 3. 프롬프트 템플릿
prompt = ChatPromptTemplate.from_template("""
다음 컨텍스트를 바탕으로 질문에 답변하세요.
컨텍스트에 없는 내용은 모른다고 답하세요.

컨텍스트:
{context}

질문: {question}
""")

# 4. LCEL로 파이프라인 구성
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 5. 실행
answer = rag_chain.invoke("연차 신청은 며칠 전에 해야 하나요?")
print(answer)
```

### LlamaIndex 구현

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# 1. 전역 설정
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.node_parser = SentenceSplitter(chunk_size=500, chunk_overlap=100)

# 2. 문서 로드 및 인덱스 구축
documents = SimpleDirectoryReader(input_files=["company_policy.pdf"]).load_data()
index = VectorStoreIndex.from_documents(documents, show_progress=True)

# 3. QueryEngine 생성
query_engine = index.as_query_engine(
    similarity_top_k=4,
    response_mode="compact",  # 검색된 노드를 압축해 응답
)

# 4. 실행
response = query_engine.query("연차 신청은 며칠 전에 해야 하나요?")
print(response)

# 소스 문서 확인 (출처 추적)
for node in response.source_nodes:
    print(f"출처: {node.metadata.get('file_name')} | 점수: {node.score:.3f}")
```

### 코드 비교 분석

| 항목 | LangChain | LlamaIndex |
|------|-----------|------------|
| 코드 라인 수 | 약 35줄 | 약 20줄 |
| 파이프라인 구성 | LCEL (`|` 연산자) | 자동 (Settings 중심) |
| 소스 추적 | 별도 구현 필요 | 기본 지원 |
| 유연성 | 높음 (세부 제어 가능) | 중간 (추상화 높음) |
| 학습 곡선 | 가파름 | 완만 |

## 고급 기능 비교

### 하이브리드 검색

의미 검색(벡터)과 키워드 검색(BM25)을 결합한 하이브리드 검색은 RAG 품질을 크게 향상시킵니다.

**LangChain:**
```python
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

bm25_retriever = BM25Retriever.from_documents(chunks, k=4)
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.4, 0.6],  # 키워드 40%, 벡터 60%
)
```

**LlamaIndex:**
```python
from llama_index.core.retrievers import VectorIndexRetriever, BM25Retriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SentenceTransformerRerank

# 벡터 리트리버
vector_retriever = VectorIndexRetriever(index=index, similarity_top_k=6)

# BM25 리트리버
bm25_retriever = BM25Retriever.from_defaults(
    docstore=index.docstore, similarity_top_k=6
)

# 재랭킹 (LlamaIndex의 강점)
reranker = SentenceTransformerRerank(
    model="cross-encoder/ms-marco-MiniLM-L-2-v2",
    top_n=4,
)

query_engine = RetrieverQueryEngine(
    retriever=vector_retriever,
    node_postprocessors=[reranker],
)
```

LlamaIndex는 재랭킹(Reranking) 통합이 훨씬 간단합니다.

### 에이전트 구현

**LangChain (에이전트 강점):**
```python
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool

@tool
def search_policy(query: str) -> str:
    """회사 내규에서 정보를 검색합니다."""
    docs = retriever.invoke(query)
    return "\n".join(d.page_content for d in docs)

@tool
def get_employee_info(employee_id: str) -> str:
    """직원 정보를 조회합니다."""
    # 실제 HR 시스템 API 호출
    return f"직원 {employee_id}: 입사일 2022-03-01, 부서 개발팀"

tools = [search_policy, get_employee_info]
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = agent_executor.invoke({"input": "2년 차 직원의 연차는 며칠인가요?"})
```

**LlamaIndex (Workflows):**
```python
from llama_index.core.workflow import Workflow, StartEvent, StopEvent, step
from llama_index.core.tools import QueryEngineTool

class RAGWorkflow(Workflow):
    @step
    async def retrieve(self, ev: StartEvent) -> StopEvent:
        query = ev.get("query")
        response = query_engine.query(query)
        return StopEvent(result=str(response))

workflow = RAGWorkflow(timeout=30)
result = await workflow.run(query="연차 규정을 알려주세요.")
```

### 벡터 DB 연동

두 프레임워크 모두 주요 벡터 DB를 지원합니다.

```python
# Pinecone 연동 — LangChain
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

pc = Pinecone(api_key="...")
index = pc.Index("my-index")
vectorstore = PineconeVectorStore(index=index, embedding=embeddings)

# Pinecone 연동 — LlamaIndex
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import StorageContext

vector_store = PineconeVectorStore(pinecone_index=index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
```

## 프레임워크 선택 기준

### LangChain을 선택해야 할 때

**복잡한 에이전트 시스템**이 필요할 때입니다. 여러 도구를 자율적으로 선택하고, 멀티스텝 추론을 수행하는 에이전트를 만든다면 LangChain의 에이전트 생태계가 훨씬 성숙해 있습니다.

**다양한 LLM을 교체해 사용**해야 할 때입니다. OpenAI, Anthropic, Ollama 로컬 모델을 코드 변경 없이 교체할 수 있는 추상화가 필요하다면 LangChain이 유리합니다.

**LangSmith 디버깅 생태계**가 필요할 때입니다. 프롬프트 추적, A/B 테스트, 평가 파이프라인까지 하나의 플랫폼에서 관리하고 싶다면 LangSmith와 LangChain 조합을 선택합니다.

### LlamaIndex를 선택해야 할 때

**문서 Q&A 시스템**이 핵심일 때입니다. PDF, Word, 웹페이지 등 다양한 문서 포맷을 인덱싱하고 정확하게 답변을 생성하는 것이 주목적이라면 LlamaIndex가 더 간단하고 강력합니다.

**LlamaParse가 필요**할 때입니다. 복잡한 표, 그래프, 레이아웃이 있는 PDF를 정확하게 파싱해야 한다면 LlamaParse(유료)는 현재 최상위 솔루션입니다.

**재랭킹과 검색 품질 최적화**에 집중할 때입니다. LlamaIndex의 재랭킹, 쿼리 변환, 멀티쿼리 등 RAG 파이프라인 품질 개선 기능이 더 직관적으로 구현되어 있습니다.

### 둘 다 써도 된다

실제로 두 프레임워크는 함께 사용할 수 있습니다. LlamaIndex로 인덱싱하고, LangChain 에이전트에서 LlamaIndex QueryEngine을 도구로 사용하는 패턴이 실무에서 자주 쓰입니다.

```python
from langchain_core.tools import Tool
from llama_index.core import VectorStoreIndex

# LlamaIndex로 인덱스 구축
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

# LangChain 도구로 래핑
rag_tool = Tool(
    name="company_policy_search",
    description="회사 내규 문서에서 정보를 검색합니다.",
    func=lambda q: str(query_engine.query(q)),
)

# LangChain 에이전트에서 사용
tools = [rag_tool, get_employee_info]
agent_executor = AgentExecutor(agent=agent, tools=tools)
```

## 성능과 비용 고려

두 프레임워크는 LLM과 임베딩 API를 사용하므로, 실제 비용은 프레임워크가 아닌 **API 호출 횟수와 토큰 수**에 의해 결정됩니다.

그러나 일부 기능은 추가 API 호출을 유발합니다. LangChain의 멀티쿼리 리트리버는 질문을 여러 변형으로 바꿔 각각 검색하므로 임베딩 API를 여러 번 호출합니다. LlamaIndex의 쿼리 변환도 마찬가지입니다. 이러한 기능을 사용할 때는 비용 트레이드오프를 인지해야 합니다.

## 마치며

두 프레임워크 모두 2026년 기준으로 충분히 성숙했고 프로덕션 사용에 적합합니다. 빠르게 RAG Q&A를 만들어야 한다면 LlamaIndex, 복잡한 에이전트 시스템을 구축한다면 LangChain을 먼저 시도해 보시기 바랍니다.

무엇보다 중요한 것은 프레임워크 선택보다 **RAG 파이프라인의 품질**입니다. 청킹 전략, 임베딩 모델 선택, 재랭킹 적용 여부가 프레임워크 선택보다 최종 품질에 훨씬 큰 영향을 미칩니다.
