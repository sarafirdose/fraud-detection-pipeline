"""
Automated Tests for Stateful User Behavioral Profiling
"""

import time
import pytest
from stream.behavior_profile import AccountProfile, BehavioralProfilerService


def test_account_profile_rolling_metrics():
    profile = AccountProfile("C123456789")
    t0 = time.time()

    # 1. First transaction ($50)
    res1 = profile.add_transaction(amount=50.0, current_time=t0)
    assert res1["velocity_1h"] == 1
    assert res1["velocity_24h"] == 1
    assert res1["volume_1h"] == 50.0
    assert res1["avg_amount"] == 50.0
    assert res1["amount_deviation_ratio"] == 1.0

    # 2. Second transaction after 5 mins ($50)
    res2 = profile.add_transaction(amount=50.0, current_time=t0 + 300)
    assert res2["velocity_1h"] == 2
    assert res2["volume_1h"] == 100.0
    assert res2["avg_amount"] == 50.0

    # 3. Third transaction: Massive surge ($5,000)
    res3 = profile.add_transaction(amount=5000.0, current_time=t0 + 600)
    assert res3["velocity_1h"] == 3
    assert res3["amount_deviation_ratio"] >= 50.0
    # Behavioral risk should spike significantly
    assert res3["behavior_risk_score"] >= 30.0


def test_behavioral_profiler_service_lru_and_latency():
    profiler = BehavioralProfilerService(max_accounts=5)
    
    # Process 10 different accounts to test bounded LRU eviction
    for i in range(10):
        tx = {
            "nameOrig": f"C_USER_{i}",
            "amount": 100.0 + i,
            "emitted_at": time.time()
        }
        res = profiler.process_transaction(tx)
        assert "velocity_1h" in res
        assert "behavior_latency_ms" in res
        # Latency requirement: sub-20ms
        assert res["behavior_latency_ms"] < 20.0

    # Total active accounts in memory must strictly be bounded <= max_accounts
    assert profiler.active_account_count() <= 5
