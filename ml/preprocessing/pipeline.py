"""Production Preprocessing Pipeline for Financial Fraud Detection."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
import pandas as pd
import sys
import types

# Ensure compatibility when Windows Smart App Control blocks optional sklearn C-extensions
if "sklearn.decomposition._online_lda_fast" not in sys.modules:
    try:
        from sklearn.decomposition import _online_lda_fast  # noqa: F401
    except (ImportError, OSError):
        _m = types.ModuleType("sklearn.decomposition._online_lda_fast")
        _m._dirichlet_expectation_1d = None
        _m._dirichlet_expectation_2d = None
        _m.mean_change = None
        sys.modules["sklearn.decomposition._online_lda_fast"] = _m

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.features.feature_engineer import FraudFeatureEngineer


class FullFraudPreprocessor(BaseEstimator, TransformerMixin):
    """Complete preprocessing and feature engineering pipeline for fraud detection.

    Steps:
    1. Feature Engineering (ratios, cyclical temporal encoding, leakage removal)
    2. Missing value imputation (median for numerical, constant for categorical)
    3. Scaling (StandardScaler for numerical)
    4. Categorical One-Hot Encoding (OneHotEncoder with handle_unknown='ignore')
    """

    def __init__(
        self,
        numerical_features: Optional[List[str]] = None,
        categorical_features: Optional[List[str]] = None,
    ) -> None:
        self.feature_engineer = FraudFeatureEngineer()
        self.numerical_features: Optional[List[str]] = numerical_features
        self.categorical_features: Optional[List[str]] = categorical_features
        self.column_transformer: Optional[ColumnTransformer] = None
        self.transformed_feature_names_: List[str] = []
        self.is_fitted_: bool = False

    def _infer_feature_types(self, df_engineered: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """Automatically classify features into numerical and categorical columns."""
        num_cols: List[str] = []
        cat_cols: List[str] = []

        for col in df_engineered.columns:
            if pd.api.types.is_numeric_dtype(df_engineered[col]):
                num_cols.append(col)
            else:
                cat_cols.append(col)

        return num_cols, cat_cols

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "FullFraudPreprocessor":
        """Fit feature engineer and ColumnTransformer on training data only."""
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        # 1. Fit & transform feature engineer
        df_eng = self.feature_engineer.fit_transform(X)

        # 2. Identify numerical & categorical columns
        if self.numerical_features is None or self.categorical_features is None:
            inferred_num, inferred_cat = self._infer_feature_types(df_eng)
            self.numerical_features = self.numerical_features or inferred_num
            self.categorical_features = self.categorical_features or inferred_cat

        # 3. Build sub-pipelines
        num_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])

        cat_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])

        self.column_transformer = ColumnTransformer(
            transformers=[
                ("num", num_pipeline, self.numerical_features),
                ("cat", cat_pipeline, self.categorical_features),
            ],
            remainder="drop",
        )

        self.column_transformer.fit(df_eng)

        # 4. Extract output feature names
        try:
            self.transformed_feature_names_ = list(
                self.column_transformer.get_feature_names_out()
            )
        except Exception:
            # Fallback for dynamic feature names
            self.transformed_feature_names_ = (
                [f"num__{c}" for c in self.numerical_features]
                + [f"cat__{c}" for c in self.categorical_features]
            )

        self.is_fitted_ = True
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform raw input into model-ready matrix."""
        if not self.is_fitted_ or self.column_transformer is None:
            raise RuntimeError("FullFraudPreprocessor is not fitted yet. Call fit() before transform().")

        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        df_eng = self.feature_engineer.transform(X)
        transformed = self.column_transformer.transform(df_eng)
        return transformed

    def fit_transform(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> np.ndarray:
        """Fit on training data and return transformed model-ready matrix."""
        return self.fit(X, y).transform(X)

    def get_feature_names_out(self, input_features: Optional[List[str]] = None) -> List[str]:
        """Return names of output features after one-hot encoding and scaling."""
        return self.transformed_feature_names_

    def save(self, artifact_path: Union[str, Path]) -> None:
        """Serialize fitted preprocessor pipeline to disk."""
        path = Path(artifact_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, artifact_path: Union[str, Path]) -> "FullFraudPreprocessor":
        """Load fitted preprocessor pipeline from disk."""
        return joblib.load(artifact_path)

    def get_metadata(self) -> Dict[str, Any]:
        """Export metadata describing the preprocessor configuration and output dimensions."""
        return {
            "is_fitted": self.is_fitted_,
            "numerical_features_count": len(self.numerical_features or []),
            "numerical_features": self.numerical_features or [],
            "categorical_features_count": len(self.categorical_features or []),
            "categorical_features": self.categorical_features or [],
            "total_output_features": len(self.transformed_feature_names_),
            "output_feature_names": self.transformed_feature_names_,
        }
