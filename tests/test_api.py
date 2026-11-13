from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["meta"]["waterbodies"] > 1000


def test_search_named_lake():
    response = client.get("/api/search", params={"q": "Granby"})
    assert response.status_code == 200
    names = [item["name"] for item in response.json()["items"]]
    assert names, "expected Granby matches"
    assert names[0] == "Lake Granby"


def test_bbox_and_filters():
    response = client.get(
        "/api/waterbodies",
        params={"bbox": "-106.2,39.9,-105.5,40.4", "named_only": True, "limit": 10},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert len(body["items"]) <= 10


def test_detail_has_observation_classes():
    search = client.get("/api/search", params={"q": "Green Lake Number 1"}).json()["items"]
    assert search
    detail = client.get(f"/api/waterbodies/{search[0]['id']}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["observation_classes"]["field_measurement"] is False
    assert "timeseries" in body
    assert body["prediction"]["model_version"]
