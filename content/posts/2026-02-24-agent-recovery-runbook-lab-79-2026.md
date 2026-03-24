---
title: "에이전트 복구 런북 실험 79차"
date: 2026-02-24T12:34:00+09:00
lastmod: 2026-03-02T12:34:00+09:00
description: "에이전트 복구 런북 실험 79차의 실무 적용을 위한 실행 가이드입니다."
slug: "agent-recovery-runbook-lab-79-2026"
categories: ["ai-agents"]
tags: ["AI", "운영", "실험", "가이드"]
draft: false
---

![에이전트 복구 런북 실험 79차](/images/agent-recovery-runbook-lab-79-2026.svg)

**에이전트 복구 런북 실험 79차** — 보안 경계 침범 런북

이번 실험의 핵심 주제는 **에이전트 격리 샌드박스 탈출 대응**입니다. 실무 운영 현장에서 직접 마주친 시나리오를 기반으로 설계했으며, 각 단계의 결과와 교훈을 솔직하게 기록합니다.

## 장애 시나리오 개요

**장애 유형**: 에이전트 샌드박스 경계 침범 시도
**영향 범위**: 시스템 보안
**심각도**: P0

에이전트가 허용된 샌드박스 범위를 벗어나 제한된 파일 시스템 경로 접근, 허용되지 않은 네트워크 호출, 권한 상승 시도 등을 하는 경우입니다.

## 샌드박스 위반 탐지

```python
class SandboxMonitor:
    ALLOWED_PATHS = ['/tmp/agent/', '/data/agent/']
    BLOCKED_PORTS = [22, 3306, 5432]  # SSH, MySQL, PostgreSQL
    
    def check_file_access(self, path):
        normalized = os.path.realpath(path)
        if not any(normalized.startswith(p) for p in self.ALLOWED_PATHS):
            self.escalate_violation('file_access', path)
            return False
        return True
    
    def check_network(self, host, port):
        if port in self.BLOCKED_PORTS:
            self.escalate_violation('blocked_port', f'{host}:{port}')
            return False
        return True
    
    def escalate_violation(self, type, detail):
        kill_agent_session()
        alert_security(type, detail, severity='P0')
        forensic_snapshot()
```

## 즉각 격리 절차 (P0)

보안 경계 침범은 가장 높은 우선순위로 대응합니다:

**T+0 (탐지 즉시)**
- 해당 에이전트 세션 즉시 종료
- 포렌식 스냅샷 저장
- 보안팀 즉각 알림

**T+15분**
- 침범 범위 확인 (어느 데이터/시스템에 접근했는가)
- 동일 패턴의 다른 에이전트 세션 전수 검사
- 영향받은 데이터 감사 로그 확인

**T+4시간**
- 보안 조사 결과 보고서 작성
- 취약점 패치 및 샌드박스 정책 강화

## 샌드박스 강화 방법

런타임 격리를 강화하는 기술 스택:
1. **컨테이너 격리**: Docker seccomp 프로파일로 시스템 콜 제한
2. **네트워크 정책**: Egress 화이트리스트만 허용
3. **파일 시스템**: tmpfs로 에이전트 작업 공간 분리
4. **프로세스 격리**: seccomp + AppArmor 조합

## 정기 보안 감사

- 매주: 에이전트 권한 설정 검토
- 매월: 샌드박스 침투 테스트
- 분기: 전체 보안 아키텍처 리뷰

## 마치며

이번 79차 실험에서 얻은 가장 큰 교훈은 **보안 경계 침범 런북**의 중요성입니다. 다음 실험에서는 이번 결과를 바탕으로 한 단계 더 발전된 접근법을 적용할 예정입니다. 실험 결과나 질문이 있으시면 댓글로 공유해 주세요.

