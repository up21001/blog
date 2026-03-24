---
title: "Next.js 15 완전 가이드 — App Router로 풀스택 웹앱 만들기"
date: 2025-04-13T08:00:00+09:00
lastmod: 2025-04-15T08:00:00+09:00
description: "Next.js 15의 App Router 구조, Server Components, Route Handlers, Vercel 배포까지 풀스택 웹앱 개발에 필요한 모든 것을 13년 차 엔지니어가 실무 관점에서 정리합니다."
slug: "nextjs-15-app-router-fullstack-guide"
categories: ["software-dev"]
tags: ["Next.js", "App Router", "React", "풀스택", "Vercel"]
series: []
draft: false
---

Next.js 15가 나온 뒤로 "App Router를 어떻게 써야 하는가"라는 질문을 주변에서 자주 받습니다. Pages Router에 익숙한 분들은 새로운 파일 구조와 Server Components 개념이 낯설고, 처음 Next.js를 배우는 분들은 어디서부터 시작해야 할지 막막하다고 합니다. 이 글에서는 Next.js 15의 핵심 개념을 실무 관점에서 정리하고, 실제로 풀스택 웹앱을 만들 때 어떻게 적용하는지 설명합니다.

![Next.js 15 App Router 아키텍처 다이어그램](/images/nextjs-15-app-router-guide.svg)

## Next.js 15에서 달라진 것들

Next.js 15는 React 19를 완전 지원하고, Turbopack이 기본 개발 서버로 활성화됩니다. 가장 크게 체감되는 변화는 `fetch` 캐싱 기본값입니다. 이전 버전에서는 `fetch`가 기본적으로 캐시되었지만, Next.js 15부터는 기본값이 `no-store`로 바뀌었습니다. 즉, 명시적으로 캐싱을 선언해야 합니다.

```js
// Next.js 15: 명시적으로 캐시 설정 필요
const data = await fetch('/api/posts', {
  next: { revalidate: 3600 } // 1시간 캐시
})
```

이 변화는 처음에는 불편하게 느껴질 수 있지만, 의도치 않은 stale 데이터 문제를 사전에 차단해주는 올바른 방향입니다.

## App Router 디렉토리 구조

App Router는 `app/` 디렉토리를 중심으로 동작합니다. 각 폴더가 라우트 세그먼트가 되고, 특정 파일명에 의미가 부여됩니다.

```
app/
├── layout.tsx          # 루트 레이아웃 (공통 HTML 구조)
├── page.tsx            # / 경로
├── loading.tsx         # 로딩 UI
├── error.tsx           # 에러 UI
├── not-found.tsx       # 404 UI
├── globals.css
├── blog/
│   ├── page.tsx        # /blog 경로
│   └── [slug]/
│       └── page.tsx    # /blog/:slug 경로
└── api/
    └── posts/
        └── route.ts    # /api/posts API 엔드포인트
```

`layout.tsx`는 중첩 레이아웃을 지원합니다. 루트 레이아웃에서 전체 HTML 구조를 정의하고, 하위 경로별로 레이아웃을 추가할 수 있습니다. 이 구조 덕분에 대시보드 레이아웃, 마케팅 페이지 레이아웃 등을 독립적으로 관리할 수 있습니다.

## Server Components와 Client Components

App Router의 가장 중요한 개념이 Server Components입니다. `app/` 디렉토리 안의 모든 컴포넌트는 기본적으로 Server Component입니다. Server Component는 서버에서만 실행되므로, 데이터베이스에 직접 접근하거나 환경 변수를 안전하게 사용할 수 있습니다.

```tsx
// app/blog/page.tsx — Server Component (기본값)
import { db } from '@/lib/db'

export default async function BlogPage() {
  // 서버에서 직접 DB 쿼리 — 클라이언트에 노출 안 됨
  const posts = await db.post.findMany({
    orderBy: { createdAt: 'desc' },
    take: 10,
  })

  return (
    <ul>
      {posts.map(post => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  )
}
```

반면 상태(state), 이벤트 핸들러, 브라우저 API가 필요하면 `'use client'` 지시어를 파일 상단에 추가해서 Client Component로 만듭니다.

```tsx
'use client'
// Client Component: useState, 이벤트 핸들러 사용 가능
import { useState } from 'react'

export function Counter() {
  const [count, setCount] = useState(0)
  return (
    <button onClick={() => setCount(c => c + 1)}>
      클릭: {count}
    </button>
  )
}
```

실무에서 중요한 원칙이 있습니다. "가능한 한 Server Component로 유지하고, 반드시 필요한 경우에만 Client Component로 전환한다"는 것입니다. Client Component를 트리의 말단(leaf)에 배치할수록 번들 크기가 줄고 성능이 좋아집니다.

## Route Handlers로 API 만들기

Next.js 15에서는 `app/api/` 경로에 `route.ts` 파일을 만들어 REST API를 구현합니다. Pages Router의 `pages/api/` 방식을 대체합니다.

```ts
// app/api/posts/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const page = Number(searchParams.get('page') ?? '1')

  const posts = await db.post.findMany({
    skip: (page - 1) * 10,
    take: 10,
    orderBy: { createdAt: 'desc' },
  })

  return NextResponse.json({ posts })
}

export async function POST(request: NextRequest) {
  const body = await request.json()
  const post = await db.post.create({ data: body })
  return NextResponse.json(post, { status: 201 })
}
```

Route Handlers는 Edge Runtime에서도 실행할 수 있습니다. 응답 속도가 중요한 API에는 파일 상단에 `export const runtime = 'edge'`를 추가하면 됩니다.

## Server Actions로 폼 처리하기

Server Actions는 클라이언트에서 직접 서버 함수를 호출하는 기능입니다. 별도의 API 엔드포인트 없이 폼 제출을 처리할 수 있어서 코드량이 크게 줄어듭니다.

```tsx
// app/posts/new/page.tsx
export default function NewPostPage() {
  async function createPost(formData: FormData) {
    'use server'  // 이 함수는 서버에서 실행됨
    const title = formData.get('title') as string
    const content = formData.get('content') as string

    await db.post.create({ data: { title, content } })
    redirect('/blog')
  }

  return (
    <form action={createPost}>
      <input name="title" placeholder="제목" />
      <textarea name="content" placeholder="내용" />
      <button type="submit">게시</button>
    </form>
  )
}
```

Server Actions를 사용하면 Progressive Enhancement도 자동으로 지원됩니다. JavaScript가 비활성화된 환경에서도 폼이 작동합니다.

## 데이터 패칭 패턴

Next.js 15에서 권장하는 데이터 패칭 패턴은 세 가지입니다.

**1. 서버에서 직접 fetch**

```tsx
// 정적 데이터 (빌드 시 캐시)
const res = await fetch('https://api.example.com/posts', {
  cache: 'force-cache'
})

// 주기적 재검증 (ISR)
const res = await fetch('https://api.example.com/posts', {
  next: { revalidate: 60 }
})

// 항상 최신 데이터
const res = await fetch('https://api.example.com/posts', {
  cache: 'no-store'
})
```

**2. ORM 직접 사용 (Server Component에서)**

Prisma, Drizzle 같은 ORM을 Server Component에서 직접 호출하는 방식입니다. 중간에 API 레이어가 없어서 레이턴시가 줄어듭니다.

**3. React Query / SWR (Client Component에서)**

실시간 업데이트가 필요하거나 낙관적 UI 패턴을 구현할 때는 클라이언트 사이드 데이터 패칭 라이브러리를 사용합니다.

## Middleware로 인증 처리하기

`middleware.ts`를 프로젝트 루트에 두면 모든 요청을 가로채서 처리할 수 있습니다. 인증 확인, A/B 테스트, 국제화 처리 등에 활용합니다.

```ts
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value

  // 보호된 경로 처리
  if (request.nextUrl.pathname.startsWith('/dashboard')) {
    if (!token) {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/api/protected/:path*'],
}
```

## 메타데이터 API

Next.js 15는 SEO를 위한 Metadata API를 제공합니다. `layout.tsx`나 `page.tsx`에서 `metadata` 객체를 export하면 됩니다.

```tsx
// app/blog/[slug]/page.tsx
import type { Metadata } from 'next'

type Props = { params: { slug: string } }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const post = await getPost(params.slug)

  return {
    title: post.title,
    description: post.summary,
    openGraph: {
      title: post.title,
      description: post.summary,
      images: [post.coverImage],
    },
  }
}
```

동적 메타데이터도 `generateMetadata` 함수를 통해 쉽게 처리할 수 있습니다.

## Vercel 배포

Next.js는 Vercel에 배포할 때 가장 많은 기능을 활용할 수 있습니다. `vercel deploy` 한 줄로 배포가 완료되고, Edge Functions, CDN 캐싱, ISR이 자동으로 설정됩니다.

```bash
npm install -g vercel
vercel login
vercel deploy
```

환경 변수는 Vercel 대시보드의 Settings → Environment Variables에서 관리합니다. `NEXT_PUBLIC_` 접두사가 붙은 변수만 클라이언트에 노출되므로, 민감한 키는 반드시 서버 전용 변수로 선언해야 합니다.

Vercel이 아닌 자체 서버에 배포할 때는 `next build && next start`로 Node.js 서버를 실행하거나, Docker 이미지를 만들어 배포합니다.

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY . .
RUN npm ci && npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
CMD ["node", "server.js"]
```

## 실무에서 주의할 포인트

13년간 다양한 프레임워크를 써온 경험에서 Next.js 15로 처음 프로젝트를 시작할 때 자주 만나는 문제들을 정리합니다.

**Client/Server 경계 혼동**: `'use client'` 컴포넌트에서 Server Component를 import할 수 없습니다. 방향은 항상 Server → Client입니다. props로 전달하거나 Children 패턴을 활용하세요.

**환경 변수 노출**: `NEXT_PUBLIC_`이 없는 변수를 클라이언트 코드에서 참조하면 `undefined`가 됩니다. 빌드 시점에는 오류가 나지 않으므로 특히 주의해야 합니다.

**캐싱 복잡도**: fetch 캐시, Router Cache, Full Route Cache 등 여러 캐시 레이어가 존재합니다. 예상치 못한 stale 데이터가 나타나면 `revalidatePath()` 또는 `revalidateTag()`를 사용하세요.

**번들 크기**: 대형 라이브러리를 Server Component에서만 사용하면 클라이언트 번들에 포함되지 않습니다. `next/dynamic`의 `ssr: false` 옵션도 적극 활용하세요.

## 마치며

Next.js 15의 App Router는 처음에는 개념이 많아 보이지만, 핵심은 단순합니다. "데이터 패칭과 렌더링은 서버에서, 인터랙션은 클라이언트에서"라는 원칙을 따르면 됩니다. Server Components를 최대한 활용해서 클라이언트 번들을 줄이고, Route Handlers와 Server Actions로 API를 정리하면 기존 Pages Router 대비 훨씬 깔끔한 코드베이스를 만들 수 있습니다.

풀스택 웹앱을 빠르게 프로토타이핑해야 하는 상황이라면 Next.js 15 + Prisma + Vercel 조합을 강력히 추천합니다. 배포까지의 시간이 눈에 띄게 줄어들 것입니다.
