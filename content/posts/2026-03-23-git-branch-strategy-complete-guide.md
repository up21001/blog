---
title: "Git 브랜치 전략 완벽 가이드 — GitHub Flow vs Git Flow vs Trunk-based"
date: 2026-03-23T22:50:00+09:00
lastmod: 2026-03-23T22:50:00+09:00
description: "Git Flow, GitHub Flow, Trunk-based Development를 실무 관점에서 비교 분석. 팀 규모와 배포 사이클에 따른 최적의 브랜치 전략 선택법을 13년 경력 엔지니어가 정리합니다."
slug: "git-branch-strategy-complete-guide"
categories: ["software-dev"]
tags: ["Git", "Git Flow", "GitHub Flow", "Trunk-based", "브랜치전략"]
series: []
draft: false
---

"우리 팀은 어떤 브랜치 전략을 써야 할까요?"

기술 면접에서 자주 나오는 질문이기도 하고, 팀이 새로 꾸려질 때마다 반드시 논의하는 주제입니다. 13년 동안 스타트업부터 대기업 SI까지 다양한 조직에서 일하면서 Git Flow, GitHub Flow, Trunk-based Development를 모두 써봤습니다. 각각 잘 맞는 환경이 있고, 억지로 적용하면 오히려 팀 속도를 죽입니다.

이 글에서는 세 전략을 실무 관점에서 비교하고, 상황별 선택 기준을 정리합니다.

## Git Flow — 체계적인 릴리즈 관리

Vincent Driessen이 2010년에 제안한 모델입니다. 한국 개발팀에서 가장 오래, 가장 많이 쓰인 전략이기도 합니다.

![Git 브랜치 전략 비교](/images/git-branch-strategy-comparison.svg)

### 브랜치 구조

Git Flow에는 두 개의 영구 브랜치와 세 가지 임시 브랜치가 있습니다.

**영구 브랜치:**
- `main` (또는 `master`): 항상 프로덕션 배포 상태
- `develop`: 다음 릴리즈를 위한 통합 브랜치

**임시 브랜치:**
- `feature/*`: 새 기능 개발. `develop`에서 분기, `develop`으로 병합
- `release/*`: 출시 준비. `develop`에서 분기, `main`과 `develop`으로 병합
- `hotfix/*`: 긴급 패치. `main`에서 분기, `main`과 `develop`으로 병합

```bash
# Git Flow 워크플로우 예시

# 1. feature 브랜치 생성
git checkout develop
git checkout -b feature/user-authentication

# 2. 개발 완료 후 develop에 머지
git checkout develop
git merge --no-ff feature/user-authentication
git branch -d feature/user-authentication

# 3. 릴리즈 준비
git checkout -b release/1.2.0
# 버전 번호 수정, 최종 버그 수정...
git checkout main
git merge --no-ff release/1.2.0
git tag -a v1.2.0
git checkout develop
git merge --no-ff release/1.2.0

# 4. 핫픽스
git checkout main
git checkout -b hotfix/login-crash
# 버그 수정...
git checkout main
git merge --no-ff hotfix/login-crash
git checkout develop
git merge --no-ff hotfix/login-crash
```

### 언제 Git Flow가 맞는가

Git Flow는 **버전 릴리즈 사이클이 명확한 제품**에 적합합니다.

- 앱스토어에 배포하는 모바일 앱 (v1.0, v1.1, v2.0)
- 분기별/월별 릴리즈를 하는 B2B SaaS
- 동시에 여러 버전을 유지해야 하는 라이브러리/SDK
- 엄격한 QA 프로세스가 있는 금융, 의료 소프트웨어

### Git Flow의 단점

브랜치가 많아서 복잡합니다. 특히 hotfix를 `main`과 `develop` 양쪽에 모두 반영해야 한다는 게 실수가 잦은 포인트입니다. CI/CD가 없거나 약한 팀에서는 브랜치 관리 자체가 부담이 됩니다.

당근마켓, 화해 등 국내 유명 스타트업들이 Git Flow에서 다른 전략으로 전환한 이유도 이 복잡도 때문입니다.

## GitHub Flow — 단순하고 빠른 배포

GitHub이 자체적으로 사용하고 공개한 모델입니다. 규칙이 단 하나입니다: **`main`은 항상 배포 가능한 상태여야 한다.**

### 워크플로우

```bash
# 1. main에서 feature 브랜치 생성
git checkout main
git checkout -b feature/add-dark-mode

# 2. 개발 + 커밋
git add .
git commit -m "feat: 다크모드 토글 추가"
git push origin feature/add-dark-mode

# 3. Pull Request 생성
# GitHub에서 PR 생성 → 코드 리뷰 → CI 통과 확인

# 4. main에 Squash Merge 또는 Rebase Merge
# 병합 즉시 프로덕션 배포 (CI/CD 자동)

# 5. feature 브랜치 삭제
git branch -d feature/add-dark-mode
```

PR이 `main`에 병합되는 순간 자동으로 프로덕션에 배포됩니다. 그렇기 때문에 CI/CD 파이프라인이 탄탄해야 합니다.

### GitHub Flow가 맞는 환경

- **하루에 여러 번 배포하는 팀** (웹 서비스, SaaS)
- 소수 정예 팀 (5명 이하)
- 다버전 유지가 필요 없는 서비스
- CI/CD가 이미 잘 갖춰진 팀

### 주의할 점

feature 브랜치에서 `main`으로 바로 가기 때문에, 미완성 기능이 `main`에 들어가면 문제가 됩니다. 이를 해결하는 기법이 **Feature Flag**입니다.

```python
# Feature Flag 예시
if feature_flags.is_enabled('new_payment_flow', user=current_user):
    return new_payment_view()
else:
    return legacy_payment_view()
```

코드는 `main`에 있지만 플래그로 비활성화해두고, 준비가 되면 플래그만 켜는 방식입니다.

## Trunk-based Development — 대규모 팀의 선택

Google, Facebook, Netflix 같은 빅테크가 사용하는 방식입니다. `main`(trunk) 브랜치 하나만 운영하고, 모든 개발자가 자주 (하루에 최소 1번) 직접 커밋하거나, 1~2일 내로 병합하는 짧은 feature 브랜치를 사용합니다.

### 핵심 원칙

1. **작은 단위로 자주 커밋**: 큰 PR 대신 작은 커밋을 매일
2. **브랜치 수명 최소화**: feature 브랜치는 이틀을 넘기지 않는다
3. **강력한 CI**: 모든 커밋에 자동 테스트 실행
4. **Feature Flag 적극 활용**: 미완성 코드도 trunk에 병합 가능

```bash
# Trunk-based 워크플로우
git checkout main
git pull origin main

# 작은 단위 작업
git checkout -b feature/add-email-validation
# 1~2일 안에 완료 가능한 작은 단위로 작업
git commit -m "feat: 이메일 형식 검증 추가"
git push origin feature/add-email-validation

# PR → CI 통과 → 즉시 main 병합
# feature 브랜치 삭제
```

### Trunk-based가 맞는 환경

- **대규모 팀** (10명 이상 개발자)
- CI/CD 성숙도가 높은 조직
- 하루에 수십 번 배포하는 팀
- 강력한 자동화 테스트 커버리지가 있는 경우

### 가장 어려운 점

팀 규율이 필요합니다. "이 커밋이 trunk에 들어가도 안전한가?"를 항상 고민해야 합니다. 테스트 커버리지가 낮은 상태에서 Trunk-based를 도입하면 프로덕션 장애가 잦아집니다.

## 실무에서의 선택 기준

| 상황 | 추천 전략 |
|------|----------|
| 모바일 앱, 버전 관리 필요 | Git Flow |
| 스타트업 웹 서비스 | GitHub Flow |
| 대규모 팀, 빠른 배포 | Trunk-based |
| CI/CD 없음 | Git Flow |
| 1인 개발 | GitHub Flow (단순하게) |

## 브랜치 이름 컨벤션

어떤 전략을 쓰든 일관된 이름 규칙이 필요합니다.

```
feature/[이슈번호]-[설명]    → feature/123-add-user-auth
fix/[이슈번호]-[설명]        → fix/456-login-crash
hotfix/[버전]-[설명]         → hotfix/1.2.1-payment-error
release/[버전]               → release/1.3.0
chore/[설명]                 → chore/update-dependencies
```

## 커밋 메시지 컨벤션

Conventional Commits를 사용하면 자동으로 CHANGELOG를 생성할 수 있습니다.

```
<type>(<scope>): <description>

feat: 새로운 기능
fix: 버그 수정
docs: 문서만 변경
style: 코드 스타일 (공백, 세미콜론 등)
refactor: 기능 변경 없는 리팩토링
test: 테스트 추가/수정
chore: 빌드 설정, 패키지 업데이트

예시:
feat(auth): JWT 리프레시 토큰 추가
fix(payment): 결제 금액 소수점 오류 수정
docs(api): 사용자 API 엔드포인트 문서 업데이트
```

## 결론: 완벽한 전략은 없다

브랜치 전략을 바꾸는 것만으로 팀 생산성이 마법처럼 올라가지 않습니다. 중요한 것은 **팀이 합의한 규칙을 일관되게 지키는 것**입니다.

작은 팀이라면 GitHub Flow로 시작하는 걸 권장합니다. 규칙이 단순해서 온보딩이 쉽고, CI/CD를 잘 갖추면 빠른 배포가 가능합니다. 팀이 커지고 배포 빈도가 올라가면 그때 Trunk-based로 전환을 고려하면 됩니다.

Git Flow는 앱스토어 배포처럼 릴리즈 사이클이 명확할 때 여전히 유효합니다. 무조건 나쁜 전략이 아닙니다. 맞는 환경이 있을 뿐입니다.
