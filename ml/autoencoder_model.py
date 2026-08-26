"""
Neural Autoencoder Anomaly Detection Model

Unsupervised deep reconstruction anomaly detector.
Trains on non-fraudulent (normal) transactions to learn the normal manifold.
Anomalous transactions produce high reconstruction error (MSE),
which is normalized into a 0-100 anomaly score.
"""

import os
import sys
import logging
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import settings
from ml.features import extract_features_from_dict, extract_features_from_dataframe, FEATURE_COLUMNS

logger = logging.getLogger("autoencoder_model")


class AutoencoderAnomalyModel:
    """Neural Autoencoder for reconstruction-based anomaly detection."""

    def __init__(self, bottleneck_dim: int = 6, max_iter: int = 60, random_state: int = 42):
        self.bottleneck_dim = bottleneck_dim
        self.max_iter = max_iter
        self.random_state = random_state
        self.scaler = StandardScaler()
        # Symmetric bottleneck encoder-decoder architecture: e.g. 18 -> 12 -> 6 -> 12 -> 18
        self.model = MLPRegressor(
            hidden_layer_sizes=(12, self.bottleneck_dim, 12),
            activation="relu",
            solver="adam",
            max_iter=self.max_iter,
            random_state=self.random_state,
            early_stopping=True,
            validation_fraction=0.1
        )
        self.err_mean = 0.0
        self.err_std = 1.0
        self.err_max = 5.0
        self.is_fitted = False

    def fit(self, X_normal: pd.DataFrame):
        """
        Trains the autoencoder on normal (non-fraud) transaction features.
        """
        logger.info(f"Training Autoencoder on {len(X_normal):,} normal transactions...")
        X_scaled = self.scaler.fit_transform(X_normal)
        
        # Autoencoder learns to reconstruct its own input: X -> X
        self.model.fit(X_scaled, X_scaled)
        self.is_fitted = True

        # Calibrate baseline reconstruction errors
        reconstructed = self.model.predict(X_scaled)
        mse_errors = np.mean(np.square(X_scaled - reconstructed), axis=1)

        self.err_mean = float(np.mean(mse_errors))
        self.err_std = float(np.std(mse_errors)) + 1e-6
        self.err_max = float(np.percentile(mse_errors, 99.5))
        logger.info(f"Autoencoder calibrated: err_mean={self.err_mean:.4f}, err_max={self.err_max:.4f}")
        return self

    def score_sample(self, X_sample: pd.DataFrame) -> float:
        """
        Calculates reconstruction MSE and maps to normalized 0-100 anomaly score.
        """
        if not self.is_fitted:
            return 0.0

        X_scaled = self.scaler.transform(X_sample)
        reconstructed = self.model.predict(X_scaled)
        mse = float(np.mean(np.square(X_scaled - reconstructed)))

        # Sigmoid-like / linear scaling relative to normal calibration
        if mse <= self.err_mean:
            normalized = (mse / max(1e-4, self.err_mean)) * 25.0
        else:
            excess = (mse - self.err_mean) / max(1e-4, (self.err_max - self.err_mean))
            normalized = 25.0 + min(75.0, excess * 75.0)

        return round(float(np.clip(normalized, 0.0, 100.0)), 2)

    def predict_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """Inference for single transaction."""
        X_df = extract_features_from_dict(tx)
        score = self.score_sample(X_df)
        return {
            "anomaly_score": score,
            "is_anomaly": score >= 50.0,
            "model_type": "Autoencoder"
        }

    def save(self, path: Optional[str] = None):
        """Serializes autoencoder artifact."""
        path = path or settings.AUTOENCODER_MODEL_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            "model": self.model,
            "scaler": self.scaler,
            "err_mean": self.err_mean,
            "err_std": self.err_std,
            "err_max": self.err_max,
            "is_fitted": self.is_fitted
        }, path)
        logger.info(f"Autoencoder model saved to: {path}")

    @classmethod
    def load(cls, path: Optional[str] = None) -> "AutoencoderAnomalyModel":
        """Deserializes autoencoder artifact."""
        path = path or settings.AUTOENCODER_MODEL_PATH
        if not os.path.exists(path):
            raise FileNotFoundError(f"Autoencoder model file not found at {path}")

        data = joblib.load(path)
        instance = cls()
        instance.model = data["model"]
        instance.scaler = data["scaler"]
        instance.err_mean = data.get("err_mean", 0.0)
        instance.err_std = data.get("err_std", 1.0)
        instance.err_max = data.get("err_max", 5.0)
        instance.is_fitted = data.get("is_fitted", True)
        return instance


if __name__ == "__main__":
    from scripts.generate_sample_data import generate_paysim_sample
    data_path = settings.DATASET_PATH
    if not os.path.exists(data_path):
        generate_paysim_sample(num_records=20000, output_path=data_path)

    df = pd.read_csv(data_path)
    # Train only on non-fraud transactions
    df_normal = df[df["isFraud"] == 0]
    X_normal = extract_features_from_dataframe(df_normal)

    ae = AutoencoderAnomalyModel()
    ae.fit(X_normal)
    ae.save()
    print("Autoencoder trained and saved successfully.")
