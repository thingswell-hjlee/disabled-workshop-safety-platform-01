# Reliability Test Package Specification

> **프로젝트**: AI기반 장애인직업재활시설 스마트안전시스템  
> **패키지 유형**: Reliability Test  
> **대상**: QA팀 / 72시간 연속 운영 시험  
> **문서 버전**: 1.0

---

## 1. 개요

72시간(3일) 연속 운영 시험을 자동으로 수행하기 위한 테스트 패키지입니다.  
프로덕션 Ubuntu 패키지를 기반으로 테스트 자동화 스크립트, 모니터링 도구, 이벤트 주입 도구, 리포트 생성기를 추가로 포함합니다.

### 목적

- 시스템 안정성 검증 (메모리 누수, GPU 메모리 누수 감지)
- 장시간 운영 시 성능 저하 여부 확인
- 에러 발생률 및 복구 능력 검증
- 인수시험 전 품질 확인

---

## 2. 패키지 구성 (Ubuntu 패키지 + 추가 콘텐츠)

### 2.1 기본 포함 (Ubuntu Online 패키지 전체)

Ubuntu 프로덕션 패키지의 모든 구성 요소가 포함됩니다:
- docker-compose.yml / docker-compose.gpu.yml
- 설치/운영 스크립트 8종
- 설정 파일 및 systemd 유닛

### 2.2 추가 콘텐츠 (Reliability Test 전용)

| 디렉토리 | 내용 |
|----------|------|
| `test-scripts/` | 72시간 테스트 자동화 스크립트 |
| `monitoring/` | 메트릭 수집 및 모니터링 스크립트 |
| `event-injection/` | 시뮬레이션 이벤트 주입 도구 |
| `report-templates/` | 결과 리포트 생성 템플릿 |
| `test-config/` | 테스트 전용 설정 파일 |

---

## 3. 테스트 자동화 스크립트

### 3.1 run-72h-test.sh

72시간 연속 운영 테스트를 시작합니다.

**동작 순서:**
1. 사전 환경 확인 (GPU, 디스크 공간, 시스템 시간 동기화)
2. 시스템 시작 (docker compose up)
3. 초기 헬스체크 (모든 서비스 정상 확인)
4. 모니터링 데몬 시작 (5분 간격 메트릭 수집)
5. 이벤트 주입 스케줄 시작
6. 72시간 대기 (중간 체크포인트 6시간마다)
7. 테스트 종료 + 리포트 생성

```bash
# 실행 예시
sudo ./test-scripts/run-72h-test.sh

# 커스텀 기간 (예: 24시간)
sudo ./test-scripts/run-72h-test.sh --duration 24h

# 백그라운드 실행
sudo nohup ./test-scripts/run-72h-test.sh > test-output.log 2>&1 &
```

**출력:**
- 실시간 콘솔 로그
- 6시간마다 중간 리포트
- 최종 결과 리포트 (JSON + MD)

### 3.2 inject-events.sh

시뮬레이션 이벤트를 주입합니다.

**이벤트 유형:**

| 이벤트 | 주입 방법 | 빈도 |
|--------|-----------|------|
| 낙상 감지 | MQTT publish | 30분마다 1회 |
| 화재 감지 | MQTT publish | 2시간마다 1회 |
| 침입 감지 | MQTT publish | 1시간마다 1회 |
| 환경 센서 이상 | MQTT publish | 15분마다 1회 |
| 심박수 이상 | MQTT publish | 45분마다 1회 |
| GPIO 알람 | GPIO 시뮬레이션 | 이벤트 연동 |

```bash
# 이벤트 주입 시작
./test-scripts/inject-events.sh --mode scheduled

# 단일 이벤트 주입 (수동)
./test-scripts/inject-events.sh --event fall --camera cam01

# 부하 테스트 (대량 이벤트)
./test-scripts/inject-events.sh --mode stress --rate 10/min
```

**MQTT 이벤트 주입 예시:**
```bash
mosquitto_pub -h localhost -p 1883 \
  -t "thingswell/safety/events/fall" \
  -m '{
    "event_type": "fall_detected",
    "camera_id": "cam01",
    "timestamp": "2025-01-15T14:30:00Z",
    "confidence": 0.92,
    "bbox": {"x": 100, "y": 200, "w": 80, "h": 150}
  }'
```

### 3.3 collect-metrics.sh

시스템 메트릭을 수집합니다.

**수집 항목 (5분 간격):**

| 카테고리 | 메트릭 | 단위 |
|----------|--------|------|
| **GPU** | GPU 사용률 | % |
| **GPU** | GPU 메모리 사용량 | MB |
| **GPU** | GPU 온도 | °C |
| **CPU** | CPU 사용률 | % |
| **CPU** | CPU 온도 | °C |
| **RAM** | 메모리 사용량 | MB / % |
| **AI** | DeepStream FPS | frames/sec |
| **AI** | 추론 지연시간 (latency) | ms |
| **Events** | 이벤트 처리 수 (누적) | count |
| **Events** | 이벤트 처리 지연 | ms |
| **Errors** | 에러 발생 수 | count |
| **Errors** | 컨테이너 재시작 횟수 | count |
| **Disk** | 디스크 사용량 | GB / % |
| **Network** | MQTT 메시지 처리량 | msg/sec |
| **Docker** | 컨테이너별 메모리 | MB |

```bash
# 메트릭 수집 시작 (데몬 모드)
./test-scripts/collect-metrics.sh --daemon --interval 300

# 수동 단일 수집
./test-scripts/collect-metrics.sh --once

# 결과 확인
cat metrics/metrics-20250115.csv
```

**출력 형식 (CSV):**
```csv
timestamp,gpu_util,gpu_mem_mb,gpu_temp,cpu_util,ram_mb,ram_pct,fps,latency_ms,events_total,errors_total,disk_pct
2025-01-15T14:00:00Z,45,3200,62,25,8500,53,30,12,1500,0,35
2025-01-15T14:05:00Z,47,3210,63,27,8520,53,29,13,1520,0,35
```

### 3.4 generate-report.sh

테스트 결과 리포트를 생성합니다.

**동작 순서:**
1. 메트릭 CSV 파일 분석
2. 통계 계산 (평균, 최대, 최소, 표준편차)
3. Pass/Fail 기준 판정
4. 이벤트 처리 통계 계산
5. 에러/재시작 로그 분석
6. 리포트 생성 (Markdown + JSON)

```bash
# 리포트 생성
./test-scripts/generate-report.sh --input metrics/ --output report/

# 결과 파일
# report/reliability-test-report-v1.0.0-20250118.md
# report/reliability-test-report-v1.0.0-20250118.json
```

---

## 4. 모니터링 상세

### 5분 간격 메트릭 수집 구성

```bash
# cron 또는 systemd timer 기반
*/5 * * * * /opt/thingswell-safety/test-scripts/collect-metrics.sh --once >> /var/log/thingswell-metrics.log
```

### 실시간 모니터링 대시보드

테스트 중 실시간 모니터링을 위한 별도 도구:

```bash
# GPU 모니터링 (실시간)
watch -n 5 nvidia-smi

# Docker 리소스 모니터링
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# 종합 모니터링 (tmux 기반)
./monitoring/start-monitoring-dashboard.sh
```

### 알림 설정

테스트 중 이상 감지 시 즉시 알림:

| 조건 | 액션 |
|------|------|
| GPU 메모리 > 90% | 로그 경고 + 콘솔 알림 |
| CPU > 95% (5분 지속) | 로그 경고 |
| 컨테이너 재시작 발생 | 즉시 로그 기록 |
| FPS < 10 (5분 지속) | 로그 경고 |
| 디스크 > 90% | 로그 경고 + 오래된 로그 정리 |

---

## 5. 리포트 템플릿: Pass/Fail 기준

### 5.1 필수 Pass 기준 (Mandatory)

| # | 항목 | Pass 기준 | Fail 조건 |
|---|------|-----------|-----------|
| 1 | 연속 운영 시간 | 72시간 무중단 | 서비스 다운 발생 |
| 2 | GPU 메모리 누수 | 증가량 < 100MB/24h | 지속적 증가 |
| 3 | RAM 누수 | 증가량 < 500MB/24h | 지속적 증가 |
| 4 | AI FPS | 평균 ≥ 25 FPS | 평균 < 20 FPS |
| 5 | 이벤트 처리 지연 | 평균 < 500ms | 평균 > 1000ms |
| 6 | 에러율 | < 0.1% | ≥ 1% |
| 7 | 컨테이너 재시작 | 0회 | ≥ 1회 (watchdog 외) |

### 5.2 권장 Pass 기준 (Recommended)

| # | 항목 | 권장 기준 |
|---|------|-----------|
| 1 | GPU 온도 | 최대 < 85°C |
| 2 | CPU 사용률 | 평균 < 70% |
| 3 | 디스크 증가 | < 10GB/24h |
| 4 | AI 추론 지연 | 평균 < 30ms |

### 5.3 리포트 출력 형식

```markdown
# 신뢰성 테스트 리포트

## 테스트 요약
- 버전: v1.0.0-rc.1
- 시작: 2025-01-15 09:00:00 KST
- 종료: 2025-01-18 09:00:00 KST
- 기간: 72시간 00분
- 결과: ✅ PASS / ❌ FAIL

## 필수 항목 결과
| 항목 | 결과 | 측정값 | 기준 |
|------|------|--------|------|
| 연속 운영 | ✅ PASS | 72h 00m | ≥ 72h |
| GPU 메모리 누수 | ✅ PASS | +45MB/24h | < 100MB/24h |
| ...

## 통계 요약
- GPU 사용률: 평균 45%, 최대 72%, 최소 30%
- FPS: 평균 28.5, 최소 24, 최대 32
- 이벤트 처리: 총 2,880건, 평균 지연 120ms
- 에러: 0건 (에러율 0.00%)
```

---

## 6. 시뮬레이션 이벤트 주입 도구

### 6.1 MQTT 이벤트 주입

```bash
# 이벤트 유형별 토픽
thingswell/safety/events/fall          # 낙상 감지
thingswell/safety/events/fire          # 화재 감지
thingswell/safety/events/intrusion     # 구역 침입
thingswell/safety/events/environment   # 환경 센서 이상
thingswell/safety/events/heartrate     # 심박수 이상
```

### 6.2 카메라 시뮬레이션 (Fake RTSP)

인터넷 없는 환경에서 카메라 입력을 시뮬레이션:

```bash
# 녹화된 영상을 RTSP 스트림으로 재생
./event-injection/start-fake-rtsp.sh --video sample_factory.mp4 --port 8554

# 다중 카메라 시뮬레이션
./event-injection/start-fake-rtsp.sh --config fake-cameras.yml
```

**fake-cameras.yml 예시:**
```yaml
cameras:
  - id: cam01
    video: samples/factory_floor_01.mp4
    port: 8554
    loop: true
  - id: cam02
    video: samples/entrance_01.mp4
    port: 8555
    loop: true
  - id: cam03
    video: samples/workshop_01.mp4
    port: 8556
    loop: true
```

### 6.3 센서 시뮬레이션

```bash
# 환경 센서 시뮬레이션 (온도, 습도, CO, 먼지)
./event-injection/simulate-sensors.sh --interval 60

# 심박수 시뮬레이션 (정상 + 간헐적 이상)
./event-injection/simulate-heartrate.sh --workers 10 --abnormal-rate 0.05
```

---

## 7. 폴더 구조 (패키지 내부)

```
thingswell-safety-platform-reliability-test-v1.0.0/
├── (ubuntu-online 패키지 전체 포함)
│   ├── docker-compose.yml
│   ├── docker-compose.gpu.yml
│   ├── .env.example
│   ├── scripts/
│   ├── config/
│   ├── systemd/
│   └── docs/
│
├── test-scripts/
│   ├── run-72h-test.sh              # 72시간 테스트 메인
│   ├── inject-events.sh             # 이벤트 주입
│   ├── collect-metrics.sh           # 메트릭 수집
│   └── generate-report.sh           # 리포트 생성
│
├── monitoring/
│   ├── start-monitoring-dashboard.sh # 실시간 모니터링
│   ├── alert-rules.yml              # 알림 규칙
│   └── grafana-dashboard.json       # Grafana 대시보드 (선택)
│
├── event-injection/
│   ├── start-fake-rtsp.sh           # 카메라 시뮬레이션
│   ├── simulate-sensors.sh          # 센서 시뮬레이션
│   ├── simulate-heartrate.sh        # 심박수 시뮬레이션
│   ├── fake-cameras.yml             # 카메라 설정
│   └── samples/                     # 샘플 영상 파일
│       ├── factory_floor_01.mp4
│       ├── entrance_01.mp4
│       └── workshop_01.mp4
│
├── report-templates/
│   ├── report-template.md           # 리포트 템플릿 (Markdown)
│   ├── report-template.json         # 리포트 구조 (JSON)
│   └── pass-fail-criteria.yml       # Pass/Fail 기준 정의
│
├── test-config/
│   ├── test-env.example             # 테스트 환경 변수
│   ├── test-schedule.yml            # 이벤트 주입 스케줄
│   └── metric-config.yml            # 메트릭 수집 설정
│
├── metrics/                          # (실행 시 생성)
│   └── .gitkeep
│
└── report/                           # (실행 시 생성)
    └── .gitkeep
```

---

## 참고 문서

- [release-automation-plan.md](./release-automation-plan.md)
- [distribution-package-spec.md](./distribution-package-spec.md)
- [ubuntu-install-package-spec.md](./ubuntu-install-package-spec.md)
- [release-version-policy.md](./release-version-policy.md)
