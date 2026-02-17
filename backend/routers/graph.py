from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Query, Request

from backend.models.api_models import ApiResponse
from backend.models.graph_models import (
    GraphData,
    NodeDetail,
    PathResult,
    SearchResult,
)

router = APIRouter(prefix="/graph", tags=["graph"])


def _get_neo4j_service(request: Request):
    return request.app.state.neo4j_service


@router.get("/node/{node_id}")
async def get_node(request: Request, node_id: str) -> ApiResponse[NodeDetail]:
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    detail = await svc.get_node_detail(node_id)
    if not detail:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Entity with ID {node_id} not found",
                },
            },
        )
    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=NodeDetail(**detail),
        meta={
            "query_time_ms": round(elapsed, 1),
            "node_count": 1 + len(detail["neighbors"]),
            "edge_count": len(detail["edges"]),
            "source": "neo4j",
        },
    )


@router.get("/node/{node_id}/neighbors")
async def get_neighbors(
    request: Request,
    node_id: str,
    type: str | None = Query(None, description="Filter by node type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ApiResponse[GraphData]:
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    result = await svc.get_neighbors(
        node_id, node_type_filter=type, limit=limit, offset=offset
    )
    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=GraphData(nodes=result["nodes"], edges=result["edges"]),
        meta={
            "query_time_ms": round(elapsed, 1),
            "node_count": len(result["nodes"]),
            "edge_count": len(result["edges"]),
            "source": "neo4j",
        },
    )


@router.get("/search")
async def search(
    request: Request,
    q: str = Query(..., min_length=1, description="Search term"),
    type: str | None = Query(None, description="Filter by node type"),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[list[SearchResult]]:
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    results = await svc.search(q, node_type=type, limit=limit)
    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=results,
        meta={
            "query_time_ms": round(elapsed, 1),
            "node_count": len(results),
            "edge_count": 0,
            "source": "neo4j",
        },
    )


@router.get("/path")
async def get_path(
    request: Request,
    from_id: str = Query(..., alias="from", description="Source node ID"),
    to_id: str = Query(..., alias="to", description="Target node ID"),
    max_depth: int = Query(6, ge=1, le=10),
) -> ApiResponse[PathResult]:
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    result = await svc.get_path(from_id, to_id, max_depth=max_depth)
    if not result:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NO_PATH",
                    "message": f"No path found between {from_id} and {to_id} within {max_depth} hops",
                },
            },
        )
    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=PathResult(**result),
        meta={
            "query_time_ms": round(elapsed, 1),
            "node_count": len(result["nodes"]),
            "edge_count": len(result["edges"]),
            "source": "neo4j",
        },
    )


@router.get("/overview")
async def get_overview(
    request: Request,
    limit: int = Query(200, ge=1, le=500),
) -> ApiResponse[GraphData]:
    """Return the full graph for the initial overview."""
    start = time.monotonic()
    svc = _get_neo4j_service(request)

    from backend.models.graph_models import (
        GraphNode as GN,
        NodeType as NT,
        GraphEdge as GE,
        EdgeType as ET,
    )

    def _safe_props(raw: dict) -> dict:
        """Convert neo4j native types to JSON-serializable values."""
        out = {}
        for k, v in raw.items():
            if hasattr(v, "iso_format"):
                out[k] = v.iso_format()
            elif hasattr(v, "isoformat"):
                out[k] = v.isoformat()
            else:
                out[k] = v
        return out

    node_type_order = [
        "Politician",
        "PoliticalFamily",
        "Municipality",
        "Agency",
        "Contract",
        "Contractor",
        "AuditFinding",
        "Bill",
        "Person",
    ]

    nodes_query = """
    MATCH (n)
    RETURN n, labels(n) as labels, elementId(n) as eid
    LIMIT $limit
    """
    async with svc.driver.session() as session:
        result = await session.run(nodes_query, limit=limit)
        node_ids = []
        nodes = []
        seen = set()
        async for record in result:
            rec = dict(record)
            node = rec["n"]
            eid = str(rec["eid"])
            if eid in seen:
                continue
            seen.add(eid)
            node_ids.append(eid)
            labels = rec["labels"]
            props = _safe_props(dict(node))
            node_type = next((nt for nt in node_type_order if nt in labels), "Person")
            label = props.pop(
                "name", props.get("title", props.get("reference_number", ""))
            )
            risk = props.pop("risk_score", None)
            nodes.append(
                GN(
                    id=eid,
                    label=str(label),
                    type=NT(node_type),
                    properties=props,
                    risk_score=risk,
                )
            )

        edges_query = """
        MATCH (a)-[r]->(b)
        WHERE elementId(a) IN $ids AND elementId(b) IN $ids
        RETURN r, type(r) as rel_type, elementId(r) as rid,
               elementId(startNode(r)) as src, elementId(endNode(r)) as tgt
        """
        result = await session.run(edges_query, ids=node_ids)
        edges = []
        seen_edges = set()
        et_map = {e.value: e for e in ET}
        async for record in result:
            rec = dict(record)
            rid = str(rec["rid"])
            if rid in seen_edges:
                continue
            seen_edges.add(rid)
            rel = rec["r"]
            props = _safe_props(dict(rel))
            et = et_map.get(rec["rel_type"], ET.AWARDED_TO)
            edges.append(
                GE(
                    id=rid,
                    source=str(rec["src"]),
                    target=str(rec["tgt"]),
                    type=et,
                    properties=props,
                )
            )

    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=GraphData(nodes=nodes, edges=edges),
        meta={
            "query_time_ms": round(elapsed, 1),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "source": "neo4j",
        },
    )


@router.get("/subgraph")
async def get_subgraph(
    request: Request,
    center: str = Query(..., description="Center node ID"),
    depth: int = Query(2, ge=1, le=4),
) -> ApiResponse[GraphData]:
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    result = await svc.get_subgraph(center, depth=depth)
    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=GraphData(nodes=result["nodes"], edges=result["edges"]),
        meta={
            "query_time_ms": round(elapsed, 1),
            "node_count": len(result["nodes"]),
            "edge_count": len(result["edges"]),
            "source": "neo4j",
        },
    )


@router.get("/community/{community_id}")
async def get_community(
    request: Request,
    community_id: str,
) -> ApiResponse[dict]:
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    result = await svc.get_community(community_id)
    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data={
            "nodes": [n.model_dump(mode="json") for n in result["nodes"]],
            "edges": [e.model_dump(mode="json") for e in result["edges"]],
            "summary": result.get("summary", ""),
        },
        meta={
            "query_time_ms": round(elapsed, 1),
            "node_count": len(result["nodes"]),
            "edge_count": len(result["edges"]),
            "source": "neo4j",
        },
    )
