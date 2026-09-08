"""
Automated Tests for Neural Autoencoder Anomaly Detection Model
"""

import pytest
import numpy as np
import pandas as pd
from ml.features import extract_features_from_dataframe
from ml.autoencoder_model import AutoencoderAnomalyModel


@pytest.fixture
def normal_features_df():
    # 25 normal transactions
    data = {
        "step": list(range(1, 26)),
        "type": ["PAYMENT"] * 15 + ["CASH_IN"] * 10,
        "amount": [20.0 + i * 5 for i in range(25)],
        "nameOrig": [f"C{i}" for i in range(25)],
        "oldbalanceOrg": [1000.0] * 25,
        "newbalanceOrig": [980.0] * 25,
        "nameDest": [f"M{i}" for i in range(25)],
        "oldbalanceDest": [0.0] * 25,
        "newbalanceDest": [0.0] * 25,
        "isFraud": [0] * 25
    }
    df = pd.DataFrame(data)
    return extract_features_from_dataframe(df)


def test_autoencoder_fit_and_score(normal_features_df):
    ae = AutoencoderAnomalyModel(bottleneck_dim=4, max_iter=25, random_state=42)
    ae.fit(normal_features_df)
    assert ae.is_fitted is True

    # Test scoring on normal sample
    score_norm = ae.score_sample(normal_features_df.iloc[[0]])
    assert isinstance(score_norm, float)
    assert 0.0 <= score_norm <= 100.0


def test_autoencoder_anomaly_high_error(normal_features_df):
    ae = AutoencoderAnomalyModel(bottleneck_dim=4, max_iter=25, random_state=42)
    ae.fit(normal_features_df)

    # Extreme outlier transaction
    outlier_tx = {
        "step": 99,
        "type": "TRANSFER",
        "amount": 10000000.0,
        "nameOrig": "C9999",
        "oldbalanceOrg": 10000000.0,
        "newbalanceOrig": 0.0,
        "nameDest": "C1111",
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0
    }
    res = ae.predict_transaction(outlier_tx)
    assert "anomaly_score" in res
    assert res["anomaly_score"] >= 20.0
