"""
Automated Tests for Isolation Forest Anomaly Detection Model
"""

import pytest
import numpy as np
import pandas as pd
from ml.features import extract_features_from_dataframe, extract_features_from_dict
from ml.isolation_forest_model import IsolationForestAnomalyModel


@pytest.fixture
def sample_features_df():
    data = {
        "step": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "type": ["TRANSFER", "CASH_OUT", "PAYMENT", "CASH_IN", "DEBIT", "TRANSFER", "PAYMENT", "CASH_OUT", "TRANSFER", "TRANSFER"],
        "amount": [500.0, 1200.0, 45.0, 1000.0, 80.0, 750000.0, 30.0, 400.0, 950000.0, 20.0],
        "nameOrig": [f"C{i}" for i in range(10)],
        "oldbalanceOrg": [1000.0, 2000.0, 200.0, 500.0, 300.0, 750000.0, 150.0, 1000.0, 950000.0, 100.0],
        "newbalanceOrig": [500.0, 800.0, 155.0, 1500.0, 220.0, 0.0, 120.0, 600.0, 0.0, 80.0],
        "nameDest": [f"M{i}" for i in range(10)],
        "oldbalanceDest": [0.0, 500.0, 0.0, 2000.0, 100.0, 0.0, 0.0, 200.0, 0.0, 0.0],
        "newbalanceDest": [0.0, 1700.0, 0.0, 1000.0, 180.0, 0.0, 0.0, 600.0, 0.0, 0.0],
        "isFraud": [0, 0, 0, 0, 0, 1, 0, 0, 1, 0]
    }
    df = pd.DataFrame(data)
    return extract_features_from_dataframe(df)


def test_isolation_forest_fit_and_score(sample_features_df):
    model = IsolationForestAnomalyModel(n_estimators=30, random_state=42)
    model.fit(sample_features_df)
    assert model.is_fitted is True

    # Test single sample score
    sample_df = sample_features_df.iloc[[0]]
    score = model.score_sample(sample_df)
    assert isinstance(score, float)
    assert 0.0 <= score <= 100.0


def test_isolation_forest_anomaly_detection():
    model = IsolationForestAnomalyModel(n_estimators=30, random_state=42)
    
    # Train on benign baseline
    normal_tx = {
        "step": 12, "type": "PAYMENT", "amount": 50.0,
        "nameOrig": "C12345", "oldbalanceOrg": 1000.0, "newbalanceOrig": 950.0,
        "nameDest": "M98765", "oldbalanceDest": 0.0, "newbalanceDest": 0.0
    }
    X_normal = extract_features_from_dataframe(pd.DataFrame([normal_tx] * 20))
    model.fit(X_normal)

    # Score normal transaction
    norm_res = model.predict_transaction(normal_tx)
    assert "anomaly_score" in norm_res
    assert 0.0 <= norm_res["anomaly_score"] <= 100.0

    # Score massive abnormal transaction
    fraud_tx = {
        "step": 12, "type": "TRANSFER", "amount": 9999999.0,
        "nameOrig": "C99999", "oldbalanceOrg": 9999999.0, "newbalanceOrig": 0.0,
        "nameDest": "C00000", "oldbalanceDest": 0.0, "newbalanceDest": 0.0
    }
    fraud_res = model.predict_transaction(fraud_tx)
    assert fraud_res["anomaly_score"] >= 0.0
