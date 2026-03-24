---
title: "에이전트 복구 런북 실험 80차"
date: 2026-02-25T08:00:00+09:00
lastmod: 2026-03-02T08:00:00+09:00
description: "에이전트 복구 런북 실험 80차의 실무 적용을 위한 실행 가이드입니다."
slug: "agent-recovery-runbook-lab-80-2026"
categories: ["ai-agents"]
tags: ["AI", "운영", "실험", "가이드"]
draft: false
---

![에이전트 복구 런북 실험 80차](/images/agent-recovery-runbook-lab-80-2026.svg)

**에이전트 복구 런북 실험 80차** — 의존 시스템 장애 전파 방지

이번 실험의 핵심 주제는 **다운스트림 시스템 장애 시 에이전트 격리**입니다. 실무 운영 현장에서 직접 마주친 시나리오를 기반으로 설계했으며, 각 단계의 결과와 교훈을 솔직하게 기록합니다.

## 장애 시나리오 개요

**장애 유형**: 의존 외부 시스템 다운
**영향 범위**: 해당 시스템을 사용하는 에이전트 전체
**심각도**: P2

에이전트가 의존하는 데이터베이스, 외부 API, 내부 서비스가 다운됐을 때 에이전트가 무한 대기하거나 오류를 전파하는 것을 방지합니다.

## 서킷 브레이커 패턴

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.state = 'CLOSED'  # CLOSED / OPEN / HALF_OPEN
        self.failures = 0
        self.threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
    
    def call(self, fn, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise CircuitOpenError('Service unavailable')
        
        try:
            result = fn(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
```

## 의존 시스템 다운 시 에이전트 행동 설계

의존 시스템 상태에 따른 에이전트 행동 매트릭스:

| 시스템 상태 | 에이전트 행동 |
|------------|-------------|
| 정상 | 표준 처리 |
| 지연 (<5초) | 재시도 1회 후 계속 |
| 지연 (>5초) | 타임아웃 처리, 부분 결과 반환 |
| 완전 다운 | 대체 경로 사용 또는 우아한 실패 |
| 데이터 오류 | 즉각 중단, 오염 방지 |

## 의존성 헬스체크 대시보드

에이전트가 의존하는 모든 시스템의 실시간 상태를 한 화면에서 확인할 수 있는 대시보드를 구축합니다. 시스템 다운 감지 시 영향받는 에이전트를 자동으로 식별하여 사전 격리합니다.

## 장애 전파 방지 설계 원칙

1. **비동기 처리**: 동기 호출 최소화로 단일 장애 전파 차단
2. **폴백 메커니즘**: 모든 외부 의존성에 폴백 경로 정의
3. **타임아웃 강제**: 모든 외부 호출에 최대 타임아웃 설정
4. **벌크헤드 패턴**: 서비스별 스레드풀 분리

## 마치며

이번 80차 실험에서 얻은 가장 큰 교훈은 **의존 시스템 장애 전파 방지**의 중요성입니다. 다음 실험에서는 이번 결과를 바탕으로 한 단계 더 발전된 접근법을 적용할 예정입니다. 실험 결과나 질문이 있으시면 댓글로 공유해 주세요.

