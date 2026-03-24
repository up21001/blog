---
title: "Aider로 터미널에서 AI 페어 프로그래밍 하기 — 오픈소스 AI 코딩 도구"
date: 2022-09-30T08:00:00+09:00
lastmod: 2022-10-01T08:00:00+09:00
description: "Aider 설치부터 모델 선택, Git 자동 커밋, 실전 워크플로우까지 오픈소스 터미널 AI 페어 프로그래밍 도구 Aider를 완전히 활용하는 방법을 정리합니다."
slug: "aider-terminal-ai-pair-programming"
categories: ["ai-automation"]
tags: ["Aider", "터미널 AI", "페어 프로그래밍", "오픈소스", "Claude"]
series: []
draft: false
---

Cursor나 Copilot 같은 GUI 기반 AI 코딩 도구가 대세인 시대에 굳이 터미널 도구를 쓰는 이유가 있을까요? 있습니다. Aider를 쓰는 이유는 크게 세 가지입니다.

첫째, **어떤 에디터에서도 동작합니다.** Vim, Emacs, 심지어 원격 서버의 nano 환경에서도 Aider는 터미널에서 실행됩니다. 둘째, **오픈소스입니다.** API 키만 있으면 로컬에서 자유롭게 실행할 수 있고, 사용 패턴이 외부로 전송되지 않습니다. 셋째, **Git과 자동으로 통합됩니다.** Aider는 변경 사항마다 자동으로 커밋을 생성합니다.

13년 차 엔지니어로서 임베디드 개발 환경, WSL2, 원격 서버 등 GUI 도구가 불편한 환경에서 Aider를 자주 활용합니다. 이 글에서는 설치부터 실전 워크플로우까지 정리합니다.

![Aider 터미널 AI 페어 프로그래밍 워크플로우](/images/aider-terminal-workflow.svg)

## Aider란?

Aider는 Paul Gauthier가 만든 오픈소스 터미널 AI 코딩 도구입니다. GitHub에서 20,000개 이상의 스타를 받았으며, 활발하게 개발 중입니다.

핵심 특징:
- Python으로 작성된 CLI 도구
- Claude, GPT-4, Gemini, DeepSeek 등 100개 이상의 LLM 지원
- 변경 사항 자동 Git 커밋
- 전체 Git 히스토리를 컨텍스트로 활용 가능
- 멀티파일 편집 지원

Aider의 독특한 점은 **LLM 벤치마크를 자체적으로 운영**한다는 것입니다. [aider.chat/docs/leaderboards](https://aider.chat/docs/leaderboards)에서 어떤 모델이 코딩 작업에서 실제로 잘 작동하는지 정기적으로 측정하고 공개합니다. 도구 선택 시 유용한 참고자료입니다.

## 설치 방법

### 기본 설치

Python 3.9 이상이 설치된 환경에서 pip로 설치합니다.

```bash
pip install aider-chat
```

최신 버전 유지를 위해 주기적으로 업데이트합니다.

```bash
pip install --upgrade aider-chat
```

### pipx를 사용하는 방법 (권장)

전역 환경 오염을 피하려면 pipx를 사용하는 것이 좋습니다.

```bash
pipx install aider-chat
pipx upgrade aider-chat
```

### API 키 설정

사용할 모델의 API 키를 환경변수로 설정합니다.

```bash
# Claude 사용 시
export ANTHROPIC_API_KEY=sk-ant-...

# OpenAI 사용 시
export OPENAI_API_KEY=sk-...

# Gemini 사용 시
export GEMINI_API_KEY=AI...
```

`.bashrc` 또는 `.zshrc`에 추가해두면 영구적으로 적용됩니다.

```bash
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
source ~/.bashrc
```

## 기본 사용법

### 첫 실행

```bash
# Git 저장소 안에서 실행
cd my-project

# Claude Sonnet으로 특정 파일 열기
aider --model claude-3-5-sonnet-20241022 src/api.py src/utils.py
```

실행하면 다음과 같은 프롬프트가 나타납니다.

```
Aider v0.68.0
Models: claude-3-5-sonnet-20241022 with diff edit format, weak model claude-3-haiku-20240307
Git repo: .git with 47 files
Repo-map: using 1024 tokens, auto refresh
Added src/api.py to the chat.
Added src/utils.py to the chat.

You can add files to the chat with /add and drop them with /drop.

>
```

이제 자연어로 작업을 요청할 수 있습니다.

### 기본 명령어

```
/add 파일명        — 파일을 채팅에 추가
/drop 파일명       — 파일을 채팅에서 제거
/files             — 현재 추가된 파일 목록
/diff              — 마지막 변경 사항 diff 보기
/undo              — 마지막 변경 사항 되돌리기
/git 명령어        — git 명령 실행
/run 명령어        — 쉘 명령 실행 후 결과를 AI에 전달
/help              — 전체 명령어 도움말
/exit              — 종료
```

## 모델 선택 가이드

Aider는 100개 이상의 모델을 지원합니다. 어떤 모델을 선택하느냐가 결과 품질과 비용에 직결됩니다.

### 2026년 3월 기준 추천 모델

**최고 품질 (복잡한 작업)**

```bash
# Claude 3.7 Sonnet — 현재 코딩 벤치마크 최상위권
aider --model claude-3-7-sonnet-20250219

# o3-mini — 알고리즘, 수학 문제
aider --model o3-mini
```

**품질/비용 균형 (일상 작업)**

```bash
# Claude 3.5 Sonnet — 가성비 최고
aider --model claude-3-5-sonnet-20241022

# GPT-4o — 범용성 높음
aider --model gpt-4o
```

**저비용 고속 (단순 작업)**

```bash
# DeepSeek Coder — 코딩 특화, 저렴
aider --model deepseek/deepseek-coder

# Gemini Flash — 빠름
aider --model gemini/gemini-2.0-flash-exp
```

### 기본 모델 설정

매번 `--model` 플래그를 입력하기 귀찮다면 `.aider.conf.yml` 파일을 프로젝트 루트 또는 홈 디렉토리에 생성합니다.

```yaml
# ~/.aider.conf.yml
model: claude-3-5-sonnet-20241022
auto-commits: true
dark-mode: true
```

## Git 자동 커밋 기능

Aider의 가장 독특한 기능입니다. AI가 파일을 수정할 때마다 자동으로 Git 커밋을 생성합니다.

```
> JWT 토큰 갱신 함수를 auth.py에 추가해줘

aider: auth.py에 refresh_token() 함수를 추가하겠습니다.
...
Commit 3f8a2c1 feat: add JWT token refresh function to auth.py
```

커밋 메시지도 AI가 변경 내용을 보고 자동으로 생성합니다. 이 기능 덕분에 실험적인 변경을 과감하게 시도할 수 있습니다. 마음에 들지 않으면 `/undo`로 즉시 되돌릴 수 있습니다.

**자동 커밋 비활성화 (원할 경우)**

```bash
aider --no-auto-commits
```

## 실전 워크플로우

### 워크플로우 1: 기능 추가

```bash
aider --model claude-3-5-sonnet-20241022 \
  src/services/user.py \
  src/models/user.py \
  tests/test_user.py
```

```
> User 모델에 소프트 삭제(soft delete) 기능을 추가해줘.
  deleted_at 필드를 추가하고, delete() 메서드가 실제 삭제 대신
  deleted_at에 현재 시간을 기록하도록 바꿔줘.
  기존 쿼리들은 deleted_at IS NULL 조건을 자동으로 포함하도록 해줘.
  테스트 파일에 관련 테스트도 추가해줘.
```

### 워크플로우 2: 버그 수정

`/run` 명령으로 테스트 실행 결과를 AI가 직접 읽게 합니다.

```bash
aider src/api.py tests/test_api.py
```

```
/run pytest tests/test_api.py -v 2>&1 | head -50
```

Aider가 테스트 실패 내용을 읽고 수정을 제안합니다.

```
> 위 테스트 실패를 분석하고 수정해줘
```

### 워크플로우 3: 코드 리뷰 요청

```
> /add src/payment.py
> 이 결제 처리 코드에서 보안 취약점이나 에러 처리 누락이 있는지 검토해줘.
  실제 수정은 하지 말고 분석만 해줘.
```

마지막 줄 "실제 수정은 하지 말고"가 중요합니다. Aider는 기본적으로 변경을 바로 적용하기 때문에, 분석만 원한다면 명시적으로 지시해야 합니다.

### 워크플로우 4: 레거시 코드 문서화

```bash
aider --model claude-3-5-sonnet-20241022 legacy/payment_processor.c
```

```
> 이 C 파일 전체에 Doxygen 형식 주석을 추가해줘.
  각 함수의 파라미터, 반환값, 부수 효과를 설명해줘.
```

Aider가 파일 전체를 읽고 순차적으로 주석을 추가합니다. 5000줄 C 파일에도 적용됩니다.

## 고급 사용법

### Repo Map

Aider는 전체 Git 저장소의 파일 구조와 심볼 맵을 자동으로 생성합니다. 이 "Repo Map" 덕분에 컨텍스트에 명시적으로 추가하지 않은 파일도 AI가 구조를 파악할 수 있습니다.

```bash
# Repo Map 크기 조정 (토큰 수)
aider --map-tokens 2048
```

큰 프로젝트에서는 토큰 수를 늘려야 전체 구조를 더 잘 파악합니다.

### 다중 파일 한 번에 추가

```bash
# 패턴으로 파일 추가
aider src/**/*.py tests/**/*.py
```

### `.aiderignore` 파일

`.gitignore`와 유사하게, AI 컨텍스트에서 제외할 파일을 지정합니다.

```
# .aiderignore
*.log
.env
node_modules/
dist/
__pycache__/
```

민감한 정보가 담긴 파일이나 자동 생성 파일은 여기서 제외하는 것이 좋습니다.

### 코드 없이 대화만 하기 (Ask 모드)

파일을 수정하지 않고 질문만 할 때는 `/ask` 명령을 사용합니다.

```
/ask 이 프로젝트에서 결제 처리 흐름을 전체적으로 설명해줘
```

또는 세션 전체를 읽기 전용 모드로 실행:

```bash
aider --no-auto-commits --dry-run
```

## 비용 관리

Aider를 사용하면 API 비용이 발생합니다. 효율적으로 관리하는 방법:

**비용 추적**

Aider는 세션 종료 시 사용된 토큰 수와 예상 비용을 표시합니다.

```
Tokens: 12,450 sent, 3,200 received. Cost: $0.052 message, $0.187 session.
```

**비용 절감 전략**

1. 일상적인 작업은 Claude 3.5 Sonnet이나 DeepSeek 사용
2. 복잡한 설계 작업에만 Claude 3.7 또는 o3-mini 사용
3. 불필요한 파일을 컨텍스트에서 제거 (`/drop`)
4. Repo Map 크기를 적절하게 조정

월 100달러 이하로 Cursor Pro보다 더 자유롭게 최신 모델을 선택해서 사용할 수 있는 경우도 많습니다.

## Cursor/Copilot과 함께 쓰는 방법

Aider는 Cursor나 Copilot과 함께 사용할 수 있습니다. 둘은 경쟁 관계가 아닙니다.

**실전 조합 예시:**
- **Cursor**: 일상적인 코딩, 인라인 완성, GUI 기반 Composer 작업
- **Aider**: CI/CD 스크립트 작성, 원격 서버 작업, 대규모 리팩토링 자동화

특히 CI/CD 파이프라인이나 Dockerfile, GitHub Actions 워크플로우 같은 인프라 코드 작성에 Aider가 잘 맞습니다. 터미널에서 바로 실행하고, 결과를 확인하고, `/run` 으로 AI에 피드백을 주는 흐름이 자연스럽습니다.

## 마무리

Aider는 "특정 에디터에 묶이고 싶지 않은" 개발자, "API 키만 있으면 어디서든 AI 코딩을 하고 싶은" 개발자에게 최적의 도구입니다. 오픈소스이기 때문에 코드를 직접 보거나 수정할 수도 있고, 자체 서버에 배포해서 팀 전체가 공유하는 방식도 가능합니다.

GUI 도구의 편의성을 포기하는 대신 유연성과 투명성을 얻는 트레이드오프입니다. Vim이나 Emacs를 즐겨 쓰거나, 원격 서버 작업이 많거나, 특정 벤더 락인을 피하고 싶은 개발자라면 Aider는 진지하게 고려할 가치가 있는 도구입니다.

```bash
pip install aider-chat
export ANTHROPIC_API_KEY=your-key
aider --model claude-3-5-sonnet-20241022 your_file.py
```

이 세 줄로 시작할 수 있습니다.
