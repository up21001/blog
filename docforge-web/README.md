# DocForge 웹앱

주제만 입력하면 **마크다운 문서**를 생성하고, 선택 시 **삽화 이미지**(Imagen → Gemini 이미지 폴백, AiVS 패턴)를 붙입니다. 텍스트는 `gemini-2.5-flash`를 사용합니다.

---

## 요구 사항

- Python 3.10+
- `GEMINI_API_KEY` — 블로그 프로젝트 루트 `c:\My\Claude\Blog\blog\.env` 또는 이 폴더의 `.env`에 설정
- (선택) `DOCFORGE_POSTS_DIR` — **저장** 시 사용할 경로. 비우면 `blog/content/posts` 로 간주합니다. `…/content`만 지정해도 자동으로 `…/content/posts`를 씁니다. 쓰기 가능 여부는 Windows에서도 실제 임시 파일 생성으로 검사합니다.

---

## 설치

```bash
cd docforge-web
pip install -r requirements.txt
```

---

## 실행

PowerShell:

```powershell
cd c:\My\Claude\Blog\blog\docforge-web
.\run.ps1
```

또는:

```bash
cd docforge-web
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8765
```

브라우저 주소창에 **`http://127.0.0.1:8765/`** 를 입력해 연다. (`index.html`을 탐색기에서 더블클릭해 **파일로 열면** `file://` 이라 API에 연결되지 않는다.)

---

## 시스템 구조

```
docforge-web/
├── app.py                     FastAPI 앱 (API 엔드포인트)
├── run.ps1                    로컬 실행 스크립트 (127.0.0.1:8765)
├── run-lan.ps1                LAN 노출용 실행 스크립트 (0.0.0.0:8765)
├── requirements.txt
├── .env.example               API 키 예시
├── data/
│   └── user_prompts.json      사용자 편집 프롬프트 (없으면 코드 기본값)
├── services/
│   ├── prompts.py             내장 시스템 프롬프트 (BLOG / PHILOSOPHY / PLAIN)
│   ├── prompt_config.py       프롬프트 로드·저장·검증 로직
│   ├── text_gen.py            Gemini 텍스트 생성 (gemini-2.5-flash)
│   ├── image_gen.py           Imagen / Gemini 이미지 생성 (폴백 체인)
│   ├── markdown_images.py     생성 이미지를 마크다운에 삽입
│   └── publish.py             content/posts 저장 · 파일명 추천
└── static/
    ├── index.html             메인 UI
    ├── app.js                 메인 UI 동작 (생성·미리보기·저장·재생성)
    ├── style.css              전체 스타일
    ├── edit.html              프롬프트 편집 UI
    ├── edit.js                편집 페이지 동작
    └── edit.css               편집 페이지 스타일
```

---

## 사용 흐름 (생성 → 검토 → 배포)

### 1단계: 생성

메인 화면(`/`)에서:

| 옵션 | 설명 |
|------|------|
| **주제** | 자유 텍스트. 한국어·영어 모두 가능 |
| **템플릿** | `blog` (Hugo 기술 블로그) / `philosophy` (철학 에세이) / `plain` (일반 문서) |
| **본문 분량** | `short` / `medium` / `long` / `very_long` — Gemini에 분량 지시 추가 |
| **이미지 생성** | 체크 시 섹션별 삽화 이미지 자동 생성 |
| **이미지 수** | 0~4장 |

### 2단계: 검토

생성 후 화면 아래에 결과가 표시된다:

- **미리보기 탭** — 렌더링된 마크다운 확인
- **마크다운 탭** — 원문 편집 가능 `<textarea>`
- **이미지 프롬프트 패널** — 각 장의 영문 프롬프트를 직접 편집 가능

### 3단계: 재생성 (Regen Bar)

검토 후 부분 재생성이 필요하면 **재생성 바**를 활용:

| 버튼 | 동작 |
|------|------|
| 🔄 **전체** | 주제·설정 동일, 전체 새로 생성 |
| 📝 **텍스트만** | 현재 이미지 프롬프트를 유지한 채 본문만 재생성 |
| 🖼 **이미지만** | 편집한 이미지 프롬프트로 이미지만 재생성 (본문 유지) |
| **톤 선택** | `격식체` / `구어체` / `학술체` / `쉽게 설명` |
| ✏️ **이 톤으로** | 선택한 톤을 프롬프트에 추가해 전체 재생성 |

> 이미지만 재생성할 때는 **이미지 프롬프트 패널**에서 프롬프트를 수정한 뒤 🖼를 누른다.

### 4단계: 저장

- **카테고리 폴더** 선택 (`software-dev`, `tech-review` 등 — 디스크의 `content/posts` 직속 하위 폴더 목록 자동 읽기)
- **파일명** 확인 (추천 파일명 자동 생성)
- **선택한 폴더에 저장** → `content/posts/<카테고리>/파일명.md` 로 저장

---

## 프롬프트 편집 (`/edit`)

`http://127.0.0.1:8765/edit` 에서:

| 항목 | 설명 | 플레이스홀더 |
|------|------|--------------|
| **blog** | Hugo 기술 블로그 시스템 지시 | (시스템 프롬프트, 없음) |
| **philosophy** | 철학 에세이 시스템 지시 | (시스템 프롬프트, 없음) |
| **plain** | 일반 문서 시스템 지시 | (시스템 프롬프트, 없음) |
| **document_user** | 주제를 Gemini에 전달하는 사용자 메시지 템플릿 | `{topic}` (필수) |
| **image_prompt_generator** | 영문 이미지 프롬프트 문장을 생성하는 Gemini용 프롬프트 | `{topic}`, `{excerpt}`, `{count}` (모두 필수) |

### 저장 위치
- `docforge-web/data/user_prompts.json`
- 파일이 없으면 `services/prompts.py` 와 `services/prompt_config.py` 의 코드 기본값 사용

### 버튼 동작
| 버튼 | 동작 |
|------|------|
| **저장** | 현재 폼 내용을 `data/user_prompts.json` 에 저장 |
| **기본값 불러오기 (미리보기만)** | 코드 내장 기본값을 폼에 채움 (저장은 하지 않음) |
| **저장 파일 삭제 · 전부 기본값** | `user_prompts.json` 삭제 후 기본값 복구 |

---

## 프롬프트 구조 (BLOG 템플릿)

`blog` 템플릿은 **모듈형 블록** 구조를 출력한다:

```
[BLOCK 1: HUGO FRONT MATTER]
  title, date, description, slug, categories, tags, series, draft

[BLOCK 2: INTRODUCTION]
  <!-- BLOCK: intro | REGENERATE: intro만 다시 쓰려면 이 블록만 선택 후 재생성 -->

[BLOCK 3: MAIN SECTIONS — 각 H2마다 독립 블록]
  ## 섹션 제목
  <!-- BLOCK: section-N -->
  본문 (표·코드·리스트)
  <!-- VISUAL-START: diagram-N -->
  <!-- PROMPT: {{IMAGE_PROMPT}} -->
  <!-- STYLE: infographic | technical-diagram | ... -->
  <!-- VISUAL-END: diagram-N -->

[BLOCK 4: SUMMARY]
  <!-- BLOCK: summary -->
  ## 마치며

[BLOCK 5: REGENERATION GUIDE]
  <!-- 🔄 REGENERATION GUIDE ... -->
```

### 카테고리 목록 (Front Matter)
`ai-agents` | `ai-automation` | `ai-ops` | `mcp` | `software-dev` | `tech-review` | `hardware-lab` | `prompt-engineering` | `engineering-life` | `learning-log` | `thinking` | `daily-log`

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/health` | 서버 상태 · API 키 설정 여부 · 모델 정보 |
| GET | `/api/content-target` | `posts_dir`, `writable`, `subfolders` (posts 직속 하위 폴더 목록) |
| POST | `/api/generate` | 문서 생성. Body: `topic`, `template`, `with_images`, `max_images`, `length`, `image_hints` |
| POST | `/api/publish-post` | 마크다운 저장. Body: `markdown`, `filename`, `slug_hint`, `subfolder` |
| GET | `/api/prompts` | 현재 프롬프트 + 플레이스홀더 안내 (편집 화면용) |
| POST | `/api/prompts` | 프롬프트 저장 (부분 업데이트) |
| GET | `/api/prompts/builtins` | 코드 내장 기본 프롬프트 (되돌리기 미리보기용) |
| POST | `/api/prompts/reset` | `user_prompts.json` 삭제 → 기본값 복구 |

### `/api/generate` 요청 Body

```json
{
  "topic": "주제 텍스트",
  "template": "blog",
  "with_images": true,
  "max_images": 2,
  "length": "medium",
  "image_hints": "이미지 추가 힌트 (선택)"
}
```

`length` 값: `short` | `medium` | `long` | `very_long`

### `/api/generate` 응답

```json
{
  "ok": true,
  "markdown": "---\ntitle: ...",
  "images": [{"index": 0, "prompt": "...", "model": "...", "mime": "image/png", "data_base64": "..."}],
  "image_prompts": ["prompt1", "prompt2"],
  "suggested_filename": "2026-03-24-topic-slug.md",
  "models": {...},
  "manifest": {"slug": "...", "elapsed_ms": 1234, "image_count": 2}
}
```

---

## 이미지 생성 모델 체인

`image_gen.py` 에 정의된 순서대로 시도, 실패 시 다음으로 폴백:

1. **Imagen 4** (Google 이미지 생성 모델)
2. **Gemini 이미지** (Gemini 멀티모달 폴백)

이미지 생성에 실패하면 해당 위치의 `<!-- VISUAL -->` 주석이 마크다운에서 제거된다 (깨진 이미지 방지).

---

## 연결이 안 될 때

1. 터미널에 `Uvicorn running on http://127.0.0.1:8765` 가 보이는지 확인한다.
2. 다른 프로그램이 8765 포트를 쓰면 `--port 8770` 등으로 바꾼다.
3. 프롬프트 편집 후 반영이 안 되면 서버를 재시작한다 (`Ctrl+C` → 다시 `.\run.ps1`).
4. 방화벽이 막으면 LAN 노출이 필요한 경우에만 `run-lan.ps1` 을 사용한다.

---

## 보안

- API 키(`GEMINI_API_KEY`)는 서버 사이드에서만 사용하며 브라우저로 전송되지 않는다.
- CORS는 로컬 개발 편의를 위해 `*` 허용 상태다. 외부에 노출할 경우 `app.py`의 `allow_origins`를 제한한다.
