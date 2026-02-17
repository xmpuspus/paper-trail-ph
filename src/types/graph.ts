export type NodeType =
  | "Politician"
  | "PoliticalFamily"
  | "Municipality"
  | "Agency"
  | "Contract"
  | "Contractor"
  | "AuditFinding"
  | "Bill"
  | "Person"
  | "CampaignDonation"
  | "BlacklistEntry"
  | "SALNRecord";

export type EdgeType =
  | "MEMBER_OF"
  | "GOVERNS"
  | "HAS_AGENCY"
  | "PROCURED"
  | "AWARDED_TO"
  | "BID_ON"
  | "CO_BID_WITH"
  | "SUBCONTRACTED_TO"
  | "AUDITED"
  | "INVOLVES_OFFICIAL"
  | "AUTHORED"
  | "CO_AUTHORED_WITH"
  | "OWNED_BY"
  | "FAMILY_OF"
  | "LOCATED_IN"
  | "ASSOCIATED_WITH"
  | "DONATED_TO"
  | "BLACKLISTED"
  | "DECLARED_WEALTH"
  | "RE_REGISTERED_AS"
  | "SAME_ADDRESS_AS"
  | "SHARES_DIRECTOR_WITH"
  | "ALLIED_WITH";

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  properties: Record<string, unknown>;
  risk_score?: number;
  red_flags?: RedFlag[];
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  properties: Record<string, unknown>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface RedFlag {
  type: RedFlagType;
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  evidence: string;
  detected_at: string;
}

export type RedFlagType =
  | "single_bidder"
  | "identical_bid_amounts"
  | "rotating_winners"
  | "split_contracts"
  | "abnormal_pricing"
  | "geographic_anomaly"
  | "timing_cluster"
  | "concentration"
  | "collusion_ring"
  | "political_connection"
  | "shell_network"
  | "cross_agency_pattern"
  | "audit_repeat"
  | "shell_company"
  | "phoenix_company"
  | "campaign_connection"
  | "circular_flow";

export interface NodeDetail {
  node: GraphNode;
  neighbors: GraphNode[];
  edges: GraphEdge[];
  stats: Record<string, number | string>;
}

export interface PathResult {
  nodes: GraphNode[];
  edges: GraphEdge[];
  length: number;
}

export interface CommunityResult {
  id: string;
  summary: string;
  members: GraphNode[];
  edges: GraphEdge[];
}
