# S3 Event Clip Storage Structure

> **Status:** Platform 1.0
> **Reference:** docs/aws-iot-message-schema.md Section 3

## Bucket Naming

```
safety-platform-events-{account_id}
```

Production: `safety-platform-events-123456789012`
Staging: `safety-platform-events-staging-123456789012`

## Directory Structure

```
s3://safety-platform-events-{account_id}/
├── events/
│   └── {site_id}/
│       └── {YYYY}/
│           └── {MM}/
│               └── {DD}/
│                   ├── {event_id}.mp4          # Video clip
│                   └── {event_id}.jpg          # Thumbnail (optional)
├── models/
│   └── {site_id}/
│       └── {model_type}/
│           └── {model_version}/
│               └── model.zip                   # Model package
└── logs/  (reserved Platform 2.0+)
    └── {site_id}/
        └── {YYYY}/{MM}/{DD}/
            └── {component}-{HH}.log.gz
```

## Key Patterns

### Event Video Clips

| Pattern | Example |
|---------|---------|
| `events/{site_id}/{YYYY}/{MM}/{DD}/{event_id}.mp4` | `events/SITE-001/2025/05/19/EVT-20250519120000-001.mp4` |

### Event Thumbnails

| Pattern | Example |
|---------|---------|
| `events/{site_id}/{YYYY}/{MM}/{DD}/{event_id}.jpg` | `events/SITE-001/2025/05/19/EVT-20250519120000-001.jpg` |

### Model Packages

| Pattern | Example |
|---------|---------|
| `models/{site_id}/{model_type}/{model_version}/model.zip` | `models/SITE-001/pgie/v1.1.0-tao-ds/model.zip` |

## Upload Flow (Platform 1.0)

```
1. Edge: Event detected → Rolling buffer saves clip to local disk
2. Edge: clip_path = /data/clips/EVT-xxx.mp4
3. Edge: AWS Sync uploads to S3 (IAM STS temporary credentials)
4. Edge: clip_s3_key set in event record
5. IoT: Event message published with clip_s3_key
6. Cloud: Dashboard can generate pre-signed URL for clip playback
```

## Access Control

| Operation | Method |
|-----------|--------|
| Upload (Edge → S3) | IAM STS AssumeRole with time-limited credentials |
| Download (Dashboard) | S3 pre-signed URL (15min expiry) |
| Model download (Edge) | IAM STS AssumeRole |

## Lifecycle Rules (Platform 1.0)

| Rule | Target | Action | Days |
|------|--------|--------|------|
| Clips to IA | `events/` | Transition to Infrequent Access | 30 |
| Clips to Glacier | `events/` | Transition to Glacier | 90 |
| Delete old clips | `events/` | Delete | 365 |
| Model retention | `models/` | Keep indefinitely | - |

## Bucket Policy Template

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowEdgeUpload",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${account_id}:role/safety-edge-upload-role"
      },
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::safety-platform-events-${account_id}/events/${site_id}/*"
    },
    {
      "Sid": "AllowDashboardRead",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${account_id}:role/safety-dashboard-role"
      },
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::safety-platform-events-${account_id}/events/*"
    }
  ]
}
```

## Mock Mode (Local Development)

로컬 개발 시 S3는 사용하지 않습니다.
- `clip_s3_key` 필드는 `null` 또는 mock path로 채움
- 영상 클립은 로컬 파일시스템 (`/data/clips/`) 참조
- 실제 S3 업로드는 `AWS_MODE=live` 시에만 활성화

## Cost Estimation (Platform 1.0, 1 site)

| Item | Estimate |
|------|----------|
| Storage (30 events/day × 60s × 5MB) | ~4.5GB/month |
| PUT requests | ~900/month |
| GET requests | ~5,000/month |
| Data transfer | ~10GB/month |
| **Monthly cost** | **~$2-5** |
