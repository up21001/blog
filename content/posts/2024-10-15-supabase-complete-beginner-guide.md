---
title: "Supabase 완전 입문 — Firebase 대안으로 백엔드 10분 만에 구축하기"
date: 2024-10-15T10:17:00+09:00
lastmod: 2024-10-16T10:17:00+09:00
description: "Supabase로 인증, 데이터베이스, 스토리지, 실시간 기능을 10분 안에 구축하는 완전 입문 가이드. Firebase와의 차이점과 마이그레이션 전략도 다룹니다."
slug: "supabase-complete-beginner-guide"
categories: ["software-dev"]
tags: ["Supabase", "Firebase 대안", "백엔드", "PostgreSQL", "풀스택"]
series: []
draft: false
---

![Supabase 아키텍처](/images/supabase-beginner-guide-2026.svg)

백엔드를 직접 구축하는 일은 여전히 시간이 많이 걸립니다. 인증 로직, 데이터베이스 설계, 파일 스토리지, API 엔드포인트까지 하나씩 만들다 보면 정작 핵심 기능 개발에 집중하기 어려워집니다. Firebase가 이 문제를 해결해줬지만, NoSQL의 한계와 벤더 종속성은 늘 걸림돌이었습니다. Supabase는 PostgreSQL을 기반으로 Firebase의 편의성과 SQL의 유연성을 동시에 제공합니다.

## Supabase란?

Supabase는 오픈소스 Firebase 대안입니다. PostgreSQL 데이터베이스를 중심으로 인증, 실시간 구독, 파일 스토리지, 엣지 함수를 하나의 플랫폼에서 제공합니다. 클라우드 서비스로 사용할 수도 있고, Docker로 자체 서버에 직접 호스팅할 수도 있습니다.

핵심 구성 요소는 다음과 같습니다.

- **Database**: PostgreSQL 15 기반. 전체 SQL 쿼리와 마이그레이션 지원
- **Auth**: 이메일, 소셜 로그인, Magic Link, SMS 인증
- **Storage**: 파일 업로드 및 CDN 배포. RLS 기반 접근 제어
- **Realtime**: WebSocket을 통한 DB 변경 이벤트 실시간 구독
- **Edge Functions**: Deno 런타임 기반 서버리스 함수

## 프로젝트 생성

### 클라우드 계정 설정

[supabase.com](https://supabase.com)에서 무료 계정을 만들고 새 프로젝트를 생성합니다. 지역은 `Northeast Asia (Seoul)`을 선택하면 레이턴시를 최소화할 수 있습니다.

프로젝트 생성 후 대시보드에서 두 가지 값을 확인합니다.

- **Project URL**: `https://[project-id].supabase.co`
- **anon public key**: 클라이언트에서 사용하는 공개 키

### 클라이언트 SDK 설치

```bash
npm install @supabase/supabase-js
```

```typescript
// src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseKey)
```

## 데이터베이스 설정

### 테이블 생성

Supabase 대시보드의 Table Editor에서 GUI로 테이블을 만들 수 있습니다. SQL Editor를 선호한다면 직접 작성하는 것이 더 빠릅니다.

```sql
-- 게시글 테이블 생성
CREATE TABLE posts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER posts_updated_at
  BEFORE UPDATE ON posts
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();
```

### Row Level Security (RLS)

RLS는 Supabase의 핵심 보안 기능입니다. 테이블 레벨에서 행 단위 접근 제어를 정의합니다.

```sql
-- RLS 활성화
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

-- 본인 게시글만 조회 가능
CREATE POLICY "Users can read own posts"
  ON posts FOR SELECT
  USING (auth.uid() = user_id);

-- 로그인한 사용자만 게시글 작성 가능
CREATE POLICY "Authenticated users can insert"
  ON posts FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- 본인 게시글만 수정 가능
CREATE POLICY "Users can update own posts"
  ON posts FOR UPDATE
  USING (auth.uid() = user_id);

-- 전체 공개 게시글 조회 (별도 컬럼 활용 시)
CREATE POLICY "Public posts are visible to all"
  ON posts FOR SELECT
  USING (is_public = true);
```

### CRUD 쿼리

```typescript
// 전체 조회
const { data: posts, error } = await supabase
  .from('posts')
  .select('*')
  .order('created_at', { ascending: false })

// 필터링
const { data } = await supabase
  .from('posts')
  .select('id, title, created_at')
  .eq('user_id', userId)
  .gte('created_at', '2026-01-01')
  .limit(10)

// 생성
const { data: newPost, error } = await supabase
  .from('posts')
  .insert({ title: '새 게시글', content: '내용', user_id: userId })
  .select()
  .single()

// 수정
const { error } = await supabase
  .from('posts')
  .update({ title: '수정된 제목' })
  .eq('id', postId)

// 삭제
const { error } = await supabase
  .from('posts')
  .delete()
  .eq('id', postId)
```

### JOIN 쿼리

Supabase는 외래 키 관계를 자동으로 인식해 간결한 JOIN 문법을 제공합니다.

```typescript
// posts와 작성자 프로필 함께 조회
const { data } = await supabase
  .from('posts')
  .select(`
    id,
    title,
    created_at,
    profiles (
      username,
      avatar_url
    )
  `)
```

## 인증 (Auth)

### 이메일 회원가입 / 로그인

```typescript
// 회원가입
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'securepassword',
  options: {
    data: {
      username: 'myusername',  // 메타데이터 추가 가능
    }
  }
})

// 로그인
const { data: session, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'securepassword',
})

// 로그아웃
await supabase.auth.signOut()
```

### 소셜 로그인

```typescript
// Google 로그인
const { error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: {
    redirectTo: `${window.location.origin}/auth/callback`,
  },
})

// GitHub 로그인
const { error } = await supabase.auth.signInWithOAuth({
  provider: 'github',
})
```

대시보드 Authentication > Providers 에서 각 소셜 서비스의 Client ID와 Secret을 설정해야 합니다.

### 세션 관리

```typescript
// 현재 세션 확인
const { data: { session } } = await supabase.auth.getSession()

// 세션 변경 이벤트 구독
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_IN') {
    console.log('로그인:', session?.user)
  }
  if (event === 'SIGNED_OUT') {
    console.log('로그아웃')
  }
})
```

## 스토리지 (Storage)

### 버킷 생성 및 파일 업로드

```typescript
// 파일 업로드
const { data, error } = await supabase.storage
  .from('avatars')
  .upload(`${userId}/profile.jpg`, file, {
    contentType: 'image/jpeg',
    upsert: true,  // 동일 경로 파일 덮어쓰기
  })

// 공개 URL 생성
const { data: { publicUrl } } = supabase.storage
  .from('avatars')
  .getPublicUrl(`${userId}/profile.jpg`)

// 임시 서명 URL (비공개 버킷용, 1시간 유효)
const { data } = await supabase.storage
  .from('private-docs')
  .createSignedUrl('report.pdf', 3600)
```

### 스토리지 RLS 설정

```sql
-- 본인 파일만 업로드 가능
CREATE POLICY "Users can upload own avatar"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'avatars' AND
    (storage.foldername(name))[1] = auth.uid()::text
  );
```

## 실시간 구독 (Realtime)

### 테이블 변경 이벤트 구독

```typescript
// 새 메시지 실시간 수신
const channel = supabase
  .channel('messages-channel')
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'messages',
      filter: `room_id=eq.${roomId}`,
    },
    (payload) => {
      console.log('새 메시지:', payload.new)
      setMessages(prev => [...prev, payload.new])
    }
  )
  .subscribe()

// 구독 해제 (컴포넌트 언마운트 시)
return () => {
  supabase.removeChannel(channel)
}
```

### Presence (온라인 상태)

```typescript
// 온라인 사용자 추적
const channel = supabase.channel('room-1')

channel
  .on('presence', { event: 'sync' }, () => {
    const state = channel.presenceState()
    console.log('현재 접속자:', state)
  })
  .subscribe(async (status) => {
    if (status === 'SUBSCRIBED') {
      await channel.track({ user_id: userId, online_at: new Date() })
    }
  })
```

## Edge Functions

서버리스 함수는 Deno 런타임에서 실행됩니다.

```typescript
// supabase/functions/send-email/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'

serve(async (req) => {
  const { email, message } = await req.json()

  // 외부 이메일 서비스 호출
  const response = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${Deno.env.get('RESEND_API_KEY')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: 'noreply@myapp.com',
      to: email,
      subject: '알림',
      text: message,
    }),
  })

  return new Response(JSON.stringify({ success: true }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
```

배포 및 호출:

```bash
# Supabase CLI로 배포
supabase functions deploy send-email

# 클라이언트에서 호출
const { data, error } = await supabase.functions.invoke('send-email', {
  body: { email: 'user@example.com', message: '안녕하세요' },
})
```

## Firebase vs Supabase 비교

| 항목 | Firebase | Supabase |
|------|---------|---------|
| 데이터베이스 | Firestore (NoSQL) | PostgreSQL (SQL) |
| 쿼리 | 제한적 | 전체 SQL 지원 |
| 오픈소스 | No | Yes |
| 자체 호스팅 | No | Yes (Docker) |
| 실시간 | Yes | Yes |
| 가격 (무료) | Spark 플랜 | 2개 프로젝트 |
| 마이그레이션 | 어려움 | SQL 덤프 가능 |
| TypeScript 지원 | 부분적 | 완전 지원 |

복잡한 관계형 데이터나 집계 쿼리가 필요하다면 Supabase가 확실히 유리합니다. Firebase는 단순한 문서 저장에는 여전히 편리합니다.

## 무료 플랜 한도

무료 플랜으로 시작할 때 알아야 할 한도입니다.

- 데이터베이스: 500MB
- 스토리지: 1GB
- 대역폭: 5GB / 월
- Edge Functions: 50만 호출 / 월
- 프로젝트: 2개
- 비활성 프로젝트는 1주일 후 일시 정지 (재활성화 가능)

사이드 프로젝트나 소규모 서비스라면 무료 플랜으로 충분히 운영할 수 있습니다.

## 정리

Supabase는 풀스택 개발자나 1인 개발자에게 최적화된 백엔드 플랫폼입니다. PostgreSQL의 강력함 위에 인증, 스토리지, 실시간 기능을 더한 것이 핵심입니다. Firebase에 익숙하다면 30분 안에 기본 기능을 전환할 수 있고, 처음 백엔드를 구축하는 분이라면 이 가이드의 내용만으로 실제 서비스를 시작할 수 있습니다. `supabase.com`에서 무료로 시작해보시기 바랍니다.
