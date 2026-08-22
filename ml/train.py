"""
Machine Learning Training Pipeline for PaySim Fraud Detection

Trains an XGBoost / Random Forest classifier optimized for highly imbalanced
fraud detection. Evaluates and exports comprehensive fraud metrics (Precision,
Recall, F1, ROC-AUC, PR-AUC, Confusion Matrix) and saves artifacts for real-time scoring.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix, classification_report
)

# Support running directly or as module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ml.features import extract_features_from_dataframe, FEATURE_COLUMNS
from scripts.generate_sample_data import generate_paysim_sample
from config.settings import settings


def train_fraud_model(
    data_path: str = None,
    model_output_path: str = None,
    metadata_output_path: str = None,
    test_size: float = 0.25,
    random_state: int = 42
):
    """
    Trains, evaluates, and persists the fraud detection model.
    """
    data_path = data_path or settings.DATASET_PATH
    model_output_path = model_output_path or settings.MODEL_PATH
    metadata_output_path = metadata_output_path or settings.MODEL_METADATA_PATH

    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    os.makedirs(os.path.dirname(metadata_output_path), exist_ok=True)

    # 1. Dataset Verification & Loading
    if not os.path.exists(data_path):
        if os.path.exists(settings.PAYSIM_RAW_PATH):
            print(f"Found raw PaySim dataset at: {settings.PAYSIM_RAW_PATH}")
            data_path = settings.PAYSIM_RAW_PATH
            is_synthetic = False
        else:
            print(f"Dataset not found at '{data_path}'. Generating PaySim-compatible synthetic demo data...")
            generate_paysim_sample(num_records=30000, output_path=data_path)
            is_synthetic = True
    else:
        is_synthetic = "sample" in data_path.lower() or "synthetic" in data_path.lower()

    print(f"Loading dataset from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Dataset loaded: {len(df):,} records, {len(df.columns)} columns")
    print(f"Columns: {list(df.columns)}")

    required_cols = ["amount", "type", "nameOrig", "oldbalanceOrg", "newbalanceOrig", "nameDest", "oldbalanceDest", "newbalanceDest", "isFraud"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required PaySim column: {col}")

    total_records = len(df)
    fraud_records = int(df["isFraud"].sum())
    normal_records = total_records - fraud_records
    fraud_rate = (fraud_records / total_records) * 100.0

    print(f"\n--- Dataset Class Distribution ---")
    print(f"Normal Transactions: {normal_records:,} ({(100 - fraud_rate):.2f}%)")
    print(f"Fraud Transactions : {fraud_records:,} ({fraud_rate:.2f}%)")

    # 2. Feature Extraction
    print("\nExtracting domain & balance discrepancy features...")
    X = extract_features_from_dataframe(df)
    y = df["isFraud"].astype(int)

    # 3. Train/Test Stratified Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    print(f"Train split: {len(X_train):,} rows ({y_train.sum()} fraud)")
    print(f"Test split : {len(X_test):,} rows ({y_test.sum()} fraud)")

    # 4. Model Training (XGBoost with Class Imbalance Weighting)
    pos_scale = (len(y_train) - y_train.sum()) / max(1, y_train.sum())
    print(f"\nTraining XGBoost Classifier (scale_pos_weight={pos_scale:.2f})...")

    try:
        from xgboost import XGBClassifier
        model = XGBClassifier(
            n_estimators=120,
            max_depth=5,
            learning_rate=0.08,
            scale_pos_weight=pos_scale,
            eval_metric="aucpr",
            random_state=random_state,
            n_jobs=-1
        )
        model_name = "XGBoost Classifier"
    except Exception as e:
        print(f"XGBoost unavailable ({e}), falling back to Scikit-Learn RandomForestClassifier...")
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1
        )
        model_name = "RandomForest Classifier"

    start_time = time.time()
    model.fit(X_train, y_train)
    train_duration = round(time.time() - start_time, 2)
    print(f"Training completed in {train_duration}s")

    # 5. Evaluation
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= settings.FRAUD_SCORE_THRESHOLD).astype(int)

    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_pred_proba)) if len(np.unique(y_test)) > 1 else 1.0
    pr_auc = float(average_precision_score(y_test, y_pred_proba)) if len(np.unique(y_test)) > 1 else 1.0
    cm = confusion_matrix(y_test, y_pred).tolist()

    print("\n" + "="*50)
    print(f"=== {model_name} Model Evaluation ===")
    print("="*50)
    print(f"Precision          : {precision:.4f}  (Low False Positives)")
    print(f"Recall (Sensitivity): {recall:.4f}  (Low False Negatives / Missed Fraud)")
    print(f"F1-Score           : {f1:.4f}")
    print(f"ROC-AUC            : {roc_auc:.4f}")
    print(f"PR-AUC (Avg Prec)  : {pr_auc:.4f}")
    print("\nConfusion Matrix:")
    print(f"  [TN: {cm[0][0]:<6}  FP: {cm[0][1]:<6}]")
    print(f"  [FN: {cm[1][0]:<6}  TP: {cm[1][1]:<6}]")
    print("="*50)

    # Feature Importance
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_.tolist()
        feat_imp = sorted(
            [{"feature": col, "importance": round(imp, 4)} for col, imp in zip(FEATURE_COLUMNS, importances)],
            key=lambda x: x["importance"],
            reverse=True
        )
    else:
        feat_imp = []

    # 6. Save Model Artifact and Metadata
    joblib.dump(model, model_output_path)
    print(f"\nTrained model artifact saved to: {model_output_path}")

    metadata = {
        "model_name": model_name,
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "dataset_source": "PaySim-compatible synthetic demo data" if is_synthetic else "PaySim Benchmark Dataset",
        "dataset_path": data_path,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "fraud_count_total": fraud_records,
        "fraud_rate_pct": round(fraud_rate, 3),
        "metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "confusion_matrix": {
                "true_negative": cm[0][0],
                "false_positive": cm[0][1],
                "false_negative": cm[1][0],
                "true_positive": cm[1][1]
            }
        },
        "feature_columns": FEATURE_COLUMNS,
        "feature_importances": feat_imp,
        "thresholds": {
            "fraud_score_threshold": settings.FRAUD_SCORE_THRESHOLD,
            "high_risk_threshold": settings.HIGH_RISK_THRESHOLD,
            "critical_risk_threshold": settings.CRITICAL_RISK_THRESHOLD
        }
    }

    with open(metadata_output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Model metadata exported to: {metadata_output_path}")

    return model, metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Fraud Detection ML Model")
    parser.add_argument("--data", type=str, default=None, help="Path to PaySim CSV dataset")
    parser.add_argument("--model-out", type=str, default=None, help="Output path for saved model .joblib")
    parser.add_argument("--meta-out", type=str, default=None, help="Output path for metadata .json")
    args = parser.parse_args()

    train_fraud_model(
        data_path=args.data,
        model_output_path=args.model_out,
        metadata_output_path=args.meta_out
    )
