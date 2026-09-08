"""
Automated Tests for Unified Fraud Risk Scorer & Explainability Engine
"""

import pytest
from ml.unified_scorer import UnifiedFraudScorer


def test_unified_risk_score_structure():
    scorer = UnifiedFraudScorer()
    
    tx = {
        "step": 15,
        "type": "PAYMENT",
        "amount": 75.0,
        "nameOrig": "C1000000001",
        "oldbalanceOrg": 500.0,
        "newbalanceOrig": 425.0,
        "nameDest": "M2000000002",
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0
    }

    res = scorer.score_transaction(tx)
    
    assert "fraud_probability" in res
    assert "anomaly_score" in res
    assert "behavioral_risk" in res
    assert "final_risk_score" in res
    assert "risk_level" in res
    assert "model_used" in res
    assert "explanation" in res
    assert isinstance(res["explanation"], list)
    assert len(res["explanation"]) >= 1
    assert 0.0 <= res["final_risk_score"] <= 100.0


def test_unified_risk_score_critical_fraud():
    scorer = UnifiedFraudScorer()
    
    fraud_tx = {
        "step": 80,
        "type": "TRANSFER",
        "amount": 800000.0,
        "nameOrig": "C999888777",
        "oldbalanceOrg": 800000.0,
        "newbalanceOrig": 0.0,
        "nameDest": "C111222333",
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0
    }

    res = scorer.score_transaction(fraud_tx)
    assert res["is_fraud"] is True
    assert res["risk_level"] in ["HIGH", "CRITICAL"]
    assert res["final_risk_score"] >= 70.0
    # Must contain explainability factors
    assert any("drain" in exp.lower() or "transfer" in exp.lower() or "probability" in exp.lower() for exp in res["explanation"])
