import type { NodeType } from "@/types/graph";

export const NODE_LABELS: Record<NodeType, string> = {
  Politician: "Politician",
  PoliticalFamily: "Political Family",
  Municipality: "Municipality",
  Agency: "Agency",
  Contract: "Contract",
  Contractor: "Contractor",
  AuditFinding: "Audit Finding",
  Bill: "Bill",
  Person: "Person",
  CampaignDonation: "Campaign Donation",
  BlacklistEntry: "Blacklist Entry",
  SALNRecord: "SALN Record",
};

export const NODE_COLORS: Record<NodeType, string> = {
  Politician: "#0038A8",
  PoliticalFamily: "#1A1A5E",
  Municipality: "#607D8B",
  Agency: "#0D7377",
  Contract: "#D4A843",
  Contractor: "#2E7D32",
  AuditFinding: "#D32F2F",
  Bill: "#7B1FA2",
  Person: "#8D6E63",
  CampaignDonation: "#E65100",
  BlacklistEntry: "#B71C1C",
  SALNRecord: "#1565C0",
};

export const NODE_SHAPES: Record<NodeType, string> = {
  Politician: "circle",
  PoliticalFamily: "bordered",
  Municipality: "square",
  Agency: "square",
  Contract: "diamond",
  Contractor: "triangle",
  AuditFinding: "bordered",
  Bill: "square",
  Person: "circle",
  CampaignDonation: "diamond",
  BlacklistEntry: "bordered",
  SALNRecord: "square",
};

export const NODE_SIZES: Record<NodeType, number> = {
  Politician: 8,
  PoliticalFamily: 10,
  Municipality: 6,
  Agency: 9,
  Contract: 4,
  Contractor: 7,
  AuditFinding: 6,
  Bill: 5,
  Person: 4,
  CampaignDonation: 5,
  BlacklistEntry: 5,
  SALNRecord: 4,
};

export const EDGE_COLORS: Record<string, string> = {
  MEMBER_OF: "#6366f1",
  GOVERNS: "#0038A8",
  HAS_AGENCY: "#94a3b8",
  PROCURED: "#0D7377",
  AWARDED_TO: "#D4A843",
  BID_ON: "#a3a3a3",
  CO_BID_WITH: "#f97316",
  SUBCONTRACTED_TO: "#8b5cf6",
  AUDITED: "#D32F2F",
  INVOLVES_OFFICIAL: "#ef4444",
  AUTHORED: "#7B1FA2",
  CO_AUTHORED_WITH: "#a78bfa",
  OWNED_BY: "#78716c",
  FAMILY_OF: "#ec4899",
  LOCATED_IN: "#607D8B",
  ASSOCIATED_WITH: "#f59e0b",
  DONATED_TO: "#E65100",
  BLACKLISTED: "#B71C1C",
  DECLARED_WEALTH: "#1565C0",
  RE_REGISTERED_AS: "#880E4F",
  SAME_ADDRESS_AS: "#4E342E",
  SHARES_DIRECTOR_WITH: "#4E342E",
  ALLIED_WITH: "#283593",
};

export const API_BASE = "/api/v1";

export const DISCLAIMER =
  "All data shown is sourced from Philippine public records: DPWH Transparency Portal (transparency.dpwh.gov.ph), PhilGEPS (philgeps.gov.ph), Open Congress PH (open-congress-api.bettergov.ph), PSA (psa.gov.ph), and COA audit reports. Red flags are statistical indicators that may warrant further investigation — they are not accusations of wrongdoing.";

export const SUGGESTED_QUESTIONS = [
  "Which contractors dominate DPWH procurement in a specific region?",
  "Show me contractors that frequently co-bid on the same projects.",
  "Which agencies have the highest contractor concentration (HHI)?",
  "Are there contracts clustering just below the competitive bidding threshold?",
  "Which contractors operate across the most regions?",
  "Show me single-bidder contract awards — which agencies have the most?",
  "Which contractors share directors or registered addresses?",
  "What are the largest contracts awarded through negotiated procurement?",
  "Which regions have the lowest project completion rates?",
  "Show me COA audit findings by agency and severity.",
  "Which contractors have the highest total contract value?",
  "Are there contractors linked to blacklist entries?",
];

// Insight banners are populated dynamically from real graph analysis.
// No hardcoded findings — all insights must come from actual data loaded via the pipeline.
export const INSIGHT_BANNERS: {
  text: string;
  query: string;
  type: "pattern" | "risk" | "dynasty" | "audit";
}[] = [];

export const CURRENCY_FORMAT = new Intl.NumberFormat("en-PH", {
  style: "currency",
  currency: "PHP",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

export function formatPeso(amount: number): string {
  return CURRENCY_FORMAT.format(amount);
}

export function formatCompact(amount: number): string {
  if (amount == null || isNaN(amount)) return "—";
  if (amount >= 1_000_000_000) return `P${(amount / 1_000_000_000).toFixed(1)}B`;
  if (amount >= 1_000_000) return `P${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `P${(amount / 1_000).toFixed(0)}K`;
  return `P${amount}`;
}
