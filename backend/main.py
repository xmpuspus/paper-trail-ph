from __future__ import annotations

import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from neo4j import AsyncGraphDatabase

from backend.config import settings
from backend.routers import analytics, chat, graph, pipeline
from backend.services.graphrag_service import GraphRAGService
from backend.services.llm_service import LLMService
from backend.services.neo4j_service import Neo4jService
from backend.services.red_flag_service import RedFlagService

logger = logging.getLogger("paper-trail-ph")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
)

# in-memory rate limiter: tracks {ip: [(timestamp, ...),]}
_rate_limits: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))


def _check_rate_limit(
    ip: str, bucket: str, max_requests: int, window: float = 60.0
) -> bool:
    """Return True if request is allowed, False if rate limited."""
    now = time.monotonic()
    timestamps = _rate_limits[ip][bucket]
    # prune expired entries
    _rate_limits[ip][bucket] = [t for t in timestamps if now - t < window]
    if len(_rate_limits[ip][bucket]) >= max_requests:
        return False
    _rate_limits[ip][bucket].append(now)
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: init Neo4j driver and services
    logger.info("Connecting to Neo4j at %s", settings.neo4j_uri)
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    # verify connectivity
    try:
        await driver.verify_connectivity()
        logger.info("Neo4j connection established")
    except Exception as e:
        logger.error("Failed to connect to Neo4j: %s", e)
        # store driver anyway so endpoints can return proper errors

    app.state.neo4j_driver = driver
    app.state.neo4j_service = Neo4jService(driver)
    app.state.red_flag_service = RedFlagService(driver)
    app.state.llm_service = LLMService()
    app.state.graphrag_service = GraphRAGService(
        app.state.neo4j_service,
        app.state.llm_service,
    )

    yield

    # shutdown
    logger.info("Closing Neo4j driver")
    await driver.close()


app = FastAPI(
    title="paper-trail-ph",
    description="Philippine Public Accountability Graph API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend origin (configurable for production)
_cors_origins = [o.strip() for o in (settings.cors_origins or "http://localhost:3000").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next) -> Response:
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    if path.startswith("/api/v1/chat"):
        if not _check_rate_limit(client_ip, "chat", settings.chat_rate_limit):
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Too many chat requests. Please wait before trying again.",
                    },
                },
            )
    elif path.startswith("/api/v1/") and not _check_rate_limit(
        client_ip,
        "graph",
        settings.graph_rate_limit,
    ):
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "RATE_LIMITED",
                    "message": "Too many requests. Please wait before trying again.",
                },
            },
        )

    return await call_next(request)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            },
        },
    )


# mount routers under /api/v1
app.include_router(graph.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(pipeline.router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, Any]:
    neo4j_ok = False
    try:
        driver = app.state.neo4j_driver
        await driver.verify_connectivity()
        neo4j_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if neo4j_ok else "degraded",
        "neo4j": "connected" if neo4j_ok else "disconnected",
        "version": "0.1.0",
    }
