import os
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "Real-Time Financial Fraud Detection Pipeline"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TRANSACTIONS_TOPIC: str = "transactions"
    KAFKA_ALERTS_TOPIC: str = "fraud-alerts"
    KAFKA_GROUP_ID: str = "fraud-detection-group"
    KAFKA_CLIENT_ID: str = "fraud-detection-client"

    # MongoDB Configuration
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "fraud_detection"
    MONGO_TRANSACTIONS_COLLECTION: str = "transactions"
    MONGO_ALERTS_COLLECTION: str = "fraud_alerts"
    MONGO_METRICS_COLLECTION: str = "system_metrics"

    # Cassandra Configuration (Optional Storage)
    CASSANDRA_HOSTS: str = "localhost"
    CASSANDRA_PORT: int = 9042
    CASSANDRA_KEYSPACE: str = "fraud_detection"
    ENABLE_CASSANDRA: bool = False

    # Machine Learning & Data Paths
    DATASET_PATH: str = "data/sample_transactions.csv"
    PAYSIM_RAW_PATH: str = "data/PS_20174392719_1491204439457_log.csv"
    MODEL_PATH: str = "models/fraud_model.joblib"
    RF_MODEL_PATH: str = "models/rf_model.joblib"
    IFOREST_MODEL_PATH: str = "models/isolation_forest.joblib"
    AUTOENCODER_MODEL_PATH: str = "models/autoencoder_model.joblib"
    MODEL_METADATA_PATH: str = "models/model_metadata.json"
    MODEL_COMPARISON_PATH: str = "models/model_comparison.json"

    # Model Selection & Ensemble Configuration
    # Modes: SUPERVISED_XGBOOST | SUPERVISED_RANDOM_FOREST | UNSUPERVISED_ISOLATION_FOREST | UNSUPERVISED_AUTOENCODER | ENSEMBLE
    ACTIVE_MODEL_MODE: str = "SUPERVISED_XGBOOST"
    ENSEMBLE_SUPERVISED_WEIGHT: float = 0.65
    ENSEMBLE_ANOMALY_WEIGHT: float = 0.35
    BEHAVIORAL_RISK_WEIGHT: float = 0.20

    # User Behavioral Profiling Configuration
    BEHAVIOR_WINDOW_1H_SECONDS: int = 3600
    BEHAVIOR_WINDOW_24H_SECONDS: int = 86400
    BEHAVIOR_MAX_ACCOUNTS: int = 10000

    # Streaming / Simulation Defaults
    TRANSACTION_RATE: float = 5.0  # transactions per second
    BATCH_SIZE: int = 10
    FRAUD_SCORE_THRESHOLD: float = 0.50  # Risk score >= 50% flagged as fraud
    HIGH_RISK_THRESHOLD: float = 0.70
    CRITICAL_RISK_THRESHOLD: float = 0.85

    # FastAPI Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


settings = Settings()
