from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from storage.database import init_db
from api import (
    repo_router,
    graph_router,
    ask_router,
    summary_router,
    jobs_router,
    search_router,
)

log = structlog.get_logger()

app = FastAPI(
    title="DCRS — Developer Context Recovery System",
    description="Repository intelligence platform. Understand any codebase in 10 minutes.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repo_router)
app.include_router(graph_router)
app.include_router(ask_router)
app.include_router(summary_router)
app.include_router(jobs_router)
app.include_router(search_router)


@app.on_event("startup")
async def startup():
    log.info("DCRS backend starting up")
    await init_db()
    log.info("Application startup complete")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "dcrs-backend"}


@app.get("/")
async def root():
    return {
        "service": "DCRS",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": [
            "POST /repo",
            "POST /repo/upload",
            "GET  /repo/{id}",
            "GET  /graph/{repo_id}",
            "POST /ask",
            "GET  /summary/{repo_id}",
            "GET  /search/{repo_id}?q=",
            "GET  /jobs/{repo_id}",
        ],
    }
