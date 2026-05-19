# Deployment Plan - Platform 1.0

## 1. 배포 전략 개요

### 1.1 환경 구성

| 환경 | 용도 | 인프라 |
|------|------|--------|
| **Local Dev** | 개발·디버깅 | Docker Compose (개발자 PC) |
| **Edge (Production)** | 현장 실운영 | Docker Compose (Edge Server) |
| **Cloud (Production)** | 원격 모니터링 | AWS ECS Fargate |

### 1.2 배포 파이프라인

```
[GitHub] → [GitHub Actions CI] → [Docker Build] → [ECR Push] → [ECS Deploy]
                                       │
                                       └→ [Edge: docker pull → docker-compose up]
```

## 2. Edge 배포 (On-Premise)

### 2.1 배포 방식

- Docker Compose 기반 전체 서비스 배포
- 이미지: Private Docker Registry (ECR) 또는 로컬 빌드
- 업데이트: `docker compose pull && docker compose up -d`

### 2.2 배포 절차

```bash
# 1. 이미지 Pull (인터넷 연결 시)
docker compose pull

# 2. 서비스 업데이트 (Rolling)
docker compose up -d --no-deps <service_name>

# 3. 헬스체크 확인
curl http://localhost:8080/health

# 4. 전체 재시작 (필요 시)
docker compose down && docker compose up -d
```

### 2.3 AI 모델 배포

```
[Training Server] → 모델 최적화 완료
                  → model_version 태깅
                  → Edge AI Service로 모델 파일 복사 (NFS/SCP)
                  → AI Inference Service Hot-swap (API 호출)
                  → 헬스체크 → 성능 검증
                  → (실패 시) 자동 롤백
```

### 2.4 롤백 절차

```bash
# 이전 버전으로 롤백
docker compose down
docker tag safety-platform/ai-inference:1.0 safety-platform/ai-inference:rollback
docker compose up -d

# 모델 롤백
curl -X POST http://localhost:8081/api/v1/model/rollback
```

## 3. Cloud 배포 (AWS)

### 3.1 CI/CD 파이프라인 (GitHub Actions)

```yaml
# .github/workflows/deploy-cloud.yml
name: Deploy to Cloud
on:
  push:
    branches: [release/platform-1.0]
    paths: ['apps/dashboard-backend/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build & Push to ECR
      - name: Deploy to ECS
      - name: Health Check
      - name: Notify
```

### 3.2 ECS 배포 전략

| 항목 | 설정 |
|------|------|
| 배포 방식 | Rolling Update |
| 최소 헬시 | 100% |
| 최대 | 200% |
| 헬스체크 | /health, 30초 간격 |
| 드레이닝 | 60초 |

### 3.3 데이터베이스 마이그레이션

```bash
# ECS Task로 마이그레이션 실행
aws ecs run-task --task-definition safety-db-migrate --cluster safety-prod
```

## 4. 환경 변수 관리

### 4.1 Secret 관리

| 환경 | 방법 |
|------|------|
| Local Dev | .env 파일 (gitignore) |
| Edge Prod | /etc/safety-platform/.env (root 읽기전용) |
| Cloud Prod | AWS Secrets Manager + ECS Task Role |

### 4.2 Secret 종류

| Secret | 저장소 |
|--------|--------|
| DB Password | AWS Secrets Manager |
| JWT Secret Key | AWS Secrets Manager |
| IoT 인증서 | AWS IoT + S3 (암호화) |
| MQTT Password | Edge /etc/ 파일 |

## 5. 모니터링·알림

### 5.1 배포 모니터링

| 지표 | 정상 | 경고 | 조치 |
|------|------|------|------|
| 배포 성공률 | 100% | < 100% | 로그 확인, 롤백 |
| 헬스체크 | 200 OK | 503/timeout | 자동 재시작 |
| 에러율 | < 1% | > 5% | 롤백 |
| 응답 시간 | < 500ms | > 2000ms | 스케일링 확인 |

### 5.2 알림 채널

| 이벤트 | 채널 |
|--------|------|
| 배포 성공 | Slack |
| 배포 실패 | Slack + SMS |
| 서비스 다운 | SMS + 전화 |
| Edge 오프라인 | Slack + SMS |

## 6. 배포 체크리스트

### 6.1 Edge 배포 전

- [ ] Docker 이미지 빌드 확인
- [ ] .env 설정값 검증
- [ ] GPU 드라이버 + CUDA 버전 확인
- [ ] 디스크 용량 확인 (> 20GB)
- [ ] 네트워크 연결 테스트 (MQTT, 클라우드)

### 6.2 Cloud 배포 전

- [ ] 테스트 환경에서 검증 완료
- [ ] DB 마이그레이션 계획 확인
- [ ] Secret 업데이트 필요 여부
- [ ] 롤백 계획 준비
- [ ] 서비스 팀 공지

---

*버전: 0.1 | 작성일: 2025-05-19*
