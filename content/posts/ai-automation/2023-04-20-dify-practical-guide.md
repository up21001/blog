---
title: "Dify란 무엇인가: 2026년 LLM 앱 개발 플랫폼 실무 가이드"
date: 2023-04-20T08:00:00+09:00
lastmod: 2023-04-21T08:00:00+09:00
description: "Dify가 왜 주목받는지, workflows와 knowledge, agents, observability, model provider abstraction, MCP/public API까지 2026년 기준으로 정리한 실무 가이드입니다."
slug: "dify-practical-guide"
categories: ["ai-automation"]
tags: ["Dify", "LLM App Platform", "Workflow", "Knowledge", "Agents", "Observability", "Model Providers"]
series: ["AI Agent Tooling 2026"]
featureimage: "/images/dify-workflow-2026.svg"
draft: false
---

`Dify`는 2026년 기준으로 `LLM app development platform`, `Dify`, `workflow app`, `knowledge base`, `agents`, `observability` 같은 검색어에서 계속 강한 주제입니다. 모델 자체를 만드는 것이 아니라, 모델을 이용한 제품을 빨리 만들고 운영하는 플랫폼이 필요하기 때문입니다.

Dify 공식 문서는 Dify를 agentic app building 플랫폼으로 설명합니다. Workflow와 Chatflow를 중심으로 앱을 만들고, Knowledge로 RAG를 붙이고, Model Providers로 모델 공급자를 추상화하며, Run History와 Tracing으로 실행을 추적합니다. 즉 `Dify란`, `LLM 앱 플랫폼`, `workflow app`, `knowledge base`, `agent builder` 검색 의도와 잘 맞습니다.

![Dify 워크플로우](/images/dify-workflow-2026.svg)

## 이런 분께 추천합니다

- LLM 앱을 빠르게 제품화하고 싶은 팀
- 워크플로우, 지식베이스, 에이전트를 한 플랫폼에서 관리하고 싶은 개발자
- `Dify`, `RAG`, `observability`, `MCP`, `workflow app`을 함께 이해하고 싶은 분

## Dify의 핵심은 무엇인가

핵심은 "앱 빌딩에 필요한 모델, 지식, 워크플로우, 관측성을 한 번에 묶는다"는 점입니다.

| 요소 | 의미 |
|---|---|
| Workflow / Chatflow | 앱 실행 흐름 |
| Knowledge | RAG 기반 지식 연결 |
| Agent node | 도구를 자율적으로 쓰는 에이전트 |
| Model Providers | OpenAI, Anthropic, Ollama 등 추상화 |
| Run History / Tracing | 실행 추적과 디버깅 |
| Tools / MCP | 외부 서비스 연결 |

이 구조 덕분에 Dify는 개발자만 쓰는 프레임워크가 아니라, 팀 전체가 함께 만드는 LLM 앱 플랫폼이 됩니다.

## 왜 지금 주목받는가

Dify는 단순한 챗봇 빌더보다 범위가 넓습니다.

- 워크플로우 앱을 웹앱으로 배포할 수 있다
- 지식베이스로 사내 문서를 붙일 수 있다
- 에이전트 노드로 도구 사용을 넣을 수 있다
- 실행 로그와 tracing으로 운영성을 갖춘다

특히 Model Providers가 워크스페이스 단위로 관리돼서, 프로토타입과 프로덕션의 공급자 분리를 운영하기 좋습니다.

## 어떤 팀에 잘 맞는가

- 내부 업무 자동화나 고객 응대 앱을 빨리 만들고 싶다
- RAG, agent, workflow를 한 플랫폼에서 관리하고 싶다
- 모델 공급자를 환경별로 바꾸고 싶다
- 실행 이력과 tracing이 중요하다

## 실무 도입 시 체크할 점

1. Workflow와 Chatflow 중 먼저 필요한 형태를 고릅니다.
2. Knowledge base를 데이터 소스별로 분리합니다.
3. Model Providers를 개발/운영 환경별로 나눕니다.
4. Run History와 Tracing을 검토하면서 병목을 찾습니다.
5. Tools와 MCP 연결의 권한 범위를 정의합니다.

## 장점과 주의점

장점:

- 앱 빌딩 흐름이 명확합니다.
- RAG와 에이전트 구성이 좋습니다.
- 모델 공급자 추상화가 유용합니다.
- 실행 로그와 tracing이 실무적입니다.

주의점:

- 워크플로우가 커질수록 설계 규칙이 중요합니다.
- 권한과 비용 정책을 먼저 정하지 않으면 운영이 복잡해집니다.
- 플랫폼 기능이 많아서 초반에 범위를 좁히는 게 중요합니다.

![Dify 선택 흐름](/images/dify-choice-flow-2026.svg)

## 검색형 키워드

- `Dify란`
- `LLM 앱 개발 플랫폼`
- `Dify workflow`
- `Dify knowledge base`
- `Dify observability`

## 한 줄 결론

Dify는 2026년 기준으로 워크플로우, 지식, 에이전트, 관측성을 한 플랫폼에서 묶어 LLM 앱을 빠르게 만들고 운영하려는 팀에게 가장 실용적인 선택지 중 하나입니다.

## 참고 자료

- Dify key concepts: https://docs.dify.ai/en/guides/workflow/node/start
- Knowledge: https://docs.dify.ai/en/guides/knowledge-base/readme
- Model Providers: https://docs.dify.ai/en/guides/model-configuration/predefined-model
- Agent node: https://docs.dify.ai/en/use-dify/nodes/agent
- Run History: https://docs.dify.ai/en/guides/workflow/debug-and-preview/history-and-logs

## 함께 읽으면 좋은 글

- [LangGraph란 무엇인가: 2026년 상태 저장 AI 에이전트 오케스트레이션 실무 가이드](/posts/langgraph-practical-guide/)
- [Open WebUI란 무엇인가: 2026년 셀프호스팅 AI 플랫폼 실무 가이드](/posts/open-webui-practical-guide/)
- [RAG 평가 프레임워크가 왜 중요한가: 2026년 AI 품질 검증 실무 가이드](/posts/ragas-practical-guide/)
