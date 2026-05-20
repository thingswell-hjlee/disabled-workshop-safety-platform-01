# Ubuntu Edge AI Server Install Package Specification

> **프로젝트**: AI기반 장애인직업재활시설 스마트안전시스템  
> **패키지 유형**: Ubuntu Online  
> **대상**: 프로덕션 Edge AI 서버 (NVIDIA GPU)  
> **문서 버전**: 1.0

---

## 1. 개요

NVIDIA GPU가 장착된 Ubuntu Edge AI 서버에 스마트안전시스템을 설치하기 위한 프로덕션 패키지입니다.  
DeepStream + TensorRT 기반 실시간 AI 추론이 가능하며, systemd 통합으로 자동 시작/복구를 지원합니다.

---

## 2. 대상 환경 (Target)

- **용도**: 프로덕션 Edge AI 서버
- **위치**: 장애인직업재활시설 현장
- **모드**: Full production (GPU 가속)

---

## 3. 사전 요구 사항 (Prerequisites)

| 항목 | 요구 사항 |
|------|-----------|
| OS | Ubuntu 22.04 LTS (Server/Desktop) |
| NVIDIA Driver | 535 이상 |
| CUDA | 12.x (Driver에 포함) |
| Docker | 24.x 이상 |
| NVIDIA Container Toolkit | 최신 버전 |
| RAM | 16GB 이상 (32GB 권장) |
| GPU | NVIDIA RTX 3060 이상 (8GB VRAM+) |
| 디스크 | 100GB SSD 여유 공간 |
| 네트워크 | 인터넷 연결 (Docker 이미지 pull) |

### NVIDIA 환경 확인 명령어

```bash
# GPU 드라이버 확인
nvidia-smi

# Docker NVIDIA 런타임 확인
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Docker 버전 확인
docker --version
docker compose version
```

---

## 4. 패키지 내용 (Package Contents)

### 4.1 핵심 파일

| 파일 | 설명 |
|------|------|
| `docker-compose.yml` | 기본 서비스 Compose 설정 |
| `docker-compose.gpu.yml` | NVIDIA GPU 오버라이드 설정 |
| `.env.example` | 환경 변수 템플릿 |
| `VERSION` | 버전 정보 |
| `RELEASE_NOTES.md` | 릴리즈 노트 |
| `CHECKSUMS.sha256` | 파일 무결성 해시 |
| `LICENSE` | 라이선스 |

### 4.2 스크립트 (Bash)

| 스크립트 | 설명 |
|----------|------|
| `scripts/install-online.sh` | 온라인 설치 (Docker 이미지 pull + 설정) |
| `scripts/install-offline.sh` | 오프라인 설치 (USB에서 이미지 로드) |
| `scripts/start.sh` | 서비스 시작 |
| `scripts/stop.sh` | 서비스 중지 |
| `scripts/update.sh` | 최신 버전으로 업데이트 |
| `scripts/rollback.sh` | 이전 버전으로 롤백 |
| `scripts/healthcheck.sh` | 헬스체크 (전체 시스템 상태 확인) |
| `scripts/collect-logs.sh` | 로그 수집 (디버깅용 아카이브 생성) |

### 4.3 설정 파일

| 파일/디렉토리 | 설명 |
|--------------|------|
| `config/source_list.yml` | 카메라/센서 소스 설정 |
| `config/thresholds.yml` | 이벤트 임계값 설정 |
| `config/roi/` | ROI (Region of Interest) 설정 |
| `config/dashboard.yml` | 대시보드 설정 |
| `config/mqtt.yml` | MQTT 브로커 설정 |
| `config/nginx/` | Nginx 리버스 프록시 설정 |

### 4.4 systemd 서비스 파일

| 파일 | 설명 |
|------|------|
| `systemd/thingswell-safety.service` | 메인 서비스 유닛 |
| `systemd/thingswell-safety-watchdog.service` | 워치독 서비스 |
| `systemd/thingswell-safety-watchdog.timer` | 워치독 타이머 (5분 간격) |

### 4.5 문서

| 파일 | 설명 |
|------|------|
| `docs/INSTALL_GUIDE.md` | 설치 가이드 |
| `docs/QUICK_START.md` | 빠른 시작 가이드 |
| `docs/GPU_SETUP.md` | GPU 설정 가이드 |
| `docs/TROUBLESHOOTING.md` | 문제 해결 가이드 |

---

## 5. 스크립트 동작 상세

### 5.1 install-online.sh

온라인 환경에서 초기 설치를 수행합니다.

**동작 순서:**
1. root 권한 확인
2. 사전 요구 사항 검증 (OS, Docker, NVIDIA Driver, GPU)
3. `.env.example` → `.env` 복사 및 기본값 설정
4. Docker 이미지 pull (`docker compose pull`)
5. 디렉토리 구조 생성 (`/opt/thingswell-safety/`)
6. 초기 데이터베이스 마이그레이션
7. systemd 서비스 등록 및 활성화
8. 방화벽 설정 (UFW)
9. 설치 완료 메시지 + 대시보드 URL 표시

```bash
# 실행 예시
sudo ./scripts/install-online.sh
```

### 5.2 install-offline.sh

USB 오프라인 패키지에서 Docker 이미지를 로드합니다.

**동작 순서:**
1. root 권한 확인
2. USB 마운트 경로 확인
3. 체크섬 검증 (`sha256sum -c`)
4. Docker 이미지 `.tar` 파일 로드 (`docker load`)
5. TensorRT 모델 파일 복사
6. `.env` 설정
7. 디렉토리 구조 생성
8. 초기 데이터베이스 마이그레이션
9. systemd 서비스 등록

```bash
# 실행 예시
sudo ./scripts/install-offline.sh --usb-path /media/usb/THINGSWELL_SAFETY_USB_v1.0.0
```

### 5.3 start.sh

모든 서비스를 시작합니다.

**동작 순서:**
1. `.env` 파일 존재 확인
2. NVIDIA GPU 접근 가능 여부 확인
3. `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d`
4. 헬스체크 대기 (최대 180초)
5. 서비스 상태 표시

```bash
# 실행 예시
sudo ./scripts/start.sh
```

### 5.4 stop.sh

모든 서비스를 중지합니다.

**동작 순서:**
1. `docker compose -f docker-compose.yml -f docker-compose.gpu.yml down`
2. 서비스 중지 확인
3. GPU 메모리 해제 확인

```bash
# 실행 예시
sudo ./scripts/stop.sh
```

### 5.5 update.sh

최신 버전으로 업데이트합니다.

**동작 순서:**
1. 현재 버전 백업 (rollback용)
2. 새 버전 이미지 pull
3. 서비스 중지
4. 데이터베이스 마이그레이션 (필요 시)
5. 설정 파일 병합 (변경 감지)
6. 서비스 재시작
7. 헬스체크 확인
8. 실패 시 자동 롤백

```bash
# 실행 예시
sudo ./scripts/update.sh
# 특정 버전으로 업데이트
sudo ./scripts/update.sh --version v1.1.0
```

### 5.6 rollback.sh

이전 버전으로 롤백합니다.

**동작 순서:**
1. 백업된 이전 버전 확인
2. 서비스 중지
3. 이전 버전 이미지로 전환
4. 데이터베이스 마이그레이션 롤백 (필요 시)
5. 설정 파일 복원
6. 서비스 재시작
7. 헬스체크 확인

```bash
# 실행 예시
sudo ./scripts/rollback.sh
# 특정 버전으로 롤백
sudo ./scripts/rollback.sh --version v1.0.0-rc.2
```

### 5.7 healthcheck.sh

전체 시스템 상태를 확인합니다.

**동작 순서:**
1. Docker 서비스 상태 확인
2. 각 컨테이너 헬스 상태 조회
3. GPU 상태 확인 (nvidia-smi)
4. 디스크 사용량 확인
5. 네트워크 연결 상태 (MQTT, DB)
6. AI 파이프라인 FPS 확인
7. 결과 요약 출력 (pass/fail)

```bash
# 실행 예시
./scripts/healthcheck.sh
# JSON 출력
./scripts/healthcheck.sh --format json
```

### 5.8 collect-logs.sh

디버깅용 로그를 수집합니다.

**동작 순서:**
1. Docker 컨테이너 로그 수집 (최근 24시간)
2. 시스템 로그 수집 (journalctl)
3. GPU 상태 스냅샷
4. 디스크/메모리 상태
5. 설정 파일 (민감 정보 마스킹)
6. `.tar.gz` 아카이브로 압축

```bash
# 실행 예시
sudo ./scripts/collect-logs.sh
# 출력: logs-thingswell-safety-20250115-143000.tar.gz
```

---

## 6. GPU 설정 (docker-compose.gpu.yml)

```yaml
version: '3.8'

services:
  deepstream-pipeline:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility,video
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu, compute, video]
    volumes:
      - ./models:/opt/nvidia/deepstream/models:ro
      - ./config/deepstream:/opt/nvidia/deepstream/config:ro
```

### GPU 리소스 할당

| 서비스 | GPU 사용 | VRAM 추정 |
|--------|----------|-----------|
| DeepStream Pipeline | ✅ 전용 | ~4-6GB |
| Dashboard Backend | ❌ CPU only | - |
| Dashboard UI | ❌ CPU only | - |
| MQTT Broker | ❌ CPU only | - |
| Database | ❌ CPU only | - |

---

## 7. systemd 서비스 통합

### 메인 서비스 (thingswell-safety.service)

```ini
[Unit]
Description=ThingsWell Safety Platform
After=docker.service nvidia-persistenced.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/thingswell-safety
ExecStart=/opt/thingswell-safety/scripts/start.sh
ExecStop=/opt/thingswell-safety/scripts/stop.sh
TimeoutStartSec=300
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
```

### 워치독 서비스 (thingswell-safety-watchdog.service)

```ini
[Unit]
Description=ThingsWell Safety Platform Watchdog
After=thingswell-safety.service

[Service]
Type=oneshot
ExecStart=/opt/thingswell-safety/scripts/healthcheck.sh --auto-restart
```

### 워치독 타이머 (thingswell-safety-watchdog.timer)

```ini
[Unit]
Description=ThingsWell Safety Platform Watchdog Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
AccuracySec=1min

[Install]
WantedBy=timers.target
```

### systemd 명령어

```bash
# 서비스 시작/중지/재시작
sudo systemctl start thingswell-safety
sudo systemctl stop thingswell-safety
sudo systemctl restart thingswell-safety

# 부팅 시 자동 시작 활성화
sudo systemctl enable thingswell-safety
sudo systemctl enable thingswell-safety-watchdog.timer

# 상태 확인
sudo systemctl status thingswell-safety
sudo journalctl -u thingswell-safety -f
```

---

## 8. 폴더 구조 (tar.gz 내부)

```
thingswell-safety-platform-ubuntu-online-v1.0.0/
├── VERSION
├── RELEASE_NOTES.md
├── CHECKSUMS.sha256
├── LICENSE
├── README.md
├── docker-compose.yml
├── docker-compose.gpu.yml
├── .env.example
├── scripts/
│   ├── install-online.sh
│   ├── install-offline.sh
│   ├── start.sh
│   ├── stop.sh
│   ├── update.sh
│   ├── rollback.sh
│   ├── healthcheck.sh
│   └── collect-logs.sh
├── config/
│   ├── source_list.yml
│   ├── thresholds.yml
│   ├── dashboard.yml
│   ├── mqtt.yml
│   ├── roi/
│   │   └── default.json
│   └── nginx/
│       ├── nginx.conf
│       └── ssl/
├── systemd/
│   ├── thingswell-safety.service
│   ├── thingswell-safety-watchdog.service
│   └── thingswell-safety-watchdog.timer
├── models/
│   └── .gitkeep  (모델은 별도 다운로드 또는 USB에서 복사)
└── docs/
    ├── INSTALL_GUIDE.md
    ├── QUICK_START.md
    ├── GPU_SETUP.md
    └── TROUBLESHOOTING.md
```

---

## 참고 문서

- [distribution-package-spec.md](./distribution-package-spec.md)
- [windows11-install-package-spec.md](./windows11-install-package-spec.md)
- [offline-usb-package-spec.md](./offline-usb-package-spec.md)
