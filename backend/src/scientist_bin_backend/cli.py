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
        reload_dirs=["src"] if reload else None,
    )


@app.command()
def train(
    objective: str = typer.Argument(..., help="Training objective description"),
    data: str = typer.Option("", "--data", help="Data description"),
    data_file: str | None = typer.Option(None, "--data-file", help="Path to dataset file"),
    framework: str | None = typer.Option(None, "--framework", help="Framework preference"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip plan review"),
    deep_research: bool = typer.Option(
        False, "--deep-research", help="Run autonomous research campaign"
    ),
    budget: int = typer.Option(
        10, "--budget", help="Max experiment iterations (deep research only)"
    ),
    time_limit: str = typer.Option(
        "4h",
        "--time-limit",
        help="Wall-clock time limit, e.g. 4h, 30m (deep research only)",
    ),
) -> None:
    """Run full training pipeline locally (no server required)."""
    import asyncio
    from pathlib import Path

    from scientist_bin_backend.utils.naming import generate_experiment_id

    # Resolve data file path to absolute and validate before starting the agent
    resolved_data_file = None
    if data_file:
        resolved = Path(data_file).resolve()
        if not resolved.exists():
            typer.echo(f"Error: Data file not found: {resolved}", err=True)
            raise typer.Exit(code=1)
        resolved_data_file = str(resolved)

    experiment_id = generate_experiment_id(objective)

    # Pre-flight: check that required framework venvs are available
    from scientist_bin_backend.execution.sandbox import get_framework_python

    try:
        get_framework_python("analyst")
    except RuntimeError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)

    if framework:
        try:
            get_framework_python(framework)
        except RuntimeError as exc:
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(code=1)

    # -------------------------------------------------------------------
    # Deep Research path: delegate to CampaignAgent
    # -------------------------------------------------------------------
    if deep_research:
        import re

        if not resolved_data_file:
            typer.echo(
                "Error: --data-file is required for --deep-research",
                err=True,
            )
            raise typer.Exit(code=1)

        match = re.match(r"^(\d+)(h|m|s)$", time_limit.strip())
        if not match:
            typer.echo(
                "Invalid time limit format. Use e.g. '4h', '30m', '300s'.",
                err=True,
            )
            raise typer.Exit(code=1)
        value, unit = int(match.group(1)), match.group(2)
        seconds = value * {"h": 3600, "m": 60, "s": 1}[unit]

        from scientist_bin_backend.agents.campaign.agent import CampaignAgent

        if not quiet:
            typer.echo("\n  Scientist-Bin  |  Deep Research Campaign")
            typer.echo(f"  Experiment: {experiment_id}")
            typer.echo(f"  Objective:  {objective}")
            typer.echo(f"  Data file:  {resolved_data_file}")
            typer.echo(f"  Budget:     {budget} experiments, {time_limit}")
            typer.echo("")

        agent = CampaignAgent()
        result = asyncio.run(
            agent.run(
                objective=objective,
                data_file_path=resolved_data_file,
                data_description=data,
                budget_max_iterations=budget,
                budget_time_limit_seconds=float(seconds),
            )
        )

        if not quiet:
            typer.echo(
                f"\nCampaign complete: "
                f"{result.total_iterations} experiments in "
                f"{result.total_time_seconds:.1f}s"
            )
            if result.best_algorithm:
                typer.echo(f"  Best: {result.best_algorithm}")
            for k, v in list(result.best_metrics.items())[:5]:
                typer.echo(f"    {k}: {v}")

        typer.echo(result.model_dump_json(indent=2))
        return

    # -------------------------------------------------------------------
    # Standard path: delegate to CentralAgent
    # -------------------------------------------------------------------
    from scientist_bin_backend.agents.central.agent import CentralAgent
    from scientist_bin_backend.agents.central.schemas import TrainRequest

    agent = CentralAgent()
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

        # Pre-register queue BEFORE the agent starts so no early events are lost
        queue = event_bus.pre_register(experiment_id)

        async def print_events() -> None:
            async for event in event_bus.consume(experiment_id, queue):
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
    analysis_file: str | None = typer.Option(
        None, "--analysis-file", help="Analysis report (.md) from analyst agent"
    ),
    profile_file: str | None = typer.Option(
        None, "--profile-file", help="Data profile JSON from analyst agent"
    ),
    run_analyst: bool = typer.Option(
        False, "--run-analyst", help="Auto-run analyst first to generate upstream context"
    ),
) -> None:
    """Run only the Plan Agent (research, plan generation, HITL review).

    For best results, provide upstream context from the analyst agent via
    --analysis-file and --profile-file, or use --run-analyst to auto-run
    the analyst first.
    """
    import asyncio
    import json
    from pathlib import Path

    from scientist_bin_backend.agents.plan.agent import PlanAgent
    from scientist_bin_backend.utils.naming import generate_experiment_id

    experiment_id = generate_experiment_id(objective)

    analysis_report = None
    data_profile = None
    problem_type = None

    # Optionally run the analyst first to generate context
    if run_analyst and data_file:
        from scientist_bin_backend.agents.analyst.agent import AnalystAgent

        resolved = Path(data_file).resolve()
        if not resolved.exists():
            typer.echo(f"Error: Data file not found: {resolved}", err=True)
            raise typer.Exit(code=1)

        typer.echo("  Running analyst agent for upstream context...")
        analyst = AnalystAgent()

        async def run_analyst_agent() -> dict:
            return await analyst.run(
                objective=objective,
                data_file_path=str(resolved),
                experiment_id=experiment_id,
            )

        analyst_result = asyncio.run(run_analyst_agent())
        analysis_report = analyst_result.get("analysis_report")
        data_profile = analyst_result.get("data_profile")
        problem_type = analyst_result.get("problem_type")
        typer.echo("  Analyst complete. Running plan agent...\n")

    # Load from files if provided (overrides analyst output)
    if analysis_file:
        p = Path(analysis_file).resolve()
        if p.exists():
            analysis_report = p.read_text(encoding="utf-8")

    if profile_file:
        p = Path(profile_file).resolve()
        if p.exists():
            data_profile = json.loads(p.read_text(encoding="utf-8"))
            problem_type = data_profile.get("problem_type") or problem_type

    agent = PlanAgent()

    async def run() -> dict:
        return await agent.run(
            objective=objective,
            data_description=data,
            data_file_path=data_file,
            framework_preference=framework,
            experiment_id=experiment_id,
            auto_approve=auto_approve,
            analysis_report=analysis_report,
            data_profile=data_profile,
            problem_type=problem_type,
        )

    result = asyncio.run(run())
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command()
def analyze(
    data_file: str = typer.Argument(..., help="Path to dataset file"),
    objective: str = typer.Option("", "--objective", help="Training objective"),
    task_analysis: str | None = typer.Option(
        None, "--task-analysis", help="Task analysis JSON file from central agent"
    ),
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

    ta = None
    if task_analysis:
        ta_path = Path(task_analysis).resolve()
        if ta_path.exists():
            ta = json.loads(ta_path.read_text(encoding="utf-8"))

    agent = AnalystAgent()
    experiment_id = generate_experiment_id(objective)

    async def run() -> dict:
        return await agent.run(
            objective=objective,
            data_file_path=str(resolved),
            task_analysis=ta,
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
    problem_type: str | None = typer.Option(
        None, "--problem-type", help="Problem type (classification, regression, clustering)"
    ),
    max_iterations: int = typer.Option(5, "--max-iterations", help="Max training iterations"),
) -> None:
    """Run only the Sklearn Agent (code generation, training, iteration)."""
    import asyncio
    import json
    from pathlib import Path

    from scientist_bin_backend.agents.frameworks.sklearn.agent import SklearnAgent
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
            problem_type=problem_type,
            max_iterations=max_iterations,
            experiment_id=experiment_id,
        )

    result = asyncio.run(run())
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command(name="train-flaml")
def train_flaml(
    objective: str = typer.Argument(..., help="Training objective description"),
    data_dir: str | None = typer.Option(None, "--data-dir", help="Dir with train/val/test CSVs"),
    plan_file: str | None = typer.Option(None, "--plan-file", help="Execution plan JSON file"),
    analysis_file: str | None = typer.Option(None, "--analysis-file", help="Analysis report file"),
    problem_type: str | None = typer.Option(
        None, "--problem-type", help="Problem type (classification, regression, ts_forecast)"
    ),
    max_iterations: int = typer.Option(5, "--max-iterations", help="Max training iterations"),
    time_budget: int = typer.Option(120, "--time-budget", help="FLAML time budget in seconds"),
) -> None:
    """Run only the FLAML Agent (AutoML code generation, training, iteration)."""
    import asyncio
    import json
    from pathlib import Path

    from scientist_bin_backend.agents.frameworks.flaml.agent import FlamlAgent
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

    # Inject time_budget into execution plan if not already set
    if execution_plan is None:
        execution_plan = {}
    execution_plan.setdefault("time_budget", time_budget)

    analysis_report = None
    if analysis_file:
        analysis_path = Path(analysis_file).resolve()
        if analysis_path.exists():
            analysis_report = analysis_path.read_text(encoding="utf-8")

    agent = FlamlAgent()
    experiment_id = generate_experiment_id(objective)

    async def run() -> dict:
        return await agent.run(
            objective=objective,
            execution_plan=execution_plan,
            analysis_report=analysis_report,
            split_data_paths=split_data_paths,
            problem_type=problem_type,
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
            framework_results=experiment_data,
            experiment_history=experiment_data.get("experiment_history", []),
            experiment_id=experiment_id,
        )

    result = asyncio.run(run())
    typer.echo(json.dumps(result, indent=2, default=str))


# ---------------------------------------------------------------------------
# Server-interaction commands
# ---------------------------------------------------------------------------


@app.command(name="train-remote")
def train_remote(
    objective: str = typer.Argument(..., help="Training objective description"),
    data: str = typer.Option("", "--data", help="Data description"),
    data_file: str | None = typer.Option(None, "--data-file", help="Path to dataset file"),
    framework: str | None = typer.Option(None, "--framework", help="Framework preference"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip plan review"),
    base_url: str = typer.Option("http://localhost:8000", "--base-url", help="Server URL"),
    follow: bool = typer.Option(True, "--follow/--no-follow", help="Stream events in real-time"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
) -> None:
    """Submit training request to a running server and optionally stream events."""
    from pathlib import Path

    import httpx

    # Validate data file exists locally before submitting
    if data_file:
        resolved = Path(data_file).resolve()
        if not resolved.exists():
            typer.echo(f"Error: Data file not found: {resolved}", err=True)
            raise typer.Exit(code=1)

    payload: dict = {
        "objective": objective,
        "data_description": data,
        "auto_approve_plan": auto_approve,
    }
    if data_file:
        payload["data_file_path"] = data_file
    if framework:
        payload["framework_preference"] = framework

    response = httpx.post(f"{base_url}/api/v1/train", json=payload)
    response.raise_for_status()
    experiment = response.json()
    experiment_id = experiment["id"]

    if not quiet:
        typer.echo(f"  Experiment submitted: {experiment_id}")

    if follow and not quiet:
        _stream_remote_events(base_url, experiment_id)
    elif not quiet:
        typer.echo(f"  Use 'scientist-bin watch {experiment_id}' to stream events.")


@app.command()
def watch(
    experiment_id: str = typer.Argument(..., help="Experiment ID to watch"),
    base_url: str = typer.Option("http://localhost:8000", "--base-url", help="Server URL"),
) -> None:
    """Watch real-time events from a running experiment on the server."""
    _stream_remote_events(base_url, experiment_id)


@app.command()
def review(
    experiment_id: str = typer.Argument(..., help="Experiment ID waiting for review"),
    feedback: str = typer.Argument(..., help="'approve' or revision feedback text"),
    base_url: str = typer.Option("http://localhost:8000", "--base-url", help="Server URL"),
) -> None:
    """Submit plan review feedback for a waiting experiment."""
    import httpx

    try:
        response = httpx.post(
            f"{base_url}/api/v1/experiments/{experiment_id}/review",
            json={"feedback": feedback},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.json().get("detail", str(exc))
        typer.echo(f"Error: {detail}", err=True)
        raise typer.Exit(code=1)
    data = response.json()
    typer.echo(f"  Review submitted: {data.get('status', 'ok')}")


@app.command()
def download(
    experiment_id: str = typer.Argument(..., help="Experiment ID"),
    artifact_type: str = typer.Argument(
        ..., help="Artifact type: model, results, analysis, summary, plan, charts, journal, all"
    ),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    base_url: str = typer.Option("http://localhost:8000", "--base-url", help="Server URL"),
) -> None:
    """Download an experiment artifact from the server."""
    types = ["model", "results", "analysis", "summary", "plan", "charts", "journal"]
    if artifact_type == "all":
        for t in types:
            _download_single_artifact(base_url, experiment_id, t, output_dir=output)
        return

    if artifact_type not in types:
        valid = ", ".join(types)
        typer.echo(
            f"Error: Unknown artifact type '{artifact_type}'. Choose from: {valid}, all",
            err=True,
        )
        raise typer.Exit(code=1)

    _download_single_artifact(base_url, experiment_id, artifact_type, output_path=output)


@app.command(name="list")
def list_experiments(
    status: str | None = typer.Option(None, "--status", help="Filter by status"),
    framework: str | None = typer.Option(None, "--framework", help="Filter by framework"),
    search: str | None = typer.Option(None, "--search", help="Search in objective text"),
    limit: int = typer.Option(50, "--limit", help="Max results"),
    base_url: str = typer.Option("http://localhost:8000", "--base-url", help="Server URL"),
) -> None:
    """List experiments on server with optional filtering."""
    import httpx

    params: dict = {"limit": limit}
    if status:
        params["status"] = status
    if framework:
        params["framework"] = framework
    if search:
        params["search"] = search

    response = httpx.get(f"{base_url}/api/v1/experiments", params=params)
    response.raise_for_status()
    data = response.json()
    experiments = data.get("experiments", [])
    total = data.get("total", len(experiments))

    if not experiments:
        typer.echo("No experiments found.")
        return

    for exp in experiments:
        exp_status = exp.get("status", "unknown")
        typer.echo(f"  {exp['id']}  [{exp_status}]  {exp.get('objective', '')[:60]}")

    if total > len(experiments):
        typer.echo(f"\n  Showing {len(experiments)} of {total} experiments")


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


@app.command()
def provision(
    frameworks: list[str] = typer.Argument(
        None, help="Framework venvs to provision (e.g., traditional, pytorch-gpu, analyst)"
    ),
    all_: bool = typer.Option(False, "--all", help="Provision all available framework venvs"),
) -> None:
    """Create and sync framework virtual environments.

    Each framework runs ML code in its own isolated venv. Use this command
    to install the required dependencies before training.

    Examples:
        scientist-bin provision analyst traditional
        scientist-bin provision pytorch-gpu
        scientist-bin provision --all
    """
    import shutil
    import subprocess
    import sys
    from pathlib import Path

    frameworks_dir = Path(__file__).resolve().parent.parent.parent / "framework_venvs"

    if not frameworks_dir.exists():
        typer.echo(f"Frameworks directory not found: {frameworks_dir}", err=True)
        raise typer.Exit(code=1)

    # Discover available frameworks
    available = sorted(
        d.name for d in frameworks_dir.iterdir()
        if d.is_dir() and (d / "pyproject.toml").exists()
    )

    if all_:
        targets = available
    elif frameworks:
        targets = frameworks
    else:
        typer.echo("Available framework venvs:")
        for name in available:
            typer.echo(f"  {name}")
        typer.echo("\nUsage: scientist-bin provision <name> [<name> ...] or --all")
        return

    # Find uv executable
    uv_path = shutil.which("uv")
    if not uv_path:
        typer.echo("Error: 'uv' not found. Install it: https://docs.astral.sh/uv/", err=True)
        raise typer.Exit(code=1)

    for name in targets:
        fw_dir = frameworks_dir / name
        if not (fw_dir / "pyproject.toml").exists():
            typer.echo(f"  [SKIP] {name} — no pyproject.toml found")
            continue

        typer.echo(f"  Provisioning {name}...", nl=False)
        result = subprocess.run(
            [uv_path, "sync", "--directory", str(fw_dir)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            # Verify Python executable exists
            if sys.platform == "win32":
                python_path = fw_dir / ".venv" / "Scripts" / "python.exe"
            else:
                python_path = fw_dir / ".venv" / "bin" / "python"
            if python_path.exists():
                typer.echo(" OK")
            else:
                typer.echo(f" WARN (synced but python not found at {python_path})")
        else:
            typer.echo(" FAILED")
            typer.echo(f"    stderr: {result.stderr[:500]}", err=True)


@app.command(name="provision-status")
def provision_status() -> None:
    """Show which framework virtual environments are provisioned."""
    import sys
    from pathlib import Path

    frameworks_dir = Path(__file__).resolve().parent.parent.parent / "framework_venvs"

    if not frameworks_dir.exists():
        typer.echo("No frameworks directory found.")
        return

    available = sorted(
        d.name for d in frameworks_dir.iterdir()
        if d.is_dir() and (d / "pyproject.toml").exists()
    )

    if not available:
        typer.echo("No framework definitions found.")
        return

    typer.echo("Framework venv status:")
    for name in available:
        fw_dir = frameworks_dir / name
        if sys.platform == "win32":
            python_path = fw_dir / ".venv" / "Scripts" / "python.exe"
        else:
            python_path = fw_dir / ".venv" / "bin" / "python"

        if python_path.exists():
            typer.echo(f"  {name}: provisioned")
        else:
            typer.echo(f"  {name}: not provisioned")


@app.command()
def deploy(
    experiment_id: str = typer.Argument(..., help="Experiment ID to deploy"),
    tag: str | None = typer.Option(
        None,
        "--tag",
        help="Docker image tag",
    ),
    push: bool = typer.Option(
        False,
        "--push",
        help="Push image to registry after build",
    ),
    output_dir: str | None = typer.Option(
        None,
        "--output-dir",
        help="Write artifacts only (no build)",
    ),
    build: bool = typer.Option(
        True,
        "--build/--no-build",
        help="Build Docker image",
    ),
) -> None:
    """Deploy a trained model as a Docker inference container.

    Generates a Dockerfile, serve.py, and requirements.txt, then optionally
    builds a Docker image. The inference server exposes /predict, /health,
    and /info endpoints.
    """
    from pathlib import Path

    from scientist_bin_backend.deploy.builder import (
        build_docker_image,
        generate_deploy_artifacts,
        push_docker_image,
    )

    dest = Path(output_dir) if output_dir else None

    try:
        deploy_dir = generate_deploy_artifacts(experiment_id, output_dir=dest)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Deploy artifacts written to: {deploy_dir}")

    if not build:
        typer.echo("Skipping Docker build (--no-build).")
        return

    try:
        image_tag = build_docker_image(deploy_dir, tag=tag, experiment_id=experiment_id)
        typer.echo(f"Docker image built: {image_tag}")
    except RuntimeError as exc:
        typer.echo(f"Docker build failed:\n{exc}", err=True)
        raise typer.Exit(code=1) from exc

    if push:
        try:
            push_docker_image(image_tag)
            typer.echo(f"Docker image pushed: {image_tag}")
        except RuntimeError as exc:
            typer.echo(f"Docker push failed:\n{exc}", err=True)
            raise typer.Exit(code=1) from exc


@app.command()
def campaign(
    objective: str = typer.Argument(
        ...,
        help="High-level research objective",
    ),
    data_file: str = typer.Option(
        ...,
        "--data-file",
        help="Path to dataset file",
    ),
    budget: int = typer.Option(
        10,
        "--budget",
        help="Maximum number of experiments",
    ),
    time_limit: str = typer.Option(
        "4h",
        "--time-limit",
        help="Wall-clock time limit (e.g. 1h, 30m)",
    ),
    data: str = typer.Option("", "--data", help="Data description"),
) -> None:
    """Run an autonomous research campaign (long-running experiment loop).

    The campaign orchestrator generates hypotheses, runs experiments,
    extracts insights, and iterates until budget is exhausted or
    results converge.
    """
    import asyncio
    import re
    from pathlib import Path

    # Parse time limit
    match = re.match(r"^(\d+)(h|m|s)$", time_limit.strip())
    if not match:
        typer.echo(
            "Invalid time limit format. Use e.g. '4h', '30m', '300s'.",
            err=True,
        )
        raise typer.Exit(code=1)
    value, unit = int(match.group(1)), match.group(2)
    seconds = value * {"h": 3600, "m": 60, "s": 1}[unit]

    # Resolve data file
    data_path = Path(data_file)
    if not data_path.is_absolute():
        backend_data = Path(__file__).resolve().parent.parent / "data"
        candidate = backend_data / data_path
        if candidate.exists():
            data_path = candidate
    data_path = data_path.resolve()

    if not data_path.exists():
        typer.echo(f"Data file not found: {data_path}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Starting campaign: {objective}")
    typer.echo(f"  Data: {data_path}")
    typer.echo(f"  Budget: {budget} experiments, {time_limit}")

    from scientist_bin_backend.agents.campaign.agent import CampaignAgent

    agent = CampaignAgent()
    result = asyncio.run(
        agent.run(
            objective=objective,
            data_file_path=str(data_path),
            data_description=data,
            budget_max_iterations=budget,
            budget_time_limit_seconds=float(seconds),
        )
    )

    typer.echo(f"\nCampaign complete: {result.get('campaign_status', '?')}")
    best = result.get("best_result", {})
    if best:
        typer.echo(f"  Best: {best.get('algorithm', '?')}")
        metrics = best.get("metrics", {})
        for k, v in list(metrics.items())[:5]:
            typer.echo(f"    {k}: {v}")


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
    elif etype == "plan_review_pending":
        typer.echo("  [plan] Waiting for plan review...")
    elif etype in (
        "analysis_completed",
        "framework_completed",
        "summary_completed",
    ):
        typer.echo(f"  [{etype}] completed")
    elif etype == "error":
        msg = data.get("message", "Unknown error")
        typer.echo(f"  [error] {msg}")


def _print_sse_event(event_type: str, data: dict) -> None:
    """Format and print a parsed SSE event to the terminal."""
    if event_type == "phase_change":
        phase = data.get("data", {}).get("phase", "?")
        msg = data.get("data", {}).get("message", "")
        if msg:
            typer.echo(f"  [{phase}] {msg}")
    elif event_type == "experiment_done":
        best = data.get("data", {}).get("best_model", "?")
        typer.echo(f"  [done] Best model: {best}")
    elif event_type == "run_started":
        typer.echo("  [run] Started")
    elif event_type == "run_completed":
        status = data.get("data", {}).get("status", "?")
        wall = data.get("data", {}).get("wall_time_seconds", "?")
        typer.echo(f"  [run] {status} in {wall}s")
    elif event_type == "plan_review_pending":
        typer.echo("  [plan] Waiting for plan review...")
    elif event_type == "error":
        msg = data.get("data", {}).get("message", "Unknown error")
        typer.echo(f"  [error] {msg}")
    elif event_type in (
        "analysis_completed",
        "plan_completed",
        "framework_completed",
        "summary_completed",
    ):
        typer.echo(f"  [{event_type}] completed")


def _stream_remote_events(base_url: str, experiment_id: str) -> None:
    """Connect to SSE endpoint and print events until the experiment finishes."""
    import json as json_module

    import httpx

    url = f"{base_url}/api/v1/experiments/{experiment_id}/events"
    try:
        with httpx.stream("GET", url, timeout=None) as response:
            response.raise_for_status()
            event_type = ""
            for line in response.iter_lines():
                if line.startswith("event: "):
                    event_type = line[7:].strip()
                elif line.startswith("data: "):
                    raw = line[6:].strip()
                    try:
                        data = json_module.loads(raw)
                    except json_module.JSONDecodeError:
                        data = {"data": {"message": raw}}
                    _print_sse_event(event_type, data)
                    if event_type in ("experiment_done", "error"):
                        return
    except httpx.ConnectError:
        typer.echo("Server is not reachable.", err=True)
        raise typer.Exit(code=1)
    except httpx.HTTPStatusError as exc:
        typer.echo(f"Error: {exc.response.status_code} — {exc.response.text}", err=True)
        raise typer.Exit(code=1)


def _download_single_artifact(
    base_url: str,
    experiment_id: str,
    artifact_type: str,
    output_path: str | None = None,
    output_dir: str | None = None,
) -> None:
    """Download a single artifact from the server."""
    from pathlib import Path

    import httpx

    url = f"{base_url}/api/v1/experiments/{experiment_id}/artifacts/{artifact_type}"
    try:
        response = httpx.get(url)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            typer.echo(f"  {artifact_type}: not found (skipping)")
            return
        raise

    # Determine output filename from Content-Disposition or default
    cd = response.headers.get("content-disposition", "")
    if "filename=" in cd:
        filename = cd.split("filename=")[1].strip('"')
    else:
        filename = f"{experiment_id}_{artifact_type}"

    if output_path:
        dest = Path(output_path)
    elif output_dir:
        dest = Path(output_dir) / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
    else:
        dest = Path(filename)

    dest.write_bytes(response.content)
    typer.echo(f"  {artifact_type}: {dest}")


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
