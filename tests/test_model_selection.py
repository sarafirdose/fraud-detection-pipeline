"""
Automated Tests for Model Mode Switching & Ensemble Scoring
"""

import pytest
from ml.unified_scorer import UnifiedFraudScorer


def test_model_mode_switching():
    scorer = UnifiedFraudScorer()

    # 1. Test Supervised XGBoost
    scorer.set_mode("SUPERVISED_XGBOOST")
    assert scorer.mode == "SUPERVISED_XGBOOST"

    # 2. Test Supervised Random Forest
    scorer.set_mode("SUPERVISED_RANDOM_FOREST")
    assert scorer.mode == "SUPERVISED_RANDOM_FOREST"

    # 3. Test Unsupervised Isolation Forest
    scorer.set_mode("UNSUPERVISED_ISOLATION_FOREST")
    assert scorer.mode == "UNSUPERVISED_ISOLATION_FOREST"

    # 4. Test Unsupervised Autoencoder
    scorer.set_mode("UNSUPERVISED_AUTOENCODER")
    assert scorer.mode == "UNSUPERVISED_AUTOENCODER"

    # 5. Test Ensemble
    scorer.set_mode("ENSEMBLE")
    assert scorer.mode == "ENSEMBLE"

    # 6. Invalid mode should raise ValueError
    with pytest.raises(ValueError):
        scorer.set_mode("INVALID_MODE_NAME")


def test_ensemble_scoring_calculation():
    scorer = UnifiedFraudScorer(mode="ENSEMBLE")
    tx = {
        "step": 45,
        "type": "CASH_OUT",
        "amount": 250000.0,
        "nameOrig": "C555444333",
        "oldbalanceOrg": 250000.0,
        "newbalanceOrig": 0.0,
        "nameDest": "C999111222",
        "oldbalanceDest": 50000.0,
        "newbalanceDest": 300000.0
    }
    res = scorer.score_transaction(tx)
    assert res["active_model_mode"] == "ENSEMBLE"
    assert "Multi-Model Ensemble" in res["model_used"]
    assert 0.0 <= res["final_risk_score"] <= 100.0
