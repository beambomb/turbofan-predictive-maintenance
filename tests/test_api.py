import pytest
from fastapi.testclient import TestClient
from src.serving.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "active_model" in data


def test_predict_rul_success():
    payload = {
        "engine_id": 42,
        "features": [0.0] * 38
    }
    response = client.post("/predict-rul", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["engine_id"] == 42
    assert 0.0 <= data["predicted_rul"] <= 125.0
    assert data["health_status"] in ["HEALTHY", "WARNING", "CRITICAL"]
    assert "recommended_action" in data
    assert "inference_time_ms" in data


def test_predict_rul_invalid_length():
    payload = {
        "engine_id": 42,
        "features": [1.0, 2.0, 3.0]
    }
    response = client.post("/predict-rul", json=payload)
    assert response.status_code == 400
    assert "Jumlah fitur harus tepat 38 angka" in response.json()["detail"]


def test_get_available_engines():
    response = client.get("/ws-engines")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert 1 in data


def test_live_demo_page():
    response = client.get("/live-demo")
    assert response.status_code == 200
    assert "NASA Turbofan RUL - Live Stream" in response.text
    assert "text/html" in response.headers["content-type"]


def test_websocket_telemetry_stream():
    with client.websocket_connect("/ws/telemetry/1?interval=0.01") as websocket:
        data = websocket.receive_json()
        assert data["engine_id"] == 1
        assert "cycle" in data
        assert "predicted_rul" in data
        assert 0.0 <= data["predicted_rul"] <= 125.0
        assert data["health_status"] in ["HEALTHY", "WARNING", "CRITICAL"]
        assert "sensors" in data
        assert "lpc_temp" in data["sensors"]
