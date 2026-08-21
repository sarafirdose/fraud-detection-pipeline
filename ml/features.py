"""
Feature Engineering for PaySim Financial Fraud Detection

Extracts behavioral, balance discrepancy, and domain-specific features
from raw transaction data. Both training and real-time streaming pipelines
use this identical feature extractor.
"""

import re
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Union


FEATURE_COLUMNS = [
    "amount",
    "log_amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
    "errorBalanceOrig",
    "errorBalanceDest",
    "origBalanceDrainRatio",
    "destBalanceChangeRatio",
    "is_merchant_dest",
    "is_transfer_or_cashout",
    "hour_of_day",
    "type_CASH_IN",
    "type_CASH_OUT",
    "type_DEBIT",
    "type_PAYMENT",
    "type_TRANSFER"
]

ALL_TRANSACTION_TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]


def mask_account_id(account_id: str) -> str:
    """
    Mask raw account ID for security and compliance (e.g. C1234567890 -> C1***7890).
    Never exposes raw financial account numbers.
    """
    if not account_id or not isinstance(account_id, str):
        return "UNKNOWN"
    acc = account_id.strip()
    if len(acc) <= 5:
        return acc[:1] + "***"
    return f"{acc[:2]}***{acc[-4:]}"


def extract_features_from_dict(tx: Dict[str, Any]) -> pd.DataFrame:
    """
    Extracts features from a single raw transaction dictionary for real-time inference.
    """
    amount = float(tx.get("amount", 0.0))
    old_orig = float(tx.get("oldbalanceOrg", 0.0))
    new_orig = float(tx.get("newbalanceOrig", 0.0))
    old_dest = float(tx.get("oldbalanceDest", 0.0))
    new_dest = float(tx.get("newbalanceDest", 0.0))
    tx_type = str(tx.get("type", "PAYMENT")).upper()
    name_dest = str(tx.get("nameDest", ""))
    step = int(tx.get("step", 1))

    log_amount = np.log1p(max(0.0, amount))
    error_balance_orig = new_orig + amount - old_orig
    error_balance_dest = old_dest + amount - new_dest
    orig_balance_drain_ratio = amount / (old_orig + 1.0)
    dest_balance_change_ratio = abs(new_dest - old_dest) / (amount + 1.0)
    is_merchant_dest = 1.0 if name_dest.startswith("M") else 0.0
    is_transfer_or_cashout = 1.0 if tx_type in ["TRANSFER", "CASH_OUT"] else 0.0
    hour_of_day = float(step % 24)

    row = {
        "amount": amount,
        "log_amount": log_amount,
        "oldbalanceOrg": old_orig,
        "newbalanceOrig": new_orig,
        "oldbalanceDest": old_dest,
        "newbalanceDest": new_dest,
        "errorBalanceOrig": error_balance_orig,
        "errorBalanceDest": error_balance_dest,
        "origBalanceDrainRatio": orig_balance_drain_ratio,
        "destBalanceChangeRatio": dest_balance_change_ratio,
        "is_merchant_dest": is_merchant_dest,
        "is_transfer_or_cashout": is_transfer_or_cashout,
        "hour_of_day": hour_of_day,
    }

    # One-hot encode types
    for t in ALL_TRANSACTION_TYPES:
        row[f"type_{t}"] = 1.0 if tx_type == t else 0.0

    df = pd.DataFrame([row], columns=FEATURE_COLUMNS)
    return df


def extract_features_from_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts features from a pandas DataFrame (used during batch model training).
    """
    df = df.copy()

    # Core numerical fields
    amount = df["amount"].astype(float)
    old_orig = df["oldbalanceOrg"].astype(float)
    new_orig = df["newbalanceOrig"].astype(float)
    old_dest = df["oldbalanceDest"].astype(float)
    new_dest = df["newbalanceDest"].astype(float)
    step = df["step"].astype(int)

    features_df = pd.DataFrame(index=df.index)
    features_df["amount"] = amount
    features_df["log_amount"] = np.log1p(np.maximum(0.0, amount))
    features_df["oldbalanceOrg"] = old_orig
    features_df["newbalanceOrig"] = new_orig
    features_df["oldbalanceDest"] = old_dest
    features_df["newbalanceDest"] = new_dest

    # Discrepancy & Behavioral features
    features_df["errorBalanceOrig"] = new_orig + amount - old_orig
    features_df["errorBalanceDest"] = old_dest + amount - new_dest
    features_df["origBalanceDrainRatio"] = amount / (old_orig + 1.0)
    features_df["destBalanceChangeRatio"] = np.abs(new_dest - old_dest) / (amount + 1.0)

    # Identifiers & timing
    name_dest = df["nameDest"].astype(str)
    features_df["is_merchant_dest"] = name_dest.str.startswith("M").astype(float)
    features_df["is_transfer_or_cashout"] = df["type"].isin(["TRANSFER", "CASH_OUT"]).astype(float)
    features_df["hour_of_day"] = (step % 24).astype(float)

    # One-hot encoding
    for t in ALL_TRANSACTION_TYPES:
        features_df[f"type_{t}"] = (df["type"] == t).astype(float)

    return features_df[FEATURE_COLUMNS]


def identify_risk_factors(tx: Dict[str, Any], risk_score: float) -> List[str]:
    """
    Identifies human-interpretable risk factors explaining why a transaction
    was classified as suspicious or high risk.
    """
    factors = []
    amount = float(tx.get("amount", 0.0))
    old_orig = float(tx.get("oldbalanceOrg", 0.0))
    new_orig = float(tx.get("newbalanceOrig", 0.0))
    old_dest = float(tx.get("oldbalanceDest", 0.0))
    new_dest = float(tx.get("newbalanceDest", 0.0))
    tx_type = str(tx.get("type", "")).upper()

    # Rule/Feature Explanations
    if tx_type in ["TRANSFER", "CASH_OUT"]:
        factors.append(f"High-risk transaction type: {tx_type}")

    if amount >= 200000.0:
        factors.append(f"Unusually large transaction amount (${amount:,.2f}) exceeding threshold")

    if old_orig > 0 and new_orig == 0.0 and amount >= (old_orig * 0.90):
        factors.append("Complete origin account balance drain (funds reduced to $0.00)")

    if old_orig == 0.0 and amount > 1000.0:
        factors.append(f"Zero initial origin balance before transfer of ${amount:,.2f}")

    if tx_type == "TRANSFER" and old_dest == 0.0 and new_dest == 0.0:
        factors.append("Destination account balance remained zero after receiving funds (immediate sweep anomaly)")

    error_orig = abs(new_orig + amount - old_orig)
    if error_orig > 100.0:
        factors.append(f"Origin balance ledger discrepancy detected (delta: ${error_orig:,.2f})")

    if risk_score >= 80.0:
        factors.append("Machine learning model detected critical anomalous pattern signature")

    if not factors:
        if risk_score >= 50.0:
            factors.append("Elevated multivariate risk score across transaction features")
        else:
            factors.append("Standard transaction pattern within normal bounds")

    return factors
