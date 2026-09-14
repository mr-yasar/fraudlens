# ML Model Training, Evaluation & Imbalance Handling Report

**System Module:** `ml/training/trainer.py`  
**Execution Script:** `ml/training/train.py`  
**Artifact Directory:** `ml/artifacts/`

---

## 1. Machine Learning Pipeline Architecture

```
Validated Dataset
        │
        ▼
Stratified Train/Val/Test Split (70% / 15% / 15%)
        │
        ▼
FullFraudPreprocessor (Feature Engineering + Scaling + OneHotEncoding)
        │
        ▼
Class Imbalance Handling
├─ Logistic Regression: class_weight="balanced"
├─ Random Forest: class_weight="balanced"
└─ XGBoost: scale_pos_weight = (n_neg / n_pos)
        │
        ▼
Model Training & Evaluation
├─ Accuracy, Precision, Recall, F1-Score
├─ ROC-AUC & PR-AUC (Average Precision)
├─ False Positive Rate (FPR) & False Negative Rate (FNR)
└─ Confusion Matrix
        │
        ▼
Artifact Serialization (ml/artifacts/)
├─ logistic_regression.joblib
├─ random_forest.joblib
├─ xgboost.joblib
├─ preprocessor.joblib
├─ feature_metadata.json
├─ evaluation_results.json
└─ training_metadata.json
```

---

## 2. Models Trained & Evaluated

### 1. Logistic Regression (Baseline Linear Classifier)
- **Configuration:** `LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42, solver="lbfgs")`
- **Imbalance Handling:** Inverse frequency weighting via `class_weight="balanced"`.
- **Strengths:** High interpretability, linear log-odds coefficients, fast baseline.

### 2. Random Forest (Bagging Non-Linear Classifier)
- **Configuration:** `RandomForestClassifier(n_estimators=100, max_depth=12, class_weight="balanced", random_state=42, n_jobs=-1)`
- **Imbalance Handling:** Sub-tree bootstrap weighting via `class_weight="balanced"`.
- **Strengths:** Robust to non-linear interactions, handles numerical and categorical feature mixtures smoothly.

### 3. XGBoost (Gradient Boosted Decision Trees)
- **Configuration:** `XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, scale_pos_weight=scale_pos_weight, eval_metric="logloss", random_state=42)`
- **Imbalance Handling:** Exact negative-to-positive ratio weighting via `scale_pos_weight`.
- **Strengths:** State-of-the-art tabular performance, gradient optimization on hard fraud edge cases.

---

## 3. Evaluation Metrics for Imbalanced Fraud Detection

Because fraud detection datasets are heavily imbalanced (typically 1% - 5% fraud rate):
1. **PR-AUC (Precision-Recall Area Under Curve / Average Precision)**: Primary metric reflecting the precision-recall trade-off across varying detection thresholds.
2. **Recall (Sensitivity / True Positive Rate)**: Measures fraud capture efficiency ($TP / (TP + FN)$).
3. **Precision**: Measures alert reliability ($TP / (TP + FP)$).
4. **False Positive Rate (FPR)**: Customer friction rate ($FP / (FP + TN)$).
5. **False Negative Rate (FNR)**: Missed fraud rate ($FN / (FN + TP)$).
6. **ROC-AUC**: Global ranking discriminative ability.

---

## 4. Model Artifact Registry

All trained pipelines and metadata are stored in `ml/artifacts/`:
- `logistic_regression.joblib`: Serialized Logistic Regression model.
- `random_forest.joblib`: Serialized Random Forest model.
- `xgboost.joblib`: Serialized XGBoost model.
- `preprocessor.joblib`: Serialized fitted `FullFraudPreprocessor`.
- `feature_metadata.json`: Feature list, types, and input/output dimensions.
- `evaluation_results.json`: Complete metrics dictionary for validation and test splits.
- `training_metadata.json`: Timestamp, hyperparameters, seed, and data split sizes.
