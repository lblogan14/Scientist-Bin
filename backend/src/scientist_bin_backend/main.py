"""FastAPI application factory and entry point."""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from scientist_bin_backend.api.routes import router
from scientist_bin_backend.config.settings import get_settings


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title="Scientist-Bin",
        version="0.1.0",
        description="Multi-agent system for automated data science model training and evaluation",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(router)

    @application.get("/")
    async def root() -> dict:
        return {
            "name": "Scientist-Bin",
            "version": "0.1.0",
            "docs": "/docs",
        }

    return application


app = create_app()
