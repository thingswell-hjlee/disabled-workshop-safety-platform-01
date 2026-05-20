# ONNX & TensorRT Engine Conversion Guide

> **Platform 1.0** | AI기반 장애인직업재활시설 스마트안전시스템
> **목적:** TAO 학습 모델 → ONNX → TensorRT Engine 변환 절차

---

## 1. 변환 파이프라인 개요

```
TAO Model (.tlt/.hdf5)
    ↓ [TAO export]
ONNX Model (.onnx)
    ↓ [trtexec]
TensorRT Engine (.engine)
    ↓ [deploy]
DeepStream (추론 서비스)
```

---

## 2. TAO → ONNX Export

### 2.1 TAO export 명령어

```bash
# TAO Docker 컨테이너 내에서 실행
tao model detectnet_v2 export \
  -m /workspace/experiments/detectnet_v2/weights/model.tlt \
  -o /workspace/models/export/safety_detector.onnx \
  -k tlt_encode \
  --data_type fp16 \
  --engine_file /workspace/models/export/safety_detector.engine \
  --cal_cache_file /workspace/models/export/cal.bin \
  --batch_size 8 \
  --max_batch_size 8 \
  --input_dims "3,544,960"
```

### 2.2 Export 매개변수

| 매개변수 | 값 | 설명 |
|----------|-----|------|
| `-m` | model.tlt 경로 | 학습 완료 모델 |
| `-o` | output.onnx 경로 | ONNX 출력 경로 |
| `-k` | tlt_encode | TAO 암호화 키 |
| `--data_type` | fp16 | 정밀도 (fp16/fp32/int8) |
| `--batch_size` | 8 | 배치 크기 (카메라 8대) |
| `--input_dims` | 3,544,960 | CHW 입력 차원 |

### 2.3 ONNX 검증

```bash
# ONNX 모델 정보 확인
python3 -c "
import onnx
model = onnx.load('/workspace/models/export/safety_detector.onnx')
onnx.checker.check_model(model)
print(f'Model IR version: {model.ir_version}')
print(f'Opset version: {model.opset_import[0].version}')
for inp in model.graph.input:
    print(f'Input: {inp.name}, shape: {[d.dim_value for d in inp.type.tensor_type.shape.dim]}')
for out in model.graph.output:
    print(f'Output: {out.name}')
"
```

---

## 3. ONNX → TensorRT Engine

### 3.1 trtexec 명령어

```bash
# TensorRT 컨테이너 내에서 실행
/usr/src/tensorrt/bin/trtexec \
  --onnx=/workspace/models/export/safety_detector.onnx \
  --saveEngine=/workspace/models/export/safety_detector_v1.0.0_fp16.engine \
  --fp16 \
  --workspace=4096 \
  --minShapes=input:1x3x544x960 \
  --optShapes=input:8x3x544x960 \
  --maxShapes=input:8x3x544x960 \
  --verbose
```

### 3.2 trtexec 매개변수

| 매개변수 | 값 | 설명 |
|----------|-----|------|
| `--onnx` | .onnx 경로 | ONNX 입력 모델 |
| `--saveEngine` | .engine 경로 | TensorRT engine 출력 |
| `--fp16` | (flag) | FP16 최적화 활성화 |
| `--workspace` | 4096 (MB) | GPU 메모리 할당 |
| `--minShapes` | 1x3x544x960 | 최소 배치 (단일 추론) |
| `--optShapes` | 8x3x544x960 | 최적 배치 (8카메라) |
| `--maxShapes` | 8x3x544x960 | 최대 배치 |

### 3.3 INT8 양자화 (선택사항)

```bash
# INT8 양자화 (캘리브레이션 데이터 필요)
/usr/src/tensorrt/bin/trtexec \
  --onnx=/workspace/models/export/safety_detector.onnx \
  --saveEngine=/workspace/models/export/safety_detector_v1.0.0_int8.engine \
  --int8 \
  --calib=/workspace/models/export/cal.bin \
  --workspace=4096 \
  --minShapes=input:1x3x544x960 \
  --optShapes=input:8x3x544x960 \
  --maxShapes=input:8x3x544x960
```

### 3.4 Engine 성능 벤치마크

```bash
# 성능 테스트
/usr/src/tensorrt/bin/trtexec \
  --loadEngine=/workspace/models/export/safety_detector_v1.0.0_fp16.engine \
  --batch=8 \
  --warmUp=500 \
  --duration=10 \
  --iterations=100
```

예상 출력:
```
[TensorRT] Throughput: XX.X qps
[TensorRT] Latency: min = X.XX ms, max = X.XX ms, mean = X.XX ms
```

---

## 4. 변환 스크립트

### 4.1 자동 변환 스크립트

`scripts/convert-model.sh` 사용:

```bash
# TAO → ONNX → TensorRT 전체 변환
./services/training-pipeline/scripts/convert-to-engine.sh \
  --model /path/to/model.tlt \
  --output /models/staged/v1.0.0-tao-ds/ \
  --precision fp16 \
  --batch-size 8

# ONNX → TensorRT만 실행
./services/training-pipeline/scripts/convert-to-engine.sh \
  --onnx /path/to/model.onnx \
  --output /models/staged/v1.0.0-tao-ds/ \
  --precision fp16 \
  --batch-size 8
```

---

## 5. 변환 결과 검증

### 5.1 필수 확인 항목

| 항목 | 검증 방법 | 합격 기준 |
|------|-----------|-----------|
| Engine 파일 생성 | `ls -la *.engine` | 파일 존재 & 크기 > 10MB |
| Engine 로드 가능 | trtexec --loadEngine | 에러 없음 |
| 추론 성능 | trtexec benchmark | FPS ≥ 30 (8 batch) |
| 정확도 | 테스트 이미지 추론 | mAP 변화 < 1% |

### 5.2 Checksum 생성

```bash
# 모델 패키지에 포함할 checksum 생성
sha256sum /models/staged/v1.0.0-tao-ds/model.engine | awk '{print "sha256:" $1}'
```

---

## 6. GPU 아키텍처 호환성

**중요:** TensorRT Engine은 빌드 시점의 GPU 아키텍처에 종속됩니다.

| 시나리오 | 대응 |
|----------|------|
| 학습서버 GPU = Edge GPU | 학습서버에서 변환 후 그대로 배포 |
| 학습서버 GPU ≠ Edge GPU | Edge 서버에서 ONNX → Engine 변환 필수 |
| 여러 Edge 서버 (동일 GPU) | 한 번 변환 후 복사 |
| 여러 Edge 서버 (다른 GPU) | 각 서버에서 개별 변환 |

### Platform 1.0 기준

- 학습 서버: RTX 3090 / A4000 (Ampere)
- Edge AI 서버: Jetson Orin 또는 동급 GPU
- **권장:** ONNX 형태로 전달 후 Edge에서 Engine 변환

---

## 7. 파일 명명 규칙

```
{model_name}_{version}_{precision}.{extension}
```

| 파일 | 예시 |
|------|------|
| ONNX | `safety_detector_v1.0.0.onnx` |
| FP16 Engine | `safety_detector_v1.0.0_fp16.engine` |
| INT8 Engine | `safety_detector_v1.0.0_int8.engine` |
| Calibration | `safety_detector_v1.0.0_cal.bin` |

---

## 8. 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| trtexec OOM | GPU 메모리 부족 | workspace 줄이기, batch 줄이기 |
| Unsupported op | ONNX opset 미지원 | TAO export 시 opset 버전 조정 |
| Engine 로드 실패 | GPU 아키텍처 불일치 | 대상 GPU에서 재변환 |
| 정확도 저하 > 5% | 양자화 오류 | 캘리브레이션 데이터 확대 |
| Shape mismatch | input_dims 불일치 | 입력 차원 확인 (3,544,960) |
