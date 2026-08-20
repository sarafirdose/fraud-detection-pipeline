"""
Kafka Transaction Producer

Streams PaySim financial transactions to Kafka topic 'transactions'.
Supports:
- Configurable streaming speed (TRANSACTION_RATE)
- Dynamic rate adjustment & pause/resume via runtime controller
- Automatic dataset looping/replay
- Injection of Demo Suspicious/Fraudulent transactions
- Timestamps and streaming metadata
"""

import os
import sys
import json
import time
import random
import logging
import argparse
import threading
from typing import Optional, Dict, Any
import pandas as pd

# Support relative module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import settings
from scripts.generate_sample_data import generate_paysim_sample

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (Producer) %(message)s")
logger = logging.getLogger("transaction_producer")


import socket

def is_port_open(host: str, port: int, timeout: float = 0.15) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def create_kafka_producer(bootstrap_servers: str = None, retries: int = 1):
    """Initializes Kafka Producer with fast pre-check."""
    bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
    host, port_str = bootstrap_servers.split(":") if ":" in bootstrap_servers else ("localhost", "9092")
    
    if not is_port_open(host, int(port_str), timeout=0.15):
        logger.info(f"Kafka broker not active on {bootstrap_servers}. Using fast in-process stream engine.")
        return None

    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            retries=1,
            request_timeout_ms=1000,
            acks=1
        )
        logger.info(f"Connected to Kafka broker at {bootstrap_servers}")
        return producer
    except Exception as e:
        logger.info(f"Kafka producer initialization bypassed: {e}")
        return None


class TransactionProducerService:
    """Manages the continuous transaction streaming loop."""

    def __init__(self, data_path: Optional[str] = None, rate: Optional[float] = None):
        self.data_path = data_path or settings.DATASET_PATH
        self.rate = rate or settings.TRANSACTION_RATE
        self.running = False
        self.paused = False
        self.producer = None
        self.df = None
        self.current_index = 0
        self.total_sent = 0
        self.lock = threading.Lock()

    def load_data(self):
        """Loads dataset or generates if missing."""
        if not os.path.exists(self.data_path):
            if os.path.exists(settings.PAYSIM_RAW_PATH):
                self.data_path = settings.PAYSIM_RAW_PATH
            else:
                logger.info(f"Dataset not found. Generating sample data at {self.data_path}...")
                generate_paysim_sample(num_records=30000, output_path=self.data_path)

        logger.info(f"Loading transaction stream from {self.data_path}...")
        self.df = pd.read_csv(self.data_path)
        logger.info(f"Loaded {len(self.df):,} transactions for streaming.")

    def set_rate(self, new_rate: float):
        """Adjusts transactions per second rate dynamically."""
        with self.lock:
            self.rate = max(0.1, float(new_rate))
            logger.info(f"Producer rate updated to {self.rate} tx/sec")

    def pause(self):
        with self.lock:
            self.paused = True
            logger.info("Producer stream paused.")

    def resume(self):
        with self.lock:
            self.paused = False
            logger.info("Producer stream resumed.")

    def stop(self):
        with self.lock:
            self.running = False
            logger.info("Stopping producer...")

    def send_demo_fraud(
        self,
        tx_type: str = "TRANSFER",
        amount: float = 650000.00,
        drain_account: bool = True
    ) -> Dict[str, Any]:
        """
        Creates and sends a deliberate demo suspicious transaction through the Kafka pipeline.
        Clearly labeled with is_demo=True.
        """
        orig_id = f"C{random.randint(8000000000, 9999999999)}"
        dest_id = f"C{random.randint(1000000000, 2999999999)}"
        old_orig = amount if drain_account else amount * 1.05
        new_orig = 0.0 if drain_account else (old_orig - amount)
        old_dest = 0.0
        new_dest = 0.0

        demo_tx = {
            "transaction_id": f"DEMO-TX-{int(time.time()*1000)}-{random.randint(100, 999)}",
            "step": random.randint(1, 100),
            "type": tx_type,
            "amount": float(amount),
            "nameOrig": orig_id,
            "oldbalanceOrg": float(old_orig),
            "newbalanceOrig": float(new_orig),
            "nameDest": dest_id,
            "oldbalanceDest": float(old_dest),
            "newbalanceDest": float(new_dest),
            "is_demo": True,
            "demo_description": "PaySim-compatible synthetic demo fraud (account drain pattern)",
            "emitted_at": time.time()
        }

        if self.producer is None:
            self.producer = create_kafka_producer()
            if self.producer is None:
                logger.info("Kafka broker offline. Routing demo fraud through local stream processor...")
                from streaming.stream_processor import local_stream_processor
                return local_stream_processor.process_message(demo_tx)

        self.producer.send(
            settings.KAFKA_TRANSACTIONS_TOPIC,
            key=demo_tx["transaction_id"],
            value=demo_tx
        )
        self.producer.flush()
        logger.info(f"==> Injected DEMO FRAUD Transaction to Kafka: {demo_tx['transaction_id']} (${amount:,.2f})")
        return demo_tx

    def run(self, max_records: Optional[int] = None):
        """Main producer loop."""
        self.load_data()
        self.producer = create_kafka_producer()
        is_direct_mode = self.producer is None

        if is_direct_mode:
            logger.info("⚡ Kafka broker not detected locally. Operating in High-Speed In-Process Streaming Mode.")
            from streaming.stream_processor import local_stream_processor

        self.running = True
        logger.info(f"Starting transaction producer @ {self.rate} tx/sec...")

        records = self.df.to_dict(orient="records")
        num_records = len(records)

        try:
            while self.running:
                if self.paused:
                    time.sleep(0.5)
                    continue

                tx_data = records[self.current_index].copy()
                tx_id = f"TX-{int(time.time()*1000)}-{self.current_index:06d}"

                payload = {
                    "transaction_id": tx_id,
                    "step": int(tx_data.get("step", 1)),
                    "type": str(tx_data.get("type", "PAYMENT")),
                    "amount": float(tx_data.get("amount", 0.0)),
                    "nameOrig": str(tx_data.get("nameOrig", "")),
                    "oldbalanceOrg": float(tx_data.get("oldbalanceOrg", 0.0)),
                    "newbalanceOrig": float(tx_data.get("newbalanceOrig", 0.0)),
                    "nameDest": str(tx_data.get("nameDest", "")),
                    "oldbalanceDest": float(tx_data.get("oldbalanceDest", 0.0)),
                    "newbalanceDest": float(tx_data.get("newbalanceDest", 0.0)),
                    "is_demo": False,
                    "emitted_at": time.time()
                }

                if is_direct_mode:
                    local_stream_processor.process_message(payload)
                else:
                    self.producer.send(
                        settings.KAFKA_TRANSACTIONS_TOPIC,
                        key=tx_id,
                        value=payload
                    )

                self.total_sent += 1
                self.current_index = (self.current_index + 1) % num_records

                if not is_direct_mode and self.total_sent % 50 == 0:
                    self.producer.flush()

                if max_records and self.total_sent >= max_records:
                    break

                # Sleep to maintain desired rate
                delay = 1.0 / max(0.1, self.rate)
                time.sleep(delay)

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received.")
        finally:
            self.running = False
            if self.producer:
                try:
                    self.producer.flush()
                    self.producer.close()
                except Exception:
                    pass


# Singleton instance for programmatic/FastAPI control
producer_service = TransactionProducerService()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PaySim Kafka Transaction Stream Producer")
    parser.add_argument("--rate", type=float, default=5.0, help="Transactions per second")
    parser.add_argument("--data", type=str, default=None, help="Path to PaySim CSV dataset")
    parser.add_argument("--count", type=int, default=None, help="Total transactions to emit (None for infinite)")
    parser.add_argument("--inject-fraud", action="store_true", help="Send a single demo fraud transaction and exit")
    args = parser.parse_args()

    if args.inject_fraud:
        producer_service.send_demo_fraud()
    else:
        service = TransactionProducerService(data_path=args.data, rate=args.rate)
        service.run(max_records=args.count)
