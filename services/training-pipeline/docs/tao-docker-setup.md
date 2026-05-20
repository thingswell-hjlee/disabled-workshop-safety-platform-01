# TAO Toolkit Docker Setup Guide

> **Platform 1.0** | AI기반 장애인직업재활시설 스마트안전시스템
> **대상 서버:** 로컬 AI 엣지 학습·최적화 서버

---

## 1. 시스템 요구사항

| 항목 | 최소 사양 | 권장 사양 |
|------|-----------|-----------|
| OS | Ubuntu 20.04 LTS | Ubuntu 22.04 LTS |
| GPU | NVIDIA GPU (Turing+) | RTX 3090 / A4000 이상 |
| VRAM | 8GB | 16GB 이상 |
| RAM | 16GB | 32GB 이상 |
| Disk | 100GB SSD | 500GB NVMe SSD |
| Docker | 24.0+ | 최신 안정 버전 |
| NVIDIA Driver | 535+ | 545+ |
| CUDA | 12.2+ | 12.4+ |

---

## 2. 사전 설치 항목

### 2.1 NVIDIA Driver 설치

```bash
# Ubuntu 22.04
sudo apt-get update
sudo apt-get install -y nvidia-driver-545
sudo reboot

# 설치 확인
nvidia-smi
```

### 2.2 Docker 설치

```bash
# Docker Engine 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# 확인
docker --version
```

### 2.3 NVIDIA Container Toolkit 설치

```bash
# Repository 추가
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 설치
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 확인
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

---

## 3. TAO Toolkit Docker 환경

### 3.1 TAO Toolkit Container 정보

| 항목 | 값 |
|------|-----|
| Registry | `nvcr.io/nvidia/tao/tao-toolkit` |
| Tag (권장) | `5.5.0-tf2.11.0` (Object Detection) |
| Alternative | `5.5.0-pyt2.1.0` (PyTorch 기반) |
| Purpose | 모델 학습, 평가, Export |

### 3.2 TAO Docker 실행 스크립트

`scripts/setup-tao-docker.sh`를 사용하여 TAO 환경을 구성합니다:

```bash
# 기본 실행 (대화형)
./scripts/setup-tao-docker.sh interactive

# 학습 작업 실행
./scripts/setup-tao-docker.sh train <spec_file>

# Export (ONNX 변환)
./scripts/setup-tao-docker.sh export <model_path> <output_path>
```

### 3.3 Volume Mount 구조

```
Host Path                              → Container Path
─────────────────────────────────────────────────────────
services/training-pipeline/datasets/   → /workspace/datasets/
services/training-pipeline/configs/    → /workspace/configs/
models/                                → /workspace/models/
/tmp/tao-experiments/                  → /workspace/experiments/
```

### 3.4 TAO Toolkit 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `KEY` | TAO encryption key | `tlt_encode` |
| `NUM_GPUS` | 사용 GPU 수 | `1` |
| `GPU_INDEX` | GPU 디바이스 인덱스 | `0` |

---

## 4. TensorRT Container (Engine 변환용)

### 4.1 Container 정보

| 항목 | 값 |
|------|-----|
| Registry | `nvcr.io/nvidia/tensorrt` |
| Tag (권장) | `24.05-py3` |
| Purpose | ONNX → TensorRT Engine 변환 |

### 4.2 Edge AI 서버와 동일 환경 유지

**중요:** TensorRT Engine은 생성된 GPU 아키텍처에 종속됩니다.
- 학습 서버와 Edge AI 서버의 GPU 아키텍처가 다를 경우, Edge 서버에서 직접 변환해야 합니다.
- 동일 GPU인 경우 학습 서버에서 변환 후 전달 가능합니다.

---

## 5. Docker Compose (학습 서버)

`docker-compose.training.yml`:

```yaml
version: '3.8'

services:
  tao-toolkit:
    image: nvcr.io/nvidia/tao/tao-toolkit:5.5.0-tf2.11.0
    container_name: safety-tao-training
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - KEY=tlt_encode
    volumes:
      - ./services/training-pipeline/datasets:/workspace/datasets
      - ./services/training-pipeline/configs:/workspace/configs
      - ./models:/workspace/models
      - /tmp/tao-experiments:/workspace/experiments
    working_dir: /workspace
    shm_size: '8g'
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  tensorrt-converter:
    image: nvcr.io/nvidia/tensorrt:24.05-py3
    container_name: safety-tensorrt-converter
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    volumes:
      - ./models:/workspace/models
      - ./services/training-pipeline/configs:/workspace/configs
    working_dir: /workspace
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

---

## 6. 환경 검증 체크리스트

```bash
# 1. GPU 확인
nvidia-smi

# 2. Docker GPU 접근 확인
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi

# 3. NGC 로그인 확인
docker login nvcr.io

# 4. TAO Container Pull 확인
docker pull nvcr.io/nvidia/tao/tao-toolkit:5.5.0-tf2.11.0

# 5. Disk 용량 확인 (최소 100GB 여유)
df -h /

# 6. 메모리 확인 (최소 16GB)
free -h
```

---

## 7. 문제 해결 (Troubleshooting)

| 증상 | 원인 | 해결 |
|------|------|------|
| `nvidia-smi` 실패 | 드라이버 미설치/미로드 | 드라이버 재설치 후 reboot |
| Docker GPU 접근 불가 | nvidia-container-toolkit 미설치 | Section 2.3 재실행 |
| `nvcr.io` Pull 실패 | NGC 인증 미설정 | NGC API Key 설정 (docs/ngc-model-download.md 참조) |
| OOM (Out of Memory) | VRAM 부족 | batch_size 줄이기 또는 image_size 축소 |
| Permission Denied | Docker socket 권한 | `sudo usermod -aG docker $USER` |

---

## 주의사항

- NGC API Key는 절대 Git에 커밋하지 않습니다.
- `.env.example`에 설정 방법만 기록합니다.
- 실제 키는 서버의 `~/.ngc/config` 또는 환경변수로 관리합니다.
