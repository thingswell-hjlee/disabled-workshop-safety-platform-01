# AI Inference Engine Service

> 영상·센서·바이오 데이터를 기반으로 실시간 위험 감지·판단을 수행하는 Edge AI 추론 서비스

## 역할

- 8채널 영상 동시 AI 추론 (YOLOv8 + TensorRT)
- 낙상 감지, 이상행동 감지, 위험구역 침입 감지
- 센서 임계치 기반 이상 감지
- 바이오 데이터(심박, 체온, 가속도) 이상 감지
- confidence score 부여 및 이벤트 발행

## 기술 스택

- Python 3.11, TensorRT 8.x, ONNX Runtime
- Redis Streams (입력/출력)
- CUDA 12.x, cuDNN 8.x

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 서비스 헬스체크 (GPU 상태 포함) |
| GET | /api/v1/models | 현재 로드된 모델 목록 |
| GET | /api/v1/models/{model_id}/info | 모델 상세 정보 |
| POST | /api/v1/models/{model_id}/reload | 모델 핫스왑 요청 |
| GET | /api/v1/inference/stats | 추론 통계 (FPS, 지연, GPU 사용률) |
| GET | /api/v1/zones | 위험구역 설정 조회 |
| PUT | /api/v1/zones/{camera_id} | 위험구역 polygon 설정 |

## Redis Stream I/O

**입력:**
- `stream:frames:{device_id}` - 영상 프레임
- `stream:bio` - 생체 데이터
- `stream:sensors` - 환경센서 데이터

**출력:**
- `stream:events` - 감지 이벤트 (event_type, risk_level, confidence)
