# AWS Cloud Architecture - Platform 1.0

## 1. 개요

Platform 1.0의 AWS 클라우드 구성은 최소한의 서비스로 핵심 기능(원격 모니터링, 이벤트 저장, 모델 관리)을 제공한다.

### 1.1 설계 원칙

- **최소 구성**: Platform 1.0에 필요한 서비스만 배포
- **비용 최적화**: 프리티어·온디맨드 활용, 오버프로비저닝 방지
- **보안 기본**: VPC 격리, TLS 통신, IAM 최소 권한
- **확장 대비**: Platform 2.0/3.0 확장 가능한 구조

## 2. AWS 서비스 구성

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud (ap-northeast-2)                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                        VPC (10.0.0.0/16)                     ││
│  │                                                              ││
│  │  ┌──────────────────┐  ┌──────────────────┐                 ││
│  │  │ Public Subnet     │  │ Private Subnet    │                ││
│  │  │ 10.0.1.0/24       │  │ 10.0.2.0/24       │                ││
│  │  │                    │  │                    │                ││
│  │  │ [ALB]             │  │ [ECS - Dashboard]  │                ││
│  │  │ [NAT Gateway]     │  │ [RDS PostgreSQL]   │                ││
│  │  └──────────────────┘  └──────────────────┘                 ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐│
│  │ IoT Core   │  │ S3         │  │ DynamoDB   │  │ CloudWatch ││
│  │ (MQTT)     │  │ (Storage)  │  │ (Model Reg)│  │ (Logs)     ││
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
        ▲
        │ MQTT over TLS / HTTPS
        │
┌───────┴────────┐
│ Edge AI Server  │
│ (On-Premise)    │
└────────────────┘
```

## 3. 서비스별 상세

### 3.1 AWS IoT Core

| 항목 | 설정 |
|------|------|
| **용도** | Edge↔Cloud MQTT 통신 |
| **프로토콜** | MQTT over TLS (port 8883) |
| **인증** | X.509 인증서 기반 |
| **토픽** | `safety/{site_id}/events`, `safety/{site_id}/status` |
| **규칙** | IoT Rule → Lambda → RDS 저장 |

### 3.2 Amazon S3

| 버킷 | 용도 | 수명주기 |
|------|------|----------|
| `safety-platform-events-{account}` | 이벤트 영상 클립 | 90일 → Glacier |
| `safety-platform-models-{account}` | AI 모델 파일 | 영구 보관 |
| `safety-platform-logs-{account}` | 시스템 로그 | 90일 → 삭제 |

### 3.3 Amazon RDS (PostgreSQL)

| 항목 | 설정 |
|------|------|
| **인스턴스** | db.t3.micro (Platform 1.0) |
| **엔진** | PostgreSQL 15 |
| **스토리지** | 20GB gp3 (자동 확장) |
| **백업** | 7일 자동 백업 |
| **접근** | Private Subnet, Security Group 제한 |

### 3.4 Amazon ECS (Fargate)

| 항목 | 설정 |
|------|------|
| **용도** | 클라우드 대시보드 백엔드 |
| **태스크** | dashboard-backend (FastAPI) |
| **CPU/Memory** | 0.5 vCPU / 1GB |
| **Auto-scaling** | 최소 1, 최대 2 태스크 |
| **로드밸런서** | ALB (HTTPS 종단) |

### 3.5 DynamoDB

| 테이블 | 파티션 키 | 정렬 키 | 용도 |
|--------|-----------|---------|------|
| `model-registry` | model_type | model_version | 모델 버전 관리 |
| `device-status` | site_id | device_id | 장비 상태 캐시 |

### 3.6 CloudWatch

| 항목 | 설정 |
|------|------|
| **로그 그룹** | /safety-platform/dashboard, /safety-platform/iot |
| **메트릭** | 이벤트 수, 에러율, 지연시간 |
| **알람** | 에러율 > 5%, RDS CPU > 80% |
| **보관** | 90일 |

## 4. 네트워크 설계

### 4.1 VPC 구성

| 서브넷 | CIDR | AZ | 리소스 |
|--------|------|----|--------|
| Public-A | 10.0.1.0/24 | ap-northeast-2a | ALB, NAT GW |
| Public-B | 10.0.3.0/24 | ap-northeast-2c | ALB (멀티 AZ) |
| Private-A | 10.0.2.0/24 | ap-northeast-2a | ECS, RDS |
| Private-B | 10.0.4.0/24 | ap-northeast-2c | RDS (멀티 AZ) |

### 4.2 Security Group

| SG | 인바운드 | 용도 |
|----|----------|------|
| sg-alb | 443 (0.0.0.0/0) | 대시보드 HTTPS 접근 |
| sg-ecs | 8080 (sg-alb) | ALB → ECS 통신 |
| sg-rds | 5432 (sg-ecs) | ECS → RDS 통신 |

## 5. 비용 추정 (월간)

| 서비스 | 예상 비용 (USD) | 비고 |
|--------|-----------------|------|
| IoT Core | ~$5 | 메시지 10만/월 기준 |
| S3 | ~$3 | 50GB 저장 기준 |
| RDS (t3.micro) | ~$15 | 단일 AZ |
| ECS (Fargate) | ~$20 | 0.5vCPU 상시 |
| ALB | ~$18 | 기본 + 요청 처리 |
| DynamoDB | ~$1 | 온디맨드 |
| CloudWatch | ~$3 | 로그 + 메트릭 |
| NAT Gateway | ~$35 | 시간 + 처리량 |
| **합계** | **~$100/월** | Platform 1.0 기준 |

## 6. Platform 2.0/3.0 확장 계획

| 항목 | Platform 2.0 | Platform 3.0 |
|------|-------------|-------------|
| ECS | t3.small, Auto-scale 4 | EKS 전환 |
| RDS | db.t3.small, 멀티 AZ | Aurora Serverless |
| 추가 서비스 | SageMaker, SES | Cognito, API GW, Multi-region |

---

*버전: 0.1 | 작성일: 2025-05-19*
