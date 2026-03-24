---
title: "n8n으로 AI 워크플로우 자동화 — 코딩 없이 AI 파이프라인 만들기"
date: 2024-10-02T08:00:00+09:00
lastmod: 2024-10-04T08:00:00+09:00
description: "오픈소스 자동화 도구 n8n으로 Claude·GPT-4o를 연결한 AI 워크플로우를 만드는 방법을 다룹니다. 로컬 설치부터 Zapier 비교, 실전 자동화 예시까지 상세히 정리합니다."
slug: "n8n-ai-workflow-automation-guide"
categories: ["ai-automation"]
tags: ["n8n", "AI 자동화", "워크플로우", "Zapier 대안", "노코드"]
series: []
draft: false
---

![n8n AI 워크플로우 파이프라인](/images/n8n-ai-workflow-2026.svg)

Zapier를 쓰다가 월 청구서를 보고 놀란 경험이 있으신가요? 저는 2024년에 Zapier 청구액이 월 $120을 넘어서면서 대안을 찾기 시작했습니다. 그 결과 발견한 것이 **n8n**이었고, 지금은 개인 서버에서 20개 이상의 워크플로우를 무료로 돌리고 있습니다. n8n은 코드를 전혀 몰라도 쓸 수 있지만, 엔지니어라면 JavaScript 코드를 직접 삽입해서 훨씬 강력하게 활용할 수 있는 도구입니다.

---

## n8n이란 무엇인가

n8n은 **Fair-code 라이선스 기반의 오픈소스 워크플로우 자동화 도구**입니다. 2019년 Jan Oberhauser가 창업한 베를린 스타트업이 개발했으며, 2026년 현재 GitHub에서 5만 개 이상의 스타를 받고 있습니다.

핵심 특징을 세 가지로 요약하면 다음과 같습니다.

**셀프호스팅 가능**: 자체 서버에 설치하면 실행 횟수 제한이 없습니다. Zapier는 월 사용량에 따라 요금이 기하급수적으로 증가하지만, n8n 셀프호스팅은 서버 비용(월 $5~10)만 부담합니다.

**코드와 노코드 혼용**: 비개발자는 드래그 앤 드롭으로 워크플로우를 만들고, 개발자는 JavaScript/Python 코드 노드를 삽입해 복잡한 로직을 처리합니다.

**400개 이상의 내장 노드**: Gmail, Slack, GitHub, Airtable, PostgreSQL, Shopify, Stripe 등 주요 서비스가 모두 기본 내장됩니다.

---

## n8n 설치 방법

### 방법 1: Docker로 로컬 설치 (가장 빠름)

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n
```

브라우저에서 `http://localhost:5678`로 접속하면 바로 사용할 수 있습니다.

### 방법 2: Docker Compose (영구 운영)

```yaml
version: "3.8"

services:
  n8n:
    image: docker.n8n.io/n8nio/n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=your-domain.com
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://your-domain.com/
      - GENERIC_TIMEZONE=Asia/Seoul
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:
```

```bash
docker compose up -d
```

### 방법 3: npm으로 설치

```bash
npm install -g n8n
n8n start
```

### 방법 4: n8n Cloud (관리형 서비스)

`https://n8n.io`에서 계정을 만들면 설치 없이 바로 사용할 수 있습니다. 월 $20부터 시작하며, 소규모 팀에는 적합한 선택입니다.

---

## n8n의 AI 노드 완전 정리

n8n 1.x 버전부터 AI 기능이 대폭 강화됐습니다. 핵심 AI 관련 노드를 살펴보겠습니다.

### AI Agent 노드

AI Agent 노드는 단순 텍스트 생성을 넘어, 도구를 사용하는 에이전트를 구성할 수 있습니다. 노드 설정에서 사용할 LLM(Claude, GPT-4o, Gemini 등)과 에이전트가 쓸 수 있는 도구를 지정하면, 모델이 알아서 도구를 선택하고 순서를 정해 실행합니다.

**지원 LLM 목록:**
- Anthropic Claude (claude-opus-4-5, claude-sonnet-4-5 등)
- OpenAI GPT-4o, GPT-4o mini
- Google Gemini 1.5 Pro
- Mistral AI
- Ollama (로컬 모델)

### Basic LLM Chain 노드

단순 텍스트 생성 작업에 적합합니다. 이전 노드의 데이터를 프롬프트에 삽입하고 LLM 응답을 다음 노드로 전달하는 가장 기본적인 패턴입니다.

### Embeddings 노드

텍스트를 벡터로 변환합니다. Pinecone이나 Qdrant 같은 벡터 DB 노드와 결합해서 RAG 파이프라인을 구성할 수 있습니다.

### Vector Store 노드

Pinecone, Chroma, Supabase Vector, Qdrant와 연동해서 문서 저장 및 유사도 검색을 수행합니다.

---

## 실전 자동화 예시 3가지

### 예시 1: AI 뉴스 다이제스트 자동화

매일 아침 9시에 RSS 피드를 수집하고, Claude로 요약한 뒤 Slack에 전송하는 워크플로우입니다.

**워크플로우 구성:**

1. **Schedule Trigger** — 매일 09:00 (cron: `0 9 * * *`)
2. **RSS Feed Read** — 여러 URL을 배열로 지정
3. **Code 노드** — 지난 24시간 이내 항목만 필터링
4. **AI Agent 노드** (Claude claude-sonnet-4-5) — 각 기사를 3줄로 요약 + 중요도 점수 부여
5. **IF 노드** — 중요도 점수 7점 이상만 통과
6. **Slack 노드** — `#ai-digest` 채널에 요약 전송

**Code 노드 예시:**

```javascript
const items = $input.all();
const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);

return items.filter(item => {
  const pubDate = new Date(item.json.pubDate);
  return pubDate > oneDayAgo;
}).map(item => ({
  json: {
    title: item.json.title,
    link: item.json.link,
    content: item.json.content?.substring(0, 1500) || ""
  }
}));
```

**AI Agent 프롬프트:**

```
다음 뉴스 기사를 분석해주세요.

제목: {{ $json.title }}
내용: {{ $json.content }}

아래 JSON 형식으로만 응답하세요:
{
  "summary": "3줄 이내 요약",
  "importance": 1~10 점수,
  "reason": "중요도 판단 이유 한 줄"
}
```

### 예시 2: GitHub PR 자동 레이블링

새 PR이 열리면 변경된 파일을 분석해서 자동으로 레이블을 붙이는 워크플로우입니다.

**워크플로우 구성:**

1. **GitHub Trigger** — `pull_request.opened` 이벤트
2. **HTTP Request 노드** — GitHub API로 변경 파일 목록 조회
3. **AI Agent 노드** (GPT-4o mini) — 파일 경로 목록을 보고 적절한 레이블 추천
4. **GitHub 노드** — PR에 레이블 추가

**비용**: GPT-4o mini 기준 PR당 약 $0.001 미만입니다.

### 예시 3: 고객 문의 자동 분류 및 답변 초안 생성

```
[Gmail Trigger] → 새 고객 문의 수신
    ↓
[AI Agent] → 문의 유형 분류 (환불/기술지원/일반문의/스팸)
    ↓
[Switch 노드] → 유형별 분기
    ├─ 환불 → [Notion 노드] 환불 정책 DB 검색 → [AI Agent] 답변 초안 생성
    ├─ 기술지원 → [Slack] 기술팀 채널 알림
    ├─ 일반문의 → [AI Agent] FAQ 기반 자동 답변 생성
    └─ 스팸 → [Gmail] 스팸 폴더로 이동
```

---

## n8n에서 Claude API 연결하기

1. n8n 좌측 메뉴에서 **Credentials** 클릭
2. **Add Credential** → **Anthropic** 검색
3. API Key 입력 (Anthropic Console에서 발급)
4. **Save** 후 AI Agent 노드에서 해당 Credential 선택

```
Anthropic Console: https://console.anthropic.com/settings/keys
```

모델 선택 시 작업 성격에 따라 적절한 모델을 고릅니다.

| 작업 | 권장 모델 | 이유 |
|------|-----------|------|
| 단순 분류/요약 | claude-haiku-3-5 | 빠르고 저렴 |
| 코드 생성/분석 | claude-sonnet-4-5 | 균형 잡힌 성능 |
| 복잡한 추론 | claude-opus-4-5 | 최고 품질 |

---

## n8n vs Zapier 비교

| 항목 | n8n (셀프호스팅) | Zapier |
|------|-----------------|--------|
| 월 비용 | $5~10 (서버비) | $20~$599 |
| 실행 횟수 | 무제한 | 플랜별 제한 |
| 커스텀 코드 | JavaScript/Python 지원 | 제한적 |
| AI 노드 | 내장 (오픈소스) | Zapier AI (제한적) |
| 데이터 위치 | 자체 서버 | Zapier 서버 |
| 학습 곡선 | 보통 | 낮음 |
| 지원 서비스 수 | 400+ | 6,000+ |
| 오픈소스 | O | X |

서비스 연동 수는 Zapier가 훨씬 많지만, AI 자동화와 비용 효율성은 n8n이 압도적입니다. 스타트업이나 엔지니어 팀이라면 n8n 셀프호스팅을 강력히 추천합니다.

---

## n8n 운영 팁

### 오류 핸들링 설정

모든 워크플로우에 **Error Workflow**를 연결해두는 것이 좋습니다. 설정 방법은 워크플로우 설정 → Error Workflow → 오류 처리 전용 워크플로우 지정입니다.

오류 처리 워크플로우는 보통 다음과 같이 구성합니다.

```
[Error Trigger] → [Slack 노드] 오류 알림 전송 + [Airtable] 오류 로그 저장
```

### 실행 데이터 보존 기간 설정

기본 설정으로 실행 기록이 무제한 쌓이면 DB가 커집니다. 환경 변수로 보존 기간을 제한합니다.

```bash
EXECUTIONS_DATA_MAX_AGE=168  # 7일 (시간 단위)
EXECUTIONS_DATA_PRUNE=true
```

### 웹훅 보안 설정

외부에서 접근하는 웹훅에는 반드시 인증을 추가합니다. n8n의 웹훅 노드에서 **Authentication** → **Header Auth** 또는 **Basic Auth**를 설정합니다.

---

## 자주 쓰는 n8n 표현식

n8n의 표현식 엔진은 JavaScript 기반입니다.

```javascript
// 이전 노드의 특정 필드 참조
{{ $json.fieldName }}

// 특정 노드의 출력 참조
{{ $node["NodeName"].json.field }}

// 현재 시간
{{ $now.toISO() }}

// 날짜 포맷
{{ $now.format("YYYY-MM-DD") }}

// 배열 첫 번째 항목
{{ $json.items[0] }}

// 조건 표현식
{{ $json.status === "active" ? "활성" : "비활성" }}
```

---

n8n은 처음에는 설정이 번거로워 보이지만, 한 번 구성해두면 반복 작업을 완전히 자동화할 수 있습니다. 특히 AI 노드와 결합하면 단순 자동화를 넘어 지능형 파이프라인을 구축할 수 있습니다. 저는 현재 이메일 분류, 콘텐츠 수집, 주간 리포트 생성, GitHub PR 알림 등 20개 이상의 워크플로우를 n8n으로 운영하고 있으며, 덕분에 주당 약 5시간의 반복 작업을 줄였습니다.
