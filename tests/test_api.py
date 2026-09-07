"""
Integration tests for FastAPI REST Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "docs_url" in data


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert data["model_loaded"] is True


def test_model_info_endpoint():
    response = client.get("/api/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "metrics" in data
    assert "feature_importances" in data


def test_stats_endpoint():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert "fraud_alerts" in data
    assert "fraud_rate_pct" in data


def test_transactions_endpoint():
    response = client.get("/api/transactions?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_fraud_alerts_endpoint():
    response = client.get("/api/fraud-alerts?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_simulator_status():
    response = client.get("/api/simulator/status")
    assert response.status_code == 200
    data = response.json()
    assert "running" in data
    assert "rate" in data
