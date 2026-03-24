---
title: "OpenAI Remote MCP란 무엇인가: Responses API에서 외부 도구를 연결하는 실무 가이드"
date: 2023-12-02T08:00:00+09:00
lastmod: 2023-12-03T08:00:00+09:00
description: "OpenAI remote MCP란 무엇인지, Responses API에서 어떻게 연결하는지, approvals와 allowed_tools를 왜 같이 설계해야 하는지, 공식 문서를 바탕으로 정리합니다."
slug: "openai-remote-mcp-practical-guide"
categories: ["mcp"]
tags: ["OpenAI Remote MCP", "Responses API", "Model Context Protocol", "MCP", "OpenAI Tools", "AI 에이전트", "Tool Calling"]
featureimage: "/images/openai-remote-mcp-workflow-2026.svg"
series: ["AI Agent Tooling 2026"]
draft: false
---

`OpenAI remote MCP`는 2026년 AI 애플리케이션 개발자라면 반드시 이해해야 하는 주제입니다. 함수 호출만으로는 부족하고, 외부 서비스와 문서 시스템, 업무 도구를 표준 방식으로 연결해야 하는 요구가 빠르게 늘고 있기 때문입니다. OpenAI는 이 지점에서 Responses API 안에 `mcp` 도구 타입을 넣어 원격 MCP 서버와 커넥터를 다룰 수 있게 하고 있습니다.

OpenAI 공식 문서는 remote MCP servers와 connectors를 사용해 모델에 새로운 기능을 부여할 수 있다고 설명합니다. 그리고 승인, 허용 도구 제한, 인증, 안전성까지 별도 섹션으로 다루고 있습니다. 즉, 이 기능은 단순 데모가 아니라 실제 프로덕션 설계 이슈로 봐야 합니다.

![OpenAI Remote MCP 워크플로우](/images/openai-remote-mcp-workflow-2026.svg)

## 이런 분께 추천합니다

- Responses API에 외부 도구를 붙이려는 개발자
- function calling과 remote MCP의 역할 차이가 궁금한 팀
- `OpenAI remote MCP`, `Responses API mcp`, `allowed_tools`, `require_approval`을 정리하고 싶은 독자

## OpenAI remote MCP란 무엇인가요?

OpenAI의 remote MCP는 Responses API에서 외부 MCP 서버를 도구처럼 연결해 사용하는 방식입니다. 공식 가이드 기준으로, `tools` 배열 안에 `type: "mcp"` 항목을 추가하고 `server_url`과 승인 정책 등을 전달합니다.

개념 예시는 아래와 같습니다.

```python
from openai import OpenAI

client = OpenAI()

resp = client.responses.create(
    model="gpt-5",
    tools=[{
        "type": "mcp",
        "server_label": "docs",
        "server_url": "https://example.com/sse",
        "require_approval": "never",
        "allowed_tools": ["search", "fetch"]
    }],
    input="최근 배포 문서를 찾아 요약해줘"
)
```

핵심은 모델이 임의의 외부 서비스 API를 직접 이해하는 것이 아니라, MCP 서버가 노출하는 도구 정의를 가져와 그 안에서 동작한다는 점입니다.

## Connectors와는 무엇이 다른가요?

OpenAI 공식 문서는 connectors와 remote MCP를 같은 큰 도구 계층에서 설명하지만, 관리 주체가 다릅니다.

| 항목 | Connectors | Remote MCP |
|---|---|---|
| 운영 주체 | OpenAI-maintained wrapper | 제3자 또는 직접 운영 서버 |
| 연결 방식 | `connector_id` | `server_url` |
| 활용 예 | Gmail, Google Drive | 자체 문서 서버, 내부 도구, 공식 MCP 서버 |

즉, connectors는 OpenAI가 관리하는 연결이고, remote MCP는 직접 신뢰하고 연결해야 하는 외부 서버입니다.

## 어떻게 동작하나요?

OpenAI 가이드는 과정을 크게 세 단계로 설명합니다.

1. 서버에서 도구 목록을 가져옵니다.
2. 모델이 필요 시 특정 도구를 선택합니다.
3. API가 서버에 실제 도구 호출을 수행하고, 결과를 모델 컨텍스트에 넣습니다.

이 과정에서 `mcp_list_tools`, `mcp_call`, `mcp_approval_request` 같은 출력 항목이 생깁니다. 즉, 단순 텍스트 응답이 아니라 도구 사용 이벤트 흐름을 함께 보게 됩니다.

## `allowed_tools`와 `require_approval`이 왜 중요한가요?

OpenAI 문서는 이 두 설정을 매우 강하게 강조합니다. 이유는 간단합니다. 원격 MCP 서버는 강력하고, 그만큼 위험하기 때문입니다.

### `allowed_tools`

일부 MCP 서버는 수십 개 도구를 노출할 수 있습니다. 문서도 이 경우 비용과 지연이 커질 수 있다고 설명합니다. 그래서 필요한 도구만 가져오는 `allowed_tools`가 중요합니다.

### `require_approval`

OpenAI는 기본적으로 MCP 호출 전에 승인을 요청하도록 설계되어 있습니다. 민감한 액션이 가능한 서버라면 이 승인 흐름을 유지하는 편이 맞습니다.

실무적으로는 이렇게 생각하면 됩니다.

- 검색/조회 중심 서버: 승인 완화 검토 가능
- 쓰기/삭제/외부 액션 서버: 승인 유지가 기본

## 어떤 서버를 연결해야 할까요?

OpenAI 문서는 공식 서버를 우선 신뢰하라고 권고합니다. 예를 들어 서비스 제공자가 직접 운영하는 MCP 서버가 있다면, 제3자 프록시 서버보다 그쪽이 낫습니다.

실무 체크리스트는 아래와 같습니다.

- 서버 운영 주체가 명확한가
- OAuth 또는 적절한 인증이 있는가
- 도구 수가 과도하지 않은가
- 도구 설명이 명확한가
- 민감 데이터 유출 위험이 없는가

## OpenAI가 직접 제공하는 MCP도 있나요?

네. OpenAI는 공식 개발자 문서용 공개 MCP 서버도 제공합니다. 문서 기준 서버 URL은 `https://developers.openai.com/mcp`입니다. 이 서버는 개발자 문서를 검색하고 읽는 용도이며, API를 대신 호출하지는 않습니다.

이 사례는 remote MCP의 좋은 입문 예시입니다. 검색형 도구와 읽기 전용 리소스를 어떻게 MCP로 노출할 수 있는지 보여주기 때문입니다.

## 검색형 키워드로 왜 강한가요?

- `OpenAI remote MCP`
- `Responses API mcp`
- `OpenAI connectors`
- `allowed_tools`
- `require_approval`
- `OpenAI MCP server`

에이전트 개발자와 플랫폼 개발자 모두가 찾는 검색어라 유입 질이 좋습니다.

![Remote MCP 보안 설계 체크리스트](/images/openai-remote-mcp-checklist-2026.svg)

## 추천 카테고리

이 글은 `ai-automation` 카테고리에 두는 것이 가장 맞습니다. 도구 연결 구조와 승인 흐름 설계 자체가 AI 자동화 주제이기 때문입니다.

## 핵심 요약

1. OpenAI remote MCP는 Responses API에서 외부 MCP 서버를 도구처럼 연결하는 방식입니다.
2. `allowed_tools`와 `require_approval`은 성능 옵션이 아니라 보안 설계 요소입니다.
3. 공식 서버, 읽기 전용 서버, 최소 도구 노출 원칙을 우선으로 잡는 편이 안전합니다.

## 참고 자료

- Remote MCP and connectors guide: https://platform.openai.com/docs/guides/tools-remote-mcp
- OpenAI MCP docs server: https://platform.openai.com/docs/docs-mcp
- Build MCP servers for ChatGPT and API integrations: https://platform.openai.com/docs/mcp/

## 함께 읽으면 좋은 글

- [OpenAI Responses API란 무엇인가: 2026년 에이전트형 앱 개발을 위한 실무 가이드](/posts/openai-responses-api-practical-guide/)
- [MCP 서버란 무엇인가: 2026 AI 에이전트 실무를 위한 Model Context Protocol 가이드](/posts/mcp-server-practical-guide-2026/)
- [GitHub Models란 무엇인가: 2026년 저장소 안에서 AI 프롬프트와 평가를 관리하는 방법](/posts/github-models-practical-guide-2026/)
