// The confidence-tier and status visual language. This is the honesty layer:
// a recorded relationship must never look like an inferred one.

import type { GraphNode, Overlay, InNews } from "./types";

export interface TierStyle {
  key: "recorded" | "derived" | "namesake" | "predicted";
  label: string;
  desc: string;
  cssVar: string;
  curved: boolean; // derived links are curved + lighter so they read as "soft"
  opacity: number;
}

export const TIERS: Record<string, TierStyle> = {
  recorded: {
    key: "recorded",
    label: "Recorded",
    desc: "On the public record: a contract award, joint venture, revoked license, blacklist, court filing, or COA finding. Solid line, with a source.",
    cssVar: "--tier-recorded",
    curved: false,
    opacity: 1,
  },
  derived: {
    key: "derived",
    label: "Inferred from records",
    desc: "Not a stated relationship but computed from the data: firms that are both top awardees in the same district offices. Curved, lighter line.",
    cssVar: "--tier-derived",
    curved: true,
    opacity: 0.5,
  },
  namesake: {
    key: "namesake",
    label: "Possible namesake (unverified)",
    desc: "A shared surname is not a relationship. Not shown in this release; reserved for a future, human-verified layer.",
    cssVar: "--tier-namesake",
    curved: true,
    opacity: 0.3,
  },
  predicted: {
    key: "predicted",
    label: "Predicted (statistical, unverified)",
    desc: "Not a recorded or inferred relationship, but a Node2Vec similarity in bidding footprint between firms with no recorded joint venture. Not evidence of a relationship. Off by default.",
    cssVar: "--tier-predicted",
    curved: true,
    opacity: 0.35,
  },
};

// Node status, most sensitive first. A colour never carries meaning alone: every
// status ships with a legend label and, on the node card, a source link.
export type StatusKey = "alleged" | "action" | "news" | "entity" | "person" | "normal";

export interface StatusStyle {
  key: StatusKey;
  label: string;
  cssVar: string;
}

export const STATUS: Record<StatusKey, StatusStyle> = {
  alleged: { key: "alleged", label: "Charge or COA flag on record (case pending, allegation)", cssVar: "--alert" },
  action: { key: "action", label: "Recorded official action (license revoked / blacklisted)", cssVar: "--signal" },
  news: { key: "news", label: "Named in recent news coverage", cssVar: "--water" },
  entity: { key: "entity", label: "Procuring entity (DPWH district office)", cssVar: "--node-entity" },
  person: { key: "person", label: "Person on the record (source-linked)", cssVar: "--node-person" },
  normal: { key: "normal", label: "Contractor (no flag on record)", cssVar: "--node-contractor" },
};

const ALLEGED = new Set([
  "charged_pending", "flagged_review", "lookout_order",
  "amlc_freeze", "under_investigation", "capitalization_flag", "performance_flag",
]);
const ACTION = new Set(["license_revoked", "blacklisted", "sec_cancelled"]);

export function nodeStatus(
  node: GraphNode,
  overlay?: Overlay | null,
  inNews?: InNews | null,
): StatusKey {
  if (node.type === "ProcuringEntity") return "entity";
  if (node.type === "Person") return "person";
  const o = overlay?.firms?.[node.key];
  if (o) {
    const types = o.actions.map((a) => a.type);
    if (types.some((t) => ALLEGED.has(t))) return "alleged";
    if (types.some((t) => ACTION.has(t))) return "action";
  }
  if (node.revoked) return "action";
  if (inNews?.firms?.[node.key]) return "news";
  return "normal";
}

// Human labels + tone for each curated overlay action type.
export type ActionTone = "action" | "alleged" | "note" | "cleared";
export const ACTION_META: Record<string, { label: string; tone: ActionTone }> = {
  license_revoked: { label: "License revoked", tone: "action" },
  sec_cancelled: { label: "SEC registration cancelled", tone: "action" },
  blacklisted: { label: "Blacklisted", tone: "action" },
  charged_pending: { label: "Charged (case pending)", tone: "alleged" },
  flagged_review: { label: "Flagged in audit", tone: "alleged" },
  lookout_order: { label: "Immigration lookout order", tone: "alleged" },
  amlc_freeze: { label: "Assets frozen (AMLC)", tone: "alleged" },
  under_investigation: { label: "Under investigation", tone: "alleged" },
  capitalization_flag: { label: "Capitalization questioned", tone: "alleged" },
  performance_flag: { label: "Project performance questioned", tone: "alleged" },
  political_tie: { label: "Political / campaign-finance tie", tone: "note" },
  cleared: { label: "Cleared by regulator", tone: "cleared" },
};

// Honest size: node radius scales with recorded flood-control contract value.
// Persons carry no contract value; they render small and constant.
export function nodeRadius(node: GraphNode): number {
  if (node.type === "Person") return 4;
  const v = node.type === "Contractor" ? node.fc_value ?? 0 : node.fc_value ?? 0;
  const min = 2.5;
  const max = node.type === "ProcuringEntity" ? 11 : 16;
  if (v <= 0) return min;
  // sqrt so area (not radius) tracks value; clamp to a readable band.
  const r = Math.sqrt(v / 1e9) * 2.4;
  return Math.max(min, Math.min(max, r));
}

export function communityVar(community: number | null | undefined): string {
  if (community == null) return "--cat-other";
  const slot = (community % 8) + 1;
  return `--cat-${slot}`;
}

// Resolve a CSS custom property to its computed hex (Sigma needs concrete colours).
export function cssColor(varName: string, fallback = "#888"): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
  return v || fallback;
}
