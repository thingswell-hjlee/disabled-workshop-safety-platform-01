# USB Offline Package Specification

> **프로젝트**: AI기반 장애인직업재활시설 스마트안전시스템  
> **패키지 유형**: USB Offline  
> **대상**: 인터넷 미연결 현장  
> **문서 버전**: 1.0

---

## 1. 개요

인터넷 연결이 불가능한 현장에서 완전한 오프라인 설치를 지원하기 위한 USB 패키지입니다.  
Docker 이미지, TensorRT 모델, 설치 스크립트, 설정 파일 등 모든 구성 요소를 포함합니다.

---

## 2. USB 폴더 구조

```
THINGSWELL_SAFETY_USB_${VERSION}/
├── 00_README_FIRST/
│   ├── README.md                    # 빠른 시작 가이드 (한국어)
│   ├── QUICK_START_WIN11.md         # Windows 11 빠른 시작
│   ├── QUICK_START_UBUNTU.md        # Ubuntu 빠른 시작
│   └── CHECKSUMS_VERIFY.md          # 체크섬 검증 방법
│
├── 01_WINDOWS11/
│   ├── thingswell-safety-platform-win11-online-v1.0.0.zip
│   ├── install-offline.ps1          # 오프라인 설치 스크립트 (루트에 복사)
│   └── README.md
│
├── 02_UBUNTU_EDGE_SERVER/
│   ├── thingswell-safety-platform-ubuntu-online-v1.0.0.tar.gz
│   ├── install-offline.sh           # 오프라인 설치 스크립트 (루트에 복사)
│   └── README.md
│
├── 03_DOCKER_IMAGES/
│   ├── deepstream-pipeline-v1.0.0.tar       # DeepStream AI Pipeline
│   ├── dashboard-backend-v1.0.0.tar         # FastAPI Backend
│   ├── dashboard-ui-v1.0.0.tar              # React/Next.js Frontend
│   ├── mqtt-broker-v1.0.0.tar               # Mosquitto MQTT
│   ├── timescaledb-v1.0.0.tar               # TimescaleDB
│   ├── redis-v1.0.0.tar                     # Redis Cache
│   ├── nginx-proxy-v1.0.0.tar               # Nginx Reverse Proxy
│   ├── IMAGE_LIST.md                        # 이미지 목록 및 버전
│   └── load-all-images.sh                   # 전체 이미지 로드 스크립트
│
├── 04_MODELS/
│   ├── pgie/
│   │   ├── pgie_detector.engine             # Primary GIE (객체 탐지)
│   │   ├── pgie_config.txt                  # PGIE 설정
│   │   └── labels.txt                       # 클래스 라벨
│   ├── sgie/
│   │   ├── sgie_classifier.engine           # Secondary GIE (행동 인식)
│   │   ├── sgie_config.txt                  # SGIE 설정
│   │   └── labels.txt                       # 클래스 라벨
│   ├── MODEL_INFO.md                        # 모델 정보 (버전, 정확도)
│   └── COMPATIBILITY.md                     # GPU 호환성 정보
│
├── 05_CONFIG_TEMPLATE/
│   ├── .env.example                         # 환경 변수 템플릿
│   ├── source_list.yml                      # 카메라 소스 설정 예시
│   ├── thresholds.yml                       # 이벤트 임계값 설정
│   └── roi/
│       ├── default.json                     # 기본 ROI 설정
│       └── example_factory.json             # 공장 레이아웃 예시
│
├── 06_INSTALL_GUIDE/
│   ├── INSTALL_GUIDE_WIN11.md               # Windows 11 설치 매뉴얼
│   ├── INSTALL_GUIDE_UBUNTU.md              # Ubuntu 설치 매뉴얼
│   ├── INSTALL_GUIDE_WIN11.pdf              # PDF 버전
│   ├── INSTALL_GUIDE_UBUNTU.pdf             # PDF 버전
│   └── images/                              # 설치 가이드 스크린샷
│
├── 07_TEST_TOOLS/
│   ├── healthcheck.sh                       # 시스템 헬스체크
│   ├── healthcheck.ps1                      # Windows 헬스체크
│   ├── mqtt-test.sh                         # MQTT 연결 테스트
│   ├── mqtt-test.ps1                        # Windows MQTT 테스트
│   ├── gpio-test.sh                         # GPIO 경보 테스트
│   ├── camera-test.sh                       # 카메라 연결 테스트
│   └── README.md                            # 테스트 도구 사용법
│
├── 08_RELEASE_NOTES/
│   ├── RELEASE_NOTES.md                     # 릴리즈 노트
│   ├── CHANGELOG.md                         # 전체 변경 이력
│   └── KNOWN_ISSUES.md                      # 알려진 이슈
│
└── 09_CHECKSUMS/
    ├── CHECKSUMS.sha256                     # 전체 파일 SHA-256 해시
    ├── verify.sh                            # Linux 검증 스크립트
    └── verify.ps1                           # Windows 검증 스크립트
```

---

## 3. Docker 이미지 목록 및 크기

| # | 이미지 | 태그 | 추정 크기 | 설명 |
|---|--------|------|-----------|------|
| 1 | `thingswell/deepstream-pipeline` | v1.0.0 | ~4.0GB | DeepStream + TensorRT AI 파이프라인 |
| 2 | `thingswell/dashboard-backend` | v1.0.0 | ~500MB | FastAPI 기반 REST API 서버 |
| 3 | `thingswell/dashboard-ui` | v1.0.0 | ~300MB | React/Next.js 대시보드 프론트엔드 |
| 4 | `eclipse-mosquitto` | 2.0 | ~50MB | MQTT 메시지 브로커 |
| 5 | `timescale/timescaledb` | latest-pg15 | ~400MB | 시계열 데이터베이스 |
| 6 | `redis` | 7-alpine | ~100MB | 캐시/세션 저장소 |
| 7 | `nginx` | alpine | ~50MB | 리버스 프록시 |
| | | | **~5.4GB** | **합계 (압축 전)** |

### 이미지 저장 명령어

```bash
# 개별 이미지 저장
docker save thingswell/deepstream-pipeline:v1.0.0 -o deepstream-pipeline-v1.0.0.tar
docker save thingswell/dashboard-backend:v1.0.0 -o dashboard-backend-v1.0.0.tar

# 전체 이미지 저장 (build script에서 자동화)
./scripts/build-usb-offline-package.sh
```

---

## 4. 모델 패키지 내용

### 4.1 PGIE (Primary GIE) - 객체 탐지

| 파일 | 크기 | 설명 |
|------|------|------|
| `pgie_detector.engine` | ~200MB | TensorRT 최적화 객체 탐지 모델 |
| `pgie_config.txt` | ~2KB | DeepStream PGIE 설정 |
| `labels.txt` | ~1KB | 탐지 클래스: person, fire, smoke, vehicle 등 |

### 4.2 SGIE (Secondary GIE) - 행동 인식

| 파일 | 크기 | 설명 |
|------|------|------|
| `sgie_classifier.engine` | ~150MB | TensorRT 최적화 행동 인식 모델 |
| `sgie_config.txt` | ~2KB | DeepStream SGIE 설정 |
| `labels.txt` | ~1KB | 행동 클래스: fall, normal, running, loitering 등 |

### 4.3 GPU 호환성

| GPU | 지원 | 비고 |
|-----|------|------|
| RTX 3060 (8GB) | ✅ | 최소 사양 |
| RTX 3070 (8GB) | ✅ | 권장 |
| RTX 3080 (10GB) | ✅ | 권장 |
| RTX 4060 (8GB) | ✅ | 차세대 |
| RTX 4070+ | ✅ | 고성능 |
| Tesla T4 (16GB) | ✅ | 서버용 |

> ⚠️ **주의**: TensorRT `.engine` 파일은 GPU 아키텍처에 종속적입니다.  
> 다른 GPU 아키텍처 사용 시 모델 재빌드가 필요할 수 있습니다.

---

## 5. 설치 플로우 (Installation Flow)

### Ubuntu Edge AI Server

```
USB 삽입
  │
  ├─ 1. USB 마운트 확인
  │     $ sudo mount /dev/sdb1 /media/usb
  │
  ├─ 2. 체크섬 검증
  │     $ cd /media/usb/THINGSWELL_SAFETY_USB_v1.0.0/09_CHECKSUMS
  │     $ ./verify.sh
  │
  ├─ 3. Docker 이미지 로드
  │     $ cd ../03_DOCKER_IMAGES
  │     $ ./load-all-images.sh
  │     # (또는) docker load -i deepstream-pipeline-v1.0.0.tar
  │
  ├─ 4. 모델 복사
  │     $ sudo cp -r ../04_MODELS/* /opt/thingswell-safety/models/
  │
  ├─ 5. 패키지 설치
  │     $ cd ../02_UBUNTU_EDGE_SERVER
  │     $ sudo ./install-offline.sh --usb-path /media/usb/THINGSWELL_SAFETY_USB_v1.0.0
  │
  ├─ 6. 환경 설정
  │     $ sudo nano /opt/thingswell-safety/.env
  │     # 카메라 IP, 시설명, 알림 설정 등 변경
  │
  ├─ 7. 서비스 시작
  │     $ sudo systemctl start thingswell-safety
  │
  └─ 8. 헬스체크
        $ /opt/thingswell-safety/scripts/healthcheck.sh
```

### Windows 11 (Demo)

```
USB 삽입
  │
  ├─ 1. 09_CHECKSUMS\verify.ps1 실행 (체크섬 검증)
  │
  ├─ 2. 01_WINDOWS11 폴더에서 zip 압축 해제
  │
  ├─ 3. install-offline.ps1 실행
  │     > .\install-offline.ps1 -UsbPath "E:\THINGSWELL_SAFETY_USB_v1.0.0"
  │
  ├─ 4. Docker 이미지 자동 로드 (03_DOCKER_IMAGES 에서)
  │
  ├─ 5. 서비스 시작
  │     > .\scripts\start.ps1
  │
  └─ 6. 브라우저에서 대시보드 접속
        http://localhost:8080
```

---

## 6. 전체 USB 크기 추정

| 구성 요소 | 추정 크기 |
|-----------|-----------|
| 00_README_FIRST | ~100KB |
| 01_WINDOWS11 | ~50MB |
| 02_UBUNTU_EDGE_SERVER | ~80MB |
| 03_DOCKER_IMAGES | ~5.4GB |
| 04_MODELS | ~350MB |
| 05_CONFIG_TEMPLATE | ~50KB |
| 06_INSTALL_GUIDE | ~20MB |
| 07_TEST_TOOLS | ~500KB |
| 08_RELEASE_NOTES | ~100KB |
| 09_CHECKSUMS | ~50KB |
| **합계** | **~8-12GB** |

> 💡 실제 크기는 Docker 이미지 레이어 공유 및 압축 방식에 따라 변동됩니다.

---

## 7. USB 포맷 요구 사항

| 항목 | 요구 사항 | 이유 |
|------|-----------|------|
| **파일 시스템** | exFAT | 4GB 이상 파일 지원 (Docker 이미지) |
| **용량** | 32GB 이상 | ~12GB 데이터 + 여유 공간 |
| **인터페이스** | USB 3.0 이상 | 대용량 파일 전송 속도 |
| **라벨** | `THINGSWELL_v1_0_0` | 식별 용이성 |

### USB 포맷 방법

```bash
# Linux
sudo mkfs.exfat -n "THINGSWELL_v1_0_0" /dev/sdb1

# Windows (관리자 PowerShell)
Format-Volume -DriveLetter E -FileSystem exFAT -NewFileSystemLabel "THINGSWELL_v1_0_0"
```

### FAT32 vs exFAT

| 파일 시스템 | 최대 파일 크기 | 적합성 |
|------------|---------------|--------|
| FAT32 | 4GB | ❌ Docker 이미지 크기 초과 |
| exFAT | 16EB | ✅ 대용량 파일 지원 |
| NTFS | 16TB | ⚠️ Linux 쓰기 호환성 이슈 가능 |

---

## 8. 빌드 스크립트 (USB 패키지 생성)

```bash
#!/bin/bash
# scripts/build-usb-offline-package.sh

VERSION=${1:-$(cat VERSION)}
USB_DIR="THINGSWELL_SAFETY_USB_${VERSION}"

# 1. 디렉토리 구조 생성
mkdir -p "${USB_DIR}"/{00_README_FIRST,01_WINDOWS11,02_UBUNTU_EDGE_SERVER}
mkdir -p "${USB_DIR}"/{03_DOCKER_IMAGES,04_MODELS/pgie,04_MODELS/sgie}
mkdir -p "${USB_DIR}"/{05_CONFIG_TEMPLATE/roi,06_INSTALL_GUIDE/images}
mkdir -p "${USB_DIR}"/{07_TEST_TOOLS,08_RELEASE_NOTES,09_CHECKSUMS}

# 2. Docker 이미지 저장
docker save thingswell/deepstream-pipeline:${VERSION} \
  -o "${USB_DIR}/03_DOCKER_IMAGES/deepstream-pipeline-${VERSION}.tar"
# ... (나머지 이미지)

# 3. 체크섬 생성
cd "${USB_DIR}"
find . -type f ! -path "./09_CHECKSUMS/*" -exec sha256sum {} \; > 09_CHECKSUMS/CHECKSUMS.sha256
```

---

## 참고 문서

- [distribution-package-spec.md](./distribution-package-spec.md)
- [windows11-install-package-spec.md](./windows11-install-package-spec.md)
- [ubuntu-install-package-spec.md](./ubuntu-install-package-spec.md)
- [reliability-test-package-spec.md](./reliability-test-package-spec.md)
