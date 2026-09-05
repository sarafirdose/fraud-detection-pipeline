"""
Main FastAPI Application Entrypoint

Initializes API routers, CORS, Prometheus /metrics endpoint, WebSocket live push loop, and lifecycle.
"""

import os
import sys
import time
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pymongo import DESCENDING

# Path resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config.settings import settings
from backend.app.database import MongoManager
from backend.app.websocket import ws_manager
from backend.app.routes import (
    health_router,
    transactions_router,
    alerts_router,
    analytics_router,
    simulator_router,
    model_info_router
)
from monitoring.metrics import (
    generate_latest,
    CONTENT_TYPE_LATEST,
    API_REQUEST_COUNT,
    API_REQUEST_LATENCY,
    TRANSACTIONS_PER_SECOND,
    ACTIVE_ACCOUNTS
)
from stream.behavior_profile import behavior_profiler
from storage.cassandra_client import cassandra_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (FastAPI) %(message)s")
logger = logging.getLogger("fraud_backend")


# Background task for live WebSocket updates
async def live_broadcast_worker():
    """Polls latest updates and pushes real-time diffs to connected WebSockets."""
    logger.info("Starting WebSocket live broadcast worker...")
    last_tx_time = 0.0
    last_alert_time = 0.0
    last_count = 0
    last_t = time.time()

    while True:
        try:
            now_t = time.time()
            from backend.app.local_storage import local_store
            st = local_store.get_stats()
            curr_count = st["total_transactions"]
            
            # Compute TPS
            dt = max(0.1, now_t - last_t)
            tps = round((curr_count - last_count) / dt, 1)
            TRANSACTIONS_PER_SECOND.set(max(0.0, tps))
            ACTIVE_ACCOUNTS.set(behavior_profiler.active_account_count())

            last_count = curr_count
            last_t = now_t

            if ws_manager.active_connections:
                db = MongoManager.get_db()
                new_txs = []
                new_alerts = []

                if db is not None:
                    try:
                        tx_coll = db[settings.MONGO_TRANSACTIONS_COLLECTION]
                        query = {"evaluated_at": {"$gt": last_tx_time}} if last_tx_time > 0 else {}
                        cursor = tx_coll.find(query, {"_id": 0}).sort("evaluated_at", DESCENDING).limit(10)
                        new_txs = await cursor.to_list(10)

                        alert_coll = db[settings.MONGO_ALERTS_COLLECTION]
                        alert_query = {"created_at": {"$gt": last_alert_time}} if last_alert_time > 0 else {}
                        alert_cursor = alert_coll.find(alert_query, {"_id": 0}).sort("created_at", DESCENDING).limit(5)
                        new_alerts = await alert_cursor.to_list(5)
                    except Exception:
                        pass

                # Fallback to local_store
                if not new_txs:
                    local_all_tx = local_store.get_recent_transactions(10)
                    new_txs = [t for t in local_all_tx if (t.get("evaluated_at", 0.0) > last_tx_time)]
                if not new_alerts:
                    local_all_alts = local_store.get_alerts(5)
                    new_alerts = [a for a in local_all_alts if (a.get("created_at", 0.0) > last_alert_time)]

                if new_txs:
                    last_tx_time = max(t.get("evaluated_at", 0.0) for t in new_txs)
                    for tx in reversed(new_txs):
                        await ws_manager.broadcast("transaction", tx)

                if new_alerts:
                    last_alert_time = max(a.get("created_at", 0.0) for a in new_alerts)
                    for alert in reversed(new_alerts):
                        await ws_manager.broadcast("alert", alert)

                # Push KPI update
                await ws_manager.broadcast("kpi_update", {
                    "total_transactions": st["total_transactions"],
                    "fraud_alerts": st["fraud_alerts"],
                    "fraud_rate_pct": st["fraud_rate_pct"],
                    "high_critical_alerts": st["high_critical_alerts"],
                    "active_accounts": behavior_profiler.active_account_count(),
                    "tps": tps
                })

        except Exception as e:
            logger.debug(f"Broadcast worker transient loop: {e}")

        await asyncio.sleep(0.5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Database & Storage connections...")
    await MongoManager.connect()
    cassandra_client.connect()
    # Start WebSocket worker
    worker_task = asyncio.create_task(live_broadcast_worker())
    yield
    # Shutdown
    worker_task.cancel()
    await MongoManager.close()
    cassandra_client.close()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real-Time Financial Fraud Detection & Anomaly Monitoring Platform",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    endpoint = request.url.path
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    
    # Avoid recording /metrics itself in loop
    if endpoint != "/metrics":
        API_REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=str(response.status_code)
        ).inc()
        API_REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    return response


# Register REST Routers
app.include_router(health_router)
app.include_router(transactions_router)
app.include_router(alerts_router)
app.include_router(analytics_router)
app.include_router(simulator_router)
app.include_router(model_info_router)


@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "metrics_url": "/metrics",
        "websocket_url": "/ws/live",
        "active_model_mode": settings.ACTIVE_MODEL_MODE
    }


@app.get("/metrics")
async def prometheus_metrics_endpoint():
    """Exposes standard Prometheus scrape metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
