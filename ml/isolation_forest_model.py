"""
Isolation Forest Anomaly Detection Model

Unsupervised anomaly detector for financial transactions.
Isolates anomalous instances by randomly partitioning feature space.
Normalizes anomaly score into a 0-100 anomaly risk score.
"""

import os
import sys
import logging
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from sklearn.ensemble import IsolationForest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import settings
from ml.features import extract_features_from_dict, extract_features_from_dataframe, FEATURE_COLUMNS

logger = logging.getLogger("isolation_forest_model")


class IsolationForestAnomalyModel:
    """Unsupervised Isolation Forest anomaly detector."""

    def __init__(self, contamination: float = 0.02, n_estimators: int = 150, random_state: int = 42):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            max_samples="auto",
            random_state=self.random_state,
            n_jobs=-1
        )
        self.score_min = -0.5
        self.score_max = 0.5
        self.is_fitted = False

    def fit(self, X: pd.DataFrame):
        """Fits the Isolation Forest on feature matrix."""
        logger.info(f"Training Isolation Forest with {len(X):,} samples...")
        self.model.fit(X)
        self.is_fitted = True

        # Calibrate score min and max for robust 0-100 normalization
        raw_scores = self.model.decision_function(X)
        self.score_min = float(np.percentile(raw_scores, 0.5))
        self.score_max = float(np.percentile(raw_scores, 99.5))
        logger.info(f"Isolation Forest calibrated: score_range=[{self.score_min:.4f}, {self.score_max:.4f}]")
        return self

    def score_sample(self, X_sample: pd.DataFrame) -> float:
        """
        Computes normalized 0-100 anomaly risk score.
        Lower decision_function means more abnormal/isolated.
        Normalized: 0 = completely normal, 100 = extreme outlier anomaly.
        """
        if not self.is_fitted:
            return 0.0

        raw_score = float(self.model.decision_function(X_sample)[0])
        # Decision function is positive for inliers, negative for outliers
        # Map: raw <= score_min -> 100.0, raw >= score_max -> 0.0
        clipped = np.clip(raw_score, self.score_min, self.score_max)
        if self.score_max > self.score_min:
            normalized = (self.score_max - clipped) / (self.score_max - self.score_min)
        else:
            normalized = 0.0
        return round(float(normalized * 100.0), 2)

    def predict_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """Inference for a single transaction dictionary."""
        X_df = extract_features_from_dict(tx)
        anomaly_score = self.score_sample(X_df)
        is_anomaly = anomaly_score >= 50.0
        return {
            "anomaly_score": anomaly_score,
            "is_anomaly": is_anomaly,
            "model_type": "IsolationForest"
        }

    def save(self, path: Optional[str] = None):
        """Serializes model artifact and calibration parameters."""
        path = path or settings.IFOREST_MODEL_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            "model": self.model,
            "score_min": self.score_min,
            "score_max": self.score_max,
            "is_fitted": self.is_fitted,
            "contamination": self.contamination
        }, path)
        logger.info(f"Isolation Forest model saved to: {path}")

    @classmethod
    def load(cls, path: Optional[str] = None) -> "IsolationForestAnomalyModel":
        """Deserializes model artifact."""
        path = path or settings.IFOREST_MODEL_PATH
        if not os.path.exists(path):
            raise FileNotFoundError(f"Isolation Forest model file not found at {path}")

        data = joblib.load(path)
        instance = cls()
        instance.model = data["model"]
        instance.score_min = data.get("score_min", -0.5)
        instance.score_max = data.get("score_max", 0.5)
        instance.is_fitted = data.get("is_fitted", True)
        instance.contamination = data.get("contamination", 0.02)
        return instance


if __name__ == "__main__":
    from scripts.generate_sample_data import generate_paysim_sample
    data_path = settings.DATASET_PATH
    if not os.path.exists(data_path):
        generate_paysim_sample(num_records=20000, output_path=data_path)

    df = pd.read_csv(data_path)
    X = extract_features_from_dataframe(df)

    iforest = IsolationForestAnomalyModel()
    iforest.fit(X)
    iforest.save()
    print("Isolation Forest trained and saved successfully.")
