-- ============================================================
-- Platform 1.0 - Seed Data (초기 데이터)
-- Reference: docs/data-model.md
--
-- 단일 사이트(SITE-001) 기준 기본 장비 등록
-- ============================================================

-- 1. Site
INSERT INTO sites (site_id, name, address, timezone, status)
VALUES ('SITE-001', '장애인직업재활시설 A', '서울특별시 강남구 테헤란로 123', 'Asia/Seoul', 'ACTIVE')
ON CONFLICT (site_id) DO NOTHING;

-- 2. Zones
INSERT INTO zones (zone_id, site_id, name, zone_type) VALUES
('ZONE-A', 'SITE-001', '작업장 A', 'WORK'),
('ZONE-B', 'SITE-001', '작업장 B', 'WORK'),
('ZONE-C', 'SITE-001', '장비실', 'DANGER'),
('ZONE-D', 'SITE-001', '휴게실', 'REST'),
('ZONE-E', 'SITE-001', '복도', 'PASSAGE')
ON CONFLICT (zone_id) DO NOTHING;

-- 3. Devices - IP Cameras (8)
INSERT INTO devices (device_id, site_id, device_type, name, zone_id, status) VALUES
('CAM-001', 'SITE-001', 'IP_CAMERA', '작업장A 북측', 'ZONE-A', 'CONNECTED'),
('CAM-002', 'SITE-001', 'IP_CAMERA', '작업장A 남측', 'ZONE-A', 'CONNECTED'),
('CAM-003', 'SITE-001', 'IP_CAMERA', '작업장B 북측', 'ZONE-B', 'CONNECTED'),
('CAM-004', 'SITE-001', 'IP_CAMERA', '작업장B 남측', 'ZONE-B', 'CONNECTED'),
('CAM-005', 'SITE-001', 'IP_CAMERA', '장비실 입구', 'ZONE-C', 'CONNECTED'),
('CAM-006', 'SITE-001', 'IP_CAMERA', '장비실 내부', 'ZONE-C', 'CONNECTED'),
('CAM-007', 'SITE-001', 'IP_CAMERA', '복도 1', 'ZONE-E', 'CONNECTED'),
('CAM-008', 'SITE-001', 'IP_CAMERA', '복도 2', 'ZONE-E', 'CONNECTED')
ON CONFLICT (device_id) DO NOTHING;

-- 4. Devices - Smart Bands (8)
INSERT INTO devices (device_id, site_id, device_type, name, status) VALUES
('BAND-001', 'SITE-001', 'SMART_BAND', '밴드 #1', 'CONNECTED'),
('BAND-002', 'SITE-001', 'SMART_BAND', '밴드 #2', 'CONNECTED'),
('BAND-003', 'SITE-001', 'SMART_BAND', '밴드 #3', 'CONNECTED'),
('BAND-004', 'SITE-001', 'SMART_BAND', '밴드 #4', 'CONNECTED'),
('BAND-005', 'SITE-001', 'SMART_BAND', '밴드 #5', 'CONNECTED'),
('BAND-006', 'SITE-001', 'SMART_BAND', '밴드 #6', 'CONNECTED'),
('BAND-007', 'SITE-001', 'SMART_BAND', '밴드 #7', 'CONNECTED'),
('BAND-008', 'SITE-001', 'SMART_BAND', '밴드 #8', 'CONNECTED')
ON CONFLICT (device_id) DO NOTHING;

-- 5. Devices - Environment Sensors (2)
INSERT INTO devices (device_id, site_id, device_type, name, zone_id, status) VALUES
('ENV-001', 'SITE-001', 'ENV_SENSOR', '환경센서 A구역', 'ZONE-A', 'CONNECTED'),
('ENV-002', 'SITE-001', 'ENV_SENSOR', '환경센서 B구역', 'ZONE-B', 'CONNECTED')
ON CONFLICT (device_id) DO NOTHING;

-- 6. Devices - Fire Contact (1)
INSERT INTO devices (device_id, site_id, device_type, name, status) VALUES
('FIRE-001', 'SITE-001', 'FIRE_CONTACT', '화재감지 접점', 'CONNECTED')
ON CONFLICT (device_id) DO NOTHING;

-- 7. Devices - Alarm (1)
INSERT INTO devices (device_id, site_id, device_type, name, status) VALUES
('ALARM-001', 'SITE-001', 'ALARM_DEVICE', '사이렌/경광등', 'CONNECTED')
ON CONFLICT (device_id) DO NOTHING;

-- 8. Devices - NVR (1)
INSERT INTO devices (device_id, site_id, device_type, name, status) VALUES
('NVR-001', 'SITE-001', 'NVR', '8채널 NVR', 'CONNECTED')
ON CONFLICT (device_id) DO NOTHING;

-- 9. Workers (sample 8)
INSERT INTO workers (worker_id, site_id, name, band_device_id, zone_id, status) VALUES
('WKR-0001', 'SITE-001', '김철수', 'BAND-001', 'ZONE-A', 'ACTIVE'),
('WKR-0002', 'SITE-001', '이영희', 'BAND-002', 'ZONE-A', 'ACTIVE'),
('WKR-0003', 'SITE-001', '박민수', 'BAND-003', 'ZONE-B', 'ACTIVE'),
('WKR-0004', 'SITE-001', '정은지', 'BAND-004', 'ZONE-B', 'ACTIVE'),
('WKR-0005', 'SITE-001', '최지훈', 'BAND-005', 'ZONE-A', 'ACTIVE'),
('WKR-0006', 'SITE-001', '한소영', 'BAND-006', 'ZONE-B', 'ACTIVE'),
('WKR-0007', 'SITE-001', '강태원', 'BAND-007', 'ZONE-A', 'ACTIVE'),
('WKR-0008', 'SITE-001', '윤미래', 'BAND-008', 'ZONE-B', 'ACTIVE')
ON CONFLICT (worker_id) DO NOTHING;

-- 10. Model Versions (initial)
INSERT INTO model_versions (model_version, site_id, model_type, model_name, framework, precision, engine_path, status, deployed_at)
VALUES
('v1.0.0-tao-ds', 'SITE-001', 'PGIE_DETECTION', 'PeopleNet', 'TENSORRT', 'FP16',
 '/models/active/pgie/peoplenet_v1.0.0_fp16.engine', 'ACTIVE', NOW()),
('v1.0.0-tao-ds', 'SITE-001', 'SGIE_ACTION', 'ActionRecognitionNet', 'TENSORRT', 'FP16',
 '/models/active/sgie/actionrecog_v1.0.0_fp16.engine', 'ACTIVE', NOW())
ON CONFLICT (model_version) DO NOTHING;
