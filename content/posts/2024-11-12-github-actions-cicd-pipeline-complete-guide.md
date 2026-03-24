---
title: "GitHub Actions로 CI/CD 파이프라인 완전 구축 — 실전 yaml 예시 총정리"
date: 2024-11-12T08:00:00+09:00
lastmod: 2024-11-14T08:00:00+09:00
description: "GitHub Actions로 CI/CD 파이프라인을 처음부터 구축하는 방법을 정리합니다. workflow 기본 구조, 빌드/테스트/배포 자동화, secrets 관리, 실전 yaml 예시를 단계별로 다룹니다."
slug: "github-actions-cicd-pipeline-complete-guide"
categories: ["software-dev"]
tags: ["GitHub Actions", "CI/CD", "자동화", "DevOps", "배포 파이프라인"]
featureimage: "/images/github-actions-cicd-pipeline.svg"
series: []
draft: false
---

코드를 push할 때마다 자동으로 테스트를 돌리고, 리뷰가 통과되면 배포까지 이어지는 흐름. GitHub Actions는 그 흐름을 별도 서버 없이 yaml 파일 하나로 구현합니다. 13년간 다양한 CI 도구를 써온 입장에서, GitHub Actions는 "설정 비용 대비 커버리지"가 가장 높은 도구입니다. Jenkins처럼 전용 서버가 필요 없고, CircleCI처럼 별도 계정을 관리할 필요도 없습니다. 리포지토리에 `.github/workflows/` 디렉토리만 있으면 시작됩니다.

![GitHub Actions CI/CD 파이프라인 흐름](/images/github-actions-cicd-pipeline.svg)

## GitHub Actions란 무엇인가요?

GitHub Actions는 GitHub 리포지토리에서 직접 동작하는 자동화 플랫폼입니다. 코드 push, PR 생성, 스케줄, 외부 이벤트 등 다양한 트리거에 반응해서 정해진 작업을 실행합니다. 공식 Marketplace에 15,000개 이상의 Action이 등록되어 있어, 직접 스크립트를 짜지 않아도 대부분의 작업을 조합할 수 있습니다.

핵심 개념을 먼저 정리하면 다음과 같습니다.

- **Workflow**: `.github/workflows/*.yml` 파일. 자동화의 최상위 단위
- **Event**: workflow를 실행시키는 트리거 (`push`, `pull_request`, `schedule` 등)
- **Job**: 독립적으로 실행되는 작업 단위. 기본적으로 병렬 실행
- **Step**: Job 안의 개별 명령. 순차 실행
- **Action**: 재사용 가능한 Step 단위 패키지 (`uses: actions/checkout@v4`)
- **Runner**: Job이 실행되는 서버. GitHub 호스팅(ubuntu, windows, macos) 또는 셀프 호스팅

## Workflow 기본 구조

가장 단순한 workflow 파일부터 시작하겠습니다.

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: 코드 체크아웃
        uses: actions/checkout@v4

      - name: Node.js 설정
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: 의존성 설치
        run: npm ci

      - name: 빌드
        run: npm run build

      - name: 테스트
        run: npm test
```

`on` 섹션이 트리거입니다. `main`과 `develop` 브랜치에 push가 되거나, `main` 브랜치로 PR이 생성될 때 실행됩니다. `runs-on: ubuntu-latest`는 GitHub에서 제공하는 Ubuntu 가상 머신을 사용한다는 의미입니다. 매 실행마다 새로운 환경이 생성되므로 이전 실행의 오염 걱정이 없습니다.

## 빌드/테스트/배포 파이프라인 분리

실무에서는 빌드, 테스트, 배포를 별도 Job으로 분리합니다. `needs` 키워드로 의존 관계를 정의하면, 테스트가 통과한 경우에만 배포가 실행되는 흐름을 만들 수 있습니다.

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      build-artifact: ${{ steps.build.outputs.artifact }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: 빌드
        id: build
        run: npm run build
      - name: 빌드 결과물 업로드
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 1

  test:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: 단위 테스트
        run: npm run test:unit
      - name: 통합 테스트
        run: npm run test:integration
      - name: 커버리지 리포트
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}

  deploy-staging:
    runs-on: ubuntu-latest
    needs: [build, test]
    if: github.ref == 'refs/heads/main'
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: 빌드 결과물 다운로드
        uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/
      - name: Staging 배포
        run: |
          echo "Deploying to staging..."
          # 실제 배포 명령 (예: AWS CLI, rsync 등)

  deploy-production:
    runs-on: ubuntu-latest
    needs: [deploy-staging]
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: 빌드 결과물 다운로드
        uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/
      - name: Production 배포
        run: |
          echo "Deploying to production..."
```

`needs: [build, test]`는 build와 test Job이 모두 성공해야 해당 Job이 실행됩니다. `if: github.ref == 'refs/heads/main'`은 main 브랜치에서만 배포가 실행되도록 조건을 걸어둔 것입니다.

## Secrets와 환경 변수 관리

배포 과정에서 API 키, 서버 접근 정보 같은 민감한 값은 코드에 직접 넣으면 안 됩니다. GitHub Secrets를 사용하면 암호화된 상태로 저장하고, workflow에서 `${{ secrets.변수명 }}` 형태로 참조할 수 있습니다.

**Secrets 등록 방법**

1. GitHub 리포지토리 → Settings → Secrets and variables → Actions
2. "New repository secret" 클릭
3. Name과 Secret 값 입력

**Workflow에서 사용**

```yaml
steps:
  - name: AWS 배포
    env:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      AWS_REGION: ap-northeast-2
    run: |
      aws s3 sync dist/ s3://${{ secrets.S3_BUCKET_NAME }} --delete
      aws cloudfront create-invalidation \
        --distribution-id ${{ secrets.CF_DISTRIBUTION_ID }} \
        --paths "/*"
```

**Environment Secrets**로 배포 환경별 값을 분리하는 것도 중요합니다. Settings → Environments에서 `staging`과 `production` 환경을 만들고, 각 환경별로 다른 Secrets를 등록합니다. `production` 환경에는 "Required reviewers"를 설정해서 배포 전 승인 과정을 강제할 수 있습니다.

```yaml
deploy-production:
  environment:
    name: production
    url: https://yourdomain.com
  # Required reviewers가 승인해야만 실행됩니다
```

## Matrix Strategy로 병렬 테스트

여러 Node.js 버전, 여러 OS에서 동시에 테스트하려면 Matrix Strategy를 사용합니다.

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [18, 20, 22]
      fail-fast: false  # 하나 실패해도 나머지 계속 실행

    steps:
      - uses: actions/checkout@v4
      - name: Node.js ${{ matrix.node-version }} 설정
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

이 설정은 3 OS × 3 Node 버전 = 9개의 Job을 동시에 실행합니다. 특정 조합을 제외하려면 `exclude`를 사용합니다.

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    node-version: [18, 20, 22]
    exclude:
      - os: windows-latest
        node-version: 18
```

## 캐시 최적화

매번 `npm install`을 처음부터 실행하면 시간이 많이 걸립니다. `actions/cache`를 사용하면 `node_modules`를 캐시해서 빌드 시간을 크게 단축할 수 있습니다. `actions/setup-node@v4`는 `cache: 'npm'` 옵션을 지원해서 별도로 cache Action을 쓰지 않아도 됩니다.

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'  # package-lock.json 해시 기반 캐시 자동 처리
```

Docker 이미지를 빌드하는 경우에는 레이어 캐시를 활용합니다.

```yaml
- name: Docker 레이어 캐시 설정
  uses: actions/cache@v4
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-buildx-

- name: Docker 빌드 & Push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ${{ secrets.DOCKER_USERNAME }}/myapp:latest
    cache-from: type=local,src=/tmp/.buildx-cache
    cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max
```

## 실전 패턴 — Node.js 앱 전체 파이프라인

지금까지 다룬 내용을 합쳐서 실전에서 바로 쓸 수 있는 완성 파이프라인입니다.

```yaml
name: Node.js CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true  # 같은 브랜치의 이전 실행 자동 취소

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check

  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: testpassword
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: 테스트 실행
        env:
          DATABASE_URL: postgresql://postgres:testpassword@localhost:5432/testdb
          NODE_ENV: test
        run: npm run test:coverage
      - name: 커버리지 업로드
        uses: codecov/codecov-action@v4
        if: always()

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run build
      - name: Cloudflare Pages 배포
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: my-project
          directory: dist
          gitHubToken: ${{ secrets.GITHUB_TOKEN }}

  notify:
    runs-on: ubuntu-latest
    needs: [lint, test, deploy]
    if: always()
    steps:
      - name: Slack 알림
        uses: slackapi/slack-github-action@v1.26.0
        with:
          payload: |
            {
              "text": "배포 결과: ${{ needs.deploy.result }} — ${{ github.repository }}@${{ github.sha }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

`services` 섹션은 테스트에 필요한 데이터베이스나 Redis를 Docker 컨테이너로 실행합니다. 테스트가 끝나면 자동으로 종료됩니다. `concurrency` 설정은 같은 브랜치에서 새 push가 오면 이전 workflow를 자동으로 취소해서 리소스 낭비를 줄입니다.

## PR 자동 체크와 Branch Protection

workflow가 제대로 동작하려면 Branch Protection과 연계해야 합니다. Settings → Branches → Branch protection rules에서 main 브랜치에 다음을 설정합니다.

- Require status checks to pass before merging: CI workflow의 Job들 선택
- Require branches to be up to date before merging: 활성화
- Require pull request reviews before merging: 리뷰어 수 설정

이 설정이 있으면 CI가 실패하거나 리뷰가 없는 PR은 merge 버튼 자체가 비활성화됩니다. 팀 규모에 상관없이 코드 품질 기준을 자동으로 유지할 수 있습니다.

## 스케줄 실행과 수동 트리거

```yaml
on:
  schedule:
    - cron: '0 9 * * 1-5'  # 평일 오전 9시 (UTC 기준 0시)
  workflow_dispatch:         # 수동 실행 버튼 활성화
    inputs:
      environment:
        description: '배포 환경'
        required: true
        default: 'staging'
        type: choice
        options: [staging, production]
```

`workflow_dispatch`를 추가하면 GitHub UI에서 "Run workflow" 버튼이 생깁니다. `inputs`로 매개변수를 받을 수 있어서, 긴급 재배포나 특정 환경 선택이 필요한 상황에 유용합니다.

## 비용과 한도

GitHub Actions는 공개 리포지토리에서 무제한 무료입니다. 비공개 리포지토리는 계정 플랜에 따라 월 2,000~50,000분의 무료 사용량이 있습니다. Ubuntu runner 기준으로 분당 약 $0.008입니다. 캐시를 잘 활용하고 불필요한 Job을 줄이면 비용을 크게 낮출 수 있습니다.

실무에서 GitHub Actions를 도입할 때 가장 먼저 챙겨야 할 것은 "PR마다 테스트가 자동으로 돌고, main 브랜치는 항상 배포 가능한 상태"라는 기준선입니다. 복잡한 파이프라인보다 이 기준선이 먼저입니다. 기준선이 잡히면 Matrix, 캐시 최적화, 환경 분리는 필요에 따라 하나씩 추가하면 됩니다.
