---
title: "하네스(Harness) 엔지니어링 완전 가이드 — CI/CD부터 비용 관리까지"
date: 2023-10-27T09:00:00+09:00
lastmod: 2023-10-27T09:00:00+09:00
description: "Harness CI/CD 플랫폼의 아키텍처, GitOps 워크플로우, 피처 플래그, 클라우드 비용 관리까지. 개발자를 위한 Harness 완전 정복 가이드."
slug: "harness-engineering-for-developers"
categories: ["ai-agents"]
tags: ["Harness", "CI/CD", "DevOps", "GitOps", "피처플래그", "클라우드비용"]
featureimage: "/images/posts/하네스-엔지니어링/svg-1.svg"
series: []
draft: false
---

개발팀이 성장할수록 소프트웨어 배포 파이프라인은 점점 복잡해진다. Jenkins 플러그인 지옥, 수작업으로 관리되는 환경 변수, 배포마다 달라지는 절차, 그리고 클라우드 비용이 어디서 새는지 파악하지 못하는 상황. 이런 고통을 구조적으로 해결하기 위해 등장한 것이 **Harness**다.

Harness는 단순한 CI/CD 도구가 아니다. CI, CD, GitOps, Feature Flags, Cloud Cost Management, Security Testing Orchestration을 하나의 플랫폼에서 제공하는 **통합 소프트웨어 딜리버리 플랫폼**이다. 이 글에서는 Harness의 핵심 아키텍처부터 실전 운영 팁까지, 개발자 관점에서 깊이 있게 다룬다.

---

## 1. Harness란 무엇인가 — CI/CD 플랫폼의 재정의

### 기존 CI/CD 도구의 한계

Jenkins는 오랫동안 CI/CD의 표준이었다. 하지만 현대적인 마이크로서비스, 멀티클라우드 환경에서 Jenkins는 여러 한계를 드러낸다.

- **플러그인 관리 부담**: 수백 개의 플러그인이 서로 충돌하거나 업데이트가 끊기는 문제
- **스크립팅 위주의 파이프라인**: Groovy 기반 Jenkinsfile은 유지보수가 어렵다
- **가시성 부족**: 배포 상태, 실패 원인, 롤백 이력을 한눈에 보기 어렵다
- **비용 통제 불가**: 어떤 파이프라인이 얼마나 클라우드 리소스를 소비하는지 알 수 없다

GitHub Actions, GitLab CI도 좋은 선택이지만, 대규모 엔터프라이즈 환경에서 멀티 클라우드, 멀티 팀, 거버넌스 요구사항을 충족하기엔 여전히 부족하다.

### Harness의 접근 방식

Harness는 2017년 Jyoti Bansal(AppDynamics 창업자)이 설립했다. 핵심 철학은 **"개발자가 배포에 쓰는 시간을 최소화하고, 비즈니스 가치 창출에 집중하게 한다"**는 것이다.

Harness가 제공하는 모듈:

| 모듈 | 설명 |
|------|------|
| **CI (Continuous Integration)** | 빌드, 테스트, 아티팩트 관리 |
| **CD (Continuous Delivery)** | 다양한 배포 전략, 환경 관리 |
| **GitOps** | Git 기반 선언적 인프라 관리 |
| **Feature Flags** | 기능 토글, A/B 테스트 |
| **Cloud Cost Management** | 클라우드 비용 가시성 및 최적화 |
| **Security Testing Orchestration** | 보안 취약점 스캔 통합 |
| **Chaos Engineering** | 장애 주입 및 복원력 테스트 |

---

## 2. Harness 아키텍처 — Control Plane과 Delegate

Harness의 아키텍처를 이해하는 것이 운영의 출발점이다.

![하네스 CI의 아키텍처 다이어그램 — Control Plane SaaS와 고객 인프라 내 Delegate 모델](/images/posts/하네스-엔지니어링/svg-1.svg)

### Control Plane (SaaS)

Harness의 두뇌 역할을 하는 Control Plane은 Harness가 호스팅하는 SaaS 레이어다. 여기서 파이프라인 정의, 실행 오케스트레이션, 대시보드, 로그 수집이 이루어진다.

- `app.harness.io`로 접근하는 웹 UI
- REST API 및 GraphQL API 제공
- 파이프라인 YAML 저장 및 버전 관리
- 실행 이력, 아티팩트 레지스트리 연동

### Delegate — 고객 인프라의 에이전트

**Delegate**는 고객의 인프라(온프레미스, AWS, GCP, Azure, Kubernetes 클러스터) 내에 배포되는 경량 에이전트다. Control Plane의 명령을 받아 실제 작업을 수행한다.

Delegate의 역할:
- 빌드 작업 실행 (Docker 빌드, 테스트 등)
- 쿠버네티스 클러스터 배포
- 시크릿 접근 (Vault, AWS Secrets Manager 등)
- 방화벽 안쪽 서비스와의 통신

**왜 이 구조가 중요한가?** Harness는 고객의 인프라에 직접 접근하지 않는다. Delegate가 Control Plane으로 아웃바운드 연결을 맺는 방식이라, 인바운드 포트를 열 필요가 없다. 보안에 민감한 금융, 의료 업계에서 Harness를 채택하는 주요 이유다.

### Self-Managed Enterprise Edition (SMEE)

SaaS가 불가능한 환경을 위해 Harness는 온프레미스 설치형인 SMEE를 제공한다. 쿠버네티스 클러스터에 Helm 차트로 배포하며, 에어갭(air-gapped) 환경도 지원한다.

```bash
# Helm으로 Harness SMEE 설치
helm repo add harness https://harness.github.io/helm-charts
helm install harness harness/harness \
  --namespace harness \
  --create-namespace \
  -f values.yaml
```

---

## 3. Harness의 6가지 핵심 이점

![하네스 사용의 6가지 핵심 이점](/images/posts/하네스-엔지니어링/svg-2.svg)

Harness를 도입하는 팀들이 공통적으로 보고하는 이점을 정리하면 다음과 같다.

1. **배포 속도 향상**: 파이프라인 자동화와 병렬 실행으로 배포 주기 단축
2. **개발자 생산성 증가**: 반복적인 인프라 작업 자동화, 배포 관련 컨텍스트 스위칭 최소화
3. **클라우드 비용 최적화**: 낭비되는 리소스 실시간 파악, 자동 추천
4. **릴리즈 유연성**: 카나리, 블루/그린 등 다양한 배포 전략으로 리스크 최소화
5. **보안 및 컴플라이언스**: OPA 정책 강제, RBAC, 감사 로그
6. **통합 DevOps 플랫폼**: CI, CD, 비용, 보안을 하나의 플랫폼에서

---

## 4. CI (Continuous Integration) — 파이프라인 구성

### YAML 기반 파이프라인 정의

Harness CI의 모든 파이프라인은 YAML로 정의된다. Git 저장소에 `.harness/` 디렉토리를 만들고 파이프라인 파일을 저장하면, 변경 사항이 자동으로 반영된다.

```yaml
pipeline:
  name: Build and Test
  identifier: build_and_test
  projectIdentifier: my_project
  orgIdentifier: default
  stages:
    - stage:
        name: Build
        identifier: Build
        type: CI
        spec:
          cloneCodebase: true
          infrastructure:
            type: KubernetesDirect
            spec:
              connectorRef: my_k8s_cluster
              namespace: harness-builds
          execution:
            steps:
              - step:
                  type: Run
                  name: Run Tests
                  identifier: Run_Tests
                  spec:
                    connectorRef: dockerhub
                    image: golang:1.21
                    command: |
                      go test ./... -v -coverprofile=coverage.out
                      go tool cover -html=coverage.out -o coverage.html
              - step:
                  type: BuildAndPushDockerRegistry
                  name: Build and Push Image
                  identifier: Build_Push
                  spec:
                    connectorRef: dockerhub
                    repo: myorg/myapp
                    tags:
                      - <+pipeline.sequenceId>
                      - latest
```

### 빌드 인프라 옵션

Harness CI는 다양한 빌드 인프라를 지원한다.

| 인프라 타입 | 설명 | 적합한 경우 |
|------------|------|------------|
| **Kubernetes** | 자체 K8s 클러스터에서 실행 | 비용 최적화, 커스텀 환경 |
| **Cloud** (Harness Cloud) | Harness가 관리하는 클라우드 런너 | 빠른 시작, 관리 부담 없음 |
| **Docker** | 로컬 Docker로 실행 | 개발/테스트 환경 |
| **VM** | 가상 머신에서 실행 | 특수 하드웨어 요구 시 |

### 테스트 인텔리전스 (Test Intelligence)

Harness CI의 가장 강력한 기능 중 하나가 **Test Intelligence**다. ML을 활용해 변경된 코드와 관련된 테스트만 선별해 실행한다.

```yaml
- step:
    type: RunTests
    name: Run Tests with TI
    identifier: Run_Tests_TI
    spec:
      language: Java
      buildTool: Maven
      args: test
      runOnlySelectedTests: true  # Test Intelligence 활성화
      testAnnotations: "@Test,@org.junit.Test"
```

실제 사례: 10,000개 테스트 스위트에서 변경 관련 300개만 실행 → 테스트 시간 70% 단축.

### 캐싱 전략

빌드 속도를 높이는 핵심은 캐싱이다. Harness는 레이어 캐싱과 의존성 캐싱을 모두 지원한다.

```yaml
- step:
    type: RestoreCacheGCS
    name: Restore Cache
    identifier: Restore_Cache
    spec:
      connectorRef: gcs_connector
      bucket: my-build-cache
      key: maven-{{ checksum "pom.xml" }}

- step:
    type: SaveCacheGCS
    name: Save Cache
    identifier: Save_Cache
    spec:
      connectorRef: gcs_connector
      bucket: my-build-cache
      key: maven-{{ checksum "pom.xml" }}
      sourcePaths:
        - /root/.m2/repository
```

---

## 5. CD (Continuous Delivery) — 배포 전략

### 배포 전략 개요

Harness CD는 현대적인 배포 패턴을 기본 제공한다. 팀이 직접 배포 스크립트를 작성할 필요 없이, 검증된 전략을 설정만으로 사용할 수 있다.

#### 카나리 배포 (Canary Deployment)

트래픽의 일부(예: 10%)를 새 버전으로 라우팅하고, 에러율/레이턴시를 모니터링한 뒤 점진적으로 확대한다.

```yaml
- step:
    type: K8sCanaryDeploy
    name: Canary Deploy
    identifier: canary_deploy
    spec:
      instanceSelection:
        type: Percentage
        spec:
          percentage: 10
      skipDryRun: false
- step:
    type: Verify
    name: Verify Canary
    identifier: verify_canary
    spec:
      type: Continuous
      spec:
        monitoredServiceRef: my_service
        healthSources:
          - prometheus
        duration: 15m
        sensitivity: MEDIUM
- step:
    type: K8sCanaryDelete
    name: Delete Canary
    identifier: delete_canary
```

#### 블루/그린 배포 (Blue/Green Deployment)

두 개의 동일한 환경을 유지하고, 새 버전 검증 후 트래픽을 전환한다. 문제 발생 시 즉시 롤백 가능.

```yaml
- step:
    type: K8sBlueGreenDeploy
    name: Blue Green Deploy
    identifier: bg_deploy
    spec:
      skipDryRun: false
- step:
    type: K8sBGSwapServices
    name: Swap Services
    identifier: swap_services
    spec:
      skipDryRun: false
```

#### 롤링 배포 (Rolling Deployment)

기존 인스턴스를 순차적으로 교체한다. 가장 단순하지만, 롤백 시 전체 배포가 필요하다.

### 환경 관리

Harness는 **환경(Environment)**과 **인프라 정의(Infrastructure Definition)**를 분리해 관리한다.

```yaml
environment:
  name: Production
  identifier: production
  type: Production
  variables:
    - name: REPLICA_COUNT
      type: String
      value: "10"
    - name: MEMORY_LIMIT
      type: String
      value: "2Gi"
```

환경별로 다른 설정 값, 시크릿, 승인 정책을 적용할 수 있어 개발/스테이징/프로덕션 환경을 안전하게 분리할 수 있다.

### 자동 롤백

Harness CD의 핵심 안전장치는 **자동 롤백**이다. 모니터링 지표(Prometheus, Datadog, New Relic 등)를 연동해 배포 후 이상 지표 감지 시 자동으로 이전 버전으로 롤백한다.

```yaml
rollbackSteps:
  - step:
      type: K8sRollingRollback
      name: Rollback
      identifier: rollback
      spec: {}
```

---

## 6. GitOps 워크플로우 — Git이 진실의 원천

![하네스 CI의 GitOps 기반 워크플로우 — Git 커밋에서 파이프라인 트리거, 빌드/배포까지](/images/posts/하네스-엔지니어링/svg-3.svg)

### GitOps란?

GitOps는 인프라와 애플리케이션 설정을 Git 저장소에 선언적으로 관리하는 방식이다. Git이 **단일 진실 원천(Single Source of Truth)**이 되며, 모든 변경은 Pull Request를 통해 이루어진다.

Harness GitOps는 **Argo CD**를 기반으로 구축되어 있어, 강력한 쿠버네티스 GitOps 기능을 Harness 플랫폼에서 통합 관리할 수 있다.

### GitOps 워크플로우

1. 개발자가 애플리케이션 코드 또는 Kubernetes 매니페스트를 Git에 푸시
2. Harness CI가 빌드/테스트를 실행하고 새 컨테이너 이미지를 생성
3. Harness가 이미지 태그를 Git 설정 저장소에 자동 업데이트 (PR 생성)
4. PR 병합 시 Harness GitOps Agent가 클러스터 상태를 Git과 동기화
5. 클러스터 상태와 Git 상태의 드리프트 감지 및 자동 수정

```yaml
# GitOps Application 정의
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: harness-gitops
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/k8s-configs
    targetRevision: main
    path: apps/my-app/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### PR 파이프라인 트리거

```yaml
triggers:
  - trigger:
      name: PR Trigger
      identifier: pr_trigger
      enabled: true
      source:
        type: Webhook
        spec:
          type: Github
          spec:
            event: PullRequest
            actions:
              - Open
              - Reopen
              - Edit
            autoAbortPreviousExecutions: true
```

---

## 7. Feature Flags — 안전한 기능 출시

![피처 플래그(Feature Flags) 개념 아이콘 — 토글 스위치](/images/posts/하네스-엔지니어링/svg-4.svg)

### 피처 플래그란?

**Feature Flag**(기능 플래그)는 코드 배포와 기능 출시를 분리하는 기법이다. 코드는 이미 프로덕션에 배포되어 있지만, 특정 사용자 그룹에게만 기능을 활성화할 수 있다.

"Deploy dark"라고도 불리는 이 방식의 이점:
- 기능 출시 타이밍을 비즈니스 팀이 제어 가능
- 특정 사용자 세그먼트 대상 A/B 테스트
- 문제 발생 시 코드 롤백 없이 즉시 기능 비활성화
- 점진적 롤아웃으로 리스크 최소화

### Harness Feature Flags SDK 사용법

**JavaScript/Node.js:**

```javascript
import { initialize, variation } from '@harnessio/ff-javascript-client-sdk';

// SDK 초기화
const client = initialize('YOUR_SDK_KEY', {
  identifier: 'user123',
  attributes: {
    email: 'user@example.com',
    plan: 'premium',
    country: 'KR'
  }
});

// 플래그 평가
await client.waitForInitialization();
const showNewDashboard = variation('new_dashboard_ui', false);

if (showNewDashboard) {
  renderNewDashboard();
} else {
  renderLegacyDashboard();
}
```

**Java/Spring Boot:**

```java
@Service
public class FeatureService {

    @Autowired
    private CfClient cfClient;

    public boolean isNewCheckoutEnabled(String userId) {
        Target target = Target.builder()
            .identifier(userId)
            .name(userId)
            .attribute("plan", getUserPlan(userId))
            .build();

        return cfClient.boolVariation("new_checkout_flow", target, false);
    }
}
```

### 타겟팅 규칙 설정

Harness Feature Flags의 강점은 유연한 타겟팅 규칙이다.

```yaml
# 피처 플래그 설정 예시
feature_flag:
  identifier: new_checkout_flow
  name: New Checkout Flow
  kind: boolean
  defaultEnabled: false

  targeting_rules:
    # 베타 사용자 그룹 100% 활성화
    - clauses:
        - attribute: group
          op: equal
          values: ["beta_users"]
      serve: true

    # 프리미엄 플랜 사용자 20% 활성화 (점진적 롤아웃)
    - clauses:
        - attribute: plan
          op: equal
          values: ["premium"]
      serve:
        distribution:
          - variation: true
            weight: 20000  # 20%
          - variation: false
            weight: 80000  # 80%
```

### A/B 테스트 통합

피처 플래그와 분석 도구를 연동해 A/B 테스트 결과를 측정할 수 있다.

```javascript
// Amplitude/Mixpanel과 연동
const variant = variation('checkout_button_color', 'blue');

analytics.track('Checkout Initiated', {
  ff_checkout_button: variant,
  userId: currentUser.id
});
```

---

## 8. Cloud Cost Management — 클라우드 비용 통제

![클라우드 비용 관리(Cloud Cost Management) 아이콘](/images/posts/하네스-엔지니어링/svg-5.svg)

### 클라우드 비용의 현실

AWS, GCP, Azure를 사용하는 팀의 공통적인 고민: **"이번 달 클라우드 비용이 왜 이렇게 많이 나왔지?"** 서비스별, 팀별, 환경별 비용 분석이 안 되면 낭비를 막을 수 없다.

Harness Cloud Cost Management(CCM)은 이 문제를 구조적으로 해결한다.

### 비용 가시성 (Cost Visibility)

CCM은 클라우드 비용을 다양한 차원으로 분석할 수 있게 한다.

- **서비스별**: 어떤 마이크로서비스가 얼마를 쓰는가?
- **환경별**: 개발/스테이징/프로덕션 비용 비교
- **팀별**: 팀 레이블 기반 비용 할당
- **시간별 트렌드**: 이상 지출 감지

```yaml
# CCM 퍼스펙티브 설정
perspective:
  name: Backend Services
  rules:
    - viewConditions:
        - viewField:
            fieldId: label.k8s-app
            fieldName: k8s-app
            identifier: LABEL
          operator: IN
          values:
            - api-server
            - auth-service
            - payment-service
```

### 자동 추천 (AutoStopping & Recommendations)

**AutoStopping**: 비프로덕션 환경의 리소스를 트래픽이 없을 때 자동으로 중지한다. 개발/QA 환경에서 평균 70% 비용 절감 효과.

```yaml
autostopping_rule:
  name: Dev Cluster Auto-Stop
  cloud_provider: AWS
  resources:
    - type: ECS
      cluster: dev-cluster
  idle_time_minutes: 15
  warmup_time_seconds: 30
```

**Spot/Reserved Instance 추천**: 사용 패턴을 분석해 온디맨드 → 스팟/예약 인스턴스 전환을 추천한다.

### 예산 알림

```yaml
budget:
  name: Production Monthly Budget
  amount: 50000  # $50,000
  period: MONTHLY
  alerts:
    - threshold: 80  # 80% 도달 시 알림
      channels:
        - slack: "#cloud-costs"
        - email: "devops@company.com"
    - threshold: 100  # 예산 초과 시 알림
      channels:
        - pagerduty: "cloud-cost-oncall"
```

---

## 9. 보안 및 거버넌스

### OPA (Open Policy Agent) 정책

Harness는 OPA 정책을 파이프라인 실행 전/후에 강제할 수 있다. 조직의 배포 규칙을 코드로 관리할 수 있다.

```rego
# Rego 정책 예시: 프로덕션 배포는 승인 필수
package pipeline

deny[msg] {
  input.pipeline.stages[_].stage.spec.execution.steps[_].step.type == "K8sRollingDeploy"
  input.pipeline.stages[_].stage.spec.environment.identifier == "production"
  not has_approval_step
  msg := "Production deployments require an approval step"
}

has_approval_step {
  input.pipeline.stages[_].stage.spec.execution.steps[_].step.type == "HarnessApproval"
}
```

### RBAC (Role-Based Access Control)

Harness는 세밀한 권한 관리를 지원한다.

```yaml
role:
  name: Developer
  identifier: developer
  permissions:
    - core_pipeline_view
    - core_pipeline_execute
    - core_environment_view
  # 프로덕션 환경 직접 배포 불가
  resourceGroups:
    - non_production_resources
```

### 시크릿 관리

Harness는 자체 시크릿 매니저 외에 외부 시크릿 저장소와 통합된다.

- **HashiCorp Vault**: 동적 시크릿, 자동 갱신
- **AWS Secrets Manager**: AWS 네이티브 시크릿
- **GCP Secret Manager**: GCP 환경 지원
- **Azure Key Vault**: Azure 환경 지원

```yaml
# 파이프라인에서 시크릿 참조
- step:
    type: Run
    spec:
      envVariables:
        DB_PASSWORD: <+secrets.getValue("production_db_password")>
        API_KEY: <+secrets.getValue("external_api_key")>
```

### 감사 로그 (Audit Trail)

모든 액션(파이프라인 실행, 환경 변경, 시크릿 접근)이 감사 로그에 기록된다. 컴플라이언스 요구사항(SOC2, ISO 27001 등) 충족에 필수적이다.

---

## 10. 실전 팁 — Delegate 운영과 파이프라인 최적화

### Delegate 운영 베스트 프랙티스

**1. Delegate 고가용성 구성**

단일 Delegate는 SPOF(단일 장애점)가 된다. 최소 2개 이상의 Delegate를 운영하고, Delegate 셀렉터로 특정 작업을 특정 Delegate에 라우팅하라.

```yaml
# Delegate Selector 활용
- step:
    type: Run
    spec:
      delegateSelectors:
        - prod-delegate  # 특정 Delegate 그룹 지정
```

**2. Delegate 리소스 설정**

```yaml
# K8s Delegate 리소스 설정
resources:
  limits:
    cpu: "1"
    memory: 4Gi
  requests:
    cpu: 500m
    memory: 2Gi
```

**3. Delegate 버전 관리**

Harness는 자동 업그레이드를 지원하지만, 프로덕션 환경에서는 특정 버전을 고정하는 것을 권장한다.

```yaml
DELEGATE_IMAGE: harness/delegate:23.10.81202
AUTO_UPGRADE: "false"
```

### 파이프라인 최적화

**병렬 스테이지 실행:**

```yaml
stages:
  - parallel:
      - stage:
          name: Unit Tests
          # ...
      - stage:
          name: Lint
          # ...
      - stage:
          name: Security Scan
          # ...
  - stage:
      name: Build Docker Image
      # 위 모든 스테이지 완료 후 실행
```

**조건부 실행:**

```yaml
- step:
    name: Deploy to Prod
    when:
      condition: <+trigger.targetBranch> == "main"
      stageStatus: Success
```

**파이프라인 템플릿 활용:**

반복되는 파이프라인 패턴은 템플릿으로 만들어 재사용하라. 수십 개 마이크로서비스의 파이프라인을 하나의 템플릿으로 관리할 수 있다.

```yaml
template:
  name: Standard Build Template
  identifier: standard_build
  versionLabel: v1
  type: Stage
  spec:
    type: CI
    spec:
      cloneCodebase: true
      execution:
        steps:
          - step:
              type: Run
              name: Build
              spec:
                command: make build
          - step:
              type: Run
              name: Test
              spec:
                command: make test
```

### 트러블슈팅 가이드

**Delegate 연결 문제:**

```bash
# Delegate 로그 확인
kubectl logs -n harness-delegate deployment/harness-delegate -f

# Delegate 상태 확인
kubectl get pods -n harness-delegate

# 네트워크 연결 테스트
kubectl exec -n harness-delegate deploy/harness-delegate -- \
  curl -s https://app.harness.io/api/health
```

**파이프라인 실패 디버깅:**

1. 파이프라인 실행 페이지에서 실패한 스텝 선택
2. "View Logs" 클릭으로 상세 로그 확인
3. "Re-run from Failed Stage" 옵션으로 실패 지점부터 재실행

**흔한 오류와 해결책:**

| 오류 | 원인 | 해결책 |
|------|------|--------|
| `Delegate not available` | Delegate가 오프라인 또는 과부하 | Delegate 파드 상태 확인, 스케일 아웃 |
| `Secret not found` | 시크릿 참조 오류 또는 권한 부족 | 시크릿 이름, 스코프 확인 |
| `Image pull failed` | 컨테이너 레지스트리 인증 문제 | Connector 자격증명 업데이트 |
| `Timeout exceeded` | 빌드/배포 시간 초과 | timeout 값 증가, 병렬화 검토 |

---

## 11. 다른 CI/CD 도구와 비교 — 언제 Harness를 선택할지

### 주요 도구 비교

| 항목 | Harness | GitHub Actions | Jenkins | ArgoCD |
|------|---------|---------------|---------|--------|
| **설정 방법** | YAML + UI | YAML | Groovy | YAML |
| **학습 곡선** | 중간 | 낮음 | 높음 | 낮음 |
| **엔터프라이즈 기능** | 매우 강함 | 보통 | 플러그인 의존 | CD에 특화 |
| **비용 관리** | 내장 | 없음 | 없음 | 없음 |
| **피처 플래그** | 내장 | 없음 | 없음 | 없음 |
| **거버넌스** | OPA 내장 | 제한적 | 플러그인 필요 | 없음 |
| **가격** | 유료 (무료 티어 있음) | 사용량 기반 | 오픈소스 | 오픈소스 |

### Harness가 적합한 경우

- **대규모 엔터프라이즈**: 수십~수백 개의 마이크로서비스, 여러 팀, 멀티클라우드 환경
- **컴플라이언스 중요**: 금융, 의료, 정부 등 감사 및 거버넌스 요구사항이 엄격한 산업
- **비용 최적화 필요**: 클라우드 지출을 팀/서비스별로 추적하고 최적화하려는 조직
- **통합 플랫폼 선호**: CI, CD, 피처 플래그, 비용 관리를 하나의 도구로 관리하려는 팀
- **보안 요구사항**: Delegate 모델로 인바운드 연결 없이 온프레미스/프라이빗 클라우드 운영

### Harness가 맞지 않는 경우

- **소규모 팀 또는 단순한 배포**: GitHub Actions나 GitLab CI로 충분할 수 있다
- **오픈소스 요구**: Harness의 일부 기능은 유료다
- **높은 커스터마이징**: Jenkins처럼 거의 모든 것을 코드로 제어하고 싶다면 진입 장벽이 있다

---

## 마무리 — Harness와 함께하는 현대적 DevOps

Harness는 단순히 Jenkins를 대체하는 도구가 아니다. **소프트웨어 딜리버리 전체를 하나의 통합 플랫폼으로 관리**하는 패러다임 전환을 제안한다.

CI/CD 파이프라인 자동화로 시작해, GitOps로 인프라를 코드로 관리하고, Feature Flags로 안전하게 기능을 출시하며, Cloud Cost Management로 클라우드 지출을 최적화하는 모든 과정이 하나의 플랫폼 안에서 이루어진다.

도입 여부를 고민 중이라면, Harness의 **무료 티어**로 시작해보길 권한다. 14일 무료 체험 후에도 Harness Cloud 500 빌드 크레딧, Feature Flags 25,000 MAU, Developer 플랜이 무료로 제공된다.

핵심은 도구가 아니라 **"개발팀이 배포에 드는 인지적 부담을 얼마나 줄일 수 있는가"**다. Harness는 그 답을 플랫폼 레벨에서 제시하고 있다.

---

*참고 자료: [Harness 공식 문서](https://developer.harness.io), [Harness University](https://university.harness.io)*
