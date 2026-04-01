"""Scientist-Bin CLI — Typer application for local agent execution and server management."""

import typer

app = typer.Typer(
    name="scientist-bin",
    help="Multi-agent system for automated data science model training and evaluation.",
)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
) -> None:
    """Start the FastAPI server."""
    import uvicorn

    uvicorn.run(
        "scientist_bin_backend.main:app",
        host=host,
        port=port,
        reload=reload,
        reload_excludes=["data/*", "outputs/*"] if reload else None,
    )


@app.command()
def train(
    objective: str = typer.Argument(..., help="Training objective description"),
    data: str = typer.Option("", "--data", help="Data description"),
    data_file: str | None = typer.Option(None, "--data-file", help="Path to dataset file"),
    framework: str | None = typer.Option(None, "--framework", help="Framework preference"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip plan review"),
) -> None:
    """Run full training pipeline locally (no server required)."""
    import asyncio
    from pathlib import Path

    from scientist_bin_backend.agents.central.agent import CentralAgent
    from scientist_bin_backend.agents.central.schemas import TrainRequest
    from scientist_bin_backend.utils.naming import generate_experiment_id

    # Resolve data file path to absolute and validate before starting the agent
    resolved_data_file = None
    if data_file:
        resolved = Path(data_file).resolve()
        if not resolved.exists():
            typer.echo(f"Error: Data file not found: {resolved}", err=True)
            raise typer.Exit(code=1)
        resolved_data_file = str(resolved)

    agent = CentralAgent()
    experiment_id = generate_experiment_id(objective)
    request = TrainRequest(
        objective=objective,
        data_description=data,
        data_file_path=resolved_data_file,
        framework_preference=framework,
        auto_approve_plan=auto_approve,
    )

    async def run_with_progress() -> "AgentResponse":  # noqa: F821
        from scientist_bin_backend.events.bus import event_bus

        if not quiet:
            typer.echo("\n  Scientist-Bin  |  Training Agent")
            typer.echo(f"  Experiment: {experiment_id}")
            typer.echo(f"  Objective:  {objective}")
            if resolved_data_file:
                typer.echo(f"  Data file:  {resolved_data_file}")
            typer.echo("")

        async def print_events() -> None:
            async for event in event_bus.subscribe(experiment_id):
                if not quiet:
                    _print_event(event)

        event_task = asyncio.create_task(print_events())
        try:
            result = await agent.run(request, experiment_id=experiment_id)
        finally:
            await event_bus.close(experiment_id)
            await event_task

        return result

    result = asyncio.run(run_with_progress())
    if not quiet:
        typer.echo("")

    # Save artifacts to top-level output directories
    _save_artifacts(experiment_id, result, quiet)

    typer.echo(result.model_dump_json(indent=2))


# ---------------------------------------------------------------------------
# Per-agent standalone commands
# ---------------------------------------------------------------------------


@app.command()
def plan(
    objective: str = typer.Argument(..., help="Training objective description"),
    data: str = typer.Option("", "--data", help="Data description"),
    data_file: str | None = typer.Option(None, "--data-file", help="Path to dataset file"),
    framework: str | None = typer.Option(None, "--framework", help="Framework preference"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Auto-approve plan"),
) -> None:
    """Run only the Plan Agent (research, plan generation, HITL review)."""
    import asyncio
    import json

    from scientist_bin_backend.agents.plan.agent import PlanAgent
    from scientist_bin_backend.utils.naming import generate_experiment_id

    agent = PlanAgent()
    experiment_id = generate_experiment_id(objective)

    async def run() -> dict:
        return await agent.run(
            objective=objective,
            data_description=data,
            data_file_path=data_file,
            framework_preference=framework,
            experiment_id=experiment_id,
            auto_approve=auto_approve,
        )

    result = asyncio.run(run())
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command()
def analyze(
    data_file: str = typer.Argument(..., help="Path to dataset file"),
    plan_file: str | None = typer.Option(None, "--plan-file", help="Execution plan JSON file"),
    objective: str = typer.Option("", "--objective", help="Training objective"),
) -> None:
    """Run only the Analyst Agent (data profiling, cleaning, splitting)."""
    import asyncio
    import json
    from pathlib import Path

    from scientist_bin_backend.agents.analyst.agent import AnalystAgent
    from scientist_bin_backend.utils.naming import generate_experiment_id

    resolved = Path(data_file).resolve()
    if not resolved.exists():
        typer.echo(f"Error: Data file not found: {resolved}", err=True)
        raise typer.Exit(code=1)

    execution_plan = None
    if plan_file:
        plan_path = Path(plan_file).resolve()
        if plan_path.exists():
            execution_plan = json.loads(plan_path.read_text(encoding="utf-8"))

    agent = AnalystAgent()
    experiment_id = generate_experiment_id(objective)

    async def run() -> dict:
        return await agent.run(
            objective=objective,
            data_file_path=str(resolved),
            execution_plan=execution_plan,
            experiment_id=experiment_id,
        )

    result = asyncio.run(run())
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command(name="train-sklearn")
def train_sklearn(
    objective: str = typer.Argument(..., help="Training objective description"),
    data_dir: str | None = typer.Option(None, "--data-dir", help="Dir with train/val/test CSVs"),
    plan_file: str | None = typer.Option(None, "--plan-file", help="Execution plan JSON file"),
    analysis_file: str | None = typer.Option(None, "--analysis-file", help="Analysis report file"),
    max_iterations: int = typer.Option(5, "--max-iterations", help="Max training iterations"),
) -> None:
    """Run only the Sklearn Agent (code generation, training, iteration)."""
    import asyncio
    import json
    from pathlib import Path

    from scientist_bin_backend.agents.sklearn.agent import SklearnAgent
    from scientist_bin_backend.utils.naming import generate_experiment_id

    split_data_paths = {}
    if data_dir:
        d = Path(data_dir).resolve()
        split_data_paths = {
            "train": str(d / "train.csv"),
            "val": str(d / "val.csv"),
            "test": str(d / "test.csv"),
        }

    execution_plan = None
    if plan_file:
        plan_path = Path(plan_file).resolve()
        if plan_path.exists():
            execution_plan = json.loads(plan_path.read_text(encoding="utf-8"))

    analysis_report = None
    if analysis_file:
        analysis_path = Path(analysis_file).resolve()
        if analysis_path.exists():
            analysis_report = analysis_path.read_text(encoding="utf-8")

    agent = SklearnAgent()
    experiment_id = generate_experiment_id(objective)

    async def run() -> dict:
        return await agent.run(
            objective=objective,
            execution_plan=execution_plan,
            analysis_report=analysis_report,
            split_data_paths=split_data_paths,
            max_iterations=max_iterations,
            experiment_id=experiment_id,
        )

    result = asyncio.run(run())
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command()
def summarize(
    experiment_id: str = typer.Argument(..., help="Experiment ID to summarize"),
) -> None:
    """Run only the Summary Agent (review experiments, select best, generate report)."""
    import asyncio
    import json
    from pathlib import Path

    from scientist_bin_backend.agents.summary.agent import SummaryAgent

    # Load experiment results from the outputs directory
    _backend_dir = Path(__file__).resolve().parent.parent.parent
    results_path = _backend_dir / "outputs" / "results" / f"{experiment_id}.json"

    experiment_data: dict = {}
    if results_path.exists():
        experiment_data = json.loads(results_path.read_text(encoding="utf-8"))

    agent = SummaryAgent()

    async def run() -> dict:
        return await agent.run(
            objective=experiment_data.get("objective", ""),
            problem_type=experiment_data.get("problem_type"),
            execution_plan=experiment_data.get("plan"),
            analysis_report=experiment_data.get("analysis_report"),
            sklearn_results=experiment_data,
            experiment_history=experiment_data.get("experiment_history", []),
            experiment_id=experiment_id,
        )

    result = asyncio.run(run())
    typer.echo(json.dumps(result, indent=2, default=str))


# ---------------------------------------------------------------------------
# Existing server-interaction commands
# ---------------------------------------------------------------------------


@app.command(name="train-remote")
def train_remote(
    objective: str = typer.Argument(..., help="Training objective description"),
    data: str = typer.Option("", "--data", help="Data description"),
    data_file: str | None = typer.Option(None, "--data-file", help="Path to dataset file"),
    framework: str | None = typer.Option(None, "--framework", help="Framework preference"),
    base_url: str = typer.Option("http://localhost:8000", "--base-url", help="Server URL"),
) -> None:
    """Submit training request to a running server."""
    import httpx

    payload: dict = {"objective": objective, "data_description": data}
    if data_file:
        payload["data_file_path"] = data_file
    if framework:
        payload["framework_preference"] = framework
    response = httpx.post(f"{base_url}/api/v1/train", json=payload)
    response.raise_for_status()
    typer.echo(response.json())


@app.command(name="list")
def list_experiments(
    base_url: str = typer.Option("http://localhost:8000", "--base-url", help="Server URL"),
) -> None:
    """List all experiments on server."""
    import httpx

    response = httpx.get(f"{base_url}/api/v1/experiments")
    response.raise_for_status()
    experiments = response.json()
    if not experiments:
        typer.echo("No experiments found.")
        return
    for exp in experiments:
        status = exp.get("status", "unknown")
        typer.echo(f"  {exp['id']}  [{status}]  {exp.get('objective', '')[:60]}")


@app.command()
def show(
    experiment_id: str = typer.Argument(..., help="Experiment ID"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    base_url: str = typer.Option("http://localhost:8000", "--base-url", help="Server URL"),
) -> None:
    """Show experiment details."""
    import json as json_module

    import httpx

    response = httpx.get(f"{base_url}/api/v1/experiments/{experiment_id}")
    response.raise_for_status()
    data = response.json()
    if json_output:
        typer.echo(json_module.dumps(data, indent=2))
    else:
        typer.echo(f"ID:        {data['id']}")
        typer.echo(f"Objective: {data.get('objective', '')}")
        typer.echo(f"Status:    {data.get('status', 'unknown')}")
        typer.echo(f"Framework: {data.get('framework', 'N/A')}")
        typer.echo(f"Created:   {data.get('created_at', '')}")
        typer.echo(f"Updated:   {data.get('updated_at', '')}")
        if data.get("result"):
            typer.echo(f"Result:    {json_module.dumps(data['result'], indent=2)}")


@app.command()
def delete(
    experiment_id: str = typer.Argument(..., help="Experiment ID"),
    base_url: str = typer.Option("http://localhost:8000", "--base-url", help="Server URL"),
) -> None:
    """Delete an experiment."""
    import httpx

    response = httpx.delete(f"{base_url}/api/v1/experiments/{experiment_id}")
    response.raise_for_status()
    typer.echo(f"Deleted experiment {experiment_id}")


@app.command()
def health(
    base_url: str = typer.Option("http://localhost:8000", "--base-url", help="Server URL"),
) -> None:
    """Check server health."""
    import httpx

    try:
        response = httpx.get(f"{base_url}/api/v1/health")
        response.raise_for_status()
        typer.echo(response.json())
    except httpx.ConnectError:
        typer.echo("Server is not reachable.", err=True)
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _print_event(event: "ExperimentEvent") -> None:  # noqa: F821
    """Format and print an experiment event to the terminal."""
    data = event.data
    etype = event.event_type

    if etype == "phase_change":
        phase = data.get("phase", "?")
        msg = data.get("message") or data.get("summary", "")
        if msg:
            typer.echo(f"  [{phase}] {msg}")
    elif etype == "agent_activity":
        action = data.get("action", "?")
        iteration = data.get("iteration", 0)
        decision = data.get("decision")
        if decision:
            typer.echo(f"  [iter {iteration}] {action} -> {decision}")
        else:
            typer.echo(f"  [iter {iteration}] {action}")
    elif etype == "run_started":
        timeout = data.get("timeout", "?")
        est = data.get("estimated_duration")
        est_str = f", estimated: {est:.0f}s" if est else ""
        typer.echo(f"  [run] Started (timeout: {timeout}s{est_str})")
    elif etype == "run_completed":
        status = data.get("status", "?")
        wall = data.get("wall_time_seconds", "?")
        typer.echo(f"  [run] {status} in {wall}s")
    elif etype == "metric_update":
        name = data.get("name", "?")
        value = data.get("value", "?")
        typer.echo(f"  [metric] {name} = {value}")
    elif etype == "experiment_done":
        best = data.get("best_model", "?")
        metrics = data.get("best_metrics", {})
        metrics_str = ", ".join(f"{k}={v:.4f}" for k, v in metrics.items())
        typer.echo(f"  [done] Best model: {best} ({metrics_str})")
    elif etype == "plan_completed":
        approved = data.get("plan_approved", False)
        typer.echo(f"  [plan] Plan {'approved' if approved else 'pending'}")
    elif etype in ("analysis_completed", "sklearn_completed", "summary_completed"):
        typer.echo(f"  [{etype}] completed")
    elif etype == "error":
        msg = data.get("message", "Unknown error")
        typer.echo(f"  [error] {msg}")


def _save_artifacts(
    experiment_id: str,
    result: "AgentResponse",  # noqa: F821
    quiet: bool,
) -> None:
    """Save model, results JSON, and journal to top-level output directories."""
    from scientist_bin_backend.utils.artifacts import save_experiment_artifacts

    saved = save_experiment_artifacts(experiment_id, result.model_dump())

    if not quiet:
        if "results" in saved:
            typer.echo(f"  [saved] Results  -> {saved['results']}")
        if "model" in saved:
            typer.echo(f"  [saved] Model    -> {saved['model']}")
        if "journal" in saved:
            typer.echo(f"  [saved] Journal  -> {saved['journal']}")
        typer.echo("")
