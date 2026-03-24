---
title: "로컬 LLM 실전 가이드 — Ollama로 내 PC에서 AI 돌리기"
date: 2023-11-21T08:00:00+09:00
lastmod: 2023-11-28T08:00:00+09:00
description: "Ollama로 로컬 LLM을 설치하고 운영하는 완전한 실전 가이드입니다. Llama3, Mistral, Gemma 모델 선택부터 Python API 연동, GPU 가속, Open WebUI 설정까지 상세히 다룹니다."
slug: "ollama-local-llm-complete-guide"
categories: ["ai-automation"]
tags: ["Ollama", "로컬 LLM", "Llama3", "AI 프라이버시", "오픈소스 LLM"]
series: []
draft: false
---

API 비용이 부담스럽거나, 민감한 데이터를 외부 서버에 보내기 꺼려지거나, 인터넷 없이 AI를 사용해야 하는 상황이라면 로컬 LLM이 답입니다. **Ollama**는 로컬 LLM 실행의 진입 장벽을 극적으로 낮춘 도구입니다. 복잡한 환경 설정 없이 명령어 몇 줄로 최신 오픈소스 LLM을 PC에서 실행할 수 있습니다.

13년 차 엔지니어로서 로컬 LLM을 개인 프로젝트와 사내 도구에 적용한 경험을 바탕으로, Ollama 설치부터 프로덕션 수준의 API 연동까지 실전 중심으로 정리합니다.

## 로컬 LLM을 선택해야 하는 이유

**비용**: Claude나 GPT-4o API는 1M 토큰당 수 달러가 청구됩니다. 대용량 문서 처리나 반복적인 배치 작업을 하면 월 비용이 수십만 원을 넘기도 합니다. 로컬 LLM은 전기 요금 외에 추가 비용이 없습니다.

**프라이버시**: 소스 코드, 고객 데이터, 내부 문서를 외부 API에 전송하면 데이터 유출 리스크가 있습니다. 특히 금융, 의료, 법률 분야에서는 규제 준수 문제도 생깁니다. 로컬 LLM은 데이터가 장치 밖으로 나가지 않습니다.

**지연 시간**: 클라우드 API는 네트워크 왕복 시간이 필수적으로 발생합니다. 로컬에서 실행하면 네트워크 레이턴시가 제로입니다.

**오프라인 동작**: 인터넷이 없는 환경에서도 AI 기능을 구현할 수 있습니다.

{{< figure src="/images/ollama-local-llm-guide.svg" alt="Ollama 로컬 LLM 아키텍처" caption="Ollama를 중심으로 한 로컬 LLM 실행 환경 구성도" >}}

## Ollama 설치

### macOS / Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows

[ollama.com](https://ollama.com)에서 Windows 설치 파일(.exe)을 다운로드해 실행합니다. 설치 후 시스템 트레이에 Ollama 아이콘이 나타납니다.

설치가 완료되면 `localhost:11434`에서 REST API 서버가 자동으로 시작됩니다.

```bash
# 설치 확인
ollama --version

# 서버 상태 확인
curl http://localhost:11434/api/tags
```

## 모델 선택 가이드

Ollama는 수백 개의 오픈소스 모델을 지원합니다. 상황에 맞는 모델을 선택하는 것이 중요합니다.

### Llama 3.2 — 범용 최강자

Meta의 Llama 3.2는 현재 오픈소스 LLM 중 가장 균형 잡힌 성능을 보여줍니다.

```bash
ollama pull llama3.2          # 3B 모델 (약 2GB, RAM 4GB+)
ollama pull llama3.2:8b       # 8B 모델 (약 5GB, RAM 8GB+)
ollama pull llama3.1:70b      # 70B 모델 (약 40GB, RAM 64GB+)
```

| 모델 크기 | RAM 요구량 | 추론 속도 | 품질 |
|-----------|-----------|-----------|------|
| 3B | 4GB | 매우 빠름 | 보통 |
| 8B | 8GB | 빠름 | 좋음 |
| 70B | 64GB | 느림 | 우수 |

대부분의 개발자에게는 **8B 모델**이 속도와 품질의 균형점입니다.

### Mistral / Mixtral — 코딩과 추론

```bash
ollama pull mistral           # 7B (약 4GB)
ollama pull mixtral           # 8x7B MoE (약 26GB)
ollama pull codestral         # 코딩 특화
```

Mistral 7B은 같은 크기 모델 중 코딩 능력이 뛰어납니다. Mixtral은 Mixture of Experts 아키텍처로 70B급 성능을 26GB 메모리로 구현합니다.

### Gemma 2 / Phi-3 — 저사양 최적화

```bash
ollama pull gemma2:2b         # 2B (약 1.6GB, RAM 4GB)
ollama pull phi3:mini         # 3.8B (약 2.3GB)
ollama pull phi3.5            # 3.8B, 성능 개선판
```

RAM이 8GB 이하이거나 GPU 없이 CPU만으로 실행해야 한다면 Gemma2 2B나 Phi-3 mini가 현실적인 선택입니다.

### 한국어 특화 모델

```bash
ollama pull exaone3.5         # LG AI Research, 한국어 특화
ollama pull qwen2.5:7b        # 중국어/영어/한국어 다국어
```

한국어 처리가 중요하다면 **EXAONE 3.5**를 추천합니다. LG AI Research가 공개한 모델로 한국어 이해와 생성 품질이 오픈소스 중 최상위권입니다.

## 기본 사용법

### CLI로 즉시 대화

```bash
# 모델 실행 및 대화
ollama run llama3.2

# 단일 질문 전송
ollama run llama3.2 "Python 제너레이터를 설명해 주세요."

# 파일 내용 전달
cat code.py | ollama run codestral "이 코드를 리뷰해 주세요."
```

### Modelfile로 커스텀 모델 생성

특정 역할이나 파라미터로 커스터마이즈한 모델을 만들 수 있습니다.

```dockerfile
# Modelfile
FROM llama3.2:8b

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 8192

SYSTEM """
당신은 13년 경력의 시니어 Python 개발자입니다.
코드 리뷰 시 명확하고 구체적인 개선 방향을 제시합니다.
항상 한국어로 답변합니다.
"""
```

```bash
ollama create code-reviewer -f Modelfile
ollama run code-reviewer
```

## Python으로 Ollama API 연동

Ollama는 OpenAI 호환 API를 제공합니다. 기존 OpenAI SDK 코드를 거의 그대로 재사용할 수 있습니다.

### 방법 1: OpenAI SDK 활용 (권장)

```python
from openai import OpenAI

# base_url만 변경하면 OpenAI 코드를 그대로 사용
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # 로컬이므로 아무 값이나 가능
)

response = client.chat.completions.create(
    model="llama3.2:8b",
    messages=[
        {"role": "system", "content": "당신은 Python 전문가입니다."},
        {"role": "user", "content": "asyncio와 threading의 차이를 설명해 주세요."}
    ],
    max_tokens=800,
    temperature=0.3,
)

print(response.choices[0].message.content)
```

### 방법 2: Ollama Python 라이브러리

```bash
pip install ollama
```

```python
import ollama

# 기본 호출
response = ollama.chat(
    model="llama3.2:8b",
    messages=[{"role": "user", "content": "Docker와 VM의 차이는?"}]
)
print(response["message"]["content"])

# 스트리밍
stream = ollama.chat(
    model="llama3.2:8b",
    messages=[{"role": "user", "content": "REST API 설계 원칙을 설명해 주세요."}],
    stream=True,
)

for chunk in stream:
    print(chunk["message"]["content"], end="", flush=True)
print()

# 임베딩 생성
embeddings = ollama.embeddings(
    model="nomic-embed-text",
    prompt="로컬 LLM의 장점은 무엇인가?"
)
print(f"임베딩 차원: {len(embeddings['embedding'])}")
```

### 방법 3: 직접 REST API 호출

```python
import requests
import json

def ollama_chat(model: str, message: str) -> str:
    """Ollama REST API 직접 호출"""
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "stream": False,
        }
    )
    return response.json()["message"]["content"]

result = ollama_chat("llama3.2:8b", "머신러닝과 딥러닝의 차이는?")
print(result)
```

## LangChain과 연동

LangChain에서 Ollama를 로컬 LLM 백엔드로 사용할 수 있습니다.

```bash
pip install langchain langchain-ollama langchain-community
```

```python
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatOllama(
    model="llama3.2:8b",
    temperature=0.3,
    base_url="http://localhost:11434",
)

messages = [
    SystemMessage(content="당신은 친절한 기술 튜터입니다."),
    HumanMessage(content="쿠버네티스 Pod와 Container의 관계를 설명해 주세요."),
]

response = llm.invoke(messages)
print(response.content)

# 스트리밍
for chunk in llm.stream(messages):
    print(chunk.content, end="", flush=True)
```

## Open WebUI 설치 — 브라우저 ChatGPT UI

Ollama만으로는 터미널 인터페이스만 사용할 수 있습니다. Open WebUI를 설치하면 ChatGPT와 동일한 브라우저 UI로 로컬 LLM을 사용할 수 있습니다.

```bash
# Docker로 설치 (권장)
docker run -d \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

`http://localhost:3000`으로 접속하면 Ollama에 설치된 모든 모델을 선택해 대화할 수 있습니다.

## GPU 가속 설정

GPU가 있으면 CPU 대비 3~10배 빠른 추론이 가능합니다.

### NVIDIA GPU (CUDA)

Ollama는 NVIDIA GPU를 자동으로 감지합니다. CUDA 드라이버가 설치되어 있으면 별도 설정 없이 GPU 가속이 활성화됩니다.

```bash
# GPU 사용 확인
ollama ps
# NAME             ID              SIZE    PROCESSOR    UNTIL
# llama3.2:8b      abc123          5.0 GB  100% GPU     ...
```

### GPU VRAM 최적화

```bash
# VRAM 사용량 조절 (기본값: 80%)
OLLAMA_GPU_MEMORY_FRACTION=0.9 ollama serve

# 여러 GPU 사용
CUDA_VISIBLE_DEVICES=0,1 ollama serve
```

### GPU가 없는 경우 CPU 최적화

```bash
# CPU 스레드 수 조절
OLLAMA_NUM_PARALLEL=2 ollama serve

# 모델 레이어를 RAM에 유지
OLLAMA_KEEP_ALIVE=60m ollama serve
```

## 성능 벤치마크 (개인 PC 기준)

| 환경 | 모델 | 토큰/초 |
|------|------|---------|
| M2 MacBook Pro (16GB) | Llama3.2 8B | ~35 t/s |
| RTX 3080 (10GB VRAM) | Llama3.2 8B | ~80 t/s |
| RTX 4090 (24GB VRAM) | Llama3.1 70B | ~25 t/s |
| Core i7 CPU only | Llama3.2 3B | ~8 t/s |

MacBook Pro M 시리즈는 통합 메모리 덕분에 CPU/GPU 경계 없이 큰 모델을 효율적으로 실행합니다. Apple Silicon 환경에서는 별도 GPU 없이도 충분한 성능을 낼 수 있습니다.

## 실전 활용 사례

### 코드 리뷰 자동화

```python
import subprocess
import ollama

def review_git_diff() -> str:
    """git diff 결과를 로컬 LLM으로 코드 리뷰"""
    diff = subprocess.check_output(["git", "diff", "HEAD"], text=True)

    if not diff:
        return "변경사항이 없습니다."

    response = ollama.chat(
        model="codestral",
        messages=[{
            "role": "user",
            "content": f"다음 코드 변경사항을 리뷰해 주세요:\n\n{diff}"
        }]
    )
    return response["message"]["content"]

print(review_git_diff())
```

### 로컬 문서 Q&A

```python
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

def build_local_rag(pdf_path: str):
    """로컬 PDF를 기반으로 Q&A 시스템 구축"""
    # 문서 로드
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    # 청킹
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    # 로컬 임베딩 + 벡터 DB (완전 오프라인)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    # 로컬 LLM으로 응답 생성
    llm = ChatOllama(model="llama3.2:8b", temperature=0)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    return retriever, llm
```

## 마치며

Ollama는 로컬 LLM 생태계에서 사실상 표준 도구가 되었습니다. 설치 간편함, OpenAI 호환 API, 풍부한 모델 지원이라는 세 가지 강점이 동시에 충족되는 도구는 현재 Ollama가 유일합니다.

API 비용 절감, 데이터 프라이버시, 오프라인 동작 중 한 가지라도 필요하다면 로컬 LLM 도입을 진지하게 검토해 보시기 바랍니다. RAM 16GB 이상의 현대적인 개발 PC라면 8B 모델로 충분히 실용적인 AI 앱을 만들 수 있습니다.
