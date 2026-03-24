---
title: "Docker Compose로 Node.js & PostgreSQL 로컬 개발 환경 초고속 구축하기"
date: 2021-09-18T08:00:00+09:00
lastmod: 2021-09-23T08:00:00+09:00
description: "Docker Compose를 활용하여 Node.js 애플리케이션과 PostgreSQL 데이터베이스를 포함하는 로컬 개발 환경을 효율적으로 구축하는 방법을 설명합니다. 개발 생산성 향상과 환경 일관성 유지에 초점을 맞춥니다."
slug: "docker-compose-nodejs-postgresql-local-development-environment"
categories: ["software-dev"]
tags: ["Docker Compose", "Node.js 개발 환경", "PostgreSQL Docker", "로컬 개발", "컨테이너화", "개발 생산성"]
draft: false
---

![Docker Compose 아키텍처 다이어그램](/images/docker-compose-architecture.svg)

안녕하세요, 13년 차 하드웨어/소프트웨어 엔지니어이자 기술 블로거입니다. 오늘은 개발자라면 누구나 한 번쯤 겪어봤을 '내 컴퓨터에서는 되는데 네 컴퓨터에서는 안돼!' 문제를 해결해 줄 강력한 도구, Docker Compose를 활용하여 Node.js 애플리케이션과 PostgreSQL 데이터베이스로 구성된 로컬 개발 환경을 구축하는 방법을 공유하고자 합니다. 이 가이드를 통해 개발 환경 설정에 드는 시간을 줄이고, 핵심 개발에 집중할 수 있게 될 것입니다.

### 1. 왜 Docker Compose로 로컬 개발 환경을 구축해야 할까요?

전통적인 개발 환경 설정은 많은 시간과 노력을 필요로 합니다. Node.js 런타임 설치, PostgreSQL 데이터베이스 설치, 의존성 관리 등 각 컴포넌트마다 다른 설치 과정을 거쳐야 하며, 버전 충돌이나 운영체제(OS)별 차이로 인해 예측치 못한 문제가 발생하기도 합니다. 특히 팀 프로젝트에서는 각 개발자의 환경이 달라 디버깅에 어려움을 겪는 경우가 빈번합니다.

Docker Compose는 이러한 문제를 해결해 줍니다. 애플리케이션과 그 의존성(데이터베이스, 캐시 등)을 컨테이너화하고, YAML 파일을 통해 이 컨테이너들을 한 번에 정의하고 실행할 수 있도록 합니다. 이는 다음과 같은 이점을 제공합니다.

*   **환경 일관성:** 모든 팀원이 동일한 개발 환경을 공유하여 "내 컴퓨터에서는 되는데..." 문제를 방지합니다.
*   **빠른 설정:** 새로운 개발자가 프로젝트에 합류했을 때, `docker-compose up` 명령 하나로 모든 환경을 구축할 수 있습니다.
*   **격리성:** 각 서비스가 독립된 컨테이너에서 실행되므로, 한 서비스의 변경이 다른 서비스에 영향을 주지 않습니다.
*   **쉬운 버전 관리:** `docker-compose.yml` 파일만으로 각 서비스의 버전을 명확히 관리할 수 있습니다.

필자의 경험상, 초기 프로젝트 설정 단계에서 Docker Compose를 도입하면 장기적으로 개발 생산성을 크게 향상시킬 수 있었습니다.

### 2. Node.js & PostgreSQL 개발 환경 구축을 위한 Docker Compose 설정

이제 본격적으로 Docker Compose 파일을 작성하고 Node.js 애플리케이션 및 PostgreSQL 데이터베이스 컨테이너를 정의해 보겠습니다.

#### 2.1 프로젝트 구조 설정

먼저 다음과 같은 프로젝트 디렉토리 구조를 만듭니다.

```
.
├── docker-compose.yml
├── node-app/
│   ├── Dockerfile
│   ├── package.json
│   ├── package-lock.json
│   └── server.js
└── .env
```

*   `docker-compose.yml`: Docker Compose 설정을 정의하는 파일입니다.
*   `node-app/`: Node.js 애플리케이션 코드를 포함하는 디렉토리입니다.
*   `.env`: 환경 변수를 관리하는 파일입니다.

#### 2.2 `.env` 파일 설정

데이터베이스 연결 정보와 같은 민감한 정보는 `.env` 파일에 저장하여 관리하는 것이 좋습니다.

```env
# PostgreSQL 설정
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=mydb
PG_PORT=5432

# Node.js 설정
NODE_PORT=3000
```

#### 2.3 `node-app/Dockerfile` 작성

Node.js 애플리케이션을 위한 Docker 이미지를 빌드하는 `Dockerfile`입니다.

```dockerfile
# node-app/Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["node", "server.js"]
```

*   `FROM node:18-alpine`: Node.js 18 버전의 Alpine Linux 기반 이미지를 사용합니다. 경량화된 이미지로 컨테이너 크기를 줄일 수 있습니다.
*   `WORKDIR /app`: 컨테이너 내부의 작업 디렉토리를 `/app`으로 설정합니다.
*   `COPY package*.json ./`: `package.json`과 `package-lock.json` 파일을 작업 디렉토리로 복사합니다.
*   `RUN npm install`: Node.js 의존성 패키지를 설치합니다. 이 단계를 `COPY . .` 앞에 두면, 소스 코드가 변경되어도 `node_modules`가 재빌드되지 않아 빌드 속도를 높일 수 있습니다.
*   `COPY . .`: 현재 디렉토리의 모든 파일(Node.js 소스 코드)을 `/app`으로 복사합니다.
*   `EXPOSE 3000`: Node.js 애플리케이션이 3000번 포트에서 실행됨을 외부에 알립니다.
*   `CMD ["node", "server.js"]`: 컨테이너가 시작될 때 `server.js` 파일을 실행합니다.

#### 2.4 `node-app/server.js` 작성 (간단한 Node.js 애플리케이션)

PostgreSQL에 연결하여 데이터를 저장하고 조회하는 간단한 Node.js 애플리케이션입니다. `pg` 라이브러리를 사용합니다.

```javascript
// node-app/server.js
const express = require('express');
const { Pool } = require('pg');
const app = express();
const port = process.env.NODE_PORT || 3000;

// PostgreSQL 연결 설정
const pool = new Pool({
  user: process.env.POSTGRES_USER,
  host: 'db', // Docker Compose 서비스 이름으로 호스트 지정
  database: process.env.POSTGRES_DB,
  password: process.env.POSTGRES_PASSWORD,
  port: process.env.PG_PORT,
});

app.use(express.json());

// 루트 경로
app.get('/', (req, res) => {
  res.send('Node.js & PostgreSQL Docker Compose Example!');
});

// 데이터베이스 연결 테스트 및 테이블 생성
app.get('/init', async (req, res) => {
  try {
    const client = await pool.connect();
    await client.query(`
      CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        text VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);
    client.release();
    res.status(200).send('Database initialized and table created successfully!');
  } catch (err) {
    console.error('Database initialization error:', err);
    res.status(500).send('Failed to initialize database.');
  }
});

// 메시지 저장
app.post('/messages', async (req, res) => {
  const { text } = req.body;
  if (!text) {
    return res.status(400).send('Message text is required.');
  }
  try {
    const client = await pool.connect();
    const result = await client.query(
      'INSERT INTO messages(text) VALUES($1) RETURNING *',
      [text]
    );
    client.release();
    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error('Error saving message:', err);
    res.status(500).send('Failed to save message.');
  }
});

// 모든 메시지 조회
app.get('/messages', async (req, res) => {
  try {
    const client = await pool.connect();
    const result = await client.query('SELECT * FROM messages ORDER BY created_at DESC');
    client.release();
    res.status(200).json(result.rows);
  } catch (err) {
    console.error('Error fetching messages:', err);
    res.status(500).send('Failed to fetch messages.');
  }
});

app.listen(port, () => {
  console.log(`Node.js app listening at http://localhost:${port}`);
});
```

`node-app/package.json` 파일도 생성해야 합니다.

```json
{
  "name": "node-app",
  "version": "1.0.0",
  "description": "Node.js app with PostgreSQL",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "pg": "^8.11.3"
  }
}
```

#### 2.5 `docker-compose.yml` 작성

이제 Node.js 애플리케이션과 PostgreSQL 데이터베이스를 함께 실행하기 위한 `docker-compose.yml` 파일을 작성합니다.

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: ./node-app
    ports:
      - "${NODE_PORT}:${NODE_PORT}"
    environment:
      NODE_ENV: development
      PG_PORT: ${PG_PORT}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    depends_on:
      - db
    volumes:
      - ./node-app:/app
      - /app/node_modules # node_modules는 호스트에 마운트하지 않음
    env_file:
      - ./.env

  db:
    image: postgres:15-alpine
    ports:
      - "${PG_PORT}:${PG_PORT}"
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - db_data:/var/lib/postgresql/data
    env_file:
      - ./.env

volumes:
  db_data:
```

*   `version: '3.8'`: Docker Compose 파일 형식 버전을 지정합니다.
*   `services`: 실행할 서비스들을 정의합니다.
    *   **`app` 서비스 (Node.js 애플리케이션):**
        *   `build: ./node-app`: `node-app` 디렉토리의 `Dockerfile`을 사용하여 이미지를 빌드합니다.
        *   `ports: - "${NODE_PORT}:${NODE_PORT}"`: 호스트의 `NODE_PORT`(예: 3000)와 컨테이너의 3000번 포트를 연결합니다. `.env` 파일의 변수를 사용합니다.
        *   `environment`: 컨테이너 내부에 전달될 환경 변수들을 정의합니다. `.env` 파일의 변수를 참조합니다.
        *   `depends_on: - db`: `app` 서비스는 `db` 서비스가 시작된 후에 시작되어야 함을 명시합니다. (이것은 시작 순서만 보장하며, `db` 서비스가 완전히 준비되었음을 보장하지는 않습니다. 실제 프로덕션 환경에서는 헬스 체크를 추가하는 것이 좋습니다.)
        *   `volumes`:
            *   `- ./node-app:/app`: 호스트의 `node-app` 디렉토리를 컨테이너의 `/app` 디렉토리에 마운트(바인드 마운트)합니다. 이를 통해 호스트에서 코드를 수정하면 컨테이너에 즉시 반영되어 개발 시 편리합니다.
            *   `- /app/node_modules`: `node_modules` 디렉토리는 호스트에 마운트하지 않도록 명시적으로 제외합니다. 컨테이너 내부의 `node_modules`를 사용해야 합니다. 그렇지 않으면 호스트의 OS와 컨테이너의 OS가 달라 의존성 문제가 발생할 수 있습니다.
        *   `env_file: - ./.env`: `.env` 파일에서 환경 변수를 로드합니다.
    *   **`db` 서비스 (PostgreSQL 데이터베이스):**
        *   `image: postgres:15-alpine`: PostgreSQL 15 버전의 Alpine Linux 기반 이미지를 사용합니다.
        *   `ports: - "${PG_PORT}:${PG_PORT}"`: 호스트의 `PG_PORT`(예: 5432)와 컨테이너의 5432번 포트를 연결합니다.
        *   `environment`: PostgreSQL 컨테이너에 필요한 환경 변수들을 정의합니다. `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`는 데이터베이스 초기 설정에 사용됩니다.
        *   `volumes: - db_data:/var/lib/postgresql/data`: `db_data`라는 이름의 Docker 볼륨을 생성하고, 이를 PostgreSQL 데이터가 저장되는 컨테이너 내부 경로에 마운트합니다. 이 볼륨을 사용하면 컨테이너가 삭제되어도 데이터는 유지됩니다.
        *   `env_file: - ./.env`: `.env` 파일에서 환경 변수를 로드합니다.
*   `volumes`: Docker 볼륨을 정의합니다. `db_data`는 PostgreSQL 데이터 영속성을 위해 사용됩니다.

#### 2.6 Docker Compose 실행

모든 파일 작성을 마쳤다면, 프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 서비스를 시작합니다.

```bash
docker-compose up --build
```

*   `up`: `docker-compose.yml` 파일에 정의된 서비스들을 시작합니다.
*   `--build`: 이미지가 아직 빌드되지 않았거나 `Dockerfile`이 변경되었을 경우, 다시 빌드하도록 합니다.

백그라운드에서 실행하려면 `-d` 옵션을 추가합니다.

```bash
docker-compose up -d --build
```

컨테이너의 로그를 확인하려면:

```bash
docker-compose logs -f
```

서비스가 정상적으로 실행되면, 웹 브라우저에서 `http://localhost:3000`에 접속하여 Node.js 애플리케이션을 확인할 수 있습니다.

**테스트 절차:**

1.  브라우저 또는 `curl`로 `http://localhost:3000/init`에 접속하여 데이터베이스를 초기화하고 `messages` 테이블을 생성합니다.
    ```bash
    curl http://localhost:3000/init
    ```
2.  새로운 메시지를 저장합니다.
    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"text": "Hello Docker Compose!"}' http://localhost:3000/messages
    ```
3.  저장된 메시지들을 조회합니다.
    ```bash
    curl http://localhost:3000/messages
    ```

#### 2.7 Docker Compose 서비스 중지 및 삭제

개발이 완료되거나 서비스를 중지하고 싶을 때는 다음 명령어를 사용합니다.

```bash
docker-compose down
```

*   `down`: `docker-compose.yml` 파일에 정의된 서비스들을 중지하고 컨테이너를 제거합니다.

데이터 볼륨까지 완전히 삭제하려면 `-v` 옵션을 추가합니다.

```bash
docker-compose down -v
```

이 명령은 `db_data` 볼륨도 함께 삭제하므로, 데이터가 영구적으로 지워진다는 점에 유의해야 합니다.

### 3. 결론 및 요약

Docker Compose는 Node.js와 PostgreSQL을 포함한 복잡한 로컬 개발 환경을 쉽고 빠르게 구축할 수 있도록 돕는 강력한 도구입니다. 이 글에서 제시된 `.env`, `Dockerfile`, `docker-compose.yml` 파일을 통해 환경 일관성을 확보하고, 개발 생산성을 크게 향상시킬 수 있습니다.

*   Docker Compose는 개발 환경의 일관성을 보장하고, 초기 설정 시간을 대폭 단축시킵니다.
*   Node.js 애플리케이션과 PostgreSQL 데이터베이스를 컨테이너화하여 독립적으로 관리하고 연동할 수 있습니다.
*   `docker-compose up --build` 명령 하나로 전체 개발 스택을 간편하게 시작하고 관리할 수 있습니다.

필자의 경험상, 한 번 Docker Compose의 편리함에 익숙해지면 다시는 수동 환경 설정으로 돌아가고 싶지 않을 것입니다. 지금 바로 여러분의 프로젝트에 적용해 보시길 강력히 추천합니다!

![Docker Compose Workflow](image-placeholder.png)