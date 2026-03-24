---
title: "Hugo + Cloudflare Pages 자동 배포 파이프라인 구축 완전 가이드 — 2편"
date: 2021-06-04T08:00:00+09:00
lastmod: 2021-06-09T08:00:00+09:00
description: "Hugo 블로그를 Cloudflare Pages에 연동하여 git push 한 번으로 전 세계에 자동 배포되는 파이프라인을 구축하는 방법을 단계별로 설명합니다."
slug: "blog-automation-series-2-hugo-cloudflare"
categories: ["ai-automation"]
tags: ["Hugo 설치", "Cloudflare Pages", "자동 배포", "GitHub 연동", "Blowfish 테마", "정적 사이트 생성"]
series: ["블로그-자동화"]
draft: false
---

Hugo와 Cloudflare Pages를 연동하면 git push 한 번으로 전 세계에 자동 배포되는 블로그를 만들 수 있습니다. 설정만 한 번 해두면 이후에는 글 쓰는 것 외에 아무것도 신경 쓸 필요가 없습니다. 이 편에서는 Hugo 설치부터 Cloudflare Pages 자동 배포까지 전 과정을 단계별로 설명합니다.

![Hugo Cloudflare 배포 흐름](/images/hugo-cloudflare-deploy-flow.svg)

## Hugo 설치

Hugo는 운영체제별로 설치 방법이 다릅니다. 공식적으로는 Extended 버전 설치를 권장합니다. SCSS/SASS 처리를 위해 Extended 버전이 필요한 테마들이 많기 때문입니다.

### Windows

Windows에서 가장 간편한 설치 방법은 Scoop 패키지 매니저를 사용하는 것입니다.

```powershell
# Scoop 설치 (이미 설치된 경우 생략)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# Hugo Extended 설치
scoop install hugo-extended
```

Winget을 사용하는 경우:

```powershell
winget install Hugo.Hugo.Extended
```

또는 [Hugo 공식 GitHub 릴리스](https://github.com/gohugoio/hugo/releases)에서 `hugo_extended_0.145.0_windows-amd64.zip`을 직접 다운로드하여 PATH에 추가할 수도 있습니다.

### macOS

```bash
brew install hugo
```

### Linux (Ubuntu/Debian)

```bash
# snap 사용
sudo snap install hugo

# 또는 직접 다운로드
wget https://github.com/gohugoio/hugo/releases/download/v0.145.0/hugo_extended_0.145.0_linux-amd64.tar.gz
tar xzf hugo_extended_0.145.0_linux-amd64.tar.gz
sudo mv hugo /usr/local/bin/
```

### 설치 확인

```bash
hugo version
# hugo v0.145.0+extended ...
```

## Hugo 프로젝트 생성

```bash
hugo new site my-blog
cd my-blog
git init
```

이 명령으로 다음 구조가 생성됩니다.

```
my-blog/
├── archetypes/
├── assets/
├── content/
├── data/
├── layouts/
├── public/         # 빌드 결과물 (git에 포함하지 않음)
├── resources/
├── static/
├── themes/
└── hugo.toml       # 메인 설정 파일
```

## Blowfish 테마 설치

Blowfish는 Hugo 테마 중에서 기능이 가장 풍부한 편에 속합니다. 다크모드, 반응형 디자인, 검색, 태그/카테고리, 소셜 링크, 구글 애널리틱스 연동 등을 기본 제공합니다.

Git submodule 방식으로 설치합니다.

```bash
git submodule add -b main https://github.com/nunocoracao/blowfish.git themes/blowfish
```

또는 Hugo Modules 방식:

```bash
# go.mod 초기화
hugo mod init github.com/your-username/your-blog

# hugo.toml에 추가
# [module]
#   [[module.imports]]
#     path = "github.com/nunocoracao/blowfish"
```

## hugo.toml 설정

Blowfish 테마를 활용하기 위한 핵심 설정입니다.

```toml
baseURL = "https://blog-8ye.pages.dev"
languageCode = "ko"
defaultContentLanguage = "ko"
title = "My Blog"
theme = "blowfish"

[taxonomies]
  tag = "tags"
  category = "categories"

[params]
  colorScheme = "ocean"      # 색상 테마: ocean, fire, forest, slate 등
  defaultAppearance = "dark" # 기본 다크모드
  autoSwitchAppearance = true # 시스템 설정 따라가기

  enableSearch = true        # 검색 기능
  enableCodeCopy = true      # 코드 복사 버튼

  [params.homepage]
    layout = "profile"       # 홈 레이아웃: profile, page, hero, background
    showRecent = true
    showRecentItems = 5

[params.article]
  showDate = true
  showDateUpdated = true
  showReadingTime = true
  showTableOfContents = true # 목차 자동 생성
  showTaxonomies = true
  showWordCount = true

[params.list]
  showCards = true
  groupByYear = true

[markup]
  [markup.highlight]
    style = "dracula"        # 코드 하이라이팅 스타일
    lineNos = false
    guessSyntax = true
  [markup.goldmark]
    [markup.goldmark.renderer]
      unsafe = true          # HTML 태그 허용

[outputs]
  home = ["HTML", "RSS", "JSON"]  # JSON은 검색 기능에 필요
```

### 언어 설정 파일

`config/_default/languages.ko.toml` 파일을 생성합니다.

```toml
languageName = "한국어"
weight = 1

[params]
  displayName = "KO"
  isoCode = "ko"
  rtl = false
  dateFormat = "2006년 1월 2일"

  [params.author]
    name = "작성자 이름"
    bio = "블로그 소개 문구"
    links = [
      { github = "https://github.com/username" }
    ]
```

## 첫 포스트 작성

```bash
hugo new content posts/2026-03-23-first-post.md
```

생성된 파일을 열면 archetypes에 정의된 front matter가 자동으로 채워져 있습니다.

기본 front matter 템플릿을 커스터마이즈하려면 `archetypes/default.md`를 수정합니다.

```markdown
---
title: "{{ replace .File.ContentBaseName "-" " " | title }}"
date: 2021-06-04T08:00:00+09:00
lastmod: 2021-06-09T08:00:00+09:00
description: ""
slug: "{{ .File.ContentBaseName }}"
categories: ["ai-automation"]
tags: []
draft: false
---
```

## 로컬 미리보기

```bash
hugo server -D
```

`-D` 플래그는 draft: true인 포스트도 표시합니다. 브라우저에서 `http://localhost:1313`으로 접속하면 실시간으로 변경사항이 반영되는 미리보기를 볼 수 있습니다.

## GitHub 저장소 연결

```bash
# .gitignore 생성
echo "public/" >> .gitignore
echo "resources/" >> .gitignore
echo ".hugo_build.lock" >> .gitignore

# GitHub에 저장소 생성 후 연결
git remote add origin https://github.com/your-username/your-blog.git
git add .
git commit -m "initial: Hugo blog setup"
git push -u origin main
```

## Cloudflare Pages 연동

### 1. Cloudflare 대시보드 접속

[Cloudflare 대시보드](https://dash.cloudflare.com)에 로그인한 뒤 왼쪽 사이드바에서 **Workers & Pages**를 클릭합니다.

### 2. 새 Pages 프로젝트 생성

**Create application** → **Pages** → **Connect to Git**을 선택합니다.

GitHub 계정을 연결하면 저장소 목록이 나타납니다. 방금 만든 블로그 저장소를 선택하고 **Begin setup**을 클릭합니다.

### 3. 빌드 설정

빌드 설정 화면에서 다음과 같이 입력합니다.

| 항목 | 값 |
|---|---|
| 프로젝트 이름 | blog (또는 원하는 이름) |
| Production branch | main |
| 프레임워크 사전 설정 | Hugo |
| 빌드 명령어 | hugo --minify |
| 빌드 출력 디렉토리 | public |

### 4. 환경 변수 설정

Hugo 버전을 명시하지 않으면 Cloudflare Pages가 오래된 버전으로 빌드할 수 있습니다. **Environment variables** 섹션에 다음을 추가합니다.

| 변수명 | 값 |
|---|---|
| HUGO_VERSION | 0.145.0 |

**Save and Deploy** 버튼을 클릭하면 첫 번째 빌드가 시작됩니다.

### 5. 배포 완료 확인

빌드 로그를 실시간으로 확인할 수 있습니다. 성공하면 `your-project.pages.dev` 형태의 URL이 발급됩니다.

이후로는 `git push`할 때마다 Cloudflare Pages가 자동으로 빌드와 배포를 실행합니다.

## 커스텀 도메인 연결 (선택사항)

자체 도메인이 있다면 Cloudflare Pages 프로젝트의 **Custom domains** 탭에서 연결할 수 있습니다. 도메인이 Cloudflare에 등록되어 있다면 DNS 설정이 자동으로 처리됩니다.

## 배포 최적화 팁

### hugo.toml에 baseURL 정확히 설정

`baseURL`이 잘못 설정되어 있으면 CSS, JavaScript, 이미지 경로가 깨질 수 있습니다. Cloudflare Pages에서 발급된 URL을 정확히 입력합니다.

```toml
baseURL = "https://blog-8ye.pages.dev"
```

### public 폴더를 git에 포함하지 않기

Cloudflare Pages가 직접 빌드하므로 `public/` 디렉토리를 git에 포함할 필요가 없습니다. `.gitignore`에 반드시 추가합니다.

### 빌드 시간 단축

Hugo는 기본적으로 매우 빠르지만, 포스트가 수백 개로 늘어나도 Cloudflare Pages의 빌드 시간은 보통 30초 이내입니다. 이미지가 많다면 `static/` 대신 Cloudflare Images나 외부 CDN을 활용하면 저장소 크기를 줄일 수 있습니다.

## 배포 흐름 정리

1. 로컬에서 포스트 작성 또는 `generate_post.py`로 자동 생성
2. `git add`, `git commit`, `git push`
3. Cloudflare Pages가 push를 감지하고 빌드 시작 (약 5초 후)
4. `hugo --minify` 실행 (약 30초)
5. `public/` 디렉토리를 전 세계 CDN에 배포
6. 약 60초 후 라이브 상태 확인 가능

이 흐름이 완성되면 글쓰기에만 집중할 수 있는 환경이 만들어집니다. 다음 편에서는 Gemini API를 활용해 포스트 초안을 자동 생성하는 Python 스크립트를 구현합니다.
