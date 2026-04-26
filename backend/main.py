from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routes import agents as agents_routes
from backend.routes import generate as generate_routes
from backend.routes import idea as idea_routes
from backend.routes import trends as trends_routes
from backend.workers.trends_worker import start_scheduler, stop_scheduler

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    await init_db()
    start_scheduler()
    log.info("app.started")
    yield
    stop_scheduler()


app = FastAPI(
    title="ContentForge-AI",
    description="Local-first AI-powered YouTube automation platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(idea_routes.router)
app.include_router(agents_routes.router)
app.include_router(generate_routes.router)
app.include_router(trends_routes.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict:
    return {
        "name": "ContentForge-AI",
        "docs": "/docs",
        "endpoints": ["/idea/submit", "/agents/status", "/generate/final", "/trends"],
    }
