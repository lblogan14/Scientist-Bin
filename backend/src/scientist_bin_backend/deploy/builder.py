"""Docker inference container builder.

Generates deployment artifacts (Dockerfile, serve.py, requirements.txt, metadata.json)
and optionally builds a Docker image for serving a trained model.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

from scientist_bin_backend.deploy.templates import (
    DOCKERFILE_TEMPLATE,
    REQUIREMENTS_TEMPLATE,
    SERVE_TEMPLATE,
)

logger = logging.getLogger(__name__)

_OUTPUTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "outputs"


def _get_package_version(package: str) -> str:
    """Get installed version of a Python package."""
    try:
        from importlib.metadata import version

        return version(package)
    except Exception:
        return "latest"


def _build_metadata(experiment_id: str, result_path: Path) -> dict:
    """Build metadata dict from the experiment result JSON."""
    metadata: dict = {"experiment_id": experiment_id}

    if result_path.exists():
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
            metadata["algorithm"] = result.get("best_model", "unknown")
            metadata["problem_type"] = result.get("problem_type", "classification")
            metadata["framework"] = result.get("framework", "sklearn")
            metadata["best_hyperparameters"] = result.get("best_hyperparameters", {})
            metadata["test_metrics"] = result.get("test_metrics", {})

            # Extract feature names from data profile if available
            data_profile = result.get("data_profile")
            if data_profile and isinstance(data_profile, dict):
                metadata["feature_columns"] = data_profile.get("column_names", [])
                metadata["n_features"] = data_profile.get("n_features")
                metadata["n_samples"] = data_profile.get("n_samples")
        except Exception:
            logger.warning("Could not parse result JSON for %s", experiment_id)

    return metadata


def generate_deploy_artifacts(
    experiment_id: str,
    output_dir: Path | None = None,
) -> Path:
    """Generate all deployment artifacts for an experiment.

    Creates a deploy directory containing:
      - Dockerfile
      - requirements.txt
      - serve.py
      - model.joblib (copied)
      - metadata.json

    Args:
        experiment_id: The experiment ID to deploy.
        output_dir: Where to write the artifacts. Defaults to
                    outputs/deploy/{experiment_id}/

    Returns:
        Path to the output directory.

    Raises:
        FileNotFoundError: If the model file doesn't exist.
    """
    model_path = _OUTPUTS_DIR / "models" / f"{experiment_id}.joblib"
    result_path = _OUTPUTS_DIR / "results" / f"{experiment_id}.json"

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}\n"
            f"Run 'scientist-bin train' first to produce a model."
        )

    if output_dir is None:
        output_dir = _OUTPUTS_DIR / "deploy" / experiment_id

    output_dir.mkdir(parents=True, exist_ok=True)

    # Build metadata
    metadata = _build_metadata(experiment_id, result_path)

    # Write metadata.json
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, default=str),
        encoding="utf-8",
    )

    # Copy model
    shutil.copy2(model_path, output_dir / "model.joblib")

    # Write Dockerfile
    (output_dir / "Dockerfile").write_text(
        DOCKERFILE_TEMPLATE.format(experiment_id=experiment_id),
        encoding="utf-8",
    )

    # Write requirements.txt
    (output_dir / "requirements.txt").write_text(
        REQUIREMENTS_TEMPLATE.format(
            sklearn_version=_get_package_version("scikit-learn"),
            pandas_version=_get_package_version("pandas"),
            numpy_version=_get_package_version("numpy"),
            joblib_version=_get_package_version("joblib"),
        ),
        encoding="utf-8",
    )

    # Write serve.py
    (output_dir / "serve.py").write_text(
        SERVE_TEMPLATE.format(
            experiment_id=experiment_id,
            algorithm=metadata.get("algorithm", "unknown"),
            problem_type=metadata.get("problem_type", "classification"),
        ),
        encoding="utf-8",
    )

    logger.info("Deploy artifacts written to %s", output_dir)
    return output_dir


def build_docker_image(
    deploy_dir: Path,
    tag: str | None = None,
    experiment_id: str = "",
) -> str:
    """Build a Docker image from the generated deploy artifacts.

    Args:
        deploy_dir: Directory containing the Dockerfile and artifacts.
        tag: Docker image tag. Defaults to scientist-bin/{experiment_id}:latest.
        experiment_id: Used for default tag generation.

    Returns:
        The Docker image tag.

    Raises:
        RuntimeError: If docker build fails.
    """
    if tag is None:
        safe_id = experiment_id.replace("/", "-").replace("\\", "-")
        tag = f"scientist-bin/{safe_id}:latest"

    logger.info("Building Docker image: %s", tag)

    result = subprocess.run(
        ["docker", "build", "-t", tag, "."],
        cwd=deploy_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Docker build failed (exit code {result.returncode}):\n{result.stderr}"
        )

    logger.info("Docker image built: %s", tag)
    return tag


def push_docker_image(tag: str) -> None:
    """Push a Docker image to the registry.

    Args:
        tag: The Docker image tag to push.

    Raises:
        RuntimeError: If docker push fails.
    """
    logger.info("Pushing Docker image: %s", tag)

    result = subprocess.run(
        ["docker", "push", tag],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Docker push failed (exit code {result.returncode}):\n{result.stderr}"
        )

    logger.info("Docker image pushed: %s", tag)
