"""Fraud Prediction and Explainable AI Endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.models.user import User
from backend.app.api.deps import require_investigator
from backend.app.schemas.prediction import (
    TransactionPredictionInput,
    PredictionResponse,
    LocalExplanationResponse,
    GlobalExplanationResponse,
)
from backend.app.services.prediction_service import FraudPredictionService

router = APIRouter()


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Score Financial Transaction for Fraud & Risk",
    description="Evaluates transaction against active ML model, calculates multi-factor risk score (0-100), risk level (LOW, MEDIUM, HIGH), and returns top SHAP attributions.",
)
def predict_fraud(
    transaction_input: TransactionPredictionInput,
    current_user: User = Depends(require_investigator),
) -> PredictionResponse:
    """Evaluate fraud probability and classify transaction as FRAUD or GENUINE."""
    service = FraudPredictionService.get_instance()
    try:
        response = service.predict_transaction(transaction_input)
        return response
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prediction failed: {str(e)}",
        )


@router.post(
    "/explain",
    response_model=LocalExplanationResponse,
    summary="Generate Local SHAP Explanation for Transaction",
    description="Produces feature-by-feature SHAP attributions indicating which factors increased or decreased fraud probability.",
)
def explain_transaction(
    transaction_input: TransactionPredictionInput,
    top_k: int = Query(5, ge=1, le=20, description="Number of top contributing factors to highlight"),
    current_user: User = Depends(require_investigator),
) -> LocalExplanationResponse:
    """Generate exact local SHAP feature attribution report for a single transaction."""
    service = FraudPredictionService.get_instance()
    try:
        explanation = service.explain_transaction(transaction_input, top_k=top_k)
        return explanation
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Explanation generation failed: {str(e)}",
        )


@router.get(
    "/explain/global",
    response_model=GlobalExplanationResponse,
    summary="Get Global Model Feature Importance Rankings",
    description="Retrieves precomputed global mean absolute SHAP importance rankings across the active model.",
)
def get_global_model_explanation(
    current_user: User = Depends(require_investigator),
) -> GlobalExplanationResponse:
    """Retrieve global SHAP feature importance rankings."""
    service = FraudPredictionService.get_instance()
    try:
        return service.get_global_explanation()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Global explanation retrieval failed: {str(e)}",
        )


@router.post(
    "/explain/counterfactual",
    summary="Generate Actionable Counterfactual Scenario",
    description="Produces minimal feature perturbations demonstrating how a high-risk transaction could legitimately transition to ALLOW / REVIEW.",
)
def generate_counterfactual_explanation(
    transaction_input: TransactionPredictionInput,
    current_user: User = Depends(require_investigator),
) -> Dict[str, Any]:
    """Compute minimal verified counterfactual feature perturbation."""
    service = FraudPredictionService.get_instance()
    try:
        raw_dict = transaction_input.model_dump()
        pred_res = service.predict_transaction(transaction_input)
        
        decision_tier = "BLOCK" if pred_res.risk_level == "HIGH" else ("REVIEW" if pred_res.risk_level == "MEDIUM" else "ALLOW")
        
        from ml.explainability.counterfactual_engine import CounterfactualEngine
        cf_res = CounterfactualEngine.generate_counterfactual(
            raw_payload=raw_dict,
            preprocessor=service.preprocessor,
            model=service.model,
            risk_engine=service.risk_engine,
            original_prob=pred_res.fraud_probability,
            original_risk=float(pred_res.risk_score),
            original_decision=decision_tier,
            threshold=pred_res.threshold_used,
        )
        return cf_res.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Counterfactual generation failed: {str(e)}",
        )
