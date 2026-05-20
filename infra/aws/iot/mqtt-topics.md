# AWS IoT Core MQTT Topic Structure

> **Status:** Platform 1.0
> **Reference:** docs/aws-iot-message-schema.md

## Topic Hierarchy

```
safety/
├── {site_id}/
│   ├── events          # Edge → Cloud: 안전 이벤트 전송
│   ├── status          # Edge → Cloud: 엣지 서버 상태 보고 (60초 간격)
│   └── models          # Bidirectional: 모델 배포 명령/상태
```

## Topic Details

### 1. `safety/{site_id}/events`

| Property | Value |
|----------|-------|
| Direction | Edge → Cloud |
| QoS | 1 (At least once) |
| Payload | Event message (see below) |
| Deduplication | `idempotency_key` field |
| Priority | CRITICAL > WARNING > NORMAL |

**Payload Fields:**
- `event_id` (required): `EVT-YYYYMMDDHHmmss-SEQ`
- `site_id` (required): `SITE-NNN`
- `device_id` (required): Source device ID
- `worker_id` (optional): Associated worker
- `event_type` (required): event_type enum
- `risk_level` (required): CRITICAL | WARNING | NORMAL
- `confidence` (optional): 0.0~1.0
- `model_version` (optional): Model version string
- `timestamp` (required): ISO 8601 UTC
- `context_summary` (required): Human-readable summary
- `clip_s3_key` (optional): S3 key for video clip
- `idempotency_key` (required): `{site_id}:{event_id}`

### 2. `safety/{site_id}/status`

| Property | Value |
|----------|-------|
| Direction | Edge → Cloud |
| QoS | 1 |
| Interval | 60 seconds |
| Payload | Edge status report |

**Payload Fields:**
- `site_id`, `timestamp`, `edge_status` (HEALTHY|DEGRADED|ERROR)
- `deepstream_fps` (array), `gpu_utilization` (0.0~1.0)
- `active_cameras`, `active_bands`, `pending_cloud_events`

### 3. `safety/{site_id}/models`

| Property | Value |
|----------|-------|
| Direction | Bidirectional |
| QoS | 1 |
| Payload | Deploy command / Status report |

**Cloud → Edge:** `action` (DEPLOY|ROLLBACK|STATUS_REQUEST), `model_version`, `model_type`, `s3_uri`
**Edge → Cloud:** `action` (DEPLOY_STATUS), `model_version`, `status`, `progress`, `error_message`

## IoT Core Rules (Platform 1.0)

| Rule Name | Topic Filter | Action |
|-----------|-------------|--------|
| `safety-events-to-rds` | `safety/+/events` | Lambda → PostgreSQL insert |
| `safety-events-critical-notify` | `safety/+/events` (risk_level=CRITICAL) | Lambda → SNS notification |
| `safety-status-to-rds` | `safety/+/status` | Lambda → PostgreSQL upsert |
| `safety-models-to-lambda` | `safety/+/models` | Lambda → Deploy orchestration |

## IoT Policy Template

Edge device는 자신의 `site_id` 토픽에만 publish/subscribe 가능:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["iot:Publish"],
      "Resource": [
        "arn:aws:iot:*:*:topic/safety/${site_id}/events",
        "arn:aws:iot:*:*:topic/safety/${site_id}/status",
        "arn:aws:iot:*:*:topic/safety/${site_id}/models"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Subscribe"],
      "Resource": [
        "arn:aws:iot:*:*:topicfilter/safety/${site_id}/models"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Connect"],
      "Resource": ["arn:aws:iot:*:*:client/${site_id}-edge-*"]
    }
  ]
}
```

## Local Mock Mode

개발 환경에서는 Mosquitto broker를 사용하여 동일한 topic 구조로 테스트합니다.
`scripts/mock-aws-iot-receiver.sh` 실행으로 mock receiver를 시작할 수 있습니다.
