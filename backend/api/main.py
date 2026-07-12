from __future__ import annotations

from fastapi import FastAPI

from backend.api.routes import campaigns, jobs, health, policy, audit, metrics, admin, automation
from backend.api.middleware import auth_rate_limit_and_audit_middleware
from backend.db.models import Base
from backend.db.session import engine
from backend.observability.telemetry import setup_telemetry


from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(title="HRM AI API", version="0.1.0")

    @app.on_event("startup")
    def ensure_database_schema() -> None:
        Base.metadata.create_all(bind=engine)

    # Enable CORS for frontend requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(auth_rate_limit_and_audit_middleware)

    app.include_router(health.router, tags=["health"])
    app.include_router(automation.router, prefix="/automation", tags=["automation"])
    app.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
    app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
    app.include_router(policy.router, prefix="/policy", tags=["policy"])
    app.include_router(audit.router, prefix="/audit", tags=["audit"])
    app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
    app.include_router(admin.router, prefix="/admin", tags=["admin"])
    setup_telemetry(app)

    return app


app = create_app()
