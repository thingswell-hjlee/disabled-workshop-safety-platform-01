# Windows 11 Install Package Specification

> **프로젝트**: AI기반 장애인직업재활시설 스마트안전시스템  
> **패키지 유형**: Win11 Online  
> **대상**: 데모/내부 테스트 환경  
> **문서 버전**: 1.0

---

## 1. 개요

Windows 11 환경에서 Docker Desktop을 이용하여 스마트안전시스템을 실행하기 위한 설치 패키지입니다.  
**GPU 가속 없이** 데모 모드로 동작하며, 내부 시험 및 데모 시연 용도로 사용됩니다.

---

## 2. 대상 환경 (Target)

- **용도**: 데모/내부 테스트
- **OS**: Windows 11 (22H2 이상)
- **모드**: Demo mode (GPU 가속 없음)

---

## 3. 사전 요구 사항 (Prerequisites)

| 항목 | 요구 사항 |
|------|-----------|
| OS | Windows 11 Pro/Enterprise (22H2+) |
| Docker | Docker Desktop 4.x 이상 |
| WSL2 | WSL2 활성화 + Ubuntu 배포판 |
| RAM | 16GB 이상 |
| 디스크 | 50GB 여유 공간 |
| 네트워크 | 인터넷 연결 (Docker 이미지 pull) |

### Docker Desktop 설정 요구 사항

```
Settings > Resources > WSL Integration: 활성화
Settings > Resources > Memory: 8GB 이상 할당
Settings > Resources > CPU: 4 코어 이상 할당
```

---

## 4. 패키지 내용 (Package Contents)

### 4.1 핵심 파일

| 파일 | 설명 |
|------|------|
| `docker-compose.windows.yml` | Windows Docker Desktop용 Compose 설정 |
| `.env.example` | 환경 변수 템플릿 |
| `VERSION` | 버전 정보 |
| `RELEASE_NOTES.md` | 릴리즈 노트 |
| `CHECKSUMS.sha256` | 파일 무결성 해시 |
| `LICENSE` | 라이선스 |

### 4.2 스크립트 (PowerShell)

| 스크립트 | 설명 |
|----------|------|
| `scripts/install-online.ps1` | 온라인 설치 (Docker 이미지 pull + 설정) |
| `scripts/install-offline.ps1` | 오프라인 설치 (USB에서 이미지 로드) |
| `scripts/start.ps1` | 서비스 시작 |
| `scripts/stop.ps1` | 서비스 중지 |
| `scripts/update.ps1` | 최신 버전으로 업데이트 |
| `scripts/uninstall.ps1` | 완전 제거 (컨테이너, 볼륨, 이미지) |
| `scripts/status.ps1` | 서비스 상태 확인 |

### 4.3 설정 파일

| 파일/디렉토리 | 설명 |
|--------------|------|
| `config/source_list.yml` | 카메라/센서 소스 설정 |
| `config/thresholds.yml` | 이벤트 임계값 설정 |
| `config/roi/` | ROI (Region of Interest) 설정 |
| `config/dashboard.yml` | 대시보드 설정 |

### 4.4 문서

| 파일 | 설명 |
|------|------|
| `docs/INSTALL_GUIDE.md` | 설치 가이드 |
| `docs/QUICK_START.md` | 빠른 시작 가이드 |
| `docs/TROUBLESHOOTING.md` | 문제 해결 가이드 |

---

## 5. 스크립트 동작 상세

### 5.1 install-online.ps1

온라인 환경에서 초기 설치를 수행합니다.

**동작 순서:**
1. 사전 요구 사항 확인 (Docker Desktop, WSL2, 메모리)
2. `.env.example` → `.env` 복사 및 기본값 설정
3. Docker 이미지 pull (`docker compose pull`)
4. 초기 데이터베이스 마이그레이션
5. 설치 완료 메시지 + 대시보드 URL 표시

```powershell
# 실행 예시
.\scripts\install-online.ps1
```

### 5.2 install-offline.ps1

USB 오프라인 패키지에서 Docker 이미지를 로드합니다.

**동작 순서:**
1. USB 드라이브 경로 입력 받기
2. Docker 이미지 `.tar` 파일 확인
3. `docker load` 로 이미지 로드
4. `.env` 설정
5. 초기 데이터베이스 마이그레이션

```powershell
# 실행 예시
.\scripts\install-offline.ps1 -UsbPath "E:\THINGSWELL_SAFETY_USB_v1.0.0"
```

### 5.3 start.ps1

모든 서비스를 시작합니다.

**동작 순서:**
1. Docker Desktop 실행 상태 확인
2. `.env` 파일 존재 확인
3. `docker compose -f docker-compose.windows.yml up -d`
4. 헬스체크 대기 (최대 120초)
5. 서비스 상태 표시 + 대시보드 URL

```powershell
# 실행 예시
.\scripts\start.ps1
```

### 5.4 stop.ps1

모든 서비스를 중지합니다.

**동작 순서:**
1. `docker compose -f docker-compose.windows.yml down`
2. 서비스 중지 확인

```powershell
# 실행 예시
.\scripts\stop.ps1
```

### 5.5 update.ps1

최신 버전으로 업데이트합니다.

**동작 순서:**
1. 현재 버전 확인
2. 서비스 중지
3. Docker 이미지 pull (최신)
4. 데이터베이스 마이그레이션 (필요 시)
5. 서비스 재시작
6. 업데이트 완료 메시지

```powershell
# 실행 예시
.\scripts\update.ps1
```

### 5.6 uninstall.ps1

시스템을 완전히 제거합니다.

**동작 순서:**
1. 사용자 확인 프롬프트 (데이터 삭제 경고)
2. 서비스 중지
3. Docker 컨테이너 삭제
4. Docker 볼륨 삭제 (데이터 포함)
5. Docker 이미지 삭제 (선택)
6. 설정 파일 백업 (선택)
7. 제거 완료 메시지

```powershell
# 실행 예시
.\scripts\uninstall.ps1
# 데이터 보존 모드
.\scripts\uninstall.ps1 -KeepData
```

### 5.7 status.ps1

현재 서비스 상태를 확인합니다.

**동작 순서:**
1. Docker Desktop 실행 상태 확인
2. 각 컨테이너 상태 조회
3. 리소스 사용량 표시 (CPU, Memory)
4. 대시보드 접근 가능 여부

```powershell
# 실행 예시
.\scripts\status.ps1
```

---

## 6. Ubuntu 대비 제한 사항 (Limitations)

| 항목 | Windows 11 (Demo) | Ubuntu (Production) |
|------|-------------------|---------------------|
| GPU 가속 | ❌ 미지원 | ✅ NVIDIA GPU |
| DeepStream | ❌ CPU 모드/Mock | ✅ 전체 파이프라인 |
| TensorRT 추론 | ❌ 미지원 | ✅ 실시간 추론 |
| 실시간 카메라 | ⚠️ 제한적 (1-2대) | ✅ 다중 카메라 |
| 성능 | ⚠️ 데모용 | ✅ 프로덕션급 |
| systemd 통합 | ❌ 해당없음 | ✅ 자동 시작 |
| 자동 복구 | ❌ 수동 | ✅ restart policy + watchdog |
| 롤백 | ❌ 미지원 | ✅ 이전 버전 복구 |

### Demo Mode 동작

Windows 11에서는 GPU가 없으므로 다음과 같이 동작합니다:

- **AI 추론**: Mock 데이터 또는 사전 녹화된 결과 재생
- **영상 분석**: 실시간 분석 대신 시뮬레이션 이벤트 생성
- **대시보드**: 정상 동작 (데모 데이터 표시)
- **알림 시스템**: 정상 동작 (시뮬레이션 이벤트 기반)

---

## 7. 폴더 구조 (ZIP 내부)

```
thingswell-safety-platform-win11-online-v1.0.0/
├── VERSION
├── RELEASE_NOTES.md
├── CHECKSUMS.sha256
├── LICENSE
├── README.md
├── docker-compose.windows.yml
├── .env.example
├── scripts/
│   ├── install-online.ps1
│   ├── install-offline.ps1
│   ├── start.ps1
│   ├── stop.ps1
│   ├── update.ps1
│   ├── uninstall.ps1
│   └── status.ps1
├── config/
│   ├── source_list.yml
│   ├── thresholds.yml
│   ├── dashboard.yml
│   └── roi/
│       └── default.json
└── docs/
    ├── INSTALL_GUIDE.md
    ├── QUICK_START.md
    └── TROUBLESHOOTING.md
```

---

## 참고 문서

- [distribution-package-spec.md](./distribution-package-spec.md)
- [ubuntu-install-package-spec.md](./ubuntu-install-package-spec.md)
- [offline-usb-package-spec.md](./offline-usb-package-spec.md)
