-- Platform 1.0 Integration Test - Database Schema
-- This creates the minimal tables needed for event storage testing

CREATE TABLE IF NOT EXISTS safety_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(30) UNIQUE NOT NULL,
    site_id VARCHAR(10) NOT NULL,
    device_id VARCHAR(10) NOT NULL,
    worker_id VARCHAR(10),
    event_type VARCHAR(30) NOT NULL,
    risk_level VARCHAR(10) NOT NULL,
    confidence FLOAT,
    model_version VARCHAR(30),
    timestamp TIMESTAMPTZ NOT NULL,
    event_state VARCHAR(15) NOT NULL DEFAULT 'ACTIVE',
    context JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_site_id ON safety_events(site_id);
CREATE INDEX idx_events_event_type ON safety_events(event_type);
CREATE INDEX idx_events_risk_level ON safety_events(risk_level);
CREATE INDEX idx_events_timestamp ON safety_events(timestamp);
CREATE INDEX idx_events_device_id ON safety_events(device_id);

-- Duplicate event check constraint
CREATE UNIQUE INDEX idx_events_idempotency ON safety_events(event_id);
