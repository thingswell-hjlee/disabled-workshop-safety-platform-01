"""
Mock AWS Event Receiver
========================
AWS Cloud의 이벤트 수신을 시뮬레이션한다.
stream:cloud-queue를 소비하여 MQTT 페이로드로 변환하고 DB에 저장하는 흐름을 mock.

사용 흐름:
1. MockAwsReceiver 인스턴스 생성
2. consume_cloud_queue() → stream:cloud-queue에서 메시지 읽기
3. transform_to_mqtt() → MQTT 페이로드 형식으로 변환
4. store_event() → PostgreSQL 또는 in-memory 저장

Reference: docs/aws-iot-message-schema.md
"""

import json
from datetime import datetime, timezone
from typing import Optional


class MockAwsReceiver:
    """AWS Cloud의 이벤트 수신 및 처리를 시뮬레이션"""

    def __init__(self, redis_client, pg_connection=None):
        self.redis = redis_client
        self.pg_conn = pg_connection
        self.received_events: list = []
        self.mqtt_payloads: list = []
        self._consumer_group = "cg-aws-sync"
        self._consumer_name = "aws-sync-test"

    def setup_consumer_group(self):
        """Consumer group 생성 (이미 존재하면 무시)"""
        try:
            self.redis.xgroup_create(
                "stream:cloud-queue", self._consumer_group, id="0", mkstream=True
            )
        except Exception:
            pass  # Group already exists

    def consume_cloud_queue(self, count: int = 10, block: int = 1000) -> list:
        """
        stream:cloud-queue에서 메시지를 읽는다.
        
        Args:
            count: 한 번에 읽을 최대 메시지 수
            block: 블로킹 대기 시간 (ms)
            
        Returns:
            읽은 메시지 목록
        """
        messages = self.redis.xreadgroup(
            groupname=self._consumer_group,
            consumername=self._consumer_name,
            streams={"stream:cloud-queue": ">"},
            count=count,
            block=block,
        )

        result = []
        if messages:
            for stream_name, stream_messages in messages:
                for msg_id, msg_data in stream_messages:
                    self.received_events.append(msg_data)
                    result.append({"id": msg_id, "data": msg_data})
                    # ACK the message
                    self.redis.xack(
                        "stream:cloud-queue", self._consumer_group, msg_id
                    )
        return result

    def consume_all_pending(self) -> list:
        """
        stream:cloud-queue의 모든 메시지를 XRANGE로 읽는다 (consumer group 없이).
        테스트 검증용.
        """
        messages = self.redis.xrange("stream:cloud-queue", "-", "+")
        result = []
        for msg_id, msg_data in messages:
            result.append({"id": msg_id, "data": msg_data})
            self.received_events.append(msg_data)
        return result

    def transform_to_mqtt(self, cloud_msg: dict) -> dict:
        """
        stream:cloud-queue 메시지를 MQTT 페이로드로 변환.
        
        Reference: docs/aws-iot-message-schema.md Section 2.1
        
        Returns:
            MQTT safety/{site_id}/events 페이로드
        """
        confidence_str = cloud_msg.get("confidence", "")
        confidence = float(confidence_str) if confidence_str else None

        mqtt_payload = {
            "event_id": cloud_msg["event_id"],
            "site_id": cloud_msg["site_id"],
            "device_id": cloud_msg["device_id"],
            "worker_id": cloud_msg.get("worker_id") or None,
            "event_type": cloud_msg["event_type"],
            "risk_level": cloud_msg["risk_level"],
            "confidence": confidence,
            "model_version": cloud_msg.get("model_version") or None,
            "timestamp": cloud_msg["timestamp"],
            "context_summary": f"{cloud_msg['event_type']} event from {cloud_msg['device_id']}",
            "clip_s3_key": self._generate_s3_key(cloud_msg) if cloud_msg.get("clip_path") else None,
            "idempotency_key": cloud_msg["idempotency_key"],
        }

        self.mqtt_payloads.append(mqtt_payload)
        return mqtt_payload

    def _generate_s3_key(self, msg: dict) -> str:
        """S3 업로드 경로 생성: events/{site_id}/{YYYY}/{MM}/{DD}/{event_id}.mp4"""
        ts = msg.get("timestamp", "")
        try:
            dt = datetime.strptime(ts[:10], "%Y-%m-%d")
            return f"events/{msg['site_id']}/{dt.year}/{dt.month:02d}/{dt.day:02d}/{msg['event_id']}.mp4"
        except (ValueError, IndexError):
            return f"events/{msg['site_id']}/unknown/{msg['event_id']}.mp4"

    def store_event(self, mqtt_payload: dict) -> bool:
        """
        이벤트를 PostgreSQL에 저장 (또는 in-memory 저장).
        
        Returns:
            저장 성공 여부
        """
        if self.pg_conn is None:
            # In-memory storage for tests without PostgreSQL
            return True

        try:
            with self.pg_conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO safety_events 
                    (event_id, site_id, device_id, worker_id, event_type, 
                     risk_level, confidence, model_version, timestamp, event_state)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING
                    RETURNING id
                    """,
                    (
                        mqtt_payload["event_id"],
                        mqtt_payload["site_id"],
                        mqtt_payload["device_id"],
                        mqtt_payload.get("worker_id"),
                        mqtt_payload["event_type"],
                        mqtt_payload["risk_level"],
                        mqtt_payload.get("confidence"),
                        mqtt_payload.get("model_version"),
                        mqtt_payload["timestamp"],
                        "ACTIVE",
                    ),
                )
                result = cur.fetchone()
                return result is not None
        except Exception as e:
            print(f"DB storage error: {e}")
            return False

    def check_duplicate(self, event_id: str) -> bool:
        """
        중복 이벤트 검사 (idempotency check).
        
        Returns:
            True if duplicate exists
        """
        if self.pg_conn is None:
            # In-memory check
            return any(
                e.get("event_id") == event_id for e in self.received_events[:-1]
            )

        try:
            with self.pg_conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM safety_events WHERE event_id = %s",
                    (event_id,),
                )
                count = cur.fetchone()[0]
                return count > 0
        except Exception:
            return False

    def get_stored_events_count(self) -> int:
        """저장된 이벤트 수 조회"""
        if self.pg_conn is None:
            return len(self.received_events)

        try:
            with self.pg_conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM safety_events")
                return cur.fetchone()[0]
        except Exception:
            return 0
