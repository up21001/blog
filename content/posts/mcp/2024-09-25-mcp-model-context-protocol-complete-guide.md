---
title: "MCP(Model Context Protocol) 완전 가이드 — Claude가 외부 도구를 쓰는 방법"
date: 2024-09-25T08:00:00+09:00
lastmod: 2024-10-02T08:00:00+09:00
description: "Anthropic이 공개한 MCP(Model Context Protocol)의 개념, 아키텍처, 서버 설정 방법, 그리고 파일시스템·GitHub·웹 검색 연동 실전 예시를 13년 차 엔지니어가 상세히 정리합니다."
slug: "mcp-model-context-protocol-complete-guide"
categories: ["mcp"]
tags: ["MCP", "Model Context Protocol", "Claude", "AI 도구 연동", "Anthropic"]
series: []
draft: false
---

![MCP 아키텍처](/images/mcp-model-context-protocol-2026.svg)

Claude가 파일을 읽고, GitHub PR을 열고, 웹을 검색하는 장면을 보신 적이 있으신가요? 이 모든 것을 가능하게 하는 표준이 **MCP(Model Context Protocol)**입니다. Anthropic이 2024년 11월에 공개한 이 오픈 표준은, LLM이 외부 도구와 데이터 소스를 연결하는 방식을 하나의 프로토콜로 통일합니다. 지금부터 MCP의 개념부터 실전 설정까지 빠짐없이 다루겠습니다.

---

## MCP란 무엇인가

MCP는 **AI 호스트(LLM 앱)와 외부 도구(서버) 사이의 통신 규약**입니다. USB-C가 다양한 기기를 하나의 케이블로 연결하듯, MCP는 Claude·GPT·Gemini 같은 여러 모델이 공통된 방식으로 외부 리소스에 접근할 수 있게 해줍니다.

MCP 이전에는 각 애플리케이션이 파일 읽기, API 호출, DB 쿼리를 모두 자체 구현해야 했습니다. 모델이 바뀌면 모든 연동 코드를 다시 작성해야 했고, 보안 정책을 일관성 있게 유지하기도 어려웠습니다. MCP는 이 문제를 해결합니다.

### MCP의 세 가지 핵심 구성 요소

**MCP Host(호스트)**: LLM을 실행하는 애플리케이션입니다. Claude Desktop, Claude.ai, Cursor IDE, 또는 여러분이 직접 만든 앱이 여기에 해당합니다.

**MCP Client(클라이언트)**: 호스트 내부에서 MCP 서버와 통신을 중계하는 컴포넌트입니다. JSON-RPC 2.0 프로토콜을 사용해 서버와 대화합니다.

**MCP Server(서버)**: 실제 기능을 제공하는 경량 프로세스입니다. 파일시스템 접근, GitHub API 호출, 데이터베이스 쿼리 등을 수행합니다. 서버는 `Tools`, `Resources`, `Prompts` 세 가지 타입의 기능을 노출할 수 있습니다.

---

## MCP 아키텍처 상세

### 통신 프로토콜

MCP는 **JSON-RPC 2.0**을 기반으로 합니다. 호스트가 `tools/call` 같은 메서드를 요청하면 서버가 결과를 반환하는 단순한 구조입니다.

### 트랜스포트 방식

MCP는 두 가지 트랜스포트를 지원합니다.

**stdio (Standard I/O)**: 로컬 서버에 적합합니다. 호스트가 서버 프로세스를 자식 프로세스로 실행하고, 표준 입출력으로 통신합니다. 네트워크가 필요 없어 보안성이 높고 레이턴시가 낮습니다.

**HTTP + Server-Sent Events (SSE)**: 원격 서버에 적합합니다. 클라이언트가 HTTP POST로 요청을 보내고, 서버는 SSE 스트림으로 응답합니다. 이 방식은 여러 호스트가 하나의 서버를 공유할 때 유용합니다.

### 서버가 제공하는 기능 타입

| 타입 | 설명 | 예시 |
|------|------|------|
| **Tools** | 모델이 실행할 수 있는 함수 | 파일 읽기, API 호출, 명령 실행 |
| **Resources** | 모델이 읽을 수 있는 데이터 | 파일 내용, DB 레코드, 설정 |
| **Prompts** | 재사용 가능한 프롬프트 템플릿 | 코드 리뷰 템플릿, 번역 지침 |

---

## 공식 MCP 서버 목록

Anthropic과 커뮤니티가 관리하는 주요 공식 서버입니다.

### Anthropic 공식 서버

- `@modelcontextprotocol/server-filesystem` — 로컬 파일시스템 읽기/쓰기
- `@modelcontextprotocol/server-github` — GitHub 리포지토리, PR, Issue 관리
- `@modelcontextprotocol/server-gitlab` — GitLab 연동
- `@modelcontextprotocol/server-google-drive` — Google Drive 파일 접근
- `@modelcontextprotocol/server-slack` — Slack 메시지 읽기/전송
- `@modelcontextprotocol/server-postgres` — PostgreSQL 쿼리 실행
- `@modelcontextprotocol/server-sqlite` — SQLite 데이터베이스 연동
- `@modelcontextprotocol/server-brave-search` — Brave Search API를 통한 웹 검색
- `@modelcontextprotocol/server-puppeteer` — 브라우저 자동화

### 인기 커뮤니티 서버

- `mcp-server-cloudflare` — Cloudflare Workers/KV 관리
- `mcp-server-kubernetes` — K8s 클러스터 관리
- `mcp-obsidian` — Obsidian 노트 연동
- `mcp-server-linear` — Linear 이슈 트래커 연동

---

## Claude Desktop에서 MCP 서버 설정하기

### 1단계: Node.js 설치 확인

```bash
node --version  # v18 이상 권장
npm --version
```

### 2단계: 설정 파일 위치 확인

Claude Desktop의 MCP 설정 파일은 운영체제마다 다릅니다.

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### 3단계: 기본 설정 구조

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/yourname/projects",
        "/Users/yourname/documents"
      ]
    },
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
      }
    },
    "brave-search": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-brave-search"
      ],
      "env": {
        "BRAVE_API_KEY": "your_brave_api_key"
      }
    }
  }
}
```

### 4단계: Claude Desktop 재시작

설정 파일을 저장한 후 Claude Desktop을 완전히 종료하고 다시 실행합니다. 좌측 하단의 툴 아이콘(망치 모양)을 클릭해 서버가 정상 연결됐는지 확인합니다.

---

## 실전 활용 예시

### 예시 1: 파일시스템 서버로 코드 리뷰

파일시스템 서버를 연결하면 Claude에게 이렇게 요청할 수 있습니다.

```
/Users/myproject/src/auth.ts 파일을 읽고 보안 취약점을 찾아줘.
```

Claude는 MCP를 통해 실제 파일을 읽고, 코드를 분석한 후 구체적인 보안 이슈를 짚어줍니다. 파일 경로를 복사해서 붙여넣을 필요가 없습니다.

### 예시 2: GitHub 서버로 PR 자동 작성

```
현재 main 브랜치와 feature/auth 브랜치의 차이를 분석하고,
PR 제목과 설명을 작성한 후 PR을 열어줘.
```

Claude가 `git diff`에 해당하는 작업을 MCP로 수행하고, PR을 자동으로 생성합니다.

### 예시 3: PostgreSQL 서버로 데이터 분석

```
지난 30일간 신규 가입자 수를 날짜별로 집계하고,
이탈률이 가장 높은 날의 특이사항을 분석해줘.
```

Claude가 SQL 쿼리를 작성하고 실행한 후, 결과를 분석해 인사이트를 제공합니다.

---

## 직접 MCP 서버 만들기

간단한 Python MCP 서버 예시입니다.

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import mcp.types as types

server = Server("my-custom-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_weather",
            description="특정 도시의 현재 날씨를 가져옵니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "날씨를 조회할 도시 이름"
                    }
                },
                "required": ["city"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_weather":
        city = arguments["city"]
        # 실제 날씨 API 호출 로직
        weather_data = fetch_weather(city)
        return [TextContent(type="text", text=f"{city} 현재 날씨: {weather_data}")]
    raise ValueError(f"알 수 없는 도구: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

이 서버를 Claude Desktop에 등록하면 됩니다.

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/path/to/weather_server.py"]
    }
  }
}
```

---

## TypeScript로 MCP 서버 만들기

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "my-ts-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "calculate",
      description: "두 숫자를 더합니다",
      inputSchema: {
        type: "object",
        properties: {
          a: { type: "number" },
          b: { type: "number" },
        },
        required: ["a", "b"],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "calculate") {
    const { a, b } = request.params.arguments as { a: number; b: number };
    return {
      content: [{ type: "text", text: `결과: ${a + b}` }],
    };
  }
  throw new Error(`Unknown tool: ${request.params.name}`);
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

---

## MCP 보안 고려사항

MCP 서버를 운영할 때 반드시 지켜야 할 보안 원칙이 있습니다.

**최소 권한 원칙**: 파일시스템 서버에는 꼭 필요한 디렉토리만 경로로 지정합니다. 홈 디렉토리 전체를 노출하지 않습니다.

**API 키 관리**: 서버 설정 파일에 API 키를 직접 넣지 말고, 환경 변수나 시스템 키체인을 사용합니다.

**원격 서버 검증**: 서드파티가 제공하는 원격 MCP 서버를 사용할 때는 소스를 반드시 검토합니다. 악의적인 서버는 민감한 데이터를 외부로 전송할 수 있습니다.

**샌드박스 실행**: 프로덕션 환경에서는 MCP 서버를 컨테이너나 별도의 사용자 계정으로 격리하여 실행합니다.

---

## MCP vs 기존 함수 호출(Function Calling)의 차이

| 구분 | 기존 함수 호출 | MCP |
|------|--------------|-----|
| 표준화 | 모델별 상이 | 공통 표준 |
| 재사용성 | 앱마다 재구현 | 서버 한 번 작성으로 재사용 |
| 멀티 모달 지원 | 제한적 | 텍스트, 이미지, 파일 모두 지원 |
| 에코시스템 | 파편화 | Anthropic 중심 통합 생태계 |
| 보안 제어 | 앱 수준 | 서버 수준 격리 |

---

## MCP 디버깅

MCP 서버가 정상 작동하지 않을 때 디버깅하는 방법입니다.

**MCP Inspector 사용**:

```bash
npx @modelcontextprotocol/inspector
```

브라우저에서 `http://localhost:5173`으로 접속하면 서버의 도구 목록 확인, 직접 호출 테스트가 가능합니다.

**Claude Desktop 로그 확인**:

```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp*.log

# Windows
Get-Content "$env:APPDATA\Claude\logs\mcp*.log" -Wait
```

---

## 앞으로의 MCP 생태계

MCP는 Anthropic이 공개한 이후 빠르게 성장하고 있습니다. 2026년 현재 300개 이상의 공식·커뮤니티 서버가 등록되어 있으며, Cursor, Zed, Replit 같은 IDE들도 MCP를 지원합니다. Microsoft의 GitHub Copilot 역시 MCP 통합을 준비 중입니다.

MCP는 단순히 Claude를 위한 프로토콜이 아니라, LLM과 외부 세계를 연결하는 표준 인터페이스로 자리 잡고 있습니다. 지금 파일시스템 서버 하나를 연결해보는 것만으로도, AI 어시스턴트의 활용도가 전혀 다른 수준으로 높아짐을 체감하실 수 있을 것입니다.

13년 동안 여러 외부 연동을 직접 구현해왔지만, MCP처럼 표준화된 방식으로 AI와 도구를 연결하는 접근은 확실히 다릅니다. 한 번 배워두면 어떤 MCP 지원 LLM에서든 동일한 서버를 재사용할 수 있으니, 지금 투자할 가치가 충분합니다.
