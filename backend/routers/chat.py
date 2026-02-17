from __future__ import annotations

import json
import time
import uuid

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from backend.models.api_models import ApiResponse, ChatRequest, SuggestedQuestion

router = APIRouter(prefix="/chat", tags=["chat"])

SUGGESTED_QUESTIONS = [
    SuggestedQuestion(
        question="Which contractors have the most single-source contracts?",
        category="red_flags",
        description="Find contractors that frequently win without competition",
    ),
    SuggestedQuestion(
        question="Show me the top 5 agencies by procurement concentration",
        category="analytics",
        description="Agencies where a few contractors dominate",
    ),
    SuggestedQuestion(
        question="Which contractors bid together most frequently?",
        category="network",
        description="Identify co-bidding patterns that may indicate collusion",
    ),
    SuggestedQuestion(
        question="What are the biggest contracts awarded this year?",
        category="procurement",
        description="Largest government contracts by value",
    ),
    SuggestedQuestion(
        question="Are there contractors with political family connections?",
        category="red_flags",
        description="Ownership chains linking contractors to politicians",
    ),
    SuggestedQuestion(
        question="Which agencies have the most audit findings?",
        category="accountability",
        description="Agencies with repeated COA observations",
    ),
    SuggestedQuestion(
        question="Show me contractors winning in regions far from their address",
        category="red_flags",
        description="Geographic anomalies in contract awards",
    ),
    SuggestedQuestion(
        question="What is the total procurement value by agency type?",
        category="analytics",
        description="Breakdown of spending across national and local agencies",
    ),
]


@router.post("")
async def chat(request: Request, body: ChatRequest):
    """Stream GraphRAG answer via SSE."""
    graphrag = request.app.state.graphrag_service
    message_id = str(uuid.uuid4())

    # user-provided key for this request only (never stored)
    api_key = request.headers.get("x-api-key")

    context = None
    if body.context:
        context = body.context.model_dump()

    history = None
    if body.history:
        history = [{"role": m.role, "content": m.content} for m in body.history]

    async def event_generator():
        start = time.monotonic()

        # send message ID
        yield {"event": "message_id", "data": json.dumps({"message_id": message_id})}

        try:
            async for event in graphrag.answer_stream(
                body.message, context=context, history=history, api_key=api_key
            ):
                yield {"event": event["event"], "data": event["data"]}
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"code": "LLM_ERROR", "message": str(e)}),
            }

        elapsed = (time.monotonic() - start) * 1000
        yield {
            "event": "meta",
            "data": json.dumps({"query_time_ms": round(elapsed, 1)}),
        }

    return EventSourceResponse(event_generator())


@router.get("/suggestions")
async def suggestions() -> ApiResponse[list[SuggestedQuestion]]:
    return ApiResponse(
        data=SUGGESTED_QUESTIONS,
        meta={"count": len(SUGGESTED_QUESTIONS)},
    )
