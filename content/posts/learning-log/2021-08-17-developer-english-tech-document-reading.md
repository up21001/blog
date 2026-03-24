---
title: "개발자를 위한 영어 기술 문서 읽기 — 3단계 독해법"
date: 2021-08-17T08:00:00+09:00
lastmod: 2021-08-21T08:00:00+09:00
description: "영어 기술 문서를 빠르고 정확하게 읽는 스캐닝-스키밍-딥리딩 3단계 전략. 개발자가 자주 만나는 영어 패턴과 실전 활용법을 정리합니다."
slug: "developer-english-tech-document-reading"
categories: ["learning-log"]
tags: ["영어공부", "기술문서", "개발자영어", "독해법", "학습전략"]
series: []
draft: false
---

"공식 문서는 영어밖에 없어요. 어떻게 읽어야 하나요?"

이 질문을 참 많이 받습니다. 솔직히 저도 주니어 시절에 영어 기술 문서가 두려웠습니다. 모르는 단어가 나오면 번역기를 켜고, 문장 하나하나 해석하다가 정작 핵심을 놓치는 경우가 많았습니다.

13년 동안 영어 공식 문서, RFC, 논문, GitHub 이슈를 읽으면서 체득한 독해 전략을 정리합니다. 영어 실력보다 **읽는 방법**이 더 중요합니다.

## 왜 번역에 의존하면 안 되는가

GPT나 DeepL로 기술 문서를 번역하는 분들이 많습니다. 빠르고 편리한 건 맞습니다. 하지만 두 가지 문제가 있습니다.

첫째, **기술 용어 번역이 부정확**합니다. "deprecated"를 "더 이상 사용되지 않음"으로 번역하는 것과 그 의미를 뼛속 깊이 아는 것은 다릅니다. "thread-safe"가 "스레드 안전"이 되어버리면 오히려 이해가 어려워집니다.

둘째, **맥락을 잃습니다**. 기술 문서의 "Note that", "Warning", "See also" 같은 구조적 표현들은 문서 내에서 중요한 신호입니다. 번역하면 이 신호가 흐릿해집니다.

## 3단계 독해 전략

![개발자 기술 문서 영어 독해 3단계 전략](/images/developer-english-reading-method.svg)

### 1단계: 스캐닝 (2~3분)

문서 전체를 훑어보는 단계입니다. 단어 하나하나를 읽지 않습니다.

확인할 것:
- 제목과 소제목 구조
- 코드 블록의 위치와 양
- 다이어그램이나 테이블 유무
- 문서의 길이와 섹션 구성

이 단계의 목표는 딱 하나입니다. "이 문서가 무엇을 다루는가?" 모르는 단어가 나와도 괜찮습니다. 전체 지형을 파악하는 것이 목적입니다.

### 2단계: 스키밍 (5~10분)

필요한 섹션을 선택해서 빠르게 읽는 단계입니다. 모든 문장을 다 읽지 않습니다.

집중할 곳:
- 각 섹션의 **첫 문장**과 **끝 문장** (topic sentence)
- **볼드체**, _이탤릭체_, `코드 블록`으로 강조된 부분
- "Note", "Warning", "Important", "Tip" 박스

이 단계에서 "내가 깊이 읽어야 할 섹션이 어딘지" 파악합니다. 전체 문서 중 실제로 필요한 부분은 20~30%인 경우가 많습니다.

### 3단계: 딥 리딩 (20~60분)

선택한 섹션만 정밀하게 읽습니다. 코드를 직접 실행하면서 읽습니다.

이 단계에서만 사전을 찾거나 번역을 참고합니다. 전체를 번역하는 것이 아니라, 이해가 안 되는 특정 문장만 확인합니다.

읽으면서 메모합니다. 노션이나 마크다운 파일에 핵심 내용을 내 말로 정리하는 것이 가장 효과적인 학습 방법입니다.

## 자주 쓰이는 기술 문서 영어 패턴

기술 문서에는 반복적으로 나오는 표현들이 있습니다. 이것들을 패턴으로 익히면 독해 속도가 크게 올라갑니다.

### 설명/정의 패턴

```
X is a/an Y that Z.
→ X는 Z하는 Y입니다.
예: "FastAPI is a modern web framework that allows you to build APIs quickly."

X refers to Y.
→ X는 Y를 가리킵니다.
예: "Dependency injection refers to the pattern of providing dependencies from outside."

X can be described as Y.
→ X는 Y로 설명할 수 있습니다.
```

### 주의/경고 패턴

```
Note that X.          → X를 주의하세요. (중요한 추가 정보)
Warning: X.           → 경고: X. (잘못하면 문제 발생)
Be aware that X.      → X를 인식하고 있어야 합니다.
Caution: X.           → 주의: X. (잠재적 위험)
```

이 단어들은 절대 그냥 넘기면 안 됩니다. 문서 작성자가 특별히 강조한 내용입니다.

### 사용 안내 패턴

```
This is deprecated. Use X instead.
→ 이것은 더 이상 권장하지 않습니다. X를 사용하세요.

X is not recommended for production use.
→ X는 프로덕션 환경에서 권장하지 않습니다.

X requires Y to be installed first.
→ X를 사용하려면 Y가 먼저 설치되어 있어야 합니다.
```

### 함수/API 설명 패턴

```
X takes/accepts Y as argument(s).
→ X는 Y를 인자로 받습니다.

X returns Y.
→ X는 Y를 반환합니다.

X raises/throws Y when Z.
→ X는 Z일 때 Y 예외를 발생시킵니다.

If X is not specified, defaults to Y.
→ X가 지정되지 않으면 기본값은 Y입니다.
```

### 조건/예외 패턴

```
Unless X, Y will happen.
→ X가 아닌 경우, Y가 발생합니다.

Provided that X, Y is possible.
→ X를 충족하면 Y가 가능합니다.

In the event that X, ...
→ X가 발생하는 경우, ...

This behavior is undefined if X.
→ X인 경우 이 동작은 정의되지 않습니다. (매우 위험한 표현)
```

## 실전 예시: FastAPI 공식 문서 읽기

```
"Declare Request Body

When you need to send data from a client (let's say, a browser) to your API,
you send it as a request body.

A request body is data sent by the client to your API.
A response body is the data your API sends to the client.

Your API almost always has to send a response body.
But clients don't necessarily need to send request bodies all the time,
sometimes they only request a path, maybe with some query parameters,
but don't send a body.

To declare a request body, you use Pydantic models with all their power and benefits."
```

**스캐닝**: "Request Body", "Pydantic models" — 요청 바디를 Pydantic으로 다루는 내용.

**스키밍**: 첫 문장 "When you need to send data..." — 클라이언트에서 데이터 보내는 것에 관한 내용.

**딥 리딩**: "response body is the data your API sends to the client" — request/response 방향 정확히 파악. "clients don't necessarily need to send request bodies all the time" — GET 요청에는 body 없어도 된다는 것.

번역 없이도 충분히 이해됩니다.

## 어휘 확장 전략

무작정 단어장을 외우는 것보다 **컨텍스트 속에서 반복 노출**이 효과적입니다.

**기술 문서 전용 단어 노트** 만들기: 모르는 단어를 만나면 그 문장째로 기록해둡니다. 단어만 적는 것이 아니라 쓰인 맥락을 함께 저장합니다.

```
deprecated
→ "This feature is deprecated and will be removed in v3.0."
→ 이전 버전에서 사용되었지만 앞으로 제거될 예정인 기능
```

**같은 단어를 여러 문서에서 보기**: 한 번 본 단어는 다른 문서에서도 의식적으로 찾아봅니다. 5번 보면 안 잊어버립니다.

## 추천 연습 자료

- **MDN Web Docs**: 웹 개발자라면 가장 정석적인 기술 영어
- **Python 공식 문서**: 명확하고 간결한 영어의 모범
- **FastAPI 공식 문서**: 한국어 번역도 있어서 대조하며 읽기 좋음
- **GitHub Issues/PR**: 실제 개발자들의 비공식 영어, 실무에서 쓰이는 표현들

기술 영어는 일반 영어보다 쉽습니다. 쓰이는 어휘가 제한적이고, 문장 구조가 단순하며, 감정 표현이 없습니다. 두려워하지 말고 원문에 자주 노출되는 것이 가장 빠른 방법입니다.
