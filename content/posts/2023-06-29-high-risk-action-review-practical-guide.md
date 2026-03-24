---
title: "High-Risk Action Review란 무엇인가: AI 에이전트 고위험 작업을 검토하는 실무 가이드"
date: 2023-06-29T08:00:00+09:00
lastmod: 2023-07-04T08:00:00+09:00
description: "결제, 삭제, 외부 전송 같은 고위험 작업을 AI 에이전트가 수행하기 전에 어떻게 검토해야 하는지 정리합니다."
slug: "high-risk-action-review-practical-guide"
categories: ["ai-automation"]
tags: ["High-Risk Action Review", "Risk Review", "Human in the Loop", "Approval Flow", "Audit Log", "Agent Safety"]
series: ["AI Approval Flow 2026"]
featureimage: "/images/high-risk-action-review-workflow-2026.svg"
draft: true
---

고위험 작업은 자동화의 편의보다 안전이 우선입니다. 삭제, 결제, 외부 발송, 권한 변경처럼 되돌리기 어려운 행동은 사전 검토가 필요합니다. High-Risk Action Review는 이런 작업을 사람이 확인할 수 있는 구조로 바꾸는 과정입니다.

이 글은 [Agent Approval Flow](/posts/agent-approval-flow-practical-guide/), [Human in the Loop](/posts/human-in-the-loop-practical-guide/), [Risk-Based Automation](/posts/risk-based-automation-practical-guide/), [AI Access Control](/posts/ai-access-control-practical-guide/)와 연결해서 보면 좋습니다.

![High risk action review workflow](/images/high-risk-action-review-workflow-2026.svg)

## 개요

고위험 작업 검토는 에이전트가 실행할 수 있는 작업과 반드시 사람의 판단이 필요한 작업을 분리하는 장치입니다. 핵심은 "검토해야 하는 이유"를 사용자가 바로 이해하게 만드는 것입니다.

## 왜 중요한가

- 잘못된 삭제나 전송은 복구 비용이 큽니다.
- 외부 시스템 연동은 영향 범위가 넓습니다.
- 규정상 승인 없이 실행하면 감사 문제가 생깁니다.
- 검토 흐름이 없으면 자동화의 신뢰가 떨어집니다.

## 승인 UX/정책 설계

고위험 작업 검토는 다음 기준으로 설계하면 됩니다.

1. 사용자에게 작업 영향 범위를 먼저 보여줍니다.
2. 위험 사유를 자동 요약합니다.
3. 승인 시간 제한과 재승인 조건을 둡니다.
4. 검토 결과를 감사 로그와 연결합니다.
5. 취소 또는 롤백 가능 여부를 함께 표시합니다.

검토 화면은 단순 확인창이 아니라, 정책의 결과를 설명하는 UI여야 합니다.

![High risk action review choice flow](/images/high-risk-action-review-choice-flow-2026.svg)

### 아키텍처 도식

![High risk action review architecture](/images/high-risk-action-review-architecture-2026.svg)

에이전트는 작업을 제안하고, 정책 엔진은 위험도를 계산하고, 리뷰 UI는 판단을 보여주고, 감사 로그는 결과를 남깁니다. 이 흐름이 분리되어 있어야 운영 책임이 분명해집니다.

## 체크리스트

- 작업의 되돌림 가능성을 분류했는가
- 승인 전 영향 범위를 보여주는가
- 검토 사유가 자동으로 요약되는가
- 승인 기한과 만료 조건이 있는가
- 승인 이력이 감사 로그에 남는가

## 결론

High-Risk Action Review는 자동화를 멈추는 장치가 아니라, 자동화를 안전하게 확장하는 장치입니다. 위험도가 높은 작업일수록 화면과 정책을 분리해서 설계해야 합니다.

## 함께 읽으면 좋은 글

- [Agent Approval Flow](/posts/agent-approval-flow-practical-guide/)
- [Human Approval UI](/posts/human-approval-ui-practical-guide/)
- [Risk-Based Automation](/posts/risk-based-automation-practical-guide/)
- [AI Access Control](/posts/ai-access-control-practical-guide/)
- [Enterprise AI Governance](/posts/enterprise-ai-governance-practical-guide/)
