"""Model Version tracking model definition."""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from backend.app.core.database import Base


class ModelVersion(Base):
    """Machine learning model metadata, performance metrics, and deployment status."""

    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_name = Column(String(100), index=True, nullable=False)
    version = Column(String(50), nullable=False)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    roc_auc = Column(Float, nullable=True)
    pr_auc = Column(Float, nullable=True)
    model_path = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    trained_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("model_name", "version", name="uq_model_version_name_ver"),
    )

    def __repr__(self) -> str:
        return f"<ModelVersion id={self.id} model='{self.model_name}' version='{self.version}' f1={self.f1_score}>"
