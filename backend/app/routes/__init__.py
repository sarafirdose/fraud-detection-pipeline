from .health import router as health_router
from .transactions import router as transactions_router
from .alerts import router as alerts_router
from .analytics import router as analytics_router
from .simulator import router as simulator_router
from .model_info import router as model_info_router

__all__ = [
    "health_router",
    "transactions_router",
    "alerts_router",
    "analytics_router",
    "simulator_router",
    "model_info_router"
]
