-- ============================================================
-- Platform 1.0 - PostgreSQL Database Schema (AWS RDS)
-- Reference: docs/data-model.md
--
-- Usage:
--   psql -h localhost -U safety_admin -d safety_platform -f init-schema.sql
--
-- NOTE: Platform 2.0/3.0 확장 필드는 nullable로 예약만 해둠
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. SITES
-- ============================================================
CREATE TABLE IF NOT EXISTS sites (
    site_id         VARCHAR(10)  PRIMARY KEY,  -- SITE-001
    name            VARCHAR(100) NOT NULL,
    address         VARCHAR(200) NOT NULL,
    timezone        VARCHAR(30)  NOT NULL DEFAULT 'Asia/Seoul',
    status          VARCHAR(10)  NOT NULL DEFAULT 'ACTIVE'
                    CHECK (status IN ('ACTIVE', 'INACTIVE')),
    config          JSONB,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 2. ZONES
-- ============================================================
CREATE TABLE IF NOT EXISTS zones (
    zone_id         VARCHAR(20)  PRIMARY KEY,
    site_id         VARCHAR(10)  NOT NULL REFERENCES sites(site_id),
    name            VARCHAR(50)  NOT NULL,
    zone_type       VARCHAR(20)  NOT NULL
                    CHECK (zone_type IN ('WORK', 'DANGER', 'REST', 'PASSAGE')),
    polygon         JSONB,
    camera_ids      JSONB,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 3. WORKERS
-- ============================================================
CREATE TABLE IF NOT EXISTS workers (
    worker_id       VARCHAR(10)  PRIMARY KEY,  -- WKR-0001
    site_id         VARCHAR(10)  NOT NULL REFERENCES sites(site_id),
    name            VARCHAR(50)  NOT NULL,
    band_device_id  VARCHAR(10),
    zone_id         VARCHAR(20),
    status          VARCHAR(10)  NOT NULL DEFAULT 'ACTIVE'
                    CHECK (status IN ('ACTIVE', 'INACTIVE', 'LEAVE')),
    emergency_contact VARCHAR(20),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 4. DEVICES
-- ============================================================
CREATE TABLE IF NOT EXISTS devices (
    device_id       VARCHAR(10)  PRIMARY KEY,  -- CAM-001, BAND-003
    site_id         VARCHAR(10)  NOT NULL REFERENCES sites(site_id),
    device_type     VARCHAR(20)  NOT NULL
                    CHECK (device_type IN (
                        'IP_CAMERA', 'SMART_BAND', 'ENV_SENSOR',
                        'FIRE_CONTACT', 'ALARM_DEVICE', 'NVR'
                    )),
    name            VARCHAR(50)  NOT NULL,
    zone_id         VARCHAR(20),
    status          VARCHAR(20)  NOT NULL DEFAULT 'CONNECTED'
                    CHECK (status IN ('CONNECTED', 'DISCONNECTED', 'ERROR', 'MAINTENANCE')),
    ip_address      VARCHAR(15),
    firmware_version VARCHAR(20),
    last_heartbeat  TIMESTAMP WITH TIME ZONE,
    metadata        JSONB,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 5. EVENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS events (
    event_id        VARCHAR(25)  PRIMARY KEY,  -- EVT-YYYYMMDDHHmmss-SEQ
    site_id         VARCHAR(10)  NOT NULL REFERENCES sites(site_id),
    device_id       VARCHAR(10)  NOT NULL REFERENCES devices(device_id),
    worker_id       VARCHAR(10),
    event_type      VARCHAR(30)  NOT NULL
                    CHECK (event_type IN (
                        'FALL_DETECTED', 'COLLAPSE_DETECTED', 'ZONE_INTRUSION',
                        'STILLNESS_DETECTED', 'HAZARDOUS_ACTION', 'FIRE_DETECTED',
                        'HEARTRATE_ABNORMAL', 'TEMPERATURE_ABNORMAL',
                        'BAND_FALL_DETECTED', 'BAND_DISCONNECTED',
                        'ENV_THRESHOLD_EXCEEDED', 'DEVICE_OFFLINE', 'DEVICE_ONLINE',
                        'NORMAL_RESTORED', 'SYSTEM_ALERT'
                    )),
    risk_level      VARCHAR(10)  NOT NULL
                    CHECK (risk_level IN ('CRITICAL', 'WARNING', 'NORMAL')),
    confidence      FLOAT,
    model_version   VARCHAR(30),
    timestamp       TIMESTAMP WITH TIME ZONE NOT NULL,
    state           VARCHAR(15)  NOT NULL DEFAULT 'ACTIVE'
                    CHECK (state IN ('ACTIVE', 'ACKNOWLEDGED', 'ARCHIVED')),
    context_summary TEXT,
    acknowledged_by VARCHAR(30),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    ack_reason      TEXT,
    clip_path       VARCHAR(200),
    clip_s3_key     VARCHAR(200),
    idempotency_key VARCHAR(50)  NOT NULL UNIQUE,
    synced_to_cloud BOOLEAN      NOT NULL DEFAULT FALSE,
    -- Platform 2.0 reserved
    feedback_type   VARCHAR(20)
                    CHECK (feedback_type IN ('TRUE_POSITIVE', 'FALSE_POSITIVE', 'MISSED') OR feedback_type IS NULL),
    -- Platform 3.0 reserved
    reanalysis_result JSONB,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_events_site_timestamp ON events(site_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_risk_level ON events(risk_level);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_state ON events(state);
CREATE INDEX IF NOT EXISTS idx_events_device_id ON events(device_id);
CREATE INDEX IF NOT EXISTS idx_events_worker_id ON events(worker_id);
CREATE INDEX IF NOT EXISTS idx_events_synced ON events(synced_to_cloud) WHERE synced_to_cloud = FALSE;

-- ============================================================
-- 6. EVENT_CONTEXT
-- ============================================================
CREATE TABLE IF NOT EXISTS event_contexts (
    context_id      VARCHAR(30)  PRIMARY KEY,
    event_id        VARCHAR(25)  NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    video_clip      JSONB,
    sensor_snapshot JSONB,
    inference_detail JSONB,
    system_state    JSONB,
    activity_index  FLOAT,
    quality_level   INT          NOT NULL DEFAULT 0,
    buffer_duration_sec INT      NOT NULL DEFAULT 60,
    -- Platform 2.0/3.0 reserved
    extended_context JSONB,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_event_contexts_event_id ON event_contexts(event_id);

-- ============================================================
-- 7. MODEL_VERSIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS model_versions (
    model_version   VARCHAR(30)  PRIMARY KEY,  -- v1.0.0-tao-ds
    site_id         VARCHAR(10)  NOT NULL REFERENCES sites(site_id),
    model_type      VARCHAR(20)  NOT NULL
                    CHECK (model_type IN ('PGIE_DETECTION', 'SGIE_ACTION', 'CUSTOM')),
    model_name      VARCHAR(50)  NOT NULL,
    framework       VARCHAR(10)  NOT NULL
                    CHECK (framework IN ('TENSORRT', 'ONNX', 'TAO')),
    precision       VARCHAR(5)   NOT NULL
                    CHECK (precision IN ('FP16', 'INT8', 'FP32')),
    engine_path     VARCHAR(200) NOT NULL,
    file_size_mb    FLOAT,
    trained_at      TIMESTAMP WITH TIME ZONE,
    dataset_id      VARCHAR(30),
    metrics         JSONB,
    status          VARCHAR(10)  NOT NULL DEFAULT 'STAGED'
                    CHECK (status IN ('STAGED', 'ACTIVE', 'ROLLBACK', 'ARCHIVED')),
    deployed_at     TIMESTAMP WITH TIME ZONE,
    s3_key          VARCHAR(200),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 8. DEVICE_HEALTH
-- ============================================================
CREATE TABLE IF NOT EXISTS device_health (
    health_id       VARCHAR(40)  PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    device_id       VARCHAR(10)  NOT NULL REFERENCES devices(device_id),
    site_id         VARCHAR(10)  NOT NULL REFERENCES sites(site_id),
    timestamp       TIMESTAMP WITH TIME ZONE NOT NULL,
    status          VARCHAR(20)  NOT NULL
                    CHECK (status IN ('CONNECTED', 'DISCONNECTED', 'ERROR')),
    metrics         JSONB,
    gpu_metrics     JSONB,
    error_message   TEXT,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_device_health_device_ts ON device_health(device_id, timestamp DESC);

-- ============================================================
-- 9. EDGE_STATUS (for safety/{site_id}/status messages)
-- ============================================================
CREATE TABLE IF NOT EXISTS edge_status (
    id              SERIAL PRIMARY KEY,
    site_id         VARCHAR(10)  NOT NULL REFERENCES sites(site_id),
    timestamp       TIMESTAMP WITH TIME ZONE NOT NULL,
    edge_status     VARCHAR(10)  NOT NULL
                    CHECK (edge_status IN ('HEALTHY', 'DEGRADED', 'ERROR')),
    deepstream_fps  JSONB        NOT NULL,
    gpu_utilization FLOAT        NOT NULL,
    active_cameras  INT          NOT NULL,
    active_bands    INT          NOT NULL,
    pending_cloud_events INT     NOT NULL DEFAULT 0,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_edge_status_site_ts ON edge_status(site_id, timestamp DESC);
