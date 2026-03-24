---
title: "Synthetic Dataset Generation이란 무엇인가: RAG 평가용 데이터를 빠르게 만드는 실무 가이드"
date: 2024-06-09T08:00:00+09:00
lastmod: 2024-06-10T08:00:00+09:00
description: "RAG와 LLM 평가를 위한 synthetic dataset을 어떻게 만들고, 어떤 검증 단계를 거치며, 운영에 어떻게 붙이는지 정리한 가이드입니다."
slug: "synthetic-dataset-generation-practical-guide"
categories: ["ai-automation"]
tags: ["Synthetic Dataset", "RAG Evaluation", "Test Data", "Ragas", "OpenAI Evals", "Retrieval", "LLM Testing"]
series: ["RAG Evaluation 2026"]
featureimage: "/images/synthetic-dataset-generation-workflow-2026.svg"
draft: true
---

평가용 데이터셋이 없으면 RAG 품질은 감으로만 보게 됩니다. Synthetic dataset generation은 실제 운영 질문을 바탕으로 테스트용 질문과 정답, 근거를 빠르게 만드는 방법입니다.

![Synthetic dataset generation workflow](/images/synthetic-dataset-generation-workflow-2026.svg)

## 개요

Synthetic dataset은 사람이 손으로 다 만들기 어려운 평가 데이터를 보완합니다.

보통 아래 형태로 만듭니다.

- 질문
- 기대 답변
- 정답 근거 문서
- 실패 유형 태그

## 왜 중요한가

RAG 평가에서 가장 큰 병목은 모델이 아니라 데이터셋입니다.

- 질문이 부족하면 회귀를 못 잡습니다.
- 실제 사용자 질문과 다르면 평가가 의미 없습니다.
- 정답 근거가 없으면 retrieval 평가가 흔들립니다.

Synthetic data는 이 병목을 줄여 줍니다.

## 생성 방법

실무에서는 다음 흐름이 많습니다.

1. 실제 로그에서 질문 패턴을 모읍니다.
2. 문서군별로 대표 질문을 뽑습니다.
3. LLM으로 변형 질문과 정답 후보를 만듭니다.
4. 사람이나 룰 기반 검증을 거칩니다.
5. 평가셋으로 고정하고 회귀에 사용합니다.

OpenAI Evals와 [Ragas 실무 가이드](/posts/ragas-practical-guide/)를 같이 보면 설계가 쉬워집니다.

## 운영 팁

- 실제 사용자 질문을 기반으로 시작하십시오.
- 문서 버전별로 데이터셋을 나누십시오.
- 생성된 샘플은 반드시 검수하십시오.
- 쉬운 질문과 어려운 질문을 섞으십시오.
- 실패 케이스를 별도 카테고리로 보관하십시오.

## 체크리스트

- 데이터셋이 실제 트래픽을 반영하는가
- 정답 근거가 명시되어 있는가
- 질문 유형이 골고루 포함되어 있는가
- 데이터셋 버전이 관리되는가
- 회귀 테스트에 바로 쓸 수 있는 형태인가

## 결론

Synthetic dataset generation은 평가 자동화의 출발점입니다. 데이터셋이 있어야 지표가 생기고, 지표가 있어야 개선이 가능합니다.

처음에는 작게 만들고, 실제 실패 케이스를 계속 흡수하는 방식이 가장 안정적입니다.

## 함께 읽으면 좋은 글

- [Ragas란 무엇인가: 2026년 RAG 평가와 실험 실무 가이드](/posts/ragas-practical-guide/)
- [OpenAI Evals 실무 가이드: 프롬프트와 모델 품질을 정량적으로 검증하는 방법](/posts/openai-evals-practical-guide/)
- [RAG 평가란 무엇인가: 검색 품질과 답변 품질을 함께 보는 실무 가이드](/posts/rag-evaluation-practical-guide/)
- [RAG Ops 실무 가이드: 검색 품질과 운영 지표를 함께 관리하는 방법](/posts/rag-ops-practical-guide/)

