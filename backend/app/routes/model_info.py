"""
Model Metadata, Diagnostics, Benchmarking & Model Mode Selection Routes
"""

import os
import json
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from backend.app.models import ModelInfoResponse
from ml.predictor import predictor
from ml.unified_scorer import unified_scorer
from config.settings import settings

router = APIRouter(prefix="/api", tags=["Model Management"])


class ModelModeRequest(BaseModel):
    mode: str = Field(..., description="Selected model mode", pattern="^(SUPERVISED_XGBOOST|SUPERVISED_RANDOM_FOREST|UNSUPERVISED_ISOLATION_FOREST|UNSUPERVISED_AUTOENCODER|ENSEMBLE)$")


@router.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    """Returns trained model performance statistics, feature importances, and metadata."""
    if os.path.exists(settings.MODEL_METADATA_PATH):
        try:
            with open(settings.MODEL_METADATA_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                return ModelInfoResponse(**meta)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading model metadata: {e}")

    if predictor.metadata:
        return ModelInfoResponse(**predictor.metadata)

    raise HTTPException(status_code=404, detail="Model metadata not found. Please train model first.")


@router.get("/model-mode")
async def get_current_model_mode():
    """Returns currently active scoring model mode and ensemble weights."""
    return {
        "active_mode": unified_scorer.mode,
        "available_modes": [
            "SUPERVISED_XGBOOST",
            "SUPERVISED_RANDOM_FOREST",
            "UNSUPERVISED_ISOLATION_FOREST",
            "UNSUPERVISED_AUTOENCODER",
            "ENSEMBLE"
        ],
        "ensemble_weights": {
            "supervised_weight": settings.ENSEMBLE_SUPERVISED_WEIGHT,
            "anomaly_weight": settings.ENSEMBLE_ANOMALY_WEIGHT,
            "behavioral_weight": settings.BEHAVIORAL_RISK_WEIGHT
        }
    }


@router.post("/model-mode")
async def set_model_mode(req: ModelModeRequest):
    """Dynamically switches active scoring architecture."""
    try:
        unified_scorer.set_mode(req.mode)
        settings.ACTIVE_MODEL_MODE = req.mode
        return {
            "status": "success",
            "message": f"Active model mode updated to {req.mode}",
            "active_mode": req.mode
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/model-comparison")
async def get_model_comparison():
    """Returns complete 4-model comparison benchmarks across supervised and unsupervised paradigms."""
    if os.path.exists(settings.MODEL_COMPARISON_PATH):
        try:
            with open(settings.MODEL_COMPARISON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading comparison JSON: {e}")

    # Fallback to computing comparison if file missing
    from ml.model_comparison import run_model_comparison
    return run_model_comparison()
