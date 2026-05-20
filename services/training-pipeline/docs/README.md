# AI Training Pipeline - TAO/NGC 기반 학습 시스템

> **Platform 1.0** | AI기반 장애인직업재활시설 스마트안전시스템
> **브랜치:** `feature/ai-training-tao-ngc`
> **담당:** AI Training Software (Session S3)

---

## 1. 개요

학습 AI 서버에서 수행하는 모델 학습 파이프라인의 기본 구조입니다.

### 주요 기능

| # | 기능 | 상태 |
|---|------|------|
| 1 | 데이터셋 폴더 구조 표준 | ✅ 완료 |
| 2 | 라벨 매니페스트 (6 classes) | ✅ 완료 |
| 3 | Event Clip → Dataset 변환 | ✅ 완료 |
| 4 | TAO Docker 실행 환경 | ✅ 문서화 |
| 5 | NGC Pretrained Model 다운로드 | ✅ 스크립트 |
| 6 | TAO 학습 설정 템플릿 | ✅ 완료 |
| 7 | ONNX/TensorRT 변환 절차 | ✅ 문서화 |
| 8 | 모델 패키지 빌드 | ✅ 스크립트 |
| 9 | 모델 패키지 검증 | ✅ 스크립트 |
| 10 | 샘플 모델 패키지 | ✅ 완료 |

---

## 2. 디렉토리 구조

```
services/training-pipeline/
├── configs/
│   ├── training-pipeline.yaml        # 서비스 설정
│   ├── detectnet_v2_train.yaml       # TAO 학습 스펙
│   └── detectnet_v2_export.yaml      # TAO Export 스펙
├── datasets/
│   ├── raw/                          # 원본 데이터
│   │   ├── clips/                    # 이벤트 영상 클립
│   │   ├── frames/                   # 추출 프레임
│   │   └── annotations/             # KITTI 라벨
│   ├── processed/                    # 학습용 데이터
│   │   ├── train/images/, labels/
│   │   ├── val/images/, labels/
│   │   └── test/images/, labels/
│   └── manifests/
│       ├── label_map.json            # 클래스 정의
│       ├── dataset_manifest.json     # 데이터셋 메타
│       └── split_info.json           # 분할 정보
├── docs/
│   ├── tao-docker-setup.md           # TAO Docker 가이드
│   ├── ngc-model-download.md         # NGC 다운로드 가이드
│   ├── onnx-tensorrt-conversion.md   # 변환 절차
│   └── README.md                     # 이 문서
├── scripts/
│   └── clip_to_dataset.py            # 클립→데이터셋 변환
├── src/
│   ├── api.py                        # REST API
│   └── models.py                     # 데이터 모델
├── Dockerfile
└── requirements.txt

models/sample-model-package/           # 샘플 모델 패키지
├── model_manifest.json                # 추론 서버용 매니페스트
├── registry.json                      # 모델 레지스트리
├── pgie/
│   ├── model.engine                   # TensorRT engine (placeholder)
│   ├── labels.txt                     # 6개 클래스 라벨
│   ├── config.txt                     # DeepStream nvinfer 설정
│   └── metadata.json                  # 모델 메타데이터
└── sgie/                              # Platform 2.0+ 예약

scripts/
├── setup-tao-docker.sh                # TAO Docker 실행기
├── download-ngc-model.sh              # NGC 모델 다운로드
├── build-model-package.sh             # 모델 패키지 빌드
└── validate-model-package.sh          # 모델 패키지 검증
```

---

## 3. 빠른 시작

### 3.1 사전 요구사항

- NVIDIA GPU (Turing 이상) + Driver 535+
- Docker 24.0+ with NVIDIA Container Toolkit
- NGC API Key (https://ngc.nvidia.com)

### 3.2 NGC 인증 설정

```bash
# NGC CLI 설치 (최초 1회)
# 상세: services/training-pipeline/docs/ngc-model-download.md

# Docker Registry 로그인
docker login nvcr.io
# Username: $oauthtoken
# Password: <NGC_API_KEY>
```

### 3.3 Pretrained 모델 다운로드

```bash
# PeopleNet v2.6 (권장)
./scripts/download-ngc-model.sh peoplenet

# 목록 확인
./scripts/download-ngc-model.sh --list
```

### 3.4 데이터셋 변환

```bash
# Event clip → 학습 데이터셋 (dry-run)
python3 services/training-pipeline/scripts/clip_to_dataset.py \
  --input services/training-pipeline/datasets/raw/clips \
  --output services/training-pipeline/datasets/processed \
  --dry-run

# 실제 변환 (opencv-python 필요)
python3 services/training-pipeline/scripts/clip_to_dataset.py \
  --input services/training-pipeline/datasets/raw/clips \
  --output services/training-pipeline/datasets/processed \
  --fps 5
```

### 3.5 TAO 학습 실행

```bash
# 대화형 세션
./scripts/setup-tao-docker.sh interactive

# 학습 실행
./scripts/setup-tao-docker.sh train detectnet_v2_train.yaml

# 모델 Export (ONNX)
./scripts/setup-tao-docker.sh export /workspace/experiments/detectnet_v2/weights/model.tlt

# TensorRT 변환
./scripts/setup-tao-docker.sh convert /workspace/models/export/model.onnx /workspace/models/export/model.engine
```

### 3.6 모델 패키지 빌드

```bash
# 패키지 생성
./scripts/build-model-package.sh \
  --version v1.0.0-tao-ds \
  --engine /path/to/model.engine \
  --output models/staged/v1.0.0-tao-ds

# 패키지 검증
./scripts/validate-model-package.sh models/staged/v1.0.0-tao-ds
```

---

## 4. 테스트 실행

### 4.1 모델 패키지 검증

```bash
# 샘플 모델 패키지 검증
./scripts/validate-model-package.sh models/sample-model-package/
# 결과: 41 PASS / 0 FAIL / 0 WARN
```

### 4.2 JSON 스키마 검증

```bash
python3 -c "
import json, re

# label_map.json
with open('services/training-pipeline/datasets/manifests/label_map.json') as f:
    lm = json.load(f)
assert lm['num_classes'] == 6
print('[PASS] label_map.json')

# model_manifest.json
with open('models/sample-model-package/model_manifest.json') as f:
    mm = json.load(f)
v = mm['models'][0]['model_version']
assert re.match(r'^v\d+\.\d+\.\d+-(tao|pretrained|custom)-(ds|cloud)$', v)
print('[PASS] model_manifest.json')

# registry.json
with open('models/sample-model-package/registry.json') as f:
    reg = json.load(f)
assert reg['site_id'] == 'SITE-001'
print('[PASS] registry.json')

print('All validations passed!')
"
```

### 4.3 빌드 스크립트 End-to-End

```bash
# 새 모델 패키지 빌드 + 검증
./scripts/build-model-package.sh \
  --version v1.1.0-tao-ds \
  --engine models/sample-model-package/pgie/model.engine \
  --output /tmp/test-model-package

./scripts/validate-model-package.sh /tmp/test-model-package
```

---

## 5. 스키마 준수 사항

이 구현은 다음 확정 스키마를 기준으로 작성되었습니다:

| 참조 문서 | 준수 항목 |
|-----------|-----------|
| `docs/model-package-schema.md` | 폴더 구조, registry.json, metadata.json, version naming |
| `docs/event-message-schema.md` | event_type enum, class 매핑 |
| `docs/interface-schema.md` | site_id 형식, model_version 패턴, Session S3 경계 |
| `docs/deployment-plan.md` | staged→active 배포 경로, 검증 기준 |
| `docs/release-automation-plan.md` | 버전 명명, 배포판 호환 |

### 변경 금지 항목

- `event_type`, `risk_level`, `site_id`, `device_id`, `camera_id`, `worker_id`, `model_version` 구조
- Redis Streams JSON, AWS IoT MQTT Payload, Event Message Schema

---

## 6. 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `NGC_API_KEY` | NGC API Key | (설정 필요) |
| `TAO_KEY` | TAO 암호화 키 | `tlt_encode` |
| `NUM_GPUS` | 사용 GPU 수 | `1` |
| `GPU_INDEX` | GPU 디바이스 인덱스 | `0` |
| `TAO_EXPERIMENTS_DIR` | 실험 디렉토리 | `/tmp/tao-experiments` |

> **주의:** NGC_API_KEY는 절대 Git에 커밋하지 않습니다.

---

## 7. 미완료 항목 (TODO)

| 항목 | Platform | 비고 |
|------|----------|------|
| 실제 TAO 학습 실행 | 1.0 | GPU 서버 필요 |
| INT8 캘리브레이션 | 1.0 | 학습 데이터 확보 후 |
| 자동 데이터 수집 파이프라인 | 2.0 | Edge → Training 자동 전송 |
| 모델 자동 재학습 | 3.0 | 오탐/미탐 피드백 기반 |
| 모델 A/B 테스트 | 3.0 | 다중 모델 동시 평가 |
| S3 모델 자동 업로드 | 2.0 | AWS 연동 |
| 학습 메트릭 대시보드 | 2.0 | TensorBoard 연동 |

---

## 8. 관련 문서

- [TAO Docker Setup](./tao-docker-setup.md)
- [NGC Model Download](./ngc-model-download.md)
- [ONNX/TensorRT Conversion](./onnx-tensorrt-conversion.md)
- [Dataset Structure](../datasets/README.md)
- [Model Package Schema](../../../docs/model-package-schema.md)
