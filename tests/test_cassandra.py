"""
Automated Tests for Cassandra Storage & Graceful Fallback
"""

import pytest
from storage.cassandra_client import CassandraClient


def test_cassandra_graceful_offline_fallback():
    client = CassandraClient()
    # When Cassandra is disabled / offline, connect() should return False without crashing
    res = client.connect()
    assert res is False
    assert client.is_connected is False

    # Insert calls should return False gracefully without raising exceptions
    tx_ok = client.insert_transaction({"nameOrig": "C123", "amount": 100.0})
    assert tx_ok is False

    alt_ok = client.insert_alert({"alert_id": "ALT-1", "amount": 100.0})
    assert alt_ok is False
