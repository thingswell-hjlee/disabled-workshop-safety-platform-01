# AI기반 장애인직업재활시설 스마트안전시스템

> Platform 1.0 - 핵심 안전 기능 통합 동작

## Overview

장애인직업재활시설의 작업 현장에서 발생할 수 있는 안전사고를 AI 기반으로 실시간 감지·판단·알림하는 스마트안전시스템입니다.

### 핵심 기능

- **실시간 AI 위험 감지**: 영상 기반 낙상·이상행동·위험구역 침입 감지
- **다중 센서 융합**: 영상 + 환경센서 + 스마트밴드 통합 판단
- **즉시 현장 경보**: Edge AI 서버 기반 로컬 독립 알람 동작
- **원격 모니터링**: AWS 클라우드 기반 관리자 대시보드

## Project Structure

```
├── apps/                    # 사용자 대면 애플리케이션
│   ├── dashboard-ui/        # 관리자 대시보드 (React/Next.js)
│   └── dashboard-backend/   # 대시보드 API (FastAPI)
│
├── services/                # 백엔드 마이크로서비스
│   ├── device-gateway/      # 장비 연동 서비스
│   ├── ai-inference/        # AI 추론 엔진
│   ├── event-processor/     # 이벤트 처리·위험등급 판정
│   ├── alarm-controller/    # 접점 알람 제어
│   ├── cloud-sync/          # 클라우드 동기화
│   └── training-pipeline/   # 모델 학습·최적화
│
├── packages/                # 공유 라이브러리·SDK
│   ├── sdk-common/          # 공통 유틸리티, 설정, 상수
│   └── sdk-ai-event/       # AI 이벤트 스키마·타입
│
├── database/                # 데이터베이스
│   ├── migrations/          # 스키마 마이그레이션
│   └── seeds/               # 초기 데이터
│
├── tests/                   # 테스트
│   ├── unit/                # 단위 테스트
│   ├── integration/         # 통합 테스트
│   └── e2e/                 # End-to-End 테스트
│
├── docs/                    # 프로젝트 문서
│   ├── architecture/        # 아키텍처 설계
│   └── requirements/        # 요구사항
│
├── infra/                   # 인프라 설정
│   └── aws/                 # AWS 배포 설정
│
└── .kiro/                   # Kiro 설정 (specs)
    └── specs/               # inception, requirements 등
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Edge AI | TensorRT, ONNX Runtime, Python 3.11 |
| Message Broker | MQTT (Mosquitto), Redis Streams |
| Backend API | FastAPI |
| Frontend | React, Next.js |
| Database | PostgreSQL, Redis |
| Cloud | AWS (S3, RDS, IoT Core, ECS) |
| Container | Docker, Docker Compose |
| CI/CD | GitHub Actions |

## Getting Started

### Prerequisites

- Docker & Docker Compose
- NVIDIA GPU + CUDA 12.x + TensorRT
- Python 3.11+
- Node.js 20+

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/thingswell-hjlee/disabled-workshop-safety-platform-01.git

# 2. Copy environment template
cp .env.example .env

# 3. Start services (development)
docker compose up -d

# 4. Access dashboard
open http://localhost:3000
```

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | 안정 릴리즈 |
| `develop` | 개발 통합 |
| `release/platform-1.0` | Platform 1.0 릴리즈 준비 |
| `feature/*` | 기능 개발 |

## Platform Versions

| Version | Status | Description |
|---------|--------|-------------|
| **1.0** | 🔨 In Progress | 핵심 안전 기능 통합 동작 |
| 2.0 | 📋 Planned | 운영 관리 + 현장 맞춤 AI |
| 3.0 | 📋 Planned | 고도화·SaaS·다중 현장 |

## License

Private - All rights reserved.
