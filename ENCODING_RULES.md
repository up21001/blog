# Encoding Rules

한글이 들어간 문서와 코드 파일을 수정할 때는 아래 규칙을 반드시 따른다.

## 기본 원칙

- 모든 텍스트 파일은 `UTF-8`로 읽고 저장한다.
- PowerShell 콘솔 출력만 보고 한글이 깨졌다고 판단하지 않는다.
- `Get-Content` 출력이 깨져 보여도, 실제 파일 손상 여부는 반드시 Python `utf-8` 읽기로 다시 확인한다.
- 한글 본문 수정과 경로 수정은 한 번에 하지 않는다. 각각 별도로 검증한다.

## 금지 사항

- 한글 파일 내용을 PowerShell 콘솔 표시만 보고 복구 판단하지 말 것
- 인코딩 확인 없이 `Set-Content` 결과만 믿고 덮어쓰지 말 것
- 한글 파일에 대해 광범위한 치환을 먼저 하지 말 것
- mojibake 여부를 확인하지 않은 상태에서 slug, 이미지 경로, 본문 텍스트를 동시에 수정하지 말 것

## 필수 점검 절차

1. 수정 전 원본 파일을 `python`으로 `utf-8` 읽기 확인
2. 필요하면 `unicode_escape` 또는 바이트 일부를 같이 확인
3. 수정 범위를 최소화
4. 수정 후 다시 `python`으로 `utf-8` 읽기 확인
5. 이미지/SVG 문서라면 본문 경로와 실제 `static/images/...` 경로를 함께 대조
6. Hugo 빌드 후 `public/.../index.html`의 최종 `src` 경로까지 확인

## 권장 명령

UTF-8 검증:

```powershell
@'
from pathlib import Path
p = Path(r'content/posts/example.md')
for i, line in enumerate(p.read_text(encoding='utf-8').splitlines()[:20], start=1):
    print(f'{i}: ' + line.encode('unicode_escape').decode())
'@ | python -
```

이미지 경로 점검:

```powershell
@'
from pathlib import Path
p = Path(r'content/posts/example.md')
for i, line in enumerate(p.read_text(encoding='utf-8').splitlines(), start=1):
    if '/images/posts/' in line:
        print(f'{i}: ' + line.encode('unicode_escape').decode())
'@ | python -
```

빌드 결과 점검:

```powershell
@'
from pathlib import Path
p = Path(r'public/posts/example/index.html')
for i, line in enumerate(p.read_text(encoding='utf-8').splitlines(), start=1):
    if 'src="/images/posts/' in line:
        print(f'{i}: ' + line.strip().encode('unicode_escape').decode())
'@ | python -
```

## 이번 프로젝트에서 특히 주의할 점

- 블로그 본문은 `content/posts/...`
- 자산은 `static/images/posts/<slug>/...`
- 최종 렌더 결과는 `public/posts/<slug>/index.html`
- 본문에 들어간 이미지 경로는 반드시 최종 `slug` 기준으로 맞춘다.

## 재발 방지 규칙

- 한글 파일을 수정할 때는 먼저 "콘솔 표시 문제인지, 파일 손상인지"를 분리해서 확인한다.
- 파일 손상 판정 전에는 내용 복구 작업을 하지 않는다.
- 경로 수정만 필요한 경우 본문 텍스트는 건드리지 않는다.
