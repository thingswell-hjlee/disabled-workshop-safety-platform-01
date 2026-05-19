# Services

Edge AI 서버에서 동작하는 백엔드 마이크로서비스 모음입니다.

## 구성

| Service | 설명 | 입력 | 출력 |
|---------|------|------|------|
| `device-gateway` | 장비 데이터 수집·정규화 | RTSP, MQTT, GPIO | Redis Stream |
| `ai-inference` | AI 실시간 추론 | Redis Stream (프레임, 센서) | Redis Stream (이벤트) |
| `event-processor` | 위험등급 판정·라우팅 | Redis Stream (이벤트) | 알람, 저장, 클라우드 큐 |
| `alarm-controller` | 접점 알람 제어 | Redis Stream (알람 명령) | GPIO 출력 |
| `cloud-sync` | 클라우드 이벤트 동기화 | Redis Queue | AWS IoT Core |
| `training-pipeline` | 모델 학습·최적화·배포 | 추론 결과, 원시 데이터 | 최적화 모델 |

## 통신 방식

- 서비스 간: Redis Streams (비동기, 느슨한 결합)
- 외부 장비: MQTT, RTSP, GPIO/RS-485
- 클라우드: MQTT over TLS, HTTPS

## 배포

모든 서비스는 Docker 컨테이너로 패키징되며, Docker Compose로 통합 배포됩니다.
