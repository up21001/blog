---
title: "Docker 완전 입문 2026 — 개발자라면 반드시 알아야 할 컨테이너 기초"
date: 2024-09-09T08:00:00+09:00
lastmod: 2024-09-14T08:00:00+09:00
description: "Docker 개념부터 설치, 기본 명령어, Dockerfile 작성, docker-compose 실전까지. 2026년 기준 개발자가 반드시 알아야 할 컨테이너 기초를 정리합니다."
slug: "docker-complete-beginner-guide-2026"
categories: ["software-dev"]
tags: ["Docker", "컨테이너", "Dockerfile", "docker-compose", "개발 환경"]
series: []
draft: false
---

![Docker 컨테이너 구조](/images/docker-beginner-guide-2026.svg)

"내 로컬에서는 되는데요"라는 말은 개발 팀에서 가장 듣기 싫은 문장 중 하나입니다. 환경 차이에서 비롯된 문제는 디버깅에 시간을 낭비하게 만들고, 협업 효율을 떨어뜨립니다. Docker는 이 문제를 근본적으로 해결합니다. 코드와 실행 환경을 하나의 컨테이너로 묶어 어디서나 동일하게 동작하게 만드는 것이 핵심입니다. 13년간 다양한 배포 환경을 경험하면서 Docker는 선택이 아닌 필수 기술이 됐습니다.

## Docker란 무엇인가

Docker는 애플리케이션과 그 실행 환경을 컨테이너 단위로 패키징하는 플랫폼입니다. 가상 머신(VM)과 자주 비교되지만 동작 방식이 다릅니다.

- **VM**: 하이퍼바이저 위에 게스트 OS 전체를 올립니다. 수 GB 크기, 부팅에 수십 초가 걸립니다.
- **컨테이너**: 호스트 OS의 커널을 공유하고 프로세스 격리만 수행합니다. 수 MB 크기, 밀리초 단위로 시작합니다.

컨테이너는 이미지에서 실행됩니다. 이미지는 애플리케이션 실행에 필요한 모든 것(코드, 런타임, 라이브러리, 환경변수)을 담은 불변의 스냅샷입니다.

## 설치

### macOS

```bash
# Homebrew로 설치
brew install --cask docker

# 또는 Docker Desktop 공식 설치 파일 사용
# https://docs.docker.com/desktop/install/mac-install/
```

### Linux (Ubuntu)

```bash
# 공식 스크립트로 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 현재 사용자를 docker 그룹에 추가 (sudo 없이 사용)
sudo usermod -aG docker $USER
newgrp docker
```

### Windows

Docker Desktop을 설치하고 WSL2 백엔드를 활성화합니다. Windows 11에서는 WSL2가 기본으로 설치됩니다.

### 설치 확인

```bash
docker --version
# Docker version 26.1.0, build ...

docker run hello-world
# Hello from Docker! 메시지가 출력되면 정상
```

## 핵심 개념

### 이미지 (Image)

컨테이너의 설계도입니다. 레이어 구조로 이루어져 있어 변경된 레이어만 새로 다운로드합니다.

```bash
# Docker Hub에서 이미지 검색
docker search nginx

# 이미지 다운로드
docker pull nginx:1.25-alpine

# 다운로드된 이미지 목록
docker images

# 이미지 삭제
docker rmi nginx:1.25-alpine
```

### 컨테이너 (Container)

이미지를 실행한 인스턴스입니다. 이미지 하나에서 여러 컨테이너를 실행할 수 있습니다.

```bash
# 컨테이너 실행
docker run nginx

# 백그라운드 실행 (-d), 포트 매핑 (-p), 이름 지정 (--name)
docker run -d -p 8080:80 --name my-nginx nginx

# 실행 중인 컨테이너 목록
docker ps

# 모든 컨테이너 목록 (중지된 것 포함)
docker ps -a

# 컨테이너 중지
docker stop my-nginx

# 컨테이너 시작
docker start my-nginx

# 컨테이너 삭제
docker rm my-nginx

# 중지 후 삭제
docker rm -f my-nginx
```

### 주요 실행 옵션

```bash
# 환경변수 설정
docker run -e NODE_ENV=production -e PORT=3000 my-app

# 볼륨 마운트 (호스트:컨테이너)
docker run -v $(pwd)/data:/app/data my-app

# 네트워크 지정
docker run --network my-network my-app

# 컨테이너 내부 쉘 접속
docker run -it ubuntu bash

# 실행 중인 컨테이너에 접속
docker exec -it my-nginx bash

# 로그 확인
docker logs my-nginx
docker logs -f my-nginx  # 실시간 스트리밍
```

## Dockerfile 작성

Dockerfile은 이미지 빌드 지침서입니다. 각 명령어가 하나의 레이어를 생성합니다.

### Node.js 애플리케이션 예시

```dockerfile
# Dockerfile
# 1. 베이스 이미지 지정
FROM node:20-alpine

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 의존성 파일 먼저 복사 (캐시 활용)
COPY package*.json ./

# 4. 의존성 설치
RUN npm ci --only=production

# 5. 소스 코드 복사
COPY . .

# 6. 빌드 (TypeScript 등)
RUN npm run build

# 7. 포트 노출 (문서용, 실제 매핑은 run 시 -p로)
EXPOSE 3000

# 8. 실행 명령
CMD ["node", "dist/index.js"]
```

### 멀티 스테이지 빌드 (권장)

빌드 도구를 최종 이미지에 포함시키지 않아 이미지 크기를 줄입니다.

```dockerfile
# Dockerfile
# Stage 1: 빌드
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: 실행
FROM node:20-alpine AS runner

WORKDIR /app

# 프로덕션 의존성만 설치
COPY package*.json ./
RUN npm ci --only=production

# 빌드 결과물만 복사
COPY --from=builder /app/dist ./dist

EXPOSE 3000
CMD ["node", "dist/index.js"]
```

빌드 도구(TypeScript 컴파일러, webpack 등)가 최종 이미지에 포함되지 않아 이미지 크기가 크게 줄어듭니다.

### .dockerignore

불필요한 파일이 이미지에 포함되지 않도록 제외합니다.

```plaintext
node_modules
.git
.gitignore
*.md
dist
.env
.env.*
coverage
.nyc_output
```

### 이미지 빌드

```bash
# 현재 디렉토리의 Dockerfile로 빌드
docker build -t my-app:1.0 .

# 특정 Dockerfile 지정
docker build -f Dockerfile.prod -t my-app:prod .

# 빌드 인수 전달
docker build --build-arg NODE_ENV=production -t my-app .

# 빌드 결과 확인
docker images my-app
```

## docker-compose

여러 컨테이너를 함께 정의하고 관리합니다. 실무에서 가장 많이 사용하는 방식입니다.

### 기본 구성 예시

```yaml
# docker-compose.yml
version: '3.9'

services:
  # Node.js 앱
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:password@db:5432/myapp
      - REDIS_URL=redis://cache:6379
    volumes:
      - ./src:/app/src  # 개발 중 소스 변경 실시간 반영
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_started
    restart: unless-stopped

  # PostgreSQL 데이터베이스
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql  # 초기 SQL
    ports:
      - "5432:5432"  # 로컬 DB 클라이언트 접속용
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis 캐시
  cache:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  # Nginx 리버스 프록시 (선택)
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

### docker-compose 주요 명령어

```bash
# 모든 서비스 시작 (백그라운드)
docker-compose up -d

# 특정 서비스만 시작
docker-compose up -d app db

# 서비스 중지 (컨테이너 삭제)
docker-compose down

# 볼륨까지 삭제 (데이터 초기화)
docker-compose down -v

# 로그 확인
docker-compose logs -f app

# 특정 서비스 쉘 접속
docker-compose exec app sh

# 서비스 재시작
docker-compose restart app

# 이미지 재빌드
docker-compose build --no-cache app
docker-compose up -d --build

# 현재 상태 확인
docker-compose ps
```

### 환경별 설정 분리

```yaml
# docker-compose.override.yml (개발 환경 — 자동 적용)
version: '3.9'

services:
  app:
    environment:
      - DEBUG=true
    volumes:
      - ./src:/app/src
    command: npm run dev
```

```bash
# 프로덕션 환경
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 네트워크와 볼륨

### 네트워크

같은 docker-compose 파일에 정의된 서비스는 서비스 이름으로 서로 통신합니다. `app` 서비스에서 `db` 서비스에 접근할 때 호스트명이 `db`입니다.

```bash
# 수동으로 네트워크 생성
docker network create my-network

# 컨테이너를 네트워크에 연결
docker run --network my-network my-app

# 네트워크 목록
docker network ls

# 네트워크 상세 정보
docker network inspect my-network
```

### 볼륨

데이터 영속성을 위해 사용합니다. 컨테이너가 삭제돼도 볼륨의 데이터는 유지됩니다.

```bash
# Named volume 생성
docker volume create my-data

# 볼륨 목록
docker volume ls

# 볼륨 상세 정보 (실제 저장 경로 확인)
docker volume inspect my-data

# 미사용 볼륨 정리
docker volume prune
```

## 실전 팁

### 이미지 크기 최소화

```dockerfile
# 알파인 리눅스 사용 (수십 MB → 수 MB)
FROM node:20-alpine

# apt 캐시 정리
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# npm 캐시 정리
RUN npm ci && npm cache clean --force
```

### 레이어 캐시 활용

변경이 잦은 파일일수록 Dockerfile 뒤쪽에 배치합니다. 의존성 파일(`package.json`)이 소스 코드보다 훨씬 덜 변경되므로 먼저 복사합니다.

```dockerfile
# 좋은 예: 캐시 활용
COPY package*.json ./
RUN npm ci
COPY . .

# 나쁜 예: 매번 전체 재설치
COPY . .
RUN npm ci
```

### 보안 고려사항

```dockerfile
# root로 실행하지 않기
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# 시크릿을 이미지에 굽지 않기
# 나쁜 예
ENV API_KEY=secret123

# 좋은 예 — 런타임에 환경변수로 주입
# docker run -e API_KEY=secret123 my-app
```

### 리소스 정리

```bash
# 중지된 컨테이너, 미사용 이미지, 네트워크, 볼륨 일괄 정리
docker system prune -a

# 디스크 사용량 확인
docker system df
```

### 헬스체크

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
```

## 자주 마주치는 문제

**포트 충돌**
```bash
# 포트를 사용 중인 프로세스 확인
lsof -i :3000
# 다른 포트로 매핑
docker run -p 3001:3000 my-app
```

**볼륨 권한 문제 (Linux)**
```bash
# 컨테이너 내부 사용자 UID를 호스트와 맞춤
docker run --user $(id -u):$(id -g) my-app
```

**이미지 빌드 캐시 무효화**
```bash
docker build --no-cache -t my-app .
```

**컨테이너 로그가 너무 많이 쌓일 때**
```yaml
# docker-compose.yml
services:
  app:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

## 정리

Docker는 처음 접할 때 개념이 낯설게 느껴지지만, 기본 명령어 20개 정도를 익히면 일상적인 개발에 바로 적용할 수 있습니다. 가장 빠른 학습 방법은 현재 프로젝트에 `docker-compose.yml`을 만들어 데이터베이스부터 컨테이너로 실행해보는 것입니다. 로컬 환경에 PostgreSQL이나 Redis를 직접 설치하는 대신 `docker-compose up -d db`로 시작해보시기 바랍니다. 팀 전원이 동일한 환경에서 작업하는 경험은 한 번 해보면 다시는 이전으로 돌아가기 어렵습니다.
