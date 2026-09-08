"""
End-to-End Pipeline simulation tests
"""

import pytest
import time
from ml.predictor import predictor
from streaming.stream_processor import StreamProcessor


def test_pipeline_message_processing_mock_db():
    processor = StreamProcessor()
    # Test message processing without requiring active MongoDB or Kafka broker
    processor.db = None
    processor.kafka_producer = None

    sample_tx = {
        "transaction_id": "TEST-TX-001",
        "step": 1,
        "type": "CASH_OUT",
        "amount": 900000.0,
        "nameOrig": "C1234567890",
        "oldbalanceOrg": 900000.0,
        "newbalanceOrig": 0.0,
        "nameDest": "C0987654321",
        "oldbalanceDest": 1000.0,
        "newbalanceDest": 901000.0,
        "emitted_at": time.time(),
        "is_demo": True
    }

    result = processor.process_message(sample_tx)

    assert result["transaction_id"] == "TEST-TX-001"
    assert result["is_fraud"] is True
    assert result["risk_level"] in ["HIGH", "CRITICAL"]
    assert result["risk_score"] >= 70.0
    assert result["nameOrigMasked"] == "C1***7890"
    assert result["nameDestMasked"] == "C0***4321"
    assert "end_to_end_latency_ms" in result
    assert result["end_to_end_latency_ms"] >= 0.0
