"""
Optional Apache Cassandra NoSQL Client

Provides high write-throughput persistence for transactions and alerts.
Guarantees resilient, non-blocking fallback if Cassandra is unavailable.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import settings

logger = logging.getLogger("cassandra_client")


class CassandraClient:
    """Optional Cassandra sink with automatic graceful fallback."""

    def __init__(self):
        self.session = None
        self.cluster = None
        self.is_connected = False
        self.insert_tx_stmt = None
        self.insert_alert_stmt = None

    def connect(self) -> bool:
        """Attempts to connect to Cassandra keyspace."""
        if not settings.ENABLE_CASSANDRA:
            logger.info("Cassandra unavailable — using primary storage.")
            return False

        try:
            from cassandra.cluster import Cluster
            from cassandra.query import SimpleStatement

            hosts = [h.strip() for h in settings.CASSANDRA_HOSTS.split(",")]
            self.cluster = Cluster(hosts, port=settings.CASSANDRA_PORT, connect_timeout=2.0)
            self.session = self.cluster.connect()

            # Initialize Keyspace & Schema
            self.session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {settings.CASSANDRA_KEYSPACE}
                WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};
            """)
            self.session.set_keyspace(settings.CASSANDRA_KEYSPACE)

            self.session.execute("""
                CREATE TABLE IF NOT EXISTS transactions_by_account (
                    account_id text,
                    transaction_time timestamp,
                    transaction_id text,
                    transaction_type text,
                    amount double,
                    dest_account text,
                    old_balance_orig double,
                    new_balance_orig double,
                    old_balance_dest double,
                    new_balance_dest double,
                    risk_score double,
                    risk_level text,
                    is_fraud boolean,
                    model_used text,
                    processing_latency_ms double,
                    PRIMARY KEY ((account_id), transaction_time, transaction_id)
                ) WITH CLUSTERING ORDER BY (transaction_time DESC, transaction_id ASC);
            """)

            self.session.execute("""
                CREATE TABLE IF NOT EXISTS fraud_alerts_by_time (
                    date_bucket text,
                    created_at timestamp,
                    alert_id text,
                    transaction_id text,
                    account_id text,
                    dest_account text,
                    transaction_type text,
                    amount double,
                    risk_score double,
                    risk_level text,
                    risk_factors list<text>,
                    status text,
                    is_demo boolean,
                    PRIMARY KEY ((date_bucket), created_at, alert_id)
                ) WITH CLUSTERING ORDER BY (created_at DESC, alert_id ASC);
            """)

            self.is_connected = True
            logger.info(f"Connected to Apache Cassandra keyspace '{settings.CASSANDRA_KEYSPACE}'")
            return True

        except Exception as e:
            self.is_connected = False
            logger.info(f"Cassandra unavailable — using primary storage ({e}).")
            return False

    def insert_transaction(self, tx: Dict[str, Any]) -> bool:
        """Writes transaction record to Cassandra if connected."""
        if not self.is_connected or not self.session:
            return False

        try:
            t_epoch = tx.get("evaluated_at") or tx.get("emitted_at", datetime.utcnow().timestamp())
            t_dt = datetime.fromtimestamp(t_epoch)

            query = """
                INSERT INTO transactions_by_account (
                    account_id, transaction_time, transaction_id, transaction_type,
                    amount, dest_account, old_balance_orig, new_balance_orig,
                    old_balance_dest, new_balance_dest, risk_score, risk_level,
                    is_fraud, model_used, processing_latency_ms
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.session.execute(query, (
                str(tx.get("nameOrig", "UNKNOWN")),
                t_dt,
                str(tx.get("transaction_id", "")),
                str(tx.get("type", "")),
                float(tx.get("amount", 0.0)),
                str(tx.get("nameDest", "")),
                float(tx.get("oldbalanceOrg", 0.0)),
                float(tx.get("newbalanceOrig", 0.0)),
                float(tx.get("oldbalanceDest", 0.0)),
                float(tx.get("newbalanceDest", 0.0)),
                float(tx.get("risk_score", 0.0)),
                str(tx.get("risk_level", "LOW")),
                bool(tx.get("is_fraud", False)),
                str(tx.get("model_used", "")),
                float(tx.get("processing_latency_ms", 0.0))
            ))
            return True
        except Exception as e:
            logger.debug(f"Cassandra transaction write error: {e}")
            return False

    def insert_alert(self, alert: Dict[str, Any]) -> bool:
        """Writes fraud alert record to Cassandra if connected."""
        if not self.is_connected or not self.session:
            return False

        try:
            t_epoch = alert.get("created_at", datetime.utcnow().timestamp())
            t_dt = datetime.fromtimestamp(t_epoch)
            date_bucket = t_dt.strftime("%Y-%m-%d")

            query = """
                INSERT INTO fraud_alerts_by_time (
                    date_bucket, created_at, alert_id, transaction_id,
                    account_id, dest_account, transaction_type, amount,
                    risk_score, risk_level, risk_factors, status, is_demo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.session.execute(query, (
                date_bucket,
                t_dt,
                str(alert.get("alert_id", "")),
                str(alert.get("transaction_id", "")),
                str(alert.get("nameOrigMasked", "")),
                str(alert.get("nameDestMasked", "")),
                str(alert.get("type", "")),
                float(alert.get("amount", 0.0)),
                float(alert.get("risk_score", 0.0)),
                str(alert.get("risk_level", "HIGH")),
                list(alert.get("risk_factors", [])),
                str(alert.get("status", "NEW")),
                bool(alert.get("is_demo", False))
            ))
            return True
        except Exception as e:
            logger.debug(f"Cassandra alert write error: {e}")
            return False

    def close(self):
        if self.cluster:
            try:
                self.cluster.shutdown()
            except Exception:
                pass


cassandra_client = CassandraClient()
