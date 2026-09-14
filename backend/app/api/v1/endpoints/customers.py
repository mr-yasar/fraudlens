"""Customer Management Endpoints (Phase 11)."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, asc, func
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.api.deps import require_investigator
from backend.app.schemas.customer import (
    CustomerResponse,
    CustomerBehavioralStats,
    CustomerDetailResponse,
    CustomerListResponse,
)
from backend.app.schemas.transaction import (
    TransactionSummaryResponse,
    TransactionListResponse,
)

router = APIRouter()


@router.get(
    "",
    response_model=CustomerListResponse,
    summary="List Customers with Pagination and Search",
    description="Retrieves a paginated list of customers with dynamic transaction count calculation and search capabilities.",
)
def list_customers(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by customer_id substring"),
    sort_by: str = Query("created_at", description="Sort field: created_at, customer_id, account_age_days"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> CustomerListResponse:
    """List customers with pagination, sorting, and search."""
    # Subquery for transaction count per customer
    tx_count_subquery = (
        db.query(
            Transaction.customer_id,
            func.count(Transaction.id).label("tx_count"),
        )
        .group_by(Transaction.customer_id)
        .subquery()
    )

    query = db.query(
        Customer,
        func.coalesce(tx_count_subquery.c.tx_count, 0).label("transaction_count"),
    ).outerjoin(
        tx_count_subquery,
        Customer.customer_id == tx_count_subquery.c.customer_id,
    )

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(Customer.customer_id.ilike(search_term))

    # Apply sorting
    sort_field_map = {
        "created_at": Customer.created_at,
        "customer_id": Customer.customer_id,
        "account_age_days": Customer.account_age_days,
    }
    sort_col = sort_field_map.get(sort_by, Customer.created_at)
    order_func = desc if sort_order.lower() == "desc" else asc
    query = query.order_by(order_func(sort_col))

    total = query.count()
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()

    items = []
    for cust, tx_count in results:
        items.append(
            CustomerResponse(
                id=cust.id,
                customer_id=cust.customer_id,
                account_age_days=cust.account_age_days,
                created_at=cust.created_at,
                transaction_count=int(tx_count),
            )
        )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    return CustomerListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerDetailResponse,
    summary="Get Customer Profile & Behavioral Statistics",
    description="Returns detailed customer information, historical transaction count, recent transactions, and dynamic behavioral statistics.",
)
def get_customer_detail(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> CustomerDetailResponse:
    """Get single customer profile with dynamic behavioral metrics."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found.",
        )

    # 1. Calculate actual database statistics for this customer
    tx_query = db.query(Transaction).filter(Transaction.customer_id == customer_id)
    total_tx_count = tx_query.count()

    stats_row = (
        db.query(
            func.count(Transaction.id).label("cnt"),
            func.avg(Transaction.amount).label("avg_amt"),
            func.min(Transaction.amount).label("min_amt"),
            func.max(Transaction.amount).label("max_amt"),
        )
        .filter(Transaction.customer_id == customer_id)
        .first()
    )

    avg_amt = float(stats_row.avg_amt) if stats_row and stats_row.avg_amt is not None else 0.0
    min_amt = float(stats_row.min_amt) if stats_row and stats_row.min_amt is not None else 0.0
    max_amt = float(stats_row.max_amt) if stats_row and stats_row.max_amt is not None else 0.0

    # Recent transactions count (within 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_cnt = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.customer_id == customer_id, Transaction.created_at >= thirty_days_ago)
        .scalar()
        or 0
    )

    # High risk and fraud counts
    high_risk_cnt = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.customer_id == customer_id, Transaction.risk_level == "HIGH")
        .scalar()
        or 0
    )

    fraud_cnt = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.customer_id == customer_id, Transaction.prediction == 1)
        .scalar()
        or 0
    )

    behavioral_stats = CustomerBehavioralStats(
        transaction_count=total_tx_count,
        average_transaction_amount=round(avg_amt, 2),
        min_transaction_amount=round(min_amt, 2),
        max_transaction_amount=round(max_amt, 2),
        recent_transaction_count=recent_cnt,
        high_risk_transaction_count=high_risk_cnt,
        fraud_transaction_count=fraud_cnt,
    )

    # 2. Get top 10 recent transactions
    recent_txs = (
        db.query(Transaction)
        .filter(Transaction.customer_id == customer_id)
        .order_by(desc(Transaction.created_at))
        .limit(10)
        .all()
    )

    recent_tx_list = [
        {
            "id": tx.id,
            "transaction_id": tx.transaction_id,
            "amount": float(tx.amount),
            "merchant_category": tx.merchant_category,
            "fraud_probability": tx.fraud_probability,
            "prediction": "FRAUD" if tx.prediction == 1 else "GENUINE",
            "risk_score": tx.risk_score,
            "risk_level": tx.risk_level,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }
        for tx in recent_txs
    ]

    return CustomerDetailResponse(
        id=customer.id,
        customer_id=customer.customer_id,
        account_age_days=customer.account_age_days,
        created_at=customer.created_at,
        transaction_count=total_tx_count,
        behavioral_stats=behavioral_stats,
        recent_transactions=recent_tx_list,
    )


@router.get(
    "/{customer_id}/transactions",
    response_model=TransactionListResponse,
    summary="Get Customer Transaction History",
    description="Retrieves a paginated list of transactions specifically belonging to the given customer with multi-field filtering and sorting.",
)
def get_customer_transactions(
    customer_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (LOW, MEDIUM, HIGH)"),
    prediction: Optional[str] = Query(None, description="Filter by prediction (FRAUD or GENUINE)"),
    min_amount: Optional[float] = Query(None, ge=0.0, description="Minimum transaction amount"),
    max_amount: Optional[float] = Query(None, ge=0.0, description="Maximum transaction amount"),
    start_date: Optional[datetime] = Query(None, description="Earliest transaction creation datetime"),
    end_date: Optional[datetime] = Query(None, description="Latest transaction creation datetime"),
    sort_by: str = Query("created_at", description="Sort field: created_at, amount, risk_score, fraud_probability"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> TransactionListResponse:
    """Retrieve filtered, paginated transaction history for a specific customer."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found.",
        )

    query = db.query(Transaction).filter(Transaction.customer_id == customer_id)

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
    sort_field_map = {
        "created_at": Transaction.created_at,
        "amount": Transaction.amount,
        "risk_score": Transaction.risk_score,
        "fraud_probability": Transaction.fraud_probability,
    }
    sort_col = sort_field_map.get(sort_by, Transaction.created_at)
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
