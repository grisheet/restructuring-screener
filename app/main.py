"""FastAPI application factory for the Restructuring Screener."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import companies, events, screens, watchlists, health
from app.database.session import engine
from app.database.base import Base


def create_app() -> FastAPI:
    app = FastAPI(
        title="Restructuring Screener",
        description="Event-driven corporate restructuring screener with explainable scoring",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, tags=["health"])
    app.include_router(companies.router, prefix="/companies", tags=["companies"])
    app.include_router(events.router, prefix="/events", tags=["events"])
    app.include_router(screens.router, prefix="/screens", tags=["screens"])
    app.include_router(watchlists.router, prefix="/watchlists", tags=["watchlists"])

    return app


app = create_app()
