-- ==========================================================
-- Apache Cassandra Schema for High-Throughput Fraud Storage
-- Keyspace: fraud_detection
-- ==========================================================

CREATE KEYSPACE IF NOT EXISTS fraud_detection
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE fraud_detection;

-- 1. Transactions Partitioned by Account with Clustering by Timestamp
-- Supports high-write throughput and fast retrieval of user history
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

-- 2. Fraud Alerts Partitioned by Date Bucket with Clustering by Created Time
-- Supports rapid querying of all fraud alerts in time windows
CREATE TABLE IF NOT EXISTS fraud_alerts_by_time (
    date_bucket text, -- Format: YYYY-MM-DD
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
