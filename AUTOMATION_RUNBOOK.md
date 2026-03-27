# 블로그 자동화 운영 런북

> UTF-8 및 한글 파일 수정 규칙은 [ENCODING_RULES.md](/c:/My/Claude/Blog/blog/ENCODING_RULES.md)를 우선 참고합니다.

이 문서는 이 프로젝트에서 블로그 자동화를 안정적으로 반복 실행하기 위한 기준 문서입니다.
주요 목적은 "생성 -> 검토 -> 저장 -> 배포" 흐름에서 누락 없이 운영하는 것입니다.

## 1) 현재 자동화 구성 요약

- 콘텐츠 엔진: Hugo + Blowfish
- 생성 스크립트: `generate_post.py`
- 출력 경로: `content/posts/`
- 배포 경로: GitHub `main` push -> Cloudflare Pages 자동 빌드
- 보조 편집 경로: `static/admin/config.yml` 기반 CMS

## 2) 표준 실행 플로우 (CLI)

1. 주제 입력으로 포스트 생성
   - `python generate_post.py "주제"`
2. 생성 결과 미리보기 확인
3. 저장 여부 확인 (`Y/n`)
4. 저장 후 Front Matter 점검
5. 필요 시 `draft: false` 전환
6. Git 반영 및 push
7. Cloudflare Pages 배포 상태 확인

## 3) Front Matter 최소 체크리스트

- `title` 존재
- `date`, `lastmod` 존재
- `description` 존재 (검색 요약 문구)
- `slug` 존재 (영문 하이픈)
- `categories` 존재 (프로젝트 분류 체계 준수)
- `tags` 5개 이상 권장
- `draft` 상태 확인 (`false`면 공개 배포 대상)

## 4) 프로젝트 분류 기준

현재 사이트 메뉴/카테고리 기준:

- `hardware-lab`
- `software-dev`
- `ai-automation`
- `tech-review`
- `engineering-life`
- `learning-log`
- `daily-log`
- `thinking`

포스트 생성 시 위 분류와 일치하도록 유지합니다.

## 5) 배포 전 점검

- 내부 링크가 상대/절대 경로 기준으로 깨지지 않는지 확인
- 이미지 경로가 `/images/...` 또는 프로젝트 규칙에 맞는지 확인
- 코드 블록 언어 태그 지정 여부 확인
- 오탈자 및 문단 분리 가독성 확인
- 공개 문서에서 민감정보(API 키, 토큰) 미포함 확인

## 6) 운영 원칙

- 자동 생성 결과는 초안으로 보고 사람이 최종 검수합니다.
- `draft: true` 상태로 저장 후 검수 완료 시 `false`로 전환합니다.
- 생성 실패 시 즉시 재시도하지 말고 원인(API 키, 네트워크, 토큰 길이)을 먼저 확인합니다.
- 장문 생성 시 토큰 제한으로 잘릴 수 있으므로 본문 길이와 결론 유무를 확인합니다.

## 7) 자주 발생하는 이슈

- API 키 누락: `GEMINI_API_KEY` 확인
- 파일명/slug 품질 저하: Front Matter `slug` 직접 보정
- 본문 길이 부족: 주제 입력을 더 구체화해 재생성
- 배포 미반영: Git push 여부와 Pages 빌드 로그 확인

## 8) 향후 자동화 확장 TODO

- 비대화형 플래그 추가 (`--yes`, `--no-push`)
- 생성 후 품질검사 자동화 (Front Matter lint, 링크 검사)
- 카테고리/태그 자동 정규화
- 발행 승인 워크플로우 (초안 -> 리뷰 -> 공개)
- 배포 성공 여부 자동 알림 (Webhook/메신저)

---

최종 원칙: 자동화는 글쓰기 부담을 줄이되, 품질 책임은 문서 검수 단계에서 확보합니다.
