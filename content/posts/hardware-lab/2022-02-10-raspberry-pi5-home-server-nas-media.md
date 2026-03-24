---
title: "Raspberry Pi 5로 홈 서버 구축하기 — NAS + 미디어 서버 완전 정복"
date: 2022-02-10T08:00:00+09:00
lastmod: 2022-02-17T08:00:00+09:00
description: "Raspberry Pi 5로 Samba NAS, Jellyfin 미디어 서버, Pi-hole DNS, WireGuard VPN을 한 번에 구축하는 완전 가이드. 8GB 모델과 NVMe SSD 조합으로 진짜 쓸 만한 홈 서버를 만드는 법."
slug: "raspberry-pi5-home-server-nas-media"
categories: ["hardware-lab"]
tags: ["Raspberry Pi 5", "홈서버", "NAS", "Jellyfin", "자작서버"]
series: []
draft: false
---

클라우드 스토리지 요금이 또 올랐습니다. 구글 드라이브, iCloud, Dropbox... 매달 나가는 돈을 합산해보니 연간 꽤 적지 않은 금액이더군요. 13년 차 엔지니어로서 "이거 내가 직접 만들면 안 되나?" 라는 생각이 든 건 당연한 수순이었습니다.

Raspberry Pi 5가 나왔을 때부터 눈여겨봤습니다. 이전 세대와 달리 PCIe 인터페이스를 지원하고, 성능이 3배 가까이 향상됐거든요. 이번 글에서는 Raspberry Pi 5 한 대로 NAS, 미디어 서버, DNS 광고 차단기, VPN 서버를 모두 구축하는 방법을 정리합니다.

## 왜 Raspberry Pi 5인가

2026년 기준으로 홈 서버용 SBC(Single Board Computer) 선택지는 다양합니다. 오드로이드, 락칩 기반 보드들도 있지만, 커뮤니티 지원과 문서화 수준에서 Raspberry Pi를 따라올 제품이 없습니다.

Raspberry Pi 5의 핵심 스펙을 정리하면 다음과 같습니다.

- **프로세서**: Broadcom BCM2712, Cortex-A76 쿼드코어 2.4GHz
- **RAM**: 4GB / 8GB (홈 서버는 8GB 추천)
- **스토리지 인터페이스**: PCIe 2.0 x1 (M.2 HAT+를 통해 NVMe 연결)
- **네트워크**: 기가비트 이더넷
- **소비 전력**: 풀로드 시 약 12W

전력 소비가 낮다는 점이 핵심입니다. 연중무휴 24시간 켜두는 서버라면 전기세가 중요한데, Pi 5는 일반 NAS 제품 대비 전력을 30~40% 절약할 수 있습니다.

## 필요한 하드웨어

| 품목 | 추천 사양 | 가격 (대략) |
|------|----------|------------|
| Raspberry Pi 5 | 8GB 모델 | 약 9만원 |
| M.2 HAT+ | 공식 M.2 HAT+ | 약 1.5만원 |
| NVMe SSD | Samsung 980 1TB | 약 8만원 |
| 공식 전원 어댑터 | 27W USB-C PD | 약 1.5만원 |
| 케이스 | Argon NEO 5 등 | 약 3만원 |
| microSD | 32GB (부트용) | 약 1만원 |

총 25만원 내외로 준비 가능합니다. 상업용 1TB NAS 제품 가격과 비슷하지만, 확장성과 커스터마이징 면에서 비교가 안 됩니다.

## 전체 아키텍처

![Raspberry Pi 5 홈 서버 아키텍처](/images/raspberry-pi5-home-server-architecture.svg)

외부 인터넷에서 들어오는 트래픽은 공유기를 거쳐 Pi 5로 전달됩니다. Pi 5 위에서 Docker 컨테이너들이 각자의 역할을 담당하고, Pi-hole이 DNS 레벨에서 광고를 차단합니다.

## OS 설치 및 기본 설정

### Ubuntu Server 24.04 LTS 설치

Raspberry Pi Imager를 사용하면 간단합니다.

```bash
# Raspberry Pi Imager 다운로드 후
# Ubuntu Server 24.04 LTS (64-bit) 선택
# 고급 옵션에서 SSH 활성화, 사용자명/비밀번호 설정
```

microSD에 이미지를 굽고 부팅하면 됩니다. NVMe SSD를 M.2 HAT+에 장착한 뒤, 나중에 부팅 순서를 바꿔서 SSD로 부팅하도록 설정합니다.

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Docker Compose v2 확인
docker compose version
```

### NVMe SSD를 루트로 이동

```bash
# 현재 microSD의 내용을 SSD로 복사
sudo rsync -axv / /mnt/ssd/

# /boot/firmware/cmdline.txt 수정
# root=PARTUUID=... 부분을 SSD의 PARTUUID로 변경
sudo blkid /dev/nvme0n1p2
```

## Samba NAS 설정

가장 기본적인 파일 공유 서버입니다. Docker Compose로 구성합니다.

```yaml
# docker-compose.yml
version: '3.8'

services:
  samba:
    image: dperson/samba:latest
    restart: always
    ports:
      - "139:139"
      - "445:445"
    volumes:
      - /data/nas:/mount/nas
    environment:
      - USERID=1000
      - GROUPID=1000
    command: >
      -u "pi;password123"
      -s "NAS;/mount/nas;yes;no;no;pi"
      -g "log level = 2"
```

```bash
docker compose up -d
```

Windows에서는 `\\192.168.1.xxx\NAS`로, macOS에서는 Finder → 이동 → 서버 연결 → `smb://192.168.1.xxx`로 접근합니다.

## Jellyfin 미디어 서버

Netflix 같은 UI로 개인 미디어를 스트리밍할 수 있습니다.

```yaml
  jellyfin:
    image: jellyfin/jellyfin:latest
    restart: always
    ports:
      - "8096:8096"
    volumes:
      - /data/jellyfin/config:/config
      - /data/jellyfin/cache:/cache
      - /data/media:/media:ro
    environment:
      - JELLYFIN_PublishedServerUrl=http://192.168.1.xxx:8096
```

`http://192.168.1.xxx:8096`으로 접근해서 초기 설정을 진행합니다. 미디어 폴더를 지정하면 자동으로 메타데이터(포스터, 줄거리 등)를 긁어옵니다.

Pi 5의 성능이면 1080p 스트리밍은 무리 없이 처리됩니다. 4K 트랜스코딩은 버벅일 수 있으니, 가능하면 Direct Play 형식으로 인코딩된 파일을 사용하는 것이 좋습니다.

## Pi-hole DNS 광고 차단기

DNS 레벨에서 광고를 차단하므로 앱, TV, 게임기 등 모든 기기에 효과가 있습니다.

```yaml
  pihole:
    image: pihole/pihole:latest
    restart: always
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "8080:80"
    volumes:
      - /data/pihole/etc-pihole:/etc/pihole
      - /data/pihole/etc-dnsmasq.d:/etc/dnsmasq.d
    environment:
      - TZ=Asia/Seoul
      - WEBPASSWORD=your_password_here
      - FTLCONF_LOCAL_IPV4=192.168.1.xxx
```

설치 후 공유기의 DNS 서버를 Pi 5의 IP로 변경하면 전체 네트워크에 적용됩니다. 보통 광고 차단율이 20~30%에 달합니다.

## WireGuard VPN

외부에서 집 네트워크에 안전하게 접속하기 위한 VPN입니다.

```yaml
  wireguard:
    image: linuxserver/wireguard:latest
    restart: always
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    ports:
      - "51820:51820/udp"
    volumes:
      - /data/wireguard/config:/config
      - /lib/modules:/lib/modules:ro
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Asia/Seoul
      - SERVERURL=your.ddns.address
      - PEERS=phone,laptop,tablet
```

`PEERS`에 연결할 기기 이름을 나열하면, `/data/wireguard/config/peer_phone/` 폴더에 QR 코드와 설정 파일이 생성됩니다. 스마트폰에서 WireGuard 앱으로 QR 코드를 스캔하면 바로 연결됩니다.

## Portainer + Grafana 모니터링

```yaml
  portainer:
    image: portainer/portainer-ce:latest
    restart: always
    ports:
      - "9000:9000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /data/portainer:/data
```

Portainer는 웹 UI에서 Docker 컨테이너를 관리할 수 있게 해줍니다. 터미널 없이도 컨테이너 시작/중지, 로그 확인이 가능합니다.

## DDNS 설정 (외부 접속)

집 IP는 대부분 유동 IP이므로 DDNS(Dynamic DNS)가 필요합니다. DuckDNS를 무료로 사용할 수 있습니다.

```bash
# crontab -e
*/5 * * * * curl -s "https://www.duckdns.org/update?domains=YOURNAME&token=YOUR_TOKEN&ip=" > /tmp/duck.log 2>&1
```

공유기에서 포트 포워딩으로 51820(WireGuard), 443(HTTPS) 등을 Pi 5로 연결합니다.

## 운영 팁

**백업은 필수입니다.** NAS 데이터는 3-2-1 규칙을 따르는 것이 좋습니다. 원본 1개, 로컬 백업 1개, 외부(클라우드) 백업 1개. rclone을 사용하면 B2나 구글 드라이브로 자동 백업 설정이 가능합니다.

```bash
# rclone 설치 후 백업 스크립트
rclone sync /data/nas remote:backup-bucket --log-file=/var/log/rclone.log
```

**전력 차단 대비**도 중요합니다. 갑자기 전원이 나가면 파일 시스템이 손상될 수 있습니다. 소형 UPS를 달아두면 안전합니다. 5만원대 제품으로도 충분합니다.

**온도 관리**도 신경 써야 합니다. Pi 5는 공식 액티브 쿨러나 써드파티 케이스(Argon NEO 5 등)를 사용하면 장시간 안정적으로 운영 가능합니다.

## 실제 운영 후기

저는 약 6개월째 이 구성으로 홈 서버를 운영 중입니다. 클라우드 스토리지 비용을 완전히 제거했고, 집 어디서나 미디어를 스트리밍하고, 스마트폰에서도 VPN을 통해 집 NAS에 접근합니다. 가끔 업데이트나 재시작 외에 특별한 문제는 없었습니다.

"직접 만드는 서버" 라는 말에 겁먹을 필요가 없습니다. Docker Compose 파일 몇 개만 이해하면 됩니다. 처음 셋업에 반나절, 이후 유지보수는 한 달에 1시간 미만입니다.

클라우드 요금 고민 중이시라면 시작해보시기 바랍니다.
