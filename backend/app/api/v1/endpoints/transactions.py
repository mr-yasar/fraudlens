"""Transaction Management & Real-Time Risk Evaluation Endpoints (Phases 11 & 12)."""

from datetime import datetime, timezone
import json
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, asc, func, or_
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.shap_explanation import ShapExplanation
from backend.app.models.audit_log import AuditLog
from backend.app.api.deps import require_investigator
from backend.app.schemas.prediction import (
    TransactionPredictionInput,
    LocalExplanationResponse,
)
from backend.app.schemas.transaction import (
    TransactionCreateInput,
    TransactionSummaryResponse,
    TransactionDetailResponse,
    TransactionListResponse,
    RealtimeEvaluationResponse,
)
from backend.app.services.prediction_service import FraudPredictionService

router = APIRouter()


def _ensure_customer_exists(db: Session, customer_id: str, account_age_days: Optional[float] = None) -> Customer:
    """Ensure customer record exists in database, creating if necessary."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        customer = Customer(
            customer_id=customer_id,
            account_age_days=int(account_age_days) if account_age_days is not None else 30,
        )
        db.add(customer)
        db.flush()
    return customer


@router.post(
    "",
    response_model=TransactionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create, Score, and Persist Financial Transaction",
    description="Evaluates transaction against active ML model and risk engine, persists the record, stores SHAP attributions, and returns the enriched transaction.",
)
def create_transaction(
    payload: TransactionCreateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> TransactionDetailResponse:
    """Create and score a financial transaction with full database persistence."""
    # Ensure transaction_id
    tx_id = payload.transaction_id or f"TX-{uuid.uuid4().hex[:12].upper()}"
    payload.transaction_id = tx_id

    # Ensure customer_id
    cust_id = payload.customer_id or f"CUST-{uuid.uuid4().hex[:8].upper()}"
    payload.customer_id = cust_id

    # 1. Check for duplicate transaction_id
    existing_tx = db.query(Transaction).filter(Transaction.transaction_id == tx_id).first()
    if existing_tx:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transaction with ID '{tx_id}' already exists.",
        )

    # 2. Ensure customer is provisioned
    _ensure_customer_exists(db, cust_id, payload.account_age_days)

    # 3. Run active prediction and risk scoring service
    prediction_service = FraudPredictionService.get_instance()
    try:
        pred_res = prediction_service.predict_transaction(payload, include_shap_summary=True)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction evaluation failed: {str(e)}",
        )

    # 4. Persist Transaction
    db_tx = Transaction(
        transaction_id=tx_id,
        customer_id=cust_id,
        amount=payload.transaction_amount,
        transaction_hour=payload.transaction_hour,
        merchant_category=payload.merchant_category,
        transaction_country=payload.transaction_country,
        geo_location_region=payload.geo_location_region,
        device_type=payload.device_type,
        transaction_type=payload.transaction_type,
        fraud_probability=pred_res.fraud_probability,
        prediction=1 if pred_res.prediction == "FRAUD" else 0,
        risk_score=float(pred_res.risk_score),
        risk_level=pred_res.risk_level,
    )
    db.add(db_tx)
    db.flush()

    # 5. Persist SHAP Explanations
    shap_records = []
    if pred_res.top_shap_factors:
        for factor in pred_res.top_shap_factors:
            shap_rec = ShapExplanation(
                transaction_id=tx_id,
                feature_name=factor.get("feature_name", "unknown"),
                shap_value=float(factor.get("shap_value", 0.0)),
                impact=factor.get("impact", "neutral"),
            )
            db.add(shap_rec)
            shap_records.append({
                "feature_name": shap_rec.feature_name,
                "shap_value": shap_rec.shap_value,
                "impact": shap_rec.impact,
            })

    # 6. If HIGH risk or FRAUD, record in-app alert and AuditLog
    if pred_res.risk_level == "HIGH" or pred_res.prediction == "FRAUD":
        from backend.app.services.alert_service import AlertService, AlertType
        from backend.app.models.alert import Alert
        existing_alert = db.query(Alert).filter(Alert.entity_id == tx_id, Alert.is_acknowledged.is_(False)).first()
        if not existing_alert:
            AlertService.create_alert(
                db=db,
                alert_type=AlertType.HIGH_RISK_PAYMENT,
                severity="HIGH" if pred_res.risk_level == "HIGH" else "MEDIUM",
                entity_id=tx_id,
                message=f"High-risk transaction flagged: {tx_id} (Score: {pred_res.risk_score}/100, Prob: {pred_res.fraud_probability:.2f})",
                details={
                    "risk_score": pred_res.risk_score,
                    "risk_level": pred_res.risk_level,
                    "fraud_probability": pred_res.fraud_probability,
                    "prediction": pred_res.prediction,
                    "model_name": pred_res.model_name,
                },
            )
        audit = AuditLog(
            user_id=current_user.id,
            action="HIGH_RISK_TRANSACTION_FLAGGED",
            resource_type="transaction",
            resource_id=tx_id,
            details=json.dumps({
                "risk_score": pred_res.risk_score,
                "risk_level": pred_res.risk_level,
                "fraud_probability": pred_res.fraud_probability,
                "prediction": pred_res.prediction,
                "risk_factors": pred_res.risk_factors,
            }),
        )
        db.add(audit)

    db.commit()
    db.refresh(db_tx)

    return TransactionDetailResponse(
        id=db_tx.id,
        transaction_id=db_tx.transaction_id,
        customer_id=db_tx.customer_id,
        amount=float(db_tx.amount),
        transaction_hour=db_tx.transaction_hour,
        merchant_category=db_tx.merchant_category,
        transaction_country=db_tx.transaction_country,
        geo_location_region=db_tx.geo_location_region,
        device_type=db_tx.device_type,
        transaction_type=db_tx.transaction_type,
        fraud_probability=db_tx.fraud_probability,
        prediction="FRAUD" if db_tx.prediction == 1 else "GENUINE",
        risk_score=db_tx.risk_score,
        risk_level=db_tx.risk_level,
        created_at=db_tx.created_at,
        model_name=pred_res.model_name,
        model_version=pred_res.model_version,
        threshold_used=pred_res.threshold_used,
        risk_factors=pred_res.risk_factors,
        top_shap_factors=pred_res.top_shap_factors,
        shap_explanations=shap_records,
    )


@router.post(
    "/evaluate",
    response_model=RealtimeEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Real-Time Transaction Risk Evaluation (Phase 12)",
    description="Application-level real-time evaluation pipeline: Input Validation -> Preprocessing -> Active ML Model -> Threshold Decision -> Multi-Factor Risk Score -> SHAP Explanation -> Alert Decision -> Persistence.",
)
def evaluate_realtime_transaction(
    payload: TransactionCreateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> RealtimeEvaluationResponse:
    """Execute real-time risk assessment workflow with alert generation and persistence."""
    tx_id = payload.transaction_id or f"RT-{uuid.uuid4().hex[:12].upper()}"
    payload.transaction_id = tx_id

    cust_id = payload.customer_id or f"CUST-{uuid.uuid4().hex[:8].upper()}"
    payload.customer_id = cust_id

    # 1. Ensure customer is provisioned
    _ensure_customer_exists(db, cust_id, payload.account_age_days)

    # 2. Evaluate with FraudPredictionService
    prediction_service = FraudPredictionService.get_instance()
    try:
        pred_res = prediction_service.predict_transaction(payload, include_shap_summary=True)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Real-time evaluation failed: {str(e)}",
        )

    # 3. Alert Decision: HIGH risk generates immediate investigator alert
    alert_generated = (pred_res.risk_level == "HIGH")

    # 4. Persist or update transaction
    existing_tx = db.query(Transaction).filter(Transaction.transaction_id == tx_id).first()
    if not existing_tx:
        db_tx = Transaction(
            transaction_id=tx_id,
            customer_id=cust_id,
            amount=payload.transaction_amount,
            transaction_hour=payload.transaction_hour,
            merchant_category=payload.merchant_category,
            transaction_country=payload.transaction_country,
            geo_location_region=payload.geo_location_region,
            device_type=payload.device_type,
            transaction_type=payload.transaction_type,
            fraud_probability=pred_res.fraud_probability,
            prediction=1 if pred_res.prediction == "FRAUD" else 0,
            risk_score=float(pred_res.risk_score),
            risk_level=pred_res.risk_level,
        )
        db.add(db_tx)
    else:
        existing_tx.fraud_probability = pred_res.fraud_probability
        existing_tx.prediction = 1 if pred_res.prediction == "FRAUD" else 0
        existing_tx.risk_score = float(pred_res.risk_score)
        existing_tx.risk_level = pred_res.risk_level

    # 5. Persist SHAP Explanations
    if pred_res.top_shap_factors:
        # Clear any prior explanations for idempotency if existing
        db.query(ShapExplanation).filter(ShapExplanation.transaction_id == tx_id).delete()
        for factor in pred_res.top_shap_factors:
            shap_rec = ShapExplanation(
                transaction_id=tx_id,
                feature_name=factor.get("feature_name", "unknown"),
                shap_value=float(factor.get("shap_value", 0.0)),
                impact=factor.get("impact", "neutral"),
            )
            db.add(shap_rec)

    # 6. Record in-app Alert and Audit Event if HIGH risk
    if alert_generated:
        from backend.app.services.alert_service import AlertService, AlertType
        from backend.app.models.alert import Alert
        existing_alert = db.query(Alert).filter(Alert.entity_id == tx_id, Alert.is_acknowledged.is_(False)).first()
        if not existing_alert:
            AlertService.create_alert(
                db=db,
                alert_type=AlertType.HIGH_RISK_PAYMENT,
                severity="HIGH",
                entity_id=tx_id,
                message=f"Real-time high-risk alert: {tx_id} (Score: {pred_res.risk_score}/100, Prob: {pred_res.fraud_probability:.2f})",
                details={
                    "risk_score": pred_res.risk_score,
                    "risk_level": pred_res.risk_level,
                    "fraud_probability": pred_res.fraud_probability,
                    "prediction": pred_res.prediction,
                    "model_name": pred_res.model_name,
                },
            )
        audit = AuditLog(
            user_id=current_user.id,
            action="REALTIME_HIGH_RISK_ALERT",
            resource_type="transaction",
            resource_id=tx_id,
            details=json.dumps({
                "alert": True,
                "risk_score": pred_res.risk_score,
                "risk_level": pred_res.risk_level,
                "fraud_probability": pred_res.fraud_probability,
                "prediction": pred_res.prediction,
                "top_factors": pred_res.risk_factors,
            }),
        )
        db.add(audit)

    db.commit()

    return RealtimeEvaluationResponse(
        transaction_id=tx_id,
        prediction=pred_res.prediction,
        fraud_probability=pred_res.fraud_probability,
        risk_score=pred_res.risk_score,
        risk_level=pred_res.risk_level,
        model_name=pred_res.model_name,
        model_version=pred_res.model_version,
        threshold_used=pred_res.threshold_used,
        risk_factors=pred_res.risk_factors,
        top_explanations=pred_res.top_shap_factors or [],
        alert_generated=alert_generated,
        anomaly_score=pred_res.anomaly_score,
        anomaly_status=pred_res.anomaly_status,
        uncertainty_score=pred_res.uncertainty_score,
        uncertainty_level=pred_res.uncertainty_level,
        counterfactual=pred_res.counterfactual,
        composed_explanation=pred_res.composed_explanation,
    )


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="List Transactions with Search and Multi-Factor Filters",
    description="Retrieves a paginated list of transactions with support for risk level, prediction classification, amount range, and timestamp filters.",
)
def list_transactions(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    customer_id: Optional[str] = Query(None, description="Filter by customer identifier"),
    search: Optional[str] = Query(None, description="Search by transaction_id or customer_id"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: LOW, MEDIUM, HIGH"),
    prediction: Optional[str] = Query(None, description="Filter by prediction: FRAUD or GENUINE"),
    min_amount: Optional[float] = Query(None, ge=0.0, description="Minimum transaction amount"),
    max_amount: Optional[float] = Query(None, ge=0.0, description="Maximum transaction amount"),
    start_date: Optional[datetime] = Query(None, description="Earliest transaction creation datetime"),
    end_date: Optional[datetime] = Query(None, description="Latest transaction creation datetime"),
    sort_by: str = Query("created_at", description="Sort column: created_at, amount, risk_score, fraud_probability"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> TransactionListResponse:
    """List transactions with flexible filtering, search, and pagination."""
    query = db.query(Transaction)

    if customer_id:
        query = query.filter(Transaction.customer_id == customer_id.strip())

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Transaction.transaction_id.ilike(search_pattern),
                Transaction.customer_id.ilike(search_pattern),
                Transaction.merchant_category.ilike(search_pattern),
            )
        )

    if risk_level:
        query = query.filter(Transaction.risk_level == risk_level.upper().strip())

    if prediction:
        pred_clean = prediction.upper().strip()
        if pred_clean == "FRAUD":
            query = query.filter(Transaction.prediction == 1)
        elif pred_clean == "GENUINE":
            query = query.filter(Transaction.prediction == 0)

    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)

    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)

    if start_date is not None:
        query = query.filter(Transaction.created_at >= start_date)

    if end_date is not None:
        query = query.filter(Transaction.created_at <= end_date)

    # Sorting
    sort_map = {
        "created_at": Transaction.created_at,
        "amount": Transaction.amount,
        "risk_score": Transaction.risk_score,
        "fraud_probability": Transaction.fraud_probability,
    }
    sort_col = sort_map.get(sort_by, Transaction.created_at)
    order_func = desc if sort_order.lower() == "desc" else asc
    query = query.order_by(order_func(sort_col))

    total = query.count()
    offset = (page - 1) * page_size
    tx_records = query.offset(offset).limit(page_size).all()

    items = [
        TransactionSummaryResponse(
            id=t.id,
            transaction_id=t.transaction_id,
            customer_id=t.customer_id,
            amount=float(t.amount),
            transaction_hour=t.transaction_hour,
            merchant_category=t.merchant_category,
            transaction_country=t.transaction_country,
            geo_location_region=t.geo_location_region,
            device_type=t.device_type,
            transaction_type=t.transaction_type,
            fraud_probability=t.fraud_probability,
            prediction="FRAUD" if t.prediction == 1 else "GENUINE",
            risk_score=t.risk_score,
            risk_level=t.risk_level,
            created_at=t.created_at,
        )
        for t in tx_records
    ]

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    return TransactionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionDetailResponse,
    summary="Get Transaction Details by ID",
    description="Retrieves complete transaction information including risk scoring, prediction classification, model metadata, and stored explanations.",
)
def get_transaction_detail(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> TransactionDetailResponse:
    """Retrieve detailed transaction record with metadata and explanations."""
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{transaction_id}' not found.",
        )

    # Fetch stored SHAP explanations
    shap_explanations = (
        db.query(ShapExplanation)
        .filter(ShapExplanation.transaction_id == transaction_id)
        .all()
    )
    shap_list = [
        {
            "feature_name": s.feature_name,
            "shap_value": s.shap_value,
            "impact": s.impact,
        }
        for s in shap_explanations
    ]

    # Model metadata from active prediction service
    service = FraudPredictionService.get_instance()

    return TransactionDetailResponse(
        id=tx.id,
        transaction_id=tx.transaction_id,
        customer_id=tx.customer_id,
        amount=float(tx.amount),
        transaction_hour=tx.transaction_hour,
        merchant_category=tx.merchant_category,
        transaction_country=tx.transaction_country,
        geo_location_region=tx.geo_location_region,
        device_type=tx.device_type,
        transaction_type=tx.transaction_type,
        fraud_probability=tx.fraud_probability,
        prediction="FRAUD" if tx.prediction == 1 else "GENUINE",
        risk_score=tx.risk_score,
        risk_level=tx.risk_level,
        created_at=tx.created_at,
        model_name=service.model_name,
        model_version=service.model_version,
        threshold_used=service.threshold,
        risk_factors=[],
        top_shap_factors=shap_list if shap_list else None,
        shap_explanations=shap_list,
    )


@router.get(
    "/{transaction_id}/explanation",
    response_model=LocalExplanationResponse,
    summary="Get SHAP Local Explanation for Persisted Transaction",
    description="Retrieves or recomputes full local SHAP attribution values for a specific persisted transaction using the Phase 10 SHAP engine.",
)
def get_transaction_explanation(
    transaction_id: str,
    top_k: int = Query(5, ge=1, le=20, description="Top positive and negative factors count"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> LocalExplanationResponse:
    """Retrieve or compute exact local SHAP feature attribution report for a transaction."""
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{transaction_id}' not found.",
        )

    # Load customer to get account age
    customer = db.query(Customer).filter(Customer.customer_id == tx.customer_id).first()
    account_age = float(customer.account_age_days) if customer and customer.account_age_days is not None else 30.0

    # Build input representation from transaction record using primary CSV schema
    # (the active model was trained on financial_fraud_customer_transactions.csv schema)
    tx_amount = float(tx.amount)

    # Infer device type: transaction stores old device_type values; map to new CSV Device_Type values
    raw_device = tx.device_type or "Windows"
    # Map legacy device types to primary CSV values
    device_map = {
        "web": "Windows", "mobile": "iOS", "pos": "Android",
        "ios": "iOS", "android": "Android", "mac": "Mac", "macos": "Mac",
        "windows": "Windows", "linux": "Linux",
    }
    device_type_val = device_map.get(raw_device.lower(), raw_device)

    # Infer location from geo_location_region (or transaction_country)
    location_val = tx.geo_location_region or tx.transaction_country or "Mumbai"
    usual_location_val = location_val  # Default to same unless location mismatch stored

    # Infer transaction type from stored type
    tx_type_raw = tx.transaction_type or "Purchase"
    # Map legacy types to primary CSV values
    tx_type_map = {
        "online_payment": "Transfer", "card_present": "Purchase",
        "transfer": "Transfer", "payment": "Payment",
        "withdrawal": "Withdrawal", "deposit": "Deposit", "purchase": "Purchase",
    }
    tx_type_val = tx_type_map.get(tx_type_raw.lower(), tx_type_raw)

    # Build the input with primary CSV field names
    # For amounts, use stored amount and estimate historical average
    avg_amount = tx_amount * 0.75  # Conservative estimate of historical average

    tx_input = TransactionPredictionInput(
        transaction_id=tx.transaction_id,
        customer_id=tx.customer_id,
        # Primary CSV fields
        Amount=tx_amount,
        Transaction_Hour=tx.transaction_hour or 12,
        Transaction_Type=tx_type_val,
        Device_Type=device_type_val,
        Location=location_val,
        Usual_Location=usual_location_val,
        New_Device=0,
        Account_Age_Days=float(account_age),
        Previous_Transaction_Amount=avg_amount,
        Average_Previous_Amount=avg_amount,
        Amount_Deviation=tx_amount - avg_amount,
        Amount_Ratio=tx_amount / (avg_amount + 1e-5),
        Transactions_Last_24H=3.0,
        Failed_Attempts=0,
        International_Transaction=1 if tx.transaction_country and tx.transaction_country.upper() not in ["IN", "US", "GB", "CA"] else 0,
        Unusual_Location=0,
        # Legacy compatibility fields (some models may use these)
        transaction_amount=tx_amount,
        transaction_hour=tx.transaction_hour or 12,
        device_type=raw_device,
        geo_location_region=location_val,
        transaction_type=tx_type_raw,
        account_age_days=float(account_age),
        avg_transaction_amount_30d_customer=avg_amount,
        transaction_velocity_24h=3.0,
        transaction_velocity_1h=1.0,
        merchant_category=tx.merchant_category or "general",
        transaction_country=tx.transaction_country or "IN",
        previous_chargebacks=0,
        is_high_risk_merchant_category=1 if tx.merchant_category in ["Jewelry", "Electronics", "Crypto"] else 0,
        is_weekend=0,
        customer_total_transactions_30d=10.0,
    )

    service = FraudPredictionService.get_instance()
    try:
        explanation = service.explain_transaction(tx_input, top_k=top_k)
        return explanation
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Explanation calculation failed: {str(e)}",
        )
