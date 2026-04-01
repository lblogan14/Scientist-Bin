"""Tests for the REST API endpoints."""

from __future__ import annotations

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


def test_create_experiment_with_auto_approve(client):
    """The auto_approve_plan field should be accepted in the request body."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ) as mock_run:
        create_resp = client.post(
            "/api/v1/train",
            json={
                "objective": "Classify iris",
                "auto_approve_plan": True,
            },
        )
    assert create_resp.status_code == 200
    # Verify auto_approve_plan was passed through to _run_training
    mock_run.assert_called_once()
    call_kwargs = mock_run.call_args
    # _run_training is called with positional args from background_tasks.add_task
    # The last argument is auto_approve_plan
    assert call_kwargs[0][-1] is True


def test_create_experiment_auto_approve_default_false(client):
    """When auto_approve_plan is not specified, it defaults to False."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ) as mock_run:
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Classify iris"},
        )
    assert create_resp.status_code == 200
    mock_run.assert_called_once()
    call_kwargs = mock_run.call_args
    assert call_kwargs[0][-1] is False


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


# ---------------------------------------------------------------------------
# Plan endpoint tests
# ---------------------------------------------------------------------------


def test_get_plan_nonexistent(client):
    response = client.get("/api/v1/experiments/does-not-exist/plan")
    assert response.status_code == 404


def test_get_plan_empty(client):
    """Plan is None initially for a new experiment."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test plan"},
        )
    exp_id = create_resp.json()["id"]
    resp = client.get(f"/api/v1/experiments/{exp_id}/plan")
    assert resp.status_code == 200
    assert resp.json() == {"execution_plan": None}


# ---------------------------------------------------------------------------
# Analysis endpoint tests
# ---------------------------------------------------------------------------


def test_get_analysis_nonexistent(client):
    response = client.get("/api/v1/experiments/does-not-exist/analysis")
    assert response.status_code == 404


def test_get_analysis_empty(client):
    """Analysis report and split paths are None initially."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test analysis"},
        )
    exp_id = create_resp.json()["id"]
    resp = client.get(f"/api/v1/experiments/{exp_id}/analysis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["analysis_report"] is None
    assert data["split_data_paths"] is None


# ---------------------------------------------------------------------------
# Summary endpoint tests
# ---------------------------------------------------------------------------


def test_get_summary_nonexistent(client):
    response = client.get("/api/v1/experiments/does-not-exist/summary")
    assert response.status_code == 404


def test_get_summary_empty(client):
    """Summary report is None initially."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test summary"},
        )
    exp_id = create_resp.json()["id"]
    resp = client.get(f"/api/v1/experiments/{exp_id}/summary")
    assert resp.status_code == 200
    assert resp.json() == {"summary_report": None}
