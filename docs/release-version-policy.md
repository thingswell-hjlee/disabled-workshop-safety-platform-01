# Release Version Policy

> **프로젝트**: AI기반 장애인직업재활시설 스마트안전시스템  
> **문서 버전**: 1.0

---

## 1. 버전 체계 (Semantic Versioning)

### 형식

```
v{major}.{minor}.{patch}[-prerelease]
```

| 구성 요소 | 설명 | 변경 시점 |
|-----------|------|-----------|
| **major** | 주 버전 | 하위 호환성 깨지는 변경 (Breaking Changes) |
| **minor** | 부 버전 | 하위 호환 기능 추가 (New Features) |
| **patch** | 패치 버전 | 버그 수정 (Bug Fixes) |
| **prerelease** | 프리릴리즈 | 정식 배포 전 단계 식별 |

### 예시

```
v1.0.0          → Platform 1.0 정식 릴리즈
v1.1.0          → 신규 기능 추가 (하위 호환)
v1.1.1          → 버그 수정
v2.0.0          → 아키텍처 변경 (Breaking Change)
v1.0.0-alpha.1  → 알파 테스트 1회차
v1.0.0-beta.2   → 베타 테스트 2회차
v1.0.0-rc.1     → Release Candidate 1회차
```

---

## 2. Pre-release 단계 정의

### 단계별 정의

| 단계 | 식별자 | 목적 | 품질 수준 | 대상 |
|------|--------|------|-----------|------|
| **Alpha** | `-alpha.N` | 내부 개발 테스트 | 불안정, 기능 미완성 가능 | 개발팀 |
| **Beta** | `-beta.N` | 기능 통합 테스트 | 주요 기능 완성, 버그 존재 가능 | 내부 QA팀 |
| **RC** | `-rc.N` | 신뢰성/인수 시험 | 배포 준비 완료, 최종 검증 | QA + 고객 현장 |
| **Release** | (없음) | 정식 배포 | 프로덕션 품질 | 고객/납품 |

### 단계 진행 흐름

```
alpha.1 → alpha.2 → ... → beta.1 → beta.2 → ... → rc.1 → rc.2 → ... → release
```

### N (순번) 규칙

- 동일 단계 내에서 1부터 순차 증가
- 상위 단계 진입 시 N=1로 리셋
- 예: `alpha.3` → `beta.1` → `beta.2` → `rc.1`

---

## 3. 태그 형식 (Tag Format)

### 태그 명명 규칙

```
v{major}.{minor}.{patch}[-{stage}.{N}]
```

### Platform 1.0 태그 예시

```
v1.0.0-alpha.1    # 첫 번째 알파 빌드
v1.0.0-alpha.2    # 두 번째 알파 빌드
v1.0.0-alpha.3    # 세 번째 알파 빌드
v1.0.0-beta.1     # 첫 번째 베타 빌드
v1.0.0-beta.2     # 두 번째 베타 (버그 수정 후)
v1.0.0-beta.3     # 세 번째 베타 (추가 수정)
v1.0.0-rc.1       # 첫 번째 RC (신뢰성 시험 투입)
v1.0.0-rc.2       # 두 번째 RC (시험 중 발견된 이슈 수정)
v1.0.0            # 정식 릴리즈
```

### 태그 생성 방법

```bash
# 태그 생성 (Annotated Tag)
git tag -a v1.0.0-alpha.1 -m "Platform 1.0 Alpha 1 - 초기 통합 빌드"

# 태그 푸시
git push origin v1.0.0-alpha.1

# 정식 릴리즈 태그
git tag -a v1.0.0 -m "Platform 1.0 정식 릴리즈"
git push origin v1.0.0
```

---

## 4. 브랜치 전략 (Branch Strategy)

### 브랜치 구조

```
main (production)
  │
  ├── release/v1.0.0 (릴리즈 준비)
  │     │
  │     ├── hotfix/v1.0.0-rc.1-fix-xxx
  │     └── hotfix/v1.0.0-rc.2-fix-yyy
  │
  └── develop (개발 메인)
        │
        ├── feature/xxx
        ├── feature/yyy
        └── bugfix/zzz
```

### 브랜치별 역할

| 브랜치 | 역할 | 태그 가능 | 보호 |
|--------|------|-----------|------|
| `main` | 프로덕션 릴리즈 | ✅ (release only) | ✅ Protected |
| `develop` | 개발 통합 | ✅ (alpha) | ✅ Protected |
| `release/v{X.Y.Z}` | 릴리즈 준비 | ✅ (beta, rc) | ✅ Protected |
| `feature/*` | 기능 개발 | ❌ | ❌ |
| `hotfix/*` | 긴급 수정 | ❌ | ❌ |

### 릴리즈 플로우

```
1. develop에서 기능 개발 완료
   └─ alpha 태그: v1.0.0-alpha.N (develop에서)

2. release/v1.0.0 브랜치 생성 (develop에서 분기)
   └─ beta 태그: v1.0.0-beta.N (release 브랜치에서)

3. QA 테스트 + 버그 수정 (release 브랜치)
   └─ rc 태그: v1.0.0-rc.N (release 브랜치에서)

4. 신뢰성 시험 통과
   └─ main으로 머지 + release 태그: v1.0.0

5. main → develop 역머지 (sync)
```

---

## 5. 단계 진입 기준 (Stage Criteria)

### Alpha 진입 기준

| # | 기준 | 확인 방법 |
|---|------|-----------|
| 1 | 핵심 기능 구현 완료 (일부 미완성 허용) | PR 머지 상태 |
| 2 | Docker Compose로 시스템 기동 가능 | `docker compose up` 성공 |
| 3 | 기본 단위 테스트 통과 | CI 통과 |
| 4 | 빌드 오류 없음 | CI 빌드 성공 |

### Beta 진입 기준

| # | 기준 | 확인 방법 |
|---|------|-----------|
| 1 | 모든 계획 기능 구현 완료 | Task 완료율 100% |
| 2 | 단위 테스트 커버리지 ≥ 70% | CI 리포트 |
| 3 | 통합 테스트 통과 | CI 통합 테스트 |
| 4 | Critical/Blocker 버그 없음 | Issue tracker |
| 5 | API 문서 완성 | 문서 리뷰 완료 |
| 6 | 설치 스크립트 동작 확인 | 수동 검증 |

### RC 진입 기준

| # | 기준 | 확인 방법 |
|---|------|-----------|
| 1 | Beta 테스트 완료 + 버그 수정 | QA 사인오프 |
| 2 | 성능 테스트 통과 (FPS ≥ 25) | 성능 테스트 리포트 |
| 3 | 보안 취약점 스캔 완료 | 보안 스캔 리포트 |
| 4 | 설치/업데이트/롤백 시나리오 검증 | 수동 검증 |
| 5 | 문서 최종 리뷰 완료 | 문서 사인오프 |
| 6 | 알려진 이슈 문서화 완료 | KNOWN_ISSUES.md |

### Release 진입 기준

| # | 기준 | 확인 방법 |
|---|------|-----------|
| 1 | 72시간 신뢰성 시험 PASS | 시험 리포트 |
| 2 | 고객 현장 인수시험 PASS (해당 시) | 인수시험 체크리스트 |
| 3 | 모든 Critical/Major 이슈 해결 | Issue tracker |
| 4 | 납품 문서 완성 | 문서 검수 |
| 5 | 릴리즈 노트 작성 완료 | RELEASE_NOTES.md |
| 6 | PM/PL 최종 승인 | 승인 기록 |

---

## 6. Changelog 생성 규칙

### 자동 생성 기반

Changelog는 Conventional Commits를 기반으로 자동 생성합니다.

### Commit 메시지 형식

```
{type}({scope}): {description}

[optional body]

[optional footer]
```

### Type → Changelog 매핑

| Commit Type | Changelog 섹션 | 설명 |
|-------------|---------------|------|
| `feat` | ✨ 신규 기능 (Features) | 새로운 기능 추가 |
| `fix` | 🐛 버그 수정 (Bug Fixes) | 버그 수정 |
| `perf` | ⚡ 성능 개선 (Performance) | 성능 최적화 |
| `refactor` | ♻️ 리팩토링 (Refactoring) | 기능 변경 없는 코드 개선 |
| `docs` | 📝 문서 (Documentation) | 문서 변경 |
| `test` | ✅ 테스트 (Tests) | 테스트 추가/수정 |
| `ci` | 🔧 CI/CD | CI 파이프라인 변경 |
| `chore` | (표시 안 함) | 기타 잡무 |

### Breaking Changes 표시

```
feat(api)!: API 응답 형식 변경

BREAKING CHANGE: 이벤트 API 응답에서 `data` 필드가 `payload`로 변경됨
```

### Changelog 출력 예시

```markdown
# Changelog

## [v1.0.0] - 2025-03-01

### ✨ 신규 기능
- **deepstream**: DeepStream 6.4 기반 AI 파이프라인 구현
- **dashboard**: 실시간 이벤트 대시보드 UI
- **alert**: GPIO 경보 연동 시스템

### 🐛 버그 수정
- **mqtt**: 재연결 시 메시지 유실 문제 수정
- **database**: TimescaleDB 마이그레이션 오류 수정

### ⚡ 성능 개선
- **pipeline**: 멀티스트림 FPS 30% 향상

### 📝 문서
- 설치 가이드 작성
- API 문서 완성
```

### 자동 생성 도구

```bash
# git-cliff 또는 conventional-changelog 사용
git cliff --tag v1.0.0 --output CHANGELOG.md

# 또는 자체 스크립트
./scripts/generate-release-notes.sh v1.0.0-rc.1 v1.0.0
```

---

## 7. 이전 버전 폐기 정책 (Deprecation Policy)

### Pre-release 버전 폐기

| 유형 | 보관 기간 | 삭제 시점 |
|------|-----------|-----------|
| Alpha | 다음 Beta 릴리즈까지 | Beta.1 릴리즈 후 삭제 |
| Beta | 다음 RC 릴리즈까지 | RC.1 릴리즈 후 삭제 |
| RC | 정식 릴리즈까지 | Release 후 30일 보관 후 삭제 |

### 정식 릴리즈 보관

| 유형 | 보관 기간 | 비고 |
|------|-----------|------|
| 현재 버전 (latest) | 영구 보관 | 항상 접근 가능 |
| 직전 버전 (previous) | 6개월 | 롤백 필요 시 대비 |
| 이전 메이저 버전 | 12개월 | EOL 공지 후 삭제 |

### EOL (End of Life) 공지

```markdown
## ⚠️ EOL 공지: v0.x.x 지원 종료

v0.x.x 버전의 지원이 종료됩니다.

- 지원 종료일: 2025-06-01
- 마지막 보안 패치: v0.9.5
- 권장 조치: v1.0.0 이상으로 업그레이드

업그레이드 가이드: [마이그레이션 문서 링크]
```

### 삭제 프로세스

1. EOL 30일 전 공지 (게시판 + 알림)
2. EOL 후 GitHub Release에서 Draft 전환 (다운로드 링크 비활성화)
3. EOL 후 60일 후 완전 삭제

---

## 8. 버전 관리 도구 및 자동화

### VERSION 파일

프로젝트 루트의 `VERSION` 파일로 현재 버전을 관리합니다:

```
1.0.0
```

### 버전 범프 자동화

```bash
# Patch 버전 업 (1.0.0 → 1.0.1)
./scripts/bump-version.sh patch

# Minor 버전 업 (1.0.0 → 1.1.0)
./scripts/bump-version.sh minor

# Major 버전 업 (1.0.0 → 2.0.0)
./scripts/bump-version.sh major

# Pre-release (1.0.0 → 1.1.0-alpha.1)
./scripts/bump-version.sh minor --pre alpha
```

### CI 연동

GitHub Actions에서 태그 기반으로 자동 배포:

```yaml
on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    steps:
      - name: Extract version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_ENV
```

---

## 참고 문서

- [release-automation-plan.md](./release-automation-plan.md)
- [distribution-package-spec.md](./distribution-package-spec.md)
- [SemVer 2.0.0 Specification](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
