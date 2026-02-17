import type { GraphData, GraphNode, GraphEdge, NodeDetail, PathResult, RedFlag } from "./graph";

export interface ApiResponse<T> {
  data: T;
  meta: {
    query_time_ms: number;
    node_count?: number;
    edge_count?: number;
    source?: string;
  };
}

export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}

export interface SearchResult {
  id: string;
  name: string;
  type: string;
  context: string;
  score: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
}

export interface AgencyConcentration {
  agency_id: string;
  agency_name: string;
  hhi: number;
  top_contractors: {
    id: string;
    name: string;
    contract_count: number;
    total_value: number;
    share: number;
  }[];
  procurement_methods: {
    method: string;
    count: number;
    total_value: number;
  }[];
  total_contracts: number;
  total_value: number;
}

export interface ContractorProfile {
  contractor_id: string;
  contractor_name: string;
  registration_number: string;
  classification: string;
  total_contracts: number;
  total_value: number;
  agencies: {
    id: string;
    name: string;
    contract_count: number;
    total_value: number;
  }[];
  co_bidders: {
    id: string;
    name: string;
    co_bid_count: number;
    win_pattern: string;
  }[];
  win_rate: number;
  red_flags: RedFlag[];
}

export interface GraphStats {
  total_nodes: number;
  total_edges: number;
  node_counts: Record<string, number>;
  edge_counts: Record<string, number>;
  total_contract_value: number;
  date_range: {
    earliest: string;
    latest: string;
  };
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  graph_context?: GraphData;
  sources?: string[];
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  context?: {
    focused_node_id?: string;
    visible_node_ids?: string[];
  };
}
