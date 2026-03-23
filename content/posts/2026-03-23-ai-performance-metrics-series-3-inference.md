---
title: "AI 성능 지표 보고서 시리즈 3편: TTFT, TPS, P95로 추론 성능을 운영지표로 바꾸는 방법"
date: 2026-03-23T20:30:00+09:00
lastmod: 2026-03-23T20:30:00+09:00
description: "LLM 추론 성능의 핵심 지표인 TTFT, TPS, 지연시간 백분위(P95/P99)를 실제 운영 보고서에 적용하는 방법을 정리합니다."
slug: "ai-performance-metrics-series-3-inference"
categories: ["ai-automation"]
tags: ["TTFT", "TPS", "P95", "LLM Latency", "AI 운영 지표"]
draft: false
---

![AI 성능 보고서 대시보드](/images/ai-metrics-report-dashboard.svg)

사용자는 벤치마크 점수가 아니라 체감 속도로 모델을 평가합니다. 따라서 추론 성능 보고서의 핵심은 "평균 지연시간"이 아니라 "느린 구간을 얼마나 통제하느냐"입니다. 여기서 중요한 지표가 TTFT, TPS, P95/P99입니다.

## 핵심 지표 정의

| 지표 | 의미 | 사용자 체감 |
|---|---|---|
| TTFT(Time To First Token) | 첫 토큰이 나오기까지 시간 | "반응 시작이 느리다" |
| TPS(Tokens Per Second) | 초당 생성 토큰 수 | "답변이 끊긴다/빠르다" |
| P95/P99 Latency | 상위 느린 구간 지연시간 | "가끔 매우 느리다" |

필자의 경험상 평균값이 좋아도 P95가 나쁘면 고객 불만은 계속됩니다. 이유는 사용자가 느린 요청을 훨씬 강하게 기억하기 때문입니다.

## 측정 원칙

### 1) 트래픽을 분리해서 측정

- 모델별
- 서비스 티어별
- 요청 유형별(짧은 Q&A, 장문 요약, 코드 생성)

모든 요청을 섞어 평균 내면 문제 구간이 가려집니다.

### 2) 출력 길이를 함께 기록

출력 토큰 수가 길수록 총 지연시간은 늘어납니다. 따라서 성능 비교 시 "토큰 길이 정규화"가 필요합니다.

### 3) 백분위 중심 운영

P50은 기준선, P95는 운영 안정성, P99는 장애 조짐 탐지에 쓰는 것이 일반적입니다.

## OpenAI 문서 기반 실무 팁

OpenAI 공식 문서에서도 지연시간 최적화는 다음 항목을 강조합니다.

- 출력 토큰 수 줄이기
- 입력 토큰 최적화
- 스트리밍 사용으로 체감 대기시간 단축
- 병렬화 가능한 요청 동시 처리
- 모델/서비스 티어를 분리해 측정

즉, 성능 최적화는 인프라 문제만이 아니라 프롬프트/출력 설계 문제이기도 합니다.

## 보고서 예시 템플릿

1. 주간 요청량 / 실패율  
2. TTFT P50/P95/P99  
3. TPS P50/P95  
4. 요청 유형별 지연 상위 3개  
5. 최적화 액션(프롬프트 압축, 캐싱, 스트리밍)  
6. 다음 주 목표치

## 하드웨어 지표와 연결하는 법

GPU 성능 수치(TFLOPS, TOPS)는 중요하지만, 직접 사용자 지연시간으로 연결되지 않을 수 있습니다. 예를 들어 H100의 FP8 처리량이 높아도, 배치 정책이나 큐잉 전략이 잘못되면 TTFT는 오히려 악화될 수 있습니다.

결국 하드웨어 지표는 "잠재 성능", TTFT/TPS/P95는 "실제 서비스 성능"입니다. 보고서에서는 두 레벨을 분리해서 표현해야 오해가 줄어듭니다.

## 결론

추론 성능 보고서의 핵심은 평균 속도가 아니라 느린 요청 통제력입니다.  
TTFT, TPS, P95를 분리해 관리하면 사용자 체감 품질이 안정됩니다.  
다음 편에서는 비용과 안정성을 결합한 최종 운영 KPI 대시보드를 다룹니다.

## 참고 자료

- [OpenAI Latency Optimization Guide](https://platform.openai.com/docs/guides/latency-optimization)
- [OpenAI Production Best Practices](https://developers.openai.com/api/docs/guides/production-best-practices)
- [OpenAI Troubleshooting Latency](https://help.openai.com/en/articles/1000499-troubleshooting-api-errors-and-latency)
- [NVIDIA H100 Datasheet](https://resources.nvidia.com/en-us-tensor-core-gpu/nvidia-h100-datasheet)
