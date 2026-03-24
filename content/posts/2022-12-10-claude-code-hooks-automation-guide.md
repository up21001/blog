---
title: "Claude Code Hooks 완벽 가이드 — 자동화 훅으로 개발 워크플로우 혁신하기"
date: 2022-12-10T08:00:00+09:00
lastmod: 2022-12-11T08:00:00+09:00
description: "Claude Code Hooks의 PreToolUse, PostToolUse 설정 방법과 린트 자동화, 보안 차단, 알림 발송 등 실전 활용 예시를 상세히 정리합니다."
slug: "claude-code-hooks-automation-guide"
categories: ["ai-automation"]
tags: ["Claude Code Hooks", "개발 자동화", "settings.json", "AI 워크플로우"]
series: []
draft: false
---

Claude Code를 쓰다 보면 반복적으로 하는 일이 생깁니다. 파일을 수정할 때마다 린트를 돌리고, 특정 명령어 실행 전에 승인을 요청하고, 작업이 끝나면 슬랙으로 알림을 보내는 일들입니다. 이런 작업을 매번 수동으로 하는 대신, Hooks로 자동화할 수 있습니다.

Claude Code Hooks는 Claude가 특정 도구를 실행하기 전후에 사용자 정의 명령을 실행할 수 있는 자동화 레이어입니다. 팀 컨벤션 강제, 보안 정책 적용, 알림 연동을 코드 한 줄 없이 설정 파일만으로 처리할 수 있습니다.

![Claude Code Hooks — 자동화 훅 실행 흐름](/images/claude-code-hooks-automation.svg)

## Hooks가 필요한 이유

13년간 개발하면서 팀 컨벤션 관리가 얼마나 어려운지 직접 겪었습니다. 코드 리뷰에서 포맷팅 이슈를 계속 지적하고, CI에서 린트 에러로 배포가 막히는 일이 반복됩니다. Claude Code를 팀에 도입할 때도 같은 문제가 생깁니다. AI가 만든 코드가 팀 스타일 가이드를 따르지 않거나, 실수로 위험한 명령을 실행할 수 있습니다.

Hooks는 이 문제를 해결합니다. Claude의 행동 전후에 체크포인트를 심어서, 팀이 정한 규칙을 자동으로 강제할 수 있습니다.

## Hooks 기본 구조

Hooks는 `~/.claude/settings.json` 또는 프로젝트의 `.claude/settings.json`에 설정합니다.

```json
{
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Notification": [...],
    "Stop": [...]
  }
}
```

각 훅 타입은 배열로 여러 규칙을 등록할 수 있습니다. 각 규칙은 `matcher`와 `hooks` 두 가지 필드로 구성됩니다.

```json
{
  "matcher": "Write",
  "hooks": [
    {
      "type": "command",
      "command": "echo 'File write detected'"
    }
  ]
}
```

## 훅 타입별 상세 설명

### PreToolUse

Claude가 도구를 실행하기 **전**에 실행됩니다. 검증, 차단, 사전 처리에 사용합니다.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx eslint --fix-dry-run ${TOOL_INPUT_PATH}"
          }
        ]
      }
    ]
  }
}
```

PreToolUse 훅에서 명령이 비정상 종료(exit code != 0)되면, Claude는 해당 도구 실행을 중단합니다. 이 특성을 활용해 위험한 작업을 차단할 수 있습니다.

### PostToolUse

Claude가 도구를 실행한 **후**에 실행됩니다. 후처리, 알림, 포맷 적용에 사용합니다.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write ${TOOL_RESULT_PATH}"
          }
        ]
      }
    ]
  }
}
```

PostToolUse는 도구 실행 결과에 영향을 주지 않으므로 알림이나 로깅에 적합합니다.

### Notification

Claude가 사용자에게 알림을 보낼 때 실행됩니다. 시스템 알림이나 외부 서비스 연동에 활용합니다.

```json
{
  "hooks": {
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude 작업 완료\" with title \"Claude Code\"'"
          }
        ]
      }
    ]
  }
}
```

### Stop

Claude 세션이 종료될 때 실행됩니다. 정리 작업이나 최종 보고에 사용합니다.

## matcher 패턴 이해하기

`matcher` 필드는 어떤 도구에 훅을 적용할지 지정합니다. 도구 이름을 정확히 지정하거나 정규식을 사용할 수 있습니다.

| matcher 값 | 적용 대상 |
|---|---|
| `"Write"` | 파일 쓰기 도구 |
| `"Read"` | 파일 읽기 도구 |
| `"Bash"` | 쉘 명령 실행 도구 |
| `"Edit"` | 파일 편집 도구 |
| `""` (빈 문자열) | 모든 도구 |
| `"Write\|Edit"` | Write 또는 Edit 도구 |

## 환경변수로 컨텍스트 접근

훅 명령에서는 Claude가 실행하려는 도구의 정보를 환경변수로 받을 수 있습니다.

| 환경변수 | 설명 |
|---|---|
| `TOOL_NAME` | 실행 중인 도구 이름 |
| `TOOL_INPUT` | 도구 입력값 (JSON) |
| `TOOL_INPUT_PATH` | 파일 경로 (Write, Read 등) |
| `TOOL_RESULT` | 도구 실행 결과 (PostToolUse) |
| `TOOL_RESULT_PATH` | 결과 파일 경로 (PostToolUse) |

## 실전 예시 모음

### 예시 1: 파일 저장 전 린트 검사

파일을 작성하기 전에 린트를 실행해서 규칙을 지키지 않으면 차단합니다.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'if [[ \"$TOOL_INPUT_PATH\" == *.ts ]]; then npx tsc --noEmit --skipLibCheck && echo ok; fi'"
          }
        ]
      }
    ]
  }
}
```

TypeScript 파일을 쓰기 전에 타입 검사를 실행합니다. 타입 에러가 있으면 파일 작성이 차단됩니다.

### 예시 2: 위험 명령어 차단

`rm -rf`나 `DROP TABLE` 같은 위험한 명령어를 차단합니다.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'if echo \"$TOOL_INPUT\" | grep -qE \"rm -rf|DROP TABLE|truncate\"; then echo \"위험 명령어 차단됨\" >&2; exit 1; fi'"
          }
        ]
      }
    ]
  }
}
```

이 훅은 Bash 도구가 실행될 때마다 명령어 내용을 검사해서, 위험 패턴이 감지되면 실행을 차단합니다.

### 예시 3: 파일 저장 후 자동 포맷

Python 파일을 수정한 뒤 자동으로 black과 isort를 실행합니다.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'if [[ \"$TOOL_RESULT_PATH\" == *.py ]]; then black \"$TOOL_RESULT_PATH\" && isort \"$TOOL_RESULT_PATH\"; fi'"
          }
        ]
      }
    ]
  }
}
```

AI가 생성한 Python 코드도 팀 포맷팅 기준을 자동으로 맞춥니다.

### 예시 4: 슬랙 알림 발송

작업이 완료되면 슬랙 채널에 알림을 보냅니다.

```json
{
  "hooks": {
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "curl -s -X POST $SLACK_WEBHOOK_URL -H 'Content-type: application/json' -d '{\"text\": \"Claude Code 작업 완료: '\"$CLAUDE_NOTIFICATION_MESSAGE\"'\"}'"
          }
        ]
      }
    ]
  }
}
```

슬랙 웹훅 URL을 환경변수로 관리하면 설정 파일에 토큰이 노출되지 않습니다.

### 예시 5: 작업 로그 기록

모든 파일 변경 사항을 타임스탬프와 함께 로그 파일에 기록합니다.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"$(date '+%Y-%m-%d %H:%M:%S') WRITE $TOOL_RESULT_PATH\" >> ~/.claude/activity.log"
          }
        ]
      }
    ]
  }
}
```

나중에 로그를 분석해서 어떤 파일을 얼마나 자주 수정했는지 파악할 수 있습니다.

### 예시 6: 관련 테스트 자동 실행

파일을 수정한 뒤 해당 파일과 관련된 테스트를 즉시 실행합니다.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'TESTFILE=$(echo $TOOL_RESULT_PATH | sed \"s/src/tests/\" | sed \"s/\\.ts$/.test.ts/\"); if [ -f \"$TESTFILE\" ]; then npx jest \"$TESTFILE\" --passWithNoTests; fi'"
          }
        ]
      }
    ]
  }
}
```

`src/api/auth.ts`를 수정하면 자동으로 `tests/api/auth.test.ts`를 실행합니다.

## 프로젝트별 vs 전역 설정

Hooks 설정은 두 레벨에서 관리할 수 있습니다.

**전역 설정** (`~/.claude/settings.json`)
- 모든 프로젝트에 적용
- 개인 워크플로우 설정에 적합

**프로젝트 설정** (`.claude/settings.json`)
- 해당 프로젝트에만 적용
- 팀 전체가 공유 (Git으로 관리)
- 프로젝트별 컨벤션 강제에 적합

팀 프로젝트라면 `.claude/settings.json`을 저장소에 포함시키는 것을 권장합니다. 새 팀원이 클론하면 자동으로 훅이 적용됩니다.

## 훅 디버깅 방법

훅이 예상대로 동작하지 않을 때 디버깅하는 방법입니다.

### 명령을 직접 실행해서 확인

훅 명령을 터미널에서 직접 실행해서 동작을 확인합니다.

```bash
TOOL_INPUT_PATH="src/api/auth.ts" bash -c 'if [[ "$TOOL_INPUT_PATH" == *.ts ]]; then npx tsc --noEmit; fi'
```

### 로그 출력 추가

훅 명령에 `echo` 문을 추가해서 실행 흐름을 추적합니다.

```json
{
  "command": "bash -c 'echo \"훅 실행: $TOOL_NAME $TOOL_INPUT_PATH\" >> /tmp/claude-hooks.log && your-actual-command'"
}
```

### exit code 확인

PreToolUse 훅의 차단 여부는 exit code로 결정됩니다. `exit 0`은 통과, `exit 1`은 차단입니다.

## 훅 작성 시 주의사항

**성능 고려**: 모든 파일 쓰기에 무거운 작업을 걸면 Claude의 응답이 느려집니다. 가능하면 빠르게 실행되는 명령을 사용하세요.

**에러 처리**: 훅 명령이 실패했을 때 어떻게 할지 미리 생각하세요. PreToolUse에서 실패하면 Claude가 해당 작업을 건너뜁니다.

**민감 정보**: API 키, 토큰 같은 민감 정보는 환경변수로 분리하세요. `settings.json`을 Git에 올릴 때 특히 주의합니다.

**플랫폼 호환성**: 팀원이 다양한 OS를 쓴다면 bash 명령이 모든 환경에서 동작하는지 확인하세요. macOS와 Linux는 대부분 호환되지만 Windows는 다를 수 있습니다.

## 팀 도입 전략

Claude Code Hooks를 팀에 도입할 때 단계적으로 진행하는 것을 권장합니다.

**1단계: 로깅만 먼저**

차단이나 강제 없이 로그만 쌓습니다. 어떤 패턴으로 Claude를 사용하는지 파악합니다.

**2단계: 포맷팅 자동화**

PostToolUse로 파일 저장 후 포맷터 자동 실행. 거부감이 가장 적고 효과가 명확합니다.

**3단계: 린트 검사 추가**

PreToolUse로 파일 저장 전 린트 검사. 팀 컨벤션 위반을 사전에 차단합니다.

**4단계: 보안 정책 추가**

위험 명령어 차단, 특정 파일 수정 제한 등 보안 관련 훅을 추가합니다.

## 핵심 요약

1. Hooks는 Claude의 도구 실행 전후에 사용자 정의 명령을 실행하는 자동화 레이어입니다.
2. PreToolUse는 실행 전 검증/차단, PostToolUse는 실행 후 포맷/알림에 적합합니다.
3. `~/.claude/settings.json` 또는 프로젝트의 `.claude/settings.json`에 설정합니다.
4. 팀 프로젝트라면 `.claude/settings.json`을 Git으로 공유해서 컨벤션을 자동으로 강제하는 것을 권장합니다.

## 참고 자료

- Claude Code Hooks 공식 문서: https://docs.anthropic.com/en/docs/claude-code/hooks
- Claude Code 설정 레퍼런스: https://docs.anthropic.com/en/docs/claude-code/settings

## 함께 읽으면 좋은 글

- [Claude Code 완전 정복 — CLI로 AI 코딩 어시스턴트 200% 활용하기](/posts/claude-code-complete-guide-cli/)
- [Claude Code CLAUDE.md 작성법 — 프로젝트별 AI 맞춤 설정 완전 가이드](/posts/claude-code-claudemd-project-setup-guide/)
- [Claude Code vs Cursor AI — 2026년 AI 코딩 도구 현실적인 비교](/posts/claude-code-vs-cursor-ai-comparison-2026/)
