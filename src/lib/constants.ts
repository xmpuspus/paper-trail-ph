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
  "All data shown is from public records. Red flags are statistical indicators that may warrant further investigation — they are not accusations of wrongdoing.";

export const SUGGESTED_QUESTIONS = [
  "What is Golden Dragon Enterprises' connection to the Binay family?",
  "Which contractors dominate DPWH Region III procurement?",
  "Are Pacific Roadworks and Golden Dragon co-bidding? Show their bid rotation pattern.",
  "Show me the circular subcontracting between Pacific Roadworks and Pampanga River Construction",
  "Is MedPrime Supply Corp a shell company? What's their capital vs contract value?",
  "How is Metro Star Builders connected to blacklisted Metro Prime Construction?",
  "Who donated to Mayor Binay's campaign and then won contracts?",
  "What is the connection between Governor Dy's family and contracts in Makati?",
  "Show me DPWH Tarlac's contractor concentration — how many bidders compete?",
  "How has Mayor Binay's declared net worth changed between 2019 and 2023?",
  "Which agencies have the most COA audit findings?",
  "Which contractors share directors or addresses? Are any linked to blacklisted companies?",
];

export const INSIGHT_BANNERS = [
  {
    text: "Circular subcontracting: P42M flows back to Pacific Roadworks via Pampanga River Construction",
    query: "Show me the circular subcontracting pattern between Pacific Roadworks and Pampanga River Construction. How much money flows in the circle?",
    type: "pattern" as const,
  },
  {
    text: "MedPrime Supply Corp: P625K capital, P890M in contracts — ratio 1:1,424",
    query: "Is MedPrime Supply Corp a shell company? Show me their registered capital vs total contract value.",
    type: "risk" as const,
  },
  {
    text: "Metro Star Builders shares director and address with blacklisted Metro Prime",
    query: "How is Metro Star Builders Corp connected to the blacklisted Metro Prime Construction? Do they share directors or addresses?",
    type: "pattern" as const,
  },
  {
    text: "Golden Dragon donated P5M to Binay campaign, then won P101M in Makati contracts",
    query: "Who donated to Mayor Binay's campaign and then won contracts from the Makati city government?",
    type: "risk" as const,
  },
  {
    text: "Cagayan Valley Builders wins in Makati — owners linked to allied governor",
    query: "What is the connection between Governor Dy's family in Isabela and contracts being won in Makati? Trace the full path.",
    type: "dynasty" as const,
  },
  {
    text: "DPWH Tarlac: 100% of contracts to one company, all single-bidder",
    query: "Show me DPWH DEO Tarlac's contractor concentration. How many companies compete for their contracts?",
    type: "audit" as const,
  },
  {
    text: "Pacific Roadworks and Golden Dragon co-bid 8 times with alternating wins",
    query: "Are Pacific Roadworks and Golden Dragon Enterprises co-bidding together? Show their bid rotation pattern and win history.",
    type: "pattern" as const,
  },
  {
    text: "Mayor Binay's declared net worth jumped 3x between SALN filings",
    query: "How has Mayor Binay's declared net worth changed between 2019 and 2023? Show the SALN timeline.",
    type: "audit" as const,
  },
];

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
