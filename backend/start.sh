#!/usr/bin/env bash
# ============================================================
#  Scientist-Bin Backend — Linux / macOS Startup Script
# ============================================================
#  Prerequisites: Python 3.11+, uv (https://docs.astral.sh/uv/)
#  Usage:  ./start.sh              (default: port 8000)
#          ./start.sh --port 9000  (custom port)
# ============================================================

set -euo pipefail

cd "$(dirname "$0")"

# -- Parse optional --port argument (default 8000) --
PORT=8000
while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# -- Check for .env --
if [[ ! -f .env ]]; then
    if [[ -f .env.example ]]; then
        echo "[WARNING] No .env file found. Copying .env.example to .env"
        echo "          Please edit .env and set your GOOGLE_API_KEY."
        cp .env.example .env
    else
        echo "[ERROR] No .env or .env.example found. Create a .env with GOOGLE_API_KEY."
        exit 1
    fi
fi

# -- Install / sync dependencies --
echo "[1/2] Syncing dependencies..."
uv sync --all-groups

# -- Start the server --
echo "[2/2] Starting Scientist-Bin backend on port ${PORT}..."
echo "       API docs: http://localhost:${PORT}/docs"
echo "       Health:   http://localhost:${PORT}/api/v1/health"
echo ""
uv run uvicorn scientist_bin_backend.main:app --host 0.0.0.0 --port "${PORT}" --reload
