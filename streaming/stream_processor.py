"""
Real-Time Stream Processor (Python + Kafka + ML + Cassandra/MongoDB + Prometheus)

Primary local streaming engine:
1. Consumes raw JSON transactions from Kafka topic 'transactions'
2. Evaluates stateful behavioral profile (velocity, amount surge, z-score)
3. Feeds transaction into Unified Fraud Scorer (XGBoost / RF / Isolation Forest / Autoencoder / Ensemble)
4. Persists enriched transactions to MongoDB collection 'transactions' & optional Cassandra
5. If classified as suspicious/fraud, writes alert to MongoDB 'fraud_alerts', Cassandra, and Kafka 'fraud-alerts'
6. Exposes Prometheus metrics and system metrics
"""

import os
import sys
import json
import time
import logging
from typing import Optional, Dict, Any
from pymongo import MongoClient, ASCENDING, DESCENDING, UpdateOne
from pymongo.errors import ConnectionFailure, PyMongoError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import settings
from ml.predictor import FraudPredictor, predictor
from ml.unified_scorer import unified_scorer
from stream.behavior_profile import behavior_profiler
from storage.cassandra_client import cassandra_client
from monitoring.metrics import (
    record_transaction_metrics,
    KAFKA_MESSAGES_CONSUMED,
    KAFKA_ERRORS,
    KAFKA_PROCESSING_LATENCY,
    ACTIVE_ACCOUNTS
)
from producer.producer import create_kafka_producer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (StreamProcessor) %(message)s")
logger = logging.getLogger("stream_processor")


class StreamProcessor:
    """Consumes from Kafka, runs Unified ML scoring & Behavioral Profiling, and persists to DBs."""

    def __init__(self):
        self.running = False
        self.predictor = predictor
        self.scorer = unified_scorer
        self.mongo_client: Optional[MongoClient] = None
        self.db = None
        self.kafka_producer = None
        self.total_processed = 0
        self.fraud_detected = 0
        self.latencies = []

    def init_mongo(self):
        """Initializes MongoDB client and creates essential indexes."""
        try:
            self.mongo_client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
            self.mongo_client.admin.command("ping")
            self.db = self.mongo_client[settings.MONGO_DB_NAME]
            logger.info(f"Connected to MongoDB database '{settings.MONGO_DB_NAME}'")

            tx_coll = self.db[settings.MONGO_TRANSACTIONS_COLLECTION]
            tx_coll.create_index([("transaction_id", ASCENDING)], unique=True)
            tx_coll.create_index([("evaluated_at", DESCENDING)])
            tx_coll.create_index([("risk_level", ASCENDING)])
            tx_coll.create_index([("is_fraud", ASCENDING)])
            tx_coll.create_index([("type", ASCENDING)])

            alert_coll = self.db[settings.MONGO_ALERTS_COLLECTION]
            alert_coll.create_index([("alert_id", ASCENDING)], unique=True)
            alert_coll.create_index([("transaction_id", ASCENDING)])
            alert_coll.create_index([("created_at", DESCENDING)])
            alert_coll.create_index([("risk_level", ASCENDING)])
            alert_coll.create_index([("status", ASCENDING)])
        except Exception as e:
            logger.info(f"MongoDB connection offline ({e}). Operating with Embedded Store.")
            self.mongo_client = None
            self.db = None

    def init_cassandra(self):
        """Attempts Cassandra optional connection."""
        cassandra_client.connect()

    def init_kafka(self):
        """Initializes Kafka producer for alerts."""
        self.kafka_producer = create_kafka_producer()

    def create_kafka_consumer(self):
        """Creates Kafka consumer for topic 'transactions'."""
        from kafka import KafkaConsumer
        try:
            consumer = KafkaConsumer(
                settings.KAFKA_TRANSACTIONS_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset="latest",
                enable_auto_commit=True,
                group_id=settings.KAFKA_GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                consumer_timeout_ms=1000
            )
            logger.info(f"Kafka consumer subscribed to topic '{settings.KAFKA_TRANSACTIONS_TOPIC}'")
            return consumer
        except Exception as e:
            logger.info(f"Kafka consumer standby: {e}")
            return None

    def process_message(self, raw_tx: Dict[str, Any]) -> Dict[str, Any]:
        """Runs Unified ML scoring and saves enriched transaction + alerts."""
        stream_start_time = time.perf_counter()
        tx_id = raw_tx.get("transaction_id", f"TX-{int(time.time()*1000)}")
        emitted_at = raw_tx.get("emitted_at", time.time())

        # 1. Run Unified Multi-Model & Behavioral Scoring
        enriched_tx = self.predictor.predict(raw_tx)
        enriched_tx["transaction_id"] = tx_id
        
        # End-to-end processing latency from producer emission to scoring completion
        now = time.time()
        e2e_latency_ms = round((now - emitted_at) * 1000.0, 2)
        enriched_tx["end_to_end_latency_ms"] = e2e_latency_ms
        enriched_tx["processed_at"] = now

        self.latencies.append(enriched_tx.get("processing_latency_ms", 1.0))
        if len(self.latencies) > 1000:
            self.latencies.pop(0)

        self.total_processed += 1
        is_fraud = enriched_tx.get("is_fraud", False)
        risk_level = enriched_tx.get("risk_level", "LOW")

        # Record in Prometheus
        stream_latency_s = (time.perf_counter() - stream_start_time)
        active_mode = enriched_tx.get("active_model_mode", "SUPERVISED_XGBOOST")
        record_transaction_metrics(enriched_tx, model_mode=active_mode, stream_lat_s=stream_latency_s)
        ACTIVE_ACCOUNTS.set(behavior_profiler.active_account_count())

        # Always persist to local_store for live UI access
        from backend.app.local_storage import local_store
        local_store.save_transaction(enriched_tx)

        # 2. Persist Transaction to MongoDB if available
        if self.db is not None:
            try:
                tx_coll = self.db[settings.MONGO_TRANSACTIONS_COLLECTION]
                tx_coll.update_one(
                    {"transaction_id": tx_id},
                    {"$set": enriched_tx},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"MongoDB write error for tx {tx_id}: {e}")

        # 3. Persist to Cassandra if available
        cassandra_client.insert_transaction(enriched_tx)

        # 4. Handle Fraud / Suspicious Alerts
        if is_fraud or risk_level in ["HIGH", "CRITICAL"]:
            self.fraud_detected += 1
            alert_doc = {
                "alert_id": f"ALT-{tx_id}",
                "transaction_id": tx_id,
                "amount": enriched_tx.get("amount", 0.0),
                "type": enriched_tx.get("type", "PAYMENT"),
                "nameOrigMasked": enriched_tx.get("nameOrigMasked", "C***"),
                "nameDestMasked": enriched_tx.get("nameDestMasked", "C***"),
                "risk_score": enriched_tx.get("risk_score", 0.0),
                "risk_level": risk_level,
                "risk_factors": enriched_tx.get("risk_factors", []),
                "explanation": enriched_tx.get("explanation", []),
                "model_used": enriched_tx.get("model_used", ""),
                "is_demo": enriched_tx.get("is_demo", False),
                "status": "NEW",  # NEW, INVESTIGATING, CONFIRMED, DISMISSED
                "created_at": now
            }

            local_store.save_alert(alert_doc)
            cassandra_client.insert_alert(alert_doc)

            if self.db is not None:
                try:
                    alert_coll = self.db[settings.MONGO_ALERTS_COLLECTION]
                    alert_coll.update_one(
                        {"alert_id": alert_doc["alert_id"]},
                        {"$set": alert_doc},
                        upsert=True
                    )
                except Exception as e:
                    logger.error(f"MongoDB alert write error: {e}")

            # Send alert to Kafka topic 'fraud-alerts'
            if self.kafka_producer:
                try:
                    self.kafka_producer.send(
                        settings.KAFKA_ALERTS_TOPIC,
                        key=tx_id,
                        value=alert_doc
                    )
                except Exception as e:
                    logger.warning(f"Kafka alert publish error: {e}")

            logger.warning(
                f"🚨 [FRAUD ALERT] Tx: {tx_id} | Type: {enriched_tx['type']} | "
                f"Amount: ${enriched_tx['amount']:,.2f} | Risk: {enriched_tx['risk_score']}% ({risk_level})"
            )

        # 5. Periodic System Metrics Update
        if self.total_processed % 20 == 0 and self.db is not None:
            avg_lat = round(sum(self.latencies) / max(1, len(self.latencies)), 2)
            metrics_doc = {
                "metric_id": "latest_system_metrics",
                "total_processed": self.total_processed,
                "fraud_detected": self.fraud_detected,
                "fraud_rate_pct": round((self.fraud_detected / max(1, self.total_processed)) * 100.0, 2),
                "avg_latency_ms": avg_lat,
                "active_accounts": behavior_profiler.active_account_count(),
                "updated_at": now
            }
            try:
                self.db[settings.MONGO_METRICS_COLLECTION].update_one(
                    {"metric_id": "latest_system_metrics"},
                    {"$set": metrics_doc},
                    upsert=True
                )
            except Exception:
                pass

        return enriched_tx

    def run(self):
        """Starts real-time streaming processing loop."""
        self.init_mongo()
        self.init_cassandra()
        self.init_kafka()
        self.running = True

        logger.info("Initializing Stream Processor loop...")

        while self.running:
            consumer = self.create_kafka_consumer()
            if consumer is None:
                logger.info("Kafka broker not available. Retrying in 5 seconds...")
                time.sleep(5)
                continue

            try:
                logger.info("⚡ Stream processor actively listening for transactions...")
                for message in consumer:
                    if not self.running:
                        break
                    raw_tx = message.value
                    if isinstance(raw_tx, dict):
                        KAFKA_MESSAGES_CONSUMED.inc()
                        self.process_message(raw_tx)
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received.")
                self.running = False
            except Exception as e:
                KAFKA_ERRORS.labels(error_type="consumer_loop").inc()
                logger.error(f"Stream processor encountered error: {e}. Reconnecting...")
                time.sleep(2)
            finally:
                try:
                    consumer.close()
                except Exception:
                    pass

        logger.info("Stream Processor shutdown completed.")


local_stream_processor = StreamProcessor()

if __name__ == "__main__":
    local_stream_processor.run()
