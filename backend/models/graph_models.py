from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    POLITICIAN = "Politician"
    POLITICAL_FAMILY = "PoliticalFamily"
    MUNICIPALITY = "Municipality"
    AGENCY = "Agency"
    CONTRACT = "Contract"
    CONTRACTOR = "Contractor"
    AUDIT_FINDING = "AuditFinding"
    BILL = "Bill"
    PERSON = "Person"
    CAMPAIGN_DONATION = "CampaignDonation"
    BLACKLIST_ENTRY = "BlacklistEntry"
    SALN_RECORD = "SALNRecord"


class EdgeType(str, Enum):
    MEMBER_OF = "MEMBER_OF"
    GOVERNS = "GOVERNS"
    HAS_AGENCY = "HAS_AGENCY"
    PROCURED = "PROCURED"
    AWARDED_TO = "AWARDED_TO"
    BID_ON = "BID_ON"
    CO_BID_WITH = "CO_BID_WITH"
    SUBCONTRACTED_TO = "SUBCONTRACTED_TO"
    AUDITED = "AUDITED"
    INVOLVES_OFFICIAL = "INVOLVES_OFFICIAL"
    AUTHORED = "AUTHORED"
    CO_AUTHORED_WITH = "CO_AUTHORED_WITH"
    OWNED_BY = "OWNED_BY"
    FAMILY_OF = "FAMILY_OF"
    LOCATED_IN = "LOCATED_IN"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    DONATED_TO = "DONATED_TO"
    BLACKLISTED = "BLACKLISTED"
    DECLARED_WEALTH = "DECLARED_WEALTH"
    RE_REGISTERED_AS = "RE_REGISTERED_AS"
    SAME_ADDRESS_AS = "SAME_ADDRESS_AS"
    SHARES_DIRECTOR_WITH = "SHARES_DIRECTOR_WITH"
    ALLIED_WITH = "ALLIED_WITH"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GraphNode(BaseModel):
    id: str
    label: str
    type: NodeType
    properties: dict[str, Any] = Field(default_factory=dict)
    risk_score: float | None = None
    red_flags: list[RedFlag] | None = None


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: EdgeType
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class RedFlag(BaseModel):
    type: str
    severity: Severity
    description: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class NodeDetail(BaseModel):
    node: GraphNode
    neighbors: list[GraphNode]
    edges: list[GraphEdge]
    stats: dict[str, Any] = Field(default_factory=dict)


class PathResult(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    length: int


class SearchResult(BaseModel):
    id: str
    name: str
    type: NodeType
    context: str = ""
    score: float = 0.0


# forward ref update
GraphNode.model_rebuild()
