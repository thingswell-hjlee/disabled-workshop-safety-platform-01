# Distribution Package Specifications

> **프로젝트**: AI기반 장애인직업재활시설 스마트안전시스템  
> **대상 릴리즈**: Platform 1.0  
> **문서 버전**: 1.0

---

## 1. 패키지 유형 및 대상

| 패키지 유형 | 대상 사용자 | 용도 | 네트워크 요구 |
|-------------|------------|------|--------------|
| Win11 Online | 개발팀, 데모 담당자 | 내부 시험/데모 | 인터넷 필요 (Docker pull) |
| Ubuntu Online | 현장 엔지니어 | 프로덕션 Edge AI 서버 설치 | 인터넷 필요 (Docker pull) |
| USB Offline | 현장 엔지니어 (오프라인) | 인터넷 없는 현장 설치 | 불필요 |
| Reliability Test | QA팀 | 72시간 신뢰성 시험 | 선택적 |
| Customer Delivery | 고객/납품 | 최종 납품 | 불필요 |

---

## 2. 공통 포함 파일 (All Packages)

모든 배포 패키지에 반드시 포함되는 공통 파일:

| 파일명 | 설명 |
|--------|------|
| `VERSION` | 버전 정보 (예: `1.0.0`) |
| `RELEASE_NOTES.md` | 릴리즈 노트 (변경사항, 신규 기능, 버그 수정, 알려진 이슈) |
| `CHECKSUMS.sha256` | 패키지 내 주요 파일의 SHA-256 해시값 |
| `LICENSE` | 라이선스 정보 |

### VERSION 파일 형식

```
1.0.0
```

### CHECKSUMS.sha256 형식

```
e3b0c44298fc1c149afbf4c8996fb924...  docker-compose.yml
a7ffc6f8bf1ed76651c14756a061d662...  .env.example
```

---

## 3. 패키지별 콘텐츠 명세

### 3.1 Win11 Online Package

| 구성 요소 | 파일/디렉토리 | 설명 |
|-----------|-------------|------|
| Compose 설정 | `docker-compose.windows.yml` | Windows Docker Desktop용 |
| 환경 설정 | `.env.example` | 환경 변수 템플릿 |
| 설치 스크립트 | `scripts/*.ps1` | PowerShell 스크립트 7종 |
| 설정 템플릿 | `config/` | 설정 파일 템플릿 |
| 문서 | `docs/` | 설치 가이드, README |

### 3.2 Ubuntu Online Package

| 구성 요소 | 파일/디렉토리 | 설명 |
|-----------|-------------|------|
| Compose 설정 | `docker-compose.yml` | 기본 compose |
| GPU Compose | `docker-compose.gpu.yml` | NVIDIA GPU 설정 |
| 환경 설정 | `.env.example` | 환경 변수 템플릿 |
| 설치 스크립트 | `scripts/*.sh` | Bash 스크립트 8종 |
| 설정 템플릿 | `config/` | 설정 파일 템플릿 |
| systemd | `systemd/` | 서비스 유닛 파일 |
| 문서 | `docs/` | 설치 가이드, README |

### 3.3 USB Offline Package

| 구성 요소 | 파일/디렉토리 | 설명 |
|-----------|-------------|------|
| Windows 패키지 | `01_WINDOWS11/` | Win11 전체 패키지 + 오프라인 설치기 |
| Ubuntu 패키지 | `02_UBUNTU_EDGE_SERVER/` | Ubuntu 전체 패키지 + 오프라인 설치기 |
| Docker 이미지 | `03_DOCKER_IMAGES/` | `docker save` .tar 파일 |
| AI 모델 | `04_MODELS/` | TensorRT .engine 파일 |
| 설정 템플릿 | `05_CONFIG_TEMPLATE/` | 환경 설정 템플릿 |
| 설치 가이드 | `06_INSTALL_GUIDE/` | 설치 매뉴얼 (PDF/MD) |
| 테스트 도구 | `07_TEST_TOOLS/` | 설치 후 검증 도구 |
| 릴리즈 노트 | `08_RELEASE_NOTES/` | 변경 사항 |
| 체크섬 | `09_CHECKSUMS/` | 무결성 검증 |

### 3.4 Reliability Test Package

| 구성 요소 | 파일/디렉토리 | 설명 |
|-----------|-------------|------|
| Ubuntu 패키지 | (ubuntu-online 전체 포함) | 기본 프로덕션 패키지 |
| 테스트 스크립트 | `test-scripts/` | 72시간 테스트 자동화 |
| 모니터링 | `monitoring/` | 메트릭 수집 스크립트 |
| 이벤트 주입 | `event-injection/` | 시뮬레이션 도구 |
| 리포트 템플릿 | `report-templates/` | 결과 리포트 생성 |

### 3.5 Customer Delivery Package

| 구성 요소 | 파일/디렉토리 | 설명 |
|-----------|-------------|------|
| USB Offline | (usb-offline 전체 포함) | 오프라인 설치 패키지 |
| 인수시험 문서 | `acceptance-test/` | 인수시험 절차서, 체크리스트 |
| 납품 문서 | `delivery-docs/` | 납품확인서, 매뉴얼 |
| 교육 자료 | `training/` | 사용자 교육 자료 |

---

## 4. 파일 크기 추정

| 패키지 | 추정 크기 | 비고 |
|--------|-----------|------|
| Win11 Online | ~50MB | 스크립트 + 설정 (이미지 미포함) |
| Ubuntu Online | ~80MB | 스크립트 + 설정 + systemd (이미지 미포함) |
| USB Offline | ~8-12GB | Docker 이미지 + TensorRT 모델 포함 |
| Reliability Test | ~100MB | Ubuntu 패키지 + 테스트 도구 |
| Customer Delivery | ~12-15GB | USB + 납품 문서 |

### Docker 이미지 크기 상세 (USB Offline 내)

| 이미지 | 추정 크기 |
|--------|-----------|
| DeepStream Pipeline | ~4GB |
| Dashboard Backend (FastAPI) | ~500MB |
| Dashboard UI (React/Next.js) | ~300MB |
| MQTT Broker (Mosquitto) | ~50MB |
| TimescaleDB/PostgreSQL | ~400MB |
| Redis | ~100MB |
| Nginx (Reverse Proxy) | ~50MB |
| **합계** | **~5.4GB** |

### TensorRT 모델 크기

| 모델 | 추정 크기 |
|------|-----------|
| PGIE (Primary GIE) - 객체 탐지 | ~200MB |
| SGIE (Secondary GIE) - 행동 인식 | ~150MB |
| **합계** | **~350MB** |

---

## 5. 무결성 검증 (Integrity Verification)

### SHA-256 Checksums

모든 배포 파일에 대해 SHA-256 해시를 생성하여 무결성을 보장합니다.

#### 생성 방법

```bash
# 체크섬 생성
sha256sum thingswell-safety-platform-*.* > CHECKSUMS.sha256

# 체크섬 검증
sha256sum -c CHECKSUMS.sha256
```

#### Windows PowerShell 검증

```powershell
# 체크섬 검증
Get-FileHash -Algorithm SHA256 .\thingswell-safety-platform-win11-online-v1.0.0.zip
```

### 검증 프로세스

1. 다운로드 완료 후 `CHECKSUMS.sha256` 파일 확인
2. 각 파일의 SHA-256 해시 계산
3. 계산된 해시와 `CHECKSUMS.sha256` 내 해시 비교
4. 불일치 시 재다운로드 또는 문의

---

## 6. 배포 방법 (Delivery Methods)

| 방법 | 대상 패키지 | 설명 |
|------|------------|------|
| **GitHub Release** | Win11 Online, Ubuntu Online, Reliability Test | 태그 기반 자동 릴리즈, 파일 첨부 |
| **Direct Download** | Win11 Online, Ubuntu Online | 게시판 링크를 통한 직접 다운로드 |
| **USB** | USB Offline, Customer Delivery | 물리적 USB 미디어 전달 |

### GitHub Release 구성

- **Tag**: `v1.0.0`, `v1.0.0-rc.1` 등
- **Title**: `Platform v1.0.0 - 정식 릴리즈`
- **Body**: 자동 생성된 릴리즈 노트
- **Assets**: 패키지 파일 + CHECKSUMS.sha256

### USB 전달 규격

- **포맷**: exFAT (4GB 이상 파일 지원)
- **용량**: 32GB USB 3.0 이상 권장
- **라벨**: `THINGSWELL_SAFETY_v1.0.0`

---

## 참고 문서

- [release-automation-plan.md](./release-automation-plan.md)
- [windows11-install-package-spec.md](./windows11-install-package-spec.md)
- [ubuntu-install-package-spec.md](./ubuntu-install-package-spec.md)
- [offline-usb-package-spec.md](./offline-usb-package-spec.md)
- [reliability-test-package-spec.md](./reliability-test-package-spec.md)
