---
title: "프롬프트 인젝션 방어 실무 가이드: LLM이 속지 않게 만드는 방법"
date: 2023-12-20T08:00:00+09:00
lastmod: 2023-12-21T08:00:00+09:00
description: "프롬프트 인젝션이 왜 위험한지, 어떤 공격 패턴이 흔한지, 그리고 실무에서 어떤 방어층을 쌓아야 하는지 정리한 가이드입니다."
slug: "prompt-injection-defense-practical-guide"
categories: ["prompt-engineering"]
tags: ["Prompt Injection", "LLM Security", "Agent Safety", "Tool Use", "Prompt Defense", "MCP Security"]
featureimage: "/images/prompt-injection-defense-workflow-2026.svg"
draft: false
---

![프롬프트 인젝션 방어 실무 가이드](/images/prompt-injection-defense-workflow-2026.svg)

프롬프트 인젝션은 "모델에게 이상한 말을 시키는 것"보다 훨씬 넓은 문제입니다. 외부 문서, 웹페이지, 이메일, PDF, MCP 서버 응답 속에 숨은 지시문이 에이전트의 행동을 바꾸면, 보안 사고로 바로 이어질 수 있습니다.

이 글은 프롬프트 인젝션을 어떻게 분류하고, 어디서 걸러내며, 어떤 방어층을 쌓아야 하는지 실무 관점에서 정리합니다. 특히 [Remote MCP Security](/posts/cloudflare-remote-mcp-security-practical-guide/), [Cloudflare MCPAgent](/posts/cloudflare-mcpagent-practical-guide/), [Anthropic Tool Use](/posts/anthropic-tool-use-practical-guide/)와 연결해서 보면 설계가 더 선명해집니다.

## 왜 중요한가

프롬프트 인젝션은 단순한 문구 문제가 아닙니다. 에이전트는 외부 텍스트를 "데이터"로 읽어야 하는데, 실제로는 그 안의 지시를 "명령"으로 오해할 수 있습니다.

- 문서 요약 에이전트가 문서 내부 지시를 따르는 경우
- 웹 검색 에이전트가 검색 결과의 악성 지시를 실행하는 경우
- MCP 서버 응답이 시스템 지시를 오염시키는 경우
- 복합 에이전트가 메모리와 도구 호출까지 함께 오염되는 경우

즉 방어 대상은 프롬프트 하나가 아니라 전체 컨텍스트 체인입니다.

## 문제 구조

공격은 보통 다음 패턴으로 들어옵니다.

1. 직접 지시형: "이전 지시를 무시하고..."
2. 은닉형: 문서, 표, 주석 속에 숨은 명령
3. 도구 유도형: 특정 URL, 파일, 함수 호출을 유도
4. 컨텍스트 오염형: 메모리, 검색 결과, 장기 컨텍스트를 오염

여기서 중요한 것은 모델이 지시문을 구분하지 못할 수 있다는 점입니다. 그래서 신뢰 경계를 코드로 나눠야 합니다.

## 실무 대응 방법

방어는 한 겹이 아니라 여러 겹이 필요합니다.

- 입력 정제: 외부 텍스트를 명령과 데이터로 분리
- 출처 표시: 어떤 텍스트가 어디서 왔는지 추적
- 권한 분리: 읽기용 도구와 실행용 도구를 나눈다
- 도구 승인: 위험 작업은 사람 승인 후 실행
- 출력 검사: 정책 위반, 비정상 형식, 과도한 권한 요청 차단

이 구조는 [Cloudflare Remote MCP Security](/posts/cloudflare-remote-mcp-security-practical-guide/) 같은 원격 도구 설계와도 맞닿아 있고, [Guardrails AI](/posts/guardrails-ai-practical-guide/)의 검증 층과도 잘 연결됩니다.

## 체크리스트

- 외부 콘텐츠를 시스템 프롬프트에 직접 섞지 않는가
- 명령과 데이터 경계를 분리했는가
- 위험한 도구는 별도 승인 흐름이 있는가
- 검색 결과와 문서 요약 결과를 신뢰 등급으로 태깅하는가
- 악성 문자열보다 행동 패턴을 함께 검사하는가
- 실패 시 에이전트가 안전하게 중단되는가

## 결론

프롬프트 인젝션 방어는 필터 하나로 해결되지 않습니다. 신뢰 경계, 권한 분리, 승인 흐름, 출력 검증을 함께 둬야 합니다. 특히 도구가 붙은 에이전트는 "모델이 똑똑하면 된다"가 아니라 "오염돼도 덜 위험하게 만든다"는 기준으로 설계해야 합니다.

## 함께 읽으면 좋은 글

- [Remote MCP 아키텍처 가이드](/posts/remote-mcp-architecture-practical-guide/)
- [Cloudflare Remote MCP Security 가이드](/posts/cloudflare-remote-mcp-security-practical-guide/)
- [Anthropic Tool Use 실무 가이드](/posts/anthropic-tool-use-practical-guide/)
- [Guardrails AI 실무 가이드](/posts/guardrails-ai-practical-guide/)
