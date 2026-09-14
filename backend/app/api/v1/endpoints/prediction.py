"""Fraud Prediction and Explainable AI Endpoints."""

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
