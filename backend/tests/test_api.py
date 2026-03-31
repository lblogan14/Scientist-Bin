"""Tests for the REST API endpoints."""

from unittest.mock import AsyncMock, patch


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Scientist-Bin"


def test_list_experiments_empty(client):
    response = client.get("/api/v1/experiments")
    assert response.status_code == 200
    assert response.json() == []


def test_create_and_get_experiment(client):
    # Mock the agent so the background task doesn't actually call the LLM
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Classify iris data", "data_description": "4 features, 3 classes"},
        )
    assert create_resp.status_code == 200
    data = create_resp.json()
    assert data["objective"] == "Classify iris data"
    assert "id" in data

    # Fetch it back
    get_resp = client.get(f"/api/v1/experiments/{data['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == data["id"]


def test_delete_experiment(client):
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test delete"},
        )
    exp_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/experiments/{exp_id}")
    assert del_resp.status_code == 200

    # Should be gone now
    get_resp = client.get(f"/api/v1/experiments/{exp_id}")
    assert get_resp.status_code == 404


def test_get_nonexistent_experiment(client):
    response = client.get("/api/v1/experiments/does-not-exist")
    assert response.status_code == 404


def test_delete_nonexistent_experiment(client):
    response = client.delete("/api/v1/experiments/does-not-exist")
    assert response.status_code == 404
