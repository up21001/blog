---
title: "에이전트 복구 런북 실험 74차"
date: 2025-11-13T14:51:00+09:00
lastmod: 2025-11-17T14:51:00+09:00
description: "에이전트 복구 런북 실험 74차의 실무 적용을 위한 실행 가이드입니다."
slug: "agent-recovery-runbook-lab-74-2026"
categories: ["ai-agents"]
tags: ["AI", "운영", "실험", "가이드"]
draft: false
---

![에이전트 복구 런북 실험 74차](/images/agent-recovery-runbook-lab-74-2026.svg)

**에이전트 복구 런북 실험 74차** — 토큰 사용량 이상 급증 대응

이번 실험의 핵심 주제는 **비용 폭증 긴급 차단 런북**입니다. 실무 운영 현장에서 직접 마주친 시나리오를 기반으로 설계했으며, 각 단계의 결과와 교훈을 솔직하게 기록합니다.

## 장애 시나리오 개요

**장애 유형**: 예상치 못한 토큰 사용량 폭증
**영향 범위**: 운영 비용, 서비스 가용성
**심각도**: P1

에이전트가 루프에 빠지거나, 비효율적인 도구를 반복 호출하거나, 잘못된 컨텍스트 관리로 인해 토큰 사용량이 예상의 5배 이상으로 급증하는 경우입니다.

## 비용 이상 감지 알람

```python
class CostGuard:
    def __init__(self, hourly_budget_usd=10.0):
        self.hourly_budget = hourly_budget_usd
        self.current_hour_cost = 0.0
    
    def record_usage(self, tokens_in, tokens_out, model):
        cost = calculate_cost(tokens_in, tokens_out, model)
        self.current_hour_cost += cost
        
        if self.current_hour_cost > self.hourly_budget * 0.8:
            alert_ops_team(self.current_hour_cost, self.hourly_budget)
        
        if self.current_hour_cost > self.hourly_budget:
            raise CostLimitExceeded()
```

## 긴급 차단 절차

**T+0 (알람 수신)**
- 비용 이상 급증 알람 확인
- 비용 폭증 원인 에이전트/세션 식별

**T+5분 (즉각 조치)**
- 해당 에이전트 세션 즉시 종료
- 시간당 토큰 한도 긴급 인하 (기존 50%로)
- 신규 에이전트 세션 임시 제한

**T+30분 (원인 분석)**
- 로그에서 비용 폭증 시작 시점과 패턴 파악
- 루프, 긴 컨텍스트, 비효율적 도구 사용 여부 확인

**T+2시간 (재개)**
- 수정 사항 적용 후 단계적 한도 복구

## 비용 보호 다층 방어

| 레이어 | 조치 | 임계값 |
|--------|------|-------|
| 세션 레벨 | 자동 세션 종료 | $5/세션 |
| 에이전트 레벨 | 경고 + 재확인 요청 | $2/시간 |
| 시스템 레벨 | 신규 세션 차단 | $20/시간 |
| 계정 레벨 | API 키 비활성화 | $100/일 |

## 사후 개선 조치

비용 폭증 사고 후 반드시 수행할 개선 사항:
1. 에이전트 프롬프트에 비용 인식 지시 추가
2. 도구 호출 전 필요성 자체 검토 단계 추가
3. 컨텍스트 자동 압축 임계값 80% → 60%로 낮춤

## 마치며

이번 74차 실험에서 얻은 가장 큰 교훈은 **토큰 사용량 이상 급증 대응**의 중요성입니다. 다음 실험에서는 이번 결과를 바탕으로 한 단계 더 발전된 접근법을 적용할 예정입니다. 실험 결과나 질문이 있으시면 댓글로 공유해 주세요.

