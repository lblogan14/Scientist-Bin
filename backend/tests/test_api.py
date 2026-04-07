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
    data = response.json()
    assert data["experiments"] == []
    assert data["total"] == 0
    assert data["offset"] == 0
    assert data["limit"] == 50


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
    # _run_training positional args from background_tasks.add_task:
    # (experiment_id, objective, data_description, data_file_path,
    #  framework, auto_approve_plan, deep_research,
    #  budget_max_iterations, budget_time_limit_seconds)
    assert call_kwargs[0][5] is True  # auto_approve_plan


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
    assert call_kwargs[0][5] is False  # auto_approve_plan


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


# ---------------------------------------------------------------------------
# Plan review endpoint tests
# ---------------------------------------------------------------------------


def test_submit_plan_review_nonexistent(client):
    """Submitting review for a nonexistent experiment returns 404."""
    resp = client.post(
        "/api/v1/experiments/does-not-exist/review",
        json={"feedback": "approve"},
    )
    assert resp.status_code == 404


def test_submit_plan_review_not_waiting(client):
    """Submitting review when experiment is not waiting returns 409."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test review"},
        )
    exp_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/v1/experiments/{exp_id}/review",
        json={"feedback": "approve"},
    )
    assert resp.status_code == 409
    assert "not waiting" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Filtering and pagination tests
# ---------------------------------------------------------------------------


def _create_experiments(client, objectives: list[tuple[str, str | None]]):
    """Helper to create multiple experiments. Returns list of experiment dicts."""
    exps = []
    for objective, framework in objectives:
        with patch(
            "scientist_bin_backend.api.routes._run_training",
            new_callable=AsyncMock,
        ):
            body: dict = {"objective": objective}
            if framework:
                body["framework_preference"] = framework
            resp = client.post("/api/v1/train", json=body)
        exps.append(resp.json())
    return exps


def test_list_experiments_pagination(client):
    """Verify offset and limit work correctly."""
    _create_experiments(
        client,
        [
            ("Exp A", None),
            ("Exp B", None),
            ("Exp C", None),
        ],
    )

    # Default: all 3
    resp = client.get("/api/v1/experiments")
    data = resp.json()
    assert data["total"] == 3

    # Limit to 2
    resp = client.get("/api/v1/experiments", params={"limit": 2})
    data = resp.json()
    assert len(data["experiments"]) == 2
    assert data["total"] == 3

    # Offset 2
    resp = client.get("/api/v1/experiments", params={"offset": 2, "limit": 10})
    data = resp.json()
    assert len(data["experiments"]) == 1


def test_list_experiments_filter_by_status(client):
    """Filter by experiment status."""
    _create_experiments(client, [("Status test", None)])

    # New experiments are "pending" by default
    resp = client.get("/api/v1/experiments", params={"status": "pending"})
    data = resp.json()
    assert data["total"] >= 1

    resp = client.get("/api/v1/experiments", params={"status": "completed"})
    data = resp.json()
    assert data["total"] == 0


def test_list_experiments_search(client):
    """Search in objective text."""
    _create_experiments(
        client,
        [
            ("Classify iris species", None),
            ("Predict house prices", None),
        ],
    )

    resp = client.get("/api/v1/experiments", params={"search": "iris"})
    data = resp.json()
    assert data["total"] >= 1
    for exp in data["experiments"]:
        assert "iris" in exp["objective"].lower()


# ---------------------------------------------------------------------------
# Artifact download endpoint tests
# ---------------------------------------------------------------------------


def test_download_artifact_nonexistent_experiment(client):
    """Downloading artifact for nonexistent experiment returns 404."""
    resp = client.get("/api/v1/experiments/does-not-exist/artifacts/model")
    assert resp.status_code == 404


def test_download_artifact_unknown_type(client):
    """Downloading an unknown artifact type returns 400."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test artifact"},
        )
    exp_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/experiments/{exp_id}/artifacts/unknown_type")
    assert resp.status_code == 400
    assert "Unknown artifact type" in resp.json()["detail"]


def test_download_artifact_not_found(client):
    """Downloading artifact that doesn't exist on disk returns 404."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test artifact missing"},
        )
    exp_id = create_resp.json()["id"]

    for artifact_type in ["model", "results", "analysis", "summary", "plan", "charts", "journal"]:
        resp = client.get(f"/api/v1/experiments/{exp_id}/artifacts/{artifact_type}")
        assert resp.status_code == 404, f"Expected 404 for {artifact_type}"


def test_download_artifact_success(client, tmp_path):
    """Downloading existing artifacts returns 200 with correct content."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test artifact success"},
        )
    exp_id = create_resp.json()["id"]

    # Create fake artifact files in the outputs directory
    from scientist_bin_backend.api.routes import _OUTPUTS_DIR

    artifacts = {
        "model": (_OUTPUTS_DIR / "models" / f"{exp_id}.joblib", b"fake-model"),
        "results": (_OUTPUTS_DIR / "results" / f"{exp_id}.json", b'{"status":"ok"}'),
        "analysis": (_OUTPUTS_DIR / "results" / f"{exp_id}_analysis.md", b"# Analysis"),
        "summary": (_OUTPUTS_DIR / "results" / f"{exp_id}_summary.md", b"# Summary"),
        "plan": (_OUTPUTS_DIR / "results" / f"{exp_id}_plan.json", b'{"plan":true}'),
        "charts": (_OUTPUTS_DIR / "results" / f"{exp_id}_charts.json", b'{"charts":[]}'),
        "journal": (_OUTPUTS_DIR / "logs" / f"{exp_id}.jsonl", b'{"event":"test"}\n'),
    }

    created_files = []
    try:
        for artifact_type, (path, content) in artifacts.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            created_files.append(path)

            resp = client.get(f"/api/v1/experiments/{exp_id}/artifacts/{artifact_type}")
            assert resp.status_code == 200, (
                f"Expected 200 for {artifact_type}, got {resp.status_code}"
            )
            assert resp.content == content, f"Content mismatch for {artifact_type}"
    finally:
        # Clean up created files
        for path in created_files:
            path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Additional filtering tests
# ---------------------------------------------------------------------------


def test_list_experiments_filter_by_framework(client):
    """Filter by ML framework."""
    _create_experiments(
        client,
        [
            ("Sklearn experiment", "sklearn"),
            ("Another sklearn", "sklearn"),
            ("Pytorch experiment", "pytorch"),
        ],
    )

    resp = client.get("/api/v1/experiments", params={"framework": "sklearn"})
    data = resp.json()
    assert data["total"] >= 2
    for exp in data["experiments"]:
        assert exp["framework"] == "sklearn"

    resp = client.get("/api/v1/experiments", params={"framework": "pytorch"})
    data = resp.json()
    assert data["total"] >= 1
    for exp in data["experiments"]:
        assert exp["framework"] == "pytorch"


def test_list_experiments_offset_beyond_total(client):
    """Offset beyond total results returns empty list."""
    _create_experiments(client, [("Edge case", None)])

    resp = client.get("/api/v1/experiments", params={"offset": 1000, "limit": 10})
    data = resp.json()
    assert data["experiments"] == []
    assert data["total"] >= 1  # Total is unaffected by offset


# ---------------------------------------------------------------------------
# Data file validation tests
# ---------------------------------------------------------------------------


def test_create_train_invalid_file_extension(client, tmp_path):
    """Reject data files with unsupported extensions."""
    bad_file = tmp_path / "data.txt"
    bad_file.write_text("some text")

    with (
        patch(
            "scientist_bin_backend.api.routes._run_training",
            new_callable=AsyncMock,
        ),
        patch(
            "scientist_bin_backend.api.routes._resolve_data_file_path",
            return_value=str(bad_file),
        ),
    ):
        resp = client.post(
            "/api/v1/train",
            json={"objective": "Test bad extension", "data_file_path": "data.txt"},
        )
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


def test_create_train_file_too_large(client, tmp_path):
    """Reject data files exceeding the size limit."""
    import os

    big_file = tmp_path / "huge.csv"
    big_file.write_text("a")  # Create a small file, then mock os.stat

    real_stat = os.stat

    def fake_stat(path, *args, **kwargs):
        result = real_stat(path, *args, **kwargs)
        if str(path) == str(big_file):
            # Return a modified stat result with large size

            return os.stat_result(
                (
                    result.st_mode,
                    result.st_ino,
                    result.st_dev,
                    result.st_nlink,
                    result.st_uid,
                    result.st_gid,
                    600 * 1024 * 1024,  # st_size
                    int(result.st_atime),
                    int(result.st_mtime),
                    int(result.st_ctime),
                )
            )
        return result

    with (
        patch(
            "scientist_bin_backend.api.routes._run_training",
            new_callable=AsyncMock,
        ),
        patch(
            "scientist_bin_backend.api.routes._resolve_data_file_path",
            return_value=str(big_file),
        ),
        patch("os.stat", side_effect=fake_stat),
    ):
        resp = client.post(
            "/api/v1/train",
            json={"objective": "Test oversized file", "data_file_path": "huge.csv"},
        )
    assert resp.status_code == 400
    assert "too large" in resp.json()["detail"]


def test_create_train_valid_csv(client, tmp_path):
    """Accept data files with supported .csv extension."""
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("col1,col2\n1,2\n")

    with (
        patch(
            "scientist_bin_backend.api.routes._run_training",
            new_callable=AsyncMock,
        ),
        patch(
            "scientist_bin_backend.api.routes._resolve_data_file_path",
            return_value=str(csv_file),
        ),
    ):
        resp = client.post(
            "/api/v1/train",
            json={"objective": "Test valid csv file", "data_file_path": "data.csv"},
        )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Path traversal protection tests
# ---------------------------------------------------------------------------


def test_download_artifact_path_traversal(client):
    """Reject experiment IDs that attempt path traversal."""
    # Create a real experiment first, then try traversal on a different endpoint
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Path traversal test"},
        )
    assert create_resp.status_code == 200

    # Attempt path traversal — experiment won't be found in store
    resp = client.get("/api/v1/experiments/../../etc/passwd/artifacts/model")
    assert resp.status_code in (400, 404, 422)


def test_download_artifact_invalid_type(client):
    """Reject unknown artifact types."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test invalid artifact type"},
        )
    exp_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/experiments/{exp_id}/artifacts/badtype")
    assert resp.status_code == 400
    assert "Unknown artifact type" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# best_run_id population tests
# ---------------------------------------------------------------------------


def test_best_run_id_not_set_initially(client):
    """best_run_id is None for a new experiment."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test best_run_id"},
        )
    exp = create_resp.json()
    assert exp["best_run_id"] is None


# ---------------------------------------------------------------------------
# Artifact save warning tests
# ---------------------------------------------------------------------------


def test_artifact_save_failure_surfaces_warnings(client):
    """When artifact saving fails, _warnings is added to the result."""
    from scientist_bin_backend.api.experiments import experiment_store

    # Create an experiment and simulate a completed result with save failure
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test warnings"},
        )
    exp_id = create_resp.json()["id"]

    # Simulate what _run_training does when artifact save fails:
    # it stores _warnings in the result dict
    result_dict = {"framework": "sklearn", "status": "completed"}
    from scientist_bin_backend.api.experiments import ExperimentStatus

    experiment_store.update(
        exp_id,
        status=ExperimentStatus.completed,
        result={**result_dict, "_warnings": ["Artifact save failed: disk full"]},
    )

    resp = client.get(f"/api/v1/experiments/{exp_id}")
    data = resp.json()
    assert data["result"]["_warnings"] == ["Artifact save failed: disk full"]


# ---------------------------------------------------------------------------
# Deep Research training path tests
# ---------------------------------------------------------------------------


def test_create_experiment_deep_research(client):
    """POST /train with deep_research=True should be accepted and passed through."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ) as mock_run:
        resp = client.post(
            "/api/v1/train",
            json={
                "objective": "Classify iris with deep research",
                "deep_research": True,
            },
        )
    assert resp.status_code == 200
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    # _run_training positional args:
    # (experiment_id, objective, data_description, data_file_path,
    #  framework, auto_approve_plan, deep_research,
    #  budget_max_iterations, budget_time_limit_seconds)
    assert call_args[0][6] is True  # deep_research


def test_create_experiment_deep_research_default_false(client):
    """When deep_research is not specified, it defaults to False."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ) as mock_run:
        resp = client.post(
            "/api/v1/train",
            json={"objective": "Normal training"},
        )
    assert resp.status_code == 200
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[0][6] is False  # deep_research


def test_create_experiment_budget_params(client):
    """budget_max_iterations and budget_time_limit_seconds should be passed through."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ) as mock_run:
        resp = client.post(
            "/api/v1/train",
            json={
                "objective": "Deep research with budget",
                "deep_research": True,
                "budget_max_iterations": 5,
                "budget_time_limit_seconds": 3600.0,
            },
        )
    assert resp.status_code == 200
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[0][7] == 5  # budget_max_iterations
    assert call_args[0][8] == 3600.0  # budget_time_limit_seconds


def test_create_experiment_budget_defaults(client):
    """Budget params have correct defaults when not specified."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ) as mock_run:
        resp = client.post(
            "/api/v1/train",
            json={"objective": "Default budget"},
        )
    assert resp.status_code == 200
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[0][7] == 10  # budget_max_iterations default
    assert call_args[0][8] == 14400.0  # budget_time_limit_seconds default


# ---------------------------------------------------------------------------
# Problem type filtering tests
# ---------------------------------------------------------------------------


def test_list_experiments_filter_by_problem_type(client):
    """Filter experiments by problem_type."""
    from scientist_bin_backend.api.experiments import experiment_store

    # Create experiments with different problem types
    exps = _create_experiments(
        client,
        [
            ("Classify flowers", "sklearn"),
            ("Predict prices", "sklearn"),
            ("Cluster customers", "sklearn"),
        ],
    )

    # Set problem_type on each experiment via the store
    experiment_store.update(exps[0]["id"], problem_type="classification")
    experiment_store.update(exps[1]["id"], problem_type="regression")
    experiment_store.update(exps[2]["id"], problem_type="clustering")

    # Filter for classification
    resp = client.get("/api/v1/experiments", params={"problem_type": "classification"})
    data = resp.json()
    assert data["total"] >= 1
    for exp in data["experiments"]:
        assert exp["problem_type"] == "classification"

    # Filter for regression
    resp = client.get("/api/v1/experiments", params={"problem_type": "regression"})
    data = resp.json()
    assert data["total"] >= 1
    for exp in data["experiments"]:
        assert exp["problem_type"] == "regression"

    # Filter for clustering
    resp = client.get("/api/v1/experiments", params={"problem_type": "clustering"})
    data = resp.json()
    assert data["total"] >= 1
    for exp in data["experiments"]:
        assert exp["problem_type"] == "clustering"

    # Non-existent problem type returns empty
    resp = client.get("/api/v1/experiments", params={"problem_type": "anomaly_detection"})
    data = resp.json()
    assert data["total"] == 0


def test_list_experiments_combined_filters(client):
    """Combine problem_type with other filters."""
    from scientist_bin_backend.api.experiments import ExperimentStatus, experiment_store

    exps = _create_experiments(
        client,
        [
            ("Classify iris A", "sklearn"),
            ("Classify iris B", "sklearn"),
        ],
    )

    experiment_store.update(
        exps[0]["id"], problem_type="classification", status=ExperimentStatus.completed
    )
    experiment_store.update(
        exps[1]["id"], problem_type="classification", status=ExperimentStatus.running
    )

    resp = client.get(
        "/api/v1/experiments",
        params={"problem_type": "classification", "status": "completed"},
    )
    data = resp.json()
    assert data["total"] >= 1
    for exp in data["experiments"]:
        assert exp["problem_type"] == "classification"
        assert exp["status"] == "completed"


# ---------------------------------------------------------------------------
# Deploy / Undeploy endpoint tests
# ---------------------------------------------------------------------------


def test_deploy_nonexistent_experiment(client):
    """Deploy for a nonexistent experiment returns 404."""
    resp = client.post("/api/v1/experiments/does-not-exist/deploy")
    assert resp.status_code == 404


def test_deploy_pending_experiment_rejected(client):
    """Only completed experiments can be deployed."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test deploy pending"},
        )
    exp_id = create_resp.json()["id"]

    resp = client.post(f"/api/v1/experiments/{exp_id}/deploy")
    assert resp.status_code == 400
    assert "completed" in resp.json()["detail"].lower()


def test_deploy_and_undeploy_completed_experiment(client):
    """Deploy + undeploy lifecycle for a completed experiment."""
    from scientist_bin_backend.api.experiments import ExperimentStatus, experiment_store

    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test deploy lifecycle"},
        )
    exp_id = create_resp.json()["id"]

    # Mark as completed so deploy will succeed
    experiment_store.update(exp_id, status=ExperimentStatus.completed)

    # Deploy
    deploy_resp = client.post(
        f"/api/v1/experiments/{exp_id}/deploy",
        json={"model_version": "v2.0"},
    )
    assert deploy_resp.status_code == 200
    deploy_data = deploy_resp.json()
    assert deploy_data["status"] == "deployed"
    assert deploy_data["model_version"] == "v2.0"
    assert deploy_data["experiment_id"] == exp_id
    assert "endpoint_url" in deploy_data

    # Get deployment status
    status_resp = client.get(f"/api/v1/experiments/{exp_id}/deployment")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "deployed"

    # Undeploy
    undeploy_resp = client.post(f"/api/v1/experiments/{exp_id}/undeploy")
    assert undeploy_resp.status_code == 200
    assert undeploy_resp.json()["status"] == "not_deployed"

    # Deployment status should now be not_deployed
    status_resp = client.get(f"/api/v1/experiments/{exp_id}/deployment")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "not_deployed"


def test_undeploy_not_deployed(client):
    """Undeploy when not deployed returns 404."""
    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test undeploy not deployed"},
        )
    exp_id = create_resp.json()["id"]

    resp = client.post(f"/api/v1/experiments/{exp_id}/undeploy")
    assert resp.status_code == 404


def test_predict_deployed_model(client):
    """Mock predict endpoint works for deployed models."""
    from scientist_bin_backend.api.experiments import ExperimentStatus, experiment_store

    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test predict"},
        )
    exp_id = create_resp.json()["id"]

    experiment_store.update(exp_id, status=ExperimentStatus.completed)
    client.post(f"/api/v1/experiments/{exp_id}/deploy")

    resp = client.post(f"/api/v1/predict/{exp_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["prediction"] == "mock_prediction_result"
    assert data["model"] == exp_id


def test_predict_not_deployed(client):
    """Predict for a non-deployed model returns 404."""
    resp = client.post("/api/v1/predict/does-not-exist")
    assert resp.status_code == 404


def test_deploy_default_version(client):
    """Deploy without specifying model_version defaults to v1.0."""
    from scientist_bin_backend.api.experiments import ExperimentStatus, experiment_store

    with patch(
        "scientist_bin_backend.api.routes._run_training",
        new_callable=AsyncMock,
    ):
        create_resp = client.post(
            "/api/v1/train",
            json={"objective": "Test default version"},
        )
    exp_id = create_resp.json()["id"]
    experiment_store.update(exp_id, status=ExperimentStatus.completed)

    resp = client.post(f"/api/v1/experiments/{exp_id}/deploy")
    assert resp.status_code == 200
    assert resp.json()["model_version"] == "v1.0"


# ---------------------------------------------------------------------------
# Journal endpoint tests
# ---------------------------------------------------------------------------


def test_get_journal_nonexistent(client):
    """Journal for nonexistent experiment returns 404."""
    resp = client.get("/api/v1/experiments/does-not-exist/journal")
    assert resp.status_code == 404
