# Model Package Schema

> **Status:** FROZEN (Platform 1.0)
> **Last Updated:** 2025-05-19
> **Purpose:** AI 모델 패키지 폴더 구조, 버전 명명 규칙, registry.json 스키마 정의

## Overview

DeepStream 파이프라인에서 사용하는 AI 모델의 관리 구조를 정의합니다. 모델 배포, 롤백, 버전 관리를 위한 표준 폴더 구조와 메타데이터를 포함합니다.

---

## 1. Folder Structure

```
/models/
├── active/                          # 현재 DeepStream에서 로드된 모델
│   ├── pgie/                        # Primary GIE (객체 감지)
│   │   ├── model.engine             # TensorRT engine file
│   │   ├── labels.txt               # Class labels
│   │   └── config.txt               # DeepStream nvinfer config
│   └── sgie/                        # Secondary GIE (분류/속성)
│       ├── model.engine
│       ├── labels.txt
│       └── config.txt
├── staged/                          # 배포 대기 모델
│   └── {model_version}/
│       ├── model.engine
│       ├── labels.txt
│       ├── config.txt
│       └── metadata.json
├── rollback/                        # 이전 버전 (즉시 복원용)
│   └── {model_version}/
│       ├── model.engine
│       ├── labels.txt
│       ├── config.txt
│       └── metadata.json
├── archived/                        # 보관용 (optional, Platform 2.0+)
│   └── {model_version}/
│       └── ...
└── registry.json                    # 모델 레지스트리 메타데이터
```

### Directory Purposes

| Directory | Purpose | Retention |
|-----------|---------|-----------|
| `/models/active/` | DeepStream이 현재 로드 중인 모델 | 항상 1개 버전 |
| `/models/staged/` | 배포 대기 중인 모델 (검증 완료) | 최대 1개 |
| `/models/rollback/` | 직전 active 버전 (즉시 복원) | 최대 1개 |
| `/models/archived/` | 과거 버전 보관 (reserved Platform 2.0+) | N/A |


---

## 2. registry.json Schema

```json
{
  "schema_version": "1.0",
  "site_id": "SITE-001",
  "last_updated": "2025-05-19T12:00:00.000Z",
  "models": [
    {
      "model_version": "v1.0.0-tao-ds",
      "model_type": "pgie",
      "model_name": "safety_detector",
      "framework": "TAO",
      "precision": "FP16",
      "engine_path": "/models/active/pgie/model.engine",
      "labels_path": "/models/active/pgie/labels.txt",
      "status": "ACTIVE",
      "deployed_at": "2025-05-19T10:00:00.000Z",
      "metrics": {
        "mAP": 0.85,
        "inference_time_ms": 12.5,
        "fps": 30,
        "classes": 6
      }
    }
  ]
}
```

### registry.json Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | Yes | Registry schema version (`1.0`) |
| `site_id` | string | Yes | `SITE-NNN` |
| `last_updated` | string | Yes | ISO 8601 UTC |
| `models` | array | Yes | Model entries |

### Model Entry Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_version` | string | Yes | `v{M}.{m}.{p}-{tool}-{target}` |
| `model_type` | string | Yes | `pgie`, `sgie` |
| `model_name` | string | Yes | Human-readable model name |
| `framework` | string | Yes | `TAO`, `PyTorch`, `TensorFlow`, `ONNX` |
| `precision` | string | Yes | `FP16`, `FP32`, `INT8` |
| `engine_path` | string | Yes | Path to TensorRT engine file |
| `labels_path` | string | Yes | Path to labels file |
| `status` | string | Yes | Model lifecycle status |
| `deployed_at` | string | Yes | ISO 8601 UTC deployment time |
| `metrics` | object | Yes | Model performance metrics |

### Model Status Values

| Status | Description |
|--------|-------------|
| `ACTIVE` | 현재 DeepStream에서 실행 중 |
| `STAGED` | 배포 대기 (검증 완료) |
| `ROLLBACK` | 롤백 대기 (이전 active) |
| `ARCHIVED` | 보관 (reserved Platform 2.0+) |

### Metrics Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mAP` | float | Yes | Mean Average Precision (0.0~1.0) |
| `inference_time_ms` | float | Yes | 평균 추론 시간 (ms) |
| `fps` | float | Yes | 처리 가능 FPS |
| `classes` | integer | Yes | 감지 클래스 수 |


---

## 3. Model Version Naming Convention

### Format

```
v{major}.{minor}.{patch}-{tool}-{target}
```

### Version Components

| Component | Description | Values |
|-----------|-------------|--------|
| `major` | Breaking changes (구조 변경, 클래스 변경) | 0, 1, 2, ... |
| `minor` | Feature additions (새 클래스 추가, 성능 개선) | 0, 1, 2, ... |
| `patch` | Bug fixes (라벨 수정, 미세 조정) | 0, 1, 2, ... |
| `tool` | Training tool / model origin | `tao`, `pretrained`, `custom` |
| `target` | Deployment target | `ds`, `cloud` |

### Tool Values

| Tool | Description |
|------|-------------|
| `tao` | NVIDIA TAO Toolkit으로 학습된 모델 |
| `pretrained` | 사전학습 모델 (fine-tuning 없이 사용) |
| `custom` | 자체 파이프라인으로 학습된 커스텀 모델 |

### Target Values

| Target | Description |
|--------|-------------|
| `ds` | DeepStream 엣지 배포용 (TensorRT engine) |
| `cloud` | 클라우드 평가/재학습용 (ONNX/PyTorch) |

### Examples

| Version | Description |
|---------|-------------|
| `v1.0.0-tao-ds` | TAO로 학습, DeepStream 초기 배포 |
| `v1.0.0-pretrained-ds` | 사전학습 모델 DeepStream 배포 |
| `v1.1.0-tao-ds` | TAO 모델 minor 업데이트 (새 클래스 추가) |
| `v2.0.0-custom-ds` | 커스텀 학습 major 버전 (구조 변경) |
| `v1.0.0-tao-cloud` | TAO 모델 클라우드 평가용 |


---

## 4. Engine File Naming

### Format

```
{model_name}_{version}_{precision}.engine
```

### Examples

| File Name | Description |
|-----------|-------------|
| `safety_detector_v1.0.0_fp16.engine` | 안전 감지기 v1.0.0 FP16 |
| `safety_detector_v1.1.0_int8.engine` | 안전 감지기 v1.1.0 INT8 |
| `action_classifier_v1.0.0_fp16.engine` | 행동 분류기 v1.0.0 FP16 |

---

## 5. Deploy Workflow States

```
              ┌─────────────────────────────────────────┐
              │                                         ▼
[STAGED] ──▶ [DEPLOYING] ──▶ [ACTIVE]         [ROLLBACK]
                  │                                  ▲
                  ▼                                  │
              [FAILED] ─────────────────────────────┘
```

### State Transitions

| From | To | Trigger | Description |
|------|----|---------|-------------|
| `STAGED` | `DEPLOYING` | Deploy command received | 배포 시작 |
| `DEPLOYING` | `ACTIVE` | Health check passed | 배포 성공, 서비스 시작 |
| `DEPLOYING` | `FAILED` | Health check failed / timeout | 배포 실패 |
| `FAILED` | `ROLLBACK` | Auto-rollback triggered | 이전 버전으로 자동 복원 |
| `ACTIVE` | `ROLLBACK` | Manual rollback command | 수동 롤백 |
| `ROLLBACK` | `ACTIVE` | Rollback model loaded | 롤백 버전이 active로 전환 |

### Deploy Process

1. **Download:** S3에서 모델 패키지 다운로드 → `/models/staged/{version}/`
2. **Validate:** Engine 파일 무결성 검증 (checksum)
3. **Stage:** Status → `STAGED`, 배포 준비 완료
4. **Deploy:** 현재 active → rollback으로 이동, staged → active로 이동
5. **Restart:** DeepStream 파이프라인 재시작 (graceful)
6. **Health Check:** 30초 내 정상 inference 확인
7. **Confirm:** Status → `ACTIVE`, registry.json 업데이트

### Rollback Process

1. **Trigger:** Health check 실패 또는 수동 rollback 명령
2. **Swap:** active → (discard), rollback → active
3. **Restart:** DeepStream 파이프라인 재시작
4. **Verify:** Health check 통과 확인
5. **Report:** MQTT `safety/{site_id}/models` 상태 보고


---

## 6. metadata.json (Per-Model Package)

각 모델 패키지 디렉토리에 포함되는 메타데이터 파일:

```json
{
  "model_version": "v1.0.0-tao-ds",
  "model_name": "safety_detector",
  "model_type": "pgie",
  "framework": "TAO",
  "precision": "FP16",
  "input_dims": { "channels": 3, "height": 544, "width": 960 },
  "classes": ["person", "fall", "collapse", "fire", "intrusion", "hazardous_action"],
  "num_classes": 6,
  "created_at": "2025-05-18T15:00:00.000Z",
  "checksum": "sha256:a1b2c3d4e5f6...",
  "training_config": {
    "epochs": 100,
    "batch_size": 8,
    "learning_rate": 0.001,
    "dataset_version": "ds-v2.1"
  },
  "evaluation": {
    "mAP": 0.85,
    "mAP_50": 0.92,
    "inference_time_ms": 12.5,
    "test_dataset_size": 5000
  }
}
```
