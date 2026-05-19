# Platform 1.0 Release Automation Plan

> **프로젝트**: AI기반 장애인직업재활시설 스마트안전시스템  
> **기술 스택**: NVIDIA DeepStream + TAO + TensorRT | Edge AI Server (Ubuntu + GPU) | AWS Cloud | Dashboard  
> **배포 방식**: Docker-based  
> **문서 버전**: 1.0  
> **최종 수정**: 2025-01

---

## 1. 배포판 유형 (5종)

| # | 배포 유형 | 대상 | 형식 | 설명 |
|---|-----------|------|------|------|
| 1 | Win11 Online | 내부 시험/데모 | `.zip` | Docker Desktop 기반 Windows 11 패키지 |
| 2 | Ubuntu Online | 프로덕션 Edge AI 서버 | `.tar.gz` | NVIDIA GPU 서버용 프로덕션 패키지 |
| 3 | USB Offline | 인터넷 미연결 현장 | USB 폴더 구조 | Docker 이미지 + 모델 포함 완전 오프라인 |
| 4 | Reliability Test | QA/신뢰성 시험 | `.tar.gz` | 72시간 연속 운영 테스트 패키지 |
| 5 | Customer Delivery | 납품/고객 전달 | USB + 문서 | 최종 납품 패키지 (인수시험 포함) |

---

## 2. 산출물 명명 규칙 (Artifact Naming)

```
thingswell-safety-platform-{type}-${VERSION}.{ext}
```

### 명명 예시

| 배포 유형 | 파일명 예시 |
|-----------|------------|
| Win11 Online | `thingswell-safety-platform-win11-online-v1.0.0.zip` |
| Ubuntu Online | `thingswell-safety-platform-ubuntu-online-v1.0.0.tar.gz` |
| USB Offline | `thingswell-safety-platform-usb-offline-v1.0.0.tar.gz` |
| Reliability Test | `thingswell-safety-platform-reliability-test-v1.0.0.tar.gz` |
| Customer Delivery | `thingswell-safety-platform-customer-delivery-v1.0.0.tar.gz` |

---

## 3. GitHub Actions Workflow Overview

### 트리거 방식: Tag-triggered

```yaml
on:
  push:
    tags:
      - 'v*.*.*'
      - 'v*.*.*-alpha.*'
      - 'v*.*.*-beta.*'
      - 'v*.*.*-rc.*'
```

### 워크플로우 파일

```
.github/workflows/release.yml
```

---

## 4. Jobs (7개)

| # | Job ID | 설명 | Runner | 의존성 |
|---|--------|------|--------|--------|
| 1 | `win-package` | Windows 11 설치 패키지 생성 | ubuntu-latest | - |
| 2 | `ubuntu-package` | Ubuntu Edge AI Server 패키지 생성 | ubuntu-latest | - |
| 3 | `offline-usb` | USB 오프라인 패키지 생성 (Docker images 포함) | ubuntu-latest | win-package, ubuntu-package |
| 4 | `reliability-test` | 신뢰성 테스트 패키지 생성 | ubuntu-latest | ubuntu-package |
| 5 | `checksum-gen` | SHA-256 체크섬 생성 | ubuntu-latest | win-package, ubuntu-package, offline-usb, reliability-test |
| 6 | `github-release-upload` | GitHub Release 생성 및 업로드 | ubuntu-latest | checksum-gen |
| 7 | `notification` | Slack/Teams 알림 전송 | ubuntu-latest | github-release-upload |

### Job 의존성 다이어그램

```
win-package ──────┐
                  ├──→ offline-usb ──┐
ubuntu-package ───┤                  ├──→ checksum-gen → github-release-upload → notification
                  ├──→ reliability-test ──┘
                  │
                  └──(독립 실행)
```

---

## 5. Build Matrix

```yaml
strategy:
  matrix:
    package-type: [win11-online, ubuntu-online, usb-offline, reliability-test]
    include:
      - package-type: win11-online
        os: ubuntu-latest
        script: scripts/build-win11-package.sh
        artifact-ext: zip
      - package-type: ubuntu-online
        os: ubuntu-latest
        script: scripts/build-ubuntu-package.sh
        artifact-ext: tar.gz
      - package-type: usb-offline
        os: ubuntu-latest
        script: scripts/build-usb-offline-package.sh
        artifact-ext: tar.gz
      - package-type: reliability-test
        os: ubuntu-latest
        script: scripts/build-reliability-package.sh
        artifact-ext: tar.gz
```

---

## 6. Release Process Flow

```
dev → alpha → beta → rc → release
```

| 단계 | 태그 예시 | 목적 | 배포 대상 |
|------|-----------|------|-----------|
| **dev** | (branch only) | 개발 중 | 개발팀 내부 |
| **alpha** | `v1.0.0-alpha.1` | 내부 개발 테스트 | 개발팀 |
| **beta** | `v1.0.0-beta.1` | 기능 통합 테스트 | 내부 QA팀 |
| **rc** | `v1.0.0-rc.1` | 신뢰성/인수 시험 | QA + 고객 현장 |
| **release** | `v1.0.0` | 정식 배포 | 고객 납품 |

### 프로세스 상세

1. **develop** 브랜치에서 기능 개발
2. `release/v1.0.0` 브랜치 생성
3. alpha 태그 → 내부 테스트
4. beta 태그 → 통합 테스트 + 버그 수정
5. rc 태그 → 72시간 신뢰성 시험 수행
6. 시험 통과 시 `main` 머지 + release 태그
7. GitHub Release 자동 생성 + 알림

---

## 7. 산출물 테이블 (Artifacts)

| 파일명 | 예상 크기 | 내용물 |
|--------|-----------|--------|
| `thingswell-safety-platform-win11-online-v1.0.0.zip` | ~50MB | docker-compose, ps1 scripts, config templates, docs |
| `thingswell-safety-platform-ubuntu-online-v1.0.0.tar.gz` | ~80MB | docker-compose, GPU config, sh scripts, systemd units, docs |
| `thingswell-safety-platform-usb-offline-v1.0.0.tar.gz` | ~8-12GB | Docker images (.tar), TensorRT models, config, full installer |
| `thingswell-safety-platform-reliability-test-v1.0.0.tar.gz` | ~100MB | ubuntu-package + test scripts, metric collectors, event injector |
| `thingswell-safety-platform-customer-delivery-v1.0.0.tar.gz` | ~12-15GB | USB package + 인수시험 문서 + 납품 문서 |
| `CHECKSUMS.sha256` | ~1KB | 모든 산출물의 SHA-256 해시 |
| `RELEASE_NOTES.md` | ~5KB | 릴리즈 노트 (변경사항, 알려진 이슈) |

---

## 8. Next PR Implementation Plan

다음 PR에서 구현할 스크립트 및 설정 파일 목록:

### 8.1 GitHub Actions Workflow

- `.github/workflows/release.yml` — 메인 릴리즈 워크플로우

### 8.2 Build Scripts

- `scripts/build-win11-package.sh` — Windows 11 패키지 빌드
- `scripts/build-ubuntu-package.sh` — Ubuntu 패키지 빌드
- `scripts/build-usb-offline-package.sh` — USB 오프라인 패키지 빌드
- `scripts/build-reliability-package.sh` — 신뢰성 테스트 패키지 빌드
- `scripts/build-customer-delivery-package.sh` — 납품 패키지 빌드

### 8.3 Utility Scripts

- `scripts/generate-checksums.sh` — SHA-256 체크섬 생성
- `scripts/generate-release-notes.sh` — 릴리즈 노트 자동 생성
- `scripts/notify-release.sh` — 릴리즈 알림 전송

### 8.4 Package Templates

- `templates/win11/` — Windows 11 패키지 템플릿 (ps1 scripts)
- `templates/ubuntu/` — Ubuntu 패키지 템플릿 (sh scripts, systemd)
- `templates/usb/` — USB 구조 템플릿
- `templates/reliability/` — 신뢰성 테스트 스크립트 템플릿

---

## 참고 문서

- [distribution-package-spec.md](./distribution-package-spec.md)
- [windows11-install-package-spec.md](./windows11-install-package-spec.md)
- [ubuntu-install-package-spec.md](./ubuntu-install-package-spec.md)
- [offline-usb-package-spec.md](./offline-usb-package-spec.md)
- [reliability-test-package-spec.md](./reliability-test-package-spec.md)
- [bulletin-board-distribution-guide.md](./bulletin-board-distribution-guide.md)
- [release-version-policy.md](./release-version-policy.md)
