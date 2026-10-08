"""Assistant Financial Context & Transaction Intelligence Service (Phases 7-9).

Provides:
- Phase 7: Safe, minimal, auditable context envelope for model interpretation
- Phase 8: Controlled read operations for transactions (default limit = 5)
- Phase 9: Wallet and account summaries with masked identifiers (•••• 4821)
"""

import re
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.transaction import Transaction
from backend.app.models.customer import Customer
from backend.app.models.approval import TransactionApproval, ApprovalStatus
from backend.app.services.assistant_identity_service import AssistantIdentityContext

logger = logging.getLogger("fraudlens.assistant.financial")

DEFAULT_RECENT_LIMIT = 5


def get_wallet_account_summary(customer_id: Optional[str], db: Session) -> Dict[str, Any]:
    """Phase 9: Compute authorized wallet/account summary without leaking raw identifiers."""
    if not customer_id:
        return {
            "account_status": "GUEST_UNLINKED",
            "available_balance": None,
            "currency": "INR",
            "account_number_masked": "•••• 0000",
        }

    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    balance = float(customer.simulated_balance) if customer and customer.simulated_balance is not None else 50000.0
    currency = customer.currency if customer and customer.currency else "INR"

    # Pending held amounts
    pending_holds = (
        db.query(func.coalesce(func.sum(TransactionApproval.amount), 0.0))
        .filter(
            TransactionApproval.customer_id == customer_id,
            TransactionApproval.status == ApprovalStatus.PENDING.value,
        )
        .scalar()
    )

    last_digits = "4821"
    if customer_id == "CUST_MOHANA_002":
        last_digits = "8912"
    elif customer_id == "CUST_SOWMIYA_003":
        last_digits = "3391"
    elif customer_id == "CUST_AJAY_004":
        last_digits = "7104"

    return {
        "account_status": "ACTIVE_VERIFIED",
        "available_balance": balance,
        "held_balance": float(pending_holds or 0.0),
        "currency": currency,
        "account_number_masked": f"•••• {last_digits}",
    }


def get_recent_transactions(
    customer_id: Optional[str],
    db: Session,
    limit: int = DEFAULT_RECENT_LIMIT,
    is_admin: bool = False,
) -> List[Dict[str, Any]]:
    """Phase 8: Retrieve customer-scoped recent transactions with safe fields."""
    query = db.query(Transaction)
    if not is_admin and customer_id:
        query = query.filter(Transaction.customer_id == customer_id)
    elif not is_admin and not customer_id:
        return []

    records = query.order_by(Transaction.created_at.desc()).limit(limit).all()
    results = []
    for r in records:
        prob_pct = f"{round(r.fraud_probability * 100, 1)}%" if r.fraud_probability is not None else "N/A"
        results.append({
            "transaction_id": r.transaction_id,
            "merchant": r.merchant_name or "Retail Store",
            "amount": float(r.amount),
            "currency": r.currency or "INR",
            "status": r.status or "SUCCESS",
            "risk_score": int(r.risk_score) if r.risk_score is not None else 15,
            "risk_level": (r.risk_level or "LOW").upper(),
            "fraud_probability": prob_pct,
            "timestamp": r.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if r.created_at else None,
            "device": "Trusted Device" if r.is_trusted_device else "Unrecognized Device",
        })
    return results


def get_transaction_summary(customer_id: Optional[str], db: Session, is_admin: bool = False) -> Dict[str, Any]:
    """Phase 8: Compute high-level ledger summary for broad queries."""
    query = db.query(Transaction)
    if not is_admin and customer_id:
        query = query.filter(Transaction.customer_id == customer_id)
    elif not is_admin and not customer_id:
        return {"total_count": 0, "total_spend": 0.0, "approved_count": 0, "held_count": 0}

    total_count = query.count()
    total_spend = query.filter(Transaction.status.in_(["SUCCESS", "ALLOW", "APPROVED"])).with_entities(
        func.coalesce(func.sum(Transaction.amount), 0.0)
    ).scalar()

    approved_count = query.filter(Transaction.status.in_(["SUCCESS", "ALLOW", "APPROVED"])).count()
    held_count = query.filter(Transaction.status.in_(["REVIEW", "PENDING_VERIFICATION", "HELD"])).count()

    return {
        "total_count": total_count,
        "total_spend": float(total_spend or 0.0),
        "approved_count": approved_count,
        "held_count": held_count,
    }


def get_pending_holds(customer_id: Optional[str], db: Session) -> List[Dict[str, Any]]:
    """Phase 8: Retrieve active pending verification holds for customer."""
    if not customer_id:
        return []

    approvals = (
        db.query(TransactionApproval)
        .filter(
            TransactionApproval.customer_id == customer_id,
            TransactionApproval.status == ApprovalStatus.PENDING.value,
        )
        .order_by(TransactionApproval.requested_at.desc())
        .limit(5)
        .all()
    )

    holds = []
    for a in approvals:
        clean_reason = a.notes or "Step-up verification challenge active"
        if clean_reason.startswith("{"):
            try:
                parsed = json.loads(clean_reason)
                clean_reason = parsed.get("reason") or parsed.get("explanation") or "Rapid transaction activity detected"
            except Exception:
                clean_reason = "Security verification required"

        holds.append({
            "approval_id": a.approval_id,
            "transaction_id": a.transaction_id,
            "amount": float(a.amount),
            "currency": a.currency,
            "risk_score": int(a.risk_score),
            "risk_level": a.risk_level,
            "reason": clean_reason,
            "requested_at": a.requested_at.strftime("%Y-%m-%d %H:%M:%S UTC") if a.requested_at else None,
        })
    return holds


def find_specific_transaction(
    customer_id: Optional[str],
    query_text: str,
    db: Session,
    is_admin: bool = False,
) -> Optional[Dict[str, Any]]:
    """Look up a specific transaction mentioned in query by ID, amount, or merchant."""
    # 1. By ID match
    tx_match = re.search(r"\b(TXN[_-]?[A-Za-z0-9_-]+)\b", query_text, re.IGNORECASE)
    if tx_match:
        tx_id = tx_match.group(1).upper()
        q = db.query(Transaction).filter(Transaction.transaction_id == tx_id)
        if not is_admin and customer_id:
            q = q.filter(Transaction.customer_id == customer_id)
        r = q.first()
        if r:
            return {
                "transaction_id": r.transaction_id,
                "merchant": r.merchant_name or "Retail Store",
                "amount": float(r.amount),
                "currency": r.currency,
                "status": r.status,
                "risk_score": int(r.risk_score) if r.risk_score is not None else 15,
                "risk_level": r.risk_level or "LOW",
                "fraud_probability": f"{round(r.fraud_probability * 100, 1)}%" if r.fraud_probability else "N/A",
                "timestamp": r.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if r.created_at else None,
            }

    # 2. By Amount match (e.g. "₹500 payment" or "500 payment")
    amt_match = re.search(r"(?:₹|\bRs\.?|\bINR\s*|\bamount\s*)?(\d{2,6})(?:\.\d{1,2})?", query_text, re.IGNORECASE)
    if amt_match:
        try:
            target_amt = float(amt_match.group(1))
            q = db.query(Transaction).filter(Transaction.amount == target_amt)
            if not is_admin and customer_id:
                q = q.filter(Transaction.customer_id == customer_id)
            r = q.order_by(Transaction.created_at.desc()).first()
            if r:
                return {
                    "transaction_id": r.transaction_id,
                    "merchant": r.merchant_name or "Retail Store",
                    "amount": float(r.amount),
                    "currency": r.currency,
                    "status": r.status,
                    "risk_score": int(r.risk_score) if r.risk_score is not None else 15,
                    "risk_level": r.risk_level or "LOW",
                    "fraud_probability": f"{round(r.fraud_probability * 100, 1)}%" if r.fraud_probability else "N/A",
                    "timestamp": r.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if r.created_at else None,
                }
        except Exception:
            pass

    return None


def build_safe_context_envelope(
    identity: AssistantIdentityContext,
    user_query: str,
    db: Session,
    ui_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Phase 7: Assemble minimal, structured, auditable context for the AI engine."""
    now_utc = datetime.now(timezone.utc)
    current_time_str = now_utc.strftime("%A, %b %d, %Y, %I:%M %p UTC")

    q_lower = user_query.lower()
    needs_wallet  = any(k in q_lower for k in ["balance", "wallet", "account", "money", "funds", "how much"])
    needs_recent  = any(k in q_lower for k in ["recent", "last", "transaction", "payment", "history", "spend", "bought", "transferred", "purchase"])
    needs_holds   = any(k in q_lower for k in ["hold", "pending", "otp", "stuck", "paused", "review", "verification", "blocked"])
    needs_tx_look = any(k in q_lower for k in ["txn", "transaction id", "specific", "that payment", "that transaction"])

    # Base Envelope — always lightweight
    wallet_summary = get_wallet_account_summary(identity.customer_id, db) if identity.customer_id else {}
    envelope: Dict[str, Any] = {
        "current_time": current_time_str,
        "authorized_user": identity.name,
        "authorized_scope": identity.authorized_scope,
        "customer_id": identity.customer_id,
        "wallet": wallet_summary,
        "account_summary": wallet_summary,
        "identity": {
            "customer_id": identity.customer_id,
            "name": identity.name,
            "role": identity.role,
        },
        "ui_view": ui_context.get("view") if ui_context else None,
    }

    # 2. Specific Transaction Lookup & Risk Explanation
    #    First check if UI provided a focused transaction or case ID in ui_context:
    specific_tx = None
    if ui_context and isinstance(ui_context, dict):
        ui_tx_id = ui_context.get("transaction_id")
        ui_case_id = ui_context.get("case_id")
        if ui_tx_id:
            tx_obj = db.query(Transaction).filter(Transaction.transaction_id == str(ui_tx_id).strip()).first()
            if tx_obj:
                specific_tx = {
                    "transaction_id": tx_obj.transaction_id,
                    "merchant": tx_obj.merchant_name or "Retail Store",
                    "amount": float(tx_obj.amount),
                    "currency": tx_obj.currency,
                    "status": tx_obj.status,
                    "risk_score": int(tx_obj.risk_score) if tx_obj.risk_score is not None else 15,
                    "risk_level": tx_obj.risk_level or "LOW",
                    "fraud_probability": f"{round(tx_obj.fraud_probability * 100, 1)}%" if tx_obj.fraud_probability else "N/A",
                    "timestamp": tx_obj.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if tx_obj.created_at else None,
                }
        elif ui_case_id:
            from backend.app.models.investigation import Investigation
            inv_obj = db.query(Investigation).filter(Investigation.case_id == str(ui_case_id).strip()).first()
            if inv_obj and inv_obj.transaction:
                tx_obj = inv_obj.transaction
                specific_tx = {
                    "transaction_id": tx_obj.transaction_id,
                    "case_id": inv_obj.case_id,
                    "merchant": tx_obj.merchant_name or "Retail Store",
                    "amount": float(tx_obj.amount),
                    "currency": tx_obj.currency,
                    "status": tx_obj.status,
                    "risk_score": int(tx_obj.risk_score) if tx_obj.risk_score is not None else 15,
                    "risk_level": tx_obj.risk_level or "LOW",
                    "fraud_probability": f"{round(tx_obj.fraud_probability * 100, 1)}%" if tx_obj.fraud_probability else "N/A",
                    "timestamp": tx_obj.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if tx_obj.created_at else None,
                }

    # If not resolved from ui_context, run query text extraction:
    if not specific_tx and (needs_tx_look or needs_holds or needs_recent):
        specific_tx = find_specific_transaction(identity.customer_id, user_query, db, is_admin=identity.is_admin)

    if specific_tx:
        envelope["focused_transaction"] = specific_tx
        tx_obj = db.query(Transaction).filter(Transaction.transaction_id == specific_tx["transaction_id"]).first()
        if tx_obj:
            from backend.app.services.assistant_explainability_service import explain_transaction_risk
            shap_records = tx_obj.shap_explanations if hasattr(tx_obj, "shap_explanations") else []
            envelope["risk_explanation"] = explain_transaction_risk(tx_obj, shap_records, is_admin=identity.is_admin)

    # 3. Recent Transactions — only when the user explicitly asks for transaction history
    if needs_recent:
        envelope["recent_transactions"] = get_recent_transactions(
            identity.customer_id, db, limit=DEFAULT_RECENT_LIMIT, is_admin=identity.is_admin
        )
        envelope["transaction_summary"] = get_transaction_summary(
            identity.customer_id, db, is_admin=identity.is_admin
        )

    # 4. Active Holds / OTP Challenges — only when question is about holds or a specific tx
    if needs_holds or specific_tx:
        envelope["active_holds"] = get_pending_holds(identity.customer_id, db)

    return envelope


def format_context_for_prompt(envelope: Dict[str, Any]) -> str:
    """Format structured context envelope into clean markdown for system instruction."""
    lines = [
        f"**System Real-Time Clock**: {envelope.get('current_time')}",
        f"**Authorized User**: {envelope.get('authorized_user')} ({envelope.get('authorized_scope')})",
    ]

    acc = envelope.get("account_summary")
    if acc and isinstance(acc, dict) and acc.get("account_number_masked"):
        bal = f"₹{acc['available_balance']:,.2f}" if acc.get("available_balance") is not None else "N/A"
        held = f"₹{acc['held_balance']:,.2f}" if acc.get("held_balance") is not None else "₹0.00"
        lines.append(f"**Account Summary**: Masked Account {acc['account_number_masked']} | Available: {bal} | Held on Hold: {held}")

    if "focused_transaction" in envelope and isinstance(envelope["focused_transaction"], dict):
        tx = envelope["focused_transaction"]
        lines.append(
            f"**Focused Transaction**: ID `{tx.get('transaction_id')}` | Merchant: {tx.get('merchant', 'N/A')} | "
            f"Amount: ₹{tx.get('amount', 0.0):,.2f} | Status: {tx.get('status', 'N/A')} | Risk Score: {tx.get('risk_score', 0)}/100 ({tx.get('risk_level', 'LOW')}) | "
            f"Fraud Likelihood: {tx.get('fraud_probability', 'N/A')} | Timestamp: {tx.get('timestamp')}"
        )

    if "risk_explanation" in envelope and isinstance(envelope["risk_explanation"], dict):
        exp = envelope["risk_explanation"]
        signals_bullet = "\n".join(f"  * {s}" for s in exp.get("verified_signals", []))
        lines.append(
            f"**Verified Risk Explanation**:\n"
            f"- Risk Score: {exp.get('risk_score', 0)}/100 ({exp.get('risk_level', 'LOW')})\n"
            f"- Fraud Probability: {exp.get('fraud_probability', 'N/A')}\n"
            f"- Verified Contributing Signals:\n{signals_bullet}\n"
            f"- Action Required: {exp.get('action_required', 'None')}"
        )

    if "active_holds" in envelope and envelope["active_holds"]:
        holds_summary = []
        for h in envelope["active_holds"]:
            holds_summary.append(f"- Tx `{h.get('transaction_id')}`: ₹{h.get('amount', 0.0):,.2f} on Hold for: {h.get('reason')} (Risk Score: {h.get('risk_score')})")
        lines.append("**Active Holds Requiring OTP**:\n" + "\n".join(holds_summary))

    if "recent_transactions" in envelope and envelope["recent_transactions"]:
        tx_lines = []
        for t in envelope["recent_transactions"][:5]:
            tx_lines.append(f"- `{t.get('transaction_id')}` | {t.get('merchant')} | ₹{t.get('amount', 0.0):,.2f} | Status: {t.get('status')} | Risk: {t.get('risk_score')}/100 ({t.get('risk_level')}) | Date: {t.get('timestamp')}")
        lines.append("**Verified Recent Transactions (Latest 5)**:\n" + "\n".join(tx_lines))

    if "transaction_summary" in envelope and isinstance(envelope["transaction_summary"], dict):
        s = envelope["transaction_summary"]
        lines.append(f"**Ledger Metrics**: {s.get('total_count', 0)} Total Transactions | Approved: {s.get('approved_count', 0)} | On Hold: {s.get('held_count', 0)} | Total Outflow: ₹{s.get('total_spend', 0.0):,.2f}")

    return "\n\n".join(lines)
