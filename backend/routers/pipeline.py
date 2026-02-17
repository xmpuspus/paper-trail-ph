from __future__ import annotations

import time

from fastapi import APIRouter, Request

from backend.models.api_models import ApiResponse, CoverageReport, PipelineStatus
from backend.models.graph_models import EdgeType, NodeType

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/status")
async def pipeline_status(request: Request) -> ApiResponse[list[PipelineStatus]]:
    """Return last update times per data source, read from pipeline metadata in Neo4j."""
    start = time.monotonic()
    sources = ["philgeps", "open_congress", "dynasties", "coa", "psgc"]
    statuses: list[PipelineStatus] = []

    driver = request.app.state.neo4j_driver
    async with driver.session() as session:
        for source in sources:
            result = await session.run(
                "MATCH (m:PipelineMeta {source: $source}) "
                "RETURN m.last_updated as last_updated, m.record_count as record_count, "
                "m.status as status",
                source=source,
            )
            record = await result.single()
            if record:
                statuses.append(
                    PipelineStatus(
                        source=source,
                        last_updated=record["last_updated"],
                        record_count=int(record["record_count"] or 0),
                        status=record["status"] or "unknown",
                    )
                )
            else:
                statuses.append(PipelineStatus(source=source))

    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=statuses,
        meta={"query_time_ms": round(elapsed, 1), "source": "neo4j"},
    )


@router.get("/coverage")
async def pipeline_coverage(request: Request) -> ApiResponse[CoverageReport]:
    """Return node/edge counts by type."""
    start = time.monotonic()
    driver = request.app.state.neo4j_driver

    node_counts: dict[str, int] = {}
    edge_counts: dict[str, int] = {}

    async with driver.session() as session:
        for nt in NodeType:
            result = await session.run(f"MATCH (n:{nt.value}) RETURN count(n) as cnt")
            record = await result.single()
            node_counts[nt.value] = record["cnt"] if record else 0

        for et in EdgeType:
            result = await session.run(
                f"MATCH ()-[r:{et.value}]->() RETURN count(r) as cnt"
            )
            record = await result.single()
            edge_counts[et.value] = record["cnt"] if record else 0

    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=CoverageReport(node_counts=node_counts, edge_counts=edge_counts),
        meta={"query_time_ms": round(elapsed, 1), "source": "neo4j"},
    )
