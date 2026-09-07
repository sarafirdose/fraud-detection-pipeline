"""
Unit tests for Feature Engineering & Explainability
"""

import pytest
import pandas as pd
import numpy as np
from ml.features import (
    mask_account_id,
    extract_features_from_dict,
    extract_features_from_dataframe,
    identify_risk_factors,
    FEATURE_COLUMNS
)


def test_mask_account_id():
    assert mask_account_id("C1234567890") == "C1***7890"
    assert mask_account_id("M9876543210") == "M9***3210"
    assert mask_account_id("C123") == "C***"
    assert mask_account_id("") == "UNKNOWN"
    assert mask_account_id(None) == "UNKNOWN"


def test_extract_features_from_dict():
    raw_tx = {
        "step": 14,
        "type": "TRANSFER",
        "amount": 50000.0,
        "nameOrig": "C1234567890",
        "oldbalanceOrg": 50000.0,
        "newbalanceOrig": 0.0,
        "nameDest": "C9876543210",
        "oldbalanceDest": 0.0,
        "newbalanceDest": 50000.0
    }

    df_feat = extract_features_from_dict(raw_tx)
    assert isinstance(df_feat, pd.DataFrame)
    assert len(df_feat) == 1
    assert list(df_feat.columns) == FEATURE_COLUMNS

    # Check calculated discrepancy features
    assert df_feat["type_TRANSFER"].iloc[0] == 1.0
    assert df_feat["type_PAYMENT"].iloc[0] == 0.0
    assert df_feat["is_transfer_or_cashout"].iloc[0] == 1.0
    assert df_feat["hour_of_day"].iloc[0] == 14.0
    assert df_feat["errorBalanceOrig"].iloc[0] == 0.0
    assert df_feat["origBalanceDrainRatio"].iloc[0] > 0.99


def test_extract_features_from_dataframe():
    data = {
        "step": [1, 2],
        "type": ["PAYMENT", "CASH_OUT"],
        "amount": [100.0, 5000.0],
        "nameOrig": ["C111", "C222"],
        "oldbalanceOrg": [500.0, 5000.0],
        "newbalanceOrig": [400.0, 0.0],
        "nameDest": ["M999", "C888"],
        "oldbalanceDest": [0.0, 100.0],
        "newbalanceDest": [0.0, 5100.0],
        "isFraud": [0, 1]
    }
    df = pd.DataFrame(data)
    feats = extract_features_from_dataframe(df)

    assert len(feats) == 2
    assert list(feats.columns) == FEATURE_COLUMNS
    assert feats["is_merchant_dest"].iloc[0] == 1.0
    assert feats["is_merchant_dest"].iloc[1] == 0.0
    assert feats["type_PAYMENT"].iloc[0] == 1.0
    assert feats["type_CASH_OUT"].iloc[1] == 1.0


def test_identify_risk_factors_drain():
    tx = {
        "type": "TRANSFER",
        "amount": 500000.0,
        "oldbalanceOrg": 500000.0,
        "newbalanceOrig": 0.0,
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0
    }
    factors = identify_risk_factors(tx, risk_score=95.0)
    assert any("Complete origin account balance drain" in f for f in factors)
    assert any("High-risk transaction type" in f for f in factors)
    assert any("large transaction amount" in f for f in factors)
