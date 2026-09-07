"""
Unit tests for Machine Learning Model and Scoring Engine
"""

import pytest
from ml.predictor import FraudPredictor, predictor


def test_predictor_loaded():
    assert predictor.model is not None
    assert predictor.metadata is not None
    assert "metrics" in predictor.metadata


def test_predict_normal_payment():
    normal_tx = {
        "step": 12,
        "type": "PAYMENT",
        "amount": 45.50,
        "nameOrig": "C1928374650",
        "oldbalanceOrg": 500.0,
        "newbalanceOrig": 454.50,
        "nameDest": "M9876543210",
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0
    }

    res = predictor.predict(normal_tx)
    assert res["is_fraud"] is False
    assert res["risk_level"] in ["LOW", "MEDIUM"]
    assert res["risk_score"] < 50.0
    assert "nameOrigMasked" in res
    assert "processing_latency_ms" in res
    assert res["nameOrigMasked"] == "C1***4650"
    assert res["nameDestMasked"] == "M9***3210"


def test_predict_fraudulent_transfer():
    fraud_tx = {
        "step": 33,
        "type": "TRANSFER",
        "amount": 850000.0,
        "nameOrig": "C9988776655",
        "oldbalanceOrg": 850000.0,
        "newbalanceOrig": 0.0,
        "nameDest": "C1122334455",
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0
    }

    res = predictor.predict(fraud_tx)
    assert res["is_fraud"] is True
    assert res["risk_level"] in ["HIGH", "CRITICAL"]
    assert res["risk_score"] >= 70.0
    assert len(res["risk_factors"]) > 0
