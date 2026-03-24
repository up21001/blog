---
title: "에이전트 복구 런북 실험 71차"
date: 2025-11-13T08:00:00+09:00
lastmod: 2025-11-18T08:00:00+09:00
description: "에이전트 복구 런북 실험 71차의 실무 적용을 위한 실행 가이드입니다."
slug: "agent-recovery-runbook-lab-71-2026"
categories: ["ai-agents"]
tags: ["AI", "운영", "실험", "가이드"]
draft: false
---

![에이전트 복구 런북 실험 71차](/images/agent-recovery-runbook-lab-71-2026.svg)

**에이전트 복구 런북 실험 71차** — 에이전트 루프 장애 처리

이번 실험의 핵심 주제는 **무한 루프 탐지 및 강제 종료**입니다. 실무 운영 현장에서 직접 마주친 시나리오를 기반으로 설계했으며, 각 단계의 결과와 교훈을 솔직하게 기록합니다.

## 장애 시나리오 개요

**장애 유형**: 에이전트 무한 루프
**영향 범위**: 해당 에이전트 세션, 컴퓨팅 리소스
**심각도**: P2

에이전트가 명확한 종료 조건 없이 반복 작업에 빠지는 경우입니다. '정보 부족 → 검색 → 결과 불충분 → 다시 검색' 사이클이 대표적입니다. 이 경우 토큰과 비용이 무한히 소모됩니다.

## 루프 감지 알고리즘

```python
class LoopDetector:
    def __init__(self, window=10, similarity_threshold=0.85):
        self.history = deque(maxlen=window)
        self.threshold = similarity_threshold
    
    def is_looping(self, current_action):
        if not self.history:
            self.history.append(current_action)
            return False
        
        # 최근 행동과 유사도 검사
        similarities = [
            cosine_similarity(current_action, past)
            for past in self.history
        ]
        max_sim = max(similarities)
        
        if max_sim > self.threshold:
            logger.warning(f'Loop detected! Similarity: {max_sim:.2f}')
            return True
        
        self.history.append(current_action)
        return False
```

## 강제 종료 절차

루프 감지 시 에스컬레이션 단계:

1. **경고 주입**: 에이전트에게 루프 가능성 알림 메시지 추가
2. **도구 제한**: 반복 사용된 도구 임시 차단
3. **강제 요약**: '지금까지 작업한 내용으로 최선의 결과를 제출하라' 지시
4. **세션 종료**: 위 조치 후에도 5회 더 루프 시 강제 종료

## 비용 보호 설정

```yaml
agent_limits:
  max_tokens_per_session: 100_000
  max_tool_calls: 50
  max_same_tool_calls: 5  # 동일 도구 연속 호출 제한
  loop_detection:
    enabled: true
    window_size: 8
    similarity_threshold: 0.80
```

## 재발 방지

에이전트 프롬프트에 명확한 종료 조건을 명시하는 것이 근본적인 해결책입니다. '최대 N번 시도 후 가능한 최선의 답변 제공'이라는 제약을 시스템 프롬프트에 포함하세요.

## 마치며

이번 71차 실험에서 얻은 가장 큰 교훈은 **에이전트 루프 장애 처리**의 중요성입니다. 다음 실험에서는 이번 결과를 바탕으로 한 단계 더 발전된 접근법을 적용할 예정입니다. 실험 결과나 질문이 있으시면 댓글로 공유해 주세요.

