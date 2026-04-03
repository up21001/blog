---
title: "gstack 완전 가이드 3부: 실제 브라우저 자동화와 멀티에이전트 병렬 실행"
date: 2026-04-03T11:00:00+09:00
lastmod: 2026-04-03T11:00:00+09:00
description: "gstack의 핵심 고급 기능인 실제 Chromium 브라우저 제어(~100ms 응답), ARIA 기반 Ref 시스템, 그리고 Conductor를 통한 10-15개 에이전트 병렬 실행을 심층 분석합니다. CSS 셀렉터 없이 UI를 자동화하는 혁신적인 방법을 알아보세요."
slug: "gstack-part3-browser-multiagent"
categories: ["ai-agents"]
tags: ["gstack", "브라우저 자동화", "Playwright", "멀티에이전트", "ARIA", "Chromium", "병렬 실행"]
series: ["gstack 완전 가이드"]
series_order: 3
draft: false
---

## AI가 브라우저를 조작한다 — 기존 방식의 한계

AI 에이전트가 웹을 자유롭게 탐색하고 버튼을 클릭하며 양식을 제출하는 시대가 왔다. 그런데 실제로 구현해보면 의외의 난관에 부딪힌다. Selenium이나 Puppeteer 기반의 CSS 셀렉터는 프레임워크가 바뀌면 깨지고, XPath는 DOM 구조 변경에 취약하다. CSP(Content Security Policy)가 강화된 현대 웹앱에서는 스크립트 주입조차 막힌다.

gstack은 이 문제를 완전히 다른 각도로 접근한다. 브라우저 자동화 전체를 **데몬 아키텍처**로 감싸고, UI 요소 식별에 CSS 셀렉터 대신 **ARIA 접근성 트리**를 활용한다. 결과적으로 ~100ms의 응답 속도와 프레임워크 무관(React, Vue, Angular 모두)한 안정성을 동시에 확보했다.

이번 3부에서는 이 고급 기능들을 깊이 파헤친다.

---

## 브라우저 데몬 아키텍처: 3계층 구조의 비밀

{{< figure src="/images/posts/gstack-part3-browser-multiagent/svg-1.svg" alt="3계층 브라우저 데몬 아키텍처" >}}

gstack의 브라우저 제어는 세 개의 계층으로 나뉜다.

### Layer 1: CLI (Bun 바이너리)

사용자 혹은 Claude가 실행하는 진입점이다. `/browse`, `/connect-chrome`, `/setup-browser-cookies` 같은 명령을 받아 Layer 2의 HTTP 서버로 전달한다. Bun 런타임 기반의 단일 바이너리로 배포되어 별도 런타임 설치가 불필요하다.

### Layer 2: HTTP 서버 (로컬호스트)

CLI와 Chromium 사이의 브리지 역할을 한다. 포트는 **10,000~60,000 사이의 랜덤 값**으로 시작해 충돌을 방지한다. 모든 요청에는 Bearer 토큰 인증이 붙는다.

**핵심 성능 포인트:**
- 첫 번째 호출: ~3초 (Chromium 프로세스 시작)
- 이후 호출: ~100~200ms (데몬이 이미 살아있으므로)

이 차이가 결정적이다. 기존 접근법은 매 명령마다 브라우저를 새로 시작하지만, gstack은 데몬이 계속 살아있어 두 번째 요청부터 극적으로 빨라진다.

### Layer 3: Chromium (DevTools Protocol)

실제 Chromium 브라우저 인스턴스다. Playwright가 Chrome DevTools Protocol(CDP)을 통해 제어한다. 자바스크립트 실행, 네트워크 가로채기, 스크린샷 등 브라우저가 할 수 있는 모든 것이 가능하다.

### 상태 파일: `.gstack/browse.json`

데몬의 현재 상태는 `.gstack/browse.json`에 저장된다:

```json
{
  "pid": 12345,
  "port": 34821,
  "token": "Bearer eyJ...",
  "startedAt": "2026-04-03T11:00:00Z",
  "binaryVersion": "1.2.3"
}
```

**30분 유휴 타임아웃**: 아무 명령도 없으면 자동 종료된다. 다음 명령 시 자동 재시작.

**버전 자동 재시작**: `binaryVersion`이 현재 바이너리와 다르면 데몬을 자동으로 재시작한다. 업데이트 후 수동으로 프로세스를 죽을 필요가 없다.

---

## `/browse` 명령 카테고리

`/browse`는 gstack 브라우저 자동화의 핵심 명령이다. 기능별로 세 범주로 나뉜다.

### READ — 현재 상태 파악

```bash
# 현재 페이지 URL 확인
/browse url

# 스크린샷 캡처 (base64 또는 파일 저장)
/browse screenshot

# ARIA 트리 스냅샷 (ref 시스템 활성화)
/browse snapshot -i

# 페이지 전체 텍스트 추출
/browse text

# 네트워크 요청 로그 확인
/browse network-log
```

### WRITE — 페이지 조작

```bash
# 특정 URL 탐색
/browse navigate https://example.com

# ref 기반 클릭
/browse click @e1

# 텍스트 입력
/browse type @e2 "입력할 내용"

# 체크박스 토글
/browse check @e4

# 양식 제출
/browse submit @e5

# 스크롤
/browse scroll down 300
```

### META — 탭과 세션 관리

```bash
# 새 탭 열기
/browse new-tab https://example.com

# 탭 목록 확인
/browse tabs

# 특정 탭으로 전환
/browse switch-tab 2

# 쿠키 확인
/browse cookies
```

---

## Ref 시스템 혁신: CSS 셀렉터 없이 UI 자동화

{{< figure src="/images/posts/gstack-part3-browser-multiagent/svg-2.svg" alt="Ref 시스템 동작 원리" >}}

gstack의 가장 혁신적인 기능 중 하나가 **Ref 시스템**이다. CSS 셀렉터나 XPath 없이 UI 요소를 안정적으로 식별한다.

### 동작 원리: 3단계

**1단계: ARIA 트리 스냅샷**

```bash
/browse snapshot -i
```

`-i` 플래그를 붙이면 현재 페이지의 ARIA 접근성 트리를 분석하고 모든 상호작용 가능한 요소에 **순번 ref**를 부여한다.

출력 예시:
```
@e1  button "로그인"
@e2  textbox "이메일"
@e3  textbox "비밀번호"
@e4  checkbox "로그인 상태 유지"
@e5  link "회원가입"
@e6  link "비밀번호 찾기"
```

**2단계: Ref → Playwright Locator 매핑**

각 ref는 내부적으로 Playwright의 `role + name` 기반 locator로 변환된다:

- `@e1` → `page.getByRole('button', { name: '로그인' })`
- `@e2` → `page.getByRole('textbox', { name: '이메일' })`

이 매핑이 핵심이다. DOM 구조가 바뀌어도 역할과 이름이 유지되는 한 locator는 안정적으로 동작한다.

**3단계: Ref로 액션 실행**

```bash
/browse type @e2 "user@example.com"
/browse type @e3 "password123"
/browse check @e4
/browse click @e1
```

### Ref 시스템의 장점

**프레임워크 무관**: React, Vue, Angular, Svelte 모두 동일하게 작동한다. 컴포넌트 내부 구현 방식과 무관하게 ARIA 트리만 읽는다.

**CSP 안전**: 스크립트를 페이지에 주입하지 않는다. Content Security Policy가 엄격한 금융, 정부 사이트에서도 동작한다.

**Staleness 자동 감지**: ref가 더 이상 유효하지 않으면(DOM 변경, 페이지 이동 등) 실행 전에 즉시 에러를 throw한다. 잘못된 요소를 클릭하는 silent failure를 방지한다.

### `-C` 플래그: 비-ARIA 요소 처리

ARIA 트리에 노출되지 않는 캔버스, 커스텀 컴포넌트 등은 `-C` 플래그로 커서 좌표 기반 클릭을 사용한다:

```bash
/browse click -C 450 320
```

---

## `/connect-chrome`: Headed 모드와 실시간 모니터링

헤드리스 모드만으로는 부족할 때가 있다. OAuth 로그인, CAPTCHA, 2FA 등은 실제 브라우저 창이 필요하다. `/connect-chrome`이 이를 해결한다.

```bash
/connect-chrome
```

이 명령은 **실제 Chrome 창을 띄우고** 그 세션에 gstack을 연결한다. 사용자가 직접 로그인하는 동안 gstack은 대기하고, 이후 자동화를 이어받는다.

**초록 shimmer 효과**: 연결된 Chrome 창에는 화면 테두리에 초록색 shimmer 애니메이션이 표시된다. "현재 이 브라우저는 gstack이 제어 중"임을 시각적으로 알려주는 안전 피드백이다.

**실시간 모니터링**: 연결 상태에서 콘솔 에러, 네트워크 요청, 팝업 다이얼로그가 실시간으로 캡처된다.

---

## 쿠키 임포트: `/setup-browser-cookies`

로컬 Chrome에 이미 로그인되어 있다면 그 세션 쿠키를 그대로 gstack에 가져올 수 있다.

```bash
/setup-browser-cookies
```

**보안 설계**:
1. Chrome의 쿠키 DB(SQLite)를 직접 읽지 않고 **임시 파일로 복사** 후 읽는다 (읽기 전용 원칙)
2. macOS에서는 쿠키 암호화 키 접근을 위해 **Keychain 다이얼로그**가 표시된다. 사용자 동의 없이는 키에 접근 불가
3. 가져온 쿠키는 gstack 세션에만 유효하며 원본 브라우저에 영향을 주지 않는다

이를 통해 Claude가 사용자와 같은 로그인 상태로 웹앱을 자동화할 수 있다.

---

## 로깅 아키텍처: 크래시에서도 살아남는 로그

gstack의 로깅 시스템은 단순한 파일 쓰기가 아니다. **3개의 링 버퍼**로 구성된 고성능 아키텍처다.

### 링 버퍼 구조

```
콘솔 버퍼   (50,000 엔트리, O(1) 삽입)
네트워크 버퍼 (50,000 엔트리, O(1) 삽입)
다이얼로그 버퍼 (50,000 엔트리, O(1) 삽입)
```

**비동기 플러시**: 1초 간격으로 `.gstack/*.log`에 비동기로 기록한다. 동기 I/O가 아니므로 브라우저 제어 명령의 레이턴시에 영향을 주지 않는다.

**크래시 생존**: 프로세스가 갑자기 죽더라도 최대 1초치 로그만 손실된다. 이미 플러시된 데이터는 디스크에 안전하게 보존된다.

로그 확인:
```bash
# 콘솔 에러/경고
cat .gstack/console.log

# 네트워크 요청/응답
cat .gstack/network.log

# alert, confirm, prompt 다이얼로그
cat .gstack/dialogs.log
```

---

## 멀티에이전트: Conductor와 10-15개 동시 실행

{{< figure src="/images/posts/gstack-part3-browser-multiagent/svg-3.svg" alt="멀티에이전트 병렬 실행 아키텍처" >}}

gstack의 가장 강력한 기능은 단일 에이전트가 아닌 **에이전트 군단**을 조율하는 능력이다.

### Conductor 오케스트레이션

Conductor는 10~15개의 전문 에이전트를 동시에 실행하는 조율 레이어다. 각 에이전트는 특정 역할에 집중한다:

- **CEO 에이전트**: 전략 결정, 인프라 세부사항은 건너뜀
- **백엔드 에이전트**: API 구현, DB 스키마
- **프론트엔드 에이전트**: UI 컴포넌트, 상태 관리
- **디자인 에이전트**: CSS, 접근성, 시각적 일관성
- **테스트 에이전트**: QA, 자동화 테스트

### 스마트 리뷰 라우팅

Conductor의 핵심 지능은 **역할 기반 라우팅**이다. 백엔드 코드 리뷰 요청이 오면 CEO와 백엔드 에이전트에게만 라우팅되고 디자인 에이전트는 건너뛴다. 반대로 CSS 변경은 디자인 에이전트와 프론트엔드 에이전트만 리뷰한다.

이 최적화로 리뷰 처리량이 비약적으로 증가한다.

### 병렬 실행의 실제 속도

순차 실행 vs 병렬 실행 비교:
- **순차 (기존)**: 15개 에이전트 × 평균 2분 = 30분
- **병렬 (gstack)**: 15개 동시 실행 = 약 2~3분

10배 이상의 처리 속도 향상이다.

---

## `/codex`: OpenAI 크로스 모델 리뷰

단일 모델의 편향을 제거하기 위해 gstack은 OpenAI Codex를 교차 검증에 활용한다.

```bash
/codex review src/auth/login.ts
```

**동작 방식**:
1. 지정된 파일/변경사항을 Claude가 분석
2. 동일한 코드를 OpenAI Codex에게도 전송
3. 두 모델의 리뷰 결과를 종합하여 출력

한 모델이 놓친 버그나 보안 이슈를 다른 모델이 잡아낼 가능성이 높다. 특히 보안 감사나 성능 최적화처럼 실수 비용이 높은 작업에 유효하다.

---

## Sidebar Agent: Chrome 사이드패널의 AI

`Sidebar Agent`는 Chrome 확장 프로그램으로 브라우저의 사이드패널에 Claude를 내장한다.

**특징**:
- Chrome 사이드패널에서 직접 에이전트와 대화
- 현재 열린 탭의 DOM, 네트워크 요청에 즉시 접근
- **5분 태스크 제한**: 장시간 실행을 방지하는 안전장치
- 브라우저를 닫지 않고도 실시간 디버깅 가능

**활용 예시**:
```
[사이드패널에서]
"현재 페이지에서 장바구니 추가 버튼이 왜 작동 안 하는지 분석해줘"
```

에이전트가 DOM을 실시간으로 분석하고 네트워크 탭을 확인하며 답변한다.

---

## 보안 모델: 로컬 우선 설계

gstack의 보안은 처음부터 로컬 우선으로 설계되었다.

### 네트워크 격리

```
허용: 127.0.0.1 (loopback only)
차단: 0.0.0.0, 외부 IP, 모든 원격 접근
```

HTTP 서버는 오직 로컬호스트에서만 접근 가능하다. 원격에서 gstack의 브라우저를 제어할 수 있는 방법이 없다.

### Bearer 토큰 인증

모든 HTTP 요청에 Bearer 토큰이 필요하다. 토큰은 데몬 시작 시 랜덤 생성되며 `.gstack/browse.json`에 저장된다. 같은 머신에서 실행 중인 다른 프로세스가 토큰 없이 gstack을 제어할 수 없다.

### 쉘 인젝션 방지

모든 명령 실행은 **명시적 인수 배열** 방식으로 처리된다:

```javascript
// 안전: 명시적 배열
spawn(['chromium', '--headless', url])

// 위험: 쉘 문자열 (gstack은 이 방식을 사용하지 않음)
exec(`chromium --headless ${url}`)
```

URL이나 입력값에 쉘 특수문자가 있어도 인젝션이 불가능하다.

### 읽기 전용 쿠키 DB

Chrome 쿠키 데이터베이스를 직접 열지 않고 임시 파일로 복사 후 읽는다. 원본 DB에 쓰기 잠금이 걸리지 않으며 Chrome 실행 중에도 안전하게 읽을 수 있다.

---

## 정리: gstack 브라우저 자동화의 핵심

gstack이 일반적인 브라우저 자동화 도구와 다른 점 세 가지:

1. **데몬 아키텍처**: 첫 호출 이후 ~100ms 응답. Chromium을 매번 시작하지 않는다.

2. **Ref 시스템**: ARIA 접근성 트리 기반. CSS 셀렉터 불필요, 프레임워크 무관, CSP 안전.

3. **멀티에이전트**: Conductor가 10~15개 에이전트를 동시 실행. 스마트 라우팅으로 효율 극대화.

이 세 가지가 결합되면 단순한 브라우저 제어를 넘어서 **AI 기반의 완전한 웹 자동화 플랫폼**이 된다.

다음 4부에서는 gstack을 실제 프로젝트에 적용한 사례와 고급 트러블슈팅을 다룬다.

---

*gstack 완전 가이드 시리즈*
- [1부: gstack 소개와 핵심 개념](/posts/ai-agents/gstack-part1-introduction/)
- [2부: 설치와 기본 워크플로우](/posts/ai-agents/gstack-part2-installation-workflow/)
- **3부: 실제 브라우저 자동화와 멀티에이전트** ← 현재 글
