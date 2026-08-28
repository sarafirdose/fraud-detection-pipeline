"""
Stateful User Behavioral Profiler

Maintains bounded rolling statistics per origin financial account:
- 1-hour & 24-hour transaction velocity (frequency count)
- 1-hour & 24-hour transaction volume (monetary sum)
- Historical average, standard deviation, max amount
- Ratio & z-score deviations of current transaction amount
- Calibrated behavioral risk score (0-100)

Employs LRU eviction and time-based purging to prevent unbounded memory growth.
"""

import time
import math
import logging
from collections import deque, OrderedDict
from typing import Dict, Any, List, Optional

logger = logging.getLogger("behavior_profiler")


class AccountProfile:
    """Bounded rolling transaction profile for a single user/origin account."""

    def __init__(self, account_id: str):
        self.account_id = account_id
        # Deque of (timestamp, amount) entries
        self.history: deque = deque(maxlen=300)
        self.total_count: int = 0
        self.total_amount_sum: float = 0.0
        self.total_amount_sq_sum: float = 0.0
        self.max_amount_seen: float = 0.0
        self.last_updated: float = time.time()

    def add_transaction(self, amount: float, current_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Updates profile with a new transaction and computes behavioral indicators.
        """
        now = current_time if current_time is not None else time.time()
        self.last_updated = now

        # Prune transactions older than 24 hours from the sliding deque
        cutoff_24h = now - 86400.0
        while self.history and self.history[0][0] < cutoff_24h:
            self.history.popleft()

        # Compute rolling window metrics before adding current transaction (to establish baseline)
        cutoff_1h = now - 3600.0
        v_1h = sum(1 for ts, _ in self.history if ts >= cutoff_1h)
        vol_1h = sum(amt for ts, amt in self.history if ts >= cutoff_1h)
        v_24h = len(self.history)
        vol_24h = sum(amt for _, amt in self.history)

        # Historical stats baseline
        if self.total_count > 0:
            avg_amount = self.total_amount_sum / self.total_count
            variance = max(0.0, (self.total_amount_sq_sum / self.total_count) - (avg_amount ** 2))
            std_amount = math.sqrt(variance)
        else:
            avg_amount = amount
            std_amount = 0.0

        # Deviations
        amount_ratio = (amount / max(1.0, avg_amount)) if self.total_count > 0 else 1.0
        amount_zscore = ((amount - avg_amount) / max(1.0, std_amount)) if (std_amount > 0 and self.total_count >= 3) else 0.0
        
        # Velocity risk: sudden burst of transactions in 1 hour
        expected_1h_vel = max(1.0, v_24h / 24.0)
        velocity_ratio = (v_1h + 1) / expected_1h_vel

        # Compute Behavioral Risk Score (0 - 100)
        risk_points = 0.0

        # Amount surge factor
        if amount_ratio >= 10.0:
            risk_points += 40.0
        elif amount_ratio >= 4.0:
            risk_points += 25.0
        elif amount_ratio >= 2.0:
            risk_points += 10.0

        # Z-score factor
        if amount_zscore >= 4.0:
            risk_points += 30.0
        elif amount_zscore >= 2.5:
            risk_points += 15.0

        # High velocity burst factor
        if v_1h >= 10:
            risk_points += 35.0
        elif v_1h >= 5:
            risk_points += 20.0
        elif velocity_ratio >= 4.0 and v_1h >= 3:
            risk_points += 15.0

        # High 1h volume surge factor
        if vol_1h > (vol_24h * 0.7) and vol_24h > 1000.0:
            risk_points += 15.0

        behavior_risk_score = round(min(100.0, max(0.0, risk_points)), 2)

        # Update running aggregates
        self.history.append((now, amount))
        self.total_count += 1
        self.total_amount_sum += amount
        self.total_amount_sq_sum += (amount ** 2)
        self.max_amount_seen = max(self.max_amount_seen, amount)

        return {
            "velocity_1h": v_1h + 1,  # Including current tx
            "velocity_24h": v_24h + 1,
            "volume_1h": round(vol_1h + amount, 2),
            "volume_24h": round(vol_24h + amount, 2),
            "avg_amount": round(avg_amount, 2),
            "std_amount": round(std_amount, 2),
            "max_amount": round(self.max_amount_seen, 2),
            "amount_deviation_ratio": round(amount_ratio, 2),
            "amount_zscore": round(amount_zscore, 2),
            "velocity_ratio": round(velocity_ratio, 2),
            "behavior_risk_score": behavior_risk_score,
            "historical_tx_count": self.total_count
        }


class BehavioralProfilerService:
    """Manages LRU dictionary of active account behavioral profiles."""

    def __init__(self, max_accounts: int = 10000):
        self.max_accounts = max_accounts
        self.profiles: OrderedDict[str, AccountProfile] = OrderedDict()

    def process_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes transaction against account history and returns behavioral features.
        """
        start_time = time.perf_counter()
        account_id = str(tx.get("nameOrig", "UNKNOWN"))
        amount = float(tx.get("amount", 0.0))
        tx_time = tx.get("emitted_at", time.time())

        if account_id in self.profiles:
            profile = self.profiles[account_id]
            self.profiles.move_to_end(account_id)
        else:
            if len(self.profiles) >= self.max_accounts:
                # Evict least recently used account
                self.profiles.popitem(last=False)
            profile = AccountProfile(account_id)
            self.profiles[account_id] = profile

        behavior_stats = profile.add_transaction(amount=amount, current_time=tx_time)
        behavior_latency_ms = round((time.perf_counter() - start_time) * 1000.0, 3)
        behavior_stats["behavior_latency_ms"] = behavior_latency_ms

        return behavior_stats

    def get_profile(self, account_id: str) -> Optional[AccountProfile]:
        return self.profiles.get(account_id)

    def active_account_count(self) -> int:
        return len(self.profiles)

    def clear(self):
        self.profiles.clear()


# Global Singleton Instance
behavior_profiler = BehavioralProfilerService()
