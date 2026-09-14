"""Dataset Management & Validation Endpoints (Admin only)."""

import io
from typing import Any, Dict
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
import pandas as pd

from backend.app.models.user import User
from backend.app.api.deps import require_admin
from ml.validation.dataset_validator import DatasetValidator, DatasetSchema

router = APIRouter()
validator = DatasetValidator()


@router.get(
    "/schema",
    summary="Get Expected Dataset Schema",
    description="Fetch expected column definitions, data types, and target specification for Lead AI Fraud Detection Dataset v2.",
)
def get_expected_schema() -> Dict[str, Any]:
    schema = DatasetSchema()
    return {
        "target_column": schema.target_column,
        "target_values": list(schema.expected_target_values),
        "expected_columns": schema.expected_columns,
        "value_constraints": schema.value_constraints,
        "known_leakage_candidates": schema.leakage_candidates,
    }


@router.post(
    "/validate",
    summary="Validate Uploaded Dataset (Admin Only)",
    description="Performs comprehensive 11-step audit (schema, missing values, duplicates, class distribution, and target leakage) on uploaded dataset.",
)
async def validate_dataset_file(
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
) -> Dict[str, Any]:
    filename = file.filename or ""
    suffix = "." + filename.split(".")[-1].lower() if "." in filename else ""

    if suffix not in [".csv", ".parquet", ".json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{suffix}'. Please upload a .csv, .parquet, or .json file.",
        )

    content = await file.read()
    try:
        if suffix == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        elif suffix == ".parquet":
            df = pd.read_parquet(io.BytesIO(content))
        else:
            df = pd.read_json(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing uploaded file: {str(e)}",
        )

    result = validator.validate_dataframe(df, file_type=suffix)
    return result.to_dict()
