---
title: "Vercel vs Cloudflare Pages vs Netlify — 2026년 정적 사이트 호스팅 비교"
date: 2024-10-19T12:34:00+09:00
lastmod: 2024-10-19T12:34:00+09:00
description: "Vercel, Cloudflare Pages, Netlify 세 플랫폼의 기능, 가격, 성능을 2026년 기준으로 비교합니다. 용도별 추천과 실전 선택 가이드를 제공합니다."
slug: "vercel-vs-cloudflare-pages-vs-netlify-2026"
categories: ["software-dev"]
tags: ["Vercel", "Cloudflare Pages", "Netlify", "정적 호스팅", "배포"]
series: []
draft: false
---

![정적 사이트 호스팅 비교](/images/hosting-comparison-2026.svg)

프론트엔드 배포 플랫폼은 이제 단순한 파일 서빙을 넘어섰습니다. 엣지 함수, 서버리스 API, 미리보기 배포, A/B 테스트까지 제공합니다. Vercel, Cloudflare Pages, Netlify는 이 시장의 3강입니다. 셋 다 무료 플랜을 제공하고 Git 기반 배포를 지원하지만, 가격 구조와 성능 특성, 생태계가 다릅니다. 어떤 것을 선택해야 할지 실제 사용 경험을 바탕으로 정리합니다.

## 플랫폼 소개

### Vercel

Next.js를 만든 회사가 운영하는 플랫폼입니다. React와 Next.js 생태계와의 통합이 가장 깊습니다. 팀 협업 기능, PR 미리보기 배포, 분석 도구가 잘 갖춰져 있어 팀 프로젝트에 많이 사용됩니다.

### Cloudflare Pages

Cloudflare의 방대한 글로벌 네트워크(330+ PoP)를 그대로 활용하는 정적 호스팅 서비스입니다. 무제한 대역폭과 무제한 빌드가 무료 플랜에 포함되어 있어 비용 효율이 압도적입니다. Workers를 통한 서버리스 연산도 강력합니다.

### Netlify

정적 사이트 호스팅 시장의 선구자입니다. Gatsby, Hugo, Jekyll 등 다양한 정적 사이트 생성기와의 호환성이 뛰어나고, Form 처리, Identity(인증), Split Testing 같은 편의 기능이 기본으로 포함됩니다.

## 상세 기능 비교

### 무료 플랜 핵심 지표

| 항목 | Vercel | Cloudflare Pages | Netlify |
|------|--------|-----------------|---------|
| 대역폭 | 100GB / 월 | **무제한** | 100GB / 월 |
| 빌드 시간 | 6,000분 / 월 | **무제한** | 300분 / 월 |
| 동시 빌드 | 1 | 1 | 1 |
| 팀원 수 | 1명 | **무제한** | 1명 |
| 커스텀 도메인 | Yes | Yes | Yes |
| HTTPS | Yes | Yes | Yes |
| 미리보기 배포 | Yes | Yes | Yes |

Cloudflare Pages의 무료 플랜은 독보적입니다. 대역폭과 빌드 모두 무제한이라는 점은 트래픽이 급증하는 서비스에서 예산 예측을 단순하게 만들어줍니다.

### 빌드 및 배포

```yaml
# Vercel — vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm ci"
}
```

```yaml
# Cloudflare Pages — 대시보드 설정 또는 wrangler.toml
[pages]
  build_command = "npm run build"
  output_directory = "dist"
```

```yaml
# Netlify — netlify.toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "20"
```

세 플랫폼 모두 Git 저장소에 push하면 자동으로 빌드와 배포가 실행됩니다. PR을 열면 미리보기 URL이 생성되는 방식도 동일합니다.

### 서버리스 함수 비교

```typescript
// Vercel — api/hello.ts (Node.js)
export default function handler(req, res) {
  res.json({ message: 'Hello from Vercel' })
}

// Edge Runtime
export const config = { runtime: 'edge' }
export default function(request) {
  return new Response('Hello from Edge')
}
```

```typescript
// Cloudflare Pages — functions/api/hello.ts (V8 Workers)
export async function onRequest(context) {
  return new Response(JSON.stringify({ message: 'Hello from CF' }), {
    headers: { 'Content-Type': 'application/json' }
  })
}
```

```typescript
// Netlify — netlify/functions/hello.ts (Node.js)
export const handler = async (event, context) => {
  return {
    statusCode: 200,
    body: JSON.stringify({ message: 'Hello from Netlify' }),
  }
}
```

Cloudflare는 V8 격리 기반 Workers를 사용하므로 Node.js API를 직접 사용할 수 없습니다. 반면 Vercel과 Netlify는 Node.js 환경을 그대로 지원합니다. 기존 Node.js 패키지 의존성이 많다면 이 점을 꼭 확인해야 합니다.

### 성능 및 글로벌 CDN

| 항목 | Vercel | Cloudflare Pages | Netlify |
|------|--------|-----------------|---------|
| CDN PoP | 글로벌 | **330+** | 글로벌 |
| 엣지 캐시 | Yes | Yes | Yes |
| HTTP/3 | Yes | **Yes (기본)** | 부분 지원 |
| 이미지 최적화 | Yes (유료) | Yes | 부분 지원 |
| 한국 엣지 | Yes | **Yes (서울 PoP)** | Yes |

체감 성능 측면에서 Cloudflare Pages가 일반적으로 가장 빠릅니다. Cloudflare의 네트워크 인프라가 기반이기 때문입니다. DDoS 방어도 기본으로 포함됩니다.

### 가격 비교 (유료 플랜)

| 플랜 | Vercel Pro | CF Pages Pro | Netlify Pro |
|------|-----------|-------------|------------|
| 월 요금 | $20 / 멤버 | $20 / 월 | $19 / 월 |
| 대역폭 | 1TB | 무제한 | 400GB |
| 빌드 | 무제한 | 무제한 | 1,000분 |
| 팀원 | 무제한 | 무제한 | 무제한 |
| 분석 | Pro 포함 | 별도 요금 | 기본 포함 |

Vercel의 $20은 멤버 1인 기준입니다. 팀원이 5명이라면 월 $100입니다. Cloudflare Pages와 Netlify는 팀 전체 기준으로 월 $20 전후이므로, 팀 규모가 클수록 차이가 커집니다.

## 프레임워크별 호환성

### Next.js

Vercel이 압도적으로 유리합니다. App Router, Server Components, ISR, Image Optimization 등 Next.js의 모든 기능이 Vercel에서 완벽히 동작합니다. Cloudflare와 Netlify에서도 Next.js를 배포할 수 있지만, 일부 기능(특히 서버 사이드 렌더링 관련)은 추가 설정이 필요하거나 제한이 있습니다.

### SvelteKit / Astro / Remix

세 플랫폼 모두 공식 어댑터를 제공합니다. 특정 플랫폼에 묶이지 않으려면 Cloudflare Pages나 Netlify가 더 적합합니다.

### Hugo / Gatsby / Jekyll

완전 정적 사이트라면 세 플랫폼 성능 차이가 거의 없습니다. Netlify는 오랫동안 Hugo, Gatsby와의 통합을 다듬어왔기 때문에 문서와 생태계가 풍부합니다.

## 실전 선택 가이드

### Vercel을 선택해야 할 때

- Next.js 프로젝트가 주력일 때
- 팀 협업 및 PR 미리보기 배포가 중요할 때
- Vercel Analytics, Speed Insights를 활용하고 싶을 때
- Node.js 서버리스 함수를 간단히 사용하고 싶을 때

```bash
# Vercel CLI로 즉시 배포
npm i -g vercel
vercel
```

### Cloudflare Pages를 선택해야 할 때

- 트래픽 예측이 어렵거나 급증 가능성이 있을 때
- 비용 최소화가 최우선일 때
- 엣지 성능이 핵심 요구사항일 때
- Workers KV, Durable Objects 등 Cloudflare 생태계를 함께 활용할 때
- DDoS 방어가 필요할 때

```bash
# Wrangler CLI로 배포
npm i -g wrangler
wrangler pages deploy dist
```

### Netlify를 선택해야 할 때

- Hugo, Gatsby 등 전통적인 정적 사이트 생성기를 사용할 때
- Form 처리, Identity 등 부가 기능을 별도 백엔드 없이 쓰고 싶을 때
- A/B 테스트(Split Testing)가 필요할 때
- Netlify CMS 또는 Decap CMS와 연동할 때

```bash
# Netlify CLI로 배포
npm i -g netlify-cli
netlify deploy --prod
```

## 마이그레이션 고려사항

세 플랫폼 간 마이그레이션은 생각보다 어렵지 않습니다. 완전 정적 사이트라면 빌드 명령어와 출력 디렉토리만 다시 설정하면 됩니다. 서버리스 함수가 있다면 런타임 차이를 확인해야 합니다. Cloudflare Workers는 Node.js API 일부를 지원하지 않으므로 `node:fs`, `node:path` 등을 사용하는 코드는 수정이 필요합니다.

## 이 블로그의 선택

이 블로그(Hugo 기반)는 현재 Cloudflare Pages에서 운영 중입니다. Hugo의 빠른 빌드 속도와 Cloudflare의 무제한 대역폭 조합이 개인 블로그에는 가장 합리적입니다. GitHub Actions와 Cloudflare Pages를 연결해 `main` 브랜치에 push할 때마다 자동 배포됩니다.

```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloudflare Pages
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true
      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v3
        with:
          hugo-version: latest
      - name: Build
        run: hugo --minify
      - name: Deploy
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CF_API_TOKEN }}
          accountId: ${{ secrets.CF_ACCOUNT_ID }}
          projectName: my-blog
          directory: public
```

## 정리

2026년 기준 세 플랫폼의 포지셔닝은 명확합니다. Vercel은 Next.js 팀 프로젝트의 표준, Cloudflare Pages는 비용 효율과 성능이 중요한 서비스, Netlify는 정적 사이트 생성기 기반 프로젝트의 강자입니다. 개인 프로젝트나 비용을 최소화하고 싶다면 Cloudflare Pages부터 시작하는 것을 권장합니다. Next.js를 본격적으로 사용한다면 Vercel이 가장 매끄럽습니다. 세 플랫폼 모두 무료로 시작할 수 있으니 직접 비교해보는 것이 가장 좋은 방법입니다.
