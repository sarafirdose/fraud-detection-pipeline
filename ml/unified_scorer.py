"""
Unified Fraud Risk Scoring & Multi-Model Inference Engine

Combines:
- Supervised ML Predictions (XGBoost / Random Forest)
- Unsupervised Anomaly Scores (Isolation Forest / Neural Autoencoder)
- Real-Time Stateful Behavioral Profile (Velocity, Amount Surge, Z-score)
- Domain Heuristics & Ledger Discrepancies

Produces a unified risk score (0-100), risk tier, and explainability factors.
"""

import os
import sys
import time
import logging
from typing import Dict, Any, List, Optional
import joblib
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import settings
from ml.features import extract_features_from_dict, identify_risk_factors, mask_account_id
from ml.isolation_forest_model import IsolationForestAnomalyModel
from ml.autoencoder_model import AutoencoderAnomalyModel
from stream.behavior_profile import behavior_profiler

logger = logging.getLogger("unified_scorer")


class UnifiedFraudScorer:
    """Unified multi-model and behavioral fraud evaluation engine."""

    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or settings.ACTIVE_MODEL_MODE
        self.xgb_model = None
        self.rf_model = None
        self.iforest_model: Optional[IsolationForestAnomalyModel] = None
        self.autoencoder_model: Optional[AutoencoderAnomalyModel] = None
        self.load_models()

    def load_models(self):
        """Loads all available model artifacts with fallback checks."""
        # 1. XGBoost
        if os.path.exists(settings.MODEL_PATH):
            try:
                self.xgb_model = joblib.load(settings.MODEL_PATH)
            except Exception as e:
                logger.warning(f"Failed loading XGBoost model: {e}")

        # 2. Random Forest
        if os.path.exists(settings.RF_MODEL_PATH):
            try:
                self.rf_model = joblib.load(settings.RF_MODEL_PATH)
            except Exception as e:
                logger.warning(f"Failed loading Random Forest model: {e}")

        # 3. Isolation Forest
        if os.path.exists(settings.IFOREST_MODEL_PATH):
            try:
                self.iforest_model = IsolationForestAnomalyModel.load(settings.IFOREST_MODEL_PATH)
            except Exception as e:
                logger.warning(f"Failed loading Isolation Forest model: {e}")

        # 4. Autoencoder
        if os.path.exists(settings.AUTOENCODER_MODEL_PATH):
            try:
                self.autoencoder_model = AutoencoderAnomalyModel.load(settings.AUTOENCODER_MODEL_PATH)
            except Exception as e:
                logger.warning(f"Failed loading Autoencoder model: {e}")

    def set_mode(self, new_mode: str):
        """Switches active scoring mode dynamically."""
        valid_modes = [
            "SUPERVISED_XGBOOST",
            "SUPERVISED_RANDOM_FOREST",
            "UNSUPERVISED_ISOLATION_FOREST",
            "UNSUPERVISED_AUTOENCODER",
            "ENSEMBLE"
        ]
        if new_mode in valid_modes:
            self.mode = new_mode
            logger.info(f"Scoring mode updated to: {self.mode}")
        else:
            raise ValueError(f"Invalid model mode '{new_mode}'. Valid options: {valid_modes}")

    def score_transaction(self, raw_tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates unified fraud risk score across ML, anomaly, and behavioral layers.
        """
        start_time = time.perf_counter()

        # 1. Feature Extraction
        X_df = extract_features_from_dict(raw_tx)
        feature_time = time.perf_counter()

        # 2. Stateful User Behavioral Profiling
        behavior_stats = behavior_profiler.process_transaction(raw_tx)
        behavior_risk = behavior_stats.get("behavior_risk_score", 0.0)

        # 3. Individual Model Inferences
        ml_start = time.perf_counter()
        
        # Supervised Probabilities
        xgb_prob = 0.0
        if self.xgb_model:
            try:
                xgb_prob = float(self.xgb_model.predict_proba(X_df)[0, 1])
            except Exception:
                pass

        rf_prob = 0.0
        if self.rf_model:
            try:
                rf_prob = float(self.rf_model.predict_proba(X_df)[0, 1])
            except Exception:
                pass

        # Unsupervised Anomaly Scores (0 - 100)
        iforest_score = 0.0
        if self.iforest_model:
            try:
                iforest_score = float(self.iforest_model.score_sample(X_df))
            except Exception:
                pass

        ae_score = 0.0
        if self.autoencoder_model:
            try:
                ae_score = float(self.autoencoder_model.score_sample(X_df))
            except Exception:
                pass

        ml_latency_ms = round((time.perf_counter() - ml_start) * 1000.0, 3)

        # 4. Mode-Based Scoring Selection
        primary_prob = xgb_prob
        primary_anomaly = iforest_score

        if self.mode == "SUPERVISED_XGBOOST":
            model_used_name = "XGBoost Classifier (Supervised)"
            final_risk = (xgb_prob * 100.0) * (1.0 - settings.BEHAVIORAL_RISK_WEIGHT) + (behavior_risk * settings.BEHAVIORAL_RISK_WEIGHT)
            primary_prob = xgb_prob

        elif self.mode == "SUPERVISED_RANDOM_FOREST":
            model_used_name = "Random Forest Classifier (Supervised)"
            final_risk = (rf_prob * 100.0) * (1.0 - settings.BEHAVIORAL_RISK_WEIGHT) + (behavior_risk * settings.BEHAVIORAL_RISK_WEIGHT)
            primary_prob = rf_prob

        elif self.mode == "UNSUPERVISED_ISOLATION_FOREST":
            model_used_name = "Isolation Forest (Unsupervised Anomaly)"
            final_risk = (iforest_score) * (1.0 - settings.BEHAVIORAL_RISK_WEIGHT) + (behavior_risk * settings.BEHAVIORAL_RISK_WEIGHT)
            primary_anomaly = iforest_score

        elif self.mode == "UNSUPERVISED_AUTOENCODER":
            model_used_name = "Neural Autoencoder (Unsupervised Reconstruction)"
            final_risk = (ae_score) * (1.0 - settings.BEHAVIORAL_RISK_WEIGHT) + (behavior_risk * settings.BEHAVIORAL_RISK_WEIGHT)
            primary_anomaly = ae_score

        else:  # ENSEMBLE mode
            model_used_name = "Multi-Model Ensemble (Supervised + Unsupervised + Behavioral)"
            sup_score = (xgb_prob * 100.0) if self.xgb_model else (rf_prob * 100.0)
            anom_score = (iforest_score * 0.5 + ae_score * 0.5)
            
            w_sup = settings.ENSEMBLE_SUPERVISED_WEIGHT
            w_anom = settings.ENSEMBLE_ANOMALY_WEIGHT
            w_beh = settings.BEHAVIORAL_RISK_WEIGHT

            # Normalized weights
            total_w = w_sup + w_anom + w_beh
            final_risk = (sup_score * w_sup + anom_score * w_anom + behavior_risk * w_beh) / max(0.1, total_w)
            primary_prob = xgb_prob
            primary_anomaly = round(anom_score, 2)

        final_risk = round(float(np.clip(final_risk, 0.0, 100.0)), 2)

        # 5. Risk Tier Determination
        if final_risk >= (settings.CRITICAL_RISK_THRESHOLD * 100.0):
            risk_level = "CRITICAL"
        elif final_risk >= (settings.HIGH_RISK_THRESHOLD * 100.0):
            risk_level = "HIGH"
        elif final_risk >= (settings.FRAUD_SCORE_THRESHOLD * 100.0):
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        is_fraud = bool(final_risk >= (settings.FRAUD_SCORE_THRESHOLD * 100.0))

        # 6. Human-Readable Explanations
        explanations = []

        # Behavioral explanations
        amt_dev = behavior_stats.get("amount_deviation_ratio", 1.0)
        if amt_dev >= 3.0:
            explanations.append(f"Transaction amount is {amt_dev:.1f}x above account historical average.")
        
        v1h = behavior_stats.get("velocity_1h", 1)
        if v1h >= 5:
            explanations.append(f"Account velocity increased significantly ({v1h} transactions in the last hour).")

        # ML explanations
        if primary_prob >= 0.70:
            explanations.append(f"Supervised model assigned high fraud probability ({(primary_prob*100):.1f}%).")
        if primary_anomaly >= 70.0:
            explanations.append(f"Unsupervised model detected anomalous behavior ({primary_anomaly:.1f}% anomaly score).")

        # Domain Heuristics (Balance drain / transfer pattern)
        heuristic_factors = identify_risk_factors(raw_tx, final_risk)
        for hf in heuristic_factors:
            if hf not in explanations and not hf.startswith("Standard"):
                explanations.append(hf)

        if not explanations:
            explanations.append("Standard transaction pattern within historical and statistical bounds.")

        total_latency_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        result = {
            **raw_tx,
            "nameOrigMasked": mask_account_id(str(raw_tx.get("nameOrig", ""))),
            "nameDestMasked": mask_account_id(str(raw_tx.get("nameDest", ""))),
            "fraud_probability": round(primary_prob, 4),
            "anomaly_score": round(primary_anomaly, 2),
            "behavioral_risk": round(behavior_risk, 2),
            "final_risk_score": final_risk,
            "risk_score": final_risk,  # Backward compatibility
            "risk_level": risk_level,
            "is_fraud": is_fraud,
            "model_used": model_used_name,
            "active_model_mode": self.mode,
            "model_scores": {
                "xgboost_prob": round(xgb_prob, 4),
                "rf_prob": round(rf_prob, 4),
                "iforest_anomaly": round(iforest_score, 2),
                "autoencoder_anomaly": round(ae_score, 2),
                "behavioral_risk": round(behavior_risk, 2)
            },
            "behavioral_profile": behavior_stats,
            "explanation": explanations,
            "risk_factors": explanations,  # Backward compatibility
            "processing_latency_ms": total_latency_ms,
            "ml_latency_ms": ml_latency_ms,
            "evaluated_at": time.time()
        }

        return result


# Global Unified Scorer Singleton
unified_scorer = UnifiedFraudScorer()
