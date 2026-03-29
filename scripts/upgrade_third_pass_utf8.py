# -*- coding: utf-8 -*-
from pathlib import Path
import re

ROOT = Path(r"c:/My/Claude/Blog/blog")
POSTS = ROOT / "content" / "posts"

SERIES = {
    "ai-automation-revenue-operations-series-2026",
    "hardware-lab-automation-ops-series-2026",
    "solo-team-ai-income-roadmap-series-2026",
    "seo-content-automation-engine-series-2026",
}

REVENUE = {
    "ai-automation-productization-blueprint-2026","ai-client-onboarding-automation-2026","prompt-quality-gate-operations-2026",
    "hitl-operations-manual-2026","ai-ops-cost-structure-optimization-2026","ai-ops-kpi-dashboard-design-2026",
    "client-retention-reporting-automation-2026","ai-automation-scale-strategy-2026","ai-automation-first-revenue-30days-2026",
    "niche-selection-framework-ai-2026","proposal-automation-template-2026","delivery-qa-framework-ai-services-2026",
    "monthly-10m-krw-ai-ops-model-2026","ai-automation-service-pricing-table-2026","prompt-failure-log-to-revenue-2026",
    "monthly-kpi-review-template-ai-ops-2026","automation-sla-design-guide-2026","reduce-rework-with-qa-framework-2026",
    "ai-automation-contract-clauses-2026"
}
INFRA = {
    "homelab-alert-automation-2026","homelab-backup-restore-drill-automation-2026","homelab-ups-event-runbook-2026",
    "homelab-segment-monitoring-2026","homelab-power-cost-scheduling-2026","homelab-monthly-ops-report-automation-2026",
    "homelab-alert-fatigue-reduction-2026","ups-power-event-runbook-2026","nas-failure-response-manual-2026",
    "backup-recovery-success-rate-ops-2026"
}
SEO = {
    "seo-keyword-clustering-topic-map-2026","content-structure-template-automation-2026","svg-pipeline-automation-2026",
    "internal-link-series-index-automation-2026","content-refresh-calendar-operations-2026","seo-content-performance-loop-2026"
}

SERIES_ROWS = {
    "ai-automation-revenue-operations-series-2026": [
        ("1편", "AI 자동화 구축형 상품화 설계", "ai-automation-productization-blueprint-2026"),
        ("2편", "고객 온보딩 자동화", "ai-client-onboarding-automation-2026"),
        ("3편", "프롬프트 품질 게이트", "prompt-quality-gate-operations-2026"),
        ("4편", "HITL 운영 매뉴얼", "hitl-operations-manual-2026"),
        ("5편", "원가 구조 최적화", "ai-ops-cost-structure-optimization-2026"),
        ("6편", "성과 대시보드 설계", "ai-ops-kpi-dashboard-design-2026"),
        ("7편", "재구매 리포팅 자동화", "client-retention-reporting-automation-2026"),
        ("8편", "확장 전략", "ai-automation-scale-strategy-2026"),
    ],
    "hardware-lab-automation-ops-series-2026": [
        ("1편", "홈랩 장애 알림 자동화", "homelab-alert-automation-2026"),
        ("2편", "백업·복구 리허설 자동화", "homelab-backup-restore-drill-automation-2026"),
        ("3편", "UPS 이벤트 런북", "homelab-ups-event-runbook-2026"),
        ("4편", "세그먼트별 모니터링", "homelab-segment-monitoring-2026"),
        ("5편", "전력비 최적화 스케줄링", "homelab-power-cost-scheduling-2026"),
        ("6편", "월간 운영 리포트", "homelab-monthly-ops-report-automation-2026"),
    ],
    "solo-team-ai-income-roadmap-series-2026": [
        ("1편", "30일 첫 매출 플랜", "ai-automation-first-revenue-30days-2026"),
        ("2편", "니치 선정 프레임워크", "niche-selection-framework-ai-2026"),
        ("3편", "제안서 자동화", "proposal-automation-template-2026"),
        ("4편", "납품 QA 체계", "delivery-qa-framework-ai-services-2026"),
        ("5편", "월 1000만원 모델", "monthly-10m-krw-ai-ops-model-2026"),
    ],
    "seo-content-automation-engine-series-2026": [
        ("1편", "키워드 클러스터링", "seo-keyword-clustering-topic-map-2026"),
        ("2편", "글 구조 템플릿 자동 생성", "content-structure-template-automation-2026"),
        ("3편", "SVG 파이프라인", "svg-pipeline-automation-2026"),
        ("4편", "내부 링크 자동 반영", "internal-link-series-index-automation-2026"),
        ("5편", "리프레시 캘린더", "content-refresh-calendar-operations-2026"),
        ("6편", "성과 분석 루프", "seo-content-performance-loop-2026"),
    ],
}


def group(slug: str):
    if slug in REVENUE:
        return "revenue"
    if slug in INFRA:
        return "infra"
    if slug in SEO:
        return "seo"
    return None

for p in POSTS.glob("*.md"):
    t = p.read_text(encoding="utf-8")
    sm = re.search(r'^slug:\s*"([^"]+)"', t, re.M)
    if not sm:
        continue
    slug = sm.group(1)

    if slug not in SERIES and group(slug) is None:
        continue

    hm = re.search(r'\A---\n.*?\n---\n\n', t, re.S)
    tm = re.search(r'^title:\s*"([^"]+)"', t, re.M)
    if not hm or not tm:
        continue

    head = hm.group(0)
    title = tm.group(1)
    img = f'![{title}](/images/{slug}.svg)\n\n'

    if slug in SERIES:
        rows = SERIES_ROWS[slug]
        table = "\n".join([f"| {a} | {b} | [바로가기](/posts/{s}/) |" for a,b,s in rows])
        body = f"""## 시리즈 목적

이 인덱스는 단순 목록이 아니라 **적용 순서와 기대 성과**를 함께 보여주는 실행 지도입니다.

## 연재 구성

| 회차 | 주제 | 링크 |
|---|---|---|
{table}

## 실행 가이드

- 이번 주 적용할 편 1개를 정합니다.  
- 적용 전/후 KPI 3개를 같은 표에서 비교합니다.  
- 실패 로그를 남기고 다음 편으로 넘어갑니다.

```mermaid
flowchart TD
    A[편 선택] --> B[적용]
    B --> C[KPI 측정]
    C --> D[회고]
    D --> E[다음 편]
```
"""
    else:
        g = group(slug)
        if g == "revenue":
            table = """| 항목 | 질문 | 기준 |
|---|---|---|
| 범위 | 어디까지 납품인가 | 포함/제외 문장 고정 |
| 가격 | 왜 이 단가인가 | 변동비+검수비 분리 |
| 품질 | 통과 기준은 무엇인가 | 수치+예시 이중 검증 |
| 재구매 | 다음 계약 근거가 있는가 | 전/후 KPI 리포트 |"""
            kpi = """| KPI | 정의 | 목표 |
|---|---|---|
| 파일럿 전환율 | 제안 대비 유료 전환 | 30% 이상 |
| 1회 통과율 | 수정 없이 승인된 비율 | 75% 이상 |
| 고객당 공헌이익 | 객단가-변동비 | 전월 대비 증가 |
| 재구매율 | 60일 내 추가 계약 | 증가 추세 |"""
            scenario = """### 실전 시나리오

- **상황**: 납품 후 수정 요청이 급증  
- **원인**: 승인 기준과 범위 문장이 모호함  
- **조치**: 반려 사유 코드화 + 승인표 계약서 별첨  
- **결과**: 재작업률 2주 내 유의미 감소"""
        elif g == "infra":
            table = """| 영역 | 관측 지표 | 임계 조건 |
|---|---|---|
| 저장소 | SMART/IO wait | 급격 증가 시 경고 |
| 전력 | UPS 배터리/부하율 | 하한 도달 시 조치 |
| 열관리 | CPU/NAS/디스크 온도 | 안전선 초과 지속 |
| 네트워크 | 지연/손실/분절 | 기준선 대비 악화 |"""
            kpi = """| KPI | 정의 | 목표 |
|---|---|---|
| MTTR | 감지~복구 완료 시간 | 전월 대비 단축 |
| 오탐 비율 | 무의미 알림 비율 | 20% 미만 |
| 복구 리허설 통과율 | 월간 시나리오 성공률 | 90% 이상 |
| 서비스 가용성 | 핵심 서비스 uptime | 99%+ |"""
            scenario = """### 실전 시나리오

- **상황**: 야간 경고가 연속 발행되어 대응 지연  
- **원인**: 중복 룰과 채널 분리 부재  
- **조치**: 동일 이벤트 집계 + 심각도별 알림 분리  
- **결과**: 오탐 감소, 실제 장애 대응 속도 개선"""
        else:
            table = """| 레이어 | 핵심 작업 | 실패 패턴 |
|---|---|---|
| 토픽맵 | 클러스터/의도 분류 | 주제 중복 |
| 작성 템플릿 | 제목-표-다이어그램 표준화 | 품질 편차 |
| 내부 링크 | 허브/시리즈 자동 연결 | 고립 문서 증가 |
| 리프레시 | 갱신 캘린더 운영 | 상위 문서 노후화 |"""
            kpi = """| KPI | 정의 | 목표 |
|---|---|---|
| 클러스터 커버율 | 계획 대비 발행 비율 | 85% 이상 |
| 내부링크 밀도 | 문서당 유효 내부링크 | 증가 추세 |
| 리프레시 준수율 | 예정 문서 갱신 완료 | 90% 이상 |
| 유입 품질 | CTR·체류·전환 | 동시 개선 |"""
            scenario = """### 실전 시나리오

- **상황**: 검색 유입은 증가했지만 전환 정체  
- **원인**: 정보형 문서 편중, 결정형 콘텐츠 부족  
- **조치**: 비교표/체크리스트/CTA 포함 문서 보강  
- **결과**: 4주 후 문의 전환율 상승"""

        body = f"""## 왜 이 문서가 중요한가

이 문서는 정보 요약보다 **실행 가능한 운영 규칙**을 만드는 데 초점을 둡니다. 실제 운영에서 가장 자주 깨지는 지점을 먼저 고정하면, 품질과 속도, 비용을 함께 개선할 수 있습니다.

## 핵심 운영 설계

{table}

## KPI 대시보드 기준

{kpi}

## 실행 절차

1. **기준선 확보**: 최근 2~4주 지표를 기준값으로 고정합니다.  
2. **변경점 1개 적용**: 한 번에 하나만 바꿔 인과를 확인합니다.  
3. **게이트 검증**: 하한 미달 시 롤백 또는 수동 검토로 전환합니다.  
4. **로그 코드화**: 실패 사유를 코드로 남겨 회고에 반영합니다.  
5. **주간 회고**: 개선 과제 3개만 다음 스프린트에 올립니다.

```mermaid
flowchart TD
    A[기준선 측정] --> B[실행]
    B --> C[게이트 검증]
    C -->|통과| D[운영 반영]
    C -->|미달| E[재시도/수동 검토]
    D --> F[KPI 리뷰]
    E --> F
    F --> G[다음 개선]
```

{scenario}

## 체크리스트

- 기준·책임자·마감이 한 문서에서 확인되는가  
- KPI가 행동으로 연결되는가  
- 실패 로그가 다음 백로그로 넘어가는가  
- 자동화 범위가 팀 역량 대비 과도하지 않은가

## 마무리

핵심은 기술이 아니라 **운영 리듬**입니다. 기준-실행-검증-개선을 끊기지 않게 반복하면, 작은 팀도 안정적으로 성과를 축적할 수 있습니다.
"""

    p.write_text(head + img + body, encoding="utf-8")

print("utf8 third-pass updated")
