# -*- coding: utf-8 -*-
"""Expand posts whose markdown body has fewer than 500 non-space chars to 1000+.
Adds/updates hero SVG, adds 참고문헌. Run from repo root: python scripts/expand_short_posts.py"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "content" / "posts"
STATIC_IMG = ROOT / "static" / "images"
MIN_BEFORE = 500
MIN_AFTER = 1000

LAB_SVG_LABELS: dict[str, tuple[str, str]] = {
    "team-ai-adoption": ("팀 AI 확산 운영 실험", "활성화 · 자동화 · 만족도"),
    "mcp-policy-audit": ("MCP 정책 감사 실험실", "준수율 · 위반 탐지 · 오탐"),
    "ai-cost-optimization": ("AI 비용 최적화 실험", "단위비용 · 품질보존 · 실험속도"),
    "agent-recovery-runbook": ("에이전트 복구 런북 실험", "MTTD · MTTR · 재발률"),
    "prompt-release-quality": ("프롬프트 릴리즈 품질 실험실", "회귀율 · 승인시간 · 게이트"),
    "ai-response-reliability": ("AI 응답 신뢰성 실험실", "정확도 · 일관성 · 지연"),
}

LAB_REFS: dict[str, list[tuple[str, str]]] = {
    "team-ai-adoption": [
        ("Google SRE - Monitoring", "https://sre.google/sre-book/monitoring-distributed-systems/"),
        ("NIST AI RMF", "https://www.nist.gov/itl/ai-risk-management-framework"),
        ("OWASP LLM Top 10", "https://owasp.org/www-project-top-10-for-large-language-model-applications/"),
    ],
    "mcp-policy-audit": [
        ("Model Context Protocol", "https://modelcontextprotocol.io/"),
        ("OWASP API Security Top 10", "https://owasp.org/www-project-api-security/"),
        ("NIST SP 800-53 Rev.5", "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final"),
    ],
    "ai-cost-optimization": [
        ("AWS Well-Architected Cost Optimization", "https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html"),
        ("Prometheus - Recording rules", "https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/"),
        ("OpenAI - Rate limits", "https://platform.openai.com/docs/guides/rate-limits"),
    ],
    "agent-recovery-runbook": [
        ("Google SRE - Incident Response", "https://sre.google/sre-book/managing-load/"),
        ("Google SRE Workbook - Postmortem", "https://sre.google/workbook/postmortem-culture/"),
        ("ITIL 4 - Incident management (Axelos)", "https://www.axelos.com/best-practice-solutions/itil"),
    ],
    "prompt-release-quality": [
        ("Semantic Versioning", "https://semver.org/"),
        ("Google SRE - Release Engineering", "https://sre.google/sre-book/release-engineering/"),
        ("OWASP LLM Top 10", "https://owasp.org/www-project-top-10-for-large-language-model-applications/"),
    ],
    "ai-response-reliability": [
        ("NIST AI RMF", "https://www.nist.gov/itl/ai-risk-management-framework"),
        ("OpenAI - Evals overview", "https://platform.openai.com/docs/guides/evals"),
        ("ISO/IEC 23894 - AI risk management", "https://www.iso.org/standard/77304.html"),
    ],
}

GENERIC_REFS = [
    ("Google Technical Writing", "https://developers.google.com/tech-writing"),
    ("Diátaxis documentation framework", "https://diataxis.fr/"),
    ("OWASP Secure Coding Practices", "https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/"),
]

NOTE_VARIANTS = [
    "이번 차수에서는 변경을 최소 단위로 쪼개고, 한 번에 하나의 가설만 검증합니다. 동시에 여러 요인을 바꾸면 회고에서 원인을 특정하기 어렵습니다.",
    "운영 지표는 ‘평균’보다 ‘하위 분위’를 함께 봅니다. P95·P99가 나빠지면 사용자 체감 품질이 먼저 무너지는 경우가 많습니다.",
    "실험 실패를 ‘데이터’로 남기는 것이 다음 스프린트의 자산입니다. 실패 코드·재현 절차·롤백 소요 시간을 기록하세요.",
    "게이트 조건은 사전 합의된 문장으로 고정합니다. 릴리즈 직전에 기준을 바꾸면 팀 신뢰와 속도가 동시에 손상됩니다.",
]


def split_front_matter(raw: str) -> tuple[dict[str, str], str] | None:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None
    fm: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        fm[k.strip()] = v.strip()
    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return fm, body


def fm_to_lines(fm: dict[str, str]) -> list[str]:
    order = ["title", "date", "lastmod", "description", "slug", "categories", "tags", "draft"]
    lines = ["---"]
    seen: set[str] = set()
    for k in order:
        if k in fm:
            lines.append(f"{k}: {fm[k]}")
            seen.add(k)
    for k, v in sorted(fm.items()):
        if k not in seen:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return lines


def body_nonspace_len(body: str) -> int:
    return sum(1 for c in body if not c.isspace())


def lab_prefix_from_slug(slug: str) -> tuple[str, int] | None:
    m = re.match(
        r"^(team-ai-adoption|mcp-policy-audit|ai-cost-optimization|agent-recovery-runbook|prompt-release-quality|ai-response-reliability)-lab-(\d+)-2026$",
        slug,
    )
    if not m:
        return None
    return m.group(1), int(m.group(2))


def load_lab_template(prefix: str) -> str:
    path = ROOT / "content" / "posts" / f"2026-03-31-{prefix}-lab-80-2026.md"
    return path.read_text(encoding="utf-8")


def expand_lab_post(path: Path, slug: str, prefix: str, n: int) -> str:
    template_raw = load_lab_template(prefix)
    sp = split_front_matter(template_raw)
    if not sp:
        raise RuntimeError(f"bad template {prefix}")
    fm_t, body_t = sp
    sp_o = split_front_matter(path.read_text(encoding="utf-8"))
    fm_o = sp_o[0] if sp_o else {}

    # Replace 80 -> n in template full text for title/description/body
    def repl80(s: str) -> str:
        s = s.replace("80차", f"{n}차")
        s = s.replace("lab-80-2026", f"lab-{n}-2026")
        return s

    fm_new = {k: repl80(v) for k, v in fm_t.items()}
    if "date" in fm_o:
        fm_new["date"] = fm_o["date"]
    if "lastmod" in fm_o:
        fm_new["lastmod"] = fm_o["lastmod"]
    fm_new["slug"] = f'"{slug}"'

    body = repl80(body_t)
    if "## 참고문헌" not in body:
        refs = LAB_REFS.get(prefix, GENERIC_REFS)
        body += "\n\n## 참고문헌\n\n"
        body += "\n".join(f"- [{t}]({u})" for t, u in refs)
    note = NOTE_VARIANTS[n % len(NOTE_VARIANTS)]
    if "## 이번 차수 실전 포인트" not in body:
        body += f"\n\n## 이번 차수 실전 포인트\n\n{note}\n"
    lines = fm_to_lines(fm_new)
    return "\n".join(lines) + "\n\n" + body + "\n"


def svg_for_lab(prefix: str, n: int, slug: str) -> str:
    title, sub = LAB_SVG_LABELS[prefix]
    tid = "g_" + re.sub(r"[^a-zA-Z0-9_]", "_", slug)
    mid = "m_" + re.sub(r"[^a-zA-Z0-9_]", "_", slug)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="{tid}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f172a"/><stop offset="100%" stop-color="#1e3a5f"/>
    </linearGradient>
    <marker id="{mid}" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect width="1200" height="630" fill="url(#{tid})"/>
  <rect x="40" y="40" width="1120" height="550" rx="20" fill="#111827" stroke="#334155"/>
  <text x="72" y="110" fill="#e2e8f0" font-size="36" font-family="Segoe UI, Malgun Gothic, sans-serif" font-weight="700">{title} {n}차</text>
  <text x="72" y="168" fill="#93c5fd" font-size="22" font-family="Segoe UI, Malgun Gothic, sans-serif">{sub}</text>
  <line x1="72" y1="200" x2="1128" y2="200" stroke="#334155" stroke-width="2"/>
  <rect x="72" y="240" width="200" height="72" rx="12" fill="#1e3a8a" stroke="#60a5fa"/><text x="112" y="284" fill="#dbeafe" font-size="16" font-family="Segoe UI, sans-serif">Baseline</text>
  <rect x="300" y="240" width="200" height="72" rx="12" fill="#1e3a8a" stroke="#60a5fa"/><text x="352" y="284" fill="#dbeafe" font-size="16" font-family="Segoe UI, sans-serif">Experiment</text>
  <rect x="528" y="240" width="200" height="72" rx="12" fill="#1e3a8a" stroke="#60a5fa"/><text x="580" y="284" fill="#dbeafe" font-size="16" font-family="Segoe UI, sans-serif">Gate</text>
  <rect x="756" y="240" width="200" height="72" rx="12" fill="#14532d" stroke="#22c55e"/><text x="810" y="284" fill="#dcfce7" font-size="16" font-family="Segoe UI, sans-serif">Ship</text>
  <path d="M272 276 L300 276" stroke="#94a3b8" stroke-width="3" marker-end="url(#{mid})"/>
  <path d="M500 276 L528 276" stroke="#94a3b8" stroke-width="3" marker-end="url(#{mid})"/>
  <path d="M728 276 L756 276" stroke="#94a3b8" stroke-width="3" marker-end="url(#{mid})"/>
  <text x="72" y="380" fill="#cbd5e1" font-size="18" font-family="Segoe UI, Malgun Gothic, sans-serif">실험 → 게이트 → 배포 → 기록 루프</text>
  <text x="72" y="430" fill="#64748b" font-size="15" font-family="Segoe UI, Malgun Gothic, sans-serif">차수별 지표는 본문 표준과 동일하게 추적</text>
</svg>
"""


def svg_generic(title_short: str, slug: str) -> str:
    safe = (title_short[:42] + "…") if len(title_short) > 42 else title_short
    tid = "g" + re.sub(r"\W+", "_", slug)[:40]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="{tid}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f172a"/><stop offset="100%" stop-color="#312e81"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#{tid})"/>
  <rect x="48" y="48" width="1104" height="534" rx="18" fill="#111827" stroke="#6366f1" stroke-opacity="0.45"/>
  <text x="88" y="120" fill="#e0e7ff" font-size="32" font-family="Segoe UI, Malgun Gothic, sans-serif" font-weight="700">{safe}</text>
  <text x="88" y="172" fill="#a5b4fc" font-size="20" font-family="Segoe UI, Malgun Gothic, sans-serif">운영 원칙 · 체크리스트 · 참고문헌</text>
  <rect x="88" y="220" width="1000" height="100" rx="12" fill="#1e1b4b" stroke="#818cf8"/>
  <text x="112" y="268" fill="#c7d2fe" font-size="17" font-family="Segoe UI, Malgun Gothic, sans-serif">목표 정의 → 실행 → 검증 → 회고</text>
  <text x="112" y="300" fill="#a5b4fc" font-size="15" font-family="Segoe UI, Malgun Gothic, sans-serif">문서는 팀의 다음 행동으로 연결될 때만 가치가 있습니다.</text>
  <rect x="88" y="360" width="320" height="180" rx="12" fill="#0c1222" stroke="#334155"/>
  <text x="112" y="404" fill="#f1f5f9" font-size="16" font-family="Segoe UI, Malgun Gothic, sans-serif" font-weight="600">핵심 질문</text>
  <text x="112" y="440" fill="#cbd5e1" font-size="14" font-family="Segoe UI, Malgun Gothic, sans-serif">· 기준선이 숫자인가</text>
  <text x="112" y="468" fill="#cbd5e1" font-size="14" font-family="Segoe UI, Malgun Gothic, sans-serif">· 롤백이 10분 내 가능한가</text>
  <text x="112" y="496" fill="#cbd5e1" font-size="14" font-family="Segoe UI, Malgun Gothic, sans-serif">· 회고가 백로그로 이어지는가</text>
</svg>
"""


def strip_yaml_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1].replace('\\"', '"')
    return s


def expand_generic(path: Path, fm: dict[str, str], body: str) -> str:
    title = strip_yaml_quotes(fm.get("title", path.stem))
    slug = strip_yaml_quotes(fm.get("slug", path.stem))
    desc = strip_yaml_quotes(fm.get("description", title + " 실무 가이드입니다."))
    # Keep short description if good
    if len(desc) < 40:
        desc = f"{title}에 대한 실행 기준, 절차, 체크리스트를 한 곳에 모은 실무 가이드입니다."

    img_name = first_image_slug(body) or f"{slug}.svg"
    img_line = f"![{title}](/images/{img_name})"

    # 기존 본문이 짧아도 서사·실험 기록이 있으면 덮어쓰지 않고 보강만 한다
    rest = body
    m_img = re.match(r"^!\[[^\]]*\]\([^)]+\)\s*\n*", rest)
    if m_img:
        rest = rest[m_img.end() :]
    if sum(1 for c in rest if not c.isspace()) >= 200 and "## 참고문헌" not in body:
        supplement = """

## 확장: 운영에 옮기기

이 글의 메시지를 팀·개인 루틴에 붙이려면, 한 가지 **측정 가능한 행동**만 다음 주에 시험해 보세요. 성공 정의를 이진(했다/안 했다)으로 두면 회고가 쉬워집니다.

## 참고문헌

"""
        supplement += "\n".join(f"- [{t}]({u})" for t, u in GENERIC_REFS)
        lines = fm_to_lines(fm)
        return "\n".join(lines) + "\n\n" + body.rstrip() + supplement + "\n"

    new_body = f"""{img_line}

## 왜 이 문서가 필요한가

이 글의 초점은 **{title}**과 관련해 현장에서 반복되는 결정을 줄이는 것입니다. 같은 논의가 매 스프린트마다 다시 열리면 속도와 품질이 동시에 떨어집니다. 지표 정의, 실행 순서, 롤백 기준, 회고 연결을 최소한의 공통 언어로 고정해 두기 위한 운영 문서입니다.

## 핵심 원칙

| 원칙 | 실무 적용 |
|---|---|
| 기준선 우선 | 숫자 없는 개선 논의 금지 |
| 단일 변경 | 한 번에 변수는 하나만 |
| 게이트 명시 | 통과/실패 조건을 문장으로 |
| 회고 연결 | 결론은 백로그 항목으로 |

## 실행 절차

1. **현재 상태 수치화**: 최근 2주 지표로 기준선을 남깁니다.  
2. **가설과 범위**: 이번 주에 바꿀 행동과 기대 효과를 한 문단으로 적습니다.  
3. **실행 및 관측**: 변경 후 48~72시간은 회귀 신호를 집중 관측합니다.  
4. **판정**: 게이트를 통과하면 표준에 반영, 실패하면 롤백하고 원인 코드를 남깁니다.  
5. **문서 갱신**: 다음 사람이 같은 실수를 하지 않도록 본 문서를 업데이트합니다.

## 체크리스트

- 이 문서만 읽고도 신규 담당자가 같은 절차를 재현할 수 있는가  
- 실패 시 “누가·언제·어떻게” 롤백하는지 한 화면에 있는가  
- 성공 정의가 수치 또는 명확한 완료 조건으로 적혀 있는가  
- 지난 회고에서 나온 액션이 실제로 반영되었는가  

```mermaid
flowchart LR
    A[기준선] --> B[실행]
    B --> C[관측]
    C --> D{{게이트}}
    D -->|통과| E[표준 반영]
    D -->|실패| F[롤백+원인]
    E --> G[회고/백로그]
    F --> G
```

### 실전 시나리오

{title}과 관련해 흔한 패턴은 “문서는 있는데 최신 운영과 어긋난다”는 것입니다. 예를 들어 임계값만 바꾸고 문서의 기준은 그대로 두면, 장애 때마다 논쟁이 재발합니다. 반대로 변경 사항을 즉시 문서에 반영하고 버전 메모를 남기면, 팀의 판단 속도가 안정됩니다.

## 마무리

운영 문서의 품질은 분량이 아니라 **재사용성**으로 측정됩니다. 이 글을 팀 주간 리뷰에 붙여 두고, 매주 한 항목씩만 개선해도 분기마다 운영 성숙도가 달라집니다.

## 참고문헌

"""
    new_body += "\n".join(f"- [{t}]({u})" for t, u in GENERIC_REFS)

    fm_new = dict(fm)
    fm_new["description"] = f'"{desc}"'
    if "draft" not in fm_new:
        fm_new["draft"] = "false"

    lines = fm_to_lines(fm_new)
    return "\n".join(lines) + "\n\n" + new_body + "\n"


def first_image_slug(body: str) -> str | None:
    m = re.search(r"!\[[^\]]*\]\(/images/([^)]+\.svg)\)", body)
    return m.group(1) if m else None


def main() -> None:
    STATIC_IMG.mkdir(parents=True, exist_ok=True)
    updated = 0
    for path in sorted(POSTS.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        sp = split_front_matter(raw)
        if not sp:
            continue
        fm, body = sp
        if body_nonspace_len(body) >= MIN_BEFORE:
            continue
        slug = strip_yaml_quotes(fm.get("slug", path.stem))
        lab = lab_prefix_from_slug(slug)

        if lab:
            prefix, n = lab
            text = expand_lab_post(path, slug, prefix, n)
            svg_name = f"{slug}.svg"
            (STATIC_IMG / svg_name).write_text(svg_for_lab(prefix, n, slug), encoding="utf-8")
        else:
            text = expand_generic(path, fm, body)
            img_name = first_image_slug(text) or f"{slug}.svg"
            svg_path = STATIC_IMG / img_name
            title = strip_yaml_quotes(fm.get("title", path.stem))
            if not svg_path.exists() or svg_path.stat().st_size < 400:
                svg_path.write_text(svg_generic(title, slug), encoding="utf-8")

        path.write_text(text, encoding="utf-8")
        # verify
        _, b2 = split_front_matter(text)
        assert body_nonspace_len(b2) >= MIN_AFTER, (path, body_nonspace_len(b2))
        updated += 1
    print(f"Updated {updated} posts (target body length >= {MIN_AFTER}).")


if __name__ == "__main__":
    main()
