# Security Baseline - Platform 1.0

## 1. 보안 원칙

| 원칙 | 적용 |
|------|------|
| **최소 권한** | IAM 역할·정책은 필요 최소한으로 설정 |
| **전송 암호화** | 모든 외부 통신 TLS 1.2+ |
| **저장 암호화** | S3 SSE, RDS 암호화, 인증서 파일 보호 |
| **인증 필수** | 모든 API 접근에 인증 토큰 필요 |
| **감사 추적** | 접근 로그 90일 보관 |
| **Secret 분리** | 코드에 Secret 포함 금지 |

## 2. 네트워크 보안

### 2.1 Edge ↔ Cloud 통신

| 통신 경로 | 프로토콜 | 인증 | 암호화 |
|-----------|----------|------|--------|
| Edge → IoT Core | MQTT 8883 | X.509 인증서 | TLS 1.2 |
| Edge → S3 | HTTPS 443 | IAM STS 토큰 | TLS 1.2 |
| Browser → Dashboard | HTTPS 443 | JWT 토큰 | TLS 1.2 |
| Edge 내부 서비스 간 | Redis 6379 | 비밀번호 | 로컬 통신 (비암호화) |

### 2.2 방화벽 규칙 (Edge)

| 방향 | 포트 | 출발지 | 용도 |
|------|------|--------|------|
| Inbound | 443 | 관리 네트워크 | 대시보드 접근 |
| Inbound | 1883 | 센서 VLAN | MQTT (내부) |
| Outbound | 8883 | Edge Server | AWS IoT Core |
| Outbound | 443 | Edge Server | AWS S3/API |
| Block | * | * | 그 외 모든 통신 차단 |

## 3. 인증·인가

### 3.1 사용자 인증

| 항목 | 설정 |
|------|------|
| 인증 방식 | ID/Password + JWT |
| 비밀번호 저장 | bcrypt (cost=12) |
| JWT 만료 | 30분 (access), 7일 (refresh) |
| 세션 관리 | Redis 기반 세션 저장 |
| 계정 잠금 | 5회 실패 → 15분 잠금 |

### 3.2 서비스 간 인증

| 통신 | 인증 방식 |
|------|-----------|
| Edge → AWS IoT | X.509 인증서 (장치별 고유) |
| Edge → AWS S3 | IAM Role (STS AssumeRole) |
| Dashboard API | JWT Bearer Token |
| 내부 서비스 | Redis AUTH 비밀번호 |

### 3.3 IAM 정책 (최소 권한)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::safety-platform-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Publish",
        "iot:Connect"
      ],
      "Resource": "arn:aws:iot:*:*:topic/safety/*"
    }
  ]
}
```

## 4. 데이터 보안

### 4.1 개인정보 보호

| 데이터 유형 | 분류 | 보호 조치 |
|-------------|------|-----------|
| 영상 데이터 | 개인영상정보 | 접근제어, 90일 자동 삭제, 암호화 저장 |
| 생체 데이터 (심박, 체온) | 민감정보 | 전송 암호화, 접근제어, 동의 필수 |
| 위치 데이터 | 개인위치정보 | 접근제어, 목적 외 사용 금지 |
| 작업자 ID | 식별정보 | 최소 수집, 접근제어 |

### 4.2 데이터 보관 정책

| 데이터 | 보관 기간 | 삭제 방법 |
|--------|-----------|-----------|
| 이벤트 로그 | 1년 | S3 수명주기 자동 삭제 |
| 영상 클립 | 90일 | S3 수명주기 → Glacier → 삭제 |
| 접근 로그 | 90일 | CloudWatch 보관 정책 |
| 생체 원시 데이터 | 30일 | Edge 로컬 자동 삭제 |
| AI 모델 | 영구 | 버전 관리 유지 |

### 4.3 암호화

| 대상 | 방식 |
|------|------|
| S3 저장 | SSE-S3 (AES-256) |
| RDS 저장 | AWS KMS 암호화 |
| 전송 | TLS 1.2+ |
| 비밀번호 | bcrypt |
| JWT | HS256 (Secret Key) |

## 5. Secret 관리

### 5.1 금지 사항

- **절대 금지**: 코드에 Secret, Password, Key, 인증서 하드코딩
- **절대 금지**: .env 파일 Git 커밋
- **절대 금지**: 로그에 Secret 출력
- **절대 금지**: 클라이언트(Frontend)에 Secret 노출

### 5.2 관리 방법

| 환경 | Secret 저장 | 접근 방법 |
|------|------------|-----------|
| 개발 | .env.example (템플릿만) | 로컬 .env 파일 |
| Edge 운영 | /etc/safety-platform/.env | Docker env_file |
| Cloud 운영 | AWS Secrets Manager | ECS Task Role |
| IoT 인증서 | AWS IoT 콘솔 | 장치 프로비저닝 |

## 6. 감사·로깅

### 6.1 감사 로그 항목

| 이벤트 | 기록 내용 |
|--------|-----------|
| 로그인 성공/실패 | user_id, IP, 시각, 결과 |
| 알람 해제 | user_id, event_id, 시각, 사유 |
| 설정 변경 | user_id, 변경 항목, 이전/이후 값 |
| 모델 배포 | user_id, model_version, 시각 |
| API 호출 | method, path, user_id, status, 시각 |

### 6.2 로그 보호

- 로그 파일 권한: 640 (owner: root, group: docker)
- 로그 위변조 방지: 중앙 수집 후 S3 Object Lock
- 로그 접근: 관리자 권한 필요

## 7. 취약점 관리

### 7.1 컨테이너 보안

| 항목 | 조치 |
|------|------|
| Base Image | 공식 이미지, 최신 패치 적용 |
| 취약점 스캔 | GitHub Dependabot, Trivy 스캔 |
| 권한 | Non-root 사용자로 실행 |
| 시크릿 | 빌드 타임에 Secret 포함 금지 |

### 7.2 정기 점검

| 주기 | 항목 |
|------|------|
| 주간 | 의존성 취약점 스캔 |
| 월간 | IAM 권한 리뷰 |
| 분기 | 인증서 만료 확인 |
| 연간 | 보안 감사 (외부) |

---

*버전: 0.1 | 작성일: 2025-05-19*
