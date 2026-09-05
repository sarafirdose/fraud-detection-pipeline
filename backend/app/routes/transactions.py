"""
Transactions REST API Routes
"""

from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from pymongo import DESCENDING
from backend.app.database import MongoManager
from backend.app.models import TransactionBase, TransactionResponse
from config.settings import settings

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionResponse)
async def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None, description="Filter by transaction type"),
    risk_level: Optional[str] = Query(None, description="Filter by risk tier (LOW, MEDIUM, HIGH, CRITICAL)"),
    is_fraud: Optional[bool] = Query(None, description="Filter by fraud classification"),
    min_amount: Optional[float] = Query(None, ge=0),
    max_amount: Optional[float] = Query(None, ge=0),
    search: Optional[str] = Query(None, description="Search transaction ID or account")
):
    db = MongoManager.get_db()
    if db is None:
        from backend.app.local_storage import local_store
        filters = {}
        if type: filters["type"] = type.upper()
        if risk_level: filters["risk_level"] = risk_level.upper()
        if is_fraud is not None: filters["is_fraud"] = is_fraud
        if min_amount is not None: filters["min_amount"] = min_amount
        if max_amount is not None: filters["max_amount"] = max_amount
        if search: filters["search"] = search
        items, total = local_store.get_transactions(skip=(page - 1) * page_size, limit=page_size, filters=filters)
        return TransactionResponse(total=total, page=page, page_size=page_size, items=items)

    query = {}
    if type:
        query["type"] = type.upper()
    if risk_level:
        query["risk_level"] = risk_level.upper()
    if is_fraud is not None:
        query["is_fraud"] = is_fraud
    if min_amount is not None or max_amount is not None:
        query["amount"] = {}
        if min_amount is not None:
            query["amount"]["$gte"] = min_amount
        if max_amount is not None:
            query["amount"]["$lte"] = max_amount
    if search:
        query["$or"] = [
            {"transaction_id": {"$regex": search, "$options": "i"}},
            {"nameOrigMasked": {"$regex": search, "$options": "i"}},
            {"nameDestMasked": {"$regex": search, "$options": "i"}}
        ]

    coll = db[settings.MONGO_TRANSACTIONS_COLLECTION]
    total = await coll.count_documents(query)
    cursor = coll.find(query, {"_id": 0}).sort("evaluated_at", DESCENDING).skip((page - 1) * page_size).limit(page_size)
    items = await cursor.to_list(length=page_size)

    return TransactionResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get("/recent", response_model=List[TransactionBase])
async def get_recent_transactions(limit: int = Query(30, ge=1, le=100)):
    db = MongoManager.get_db()
    if db is None:
        from backend.app.local_storage import local_store
        return local_store.get_recent_transactions(limit=limit)
    coll = db[settings.MONGO_TRANSACTIONS_COLLECTION]
    cursor = coll.find({}, {"_id": 0}).sort("evaluated_at", DESCENDING).limit(limit)
    res = await cursor.to_list(length=limit)
    if not res:
        from backend.app.local_storage import local_store
        return local_store.get_recent_transactions(limit=limit)
    return res


@router.get("/{transaction_id}", response_model=TransactionBase)
async def get_transaction_by_id(transaction_id: str):
    db = MongoManager.get_db()
    if db is None:
        from backend.app.local_storage import local_store
        doc = local_store.get_transaction_by_id(transaction_id)
        if doc: return doc
        raise HTTPException(status_code=404, detail="Transaction not found")
    coll = db[settings.MONGO_TRANSACTIONS_COLLECTION]
    doc = await coll.find_one({"transaction_id": transaction_id}, {"_id": 0})
    if not doc:
        from backend.app.local_storage import local_store
        doc = local_store.get_transaction_by_id(transaction_id)
        if doc: return doc
        raise HTTPException(status_code=404, detail="Transaction not found")
    return doc
