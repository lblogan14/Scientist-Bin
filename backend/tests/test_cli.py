"""Tests for the CLI (scientist-bin) commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from scientist_bin_backend.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Server-interaction commands (mock httpx)
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_ok(self):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"status": "ok"}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_resp):
            result = runner.invoke(app, ["health"])
        assert result.exit_code == 0
        assert "ok" in result.output

    def test_health_unreachable(self):
        import httpx

        with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
            result = runner.invoke(app, ["health"])
        assert result.exit_code == 1
        assert "not reachable" in result.output


class TestListExperiments:
    def test_list_empty(self):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"experiments": [], "total": 0}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_resp):
            result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No experiments found" in result.output

    def test_list_with_results(self):
        experiments = [
            {"id": "exp-1", "status": "completed", "objective": "Classify iris"},
            {"id": "exp-2", "status": "running", "objective": "Predict prices"},
        ]
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"experiments": experiments, "total": 2}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_resp):
            result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "exp-1" in result.output
        assert "Classify iris" in result.output

    def test_list_with_filters(self):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"experiments": [], "total": 0}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_resp) as mock_get:
            result = runner.invoke(
                app, ["list", "--status", "completed", "--framework", "sklearn", "--search", "iris"]
            )
        assert result.exit_code == 0
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params", {})
        assert params["status"] == "completed"
        assert params["framework"] == "sklearn"
        assert params["search"] == "iris"


class TestShow:
    def test_show_default(self):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {
            "id": "exp-1",
            "objective": "Classify iris",
            "status": "completed",
            "framework": "sklearn",
            "created_at": "2026-04-01T10:00:00Z",
            "updated_at": "2026-04-01T10:30:00Z",
            "result": None,
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_resp):
            result = runner.invoke(app, ["show", "exp-1"])
        assert result.exit_code == 0
        assert "Classify iris" in result.output
        assert "completed" in result.output

    def test_show_json(self):
        data = {"id": "exp-1", "objective": "test"}
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = data
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_resp):
            result = runner.invoke(app, ["show", "exp-1", "--json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["id"] == "exp-1"


class TestDelete:
    def test_delete_success(self):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"detail": "Experiment deleted"}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.delete", return_value=mock_resp):
            result = runner.invoke(app, ["delete", "exp-1"])
        assert result.exit_code == 0
        assert "Deleted" in result.output


class TestReview:
    def test_review_approve(self):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"status": "approved"}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.post", return_value=mock_resp):
            result = runner.invoke(app, ["review", "exp-1", "approve"])
        assert result.exit_code == 0
        assert "Review submitted" in result.output

    def test_review_http_error(self):
        import httpx

        mock_resp = MagicMock(status_code=404)
        mock_resp.json.return_value = {"detail": "Experiment not found"}
        err = httpx.HTTPStatusError("err", request=MagicMock(), response=mock_resp)

        with patch("httpx.post", side_effect=err):
            result = runner.invoke(app, ["review", "exp-1", "approve"])
        assert result.exit_code == 1
        assert "Experiment not found" in result.output


class TestDownload:
    def test_download_invalid_type(self):
        result = runner.invoke(app, ["download", "exp-1", "badtype"])
        assert result.exit_code == 1
        assert "Unknown artifact type" in result.output

    def test_download_success(self, tmp_path: Path):
        mock_resp = MagicMock(status_code=200)
        mock_resp.content = b"model-bytes"
        mock_resp.headers = {"content-disposition": 'attachment; filename="exp-1.joblib"'}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_resp):
            out = tmp_path / "model.joblib"
            result = runner.invoke(app, ["download", "exp-1", "model", "-o", str(out)])
        assert result.exit_code == 0
        assert out.read_bytes() == b"model-bytes"

    def test_download_all(self):
        mock_resp = MagicMock(status_code=200)
        mock_resp.content = b"data"
        mock_resp.headers = {"content-disposition": 'filename="f"'}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_resp):
            result = runner.invoke(app, ["download", "exp-1", "all"])
        assert result.exit_code == 0
        # Should attempt to download 7 artifact types
        assert result.output.count(":") >= 7


# ---------------------------------------------------------------------------
# Local agent commands (validate argument parsing)
# ---------------------------------------------------------------------------


class TestTrainLocal:
    def test_train_missing_data_file(self, tmp_path: Path):
        """Train command should fail if --data-file points to a non-existent file."""
        fake = str(tmp_path / "nonexistent.csv")
        result = runner.invoke(app, ["train", "Classify iris", "--data-file", fake])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_train_invokes_agent(self, tmp_path: Path):
        """Train command with valid args should invoke CentralAgent.run()."""
        import asyncio

        data_file = tmp_path / "iris.csv"
        data_file.write_text("col1,col2\n1,2\n")

        mock_result = MagicMock()
        mock_result.model_dump_json.return_value = '{"status": "ok"}'
        mock_result.model_dump.return_value = {"status": "ok"}

        async def mock_run(*args, **kwargs):
            return mock_result

        mock_bus = MagicMock()
        mock_bus.pre_register = MagicMock(return_value=asyncio.Queue())

        async def mock_consume(*a, **kw):
            return
            yield  # noqa: F841 — make this an async generator

        mock_bus.consume = mock_consume

        async def mock_close(*a):
            pass

        mock_bus.close = mock_close

        with (
            patch(
                "scientist_bin_backend.agents.central.agent.CentralAgent.run",
                side_effect=mock_run,
            ),
            patch(
                "scientist_bin_backend.utils.artifacts.save_experiment_artifacts",
                return_value={},
            ),
            patch("scientist_bin_backend.events.bus.event_bus", mock_bus),
        ):
            result = runner.invoke(
                app,
                ["train", "Classify iris", "--data-file", str(data_file), "--quiet"],
            )
        assert result.exit_code == 0
        assert "ok" in result.output


class TestAnalyze:
    def test_analyze_missing_file(self, tmp_path: Path):
        fake = str(tmp_path / "nonexistent.csv")
        result = runner.invoke(app, ["analyze", fake])
        assert result.exit_code == 1
        assert "not found" in result.output


class TestPlan:
    def test_plan_run_analyst_missing_file(self, tmp_path: Path):
        """plan --run-analyst should fail if data file does not exist."""
        fake = str(tmp_path / "nonexistent.csv")
        result = runner.invoke(app, ["plan", "Classify iris", "--data-file", fake, "--run-analyst"])
        assert result.exit_code == 1
        assert "not found" in result.output


class TestTrainSklearn:
    def test_train_sklearn_requires_objective(self):
        result = runner.invoke(app, ["train-sklearn"])
        assert result.exit_code != 0


class TestServe:
    def test_serve_invokes_uvicorn(self):
        with patch("uvicorn.run") as mock_run:
            result = runner.invoke(app, ["serve", "--port", "9999"])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        assert call_kwargs.kwargs.get("port") == 9999 or call_kwargs[1].get("port") == 9999


# ---------------------------------------------------------------------------
# Internal helper: _print_event
# ---------------------------------------------------------------------------


class TestPrintEvent:
    @pytest.fixture()
    def make_event(self):
        """Factory for lightweight event objects."""

        def _make(event_type: str, data: dict | None = None):
            ev = MagicMock()
            ev.event_type = event_type
            ev.data = data or {}
            return ev

        return _make

    def test_phase_change(self, make_event, capsys):
        from scientist_bin_backend.cli import _print_event

        _print_event(make_event("phase_change", {"phase": "execution", "message": "Starting"}))
        out = capsys.readouterr().out
        assert "execution" in out
        assert "Starting" in out

    def test_agent_activity_with_decision(self, make_event, capsys):
        from scientist_bin_backend.cli import _print_event

        _print_event(
            make_event(
                "agent_activity",
                {"action": "generate_code", "iteration": 2, "decision": "try SVM"},
            )
        )
        out = capsys.readouterr().out
        assert "generate_code" in out
        assert "try SVM" in out

    def test_experiment_done(self, make_event, capsys):
        from scientist_bin_backend.cli import _print_event

        _print_event(
            make_event(
                "experiment_done",
                {"best_model": "RandomForest", "best_metrics": {"accuracy": 0.95}},
            )
        )
        out = capsys.readouterr().out
        assert "RandomForest" in out
        assert "0.9500" in out

    def test_error_event(self, make_event, capsys):
        from scientist_bin_backend.cli import _print_event

        _print_event(make_event("error", {"message": "OOM"}))
        out = capsys.readouterr().out
        assert "OOM" in out

    def test_framework_completed(self, make_event, capsys):
        from scientist_bin_backend.cli import _print_event

        _print_event(make_event("framework_completed"))
        out = capsys.readouterr().out
        assert "framework_completed" in out

    def test_run_started(self, make_event, capsys):
        from scientist_bin_backend.cli import _print_event

        _print_event(make_event("run_started", {"timeout": 120, "estimated_duration": 30.5}))
        out = capsys.readouterr().out
        assert "120" in out
        assert "30" in out

    def test_run_completed(self, make_event, capsys):
        from scientist_bin_backend.cli import _print_event

        _print_event(make_event("run_completed", {"status": "success", "wall_time_seconds": 12}))
        out = capsys.readouterr().out
        assert "success" in out
        assert "12" in out

    def test_plan_completed(self, make_event, capsys):
        from scientist_bin_backend.cli import _print_event

        _print_event(make_event("plan_completed", {"plan_approved": True}))
        out = capsys.readouterr().out
        assert "approved" in out

    def test_plan_review_pending(self, make_event, capsys):
        from scientist_bin_backend.cli import _print_event

        _print_event(make_event("plan_review_pending"))
        out = capsys.readouterr().out
        assert "review" in out.lower()

    def test_metric_update(self, make_event, capsys):
        from scientist_bin_backend.cli import _print_event

        _print_event(make_event("metric_update", {"name": "accuracy", "value": 0.87}))
        out = capsys.readouterr().out
        assert "accuracy" in out
        assert "0.87" in out


# ---------------------------------------------------------------------------
# Framework provisioning commands
# ---------------------------------------------------------------------------


class TestProvision:
    def test_provision_no_args_lists_available(self):
        """Calling provision with no args should list available frameworks."""
        result = runner.invoke(app, ["provision"])
        assert result.exit_code == 0
        assert "analyst" in result.output
        assert "traditional" in result.output

    def test_provision_status(self):
        """provision-status should list framework names with status."""
        result = runner.invoke(app, ["provision-status"])
        assert result.exit_code == 0
        assert "analyst" in result.output.lower() or "traditional" in result.output.lower()

    def test_provision_unknown_framework(self):
        """Provisioning a nonexistent framework should show SKIP."""
        result = runner.invoke(app, ["provision", "nonexistent_framework_xyz"])
        # Should not crash; the framework dir won't have a pyproject.toml
        assert "SKIP" in result.output or "no pyproject.toml" in result.output.lower()
