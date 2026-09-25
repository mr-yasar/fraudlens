"""Merchant Intelligence API Endpoints for 29 Master Merchants."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, get_optional_current_user
from backend.app.models import User, Merchant, Transaction

router = APIRouter()


@router.get("", summary="List all master merchants with aggregated risk telemetry")
def list_merchants(
    category: Optional[str] = Query(None, description="Filter by merchant category"),
    city: Optional[str] = Query(None, description="Filter by city"),
    search: Optional[str] = Query(None, description="Search by merchant name or ID"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Retrieve all 29 master merchants along with dynamic live fraud stats computed from the database."""
    query = db.query(Merchant)

    if category:
        query = query.filter(Merchant.category.ilike(f"%{category}%"))
    if city:
        query = query.filter(Merchant.city.ilike(f"%{city}%"))
    if search:
        query = query.filter(
            (Merchant.merchant_name.ilike(f"%{search}%")) | (Merchant.merchant_id.ilike(f"%{search}%"))
        )

    merchants = query.order_by(Merchant.merchant_id).all()

    # Aggregate telemetry per merchant from transactions table
    results = []
    for m in merchants:
        tx_stats = (
            db.query(
                func.count(Transaction.id).label("total_tx"),
                func.sum(case((Transaction.is_fraud == 1, 1), else_=0)).label("fraud_tx"),
                func.sum(case((Transaction.risk_level == "HIGH", 1), else_=0)).label("high_risk_tx"),
                func.avg(Transaction.amount).label("avg_amount"),
            )
            .filter(Transaction.merchant_id == m.merchant_id)
            .first()
        )

        total_tx = int(tx_stats.total_tx or 0)
        fraud_tx = int(tx_stats.fraud_tx or 0)
        high_risk_tx = int(tx_stats.high_risk_tx or 0)
        avg_amount = float(tx_stats.avg_amount or m.average_ticket)
        current_fraud_rate = round((fraud_tx / total_tx * 100) if total_tx > 0 else 0.0, 2)

        results.append({
            "id": m.id,
            "merchant_id": m.merchant_id,
            "merchant_name": m.merchant_name,
            "category": m.category,
            "subcategory": m.subcategory,
            "city": m.city,
            "area": m.area,
            "state": m.state,
            "pincode": m.pincode,
            "latitude": m.latitude,
            "longitude": m.longitude,
            "business_age": m.business_age,
            "average_ticket": m.average_ticket,
            "operating_hours": m.operating_hours,
            "payment_channel": m.payment_channel,
            "historical_fraud_rate": round(m.historical_fraud_rate * 100, 2),
            "historical_fraud_count": m.historical_fraud_count,
            "historical_fraud_pattern": m.historical_fraud_pattern,
            "historical_fraud_summary": m.historical_fraud_summary,
            "live_telemetry": {
                "total_transactions": total_tx,
                "fraud_transactions": fraud_tx,
                "high_risk_transactions": high_risk_tx,
                "calculated_fraud_rate_pct": current_fraud_rate,
                "observed_avg_amount": round(avg_amount, 2),
            }
        })

    return {
        "count": len(results),
        "merchants": results,
    }


@router.get("/{merchant_id}", summary="Get detailed profile and risk telemetry for a merchant")
def get_merchant_detail(
    merchant_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Fetch deep-dive risk profile for a specific merchant."""
    merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant '{merchant_id}' not found",
        )

    # Calculate risk telemetry
    tx_stats = (
        db.query(
            func.count(Transaction.id).label("total_tx"),
            func.sum(case((Transaction.is_fraud == 1, 1), else_=0)).label("fraud_tx"),
            func.sum(case((Transaction.risk_level == "HIGH", 1), else_=0)).label("high_risk_tx"),
            func.sum(case((Transaction.risk_level == "MEDIUM", 1), else_=0)).label("medium_risk_tx"),
            func.sum(case((Transaction.risk_level == "LOW", 1), else_=0)).label("low_risk_tx"),
            func.avg(Transaction.amount).label("avg_amount"),
            func.max(Transaction.amount).label("max_amount"),
        )
        .filter(Transaction.merchant_id == merchant_id)
        .first()
    )

    # Common fraud scenarios observed
    scenarios = (
        db.query(Transaction.fraud_scenario, func.count(Transaction.id).label("cnt"))
        .filter(Transaction.merchant_id == merchant_id, Transaction.is_fraud == 1)
        .group_by(Transaction.fraud_scenario)
        .order_by(desc("cnt"))
        .limit(5)
        .all()
    )

    # Recent transactions
    recent_txs = (
        db.query(Transaction)
        .filter(Transaction.merchant_id == merchant_id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "merchant": {
            "id": merchant.id,
            "merchant_id": merchant.merchant_id,
            "merchant_name": merchant.merchant_name,
            "category": merchant.category,
            "subcategory": merchant.subcategory,
            "city": merchant.city,
            "area": merchant.area,
            "state": merchant.state,
            "pincode": merchant.pincode,
            "latitude": merchant.latitude,
            "longitude": merchant.longitude,
            "business_age": merchant.business_age,
            "average_ticket": merchant.average_ticket,
            "operating_hours": merchant.operating_hours,
            "payment_channel": merchant.payment_channel,
            "historical_fraud_rate": round(merchant.historical_fraud_rate * 100, 2),
            "historical_fraud_count": merchant.historical_fraud_count,
            "historical_fraud_pattern": merchant.historical_fraud_pattern,
            "historical_fraud_summary": merchant.historical_fraud_summary,
        },
        "telemetry": {
            "total_transactions": int(tx_stats.total_tx or 0),
            "fraud_transactions": int(tx_stats.fraud_tx or 0),
            "high_risk_transactions": int(tx_stats.high_risk_tx or 0),
            "medium_risk_transactions": int(tx_stats.medium_risk_tx or 0),
            "low_risk_transactions": int(tx_stats.low_risk_tx or 0),
            "observed_avg_amount": round(float(tx_stats.avg_amount or 0.0), 2),
            "observed_max_amount": round(float(tx_stats.max_amount or 0.0), 2),
            "common_fraud_scenarios": [{"scenario": s[0], "count": s[1]} for s in scenarios if s[0]],
        },
        "recent_transactions": [
            {
                "transaction_id": tx.transaction_id,
                "amount": float(tx.amount),
                "currency": tx.currency or "INR",
                "risk_score": float(tx.risk_score or 0.0),
                "risk_level": tx.risk_level or "LOW",
                "fraud_probability": float(tx.fraud_probability or 0.0),
                "is_fraud": tx.is_fraud,
                "status": tx.status,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx in recent_txs
        ]
    }
