# Platform 1.0 배포 계획 (Deployment Plan)

> **참조:** docs/design.md | docs/software-architecture.md
> **대상:** Edge AI 서버 (On-Premise) + AWS Cloud + 학습 서버

---

## 1. 배포 환경 구성

| 환경 | 용도 | 인프라 |
|------|------|--------|
| **Edge (Production)** | 현장 실운영 | Docker Compose on Edge AI Server |
| **Training (Production)** | 모델 학습·최적화 | Docker on Training Server |
| **Cloud (Production)** | 원격 모니터링, 이벤트 저장 | AWS ECS Fargate + S3 + RDS |
| **Local Dev** | 개발·디버깅 (GPU 없이 stub 모드) | Docker Compose on 개발 PC |

---

## 2. Edge AI 서버 배포

### 2.1 Docker Compose 구성

```yaml
services:
  redis:          # 메시지 브로커
  mosquitto:      # MQTT 브로커
  deepstream-app: # 8채널 영상 AI (GPU)
  event-engine:   # 위험등급 판정
  device-gateway: # 센서 수집
  alarm-controller: # GPIO 알람
  aws-sync-agent: # 클라우드 동기화
  dashboard-backend: # REST + WebSocket
  dashboard-ui:   # React/Next.js
```

### 2.2 배포 절차

```bash
# 1. 이미지 Pull/Build
docker compose pull
docker compose build

# 2. 서비스 시작
docker compose up -d

# 3. 헬스체크 확인
for port in 8001 8002 8003 8004 8005 8080; do
  curl -f http://localhost:$port/health
done

# 4. DeepStream 파이프라인 확인
curl http://localhost:8001/pipeline/sources
```

### 2.3 롤링 업데이트

```bash
# 개별 서비스 업데이트 (무중단)
docker compose up -d --no-deps --build event-engine

# DeepStream 업데이트 (2초 이내 재시작)
docker compose up -d --no-deps deepstream-app
```

### 2.4 롤백 절차

```bash
# 이전 이미지로 복원
docker compose down deepstream-app
docker tag safety/deepstream-app:latest safety/deepstream-app:rollback
docker compose up -d deepstream-app
```



---

## 3. AI 모델 배포

### 3.1 모델 배포 경로

```
[학습 서버: TAO train → export → trtexec]
    → [/models/staged/ 에 .engine 배치 (SCP/NFS)]
    → [Edge: POST /models/{id}/reload API 호출]
    → [DeepStream nvinfer 핫스왑]
    → [검증: 10프레임 추론 확인]
    → 성공: staged → active, registry.json 갱신
    → 실패: rollback/ 복원, 알림
```

### 3.2 모델 파일 구조

```
/models/
├── active/       # 현재 사용 중
├── staged/       # 배포 대기
├── rollback/     # 이전 버전 (즉시 복원용)
└── registry.json # 버전 메타데이터
```

### 3.3 배포 검증 기준

| 검증 항목 | 합격 기준 |
|-----------|-----------|
| 엔진 로드 | DeepStream 정상 로드 (에러 없음) |
| 추론 동작 | 10프레임 추론 결과 정상 |
| 성능 비교 | 이전 모델 대비 정확도 5% 이상 하락 없음 |
| 파이프라인 | FPS ≥ 15 유지 |

---

## 4. AWS 클라우드 배포

### 4.1 인프라 구성 (Terraform)

| 리소스 | 용도 | Platform 1.0 사양 |
|--------|------|-------------------|
| IoT Core | MQTT 이벤트 수신 | X.509 인증서 |
| S3 | 이벤트 클립 + 모델 저장 | Standard (수명주기 90일→Glacier) |
| RDS | 이벤트 메타데이터 | db.t3.micro PostgreSQL |
| ECS Fargate | 원격 대시보드 | 0.5vCPU / 1GB |
| ALB | HTTPS 종단 | 인증서 연동 |
| DynamoDB | 모델 레지스트리 | 온디맨드 |

### 4.2 배포 파이프라인 (GitHub Actions)

```yaml
name: Deploy Cloud Dashboard
on:
  push:
    branches: [release/platform-1.0]
    paths: ['apps/dashboard-backend/**']
jobs:
  deploy:
    steps:
      - Build Docker Image
      - Push to ECR
      - Deploy to ECS (Rolling Update)
      - Health Check
      - Notify (Slack)
```

---

## 5. CI/CD 파이프라인

### 5.1 Edge 서비스 CI

| 트리거 | 동작 | 산출물 |
|--------|------|--------|
| PR → develop | Lint + Unit Test + Docker Build | 빌드 성공 확인 |
| Merge → develop | Integration Test | 테스트 리포트 |
| Tag → v1.x.x | Docker Image Push (ECR) | 배포 이미지 |

### 5.2 모델 CI (학습 서버)

| 트리거 | 동작 | 산출물 |
|--------|------|--------|
| 학습 완료 | TAO evaluate → 성능 비교 | 메트릭 리포트 |
| 검증 합격 | TensorRT 변환 → registry 등록 | .engine 파일 |
| 배포 승인 | Edge 핫스왑 → 검증 | 배포 완료 알림 |

---

## 6. Secret 관리

| Secret | 저장 위치 | 접근 방법 |
|--------|-----------|-----------|
| DB Password | .env (Edge) / Secrets Manager (Cloud) | 환경변수 |
| JWT Secret | .env (Edge) | 환경변수 |
| AWS IoT 인증서 | /certs/ (volume mount) | 파일 경로 |
| AWS IAM 자격 | STS AssumeRole | IAM Role |
| MQTT Password | .env (Edge) | 환경변수 |

### 보안 규칙
- .env 파일: **절대 Git 커밋 금지**
- 인증서 파일: /certs/ 디렉토리, root 읽기전용 (640)
- 코드 내 Secret 하드코딩: **절대 금지**
- .env.example만 커밋 (실제 값 제외)

---

## 7. 모니터링·알림

### 7.1 배포 모니터링

| 지표 | 정상 | 경고 | 조치 |
|------|------|------|------|
| /health 응답 | 200 OK | 503/timeout | 자동 재시작 |
| DeepStream FPS | ≥15 | <10 | 로그 확인 |
| GPU 사용률 | ≤80% | >90% | 부하 분석 |
| 에러 로그 | 0건/분 | >5건/분 | 즉시 확인 |
| 배포 성공률 | 100% | <100% | 롤백 |

### 7.2 알림 채널

| 이벤트 | 채널 | 대상 |
|--------|------|------|
| 배포 성공 | 대시보드 로그 | 개발팀 |
| 배포 실패 | SMS + 대시보드 | 개발팀 + PM |
| 서비스 다운 | SMS | 운영팀 |
| 72시간 테스트 완료 | 이메일 | PM |

---

## 8. 배포 체크리스트

### Edge 배포 전
- [ ] Docker 이미지 빌드 확인
- [ ] .env 설정값 검증
- [ ] GPU 드라이버 + CUDA 버전 확인
- [ ] 디스크 용량 ≥ 20GB 여유
- [ ] 네트워크 연결 (MQTT, 카메라, 클라우드)
- [ ] 모델 파일 존재 확인 (/models/active/)
- [ ] GPIO 핀 정상 (사이렌, 경광등, 화재)
- [ ] NVR 녹화 상태 확인

### Cloud 배포 전
- [ ] 테스트 환경 검증 완료
- [ ] DB 마이그레이션 확인
- [ ] Secret 업데이트 확인
- [ ] 롤백 계획 준비
- [ ] 팀 공지 완료

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| 1.0 | 2025-05-19 | Platform 1.0 배포 계획 초안 |
