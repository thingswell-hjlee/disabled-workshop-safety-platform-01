# Device Gateway Service

> 현장 장비(IP Camera, 스마트밴드, 환경센서, 화재감지 접점)로부터 데이터를 수신하고 정규화하여 Redis Stream으로 발행하는 서비스

## 역할

- RTSP 스트림 수신 및 프레임 추출 (IP Camera 8대)
- BLE/Wi-Fi → MQTT 데이터 수신 (스마트밴드 8개)
- MQTT 환경센서 데이터 수신 (2개)
- GPIO/RS-485 화재감지 접점 신호 수신
- 장비 상태 모니터링 (연결/끊김/오류)
- 데이터 정규화 후 Redis Stream 발행

## 기술 스택

- Python 3.11
- OpenCV (RTSP 디코딩)
- GStreamer (GPU 가속 디코딩)
- paho-mqtt (MQTT 클라이언트)
- redis-py (Redis Streams)
- pyserial (RS-485)

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 서비스 헬스체크 |
| GET | /api/v1/devices | 전체 장비 상태 조회 |
| GET | /api/v1/devices/{device_id} | 개별 장비 상태 조회 |
| POST | /api/v1/devices/{device_id}/reconnect | 장비 수동 재연결 |
| GET | /api/v1/streams/status | Redis Stream 발행 상태 |

## Redis Stream 출력

| Stream | 데이터 |
|--------|--------|
| `stream:frames:{device_id}` | 영상 프레임 메타데이터 |
| `stream:bio` | 스마트밴드 생체 데이터 |
| `stream:sensors` | 환경센서 + 화재감지 데이터 |

## 실행

```bash
docker compose up device-gateway
```

## 설정

`config/device-gateway.yaml` 참조
