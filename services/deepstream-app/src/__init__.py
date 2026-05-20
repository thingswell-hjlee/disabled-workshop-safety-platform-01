"""
DeepStream 8-Channel Safety Pipeline Application

Platform 1.0 Edge AI 추론 서버 - DeepStream 기반 실시간 영상 분석 파이프라인.
8채널 RTSP 카메라 입력을 처리하고, AI 추론 결과를 Redis Streams에 발행합니다.

Mock mode: GPU/DeepStream 없이 이벤트 발행 테스트 가능
"""

__version__ = "1.0.0"
