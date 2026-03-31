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
    )


@app.command()
def train(
    objective: str = typer.Argument(..., help="Training objective description"),
    data: str = typer.Option("", "--data", help="Data description"),
    data_file: str | None = typer.Option(None, "--data-file", help="Path to dataset file"),
    framework: str | None = typer.Option(None, "--framework", help="Framework preference"),
) -> None:
    """Run training agent locally (no server required)."""
    import asyncio

    from scientist_bin_backend.agents.central.agent import CentralAgent
    from scientist_bin_backend.agents.central.schemas import TrainRequest

    agent = CentralAgent()
    request = TrainRequest(
        objective=objective,
        data_description=data,
        data_file_path=data_file,
        framework_preference=framework,
    )
    result = asyncio.run(agent.run(request))
    typer.echo(result.model_dump_json(indent=2))


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
