from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from backend.models.graph_models import RedFlag

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    data: T
    meta: dict[str, Any] = Field(default_factory=dict)


class ApiError(BaseModel):
    error: dict[str, str]


class ChatContext(BaseModel):
    focused_node_id: str | None = None
    visible_node_ids: list[str] | None = None


class ChatHistoryMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    context: ChatContext | None = None
    history: list[ChatHistoryMessage] | None = None


class ChatMessage(BaseModel):
    id: str
    role: str  # "user" | "assistant"
    content: str
    graph_context: dict[str, Any] | None = None
    sources: list[str] | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgencyConcentration(BaseModel):
    agency_id: str
    agency_name: str
    hhi: float
    top_contractors: list[dict[str, Any]]
    procurement_methods: list[dict[str, Any]]
    total_contracts: int
    total_value: float


class ContractorProfile(BaseModel):
    contractor_id: str
    name: str
    registration_number: str | None = None
    classification: str | None = None
    total_contracts: int = 0
    total_value: float = 0.0
    agencies: list[dict[str, Any]] = Field(default_factory=list)
    co_bidders: list[dict[str, Any]] = Field(default_factory=list)
    win_rate: float = 0.0
    red_flags: list[RedFlag] = Field(default_factory=list)


class GraphStats(BaseModel):
    total_nodes: int = 0
    total_edges: int = 0
    node_counts: dict[str, int] = Field(default_factory=dict)
    edge_counts: dict[str, int] = Field(default_factory=dict)
    total_contract_value: float = 0.0
    date_range: dict[str, str | None] = Field(default_factory=dict)


class PipelineStatus(BaseModel):
    source: str
    last_updated: datetime | None = None
    record_count: int = 0
    status: str = "unknown"


class CoverageReport(BaseModel):
    node_counts: dict[str, int] = Field(default_factory=dict)
    edge_counts: dict[str, int] = Field(default_factory=dict)


class RedFlagItem(BaseModel):
    entity_id: str
    entity_name: str
    entity_type: str
    red_flags: list[RedFlag]
    risk_score: float = 0.0


class SuggestedQuestion(BaseModel):
    question: str
    category: str
    description: str = ""
