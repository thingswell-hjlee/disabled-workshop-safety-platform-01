# Sample Model Package

> **Platform 1.0** | Safety Detector - Pretrained Model Package

## Overview

이 디렉토리는 추론 서버(DeepStream)에서 로딩 가능한 모델 패키지의 **샘플 구조**입니다.
실제 `.engine` 파일은 포함되지 않으며, 패키지 구조와 메타데이터 형식을 정의합니다.

## Structure

```
sample-model-package/
├── model_manifest.json    # 모델 매니페스트 (추론 서버용)
├── registry.json          # 모델 레지스트리 (docs/model-package-schema.md 준수)
├── pgie/                  # Primary GIE (객체 감지)
│   ├── model.engine       # TensorRT engine (placeholder - 실제 파일 별도)
│   ├── labels.txt         # 6개 클래스 라벨
│   ├── config.txt         # DeepStream nvinfer 설정
│   └── metadata.json      # 모델 메타데이터
├── sgie/                  # Secondary GIE (reserved for Platform 2.0+)
│   └── .gitkeep
└── README.md
```

## Model Version

- **Version:** `v1.0.0-pretrained-ds`
- **Framework:** TAO (PeopleNet v2.6 base)
- **Precision:** FP16
- **Classes:** 6 (person, fall, collapse, fire, intrusion, hazardous_action)

## Usage

추론 서버는 `model_manifest.json`을 읽어 모델 경로를 결정합니다.

```python
import json

with open('/models/model_manifest.json') as f:
    manifest = json.load(f)

active_model = next(m for m in manifest['models'] if m['status'] == 'ACTIVE')
engine_path = active_model['engine_path']
labels_path = active_model['labels_path']
```

## Validation

```bash
# 모델 패키지 유효성 검증
./scripts/validate-model-package.sh models/sample-model-package/
```

## Notes

- `model.engine` 파일은 GPU 아키텍처에 종속됨 (TensorRT)
- 실제 engine 파일은 Git LFS 또는 S3/NFS로 관리
- 이 샘플에는 placeholder만 포함
