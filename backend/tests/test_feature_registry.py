"""Unit tests for Feature Availability Registry and Leakage Control (Phase 13)."""

from backend.app.services.feature_registry import FeatureRegistry, FeatureStage


def test_feature_registry_pre_auth_boundaries():
    """Verify FeatureRegistry permits Stage A/B signals and excludes Stage C/D outcome/leakage features."""
    allowed = FeatureRegistry.get_allowed_pre_auth_features()

    # Stage A and B features MUST be allowed
    assert "amount" in allowed
    assert "merchant_category" in allowed
    assert "device_type" in allowed
    assert "historical_avg_amount" in allowed
    assert "velocity_1h" in allowed
    assert "is_new_device" in allowed
    assert "behaviour_deviation_score" in allowed

    # Stage C (Post-Auth) and Stage D (Leakage) features MUST NOT be allowed in Pre-Auth
    assert "transaction_status" not in allowed
    assert "authorization_code" not in allowed
    assert "chargeback_dispute_filed" not in allowed
    assert "investigation_final_verdict" not in allowed


def test_feature_registry_filtering():
    """Verify validate_and_filter_pre_auth_features strips out prohibited signals."""
    tainted_payload = {
        "amount": 250.0,
        "merchant_category": "retail",
        "velocity_1h": 2,
        "transaction_status": "settled",  # Post-auth!
        "authorization_code": "AUTH_9988",  # Post-auth!
        "chargeback_dispute_filed": True,  # Leakage!
    }

    filtered = FeatureRegistry.validate_and_filter_pre_auth_features(tainted_payload)

    assert "amount" in filtered
    assert "merchant_category" in filtered
    assert "velocity_1h" in filtered
    assert "transaction_status" not in filtered
    assert "authorization_code" not in filtered
    assert "chargeback_dispute_filed" not in filtered


def test_feature_manifest_completeness():
    """Verify registry manifest contains complete definitions."""
    manifest = FeatureRegistry.get_feature_manifest()
    assert len(manifest) >= 15
    for item in manifest:
        assert item.feature_name is not None
        assert item.stage in FeatureStage
        assert isinstance(item.safe_for_pre_auth, bool)
