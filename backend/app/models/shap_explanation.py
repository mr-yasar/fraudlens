"""SHAP Explanation model definition."""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class ShapExplanation(Base):
    """SHAP (SHapley Additive exPlanations) values for individual transaction features."""

    __tablename__ = "shap_explanations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(
        String(100),
        ForeignKey("transactions.transaction_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    feature_name = Column(String(100), nullable=False)
    shap_value = Column(Float, nullable=False)
    impact = Column(String(50), nullable=True)  # e.g., 'positive', 'negative', 'high_risk'
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    transaction = relationship("Transaction", back_populates="shap_explanations")

    __table_args__ = (
        Index("ix_shap_tx_feature", "transaction_id", "feature_name"),
    )

    def __repr__(self) -> str:
        return f"<ShapExplanation id={self.id} transaction_id='{self.transaction_id}' feature='{self.feature_name}' shap_value={self.shap_value}>"
