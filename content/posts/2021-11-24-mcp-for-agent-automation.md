---
title: "MCP로 에이전트 자동화 설계하기: JSON-RPC 라이프사이클과 도구 연동 핵심"
date: 2021-11-24T08:00:00+09:00
lastmod: 2021-11-29T08:00:00+09:00
description: "Model Context Protocol(MCP)의 초기화 흐름, 버전 협상, capability 설계를 바탕으로 에이전트 자동화 아키텍처를 정리합니다."
slug: "mcp-for-agent-automation"
categories: ["ai-agents"]
tags: ["MCP", "AI 에이전트", "JSON-RPC 2.0", "Tool Calling", "자동화 아키텍처"]
draft: false
---

![카테고리 인사이트 맵](/images/category-insight-map.svg)

AI 에이전트 자동화가 복잡해지는 이유는 모델 성능보다 도구 연결 방식이 제각각이기 때문입니다. MCP(Model Context Protocol)는 이 문제를 표준 인터페이스로 줄여 줍니다. 핵심은 "초기화 절차"와 "capability 협상"을 정확히 구현하는 것입니다.

## MCP 기본 구조

MCP는 JSON-RPC 2.0 메시지 위에서 동작하며, 크게 다음 흐름을 따릅니다.

1. 클라이언트 `initialize` 요청
2. 서버 `initialize` 응답 (버전/기능 명시)
3. 클라이언트 `initialized` 알림
4. 이후 tools/resources/prompts 호출

이 순서를 무시하면 연결은 되더라도 예측 불가능한 동작이 자주 발생합니다.

## 자동화 파이프라인에 MCP를 적용할 때 장점

- **표준화된 도구 호출**: 모델/런타임이 달라도 통합 방식이 단순해집니다.
- **기능 협상 가능**: 서버가 지원하지 않는 기능을 초기 단계에서 차단할 수 있습니다.
- **확장성**: 도구 추가 시 클라이언트 코어를 크게 바꾸지 않아도 됩니다.

## 실제 아키텍처 설계 예시

에이전트 자동화를 운영 환경에서 쓰려면 "모델 호출 로직"과 "도구 실행 로직"을 분리해야 합니다. MCP는 이 경계를 명확히 만들어 줍니다.

### 권장 구성

1. **Orchestrator**: 사용자 요청 해석, 실행 계획 수립  
2. **MCP Client Layer**: 버전 협상, 세션 관리, 재시도  
3. **MCP Server(s)**: 도구/리소스/프롬프트 노출  
4. **Audit/Log Layer**: 호출 이력, 실패 원인, 성능 지표 저장

이렇게 분리하면 특정 도구 서버가 교체되어도 오케스트레이션 로직은 거의 유지할 수 있습니다.

## 초기화 시점 상세 체크리스트

- 클라이언트가 지원하는 프로토콜 버전을 명시했는가
- 서버가 반환한 버전을 클라이언트가 수용 가능한가
- capabilities를 내부 기능 플래그로 변환했는가
- 초기화 완료 전 일반 요청을 보내지 않도록 막았는가
- 세션 종료와 재연결 시 상태 정리를 수행하는가

이 체크리스트는 작은 프로젝트에서는 과해 보일 수 있지만, 연결 대상 서버가 늘어날수록 장애를 막아주는 핵심 장치가 됩니다.

## 운영 단계에서 자주 발생하는 문제

### 1) 도구 호출 성공/실패 기준 불일치

일부 서버는 에러를 HTTP 상태가 아니라 payload로 반환합니다. 따라서 transport 레벨과 application 레벨의 실패를 분리해 처리해야 합니다.

### 2) 타임아웃 정책 부재

도구 호출 타임아웃이 없으면 워커가 고착되고 큐가 밀립니다. 요청 종류별 타임아웃 정책과 회로 차단(circuit breaker) 기준이 필요합니다.

### 3) Capability drift

서버 업데이트 후 capability가 바뀌었는데 클라이언트가 캐시된 가정을 유지하면 장애가 발생합니다. 재초기화 시 capability diff를 기록하면 원인 파악이 빨라집니다.

## 도입 순서 제안

1. 핵심 도구 1~2개만 MCP로 연결  
2. 초기화/에러 로깅 안정화  
3. 리소스/프롬프트 확장  
4. 다중 서버 병렬 호출 최적화  
5. 비용/성능 메트릭 기반 자동 라우팅

필자의 경험상 처음부터 모든 기능을 붙이면 복잡도만 커집니다. 작은 성공 케이스를 먼저 만든 뒤 수평 확장하는 방식이 안전합니다.

## 구현 시 실수 포인트

- 버전 협상 실패 케이스를 예외 처리하지 않음
- capability 미확인 상태에서 기능 호출
- JSON-RPC request/response ID 관리 누락

필자의 경험상 초기화 단계 로깅만 제대로 넣어도 운영 장애의 절반은 미리 잡을 수 있습니다.

## 결론

MCP는 "도구를 붙이는 기술"이 아니라 "운영 가능한 자동화 계약"입니다.  
초기화와 capability 협상부터 엄격히 지키면 에이전트 품질이 안정화됩니다.  
자동화 규모가 커질수록 MCP 기반 설계의 효과가 더 크게 드러납니다.

## 참고 자료

- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/specification/2025-03-26/)
- [MCP Overview](https://modelcontextprotocol.io/specification/2025-11-25/basic/index)
- [MCP Lifecycle](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)
