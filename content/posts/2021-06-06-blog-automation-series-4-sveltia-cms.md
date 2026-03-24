---
title: "Sveltia CMS + GitHub OAuth로 Hugo 블로그 관리자 패널 구축하기 — 4편"
date: 2021-06-06T08:00:00+09:00
lastmod: 2021-06-10T08:00:00+09:00
description: "서버 없이 Sveltia CMS와 GitHub OAuth를 활용하여 Hugo 블로그에 웹 기반 관리자 패널을 구축하고 브라우저에서 직접 포스트를 편집하는 방법을 안내합니다."
slug: "blog-automation-series-4-sveltia-cms"
categories: ["ai-automation"]
tags: ["Sveltia CMS", "GitHub OAuth", "Hugo CMS", "Decap CMS", "Cloudflare Pages Functions", "헤드리스 CMS"]
series: ["블로그-자동화"]
draft: false
---

PC 없이 태블릿이나 스마트폰에서도 블로그 포스트를 편집할 수 있으면 어떨까요? Sveltia CMS를 사용하면 그것이 가능합니다. 서버도 필요 없고, 추가 비용도 없습니다. 브라우저에서 `/admin`에 접속해 GitHub 계정으로 로그인하면 바로 포스트를 편집할 수 있는 웹 인터페이스가 열립니다.

이 편에서는 Sveltia CMS를 Hugo 블로그에 연동하는 전 과정을 설명합니다.

![Sveltia CMS 흐름](/images/sveltia-cms-flow.svg)

## Sveltia CMS란?

Sveltia CMS는 Decap CMS(구 Netlify CMS)와 100% 호환되는 오픈소스 헤드리스 CMS입니다. Decap CMS의 설정 파일(`config.yml`)을 그대로 사용하면서도 성능이 더 빠르고 UI가 더 현대적입니다.

핵심 특징을 정리하면 다음과 같습니다.

- **서버리스**: 별도 백엔드 서버가 필요 없음
- **Git 기반**: 모든 콘텐츠가 GitHub 저장소에 저장
- **OAuth 인증**: GitHub OAuth를 통한 보안 로그인
- **마크다운 에디터**: 리치 텍스트 편집 + 원본 마크다운 편집 지원
- **미디어 관리**: 이미지 업로드 및 관리 UI 제공
- **Decap CMS 호환**: 기존 Decap CMS 사용자도 즉시 전환 가능

## 파일 구조

Sveltia CMS에 필요한 파일은 세 가지입니다.

```
your-blog/
├── static/
│   └── admin/
│       ├── index.html      # CMS 진입점
│       └── config.yml      # CMS 설정
└── functions/
    ├── auth/
    │   └── [...auth].js    # OAuth 시작 엔드포인트
    └── callback/
        └── [...callback].js # OAuth 콜백 처리
```

## static/admin/index.html

CMS의 진입점 파일입니다. Sveltia CMS CDN 스크립트 하나만 포함하면 됩니다.

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="robots" content="noindex" />
  <title>Content Manager</title>
</head>
<body>
  <!-- Sveltia CMS -->
  <script src="https://unpkg.com/@sveltia/cms/dist/sveltia-cms.js"></script>
</body>
</html>
```

`noindex` 메타 태그를 추가해 검색 엔진이 관리자 패널을 인덱싱하지 않도록 합니다.

## static/admin/config.yml

CMS의 핵심 설정 파일입니다. 백엔드 연결, 미디어 경로, 콘텐츠 컬렉션을 정의합니다.

```yaml
backend:
  name: github
  repo: up21001/blog          # GitHub 저장소 (username/repo)
  branch: main                # 편집할 브랜치
  base_url: https://blog-8ye.pages.dev  # 배포된 사이트 URL
  auth_endpoint: auth         # OAuth 엔드포인트 경로
  site_id: blog-8ye.pages.dev # Cloudflare Pages 사이트 ID

# 미디어 파일 설정
media_folder: static/images   # 저장소 내 이미지 저장 경로
public_folder: /images        # HTML에서 이미지 참조 경로

# 콘텐츠 컬렉션 정의
collections:
  - name: posts
    label: 포스트
    folder: content/posts
    create: true
    slug: "{{year}}-{{month}}-{{day}}-{{slug}}"
    fields:
      - { label: "제목", name: "title", widget: "string" }
      - { label: "날짜", name: "date", widget: "datetime", format: "YYYY-MM-DDTHH:mm:ssZ" }
      - { label: "최종 수정일", name: "lastmod", widget: "datetime", format: "YYYY-MM-DDTHH:mm:ssZ" }
      - { label: "설명", name: "description", widget: "text" }
      - { label: "Slug", name: "slug", widget: "string" }
      - label: "카테고리"
        name: "categories"
        widget: "select"
        multiple: true
        options:
          - { label: "AI와 자동화", value: "ai-automation" }
          - { label: "개발 일지", value: "dev-log" }
          - { label: "아키텍처", value: "architecture" }
          - { label: "일상", value: "life" }
      - { label: "태그", name: "tags", widget: "list" }
      - { label: "임시저장", name: "draft", widget: "boolean", default: false }
      - { label: "본문", name: "body", widget: "markdown" }
```

### 주요 설정 설명

**backend.base_url**: GitHub OAuth 콜백을 처리하는 서버의 URL입니다. Cloudflare Pages 배포 URL을 입력합니다.

**backend.auth_endpoint**: OAuth 시작 엔드포인트의 경로입니다. `auth`로 설정하면 `https://your-site.pages.dev/auth`로 요청이 갑니다.

**media_folder vs public_folder**: `media_folder`는 저장소 내 실제 경로이고, `public_folder`는 Hugo가 빌드한 사이트에서 이미지를 참조하는 URL 경로입니다. Hugo는 `static/` 디렉토리를 루트로 서빙하므로 `static/images`에 저장된 파일은 `/images/`로 접근합니다.

**collections의 slug**: `{{year}}-{{month}}-{{day}}-{{slug}}` 패턴으로 파일명을 자동 생성합니다. `content/posts/2026-03-23-my-post.md` 형태가 됩니다.

## GitHub OAuth App 생성

GitHub OAuth를 통해 Sveltia CMS가 저장소에 접근하려면 OAuth App을 등록해야 합니다.

1. GitHub 계정 설정으로 이동합니다.
2. **Developer settings** → **OAuth Apps** → **New OAuth App**을 클릭합니다.
3. 다음 정보를 입력합니다.

| 항목 | 값 |
|---|---|
| Application name | Blog CMS |
| Homepage URL | https://blog-8ye.pages.dev |
| Authorization callback URL | https://blog-8ye.pages.dev/callback |

4. **Register application**을 클릭합니다.
5. **Client ID**를 복사합니다.
6. **Generate a new client secret**을 클릭하여 **Client Secret**을 생성하고 복사합니다.

Client Secret은 한 번만 표시되므로 반드시 즉시 저장합니다.

## Cloudflare Pages Functions로 OAuth 구현

GitHub OAuth는 Client Secret을 사용하는 서버 사이드 처리가 필요합니다. Cloudflare Pages Functions로 이를 처리합니다.

### 환경 변수 설정

Cloudflare Pages 대시보드에서 해당 프로젝트의 **Settings** → **Environment variables**로 이동하여 다음 변수를 추가합니다.

| 변수명 | 값 |
|---|---|
| GITHUB_CLIENT_ID | OAuth App의 Client ID |
| GITHUB_CLIENT_SECRET | OAuth App의 Client Secret |

### functions/auth/[...auth].js

OAuth 인증 흐름을 시작하는 엔드포인트입니다. 사용자를 GitHub 로그인 페이지로 리다이렉트합니다.

```javascript
export async function onRequest(context) {
  const { env } = context;
  const clientId = env.GITHUB_CLIENT_ID;

  const params = new URLSearchParams({
    client_id: clientId,
    scope: "repo,user",
    redirect_uri: `${new URL(context.request.url).origin}/callback`,
  });

  return Response.redirect(
    `https://github.com/login/oauth/authorize?${params}`,
    302
  );
}
```

### functions/callback/[...callback].js

GitHub에서 OAuth 코드를 받아 액세스 토큰으로 교환하는 엔드포인트입니다.

```javascript
export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const code = url.searchParams.get("code");

  if (!code) {
    return new Response("Missing code parameter", { status: 400 });
  }

  // GitHub에서 액세스 토큰 교환
  const tokenResponse = await fetch(
    "https://github.com/login/oauth/access_token",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        client_id: env.GITHUB_CLIENT_ID,
        client_secret: env.GITHUB_CLIENT_SECRET,
        code,
      }),
    }
  );

  const tokenData = await tokenResponse.json();

  if (tokenData.error) {
    return new Response(`OAuth error: ${tokenData.error_description}`, {
      status: 400,
    });
  }

  // Sveltia CMS가 기대하는 형식으로 토큰 전달
  const script = `
    <script>
      const receiveMessage = (message) => {
        window.opener.postMessage(
          'authorization:github:success:${JSON.stringify({
            token: tokenData.access_token,
            provider: "github",
          })}',
          message.origin
        );
        window.removeEventListener("message", receiveMessage, false);
      };
      window.addEventListener("message", receiveMessage, false);
      window.opener.postMessage("authorizing:github", "*");
    </script>
  `;

  return new Response(script, {
    headers: { "Content-Type": "text/html" },
  });
}
```

## 배포 및 접속 테스트

파일을 모두 추가했으면 git push로 배포합니다.

```bash
git add static/admin/ functions/
git commit -m "feat: Sveltia CMS 관리자 패널 추가"
git push origin main
```

Cloudflare Pages 빌드가 완료되면 `https://your-site.pages.dev/admin`에 접속합니다.

**Login with GitHub** 버튼을 클릭하면 GitHub 로그인 페이지가 열립니다. 로그인 후 저장소 접근 권한을 허용하면 CMS 메인 화면이 나타납니다.

## CMS 사용 방법

### 포스트 목록 확인

메인 화면에서 **포스트** 컬렉션을 클릭하면 `content/posts/` 디렉토리의 모든 마크다운 파일이 목록으로 표시됩니다.

### 새 포스트 작성

**New 포스트** 버튼을 클릭하면 편집 화면이 열립니다. front matter 필드가 폼 형태로 표시되고, 본문은 리치 텍스트 에디터 또는 원본 마크다운으로 편집할 수 있습니다.

### 저장 및 발행

편집 완료 후 **Save** 버튼을 클릭하면 GitHub에 자동으로 커밋됩니다. 커밋 메시지는 자동으로 생성됩니다. 이후 Cloudflare Pages가 변경을 감지하고 자동 빌드 및 배포를 진행합니다.

## 트러블슈팅

### OAuth 콜백 URL 불일치 오류

GitHub OAuth App에 등록한 콜백 URL과 실제 배포 URL이 일치해야 합니다. 커스텀 도메인을 사용하는 경우 해당 도메인으로 업데이트합니다.

### Client Secret 오류

Cloudflare Pages 환경 변수에 Client Secret이 올바르게 설정되어 있는지 확인합니다. 환경 변수 변경 후에는 재배포가 필요합니다.

### 저장소 접근 권한 오류

OAuth App의 scope에 `repo`가 포함되어 있어야 합니다. 비공개 저장소를 사용하는 경우 특히 중요합니다.

다음 편에서는 지금까지 구축한 모든 컴포넌트를 하나의 완성된 파이프라인으로 묶고 실전 운영 팁을 공유합니다.
