---
title: "Agent Approval Flow란 무엇인가: AI 에이전트 승인 단계를 안전하게 설계하는 실무 가이드"
date: 2022-06-04T08:00:00+09:00
lastmod: 2022-06-04T08:00:00+09:00
description: "AI 에이전트의 승인 단계를 어떻게 나눌지, 어떤 작업을 자동 승인하고 어떤 작업을 사람 승인으로 넘길지 정리한 실무 가이드입니다."
slug: "agent-approval-flow-practical-guide"
categories: ["ai-agents"]
tags: ["Agent Approval Flow", "Approval Flow", "Human in the Loop", "AI Governance", "Access Control", "Audit Log"]
series: ["AI Approval Flow 2026"]
featureimage: "/images/agent-approval-flow-workflow-2026.svg"
draft: false
---

Agent Approval Flow는 AI 에이전트가 모든 작업을 바로 실행하지 않고, 위험도에 따라 자동 승인, 조건부 승인, 사람 승인을 나누는 설계입니다. 승인 단계가 없으면 편리해 보이지만, 실제 운영에서는 잘못된 도구 호출과 과도한 권한 사용이 곧바로 사고로 이어집니다.

이 글은 [Human in the Loop](/posts/human-in-the-loop-practical-guide/), [Enterprise AI Governance](/posts/enterprise-ai-governance-practical-guide/), [AI Access Control](/posts/ai-access-control-practical-guide/), [Agent Retry Strategy](/posts/agent-retry-strategy-practical-guide/)와 함께 보면 좋습니다.

![Agent approval flow workflow](/images/agent-approval-flow-workflow-2026.svg)

## 개요

승인 흐름의 핵심은 "무조건 멈추기"가 아니라 "멈춰야 할 지점을 정확히 고르기"입니다. 자주 실행되는 읽기 작업은 자동화하고, 비용이 크거나 되돌리기 어려운 작업만 승인 게이트를 세우는 편이 운영 효율이 좋습니다.

## 왜 중요한가

- 잘못된 배포, 결제, 삭제 작업을 막을 수 있습니다.
- 에이전트의 권한 범위를 명확히 나눌 수 있습니다.
- 감사 로그와 운영 책임 소재를 남기기 쉬워집니다.
- 사람이 개입해야 하는 지점을 줄여서 자동화 효율을 유지할 수 있습니다.

## 승인 설계

승인 흐름은 보통 세 단계로 나누는 편이 좋습니다.

1. 저위험 작업은 즉시 실행합니다.
2. 중간 위험 작업은 조건부 승인으로 넘깁니다.
3. 고위험 작업은 사람 승인을 받은 뒤 실행합니다.

이때 중요한 기준은 작업 종류가 아니라 작업 결과입니다. 예를 들어 같은 `tool call`이라도 조회와 삭제는 다른 위험도로 봐야 합니다.

![Agent approval flow choice flow](/images/agent-approval-flow-choice-flow-2026.svg)

### 아키텍처 도식

실무에서는 아래처럼 계층을 분리하는 구성이 안전합니다.

![Agent approval flow architecture](/images/agent-approval-flow-architecture-2026.svg)

- 정책 계층에서 작업 위험도를 판정합니다.
- 승인 큐에서 대기 중인 작업을 관리합니다.
- 실행 계층은 승인된 작업만 처리합니다.
- 감사 계층은 승인 이유와 실행 결과를 기록합니다.

## 체크리스트

1. 승인 없이 실행 가능한 작업과 반드시 승인해야 하는 작업을 구분했는가.
2. 승인 기준이 사람마다 다르지 않도록 정책화했는가.
3. 승인 요청에 필요한 맥락을 충분히 보여주는가.
4. 승인 거절 후 재시도 경로를 정의했는가.
5. 모든 승인과 실행 결과가 로그로 남는가.

## 결론

Agent Approval Flow는 느리게 만드는 장치가 아니라, 자동화를 오래 운영하게 만드는 장치입니다. 승인 지점을 적절히 설계하면 속도와 안전을 동시에 확보할 수 있습니다.

### 함께 읽으면 좋은 글

- [Human in the Loop](/posts/human-in-the-loop-practical-guide/)
- [Enterprise AI Governance](/posts/enterprise-ai-governance-practical-guide/)
- [AI Access Control](/posts/ai-access-control-practical-guide/)
- [Agent Retry Strategy](/posts/agent-retry-strategy-practical-guide/)
- [Claude Code GitHub Actions](/posts/claude-code-github-actions-practical-guide/)

