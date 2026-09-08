"""
Automated Tests for Prometheus Metrics Instrumentation
"""

import pytest
from monitoring.metrics import (
    record_transaction_metrics,
    generate_latest,
    TOTAL_TRANSACTIONS,
    FRAUD_ALERTS,
    NORMAL_TRANSACTIONS,
    ACTIVE_ACCOUNTS
)


def test_prometheus_metrics_recording():
    sample_tx = {
        "type": "TRANSFER",
        "amount": 500000.0,
        "is_fraud": True,
        "risk_level": "CRITICAL",
        "ml_latency_ms": 5.2,
        "behavioral_profile": {"behavior_latency_ms": 1.1}
    }

    record_transaction_metrics(sample_tx, model_mode="SUPERVISED_XGBOOST", stream_lat_s=0.01)
    ACTIVE_ACCOUNTS.set(42)

    # Scrape output format
    metrics_text = generate_latest().decode("utf-8")
    
    assert "total_transactions_processed" in metrics_text
    assert "fraud_alerts_total" in metrics_text
    assert "active_accounts" in metrics_text
    assert "ml_inference_latency_seconds" in metrics_text
