# 게시판 배포 가이드 (Bulletin Board Distribution Guide)

> **프로젝트**: AI기반 장애인직업재활시설 스마트안전시스템  
> **대상**: 내부 게시판 배포 담당자  
> **문서 버전**: 1.0

---

## 1. 개요

스마트안전시스템 배포 파일을 내부 게시판에 공지할 때의 템플릿, 파일 목록, 보안 검증 절차를 정의합니다.

---

## 2. 게시판 공지 템플릿 (한국어)

### 2.1 제목 형식

```
[배포] ThingsWell 스마트안전시스템 v{VERSION} 배포 안내
```

**예시:**
```
[배포] ThingsWell 스마트안전시스템 v1.0.0 배포 안내
[배포] ThingsWell 스마트안전시스템 v1.0.0-rc.1 사전 배포 안내
[긴급패치] ThingsWell 스마트안전시스템 v1.0.1 보안 패치 안내
```

### 2.2 본문 템플릿

```markdown
## ThingsWell 스마트안전시스템 v{VERSION} 배포 안내

안녕하세요, ThingsWell 개발팀입니다.

스마트안전시스템 **v{VERSION}** 배포를 안내드립니다.

---

### 📋 변경 사항

#### 신규 기능
- {기능 1 설명}
- {기능 2 설명}

#### 버그 수정
- {버그 1 수정 내용}
- {버그 2 수정 내용}

#### 개선 사항
- {개선 1 내용}

---

### 📥 다운로드

| 패키지 | 대상 환경 | 파일 | 크기 |
|--------|-----------|------|------|
| Windows 11 | 데모/내부 시험 | [다운로드](링크) | ~50MB |
| Ubuntu Edge AI | 프로덕션 서버 | [다운로드](링크) | ~80MB |
| USB 오프라인 | 인터넷 미연결 현장 | 별도 전달 | ~10GB |
| 신뢰성 테스트 | QA팀 전용 | [다운로드](링크) | ~100MB |

---

### ✅ 설치 전 확인 사항

**Windows 11:**
- [ ] Docker Desktop 4.x 설치 및 실행 확인
- [ ] WSL2 활성화 확인
- [ ] 16GB 이상 RAM
- [ ] 50GB 디스크 여유 공간

**Ubuntu Edge AI Server:**
- [ ] Ubuntu 22.04 LTS
- [ ] NVIDIA Driver 535+ (`nvidia-smi` 확인)
- [ ] Docker 24.x + NVIDIA Container Toolkit
- [ ] 16GB+ RAM, RTX 3060+ GPU
- [ ] 100GB SSD 여유 공간

---

### 🔐 무결성 검증

다운로드 후 반드시 체크섬을 확인하세요:

```
SHA-256 체크섬:
{파일명1}  {해시값1}
{파일명2}  {해시값2}
```

**검증 방법:**
- Linux: `sha256sum -c CHECKSUMS.sha256`
- Windows: `Get-FileHash -Algorithm SHA256 .\파일명`

---

### 📖 설치 가이드

- Windows 11: 첨부 파일 내 `docs/INSTALL_GUIDE.md` 참조
- Ubuntu: 첨부 파일 내 `docs/INSTALL_GUIDE.md` 참조
- USB 오프라인: USB 내 `00_README_FIRST/` 폴더 참조

---

### ⚠️ 알려진 이슈

- {알려진 이슈 1}
- {알려진 이슈 2}

---

### 📞 문의

설치 또는 운영 관련 문의사항은 아래로 연락 부탁드립니다:
- 개발팀: {연락처}
- 긴급 장애: {긴급 연락처}

---

배포일: {YYYY-MM-DD}
배포 담당: {담당자명}
```

---

## 3. 버전별 다운로드 파일 목록

### 정식 릴리즈 (v1.0.0)

| # | 파일명 | 크기 | 대상 | 비고 |
|---|--------|------|------|------|
| 1 | `thingswell-safety-platform-win11-online-v1.0.0.zip` | ~50MB | Windows 11 | Docker Desktop 필요 |
| 2 | `thingswell-safety-platform-ubuntu-online-v1.0.0.tar.gz` | ~80MB | Ubuntu Edge AI | NVIDIA GPU 필요 |
| 3 | `thingswell-safety-platform-usb-offline-v1.0.0.tar.gz` | ~10GB | 오프라인 현장 | USB 별도 전달 |
| 4 | `thingswell-safety-platform-reliability-test-v1.0.0.tar.gz` | ~100MB | QA팀 | 72시간 테스트 |
| 5 | `RELEASE_NOTES-v1.0.0.md` | ~5KB | 전체 | 변경사항 |
| 6 | `CHECKSUMS.sha256` | ~1KB | 전체 | 무결성 검증 |

### Pre-release (RC/Beta)

| # | 파일명 | 비고 |
|---|--------|------|
| 1 | `thingswell-safety-platform-win11-online-v1.0.0-rc.1.zip` | RC 테스트용 |
| 2 | `thingswell-safety-platform-ubuntu-online-v1.0.0-rc.1.tar.gz` | RC 테스트용 |
| 3 | `thingswell-safety-platform-reliability-test-v1.0.0-rc.1.tar.gz` | 신뢰성 시험용 |
| 4 | `RELEASE_NOTES-v1.0.0-rc.1.md` | 변경사항 |
| 5 | `CHECKSUMS.sha256` | 무결성 검증 |

---

## 4. 버전 이력 테이블 형식

게시판에 버전 이력을 관리할 때 아래 형식을 사용합니다:

```markdown
## 버전 이력

| 버전 | 배포일 | 유형 | 주요 변경 | 다운로드 |
|------|--------|------|-----------|----------|
| v1.0.0 | 2025-03-01 | 정식 | Platform 1.0 정식 릴리즈 | [링크] |
| v1.0.0-rc.2 | 2025-02-20 | RC | 신뢰성 시험 버그 수정 | [링크] |
| v1.0.0-rc.1 | 2025-02-15 | RC | 인수시험용 릴리즈 | [링크] |
| v1.0.0-beta.3 | 2025-02-01 | Beta | 대시보드 UI 개선 | [링크] |
| v1.0.0-beta.2 | 2025-01-25 | Beta | 이벤트 처리 안정화 | [링크] |
| v1.0.0-beta.1 | 2025-01-15 | Beta | 기능 통합 테스트 | [링크] |
| v1.0.0-alpha.2 | 2025-01-10 | Alpha | AI 파이프라인 연동 | 삭제됨 |
| v1.0.0-alpha.1 | 2025-01-05 | Alpha | 초기 통합 빌드 | 삭제됨 |
```

---

## 5. 설치 전 체크리스트 (사용자용)

### Windows 11 체크리스트

```
□ Windows 11 Pro/Enterprise 버전 확인
□ Docker Desktop 4.x 설치 완료
□ Docker Desktop 실행 상태 확인 (System Tray)
□ WSL2 활성화 확인 (wsl --status)
□ 메모리 16GB 이상 확인
□ 디스크 50GB 여유 공간 확인
□ 관리자 PowerShell 실행 가능 확인
□ 다운로드 파일 체크섬 검증 완료
```

### Ubuntu Edge AI Server 체크리스트

```
□ Ubuntu 22.04 LTS 설치 확인 (lsb_release -a)
□ NVIDIA Driver 535+ 설치 확인 (nvidia-smi)
□ GPU 인식 확인 (RTX 3060 이상)
□ Docker 24.x 설치 확인 (docker --version)
□ NVIDIA Container Toolkit 설치 확인
□ docker compose plugin 확인 (docker compose version)
□ RAM 16GB 이상 확인 (free -h)
□ SSD 100GB 여유 공간 확인 (df -h)
□ 카메라 네트워크 접근 확인 (ping)
□ 다운로드 파일 체크섬 검증 완료
□ root 또는 sudo 권한 확인
```

---

## 6. Win11 vs Ubuntu 패키지 구분

게시판에서 패키지를 명확히 구분하여 혼동을 방지합니다:

### 구분 표시 가이드

| 구분 | Windows 11 | Ubuntu Edge AI |
|------|-----------|----------------|
| **아이콘/태그** | 🪟 Windows | 🐧 Ubuntu |
| **파일 확장자** | `.zip` | `.tar.gz` |
| **대상** | 데모/내부 시험 | 프로덕션 현장 |
| **GPU** | 불필요 (Demo mode) | 필수 (NVIDIA) |
| **설치 도구** | PowerShell (.ps1) | Bash (.sh) |
| **주의사항** | "데모용 - 실시간 AI 미지원" | "프로덕션용 - GPU 필수" |

### 게시판 구분 예시

```
📥 다운로드

🪟 [Windows 11 데모용] thingswell-safety-platform-win11-online-v1.0.0.zip (50MB)
   ⚠️ 데모/내부 시험 전용. 실시간 AI 분석 미지원. Docker Desktop 필요.

🐧 [Ubuntu 프로덕션용] thingswell-safety-platform-ubuntu-online-v1.0.0.tar.gz (80MB)
   ✅ 프로덕션 Edge AI 서버용. NVIDIA GPU + Docker 필요.
```

---

## 7. 링크 정책 (Direct Links vs Attached Files)

### 정책 요약

| 파일 크기 | 방식 | 이유 |
|-----------|------|------|
| < 100MB | 게시판 첨부 파일 | 직접 다운로드 편의성 |
| 100MB ~ 2GB | 직접 다운로드 링크 | 게시판 용량 제한 |
| > 2GB | USB 물리 전달 | 파일 크기 과대 |

### 링크 소스

| 소스 | URL 형식 | 대상 |
|------|----------|------|
| GitHub Release | `https://github.com/{org}/{repo}/releases/download/v{VERSION}/{filename}` | Win11, Ubuntu, Reliability |
| 내부 파일 서버 | `https://files.internal/{project}/releases/v{VERSION}/{filename}` | 대용량 파일 (백업) |
| USB | 물리적 전달 | USB Offline, Customer Delivery |

### 링크 유효성

- GitHub Release: 영구 유효 (삭제하지 않는 한)
- 내부 서버: 6개월 보관 후 아카이브
- 이전 버전: alpha/beta는 정식 릴리즈 후 삭제 가능

---

## 8. 보안 공지 (체크섬 검증 안내)

### 게시판 보안 공지 문구

```markdown
---
🔒 **보안 안내: 파일 무결성 검증**

다운로드한 파일의 무결성을 반드시 확인하세요.
변조된 파일 사용 시 시스템 보안이 위험할 수 있습니다.

**검증 방법:**

1. CHECKSUMS.sha256 파일을 다운로드합니다.
2. 아래 명령어로 검증합니다:

Linux/macOS:
$ sha256sum -c CHECKSUMS.sha256

Windows PowerShell:
> Get-FileHash .\thingswell-safety-platform-win11-online-v1.0.0.zip -Algorithm SHA256

3. 출력된 해시값이 CHECKSUMS.sha256 내 값과 일치하는지 확인합니다.
4. 불일치 시 파일을 재다운로드하거나 개발팀에 문의하세요.

⚠️ 체크섬이 일치하지 않는 파일은 절대 설치하지 마세요!
---
```

### 체크섬 파일 게시 형식

```
## CHECKSUMS.sha256 (v1.0.0)

파일별 SHA-256 해시:

a1b2c3d4e5f6...  thingswell-safety-platform-win11-online-v1.0.0.zip
f6e5d4c3b2a1...  thingswell-safety-platform-ubuntu-online-v1.0.0.tar.gz
1a2b3c4d5e6f...  thingswell-safety-platform-reliability-test-v1.0.0.tar.gz

GPG 서명: CHECKSUMS.sha256.sig (추후 제공 예정)
```

---

## 참고 문서

- [release-automation-plan.md](./release-automation-plan.md)
- [distribution-package-spec.md](./distribution-package-spec.md)
- [release-version-policy.md](./release-version-policy.md)
