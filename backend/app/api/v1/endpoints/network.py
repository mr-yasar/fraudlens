"""
Fraud Network & Relationship Graph Endpoints.
Part D & E: Fraud Intelligence Fabric.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.api.deps import get_current_user
from backend.app.services.network_intelligence_service import FraudNetworkIntelligenceService

router = APIRouter()


@router.get(
    "/graph",
    summary="Get Relationship Subgraph for Entity Visualization",
    description="Extracts multi-hop connection topology (Customer, Devices, Transactions, Merchants, Investigations) for graph visualization.",
)
def get_relationship_graph(
    customer_id: str = Query(..., description="Root customer identifier to center the relationship graph"),
    depth: int = Query(2, ge=1, le=4, description="Graph traversal depth"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve node-edge graph structure for customer entity."""
    try:
        subgraph = FraudNetworkIntelligenceService.build_relationship_subgraph(
            db=db,
            customer_id=customer_id,
            depth=depth,
        )
        return subgraph
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate network subgraph: {str(e)}",
        )


@router.get(
    "/clusters",
    summary="Get Syndicated Clusters and Shared Device Rings",
    description="Returns global analytics on multi-account hardware sharing and active fraud clusters.",
)
def get_network_clusters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve global network clusters overview."""
    try:
        clusters = FraudNetworkIntelligenceService.get_network_clusters_overview(db=db)
        return clusters
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute network clusters: {str(e)}",
        )
