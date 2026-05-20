# Training Pipeline - Dataset Folder Structure

> **Platform 1.0** | AI기반 장애인직업재활시설 스마트안전시스템

## Overview

학습 데이터셋의 표준 폴더 구조를 정의합니다.
Event Clip에서 추출된 프레임과 라벨링 데이터를 TAO Toolkit 학습에 적합한 형식으로 관리합니다.

---

## Folder Structure

```
datasets/
├── raw/                              # 원본 데이터 (이벤트 클립 기반)
│   ├── clips/                        # 이벤트 영상 클립 (.mp4)
│   │   └── {event_id}/
│   │       ├── clip.mp4              # 이벤트 전후 영상
│   │       └── metadata.json         # 클립 메타데이터
│   ├── frames/                       # 클립에서 추출된 프레임 (.jpg)
│   │   └── {event_id}/
│   │       ├── frame_0001.jpg
│   │       ├── frame_0002.jpg
│   │       └── ...
│   └── annotations/                  # 라벨링 결과 (KITTI format)
│       └── {event_id}/
│           ├── frame_0001.txt
│           ├── frame_0002.txt
│           └── ...
├── processed/                        # 학습용 정제 데이터
│   ├── train/                        # 학습 세트 (80%)
│   │   ├── images/
│   │   │   ├── img_000001.jpg
│   │   │   └── ...
│   │   └── labels/
│   │       ├── img_000001.txt
│   │       └── ...
│   ├── val/                          # 검증 세트 (10%)
│   │   ├── images/
│   │   └── labels/
│   └── test/                         # 테스트 세트 (10%)
│       ├── images/
│       └── labels/
├── manifests/                        # 데이터셋 매니페스트
│   ├── dataset_manifest.json         # 전체 데이터셋 메타정보
│   ├── label_map.json                # 클래스 ID ↔ 라벨 매핑
│   └── split_info.json               # train/val/test 분할 정보
└── README.md                         # 이 문서
```

---

## Label Format (KITTI)

TAO Toolkit 기본 라벨 형식인 KITTI format을 사용합니다.

```
{class_name} {truncated} {occluded} {alpha} {xmin} {ymin} {xmax} {ymax} {height} {width} {length} {x} {y} {z} {ry}
```

### Platform 1.0 간소화 사용

```
{class_name} 0.0 0 0.0 {xmin} {ymin} {xmax} {ymax} 0.0 0.0 0.0 0.0 0.0 0.0 0.0
```

### Class Names (6 classes)

| Class ID | Class Name | Description |
|----------|------------|-------------|
| 0 | person | 사람 (정상 상태) |
| 1 | fall | 낙상 |
| 2 | collapse | 쓰러짐 |
| 3 | fire | 화재 |
| 4 | intrusion | 위험구역 침입 |
| 5 | hazardous_action | 위험 행동 |

---

## Image Specifications

| Item | Value |
|------|-------|
| Resolution | 960 x 544 (TAO 기본) |
| Format | JPEG |
| Color Space | RGB |
| Naming | `img_{6-digit-seq}.jpg` |

---

## Data Split Ratio

| Split | Ratio | Purpose |
|-------|-------|---------|
| train | 80% | 모델 학습 |
| val | 10% | 학습 중 검증 |
| test | 10% | 최종 평가 |

---

## Clip Metadata Format

`raw/clips/{event_id}/metadata.json`:

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "camera_id": "CAM-001",
  "event_type": "FALL_DETECTED",
  "risk_level": "CRITICAL",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "duration_sec": 60,
  "pre_event_sec": 30,
  "post_event_sec": 30,
  "fps": 30,
  "resolution": {"width": 1920, "height": 1080},
  "model_version": "v1.0.0-tao-ds"
}
```

---

## Notes

- 원본 대용량 영상은 Git LFS 또는 NFS/S3로 관리
- `raw/` 디렉토리는 .gitignore에 포함 (실제 데이터 커밋 금지)
- `processed/` 디렉토리도 .gitignore에 포함
- `manifests/` 디렉토리의 스키마 정의 파일만 Git 관리
