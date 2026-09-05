"""
Health Check and Service Status Route (Fast Non-Blocking)
"""

import time
import socket
from fastapi import APIRouter
from backend.app.database import MongoManager
from backend.app.models import SystemHealth
from config.settings import settings
from ml.predictor import predictor

router = APIRouter(prefix="/api/health", tags=["Health"])


def is_port_open(host: str, port: int, timeout: float = 0.15) -> bool:
    """Fast non-blocking TCP socket check."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


@router.get("", response_model=SystemHealth)
async def check_health():
    mongo_ok = await MongoManager.is_connected()
    
    # Fast non-blocking Kafka port check
    host, port_str = settings.KAFKA_BOOTSTRAP_SERVERS.split(":") if ":" in settings.KAFKA_BOOTSTRAP_SERVERS else ("localhost", "9092")
    kafka_ok = is_port_open(host, int(port_str), timeout=0.1)
    model_loaded = predictor.model is not None
    status_str = "healthy" if (mongo_ok and kafka_ok and model_loaded) else "operational"

    return SystemHealth(
        status=status_str,
        kafka_connected=kafka_ok,
        mongo_connected=mongo_ok,
        model_loaded=model_loaded,
        database_name=settings.MONGO_DB_NAME,
        timestamp=time.time()
    )
