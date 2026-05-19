# Training Pipeline Service

> 현장 데이터 수집 → 모델 학습 → 최적화 → Edge 배포를 담당하는 로컬 AI 학습 서버

## 역할

- Edge AI 추론 결과 기반 학습 데이터 자동 수집
- 데이터 자동 분할 (train 80% / val 10% / test 10%)
- PyTorch 기반 Fine-tuning (YOLOv8)
- TensorRT INT8 양자화 최적화
- Edge AI 서버 무중단 모델 배포 (Hot-swap)
- 배포 실패 시 자동 롤백
- 클라우드 모델 레지스트리 동기화

## API 엔드포인트

### 파이프라인
| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 헬스체크 (GPU 포함) |
| GET | /api/v1/pipeline/status | 파이프라인 상태 |

### 데이터
| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/data/datasets | 데이터셋 목록 |
| GET | /api/v1/data/datasets/{id} | 데이터셋 상세 |
| POST | /api/v1/data/collect | 수집 트리거 |
| GET | /api/v1/data/stats | 수집 통계 |

### 학습
| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/training/jobs | 학습 작업 목록 |
| POST | /api/v1/training/jobs | 학습 작업 생성 |
| GET | /api/v1/training/jobs/{id} | 작업 상세 (메트릭) |
| POST | /api/v1/training/jobs/{id}/cancel | 작업 취소 |

### 모델
| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/models | 모델 목록 |
| GET | /api/v1/models/{version} | 모델 상세 |
| POST | /api/v1/models/{version}/optimize | 최적화 시작 |

### 배포
| Method | Path | 설명 |
|--------|------|------|
| POST | /api/v1/deploy/{version} | Edge 배포 |
| GET | /api/v1/deploy/status | 배포 상태 |
| POST | /api/v1/deploy/rollback | 롤백 |

## 기술 스택

- PyTorch 2.x, Ultralytics YOLOv8
- TensorRT (INT8 양자화)
- ONNX (중간 포맷)
- Redis (이벤트 트리거)
- boto3 (S3 모델 업로드)
