"""
Fraud Alerts REST API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Path
from pymongo import DESCENDING
from backend.app.database import MongoManager
from backend.app.models import FraudAlertItem, AlertStatusUpdateRequest
from config.settings import settings

router = APIRouter(prefix="/api/fraud-alerts", tags=["Fraud Alerts"])


@router.get("", response_model=List[FraudAlertItem])
async def get_fraud_alerts(
    status: Optional[str] = Query(None, description="Filter by status (NEW, INVESTIGATING, CONFIRMED, DISMISSED)"),
    risk_level: Optional[str] = Query(None, description="Filter by risk tier"),
    limit: int = Query(50, ge=1, le=200)
):
    db = MongoManager.get_db()
    if db is None:
        from backend.app.local_storage import local_store
        return local_store.get_alerts(limit=limit, status=status, risk_level=risk_level)

    query = {}
    if status:
        query["status"] = status.upper()
    if risk_level:
        query["risk_level"] = risk_level.upper()

    coll = db[settings.MONGO_ALERTS_COLLECTION]
    cursor = coll.find(query, {"_id": 0}).sort("created_at", DESCENDING).limit(limit)
    res = await cursor.to_list(length=limit)
    if not res:
        from backend.app.local_storage import local_store
        return local_store.get_alerts(limit=limit, status=status, risk_level=risk_level)
    return res


@router.get("/recent", response_model=List[FraudAlertItem])
async def get_recent_alerts(limit: int = Query(15, ge=1, le=50)):
    db = MongoManager.get_db()
    if db is None:
        from backend.app.local_storage import local_store
        return local_store.get_alerts(limit=limit)
    coll = db[settings.MONGO_ALERTS_COLLECTION]
    cursor = coll.find({}, {"_id": 0}).sort("created_at", DESCENDING).limit(limit)
    res = await cursor.to_list(length=limit)
    if not res:
        from backend.app.local_storage import local_store
        return local_store.get_alerts(limit=limit)
    return res


@router.patch("/{alert_id}/status", response_model=dict)
async def update_alert_status(
    alert_id: str = Path(..., description="The Alert ID to update"),
    body: AlertStatusUpdateRequest = ...
):
    db = MongoManager.get_db()
    from backend.app.local_storage import local_store
    local_store.update_alert_status(alert_id, body.status)

    if db is not None:
        coll = db[settings.MONGO_ALERTS_COLLECTION]
        await coll.update_one(
            {"alert_id": alert_id},
            {"$set": {"status": body.status}}
        )

    return {"message": "Alert status updated successfully", "alert_id": alert_id, "status": body.status}
