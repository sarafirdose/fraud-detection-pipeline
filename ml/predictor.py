"""
Real-Time Fraud Predictor & Scoring Engine (Unified Multi-Model Wrapper)

Provides thread-safe, low-latency inference for streaming transactions,
risk scoring (0-100), risk tier classification, explainability factors,
behavioral profiling, and multi-model selection.
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Any, Optional, List
import joblib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import settings
from ml.unified_scorer import unified_scorer, UnifiedFraudScorer

logger = logging.getLogger("fraud_predictor")


class FraudPredictor:
    """Real-time scoring engine wrapping the unified multi-model scorer."""

    def __init__(self, model_path: Optional[str] = None, metadata_path: Optional[str] = None):
        self.model_path = model_path or settings.MODEL_PATH
        self.metadata_path = metadata_path or settings.MODEL_METADATA_PATH
        self.metadata = {}
        self.scorer = unified_scorer
        self._load_metadata()

    @property
    def model(self):
        return self.scorer.xgb_model or self.scorer.rf_model

    def _load_metadata(self):
        """Loads trained metadata if available."""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata from {self.metadata_path}: {e}")

    def predict(self, raw_tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scores a single raw transaction using the unified multi-model engine.
        Returns enriched transaction payload with risk score, prediction, latency, and explainability.
        """
        return self.scorer.score_transaction(raw_tx)

    def set_model_mode(self, mode: str):
        """Switches active model mode (SUPERVISED_XGBOOST, SUPERVISED_RANDOM_FOREST, UNSUPERVISED_ISOLATION_FOREST, UNSUPERVISED_AUTOENCODER, ENSEMBLE)."""
        self.scorer.set_mode(mode)


# Global Singleton instance
predictor = FraudPredictor()
