---
title: "Kubernetes 입문 2026 — 컨테이너 오케스트레이션 처음 시작하기"
date: 2024-11-15T10:17:00+09:00
lastmod: 2024-11-21T10:17:00+09:00
description: "Kubernetes를 처음 시작하는 분을 위한 입문 가이드입니다. Pod, Service, Deployment 핵심 개념부터 minikube 실습, Docker 연동, kubectl 기본 명령까지 단계별로 정리합니다."
slug: "kubernetes-beginner-guide-2026"
categories: ["software-dev"]
tags: ["Kubernetes", "컨테이너", "오케스트레이션", "DevOps", "minikube"]
featureimage: "/images/kubernetes-beginner-guide-2026.svg"
series: []
draft: false
---

Docker로 컨테이너를 만드는 것은 어렵지 않습니다. 하지만 그 컨테이너가 100개, 1,000개가 되면 이야기가 달라집니다. 어느 서버에 올릴지, 장애가 나면 자동으로 재시작할지, 트래픽이 몰릴 때 자동으로 늘릴지 — 이런 문제를 다루는 것이 컨테이너 오케스트레이션입니다. Kubernetes(K8s)는 그 표준으로 자리 잡은 오픈소스 플랫폼입니다. 2026년 현재 AWS EKS, Google GKE, Azure AKS 모두 K8s를 기반으로 하고, 사실상 클라우드 네이티브 인프라의 공통 언어가 됐습니다.

![Kubernetes 클러스터 구조](/images/kubernetes-beginner-guide-2026.svg)

## Kubernetes가 해결하는 문제

Docker만 사용할 때의 한계를 먼저 생각해보겠습니다.

- 컨테이너가 죽으면 수동으로 재시작해야 합니다
- 여러 서버에 컨테이너를 분산하는 것이 수동 작업입니다
- 트래픽이 늘면 컨테이너 수를 수동으로 늘려야 합니다
- 배포 중 다운타임이 발생합니다
- 서비스 간 네트워크 연결이 복잡합니다

Kubernetes는 이 문제들을 자동화합니다. "nginx 컨테이너 3개를 항상 실행 상태로 유지하라"고 선언하면, 하나가 죽어도 K8s가 자동으로 새 컨테이너를 띄웁니다. 배포할 때도 기존 컨테이너를 하나씩 교체해서 다운타임 없이 업데이트합니다.

## 클러스터 구조 이해하기

K8s 클러스터는 크게 두 부분으로 나뉩니다.

**Control Plane (마스터 노드)**

클러스터의 두뇌입니다. 사용자의 요청을 받고, 어떤 워커 노드에 무엇을 실행할지 결정합니다.

- **API Server**: 모든 요청의 입구. `kubectl` 명령이 여기로 들어옵니다
- **etcd**: 클러스터 전체 상태를 저장하는 분산 키-값 저장소
- **Scheduler**: 새 Pod를 어느 노드에 올릴지 결정
- **Controller Manager**: 실제 상태와 원하는 상태의 차이를 감지하고 조정

**Worker Node (워커 노드)**

실제 컨테이너가 실행되는 서버입니다.

- **kubelet**: 각 노드의 에이전트. Control Plane의 지시를 받아 컨테이너를 관리
- **kube-proxy**: 네트워크 규칙을 관리해서 Service가 동작하게 합니다
- **Container Runtime**: 실제 컨테이너를 실행하는 엔진 (containerd, CRI-O 등)

## minikube로 로컬 실습 환경 구성

운영 K8s 클러스터를 바로 쓰기 전에, 로컬에서 minikube로 연습하는 것이 좋습니다. minikube는 단일 노드 K8s 클러스터를 로컬 컴퓨터에 실행합니다.

**설치 (macOS)**

```bash
# Homebrew로 minikube 설치
brew install minikube

# kubectl 설치 (K8s 조작 CLI)
brew install kubectl

# minikube 시작
minikube start --driver=docker

# 상태 확인
minikube status
kubectl cluster-info
```

**설치 (Ubuntu/Debian)**

```bash
# kubectl 설치
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# minikube 설치
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Docker driver로 시작
minikube start --driver=docker
```

minikube가 시작되면 `kubectl`이 자동으로 이 클러스터를 바라보도록 설정됩니다.

## 핵심 리소스 1 — Pod

Pod는 K8s에서 배포의 가장 작은 단위입니다. 하나 이상의 컨테이너가 묶인 단위로, 같은 Pod 안의 컨테이너는 네트워크와 스토리지를 공유합니다.

```yaml
# pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: nginx
spec:
  containers:
    - name: nginx
      image: nginx:1.25
      ports:
        - containerPort: 80
      resources:
        requests:
          memory: "64Mi"
          cpu: "250m"
        limits:
          memory: "128Mi"
          cpu: "500m"
```

```bash
# Pod 생성
kubectl apply -f pod.yaml

# Pod 목록 확인
kubectl get pods

# Pod 상세 정보
kubectl describe pod nginx-pod

# Pod 로그 확인
kubectl logs nginx-pod

# Pod 내부 접속
kubectl exec -it nginx-pod -- /bin/bash

# Pod 삭제
kubectl delete pod nginx-pod
```

실무에서 Pod를 직접 생성하는 경우는 드뭅니다. 대부분 Deployment를 통해 Pod를 관리합니다. Pod를 직접 생성하면 죽었을 때 자동으로 재시작되지 않기 때문입니다.

## 핵심 리소스 2 — Deployment

Deployment는 Pod를 선언적으로 관리합니다. "nginx Pod를 3개 실행 상태로 유지하라"고 선언하면, Pod가 하나 죽어도 K8s가 자동으로 새 Pod를 띄웁니다. 이미지 업데이트도 무중단으로 처리합니다.

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3            # Pod 개수 선언
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:1.25
          ports:
            - containerPort: 80
          readinessProbe:    # 준비 완료 확인
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
          livenessProbe:     # 살아있는지 확인
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 15
            periodSeconds: 20
```

```bash
# Deployment 생성
kubectl apply -f deployment.yaml

# Deployment 확인
kubectl get deployments
kubectl get pods  # nginx-deployment-xxxxx 형태로 3개 생성됨

# 이미지 업데이트 (롤링 업데이트)
kubectl set image deployment/nginx-deployment nginx=nginx:1.26

# 업데이트 진행 상황 확인
kubectl rollout status deployment/nginx-deployment

# 이전 버전으로 롤백
kubectl rollout undo deployment/nginx-deployment

# Pod 개수 조정 (스케일링)
kubectl scale deployment nginx-deployment --replicas=5
```

`readinessProbe`와 `livenessProbe`는 실무에서 반드시 설정해야 합니다. readinessProbe가 있어야 새 Pod가 실제로 요청을 받을 준비가 됐을 때만 트래픽을 받습니다. livenessProbe는 Pod가 정상 동작 중인지 주기적으로 확인해서, 응답하지 않으면 자동으로 재시작합니다.

## 핵심 리소스 3 — Service

Pod는 생성될 때마다 IP가 바뀝니다. Service는 Pod들 앞에 고정된 엔드포인트를 제공하고, 요청을 분산합니다.

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx           # 이 레이블을 가진 Pod들로 트래픽 분산
  ports:
    - protocol: TCP
      port: 80           # Service가 노출하는 포트
      targetPort: 80     # Pod의 포트
  type: ClusterIP        # 클러스터 내부에서만 접근 가능
```

Service type에 따라 접근 방식이 달라집니다.

| 타입 | 설명 | 사용 사례 |
|------|------|-----------|
| ClusterIP | 클러스터 내부에서만 접근 가능 | 마이크로서비스 간 통신 |
| NodePort | 각 노드의 특정 포트로 외부 접근 | 개발/테스트 환경 |
| LoadBalancer | 클라우드 로드밸런서 자동 생성 | 프로덕션 외부 노출 |
| ExternalName | 외부 DNS 이름으로 매핑 | 외부 서비스 연결 |

```bash
# Service 생성
kubectl apply -f service.yaml

# Service 목록 확인
kubectl get services

# minikube에서 NodePort 서비스 접근 URL 확인
minikube service nginx-service --url

# 포트 포워딩으로 로컬에서 접근
kubectl port-forward service/nginx-service 8080:80
# http://localhost:8080 으로 접근 가능
```

## ConfigMap과 Secret으로 설정 분리

컨테이너 이미지에 설정값을 하드코딩하면 환경마다 다른 이미지가 필요합니다. ConfigMap과 Secret으로 설정을 분리하면 이미지는 하나로 유지하고, 환경마다 다른 설정을 주입할 수 있습니다.

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: "production"
  LOG_LEVEL: "info"
  DATABASE_HOST: "db-service"

---
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  DATABASE_PASSWORD: cGFzc3dvcmQxMjM=  # base64 인코딩
  API_KEY: c2VjcmV0a2V5MTIz
```

```bash
# Secret 생성 (직접 base64 인코딩 없이)
kubectl create secret generic app-secret \
  --from-literal=DATABASE_PASSWORD=password123 \
  --from-literal=API_KEY=secretkey123
```

```yaml
# Deployment에서 ConfigMap/Secret 사용
spec:
  containers:
    - name: app
      image: myapp:latest
      envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secret
```

## Ingress로 HTTP 라우팅

LoadBalancer Service를 여러 개 만들면 클라우드 로드밸런서 비용이 늘어납니다. Ingress는 하나의 진입점에서 URL 경로나 도메인으로 여러 Service에 트래픽을 분배합니다.

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 8080
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 80
  tls:
    - hosts:
        - myapp.example.com
      secretName: tls-secret
```

minikube에서 Ingress를 사용하려면 addon을 활성화합니다.

```bash
minikube addons enable ingress
kubectl apply -f ingress.yaml
kubectl get ingress
```

## 자주 쓰는 kubectl 명령 모음

```bash
# 리소스 조회
kubectl get pods -n namespace-name         # 특정 네임스페이스의 Pod
kubectl get all                            # 모든 리소스 한 번에
kubectl get pods -o wide                   # 노드 정보 포함
kubectl get pods --watch                   # 실시간 상태 변화 모니터링

# 상세 정보와 이벤트 확인
kubectl describe pod pod-name
kubectl describe deployment deployment-name

# 로그 확인
kubectl logs pod-name -f                   # 실시간 로그
kubectl logs pod-name --previous           # 이전 컨테이너 로그 (재시작 후)
kubectl logs deployment/nginx-deployment   # Deployment 전체 로그

# 디버깅
kubectl exec -it pod-name -- /bin/sh       # 컨테이너 접속
kubectl top pods                           # CPU/메모리 사용량 (metrics-server 필요)
kubectl events --sort-by=.lastTimestamp    # 최근 이벤트 확인

# 네임스페이스
kubectl create namespace myapp
kubectl get pods -n kube-system            # 시스템 Pod 확인
kubectl config set-context --current --namespace=myapp  # 기본 네임스페이스 변경
```

## Horizontal Pod Autoscaler로 자동 스케일링

트래픽에 따라 Pod 수를 자동으로 조절합니다.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nginx-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nginx-deployment
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

CPU 사용률이 70%를 넘으면 Pod를 늘리고, 낮아지면 줄입니다. 최소 2개, 최대 10개 사이에서 조절합니다.

## 다음 단계

K8s 입문을 마쳤다면 다음 주제로 넘어갈 수 있습니다.

- **Helm**: K8s 애플리케이션 패키지 매니저. 복잡한 yaml을 템플릿으로 관리
- **Kustomize**: 환경별 yaml 차이를 overlay로 관리. kubectl에 내장
- **Persistent Volume**: 데이터베이스처럼 데이터를 영구적으로 저장해야 할 때
- **StatefulSet**: 데이터베이스처럼 상태가 있는 애플리케이션 배포
- **Network Policy**: Pod 간 네트워크 트래픽 제어
- **RBAC**: 사용자/서비스 계정 권한 관리

K8s는 처음에 개념이 많아서 복잡해 보입니다. 하지만 핵심은 단순합니다. "원하는 상태를 선언하면 K8s가 그 상태를 유지한다." 이 철학을 기억하면서 Pod → Deployment → Service 순서로 익혀나가면 됩니다. minikube로 실제로 명령을 치고, `kubectl describe`로 무슨 일이 일어나는지 확인하는 것이 가장 빠른 학습 방법입니다.
