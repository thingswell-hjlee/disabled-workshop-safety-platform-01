"""
Model Package Schema Validation Tests
=======================================
모델 레지스트리, 메타데이터, 버전 명명 규칙 검증.
Reference: docs/model-package-schema.md
"""

import pytest
from pydantic import ValidationError

from tests.schema.models import ModelEntry, ModelMetrics, ModelRegistry


# ──────────────────────────────────────────────────────────────────────
# Model Registry Tests
# ──────────────────────────────────────────────────────────────────────


class TestModelRegistry:
    """registry.json schema validation"""

    @pytest.mark.model
    @pytest.mark.schema
    def test_valid_registry(self, model_registry):
        """Valid model registry passes validation"""
        registry_data = {
            "schema_version": model_registry["schema_version"],
            "site_id": model_registry["site_id"],
            "last_updated": model_registry["last_updated"],
            "models": model_registry["models"],
        }
        result = ModelRegistry(**registry_data)
        assert result.schema_version == "1.0"
        assert result.site_id == "SITE-001"
        assert len(result.models) == 2

    @pytest.mark.model
    @pytest.mark.schema
    def test_registry_active_model(self, model_registry):
        """Active model entry has correct structure"""
        active_model = model_registry["models"][0]
        result = ModelEntry(**active_model)
        assert result.status == "ACTIVE"
        assert result.model_version == "v1.0.0-tao-ds"
        assert result.model_type == "pgie"
        assert result.framework == "TAO"
        assert result.precision == "FP16"

    @pytest.mark.model
    @pytest.mark.schema
    def test_registry_rollback_model(self, model_registry):
        """Rollback model entry has correct structure"""
        rollback_model = model_registry["models"][1]
        result = ModelEntry(**rollback_model)
        assert result.status == "ROLLBACK"
        assert result.model_version == "v0.9.0-pretrained-ds"


# ──────────────────────────────────────────────────────────────────────
# Model Entry Field Tests
# ──────────────────────────────────────────────────────────────────────


class TestModelEntry:
    """Individual model entry validation"""

    @pytest.mark.model
    @pytest.mark.schema
    @pytest.mark.parametrize("model_type", ["pgie", "sgie"])
    def test_valid_model_types(self, model_type):
        """Valid model_type values accepted"""
        entry = ModelEntry(
            model_version="v1.0.0-tao-ds",
            model_type=model_type,
            model_name="safety_detector",
            framework="TAO",
            precision="FP16",
            engine_path="/models/active/pgie/model.engine",
            labels_path="/models/active/pgie/labels.txt",
            status="ACTIVE",
            deployed_at="2025-05-19T10:00:00.000Z",
            metrics={"mAP": 0.85, "inference_time_ms": 12.5, "fps": 30.0, "classes": 6},
        )
        assert entry.model_type == model_type

    @pytest.mark.model
    @pytest.mark.schema
    @pytest.mark.parametrize("framework", ["TAO", "PyTorch", "TensorFlow", "ONNX"])
    def test_valid_frameworks(self, framework):
        """Valid framework values accepted"""
        entry = ModelEntry(
            model_version="v1.0.0-tao-ds",
            model_type="pgie",
            model_name="safety_detector",
            framework=framework,
            precision="FP16",
            engine_path="/models/active/pgie/model.engine",
            labels_path="/models/active/pgie/labels.txt",
            status="ACTIVE",
            deployed_at="2025-05-19T10:00:00.000Z",
            metrics={"mAP": 0.85, "inference_time_ms": 12.5, "fps": 30.0, "classes": 6},
        )
        assert entry.framework == framework

    @pytest.mark.model
    @pytest.mark.schema
    @pytest.mark.parametrize("precision", ["FP16", "FP32", "INT8"])
    def test_valid_precisions(self, precision):
        """Valid precision values accepted"""
        entry = ModelEntry(
            model_version="v1.0.0-tao-ds",
            model_type="pgie",
            model_name="safety_detector",
            framework="TAO",
            precision=precision,
            engine_path="/models/active/pgie/model.engine",
            labels_path="/models/active/pgie/labels.txt",
            status="ACTIVE",
            deployed_at="2025-05-19T10:00:00.000Z",
            metrics={"mAP": 0.85, "inference_time_ms": 12.5, "fps": 30.0, "classes": 6},
        )
        assert entry.precision == precision

    @pytest.mark.model
    @pytest.mark.schema
    @pytest.mark.parametrize("status", ["ACTIVE", "STAGED", "ROLLBACK", "ARCHIVED"])
    def test_valid_model_statuses(self, status):
        """Valid model status values accepted"""
        entry = ModelEntry(
            model_version="v1.0.0-tao-ds",
            model_type="pgie",
            model_name="safety_detector",
            framework="TAO",
            precision="FP16",
            engine_path="/models/active/pgie/model.engine",
            labels_path="/models/active/pgie/labels.txt",
            status=status,
            deployed_at="2025-05-19T10:00:00.000Z",
            metrics={"mAP": 0.85, "inference_time_ms": 12.5, "fps": 30.0, "classes": 6},
        )
        assert entry.status == status

    @pytest.mark.model
    @pytest.mark.schema
    def test_invalid_model_type_rejected(self):
        """Invalid model_type rejected"""
        with pytest.raises(ValidationError):
            ModelEntry(
                model_version="v1.0.0-tao-ds",
                model_type="tgie",  # Invalid
                model_name="safety_detector",
                framework="TAO",
                precision="FP16",
                engine_path="/models/active/pgie/model.engine",
                labels_path="/models/active/pgie/labels.txt",
                status="ACTIVE",
                deployed_at="2025-05-19T10:00:00.000Z",
                metrics={"mAP": 0.85, "inference_time_ms": 12.5, "fps": 30.0, "classes": 6},
            )

    @pytest.mark.model
    @pytest.mark.schema
    def test_invalid_framework_rejected(self):
        """Invalid framework rejected"""
        with pytest.raises(ValidationError):
            ModelEntry(
                model_version="v1.0.0-tao-ds",
                model_type="pgie",
                model_name="safety_detector",
                framework="Caffe",  # Invalid
                precision="FP16",
                engine_path="/models/active/pgie/model.engine",
                labels_path="/models/active/pgie/labels.txt",
                status="ACTIVE",
                deployed_at="2025-05-19T10:00:00.000Z",
                metrics={"mAP": 0.85, "inference_time_ms": 12.5, "fps": 30.0, "classes": 6},
            )


# ──────────────────────────────────────────────────────────────────────
# Model Metrics Tests
# ──────────────────────────────────────────────────────────────────────


class TestModelMetrics:
    """Model metrics validation"""

    @pytest.mark.model
    @pytest.mark.schema
    def test_valid_metrics(self, model_registry):
        """Valid metrics pass validation"""
        metrics_data = model_registry["models"][0]["metrics"]
        result = ModelMetrics(**metrics_data)
        assert result.mAP == 0.85
        assert result.inference_time_ms == 12.5
        assert result.fps == 30.0
        assert result.classes == 6

    @pytest.mark.model
    @pytest.mark.boundary
    def test_mAP_boundary(self):
        """mAP must be 0.0~1.0"""
        # Valid
        result = ModelMetrics(mAP=0.0, inference_time_ms=10.0, fps=30.0, classes=6)
        assert result.mAP == 0.0

        result = ModelMetrics(mAP=1.0, inference_time_ms=10.0, fps=30.0, classes=6)
        assert result.mAP == 1.0

        # Invalid
        with pytest.raises(ValidationError):
            ModelMetrics(mAP=1.5, inference_time_ms=10.0, fps=30.0, classes=6)

        with pytest.raises(ValidationError):
            ModelMetrics(mAP=-0.1, inference_time_ms=10.0, fps=30.0, classes=6)

    @pytest.mark.model
    @pytest.mark.boundary
    def test_inference_time_must_be_positive(self):
        """inference_time_ms must be > 0"""
        with pytest.raises(ValidationError):
            ModelMetrics(mAP=0.85, inference_time_ms=0.0, fps=30.0, classes=6)

        with pytest.raises(ValidationError):
            ModelMetrics(mAP=0.85, inference_time_ms=-1.0, fps=30.0, classes=6)

    @pytest.mark.model
    @pytest.mark.boundary
    def test_fps_must_be_positive(self):
        """fps must be > 0"""
        with pytest.raises(ValidationError):
            ModelMetrics(mAP=0.85, inference_time_ms=10.0, fps=0.0, classes=6)

    @pytest.mark.model
    @pytest.mark.boundary
    def test_classes_must_be_positive(self):
        """classes must be > 0"""
        with pytest.raises(ValidationError):
            ModelMetrics(mAP=0.85, inference_time_ms=10.0, fps=30.0, classes=0)
