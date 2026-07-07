// Shapes of the baked JSON in public/data (produced by scripts/build_graph.py
// and the curated overlay/in_news files). Every field here is a recorded fact
// from the DPWH dataset or a source-linked curated action.

export type NodeType = "Contractor" | "ProcuringEntity" | "Person";
export type Tier = "recorded" | "derived" | "namesake" | "predicted";

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
  first_year?: number | null;
  top_deos?: TopDeo[];
  // procuring entity
  region?: string;
  hhi_fc?: number;
  concentrated?: boolean;
  n_fc_firms?: number;
  // person (curated, source-linked in overlay.json)
  role?: string;
  status?: string;
  sources?: string[];
  firms?: string[];
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  tier: Tier;
  weight: number;
  value?: number;
  first_year?: number | null;
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
  // person entries in the index (curated, source-linked)
  role?: string;
  status?: string;
  sources?: string[];
  firms?: string[];
}

// ---- Offline network analytics (scripts/build_analytics.py) ----

export interface TemporalYear {
  year: number;
  fc_contracts: number;
  fc_value: number;
  named_share_pct: number;
  entrant_share_pct: number;
  cr10_pct: number;
  concentrated_deos: number;
  active_deos: number;
  jv_firms_cum: number;
  jv_pairs_cum: number;
  jv_giant_component: number;
}

export interface TemporalData {
  _meta: { method: string; disclaimer: string };
  years: TemporalYear[];
}

export interface SignalSection<T> {
  definition: string;
  count: number;
  items: T[];
}

export interface SignalsData {
  _meta: { framing: string; disclaimer: string };
  footprint_pairs: SignalSection<{
    firms: string[]; keys: string[]; shared_offices: number; jaccard: number; combined_fc_value: number;
  }>;
  jv_groups: SignalSection<{
    firms: string[]; keys: string[]; size: number; internal_jv_pairs: number; density: number; combined_fc_value: number;
  }>;
  alternation: SignalSection<{
    office: string; hhi: number; years: number[]; top_by_year: string[]; firms: string[]; keys: string[]; switches: number;
  }>;
  entrants: SignalSection<{
    firm: string; key: string; first_year: number; value_first_two_years: number; contracts: number;
  }>;
}

export interface PredictedPair {
  firms: string[];
  keys: string[];
  score: number;
  adamic_adar: number;
  shared_offices: number;
}

export interface PredictedTies {
  _meta: { method: string; caveat: string; disclaimer: string };
  count: number;
  pairs: PredictedPair[];
}

// ---- Recorded SEC corporate-registry layer (scripts/build_sec.py) ----

export interface SecFirm {
  key: string;
  name: string;
  graph_label?: string;
  sec_reg_no: string;
  reg_year: number;
  company_type: string;
  paid_up_capital: number | null;
  capital_note?: string;
  registered_office: string;
  region: string;
  fc_value: number;
  fc_contracts?: number;
  president?: string;
  family_control?: string;
  officer_note?: string;
  gis_url?: string | null;
  aoi_url?: string | null;
  tier: "recorded_sec";
  contract_to_capital?: number;
  re_registration?: { label: string; source: string };
}

export interface SecRatioItem {
  key: string; name: string; fc_value: number; paid_up_capital: number; ratio: number; note?: string;
}
export interface SecCoLocation { locality: string; keys: string[]; firms: string[]; note: string }
export interface SecReReg { key: string; name: string; label: string; source: string }

export interface SecData {
  _meta: {
    purpose: string; tier: string; obtainability_note: string;
    provenance: { label: string; url: string };
    compiled: string; count: number; disclaimer: string; presumption: string;
  };
  firms: Record<string, SecFirm>;
  findings: {
    contract_to_capital: { definition: string; items: SecRatioItem[] };
    co_location: { definition: string; items: SecCoLocation[] };
    re_registration: { definition: string; items: SecReReg[] };
  };
}

// ---- Temporal knowledge-graph analytics (scripts/build_temporal.py) ----

export interface TemporalAnalysis {
  _meta: { disclaimer: string; generated_note: string };
  link_prediction: {
    _meta: { method: string; disclaimer: string };
    macro_auc: number | null;
    by_year: {
      train_upto: number; predict: number; candidates: number; new_jv: number;
      auc: number | null; auc_null_mean?: number; p_label_perm?: number; p_degree_null?: number;
      top_hits?: { firms: string[]; score: number }[]; note?: string;
    }[];
  };
  dynamic_communities: {
    _meta: { method: string; disclaimer: string };
    by_year: { year: number; firms_linked: number; communities: number; largest: number; top_sizes: number[]; stability_vs_prev: number | null }[];
  };
  change_points: {
    _meta: { method: string; disclaimer: string };
    metrics: Record<string, { change_year: number; p_value: number; before_mean: number; after_mean: number | null }>;
  };
  motifs: {
    _meta: { method: string; disclaimer: string };
    counts: { jv_before_awards: number; awards_before_jv: number; concurrent: number };
    examples: { firms: string[]; jv_year: number; awards_median_year: number; relation: string; shared_awards: number }[];
  };
  hetero: {
    _meta: { purpose: string; node_types: string[]; edge_types: string[]; disclaimer: string };
    node_counts: Record<string, number>;
    edge_count: number;
    edges: { head: string; head_type: string; relation: string; tail: string; tail_type: string; date: string | null; sources: string[] }[];
  };
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
