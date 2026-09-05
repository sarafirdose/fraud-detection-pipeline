"""
Analytics, KPI Stats, and Time-Series Aggregations (Resilient with Local Store)
"""

import time
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter
from backend.app.database import MongoManager
from backend.app.models import KPISummary, DistributionItem
from backend.app.local_storage import local_store
from config.settings import settings

router = APIRouter(prefix="/api", tags=["Analytics"])


@router.get("/stats", response_model=KPISummary)
async def get_kpi_stats():
    """Calculates top-level KPI metrics from actual MongoDB data or local store."""
    db = MongoManager.get_db()
    if db is not None:
        try:
            tx_coll = db[settings.MONGO_TRANSACTIONS_COLLECTION]
            total_tx = await tx_coll.count_documents({})
            if total_tx > 0:
                fraud_tx_count = await tx_coll.count_documents({"is_fraud": True})
                high_critical_count = await tx_coll.count_documents({"risk_level": {"$in": ["HIGH", "CRITICAL"]}})
                normal_tx_count = total_tx - fraud_tx_count
                fraud_rate = round((fraud_tx_count / total_tx) * 100.0, 2)

                pipeline = [
                    {
                        "$group": {
                            "_id": None,
                            "total_amount": {"$sum": "$amount"},
                            "fraud_amount": {
                                "$sum": {
                                    "$cond": [{"$eq": ["$is_fraud", True]}, "$amount", 0.0]
                                }
                            },
                            "avg_latency": {"$avg": "$processing_latency_ms"}
                        }
                    }
                ]
                agg_res = await tx_coll.aggregate(pipeline).to_list(1)
                total_amt = round(agg_res[0].get("total_amount", 0.0), 2) if agg_res else 0.0
                fraud_amt = round(agg_res[0].get("fraud_amount", 0.0), 2) if agg_res else 0.0
                avg_lat = round(agg_res[0].get("avg_latency", 0.0) or 0.0, 2) if agg_res else 0.0

                return KPISummary(
                    total_transactions=total_tx,
                    fraud_alerts=fraud_tx_count,
                    fraud_rate_pct=fraud_rate,
                    high_critical_alerts=high_critical_count,
                    avg_latency_ms=avg_lat,
                    normal_transactions=normal_tx_count,
                    total_amount_processed=total_amt,
                    fraud_amount_detected=fraud_amt
                )
        except Exception:
            pass

    return KPISummary(**local_store.get_stats())


@router.get("/analytics/timeseries")
async def get_timeseries_analytics():
    """Returns recent transaction volume and fraud rate over time for charts."""
    docs = []
    db = MongoManager.get_db()
    if db is not None:
        try:
            tx_coll = db[settings.MONGO_TRANSACTIONS_COLLECTION]
            cursor = tx_coll.find(
                {},
                {"_id": 0, "evaluated_at": 1, "is_fraud": 1, "risk_score": 1, "amount": 1}
            ).sort("evaluated_at", -1).limit(150)
            docs = await cursor.to_list(150)
        except Exception:
            docs = []

    if not docs:
        docs = local_store.get_recent_transactions(150)

    if not docs:
        return []

    docs = list(reversed(docs))
    bucket_size = max(1, len(docs) // 15)
    points = []

    for i in range(0, len(docs), bucket_size):
        chunk = docs[i : i + bucket_size]
        if not chunk:
            continue
        
        t_epoch = chunk[-1].get("evaluated_at") or time.time()
        t_str = datetime.fromtimestamp(t_epoch).strftime("%H:%M:%S")
        total_count = len(chunk)
        fraud_count = sum(1 for d in chunk if d.get("is_fraud"))
        avg_risk = round(sum(d.get("risk_score", 0.0) for d in chunk) / total_count, 1)
        fraud_rate = round((fraud_count / total_count) * 100.0, 1)
        total_amount = round(sum(d.get("amount", 0.0) for d in chunk), 2)

        points.append({
            "timestamp": t_str,
            "epoch": t_epoch,
            "tx_count": total_count,
            "fraud_count": fraud_count,
            "fraud_rate": fraud_rate,
            "avg_risk": avg_risk,
            "volume_usd": total_amount
        })

    return points


@router.get("/analytics/distributions")
async def get_distributions():
    """Aggregates distribution metrics for charts."""
    tx_list = []
    db = MongoManager.get_db()
    if db is not None:
        try:
            tx_coll = db[settings.MONGO_TRANSACTIONS_COLLECTION]
            total_tx = await tx_coll.count_documents({})
            if total_tx > 0:
                risk_res = await tx_coll.aggregate([{"$group": {"_id": "$risk_level", "count": {"$sum": 1}}}]).to_list(10)
                type_res = await tx_coll.aggregate([{"$group": {"_id": "$type", "count": {"$sum": 1}, "fraud_count": {"$sum": {"$cond": ["$is_fraud", 1, 0]}}}}]).to_list(10)
                fraud_count = await tx_coll.count_documents({"is_fraud": True})
                normal_count = total_tx - fraud_count

                risk_dist = [{"name": r["_id"] or "UNKNOWN", "value": r["count"], "percentage": round((r["count"] / total_tx) * 100.0, 1)} for r in risk_res]
                order_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
                risk_dist.sort(key=lambda x: order_map.get(x["name"], 5))

                type_dist = [{"name": t["_id"] or "OTHER", "value": t["count"], "fraud_count": t.get("fraud_count", 0), "percentage": round((t["count"] / total_tx) * 100.0, 1)} for t in type_res]

                fraud_vs_normal = [
                    {"name": "Normal", "value": normal_count, "percentage": round((normal_count / total_tx) * 100.0, 1), "color": "#10B981"},
                    {"name": "Fraud", "value": fraud_count, "percentage": round((fraud_count / total_tx) * 100.0, 1), "color": "#EF4444"}
                ]

                return {
                    "risk_distribution": risk_dist,
                    "type_distribution": type_dist,
                    "fraud_vs_normal": fraud_vs_normal
                }
        except Exception:
            pass

    # Local Store aggregation fallback
    tx_list = local_store.get_recent_transactions(1000)
    total_tx = len(tx_list)
    if total_tx == 0:
        return {
            "risk_distribution": [
                {"name": "LOW", "value": 0, "percentage": 0.0},
                {"name": "MEDIUM", "value": 0, "percentage": 0.0},
                {"name": "HIGH", "value": 0, "percentage": 0.0},
                {"name": "CRITICAL", "value": 0, "percentage": 0.0}
            ],
            "type_distribution": [],
            "fraud_vs_normal": [
                {"name": "Normal", "value": 1, "percentage": 100.0, "color": "#10B981"},
                {"name": "Fraud", "value": 0, "percentage": 0.0, "color": "#EF4444"}
            ]
        }

    # Group risks
    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    type_counts = {}
    type_fraud_counts = {}
    fraud_count = 0

    for t in tx_list:
        r = t.get("risk_level", "LOW")
        risk_counts[r] = risk_counts.get(r, 0) + 1
        tp = t.get("type", "PAYMENT")
        type_counts[tp] = type_counts.get(tp, 0) + 1
        if t.get("is_fraud"):
            fraud_count += 1
            type_fraud_counts[tp] = type_fraud_counts.get(tp, 0) + 1

    risk_dist = [
        {"name": k, "value": v, "percentage": round((v / total_tx) * 100.0, 1)}
        for k, v in risk_counts.items()
    ]
    type_dist = [
        {"name": k, "value": v, "fraud_count": type_fraud_counts.get(k, 0), "percentage": round((v / total_tx) * 100.0, 1)}
        for k, v in type_counts.items()
    ]
    normal_count = total_tx - fraud_count

    fraud_vs_normal = [
        {"name": "Normal", "value": normal_count, "percentage": round((normal_count / total_tx) * 100.0, 1), "color": "#10B981"},
        {"name": "Fraud", "value": fraud_count, "percentage": round((fraud_count / total_tx) * 100.0, 1), "color": "#EF4444"}
    ]

    return {
        "risk_distribution": risk_dist,
        "type_distribution": type_dist,
        "fraud_vs_normal": fraud_vs_normal
    }
