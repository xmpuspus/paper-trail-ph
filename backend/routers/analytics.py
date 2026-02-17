from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException, Query, Request

from backend.models.api_models import (
    AgencyConcentration,
    ApiResponse,
    ContractorProfile,
    GraphStats,
    RedFlagItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _get_neo4j_service(request: Request):
    return request.app.state.neo4j_service


@router.get("/agency/{agency_id}/concentration")
async def agency_concentration(
    request: Request,
    agency_id: str,
) -> ApiResponse[AgencyConcentration]:
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    result = await svc.get_agency_concentration(agency_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Agency {agency_id} not found",
                },
            },
        )
    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=AgencyConcentration(**result),
        meta={
            "query_time_ms": round(elapsed, 1),
            "source": "neo4j",
        },
    )


@router.get("/contractor/{contractor_id}/profile")
async def contractor_profile(
    request: Request,
    contractor_id: str,
) -> ApiResponse[ContractorProfile]:
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    result = await svc.get_contractor_profile(contractor_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Contractor {contractor_id} not found",
                },
            },
        )
    elapsed = (time.monotonic() - start) * 1000

    # fetch red flags for the contractor
    red_flag_svc = request.app.state.red_flag_service
    contractor_flags = []
    try:
        single_bidder = await red_flag_svc.single_bidder_contracts(threshold=1)
        for flag in single_bidder:
            if flag.evidence.get("contractor_id") == contractor_id:
                contractor_flags.append(flag)
    except Exception:
        pass  # red flag detection is best-effort

    result["red_flags"] = contractor_flags
    return ApiResponse(
        data=ContractorProfile(**result),
        meta={
            "query_time_ms": round(elapsed, 1),
            "source": "neo4j",
        },
    )


@router.get("/red-flags")
async def get_red_flags(
    request: Request,
    severity: str | None = Query(
        None, description="Filter by severity: critical, high, medium, low"
    ),
    limit: int = Query(50, ge=1, le=200),
) -> ApiResponse[list[RedFlagItem]]:
    start = time.monotonic()
    red_flag_svc = request.app.state.red_flag_service

    all_flags = await red_flag_svc.detect_all()

    # group flags by entity
    entity_map: dict[str, RedFlagItem] = {}
    severity_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}

    for _category, flags in all_flags.items():
        for flag in flags:
            # determine entity_id and entity_name from evidence
            eid = (
                flag.evidence.get("contractor_id")
                or flag.evidence.get("agency_id")
                or flag.evidence.get("contract_id")
                or flag.evidence.get("contractor1_id")
                or "unknown"
            )
            ename = (
                flag.evidence.get("contractor_name")
                or flag.evidence.get("agency_name")
                or flag.evidence.get("bidder1")
                or flag.evidence.get("contractor1")
                or "Unknown"
            )
            etype = "Contractor"
            if flag.evidence.get("agency_id"):
                etype = "Agency"

            if eid not in entity_map:
                entity_map[eid] = RedFlagItem(
                    entity_id=str(eid),
                    entity_name=str(ename),
                    entity_type=etype,
                    red_flags=[],
                    risk_score=0.0,
                )
            entity_map[eid].red_flags.append(flag)
            entity_map[eid].risk_score += severity_weights.get(flag.severity.value, 1)

    # filter by severity if requested
    items = list(entity_map.values())
    if severity:
        items = [
            item
            for item in items
            if any(f.severity.value == severity for f in item.red_flags)
        ]

    # sort by risk score descending, then limit
    items.sort(key=lambda x: x.risk_score, reverse=True)
    items = items[:limit]

    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=items,
        meta={
            "query_time_ms": round(elapsed, 1),
            "node_count": len(items),
            "source": "neo4j",
        },
    )


@router.get("/stats")
async def get_stats(request: Request) -> ApiResponse[GraphStats]:
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    stats = await svc.get_stats()
    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=GraphStats(**stats),
        meta={
            "query_time_ms": round(elapsed, 1),
            "source": "neo4j",
        },
    )


@router.get("/network/communities")
async def get_network_communities(
    request: Request,
    min_connections: int = Query(
        3, ge=1, le=10, description="Minimum connections to be included in a community"
    ),
) -> ApiResponse[list[dict]]:
    """Detect communities of tightly connected entities."""
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    communities = await svc.get_network_communities(min_connections=min_connections)
    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=communities,
        meta={
            "query_time_ms": round(elapsed, 1),
            "community_count": len(communities),
            "source": "neo4j",
        },
    )


@router.get("/subcontract-cycles/{contractor_id}")
async def get_subcontract_cycles(
    request: Request,
    contractor_id: str,
) -> ApiResponse[list[dict]]:
    """Returns circular subcontracting paths involving a contractor."""
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    cycles = await svc.get_subcontract_cycles(contractor_id)
    if not cycles:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"No subcontract cycles found for contractor {contractor_id}",
                },
            },
        )
    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=cycles,
        meta={
            "query_time_ms": round(elapsed, 1),
            "cycle_count": len(cycles),
            "source": "neo4j",
        },
    )


@router.get("/campaign-contracts/{politician_id}")
async def get_campaign_contracts(
    request: Request,
    politician_id: str,
) -> ApiResponse[list[dict]]:
    """Returns campaign donation to contract paths for a politician."""
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    paths = await svc.get_campaign_contract_paths(politician_id)
    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=paths,
        meta={
            "query_time_ms": round(elapsed, 1),
            "path_count": len(paths),
            "source": "neo4j",
        },
    )


@router.get("/phoenix-companies")
async def get_phoenix_companies(
    request: Request,
) -> ApiResponse[list[dict]]:
    """Returns all phoenix company pairs detected."""
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    companies = await svc.get_phoenix_companies()
    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=companies,
        meta={
            "query_time_ms": round(elapsed, 1),
            "pair_count": len(companies),
            "source": "neo4j",
        },
    )


@router.get("/saln-timeline/{politician_id}")
async def get_saln_timeline(
    request: Request,
    politician_id: str,
) -> ApiResponse[list[dict]]:
    """Returns SALN wealth over time for a politician."""
    start = time.monotonic()
    svc = _get_neo4j_service(request)
    timeline = await svc.get_saln_timeline(politician_id)
    if not timeline:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"No SALN records found for politician {politician_id}",
                },
            },
        )
    elapsed = (time.monotonic() - start) * 1000
    return ApiResponse(
        data=timeline,
        meta={
            "query_time_ms": round(elapsed, 1),
            "record_count": len(timeline),
            "source": "neo4j",
        },
    )
