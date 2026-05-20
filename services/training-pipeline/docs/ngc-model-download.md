# NGC CLI & Pretrained Model Download Guide

> **Platform 1.0** | AI기반 장애인직업재활시설 스마트안전시스템
> **목적:** NGC CLI 설치, 인증, 사전학습 모델 다운로드

---

## 1. NGC CLI 설치

### 1.1 Linux (학습 서버)

```bash
# NGC CLI 다운로드
wget -q https://api.ngc.nvidia.com/v2/resources/nvidia/ngc-apps/ngc_cli/versions/3.41.2/files/ngccli_linux.zip -O /tmp/ngccli.zip

# 설치
unzip -q /tmp/ngccli.zip -d /usr/local/bin/
chmod +x /usr/local/bin/ngc-cli/ngc

# PATH 추가 (~/.bashrc 또는 ~/.profile)
echo 'export PATH="/usr/local/bin/ngc-cli:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 버전 확인
ngc --version
```

### 1.2 Docker 내 설치 (Dockerfile에 포함)

```dockerfile
# NGC CLI in Docker
RUN wget -q https://api.ngc.nvidia.com/v2/resources/nvidia/ngc-apps/ngc_cli/versions/3.41.2/files/ngccli_linux.zip -O /tmp/ngccli.zip \
    && unzip -q /tmp/ngccli.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/ngc-cli/ngc \
    && rm /tmp/ngccli.zip
```

---

## 2. NGC 인증 설정

### 2.1 API Key 발급

1. https://ngc.nvidia.com 로그인
2. 우측 상단 프로필 → "Setup" 클릭
3. "API Key" → "Generate API Key" 클릭
4. 생성된 키를 안전하게 보관

### 2.2 NGC CLI 인증

```bash
# 대화형 설정
ngc config set

# 입력 항목:
# API key: <발급받은 API Key>
# CLI output format: json
# org: nvidia (기본)
# team: no-team (기본)
# ace: no-ace (기본)
```

### 2.3 환경변수 기반 인증 (CI/CD용)

```bash
# .env (절대 커밋 금지)
export NGC_API_KEY=<your-ngc-api-key>

# Docker 실행 시 전달
docker run --rm \
  -e NGC_API_KEY=$NGC_API_KEY \
  nvcr.io/nvidia/tao/tao-toolkit:5.5.0-tf2.11.0 \
  ngc registry model list
```

### 2.4 Docker Registry 인증 (nvcr.io)

```bash
# nvcr.io 로그인
docker login nvcr.io
# Username: $oauthtoken
# Password: <NGC API Key>
```

---

## 3. Platform 1.0 사전학습 모델

### 3.1 추천 모델 목록

| 모델 | NGC Path | 용도 | 크기 |
|------|----------|------|------|
| PeopleNet v2.6 | `nvidia/tao/peoplenet:trainable_v2.6` | 사람 감지 (Base) | ~180MB |
| ActionRecognitionNet | `nvidia/tao/actionrecognitionnet:trainable_v2.0` | 행동 인식 | ~250MB |
| YOLOv4 | `nvidia/tao/pretrained_object_detection:yolov4` | 객체 감지 (범용) | ~240MB |
| DetectNet_v2 | `nvidia/tao/pretrained_detectnet_v2:resnet18` | 감지 (경량) | ~90MB |

### 3.2 Primary Model: PeopleNet (권장)

Platform 1.0 안전 감지의 Base 모델로 **PeopleNet v2.6**을 사용합니다.
- 사람 감지에 최적화된 사전학습 모델
- Fine-tuning으로 낙상/쓰러짐/위험행동 감지 확장 가능
- DeepStream 바로 배포 가능한 구조

---

## 4. 모델 다운로드

### 4.1 NGC CLI로 다운로드

```bash
# PeopleNet v2.6 (학습 가능 모델)
ngc registry model download-version \
  nvidia/tao/peoplenet:trainable_v2.6 \
  --dest /workspace/models/pretrained/

# DetectNet_v2 ResNet18 (경량 대안)
ngc registry model download-version \
  nvidia/tao/pretrained_detectnet_v2:resnet18 \
  --dest /workspace/models/pretrained/
```

### 4.2 스크립트를 통한 다운로드

`scripts/download-ngc-model.sh`를 사용합니다:

```bash
# PeopleNet 다운로드
./scripts/download-ngc-model.sh peoplenet

# DetectNet_v2 다운로드
./scripts/download-ngc-model.sh detectnet_v2

# 모든 권장 모델 다운로드
./scripts/download-ngc-model.sh all
```

### 4.3 다운로드 결과 구조

```
models/pretrained/
├── peoplenet_v2.6/
│   ├── model.tlt              # TAO 암호화 모델 파일
│   ├── labels.txt             # 클래스 라벨
│   └── README.md              # 모델 설명
└── detectnet_v2_resnet18/
    ├── model.tlt
    ├── labels.txt
    └── README.md
```

---

## 5. 다운로드 검증

```bash
# 파일 존재 확인
ls -la models/pretrained/peoplenet_v2.6/

# 파일 크기 확인 (model.tlt > 50MB)
stat --printf="%s bytes\n" models/pretrained/peoplenet_v2.6/model.tlt

# NGC 모델 정보 확인
ngc registry model info nvidia/tao/peoplenet:trainable_v2.6
```

---

## 6. 보안 주의사항

| 항목 | 규칙 |
|------|------|
| NGC API Key | 절대 Git 커밋 금지 |
| ~/.ngc/config | .gitignore에 포함 |
| Docker login 정보 | ~/.docker/config.json 보호 |
| 환경변수 | .env 파일 사용, .env.example만 커밋 |

### .env.example (커밋 가능)

```bash
# NGC Configuration
NGC_API_KEY=<your-ngc-api-key-here>
NGC_ORG=nvidia
NGC_TEAM=no-team
```

---

## 7. 오프라인 환경 대응

인터넷 연결이 불가한 현장에서는:

1. 외부 네트워크에서 모델 다운로드
2. USB/외장 디스크로 학습 서버에 복사
3. `/workspace/models/pretrained/` 경로에 배치

```bash
# USB에서 복사
cp -r /media/usb/models/pretrained/* models/pretrained/
```

---

## 참고

- NGC Registry: https://catalog.ngc.nvidia.com/
- TAO Toolkit Docs: https://docs.nvidia.com/tao/tao-toolkit/
- Platform 1.0 모델은 `v1.0.0-pretrained-ds` 버전으로 시작
- Fine-tuning 후 `v1.0.0-tao-ds`로 버전 갱신
