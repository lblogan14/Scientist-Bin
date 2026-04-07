"""Contract tests validating backend schemas match frontend TypeScript interfaces.

These tests ensure that the JSON produced by backend Pydantic models contains
all the fields that the frontend TypeScript types expect, preventing silent
contract breakage when either side evolves independently.
"""

from __future__ import annotations

from datetime import UTC, datetime

from scientist_bin_backend.agents.central.schemas import AgentResponse
from scientist_bin_backend.api.experiments import (
    Experiment,
    ExperimentPhase,
    ExperimentStatus,
    Framework,
    MetricPoint,
    Run,
)
from scientist_bin_backend.api.routes import TrainRequestBody

# ---------------------------------------------------------------------------
# Experiment model contract
# ---------------------------------------------------------------------------


class TestExperimentContract:
    """Verify Experiment.model_dump() produces all fields the frontend expects."""

    def test_experiment_json_has_all_expected_fields(self):
        """Every field in the frontend Experiment interface must be present."""
        exp = Experiment(id="test-001", objective="Classify iris species")
        data = exp.model_dump(mode="json")

        # All fields from frontend/src/types/api.ts :: Experiment interface
        expected_fields = [
            "id",
            "objective",
            "data_description",
            "data_file_path",
            "framework",
            "status",
            "phase",
            "runs",
            "best_run_id",
            "iteration_count",
            "progress_events",
            "result",
            "execution_plan",
            "analysis_report",
            "summary_report",
            "split_data_paths",
            "problem_type",
            "created_at",
            "updated_at",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field '{field}' in Experiment JSON"

    def test_experiment_default_values(self):
        """Verify sensible defaults match what the frontend expects."""
        exp = Experiment(id="test-002", objective="Test defaults")
        data = exp.model_dump(mode="json")

        assert data["data_description"] == ""
        assert data["data_file_path"] is None
        assert data["framework"] is None
        assert data["status"] == "pending"
        assert data["phase"] is None
        assert data["runs"] == []
        assert data["best_run_id"] is None
        assert data["iteration_count"] == 0
        assert data["progress_events"] == []
        assert data["result"] is None
        assert data["execution_plan"] is None
        assert data["analysis_report"] is None
        assert data["summary_report"] is None
        assert data["split_data_paths"] is None
        assert data["problem_type"] is None

    def test_experiment_status_values_match_frontend(self):
        """All ExperimentStatus values match the frontend union type."""
        frontend_statuses = {"pending", "running", "completed", "failed"}
        backend_statuses = {s.value for s in ExperimentStatus}
        assert backend_statuses == frontend_statuses

    def test_experiment_phase_values_match_frontend(self):
        """All ExperimentPhase values match the frontend union type."""
        frontend_phases = {
            "initializing",
            "classify",
            "eda",
            "planning",
            "plan_review",
            "data_analysis",
            "execution",
            "analysis",
            "summarizing",
            "done",
            "error",
        }
        backend_phases = {p.value for p in ExperimentPhase}
        assert backend_phases == frontend_phases

    def test_framework_values_match_frontend(self):
        """All Framework values match the frontend union type."""
        frontend_frameworks = {
            "sklearn", "flaml", "pytorch", "tensorflow", "transformers", "diffusers",
        }
        backend_frameworks = {f.value for f in Framework}
        assert backend_frameworks == frontend_frameworks

    def test_experiment_with_populated_fields(self):
        """Verify JSON structure when all fields are populated."""
        run = Run(
            id="run-001",
            experiment_id="exp-001",
            algorithm="RandomForest",
            hyperparameters={"n_estimators": 100},
            final_metrics={"accuracy": 0.95, "f1_score": 0.93},
            status="completed",
            code="import sklearn",
            stdout="Training complete",
            stderr="",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            wall_time_seconds=12.5,
        )
        exp = Experiment(
            id="exp-001",
            objective="Classify iris",
            data_description="4 features, 3 classes",
            data_file_path="/data/iris.csv",
            framework="sklearn",
            status=ExperimentStatus.completed,
            phase=ExperimentPhase.done,
            runs=[run],
            best_run_id="run-001",
            iteration_count=3,
            problem_type="classification",
            execution_plan={"approach_summary": "Try multiple classifiers"},
            analysis_report="# Analysis\nData looks clean.",
            summary_report="# Summary\nRandom Forest won.",
            split_data_paths={"train": "/data/train.csv", "val": "/data/val.csv"},
            result={"framework": "sklearn", "status": "completed"},
        )
        data = exp.model_dump(mode="json")

        assert data["framework"] == "sklearn"
        assert data["status"] == "completed"
        assert data["phase"] == "done"
        assert len(data["runs"]) == 1
        assert data["runs"][0]["algorithm"] == "RandomForest"
        assert data["problem_type"] == "classification"
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)


# ---------------------------------------------------------------------------
# Run model contract
# ---------------------------------------------------------------------------


class TestRunContract:
    """Verify Run.model_dump() matches the frontend Run interface."""

    def test_run_json_has_all_expected_fields(self):
        """Every field in the frontend Run interface must be present."""
        run = Run(id="run-001", experiment_id="exp-001")
        data = run.model_dump(mode="json")

        expected_fields = [
            "id",
            "experiment_id",
            "algorithm",
            "hyperparameters",
            "metrics",
            "final_metrics",
            "status",
            "code",
            "stdout",
            "stderr",
            "started_at",
            "completed_at",
            "wall_time_seconds",
            "artifacts",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field '{field}' in Run JSON"

    def test_run_status_values(self):
        """Run status accepts all frontend RunStatus values."""
        frontend_statuses = {"pending", "running", "completed", "failed", "timeout"}
        for status in frontend_statuses:
            run = Run(id="r", experiment_id="e", status=status)
            assert run.status == status


# ---------------------------------------------------------------------------
# MetricPoint contract
# ---------------------------------------------------------------------------


class TestMetricPointContract:
    """Verify MetricPoint matches the frontend MetricPoint interface."""

    def test_metric_point_fields(self):
        mp = MetricPoint(name="accuracy", value=0.95, step=1)
        data = mp.model_dump(mode="json")

        assert "name" in data
        assert "value" in data
        assert "step" in data
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)


# ---------------------------------------------------------------------------
# TrainRequestBody contract
# ---------------------------------------------------------------------------


class TestTrainRequestBodyContract:
    """Verify TrainRequestBody matches the frontend TrainRequest interface."""

    def test_train_request_has_all_expected_fields(self):
        """Every field in the frontend TrainRequest interface must be accepted."""
        body = TrainRequestBody(
            objective="Classify iris",
            data_description="4 features",
            data_file_path="/data/iris.csv",
            framework_preference="sklearn",
            auto_approve_plan=True,
            deep_research=True,
            budget_max_iterations=5,
            budget_time_limit_seconds=3600.0,
        )
        data = body.model_dump()

        expected_fields = [
            "objective",
            "data_description",
            "data_file_path",
            "framework_preference",
            "auto_approve_plan",
            "deep_research",
            "budget_max_iterations",
            "budget_time_limit_seconds",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field '{field}' in TrainRequestBody"

    def test_train_request_defaults(self):
        """Default values match what the frontend sends when fields are omitted."""
        body = TrainRequestBody(objective="Test")
        data = body.model_dump()

        assert data["data_description"] == ""
        assert data["data_file_path"] is None
        assert data["framework_preference"] is None
        assert data["auto_approve_plan"] is False
        assert data["deep_research"] is False
        assert data["budget_max_iterations"] == 10
        assert data["budget_time_limit_seconds"] == 14400.0

    def test_train_request_rejects_empty_objective(self):
        """Objective must be at least 1 character."""
        from pydantic import ValidationError

        try:
            TrainRequestBody(objective="")
            raise AssertionError("Should have raised ValidationError")
        except ValidationError:
            pass


# ---------------------------------------------------------------------------
# AgentResponse / ExperimentResult contract
# ---------------------------------------------------------------------------


class TestExperimentResultContract:
    """Verify AgentResponse matches the frontend ExperimentResult interface."""

    def test_agent_response_has_all_expected_fields(self):
        """Every field in the frontend ExperimentResult interface must be present."""
        resp = AgentResponse(framework="sklearn")
        data = resp.model_dump()

        # Fields from frontend/src/types/api.ts :: ExperimentResult interface
        expected_fields = [
            "framework",
            "plan",
            "plan_markdown",
            "generated_code",
            "evaluation_results",
            "experiment_history",
            "data_profile",
            "problem_type",
            "iterations",
            "analysis_report",
            "summary_report",
            "best_model",
            "best_hyperparameters",
            "test_metrics",
            "test_diagnostics",
            "selection_reasoning",
            "report_sections",
            "status",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field '{field}' in AgentResponse"

    def test_agent_response_defaults(self):
        resp = AgentResponse(framework="sklearn")
        data = resp.model_dump()

        assert data["framework"] == "sklearn"
        assert data["plan"] is None
        assert data["plan_markdown"] is None
        assert data["generated_code"] is None
        assert data["evaluation_results"] is None
        assert data["experiment_history"] == []
        assert data["data_profile"] is None
        assert data["problem_type"] is None
        assert data["iterations"] == 0
        assert data["analysis_report"] is None
        assert data["summary_report"] is None
        assert data["best_model"] is None
        assert data["best_hyperparameters"] is None
        assert data["test_metrics"] is None
        assert data["test_diagnostics"] is None
        assert data["selection_reasoning"] is None
        assert data["report_sections"] is None
        assert data["status"] == "completed"

    def test_agent_response_with_experiment_history(self):
        """Verify experiment_history records can include enriched fields."""
        record = {
            "iteration": 1,
            "algorithm": "RandomForestClassifier",
            "hyperparameters": {"n_estimators": 100},
            "metrics": {"accuracy": 0.95, "f1_score": 0.93},
            "training_time_seconds": 2.5,
            "timestamp": datetime.now(UTC).isoformat(),
            # Enriched fields (classification)
            "cv_fold_scores": {"accuracy": [0.93, 0.95, 0.94, 0.96, 0.92]},
            "cv_results_top_n": [
                {"params": {"n_estimators": 100}, "mean_score": 0.94, "std_score": 0.01, "rank": 1}
            ],
            "feature_importances": [
                {"feature": "petal_length", "importance": 0.45},
                {"feature": "petal_width", "importance": 0.35},
            ],
            "confusion_matrix": {
                "labels": ["setosa", "versicolor", "virginica"],
                "matrix": [[15, 0, 0], [0, 14, 1], [0, 2, 13]],
            },
            # Regression enriched fields
            "residual_stats": {
                "mean_residual": 0.01,
                "std_residual": 0.5,
                "max_abs_residual": 2.1,
                "residual_percentiles": {"25": -0.3, "50": 0.0, "75": 0.3},
            },
            "actual_vs_predicted": [
                {"actual": 10.0, "predicted": 9.8},
                {"actual": 20.0, "predicted": 20.5},
            ],
            "coefficients": [
                {"feature": "area", "coefficient": 1.5},
                {"feature": "rooms", "coefficient": 0.8},
            ],
            "learning_curve": [
                {"train_size": 100, "train_score": 0.9, "val_score": 0.85},
                {"train_size": 200, "train_score": 0.92, "val_score": 0.88},
            ],
            # Clustering enriched fields
            "cluster_scatter": [
                {"x": 1.0, "y": 2.0, "cluster": 0},
                {"x": 3.0, "y": 4.0, "cluster": 1},
            ],
            "elbow_data": [
                {"k": 2, "inertia": 100.0},
                {"k": 3, "inertia": 60.0},
            ],
            "cluster_sizes": [50, 30, 20],
            "n_clusters": 3,
            "silhouette_per_sample": [
                {"sample_index": 0, "score": 0.8, "cluster": 0},
                {"sample_index": 1, "score": 0.6, "cluster": 1},
            ],
            "cluster_profiles": [
                {"cluster_id": 0, "size": 50, "centroid": {"feature_a": 1.5, "feature_b": 2.3}},
            ],
        }

        resp = AgentResponse(
            framework="sklearn",
            experiment_history=[record],
        )
        data = resp.model_dump()

        assert len(data["experiment_history"]) == 1
        rec = data["experiment_history"][0]

        # Core fields
        assert rec["iteration"] == 1
        assert rec["algorithm"] == "RandomForestClassifier"
        assert "metrics" in rec
        assert "hyperparameters" in rec
        assert "training_time_seconds" in rec
        assert "timestamp" in rec

        # Classification enriched
        assert "cv_fold_scores" in rec
        assert "cv_results_top_n" in rec
        assert "feature_importances" in rec
        assert "confusion_matrix" in rec

        # Regression enriched
        assert "residual_stats" in rec
        assert "actual_vs_predicted" in rec
        assert "coefficients" in rec
        assert "learning_curve" in rec

        # Clustering enriched
        assert "cluster_scatter" in rec
        assert "elbow_data" in rec
        assert "cluster_sizes" in rec
        assert "n_clusters" in rec
        assert "silhouette_per_sample" in rec
        assert "cluster_profiles" in rec

    def test_agent_response_with_report_sections(self):
        """Verify report_sections matches the frontend SummaryReportSections interface."""
        sections = {
            "title": "Iris Classification Report",
            "executive_summary": "Best model: RandomForest with 95% accuracy.",
            "dataset_overview": "150 samples, 4 features.",
            "methodology": "5-fold cross-validation.",
            "model_comparison_table": "| Model | Accuracy | ...",
            "cv_stability_analysis": "Low variance across folds.",
            "best_model_analysis": "RandomForest generalizes well.",
            "feature_importance_analysis": "Petal length most important.",
            "hyperparameter_analysis": "n_estimators=100 optimal.",
            "error_analysis": "Misclassifications mainly between versicolor/virginica.",
            "conclusions": "Achieves strong performance.",
            "recommendations": ["Try gradient boosting", "Collect more data"],
            "reproducibility_notes": "Random seed 42.",
            "chart_data": {
                "model_comparison": [{"algorithm": "RF", "accuracy": 0.95}],
                "cv_fold_scores": {
                    "RF": {"accuracy": {"scores": [0.93, 0.95], "mean": 0.94}},
                },
                "feature_importances": {
                    "algorithm": "RF",
                    "features": [{"feature": "petal_length", "importance": 0.45}],
                },
                "confusion_matrices": {
                    "RF": {"labels": ["a", "b"], "matrix": [[10, 1], [2, 12]]},
                },
                "training_times": [{"algorithm": "RF", "time_seconds": 2.0}],
                "hyperparam_search": {
                    "RF": [{"params": {}, "mean_score": 0.94, "std_score": 0.01, "rank": 1}],
                },
                "residual_stats": {
                    "RF": {
                        "mean_residual": 0.0,
                        "std_residual": 0.5,
                        "max_abs_residual": 2.0,
                        "residual_percentiles": {"50": 0.0},
                    },
                },
                "cluster_scatter": [{"x": 1.0, "y": 2.0, "cluster": 0}],
                "elbow_curve": [{"k": 2, "inertia": 100.0}],
                "cluster_profiles": [
                    {"cluster_id": 0, "size": 50, "centroid": {"a": 1.5}},
                ],
                "silhouette_data": [{"sample_index": 0, "score": 0.8, "cluster": 0}],
                "actual_vs_predicted": [{"actual": 10.0, "predicted": 9.8}],
                "coefficients": [{"feature": "area", "coefficient": 1.5}],
                "learning_curve": [
                    {"train_size": 100, "train_score": 0.9, "val_score": 0.85},
                ],
            },
        }

        resp = AgentResponse(framework="sklearn", report_sections=sections)
        data = resp.model_dump()

        assert data["report_sections"] is not None
        rs = data["report_sections"]

        # All SummaryReportSections fields
        for field in [
            "title",
            "executive_summary",
            "dataset_overview",
            "methodology",
            "model_comparison_table",
            "cv_stability_analysis",
            "best_model_analysis",
            "feature_importance_analysis",
            "hyperparameter_analysis",
            "error_analysis",
            "conclusions",
            "recommendations",
            "reproducibility_notes",
        ]:
            assert field in rs, f"Missing report_sections field '{field}'"

        # chart_data sub-fields
        cd = rs["chart_data"]
        for field in [
            "model_comparison",
            "cv_fold_scores",
            "feature_importances",
            "confusion_matrices",
            "training_times",
            "hyperparam_search",
            "residual_stats",
            "cluster_scatter",
            "elbow_curve",
            "cluster_profiles",
            "silhouette_data",
            "actual_vs_predicted",
            "coefficients",
            "learning_curve",
        ]:
            assert field in cd, f"Missing chart_data field '{field}'"


# ---------------------------------------------------------------------------
# PaginatedExperiments contract
# ---------------------------------------------------------------------------


class TestPaginatedExperimentsContract:
    """Verify the list endpoint response matches PaginatedExperiments interface."""

    def test_paginated_response_structure(self, client):
        """Response has experiments, total, offset, limit."""
        resp = client.get("/api/v1/experiments")
        data = resp.json()

        assert "experiments" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data

        assert isinstance(data["experiments"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["offset"], int)
        assert isinstance(data["limit"], int)

    def test_paginated_experiment_entries_have_all_fields(self, client):
        """Each experiment in the list has all expected fields."""
        from unittest.mock import AsyncMock, patch

        with patch(
            "scientist_bin_backend.api.routes._run_training",
            new_callable=AsyncMock,
        ):
            client.post(
                "/api/v1/train",
                json={"objective": "Contract test experiment"},
            )

        resp = client.get("/api/v1/experiments")
        data = resp.json()
        assert len(data["experiments"]) >= 1

        exp = data["experiments"][0]
        expected_fields = [
            "id",
            "objective",
            "data_description",
            "data_file_path",
            "framework",
            "status",
            "phase",
            "runs",
            "best_run_id",
            "iteration_count",
            "progress_events",
            "result",
            "execution_plan",
            "analysis_report",
            "summary_report",
            "split_data_paths",
            "problem_type",
            "created_at",
            "updated_at",
        ]
        for field in expected_fields:
            assert field in exp, f"Missing field '{field}' in listed experiment"


# ---------------------------------------------------------------------------
# Error response contract
# ---------------------------------------------------------------------------


class TestErrorContract:
    """Verify error responses match the frontend ExperimentError interface."""

    def test_error_result_structure(self):
        """A failed experiment result should contain error and optionally traceback."""
        error_result = {"error": "Something went wrong", "traceback": "Traceback ..."}

        assert "error" in error_result
        assert isinstance(error_result["error"], str)


# ---------------------------------------------------------------------------
# Deployment contract
# ---------------------------------------------------------------------------


class TestDeploymentContract:
    """Verify deployment endpoint responses match frontend DeploymentInfo."""

    def test_deployment_not_deployed_structure(self, client):
        """Not-deployed response has expected fields."""
        from unittest.mock import AsyncMock, patch

        with patch(
            "scientist_bin_backend.api.routes._run_training",
            new_callable=AsyncMock,
        ):
            create_resp = client.post(
                "/api/v1/train",
                json={"objective": "Deployment contract test"},
            )
        exp_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/experiments/{exp_id}/deployment")
        data = resp.json()

        assert "status" in data
        assert data["status"] == "not_deployed"
        assert "experiment_id" in data

    def test_deployment_deployed_structure(self, client):
        """Deployed response has all DeploymentInfo fields."""
        from unittest.mock import AsyncMock, patch

        from scientist_bin_backend.api.experiments import ExperimentStatus, experiment_store

        with patch(
            "scientist_bin_backend.api.routes._run_training",
            new_callable=AsyncMock,
        ):
            create_resp = client.post(
                "/api/v1/train",
                json={"objective": "Deployment deployed contract"},
            )
        exp_id = create_resp.json()["id"]
        experiment_store.update(exp_id, status=ExperimentStatus.completed)

        deploy_resp = client.post(
            f"/api/v1/experiments/{exp_id}/deploy",
            json={"model_version": "v1.0"},
        )
        data = deploy_resp.json()

        # Fields from frontend DeploymentInfo interface
        assert "status" in data
        assert data["status"] == "deployed"
        assert "endpoint_url" in data
        assert "deployed_at" in data
        assert "model_version" in data
        assert data["model_version"] == "v1.0"
