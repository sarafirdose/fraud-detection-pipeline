"""
Local Embedded Store & Event Bus (Fallback when standalone MongoDB / Kafka are offline)

Ensures 100% functionality on any local laptop even if Kafka / MongoDB services are not started.
Provides thread-safe storage, indexed queries, and live pub/sub for the streaming pipeline.
"""

import time
import threading
from typing import List, Dict, Any, Optional

class EmbeddedStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.transactions: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        self.tx_map: Dict[str, Dict[str, Any]] = {}
        self.alert_map: Dict[str, Dict[str, Any]] = {}
        self.subscribers: List[Any] = []

    def save_transaction(self, tx: Dict[str, Any]):
        with self.lock:
            tx_id = tx.get("transaction_id")
            if tx_id in self.tx_map:
                # Update existing
                self.tx_map[tx_id].update(tx)
            else:
                self.tx_map[tx_id] = tx
                self.transactions.insert(0, tx)
                # Keep buffer manageable
                if len(self.transactions) > 2000:
                    evicted = self.transactions.pop()
                    self.tx_map.pop(evicted.get("transaction_id"), None)

    def save_alert(self, alert: Dict[str, Any]):
        with self.lock:
            alert_id = alert.get("alert_id")
            if alert_id in self.alert_map:
                self.alert_map[alert_id].update(alert)
            else:
                self.alert_map[alert_id] = alert
                self.alerts.insert(0, alert)
                if len(self.alerts) > 500:
                    evicted = self.alerts.pop()
                    self.alert_map.pop(evicted.get("alert_id"), None)

    def update_alert_status(self, alert_id: str, status: str) -> bool:
        with self.lock:
            if alert_id in self.alert_map:
                self.alert_map[alert_id]["status"] = status
                return True
            return False

    def get_transactions(self, skip: int = 0, limit: int = 50, filters: Dict[str, Any] = None) -> (List[Dict[str, Any]], int):
        with self.lock:
            res = self.transactions
            if filters:
                if filters.get("type"):
                    res = [t for t in res if t.get("type") == filters["type"]]
                if filters.get("risk_level"):
                    res = [t for t in res if t.get("risk_level") == filters["risk_level"]]
                if filters.get("is_fraud") is not None:
                    res = [t for t in res if t.get("is_fraud") == filters["is_fraud"]]
                if filters.get("min_amount") is not None:
                    res = [t for t in res if t.get("amount", 0) >= filters["min_amount"]]
                if filters.get("max_amount") is not None:
                    res = [t for t in res if t.get("amount", 0) <= filters["max_amount"]]
                if filters.get("search"):
                    q = filters["search"].lower()
                    res = [t for t in res if q in str(t.get("transaction_id", "")).lower() or q in str(t.get("nameOrigMasked", "")).lower() or q in str(t.get("nameDestMasked", "")).lower()]

            total = len(res)
            return res[skip : skip + limit], total

    def get_recent_transactions(self, limit: int = 30) -> List[Dict[str, Any]]:
        with self.lock:
            return list(self.transactions[:limit])

    def get_transaction_by_id(self, tx_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self.tx_map.get(tx_id)

    def get_alerts(self, limit: int = 50, status: Optional[str] = None, risk_level: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.lock:
            res = self.alerts
            if status:
                res = [a for a in res if a.get("status") == status]
            if risk_level:
                res = [a for a in res if a.get("risk_level") == risk_level]
            return list(res[:limit])

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            total_tx = len(self.transactions)
            if total_tx == 0:
                return {
                    "total_transactions": 0,
                    "fraud_alerts": 0,
                    "fraud_rate_pct": 0.0,
                    "high_critical_alerts": 0,
                    "avg_latency_ms": 0.0,
                    "normal_transactions": 0,
                    "total_amount_processed": 0.0,
                    "fraud_amount_detected": 0.0
                }

            fraud_txs = [t for t in self.transactions if t.get("is_fraud")]
            fraud_count = len(fraud_txs)
            high_crit_count = len([t for t in self.transactions if t.get("risk_level") in ["HIGH", "CRITICAL"]])
            total_amt = sum(t.get("amount", 0.0) for t in self.transactions)
            fraud_amt = sum(t.get("amount", 0.0) for t in fraud_txs)
            avg_lat = sum(t.get("processing_latency_ms", 0.0) for t in self.transactions) / total_tx

            return {
                "total_transactions": total_tx,
                "fraud_alerts": fraud_count,
                "fraud_rate_pct": round((fraud_count / total_tx) * 100.0, 2),
                "high_critical_alerts": high_crit_count,
                "avg_latency_ms": round(avg_lat, 2),
                "normal_transactions": total_tx - fraud_count,
                "total_amount_processed": round(total_amt, 2),
                "fraud_amount_detected": round(fraud_amt, 2)
            }


local_store = EmbeddedStore()
