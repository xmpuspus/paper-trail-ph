// Shapes of the baked JSON in public/data (produced by scripts/build_graph.py
// and the curated overlay/in_news files). Every field here is a recorded fact
// from the DPWH dataset or a source-linked curated action.

export type NodeType = "Contractor" | "ProcuringEntity";
export type Tier = "recorded" | "derived" | "namesake";

export interface TopDeo {
  deo: string;
  contracts?: number;
  value?: number;
  fc_contracts: number;
  fc_value: number;
}

export interface GraphNode {
  id: string;
  key: string;
  label: string;
  type: NodeType;
  // contractor
  revoked?: boolean;
  former?: string | null;
  n_contracts?: number;
  value?: number;
  fc_contracts?: number;
  fc_value?: number;
  n_regions?: number;
  n_deos?: number;
  community?: number | null;
  betweenness?: number;
  pagerank?: number;
  degree?: number;
  top_deos?: TopDeo[];
  // procuring entity
  region?: string;
  hhi_fc?: number;
  concentrated?: boolean;
  n_fc_firms?: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  tier: Tier;
  weight: number;
  value?: number;
  label: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Entity {
  id: string;
  key: string;
  label: string;
  type: NodeType;
  revoked?: boolean;
  former?: string | null;
  n_contracts: number;
  value: number;
  fc_contracts: number;
  fc_value: number;
  n_regions?: number;
  n_deos?: number;
  top_category?: string | null;
  region?: string;
  hhi_fc?: number;
  concentrated?: boolean;
  n_fc_firms?: number;
  top_deos?: TopDeo[];
  coawardees?: { key: string; name: string; shared: number; fc_shared: number }[];
}

export interface Stats {
  generated_note: string;
  source: { name: string; license: string; url: string };
  totals: { contracts: number; total_value: number; contractors: number; district_offices: number };
  flood_control: { category: string; contracts: number; value: number; firms: number; district_offices: number };
  revoked: { firms: number; contracts: number; value: number };
  concentration: {
    threshold: number;
    concentrated_fc_deos: number;
    top_concentrated: { deo: string; region: string; hhi: number; fc_value: number; fc_contracts: number; n_firms: number }[];
  };
  communities: number;
  top_flood_control_firms: { key: string; name: string; revoked: boolean; fc_value: number; fc_contracts: number }[];
  graph_main_nodes: number;
  graph_main_edges: number;
  graph_scandal_nodes: number;
  graph_scandal_edges: number;
}

export interface OverlaySource { label: string; url: string; type: string; date: string }
export interface OverlayAction { type: string; label: string; status: string; date: string; source: string }
export interface OverlayFirm { owner?: string; actions: OverlayAction[] }
export interface OverlayPerson { id: string; name: string; role: string; firms: string[]; status: string; sources: string[] }
export interface Overlay {
  _meta: { purpose: string; compiled: string; disclaimer: string; verification_note: string };
  sources: Record<string, OverlaySource>;
  investigation: { body: string; role: string; chair?: string; period: string; note: string; source: string }[];
  context: { top15_note: string; top15_source: string };
  persons: OverlayPerson[];
  firms: Record<string, OverlayFirm>;
}

export interface InNewsEntry { headline: string; source: string; url: string; date: string; articles: number }
export interface InNews {
  _meta: { reviewed: boolean; window: string; method: string; disclaimer: string };
  firms: Record<string, InNewsEntry>;
}
