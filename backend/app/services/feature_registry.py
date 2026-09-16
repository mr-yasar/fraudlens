"""Feature Availability Registry and Leakage Prevention Service (Phase 13).

Strictly enforces feature classification boundaries:
  - Stage A: Available before payment authorization
  - Stage B: Historical customer signals (available pre-auth)
  - Stage C: Post-payment / provider settlement features (STRICTLY PROHIBITED in Pre-Auth)
  - Stage D: Leakage-prone outcome indicators (STRICTLY PROHIBITED in Pre-Auth)
  - Stage E: Unknown / Unverified
"""

from enum import Enum
from typing import Any, Dict, List, Set
from pydantic import BaseModel


class FeatureStage(str, Enum):
    STAGE_A_PRE_AUTH = "STAGE_A_PRE_AUTH"
    STAGE_B_HISTORICAL = "STAGE_B_HISTORICAL"
    STAGE_C_POST_AUTH = "STAGE_C_POST_AUTH"
    STAGE_D_LEAKAGE_RISK = "STAGE_D_LEAKAGE_RISK"
    STAGE_E_UNKNOWN = "STAGE_E_UNKNOWN"


class FeatureDefinition(BaseModel):
    feature_name: str
    stage: FeatureStage
    source: str
    description: str
    safe_for_pre_auth: bool
    data_type: str


class FeatureRegistry:
    """Central registry governing feature eligibility across inference stages."""

    _REGISTRY: Dict[str, FeatureDefinition] = {
        # Stage A: Pre-Auth Transaction Request Signals
        "amount": FeatureDefinition(
            feature_name="amount",
            stage=FeatureStage.STAGE_A_PRE_AUTH,
            source="payment_request",
            description="Transaction monetary amount",
            safe_for_pre_auth=True,
            data_type="float",
        ),
        "currency": FeatureDefinition(
            feature_name="currency",
            stage=FeatureStage.STAGE_A_PRE_AUTH,
            source="payment_request",
            description="ISO currency code",
            safe_for_pre_auth=True,
            data_type="string",
        ),
        "merchant_category": FeatureDefinition(
            feature_name="merchant_category",
            stage=FeatureStage.STAGE_A_PRE_AUTH,
            source="payment_request",
            description="Merchant category code (MCC)",
            safe_for_pre_auth=True,
            data_type="string",
        ),
        "device_type": FeatureDefinition(
            feature_name="device_type",
            stage=FeatureStage.STAGE_A_PRE_AUTH,
            source="client_telemetry",
            description="Client hardware/browser platform",
            safe_for_pre_auth=True,
            data_type="string",
        ),
        "location": FeatureDefinition(
            feature_name="location",
            stage=FeatureStage.STAGE_A_PRE_AUTH,
            source="ip_geo",
            description="Client geolocation region/state",
            safe_for_pre_auth=True,
            data_type="string",
        ),
        "transaction_country": FeatureDefinition(
            feature_name="transaction_country",
            stage=FeatureStage.STAGE_A_PRE_AUTH,
            source="ip_geo",
            description="ISO country of payment origination",
            safe_for_pre_auth=True,
            data_type="string",
        ),
        "transaction_type": FeatureDefinition(
            feature_name="transaction_type",
            stage=FeatureStage.STAGE_A_PRE_AUTH,
            source="payment_request",
            description="Payment rail type (e.g. online_payment, card_not_present)",
            safe_for_pre_auth=True,
            data_type="string",
        ),
        "transaction_hour": FeatureDefinition(
            feature_name="transaction_hour",
            stage=FeatureStage.STAGE_A_PRE_AUTH,
            source="timestamp",
            description="Hour of day (0-23) in local/UTC context",
            safe_for_pre_auth=True,
            data_type="int",
        ),
        "failed_attempts": FeatureDefinition(
            feature_name="failed_attempts",
            stage=FeatureStage.STAGE_A_PRE_AUTH,
            source="session_context",
            description="Preceding failed auth / OTP attempts prior to checkout",
            safe_for_pre_auth=True,
            data_type="int",
        ),

        # Stage B: Customer Historical Signals
        "historical_avg_amount": FeatureDefinition(
            feature_name="historical_avg_amount",
            stage=FeatureStage.STAGE_B_HISTORICAL,
            source="customer_database",
            description="Customer lifetime average transaction amount",
            safe_for_pre_auth=True,
            data_type="float",
        ),
        "historical_max_amount": FeatureDefinition(
            feature_name="historical_max_amount",
            stage=FeatureStage.STAGE_B_HISTORICAL,
            source="customer_database",
            description="Customer historical maximum transaction amount",
            safe_for_pre_auth=True,
            data_type="float",
        ),
        "account_age_days": FeatureDefinition(
            feature_name="account_age_days",
            stage=FeatureStage.STAGE_B_HISTORICAL,
            source="customer_database",
            description="Days since customer account registration",
            safe_for_pre_auth=True,
            data_type="float",
        ),
        "velocity_5m": FeatureDefinition(
            feature_name="velocity_5m",
            stage=FeatureStage.STAGE_B_HISTORICAL,
            source="transaction_ledger",
            description="Transactions in trailing 5-minute rolling window",
            safe_for_pre_auth=True,
            data_type="int",
        ),
        "velocity_15m": FeatureDefinition(
            feature_name="velocity_15m",
            stage=FeatureStage.STAGE_B_HISTORICAL,
            source="transaction_ledger",
            description="Transactions in trailing 15-minute rolling window",
            safe_for_pre_auth=True,
            data_type="int",
        ),
        "velocity_1h": FeatureDefinition(
            feature_name="velocity_1h",
            stage=FeatureStage.STAGE_B_HISTORICAL,
            source="transaction_ledger",
            description="Transactions in trailing 1-hour rolling window",
            safe_for_pre_auth=True,
            data_type="int",
        ),
        "velocity_24h": FeatureDefinition(
            feature_name="velocity_24h",
            stage=FeatureStage.STAGE_B_HISTORICAL,
            source="transaction_ledger",
            description="Transactions in trailing 24-hour rolling window",
            safe_for_pre_auth=True,
            data_type="int",
        ),
        "is_new_device": FeatureDefinition(
            feature_name="is_new_device",
            stage=FeatureStage.STAGE_B_HISTORICAL,
            source="derived_behaviour",
            description="Flag indicating device hardware never seen for this customer",
            safe_for_pre_auth=True,
            data_type="bool",
        ),
        "is_unusual_location": FeatureDefinition(
            feature_name="is_unusual_location",
            stage=FeatureStage.STAGE_B_HISTORICAL,
            source="derived_behaviour",
            description="Flag indicating location never seen for this customer",
            safe_for_pre_auth=True,
            data_type="bool",
        ),
        "behaviour_deviation_score": FeatureDefinition(
            feature_name="behaviour_deviation_score",
            stage=FeatureStage.STAGE_B_HISTORICAL,
            source="derived_behaviour",
            description="Composite metric measuring deviation from normal baseline",
            safe_for_pre_auth=True,
            data_type="float",
        ),

        # Stage C: Post-Payment Outcome Signals (Disallowed Pre-Auth)
        "transaction_status": FeatureDefinition(
            feature_name="transaction_status",
            stage=FeatureStage.STAGE_C_POST_AUTH,
            source="provider_response",
            description="Final gateway settlement status",
            safe_for_pre_auth=False,
            data_type="string",
        ),
        "authorization_code": FeatureDefinition(
            feature_name="authorization_code",
            stage=FeatureStage.STAGE_C_POST_AUTH,
            source="provider_response",
            description="Network authorization code from acquiring bank",
            safe_for_pre_auth=False,
            data_type="string",
        ),
        "avs_result_code": FeatureDefinition(
            feature_name="avs_result_code",
            stage=FeatureStage.STAGE_C_POST_AUTH,
            source="provider_response",
            description="Address verification system result from issuer",
            safe_for_pre_auth=False,
            data_type="string",
        ),
        "cvv_result_code": FeatureDefinition(
            feature_name="cvv_result_code",
            stage=FeatureStage.STAGE_C_POST_AUTH,
            source="provider_response",
            description="Card verification value match code from issuer",
            safe_for_pre_auth=False,
            data_type="string",
        ),

        # Stage D: Leakage-Risk Signals (Disallowed Pre-Auth)
        "chargeback_dispute_filed": FeatureDefinition(
            feature_name="chargeback_dispute_filed",
            stage=FeatureStage.STAGE_D_LEAKAGE_RISK,
            source="dispute_system",
            description="Post-hoc chargeback dispute signal",
            safe_for_pre_auth=False,
            data_type="bool",
        ),
        "investigation_final_verdict": FeatureDefinition(
            feature_name="investigation_final_verdict",
            stage=FeatureStage.STAGE_D_LEAKAGE_RISK,
            source="investigation_system",
            description="Manual analyst final confirmation",
            safe_for_pre_auth=False,
            data_type="string",
        ),
    }

    @classmethod
    def get_allowed_pre_auth_features(cls) -> Set[str]:
        """Return the set of feature names explicitly certified for Pre-Auth decisioning."""
        return {
            name for name, defn in cls._REGISTRY.items()
            if defn.safe_for_pre_auth and defn.stage in (FeatureStage.STAGE_A_PRE_AUTH, FeatureStage.STAGE_B_HISTORICAL)
        }

    @classmethod
    def validate_and_filter_pre_auth_features(cls, input_features: Dict[str, Any]) -> Dict[str, Any]:
        """Strip any post-auth or leakage-risk features from pre-auth feature dictionaries."""
        allowed = cls.get_allowed_pre_auth_features()
        return {k: v for k, v in input_features.items() if k in allowed}

    @classmethod
    def get_feature_manifest(cls) -> List[FeatureDefinition]:
        """Return full feature registry manifest."""
        return list(cls._REGISTRY.values())
