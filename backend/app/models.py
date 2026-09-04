"""
Pydantic Data Models and Schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    transaction_id: str
    step: int
    type: str
    amount: float
    nameOrigMasked: str
    nameDestMasked: str
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float
    is_fraud: bool
    risk_score: float
    risk_level: str
    fraud_probability: Optional[float] = 0.0
    risk_factors: List[str] = []
    processing_latency_ms: Optional[float] = 0.0
    end_to_end_latency_ms: Optional[float] = 0.0
    is_demo: bool = False
    evaluated_at: Optional[float] = None


class TransactionResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[TransactionBase]


class FraudAlertItem(BaseModel):
    alert_id: str
    transaction_id: str
    amount: float
    type: str
    nameOrigMasked: str
    nameDestMasked: str
    risk_score: float
    risk_level: str
    risk_factors: List[str]
    is_demo: bool = False
    status: str = "NEW"  # NEW, INVESTIGATING, CONFIRMED, DISMISSED
    created_at: float


class AlertStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(NEW|INVESTIGATING|CONFIRMED|DISMISSED)$")


class KPISummary(BaseModel):
    total_transactions: int = 0
    fraud_alerts: int = 0
    fraud_rate_pct: float = 0.0
    high_critical_alerts: int = 0
    avg_latency_ms: float = 0.0
    normal_transactions: int = 0
    total_amount_processed: float = 0.0
    fraud_amount_detected: float = 0.0


class TimeSeriesPoint(BaseModel):
    timestamp: str
    epoch: float
    tx_count: int
    fraud_count: int
    fraud_rate: float
    avg_risk: float


class DistributionItem(BaseModel):
    name: str
    value: int
    percentage: float


class SimulatorControlRequest(BaseModel):
    action: str = Field(..., pattern="^(start|stop|pause|resume|set_rate|inject_fraud)$")
    rate: Optional[float] = None
    fraud_type: Optional[str] = "TRANSFER"
    amount: Optional[float] = 650000.00
    drain_account: Optional[bool] = True


class ModelInfoResponse(BaseModel):
    model_name: str
    trained_at: str
    dataset_source: str
    dataset_path: str
    train_samples: int
    test_samples: int
    fraud_count_total: int
    fraud_rate_pct: float
    metrics: Dict[str, Any]
    feature_columns: List[str]
    feature_importances: List[Dict[str, Any]]
    thresholds: Dict[str, float]


class SystemHealth(BaseModel):
    status: str
    kafka_connected: bool
    mongo_connected: bool
    model_loaded: bool
    database_name: str
    timestamp: float
