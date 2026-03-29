# -*- coding: utf-8 -*-
"""Regenerate 2026-03-31 batch posts with UTF-8 Korean + full article bodies."""
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "content" / "posts"
IMG = ROOT / "static" / "images"

MERMAID_FLOW = """```mermaid
flowchart TD
    A[기준선 측정] --> B[설계·범위 확정]
    B --> C[파일럿 실행]
    C --> D[품질 게이트]
    D -->|통과| E[운영 반영]
    D -->|미달| F[원인 분류·재시도]
    E --> G[KPI 기록·회고]
    F --> C
    G --> H[다음 스프린트 개선]
```"""


def fm(title: str, dt: datetime, desc: str, slug: str, category: str, tags: list[str]) -> str:
    ts = dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")
    tag_line = ", ".join(f'"{t}"' for t in tags)
    return f"""---
title: "{title}"
date: {ts}
lastmod: {ts}
description: "{desc}"
slug: "{slug}"
categories: ["{category}"]
tags: [{tag_line}]
draft: false
---

"""


def svg_cover(slug: str, headline: str, sub: str) -> None:
    safe_h = headline.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_s = sub.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    path = IMG / f"{slug}.svg"
    path.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#0b1220"/><stop offset="100%" stop-color="#1e3a5f"/>
  </linearGradient></defs>
  <rect width="1200" height="630" fill="url(#g)"/>
  <rect x="48" y="48" width="1104" height="534" rx="20" fill="#111827" stroke="#334155"/>
  <text x="88" y="130" fill="#e5e7eb" font-size="36" font-family="Segoe UI, Arial" font-weight="700">{safe_h}</text>
  <text x="88" y="188" fill="#93c5fd" font-size="22" font-family="Segoe UI, Arial">{safe_s}</text>
  <line x1="88" y1="220" x2="1112" y2="220" stroke="#334155" stroke-width="2"/>
  <text x="88" y="280" fill="#cbd5e1" font-size="20" font-family="Segoe UI, Arial">표 · 체크리스트 · Mermaid · 실무 KPI</text>
</svg>
""",
        encoding="utf-8",
    )


def long_article(
    hook: str,
    table1: str,
    table2: str,
    steps: str,
    checklist: str,
    closing: str,
) -> str:
    return f"""## 왜 이 문서가 필요한가

{hook}

## 핵심 개념 정리

{table1}

## 운영 지표 예시

{table2}

## 실행 절차

{steps}

{MERMAID_FLOW}

## 운영 체크리스트

{checklist}

## 마무리

{closing}
"""


T1 = """| 구분 | 정의 | 실무에서의 의미 |
|---|---|---|
| 범위 | 한 문장으로 끝나는 납품 경계 | 변경 요청 폭주 방지 |
| 품질 하한 | 자동 통과 최소 기준 | 재작업 비용 상한 |
| 변동비 | 요청당 모델·툴·인건비 | 가격·패키지 설계의 기준 |
| 로그 | 실패 유형·재시도 이유 | 다음 스프린트 백로그 원천 |"""

T2 = """| 지표 | 목표 예시 | 측정 주기 |
|---|---|---|
| 1회 통과율 | 75% 이상 | 주간 |
| P95 처리시간 | 사전 합의값 이내 | 주간 |
| 재작업률 | 15% 미만 | 주간 |
| 고객당 공헌이익 | 전월 대비 개선 | 월간 |"""

STEPS = """1. **기준선**: 최근 2주 운영 데이터로 현재 수치를 고정합니다.  
2. **범위 고정**: 이번 스프린트에 넣을 변경은 한 가지 원칙으로 제한합니다.  
3. **게이트**: 품질 하한 미달 시 자동 재시도 후에도 실패하면 수동 검토로 전환합니다.  
4. **기록**: 실패 로그에 원인 코드(입력/프롬프트/도구/정책)를 붙입니다.  
5. **회고**: KPI 3개만 골라 다음 주 액션으로 연결합니다."""

CHK = """- 범위·산출물·승인자가 문서 한 장에 있는가  
- 품질 하한과 롤백 경로가 합의됐는가  
- 비용(토큰·툴·인력)이 주간으로 가시화되는가  
- 고객 보고에 숫자(전/후)가 포함되는가"""

CLOSE = """핵심은 도구가 아니라 **측정 가능한 운영 루프**입니다. 같은 템플릿을 반복 적용하면 팀 확장 시에도 품질이 무너지지 않습니다."""


def write_post(filename: str, title: str, slug: str, category: str, tags: list[str], desc: str, body: str, dt: datetime):
    svg_cover(slug, title[:48], "실무 운영 가이드 2026")
    (POSTS / filename).write_text(fm(title, dt, desc, slug, category, tags) + f"![{title}](/images/{slug}.svg)\n\n" + body, encoding="utf-8")


def main():
    POSTS.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    base = datetime(2026, 3, 31, 9, 0, 0)
    n = 0

    # ---- Series indexes ----
    series_specs = [
        (
            "2026-03-31-ai-automation-revenue-operations-series-2026.md",
            "AI 자동화 수익화 운영실전 시리즈 2026: 인덱스",
            "ai-automation-revenue-operations-series-2026",
            [
                ("1편", "AI 자동화 구축형 상품화 설계", "ai-automation-productization-blueprint-2026"),
                ("2편", "고객 온보딩 자동화", "ai-client-onboarding-automation-2026"),
                ("3편", "프롬프트 품질 게이트", "prompt-quality-gate-operations-2026"),
                ("4편", "HITL 운영 매뉴얼", "hitl-operations-manual-2026"),
                ("5편", "원가 구조 최적화", "ai-ops-cost-structure-optimization-2026"),
                ("6편", "성과 대시보드 설계", "ai-ops-kpi-dashboard-design-2026"),
                ("7편", "재구매 리포팅 자동화", "client-retention-reporting-automation-2026"),
                ("8편", "확장 전략", "ai-automation-scale-strategy-2026"),
            ],
            "AI 자동화를 매출과 운영 KPI로 연결하는 8부작 시리즈 목차입니다.",
        ),
        (
            "2026-03-31-hardware-lab-automation-ops-series-2026.md",
            "Hardware-Lab 운영 자동화 시리즈 2026: 인덱스",
            "hardware-lab-automation-ops-series-2026",
            [
                ("1편", "홈랩 장애 알림 자동화", "homelab-alert-automation-2026"),
                ("2편", "백업·복구 리허설 자동화", "homelab-backup-restore-drill-automation-2026"),
                ("3편", "UPS 이벤트 런북", "homelab-ups-event-runbook-2026"),
                ("4편", "세그먼트별 모니터링", "homelab-segment-monitoring-2026"),
                ("5편", "전력비 최적화 스케줄링", "homelab-power-cost-scheduling-2026"),
                ("6편", "월간 운영 리포트", "homelab-monthly-ops-report-automation-2026"),
            ],
            "홈랩 운영을 알림·백업·전력·리포트까지 자동화하는 6부작 인덱스입니다.",
        ),
        (
            "2026-03-31-solo-team-ai-income-roadmap-series-2026.md",
            "1인·소팀 AI 수익화 로드맵 시리즈 2026: 인덱스",
            "solo-team-ai-income-roadmap-series-2026",
            [
                ("1편", "30일 첫 매출 플랜", "ai-automation-first-revenue-30days-2026"),
                ("2편", "니치 선정 프레임워크", "niche-selection-framework-ai-2026"),
                ("3편", "제안서 자동화", "proposal-automation-template-2026"),
                ("4편", "납품 QA 체계", "delivery-qa-framework-ai-services-2026"),
                ("5편", "월 1000만원 모델", "monthly-10m-krw-ai-ops-model-2026"),
            ],
            "1인·소팀이 AI 자동화로 수익을 만드는 실행 로드맵 5부작입니다.",
        ),
        (
            "2026-03-31-seo-content-automation-engine-series-2026.md",
            "SEO 콘텐츠 자동화 엔진 시리즈 2026: 인덱스",
            "seo-content-automation-engine-series-2026",
            [
                ("1편", "키워드 클러스터링", "seo-keyword-clustering-topic-map-2026"),
                ("2편", "글 구조 템플릿 자동 생성", "content-structure-template-automation-2026"),
                ("3편", "SVG 파이프라인", "svg-pipeline-automation-2026"),
                ("4편", "내부 링크 자동 반영", "internal-link-series-index-automation-2026"),
                ("5편", "리프레시 캘린더", "content-refresh-calendar-operations-2026"),
                ("6편", "성과 분석 루프", "seo-content-performance-loop-2026"),
            ],
            "SEO와 콘텐츠 생산을 엔진처럼 굴리는 6부작 시리즈 인덱스입니다.",
        ),
    ]

    for i, (fn, title, slug, rows, desc) in enumerate(series_specs):
        dt = base + timedelta(minutes=i * 5)
        table = "\n".join(f"| {a} | {b} | [바로가기](/posts/{s}/) |" for a, b, s in rows)
        body = f"""## 시리즈가 다루는 질문

많은 팀이 "도구는 샀는데 왜 매출/안정성이 안 오르지?"에 막힙니다. 이 시리즈는 **운영 체계**를 한 편씩 쌓아 올리는 것을 목표로 합니다.

## 연재 목록

| 회차 | 주제 | 링크 |
|---|---|---|
{table}

## 이렇게 읽으면 좋습니다

- 주 1편 속도로 적용하고, 매주 KPI 3개만 고릅니다.  
- 각 편의 체크리스트를 그대로 팀 회의 아젠다로 쓸 수 있습니다.  
- 실패 로그를 남기지 않으면 다음 편의 효과가 반감됩니다.

## 운영 원칙 요약

| 원칙 | 설명 |
|---|---|
| 작게 자주 | 한 스프린트에 변경점 1개 |
| 게이트 우선 | 품질 하한 미달 시 배포 중단 |
| 숫자로 말하기 | 전/후 지표를 고객·내부 모두에게 공유 |

{MERMAID_FLOW}
"""
        write_post(fn, title, slug, "series", ["시리즈", "운영", "자동화"], desc, body, dt)
        n += 1

    # ---- Topic-specific long articles (slug -> custom hook + optional table override) ----
    topics: dict[str, tuple[str, str, str, list[str], str, str]] = {}

    def reg(
        slug: str,
        title: str,
        fn: str,
        tags: list[str],
        cat: str,
        hook: str,
        extra: str = "",
    ):
        topics[slug] = (title, fn, cat, tags, hook, extra)

    reg(
        "ai-automation-productization-blueprint-2026",
        "AI 자동화 구축형 상품화 설계 2026: 패키지·범위·가격을 한 번에 정리하는 법",
        "2026-03-31-ai-automation-productization-blueprint-2026.md",
        ["AI 자동화", "상품화", "가격"],
        "ai-automation",
        "프로젝트형 자동화는 범위가 흔들리면 마진이 즉시 무너집니다. 상품화는 견적서가 아니라 운영 규칙의 묶음입니다.",
    )
    reg(
        "ai-client-onboarding-automation-2026",
        "고객 온보딩 자동화 2026: 브리프·권한·데이터를 첫 주에 고정하는 법",
        "2026-04-01-ai-client-onboarding-automation-2026.md",
        ["온보딩", "AI 자동화", "고객성공"],
        "ai-automation",
        "온보딩이 느리면 자동화 성과가 '데모'에서 끝납니다. 입력 품질을 초반에 고정해야 운영 단계에서 이익이 남습니다.",
    )
    reg(
        "prompt-quality-gate-operations-2026",
        "프롬프트 품질 게이트 운영 2026: 실패 유형 분류와 재시도 정책",
        "2026-04-01-prompt-quality-gate-operations-2026.md",
        ["프롬프트", "품질", "운영"],
        "ai-automation",
        "프롬프트 품질은 감이 아니라 게이트입니다. 실패 유형을 코드화하면 재시도 비용이 떨어집니다.",
    )
    reg(
        "hitl-operations-manual-2026",
        "HITL 운영 매뉴얼 2026: 사람 검수 기준·SLA·책임 분리",
        "2026-04-01-hitl-operations-manual-2026.md",
        ["HITL", "품질", "운영"],
        "ai-automation",
        "HITL은 비용이 아니라 리스크 관리 장치입니다. 기준이 없으면 자동화는 '불만 처리 민원 창구'가 됩니다.",
    )
    reg(
        "ai-ops-cost-structure-optimization-2026",
        "AI 운영 원가 구조 최적화 2026: 토큰·툴·인건비 분해",
        "2026-04-01-ai-ops-cost-structure-optimization-2026.md",
        ["원가", "토큰", "운영"],
        "ai-automation",
        "매출이 나와도 원가가 안 보이면 확장할수록 적자가 납니다. 변동비를 고객·요청·기능 단위로 쪼개야 합니다.",
    )
    reg(
        "ai-ops-kpi-dashboard-design-2026",
        "AI 운영 KPI 대시보드 설계 2026: 알림 기준과 주간 리뷰",
        "2026-04-01-ai-ops-kpi-dashboard-design-2026.md",
        ["KPI", "대시보드", "운영"],
        "ai-automation",
        "지표가 많으면 아무도 안 봅니다. 운영 대시보드는 '행동을 유발하는 3개'만 살아남게 설계합니다.",
    )
    reg(
        "client-retention-reporting-automation-2026",
        "재구매를 만드는 고객 리포팅 자동화 2026",
        "2026-04-01-client-retention-reporting-automation-2026.md",
        ["리포팅", "재구매", "자동화"],
        "ai-automation",
        "자동화의 가치는 내부 효율이 아니라 고객이 체감하는 결과입니다. 주간 리포트는 '다음 계약'의 설득 도구입니다.",
    )
    reg(
        "ai-automation-scale-strategy-2026",
        "AI 자동화 확장 전략 2026: 템플릿·운영대행·교육의 조합",
        "2026-04-01-ai-automation-scale-strategy-2026.md",
        ["확장", "MRR", "전략"],
        "ai-automation",
        "확장은 인원을 늘리는 게 아니라 반복 매출 구조를 쌓는 것입니다. 템플릿·운영·교육의 비율을 조절합니다.",
    )

    reg(
        "homelab-alert-automation-2026",
        "홈랩 장애 알림 자동화 설계 2026: 디스크·온도·전력 이벤트 운영",
        "2026-03-31-homelab-alert-automation-2026.md",
        ["홈랩", "모니터링", "알림"],
        "hardware-lab",
        "알림이 많으면 무시하게 되고, 적으면 장애를 놓칩니다. 신호를 계층화하고 피로도를 설계해야 합니다.",
    )
    reg(
        "homelab-backup-restore-drill-automation-2026",
        "홈랩 백업·복구 리허설 자동화 2026: 검증 작업을 루틴으로 고정",
        "2026-04-01-homelab-backup-restore-drill-automation-2026.md",
        ["백업", "복구", "홈랩"],
        "hardware-lab",
        "백업 성공 메시지는 장애 날 쓸모없습니다. 리허설을 자동 체크리스트로 고정해야 RTO가 현실이 됩니다.",
    )
    reg(
        "homelab-ups-event-runbook-2026",
        "홈랩 UPS 이벤트 런북 2026: 정전·배터리·그레이스풀 셧다운",
        "2026-04-01-homelab-ups-event-runbook-2026.md",
        ["UPS", "전력", "홈랩"],
        "hardware-lab",
        "UPS는 하드웨어가 아니라 가용성 정책입니다. 이벤트별 대응 순서를 문서 없이 운영하면 데이터 손실이 납니다.",
    )
    reg(
        "homelab-segment-monitoring-2026",
        "홈랩 세그먼트별 모니터링 설계 2026: VLAN·서비스·스토리지",
        "2026-04-01-homelab-segment-monitoring-2026.md",
        ["홈랩", "모니터링", "네트워크"],
        "hardware-lab",
        "한 대시보드에 모든 걸 넣으면 신호가 섞입니다. 세그먼트별로 질문을 분리해야 장애 원인 추적이 빨라집니다.",
    )
    reg(
        "homelab-power-cost-scheduling-2026",
        "홈랩 전력비 최적화 스케줄링 2026: 부하·온도·요금을 같이 보기",
        "2026-04-01-homelab-power-cost-scheduling-2026.md",
        ["전력", "홈랩", "비용"],
        "hardware-lab",
        "전력 최적화는 단순 절전이 아니라 서비스 SLO와의 타협입니다. 스케줄은 가용성 하한을 먼저 고정합니다.",
    )
    reg(
        "homelab-monthly-ops-report-automation-2026",
        "홈랩 월간 운영 리포트 자동화 2026: 한 장으로 회고하기",
        "2026-04-01-homelab-monthly-ops-report-automation-2026.md",
        ["홈랩", "리포트", "운영"],
        "hardware-lab",
        "월간 리포트는 형식이 아니라 개선의 출발점입니다. 수치 5개와 사건 3개만 남기면 다음 달 의사결정이 빨라집니다.",
    )

    reg(
        "ai-automation-first-revenue-30days-2026",
        "AI 자동화 30일 첫 매출 플랜 2026: 1인·소팀 실행 로드맵",
        "2026-03-31-ai-automation-first-revenue-30days-2026.md",
        ["수익화", "실행", "1인창업"],
        "ai-automation",
        "첫 매출은 완성도가 아니라 속도입니다. 30일 안에 '돈을 받을 수 있는 최소 납품'을 정의하고 파일럿으로 전환합니다.",
    )
    reg(
        "niche-selection-framework-ai-2026",
        "AI 자동화 니치 선정 프레임워크 2026: 수요·경쟁·납품 난이도",
        "2026-04-01-niche-selection-framework-ai-2026.md",
        ["니치", "전략", "AI"],
        "ai-automation",
        "모든 산업이 기회처럼 보이면 아무 데도 안 통합니다. 니치는 감이 아니라 점수표로 고릅니다.",
    )
    reg(
        "proposal-automation-template-2026",
        "AI 자동화 제안서 자동화 2026: 견적·범위·리스크를 한 템플릿에",
        "2026-04-01-proposal-automation-template-2026.md",
        ["제안서", "영업", "자동화"],
        "ai-automation",
        "제안서가 느리면 기회가 사라집니다. 변수는 고객 맞춤이고, 뼈대는 100% 재사용해야 합니다.",
    )
    reg(
        "delivery-qa-framework-ai-services-2026",
        "AI 서비스 납품 QA 체계 2026: 재작업과 분쟁을 줄이는 법",
        "2026-04-01-delivery-qa-framework-ai-services-2026.md",
        ["납품", "QA", "분쟁예방"],
        "ai-automation",
        "납품 분쟁의 대부분은 기준의 모호함에서 옵니다. QA는 체크리스트이자 계약 해석서입니다.",
    )
    reg(
        "monthly-10m-krw-ai-ops-model-2026",
        "월 1000만원 AI 운영 모델 시뮬레이션 2026: 객단가·고객 수·원가",
        "2026-04-01-monthly-10m-krw-ai-ops-model-2026.md",
        ["재무", "모델링", "AI"],
        "ai-automation",
        "목표 매출만 적어두면 실행이 흐려집니다. 객단가·고객 수·변동비를 한 표에서 맞춰야 현실적인 플랜이 됩니다.",
    )

    reg(
        "seo-keyword-clustering-topic-map-2026",
        "SEO 키워드 클러스터링 실무 2026: 토픽맵으로 콘텐츠 엔진 만들기",
        "2026-03-31-seo-keyword-clustering-topic-map-2026.md",
        ["SEO", "키워드", "콘텐츠"],
        "software-dev",
        "개별 키워드 글쓰기는 확장에 한계가 있습니다. 클러스터는 내부 링크와 시리즈 설계의 뼈대입니다.",
    )
    reg(
        "content-structure-template-automation-2026",
        "콘텐츠 구조 템플릿 자동화 2026: 개요·표·체크리스트 표준화",
        "2026-04-01-content-structure-template-automation-2026.md",
        ["콘텐츠", "템플릿", "자동화"],
        "software-dev",
        "템플릿은 글의 톤을 맞추는 도구이자 품질 하한을 보장하는 장치입니다.",
    )
    reg(
        "svg-pipeline-automation-2026",
        "SVG 다이어그램 파이프라인 자동화 2026: 커버·플로우 자산화",
        "2026-04-01-svg-pipeline-automation-2026.md",
        ["SVG", "다이어그램", "자동화"],
        "software-dev",
        "이미지 자산이 흩어지면 유지보수가 불가능합니다. 슬러그·스타일·메타데이터 규칙을 파이프라인으로 고정합니다.",
    )
    reg(
        "internal-link-series-index-automation-2026",
        "내부 링크·시리즈 인덱스 자동화 2026: 발견성 운영",
        "2026-04-01-internal-link-series-index-automation-2026.md",
        ["내부링크", "SEO", "시리즈"],
        "software-dev",
        "검색 유입만 믿으면 신규 독자는 오고 기존 독자는 잃습니다. 인덱스와 링크는 제품의 내비게이션입니다.",
    )
    reg(
        "content-refresh-calendar-operations-2026",
        "콘텐츠 리프레시 캘린더 운영 2026: 낡은 글을 자산으로",
        "2026-04-01-content-refresh-calendar-operations-2026.md",
        ["리프레시", "운영", "SEO"],
        "software-dev",
        "리프레시는 새 글만큼 ROI가 큽니다. 캘린더 없이 하면 항상 미뤄집니다.",
    )
    reg(
        "seo-content-performance-loop-2026",
        "SEO 콘텐츠 성과 분석 루프 2026: CTR·체류·전환 개선",
        "2026-04-01-seo-content-performance-loop-2026.md",
        ["분석", "SEO", "개선루프"],
        "software-dev",
        "측정 없는 콘텐츠 전략은 취미입니다. 루프는 주간 단위로 짧게 돌려야 합니다.",
    )

    standalone = [
        ("ai-automation-service-pricing-table-2026", "AI 자동화 대행 단가표 만드는 법 2026", "2026-03-31-ai-automation-service-pricing-table-2026.md", ["가격", "자동화", "영업"], "ai-automation", "단가표는 흥정 방어선이자 범위 설명서입니다. 항목을 쪼개야 마진이 보호됩니다."),
        ("prompt-failure-log-to-revenue-2026", "프롬프트 실패 로그를 매출 개선으로 연결하는 법 2026", "2026-03-31-prompt-failure-log-to-revenue-2026.md", ["프롬프트", "로그", "수익"], "ai-automation", "실패 로그는 비용이 아니라 제품 백로그입니다. 분류 체계가 곧 개선 속도입니다."),
        ("monthly-kpi-review-template-ai-ops-2026", "월간 KPI 리뷰 템플릿 2026: AI 운영팀 실전판", "2026-03-31-monthly-kpi-review-template-ai-ops-2026.md", ["KPI", "회고", "운영"], "ai-automation", "회의록이 아니라 의사결정이 나와야 합니다. 템플릿은 질문 순서가 핵심입니다."),
        ("automation-sla-design-guide-2026", "고객별 자동화 SLA 설계 가이드 2026", "2026-03-31-automation-sla-design-guide-2026.md", ["SLA", "계약", "운영"], "ai-automation", "SLA는 약속이면서 동시에 운영 한계를 드러내는 장치입니다. 측정 가능한 문장으로 써야 합니다."),
        ("reduce-rework-with-qa-framework-2026", "재작업률 50% 줄이는 QA 체계 2026", "2026-03-31-reduce-rework-with-qa-framework-2026.md", ["QA", "재작업", "품질"], "ai-automation", "재작업은 대부분 기준 전달 실패에서 옵니다. QA는 승인 전 마지막 방어선입니다."),
        ("ai-automation-contract-clauses-2026", "AI 자동화 프로젝트 계약서 핵심 조항 2026", "2026-03-31-ai-automation-contract-clauses-2026.md", ["계약", "리스크", "자동화"], "ai-automation", "모델 출력은 확률적입니다. 범위·데이터·저작권·보안 조항을 분리해 적어야 분쟁이 줄어듭니다."),
        ("homelab-alert-fatigue-reduction-2026", "홈랩 모니터링 알람 피로도 줄이는 법 2026", "2026-03-31-homelab-alert-fatigue-reduction-2026.md", ["알림", "홈랩", "SRE"], "hardware-lab", "알람이 많을수록 중요한 알람이 묻힙니다. 심각도 계층과 집계 규칙이 필요합니다."),
        ("ups-power-event-runbook-2026", "UPS·전력 이벤트 대응 런북 2026", "2026-03-31-ups-power-event-runbook-2026.md", ["UPS", "전력", "런북"], "hardware-lab", "전력 이벤트는 시간이 곧 데이터입니다. 순서가 틀리면 복구 비용이 폭증합니다."),
        ("nas-failure-response-manual-2026", "NAS 장애 대응 매뉴얼 2026", "2026-03-31-nas-failure-response-manual-2026.md", ["NAS", "스토리지", "장애"], "hardware-lab", "NAS 장애는 증상이 비슷해 원인 추적이 느립니다. 단계별 차단 표가 필요합니다."),
        ("backup-recovery-success-rate-ops-2026", "복구 성공률 중심 백업 운영 2026", "2026-03-31-backup-recovery-success-rate-ops-2026.md", ["백업", "복구", "운영"], "hardware-lab", "백업 성공은 필요조건이고 복구 성공이 충분조건입니다. 리허설 지표를 운영 KPI로 올립니다."),
    ]
    for slug, title, fn, tags, cat, hook in standalone:
        reg(slug, title, fn, tags, cat, hook)

    # Write all topic posts
    start = base + timedelta(hours=1)
    for idx, (slug, (title, fn, cat, tags, hook, extra)) in enumerate(topics.items()):
        dt = start + timedelta(minutes=idx * 12)
        body = long_article(hook, T1, T2, STEPS, CHK, CLOSE + ("\n\n" + extra if extra else ""))
        write_post(fn, title, slug, cat, tags, f"{title}의 실행 기준과 체크리스트를 담은 완성 가이드입니다.", body, dt)
        n += 1

    print("wrote", n, "posts + svgs")


if __name__ == "__main__":
    main()
