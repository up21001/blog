---
title: "Browser Credential Safety 실무 가이드: 쿠키와 비밀번호를 에이전트에서 안전하게 다루는 방법"
date: 2022-11-10T08:00:00+09:00
lastmod: 2022-11-13T08:00:00+09:00
description: "브라우저 자동화에서 비밀번호, 쿠키, OAuth 토큰, 세션 자격 증명을 안전하게 다루기 위한 실무 전략을 정리합니다."
slug: "browser-credential-safety-practical-guide"
categories: ["ai-automation"]
tags: ["Browser Credential Safety", "Cookies", "Secrets", "OAuth", "AI Agent", "Session Security", "Browser Automation"]
series: ["AI Agent Tooling 2026"]
featureimage: "/images/browser-credential-safety-workflow-2026.svg"
draft: false
---

Browser Credential Safety는 에이전트가 로그인 자격 증명과 세션 토큰을 다룰 때 어떤 값을 어디까지 허용할지 정하는 규칙입니다. 브라우저 자동화는 인증이 붙는 순간부터 보안 문제가 아니라 운영 문제가 됩니다.

![Browser Credential Safety](/images/browser-credential-safety-workflow-2026.svg)

## 개요

브라우저 자동화는 종종 사용자를 대신해 로그인합니다. 이때 비밀번호, 쿠키, OTP, OAuth 토큰, 세션 저장소가 모두 민감 정보가 됩니다.

실무에서는 "에이전트가 로그인할 수 있는가"보다 "무엇을 읽을 수 있고, 무엇을 저장할 수 있고, 무엇을 절대 출력하면 안 되는가"가 더 중요합니다.

## 왜 중요한가

자격 증명이 새면 영향 범위가 넓습니다.

- 계정 탈취로 이어질 수 있습니다.
- 여러 서비스의 세션이 동시에 노출될 수 있습니다.
- 자동화 로그와 스크린샷에 민감 정보가 남을 수 있습니다.
- 프롬프트 인젝션이 토큰 유출로 이어질 수 있습니다.

그래서 credential safety는 브라우저 자동화에서 가장 먼저 설계해야 하는 항목입니다.

## 보안 설계

기본 설계 원칙은 다음과 같습니다.

1. 비밀번호는 프롬프트와 분리합니다.
2. 쿠키와 토큰은 암호화된 vault에만 둡니다.
3. OTP와 복구 코드는 자동화하지 않습니다.
4. 민감 입력은 사용자 승인 후 주입합니다.
5. 출력 필터로 토큰, 이메일, 쿠키 값을 마스킹합니다.

이 규칙을 지키면 브라우저 자동화가 실수하더라도 피해를 줄일 수 있습니다.

## 아키텍처 도식

![Browser Credential Safety Choice Flow](/images/browser-credential-safety-choice-flow-2026.svg)

![Browser Credential Safety Architecture](/images/browser-credential-safety-architecture-2026.svg)

자격 증명 안전성은 브라우저, 비밀 저장소, 승인 UI, 감사 로그가 분리된 구조에서 가장 잘 작동합니다. 에이전트는 비밀 값을 직접 소유하지 않고, 필요한 순간에만 참조하는 편이 좋습니다.

## 체크리스트

- 비밀번호가 프롬프트나 코드에 들어 있지 않은가
- 쿠키와 토큰이 암호화 저장소에 있는가
- OTP를 에이전트가 자동으로 읽지 않는가
- 로그와 스크린샷에 마스킹이 적용되는가
- 자격 증명 주입 시 승인 단계가 있는가
- 계정 회수 절차가 준비되어 있는가

## 결론

Browser Credential Safety는 브라우저 자동화의 마지막 방어선입니다. 로그인 자동화를 할수록 비밀 정보 관리, 세션 분리, 승인 흐름은 같이 가야 합니다.

## 함께 읽으면 좋은 글

- [Secret Management for Agents 실무 가이드](/posts/secret-management-for-agents-practical-guide/)
- [Browser Agent Security 실무 가이드](/posts/browser-agent-security-practical-guide/)
- [Web Session Isolation 실무 가이드](/posts/web-session-isolation-practical-guide/)
- [AI Access Control 실무 가이드](/posts/ai-access-control-practical-guide/)
- [Prompt Injection Defense 실무 가이드](/posts/prompt-injection-defense-practical-guide/)
