"""
Simulation and Dynamic Stream Control Routes (Instant Push & Resilient)
"""

import threading
import logging
from fastapi import APIRouter, HTTPException
from backend.app.models import SimulatorControlRequest
from backend.app.websocket import ws_manager
from producer.producer import producer_service
from config.settings import settings

logger = logging.getLogger("simulator_routes")
router = APIRouter(prefix="/api/simulator", tags=["Simulator"])

_producer_thread: threading.Thread = None


@router.get("/status")
async def get_simulator_status():
    return {
        "running": producer_service.running,
        "paused": producer_service.paused,
        "rate": producer_service.rate,
        "total_sent": producer_service.total_sent,
        "current_index": producer_service.current_index,
        "target_topic": settings.KAFKA_TRANSACTIONS_TOPIC,
        "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS
    }


@router.post("/control")
async def control_simulator(req: SimulatorControlRequest):
    global _producer_thread

    action = req.action.lower()

    if action == "start":
        if req.rate:
            producer_service.set_rate(req.rate)
        if not producer_service.running:
            _producer_thread = threading.Thread(target=producer_service.run, daemon=True)
            _producer_thread.start()
            return {"message": "Producer streaming started", "rate": producer_service.rate, "running": True}
        else:
            if producer_service.paused:
                producer_service.resume()
            return {"message": "Producer already running", "running": True}

    elif action == "stop":
        producer_service.stop()
        return {"message": "Producer stopped", "running": False}

    elif action == "pause":
        producer_service.pause()
        return {"message": "Producer paused", "paused": True}

    elif action == "resume":
        producer_service.resume()
        return {"message": "Producer resumed", "paused": False}

    elif action == "set_rate":
        if req.rate:
            producer_service.set_rate(req.rate)
            return {"message": f"Rate updated to {producer_service.rate} tx/sec", "rate": producer_service.rate}
        raise HTTPException(status_code=400, detail="Rate value required")

    elif action == "inject_fraud":
        try:
            demo_tx = producer_service.send_demo_fraud(
                tx_type=req.fraud_type or "TRANSFER",
                amount=req.amount or 650000.0,
                drain_account=req.drain_account if req.drain_account is not None else True
            )
            # Immediate push to WebSocket clients
            if isinstance(demo_tx, dict):
                await ws_manager.broadcast("transaction", demo_tx)
                if demo_tx.get("is_fraud") or demo_tx.get("risk_level") in ["HIGH", "CRITICAL"]:
                    alert_payload = {
                        "alert_id": f"ALT-{demo_tx.get('transaction_id')}",
                        "transaction_id": demo_tx.get("transaction_id"),
                        "amount": demo_tx.get("amount"),
                        "type": demo_tx.get("type"),
                        "nameOrigMasked": demo_tx.get("nameOrigMasked"),
                        "nameDestMasked": demo_tx.get("nameDestMasked"),
                        "risk_score": demo_tx.get("risk_score"),
                        "risk_level": demo_tx.get("risk_level"),
                        "risk_factors": demo_tx.get("risk_factors", []),
                        "is_demo": True,
                        "status": "NEW",
                        "created_at": demo_tx.get("evaluated_at")
                    }
                    await ws_manager.broadcast("alert", alert_payload)

            return {
                "message": "Demo fraud transaction injected into stream",
                "transaction": demo_tx
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to inject demo fraud: {str(e)}")

    raise HTTPException(status_code=400, detail=f"Unknown action: {action}")


@router.post("/inject-fraud")
async def inject_fraud_direct(
    tx_type: str = "TRANSFER",
    amount: float = 650000.0,
    drain_account: bool = True
):
    """Direct convenience endpoint to inject demo fraud into the stream."""
    try:
        demo_tx = producer_service.send_demo_fraud(
            tx_type=tx_type,
            amount=amount,
            drain_account=drain_account
        )
        if isinstance(demo_tx, dict):
            await ws_manager.broadcast("transaction", demo_tx)
            if demo_tx.get("is_fraud") or demo_tx.get("risk_level") in ["HIGH", "CRITICAL"]:
                alert_payload = {
                    "alert_id": f"ALT-{demo_tx.get('transaction_id')}",
                    "transaction_id": demo_tx.get("transaction_id"),
                    "amount": demo_tx.get("amount"),
                    "type": demo_tx.get("type"),
                    "nameOrigMasked": demo_tx.get("nameOrigMasked"),
                    "nameDestMasked": demo_tx.get("nameDestMasked"),
                    "risk_score": demo_tx.get("risk_score"),
                    "risk_level": demo_tx.get("risk_level"),
                    "risk_factors": demo_tx.get("risk_factors", []),
                    "is_demo": True,
                    "status": "NEW",
                    "created_at": demo_tx.get("evaluated_at")
                }
                await ws_manager.broadcast("alert", alert_payload)

        return {
            "status": "success",
            "message": "Suspicious transaction sent through scoring pipeline",
            "transaction": demo_tx
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to inject demo fraud: {str(e)}")
