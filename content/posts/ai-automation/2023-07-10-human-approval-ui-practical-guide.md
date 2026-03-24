---
title: "Human Approval UI란 무엇인가: AI 승인 요청 화면을 실무적으로 설계하는 방법"
date: 2023-07-10T08:00:00+09:00
lastmod: 2023-07-12T08:00:00+09:00
description: "AI가 사람 승인을 요청하는 UI를 어떻게 구성해야 하는지, 필요한 정보와 승인 버튼, 거절 경로를 어떻게 설계할지 정리합니다."
slug: "human-approval-ui-practical-guide"
categories: ["ai-automation"]
tags: ["Human Approval UI", "Approval UI", "Human in the Loop", "AI Governance", "Audit Log", "Approval Flow"]
series: ["AI Approval Flow 2026"]
featureimage: "/images/human-approval-ui-workflow-2026.svg"
draft: true
---

Human Approval UI는 AI가 사람의 판단을 요청할 때 보여주는 화면입니다. 승인 자체보다 중요한 것은 "무엇을 승인하는지"를 짧고 정확하게 보여주는 일입니다. 설명이 부족하면 사용자는 승인하지 못하고, 설명이 과하면 검토 시간이 길어집니다.

이 글은 [Human in the Loop](/posts/human-in-the-loop-practical-guide/), [AI Access Control](/posts/ai-access-control-practical-guide/), [Enterprise AI Governance](/posts/enterprise-ai-governance-practical-guide/), [Claude Code GitHub Actions](/posts/claude-code-github-actions-practical-guide/)와 함께 보면 좋습니다.

![Human approval UI workflow](/images/human-approval-ui-workflow-2026.svg)

## 개요

승인 UI는 단순한 모달 창이 아니라 운영 정책의 일부입니다. 어떤 작업이 왜 멈췄는지, 어떤 결과가 예상되는지, 거절하면 다음에 어떻게 되는지를 한 화면에서 보여줘야 합니다.

## 왜 중요한가

- 승인 판단 시간을 줄일 수 있습니다.
- 사용자가 승인 위험을 이해하기 쉬워집니다.
- 반려와 재검토 흐름을 설계하기 좋습니다.
- 승인 기록을 운영 로그와 연결하기 쉽습니다.

## 승인 설계

승인 화면에는 최소한 다음 정보가 있어야 합니다.

1. 수행하려는 작업
2. 작업 대상
3. 예상 영향
4. 추천 이유
5. 승인 또는 거절 후의 다음 단계

이 정보가 없으면 사용자는 맥락을 잃고, 결국 승인 UI는 클릭만 추가한 장치가 됩니다.

![Human approval UI choice flow](/images/human-approval-ui-choice-flow-2026.svg)

### 아키텍처 도식

승인 UI는 에이전트 실행 엔진과 분리해서 설계하는 편이 안전합니다.

![Human approval UI architecture](/images/human-approval-ui-architecture-2026.svg)

- 에이전트는 승인 요청을 생성합니다.
- UI는 요청을 사람이 읽을 수 있게 정리합니다.
- 승인 저장소는 결과를 기록합니다.
- 실행기와 UI는 느슨하게 결합하는 편이 좋습니다.

## 체크리스트

1. 승인 화면이 작업 맥락을 충분히 설명하는가.
2. 승인과 거절의 결과가 명확한가.
3. 반려 후 재요청 경로가 있는가.
4. 승인 기록이 감사 로그로 남는가.
5. 모바일이나 좁은 화면에서도 읽기 쉬운가.

## 결론

Human Approval UI는 사용자의 클릭을 받는 화면이 아니라, 위험한 자동화를 사람이 이해할 수 있게 바꾸는 인터페이스입니다. 정보 구조가 좋아야 승인 품질도 좋아집니다.

### 함께 읽으면 좋은 글

- [Human in the Loop](/posts/human-in-the-loop-practical-guide/)
- [AI Access Control](/posts/ai-access-control-practical-guide/)
- [Enterprise AI Governance](/posts/enterprise-ai-governance-practical-guide/)
- [Claude Code GitHub Actions](/posts/claude-code-github-actions-practical-guide/)
- [Agent Retry Strategy](/posts/agent-retry-strategy-practical-guide/)

