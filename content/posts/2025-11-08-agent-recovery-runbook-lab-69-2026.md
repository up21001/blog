---
title: "에이전트 복구 런북 실험 69차"
date: 2025-11-08T08:00:00+09:00
lastmod: 2025-11-12T08:00:00+09:00
description: "에이전트 복구 런북 실험 69차의 실무 적용을 위한 실행 가이드입니다."
slug: "agent-recovery-runbook-lab-69-2026"
categories: ["ai-agents"]
tags: ["AI", "운영", "실험", "가이드"]
draft: false
---

![에이전트 복구 런북 실험 69차](/images/agent-recovery-runbook-lab-69-2026.svg)

**에이전트 복구 런북 실험 69차** — 외부 API 연동 장애 처리

이번 실험의 핵심 주제는 **도구 호출 실패 복구 런북**입니다. 실무 운영 현장에서 직접 마주친 시나리오를 기반으로 설계했으며, 각 단계의 결과와 교훈을 솔직하게 기록합니다.

## 장애 시나리오 개요

**장애 유형**: 외부 도구(API) 호출 실패
**영향 범위**: 특정 도구에 의존하는 에이전트 작업
**심각도**: P1-P3 (도구 중요도에 따라)

에이전트가 파일 시스템, 웹 검색, 데이터베이스 등 외부 도구를 호출할 때 실패가 발생하면 에이전트의 전체 작업이 중단될 수 있습니다.

## 도구 실패 분류

```python
class ToolFailureType:
    TRANSIENT = 'transient'   # 재시도로 해결 가능
    PERMANENT = 'permanent'   # 재시도 불가
    DEGRADED = 'degraded'     # 제한적 기능만 가능

def classify_failure(error):
    if isinstance(error, (TimeoutError, RateLimitError)):
        return ToolFailureType.TRANSIENT
    elif isinstance(error, (NotFoundError, PermissionError)):
        return ToolFailureType.PERMANENT
    elif isinstance(error, PartialResponseError):
        return ToolFailureType.DEGRADED
```

## 복구 전략별 대응

**TRANSIENT (일시적 오류)**
- 지수 백오프로 최대 3회 재시도
- 재시도 간격: 1s, 2s, 4s

**PERMANENT (영구적 오류)**
- 대체 도구로 동일 작업 시도
- 대체 도구 없으면 에이전트에게 도구 없이 작업 계속 지시

**DEGRADED (부분 기능)**
- 사용 가능한 기능 범위 내에서 작업 재구성
- 사용자에게 제한 사항 명시

## 실제 장애 케이스 예시

웹 검색 도구가 429 (Rate Limit)로 실패했을 때:
1. 15초 대기 후 재시도 → 성공 (전체 케이스의 72%)
2. 1분 대기 후 재시도 → 성공 (추가 19%)
3. 캐시된 최근 검색 결과 활용 → 부분 해결 (7%)
4. 검색 없이 에이전트 자체 지식으로 응답 → 최후 수단 (2%)

## 사전 방어 설계

도구 호출 실패를 미리 대비하는 설계 원칙:
1. 모든 도구에 타임아웃 설정
2. 중요 도구는 동등 대체 도구 지정
3. 도구 호출 결과 캐싱 (TTL 설정)
4. 에이전트 프롬프트에 '도구 실패 시 대체 행동' 명시

## 마치며

이번 69차 실험에서 얻은 가장 큰 교훈은 **외부 API 연동 장애 처리**의 중요성입니다. 다음 실험에서는 이번 결과를 바탕으로 한 단계 더 발전된 접근법을 적용할 예정입니다. 실험 결과나 질문이 있으시면 댓글로 공유해 주세요.

