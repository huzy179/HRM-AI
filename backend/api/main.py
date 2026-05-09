from __future__ import annotations

from fastapi import FastAPI

from backend.api.routes import campaigns, jobs, health


def create_app() -> FastAPI:
    app = FastAPI(title="HRM AI API", version="0.1.0")

    app.include_router(health.router, tags=["health"])
    app.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
    app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

    return app


app = create_app()

