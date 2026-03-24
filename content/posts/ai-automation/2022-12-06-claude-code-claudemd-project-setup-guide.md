---
title: "Claude Code CLAUDE.md 작성법 — 프로젝트별 AI 맞춤 설정 완전 가이드"
date: 2022-12-06T08:00:00+09:00
lastmod: 2022-12-11T08:00:00+09:00
description: "CLAUDE.md의 목적과 작성 구조, 프론트엔드·백엔드·모노레포 실전 예시, 팀 도입 팁까지 Claude Code를 프로젝트에 맞게 최적화하는 방법을 정리합니다."
slug: "claude-code-claudemd-project-setup-guide"
categories: ["ai-automation"]
tags: ["CLAUDE.md", "Claude Code", "AI 설정", "프로젝트 자동화"]
series: []
draft: false
---

Claude Code를 처음 쓸 때 가장 답답한 순간이 있습니다. 세션을 시작할 때마다 "이 프로젝트는 Next.js 14를 쓰고, TypeScript strict 모드이고, 테스트는 Jest로 실행해야 해"를 반복해서 설명해야 하는 상황입니다. 두 번이면 모를까, 매번 이 과정을 반복하다 보면 오히려 생산성이 떨어집니다.

CLAUDE.md가 이 문제를 해결합니다. 프로젝트 루트에 이 파일 하나를 만들어두면, Claude는 세션을 시작할 때 자동으로 읽어서 프로젝트 컨텍스트를 파악합니다. 새 팀원에게 주는 온보딩 문서처럼, Claude에게도 똑같은 역할을 합니다.

![CLAUDE.md 구조 — 프로젝트별 AI 맞춤 설정](/images/claude-code-claudemd-guide.svg)

## CLAUDE.md란 무엇인가요?

CLAUDE.md는 Claude Code가 프로젝트를 이해하는 데 필요한 정보를 담은 마크다운 파일입니다. 공식 문서에 따르면 Claude는 세션 시작 시 다음 순서로 이 파일을 찾습니다.

1. 현재 작업 디렉터리의 `CLAUDE.md`
2. 상위 디렉터리의 `CLAUDE.md` (순서대로)
3. 서브디렉터리의 `CLAUDE.md` (해당 디렉터리에서 작업할 때)
4. `~/.claude/CLAUDE.md` (전역 설정)

이 우선순위 덕분에 모노레포에서 루트 CLAUDE.md와 서브패키지별 CLAUDE.md를 분리해서 관리할 수 있습니다.

## CLAUDE.md가 없을 때 vs 있을 때

아무것도 없는 상태로 Claude Code를 시작하면 Claude는 파일 트리 탐색부터 시작합니다. 프로젝트 구조를 파악하고, 사용 중인 기술 스택을 추론하고, 빌드 명령을 찾아야 합니다. 이 과정이 매 세션마다 반복됩니다.

CLAUDE.md가 있으면 첫 메시지부터 바로 작업에 집중할 수 있습니다. Claude가 이미 프로젝트의 기술 스택, 코딩 컨벤션, 금지 사항을 알고 있기 때문입니다.

## CLAUDE.md 핵심 섹션

효과적인 CLAUDE.md는 아래 섹션으로 구성합니다.

### 1. 프로젝트 개요

기술 스택, 목적, 주요 아키텍처를 2-3문장으로 요약합니다.

```markdown
## 프로젝트 개요

이 프로젝트는 Next.js 14 (App Router) + TypeScript + Prisma + PostgreSQL로 구성된
SaaS 플랫폼입니다. 사용자 인증은 NextAuth.js를 사용하며, 스타일링은 Tailwind CSS를 사용합니다.
배포는 Vercel에서 이루어집니다.
```

### 2. 개발 명령어

빌드, 테스트, 린트, 개발 서버 실행 명령을 나열합니다. 이 섹션이 있으면 Claude가 직접 명령을 실행해야 할 때 틀린 명령어를 사용하는 일이 크게 줄어듭니다.

```markdown
## 개발 명령어

\`\`\`bash
# 개발 서버
npm run dev

# 빌드
npm run build

# 테스트
npm test
npm test -- --watch     # 워치 모드
npm test -- --coverage  # 커버리지

# 린트
npm run lint
npm run lint:fix

# 데이터베이스
npx prisma migrate dev  # 마이그레이션 실행
npx prisma studio       # DB GUI 열기
\`\`\`
```

### 3. 코딩 컨벤션

팀이 사용하는 네이밍 규칙, 코드 스타일, 에러 처리 방식을 명시합니다.

```markdown
## 코딩 컨벤션

- 파일명: kebab-case (예: user-profile.tsx)
- 컴포넌트: PascalCase (예: UserProfile)
- 함수/변수: camelCase
- 상수: UPPER_SNAKE_CASE
- TypeScript strict 모드 사용 (any 타입 금지)
- 에러 처리: try/catch보다 Result 타입 선호
- 비동기: async/await 사용 (Promise.then 체인 지양)
- 임포트 순서: 외부 라이브러리 → 내부 모듈 → 타입
```

### 4. 아키텍처 노트

주요 디렉터리 구조와 모듈 역할을 설명합니다.

```markdown
## 아키텍처 노트

- `src/app`: Next.js App Router 페이지
- `src/components`: 재사용 가능한 UI 컴포넌트
- `src/lib`: 비즈니스 로직 및 유틸리티
- `src/server`: 서버 전용 코드 (DB 쿼리, API 로직)
- `prisma/schema.prisma`: 데이터베이스 스키마

상태 관리는 Zustand를 사용합니다. Redux는 사용하지 않습니다.
API 라우트는 `src/app/api` 아래에 위치합니다.
서버 컴포넌트와 클라이언트 컴포넌트를 명확히 구분합니다.
```

### 5. 금지 사항

Claude가 절대로 하지 말아야 할 것을 명확히 명시합니다.

```markdown
## 금지 사항

- `prisma/migrations` 폴더 직접 수정 금지
- `.env` 파일 수정 금지 (`.env.example`은 가능)
- `package.json`의 메이저 버전 업그레이드 금지 (논의 후 진행)
- `src/types/generated` 폴더 수정 금지 (자동 생성)
- 프로덕션 데이터베이스에 직접 연결 금지
```

## 실전 예시: Next.js 프로젝트

```markdown
# CLAUDE.md

## 프로젝트 개요

Next.js 14 App Router + TypeScript + Tailwind CSS + Prisma + PostgreSQL로 구성된
B2B SaaS 플랫폼입니다. 다중 테넌트 아키텍처를 사용하며 각 조직은 독립된 데이터를 가집니다.

## 개발 명령어

\`\`\`bash
npm run dev         # 개발 서버 (포트 3000)
npm run build       # 프로덕션 빌드
npm test            # Jest 테스트
npm run lint        # ESLint 검사
npm run type-check  # TypeScript 타입 검사
npx prisma migrate dev  # DB 마이그레이션
\`\`\`

## 디렉터리 구조

- `src/app`: 페이지 및 API 라우트
- `src/components/ui`: 기본 UI 컴포넌트 (shadcn/ui 기반)
- `src/components/features`: 기능별 컴포넌트
- `src/lib/db.ts`: Prisma 클라이언트 싱글톤
- `src/lib/auth.ts`: NextAuth.js 설정
- `src/server/`: 서버 전용 비즈니스 로직

## 코딩 컨벤션

- TypeScript strict 모드, any 타입 사용 금지
- 컴포넌트는 기본 export, 유틸리티는 named export
- 서버 컴포넌트 기본, 클라이언트 컴포넌트는 'use client' 명시
- API 라우트는 NextResponse 사용
- 에러는 항상 로깅 후 사용자 친화적 메시지 반환

## 테스트

- 단위 테스트: Jest + Testing Library
- E2E 테스트: Playwright (tests/e2e/)
- 새 기능 추가 시 단위 테스트 필수

## 금지 사항

- prisma/migrations 직접 수정 금지
- .env 수정 금지 (.env.example만 수정)
- console.log 프로덕션 코드에 남기기 금지
- src/types/generated/ 수동 수정 금지 (prisma generate로 재생성)
```

## 실전 예시: Python FastAPI 백엔드

```markdown
# CLAUDE.md

## 프로젝트 개요

Python 3.11 + FastAPI + SQLAlchemy 2.0 + PostgreSQL로 구성된 REST API 서버입니다.
비동기 처리를 기본으로 하며, Alembic으로 마이그레이션을 관리합니다.

## 개발 명령어

\`\`\`bash
# 가상환경 활성화
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 개발 서버
uvicorn main:app --reload --port 8000

# 테스트
pytest
pytest --cov=app tests/      # 커버리지

# 린트 및 포맷
ruff check .
ruff format .

# 마이그레이션
alembic upgrade head
alembic revision --autogenerate -m "설명"
\`\`\`

## 코딩 컨벤션

- 타입 힌트 필수 (Python 3.11+ 스타일)
- 비동기 함수는 async def 사용
- 의존성 주입은 FastAPI Depends 활용
- 모델: SQLAlchemy ORM (raw SQL 지양)
- 스키마: Pydantic v2

## 아키텍처

- `app/api/`: 라우터 (엔드포인트만, 비즈니스 로직 없음)
- `app/services/`: 비즈니스 로직
- `app/models/`: SQLAlchemy 모델
- `app/schemas/`: Pydantic 스키마

## 금지 사항

- alembic/versions/ 수동 수정 금지
- .env 파일 수정 금지 (.env.example만 가능)
- 동기 DB 쿼리 사용 금지 (항상 async session 사용)
```

## 실전 예시: 모노레포 구성

모노레포에서는 루트 CLAUDE.md와 패키지별 CLAUDE.md를 분리합니다.

**루트 CLAUDE.md**

```markdown
# CLAUDE.md (루트)

## 모노레포 구조

pnpm workspaces 기반 모노레포입니다.

- `apps/web`: Next.js 웹 앱
- `apps/api`: FastAPI 백엔드
- `packages/ui`: 공유 UI 컴포넌트
- `packages/types`: 공유 타입 정의

## 공통 명령어

\`\`\`bash
pnpm install        # 전체 의존성 설치
pnpm build          # 전체 빌드
pnpm test           # 전체 테스트
pnpm -F web dev     # 웹만 개발 서버
pnpm -F api dev     # API만 개발 서버
\`\`\`

## 공통 컨벤션

- 패키지 간 타입은 packages/types에서 공유
- UI 컴포넌트는 packages/ui에서 관리
```

**apps/web/CLAUDE.md**

```markdown
# CLAUDE.md (web)

루트 CLAUDE.md의 공통 설정을 따릅니다.
이 섹션은 web 앱 특화 설정입니다.

## 개발 명령어

\`\`\`bash
pnpm dev    # 포트 3000
pnpm build
pnpm test
\`\`\`

## 특이사항

- App Router 전용 (Pages Router 코드 작성 금지)
- i18n: next-intl 사용 (messages/ 폴더)
```

## CLAUDE.md 작성 팁

### 팁 1: 500 단어 이내로 작성

너무 길면 Claude가 중요한 정보를 놓칠 수 있습니다. 핵심만 간결하게 작성하는 것이 좋습니다.

### 팁 2: 명령어는 항상 코드블록으로

```markdown
# 나쁜 예
테스트를 실행하려면 npm test를 실행하세요.

# 좋은 예
\`\`\`bash
npm test
\`\`\`
```

Claude가 명령어를 실행할 때 코드블록 안의 내용을 그대로 사용합니다.

### 팁 3: "하지 말아야 할 것"을 명확히

금지 사항을 명확히 쓸수록 효과가 큽니다. "직접 수정하지 마세요"보다 "절대 수정 금지: prisma/migrations/"처럼 단호하게 씁니다.

### 팁 4: 팀원과 함께 관리

CLAUDE.md를 Git으로 관리하면 팀 전체가 같은 컨텍스트를 공유합니다. 새 팀원이 합류하면 CLAUDE.md를 먼저 읽어보는 것만으로도 프로젝트 구조를 파악할 수 있습니다.

### 팁 5: 자주 쓰는 패턴 포함

팀에서 자주 쓰는 코드 패턴을 예시로 넣으면 Claude가 같은 스타일로 코드를 생성합니다.

```markdown
## 코드 패턴 예시

API 라우트 기본 구조:
\`\`\`typescript
export async function GET(request: Request) {
  try {
    const data = await getData()
    return NextResponse.json(data)
  } catch (error) {
    console.error(error)
    return NextResponse.json({ error: '서버 오류' }, { status: 500 })
  }
}
\`\`\`
```

### 팁 6: 환경 정보 포함

Node.js 버전, Python 버전, 주요 라이브러리 버전을 포함하면 호환성 문제를 줄일 수 있습니다.

```markdown
## 환경 정보

- Node.js: 20.x (LTS)
- npm: 10.x
- TypeScript: 5.3
- Next.js: 14.2
```

## CLAUDE.md와 Hooks 조합

CLAUDE.md와 Hooks를 함께 사용하면 시너지가 극대화됩니다.

- **CLAUDE.md**: Claude에게 "이렇게 해줘"라고 알려주는 문서
- **Hooks**: Claude가 "이렇게 하려 할 때" 자동으로 검증하고 처리하는 레이어

예를 들어, CLAUDE.md에 "항상 prettier로 포맷하세요"라고 쓰고, Hooks에서 파일 저장 후 자동으로 prettier를 실행하면, Claude가 규칙을 잊더라도 자동으로 컨벤션이 유지됩니다.

## 핵심 요약

1. CLAUDE.md는 Claude Code가 자동으로 읽는 프로젝트 설명 파일입니다.
2. 개요, 개발 명령어, 코딩 컨벤션, 아키텍처 노트, 금지 사항 섹션으로 구성합니다.
3. 500 단어 이내로 간결하게 작성하고, 명령어는 코드블록으로 표시합니다.
4. Git으로 관리해서 팀 전체가 공유하면 AI 작업의 일관성을 유지할 수 있습니다.

## 참고 자료

- CLAUDE.md 공식 문서: https://docs.anthropic.com/en/docs/claude-code/memory
- Claude Code 메모리 시스템: https://docs.anthropic.com/en/docs/claude-code/overview

## 함께 읽으면 좋은 글

- [Claude Code 완전 정복 — CLI로 AI 코딩 어시스턴트 200% 활용하기](/posts/claude-code-complete-guide-cli/)
- [Claude Code Hooks 완벽 가이드 — 자동화 훅으로 개발 워크플로우 혁신하기](/posts/claude-code-hooks-automation-guide/)
- [Claude API로 나만의 AI 에이전트 만들기 — Python SDK 실전 튜토리얼](/posts/claude-api-python-agent-tutorial/)
